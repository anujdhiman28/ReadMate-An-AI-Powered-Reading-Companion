"""
feedback_display_engine.py

Feedback Display Engine for the Dyslexia Assistive Reader project.

Features:
- Displays adaptive visual feedback on top of live video feed.
- Color-coded encouragement (Green = positive, Yellow = neutral, Red = retry).
- Integrates accuracy, sentiment, and emotion results.
- Works with OpenCV (camera window).

Usage:
    from feedback_display_engine import FeedbackDisplay

    fb = FeedbackDisplay()
    fb.show_feedback("Good job!", "positive", "neutral", 90)
"""

import cv2
import time
from typing import Optional


class FeedbackDisplay:
    def __init__(self, camera_index: int = 0):
        """
        Initialize the feedback display system.

        Args:
            camera_index: The index of the webcam (default=0).
        """
        self.camera_index = camera_index
        self.cap = None
        self.is_open = False

    def start_camera(self):
        """Start video capture."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Error: Could not open camera.")
        self.is_open = True

    def stop_camera(self):
        """Release camera resources."""
        if self.cap and self.is_open:
            self.cap.release()
            cv2.destroyAllWindows()
            self.is_open = False

    def show_feedback(
        self,
        feedback_message: str,
        sentiment_label: str,
        emotion_label: str,
        accuracy: float,
        duration: float = 5.0,
    ):
        """
        Display feedback message on the camera feed.

        Args:
            feedback_message: Text feedback to show.
            sentiment_label: 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'.
            emotion_label: Emotion detected (e.g., happy, sad, neutral).
            accuracy: Reading accuracy (0–100).
            duration: How long to show the message (seconds).
        """
        if not self.is_open:
            self.start_camera()

        start_time = time.time()

        # Choose color based on feedback tone
        if accuracy >= 85 or sentiment_label.upper() == "POSITIVE":
            color = (0, 255, 0)      # Green
        elif 60 <= accuracy < 85 or sentiment_label.upper() == "NEUTRAL":
            color = (0, 255, 255)    # Yellow
        else:
            color = (0, 0, 255)      # Red

        emotion_text = f"Emotion: {emotion_label.capitalize()}"
        accuracy_text = f"Accuracy: {accuracy:.1f}%"

        while time.time() - start_time < duration:
            ret, frame = self.cap.read()
            if not ret:
                break

            # Dark overlay for better text visibility
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], 150), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

            # Display feedback message
            cv2.putText(frame, feedback_message, (40, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # Display sentiment and emotion info
            cv2.putText(frame, f"Sentiment: {sentiment_label.capitalize()}", (40, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.putText(frame, emotion_text, (400, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Display accuracy score
            cv2.putText(frame, accuracy_text, (40, 145),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            cv2.imshow("Feedback Display", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.stop_camera()