# Muthu YouTube Downloader — GitHub + Render Free

## Included
- Telegram webhook bot
- MP4 and MP3 options
- yt-dlp + FFmpeg
- Optional Render Secret File at `/etc/secrets/cookies.txt`
- Default limits: 15 minutes and 45 MB

## Deploy
1. Create a new GitHub repository.
2. Upload `bot.py`, `requirements.txt`, and `render.yaml`.
3. In Render, choose **New + → Blueprint**, connect the repository, and deploy.
4. In Render → service → Environment, add `BOT_TOKEN` with your BotFather token.
5. Render generates `WEBHOOK_SECRET` from `render.yaml`. Keep it private.
6. Wait for the service to become Live, then send `/start` to your Telegram bot.

If you create a Web Service manually, use:
- Build: `apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt`
- Start: `python bot.py`
- Instance: Free

## Optional cookies
Only for content you are authorized to access:
1. Render → service → Environment → Secret Files.
2. Add file named `cookies.txt` with the complete Netscape-format contents.
3. The bot reads `/etc/secrets/cookies.txt` automatically.
4. Never commit cookies to GitHub or send them to anyone. Cookies are account session credentials; revoke the session if exposed.

## Free-tier limitations
Render Free services may sleep when idle, have limited CPU/RAM/disk, and may not handle long or large downloads reliably. The bot limits files to 45 MB and videos to 15 minutes by default. YouTube may still block requests from cloud IPs even when cookies are configured. This project does not bypass DRM, paid access, or other access controls. Use only for content you own or have permission to download and follow applicable platform terms and law.
