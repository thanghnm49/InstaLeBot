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
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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

