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
from helper import load_access_token, send_instagram_message

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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

assistant = create_assistant()
assistant_id = assistant.id

SYSTEM_MESSAGE = (
  "You are a professional customer service agent for Flat Iron Restaurant's Soho location. Keep responses clear and concise, focusing on solving problems efficiently. Flat Iron Soho's details are as follows: Address: 17 Beak Street, London W1F 9RW. Opening Hours: Sunday to Tuesday: 12:00 PM – 10:00 PM; Wednesday to Thursday: 12:00 PM – 11:00 PM; Friday to Saturday: 12:00 PM – 11:30 PM. Menu: Mains include Flat Iron Steak, Spiced Lamb, Charcoal Chicken; Sides include Creamed Spinach, Truffle Fries, Roast Aubergine; Desserts include Salted Caramel Mousse, Bourbon Vanilla Ice Cream. Dietary options: Vegetarian: Creamed Spinach, Roast Aubergine; Gluten-Free: Flat Iron Steak, Spiced Lamb; Vegan: Roast Aubergine."
)
VOICE = 'alloy'
LOG_EVENT_TYPES = [
  'response.content.done', 'rate_limits.updated', 'response.done',
  'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
  'input_audio_buffer.speech_started', 'response.create', 'session.created'
]
SHOW_TIMING_MATH = False
app = FastAPI()
if not OPENAI_API_KEY:
  raise ValueError('Missing the OpenAI API key. Please set it in the .env file.') 

def end_twilio_call():
    """Ends an active Twilio call."""
    call =TWILIO_CLIENT.calls(account_sid).update(status='completed')
    
    return call


@app.get("/", response_class=HTMLResponse)
async def index_page():
    return "<html><body><h1>Twilio Media Stream Server is running!</h1></body></html>"

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    logger.info("Received incoming call request from: %s", request.client.host)
    response = VoiceResponse()
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    logger.info("Successfully created the TwiML response")
    return HTMLResponse(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await send_session_update(openai_ws)

        # Connection specific state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.open:
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"\nReceived event: {response['type']}\n", response)

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                                "payload": audio_payload
                            }
                        }
                        await websocket.send_json(audio_delta)

                        if response_start_timestamp_twilio is None:
                            response_start_timestamp_twilio = latest_media_timestamp
                            if SHOW_TIMING_MATH:
                                print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                        # Update last_assistant_item safely
                        if response.get('item_id'):
                            last_assistant_item = response['item_id']

                        await send_mark(websocket, stream_sid)
                        
                    # Detect function call output events
                    if (response.get("type") == "conversation.item.create" and
                        response.get("item", {}).get("type") == "function_call_output"):
                        print("\nFunction call output received:\n", response)
                        # Optionally process the function call output (e.g., parse arguments, execute locally, etc.)
                        # Then trigger a follow-up event to prompt the AI to continue
                        await openai_ws.send(json.dumps({"type": "response.create"}))
                        print("Triggered response.create after function call output.")

                    # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
                            
                    if response.get("type") == "error":
                        print(f"\n\n>>> Received error from OpenAI: {response}\n\n")
                        assert False, "Received error from OpenAI"
                        
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_initial_conversation_item(openai_ws):
    """Send initial conversation item if AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Greet the user -> 'Hi this is Sophie from Flatiron, how can I help you today?'"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))

async def send_session_update(openai_ws):
    """Send session update to OpenAI WebSocket."""

    session_update = {
      "type": "session.update",
      "session": {
          "turn_detection": {"type": "server_vad", "threshold": 0.7,
          "prefix_padding_ms": 500,
          "silence_duration_ms": 800},
          "input_audio_format": "g711_ulaw",
          "output_audio_format": "g711_ulaw",
          "voice": VOICE,
          "instructions": SYSTEM_MESSAGE,
          "input_audio_transcription": {
          "model": "whisper-1"
          },
          "modalities": ["text", "audio"],
          "temperature": 0.6,
            "tools": [
                {
                "type": "function",
                "name": "end_call",
                "description": "Ends the current phone call.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    "call_sid": {
                        "type": "string",
                        "description": "ACfbf93b471d1ff33bb122a1e0ab46c14d"
                    }
                    },
                    "required": ["call_sid"]
                }
                }
            ],
        "tool_choice": "auto",
      }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    await send_initial_conversation_item(openai_ws)

#Instagram API ----------------------------------------------------------

@app.api_route("/privacy_policy", methods= ["GET", "POST"])
def privacy_policy():
    with open("privacy_policy.html", "r") as f:
        privacy_policy_html = f.read()

    return privacy_policy_html

@app.api_route("/webhook", methods=["GET"])
async def webhook(request: Request):
    return int(request.query_params.get("hub.challenge"))

@app.api_route("/webhook", methods=["POST"])
async def handle_messages(request: Request):
    data = await request.json()
    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            sender_id = messaging["sender"]["id"]

            # Quick fix: Check if 'message' and 'text' keys exist
            message = messaging.get("message")
            if not message or "text" not in message:
                print("Non-text message or unsupported event:", messaging)
                continue

            message_text = message["text"]
            thread_id = get_or_create_thread(sender_id)

            # Optional: send typing indicator
            user_access_token = load_access_token()

            OPENAI_CLIENT.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message_text
            )
            run = OPENAI_CLIENT.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )

            while True:
                status = OPENAI_CLIENT.beta.threads.runs.retrieve(run.id, thread_id=thread_id)
                if status.status == "completed":
                    break

            messages = OPENAI_CLIENT.beta.threads.messages.list(thread_id=thread_id)
            assistant_response = next(
                (msg.content[0].text.value for msg in reversed(messages.data) if msg.role == "assistant"),
                "Sorry, I didn't get that."
            )

            send_instagram_message(user_access_token, sender_id, assistant_response)

    return {"status": "ok"}


if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=PORT)
