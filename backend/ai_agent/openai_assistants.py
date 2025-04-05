import os
from openai import OpenAI
from vector_database import RAGSystem

user_threads = {}

RAGSystem

rag = RAGSystem(vector_store_name="Restaurant Details")
vector_store_id = rag.get_vector_store_id()
print("VECTOR_STORE_ID:", vector_store_id)

# Retrieve the API key from the environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

def create_assistant():
    """
    Create an OpenAI assistant with specified instructions and model.
    
    Returns:
        assistant: The created assistant object.
    """
    restaurant_name = "Flatiron Soho"
    user_name = "Jamie"
    
    assistant = OPENAI_CLIENT.beta.assistants.create(
    name="Restaurant Concierge",
    instructions=f"""
    # Restaurant Concierge for {restaurant_name}
    
    address the user as {user_name}
    
    You are a restaurant concierge that answers queries and books reservations for Flatiron.

    ## Core Functions:
    1. Answer questions about {restaurant_name} using file search tool
    2. Book reservations at {restaurant_name} using Google Calendar tool

    ## Information Queries:
    - Search files for requested information about {restaurant_name}
    - Provide accurate, concise answers
    - If information isn't found, clearly state this

    ## Reservation Process:
    1. Collect details:
    - Guest count
    - Date
    - Time
    - Name
    - Special requests

    2. Check availability:
    - Use Google Calendar to verify availability
    - If unavailable, offer alternatives

    3. Book reservation:
    - Create calendar event with all details
    - Send clear confirmation
    - Include modification/cancellation instructions

    ## Guidelines:
    - Use professional, concise language
    - Only provide information you can verify
    - Never fabricate details about the restaurant
    - Process one request at a time
    - Clarify ambiguous requests before proceeding""",
    
    model="gpt-4o-mini",
    temperature= 0.4,
    tools = [{"type": "file_search"}],
    tool_resources = {
        "file_search":{
            "vector_store_ids": [vector_store_id]
        }
    },
    response_format = {"type":"text"},
    )
    
    return assistant

def get_or_create_thread(sender_id):
    """
    Retrieve an existing thread for the sender or create a new one if it doesn't exist.

    Args:
        sender_id (str): Unique identifier for the sender.

    Returns:
        str: The thread ID associated with the sender.
    """
    if sender_id not in user_threads:
        thread = OPENAI_CLIENT.beta.threads.create()
        user_threads[sender_id] = thread.id
    return user_threads[sender_id]