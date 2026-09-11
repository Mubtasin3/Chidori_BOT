import asyncio
import functools
import logging
import random
from dataclasses import dataclass, field
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp

from views.music import MusicControls

log = logging.getLogger("GangFund.Music")

# yt-dlp is used only in executor threads so the Discord event loop never blocks.
YTDLP_BASE = {
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "ignoreerrors": False,
    "format": "bestaudio/best",
    "source_address": "0.0.0.0",
    "socket_timeout": 15,
    "retries": 3,
    "fragment_retries": 3,
    "extractor_retries": 3,
}

FFMPEG_BEFORE = (
    "-reconnect 1 -reconnect_streamed 1 -reconnect_at_eof 1 "
    "-reconnect_delay_max 5 -nostdin"
)
FFMPEG_OPTIONS = "-vn -loglevel warning"

AUTO_DISCONNECT_SECONDS = 120
MAX_QUEUE = 250
MAX_HISTORY = 50


@dataclass
class Track:
    title: str
    webpage_url: str
    duration: int = 0
    thumbnail: Optional[str] = None
    requested_by: Optional[int] = None
    stream_url: Optional[str] = None

    @property
    def duration_text(self) -> str:
        if not self.duration:
            return "LIVE/unknown"
        seconds = int(self.duration)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


@dataclass
class GuildPlayer:
    queue: list[Track] = field(default_factory=list)
    history: list[Track] = field(default_factory=list)
    current: Optional[Track] = None
    voice: Optional[discord.VoiceClient] = None
    volume: float = 0.75
    loop_mode: str = "off"  # off, song, queue
    text_channel_id: Optional[int] = None
    started_at: float = 0.0
    generation: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    disconnect_task: Optional[asyncio.Task] = None


class Music(commands.Cog):
    """Advanced per-guild music player using yt-dlp + FFmpeg."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: dict[int, GuildPlayer] = {}

    def get_player(self, guild_id: int) -> GuildPlayer:
        return self.players.setdefault(guild_id, GuildPlayer())

    def _is_url(self, value: str) -> bool:
        return value.startswith(("http://", "https://"))

    async def _ydl(self, query: str, *, flat: bool = False):
        loop = asyncio.get_running_loop()
        opts = dict(YTDLP_BASE)
        opts["extract_flat"] = flat
        opts["noplaylist"] = False if flat else True
        if not self._is_url(query):
            query = f"ytsearch1:{query}"

        def worker():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(query, download=False)

        return await loop.run_in_executor(None, worker)

    @staticmethod
    def _track_from_entry(entry: dict, requester: int) -> Optional[Track]:
        if not entry:
            return None
        webpage = entry.get("webpage_url") or entry.get("original_url") or entry.get("url")
        if not webpage:
            return None
        return Track(
            title=entry.get("title") or "Unknown title",
            webpage_url=webpage,
            duration=int(entry.get("duration") or 0),
            thumbnail=entry.get("thumbnail"),
            requested_by=requester,
        )

    async def search_tracks(self, query: str, requester: int, limit: int = 5) -> list[Track]:
        loop = asyncio.get_running_loop()
        opts = dict(YTDLP_BASE)
        opts.update({"extract_flat": True, "noplaylist": True})

        def worker():
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                return data.get("entries", []) if data else []

        entries = await loop.run_in_executor(None, worker)
        return [t for t in (self._track_from_entry(e, requester) for e in entries) if t]

    async def resolve_stream(self, track: Track) -> Track:
        """Refresh the expiring media URL immediately before playback."""
        loop = asyncio.get_running_loop()
        opts = dict(YTDLP_BASE)
        opts["noplaylist"] = True

        def worker():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(track.webpage_url, download=False)

        data = await loop.run_in_executor(None, worker)
        if not data or not data.get("url"):
            raise RuntimeError("Could not obtain a playable audio stream.")
        track.stream_url = data["url"]
        track.title = data.get("title") or track.title
        track.duration = int(data.get("duration") or track.duration or 0)
        track.thumbnail = data.get("thumbnail") or track.thumbnail
        track.webpage_url = data.get("webpage_url") or track.webpage_url
        return track

    async def extract_request(self, query: str, requester: int) -> list[Track]:
        """Return one or many tracks. Playlist URLs are expanded as a queue."""
        if self._is_url(query):
            data = await self._ydl(query, flat=True)
            if data and data.get("entries"):
                tracks = []
                for entry in data["entries"]:
                    t = self._track_from_entry(entry, requester)
                    if t:
                        tracks.append(t)
                    if len(tracks) >= MAX_QUEUE:
                        break
                if tracks:
                    return tracks

            if data and data.get("url") and not data.get("_type"):
                t = self._track_from_entry(data, requester)
                return [t] if t else []

            # Flat playlist entries can sometimes only expose an id/url.
            if data and data.get("webpage_url"):
                t = self._track_from_entry(data, requester)
                return [t] if t else []

            raise RuntimeError("That URL did not contain a playable track.")

        data = await self._ydl(query)
        if data and data.get("entries"):
            data = next((e for e in data["entries"] if e), None)
        track = self._track_from_entry(data, requester) if data else None
        if not track:
            raise RuntimeError("No playable result found.")
        return [track]

    async def ensure_voice(self, interaction: discord.Interaction) -> GuildPlayer:
        if not interaction.guild:
            raise RuntimeError("Music commands can only be used in a server.")
        if not interaction.user.voice or not interaction.user.voice.channel:
            raise RuntimeError("Join a voice channel first.")

        p = self.get_player(interaction.guild.id)
        target = interaction.user.voice.channel

        if p.voice and p.voice.is_connected():
            if p.voice.channel != target:
                raise RuntimeError(f"You must be in **{p.voice.channel.name}** to control the player.")
            return p

        p.voice = await target.connect(reconnect=True, self_deaf=True)
        p.text_channel_id = interaction.channel.id if interaction.channel else None
        return p

    def _check_control(self, interaction: discord.Interaction) -> GuildPlayer:
        if not interaction.guild:
            raise RuntimeError("This command can only be used in a server.")
        p = self.get_player(interaction.guild.id)
        if not p.voice or not p.voice.is_connected():
            raise RuntimeError("I'm not connected to a voice channel.")
        if not interaction.user.voice or interaction.user.voice.channel != p.voice.channel:
            raise RuntimeError(f"Join **{p.voice.channel.name}** to control the player.")
        return p

    async def _send_channel(self, guild_id: int, embed: discord.Embed):
        p = self.get_player(guild_id)
        if not p.text_channel_id:
            return
        channel = self.bot.get_channel(p.text_channel_id)
        if channel and hasattr(channel, "send"):
            try:
                await channel.send(embed=embed)
            except Exception:
                log.exception("Could not send music update")

    async def _disconnect_later(self, guild_id: int):
        try:
            await asyncio.sleep(AUTO_DISCONNECT_SECONDS)
            p = self.get_player(guild_id)
            if p.voice and p.voice.is_connected() and not p.queue and not p.voice.is_playing():
                await p.voice.disconnect()
                p.voice = None
                p.current = None
                await self._send_channel(
                    guild_id,
                    discord.Embed(
                        title="👋 Music player disconnected",
                        description="Queue ended and the voice channel was inactive.",
                        color=discord.Color.orange(),
                    ),
                )
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("Auto-disconnect failed")

    def _cancel_disconnect(self, p: GuildPlayer):
        if p.disconnect_task and not p.disconnect_task.done():
            p.disconnect_task.cancel()
        p.disconnect_task = None

    async def start_next(self, guild_id: int, *, announce: bool = True):
        p = self.get_player(guild_id)
        async with p.lock:
            if not p.voice or not p.voice.is_connected():
                return
            if p.voice.is_playing() or p.voice.is_paused():
                return

            if p.loop_mode == "song" and p.current:
                track = p.current
            elif p.queue:
                track = p.queue.pop(0)
                if p.current and p.current not in p.history:
                    p.history.append(p.current)
                p.current = track
            else:
                p.current = None
                p.disconnect_task = asyncio.create_task(self._disconnect_later(guild_id))
                return

            self._cancel_disconnect(p)
            p.generation += 1
            generation = p.generation

        try:
            track = await self.resolve_stream(track)
            p = self.get_player(guild_id)
            if not p.voice or not p.voice.is_connected():
                return

            source = discord.FFmpegPCMAudio(
                track.stream_url,
                before_options=FFMPEG_BEFORE,
                options=FFMPEG_OPTIONS,
            )
            source = discord.PCMVolumeTransformer(source, volume=p.volume)

            def after_play(error):
                fut = asyncio.run_coroutine_threadsafe(
                    self._after_track(guild_id, generation, error), self.bot.loop
                )
                try:
                    fut.result(timeout=0)
                except Exception:
                    pass

            p.voice.play(source, after=after_play)
            if announce:
                embed = self.nowplaying_embed(p)
                await self._send_channel(guild_id, embed)

        except Exception as exc:
            log.warning("Playback failed for guild %s: %s", guild_id, exc)
            await self._send_channel(
                guild_id,
                discord.Embed(
                    title="⚠️ Playback failed",
                    description=f"**{track.title}**\n`{str(exc)[:800]}`\n\nTrying the next track...",
                    color=discord.Color.red(),
                ),
            )
            p.current = None
            await self.start_next(guild_id)

    async def _after_track(self, guild_id: int, generation: int, error):
        await asyncio.sleep(0.25)
        p = self.get_player(guild_id)
        if generation != p.generation:
            return
        if error:
            log.warning("FFmpeg playback error in guild %s: %s", guild_id, error)

        if p.loop_mode == "queue" and p.current:
            p.queue.append(p.current)
        p.current = None
        await self.start_next(guild_id)

    def nowplaying_embed(self, p: GuildPlayer) -> discord.Embed:
        track = p.current
        if not track:
            return discord.Embed(title="🎵 Nothing is playing", description="The player is idle.")
        e = discord.Embed(
            title="🎵 Now Playing",
            description=f"**[{discord.utils.escape_markdown(track.title)}]({track.webpage_url})**",
            color=discord.Color.blurple(),
        )
        e.add_field(name="⏱️ Duration", value=track.duration_text, inline=True)
        e.add_field(name="🔊 Volume", value=f"{round(p.volume * 100)}%", inline=True)
        e.add_field(name="🔁 Loop", value=p.loop_mode.title(), inline=True)
        if track.requested_by:
            e.add_field(name="👤 Requested by", value=f"<@{track.requested_by}>", inline=True)
        if track.thumbnail:
            e.set_thumbnail(url=track.thumbnail)
        e.set_footer(text="Chidori Music • Use the buttons or /help")
        return e

    async def send_error(self, interaction: discord.Interaction, message: str):
        e = discord.Embed(title="❌ Music Error", description=message, color=discord.Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=e, ephemeral=True)
        else:
            await interaction.response.send_message(embed=e, ephemeral=True)

    async def control(self, interaction: discord.Interaction, action: str):
        try:
            p = self._check_control(interaction)
            if action == "pause":
                if not p.voice.is_playing():
                    raise RuntimeError("Nothing is currently playing.")
                p.voice.pause()
            elif action == "resume":
                if not p.voice.is_paused():
                    raise RuntimeError("The player is not paused.")
                p.voice.resume()
            elif action == "skip":
                if not p.voice.is_playing() and not p.voice.is_paused():
                    raise RuntimeError("Nothing is currently playing.")
                p.voice.stop()
            elif action == "previous":
                if len(p.history) < 1:
                    raise RuntimeError("There is no previous track.")
                previous = p.history.pop()
                if p.current:
                    p.queue.insert(0, p.current)
                p.current = previous
                if p.voice.is_playing() or p.voice.is_paused():
                    p.voice.stop()
                else:
                    await self.start_next(interaction.guild.id)
            elif action == "shuffle":
                if len(p.queue) < 2:
                    raise RuntimeError("Add at least two tracks to shuffle.")
                random.shuffle(p.queue)
            elif action == "clear":
                p.queue.clear()
            elif action == "stop":
                p.queue.clear()
                p.history.clear()
                p.current = None
                p.generation += 1
                if p.voice and p.voice.is_connected():
                    if p.voice.is_playing() or p.voice.is_paused():
                        p.voice.stop()
                    await p.voice.disconnect()
                p.voice = None
            elif action == "loop":
                modes = ["off", "song", "queue"]
                p.loop_mode = modes[(modes.index(p.loop_mode) + 1) % len(modes)]
            elif action == "vol_down":
                p.volume = max(0.05, round(p.volume - 0.05, 2))
                if p.voice and p.voice.source and hasattr(p.voice.source, "volume"):
                    p.voice.source.volume = p.volume
            elif action == "vol_up":
                p.volume = min(1.0, round(p.volume + 0.05, 2))
                if p.voice and p.voice.source and hasattr(p.voice.source, "volume"):
                    p.voice.source.volume = p.volume
            else:
                raise RuntimeError("Unknown music action.")

            labels = {
                "pause": "⏸️ Paused", "resume": "▶️ Resumed", "skip": "⏭️ Skipped",
                "previous": "⏮️ Playing previous track", "shuffle": "🔀 Queue shuffled",
                "clear": "🧹 Queue cleared", "stop": "⏹️ Player stopped",
                "loop": f"🔁 Loop: **{p.loop_mode}**", "vol_down": f"🔉 Volume: **{round(p.volume*100)}%**",
                "vol_up": f"🔊 Volume: **{round(p.volume*100)}%**",
            }
            await interaction.response.send_message(labels[action], ephemeral=True)
        except Exception as exc:
            await self.send_error(interaction, str(exc))

    @app_commands.command(name="play", description="Play a song, YouTube URL, or playlist and add it to the queue.")
    @app_commands.describe(query="Song name, YouTube URL, or playlist URL")
    async def play(self, interaction: discord.Interaction, query: str):
        try:
            if not interaction.guild:
                raise RuntimeError("This command can only be used in a server.")
            p = await self.ensure_voice(interaction)
            p.text_channel_id = interaction.channel.id if interaction.channel else p.text_channel_id
            await interaction.response.defer()
            tracks = await self.extract_request(query, interaction.user.id)
            available = MAX_QUEUE - len(p.queue)
            if available <= 0:
                raise RuntimeError(f"Queue limit reached ({MAX_QUEUE} tracks).")
            tracks = tracks[:available]
            p.queue.extend(tracks)
            was_idle = not p.voice.is_playing() and not p.voice.is_paused() and p.current is None
            if was_idle:
                await self.start_next(interaction.guild.id)

            if len(tracks) == 1:
                e = discord.Embed(
                    title="🎵 Added to Queue",
                    description=f"[{tracks[0].title}]({tracks[0].webpage_url})",
                    color=discord.Color.green(),
                )
            else:
                e = discord.Embed(
                    title="📚 Playlist Added",
                    description=f"Added **{len(tracks)}** tracks to the queue.",
                    color=discord.Color.green(),
                )
                e.add_field(name="First track", value=tracks[0].title[:1024], inline=False)
            await interaction.followup.send(embed=e, view=MusicControls())
        except Exception as exc:
            await self.send_error(interaction, str(exc))

    @app_commands.command(name="search", description="Search YouTube for songs and show the top results.")
    @app_commands.describe(query="What should I search for?")
    async def search(self, interaction: discord.Interaction, query: str):
        try:
            await interaction.response.defer()
            tracks = await self.search_tracks(query, interaction.user.id)
            if not tracks:
                raise RuntimeError("No results found.")
            e = discord.Embed(title="🔎 YouTube Search", description="", color=discord.Color.blurple())
            lines = []
            for n, t in enumerate(tracks, 1):
                lines.append(f"**{n}.** [{t.title}]({t.webpage_url}) • `{t.duration_text}`")
            e.description = "\n".join(lines)
            e.set_footer(text="Use /play with a result title or URL to play it.")
            await interaction.followup.send(embed=e)
        except Exception as exc:
            await self.send_error(interaction, str(exc))

    @app_commands.command(name="queue", description="Show the current song and queued tracks.")
    @app_commands.describe(page="Queue page number (20 tracks per page).")
    async def queue(self, interaction: discord.Interaction, page: app_commands.Range[int, 1, 100] = 1):
        try:
            if not interaction.guild:
                raise RuntimeError("This command can only be used in a server.")
            p = self.get_player(interaction.guild.id)
            e = discord.Embed(title="📋 Music Queue", color=discord.Color.blurple())
            if p.current:
                e.add_field(name="🎵 Now Playing", value=f"[{p.current.title}]({p.current.webpage_url})", inline=False)
            else:
                e.add_field(name="🎵 Now Playing", value="Nothing", inline=False)

            start = (page - 1) * 20
            items = p.queue[start:start + 20]
            if not items:
                if page > 1 and p.queue:
                    raise RuntimeError(f"Page {page} is empty. There are only {(len(p.queue)+19)//20} pages.")
                text = "Queue is empty."
            else:
                text = "\n".join(
                    f"`{start+n}.` [{t.title}]({t.webpage_url}) • `{t.duration_text}`"
                    for n, t in enumerate(items, 1)
                )
            e.add_field(name=f"📝 Up Next • Page {page}", value=text[:1024], inline=False)
            e.set_footer(text=f"{len(p.queue)} queued • Volume {round(p.volume*100)}% • Loop {p.loop_mode}")
            await interaction.response.send_message(embed=e, view=MusicControls())
        except Exception as exc:
            await self.send_error(interaction, str(exc))

    @app_commands.command(name="nowplaying", description="Show detailed information about the currently playing song.")
    async def nowplaying(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await self.send_error(interaction, "This command can only be used in a server.")
        await interaction.response.send_message(embed=self.nowplaying_embed(self.get_player(interaction.guild.id)), view=MusicControls())

    @app_commands.command(name="skip", description="Skip the currently playing song and start the next one.")
    async def skip(self, interaction: discord.Interaction):
        await self.control(interaction, "skip")

    @app_commands.command(name="previous", description="Go back to the previous track.")
    async def previous(self, interaction: discord.Interaction):
        await self.control(interaction, "previous")

    @app_commands.command(name="pause", description="Pause the currently playing song.")
    async def pause(self, interaction: discord.Interaction):
        await self.control(interaction, "pause")

    @app_commands.command(name="resume", description="Resume a paused song.")
    async def resume(self, interaction: discord.Interaction):
        await self.control(interaction, "resume")

    @app_commands.command(name="stop", description="Stop playback, clear the queue, and leave the voice channel.")
    async def stop(self, interaction: discord.Interaction):
        await self.control(interaction, "stop")

    @app_commands.command(name="disconnect", description="Disconnect the bot from the current voice channel without playing anything.")
    async def disconnect(self, interaction: discord.Interaction):
        await self.control(interaction, "stop")

    @app_commands.command(name="shuffle", description="Randomize the order of all tracks currently in the queue.")
    async def shuffle(self, interaction: discord.Interaction):
        await self.control(interaction, "shuffle")

    @app_commands.command(name="clear", description="Remove all waiting tracks while keeping the current song playing.")
    async def clear(self, interaction: discord.Interaction):
        await self.control(interaction, "clear")

    @app_commands.command(name="loop", description="Set the loop mode: off, current song, or entire queue.")
    @app_commands.describe(mode="Choose how playback should loop.")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Off", value="off"),
        app_commands.Choice(name="Current song", value="song"),
        app_commands.Choice(name="Queue", value="queue"),
    ])
    async def loop(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        try:
            p = self._check_control(interaction)
            p.loop_mode = mode.value
            await interaction.response.send_message(f"🔁 Loop mode set to **{mode.name}**.", ephemeral=True)
        except Exception as exc:
            await self.send_error(interaction, str(exc))

    @app_commands.command(name="volume", description="Set the music player volume from 5% to 100%.")
    @app_commands.describe(percent="Volume percentage, from 5 to 100.")
    async def volume(self, interaction: discord.Interaction, percent: app_commands.Range[int, 5, 100]):
        try:
            p = self._check_control(interaction)
            p.volume = percent / 100
            if p.voice.source and hasattr(p.voice.source, "volume"):
                p.voice.source.volume = p.volume
            await interaction.response.send_message(f"🔊 Volume set to **{percent}%**.", ephemeral=True)
        except Exception as exc:
            await self.send_error(interaction, str(exc))

    @app_commands.command(name="remove", description="Remove one waiting track from the queue by its queue number.")
    @app_commands.describe(position="Queue position shown by /queue (starts at 1).")
    async def remove(self, interaction: discord.Interaction, position: app_commands.Range[int, 1, 250]):
        try:
            p = self._check_control(interaction)
            index = position - 1
            if index >= len(p.queue):
                raise RuntimeError("That queue position does not exist.")
            track = p.queue.pop(index)
            await interaction.response.send_message(f"🗑️ Removed **{track.title}**.", ephemeral=True)
        except Exception as exc:
            await self.send_error(interaction, str(exc))

    @app_commands.command(name="join", description="Make the bot join your current voice channel.")
    async def join(self, interaction: discord.Interaction):
        try:
            await self.ensure_voice(interaction)
            await interaction.response.send_message("🔊 Joined your voice channel.", ephemeral=True)
        except Exception as exc:
            await self.send_error(interaction, str(exc))

    async def cog_unload(self):
        for p in self.players.values():
            if p.disconnect_task and not p.disconnect_task.done():
                p.disconnect_task.cancel()
            if p.voice and p.voice.is_connected():
                await p.voice.disconnect(force=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
