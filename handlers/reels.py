"""Handler for getting user reels."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from services.instagram import InstagramService
from utils.formatters import format_error_message
from utils.file_handler import download_file, delete_file
import logging
import re
import asyncio

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
    Handles Unicode and encoding issues properly.
    
    Args:
        caption: Original caption text
        max_length: Maximum length (default 900)
        
    Returns:
        Cleaned and truncated caption
    """
    if not caption:
        return ""
    
    try:
        # Ensure we're working with Unicode string
        if isinstance(caption, bytes):
            caption = caption.decode('utf-8', errors='replace')
        else:
            caption = str(caption)
        
        # Remove extra whitespace
        caption_clean = re.sub(r'\s+', ' ', caption).strip()
        
        # Truncate if too long (count Unicode characters properly)
        if len(caption_clean) > max_length:
            # Try to truncate at word boundary
            truncated = caption_clean[:max_length]
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:  # If we can find a space in the last 20%
                caption_clean = truncated[:last_space] + "..."
            else:
                caption_clean = truncated + "..."
        
        return caption_clean
    except Exception as e:
        # If encoding fails, try to salvage what we can
        logger.warning(f"Error cleaning caption: {str(e)}")
        try:
            return str(caption).encode('utf-8', errors='replace').decode('utf-8', errors='replace')[:max_length]
        except:
            return "Caption unavailable"


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
        
        # Ensure reels is a list
        if not isinstance(reels, list):
            logger.error(f"get_user_reels returned non-list type: {type(reels)}, value: {reels}")
            reels = []
        
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
        
        # Ensure we have a valid list before proceeding
        try:
            total_reels = len(reels)
            max_reels = min(20, total_reels)  # Limit to 20 reels
        except (TypeError, AttributeError) as e:
            logger.error(f"Error getting length of reels: {type(reels)}, error: {str(e)}")
            await processing_msg.edit_text(
                "❌ <b>Error Processing Reels</b>\n\n"
                "An error occurred while processing the reels data.\n"
                "Please try again later.",
                parse_mode=ParseMode.HTML
            )
            return
        
        await processing_msg.edit_text(
            f"🎬 <b>Found {total_reels} reels!</b>\n"
            f"Downloading and sending {max_reels} videos...\n\n"
            f"<i>This may take a moment...</i>",
            parse_mode=ParseMode.HTML
        )
        
        # Process reels to extract video URLs and captions
        reel_data = []
        try:
            reels_slice = reels[:max_reels] if max_reels > 0 else []
            for reel in reels_slice:
                try:
                    # Extract video URL from video_versions[0].url
                    video_url = instagram_service.extract_video_url(reel)
                    
                    # Extract caption/text
                    text = ""
                    if "caption" in reel:
                        caption = reel["caption"]
                        if isinstance(caption, dict):
                            text = caption.get("text", "")
                        else:
                            text = str(caption)
                    elif "text" in reel:
                        text = reel["text"]
                    
                    reel_data.append({
                        "video_url": video_url,
                        "text": text
                    })
                except Exception as e:
                    logger.error(f"Error processing reel: {str(e)}")
                    continue
        except (TypeError, AttributeError) as e:
            logger.error(f"Error slicing reels list: {type(reels)}, error: {str(e)}")
            await processing_msg.edit_text(
                "❌ <b>Error Processing Reels</b>\n\n"
                "An error occurred while processing the reels data.\n"
                "Please try again later.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Download and send videos
        sent_count = 0
        total_reels = len(reel_data)
        
        for i, reel_info in enumerate(reel_data, 1):
            video_url = reel_info.get("video_url")
            text = reel_info.get("text", "")
            
            # Update progress message for multiple reels
            if total_reels > 1:
                try:
                    await processing_msg.edit_text(
                        f"🎬 <b>Processing Reels...</b>\n\n"
                        f"Downloading reel <b>{i}</b> of <b>{total_reels}</b>\n\n"
                        f"<i>Please wait...</i>",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass  # Ignore errors updating progress message
            
            # Clean and truncate caption (Telegram caption limit is 1024)
            if text:
                caption_clean = clean_caption(text, max_length=900)
            else:
                caption_clean = f"Reel {i}/{total_reels}"
            
            try:
                if video_url:
                    # Download video file
                    try:
                        video_path = download_file(video_url, filename=f"reel_{i}.mp4")
                        try:
                            with open(video_path, 'rb') as video_file:
                                await update.message.reply_video(
                                    video=video_file,
                                    caption=caption_clean,
                                    parse_mode=None  # Plain text to avoid parsing errors
                                )
                            sent_count += 1
                            
                            # Add small delay between sends to avoid rate limiting (only for multiple reels)
                            if total_reels > 1 and i < total_reels:
                                await asyncio.sleep(1.5)  # 1.5 seconds delay between videos
                                
                        finally:
                            # Clean up downloaded file
                            delete_file(video_path)
                    except Exception as download_error:
                        logger.error(f"Failed to download and send video {i}: {str(download_error)}")
                        # Fallback: send text with video URL
                        try:
                            await update.message.reply_text(
                                f"🎬 {caption_clean}\n\n"
                                f"⚠️ <i>Video download failed</i>\n"
                                f"Video URL: {video_url}",
                                parse_mode=None
                            )
                            sent_count += 1
                        except Exception as final_error:
                            logger.error(f"Failed to send reel {i} even as text: {str(final_error)}")
                            continue
                else:
                    # No video URL, send text only
                    await update.message.reply_text(
                        f"🎬 {caption_clean}\n\n"
                        f"⚠️ <i>No video available for this reel</i>",
                        parse_mode=None
                    )
                    sent_count += 1
                
            except Exception as e:
                logger.error(f"Error sending reel {i}: {str(e)}")
                continue
        
        # Update processing message
        if sent_count > 0:
            success_msg = (
                f"✅ <b>Success!</b>\n\n"
                f"Downloaded and sent <b>{sent_count}</b> out of <b>{total_reels}</b> video reel(s).\n\n"
            )
            if sent_count < total_reels:
                success_msg += f"⚠️ <i>{total_reels - sent_count} reel(s) failed to send.</i>\n\n"
            success_msg += "<i>Enjoy watching!</i>"
            
            await processing_msg.edit_text(
                success_msg,
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
