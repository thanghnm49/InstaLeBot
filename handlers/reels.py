"""Handler for getting user reels."""
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


async def reels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /reels command.
    
    Usage: /reels <user_id> [include_feed_video]
    """
    if not context.args:
        await update.message.reply_text(
            "🎬 <b>Reels Command</b>\n\n"
            "Get all reels from a user's Instagram account with thumbnails and captions.\n\n"
            "<b>Usage:</b>\n"
            "<code>/reels &lt;user_id&gt; [include_feed_video]</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/reels 25025320</code> - Get reels (includes feed videos)\n"
            "• <code>/reels 25025320 false</code> - Get only reels\n\n"
            "<i>Note: By default, feed videos are included</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_id = context.args[0]
    
    # Parse optional include_feed_video parameter
    include_feed_video = True
    if len(context.args) > 1:
        include_feed_video = context.args[1].lower() in ['true', '1', 'yes']
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ <b>Fetching reels...</b>\n"
        "Please wait while I retrieve the reels.",
        parse_mode=ParseMode.HTML
    )
    
    try:
        instagram_service = InstagramService()
        
        # Get user reels
        reels = instagram_service.get_user_reels(user_id, include_feed_video)
        
        if not reels:
            await processing_msg.edit_text(
                "❌ <b>No Reels Found</b>\n\n"
                "The user might not have any reels or the user ID is invalid.\n\n"
                "Please check:\n"
                "• User ID is correct\n"
                "• User has public reels\n"
                "• User account exists",
                parse_mode=ParseMode.HTML
            )
            return
        
        total_reels = len(reels)
        await processing_msg.edit_text(
            f"🎬 <b>Found {total_reels} reels!</b>\n"
            f"Sending thumbnails with captions...\n\n"
            f"<i>This may take a moment...</i>",
            parse_mode=ParseMode.HTML
        )
        
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
                    # Clean and truncate caption (limit to 900 chars for safety)
                    caption_clean = clean_caption(caption, max_length=900)
                    escaped_title = escape_html(caption_clean)
                else:
                    escaped_title = f"Reel {i}"
                
                # Send image with caption
                if image_url:
                    try:
                        # Try with HTML first
                        await update.message.reply_photo(
                            photo=image_url,
                            caption=escaped_title,
                            parse_mode=ParseMode.HTML
                        )
                        sent_count += 1
                    except BadRequest as parse_error:
                        # If HTML parsing fails, try plain text
                        logger.warning(f"HTML parse error for reel {i}, trying plain text: {str(parse_error)}")
                        try:
                            # Use plain text caption (no HTML)
                            plain_caption = clean_caption(caption, max_length=900) if caption else f"Reel {i}"
                            await update.message.reply_photo(
                                photo=image_url,
                                caption=plain_caption,
                                parse_mode=None
                            )
                            sent_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to send reel thumbnail {i}: {str(e)}")
                            # Final fallback: send text only
                            try:
                                plain_caption = clean_caption(caption, max_length=900) if caption else f"Reel {i}"
                                await update.message.reply_text(
                                    f"🎬 {plain_caption}",
                                    parse_mode=None
                                )
                                sent_count += 1
                            except Exception as final_error:
                                logger.error(f"Failed to send reel {i} even as text: {str(final_error)}")
                                continue
                else:
                    # No thumbnail, send text only
                    try:
                        await update.message.reply_text(
                            f"🎬 {escaped_title}",
                            parse_mode=ParseMode.HTML
                        )
                        sent_count += 1
                    except BadRequest as e:
                        # Fallback to plain text
                        logger.warning(f"HTML parse error for text-only reel {i}, using plain text: {str(e)}")
                        plain_caption = clean_caption(caption, max_length=900) if caption else f"Reel {i}"
                        await update.message.reply_text(
                            f"🎬 {plain_caption}",
                            parse_mode=None
                        )
                        sent_count += 1
                
            except Exception as e:
                logger.error(f"Error processing reel {i}: {str(e)}")
                continue
        
        # Update processing message
        if sent_count > 0:
            await processing_msg.edit_text(
                f"✅ <b>Success!</b>\n\n"
                f"Sent <b>{sent_count}</b> reel(s) with thumbnails and captions.\n\n"
                f"<i>Enjoy watching!</i>",
                parse_mode=ParseMode.HTML
            )
        else:
            await processing_msg.edit_text(
                "❌ <b>Failed to Send Reels</b>\n\n"
                "Unable to send any reels. Please try again later.",
                parse_mode=ParseMode.HTML
            )
        
    except ValueError as e:
        logger.error(f"Value error in reels command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in reels command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))
