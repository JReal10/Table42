import os
import io
import wave
import threading
import pyaudio
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv()

class LiveASRService:
    def __init__(self, record_seconds=5, callback=None):
        """
        Initialize the live ASR service.
        
        Args:
            record_seconds (int): Duration (in seconds) for each audio chunk.
            callback (function): Optional callback function that receives the transcription text.
        """
        self.record_seconds = record_seconds
        self.callback = callback

        # Initialize ElevenLabs client
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

        # PyAudio configuration
        self.FORMAT = pyaudio.paInt16   # 16-bit PCM
        self.CHANNELS = 1               # Mono audio
        self.RATE = 16000               # 16 kHz sample rate
        self.CHUNK = 1024               # Frames per buffer

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

    def _get_wav_bytes(self, frames):
        """
        Convert a list of raw audio frames into an in-memory WAV file.
        """
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.pyaudio_instance.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
        wav_buffer.seek(0)
        return wav_buffer

    def _transcribe_loop(self):
        """
        Continuously capture audio, send chunks to the ASR API, and process transcriptions.
        """
        while self._running:
            print(f"Recording for {self.record_seconds} seconds...")
            frames = []
            try:
                for _ in range(0, int(self.RATE / self.CHUNK * self.record_seconds)):
                    data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
            except Exception as e:
                print("Error capturing audio:", e)
                continue

            wav_bytes = self._get_wav_bytes(frames)
            print("Transcribing audio chunk...")
            try:
                transcription = self.client.speech_to_text.convert(
                    file=wav_bytes,
                    model_id="scribe_v1",       # ASR model (update if needed)
                    tag_audio_events=True,      # Optional: tag events like laughter
                    language_code="eng",        # Language code (or None for auto-detect)
                    diarize=True                # Enable speaker diarization
                )
                text = transcription.text
                print("Transcription:", text)
                if self.callback:
                    self.callback(text)
            except Exception as e:
                print("Error during transcription:", e)

    def start(self):
        """
        Start the live ASR transcription in a background thread.
        """
        if not self._running:
            self._running = True
            self.thread = threading.Thread(target=self._transcribe_loop, daemon=True)
            self.thread.start()
            print("Live ASR service started.")

    def stop(self):
        """
        Stop the live ASR transcription and clean up resources.
        """
        self._running = False
        if self.thread:
            self.thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_instance.terminate()
        print("Live ASR service stopped.")

# Example usage when running this module directly.
if __name__ == "__main__":
    def print_transcription(text):
        print("Callback transcription:", text)

    # Instantiate the service with a 5-second recording chunk and a callback.
    asr_service = LiveASRService(record_seconds=5, callback=print_transcription)
    try:
        asr_service.start()
        # Keep the main thread alive.
        while True:
            pass
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping ASR service...")
    finally:
        asr_service.stop()


#Example Usage
        """
        from backend.services.live_asr_service import LiveASRService

def handle_transcription(text):
    # Process or forward the transcription text to your AI agent.
    print("Received transcription:", text)

asr_service = LiveASRService(record_seconds=5, callback=handle_transcription)
asr_service.start()

        """