"""Main bot entry point."""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN
from handlers.download import download_command
from handlers.following import following_command
from handlers.followers import followers_command
from handlers.userinfo import userinfo_command
from handlers.similar import similar_command
from handlers.videofeed import videofeed_command
from handlers.postfeed import postfeed_command
from handlers.reels import reels_command
from handlers.menu import start_command, menu_command, menu_callback

# Configure logging
# Create logs directory if it doesn't exist
import os
from pathlib import Path

logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure logging with both file and console handlers
# Use rotating file handler to prevent log files from growing too large
from logging.handlers import RotatingFileHandler

log_file = logs_dir / 'bot.log'
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB per file
    backupCount=5,  # Keep 5 backup files
    encoding='utf-8'
)
# Ensure file handler flushes immediately
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
# Ensure console handler flushes immediately
console_handler.setLevel(logging.INFO)

# Set format for both handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)
logger.info(f"Logging configured. Log file: {log_file.absolute()}")

# Test RapidAPI logging after configuration
try:
    from services.rapidapi import _test_logging
    _test_logging()
except:
    pass


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )
        except Exception:
            pass


def main():
    """Start the bot."""
    # Create application
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("download", download_command))
    application.add_handler(CommandHandler("following", following_command))
    application.add_handler(CommandHandler("followers", followers_command))
    application.add_handler(CommandHandler("userinfo", userinfo_command))
    application.add_handler(CommandHandler("similar", similar_command))
    application.add_handler(CommandHandler("videofeed", videofeed_command))
    application.add_handler(CommandHandler("postfeed", postfeed_command))
    application.add_handler(CommandHandler("reels", reels_command))
    
    # Register callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting bot...")
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)


if __name__ == "__main__":
    main()

