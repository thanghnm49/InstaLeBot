"""Instagram API wrapper service."""
from typing import Dict, Any, List, Optional
from services.rapidapi import RapidAPIClient
import re


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
        
        Args:
            user_id: Instagram user ID
            next_max_id: Pagination cursor for next page
            max_items: Maximum number of items to fetch (None for all available)
            
        Returns:
            Tuple of (list of posts, next_max_id for pagination)
        """
        all_posts = []
        current_max_id = next_max_id
        max_pages = 10  # Limit to prevent infinite loops
        
        for page in range(max_pages):
            feed_data = self.client.get_feed(user_id, current_max_id)
            
            # Extract posts from feed
            posts = []
            if isinstance(feed_data, list):
                posts = feed_data
            elif isinstance(feed_data, dict):
                if "data" in feed_data:
                    posts = feed_data["data"]
                elif "items" in feed_data:
                    posts = feed_data["items"]
                elif "posts" in feed_data:
                    posts = feed_data["posts"]
                elif "feed" in feed_data:
                    posts = feed_data["feed"]
                elif "user" in feed_data and "edge_owner_to_timeline_media" in feed_data["user"]:
                    edges = feed_data["user"]["edge_owner_to_timeline_media"].get("edges", [])
                    posts = [edge.get("node", {}) for edge in edges]
            
            all_posts.extend(posts)
            
            # Check if we have enough items
            if max_items and len(all_posts) >= max_items:
                all_posts = all_posts[:max_items]
                break
            
            # Check for next page
            next_max_id = None
            if isinstance(feed_data, dict):
                next_max_id = feed_data.get("next_max_id") or feed_data.get("next_cursor") or feed_data.get("pagination", {}).get("next_max_id")
            
            if not next_max_id:
                break  # No more pages
            
            current_max_id = next_max_id
        
        return all_posts, next_max_id
    
    def get_following_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get following list for a user.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            List of users being followed
        """
        response = self.client.get_following(user_id)
        # Extract list from response (structure may vary)
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            # Common response structures
            if "data" in response:
                return response["data"]
            elif "following" in response:
                return response["following"]
            elif "users" in response:
                return response["users"]
        return []
    
    def get_followers_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get followers list for a user.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            List of followers
        """
        response = self.client.get_followers(user_id)
        # Extract list from response (structure may vary)
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            # Common response structures
            if "data" in response:
                return response["data"]
            elif "followers" in response:
                return response["followers"]
            elif "users" in response:
                return response["users"]
        return []
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user profile information.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            User profile data
        """
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
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            # Common response structures
            if "data" in response:
                return response["data"]
            elif "users" in response:
                return response["users"]
            elif "recommendations" in response:
                return response["recommendations"]
            elif "similar_accounts" in response:
                return response["similar_accounts"]
            elif "chaining" in response:
                return response["chaining"]
        return []
    
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
            # Check for video URLs
            if "video_url" in post_data:
                media_urls.append(post_data["video_url"])
            if "video_versions" in post_data:
                for video in post_data["video_versions"]:
                    if "url" in video:
                        media_urls.append(video["url"])
            
            # Check for image URLs
            if "image_url" in post_data:
                media_urls.append(post_data["image_url"])
            if "image_versions2" in post_data:
                candidates = post_data["image_versions2"].get("candidates", [])
                for img in candidates:
                    if "url" in img:
                        media_urls.append(img["url"])
            
            # Check for carousel (multiple media)
            if "carousel_media" in post_data:
                for item in post_data["carousel_media"]:
                    if "video_versions" in item:
                        for video in item["video_versions"]:
                            if "url" in video:
                                media_urls.append(video["url"])
                    if "image_versions2" in item:
                        candidates = item["image_versions2"].get("candidates", [])
                        for img in candidates:
                            if "url" in img:
                                media_urls.append(img["url"])
            
            # Generic data field
            if "data" in post_data:
                return self.extract_media_urls(post_data["data"])
        
        return media_urls
    
    def get_video_feed(self, user_id: str, next_max_id: Optional[str] = None, max_items: Optional[int] = None) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get all videos from a user's feed with pagination support.
        
        Args:
            user_id: Instagram user ID
            next_max_id: Pagination cursor for next page
            max_items: Maximum number of items to fetch (None for all available)
            
        Returns:
            Tuple of (list of video posts, next_max_id for pagination)
        """
        all_videos = []
        current_max_id = next_max_id
        max_pages = 10  # Limit to prevent infinite loops
        
        for page in range(max_pages):
            response = self.client.get_all_video(user_id, current_max_id)
            
            # Extract list from response (structure may vary)
            videos = []
            if isinstance(response, list):
                videos = response
            elif isinstance(response, dict):
                # Common response structures
                if "data" in response:
                    videos = response["data"]
                elif "videos" in response:
                    videos = response["videos"]
                elif "items" in response:
                    videos = response["items"]
                elif "posts" in response:
                    videos = response["posts"]
            
            all_videos.extend(videos)
            
            # Check if we have enough items
            if max_items and len(all_videos) >= max_items:
                all_videos = all_videos[:max_items]
                break
            
            # Check for next page
            next_max_id = None
            if isinstance(response, dict):
                next_max_id = response.get("next_max_id") or response.get("next_cursor") or response.get("pagination", {}).get("next_max_id")
            
            if not next_max_id:
                break  # No more pages
            
            current_max_id = next_max_id
        
        return all_videos, next_max_id
    
    def get_user_reels(self, user_id: str, include_feed_video: bool = True) -> List[Dict[str, Any]]:
        """
        Get user reels.
        
        Args:
            user_id: Instagram user ID
            include_feed_video: Whether to include feed videos
            
        Returns:
            List of reel posts
        """
        response = self.client.get_reels(user_id, include_feed_video)
        # Extract list from response (structure may vary)
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            # Common response structures
            if "data" in response:
                return response["data"]
            elif "reels" in response:
                return response["reels"]
            elif "items" in response:
                return response["items"]
            elif "videos" in response:
                return response["videos"]
        return []

