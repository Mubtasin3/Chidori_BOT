import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "")
OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0") or 0)
PREFIX = os.getenv("PREFIX", "!")
PORT = int(os.getenv("PORT", "10000"))
