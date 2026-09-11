# Chidori — Multipurpose Discord Bot

This project includes moderation, tickets, giveaways, roles, welcome/logging, automod, utility tools, embed tools and an upgraded music player.

## Environment

Set these environment variables on Render:

- `DISCORD_TOKEN` — your Discord bot token
- `BOT_OWNER_ID` — bot owner user ID
- `PREFIX` — optional prefix, defaults to `!`

## Render

Use Docker deployment for the included music system because the Dockerfile installs FFmpeg.

Build/deploy is handled by the included `Dockerfile`.

The bot starts with:

```text
python bot.py
```

## Music

The music player uses:

- `discord.py`
- `yt-dlp`
- FFmpeg
- `PyNaCl`

It supports YouTube searches/URLs, playlist expansion, queues, history, pause/resume, skip/previous, volume, shuffle, queue management, loop modes, persistent controls, auto-disconnect and per-guild players.

## Slash command descriptions

All music slash commands and their important parameters have Discord-visible descriptions.
