import os, threading, logging, asyncio
import discord
from discord.ext import commands, tasks
from flask import Flask
from config import TOKEN, PREFIX
from database.database import init_db
from views.tickets import TicketPanel
from views.giveaways import GiveawayView
from views.music import MusicControls

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log=logging.getLogger("GangFund")

app=Flask(__name__)

@app.route("/")
def home():
    return "GTA RP Gang Fund Bot is online!"

@app.route("/health")
def health():
    return {"status":"online","bot":str(bot.user) if bot.user else "starting"}

def run_web_server():
    port=int(os.environ.get("PORT","10000"))
    app.run(host="0.0.0.0",port=port,threaded=True)

class Bot(commands.Bot):
    def __init__(self):
        intents=discord.Intents.default()
        intents.members=True
        intents.message_content=True
        super().__init__(command_prefix=PREFIX,intents=intents,help_command=None)

    async def setup_hook(self):
        await init_db()
        for ext in [
            "cogs.moderation","cogs.music","cogs.tickets","cogs.embeds",
            "cogs.giveaways","cogs.roles","cogs.welcome","cogs.logging",
            "cogs.utility","cogs.automod","cogs.setup","cogs.help"
        ]:
            try:
                await self.load_extension(ext)
                log.info("Loaded %s",ext)
            except Exception:
                log.exception("Failed to load %s",ext)
        self.add_view(TicketPanel())
        self.add_view(GiveawayView())
        self.add_view(MusicControls())
        try:
            synced=await self.tree.sync()
            log.info("Synced %d slash commands",len(synced))
        except Exception:
            log.exception("Slash command sync failed")

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name="/help | Community Bot"))
        log.info("Logged in as %s (%s)",self.user,self.user.id)

    async def on_command_error(self,ctx,error):
        log.error("Command error: %s",error)

bot=Bot()

if __name__=="__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN is missing. Put it in .env or Render environment variables.")
    web_thread=threading.Thread(target=run_web_server,daemon=True)
    web_thread.start()
    print("Starting GTA RP Gang Fund Bot...")
    bot.run(TOKEN)
