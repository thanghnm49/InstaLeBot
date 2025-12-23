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
    
    def get_user_feed(self, user_id: str) -> Dict[str, Any]:
        """
        Get user feed.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            Feed data with posts
        """
        return self.client.get_feed(user_id)
    
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
    
    def get_video_feed(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all videos from a user's feed.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            List of video posts
        """
        response = self.client.get_all_video(user_id)
        # Extract list from response (structure may vary)
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            # Common response structures
            if "data" in response:
                return response["data"]
            elif "videos" in response:
                return response["videos"]
            elif "items" in response:
                return response["items"]
            elif "posts" in response:
                return response["posts"]
        return []
    
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

