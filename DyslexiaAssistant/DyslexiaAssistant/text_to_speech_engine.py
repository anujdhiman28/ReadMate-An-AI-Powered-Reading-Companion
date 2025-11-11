"""
text_to_speech_engine.py

Text-to-Speech (TTS) Engine for the Dyslexia Assistive Reader project.

Features:
- Uses pyttsx3 for offline speech synthesis (works without internet).
- Supports adjustable rate, volume, and voice (male/female).
- Optional gTTS mode for natural voices (requires internet).
- Provides callbacks for word highlighting (for syncing with text display).

Usage:
    from text_to_speech_engine import TextToSpeechEngine

    tts = TextToSpeechEngine()
    tts.speak_text("Read this: six wet men had nine earphones")
"""

import os
import time
import tempfile
import threading
from typing import Callable, Optional

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from gtts import gTTS
    import playsound
except ImportError:
    gTTS = None
    playsound = None


class TextToSpeechEngine:
    def __init__(
        self,
        use_gtts: bool = False,
        rate: int = 150,
        volume: float = 1.0,
        voice_gender: str = "female",  # "male" or "female"
        on_word_callback: Optional[Callable[[str, int], None]] = None,
    ):
        """
        Initialize the TTS engine.

        Args:
            use_gtts: If True, uses Google TTS (online). Otherwise uses pyttsx3 (offline).
            rate: Speech rate (words per minute).
            volume: Volume level (0.0–1.0).
            voice_gender: Voice gender preference ("male" or "female").
            on_word_callback: Optional function called per word (for highlighting).
                              Signature: callback(word: str, index: int)
        """
        self.use_gtts = use_gtts
        self.rate = rate
        self.volume = volume
        self.voice_gender = voice_gender
        self.on_word_callback = on_word_callback

        self.engine = None
        if not use_gtts:
            if pyttsx3 is None:
                raise ImportError("pyttsx3 is not installed. Run: pip install pyttsx3")
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.rate)
            self.engine.setProperty("volume", self.volume)
            voices = self.engine.getProperty("voices")

            # Pick gendered voice if possible
            if voices:
                chosen = None
                for v in voices:
                    if self.voice_gender.lower() in v.name.lower():
                        chosen = v
                        break
                if chosen is None:
                    chosen = voices[0]
                self.engine.setProperty("voice", chosen.id)

    def speak_text(self, text: str, async_mode: bool = False):
        """
        Speak the provided text aloud.

        Args:
            text: Text to read.
            async_mode: If True, speaks in a background thread (non-blocking).
        """
        if self.use_gtts:
            self._speak_gtts(text)
        else:
            if async_mode:
                threading.Thread(target=self._speak_pyttsx3, args=(text,), daemon=True).start()
            else:
                self._speak_pyttsx3(text)

    def _speak_pyttsx3(self, text: str):
        """Speak text using pyttsx3 (offline)."""
        if not self.engine:
            raise RuntimeError("pyttsx3 engine not initialized")

        words = text.split()
        # Call on_word_callback per word if provided
        if self.on_word_callback:
            for i, word in enumerate(words):
                self.on_word_callback(word, i)
                self.engine.say(word)
                self.engine.runAndWait()
        else:
            self.engine.say(text)
            self.engine.runAndWait()

    def _speak_gtts(self, text: str):
        """Speak text using Google TTS (requires internet)."""
        if gTTS is None or playsound is None:
            raise ImportError("Please install gTTS and playsound: pip install gTTS playsound")

        tts = gTTS(text=text, lang="en")
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
            temp_file = fp.name
            tts.save(temp_file)
            playsound.playsound(temp_file)

    def stop(self):
        """Stop the speech immediately (only supported for pyttsx3)."""
        if not self.use_gtts and self.engine:
            self.engine.stop()


# ------------------------
# Example usage / demo
# ------------------------
if __name__ == "__main__":
    def on_word(word, index):
        print(f"Speaking word {index}: {word}")

    tts = TextToSpeechEngine(
        use_gtts=False,
        rate=140,
        voice_gender="female",
        on_word_callback=on_word
    )

    sentence = "Hello, I'm Lalit. How are you?"
    print("Speaking sentence...")
    tts.speak_text(sentence)
    print("Done.")
