import os
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


# Cache responses from JSON file
@lru_cache(maxsize=1)
def load_responses():
    """Function loading bot responses based on language setting."""
    language = os.getenv("LANGUAGE",
                         "en").lower()  # Default to Ukrainian if not set

    filename = "responses_ua.json" if language == "ua" else "responses_en.json"
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data["responses"]
    except FileNotFoundError:
        # Return a minimal set of responses if no response files found
        return [
            "Sorry, I'm having trouble loading my responses right now! 😅",
            "Вибачте, у мене проблеми із завантаженням відповідей! 😅"
        ]


responses = load_responses()


# Check if message has a spoiler
def spoiler_in_message(entities):
    if entities:
        for entity in entities:
            if entity.type == MessageEntityType.SPOILER:
                return True
    return False


# Handle incoming messages and process videos
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):  # pylint: disable=unused-argument
    """Handle incoming messages and process videos."""
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.strip()

    # Handle bot mention response
    if "ботяра" in message_text.lower() or "bot_health" in message_text.lower(
    ):
        await update.message.reply_text(
            f"{random.choice(responses)}\n"
            f"[Chat ID]: {update.effective_chat.id}\n"
            f"[Username]: {update.effective_user.username}")
        return

    # Check if user is not allowed
    if is_user_or_chat_not_allowed(update.effective_user.username,
                                   update.effective_chat.id):
        if update.effective_chat.type == "private":
            await update.message.reply_text(
                f"You are not allowed to use this bot.\n "
                f"[Username]:  {update.effective_user.username}\n "
                f"[Chat ID]: {update.effective_chat.id}")
        return

    message_text = message_text.replace("** ", "**")

    # Quick check before more expensive operations
    if not any(site in message_text for site in supported_sites):
        return

    if "instagram.com/stories/" in message_text:
        await update.message.reply_text("Сторіз не можу скачати. Треба логін")
        return

    # Remove '**' prefix and any spaces if present
    message_text = message_text.replace(
        "**", "") if message_text.startswith("**") else message_text
    print_logs(f"message_text is {message_text}")

    # Send checkpoint: User input received
    processing_msg = await update.message.reply_text(
        "🚀 Processing your request...")

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
            await update.message.reply_text(
                "⚙️ Compressing video, file size is above 50MB.")
            compress_video(video_path)
    except Exception as e:
        print_logs(f"Error during video compression: {e}")
        await update.message.reply_text(
            f"❌ Error occurred during video compression: {e}")
        return

    # Check if the message has a spoiler
    visibility_flag = spoiler_in_message(update.message.entities)

    # Send the video to the chat
    try:
        with open(video_path, 'rb') as video_file:
            await update.message.chat.send_video(video=video_file,
                                                 has_spoiler=visibility_flag,
                                                 disable_notification=True,
                                                 write_timeout=8000,
                                                 read_timeout=8000)
            # Send final checkpoint
            # await update.message.reply_text("✅ Video sent successfully!")
    except TimedOut as e:
        print_logs(f"Telegram timeout while sending video. {e}")
        await update.message.reply_text(
            "⏳ The video request timed out while sending. Please try again.")
    except telegram.error.TelegramError as e:
        print_logs(f"Telegram error while sending video: {e}")
        await update.message.reply_text(
            f"❌ Error occurred while sending the video. Compressed file size: "
            f"{os.path.getsize(video_path) / (1024 * 1024):.2f}MB. Telegram API Max is 50MB."
        )
    finally:
        # Clean up regardless of success or failure
        if video_path:
            cleanup_file(video_path)

        # Delete the "Processing your request..." message
        try:
            await processing_msg.delete()  # Delete the original message
        except Exception as e:
            print(f"Failed to delete processing message: {e}")


# Main function
def main():
    try:
        bot_token = os.getenv("BOT_TOKEN")
        application = Application.builder().token(bot_token).build()
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("Bot started. Ctrl+c to stop")
        application.run_polling()
    except (telegram.error.TelegramError, KeyboardInterrupt) as e:
        print("Error occurred while polling updates:", e)


if __name__ == "__main__":
    main()
