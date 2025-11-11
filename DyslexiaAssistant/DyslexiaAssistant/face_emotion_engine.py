"""
face_emotion_engine.py

Face and Emotion Detection Engine for the Dyslexia Assistive Reader project.

Features:
- Detects faces in real-time using OpenCV.
- Uses FER (Facial Emotion Recognition) to detect emotions.
- Returns dominant emotion and confidence score.
- Designed for live video integration.

Usage:
    from face_emotion_engine import FaceEmotionEngine

    engine = FaceEmotionEngine()
    emotion = engine.detect_emotion()
    print(emotion)
"""

import cv2
from fer import FER
from typing import Dict, Optional


class FaceEmotionEngine:
    def __init__(self, camera_index: int = 0):
        """
        Initialize the camera and emotion detector.

        Args:
            camera_index: Default webcam index (0 for primary camera).
        """
        self.camera_index = camera_index
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.emotion_detector = FER(mtcnn=True)  # Uses MTCNN for better face detection

    def detect_emotion(self, display: bool = True) -> Optional[Dict]:
        """
        Starts the webcam, detects face(s) and emotions in real-time.

        Args:
            display: Whether to display the camera feed window.

        Returns:
            Dictionary with detected emotion and confidence score.
            Example: {'emotion': 'happy', 'confidence': 0.94}
        """
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError("Error: Could not open webcam.")

        print("Starting emotion detection... Press 'q' to stop.")

        detected_emotion = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

            # Detect emotions using FER
            emotions = self.emotion_detector.detect_emotions(frame)
            if emotions:
                # Take the first face detected
                top_emotion, confidence = self._get_dominant_emotion(emotions[0]["emotions"])
                detected_emotion = {"emotion": top_emotion, "confidence": confidence}

                # Draw rectangles and labels
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    label = f"{top_emotion.capitalize()} ({confidence:.2f})"
                    cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            else:
                cv2.putText(frame, "No face detected", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Display feed
            if display:
                cv2.imshow("Face & Emotion Detection", frame)

            # Exit condition
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        print("Emotion detection stopped.")

        return detected_emotion

    def _get_dominant_emotion(self, emotion_dict: Dict[str, float]) -> tuple:
        """Return the dominant emotion and its confidence."""
        emotion = max(emotion_dict, key=emotion_dict.get)
        confidence = emotion_dict[emotion]
        return emotion, confidence