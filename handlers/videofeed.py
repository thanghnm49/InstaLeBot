"""Handler for getting user video feed."""
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


async def videofeed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /videofeed command.
    
    Usage: /videofeed <user_id> [max_items]
    """
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID.\n"
            "Usage: /videofeed <user_id> [max_items]\n"
            "Example: /videofeed 25025320\n"
            "Example: /videofeed 25025320 50"
        )
        return
    
    user_id = context.args[0]
    
    # Parse optional max_items parameter
    max_items = None
    if len(context.args) > 1:
        try:
            max_items = int(context.args[1])
            if max_items < 1:
                max_items = None
            elif max_items > 100:
                max_items = 100  # Limit to 100 items
        except ValueError:
            max_items = None
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Fetching video feed...")
    
    try:
        instagram_service = InstagramService()
        
        # Get video feed with pagination
        video_feed, next_max_id = instagram_service.get_video_feed(user_id, max_items=max_items)
        
        if not video_feed:
            await processing_msg.edit_text(
                "❌ No videos found. The user might not have any videos or the user ID is invalid."
            )
            return
        
        total_videos = len(video_feed)
        max_videos = min(50, total_videos) if max_items is None else min(max_items, total_videos)
        
        await processing_msg.edit_text(f"🎥 Found {total_videos} videos. Sending {max_videos} thumbnails...")
        
        # Send images with titles
        sent_count = 0
        
        for i, video in enumerate(video_feed[:max_videos], 1):
            try:
                # Extract image/thumbnail URL
                image_url = instagram_service.extract_image_url(video)
                
                # Extract caption/title
                caption = video.get("caption", video.get("text", ""))
                if caption:
                    # Clean and truncate caption
                    caption_clean = re.sub(r'\s+', ' ', str(caption)).strip()
                    title = caption_clean[:200] + "..." if len(caption_clean) > 200 else caption_clean
                    escaped_title = escape_html(title)
                else:
                    escaped_title = f"Video {i}"
                
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
                        logger.warning(f"Failed to send video thumbnail {i}: {str(e)}")
                        # Fallback: send text only
                        await update.message.reply_text(
                            f"🎥 {escaped_title}",
                            parse_mode=ParseMode.HTML
                        )
                        sent_count += 1
                else:
                    # No thumbnail, send text only
                    await update.message.reply_text(
                        f"🎥 {escaped_title}",
                        parse_mode=ParseMode.HTML
                    )
                    sent_count += 1
                
            except Exception as e:
                logger.error(f"Error processing video {i}: {str(e)}")
                continue
        
        # Update processing message
        if sent_count > 0:
            await processing_msg.edit_text(
                f"✅ Sent {sent_count} video(s) with thumbnails!"
            )
        else:
            await processing_msg.edit_text(
                "❌ Failed to send any videos. Please try again."
            )
        
    except ValueError as e:
        logger.error(f"Value error in videofeed command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in videofeed command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))
