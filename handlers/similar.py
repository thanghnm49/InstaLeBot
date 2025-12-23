"""Handler for getting similar account recommendations."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
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
            "🔍 <b>Similar Accounts Command</b>\n\n"
            "Discover account recommendations similar to a specific Instagram user.\n\n"
            "<b>Usage:</b>\n"
            "<code>/similar &lt;user_id&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/similar 25025320</code>\n\n"
            "<i>Find accounts you might be interested in!</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = context.args[0]
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ <b>Finding similar accounts...</b>\n"
        "Please wait while I analyze and find recommendations.",
        parse_mode=ParseMode.HTML
    )
    
    try:
        instagram_service = InstagramService()
        
        # Get similar accounts
        similar_accounts = instagram_service.get_similar_accounts(user_id)
        
        if not similar_accounts:
            await processing_msg.edit_text(
                "❌ <b>No Similar Accounts Found</b>\n\n"
                "Unable to find account recommendations.\n\n"
                "Possible reasons:\n"
                "• User ID is invalid\n"
                "• No recommendations available\n"
                "• Account is too new or has limited activity\n\n"
                "Please try a different user ID.",
                parse_mode=ParseMode.HTML
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

