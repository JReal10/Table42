import os
import uvicorn
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client

load_dotenv

class TwilioVoiceService:
    """
    Encapsulates Twilio client initialization and operations such as
    sending outbound calls and generating inbound voice responses.
    """
    def __init__(self):
        # Retrieve credentials from environment variables
        self.account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        self.auth_token = os.environ["TWILIO_AUTH_TOKEN"]
        self.client = Client(self.account_sid, self.auth_token)

    def send_outbound_call(self, from_number: str, to_number: str, url: str) -> str:
        """
        Initiates an outbound call and returns the call SID.
        """
        call = self.client.calls.create(
            from_=from_number,
            to=to_number,
            url=url
        )
        return call.sid

    def generate_voice_response(self, city: str) -> str:
        """
        Generates a TwiML response that speaks a message including the caller's city.
        """
        resp = VoiceResponse()
        resp.say('Never gonna give you up, {}!')
        return str(resp)


