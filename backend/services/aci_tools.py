from aipolabs import ACI
import os
from dotenv import load_dotenv

load_dotenv()

client = ACI(
    # it reads from environment variable by default so you can omit it if you set it in your environment
    api_key=os.environ.get("AIPOLABS_ACI_API_KEY")
)