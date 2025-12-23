"""Handler for getting user post feed."""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from services.instagram import InstagramService
from utils.formatters import format_error_message
from utils.file_handler import download_file, delete_file
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


def extract_posts_from_feed(feed_data: dict) -> list:
    """
    Extract posts list from feed response.
    
    Args:
        feed_data: Feed data from API
        
    Returns:
        List of posts
    """
    if isinstance(feed_data, list):
        return feed_data
    elif isinstance(feed_data, dict):
        # Common response structures
        if "data" in feed_data:
            return feed_data["data"]
        elif "items" in feed_data:
            return feed_data["items"]
        elif "posts" in feed_data:
            return feed_data["posts"]
        elif "feed" in feed_data:
            return feed_data["feed"]
        # Sometimes the feed data itself is a list of posts
        elif "user" in feed_data and "edge_owner_to_timeline_media" in feed_data["user"]:
            edges = feed_data["user"]["edge_owner_to_timeline_media"].get("edges", [])
            return [edge.get("node", {}) for edge in edges]
    return []


async def postfeed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /postfeed command.
    
    Usage: /postfeed <user_id> [max_items]
    """
    if not context.args:
        await update.message.reply_text(
            "📰 <b>Post Feed Command</b>\n\n"
            "Get all posts from a user's Instagram feed with images and captions.\n\n"
            "<b>Usage:</b>\n"
            "<code>/postfeed &lt;user_id&gt; [max_items]</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/postfeed 25025320</code> - Get all posts\n"
            "• <code>/postfeed 25025320 30</code> - Get up to 30 posts\n\n"
            "<i>Note: If you specify a number larger than available posts, all posts will be fetched</i>",
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
            # No upper limit - will fetch all available if max_items is larger
        except ValueError:
            max_items = None
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ <b>Fetching post feed...</b>\n"
        "Please wait while I retrieve the posts.",
        parse_mode=ParseMode.HTML
    )
    
    try:
        instagram_service = InstagramService()
        
        # Get user feed with pagination
        posts, next_max_id = instagram_service.get_user_feed(user_id, max_items=max_items)
        
        if not posts:
            await processing_msg.edit_text(
                "❌ <b>No Posts Found</b>\n\n"
                "The user might not have any posts or the user ID is invalid.\n\n"
                "Please check:\n"
                "• User ID is correct\n"
                "• User has public posts\n"
                "• User account exists",
                parse_mode=ParseMode.HTML
            )
            return
        
        total_posts = len(posts)
        # If max_items is specified, use it (but not more than available)
        # If max_items is None, fetch all available posts
        max_posts = min(max_items, total_posts) if max_items else total_posts
        
        await processing_msg.edit_text(
            f"📸 <b>Found {total_posts} posts!</b>\n"
            f"Sending {max_posts} images with captions...\n\n"
            f"<i>This may take a moment...</i>",
            parse_mode=ParseMode.HTML
        )
        
        # Format all posts to get only text and image_url
        formatted_posts = []
        for post in posts[:max_posts]:
            try:
                formatted_post = instagram_service.format_media_item(post)
                formatted_posts.append(formatted_post)
            except Exception as e:
                logger.error(f"Error formatting post: {str(e)}")
                continue
        
        # Send images with text captions
        sent_count = 0
        
        for i, formatted_post in enumerate(formatted_posts, 1):
            image_url = formatted_post.get("image_url")
            text = formatted_post.get("text", "")
            
            # Clean and truncate caption (Telegram caption limit is 1024)
            if text:
                caption_clean = clean_caption(text, max_length=900)
            else:
                caption_clean = f"Post {i}"
            
            try:
                if image_url:
                    # Try to send image with caption (using URL directly)
                    try:
                        await update.message.reply_photo(
                            photo=image_url,
                            caption=caption_clean,
                            parse_mode=None  # Plain text to avoid parsing errors
                        )
                        sent_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to send image from URL {i}: {str(e)}")
                        # Fallback: download and send
                        try:
                            image_path = download_file(image_url)
                            try:
                                with open(image_path, 'rb') as photo_file:
                                    await update.message.reply_photo(
                                        photo=photo_file,
                                        caption=caption_clean,
                                        parse_mode=None
                                    )
                                sent_count += 1
                            finally:
                                # Clean up downloaded file
                                delete_file(image_path)
                        except Exception as download_error:
                            logger.error(f"Failed to download and send image {i}: {str(download_error)}")
                            # Final fallback: send text only
                            await update.message.reply_text(
                                caption_clean,
                                parse_mode=None
                            )
                            sent_count += 1
                else:
                    # No image, send text only
                    await update.message.reply_text(
                        caption_clean,
                        parse_mode=None
                    )
                    sent_count += 1
                
            except Exception as e:
                logger.error(f"Error sending post {i}: {str(e)}")
                continue
        
        # Update processing message
        if sent_count > 0:
            await processing_msg.edit_text(
                f"✅ <b>Success!</b>\n\n"
                f"Sent <b>{sent_count}</b> post(s) with images and captions.\n\n"
                f"<i>Enjoy browsing!</i>",
                parse_mode=ParseMode.HTML
            )
        else:
            await processing_msg.edit_text(
                "❌ <b>Failed to Send Posts</b>\n\n"
                "Unable to send any posts. Please try again later.",
                parse_mode=ParseMode.HTML
            )
        
    except ValueError as e:
        logger.error(f"Value error in postfeed command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in postfeed command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))
