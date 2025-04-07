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

SYSTEM_MESSAGE = (
  "You are a professional customer service agent for Flat Iron Restaurant's Soho location. Keep responses clear and concise, focusing on solving problems efficiently. Flat Iron Soho's details are as follows: Address: 17 Beak Street, London W1F 9RW. Opening Hours: Sunday to Tuesday: 12:00 PM – 10:00 PM; Wednesday to Thursday: 12:00 PM – 11:00 PM; Friday to Saturday: 12:00 PM – 11:30 PM. Menu: Mains include Flat Iron Steak, Spiced Lamb, Charcoal Chicken; Sides include Creamed Spinach, Truffle Fries, Roast Aubergine; Desserts include Salted Caramel Mousse, Bourbon Vanilla Ice Cream. Dietary options: Vegetarian: Creamed Spinach, Roast Aubergine; Gluten-Free: Flat Iron Steak, Spiced Lamb; Vegan: Roast Aubergine."
  
  "Only End the call when you answered user's requests.To end a call say something under 10s, and append'GOODBYE();' at the end of your response. if what you say is longer than 10s, the call will end before you finish so keep it short! "
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

assistant = create_assistant()

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
        'wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview-2024-12-17',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)

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
                    elif data['event'] == 'stop':
                        print(f"Call ended, stream {stream_sid} stopped")
                        if openai_ws.open:
                            await openai_ws.close()
                        await websocket.close()
                        return
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
                        print(f"Received event: {response['type']}", response)

                     #first check if response['type'] == 'response.done' and response['response']['output'] is not None:
                        if response['type'] == 'response.done':
                            #print("\n\n\n @Received response.done!!!")
                            if response['response'] is not None:
                                print(f"Received event: {response['type']}", response)
                                response_object = response['response']
                                print(f"\n\n@response_object: {response_object}")
                                if not response_object['output'] == []:
                                    print(f"\n\n@response_object['output']: {response_object['output']}")
                                    output = response_object['output'][0]
                                    print(f"\n\n@output: {output}")
            
                                    if output['role'] == 'assistant':
                                        #print(f"\n\n\n @Received assistant response!!!")

                                        #check if output['content'] is not None:
                                        if output['content'] is not None:
                                            content = output['content'][0]
                                            #print(f"\n\n@content: {content}")
                                            #check if content[`transcript`] is not None:
                                            if content['transcript'] is not None:
                                                transcript = content['transcript']
                                                #(f"\n\n@transcript: {transcript}")

                                                #check if transcript ends with '@END_TWILIO_PHONECALL();':
                                                if transcript.endswith('GOODBYE();'):
                                                    print(f"\n\n\n @Received END_TWILIO_PHONECALL response!!!")
                                                    # Wait for a short duration to ensure all audio is sent before ending the call
                                                    await asyncio.sleep(10)
                                                    await websocket.close()
                                                    return
                    
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

                    # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
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
                    "text": "Greet the user with 'Hello there! How can I help you?'"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))
    
    # Uncomment the next line to have the AI speak first
    await send_initial_conversation_item(openai_ws)

    
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
