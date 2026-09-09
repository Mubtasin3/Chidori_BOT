# Multipurpose Discord Bot

A fully modular, advanced Discord Bot built with Python 3.12+, `discord.py 2.x`, SQLite (`aiosqlite`), and `yt-dlp`.

## Setup Instructions

### Local Setup (Windows / Linux)
1. **Install Python 3.12+** and **FFmpeg** (Ensure FFmpeg is added to system PATH).
2. Clone this repository.
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env` and populate your `DISCORD_TOKEN`.
6. Run the bot:
   ```bash
   python bot.py
   ```

### Deployment to Render
1. Create a Web Service on [Render](https://render.com).
2. Connect your GitHub repository.
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `python bot.py`
5. Add `DISCORD_TOKEN` in the **Environment Variables** section.
