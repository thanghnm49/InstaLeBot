"""Message formatting utilities."""
from typing import List, Dict, Any


def format_user_list(users: List[Dict[str, Any]], title: str = "Users") -> str:
    """
    Format a list of users into a readable message.
    
    Args:
        users: List of user dictionaries
        title: Title for the list
        
    Returns:
        Formatted message string
    """
    if not users:
        return f"{title}: No users found."
    
    lines = [f"*{title}* ({len(users)} users):\n"]
    
    for i, user in enumerate(users[:50], 1):  # Limit to 50 users
        username = user.get("username", user.get("user_name", "Unknown"))
        full_name = user.get("full_name", user.get("full_name", ""))
        user_id = user.get("pk", user.get("id", user.get("user_id", "")))
        
        line = f"{i}. @{username}"
        if full_name:
            line += f" - {full_name}"
        if user_id:
            line += f" (ID: {user_id})"
        
        lines.append(line)
    
    if len(users) > 50:
        lines.append(f"\n... and {len(users) - 50} more users")
    
    return "\n".join(lines)


def format_user_info(user_data: Dict[str, Any]) -> str:
    """
    Format user profile information.
    
    Args:
        user_data: User data dictionary
        
    Returns:
        Formatted message string
    """
    lines = ["*User Profile Information*\n"]
    
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
    
    lines.append(f"*Username:* @{username}")
    if full_name:
        lines.append(f"*Full Name:* {full_name}")
    if user_id:
        lines.append(f"*User ID:* {user_id}")
    if bio:
        lines.append(f"*Bio:* {bio}")
    
    lines.append("\n*Statistics:*")
    if followers:
        lines.append(f"  Followers: {followers:,}")
    if following:
        lines.append(f"  Following: {following:,}")
    if posts:
        lines.append(f"  Posts: {posts:,}")
    
    if is_verified:
        lines.append("\n✓ Verified Account")
    if is_private:
        lines.append("🔒 Private Account")
    
    if profile_pic:
        lines.append(f"\n[Profile Picture]({profile_pic})")
    
    return "\n".join(lines)


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

