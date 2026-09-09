import os
import sys
import asyncio
import threading
import discord
from discord.ext import commands
from flask import Flask
from config import TOKEN
from database.database import init_db
from views.tickets import TicketControlView, TicketSelectView
from views.giveaways import GiveawayView

app = Flask(__name__)

@app.route("/")
def home():
    return "GTA RP Gang Fund Bot is online!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        await init_db()
        self.add_view(TicketSelectView())
        self.add_view(TicketControlView())

        cogs = [
            "cogs.moderation",
            "cogs.music",
            "cogs.tickets",
            "cogs.embeds",
            "cogs.giveaways",
            "cogs.roles",
            "cogs.welcome",
            "cogs.logging",
            "cogs.automod",
            "cogs.utility"
        ]
        for cog in cogs:
            await self.load_extension(cog)
        
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Game(name="/help | Serving Guilds"))

bot = Bot()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ An unexpected error occurred.", ephemeral=True)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    print("Starting GTA RP Gang Fund Bot...")
    bot.run(TOKEN)
