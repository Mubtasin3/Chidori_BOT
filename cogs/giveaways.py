import discord, random
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone, timedelta
from database.database import connect
from views.giveaways import GiveawayView
from utils.helpers import parse_duration

class Giveaways(commands.Cog):
    def __init__(self,bot):
        self.bot=bot; self.finish_loop.start()
    def cog_unload(self): self.finish_loop.cancel()

    @app_commands.command(name="giveaway_start")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def start(self,i,duration:str,winners:app_commands.Range[int,1,20],prize:str):
        try: seconds=parse_duration(duration)
        except ValueError as e: return await i.response.send_message(str(e),ephemeral=True)
        ends=datetime.now(timezone.utc)+timedelta(seconds=seconds)
        e=discord.Embed(title="🎉 GIVEAWAY",description=f"**{prize}**\nWinners: **{winners}**\nEnds: <t:{int(ends.timestamp())}:R>")
        await i.response.defer()
        msg=await i.channel.send(embed=e,view=GiveawayView())
        async with connect() as db:
            await db.execute("INSERT INTO giveaways VALUES(?,?,?,?,?,?,?,0)",(msg.id,i.guild.id,i.channel.id,prize,winners,ends.isoformat(),i.user.id)); await db.commit()
        await i.followup.send(f"Giveaway started: {msg.jump_url}",ephemeral=True)

    async def enter(self,i):
        async with connect() as db:
            await db.execute("INSERT OR IGNORE INTO giveaway_entries VALUES(?,?)",(i.message.id,i.user.id)); await db.commit()
        await i.response.send_message("🎉 You entered!",ephemeral=True)

    @tasks.loop(seconds=10)
    async def finish_loop(self):
        await self.bot.wait_until_ready()
        now=datetime.now(timezone.utc).isoformat()
        async with connect() as db:
            cur=await db.execute("SELECT message_id,guild_id,channel_id,prize,winners FROM giveaways WHERE ended=0 AND ends_at<=?",(now,))
            rows=await cur.fetchall()
        for message_id,gid,cid,prize,winners in rows:
            async with connect() as db:
                cur=await db.execute("SELECT user_id FROM giveaway_entries WHERE message_id=?",(message_id,))
                entries=[r[0] for r in await cur.fetchall()]
                await db.execute("UPDATE giveaways SET ended=1 WHERE message_id=?",(message_id,)); await db.commit()
            guild=self.bot.get_guild(gid); channel=guild.get_channel(cid) if guild else None
            if channel:
                picked=random.sample(entries,min(winners,len(entries))) if entries else []
                mentions=", ".join(f"<@{x}>" for x in picked) or "No valid entries."
                await channel.send(f"🎉 **{prize}** winner(s): {mentions}")

async def setup(bot): await bot.add_cog(Giveaways(bot))
