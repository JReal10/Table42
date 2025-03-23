import os
import io
import wave
import threading
import time
import pyaudio
import numpy as np
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables from .env
load_dotenv()


class SilenceDetectingASRService:
    """
    A live automatic speech recognition (ASR) service that records audio until
    silence is detected, converts it to text using the ElevenLabs API, and passes 
    the transcription to an optional callback.
    """

    def __init__(self, callback=None, silence_threshold=1000, silence_duration=3.2):
        """
        Initialize the silence-detecting ASR service.

        Args:
            callback (callable): Optional callback function that receives the transcription text.
            silence_threshold (int): The audio energy level below which is considered silence.
            silence_duration (float): The duration (in seconds) of silence needed to end recording.
        """
        self.callback = callback
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration

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
        self.processing_lock = threading.Lock()

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

    def _is_silent(self, data_chunk):
        """
        Determine if an audio chunk is silent based on its energy level.

        Args:
            data_chunk (bytes): Raw audio data.

        Returns:
            bool: True if the chunk is considered silent, False otherwise.
        """
        # Convert byte data to numpy array of audio samples
        audio_samples = np.frombuffer(data_chunk, dtype=np.int16)
        
        # Calculate energy (volume) of the chunk
        energy = np.sqrt(np.mean(audio_samples.astype(np.float32)**2))
        
        # Return True if energy is below the threshold
        return energy < self.silence_threshold

    def _record_until_silence(self):
        """
        Record audio until a specified duration of silence is detected.

        Returns:
            list: List of audio frames recorded.
        """
        frames = []
        silent_chunks = 0
        chunks_per_second = int(self.RATE / self.CHUNK)
        silence_limit = int(chunks_per_second * self.silence_duration)
        
        # Wait for sound to start (skip initial silence)
        print("Waiting for speech...")
        while self._running:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            if not self._is_silent(data):
                print("Speech detected, recording...")
                frames.append(data)
                break
            time.sleep(0.01)  # Small delay to prevent CPU overuse
            
        # Record until silence threshold is reached
        while self._running:
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

    def _process_audio(self, frames):
        """
        Process the recorded audio frames by transcribing them.

        Args:
            frames (list): List of audio frames to process.
        """
        if not frames:
            print("No audio recorded.")
            return
            
        wav_bytes = self._get_wav_bytes(frames)
        print("Transcribing audio...")
        
        try:
            transcription = self.client.speech_to_text.convert(
                file=wav_bytes,
                model_id="scribe_v1",       # ASR model
                tag_audio_events=True,      # Optional: tag events like laughter
                language_code="eng",        # Language code (or None for auto-detect)
                diarize=True                # Enable speaker diarization
            )
            text = transcription.text
            print("Transcription:", text)
            if self.callback and text.strip():
                self.callback(text)
        except Exception as e:
            print("Error during transcription:", e)

    def _transcribe_loop(self):
        """
        Continuously record audio when speech is detected, stop when silence is detected,
        and process the audio by transcribing it.
        """
        while self._running:
            # Only one recording/processing can happen at a time
            with self.processing_lock:
                frames = self._record_until_silence()
                if frames:
                    self._process_audio(frames)
            
            # Small pause between recording sessions
            time.sleep(0.2)

    def start(self):
        """
        Start the silence-detecting ASR service in a background thread.
        """
        if not self._running:
            self._running = True
            self.thread = threading.Thread(target=self._transcribe_loop, daemon=True)
            self.thread.start()
            print("Silence-detecting ASR service started.")

    def stop(self):
        """
        Stop the ASR service and clean up resources.
        """
        self._running = False
        if self.thread:
            self.thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_instance.terminate()
        print("ASR service stopped.")


def main():
    """
    Example usage of the SilenceDetectingASRService class.
    """
    def handle_transcription(text):
        print(f"Received transcription: {text}")
        # Here you would send the text to your LLM and process the response
        # For example:
        # response = llm_service.generate_response(text)
        # text_to_speech_service.speak(response)
        print("LLM would process this text and respond...")

    # Instantiate the ASR service with silence detection
    # You may need to adjust these parameters based on your microphone and environment
    asr_service = SilenceDetectingASRService(
        callback=handle_transcription,
        silence_threshold=1000,  # Energy threshold for silence detection
        silence_duration=3.2     # Duration of silence to end recording (seconds)
    )
    
    try:
        asr_service.start()
        # Keep the main thread alive while the service is running
        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Stopping ASR service...")
    finally:
        asr_service.stop()


if __name__ == "__main__":
    main()