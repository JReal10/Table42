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
        resp.say('Never gonna give you up, {}!'.format(city))
        return str(resp)

# Initialize the FastAPI app
app = FastAPI(title="ARQ API")

# Create an instance of the Twilio service
twilio_service = TwilioVoiceService()

@app.api_route("/voice", methods=["GET", "POST"])
async def voice(request: Request):
    """
    Handles inbound voice requests from Twilio. It retrieves the caller's city from the request data,
    generates a TwiML response, and returns it.
    """
    # Extract the caller's city based on request method (POST sends form data, GET sends query parameters)
    if request.method == "POST":
        form_data = await request.form()
        city = form_data.get("FromCity", "there")
    else:
        city = request.query_params.get("FromCity", "there")

    # Generate the TwiML response with the service
    response_str = twilio_service.generate_voice_response(city)
    return response_str

if __name__ == "__main__":
    # Optionally send an outbound call when starting the application
    outbound_call_sid = twilio_service.send_outbound_call(
        from_number="+15558675310",
        to_number="+15017122661",
        url="http://demo.twilio.com/docs/voice.xml"
    )
    
    # Start the FastAPI server using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)
