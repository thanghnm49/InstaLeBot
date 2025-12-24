"""Instagram API wrapper service."""
from typing import Dict, Any, List, Optional
from services.rapidapi import RapidAPIClient
import re
import logging
import time

logger = logging.getLogger(__name__)


class InstagramService:
    """Service for interacting with Instagram via RapidAPI."""
    
    def __init__(self):
        """Initialize Instagram service with RapidAPI client."""
        self.client = RapidAPIClient()
    
    def extract_user_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract user ID from Instagram URL.
        
        Args:
            url: Instagram profile URL
            
        Returns:
            User ID if found, None otherwise
        """
        # Try to extract from URL patterns
        patterns = [
            r'instagram\.com/([^/?]+)',
            r'instagram\.com/u/([^/?]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def extract_post_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract post/reel ID from Instagram URL.
        
        Args:
            url: Instagram post/reel URL
            
        Returns:
            Post ID if found, None otherwise
        """
        patterns = [
            r'instagram\.com/p/([^/?]+)',
            r'instagram\.com/reel/([^/?]+)',
            r'instagram\.com/tv/([^/?]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_user_feed(self, user_id: str, next_max_id: Optional[str] = None, max_items: Optional[int] = None) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get user feed with pagination support.
        Continues fetching until no data or duplicates are found.
        
        Args:
            user_id: Instagram user ID
            next_max_id: Pagination cursor for next page
            max_items: Maximum number of items to fetch (None for all available)
            
        Returns:
            Tuple of (list of posts, next_max_id for pagination)
        """
        all_posts = []
        seen_ids = set()  # Track post IDs to detect duplicates
        current_max_id = next_max_id
        max_pages = 50  # Safety limit to prevent infinite loops
        
        logger.info(f"Starting post feed pagination for user_id={user_id}, initial_next_max_id={next_max_id}, max_items={max_items}")
        
        for page in range(max_pages):
            logger.info(f"Post feed pagination - Page {page + 1}/{max_pages} | Current next_max_id: {current_max_id} | Total posts so far: {len(all_posts)}")
            
            # Rate limiting: Add delay between API calls (except for first page)
            if page > 0:
                delay = 3  # 3 seconds delay between pagination requests
                logger.info(f"Rate limiting: Waiting {delay} seconds before next API call...")
                time.sleep(delay)
            
            feed_data = self.client.get_feed(user_id, current_max_id)
            
            # Extract posts from feed
            posts = []
            if isinstance(feed_data, list):
                posts = feed_data
            elif isinstance(feed_data, dict):
                # Check for nested data.items structure first
                if "data" in feed_data and isinstance(feed_data["data"], dict):
                    data = feed_data["data"]
                    if "items" in data and isinstance(data["items"], list):
                        items = data["items"]
                        # Extract media from items if they have a 'media' key
                        posts = []
                        for item in items:
                            if isinstance(item, dict):
                                if "media" in item:
                                    posts.append(item["media"])
                                else:
                                    posts.append(item)
                    elif isinstance(data, list):
                        posts = data
                elif "data" in feed_data and isinstance(feed_data["data"], list):
                    posts = feed_data["data"]
                elif "items" in feed_data:
                    items = feed_data["items"]
                    if isinstance(items, list):
                        # Extract media from items if they have a 'media' key
                        posts = []
                        for item in items:
                            if isinstance(item, dict):
                                if "media" in item:
                                    posts.append(item["media"])
                                else:
                                    posts.append(item)
                elif "posts" in feed_data:
                    posts = feed_data["posts"]
                elif "feed" in feed_data:
                    posts = feed_data["feed"]
                elif "user" in feed_data and "edge_owner_to_timeline_media" in feed_data["user"]:
                    edges = feed_data["user"]["edge_owner_to_timeline_media"].get("edges", [])
                    posts = [edge.get("node", {}) for edge in edges]
            
            # Process posts from this response and check for duplicates
            if posts:
                # Filter out duplicates based on title/text and image URL
                new_posts = []
                duplicate_found = False
                
                for post in posts:
                    # Extract title/text and image URL for duplicate detection
                    post_text = ""
                    post_image_url = None
                    
                    if isinstance(post, dict):
                        # Get text/caption
                        if "caption" in post:
                            caption = post["caption"]
                            if isinstance(caption, dict):
                                post_text = caption.get("text", "")
                            else:
                                post_text = str(caption)
                        elif "text" in post:
                            post_text = post["text"]
                        
                        # Get image URL
                        post_image_url = self.extract_image_url(post)
                    
                    # Check for duplicates by text and image URL
                    is_duplicate = False
                    if post_text:
                        text_key = post_text.strip()[:100]  # Use first 100 chars as key
                        if text_key in seen_ids:
                            is_duplicate = True
                            duplicate_found = True
                        else:
                            seen_ids.add(text_key)
                    
                    if not is_duplicate and post_image_url:
                        if post_image_url in seen_ids:
                            is_duplicate = True
                            duplicate_found = True
                        else:
                            seen_ids.add(post_image_url)
                    
                    # Also check by post ID as fallback
                    if not is_duplicate:
                        post_id = None
                        if isinstance(post, dict):
                            post_id = post.get("id") or post.get("pk") or post.get("media_id") or post.get("code")
                        
                        if post_id:
                            post_id_str = f"id_{post_id}"
                            if post_id_str in seen_ids:
                                is_duplicate = True
                                duplicate_found = True
                            else:
                                seen_ids.add(post_id_str)
                    
                    if not is_duplicate:
                        new_posts.append(post)
                
                # If we found duplicates and no new posts, stop pagination
                if duplicate_found and not new_posts:
                    logger.info(f"Post feed pagination - Page {page + 1}: Found duplicates, no new posts. Stopping pagination.")
                    break
                
                logger.info(f"Post feed pagination - Page {page + 1}: Found {len(posts)} posts, {len(new_posts)} new posts (after duplicate check), Total: {len(all_posts) + len(new_posts)}")
                all_posts.extend(new_posts)
            
            # Check if we have enough items
            if max_items and len(all_posts) >= max_items:
                all_posts = all_posts[:max_items]
                break
            
            # Extract next_max_id from response - check all possible locations
            next_max_id = None
            if isinstance(feed_data, dict):
                # Check top level first
                next_max_id = feed_data.get("next_max_id")
                
                # Check in data.paging_info (common location)
                if not next_max_id and "data" in feed_data and isinstance(feed_data["data"], dict):
                    data = feed_data["data"]
                    paging_info = data.get("paging_info", {})
                    if isinstance(paging_info, dict):
                        next_max_id = paging_info.get("max_id") or paging_info.get("next_max_id")
                    
                    # Also check if next_max_id is directly in data
                    if not next_max_id:
                        next_max_id = data.get("next_max_id") or data.get("max_id")
                
                # Check in pagination object
                if not next_max_id:
                    pagination = feed_data.get("pagination", {})
                    if isinstance(pagination, dict):
                        next_max_id = pagination.get("next_max_id") or pagination.get("next_cursor") or pagination.get("max_id")
            
            # Stop pagination if no next_max_id found (no more pages)
            if not next_max_id:
                logger.info(f"Post feed pagination - Page {page + 1}: No next_max_id found. Stopping pagination. Total posts collected: {len(all_posts)}")
                break
            
            logger.info(f"Post feed pagination - Page {page + 1}: Found next_max_id={next_max_id}. Continuing to next page.")
            # Use the next_max_id from response for next request
            current_max_id = next_max_id
        
        logger.info(f"Post feed pagination completed. Total posts: {len(all_posts)}, Final next_max_id: {current_max_id}")
        return all_posts, current_max_id
    
    def get_following_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get following list for a user.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            List of users being followed
        """
        logger.info(f"Getting following list for user_id={user_id}")
        response = self.client.get_following(user_id)
        # Extract list from response (structure may vary)
        result = []
        if isinstance(response, list):
            result = response
        elif isinstance(response, dict):
            # Common response structures
            if "data" in response:
                result = response["data"]
            elif "following" in response:
                result = response["following"]
            elif "users" in response:
                result = response["users"]
        
        logger.info(f"Successfully retrieved {len(result)} following users for user_id={user_id}")
        return result
    
    def get_followers_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get followers list for a user.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            List of followers
        """
        logger.info(f"Getting followers list for user_id={user_id}")
        response = self.client.get_followers(user_id)
        # Extract list from response (structure may vary)
        result = []
        if isinstance(response, list):
            result = response
        elif isinstance(response, dict):
            # Common response structures
            if "data" in response:
                result = response["data"]
            elif "followers" in response:
                result = response["followers"]
            elif "users" in response:
                result = response["users"]
        
        logger.info(f"Successfully retrieved {len(result)} followers for user_id={user_id}")
        return result
    
    def get_user_id_by_username(self, username: str) -> Optional[str]:
        """
        Get user ID by username.
        
        Args:
            username: Instagram username (without @)
            
        Returns:
            User ID if found, None otherwise
        """
        try:
            # Remove @ if present
            username = username.lstrip('@')
            
            response = self.client.get_user_id_by_username(username)
            
            # Extract user ID from response (structure may vary)
            if isinstance(response, dict):
                # Try common response structures (check both lowercase and capitalized versions)
                user_id = (
                    response.get("user_id") or 
                    response.get("UserID") or  # API returns "UserID" with capital letters
                    response.get("user_id") or 
                    response.get("id") or 
                    response.get("Id") or
                    response.get("ID") or
                    response.get("pk")
                )
                if user_id:
                    logger.info(f"Found user_id={user_id} from response keys: {list(response.keys())}")
                    return str(user_id)
                # Check in data field
                if "data" in response:
                    data = response["data"]
                    if isinstance(data, dict):
                        user_id = (
                            data.get("user_id") or 
                            data.get("UserID") or 
                            data.get("id") or 
                            data.get("Id") or
                            data.get("ID") or
                            data.get("pk")
                        )
                        if user_id:
                            logger.info(f"Found user_id={user_id} from data field")
                            return str(user_id)
                    elif isinstance(data, str):
                        # If data is directly the user ID
                        return data
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting user ID by username: {str(e)}")
        
        return None
    
    def get_username_by_user_id(self, user_id: str) -> Optional[str]:
        """
        Get username by user ID.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            Username if found, None otherwise
        """
        try:
            response = self.client.get_username_by_user_id(user_id)
            
            # Extract username from response (structure may vary)
            if isinstance(response, dict):
                # Try common response structures (check both lowercase and capitalized versions)
                username = (
                    response.get("username") or 
                    response.get("UserName") or  # API returns "UserName" with capital letters
                    response.get("user_name") or
                    response.get("userName")
                )
                if username:
                    logger.info(f"Found username={username} from response keys: {list(response.keys())}")
                    return str(username)
                # Check in data field
                if "data" in response:
                    data = response["data"]
                    if isinstance(data, dict):
                        username = (
                            data.get("username") or 
                            data.get("UserName") or 
                            data.get("user_name") or
                            data.get("userName")
                        )
                        if username:
                            logger.info(f"Found username={username} from data field")
                            return str(username)
                    elif isinstance(data, str):
                        # If data is directly the username
                        return data
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting username by user ID: {str(e)}")
        
        return None
    
    def get_user_info(self, identifier: str) -> Dict[str, Any]:
        """
        Get user profile information.
        Accepts either username or user ID.
        
        Flow:
        - If numeric (user ID) → call username_by_id to get username → call user_id_by_username with that username → call profile?user_id
        - If not numeric (username) → call user_id_by_username to get user ID → call profile?user_id
        
        Args:
            identifier: Instagram username (with or without @) or user ID
            
        Returns:
            User profile data
        """
        identifier_clean = identifier.lstrip('@').strip()
        logger.info(f"Getting user info for identifier={identifier_clean}")
        
        # Determine if it's a user ID (numeric) or username
        is_numeric = identifier_clean.isdigit()
        
        if is_numeric:
            # It's a user ID (numeric)
            logger.info(f"Identifier is numeric (user ID). Converting: user_id={identifier_clean} → username → user_id")
            # Step 1: Get username from user ID using username_by_id API
            username = self.get_username_by_user_id(identifier_clean)
            if not username:
                logger.error(f"Could not find username for user ID: {identifier_clean}")
                raise ValueError(f"Could not find username for user ID: {identifier_clean}")
            
            logger.info(f"Got username={username} from user_id={identifier_clean}")
            # Rate limiting: Add delay before next API call
            delay = 1.5  # 1.5 seconds delay between API calls
            logger.info(f"Rate limiting: Waiting {delay} seconds before next API call...")
            time.sleep(delay)
            
            # Step 2: Get user ID from username using user_id_by_username API
            user_id = self.get_user_id_by_username(username)
            if not user_id:
                logger.error(f"Could not find user ID for username: {username}")
                raise ValueError(f"Could not find user ID for username: {username}")
            
            logger.info(f"Got user_id={user_id} from username={username}")
        else:
            # It's a username (not numeric)
            logger.info(f"Identifier is username. Converting: username={identifier_clean} → user_id")
            # Get user ID from username using user_id_by_username API
            user_id = self.get_user_id_by_username(identifier_clean)
            if not user_id:
                logger.error(f"Could not find user ID for username: {identifier_clean}")
                raise ValueError(f"Could not find user ID for username: {identifier_clean}")
            
            logger.info(f"Got user_id={user_id} from username={identifier_clean}")
        
        # Rate limiting: Add delay before profile API call
        delay = 1.5  # 1.5 seconds delay before profile API
        logger.info(f"Rate limiting: Waiting {delay} seconds before profile API call...")
        time.sleep(delay)
        
        # Always use profile API with user_id (never use profile API with username directly)
        logger.info(f"Fetching profile info for user_id={user_id}")
        return self.client.get_user_info(user_id)
    
    def get_post_media(self, post_url: str) -> Dict[str, Any]:
        """
        Get media URLs from a post/reel.
        
        Args:
            post_url: Instagram post/reel URL
            
        Returns:
            Post data with media URLs
        """
        return self.client.get_post_info(post_url)
    
    def get_similar_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get similar account recommendations (discover chaining).
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            List of similar/recommended accounts
        """
        response = self.client.get_discover_chaining(user_id)
        # Extract list from response (structure may vary)
        result = []
        if isinstance(response, list):
            result = response
        elif isinstance(response, dict):
            # Common response structures
            if "data" in response:
                result = response["data"]
            elif "users" in response:
                result = response["users"]
            elif "recommendations" in response:
                result = response["recommendations"]
            elif "similar_accounts" in response:
                result = response["similar_accounts"]
            elif "chaining" in response:
                result = response["chaining"]
        
        logger.info(f"Successfully retrieved {len(result)} similar accounts for user_id={user_id}")
        return result
    
    def extract_image_url(self, media_item: Dict[str, Any]) -> Optional[str]:
        """
        Extract the first/best image URL from a media item.
        
        Args:
            media_item: Media item dictionary (post, video, reel)
            
        Returns:
            Image URL if found, None otherwise
        """
        if not isinstance(media_item, dict):
            return None
        
        # Check for direct image URL
        if "image_url" in media_item:
            return media_item["image_url"]
        
        # Check for image_versions2 (usually has candidates sorted by quality)
        if "image_versions2" in media_item:
            candidates = media_item["image_versions2"].get("candidates", [])
            if candidates:
                # Return the first (usually highest quality) or largest
                return candidates[0].get("url")
        
        # Check for thumbnail in videos
        if "cover_photo" in media_item:
            return media_item["cover_photo"].get("url")
        
        if "thumbnail_url" in media_item:
            return media_item["thumbnail_url"]
        
        # For videos, try to get first frame or thumbnail
        if "video_versions" in media_item:
            video_versions = media_item.get("video_versions", [])
            if video_versions:
                # Videos might have a cover image
                return video_versions[0].get("cover_image_url") or video_versions[0].get("thumbnail_url")
        
        # Check carousel media (get first item's image)
        if "carousel_media" in media_item:
            carousel_items = media_item.get("carousel_media", [])
            if carousel_items:
                return self.extract_image_url(carousel_items[0])
        
        return None
    
    def format_media_item(self, media_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format media item to only include text and image_url properties.
        
        Args:
            media_item: Media item dictionary (post, video, reel)
            
        Returns:
            Dictionary with only 'text' and 'image_url' keys
        """
        if not isinstance(media_item, dict):
            return {"text": "", "image_url": None}
        
        # Extract text/caption - handle nested caption structure
        text = ""
        if "caption" in media_item:
            caption = media_item["caption"]
            if isinstance(caption, dict):
                text = caption.get("text", "")
            else:
                text = str(caption)
        elif "text" in media_item:
            text = media_item["text"]
        
        if not text:
            text = ""
        
        # Extract image URL
        image_url = self.extract_image_url(media_item)
        
        return {
            "text": str(text) if text else "",
            "image_url": image_url
        }
    
    def format_media_list(self, media_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format a list of media items to only include text and image_url properties.
        
        Args:
            media_items: List of media item dictionaries
            
        Returns:
            List of dictionaries with only 'text' and 'image_url' keys
        """
        return [self.format_media_item(item) for item in media_items]
    
    def extract_media_urls(self, post_data: Dict[str, Any]) -> List[str]:
        """
        Extract media URLs from post data.
        
        Args:
            post_data: Post data from API
            
        Returns:
            List of media URLs (videos/images)
        """
        media_urls = []
        
        # Handle different response structures
        if isinstance(post_data, dict):
            # Check for video URLs first (videos take priority)
            if "video_versions" in post_data:
                video_versions = post_data["video_versions"]
                if isinstance(video_versions, list) and len(video_versions) > 0:
                    # Get the first video URL (highest quality usually)
                    first_video = video_versions[0]
                    if "url" in first_video:
                        media_urls.append(first_video["url"])
                        # Return early if we found a video (don't add images)
                        return media_urls
            
            # Check for direct video URL
            if "video_url" in post_data:
                media_urls.append(post_data["video_url"])
                return media_urls
            
            # Check for image URLs (only if no video found)
            if "image_url" in post_data:
                media_urls.append(post_data["image_url"])
            if "image_versions2" in post_data:
                candidates = post_data["image_versions2"].get("candidates", [])
                if candidates:
                    # Get the first (highest quality) image
                    if "url" in candidates[0]:
                        media_urls.append(candidates[0]["url"])
            
            # Check for carousel (multiple media)
            if "carousel_media" in post_data:
                for item in post_data["carousel_media"]:
                    if "video_versions" in item:
                        video_versions = item["video_versions"]
                        if isinstance(video_versions, list) and len(video_versions) > 0:
                            if "url" in video_versions[0]:
                                media_urls.append(video_versions[0]["url"])
                    elif "image_versions2" in item:
                        candidates = item["image_versions2"].get("candidates", [])
                        if candidates and "url" in candidates[0]:
                            media_urls.append(candidates[0]["url"])
            
            # Generic data field
            if "data" in post_data:
                return self.extract_media_urls(post_data["data"])
        
        return media_urls
    
    def extract_video_url(self, media_item: Dict[str, Any]) -> Optional[str]:
        """
        Extract the first video URL from video_versions array.
        
        Args:
            media_item: Media item dictionary (post, video, reel)
            
        Returns:
            Video URL if found, None otherwise
        """
        if not isinstance(media_item, dict):
            return None
        
        # Check for video_versions array
        if "video_versions" in media_item:
            video_versions = media_item["video_versions"]
            if isinstance(video_versions, list) and len(video_versions) > 0:
                first_video = video_versions[0]
                if "url" in first_video:
                    return first_video["url"]
        
        # Check for direct video_url
        if "video_url" in media_item:
            return media_item["video_url"]
        
        return None
    
    def get_video_feed(self, user_id: str, next_max_id: Optional[str] = None, max_items: Optional[int] = None) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get all videos from a user's feed with pagination support.
        Continues fetching until no data or duplicates are found.
        
        Args:
            user_id: Instagram user ID
            next_max_id: Pagination cursor for next page
            max_items: Maximum number of items to fetch (None for all available)
            
        Returns:
            Tuple of (list of video posts, next_max_id for pagination)
        """
        all_videos = []
        seen_ids = set()  # Track video IDs to detect duplicates
        current_max_id = next_max_id
        max_pages = 50  # Safety limit to prevent infinite loops
        
        logger.info(f"Starting video feed pagination for user_id={user_id}, initial_next_max_id={next_max_id}, max_items={max_items}")
        
        for page in range(max_pages):
            logger.info(f"Video feed pagination - Page {page + 1}/{max_pages} | Current next_max_id: {current_max_id} | Total videos so far: {len(all_videos)}")
            
            # Rate limiting: Add delay between API calls (except for first page)
            if page > 0:
                delay = 3  # 3 seconds delay between pagination requests
                logger.info(f"Rate limiting: Waiting {delay} seconds before next API call...")
                time.sleep(delay)
            
            response = self.client.get_all_video(user_id, current_max_id)
            
            # Extract list from response (structure may vary)
            videos = []
            if isinstance(response, list):
                videos = response
            elif isinstance(response, dict):
                # Check for nested data.items structure first
                if "data" in response and isinstance(response["data"], dict):
                    data = response["data"]
                    if "items" in data and isinstance(data["items"], list):
                        items = data["items"]
                        # Extract media from items if they have a 'media' key
                        videos = []
                        for item in items:
                            if isinstance(item, dict):
                                if "media" in item:
                                    videos.append(item["media"])
                                else:
                                    videos.append(item)
                    elif isinstance(data, list):
                        videos = data
                elif "data" in response and isinstance(response["data"], list):
                    videos = response["data"]
                elif "videos" in response:
                    videos = response["videos"]
                elif "items" in response:
                    items = response["items"]
                    if isinstance(items, list):
                        # Extract media from items if they have a 'media' key
                        videos = []
                        for item in items:
                            if isinstance(item, dict):
                                if "media" in item:
                                    videos.append(item["media"])
                                else:
                                    videos.append(item)
                elif "posts" in response:
                    videos = response["posts"]
            
            # Process videos from this response and check for duplicates
            if videos:
                # Filter out duplicates based on title/text and image URL
                new_videos = []
                duplicate_found = False
                
                for video in videos:
                    # Extract title/text and image URL for duplicate detection
                    video_text = ""
                    video_image_url = None
                    
                    if isinstance(video, dict):
                        # Get text/caption
                        if "caption" in video:
                            caption = video["caption"]
                            if isinstance(caption, dict):
                                video_text = caption.get("text", "")
                            else:
                                video_text = str(caption)
                        elif "text" in video:
                            video_text = video["text"]
                        
                        # Get image URL (thumbnail)
                        video_image_url = self.extract_image_url(video)
                    
                    # Check for duplicates by text and image URL
                    is_duplicate = False
                    if video_text:
                        text_key = video_text.strip()[:100]  # Use first 100 chars as key
                        if text_key in seen_ids:
                            is_duplicate = True
                            duplicate_found = True
                        else:
                            seen_ids.add(text_key)
                    
                    if not is_duplicate and video_image_url:
                        if video_image_url in seen_ids:
                            is_duplicate = True
                            duplicate_found = True
                        else:
                            seen_ids.add(video_image_url)
                    
                    # Also check by video ID as fallback
                    if not is_duplicate:
                        video_id = None
                        if isinstance(video, dict):
                            video_id = video.get("id") or video.get("pk") or video.get("media_id") or video.get("code")
                        
                        if video_id:
                            video_id_str = f"id_{video_id}"
                            if video_id_str in seen_ids:
                                is_duplicate = True
                                duplicate_found = True
                            else:
                                seen_ids.add(video_id_str)
                    
                    if not is_duplicate:
                        new_videos.append(video)
                
                # If we found duplicates and no new videos, stop pagination
                if duplicate_found and not new_videos:
                    logger.info(f"Video feed pagination - Page {page + 1}: Found duplicates, no new videos. Stopping pagination.")
                    break
                
                logger.info(f"Video feed pagination - Page {page + 1}: Found {len(videos)} videos, {len(new_videos)} new videos (after duplicate check), Total: {len(all_videos) + len(new_videos)}")
                all_videos.extend(new_videos)
            
            # Check if we have enough items
            if max_items and len(all_videos) >= max_items:
                all_videos = all_videos[:max_items]
                break
            
            # Extract next_max_id from response - check all possible locations
            next_max_id = None
            if isinstance(response, dict):
                # Check top level first
                next_max_id = response.get("next_max_id")
                
                # Check in data.paging_info (common location)
                if not next_max_id and "data" in response and isinstance(response["data"], dict):
                    data = response["data"]
                    paging_info = data.get("paging_info", {})
                    if isinstance(paging_info, dict):
                        next_max_id = paging_info.get("max_id") or paging_info.get("next_max_id")
                    
                    # Also check if next_max_id is directly in data
                    if not next_max_id:
                        next_max_id = data.get("next_max_id") or data.get("max_id")
                
                # Check in pagination object
                if not next_max_id:
                    pagination = response.get("pagination", {})
                    if isinstance(pagination, dict):
                        next_max_id = pagination.get("next_max_id") or pagination.get("next_cursor") or pagination.get("max_id")
            
            # Stop pagination if no next_max_id found (no more pages)
            if not next_max_id:
                logger.info(f"Video feed pagination - Page {page + 1}: No next_max_id found. Stopping pagination. Total videos collected: {len(all_videos)}")
                break
            
            logger.info(f"Video feed pagination - Page {page + 1}: Found next_max_id={next_max_id}. Continuing to next page.")
            # Use the next_max_id from response for next request
            current_max_id = next_max_id
        
        logger.info(f"Video feed pagination completed. Total videos: {len(all_videos)}, Final next_max_id: {current_max_id}")
        return all_videos, current_max_id
    
    def get_user_reels(self, user_id: str, include_feed_video: bool = True) -> List[Dict[str, Any]]:
        """
        Get user reels.
        
        Args:
            user_id: Instagram user ID
            include_feed_video: Whether to include feed videos
            
        Returns:
            List of reel posts
        """
        logger.info(f"Getting user reels for user_id={user_id}, include_feed_video={include_feed_video}")
        try:
            # Rate limiting: Add delay before API call
            delay = 2  # 2 seconds delay before reels API call
            logger.info(f"Rate limiting: Waiting {delay} seconds before reels API call...")
            time.sleep(delay)
            
            response = self.client.get_reels(user_id, include_feed_video)
            
            # Extract list from response (structure may vary)
            result = []
            if isinstance(response, list):
                # Ensure all items are dicts
                result = [item for item in response if isinstance(item, dict)]
            elif isinstance(response, dict):
                # Check for nested data.items structure first (most common)
                if "data" in response and isinstance(response["data"], dict):
                    data = response["data"]
                    if "items" in data and isinstance(data["items"], list):
                        items = data["items"]
                        # Extract media from items if they have a 'media' key
                        for item in items:
                            if isinstance(item, dict):
                                # If item has 'media' key, use that, otherwise use item directly
                                if "media" in item:
                                    result.append(item["media"])
                                else:
                                    result.append(item)
                    elif isinstance(data, list):
                        result = [item for item in data if isinstance(item, dict)]
                # Check for direct data as list
                elif "data" in response and isinstance(response["data"], list):
                    data = response["data"]
                    result = [item for item in data if isinstance(item, dict)]
                # Other common structures
                elif "reels" in response:
                    reels = response["reels"]
                    if isinstance(reels, list):
                        result = [item for item in reels if isinstance(item, dict)]
                elif "items" in response:
                    items = response["items"]
                    if isinstance(items, list):
                        result = [item for item in items if isinstance(item, dict)]
                elif "videos" in response:
                    videos = response["videos"]
                    if isinstance(videos, list):
                        result = [item for item in videos if isinstance(item, dict)]
            
            logger.info(f"Successfully retrieved {len(result)} reels for user_id={user_id}")
            return result
        except Exception as e:
            # Log error but return empty list
            logger.error(f"Error getting user reels for user_id={user_id}: {str(e)}", exc_info=True)
        
        return []

