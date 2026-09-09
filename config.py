import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DB_PATH = os.path.join("data", "bot.db")
DEFAULT_COLOR = 0x3498DB
SUCCESS_COLOR = 0x2ECC71
ERROR_COLOR = 0xE74C3C
WARNING_COLOR = 0xF1C40F
