import re, time
import discord
from discord.ext import commands
from discord import app_commands
from database.database import connect

class Automod(commands.Cog):
    def __init__(self,bot):
        self.bot=bot; self.recent={}; self.bad_words={}

    @commands.Cog.listener()
    async def on_message(self,message):
        if not message.guild or message.author.bot: return
        async with await connect() as db:
            cur=await db.execute("SELECT * FROM automod_config WHERE guild_id=?",(message.guild.id,))
            cfg=await cur.fetchone()
        if not cfg: return
        links=bool(cfg[1]); invites=bool(cfg[2]); spam=bool(cfg[3]); caps=bool(cfg[4]); duplicate=bool(cfg[5]); bad=(cfg[6] or "").lower().split(",")
        content=message.content
        violation=None
        if invites and re.search(r"(discord\.gg/|discord\.com/invite/)",content,re.I): violation="Discord invite"
        elif links and re.search(r"https?://",content,re.I): violation="Link"
        elif caps and len(content)>=12 and sum(c.isupper() for c in content if c.isalpha())/max(1,sum(c.isalpha() for c in content))>.75: violation="Excessive caps"
        elif any(w.strip() and w.strip() in content.lower() for w in bad): violation="Blocked word"
        if violation:
            try: await message.delete()
            except discord.HTTPException: pass
            try: await message.channel.send(f"⚠️ {message.author.mention}: {violation} blocked.",delete_after=4)
        if spam:
            now=time.monotonic(); key=(message.guild.id,message.author.id)
            arr=[x for x in self.recent.get(key,[]) if now-x<6]; arr.append(now); self.recent[key]=arr
            if len(arr)>=6:
                try: await message.author.timeout(discord.utils.utcnow()+__import__('datetime').timedelta(minutes=1),reason="Automod spam")
                except discord.HTTPException: pass

    @app_commands.command(name="automod_config")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config(self,i,links:bool=False,invites:bool=False,spam:bool=True,caps:bool=False,duplicate:bool=False,bad_words:str=""):
        async with await connect() as db:
            await db.execute("INSERT OR REPLACE INTO automod_config VALUES(?,?,?,?,?,?,?)",(i.guild.id,int(links),int(invites),int(spam),int(caps),int(duplicate),bad_words)); await db.commit()
        await i.response.send_message("Automod configuration saved.")
    @app_commands.command(name="automod_disable")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def disable(self,i):
        async with await connect() as db:
            await db.execute("DELETE FROM automod_config WHERE guild_id=?",(i.guild.id,)); await db.commit()
        await i.response.send_message("Automod disabled.")

async def setup(bot): await bot.add_cog(Automod(bot))
