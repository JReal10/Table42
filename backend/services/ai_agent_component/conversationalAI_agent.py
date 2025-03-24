from aipolabs import ACI
from dotenv import load_dotenv
import os
import openai
import json

load_dotenv

client = ACI(
    # it reads from environment variable by default so you can omit it if you set it in your environment
    api_key = os.getenv("AIPOLABS_ACI_API_KEY")

)
# Set the API key as an environment variable
os.getenv["OPENAI_API_KEY"]

# No explicit initialization is needed for the 'openai' library
# The library will automatically use the API key from the environment variable

def get_tool_definitions():
    """
    Retrieves tool definitions for Google Calendar functions.
    """
    google_calendar_status = client.functions.get_definition("GOOGLE_CALENDAR__FREEBUSY_QUERY")
    google_calendar_update = client.functions.get_definition("GOOGLE_CALENDAR__EVENTS_UPDATE")
    google_calendar_reserve = client.functions.get_definition("GOOGLE_CALENDAR__EVENTS_INSERT")
    google_calendar_delete = client.functions.get_definition("GOOGLE_CALENDAR__EVENTS_DELETE")
    
    return {
        "status": google_calendar_status,
        "update": google_calendar_update,
        "reserve": google_calendar_reserve,
        "delete": google_calendar_delete,
    }



def initialize_messages():

    context = (
        "Lima's Pasta is located in the heart of downtown at 123 Main Street, Cityville. "
        "The restaurant is easily accessible by public transport and offers nearby parking for your convenience."
    )
      
    """
    Initializes the conversation with a system prompt that outlines the role, objectives, and process.
    """
    system_prompt = f"""
    ## Role and Objective
    You are an advanced conversational AI agent designed to handle customer interactions related to restaurant bookings, reservations. Your core responsibility is ensuring seamless, polite, and professional customer service, covering:

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
    Handles detected tool calls by executing the tool, appending the results to the conversation,
    and making a follow-up GPT call to process the tool output.
    """
    print("\n[DEBUG] Tool call detected.")
    for i, tool_call in enumerate(message.tool_calls):
        print(f"[DEBUG] Tool Call {i + 1}:")
        print(f"  - Function Name: {tool_call.function.name}")
        print(f"  - Arguments: {tool_call.function.arguments}\n")
    
    # Process the first tool call detected
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    # Execute the tool
    execution_result = client.functions.execute(
        function_name,
        arguments,
        linked_account_owner_id="prototype_demo"
    )
    
    result_content = execution_result.data
    
    # Append the tool call and its result to the messages history
    messages.append(message)
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result_content)
    })
    
    # Second GPT call to process the tool output and generate a final response
    final_response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    
    final_message = final_response.choices[0].message.content
    print("Assistant:", final_message)
    messages.append({
        "role": "assistant",
        "content": final_message
    })

def main():
    # Retrieve tool definitions and organize them into a list for easy use.
    tools = get_tool_definitions()
    tool_list = [
        tools["status"],
        tools["delete"],
        tools["reserve"],
        tools["update"]
    ]
    
    # Initialize conversation messages with the system prompt.
    messages = initialize_messages()
    print("Welcome to the Lima's store, how can I help you today? Type 'exit' to quit.\n")
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        # Append the user's message to the conversation history.
        messages.append({
            "role": "user",
            "content": user_input,
        })
        
        # First GPT call (which may invoke a tool)
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tool_list,
        )
        
        message = response.choices[0].message
        
        # Check for tool calls in the assistant's response.
        if message.tool_calls:
            process_tool_calls(message, messages)
        else:
            print("\n[DEBUG] No tool call was made by the assistant.\n")
            print("Assistant:", message.content)
            messages.append({
                "role": "assistant",
                "content": message.content
            })

if __name__ == '__main__':
    main()