"""Handler for downloading Instagram media."""
from telegram import Update
from telegram.ext import ContextTypes
from services.instagram import InstagramService
from utils.file_handler import download_file, is_video_file, is_image_file, delete_file
from utils.formatters import format_error_message
import logging

logger = logging.getLogger(__name__)


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /download command.
    
    Usage: /download <instagram_url>
    """
    if not context.args:
        await update.message.reply_text(
            "Please provide an Instagram URL.\n"
            "Usage: /download <instagram_url>\n"
            "Example: /download https://www.instagram.com/p/ABC123/"
        )
        return
    
    url = " ".join(context.args)
    
    # Validate URL
    if "instagram.com" not in url:
        await update.message.reply_text(
            "❌ Invalid Instagram URL. Please provide a valid Instagram post or reel URL."
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Processing your request...")
    
    try:
        instagram_service = InstagramService()
        
        # Get post information
        post_data = instagram_service.get_post_media(url)
        
        # Extract media URLs
        media_urls = instagram_service.extract_media_urls(post_data)
        
        if not media_urls:
            await processing_msg.edit_text(
                "❌ No media found in this post. It might be a text-only post or the URL is invalid."
            )
            return
        
        # Download and send each media file
        downloaded_files = []
        successful_downloads = 0
        
        for i, media_url in enumerate(media_urls):
            filepath = None
            try:
                # Download file
                filepath = download_file(media_url)
                downloaded_files.append(filepath)
                
                # Send to user with proper file handling
                try:
                    # Convert Path to string for file operations
                    filepath_str = str(filepath)
                    
                    if is_video_file(filepath):
                        with open(filepath_str, 'rb') as f:
                            await update.message.reply_video(
                                video=f,
                                caption=f"Video {i+1} from Instagram post"
                            )
                    elif is_image_file(filepath):
                        with open(filepath_str, 'rb') as f:
                            await update.message.reply_photo(
                                photo=f,
                                caption=f"Image {i+1} from Instagram post"
                            )
                    else:
                        with open(filepath_str, 'rb') as f:
                            await update.message.reply_document(
                                document=f,
                                caption=f"Media {i+1} from Instagram post"
                            )
                    successful_downloads += 1
                except Exception as send_error:
                    logger.error(f"Error sending media {i+1}: {str(send_error)}")
                    await update.message.reply_text(
                        f"❌ Failed to send media {i+1}: {format_error_message(send_error)}"
                    )
                
            except Exception as e:
                logger.error(f"Error downloading media {i+1}: {str(e)}")
                await update.message.reply_text(
                    f"❌ Failed to download media {i+1}: {format_error_message(e)}"
                )
        
        # Clean up files after sending
        for filepath in downloaded_files:
            try:
                if filepath and filepath.exists():
                    delete_file(filepath)
            except Exception as e:
                logger.warning(f"Failed to delete file {filepath}: {str(e)}")
        
        # Update processing message
        if successful_downloads > 0:
            await processing_msg.edit_text(
                f"✅ Successfully downloaded and sent {successful_downloads} out of {len(media_urls)} media file(s)!"
            )
        else:
            await processing_msg.edit_text(
                "❌ Failed to download any media files. Please try again."
            )
        
    except ValueError as e:
        logger.error(f"Value error in download command: {str(e)}")
        await processing_msg.edit_text(format_error_message(e))
    except Exception as e:
        logger.error(f"Error in download command: {str(e)}", exc_info=True)
        await processing_msg.edit_text(format_error_message(e))

