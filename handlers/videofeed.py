"""Handler for getting user video feed."""
from telegram import Update
from telegram.ext import ContextTypes
from services.instagram import InstagramService
from utils.formatters import format_error_message
import logging

logger = logging.getLogger(__name__)


def format_video_feed(videos: list, title: str = "Video Feed") -> str:
    """
    Format a list of videos into a readable message.
    
    Args:
        videos: List of video dictionaries
        title: Title for the list
        
    Returns:
        Formatted message string
    """
    if not videos:
        return f"{title}: No videos found."
    
    lines = [f"*{title}* ({len(videos)} videos):\n"]
    
    for i, video in enumerate(videos[:20], 1):  # Limit to 20 videos
        # Extract video information
        video_id = video.get("pk", video.get("id", video.get("code", "")))
        video_url = video.get("video_url", "")
        caption = video.get("caption", video.get("text", ""))
        like_count = video.get("like_count", video.get("likes", ""))
        comment_count = video.get("comment_count", video.get("comments", ""))
        timestamp = video.get("taken_at", video.get("timestamp", ""))
        
        # Try to get video URL from video_versions if not directly available
        if not video_url and "video_versions" in video:
            video_versions = video.get("video_versions", [])
            if video_versions and len(video_versions) > 0:
                video_url = video_versions[0].get("url", "")
        
        line = f"{i}. Video {video_id}"
        if caption:
            # Truncate long captions
            caption_preview = caption[:50] + "..." if len(caption) > 50 else caption
            line += f"\n   Caption: {caption_preview}"
        if like_count:
            line += f" | ❤️ {like_count:,}"
        if comment_count:
            line += f" | 💬 {comment_count:,}"
        if video_url:
            line += f"\n   [Watch Video]({video_url})"
        
        lines.append(line)
    
    if len(videos) > 20:
        lines.append(f"\n... and {len(videos) - 20} more videos")
    
    return "\n".join(lines)


async def videofeed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /videofeed command.
    
    Usage: /videofeed <user_id>
    """
    if not context.args:
        await update.message.reply_text(
            "Please provide a user ID.\n"
            "Usage: /videofeed <user_id>\n"
            "Example: /videofeed 25025320"
        )
        return
    
    user_id = context.args[0]
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Fetching video feed...")
    
    try:
        instagram_service = InstagramService()
        
        # Get video feed
        video_feed = instagram_service.get_video_feed(user_id)
        
        if not video_feed:
            await processing_msg.edit_text(
                "❌ No videos found. The user might not have any videos or the user ID is invalid."
            )
            return
        
        # Format and send
        message = format_video_feed(video_feed, "Video Feed")
        
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
        logger.error(f"Value error in videofeed command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in videofeed command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))

