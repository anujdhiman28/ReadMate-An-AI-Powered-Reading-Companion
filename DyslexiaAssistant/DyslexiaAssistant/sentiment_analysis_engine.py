"""
sentiment_analysis_engine.py

Sentiment Analysis Engine for the Dyslexia Assistive Reader project.

Features:
- Uses a transformer-based model to detect sentiment or tone from text.
- Works with transcribed speech (from SpeechRecognitionEngine).
- Can classify text into positive, negative, or neutral tone.
- Returns label and confidence score.

Usage:
    from sentiment_analysis_engine import SentimentAnalyzer

    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("I think I can do this easily!")
    print(result)
"""

from transformers import pipeline
from typing import Dict

class SentimentAnalyzer:
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize the sentiment analysis model.

        Args:
            model_name: Name of the Hugging Face sentiment analysis model.
        """
        print(f"Loading sentiment model: {model_name} ...")
        self.analyzer = pipeline("sentiment-analysis", model=model_name)

    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of given text.

        Args:
            text: Input text (e.g., recognized speech).

        Returns:
            dict: {
                "label": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
                "confidence": float (0–1)
            }
        """
        if not text.strip():
            return {"label": "NEUTRAL", "confidence": 0.0}

        result = self.analyzer(text)[0]
        label = result["label"]
        score = result["score"]

        # Convert binary (positive/negative) to three-class style
        if score < 0.6:
            label = "NEUTRAL"

        return {"label": label, "confidence": round(score, 3)}


# -----------------------
# Example usage / demo
# -----------------------
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()

    sentences = [
        "I can’t do this, it’s too hard.",
        "I think I can get it right this time!",
        "Hmm, I’m not sure about this part.",
    ]

    for s in sentences:
        result = analyzer.analyze(s)
        print(f"Text: {s}")
        print(f"Sentiment: {result['label']} (Confidence: {result['confidence']})")
        print()