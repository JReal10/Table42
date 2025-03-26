from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
import uvicorn
from tests.test_routes import router as test_router
#from services import agent
from routes import call_handling
from services import agent

from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client

from services import agent

app = FastAPI(title = "ARQ API")

twilio_service = call_handling.TwilioVoiceService()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

from fastapi import BackgroundTasks

@app.api_route("/voice_api", methods=["GET", "POST"])
async def voice(request: Request, background_tasks: BackgroundTasks):
    """
    Starts a background conversation loop after Twilio call is initiated.
    """
    background_tasks.add_task(agent.conversation_turn_loop, "Initial context from /voice_api")
    
    # Generate a TwiML response to say "Please wait while we connect you..."
    response_str = twilio_service.generate_voice_response()
    return 0

def start_server():
  uvicorn.run(app, host = "localhost", port = 8000)
  
if __name__ == "__main__":
  start_server()

