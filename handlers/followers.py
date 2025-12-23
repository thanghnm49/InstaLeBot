"""Handler for getting followers list."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
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
            "👤 <b>Followers List Command</b>\n\n"
            "Get the list of followers for a specific Instagram user.\n\n"
            "<b>Usage:</b>\n"
            "<code>/followers &lt;user_id&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/followers 25025320</code>\n\n"
            "<i>Note: Works best with public accounts</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = context.args[0]
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ <b>Fetching followers list...</b>\n"
        "Please wait while I retrieve the data.",
        parse_mode=ParseMode.HTML
    )
    
    try:
        instagram_service = InstagramService()
        
        # Get followers list
        followers_list = instagram_service.get_followers_list(user_id)
        
        if not followers_list:
            await processing_msg.edit_text(
                "❌ <b>No Followers List Found</b>\n\n"
                "Unable to retrieve the followers list.\n\n"
                "Possible reasons:\n"
                "• User account is private\n"
                "• User ID is invalid\n"
                "• User has no followers\n\n"
                "Please check the user ID and try again.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Format and send
        message = format_user_list(followers_list, "Followers")
        
        # Telegram message limit is 4096 characters
        if len(message) > 4096:
            # Split into multiple messages
            chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]
            for chunk in chunks:
                try:
                    await update.message.reply_text(chunk, parse_mode=ParseMode.HTML)
                except Exception as e:
                    # Fallback to plain text if HTML parsing fails
                    logger.warning(f"HTML parse error in chunk, using plain text: {str(e)}")
                    await update.message.reply_text(chunk, parse_mode=None)
            await processing_msg.delete()
        else:
            try:
                await processing_msg.edit_text(message, parse_mode=ParseMode.HTML)
            except Exception as e:
                # Fallback to plain text if HTML parsing fails
                logger.warning(f"HTML parse error, using plain text: {str(e)}")
                await processing_msg.edit_text(message, parse_mode=None)
        
    except ValueError as e:
        logger.error(f"Value error in followers command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in followers command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))

