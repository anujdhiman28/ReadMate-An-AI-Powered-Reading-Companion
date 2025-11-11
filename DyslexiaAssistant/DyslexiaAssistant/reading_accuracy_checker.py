"""
reading_accuracy_checker.py

Reading Accuracy Checker for the Dyslexia Assistive Reader project.

Features:
- Compares displayed text (expected) with recognized speech (actual).
- Detects missed, extra, and mispronounced words.
- Calculates word-level accuracy and error breakdown.
- Provides detailed feedback for adaptive learning.

Usage:
    from reading_accuracy_checker import ReadingAccuracyChecker

    checker = ReadingAccuracyChecker()
    result = checker.evaluate("The quick brown fox jumps over the lazy dog",
                              "The brown fox jumped over lazy dog")

    print(result)
"""

from difflib import SequenceMatcher
from typing import Dict, List


class ReadingAccuracyChecker:
    def __init__(self, similarity_threshold: float = 0.75):
        """
        Initialize the reading accuracy checker.

        Args:
            similarity_threshold: Minimum ratio (0–1) to consider two words similar enough
                                  to be counted as correct (for fuzzy matching).
        """
        self.similarity_threshold = similarity_threshold

    def evaluate(self, expected_text: str, spoken_text: str) -> Dict:
        """
        Compare expected text with spoken text and return accuracy details.

        Args:
            expected_text: The sentence displayed to the user.
            spoken_text: The sentence recognized from the user's speech.

        Returns:
            Dictionary with accuracy score, missed/extra words, and feedback.
        """

        # Normalize: lowercase and split into words
        expected_words = [w.strip(",.!?").lower() for w in expected_text.split()]
        spoken_words = [w.strip(",.!?").lower() for w in spoken_text.split()]

        # Prepare lists for result tracking
        correct_words = []
        missed_words = []
        extra_words = []
        misread_words = []

        # Matching using difflib.SequenceMatcher
        matcher = SequenceMatcher(None, expected_words, spoken_words)
        matches = matcher.get_opcodes()

        for tag, i1, i2, j1, j2 in matches:
            if tag == "equal":
                correct_words.extend(expected_words[i1:i2])
            elif tag == "replace":
                # Check fuzzy similarity for replacements
                for e_word, s_word in zip(expected_words[i1:i2], spoken_words[j1:j2]):
                    if self._is_similar(e_word, s_word):
                        correct_words.append(e_word)
                    else:
                        misread_words.append((e_word, s_word))
            elif tag == "delete":
                missed_words.extend(expected_words[i1:i2])
            elif tag == "insert":
                extra_words.extend(spoken_words[j1:j2])

        # Calculate word-level accuracy
        total_words = len(expected_words)
        correct_count = len(correct_words)
        accuracy = (correct_count / total_words) * 100 if total_words > 0 else 0

        # Generate feedback message
        feedback = self._generate_feedback(accuracy, missed_words, misread_words, extra_words)

        return {
            "expected_text": expected_text,
            "spoken_text": spoken_text,
            "accuracy_percent": round(accuracy, 2),
            "correct_words": correct_words,
            "missed_words": missed_words,
            "extra_words": extra_words,
            "misread_words": misread_words,
            "feedback": feedback,
        }

    def _is_similar(self, w1: str, w2: str) -> bool:
        """Check fuzzy similarity between two words."""
        return SequenceMatcher(None, w1, w2).ratio() >= self.similarity_threshold

    def _generate_feedback(
        self,
        accuracy: float,
        missed: List[str],
        misread: List[tuple],
        extra: List[str],
    ) -> str:
        """Generate a friendly feedback message based on results."""
        if accuracy >= 90:
            message = "Excellent reading! You got almost everything right."
        elif accuracy >= 70:
            message = "Good effort! A few small mistakes, but you're doing great."
        elif accuracy >= 50:
            message = "You're improving! Let's try again and focus on tricky words."
        else:
            message = "Keep practicing — we’ll make it easier next round."

        # Add detail about errors
        if missed:
            message += f"\nYou missed these words: {', '.join(missed)}."
        if misread:
            wrong = [f"'{s}' instead of '{e}'" for e, s in misread]
            message += f"\nMisread words: {', '.join(wrong)}."
        if extra:
            message += f"\nExtra words you said: {', '.join(extra)}."

        return message
