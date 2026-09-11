import discord
from discord.ext import commands
from discord import app_commands
from database.database import set_config

class Setup(commands.Cog):
    def __init__(self,bot): self.bot=bot
    @app_commands.command(name="setup")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup(self,i,log_channel:discord.TextChannel=None,welcome_channel:discord.TextChannel=None,support_role:discord.Role=None,ticket_category:discord.CategoryChannel=None,suggestion_channel:discord.TextChannel=None):
        if log_channel: await set_config(i.guild.id,"log_channel",log_channel.id)
        if welcome_channel: await set_config(i.guild.id,"welcome_channel",welcome_channel.id); await set_config(i.guild.id,"welcome_enabled",1)
        if support_role: await set_config(i.guild.id,"support_role",support_role.id)
        if ticket_category: await set_config(i.guild.id,"ticket_category",ticket_category.id)
        if suggestion_channel: await set_config(i.guild.id,"suggestion_channel",suggestion_channel.id)
        await i.response.send_message("✅ Server setup saved.")
async def setup(bot): await bot.add_cog(Setup(bot))
