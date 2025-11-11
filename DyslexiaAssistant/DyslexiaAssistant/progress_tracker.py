"""
progress_tracker.py

Progress Tracker for the Dyslexia Assistive Reader project.

Features:
- Saves user reading performance per session.
- Logs accuracy, sentiment, emotion, and adaptation results.
- Supports both CSV and SQLite storage.
- Can load and summarize progress trends.

Usage:
    from progress_tracker import ProgressTracker

    tracker = ProgressTracker()
    tracker.log_session(accuracy=82, sentiment="positive", emotion="happy", level=2)
"""

import csv
import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict


class ProgressTracker:
    def __init__(self, use_sqlite: bool = False, db_path: str = "progress.db", csv_path: str = "progress_log.csv"):
        """
        Initialize the progress tracker.

        Args:
            use_sqlite: If True, use SQLite DB; else use CSV.
            db_path: Path for SQLite file.
            csv_path: Path for CSV file.
        """
        self.use_sqlite = use_sqlite
        self.db_path = db_path
        self.csv_path = csv_path

        if self.use_sqlite:
            self._init_db()
        else:
            self._init_csv()

    # --------------------------
    # CSV Functions
    # --------------------------
    def _init_csv(self):
        """Create CSV file if not exists."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "accuracy", "sentiment", "emotion", "level", "feedback"])

    def _log_to_csv(self, data: Dict):
        """Append data to CSV."""
        with open(self.csv_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                data["timestamp"],
                data["accuracy"],
                data["sentiment"],
                data["emotion"],
                data["level"],
                data["feedback"]
            ])

    # --------------------------
    # SQLite Functions
    # --------------------------
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                accuracy REAL,
                sentiment TEXT,
                emotion TEXT,
                level INTEGER,
                feedback TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _log_to_db(self, data: Dict):
        """Insert session record into SQLite DB."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO progress (timestamp, accuracy, sentiment, emotion, level, feedback)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["timestamp"],
            data["accuracy"],
            data["sentiment"],
            data["emotion"],
            data["level"],
            data["feedback"],
        ))
        conn.commit()
        conn.close()

    # --------------------------
    # Logging API
    # --------------------------
    def log_session(self, accuracy: float, sentiment: str, emotion: str, level: int, feedback: str = ""):
        """Record a single reading session."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "timestamp": timestamp,
            "accuracy": accuracy,
            "sentiment": sentiment,
            "emotion": emotion,
            "level": level,
            "feedback": feedback,
        }

        if self.use_sqlite:
            self._log_to_db(data)
        else:
            self._log_to_csv(data)

        print(f"✅ Session logged at {timestamp}")

    # --------------------------
    # Progress Summary
    # --------------------------
    def summarize_progress(self):
        """Show average accuracy and count per sentiment from records."""
        records = []
        if self.use_sqlite:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT accuracy, sentiment FROM progress")
            records = cursor.fetchall()
            conn.close()
        else:
            if not os.path.exists(self.csv_path):
                print("No progress records yet.")
                return
            with open(self.csv_path, "r", encoding="utf-8") as file:
                next(file)  # skip header
                reader = csv.reader(file)
                records = [(float(row[1]), row[2]) for row in reader if row]

        if not records:
            print("No progress data found.")
            return

        total = len(records)
        avg_acc = sum(r[0] for r in records) / total
        sentiments = {}
        for _, s in records:
            sentiments[s] = sentiments.get(s, 0) + 1

        print("\n--- Progress Summary ---")
        print(f"Total Sessions: {total}")
        print(f"Average Accuracy: {avg_acc:.2f}%")
        print("Sentiment Distribution:")
        for s, c in sentiments.items():
            print(f"  {s.capitalize()}: {c}")


# ---------------------
# Example Usage
# ---------------------
if __name__ == "__main__":
    tracker = ProgressTracker(use_sqlite=False)
    tracker.log_session(accuracy=82, sentiment="positive", emotion="happy", level=2, feedback="Good reading speed.")
    tracker.log_session(accuracy=65, sentiment="neutral", emotion="sad", level=1, feedback="Simplified next text.")
    tracker.summarize_progress()
