import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self,bot): self.bot=bot
    @app_commands.command(name="help")
    async def help(self,i):
        e=discord.Embed(title="🤖 Bot Help",description="A multipurpose community bot.")
        e.add_field(name="🎵 Music",value="`/play` `/search` `/queue` `/skip` `/pause` `/resume` `/shuffle` `/loop` `/stop`",inline=False)
        e.add_field(name="🛡️ Moderation",value="`/warn` `/warnings` `/clearwarnings` `/timeout` `/untimeout` `/kick` `/ban` `/purge` `/slowmode` `/lock` `/unlock`",inline=False)
        e.add_field(name="🎫 Tickets",value="`/ticket_setup` `/ticket_close` `/ticket_claim` `/ticket_add` `/ticket_remove` `/ticket_rename`",inline=False)
        e.add_field(name="🎉 Giveaways",value="`/giveaway_start`",inline=False)
        e.add_field(name="⚙️ Utility",value="`/ping` `/botinfo` `/serverinfo` `/userinfo` `/avatar` `/8ball` `/coinflip` `/choose` `/remind`",inline=False)
        await i.response.send_message(embed=e)
async def setup(bot): await bot.add_cog(Help(bot))
