import sys
import os
import signal
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
logger = logging.getLogger(__name__)

# Global reference for graceful shutdown
application = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    sig_name = signal.Signals(signum).name
    logger.info(f"Received {sig_name}, shutting down gracefully...")

    if application:
        # Stop the application
        application.stop_running()

    logger.info("Bot shutdown complete.")

def run_bot():
    global application

    # Initialize Flask App to access DB
    flask_app = create_app(os.getenv('FLASK_CONFIG') or 'default')

    with flask_app.app_context():
        if not Config.TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
            return

        logger.info("Starting Telegram Bot...")

        # Build the Telegram Application
        application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()

        # Store flask_app in bot_data for handlers to access thread-safe context
        application.bot_data['flask_app'] = flask_app

        # Setup handlers
        setup_handlers(application)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # kill command

        logger.info("Bot is running. Press Ctrl+C to stop.")

        # Run the bot with graceful shutdown support
        try:
            application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True  # Ignore old messages on startup
            )
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            logger.info("Bot stopped.")

if __name__ == '__main__':
    run_bot()
