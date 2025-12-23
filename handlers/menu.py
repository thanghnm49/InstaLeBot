"""Handler for menu and inline keyboard."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


def create_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Create inline keyboard menu.
    
    Returns:
        InlineKeyboardMarkup with menu buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("📥 Download Media", callback_data="menu_download"),
        ],
        [
            InlineKeyboardButton("👥 Get Following", callback_data="menu_following"),
            InlineKeyboardButton("👤 Get Followers", callback_data="menu_followers"),
        ],
        [
            InlineKeyboardButton("ℹ️ User Info", callback_data="menu_userinfo"),
            InlineKeyboardButton("🔍 Similar Accounts", callback_data="menu_similar"),
        ],
        [
            InlineKeyboardButton("🎥 Video Feed", callback_data="menu_videofeed"),
            InlineKeyboardButton("📰 Post Feed", callback_data="menu_postfeed"),
        ],
        [
            InlineKeyboardButton("🎬 Reels", callback_data="menu_reels"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    """
    welcome_message = (
        "👋 Welcome to Instagram Bot!\n\n"
        "I can help you:\n"
        "• Download Instagram videos and images\n"
        "• Get following/followers lists\n"
        "• Get user profile information\n"
        "• Find similar account recommendations\n"
        "• Get user video feed\n"
        "• Get user post feed\n"
        "• Get user reels\n\n"
        "Use the menu below or send commands directly:\n"
        "• /download <url> - Download media\n"
        "• /following <user_id> - Get following list\n"
        "• /followers <user_id> - Get followers list\n"
        "• /userinfo <user_id> - Get user info\n"
        "• /similar <user_id> - Find similar accounts\n"
        "• /videofeed <user_id> - Get video feed\n"
        "• /postfeed <user_id> - Get post feed\n"
        "• /reels <user_id> - Get reels\n"
        "• /menu - Show this menu"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=create_menu_keyboard()
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /menu command.
    """
    menu_message = (
        "📋 *Menu*\n\n"
        "Select an option from the menu below:"
    )
    
    await update.message.reply_text(
        menu_message,
        reply_markup=create_menu_keyboard(),
        parse_mode='Markdown'
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle menu button callbacks.
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "menu_download":
        await query.edit_message_text(
            "📥 *Download Media*\n\n"
            "Send me an Instagram post or reel URL to download.\n\n"
            "Usage: /download <instagram_url>\n"
            "Example: /download https://www.instagram.com/p/ABC123/",
            parse_mode='Markdown'
        )
    elif callback_data == "menu_following":
        await query.edit_message_text(
            "👥 *Get Following List*\n\n"
            "Get the list of users that a user is following.\n\n"
            "Usage: /following <user_id>\n"
            "Example: /following 25025320",
            parse_mode='Markdown'
        )
    elif callback_data == "menu_followers":
        await query.edit_message_text(
            "👤 *Get Followers List*\n\n"
            "Get the list of followers for a user.\n\n"
            "Usage: /followers <user_id>\n"
            "Example: /followers 25025320",
            parse_mode='Markdown'
        )
    elif callback_data == "menu_userinfo":
        await query.edit_message_text(
            "ℹ️ *User Information*\n\n"
            "Get profile information for a user.\n\n"
            "Usage: /userinfo <user_id>\n"
            "Example: /userinfo 25025320",
            parse_mode='Markdown'
        )
    elif callback_data == "menu_similar":
        await query.edit_message_text(
            "🔍 *Similar Account Recommendations*\n\n"
            "Get account recommendations similar to a user.\n\n"
            "Usage: /similar <user_id>\n"
            "Example: /similar 25025320",
            parse_mode='Markdown'
        )
    elif callback_data == "menu_videofeed":
        await query.edit_message_text(
            "🎥 *Video Feed*\n\n"
            "Get all videos from a user's feed.\n\n"
            "Usage: /videofeed <user_id>\n"
            "Example: /videofeed 25025320",
            parse_mode='Markdown'
        )
    elif callback_data == "menu_postfeed":
        await query.edit_message_text(
            "📰 *Post Feed*\n\n"
            "Get all posts from a user's feed.\n\n"
            "Usage: /postfeed <user_id>\n"
            "Example: /postfeed 25025320",
            parse_mode='Markdown'
        )
    elif callback_data == "menu_reels":
        await query.edit_message_text(
            "🎬 *Reels*\n\n"
            "Get all reels from a user.\n\n"
            "Usage: /reels <user_id> [include_feed_video]\n"
            "Example: /reels 25025320\n"
            "Example: /reels 25025320 true",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("❌ Unknown menu option.")

