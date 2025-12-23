"""RapidAPI client for making API requests."""
import requests
from typing import Dict, Any, Optional
import time
import logging
import json
from config import RAPIDAPI_BASE_URL, RAPIDAPI_HEADERS

# Get logger for this module
logger = logging.getLogger(__name__)

# Ensure logger propagates to root logger (so it uses the handlers configured in bot.py)
logger.propagate = True
# Set level to ensure it logs
logger.setLevel(logging.INFO)


def _ensure_logger_configured():
    """Ensure logger has handlers by checking root logger."""
    root_logger = logging.getLogger()
    if root_logger.handlers and not logger.handlers:
        # Root logger has handlers, ensure our logger uses them via propagation
        logger.propagate = True
        logger.setLevel(logging.INFO)
    
    # Always log to root logger as well to ensure it's captured
    return root_logger


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
        
        # Log API request with full URL and parameters
        params_str = json.dumps(params, ensure_ascii=False) if params else "{}"
        full_url = f"{url}?{params_str}" if params else url
        
        # Ensure logger is properly configured (set level if not already set)
        if logger.level == 0:  # NOTSET
            logger.setLevel(logging.INFO)
        
        # Ensure logger is configured and get root logger
        root_logger = _ensure_logger_configured()
        
        # Log request - ensure it's written
        request_log = f"API Request: GET {endpoint} | URL: {full_url} | Params: {params_str}"
        
        # Log to root logger directly (most reliable way)
        if root_logger.handlers:
            root_logger.info(f"[RapidAPI] {request_log}")
        # Also log to module logger (for propagation)
        logger.info(request_log)
        
        # Force flush all handlers to ensure immediate write
        for handler in root_logger.handlers:
            try:
                handler.flush()
            except:
                pass
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                # Try to parse JSON
                try:
                    response_data = response.json()
                    
                    # Log API response (truncate if too large)
                    response_str = json.dumps(response_data, ensure_ascii=False)
                    response_size = len(json.dumps(response_data, ensure_ascii=False))
                    if len(response_str) > 1000:
                        response_str = response_str[:1000] + "... [truncated]"
                    
                    # Ensure logger is configured and get root logger
                    root_logger = _ensure_logger_configured()
                    
                    # Log response - ensure it's written
                    response_log = f"API Response: GET {endpoint} | Status: {response.status_code} | Response size: {response_size} bytes | Preview: {response_str[:200]}"
                    
                    # Log to root logger directly (most reliable way)
                    if root_logger.handlers:
                        root_logger.info(f"[RapidAPI] {response_log}")
                    # Also log to module logger (for propagation)
                    logger.info(response_log)
                    
                    # Force flush all handlers to ensure immediate write
                    for handler in root_logger.handlers:
                        try:
                            handler.flush()
                        except:
                            pass
                    
                    return response_data
                except ValueError as json_error:
                    logger.error(f"API Response Error: GET {endpoint} | Invalid JSON: {str(json_error)}")
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
            user_id: Instagram user ID (must be numeric, not username)
            
        Returns:
            User profile data
            
        Raises:
            ValueError: If user_id is not numeric (should use get_user_id_by_username first)
        """
        # Validate that user_id is numeric - never accept username here
        if not user_id.isdigit():
            raise ValueError(
                f"Profile API only accepts numeric user IDs, not usernames. "
                f"Received: '{user_id}'. Use get_user_id_by_username() first to convert username to user ID."
            )
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

