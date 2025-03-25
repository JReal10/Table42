from aipolabs import ACI
from dotenv import load_dotenv
import os
import openai
import json

load_dotenv()

client = ACI(api_key=os.getenv("AIPOLABS_ACI_API_KEY"))

def get_aci_tool_definitions():
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

def get_assistant_response(transcribed_text, messages, tools):
    messages.append({"role": "user", "content": transcribed_text})

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools
    )

    message = response.choices[0].message

    if message.tool_calls:
        return process_tool_calls(message, messages)
    else:
        return message.content

# Main integration point for transcribed input
def handle_transcribed_input(transcribed_text, context):
    tools = list(get_aci_tool_definitions().values())
    messages = initialize_messages(context)

    response = get_assistant_response(transcribed_text, messages, tools)
    
    return response

if __name__ == '__main__':
    transcribed_text = input("Enter transcribed text: ")
    assistant_response = handle_transcribed_input(transcribed_text)
    print("\nAssistant Response:", assistant_response)
