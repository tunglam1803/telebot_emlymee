import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

# Import handlers from bot.py
from anime_bot.bot import start, search, today, chat, button_handler
from anime_bot.database import init_db

load_dotenv()

def main():
    # Initialize database
    init_db()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_telegram_token_here":
        print("LỖI: Chưa có TELEGRAM_BOT_TOKEN trong file .env!")
        return

    application = ApplicationBuilder().token(token).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("mylist", start)) # Placeholder for now
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # AI Chat handler (non-command messages)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))
    
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
