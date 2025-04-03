import json
import urllib.parse
import requests
import webbrowser
import os
from datetime import datetime, timedelta

TOKEN_PATH = 'ig_token.json'

def load_instagram_config(config_path='cwdchat_config.json'):
    with open(config_path, 'r') as file:
        config = json.load(file)
    return config["app_id"], config["app_secret"], config["redirect_uri"]

def generate_instagram_auth_url(app_id, redirect_uri, scopes=None):
    if scopes is None:
        scopes = [
            "instagram_business_basic",
            "instagram_business_content_publish",
            "instagram_business_manage_messages",
            "instagram_business_manage_comments"
        ]
    base_url = "https://www.instagram.com/oauth/authorize"
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": ",".join(scopes),
        "response_type": "code"
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def exchange_code_for_short_token(app_id, app_secret, redirect_uri, authorization_code):
    url = "https://api.instagram.com/oauth/access_token"
    form_data = {
        "client_id": app_id,
        "client_secret": app_secret,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": authorization_code
    }
    response = requests.post(url, data=form_data)
    data = response.json()
    return data.get("access_token")

def exchange_for_long_lived_token(app_secret, short_token):
    url = "https://graph.instagram.com/access_token"
    payload = {
        "grant_type": "ig_exchange_token",
        "client_secret": app_secret,
        "access_token": short_token
    }
    response = requests.get(url, params=payload)
    data = response.json()
    return data.get("access_token"), data.get("expires_in")

def save_access_token(token, expires_in, path=TOKEN_PATH):
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    data = {
        "access_token": token,
        "expires_at": expires_at.isoformat()
    }
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"✅ Saved access token to {path}")

def load_access_token(path=TOKEN_PATH):
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        data = json.load(f)
    expires_at = datetime.fromisoformat(data['expires_at'])
    if datetime.utcnow() >= expires_at:
        print("❌ Token expired.")
        return None
    return data['access_token']

def test_api_call(long_access_token):
    url = "https://graph.instagram.com/v21.0/me"
    payload = {
        "fields": "id,username,name,account_type,profile_picture_url,followers_count,follows_count,media_count",
        "access_token": long_access_token
    }
    response = requests.get(url, params=payload)
    print("\n📡 API Response:")
    print(json.dumps(response.json(), indent=4))

def main():

    app_id, app_secret, redirect_uri = load_instagram_config()
    auth_url = generate_instagram_auth_url(app_id, redirect_uri)

    print("\n🔗 Visit this URL to authorize the Instagram app:\n")
    print(auth_url)

    if input("\nOpen in browser? (y/n): ").strip().lower() == 'y':
        webbrowser.open(auth_url)

    redirected_url = input("\nPaste the full redirected URL after authorization:\n").strip()
    authorization_code = redirected_url.replace(redirect_uri + "?code=", "").split("&")[0]
    short_token = exchange_code_for_short_token(app_id, app_secret, redirect_uri, authorization_code)

    if not short_token:
        print("❌ Failed to get short token.")
        return

    long_token, expires_in = exchange_for_long_lived_token(app_secret, short_token)
    if not long_token:
        print("❌ Failed to get long-lived token.")
        return

    save_access_token(long_token, expires_in)

if __name__ == "__main__":
    main()


