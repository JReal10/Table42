from dotenv import load_dotenv
import os
from elevenlabs.client import ElevenLabs
from elevenlabs import play

load_dotenv()  # Load variables from .env

# Retrieve the API key from the environment
client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

text = "Hello"

def text_to_speech(text):
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_turbo_v2_5",
        output_format="mp3_44100_128",
    )
    play(audio)

text_to_speech(text)