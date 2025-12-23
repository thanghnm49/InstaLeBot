"""Handler for getting followers list."""
from telegram import Update
from telegram.ext import ContextTypes
from services.instagram import InstagramService
from utils.formatters import format_user_list, format_error_message
import logging

logger = logging.getLogger(__name__)


async def followers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /followers command.
    
    Usage: /followers <user_id>
    """
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID.\n"
            "Usage: /followers <user_id>\n"
            "Example: /followers 25025320"
        )
        return
    
    user_id = context.args[0]
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Fetching followers list...")
    
    try:
        instagram_service = InstagramService()
        
        # Get followers list
        followers_list = instagram_service.get_followers_list(user_id)
        
        if not followers_list:
            await processing_msg.edit_text(
                "❌ No followers list found. The user might be private or the user ID is invalid."
            )
            return
        
        # Format and send
        message = format_user_list(followers_list, "Followers")
        
        # Telegram message limit is 4096 characters
        if len(message) > 4096:
            # Split into multiple messages
            chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
            await processing_msg.delete()
        else:
            await processing_msg.edit_text(message, parse_mode='Markdown')
        
    except ValueError as e:
        logger.error(f"Value error in followers command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in followers command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))

