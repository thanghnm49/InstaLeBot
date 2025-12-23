"""Handler for getting user information."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from services.instagram import InstagramService
from utils.formatters import format_user_info, format_error_message, safe_split_html_message
import logging
import re

logger = logging.getLogger(__name__)


async def userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /userinfo command.
    
    Usage: /userinfo <username_or_user_id>
    """
    if not context.args:
        await update.message.reply_text(
            "ℹ️ <b>User Information Command</b>\n\n"
            "Get detailed profile information for an Instagram user.\n\n"
            "<b>Usage:</b>\n"
            "<code>/userinfo &lt;username_or_user_id&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/userinfo instagram</code> - By username\n"
            "• <code>/userinfo 25025320</code> - By user ID\n\n"
            "<i>Shows profile stats, bio, verification status, and more</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    identifier = context.args[0]
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ <b>Fetching user information...</b>\n"
        "Please wait while I retrieve the profile data.",
        parse_mode=ParseMode.HTML
    )
    
    try:
        instagram_service = InstagramService()
        
        # Get user information (accepts both username and user ID)
        user_data = instagram_service.get_user_info(identifier)
        
        if not user_data:
            await processing_msg.edit_text(
                "❌ <b>User Information Not Found</b>\n\n"
                "Unable to retrieve user information.\n\n"
                "Possible reasons:\n"
                "• Username or user ID is invalid\n"
                "• User account doesn't exist\n"
                "• Account is private or restricted\n\n"
                "Please check the username/user ID and try again.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Format and send
        message = format_user_info(user_data)
        
        # Check if profile picture URL exists
        profile_pic = user_data.get("profile_pic_url", user_data.get("profile_picture", ""))
        
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
                    plain_chunk = re.sub(r'<[^>]+>', '', chunk)
                    await update.message.reply_text(plain_chunk, parse_mode=None)
                except Exception as e:
                    logger.error(f"Unexpected error sending chunk: {str(e)}")
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
        
        # Send profile picture if available
        if profile_pic:
            try:
                await update.message.reply_photo(photo=profile_pic, caption="Profile Picture")
            except Exception as e:
                logger.warning(f"Failed to send profile picture: {str(e)}")
        
    except ValueError as e:
        logger.error(f"Value error in userinfo command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in userinfo command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))

