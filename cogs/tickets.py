import discord
from discord.ext import commands
from discord import app_commands
from database.database import get_config, connect, set_config
from views.tickets import TicketPanel
from utils.embeds import success, error

class Tickets(commands.Cog):
    def __init__(self,bot): self.bot=bot

    async def create_ticket(self, interaction, category):
        cfg=await get_config(interaction.guild.id)
        support=interaction.guild.get_role(cfg["support_role"]) if cfg["support_role"] else None
        overwrites={interaction.guild.default_role:discord.PermissionOverwrite(view_channel=False),
                    interaction.user:discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)}
        if support: overwrites[support]=discord.PermissionOverwrite(view_channel=True,send_messages=True,read_message_history=True)
        cat=interaction.guild.get_channel(cfg["ticket_category"]) if cfg["ticket_category"] else None
        ch=await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}",category=cat,overwrites=overwrites,topic=f"Ticket category: {category}")
        async with connect() as db:
            await db.execute("INSERT INTO tickets VALUES(?,?,?,?,?,datetime('now'))",(ch.id,interaction.guild.id,interaction.user.id,None,category)); await db.commit()
        await ch.send(embed=discord.Embed(title="🎫 Support Ticket",description=f"Category: **{category}**\nPlease explain your issue."))
        await interaction.response.send_message(f"Created {ch.mention}",ephemeral=True)

    @app_commands.command(name="ticket_setup")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket_setup(self,i,channel:discord.TextChannel=None):
        channel=channel or i.channel
        await channel.send(embed=discord.Embed(title="🎫 Open a Ticket",description="Choose a category below."),view=TicketPanel())
        await i.response.send_message("Ticket panel created.",ephemeral=True)

    @app_commands.command(name="ticket_close")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_close(self,i):
        await i.response.send_message(embed=success("Closing","This ticket will close in 3 seconds."))
        await __import__('asyncio').sleep(3); await i.channel.delete()

    @app_commands.command(name="ticket_claim")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_claim(self,i):
        async with connect() as db:
            await db.execute("UPDATE tickets SET claimed_by=? WHERE channel_id=?",(i.user.id,i.channel.id)); await db.commit()
        await i.response.send_message(embed=success("Claimed",f"{i.user.mention} claimed this ticket."))

    @app_commands.command(name="ticket_add")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_add(self,i,member:discord.Member):
        await i.channel.set_permissions(member,view_channel=True,send_messages=True,read_message_history=True)
        await i.response.send_message(f"Added {member.mention}.")
    @app_commands.command(name="ticket_remove")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_remove(self,i,member:discord.Member):
        await i.channel.set_permissions(member,view_channel=False)
        await i.response.send_message(f"Removed {member.mention}.")
    @app_commands.command(name="ticket_rename")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_rename(self,i,name:str):
        await i.channel.edit(name=name[:90]); await i.response.send_message("Renamed.")

async def setup(bot): await bot.add_cog(Tickets(bot))
