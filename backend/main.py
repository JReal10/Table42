"""
Instagram/OpenAI Integration with FastAPI

This application provides integration between Instagram messaging, OpenAI assistants,
and Google Calendar through ACI. It handles webhooks for Instagram direct messages
and comments.
"""

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

class Config:
    """Application configuration loaded from environment variables."""
    
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')
    PORT: int = int(os.getenv('PORT', 5050))
    LINKED_ACCOUNT_OWNER_ID: str = os.getenv("LINKED_ACCOUNT_OWNER_ID", "")
    SHOW_TIMING_MATH: bool = False
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values are present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')
        
        if not cls.LINKED_ACCOUNT_OWNER_ID:
            raise ValueError("LINKED_ACCOUNT_OWNER_ID is not set")


class OpenAIHandler:
    """Handler for OpenAI API interactions."""
    
    def __init__(self, api_key: str):
        """Initialize with OpenAI API key.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.assistant = create_assistant()
        self.comment_assistant = comment_reply_assistant()
        
    def process_message(self, thread_id: str, message_text: str, assistant_id: str) -> Dict:
        """Process a message using OpenAI's assistant API.
        
        Args:
            thread_id: OpenAI thread ID
            message_text: Message text to process
            assistant_id: ID of the assistant to use
            
        Returns:
            Dict containing response and status
        """
        # Send message to OpenAI
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message_text
        )
        
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        
        result = {
            "status": run.status,
            "run": run,
            "response": None,
            "tool_outputs": []
        }
        
        if run.status == 'completed':
            result["response"] = self._get_assistant_response(thread_id)
        
        return result
    
    def _get_assistant_response(self, thread_id: str) -> str:
        """Get the latest assistant response from a thread.
        
        Args:
            thread_id: OpenAI thread ID
            
        Returns:
            Assistant's response text
        """
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        return next(
            (msg.content[0].text.value for msg in messages.data if msg.role == "assistant"),
            "Sorry, I didn't get that."
        )
    
    def handle_tool_actions(
        self, 
        run: Any, 
        thread_id: str,
        aci_client: ACI,
        linked_account_owner_id: str
    ) -> Dict:
        """Handle tool actions required by the assistant.
        
        Args:
            run: The OpenAI run object
            thread_id: OpenAI thread ID
            aci_client: ACI client instance
            linked_account_owner_id: Linked account owner ID for ACI
            
        Returns:
            Dict containing updated run status and response
        """
        tool_outputs = []
        
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "GOOGLE_CALENDAR__EVENTS_INSERT":
                tool_output = self._execute_calendar_tool(
                    tool, aci_client, linked_account_owner_id
                )
                tool_outputs.append(tool_output)
        
        result = {
            "status": run.status,
            "response": None
        }
            
        if tool_outputs:
            try:
                run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                logger.info("Tool outputs submitted successfully.")
                
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
