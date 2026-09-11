# Chidori Bot Commands

## 🎵 Music

| Command | Description |
|---|---|
| `/play` | Play a song, YouTube URL, or playlist and add it to the queue. |
| `/search` | Search YouTube and show the top results. |
| `/queue` | Show the current song and queued tracks. |
| `/nowplaying` | Show detailed information about the current song. |
| `/join` | Join your current voice channel. |
| `/skip` | Skip the current song. |
| `/previous` | Return to the previous track. |
| `/pause` | Pause playback. |
| `/resume` | Resume playback. |
| `/volume` | Set volume from 5% to 100%. |
| `/shuffle` | Shuffle the queue. |
| `/remove` | Remove a queued track by position. |
| `/clear` | Clear waiting tracks without stopping the current song. |
| `/loop` | Choose Off, Current song, or Queue loop mode. |
| `/stop` | Stop, clear the queue, and disconnect. |
| `/disconnect` | Disconnect from voice. |

### Render music requirement

The included `Dockerfile` installs FFmpeg automatically. For music on Render, deploy this project as a **Docker** service so FFmpeg is available.

The Python web service mode does not install FFmpeg automatically.
