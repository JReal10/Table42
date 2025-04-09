import json
import os
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import requests

# Constants
TOKEN_PATH = 'ig_token.json'
CONFIG_PATH = 'cwdchat_config.json'
API_VERSION = 'v21.0'
DEFAULT_SCOPES = [
    "instagram_business_basic",
    "instagram_business_content_publish",
    "instagram_business_manage_messages",
    "instagram_business_manage_comments"
]


class InstagramAuthError(Exception):
    """Custom exception for Instagram authentication errors."""
    pass


class InstagramAuth:
    """Handles Instagram API authentication and token management."""

    def __init__(self, config_path: str = CONFIG_PATH):
        """
        Initialize the Instagram authentication handler.

        Args:
            config_path: Path to the configuration file containing app credentials.
        """
        self.app_id, self.app_secret, self.redirect_uri = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Tuple[str, str, str]:
        """
        Load Instagram API configuration from a JSON file.

        Args:
            config_path: Path to the configuration file.

        Returns:
            Tuple containing app_id, app_secret, and redirect_uri.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            KeyError: If the configuration file is missing required fields.
            json.JSONDecodeError: If the configuration file is not valid JSON.
        """
        try:
            with open(config_path, 'r') as file:
                config = json.load(file)
                return config["app_id"], config["app_secret"], config["redirect_uri"]
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        except KeyError as e:
            raise KeyError(f"Missing required configuration key: {e}")

    def generate_auth_url(self, scopes: Optional[List[str]] = None) -> str:
        """
        Generate the Instagram authorization URL.

        Args:
            scopes: List of permission scopes to request. Uses default scopes if None.

        Returns:
            The authorization URL for the user to visit.
        """
        auth_scopes = scopes if scopes else DEFAULT_SCOPES
        base_url = "https://www.instagram.com/oauth/authorize"
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": ",".join(auth_scopes),
            "response_type": "code"
        }
        return f"{base_url}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_short_token(self, authorization_code: str) -> str:
        """
        Exchange an authorization code for a short-lived access token.

        Args:
            authorization_code: The authorization code obtained after user grants permission.

        Returns:
            Short-lived access token.

        Raises:
            InstagramAuthError: If the token exchange fails.
        """
        url = "https://api.instagram.com/oauth/access_token"
        form_data = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code": authorization_code
        }
        
        response = requests.post(url, data=form_data)
        
        if response.status_code != 200:
            raise InstagramAuthError(f"Failed to obtain short token: {response.text}")
            
        data = response.json()
        token = data.get("access_token")
        
        if not token:
            raise InstagramAuthError("No access_token in response")
            
        return token

    def exchange_for_long_lived_token(self, short_token: str) -> Tuple[str, int]:
        """
        Exchange a short-lived token for a long-lived access token.

        Args:
            short_token: The short-lived access token.

        Returns:
            Tuple containing (long-lived access token, expiration time in seconds).

        Raises:
            InstagramAuthError: If the token exchange fails.
        """
        url = "https://graph.instagram.com/access_token"
        payload = {
            "grant_type": "ig_exchange_token",
            "client_secret": self.app_secret,
            "access_token": short_token
        }
        
        response = requests.get(url, params=payload)
        
        if response.status_code != 200:
            raise InstagramAuthError(f"Failed to obtain long-lived token: {response.text}")
            
        data = response.json()
        token = data.get("access_token")
        expires_in = data.get("expires_in")
        
        if not token or not expires_in:
            raise InstagramAuthError("Missing token or expiration time in response")
            
        return token, expires_in

    def save_token(self, token: str, expires_in: int, token_path: str = TOKEN_PATH) -> None:
        """
        Save an access token to a file with its expiration date.

        Args:
            token: The access token to save.
            expires_in: Token expiration time in seconds.
            token_path: Path where the token should be saved.
        """
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        data = {
            "access_token": token,
            "expires_at": expires_at.isoformat()
        }
        
        with open(token_path, 'w') as f:
            json.dump(data, f, indent=4)
            
        print(f"✅ Saved access token to {token_path}")

    def load_token(self, token_path: str = TOKEN_PATH) -> Optional[str]:
        """
        Load and validate an access token from a file.

        Args:
            token_path: Path to the token file.

        Returns:
            The access token if valid, None otherwise.
        """
        if not os.path.exists(token_path):
            return None
            
        try:
            with open(token_path, 'r') as f:
                data = json.load(f)
                
            expires_at = datetime.fromisoformat(data['expires_at'])
            
            if datetime.utcnow() >= expires_at:
                print("❌ Token expired.")
                return None
                
            return data['access_token']
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Error loading token: {e}")
            return None

    def get_valid_token(self, token_path: str = TOKEN_PATH) -> Optional[str]:
        """
        Get a valid access token, either from storage or by requesting a new one.

        Args:
            token_path: Path to the token file.

        Returns:
            A valid access token if available, None otherwise.
        """
        # First try to load an existing token
        token = self.load_token(token_path)
        if token:
            return token
            
        # If no valid token is found, guide the user through authorization
        return self.interactive_authorization(token_path)

    def interactive_authorization(self, token_path: str = TOKEN_PATH) -> Optional[str]:
        """
        Guide the user through the authorization process interactively.

        Args:
            token_path: Path where the token should be saved.

        Returns:
            A valid access token if successfully obtained, None otherwise.
        """
        try:
            # Generate authorization URL
            auth_url = self.generate_auth_url()
            
            print("\n🔗 Visit this URL to authorize the Instagram app:\n")
            print(auth_url)
            
            if input("\nOpen in browser? (y/n): ").strip().lower() == 'y':
                webbrowser.open(auth_url)
                
            # Get the authorization code from the redirected URL
            redirected_url = input("\nPaste the full redirected URL after authorization:\n").strip()
            authorization_code = redirected_url.replace(self.redirect_uri + "?code=", "").split("&")[0]
            
            # Exchange for tokens
            short_token = self.exchange_code_for_short_token(authorization_code)
            long_token, expires_in = self.exchange_for_long_lived_token(short_token)
            
            # Save the token
            self.save_token(long_token, expires_in, token_path)
            
            return long_token
        except Exception as e:
            print(f"❌ Authorization failed: {e}")
            return None


def main():
    """Main function to demonstrate Instagram authentication flow."""
    try:
        # Initialize authentication handler
        auth = InstagramAuth()
        
        # Check for existing token or get a new one
        token = auth.get_valid_token()
        if not token:
            print("Failed to obtain a valid access token.")
            return
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

