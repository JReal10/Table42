import os
from openai import OpenAI

user_threads = {}

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
    assistant = OPENAI_CLIENT.beta.assistants.create(
        name="Restaurant Customer Service",
        instructions="You are a personal math tutor. Answer questions briefly, in a sentence or less.",
        model="gpt-4o-mini"
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