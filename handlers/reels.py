"""Handler for getting user reels."""
from telegram import Update
from telegram.ext import ContextTypes
from services.instagram import InstagramService
from utils.formatters import format_error_message
import logging

logger = logging.getLogger(__name__)


def format_reels(reels: list, title: str = "Reels") -> str:
    """
    Format a list of reels into a readable message.
    
    Args:
        reels: List of reel dictionaries
        title: Title for the list
        
    Returns:
        Formatted message string
    """
    if not reels:
        return f"{title}: No reels found."
    
    lines = [f"*{title}* ({len(reels)} reels):\n"]
    
    for i, reel in enumerate(reels[:20], 1):  # Limit to 20 reels
        # Extract reel information
        reel_id = reel.get("pk", reel.get("id", reel.get("code", "")))
        caption = reel.get("caption", reel.get("text", ""))
        like_count = reel.get("like_count", reel.get("likes", ""))
        comment_count = reel.get("comment_count", reel.get("comments", ""))
        view_count = reel.get("view_count", reel.get("views", ""))
        video_url = reel.get("video_url", "")
        timestamp = reel.get("taken_at", reel.get("timestamp", ""))
        
        # Try to get video URL from video_versions if not directly available
        if not video_url and "video_versions" in reel:
            video_versions = reel.get("video_versions", [])
            if video_versions and len(video_versions) > 0:
                video_url = video_versions[0].get("url", "")
        
        # Get reel URL if available
        reel_url = ""
        if reel_id:
            reel_url = f"https://www.instagram.com/reel/{reel_id}/"
        elif "code" in reel:
            reel_url = f"https://www.instagram.com/reel/{reel.get('code')}/"
        
        line = f"{i}. 🎬 Reel {reel_id}"
        if caption:
            # Truncate long captions
            caption_preview = caption[:50] + "..." if len(caption) > 50 else caption
            line += f"\n   Caption: {caption_preview}"
        if like_count:
            line += f" | ❤️ {like_count:,}"
        if comment_count:
            line += f" | 💬 {comment_count:,}"
        if view_count:
            line += f" | 👁️ {view_count:,}"
        if video_url:
            line += f"\n   [Watch Reel]({video_url})"
        elif reel_url:
            line += f"\n   [View Reel]({reel_url})"
        
        lines.append(line)
    
    if len(reels) > 20:
        lines.append(f"\n... and {len(reels) - 20} more reels")
    
    return "\n".join(lines)


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
        
        # Format and send
        message = format_reels(reels, "Reels")
        
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
        logger.error(f"Value error in reels command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in reels command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))

