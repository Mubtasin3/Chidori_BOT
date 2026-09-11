import discord, json
from discord.ext import commands
from discord import app_commands
from database.database import connect

class EmbedBuilder(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @app_commands.command(name="embed")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def embed(self,i,title:str,description:str,color:str="5865F2",channel:discord.TextChannel=None):
        try: c=int(color.replace("#",""),16)
        except ValueError: c=0x5865F2
        e=discord.Embed(title=title,description=description,color=c)
        await (channel or i.channel).send(embed=e)
        await i.response.send_message("Embed sent.",ephemeral=True)

    @app_commands.command(name="embed_template_save")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def save(self,i,name:str,title:str,description:str,color:str="5865F2"):
        try: c=int(color.replace("#",""),16)
        except: c=0x5865F2
        payload=json.dumps({"title":title,"description":description,"color":c})
        async with connect() as db:
            await db.execute("INSERT OR REPLACE INTO embeds(guild_id,name,payload) VALUES(?,?,?)",(i.guild.id,name,payload)); await db.commit()
        await i.response.send_message(f"Saved template **{name}**.",ephemeral=True)

    @app_commands.command(name="embed_template")
    async def template(self,i,name:str,channel:discord.TextChannel=None):
        async with connect() as db:
            cur=await db.execute("SELECT payload FROM embeds WHERE guild_id=? AND name=?",(i.guild.id,name)); row=await cur.fetchone()
        if not row: return await i.response.send_message("Template not found.",ephemeral=True)
        d=json.loads(row[0]); e=discord.Embed(**d); await (channel or i.channel).send(embed=e); await i.response.send_message("Sent.",ephemeral=True)

async def setup(bot): await bot.add_cog(EmbedBuilder(bot))
