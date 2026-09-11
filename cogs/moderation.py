import discord
from discord.ext import commands
from discord import app_commands
from database.database import connect
from utils.embeds import success, error

class Moderation(commands.Cog):
    def __init__(self, bot): self.bot=bot

    async def add_warning(self, guild_id, user_id, moderator_id, reason):
        from datetime import datetime, timezone
        async with connect() as db:
            cur=await db.execute("INSERT INTO warnings(guild_id,user_id,moderator_id,reason,created_at) VALUES(?,?,?,?,?)",
                (guild_id,user_id,moderator_id,reason,datetime.now(timezone.utc).isoformat()))
            await db.commit()
            return cur.lastrowid

    @app_commands.command(name="warn")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, i, member: discord.Member, reason: str="No reason provided"):
        if member == i.user or member.bot: return await i.response.send_message(embed=error("Warn","You cannot warn yourself or a bot."), ephemeral=True)
        case=await self.add_warning(i.guild.id,member.id,i.user.id,reason)
        try: await member.send(f"You were warned in **{i.guild.name}**. Case #{case}. Reason: {reason}")
        except discord.HTTPException: pass
        await i.response.send_message(embed=success("Warning added",f"{member.mention} was warned. **Case #{case}**"))

    @app_commands.command(name="warnings")
    async def warnings(self,i,member:discord.Member):
        async with connect() as db:
            cur=await db.execute("SELECT id,reason,created_at FROM warnings WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 20",(i.guild.id,member.id))
            rows=await cur.fetchall()
        desc="\n".join(f"**#{r[0]}** — {r[1]} — <t:{int(__import__('datetime').datetime.fromisoformat(r[2]).timestamp())}:R>" for r in rows) or "No warnings."
        await i.response.send_message(embed=discord.Embed(title=f"Warnings — {member}",description=desc))

    @app_commands.command(name="clearwarnings")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clearwarnings(self,i,member:discord.Member):
        async with connect() as db:
            await db.execute("DELETE FROM warnings WHERE guild_id=? AND user_id=?",(i.guild.id,member.id)); await db.commit()
        await i.response.send_message(embed=success("Warnings cleared",f"Cleared warnings for {member.mention}."))

    @app_commands.command(name="timeout")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self,i,member:discord.Member,duration_minutes:int,reason:str="No reason provided"):
        if member.top_role >= i.user.top_role and i.user != i.guild.owner: return await i.response.send_message(embed=error("Timeout","Role hierarchy prevents this."),ephemeral=True)
        await member.timeout(discord.utils.utcnow()+__import__('datetime').timedelta(minutes=duration_minutes),reason=reason)
        await i.response.send_message(embed=success("Timed out",f"{member.mention} for {duration_minutes} minutes."))

    @app_commands.command(name="untimeout")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self,i,member:discord.Member):
        await member.timeout(None,reason="Timeout removed")
        await i.response.send_message(embed=success("Timeout removed",member.mention))

    @app_commands.command(name="kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self,i,member:discord.Member,reason:str="No reason provided"):
        await member.kick(reason=reason); await i.response.send_message(embed=success("Kicked",f"{member} was kicked."))

    @app_commands.command(name="ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self,i,member:discord.Member,reason:str="No reason provided"):
        await member.ban(reason=reason); await i.response.send_message(embed=success("Banned",f"{member} was banned."))

    @app_commands.command(name="purge")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self,i,amount:app_commands.Range[int,1,100]):
        await i.response.defer(ephemeral=True); deleted=await i.channel.purge(limit=amount)
        await i.followup.send(f"Deleted {len(deleted)} messages.",ephemeral=True)

    @app_commands.command(name="slowmode")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self,i,seconds:app_commands.Range[int,0,21600]):
        await i.channel.edit(slowmode_delay=seconds); await i.response.send_message(embed=success("Slowmode",f"Set to {seconds}s."))

    @app_commands.command(name="lock")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self,i):
        await i.channel.set_permissions(i.guild.default_role,send_messages=False)
        await i.response.send_message(embed=success("Locked","Channel locked."))

    @app_commands.command(name="unlock")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self,i):
        await i.channel.set_permissions(i.guild.default_role,send_messages=None)
        await i.response.send_message(embed=success("Unlocked","Channel unlocked."))

async def setup(bot): await bot.add_cog(Moderation(bot))
