"""Handler for getting similar account recommendations."""
from telegram import Update
from telegram.ext import ContextTypes
from services.instagram import InstagramService
from utils.formatters import format_user_list, format_error_message
import logging

logger = logging.getLogger(__name__)


async def similar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /similar command.
    
    Usage: /similar <user_id>
    """
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID.\n"
            "Usage: /similar <user_id>\n"
            "Example: /similar 25025320"
        )
        return
    
    user_id = context.args[0]
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Fetching similar account recommendations...")
    
    try:
        instagram_service = InstagramService()
        
        # Get similar accounts
        similar_accounts = instagram_service.get_similar_accounts(user_id)
        
        if not similar_accounts:
            await processing_msg.edit_text(
                "❌ No similar accounts found. The user ID might be invalid or there are no recommendations available."
            )
            return
        
        # Format and send
        message = format_user_list(similar_accounts, "Similar Account Recommendations")
        
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
        logger.error(f"Value error in similar command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in similar command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))

