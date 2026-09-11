import discord, random, asyncio
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone, timedelta
from database.database import connect
from utils.helpers import parse_duration

class Utility(commands.Cog):
    def __init__(self,bot): self.bot=bot; self.started=datetime.now(timezone.utc); self.reminder_loop.start()
    def cog_unload(self): self.reminder_loop.cancel()

    @app_commands.command(name="ping")
    async def ping(self,i): await i.response.send_message(f"🏓 Pong! `{round(self.bot.latency*1000)}ms`")
    @app_commands.command(name="botinfo")
    async def botinfo(self,i):
        await i.response.send_message(embed=discord.Embed(title="🤖 Bot Info",description=f"Guilds: **{len(self.bot.guilds)}**\nUptime: <t:{int(self.started.timestamp())}:R>"))
    @app_commands.command(name="serverinfo")
    async def serverinfo(self,i):
        g=i.guild; await i.response.send_message(embed=discord.Embed(title="🛡️ Server Info",description=f"**{g.name}**\nMembers: {g.member_count}\nChannels: {len(g.channels)}\nRoles: {len(g.roles)}"))
    @app_commands.command(name="userinfo")
    async def userinfo(self,i,member:discord.Member=None):
        member=member or i.user; await i.response.send_message(embed=discord.Embed(title=f"👤 {member}",description=f"ID: `{member.id}`\nJoined: <t:{int(member.joined_at.timestamp())}:R>"))
    @app_commands.command(name="avatar")
    async def avatar(self,i,member:discord.Member=None):
        member=member or i.user; await i.response.send_message(member.display_avatar.url)
    @app_commands.command(name="8ball")
    async def eightball(self,i,question:str): await i.response.send_message(random.choice(["Yes.","No.","Maybe.","Definitely.","Ask again later.","Absolutely not."]))
    @app_commands.command(name="coinflip")
    async def coinflip(self,i): await i.response.send_message(random.choice(["🪙 Heads!","🪙 Tails!"]))
    @app_commands.command(name="choose")
    async def choose(self,i,options:str):
        vals=[x.strip() for x in options.split(",") if x.strip()]
        if len(vals)<2: return await i.response.send_message("Give at least 2 choices separated by commas.",ephemeral=True)
        await i.response.send_message(f"🎯 I choose **{random.choice(vals)}**")
    @app_commands.command(name="remind")
    async def remind(self,i,duration:str,message:str):
        try: seconds=parse_duration(duration)
        except ValueError as e: return await i.response.send_message(str(e),ephemeral=True)
        due=datetime.now(timezone.utc)+timedelta(seconds=seconds)
        async with await connect() as db:
            await db.execute("INSERT INTO reminders(user_id,channel_id,message,due_at) VALUES(?,?,?,?)",(i.user.id,i.channel.id,message,due.isoformat())); await db.commit()
        await i.response.send_message(f"⏰ Reminder set for <t:{int(due.timestamp())}:R>.")
    @tasks.loop(seconds=15)
    async def reminder_loop(self):
        await self.bot.wait_until_ready(); now=datetime.now(timezone.utc).isoformat()
        async with await connect() as db:
            cur=await db.execute("SELECT id,user_id,channel_id,message FROM reminders WHERE sent=0 AND due_at<=?",(now,)); rows=await cur.fetchall()
            for rid,uid,cid,msg in rows: await db.execute("UPDATE reminders SET sent=1 WHERE id=?",(rid,))
            await db.commit()
        for rid,uid,cid,msg in rows:
            ch=self.bot.get_channel(cid)
            if ch:
                try: await ch.send(f"⏰ <@{uid}> **Reminder:** {msg}")
                except discord.HTTPException: pass

async def setup(bot): await bot.add_cog(Utility(bot))
