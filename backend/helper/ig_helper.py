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
<<<<<<< HEAD
    
=======
>>>>>>> a2e1a080bb2a7a9a8c9aad2041d6052da54855cb
    response = requests.post(INSTAGRAM_API_URL, headers=headers, json=json_body)
    data = response.json()
    print("\n📨 Message Send Response:")
    print(json.dumps(data, indent=4))
    return data