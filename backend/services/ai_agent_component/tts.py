import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Load environment variables from the .env file
load_dotenv()

# Retrieve the API key from the environment and initialize the client
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def text_to_speech(text, voice_id="JBFqnCBsd6RMkjVDRZzb", model_id="eleven_turbo_v2_5", output_format="mp3_44100_128"):
    """
    Convert text to speech using the ElevenLabs API and play the resulting audio.

    Parameters:
        text (str): The text to convert.
        voice_id (str): The voice ID to use for conversion.
        model_id (str): The model ID for the text-to-speech conversion.
        output_format (str): The desired audio output format.

    Returns:
        None
    """
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model_id,
        output_format=output_format,
    )
    play(audio)



if __name__ == "__main__":
    # Example usage: convert and play the sample text
    sample_text = "Hello"
    text_to_speech(sample_text)
