import discord

def success(title, description):
    return discord.Embed(title=f"✅ {title}", description=description, color=0x57F287)

def error(title, description):
    return discord.Embed(title=f"❌ {title}", description=description, color=0xED4245)

def info(title, description):
    return discord.Embed(title=f"ℹ️ {title}", description=description, color=0x5865F2)
