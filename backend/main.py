import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request,  HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv
import logging
from vector_database import RAGSystem
import json
from twilio.rest import Client
from openai import OpenAI
import json

from ai_agent import create_assistant, get_or_create_thread
from helper import load_access_token, send_instagram_message, send_facebook_message

from aipolabs import ACI

aci = ACI()

LINKED_ACCOUNT_OWNER_ID = os.getenv("LINKED_ACCOUNT_OWNER_ID", "")
if not LINKED_ACCOUNT_OWNER_ID:
    raise ValueError("LINKED_ACCOUNT_OWNER_ID is not set")

ACI_CLIENT = ACI(api_key=os.getenv("AIPOLABS_ACI_API_KEY"))

UPDATE = ACI_CLIENT.functions.get_definition("GOOGLE_CALENDAR__EVENTS_UPDATE")
RESERVE = ACI_CLIENT.functions.get_definition("GOOGLE_CALENDAR__EVENTS_INSERT")
DELETE = ACI_CLIENT.functions.get_definition("GOOGLE_CALENDAR__EVENTS_DELETE")
    

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

user_access_token_ig = load_access_token()

load_dotenv()
# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') # requires OpenAI Realtime API Access
PORT = int(os.getenv('PORT', 5050))
rag = RAGSystem(vector_store_name="Restaurant Details")
vector_store_id = rag.get_vector_store_id()
LINKED_ACCOUNT_OWNER_ID = os.getenv("LINKED_ACCOUNT_OWNER_ID")
if not LINKED_ACCOUNT_OWNER_ID:
    raise ValueError("LINKED_ACCOUNT_OWNER_ID is not set")
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_CLIENT = Client(account_sid, auth_token)
OPENAI_CLIENT = OpenAI(api_key= OPENAI_API_KEY)

LOG_EVENT_TYPES = [
  'response.content.done', 'rate_limits.updated', 'response.done',
  'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
  'input_audio_buffer.speech_started', 'response.create', 'session.created'
]

app = FastAPI()
if not OPENAI_API_KEY:
  raise ValueError('Missing the OpenAI API key. Please set it in the .env file.') 

assistant = create_assistant()

@app.get("/", response_class=HTMLResponse)
async def index_page():
    return "<html><body><h1>Twilio Media Stream Server is running!</h1></body></html>"
    
#Instagram API ----------------------------------------------------------

@app.api_route("/privacy_policy", methods= ["GET", "POST"])
def privacy_policy():
    with open("privacy_policy.html", "r") as f:
        privacy_policy_html = f.read()

    return privacy_policy_html
    
@app.get("/fb_webhook")
async def webhook(request: Request):
    return int(request.query_params.get("hub.challenge"))

@app.post("/fb_webhook")
async def webhook(request: Request):
    data = await request.json()
    
    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            sender_id = messaging["sender"]["id"]
            print(f"\n {sender_id} \n")

            # Check if message exists
            message = messaging.get("message")

            # Process actual user message
            message_text = message["text"]
            thread_id = get_or_create_thread(sender_id)
            
            # Send message to OpenAI
            OPENAI_CLIENT.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message_text
            )
            
            run = OPENAI_CLIENT.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=assistant.id,
            )

            if run.status == 'completed':
                messages = OPENAI_CLIENT.beta.threads.messages.list(
                    thread_id=thread_id
                )
                print (run.status)
                assistant_response = next(
                    (msg.content[0].text.value for msg in messages.data if msg.role == "assistant"),
                    "Sorry, I didn't get that."
                )
                print(f"\n{assistant_response}\n")
                send_facebook_message(sender_id, assistant_response)
                
            elif run.status == 'requires_action':
                tool_outputs = []
                for tool in run.required_action.submit_tool_outputs.tool_calls:
                    if tool.function.name == "GOOGLE_CALENDAR__EVENTS_INSERT":
                        try:
                            arguments = json.loads(tool.function.arguments)
                            aci_result = aci.functions.execute(
                                tool.function.name,
                                arguments,
                                linked_account_owner_id = LINKED_ACCOUNT_OWNER_ID
                            )
                            tool_outputs.append({
                                "tool_call_id": tool.id,
                                "output": aci_result.model_dump_json()
                            })
                        except Exception as e:
                            print(f"Error executing ACI Google Calendar: {e}")
                            tool_outputs.append({
                                "tool_call_id": tool.id,
                                "output": f"Error{e}"
                            })
                    
                if tool_outputs:
                    try:
                        run = OPENAI_CLIENT.beta.threads.runs.submit_tool_outputs_and_poll(thread_id=thread_id,
                        run_id = run.id,
                        tool_outputs= tool_outputs)
                        
                        print("Tool outputs submitted successfully.")
                    except Exception as e:
                        print("Failed to submit tool outputs:", e)
                else:
                    print("No tool outputs to submit")
                    
                if run.status == "completed":
                    messages = OPENAI_CLIENT.beta.threads.messages.list(thread_id=thread_id)
                    assistant_response = next(
                        (msg.content[0].text.value for msg in messages.data if msg.role == "assistant"),
                        "Sorry, I didn't get that."
                    )
                    print(f"\n{assistant_response}\n")
                    send_facebook_message(sender_id, assistant_response)
                else:
                    print(run.status)
            else: 
                print(run.status)
                                           
@app.api_route("/webhook", methods=["GET"])
async def webhook(request: Request):
    return int(request.query_params.get("hub.challenge"))

@app.api_route("/webhook", methods=["POST"])
async def webhook(request: Request):
    data = await request.json()
    
    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            sender_id = messaging["sender"]["id"]
            print(f"\n {sender_id} \n")

            # Check if message exists
            message = messaging.get("message")

            # Process actual user message
            message_text = message["text"]
            thread_id = get_or_create_thread(sender_id)
            
            # Send message to OpenAI
            OPENAI_CLIENT.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message_text
            )
            
            run = OPENAI_CLIENT.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=assistant.id,
            )

            if run.status == 'completed':
                messages = OPENAI_CLIENT.beta.threads.messages.list(
                    thread_id=thread_id
                )
                print (run.status)
                assistant_response = next(
                    (msg.content[0].text.value for msg in messages.data if msg.role == "assistant"),
                    "Sorry, I didn't get that."
                )
                print(f"\n{assistant_response}\n")
                send_instagram_message(user_access_token_ig,sender_id, assistant_response)
                
            elif run.status == 'requires_action':
                tool_outputs = []
                for tool in run.required_action.submit_tool_outputs.tool_calls:
                    if tool.function.name == "GOOGLE_CALENDAR__EVENTS_INSERT":
                        try:
                            arguments = json.loads(tool.function.arguments)
                            aci_result = aci.functions.execute(
                                tool.function.name,
                                arguments,
                                linked_account_owner_id = LINKED_ACCOUNT_OWNER_ID
                            )
                            tool_outputs.append({
                                "tool_call_id": tool.id,
                                "output": aci_result.model_dump_json()
                            })
                        except Exception as e:
                            print(f"Error executing ACI Google Calendar: {e}")
                            tool_outputs.append({
                                "tool_call_id": tool.id,
                                "output": f"Error{e}"
                            })
                    
                if tool_outputs:
                    try:
                        run = OPENAI_CLIENT.beta.threads.runs.submit_tool_outputs_and_poll(thread_id=thread_id,
                        run_id = run.id,
                        tool_outputs= tool_outputs)
                        
                        print("Tool outputs submitted successfully.")
                    except Exception as e:
                        print("Failed to submit tool outputs:", e)
                else:
                    print("No tool outputs to submit")
                    
                if run.status == "completed":
                    messages = OPENAI_CLIENT.beta.threads.messages.list(thread_id=thread_id)
                    assistant_response = next(
                        (msg.content[0].text.value for msg in messages.data if msg.role == "assistant"),
                        "Sorry, I didn't get that."
                    )
                    print(f"\n{assistant_response}\n")
                    send_instagram_message(user_access_token_ig,sender_id, assistant_response)
                else:
                    print(run.status)
            else: 
                print(run.status)


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=PORT)
