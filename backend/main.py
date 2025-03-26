from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
import uvicorn
from tests.test_routes import router as test_router
#from services import agent
from routes import call_handling
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client

app = FastAPI(title = "ARQ API")
twilio_service = call_handling.TwilioVoiceService


@app.post("/start_conversation")
async def start_conversation(background_tasks: BackgroundTasks):
    """
    API endpoint to start the conversational loop in the background.
    """
    #background_tasks.add_task(conversation_loop)
    return {"message": "Conversation loop started in the background."}
  
@app.api_route("/voice", methods=["GET", "POST"])
async def voice(request: Request):
    """
    Handles inbound voice requests from Twilio. It retrieves the caller's city from the request data,
    generates a TwiML response, and returns it.
    """

    # Generate the TwiML response with the service
    response_str = twilio_service.generate_voice_response("London")
    return response_str

def start_server():
  uvicorn.run(app, host = "localhost", port = 8000)
  
if __name__ == "__main__":
  start_server()


