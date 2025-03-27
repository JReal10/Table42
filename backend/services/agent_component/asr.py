import os
import io
import wave
import threading
import time
import pyaudio
import asyncio
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SilenceDetectingASRService:
    def __init__(self, callback=None, silence_threshold=1200, silence_duration=3.2):
        self.callback = callback
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration

        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 512

        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = self.pyaudio_instance.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

        self._running = False
        self.thread = None
        self.processing_lock = threading.Lock()

    def _get_wav_bytes(self, frames):
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.pyaudio_instance.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
        wav_buffer.seek(0)
        return wav_buffer

    def _is_silent(self, data_chunk):
        audio_samples = np.frombuffer(data_chunk, dtype=np.int16)
        energy = np.sqrt(np.mean(audio_samples.astype(np.float32)**2))
        return energy < self.silence_threshold

    def _record_until_silence(self):
        frames = []
        silent_chunks = 0
        chunks_per_second = int(self.RATE / self.CHUNK)
        silence_limit = int(chunks_per_second * self.silence_duration)

        print("Waiting for speech...")
        while True:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            if not self._is_silent(data):
                print("Speech detected, recording...")
                frames.append(data)
                break
            time.sleep(0.01)

        while True:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)
            if self._is_silent(data):
                silent_chunks += 1
                if silent_chunks >= silence_limit:
                    print(f"Silence detected for {self.silence_duration}s, stopping recording.")
                    break
            else:
                silent_chunks = 0

        return frames

    async def _process_audio(self, frames):
        if not frames:
            print("No audio recorded.")
            return ""

        wav_bytes = self._get_wav_bytes(frames)
        wav_bytes.name = 'audio.wav'  # Ensure the file has a name
        print("Sending audio to OpenAI Whisper API...")

        try:
            # Use transcriptions.create instead of audio.transcription.create
            response = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",  # Use the standard Whisper model
                file=wav_bytes,
                response_format="text"
            )
            text = response.strip()
            print("Transcription:", text)
            if self.callback and text:
                self.callback(text)
            return text
        except Exception as e:
            print("Error during transcription:", e)
            return ""

    def transcribe(self):
        frames = self._record_until_silence()
        return self._process_audio(frames)

    def start(self):
        if not self._running:
            self._running = True
            self.thread = threading.Thread(target=self._transcribe_loop, daemon=True)
            self.thread.start()
            print("Silence-detecting ASR service started.")

    def _transcribe_loop(self):
        while self._running:
            with self.processing_lock:
                frames = self._record_until_silence()
                if frames:
                    self._process_audio(frames)
            time.sleep(0.2)

    def stop(self):
        self._running = False
        if self.thread:
            self.thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_instance.terminate()
        print("ASR service stopped.")

def main():
    asr_service = SilenceDetectingASRService(
        silence_threshold=1000,
        silence_duration=3.2
    )

    print("Please speak now...")
    print("Transcribed text:", asyncio.run(asr_service.transcribe()))

if __name__ == "__main__":
    main()
