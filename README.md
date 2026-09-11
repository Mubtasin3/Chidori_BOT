# Gang Fund — Advanced Discord Community Bot

Python 3.12+ / discord.py 2.x / SQLite / Flask / yt-dlp / FFmpeg.

## Features
- Working YouTube/yt-dlp music with queue and persistent controls
- Moderation and warnings
- Tickets with category selector
- Giveaways with persistent entry button
- Role panels
- Welcome and autorole
- Logging
- Basic automod
- Embed templates
- Utility commands and persistent reminders
- SQLite storage
- Render Flask web server

## Windows
Install Python 3.12+ and FFmpeg, then:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

## Render
Build command:
`pip install -r requirements.txt`

Start command:
`python bot.py`

Set `DISCORD_TOKEN` in Render Environment Variables.

For music on Render, Docker deployment is recommended because the included Dockerfile installs FFmpeg.

## Discord Developer Portal
Enable **Server Members Intent** and **Message Content Intent** under Bot > Privileged Gateway Intents.

Never put your bot token directly in source code.
