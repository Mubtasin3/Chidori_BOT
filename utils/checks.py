import discord
from discord import app_commands
from config import OWNER_ID

def owner_only():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == OWNER_ID
    return app_commands.check(predicate)

def has_any_role(*role_names):
    async def predicate(interaction: discord.Interaction):
        return any(r.name in role_names for r in getattr(interaction.user, "roles", []))
    return app_commands.check(predicate)
