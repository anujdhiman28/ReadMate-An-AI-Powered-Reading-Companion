import time
from speech_recognition_engine import SpeechRecognitionEngine
from reading_accuracy_checker import ReadingAccuracyChecker
from sentiment_analysis_engine import SentimentAnalyzer
from face_emotion_engine import FaceEmotionEngine
from adaptation_logic import AdaptationLogic
from feedback_display_engine import FeedbackDisplay
from progress_tracker import ProgressTracker


def main():
    print("\n=== Debug-Friendly Dyslexia Assistive Reader ===\n")

    # --- Initialize components ---
    speech_engine = SpeechRecognitionEngine(use_whisper=False)
    accuracy_checker = ReadingAccuracyChecker()
    sentiment_engine = SentimentAnalyzer()
    emotion_engine = FaceEmotionEngine()
    adapt_engine = AdaptationLogic()
    feedback_engine = FeedbackDisplay()
    tracker = ProgressTracker(use_sqlite=False)

    # --- Sentence to read ---
    expected_text = "Read this: six wet men had nine earphones"
    print(f"Please read aloud:\n> {expected_text}\n")

    # --- Step 1: detect emotion (1 snapshot only) ---
    print("Opening camera for 3 seconds to capture emotion ...")
    emotion = emotion_engine.detect_emotion(display=False)
    if not emotion:
        emotion = {"emotion": "neutral", "confidence": 0.0}
    print("Detected emotion:", emotion)

    # --- Step 2: record short audio ---
    print("\nListening for 5–8 seconds. Start speaking now ...")
    speech_engine.recognizer.pause_threshold = 0.8
    speech_engine.recognizer.phrase_time_limit = 8
    spoken_text = speech_engine.listen_and_transcribe()
    print("\nRecognized speech:", spoken_text)

    if not spoken_text:
        print("No valid speech detected. Exiting.")
        return

    # --- Step 3: accuracy & sentiment ---
    accuracy = accuracy_checker.evaluate(expected_text, spoken_text)
    sentiment = sentiment_engine.analyze(spoken_text)
    print(f"\nAccuracy = {accuracy['accuracy_percent']:.1f}%  |  Sentiment = {sentiment['label']}")

    # --- Step 4: adaptation ---
    decision = adapt_engine.decide_adaptation(accuracy, sentiment, emotion)
    print("\nAdaptive feedback:", decision["feedback_message"])

    # --- Step 5: visual feedback ---
    print("\nDisplaying feedback window for 5 seconds ... (press q to close)")
    feedback_engine.show_feedback(
        feedback_message=decision["feedback_message"],
        sentiment_label=sentiment["label"],
        emotion_label=emotion["emotion"],
        accuracy=accuracy["accuracy_percent"],
        duration=5,
    )

    # --- Step 6: log progress ---
    tracker.log_session(
        accuracy=accuracy["accuracy_percent"],
        sentiment=sentiment["label"],
        emotion=emotion["emotion"],
        level=decision["new_level"],
        feedback=decision["feedback_message"],
    )
    tracker.summarize_progress()

    print("\n✅ Done.")


if __name__ == "__main__":
    main()
