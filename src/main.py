import os
import re
import random
import json
from functools import lru_cache
from dotenv import load_dotenv
import telegram
from telegram import Update
from telegram.error import TimedOut
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import MessageEntityType
from logger import print_logs
from video_utils import compress_video, download_video, cleanup_file
from permissions import is_user_or_chat_not_allowed, supported_sites

load_dotenv()

USERS_FILE = "users.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as file:
        json.dump(users, file)

users = load_users()

@lru_cache(maxsize=1)
def load_responses():
    language = os.getenv("LANGUAGE", "en").lower()
    filename = "responses_ua.json" if language == "ua" else "responses_en.json"
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data["responses"]
    except FileNotFoundError:
        return ["Sorry, I'm having trouble loading my responses!"]

responses = load_responses()

def spoiler_in_message(entities):
    if entities:
        for entity in entities:
            if entity.type == MessageEntityType.SPOILER:
                return True
    return False

# ✅ Valid link check function
def is_valid_link(text):
    pattern = r"(https?:\/\/)?(www\.)?(instagram\.com|facebook\.com|youtube\.com|youtu\.be)\/[\w\-\/\?&=]+"
    return bool(re.search(pattern, text))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    # ✅ Welcome message for new users
    if str(user_id) not in users:
        users[str(user_id)] = True
        save_users(users)  
        await update.message.reply_text(
            "👋 *Welcome to Insta/Facebook/Youtube Shorts Downloader!*\n\n"
            "📥 Just send a video link and I'll download it for you!\n"
            "✅ Supported: Instagram, Facebook, YouTube Shorts\n"
            "⚡ *Paste your link below and enjoy!*",
            parse_mode="Markdown"
        )

    # ✅ Check if link is valid
    if not is_valid_link(message_text):
        await update.message.reply_text("⚠️ *Invalid link! Please send a correct link.*", parse_mode="Markdown")
        return

    if is_user_or_chat_not_allowed(update.effective_user.username, chat_id):
        if update.effective_chat.type == "private":
            await update.message.reply_text(
                f"You are not allowed to use this bot.\n "
                f"[Username]:  {update.effective_user.username}\n "
                f"[Chat ID]: {chat_id}")
        return

    processing_msg = await update.message.reply_text("🚀 Processing your request...")

    # Download the video
    try:
        video_path = download_video(message_text)
        if not video_path or not os.path.exists(video_path):
            raise ValueError("Video download failed or file doesn't exist.")
    except Exception as e:
        print_logs(f"Error while downloading video: {e}")
        await update.message.reply_text(
            f"❌ Error occurred while downloading the video: {e}")
        return

    # Compress video if it's larger than 50MB
    try:
        if os.path.getsize(video_path) / (1024 * 1024) > 50:
            await update.message.reply_text("⚙️ Compressing video, file size is above 50MB.")
            compress_video(video_path)
    except Exception as e:
        print_logs(f"Error during video compression: {e}")
        await update.message.reply_text(
            f"❌ Error occurred during video compression: {e}")
        return

    visibility_flag = spoiler_in_message(update.message.entities)

    # Send the video to the chat
    try:
        with open(video_path, 'rb') as video_file:
            await update.message.chat.send_video(video=video_file,
                                                 has_spoiler=visibility_flag,
                                                 disable_notification=True,
                                                 write_timeout=8000,
                                                 read_timeout=8000)
    except TimedOut as e:
        print_logs(f"Telegram timeout while sending video. {e}")
        await update.message.reply_text("⏳ The video request timed out while sending. Please try again.")
    except telegram.error.TelegramError as e:
        print_logs(f"Telegram error while sending video: {e}")
        await update.message.reply_text(
            f"❌ Error occurred while sending the video. Compressed file size: "
            f"{os.path.getsize(video_path) / (1024 * 1024):.2f}MB. Telegram API Max is 50MB."
        )
    finally:
        if video_path:
            cleanup_file(video_path)
        try:
            await processing_msg.delete()
        except Exception as e:
            print(f"Failed to delete processing message: {e}")

# Main function
def main():
    try:
        bot_token = os.getenv("BOT_TOKEN")
        application = Application.builder().token(bot_token).build()
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("🚀 Bot started. Press Ctrl+C to stop.")
        application.run_polling()
    except (telegram.error.TelegramError, KeyboardInterrupt) as e:
        print("Error occurred while polling updates:", e)

if __name__ == "__main__":
    main()
