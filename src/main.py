import os
import re
import json
import asyncio
import logging
import threading
import nest_asyncio
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import MessageEntityType
import yt_dlp  # Best for Instagram, Facebook, YouTube

# ✅ Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ Logging setup (UTF-8 Support for Windows)
LOG_FILE = "bot_activity.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ✅ Flask Server Setup (No Development Warning)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running in production mode!"  # Message changed

# ✅ JSON File for User Data
USERS_FILE = "users.json"

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file)

users = load_users()

# ✅ Download video in best available quality
def download_video(url):
    output_path = "downloads"
    os.makedirs(output_path, exist_ok=True)

    ydl_opts = {
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",  # File name format
        "format": "bestvideo+bestaudio/best",  # Best quality available
        "merge_output_format": "mp4",
        "quiet": False,  # Show logs
        "noplaylist": True,  # Disable playlist downloads
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"Video download error: {e}")
        return None

# ✅ Check for spoiler messages
def spoiler_in_message(entities):
    return any(entity.type == MessageEntityType.SPOILER for entity in entities) if entities else False

# ✅ Valid link check function
def is_valid_link(text):
    pattern = r"(https?:\/\/)?(www\.)?(instagram\.com|facebook\.com|youtube\.com|youtu\.be)\/[\w\-\/\?&=]+"
    return bool(re.search(pattern, text))

# ✅ Handle messages from Telegram bot
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    logger.info(f"New Request: [User ID: {user_id}] [Chat ID: {chat_id}] [Message: {message_text}]")

    # ✅ Send welcome message to new users
    if str(user_id) not in users:
        users[str(user_id)] = True
        save_users(users)  
        await update.message.reply_text(
            "👋 Welcome! Send a video link from Instagram, Facebook, or YouTube Shorts, and I'll download it in best quality!",
            parse_mode="Markdown"
        )

    # ✅ Check for valid link
    if not is_valid_link(message_text):
        logger.warning(f"Invalid Link: {message_text} from User {user_id}")
        await update.message.reply_text("⚠️ Invalid link! Please send a correct link.", parse_mode="Markdown")
        return

    processing_msg = await update.message.reply_text("🚀 Fetching the best quality video...")

    # ✅ Download the video
    try:
        logger.info(f"Downloading video: {message_text} for User {user_id}")
        video_path = download_video(message_text)
        if not video_path or not os.path.exists(video_path):
            raise ValueError("Video download failed or file doesn't exist.")
    except Exception as e:
        logger.error(f"Download Error for {user_id}: {e}")
        await update.message.reply_text(f"❌ Error occurred while downloading the video: {e}")
        return

    visibility_flag = spoiler_in_message(update.message.entities)

    # ✅ Send the video
    try:
        with open(video_path, 'rb') as video_file:
            await update.message.chat.send_video(
                video=video_file,
                has_spoiler=visibility_flag,
                disable_notification=True,
                write_timeout=8000,
                read_timeout=8000
            )
        logger.info(f"Video sent successfully to {user_id}")

    except Exception as e:
        logger.error(f"Telegram Send Error: {e}")
        await update.message.reply_text("❌ Error occurred while sending the video.")
    finally:
        try:
            await processing_msg.delete()
        except Exception as e:
            logger.warning(f"Failed to delete processing message: {e}")

# ✅ Start bot function (Runs in separate thread)
def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🚀 Bot started and listening for messages.")
    await application.run_polling()

# ✅ Run Flask and Bot Together
if __name__ == "__main__":
    nest_asyncio.apply()
    
    # Flask ko alag thread me run karenge
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False),
        daemon=True
    ).start()

    # Telegram bot start karna
    start_bot()
