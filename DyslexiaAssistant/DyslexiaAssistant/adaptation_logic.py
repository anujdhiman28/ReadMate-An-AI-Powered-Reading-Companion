"""
adaptation_logic.py

Adaptation Logic Engine for the Dyslexia Assistive Reader project.

Purpose:
- Adjust text speed, difficulty, and tone dynamically.
- Simplify text if user shows confusion or low accuracy.
- Generate adaptive feedback and reading suggestions.

Inputs:
    - accuracy_result (from ReadingAccuracyChecker)
    - sentiment_result (from SentimentAnalyzer)
    - emotion_result (from FaceEmotionEngine)

Outputs:
    - Adaptation decision (new reading pace, text complexity level, feedback message)
"""

from transformers import pipeline
from typing import Dict, Optional


class AdaptationLogic:
    def __init__(self):
        """Initialize simplification and adaptation pipeline."""
        # T5 small is light and effective for paraphrasing/simplification
        self.simplifier = pipeline("text2text-generation", model="t5-small")

        # Default reading pace (words per minute)
        self.base_speed = 150
        self.current_level = 1  # 1 = easy, 2 = moderate, 3 = challenging

    def decide_adaptation(
        self,
        accuracy_result: Dict,
        sentiment_result: Dict,
        emotion_result: Optional[Dict] = None,
    ) -> Dict:
        """
        Decide how to adapt the next reading task.

        Args:
            accuracy_result: Dict from ReadingAccuracyChecker.
            sentiment_result: Dict from SentimentAnalyzer.
            emotion_result: Dict from FaceEmotionEngine (optional).

        Returns:
            Dict with:
                - speed (adjusted speech rate)
                - simplify_text (bool)
                - feedback_message (str)
                - new_level (int)
        """

        accuracy = accuracy_result.get("accuracy_percent", 0)
        sentiment = sentiment_result.get("label", "NEUTRAL").upper()
        emotion = emotion_result["emotion"].lower() if emotion_result else "neutral"

        simplify = False
        feedback = ""
        new_speed = self.base_speed
        level_change = 0

        # --- Adapt based on accuracy ---
        if accuracy >= 90:
            feedback += "Excellent reading! Let's try something a bit more challenging. "
            new_speed += 10
            level_change = +1
        elif 70 <= accuracy < 90:
            feedback += "Good job! You’re improving steadily. Keep practicing. "
            new_speed += 0
        elif 50 <= accuracy < 70:
            feedback += "Nice effort! Let’s slow down a bit and simplify the next sentence. "
            simplify = True
            new_speed -= 15
            level_change = -1
        else:
            feedback += "You’re doing great — let’s take it step by step. I’ll make the next line easier. "
            simplify = True
            new_speed -= 20
            level_change = -1

        # --- Adapt based on sentiment and emotion ---
        if sentiment == "NEGATIVE" or emotion in ["sad", "angry", "fear", "disgust"]:
            feedback += "You sound frustrated — take a deep breath, we’ll slow down."
            simplify = True
            new_speed -= 10
        elif sentiment == "POSITIVE" or emotion in ["happy", "surprise"]:
            feedback += "Great confidence! Keep that energy up!"
            new_speed += 5
        elif sentiment == "NEUTRAL" and emotion == "neutral":
            feedback += "Let’s keep going at the same pace."

        # Clamp reading speed
        new_speed = max(100, min(new_speed, 200))

        # Update difficulty level
        self.current_level = max(1, min(self.current_level + level_change, 3))

        return {
            "speed": new_speed,
            "simplify_text": simplify,
            "feedback_message": feedback.strip(),
            "new_level": self.current_level,
        }

    def simplify_sentence(self, sentence: str) -> str:
        """
        Simplify or paraphrase a sentence to an easier level using T5.

        Args:
            sentence: Original text.

        Returns:
            Simplified sentence.
        """
        try:
            prompt = f"simplify: {sentence}"
            result = self.simplifier(prompt, max_length=64, do_sample=False)[0]["generated_text"]
            return result.strip().capitalize()
        except Exception:
            # Fallback if simplification fails
            return sentence


# -----------------------
# Example Usage / Demo
# -----------------------
if __name__ == "__main__":
    from pprint import pprint

    adaptation = AdaptationLogic()

    # Mock results from other modules
    accuracy_result = {"accuracy_percent": 62}
    sentiment_result = {"label": "NEGATIVE", "confidence": 0.93}
    emotion_result = {"emotion": "sad", "confidence": 0.88}

    decision = adaptation.decide_adaptation(
        accuracy_result, sentiment_result, emotion_result
    )

    print("\n--- Adaptation Decision ---")
    pprint(decision)

    if decision["simplify_text"]:
        text = "Photosynthesis is the process by which green plants convert light energy into chemical energy."
        simpler = adaptation.simplify_sentence(text)
        print("\nSimplified Sentence:\n", simpler)