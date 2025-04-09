import os
import json
import logging
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from openai import OpenAI

from vector_database import RAGSystem
from ai_agent import create_assistant, get_or_create_thread, comment_reply_assistant
from helper import load_access_token, send_instagram_message, FacebookApiClient, reply_to_instagram_comment
from aipolabs import ACI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
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
                    result["status"] = "completed"
                    result["response"] = self._get_assistant_response(thread_id)
                else:
                    logger.info(f"Run status after tool submission: {run.status}")
                    result["status"] = run.status
            except Exception as e:
                logger.error(f"Failed to submit tool outputs: {e}")
        else:
            logger.info("No tool outputs to submit")
            
        return result
    
    def _execute_calendar_tool(
        self, 
        tool: Any, 
        aci_client: ACI,
        linked_account_owner_id: str
    ) -> Dict:
        """Execute a calendar tool call.
        
        Args:
            tool: Tool call object
            aci_client: ACI client instance
            linked_account_owner_id: Linked account owner ID
            
        Returns:
            Tool output dict
        """
        try:
            arguments = json.loads(tool.function.arguments)
            aci_result = aci_client.functions.execute(
                tool.function.name,
                arguments,
                linked_account_owner_id=linked_account_owner_id
            )
            return {
                "tool_call_id": tool.id,
                "output": aci_result.model_dump_json()
            }
        except Exception as e:
            logger.error(f"Error executing ACI Google Calendar: {e}")
            return {
                "tool_call_id": tool.id,
                "output": f"Error: {e}"
            }


class InstagramWebhookHandler:
    """Handler for Instagram webhook events."""
    
    def __init__(
        self, 
        openai_handler: OpenAIHandler,
        fb_client: FacebookApiClient,
        aci_client: ACI,
        config: Config
    ):
        """Initialize the Instagram webhook handler.
        
        Args:
            openai_handler: OpenAI handler instance
            fb_client: Facebook API client instance
            aci_client: ACI client instance
            config: Application configuration
        """
        self.openai_handler = openai_handler
        self.fb_client = fb_client
        self.aci_client = aci_client
        self.config = config
        self.user_access_token = load_access_token()
    
    async def handle_direct_message(self, messaging_data: Dict) -> None:
        """Handle an Instagram direct message.
        
        Args:
            messaging_data: Messaging data from the webhook
        """
        sender_id = messaging_data["sender"]["id"]
        logger.info(f"Processing direct message from sender ID: {sender_id}")

        # Check if message exists
        message = messaging_data.get("message")
        if not message or "text" not in message:
            logger.warning(f"Received message without text from {sender_id}")
            return

        # Process actual user message
        message_text = message["text"]
        thread_id = get_or_create_thread(sender_id)
        
        # Process with OpenAI
        result = self.openai_handler.process_message(
            thread_id=thread_id,
            message_text=message_text,
            assistant_id=self.openai_handler.assistant.id
        )
        
        if result["status"] == 'completed' and result["response"]:
            assistant_response = result["response"]
            logger.info(f"Assistant response: {assistant_response}")
            send_instagram_message(self.user_access_token, sender_id, assistant_response)
            
        elif result["status"] == 'requires_action':
            # Handle tool actions
            action_result = self.openai_handler.handle_tool_actions(
                run=result["run"],
                thread_id=thread_id,
                aci_client=self.aci_client,
                linked_account_owner_id=self.config.LINKED_ACCOUNT_OWNER_ID
            )
            
            if action_result["status"] == "completed" and action_result["response"]:
                assistant_response = action_result["response"]
                logger.info(f"Assistant response after tool action: {assistant_response}")
                send_instagram_message(self.user_access_token, sender_id, assistant_response)
        else:
            logger.info(f"Run ended with status: {result['status']}")
    
    async def handle_comment(self, comment_data: Dict) -> None:
        """Handle an Instagram comment.
        
        Args:
            comment_data: Comment data from the webhook
        """
        # Extract comment information
        comment_id = comment_data.get("id")
        comment_text = comment_data.get("text")
        from_user = comment_data.get("from", {})
        user_id = from_user.get("id")
        username = from_user.get("username")
        
        logger.info(f"Processing comment from {username} (ID: {user_id}): {comment_text}")
        
        # Check if this is a new comment on a feed post
        if comment_data.get("media", {}).get("media_product_type") != "FEED":
            logger.info(f"Not a FEED comment or missing media_product_type")
            return
            
        # Process the comment with the assistant
        thread_id = get_or_create_thread(user_id)
        
        # Process with OpenAI
        result = self.openai_handler.process_message(
            thread_id=thread_id,
            message_text=f"[Instagram Comment] {comment_text}",
            assistant_id=self.openai_handler.comment_assistant.id
        )
        
        if result["status"] == 'completed' and result["response"]:
            assistant_response = result["response"]
            logger.info(f"Assistant response to comment: {assistant_response}")
            reply_to_instagram_comment(comment_id, assistant_response)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Validate configuration
    Config.validate()
    
    # Initialize services
    rag = RAGSystem(vector_store_name="Restaurant Details")
    vector_store_id = rag.get_vector_store_id()
    
    aci_client = ACI()
    fb_client = FacebookApiClient()
    openai_handler = OpenAIHandler(api_key=Config.OPENAI_API_KEY)
    
    instagram_handler = InstagramWebhookHandler(
        openai_handler=openai_handler,
        fb_client=fb_client,
        aci_client=aci_client,
        config=Config
    )
    
    # Create FastAPI app
    app = FastAPI()
    
    # Register routes
    @app.get("/", response_class=HTMLResponse)
    async def index_page():
        """Serve the index page."""
        return "<html><body><h1>Twilio Media Stream Server is running!</h1></body></html>"
        
    @app.api_route("/privacy_policy", methods=["GET", "POST"])
    def privacy_policy():
        """Serve the privacy policy page."""
        with open("privacy_policy.html", "r") as f:
            privacy_policy_html = f.read()
        return privacy_policy_html
        
    @app.get("/fb_webhook")
    @app.get("/webhook")
    async def webhook_verification(request: Request):
        """Verify webhook subscription for Instagram/Facebook.
        
        Args:
            request: FastAPI request object
            
        Returns:
            hub.challenge value to verify the webhook
        """
        return int(request.query_params.get("hub.challenge"))
    
    @app.post("/fb_webhook")
    async def fb_webhook_handler(request: Request):
        """Handle Facebook webhook events.
        
        Args:
            request: FastAPI request object
        """
        data = await request.json()
        
        for entry in data.get("entry", []):
            if "messaging" in entry:
                for messaging in entry.get("messaging", []):
                    await instagram_handler.handle_direct_message(messaging)
    
    @app.post("/webhook")
    async def instagram_webhook_handler(request: Request):
        """Handle Instagram webhook events.
        
        Args:
            request: FastAPI request object
        """
        data = await request.json()
        
        for entry in data.get("entry", []):
            logger.info(f"Processing entry: {entry}")
            
            # Handle comments
            if "changes" in entry:
                for change in entry.get("changes", []):
                    logger.info(f"Processing change: {change}")
                    
                    if change.get("field") == "comments":
                        comment_data = change.get("value", {})
                        await instagram_handler.handle_comment(comment_data)
            
            # Handle direct messages
            if "messaging" in entry:
                for messaging in entry.get("messaging", []):
                    await instagram_handler.handle_direct_message(messaging)
    
    return app


# Application entry point
if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)
