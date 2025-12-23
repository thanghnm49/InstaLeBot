"""Message formatting utilities."""
from typing import List, Dict, Any
import re


def escape_html(text: str) -> str:
    """
    Escape special characters for HTML.
    Must escape & first to avoid double-escaping.
    Uses a simple, reliable approach that handles all edge cases.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for HTML
    """
    if not text:
        return ""
    
    # Convert to string and handle None
    text = str(text)
    
    # Escape in correct order: & first, then others
    # This ensures &amp; doesn't get double-escaped
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    
    # Remove any control characters that might cause issues
    # Keep only printable characters and common whitespace
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text


def format_user_list(users: List[Dict[str, Any]], title: str = "Users") -> str:
    """
    Format a list of users into a readable message using HTML.
    
    Args:
        users: List of user dictionaries
        title: Title for the list
        
    Returns:
        Formatted message string with HTML
    """
    if not users:
        return f"<b>{escape_html(title)}</b>: No users found."
    
    lines = [f"<b>{escape_html(title)}</b> ({len(users)} users):\n"]
    
    for i, user in enumerate(users[:50], 1):  # Limit to 50 users
        username = user.get("username", user.get("user_name", "Unknown"))
        full_name = user.get("full_name", user.get("full_name", ""))
        user_id = user.get("pk", user.get("id", user.get("user_id", "")))
        
        # Escape all user data
        username_escaped = escape_html(str(username))
        full_name_escaped = escape_html(str(full_name)) if full_name else ""
        user_id_escaped = escape_html(str(user_id)) if user_id else ""
        
        line = f"{i}. @{username_escaped}"
        if full_name_escaped:
            line += f" - {full_name_escaped}"
        if user_id_escaped:
            line += f" (ID: {user_id_escaped})"
        
        lines.append(line)
    
    if len(users) > 50:
        lines.append(f"\n... and {len(users) - 50} more users")
    
    return "\n".join(lines)


def format_user_info(user_data: Dict[str, Any]) -> str:
    """
    Format user profile information using HTML.
    
    Args:
        user_data: User data dictionary
        
    Returns:
        Formatted message string with HTML
    """
    lines = ["<b>User Profile Information</b>\n"]
    
    # Extract user information
    username = user_data.get("username", user_data.get("user_name", "Unknown"))
    full_name = user_data.get("full_name", "")
    user_id = user_data.get("pk", user_data.get("id", user_data.get("user_id", "")))
    bio = user_data.get("biography", user_data.get("bio", ""))
    followers = user_data.get("follower_count", user_data.get("followers", ""))
    following = user_data.get("following_count", user_data.get("following", ""))
    posts = user_data.get("media_count", user_data.get("posts", ""))
    is_verified = user_data.get("is_verified", False)
    is_private = user_data.get("is_private", False)
    profile_pic = user_data.get("profile_pic_url", user_data.get("profile_picture", ""))
    
    # Escape all user data
    username_escaped = escape_html(str(username))
    full_name_escaped = escape_html(str(full_name)) if full_name else ""
    user_id_escaped = escape_html(str(user_id)) if user_id else ""
    bio_escaped = escape_html(str(bio)) if bio else ""
    
    lines.append(f"<b>Username:</b> @{username_escaped}")
    if full_name_escaped:
        lines.append(f"<b>Full Name:</b> {full_name_escaped}")
    if user_id_escaped:
        lines.append(f"<b>User ID:</b> {user_id_escaped}")
    if bio_escaped:
        lines.append(f"<b>Bio:</b> {bio_escaped}")
    
    lines.append("\n<b>Statistics:</b>")
    if followers:
        try:
            followers_num = int(followers)
            lines.append(f"  Followers: {followers_num:,}")
        except (ValueError, TypeError):
            lines.append(f"  Followers: {escape_html(str(followers))}")
    if following:
        try:
            following_num = int(following)
            lines.append(f"  Following: {following_num:,}")
        except (ValueError, TypeError):
            lines.append(f"  Following: {escape_html(str(following))}")
    if posts:
        try:
            posts_num = int(posts)
            lines.append(f"  Posts: {posts_num:,}")
        except (ValueError, TypeError):
            lines.append(f"  Posts: {escape_html(str(posts))}")
    
    if is_verified:
        lines.append("\n✓ Verified Account")
    if is_private:
        lines.append("🔒 Private Account")
    
    if profile_pic:
        profile_pic_escaped = escape_html(profile_pic)
        lines.append(f"\n<a href=\"{profile_pic_escaped}\">Profile Picture</a>")
    
    return "\n".join(lines)


def safe_split_html_message(message: str, max_length: int = 4096) -> List[str]:
    """
    Split HTML message into chunks, ensuring we don't split in the middle of HTML tags.
    
    Args:
        message: HTML formatted message
        max_length: Maximum length per chunk (default 4096 for Telegram)
        
    Returns:
        List of message chunks
    """
    if len(message) <= max_length:
        return [message]
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(message):
        # Calculate the end position for this chunk
        end_pos = min(current_pos + max_length, len(message))
        
        # If this is the last chunk, just add it
        if end_pos >= len(message):
            chunks.append(message[current_pos:])
            break
        
        # Try to find a safe split point (newline or space, not inside HTML tag)
        # Look backwards from end_pos for a newline
        safe_split = message.rfind('\n', current_pos, end_pos)
        
        # If no newline found, try to find a space
        if safe_split == -1:
            safe_split = message.rfind(' ', current_pos, end_pos)
        
        # If still no safe split found, check if we're in the middle of an HTML tag
        # Look backwards for '<' and forwards for '>'
        if safe_split == -1:
            # Check if we're inside an HTML tag
            last_tag_start = message.rfind('<', current_pos, end_pos)
            next_tag_end = message.find('>', end_pos)
            
            if last_tag_start != -1 and next_tag_end != -1 and last_tag_start < end_pos < next_tag_end:
                # We're inside a tag, split before the tag starts
                safe_split = last_tag_start
            else:
                # Just split at max_length
                safe_split = end_pos
        
        # Extract chunk
        chunk = message[current_pos:safe_split].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move to next position (skip the newline/space we split on)
        current_pos = safe_split + 1 if safe_split < len(message) else end_pos
    
    return chunks if chunks else [message]


def format_error_message(error: Exception) -> str:
    """
    Format error message for user display.
    
    Args:
        error: Exception object
        
    Returns:
        User-friendly error message
    """
    error_msg = str(error).lower()
    error_str = str(error)
    
    # Common error messages
    if "404" in error_str or "not found" in error_msg:
        return "❌ Resource not found. Please check the user ID or URL."
    elif "429" in error_str or "rate limit" in error_msg:
        return "⏳ Rate limit exceeded. Please try again in a few moments."
    elif "401" in error_str or "403" in error_str or "unauthorized" in error_msg or "authentication" in error_msg:
        return "❌ Authentication failed. Please check API credentials."
    elif "timeout" in error_msg:
        return "⏱️ Request timed out. Please try again."
    elif "connection" in error_msg:
        return "🌐 Connection error. Please check your internet connection."
    elif "too large" in error_msg:
        return "📦 File is too large. Maximum size is 50MB."
    elif "invalid" in error_msg and "json" in error_msg:
        return "❌ Invalid response from API. Please try again later."
    elif "bad request" in error_msg or "400" in error_str:
        return "❌ Invalid request. Please check your parameters."
    else:
        # Return a generic message to avoid exposing internal errors
        return "❌ An error occurred. Please try again or contact support if the issue persists."

