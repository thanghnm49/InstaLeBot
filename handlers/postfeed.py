"""Handler for getting user post feed."""
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
            "Please provide a user ID.\n"
            "Usage: /postfeed <user_id> [max_items]\n"
            "Example: /postfeed 25025320\n"
            "Example: /postfeed 25025320 50"
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
    processing_msg = await update.message.reply_text("⏳ Fetching post feed...")
    
    try:
        instagram_service = InstagramService()
        
        # Get user feed with pagination
        posts, next_max_id = instagram_service.get_user_feed(user_id, max_items=max_items)
        
        if not posts:
            await processing_msg.edit_text(
                "❌ No posts found. The user might not have any posts or the user ID is invalid."
            )
            return
        
        total_posts = len(posts)
        max_posts = min(50, total_posts) if max_items is None else min(max_items, total_posts)
        
        await processing_msg.edit_text(f"📸 Found {total_posts} posts. Sending {max_posts} images...")
        
        # Send images with titles
        sent_count = 0
        
        for i, post in enumerate(posts[:max_posts], 1):
            try:
                # Extract image URL
                image_url = instagram_service.extract_image_url(post)
                
                # Extract caption/title
                caption = post.get("caption", post.get("text", ""))
                if caption:
                    # Clean and truncate caption
                    caption_clean = re.sub(r'\s+', ' ', str(caption)).strip()
                    title = caption_clean[:200] + "..." if len(caption_clean) > 200 else caption_clean
                    escaped_title = escape_html(title)
                else:
                    escaped_title = f"Post {i}"
                
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
                        logger.warning(f"Failed to send image {i}: {str(e)}")
                        # Fallback: send text only
                        await update.message.reply_text(
                            f"📷 {escaped_title}",
                            parse_mode=ParseMode.HTML
                        )
                        sent_count += 1
                else:
                    # No image, send text only
                    await update.message.reply_text(
                        f"📷 {escaped_title}",
                        parse_mode=ParseMode.HTML
                    )
                    sent_count += 1
                
            except Exception as e:
                logger.error(f"Error processing post {i}: {str(e)}")
                continue
        
        # Update processing message
        if sent_count > 0:
            await processing_msg.edit_text(
                f"✅ Sent {sent_count} post(s) with images!"
            )
        else:
            await processing_msg.edit_text(
                "❌ Failed to send any posts. Please try again."
            )
        
    except ValueError as e:
        logger.error(f"Value error in postfeed command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in postfeed command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))
