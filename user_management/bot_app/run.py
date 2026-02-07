import sys
import os
import asyncio
import logging
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv

# Load env vars explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '../config.env'))

# Add parent directory to path to allow importing 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from bot_app.config import Config
from bot_app.core.handlers import setup_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def run_bot():
    # Initialize Flask App to access DB
    flask_app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    
    with flask_app.app_context():
        if not Config.TELEGRAM_BOT_TOKEN:
            print("Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
            return

        print("Starting Telegram Bot...")
        
        # Build the Telegram Application
        application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Store flask_app in bot_data for handlers to access thread-safe context
        application.bot_data['flask_app'] = flask_app


        # Setup handlers
        setup_handlers(application)

        # Run the bot
        application.run_polling()

if __name__ == '__main__':
    run_bot()
