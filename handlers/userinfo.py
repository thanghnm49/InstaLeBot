"""Handler for getting user information."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from services.instagram import InstagramService
from utils.formatters import format_user_info, format_error_message
import logging

logger = logging.getLogger(__name__)


async def userinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /userinfo command.
    
    Usage: /userinfo <user_id>
    """
    if not context.args:
        await update.message.reply_text(
            "ℹ️ <b>User Information Command</b>\n\n"
            "Get detailed profile information for an Instagram user.\n\n"
            "<b>Usage:</b>\n"
            "<code>/userinfo &lt;user_id&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/userinfo 25025320</code>\n\n"
            "<i>Shows profile stats, bio, verification status, and more</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = context.args[0]
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ <b>Fetching user information...</b>\n"
        "Please wait while I retrieve the profile data.",
        parse_mode=ParseMode.HTML
    )
    
    try:
        instagram_service = InstagramService()
        
        # Get user information
        user_data = instagram_service.get_user_info(user_id)
        
        if not user_data:
            await processing_msg.edit_text(
                "❌ <b>User Information Not Found</b>\n\n"
                "Unable to retrieve user information.\n\n"
                "Possible reasons:\n"
                "• User ID is invalid\n"
                "• User account doesn't exist\n"
                "• Account is private or restricted\n\n"
                "Please check the user ID and try again.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Format and send
        message = format_user_info(user_data)
        
        # Check if profile picture URL exists
        profile_pic = user_data.get("profile_pic_url", user_data.get("profile_picture", ""))
        
        # Telegram message limit is 4096 characters
        if len(message) > 4096:
            # Split into multiple messages
            chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
            await processing_msg.delete()
        else:
            await processing_msg.edit_text(message, parse_mode='Markdown')
        
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

