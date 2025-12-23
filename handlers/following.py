"""Handler for getting following list."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from services.instagram import InstagramService
from utils.formatters import format_user_list, format_error_message, safe_split_html_message
import logging
import re

logger = logging.getLogger(__name__)


async def following_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /following command.
    
    Usage: /following <user_id>
    """
    if not context.args:
        await update.message.reply_text(
            "👥 <b>Following List Command</b>\n\n"
            "Get the list of users that a specific Instagram user is following.\n\n"
            "<b>Usage:</b>\n"
            "<code>/following &lt;user_id&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/following 25025320</code>\n\n"
            "<i>Note: Works best with public accounts</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = context.args[0]
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ <b>Fetching following list...</b>\n"
        "Please wait while I retrieve the data.",
        parse_mode=ParseMode.HTML
    )
    
    try:
        instagram_service = InstagramService()
        
        # Get following list
        following_list = instagram_service.get_following_list(user_id)
        
        if not following_list:
            await processing_msg.edit_text(
                "❌ <b>No Following List Found</b>\n\n"
                "Unable to retrieve the following list.\n\n"
                "Possible reasons:\n"
                "• User account is private\n"
                "• User ID is invalid\n"
                "• User has no following\n\n"
                "Please check the user ID and try again.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Format and send
        message = format_user_list(following_list, "Following")
        
        # Telegram message limit is 4096 characters
        if len(message) > 4096:
            # Split into multiple messages safely
            chunks = safe_split_html_message(message, max_length=4096)
            for chunk in chunks:
                try:
                    await update.message.reply_text(chunk, parse_mode=ParseMode.HTML)
                except BadRequest as e:
                    # Fallback to plain text if HTML parsing fails
                    logger.warning(f"HTML parse error in chunk, using plain text: {str(e)}")
                    # Remove HTML tags for plain text
                    plain_chunk = re.sub(r'<[^>]+>', '', chunk)
                    await update.message.reply_text(plain_chunk, parse_mode=None)
                except Exception as e:
                    logger.error(f"Unexpected error sending chunk: {str(e)}")
                    # Try plain text as last resort
                    plain_chunk = re.sub(r'<[^>]+>', '', chunk)
                    await update.message.reply_text(plain_chunk, parse_mode=None)
            await processing_msg.delete()
        else:
            try:
                await processing_msg.edit_text(message, parse_mode=ParseMode.HTML)
            except BadRequest as e:
                # Fallback to plain text if HTML parsing fails
                logger.warning(f"HTML parse error, using plain text: {str(e)}")
                plain_message = re.sub(r'<[^>]+>', '', message)
                await processing_msg.edit_text(plain_message, parse_mode=None)
            except Exception as e:
                logger.error(f"Unexpected error editing message: {str(e)}")
                plain_message = re.sub(r'<[^>]+>', '', message)
                await processing_msg.edit_text(plain_message, parse_mode=None)
        
    except ValueError as e:
        logger.error(f"Value error in following command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in following command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))

