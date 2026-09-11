import discord
from discord.ext import commands
from discord import app_commands
from database.database import connect

class RolePanel(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="rolepanel_create")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def create(self,i,role:discord.Role,label:str=None):
        label=label or role.name
        view=discord.ui.View(timeout=None)
        button=discord.ui.Button(label=label,style=discord.ButtonStyle.primary,custom_id=f"role:{role.id}")
        async def callback(interaction):
            if role >= interaction.guild.me.top_role: return await interaction.response.send_message("I cannot manage that role.",ephemeral=True)
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role); text=f"Removed **{role.name}**."
            else:
                await interaction.user.add_roles(role); text=f"Added **{role.name}**."
            await interaction.response.send_message(text,ephemeral=True)
        button.callback=callback; view.add_item(button)
        msg=await i.channel.send(embed=discord.Embed(title="🎭 Role Panel",description="Click below to toggle your role."),view=view)
        async with connect() as db:
            await db.execute("INSERT OR REPLACE INTO rolepanels VALUES(?,?,?,?)",(msg.id,i.guild.id,i.channel.id,label)); await db.commit()
        await i.response.send_message("Role panel created.",ephemeral=True)

    @app_commands.command(name="rolepanel_list")
    async def list(self,i):
        async with connect() as db:
            cur=await db.execute("SELECT message_id,title FROM rolepanels WHERE guild_id=?",(i.guild.id,)); rows=await cur.fetchall()
        await i.response.send_message("\n".join(f"{r[1]} — `{r[0]}`" for r in rows) or "No panels.",ephemeral=True)

async def setup(bot): await bot.add_cog(RolePanel(bot))
