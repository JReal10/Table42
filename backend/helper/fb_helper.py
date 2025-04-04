import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def send_facebook_message(recipient_id, message_text):
    """
    Send a text message to a user via the Facebook Messaging API.
    """
    # Get access token from environment variables
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    
    # Build URL with token
    api_url = f"https://graph.facebook.com/v21.0/me/messages?access_token={access_token}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    json_body = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=json_body)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        data = response.json()
        print("\n📨 Message Send Response:")
        print(json.dumps(data, indent=4))
        
        if "error" in data:
            print(f"Error sending message: {data['error']}")
            return None
            
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {str(e)}")
        return None