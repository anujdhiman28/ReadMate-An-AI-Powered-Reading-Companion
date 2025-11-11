"""
speech_recognition_engine.py

Speech Recognition Engine for the Dyslexia Assistive Reader project.

Features:
- Supports Google Speech Recognition (online) and Whisper (offline).
- Handles continuous or single-shot recording.
- Includes noise adjustment and silence thresholds.
- Returns recognized text for comparison with displayed text.

Usage:
    from speech_recognition_engine import SpeechRecognitionEngine

    recognizer = SpeechRecognitionEngine(use_whisper=False)
    text = recognizer.listen_and_transcribe()
    print("Recognized:", text)
"""

import speech_recognition as sr
from typing import Optional

class SpeechRecognitionEngine:
    def __init__(
        self,
        use_whisper: bool = False,
        whisper_model: str = "base",
        energy_threshold: int = 300,
        pause_threshold: float = 1.0,
        phrase_time_limit: Optional[int] = 8,
        device_index: Optional[int] = None,
    ):
        """
        Initialize the speech recognition engine.

        Args:
            use_whisper: If True, use OpenAI Whisper (requires 'whisper' package).
            whisper_model: Whisper model size ('tiny', 'base', 'small', 'medium', 'large').
            energy_threshold: Minimum audio energy to detect speech.
            pause_threshold: Seconds of silence before stopping recording.
            phrase_time_limit: Max seconds to record a single phrase.
            device_index: Optional microphone device index.
        """
        self.use_whisper = use_whisper
        self.whisper_model_name = whisper_model
        self.energy_threshold = energy_threshold
        self.pause_threshold = pause_threshold
        self.phrase_time_limit = phrase_time_limit
        self.device_index = device_index

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.pause_threshold = self.pause_threshold

        if use_whisper:
            try:
                import whisper
            except ImportError:
                raise ImportError(
                    "Please install Whisper with: pip install openai-whisper"
                )
            print(f"Loading Whisper model '{self.whisper_model_name}'...")
            self.whisper_model = whisper.load_model(self.whisper_model_name)
        else:
            self.whisper_model = None

    def listen_and_transcribe(self) -> Optional[str]:
        """
        Record audio from the microphone and return transcribed text.
        Returns None if no speech detected.
        """
        with sr.Microphone(device_index=self.device_index) as source:
            print("Adjusting for background noise... please wait.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening... speak now.")

            try:
                audio = self.recognizer.listen(source, phrase_time_limit=self.phrase_time_limit)
                print("Processing audio...")
            except sr.WaitTimeoutError:
                print("No speech detected within time limit.")
                return None

        # Transcribe audio
        if self.use_whisper:
            return self._transcribe_whisper(audio)
        else:
            return self._transcribe_google(audio)

    def _transcribe_google(self, audio: sr.AudioData) -> Optional[str]:
        """Transcribe audio using Google Speech Recognition."""
        try:
            text = self.recognizer.recognize_google(audio)
            print(f"Recognized (Google): {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"Google API error: {e}")
            return None

    def _transcribe_whisper(self, audio: sr.AudioData) -> Optional[str]:
        """Transcribe audio using Whisper (offline)."""
        import tempfile
        import numpy as np

        with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as fp:
            wav_path = fp.name
            with open(wav_path, "wb") as f:
                f.write(audio.get_wav_data())

            print("Transcribing using Whisper...")
            result = self.whisper_model.transcribe(wav_path)
            text = result["text"].strip()
            print(f"Recognized (Whisper): {text}")
            return text

    def continuous_listen(self, callback):
        """
        Continuously listens for speech and calls callback(text) when recognized.
        """
        print("Continuous listening started. Press Ctrl+C to stop.")
        with sr.Microphone(device_index=self.device_index) as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            while True:
                try:
                    print("Listening for next phrase...")
                    audio = self.recognizer.listen(source, phrase_time_limit=self.phrase_time_limit)
                    text = self._transcribe_whisper(audio) if self.use_whisper else self._transcribe_google(audio)
                    if text:
                        callback(text)
                except KeyboardInterrupt:
                    print("Stopping continuous listening.")
                    break
                except Exception as e:
                    print("Error during listening:", e)
                    continue

def on_speech_detected(text):
    print("Recognized:", text)
    # You can compare this with expected reading text here.

recognizer = SpeechRecognitionEngine(use_whisper=False)
recognizer.continuous_listen(callback=on_speech_detected)
