from aipolabs import ACI
from aipolabs.types.functions import FunctionExecutionResult, FunctionDefinitionFormat

ACI_CLIENT = ACI(api_key=os.getenv("AIPOLABS_ACI_API_KEY"))

UPDATE = ACI_CLIENT.functions.get_definition("GOOGLE_CALENDAR__EVENTS_UPDATE")
RESERVE = ACI_CLIENT.functions.get_definition("GOOGLE_CALENDAR__EVENTS_INSERT")
DELETE = ACI_CLIENT.functions.get_definition("GOOGLE_CALENDAR__EVENTS_DELETE")