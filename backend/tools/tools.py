from aipolabs import ACI
from aipolabs.types.functions import FunctionExecutionResult, FunctionDefinitionFormat
import os

def get_calendar_functions():
    """
    Retrieves Google Calendar function definitions from AipoLabs API.
    
    Returns:
        dict: Dictionary containing calendar function definitions for update, reserve, and delete operations.
    """
    ACI_CLIENT = ACI(api_key=os.getenv("AIPOLABS_ACI_API_KEY"))
    
    UPDATE = ACI_CLIENT.functions.get_definition("GOOGLE_CALENDAR__EVENTS_UPDATE")
    RESERVE = ACI_CLIENT.functions.get_definition("GOOGLE_CALENDAR__EVENTS_INSERT")
    DELETE = ACI_CLIENT.functions.get_definition("GOOGLE_CALENDAR__EVENTS_DELETE")
    
    # Return a dictionary of the calendar function definitions
    return {
        "update_event": UPDATE,
        "reserve_event": RESERVE,
        "delete_event": DELETE
    }

