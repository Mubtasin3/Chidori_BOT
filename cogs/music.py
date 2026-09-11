import asyncio, random, functools, discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
from views.music import MusicControls

YDL_OPTS={"format":"bestaudio/best","noplaylist":False,"quiet":True,"no_warnings":True,"default_search":"ytsearch"}
FFMPEG_OPTS={"before_options":"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5","options":"-vn"}

class GuildPlayer:
    def __init__(self): self.queue=[]; self.history=[]; self.current=None; self.loop=False; self.voice=None; self.volume=.5

class Music(commands.Cog):
    def __init__(self,bot): self.bot=bot; self.players={}
    def p(self,gid): return self.players.setdefault(gid,GuildPlayer())

    async def extract(self,query):
        loop=asyncio.get_running_loop()
        def work():
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                data=ydl.extract_info(query,download=False)
                if "entries" in data: data=data["entries"][0]
                return {"title":data.get("title","Unknown"),"url":data["url"],"webpage":data.get("webpage_url",query),"duration":data.get("duration",0)}
        return await loop.run_in_executor(None,work)

    async def ensure_voice(self,i):
        if not i.user.voice: raise RuntimeError("Join a voice channel first.")
        p=self.p(i.guild.id)
        if not p.voice or not p.voice.is_connected(): p.voice=await i.user.voice.channel.connect()
        elif p.voice.channel != i.user.voice.channel: raise RuntimeError("You must be in my voice channel.")
        return p

    async def play_next(self,gid):
        p=self.p(gid)
        if not p.voice: return
        if p.loop and p.current: item=p.current
        elif p.queue: item=p.queue.pop(0)
        else:
            p.current=None
            await asyncio.sleep(120)
            if p.voice and p.voice.is_connected() and not p.queue: await p.voice.disconnect()
            return
        p.current=item; p.history.append(item)
        source=await discord.FFmpegOpusAudio.from_probe(item["url"],**FFMPEG_OPTS)
        source=discord.PCMVolumeTransformer(source,volume=p.volume)
        def after(err):
            asyncio.run_coroutine_threadsafe(self.play_next(gid),self.bot.loop)
        p.voice.play(source,after=after)

    @app_commands.command(name="play")
    async def play(self,i,query:str):
        try:
            p=await self.ensure_voice(i)
            await i.response.defer()
            item=await self.extract(query)
            p.queue.append(item)
            if not p.voice.is_playing(): await self.play_next(i.guild.id)
            await i.followup.send(embed=discord.Embed(title="🎵 Added to queue",description=f"[{item['title']}]({item['webpage']})"),view=MusicControls())
        except Exception as e:
            if i.response.is_done(): await i.followup.send(f"❌ {e}",ephemeral=True)
            else: await i.response.send_message(f"❌ {e}",ephemeral=True)

    @app_commands.command(name="search")
    async def search(self,i,query:str):
        try:
            loop=asyncio.get_running_loop()
            def work():
                with yt_dlp.YoutubeDL({**YDL_OPTS,"extract_flat":True,"noplaylist":False}) as ydl:
                    return ydl.extract_info("ytsearch5:"+query,download=False)["entries"]
            entries=await loop.run_in_executor(None,work)
            text="\n".join(f"**{n+1}.** {e.get('title','Unknown')}" for n,e in enumerate(entries))
            await i.response.send_message(embed=discord.Embed(title="🔎 Search Results",description=text or "No results."))
        except Exception as e: await i.response.send_message(f"❌ Search failed: {e}",ephemeral=True)

    async def control(self,i,action):
        p=self.p(i.guild.id)
        if not p.voice or not i.user.voice or p.voice.channel != i.user.voice.channel:
            return await i.response.send_message("You must be in my voice channel.",ephemeral=True)
        if action=="pause" and p.voice.is_playing(): p.voice.pause()
        elif action=="resume" and p.voice.is_paused(): p.voice.resume()
        elif action=="skip" and p.voice.is_playing(): p.voice.stop()
        elif action=="shuffle": random.shuffle(p.queue)
        elif action=="loop": p.loop=not p.loop
        elif action=="stop": p.queue.clear(); p.loop=False; p.current=None; p.voice.stop(); await p.voice.disconnect(); p.voice=None
        elif action=="previous" and len(p.history)>1:
            p.queue.insert(0,p.history[-2])
            p.voice.stop()
        await i.response.send_message(f"🎵 `{action}` done.",ephemeral=True)

    @app_commands.command(name="skip")
    async def skip(self,i): await self.control(i,"skip")
    @app_commands.command(name="pause")
    async def pause(self,i): await self.control(i,"pause")
    @app_commands.command(name="resume")
    async def resume(self,i): await self.control(i,"resume")
    @app_commands.command(name="stop")
    async def stop(self,i): await self.control(i,"stop")
    @app_commands.command(name="shuffle")
    async def shuffle(self,i): await self.control(i,"shuffle")
    @app_commands.command(name="loop")
    async def loop(self,i): await self.control(i,"loop")
    @app_commands.command(name="queue")
    async def queue(self,i):
        p=self.p(i.guild.id); text="\n".join(f"{n+1}. {x['title']}" for n,x in enumerate(p.queue)) or "Queue is empty."
        await i.response.send_message(embed=discord.Embed(title="🎶 Queue",description=text))

async def setup(bot): await bot.add_cog(Music(bot))
