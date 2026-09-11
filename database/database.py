import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "bot.db"

SCHEMA = '''
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id INTEGER PRIMARY KEY,
    welcome_channel INTEGER,
    log_channel INTEGER,
    mod_log_channel INTEGER,
    ticket_category INTEGER,
    support_role INTEGER,
    suggestion_channel INTEGER,
    autorole INTEGER,
    welcome_enabled INTEGER DEFAULT 0,
    automod_enabled INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER, user_id INTEGER, moderator_id INTEGER,
    reason TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS tickets (
    channel_id INTEGER PRIMARY KEY,
    guild_id INTEGER, opener_id INTEGER, claimed_by INTEGER,
    category TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS giveaways (
    message_id INTEGER PRIMARY KEY,
    guild_id INTEGER, channel_id INTEGER, prize TEXT,
    winners INTEGER, ends_at TEXT, host_id INTEGER, ended INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS giveaway_entries (
    message_id INTEGER, user_id INTEGER,
    PRIMARY KEY(message_id, user_id)
);
CREATE TABLE IF NOT EXISTS rolepanels (
    message_id INTEGER PRIMARY KEY,
    guild_id INTEGER, channel_id INTEGER, title TEXT
);
CREATE TABLE IF NOT EXISTS rolepanel_options (
    message_id INTEGER, role_id INTEGER, label TEXT,
    PRIMARY KEY(message_id, role_id)
);
CREATE TABLE IF NOT EXISTS embeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER, name TEXT, payload TEXT,
    UNIQUE(guild_id, name)
);
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, channel_id INTEGER, message TEXT, due_at TEXT, sent INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS afk (
    guild_id INTEGER, user_id INTEGER, reason TEXT, created_at TEXT,
    PRIMARY KEY(guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS automod_config (
    guild_id INTEGER PRIMARY KEY,
    links INTEGER DEFAULT 0, invites INTEGER DEFAULT 0,
    spam INTEGER DEFAULT 0, caps INTEGER DEFAULT 0,
    duplicate INTEGER DEFAULT 0, bad_words TEXT DEFAULT ''
);
'''

async def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

def connect():
    return aiosqlite.connect(DB_PATH)

async def ensure_guild(guild_id: int):
    async with connect() as db:
        await db.execute("INSERT OR IGNORE INTO guild_config(guild_id) VALUES(?)", (guild_id,))
        await db.commit()

async def get_config(guild_id: int):
    await ensure_guild(guild_id)
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM guild_config WHERE guild_id=?", (guild_id,))
        return await cur.fetchone()

async def set_config(guild_id: int, key: str, value):
    allowed = {
        "welcome_channel","log_channel","mod_log_channel","ticket_category",
        "support_role","suggestion_channel","autorole","welcome_enabled","automod_enabled"
    }
    if key not in allowed:
        raise ValueError("Invalid configuration key")
    await ensure_guild(guild_id)
    async with connect() as db:
        await db.execute(f"UPDATE guild_config SET {key}=? WHERE guild_id=?", (value, guild_id))
        await db.commit()
