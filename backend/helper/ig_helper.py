import json
import requests

IG_TOKEN_PATH = "ig_token.json"
INSTAGRAM_API_URL = "https://graph.instagram.com/v21.0/me/messages"

def load_access_token(path=IG_TOKEN_PATH):
    """
    Load the Instagram access token from a JSON file.
    """
    with open(path, "r") as f:
        return json.load(f)["access_token"]


def send_instagram_message(user_access_token, recipient_id, message_text):
    """
    Send a text message to an Instagram user via the Messaging API.
    """
    headers = {
        "Authorization": f"Bearer {user_access_token}",
        "Content-Type": "application/json"
    }
    json_body = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    response = requests.post(INSTAGRAM_API_URL, headers=headers, json=json_body)
    data = response.json()
    print("\n📨 Message Send Response:")
    print(json.dumps(data, indent=4))
    return data

def reply_to_instagram_comment(comment_id, message_text, access_token=None):
    """
    Reply to an Instagram comment using the Facebook Graph API.
    """
    if not access_token:
        access_token = load_access_token()
        
    url = f"https://graph.facebook.com/v21.0/{comment_id}/replies"
    print(comment_id)
    
    payload = {
        "message": message_text,
        "access_token":'EAAQp5L2eW58BO1D8EtbXBEuImzUhCmk8iaiRdVTrmCk7YKYRl6CuilZBFzqpPyRcgvcbB13AHb8idOxyZAHb8Kmzw5WaEZB6W1aauNjCVkccIHMBI6wWCdIkXZB6WByxUbg1r3e9KytmZCkDSS8OvtSKEk00F7nHjn9GmK7lO5a2Y6TyfLBz1DIJWOX3L0ZBD7n09Kq5n7zHPxtiAMpLaOlu96VjEKl2CZARZAYZD'
    }
    
    # Notice we're using params instead of data here
    response = requests.post(url, params=payload)
    data = response.json()
    print(json.dumps(data, indent=4))
    
    return data