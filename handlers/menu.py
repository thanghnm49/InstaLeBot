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
        "👋 <b>Welcome to Instagram Bot!</b>\n\n"
        "I'm here to help you explore Instagram content easily!\n\n"
        "<b>What I can do:</b>\n"
        "📥 Download videos and images from posts/reels\n"
        "👥 Get following and followers lists\n"
        "ℹ️ View user profile information\n"
        "🔍 Discover similar account recommendations\n"
        "🎥 Browse user video feeds with thumbnails\n"
        "📰 Browse user post feeds with images\n"
        "🎬 View user reels with thumbnails\n\n"
        "<b>Quick Commands:</b>\n"
        "• <code>/download &lt;url&gt;</code> - Download media\n"
        "• <code>/postfeed &lt;user_id&gt;</code> - Get posts\n"
        "• <code>/videofeed &lt;user_id&gt;</code> - Get videos\n"
        "• <code>/reels &lt;user_id&gt;</code> - Get reels\n"
        "• <code>/userinfo &lt;user_id&gt;</code> - User profile\n"
        "• <code>/menu</code> - Show interactive menu\n\n"
        "<i>Use the buttons below or type commands directly!</i>"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=create_menu_keyboard(),
        parse_mode='HTML'
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /menu command.
    """
    menu_message = (
        "📋 <b>Main Menu</b>\n\n"
        "Select an option from the menu below to get started:\n\n"
        "<i>Tap a button to see more details about each feature!</i>"
    )
    
    await update.message.reply_text(
        menu_message,
        reply_markup=create_menu_keyboard(),
        parse_mode='HTML'
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
            "📥 <b>Download Media</b>\n\n"
            "Download videos and images from Instagram posts or reels directly to your device.\n\n"
            "<b>Usage:</b>\n"
            "<code>/download &lt;instagram_url&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/download https://www.instagram.com/p/ABC123/</code>\n"
            "• <code>/download https://www.instagram.com/reel/XYZ789/</code>\n\n"
            "<i>Supports single posts, reels, and carousel posts with multiple media!</i>",
            parse_mode='HTML'
        )
    elif callback_data == "menu_following":
        await query.edit_message_text(
            "👥 <b>Get Following List</b>\n\n"
            "View all accounts that a specific user is following.\n\n"
            "<b>Usage:</b>\n"
            "<code>/following &lt;user_id&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/following 25025320</code>\n\n"
            "<i>Works best with public accounts</i>",
            parse_mode='HTML'
        )
    elif callback_data == "menu_followers":
        await query.edit_message_text(
            "👤 <b>Get Followers List</b>\n\n"
            "View all followers of a specific Instagram user.\n\n"
            "<b>Usage:</b>\n"
            "<code>/followers &lt;user_id&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/followers 25025320</code>\n\n"
            "<i>Works best with public accounts</i>",
            parse_mode='HTML'
        )
    elif callback_data == "menu_userinfo":
        await query.edit_message_text(
            "ℹ️ <b>User Information</b>\n\n"
            "Get detailed profile information including stats, bio, and verification status.\n\n"
            "<b>Usage:</b>\n"
            "<code>/userinfo &lt;user_id&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/userinfo 25025320</code>\n\n"
            "<i>Shows followers, following, posts count, and more!</i>",
            parse_mode='HTML'
        )
    elif callback_data == "menu_similar":
        await query.edit_message_text(
            "🔍 <b>Similar Account Recommendations</b>\n\n"
            "Discover accounts similar to a user that you might be interested in.\n\n"
            "<b>Usage:</b>\n"
            "<code>/similar &lt;user_id&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/similar 25025320</code>\n\n"
            "<i>Find new accounts to follow!</i>",
            parse_mode='HTML'
        )
    elif callback_data == "menu_videofeed":
        await query.edit_message_text(
            "🎥 <b>Video Feed</b>\n\n"
            "Browse all videos from a user's feed with thumbnails and captions.\n\n"
            "<b>Usage:</b>\n"
            "<code>/videofeed &lt;user_id&gt; [max_items]</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/videofeed 25025320</code> - Get videos (up to 50)\n"
            "• <code>/videofeed 25025320 30</code> - Get up to 30 videos\n\n"
            "<i>Each video is shown with its thumbnail and caption!</i>",
            parse_mode='HTML'
        )
    elif callback_data == "menu_postfeed":
        await query.edit_message_text(
            "📰 <b>Post Feed</b>\n\n"
            "Browse all posts from a user's feed with images and captions.\n\n"
            "<b>Usage:</b>\n"
            "<code>/postfeed &lt;user_id&gt; [max_items]</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/postfeed 25025320</code> - Get posts (up to 50)\n"
            "• <code>/postfeed 25025320 30</code> - Get up to 30 posts\n\n"
            "<i>Each post is shown with its image and caption!</i>",
            parse_mode='HTML'
        )
    elif callback_data == "menu_reels":
        await query.edit_message_text(
            "🎬 <b>Reels</b>\n\n"
            "View all reels from a user with thumbnails and captions.\n\n"
            "<b>Usage:</b>\n"
            "<code>/reels &lt;user_id&gt; [include_feed_video]</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/reels 25025320</code> - Get reels (includes feed videos)\n"
            "• <code>/reels 25025320 false</code> - Get only reels\n\n"
            "<i>Each reel is shown with its thumbnail and caption!</i>",
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text("❌ <b>Unknown Option</b>\n\nPlease select a valid option from the menu.", parse_mode='HTML')

