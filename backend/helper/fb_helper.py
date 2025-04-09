
"""
Facebook API Client Module

This module provides a clean, reusable interface for interacting with the Facebook Graph API.
It handles authentication, request formatting, and error handling in a consistent manner.
"""

import os
import requests
import json
import logging
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('facebook_api')

class FacebookApiClient:
    """A client for interacting with the Facebook Graph API."""
    
    # Current Facebook Graph API version
    API_VERSION = "v21.0"
    
    # Base URLs for different API endpoints
    GRAPH_API_BASE_URL = "https://graph.facebook.com"
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize the Facebook API client.
        
        Args:
            access_token: Optional Facebook access token. If not provided,
                          it will be loaded from the FACEBOOK_ACCESS_TOKEN environment variable.
        """
        # Load environment variables if they haven't been loaded already
        load_dotenv()
        
        # Use provided token or get from environment
        self.access_token = access_token or os.getenv("FACEBOOK_ACCESS_TOKEN")
        
        if not self.access_token:
            logger.error("No Facebook access token found. Set FACEBOOK_ACCESS_TOKEN in .env file or pass as parameter.")
            raise ValueError("Facebook access token is required")
            
        # Default headers for all requests
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build a full URL for the Facebook Graph API.
        
        Args:
            endpoint: The API endpoint path.
            
        Returns:
            The complete URL including the API version.
        """
        return f"{self.GRAPH_API_BASE_URL}/{self.API_VERSION}/{endpoint}"
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the Facebook Graph API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: JSON body data for POST requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Ensure access token is included in params
        params = params or {}
        if 'access_token' not in params:
            params['access_token'] = self.access_token
            
        url = self._build_url(endpoint)
        
        try:
            logger.debug(f"Making {method} request to {url}")
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            # If we got a JSON response with an error, include it in the exception
            if hasattr(response, 'json'):
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        logger.error(f"API error: {error_data['error']}")
                except ValueError:
                    # Response wasn't valid JSON
                    pass
            raise
    
    def get_page_posts(self, page_id: str, fields: Optional[str] = None, limit: int = 25) -> Dict[str, Any]:
        """
        Get posts from a Facebook page.
        
        Args:
            page_id: The ID of the Facebook page
            fields: Comma-separated list of fields to request. If None, a default set will be used.
            limit: Maximum number of posts to retrieve
            
        Returns:
            JSON response containing page posts
        """
        if fields is None:
            fields = "message,created_time,comments.limit(10){message,from,created_time}"
            
        params = {
            "fields": fields,
            "limit": limit
        }
        
        response = self._make_request("GET", f"{page_id}/posts", params=params)
        
        logger.info(f"Retrieved {len(response.get('data', []))} posts from page {page_id}")
        return response
    
    def send_message(self, recipient_id: str, message_text: str, messaging_type: str = "RESPONSE") -> Optional[Dict[str, Any]]:
        """
        Send a text message to a user via the Facebook Messaging API.
        
        Args:
            recipient_id: The ID of the recipient
            message_text: The text content of the message
            messaging_type: The messaging type (RESPONSE, UPDATE, MESSAGE_TAG)
            
        Returns:
            JSON response if successful, None if failed
        """
        endpoint = "me/messages"
        
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
            "messaging_type": messaging_type
        }
        
        try:
            response = self._make_request("POST", endpoint, data=data)
            logger.info(f"Message sent to recipient {recipient_id}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message: {str(e)}")
            return None

    def pretty_print_response(self, response_data: Dict[str, Any], label: str = "API Response"):
        """
        Pretty print an API response for debugging purposes.
        
        Args:
            response_data: The response data to print
            label: A label to identify what response is being printed
        """
        print(f"\n📊 {label}:")
        print(json.dumps(response_data, indent=4))


# Example usage
if __name__ == "__main__":
    # Create client
    client = FacebookApiClient()
    
    # Example: Get posts from a page
    try:
        PAGE_ID = "your_page_id"  # Replace with actual page ID
        posts = client.get_page_posts(PAGE_ID)
        client.pretty_print_response(posts, "Page Posts")
    except Exception as e:
        logger.error(f"Error getting page posts: {str(e)}")
    
    # Example: Send a message
    try:
        RECIPIENT_ID = "recipient_id"  # Replace with actual recipient ID
        message_response = client.send_message(RECIPIENT_ID, "Hello from the refactored API client!")
        if message_response:
            client.pretty_print_response(message_response, "Message Send Response")
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")

    