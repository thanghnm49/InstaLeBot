"""Handler for getting user post feed."""
from telegram import Update
from telegram.ext import ContextTypes
from services.instagram import InstagramService
from utils.formatters import format_error_message
import logging

logger = logging.getLogger(__name__)


def format_post_feed(posts: list, title: str = "Post Feed") -> str:
    """
    Format a list of posts into a readable message.
    
    Args:
        posts: List of post dictionaries
        title: Title for the list
        
    Returns:
        Formatted message string
    """
    if not posts:
        return f"{title}: No posts found."
    
    lines = [f"*{title}* ({len(posts)} posts):\n"]
    
    for i, post in enumerate(posts[:20], 1):  # Limit to 20 posts
        # Extract post information
        post_id = post.get("pk", post.get("id", post.get("code", "")))
        caption = post.get("caption", post.get("text", ""))
        like_count = post.get("like_count", post.get("likes", ""))
        comment_count = post.get("comment_count", post.get("comments", ""))
        timestamp = post.get("taken_at", post.get("timestamp", ""))
        post_type = post.get("media_type", post.get("type", ""))
        
        # Get post URL if available
        post_url = ""
        if post_id:
            post_url = f"https://www.instagram.com/p/{post_id}/"
        elif "code" in post:
            post_url = f"https://www.instagram.com/p/{post.get('code')}/"
        
        # Determine post type emoji
        type_emoji = "📷"
        if post_type == 2 or "video" in str(post_type).lower():
            type_emoji = "🎥"
        elif post_type == 8 or "carousel" in str(post_type).lower():
            type_emoji = "📸"
        
        line = f"{i}. {type_emoji} Post {post_id}"
        if caption:
            # Truncate long captions
            caption_preview = caption[:50] + "..." if len(caption) > 50 else caption
            line += f"\n   Caption: {caption_preview}"
        if like_count:
            line += f" | ❤️ {like_count:,}"
        if comment_count:
            line += f" | 💬 {comment_count:,}"
        if post_url:
            line += f"\n   [View Post]({post_url})"
        
        lines.append(line)
    
    if len(posts) > 20:
        lines.append(f"\n... and {len(posts) - 20} more posts")
    
    return "\n".join(lines)


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
    
    Usage: /postfeed <user_id>
    """
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID.\n"
            "Usage: /postfeed <user_id>\n"
            "Example: /postfeed 25025320"
        )
        return
    
    user_id = context.args[0]
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Fetching post feed...")
    
    try:
        instagram_service = InstagramService()
        
        # Get user feed
        feed_data = instagram_service.get_user_feed(user_id)
        
        # Extract posts from feed
        posts = extract_posts_from_feed(feed_data)
        
        if not posts:
            await processing_msg.edit_text(
                "❌ No posts found. The user might not have any posts or the user ID is invalid."
            )
            return
        
        # Format and send
        message = format_post_feed(posts, "Post Feed")
        
        # Telegram message limit is 4096 characters
        if len(message) > 4096:
            # Split into multiple messages
            chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
            await processing_msg.delete()
        else:
            await processing_msg.edit_text(message, parse_mode='Markdown')
        
    except ValueError as e:
        logger.error(f"Value error in postfeed command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in postfeed command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))

