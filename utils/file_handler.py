"""File handling utilities for downloading and saving media."""
import os
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime
from config import DOWNLOADS_DIR


def download_file(url: str, filename: Optional[str] = None) -> Path:
    """
    Download a file from URL and save it locally.
    
    Args:
        url: URL of the file to download
        filename: Optional custom filename. If not provided, generates from URL
        
    Returns:
        Path to the downloaded file
        
    Raises:
        Exception: If download fails
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Check content length (max 50MB for Telegram)
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > 50 * 1024 * 1024:
            raise Exception("File is too large (max 50MB)")
        
        # Generate filename if not provided
        if not filename:
            # Try to get filename from URL
            url_path = url.split('?')[0]  # Remove query parameters
            url_filename = os.path.basename(url_path)
            
            if url_filename and '.' in url_filename:
                # Use filename from URL
                ext = os.path.splitext(url_filename)[1]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{url_filename}"
            else:
                # Generate filename based on content type
                content_type = response.headers.get('content-type', '')
                if 'video' in content_type:
                    ext = '.mp4'
                elif 'image' in content_type:
                    ext = '.jpg'
                else:
                    ext = '.bin'
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_media{ext}"
        
        # Ensure filename is safe
        filename = sanitize_filename(filename)
        filepath = DOWNLOADS_DIR / filename
        
        # Ensure downloads directory exists
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Download file
        try:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        except IOError as io_error:
            raise Exception(f"Failed to write file: {str(io_error)}")
        
        # Verify file was downloaded
        if not filepath.exists() or filepath.stat().st_size == 0:
            raise Exception("Downloaded file is empty or missing")
        
        return filepath
    except requests.exceptions.Timeout:
        raise Exception("Download timeout. Please try again.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error {e.response.status_code}: Failed to download file")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download file from {url}: {str(e)}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters for Windows/Unix
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


def get_file_size(filepath: Path) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in bytes
    """
    return filepath.stat().st_size


def delete_file(filepath: Path) -> bool:
    """
    Delete a file.
    
    Args:
        filepath: Path to file to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    except Exception:
        return False


def is_video_file(filepath: Path) -> bool:
    """
    Check if file is a video based on extension.
    
    Args:
        filepath: Path to file
        
    Returns:
        True if video, False otherwise
    """
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
    return filepath.suffix.lower() in video_extensions


def is_image_file(filepath: Path) -> bool:
    """
    Check if file is an image based on extension.
    
    Args:
        filepath: Path to file
        
    Returns:
        True if image, False otherwise
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    return filepath.suffix.lower() in image_extensions

