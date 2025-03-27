import openai
import json
import os
from dotenv import load_dotenv
from aipolabs import ACI
from .agent_component import SilenceDetectingASRService, RAGSystem, text_to_speech

load_dotenv()

# Initialize the client using your environment variable.
client = ACI(api_key=os.getenv("AIPOLABS_ACI_API_KEY"))

def get_aci_tool_definitions():
    """
    Retrieve and return the definitions for the ACI tools.
    """
    return {
        "status": client.functions.get_definition("GOOGLE_CALENDAR__FREEBUSY_QUERY"),
        "update": client.functions.get_definition("GOOGLE_CALENDAR__EVENTS_UPDATE"),
        "reserve": client.functions.get_definition("GOOGLE_CALENDAR__EVENTS_INSERT"),
        "delete": client.functions.get_definition("GOOGLE_CALENDAR__EVENTS_DELETE"),
    }

def initialize_messages(context):
    system_prompt = f"""
    ## Role and Objective
    You are an advanced conversational AI agent handling restaurant bookings for Lima's Pasta (jamieogundiran21@gmail.com).

    - **New reservations**
    - **Reservation modifications**
    - **Cancellations**
    - **Reservation inquiries**
    - **General restaurant information (menu, hours, location)**
    
    The restaurant details are as follows:
    - **Restaurant Name:** Lima's Pasta (jamieogundiran21@gmail.com)
    - **Context:** {context}

    Aim for a warm, helpful tone, and proactively guide customers through the process.

    ---

    ## Core Interaction Flow (4 Key Steps)

    ### 1. Intent Identification
    - Detect intent (new booking, update, cancellation, inquiry) to streamline the conversation.

    Example:
    If intent is detected:
    "Would you like to make a new reservation, check an existing one, or modify/cancel a booking?"

    ---

    ### 2. Reservation Details Collection (For New or Modified Bookings)
    - Collect all essential reservation details:
        - Full Name
        - Date and Time
        - Number of Guests

    - Example Process:
        - "May I have your full name?"
        - "Which date and time would you like to book for?"
        - "How many guests will be joining you?"

    - For modifying or checking bookings, request:
        - Name (for lookup)

    - For cancellations, always confirm the booking details before proceeding.

    ---

    ### 3. Availability Check and Alternatives
    - After gathering reservation details, check availability.

    - If available:
        - "Great news! We have availability for [Number of Guests] at [Date and Time]. Shall I confirm your reservation?"
    - If unavailable:
        - "I’m sorry, we are fully booked at that time. May I suggest an alternative time on [Same Date] or perhaps another date?"
    ---

    ### 4. Final Confirmation and Summary
    - Always confirm details before finalizing.
    - Recap the reservation to ensure accuracy.

    Example:
    "Your reservation is confirmed for [Number] guests on [Date] at [Time] under the name [Customer Name].

    - For cancellations:
    "Your reservation for [Date] at [Time] has been successfully canceled."
    """

    return [{
        "role": "system",
        "content": system_prompt
    }]

def process_tool_calls(message, messages):
    """
    Process tool calls from the assistant's message.
    """
    tool_call = message.tool_calls[0]
    execution_result = client.functions.execute(
        tool_call.function.name,
        json.loads(tool_call.function.arguments),
        linked_account_owner_id="prototype_demo"
    )

    messages.append(message)
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(execution_result.data)
    })

    final_response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return final_response.choices[0].message.content


def get_assistant_response(transcribed_text, context, tools):
    messages = initialize_messages(context)
    messages.append({
        "role": "user",
        "content": transcribed_text
    })

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools
    )

    message = response.choices[0].message

    if message.tool_calls:
        assistant_reply = process_tool_calls(message, messages)
    else:
        assistant_reply = message.content

    messages.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply
    
def initialize_conversation():
    
    tools = list(get_aci_tool_definitions().values())
    
    # Use RAG to enrich context based on the transcribed text.
    rag_client = RAGSystem(index_name="conv-ai")
    # Initialize the ASR service for capturing audio input.
    
    asr_service = SilenceDetectingASRService(
        silence_threshold=1000,   # Energy threshold for silence detection.
        silence_duration=3.2      # Duration of silence to signal end of recording.
    )
    
    print("Start the conversation (say 'exit' to quit):")
    greeting = "Hi, How can I assist you today?"
    # Use TTS to speak the assistant's response.
    text_to_speech(greeting)
    
    while True:
        # Capture user audio input.
        print("\nListening for user input...")
        transcribed_text = asr_service.transcribe()
        
        # Check for an exit command.
        if transcribed_text.strip().lower() in ["exit", "quit"]:
            print("Ending conversation.")
            break
        
        print("User said:", transcribed_text)
        

        enriched_context = rag_client.similarity_search_with_score(transcribed_text, k=1)
        print("Enriched context:", enriched_context)
        
        # Get the assistant's response using the enriched context.
        agent_response = get_assistant_response(transcribed_text, enriched_context, tools)
        print("Assistant:", agent_response)
        
        # Use TTS to speak the assistant's response.
        text_to_speech(agent_response)

if __name__ == "__main__":
    # Provide any initial context if needed.
    initialize_conversation()
