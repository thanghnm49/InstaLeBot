"""Handler for getting user reels."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from services.instagram import InstagramService
from utils.formatters import format_error_message
import logging
import re

logger = logging.getLogger(__name__)


def escape_html(text: str) -> str:
    """
    Escape special characters for HTML.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    if not text:
        return ""
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


async def reels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /reels command.
    
    Usage: /reels <user_id> [include_feed_video]
    """
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID.\n"
            "Usage: /reels <user_id> [include_feed_video]\n"
            "Example: /reels 25025320\n"
            "Example: /reels 25025320 true"
        )
        return
    
    user_id = context.args[0]
    
    # Parse optional include_feed_video parameter
    include_feed_video = True
    if len(context.args) > 1:
        include_feed_video = context.args[1].lower() in ['true', '1', 'yes']
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Fetching reels...")
    
    try:
        instagram_service = InstagramService()
        
        # Get user reels
        reels = instagram_service.get_user_reels(user_id, include_feed_video)
        
        if not reels:
            await processing_msg.edit_text(
                "❌ No reels found. The user might not have any reels or the user ID is invalid."
            )
            return
        
        await processing_msg.edit_text(f"🎬 Found {len(reels)} reels. Sending thumbnails...")
        
        # Send images with titles
        sent_count = 0
        max_reels = min(20, len(reels))  # Limit to 20 reels
        
        for i, reel in enumerate(reels[:max_reels], 1):
            try:
                # Extract image/thumbnail URL
                image_url = instagram_service.extract_image_url(reel)
                
                # Extract caption/title
                caption = reel.get("caption", reel.get("text", ""))
                if caption:
                    # Clean and truncate caption
                    caption_clean = re.sub(r'\s+', ' ', str(caption)).strip()
                    title = caption_clean[:200] + "..." if len(caption_clean) > 200 else caption_clean
                    escaped_title = escape_html(title)
                else:
                    escaped_title = f"Reel {i}"
                
                # Send image with caption
                if image_url:
                    try:
                        await update.message.reply_photo(
                            photo=image_url,
                            caption=escaped_title,
                            parse_mode=ParseMode.HTML
                        )
                        sent_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to send reel thumbnail {i}: {str(e)}")
                        # Fallback: send text only
                        await update.message.reply_text(
                            f"🎬 {escaped_title}",
                            parse_mode=ParseMode.HTML
                        )
                        sent_count += 1
                else:
                    # No thumbnail, send text only
                    await update.message.reply_text(
                        f"🎬 {escaped_title}",
                        parse_mode=ParseMode.HTML
                    )
                    sent_count += 1
                
            except Exception as e:
                logger.error(f"Error processing reel {i}: {str(e)}")
                continue
        
        # Update processing message
        if sent_count > 0:
            await processing_msg.edit_text(
                f"✅ Sent {sent_count} reel(s) with thumbnails!"
            )
        else:
            await processing_msg.edit_text(
                "❌ Failed to send any reels. Please try again."
            )
        
    except ValueError as e:
        logger.error(f"Value error in reels command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in reels command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))
