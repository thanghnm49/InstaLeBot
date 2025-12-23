"""Handler for getting user video feed."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from services.instagram import InstagramService
from utils.formatters import format_error_message
import logging
import re

logger = logging.getLogger(__name__)


def escape_html(text: str) -> str:
    """
    Escape special characters for HTML.
    Must escape & first to avoid double-escaping.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    if not text:
        return ""
    text = str(text)
    # Escape in correct order: & first, then others
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#39;')
    return text


def clean_caption(caption: str, max_length: int = 900) -> str:
    """
    Clean and truncate caption for Telegram.
    Telegram caption limit is 1024 characters, but we use 900 for safety.
    
    Args:
        caption: Original caption text
        max_length: Maximum length (default 900)
        
    Returns:
        Cleaned and truncated caption
    """
    if not caption:
        return ""
    
    # Remove extra whitespace
    caption_clean = re.sub(r'\s+', ' ', str(caption)).strip()
    
    # Truncate if too long
    if len(caption_clean) > max_length:
        # Try to truncate at word boundary
        truncated = caption_clean[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # If we can find a space in the last 20%
            caption_clean = truncated[:last_space] + "..."
        else:
            caption_clean = truncated + "..."
    
    return caption_clean


async def videofeed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /videofeed command.
    
    Usage: /videofeed <user_id> [max_items]
    """
    if not context.args:
        await update.message.reply_text(
            "🎥 <b>Video Feed Command</b>\n\n"
            "Get all videos from a user's Instagram feed with thumbnails and captions.\n\n"
            "<b>Usage:</b>\n"
            "<code>/videofeed &lt;user_id&gt; [max_items]</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/videofeed 25025320</code> - Get videos (default: up to 50)\n"
            "• <code>/videofeed 25025320 30</code> - Get up to 30 videos\n\n"
            "<i>Note: You can specify how many videos to fetch (max 100)</i>",
            parse_mode=ParseMode.HTML
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
    processing_msg = await update.message.reply_text(
        "⏳ <b>Fetching video feed...</b>\n"
        "Please wait while I retrieve the videos.",
        parse_mode=ParseMode.HTML
    )
    
    try:
        instagram_service = InstagramService()
        
        # Get video feed with pagination
        video_feed, next_max_id = instagram_service.get_video_feed(user_id, max_items=max_items)
        
        if not video_feed:
            await processing_msg.edit_text(
                "❌ <b>No Videos Found</b>\n\n"
                "The user might not have any videos or the user ID is invalid.\n\n"
                "Please check:\n"
                "• User ID is correct\n"
                "• User has public videos\n"
                "• User account exists",
                parse_mode=ParseMode.HTML
            )
            return
        
        total_videos = len(video_feed)
        max_videos = min(50, total_videos) if max_items is None else min(max_items, total_videos)
        
        await processing_msg.edit_text(
            f"🎥 <b>Found {total_videos} videos!</b>\n"
            f"Sending {max_videos} thumbnails with captions...\n\n"
            f"<i>This may take a moment...</i>",
            parse_mode=ParseMode.HTML
        )
        
        # Send images with titles
        sent_count = 0
        
        for i, video in enumerate(video_feed[:max_videos], 1):
            try:
                # Extract image/thumbnail URL
                image_url = instagram_service.extract_image_url(video)
                
                # Extract caption/title
                caption = video.get("caption", video.get("text", ""))
                if caption:
                    # Clean and truncate caption (limit to 900 chars for safety)
                    # Use plain text to avoid HTML parsing issues
                    caption_clean = clean_caption(caption, max_length=900)
                else:
                    caption_clean = f"Video {i}"
                
                # Send image with caption (always use plain text for user content)
                if image_url:
                    try:
                        await update.message.reply_photo(
                            photo=image_url,
                            caption=caption_clean,
                            parse_mode=None  # Plain text to avoid parsing errors
                        )
                        sent_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to send video thumbnail {i}: {str(e)}")
                        # Fallback: send text only
                        try:
                            await update.message.reply_text(
                                f"🎥 {caption_clean}",
                                parse_mode=None
                            )
                            sent_count += 1
                        except Exception as final_error:
                            logger.error(f"Failed to send video {i} even as text: {str(final_error)}")
                            continue
                else:
                    # No thumbnail, send text only
                    await update.message.reply_text(
                        f"🎥 {caption_clean}",
                        parse_mode=None
                    )
                    sent_count += 1
                
            except Exception as e:
                logger.error(f"Error processing video {i}: {str(e)}")
                continue
        
        # Update processing message
        if sent_count > 0:
            await processing_msg.edit_text(
                f"✅ <b>Success!</b>\n\n"
                f"Sent <b>{sent_count}</b> video(s) with thumbnails and captions.\n\n"
                f"<i>Enjoy watching!</i>",
                parse_mode=ParseMode.HTML
            )
        else:
            await processing_msg.edit_text(
                "❌ <b>Failed to Send Videos</b>\n\n"
                "Unable to send any videos. Please try again later.",
                parse_mode=ParseMode.HTML
            )
        
    except ValueError as e:
        logger.error(f"Value error in videofeed command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in videofeed command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))
