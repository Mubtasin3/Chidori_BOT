import discord
from discord.ext import commands
from database.database import get_config, set_config

class Welcome(commands.Cog):
    def __init__(self,bot): self.bot=bot
    @commands.Cog.listener()
    async def on_member_join(self,member):
        cfg=await get_config(member.guild.id)
        if cfg["welcome_enabled"] and cfg["welcome_channel"]:
            ch=member.guild.get_channel(cfg["welcome_channel"])
            if ch:
                await ch.send(f"👋 Welcome {member.mention} to **{member.guild.name}**! You are member #{member.guild.member_count}.")
        if cfg["autorole"]:
            role=member.guild.get_role(cfg["autorole"])
            if role:
                try: await member.add_roles(role)
                except discord.HTTPException: pass
    @discord.app_commands.command(name="welcome_setup")
    @discord.app_commands.checks.has_permissions(manage_guild=True)
    async def setup(self,i,channel:discord.TextChannel):
        await set_config(i.guild.id,"welcome_channel",channel.id); await set_config(i.guild.id,"welcome_enabled",1)
        await i.response.send_message(f"Welcome channel set to {channel.mention}.")
    @discord.app_commands.command(name="welcome_disable")
    @discord.app_commands.checks.has_permissions(manage_guild=True)
    async def disable(self,i):
        await set_config(i.guild.id,"welcome_enabled",0); await i.response.send_message("Welcome disabled.")
    @discord.app_commands.command(name="autorole_set")
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def autorole(self,i,role:discord.Role):
        await set_config(i.guild.id,"autorole",role.id); await i.response.send_message(f"Autorole set to {role.mention}.")
    @discord.app_commands.command(name="autorole_disable")
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def autorole_disable(self,i):
        await set_config(i.guild.id,"autorole",None); await i.response.send_message("Autorole disabled.")

async def setup(bot): await bot.add_cog(Welcome(bot))
