import discord
from discord.ext import commands
from discord import app_commands
from database.database import get_config, set_config

class Logging(commands.Cog):
    def __init__(self,bot): self.bot=bot
    async def send_log(self,guild,embed):
        cfg=await get_config(guild.id)
        if cfg["log_channel"]:
            ch=guild.get_channel(cfg["log_channel"])
            if ch:
                try: await ch.send(embed=embed)
                except discord.HTTPException: pass
    @app_commands.command(name="logs_setup")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup(self,i,channel:discord.TextChannel):
        await set_config(i.guild.id,"log_channel",channel.id); await i.response.send_message(f"Logs set to {channel.mention}.")
    @commands.Cog.listener()
    async def on_message_delete(self,message):
        if message.guild and not message.author.bot:
            await self.send_log(message.guild,discord.Embed(title="🗑️ Message Deleted",description=f"**{message.author}** in {message.channel.mention}\n{message.content[:1500]}"))
    @commands.Cog.listener()
    async def on_member_remove(self,member):
        await self.send_log(member.guild,discord.Embed(title="👋 Member Left",description=str(member)))
    @commands.Cog.listener()
    async def on_member_join(self,member):
        await self.send_log(member.guild,discord.Embed(title="📥 Member Joined",description=str(member)))

async def setup(bot): await bot.add_cog(Logging(bot))
