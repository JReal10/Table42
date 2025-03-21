import os
import io
import wave
import threading
import time
import pyaudio
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables from .env
load_dotenv()


class LiveASRService:
    """
    A live automatic speech recognition (ASR) service that continuously records audio,
    converts it to text using the ElevenLabs API, and passes the transcription to an optional callback.
           # Configure VAD and silence threshold (in seconds)
    
    
    vad = webrtcvad.Vad(2)  # Aggressiveness mode: 0 (least) to 3 (most)
    SILENCE_DURATION_THRESHOLD = 1.0  # 1 second of silence

    def record_until_silence(stream, rate, chunk):
        Capture audio until a period of silence is detected.
        
        Args:
            stream: The PyAudio stream to read from.
            rate (int): Sample rate of the audio.
            chunk (int): Number of frames per read.
            
        Returns:
            list: Collected audio frames.
        frames = []
        silence_duration = 0
        start_time = time.time()

        while True:
            frame = stream.read(chunk, exception_on_overflow=False)
            frames.append(frame)

            # Check if the current frame contains speech
            if vad.is_speech(frame, rate):
                silence_duration = 0  # Reset if speech is detected
            else:
                silence_duration += chunk / rate  # Update silence duration

            # If silence has lasted long enough, exit loop
            if silence_duration >= SILENCE_DURATION_THRESHOLD:
                break

        return frames
    """


    def __init__(self, record_seconds=5, callback=None):
        """
        Initialize the live ASR service.

        Args:
            record_seconds (int): Duration (in seconds) for each audio chunk.
            callback (callable): Optional callback function that receives the transcription text.
        """
        self.record_seconds = record_seconds
        self.callback = callback

        # Initialize ElevenLabs client using API key from environment variables
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

        # PyAudio configuration
        self.FORMAT = pyaudio.paInt16  # 16-bit PCM
        self.CHANNELS = 1              # Mono audio
        self.RATE = 16000              # 16 kHz sample rate
        self.CHUNK = 1024              # Frames per buffer

        # Initialize PyAudio and open an audio stream
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

        Args:
            frames (list): List of raw audio frames.

        Returns:
            io.BytesIO: An in-memory WAV file containing the audio data.
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
        Continuously record audio chunks, send them to the ASR API for transcription,
        and call the provided callback function with the transcribed text.
        """
        while self._running:
            print(f"Recording for {self.record_seconds} seconds...")
            frames = []
            try:
                num_frames = int(self.RATE / self.CHUNK * self.record_seconds)
                for _ in range(num_frames):
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
        Start the live ASR transcription service in a background thread.
        """
        if not self._running:
            self._running = True
            self.thread = threading.Thread(target=self._transcribe_loop, daemon=True)
            self.thread.start()
            print("Live ASR service started.")

    def stop(self):
        """
        Stop the live ASR transcription service and clean up resources.
        """
        self._running = False
        if self.thread:
            self.thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_instance.terminate()
        print("Live ASR service stopped.")


def main():
    """
    Example usage of the LiveASRService class.
    """
    def print_transcription(text):
        print("Callback transcription:", text)

    # Instantiate the ASR service with a 5-second recording chunk and a callback.
    asr_service = LiveASRService(record_seconds=5, callback=print_transcription)
    try:
        asr_service.start()
        # Keep the main thread alive while the service is running.
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping ASR service...")
    finally:
        asr_service.stop()


if __name__ == "__main__":
    main()
