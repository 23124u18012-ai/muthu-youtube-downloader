import os, re, shutil, tempfile, logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("muthu")

TOKEN = os.environ["BOT_TOKEN"]
BASE_URL = os.environ["RENDER_EXTERNAL_URL"].rstrip("/")
PORT = int(os.environ.get("PORT", "10000"))
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
MAX_SECONDS = int(os.environ.get("MAX_VIDEO_SECONDS", "900"))
MAX_MB = int(os.environ.get("MAX_FILE_MB", "45"))
COOKIE_FILE = "/etc/secrets/cookies.txt"

def is_youtube_url(value):
    return bool(re.match(r"^https?://(www\\.)?(youtube\\.com|youtu\\.be)/", value, re.I))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Muthu Video & Audio Bot!\\n\\n"
        "Send a YouTube video URL, then choose MP4 or MP3.\\n"
        f"Limits: {MAX_SECONDS // 60} minutes / {MAX_MB} MB.\\n"
        "Only download content you own or are authorized to download."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a YouTube video URL. Then choose MP4 Video or MP3 Audio.")

async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (update.message.text or "").strip()
    if not is_youtube_url(url):
        await update.message.reply_text("Please send a valid YouTube URL.")
        return
    context.user_data["url"] = url
    keyboard = [[InlineKeyboardButton("🎬 MP4 Video", callback_data="mp4"),
                 InlineKeyboardButton("🎵 MP3 Audio", callback_data="mp3")]]
    await update.message.reply_text("Choose format:", reply_markup=InlineKeyboardMarkup(keyboard))

async def download_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get("url")
    if not url:
        await query.edit_message_text("Send the video URL again.")
        return
    await query.edit_message_text("⏳ Download started. Please wait...")
    chat_id = query.message.chat_id
    folder = tempfile.mkdtemp(prefix="muthu_")
    try:
        await context.bot.send_chat_action(chat_id, ChatAction.UPLOAD_VIDEO if query.data == "mp4" else ChatAction.UPLOAD_DOCUMENT)
        opts = {
            "outtmpl": str(Path(folder) / "%(title).70s.%(ext)s"),
            "noplaylist": True, "quiet": True, "no_warnings": True,
            "socket_timeout": 20, "retries": 2, "fragment_retries": 2,
            "max_filesize": MAX_MB * 1024 * 1024,
            "match_filter": lambda info, *, incomplete: (
                f"Video exceeds {MAX_SECONDS // 60} minute limit"
                if info.get("duration") and info["duration"] > MAX_SECONDS else None
            ),
        }
        if os.path.isfile(COOKIE_FILE):
            opts["cookiefile"] = COOKIE_FILE
        if query.data == "mp3":
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}],
            })
        else:
            opts.update({"format": "best[ext=mp4][height<=720]/best[height<=720]/best", "merge_output_format": "mp4"})
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            output = Path(ydl.prepare_filename(info))
        if query.data == "mp3":
            output = output.with_suffix(".mp3")
        if not output.exists():
            candidates = [p for p in Path(folder).glob("*") if p.is_file()]
            if not candidates:
                raise RuntimeError("No output file was created.")
            output = max(candidates, key=lambda p: p.stat().st_size)
        if output.stat().st_size > MAX_MB * 1024 * 1024:
            raise RuntimeError(f"File exceeds the {MAX_MB} MB Telegram upload limit.")
        caption = (info.get("title") or "Your download")[:900]
        with output.open("rb") as stream:
            if query.data == "mp3":
                await context.bot.send_audio(chat_id, audio=stream, caption=caption, read_timeout=180, write_timeout=180)
            else:
                await context.bot.send_video(chat_id, video=stream, caption=caption, supports_streaming=True, read_timeout=180, write_timeout=180)
    except Exception as exc:
        log.exception("Download failed")
        message = str(exc)
        if "Sign in to confirm" in message:
            message = "YouTube requires sign-in for this video. Check your private cookies file, or try another permitted video."
        await context.bot.send_message(chat_id, f"❌ Download failed: {message[:600]}")
    finally:
        shutil.rmtree(folder, ignore_errors=True)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(download_choice, pattern="^(mp4|mp3)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_url))
    path = WEBHOOK_SECRET
    app.run_webhook(
        listen="0.0.0.0", port=PORT, url_path=path,
        webhook_url=f"{BASE_URL}/{path}", secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True, allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    main()
