from __future__ import annotations
import asyncio
import os
from dotenv import load_dotenv
import numpy as np
import sounddevice as sd
from openai import OpenAI
from agents.voice import StreamedAudioInput, VoicePipeline
from util import MyWorkflow

# Load environment variables
load_dotenv()
client = OpenAI(api_key= os.getenv("OPENAI_API_KEY"))

CHUNK_LENGTH_S = 0.05  # 50ms
SAMPLE_RATE = 24000
FORMAT = np.int16
CHANNELS = 1

class InitializeAgent:
    def __init__(self):
        self.should_send_audio = asyncio.Event()
        self.audio_input = StreamedAudioInput()
        self.audio_player = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=FORMAT,
        )
        self.pipeline = VoicePipeline(
            workflow=MyWorkflow(
                secret_word="dog",
                on_start=self._on_transcription
            )
        )

    def _on_transcription(self, transcription: str) -> None:
        print(f"[Transcription] {transcription}")

    async def start(self):
        print("🎤 Starting voice agent terminal app...")
        # Set the event to true immediately so audio starts flowing
        self.should_send_audio.set()
        print("[Status] 🔴 Started recording automatically.")
        
        await asyncio.gather(
            self.run_pipeline(),
            self.send_mic_audio(),
            self.input_loop()
        )

    async def run_pipeline(self):
        try:
            self.audio_player.start()            
            result = await self.pipeline.run(self.audio_input)
            
            initial_message = "Hi this is sam from Flatiron, how can I help you today?"
            
            async for event in result.stream():
                if event.type == "voice_stream_event_audio":
                    self.audio_player.write(event.data)
                    print(f"[AudioStream] Received {len(event.data)} bytes")
                elif event.type == "voice_stream_event_lifecycle":
                    print(f"[Lifecycle] {event.event}")
                    if event.event == "turn_started":
                        # Mute the microphone by stopping audio from being sent
                        print("Muting microphone...")
                        self.should_send_audio.clear()
                    elif event.event == "turn_ended":
                        # Unmute the microphone by resuming audio sending
                        print("Unmuting microphone...")
                        self.should_send_audio.set()
                        
        except Exception as e:
            print(f"[Error] {e}")
        finally:
            self.audio_player.close()

    async def send_mic_audio(self):
        stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype=FORMAT,
        )
        stream.start()

        read_size = int(SAMPLE_RATE * 0.02)

        try:
            while True:
                if stream.read_available < read_size:
                    await asyncio.sleep(0.01)
                    continue

                await self.should_send_audio.wait()
                data, _ = stream.read(read_size)
                await self.audio_input.add_audio(data)
                await asyncio.sleep(0)
        except Exception as e:
            print(f"[MicError] {e}")
        finally:
            stream.stop()
            stream.close()

    async def input_loop(self):
        asyncio.get_event_loop()

if __name__ == "__main__":
    asyncio.run(InitializeAgent().start())