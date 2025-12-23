"""RapidAPI client for making API requests."""
import requests
from typing import Dict, Any, Optional
import time
from config import RAPIDAPI_BASE_URL, RAPIDAPI_HEADERS


class RapidAPIClient:
    """Client for making requests to RapidAPI endpoints."""
    
    def __init__(self, base_url: str = RAPIDAPI_BASE_URL, headers: Dict[str, str] = None):
        """
        Initialize RapidAPI client.
        
        Args:
            base_url: Base URL for RapidAPI
            headers: Headers to include in requests
        """
        self.base_url = base_url
        self.headers = headers or RAPIDAPI_HEADERS.copy()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, retries: int = 3) -> Dict[str, Any]:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            retries: Number of retry attempts
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.RequestException: If request fails after retries
            ValueError: If resource not found or invalid response
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                # Try to parse JSON
                try:
                    return response.json()
                except ValueError as json_error:
                    raise ValueError(f"Invalid JSON response from {endpoint}: {str(json_error)}")
                    
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                
                if status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    if attempt < retries - 1:
                        time.sleep(wait_time)
                        continue
                    raise requests.exceptions.RequestException(
                        f"Rate limit exceeded. Please try again later."
                    )
                elif status_code == 404:
                    raise ValueError(f"Resource not found: {endpoint}. Please check the user ID or URL.")
                elif status_code == 401 or status_code == 403:
                    raise ValueError(f"Authentication failed. Please check your API key.")
                elif status_code == 400:
                    raise ValueError(f"Bad request. Please check your parameters.")
                elif attempt == retries - 1:
                    raise requests.exceptions.RequestException(
                        f"HTTP {status_code} error: {str(e)}"
                    )
                time.sleep(1)
            except requests.exceptions.Timeout:
                if attempt == retries - 1:
                    raise requests.exceptions.RequestException(
                        f"Request timeout for {endpoint}. Please try again."
                    )
                time.sleep(1)
            except requests.exceptions.ConnectionError:
                if attempt == retries - 1:
                    raise requests.exceptions.RequestException(
                        f"Connection error. Please check your internet connection."
                    )
                time.sleep(1)
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    raise
                time.sleep(1)
        
        raise requests.exceptions.RequestException(f"Failed to fetch {url} after {retries} attempts")
    
    def get_feed(self, user_id: str, next_max_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user feed.
        
        Args:
            user_id: Instagram user ID
            next_max_id: Pagination cursor for next page
            
        Returns:
            Feed data
        """
        params = {"user_id": user_id}
        if next_max_id:
            params["next_max_id"] = next_max_id
        return self.get("feed", params=params)
    
    def get_following(self, user_id: str) -> Dict[str, Any]:
        """
        Get following list for a user.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            Following list data
        """
        return self.get("following", params={"user_id": user_id})
    
    def get_followers(self, user_id: str) -> Dict[str, Any]:
        """
        Get followers list for a user.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            Followers list data
        """
        return self.get("followers", params={"user_id": user_id})
    
    def get_user_id_by_username(self, username: str) -> Dict[str, Any]:
        """
        Get user ID by username.
        
        Args:
            username: Instagram username (without @)
            
        Returns:
            User ID data
        """
        return self.get("user_id_by_username", params={"username": username})
    
    def get_username_by_user_id(self, user_id: str) -> Dict[str, Any]:
        """
        Get username by user ID.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            Username data
        """
        return self.get("username_by_id", params={"user_id": user_id})
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user profile information.
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            User profile data
        """
        return self.get("profile", params={"user_id": user_id})
    
    def get_post_info(self, post_url: str) -> Dict[str, Any]:
        """
        Get post information from URL.
        
        Args:
            post_url: Instagram post/reel URL
            
        Returns:
            Post data
        """
        return self.get("post", params={"url": post_url})
    
    def get_discover_chaining(self, user_id: str) -> Dict[str, Any]:
        """
        Get similar account recommendations (discover chaining).
        
        Args:
            user_id: Instagram user ID
            
        Returns:
            Similar accounts data
        """
        return self.get("discover_chaining", params={"user_id": user_id})
    
    def get_all_video(self, user_id: str, next_max_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all videos from a user's feed.
        
        Args:
            user_id: Instagram user ID
            next_max_id: Pagination cursor for next page
            
        Returns:
            Video feed data
        """
        params = {"user_id": user_id}
        if next_max_id:
            params["next_max_id"] = next_max_id
        return self.get("all_video", params=params)
    
    def get_reels(self, user_id: str, include_feed_video: bool = True) -> Dict[str, Any]:
        """
        Get user reels.
        
        Args:
            user_id: Instagram user ID
            include_feed_video: Whether to include feed videos
            
        Returns:
            Reels data
        """
        return self.get("reels", params={
            "user_id": user_id,
            "include_feed_video": str(include_feed_video).lower()
        })

