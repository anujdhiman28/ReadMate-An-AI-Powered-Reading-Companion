"""
text_display_engine.py

Text Display Engine for dyslexia-friendly text presentation.

Features:
- Tkinter-based window (preferred) that renders text in large size with adjustable
  line-spacing and letter-spacing. Supports word highlighting.
- OpenCV overlay helper to draw the same style onto video frames if you prefer overlay.
- Attempts to use OpenDyslexic font if provided; falls back to a system font.

Usage:
    python text_display_engine.py
"""

import os
import math
import textwrap
import threading
from typing import Optional, Tuple, List

try:
    import tkinter as tk
    from tkinter import font as tkfont
except Exception:
    tk = None

try:
    import cv2
except Exception:
    cv2 = None


class TextDisplayEngine:
    def __init__(
        self,
        font_path: Optional[str] = None,
        font_family: str = "OpenDyslexic",
        font_size: int = 48,
        line_spacing: int = 12,
        letter_spacing: int = 2,
        max_chars_per_line: int = 40,
        window_size: Tuple[int, int] = (900, 300),
        bg_color: str = "#F7F7F7",
        text_color: str = "#222222",
    ):
        """
        Create a display engine.

        Args:
            font_path: path to a .ttf font file (e.g., OpenDyslexic). Optional.
            font_family: font family name to use (fallbacks if font_path not provided).
            font_size: base font size in points.
            line_spacing: extra vertical pixels between lines.
            letter_spacing: extra horizontal pixels between characters.
            max_chars_per_line: wrap length for text wrapping.
            window_size: (width, height) for Tkinter window.
            bg_color / text_color: colors for UI.
        """
        self.font_path = font_path
        self.font_family = font_family
        self.font_size = font_size
        self.line_spacing = line_spacing
        self.letter_spacing = letter_spacing
        self.max_chars_per_line = max_chars_per_line
        self.window_size = window_size
        self.bg_color = bg_color
        self.text_color = text_color

        # internal state
        self.current_sentence = ""
        self.word_positions: List[Tuple[int, int, int, int]] = []  # (x, y, w, h) per word
        self.highlight_index: Optional[int] = None

        # Tkinter attributes
        self.root = None
        self.canvas = None
        self.tk_font = None
        self._tk_thread = None
        self._tk_ready = threading.Event()
        self._running = False

        if tk is None:
            raise RuntimeError("Tkinter is required for the Tkinter backend. Install tkinter for your Python.")

        # Try to register font if a font_path is provided
        if font_path and os.path.isfile(font_path):
            try:
                # On some platforms we can register a font using tkfont.Font with file (Windows often auto-detects)
                # This is best-effort — if it fails we fall back to family name.
                import platform
                if platform.system() == "Windows":
                    # Windows: adding font to tk's font families may work by creating a Font object
                    pass
                # we'll still set family name; user can ensure font is available system-wide if needed
            except Exception:
                pass

    # -----------------------------
    # Tkinter-based display methods
    # -----------------------------
    def start_tk(self):
        """Start the Tkinter window in a background thread (non-blocking)."""
        if self._running:
            return
        self._tk_thread = threading.Thread(target=self._tk_loop, daemon=True)
        self._tk_thread.start()
        # wait until ready
        self._tk_ready.wait(timeout=5)

    def _tk_loop(self):
        self.root = tk.Tk()
        self.root.title("Assistive Reader")
        w, h = self.window_size
        self.root.geometry(f"{w}x{h}")
        self.root.configure(bg=self.bg_color)

        # Create canvas
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Create font
        try:
            if self.font_path and os.path.isfile(self.font_path):
                # If a TTF is provided, use tk's font create with family may still work; try using file name
                self.tk_font = tkfont.Font(family=self.font_family, size=self.font_size)
            else:
                self.tk_font = tkfont.Font(family=self.font_family, size=self.font_size)
        except Exception:
            # Fallback to default font
            self.tk_font = tkfont.Font(size=self.font_size)

        self._running = True
        self._tk_ready.set()
        # Run the Tkinter mainloop (blocking this thread)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self._running = False
        if self.root:
            self.root.destroy()

    def stop_tk(self):
        """Stop Tkinter window and thread."""
        self._running = False
        if self.root:
            try:
                self.root.quit()
            except Exception:
                pass
        if self._tk_thread:
            self._tk_thread.join(timeout=2)

    def show_sentence(self, sentence: str, highlight_word_index: Optional[int] = None):
        """
        Display a sentence on the Tkinter canvas. This is non-blocking if Tk is started in background.
        It will replace previous text.

        Args:
            sentence: the sentence to display.
            highlight_word_index: optional index of a word to highlight (0-based).
        """
        self.current_sentence = sentence
        self.highlight_index = highlight_word_index

        if not self._running or not self.canvas:
            # If Tk hasn't been started, start it
            self.start_tk()
            # wait a short moment to ensure canvas exists
            self._tk_ready.wait(timeout=2)

        # Draw on canvas via thread-safe after()
        self.canvas.after(0, lambda: self._render_to_canvas(sentence, highlight_word_index))

    def _render_to_canvas(self, sentence: str, highlight_word_index: Optional[int]):
        """Internal: draw the sentence with spacing and optional highlight."""
        c = self.canvas
        c.delete("all")
        width = int(c.winfo_width())
        height = int(c.winfo_height())

        # Basic wrap: use textwrap to get lines under max_chars_per_line
        lines = textwrap.wrap(sentence, width=self.max_chars_per_line)

        top_margin = 20
        x_start = 30
        y = top_margin

        self.word_positions.clear()

        for line in lines:
            # draw characters with letter spacing to simulate improved readability
            x = x_start
            words = line.split(" ")
            for wi, w in enumerate(words):
                # Draw word as sequence of characters so we can compute width for highlight
                char_x = x
                word_bbox_x0 = char_x
                for ch in w:
                    # draw each character
                    c.create_text(char_x, y, text=ch, anchor="nw", font=self.tk_font, fill=self.text_color, tags=("text",))
                    # measure width of character and advance
                    ch_width = self.tk_font.measure(ch)
                    char_x += ch_width + self.letter_spacing
                word_bbox_x1 = char_x

                # measure height roughly by font metrics
                ch_height = self.tk_font.metrics("linespace")

                # store bbox for this word (useful for highlighting)
                self.word_positions.append((word_bbox_x0, y, word_bbox_x1 - word_bbox_x0, ch_height))

                # draw space
                space_width = self.tk_font.measure(" ")
                x = char_x + space_width + self.letter_spacing

            # Move to next line
            y += self.tk_font.metrics("linespace") + self.line_spacing

        # After drawing words, draw highlight if requested
        if highlight_word_index is not None and 0 <= highlight_word_index < len(self.word_positions):
            bx, by, bw, bh = self.word_positions[highlight_word_index]
            # Draw a rounded-ish rectangle behind the word
            pad_x = 6
            pad_y = 4
            c.create_rectangle(bx - pad_x, by - pad_y, bx + bw + pad_x, by + bh + pad_y,
                               fill="#FFF59D", outline="")

    # -----------------------------
    # OpenCV overlay helper
    # -----------------------------
    @staticmethod
    def overlay_text_on_frame(
        frame,
        sentence: str,
        font_scale: float = 1.0,
        thickness: int = 2,
        max_chars_per_line: int = 40,
        line_spacing_px: int = 12,
        letter_spacing_px: int = 3,
        highlight_word_index: Optional[int] = None,
        text_color: Tuple[int, int, int] = (30, 30, 30),
        bg_color: Tuple[int, int, int] = (247, 247, 247),
        box_color: Tuple[int, int, int] = (0, 0, 0),
    ):
        """
        Draw dyslexia-friendly text onto an OpenCV frame. Returns modified frame.

        Args:
            frame: OpenCV BGR image
            sentence: text to draw
            highlight_word_index: optional index of a word to highlight
        """
        if cv2 is None:
            raise RuntimeError("OpenCV not available")

        h, w, _ = frame.shape
        # draw a semi-opaque background rectangle at bottom
        rect_h = 120
        overlay = frame.copy()
        alpha = 0.75
        cv2.rectangle(overlay, (0, h - rect_h), (w, h), bg_color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # wrap text
        lines = textwrap.wrap(sentence, width=max_chars_per_line)
        y = h - rect_h + 15
        x_start = 30

        # simple word bbox tracking for highlight
        all_word_bboxes = []

        for line in lines:
            x = x_start
            words = line.split(" ")
            for wi, word in enumerate(words):
                # draw each char separately to simulate letter spacing
                word_x0 = x
                for ch in word:
                    ((ch_w, ch_h), _) = cv2.getTextSize(ch, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                    cv2.putText(frame, ch, (int(x), int(y + ch_h)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness, cv2.LINE_AA)
                    x += ch_w + letter_spacing_px
                word_x1 = x
                all_word_bboxes.append((word_x0, y, int(word_x1 - word_x0), int(ch_h)))
                # space
                space_w = cv2.getTextSize(" ", cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0][0]
                x += space_w + letter_spacing_px
            y += ch_h + line_spacing_px

        # draw highlight if requested
        if highlight_word_index is not None and 0 <= highlight_word_index < len(all_word_bboxes):
            bx, by, bw_box, bh_box = all_word_bboxes[highlight_word_index]
            pad_x = 6
            pad_y = 6
             # highlight as filled rectangle with alpha
            cv2.rectangle(frame, (int(bx - pad_x), int(by - pad_y)), (int(bx + bw_box + pad_x), int(by + bh_box + pad_y)), (0, 165, 255), -1)
            # redraw the word on top
            bx_text = int(bx)
            by_text = int(by + bh_box)
            # re-draw the characters of that word (for simplicity we'll re-render the full line)
            # (In many use-cases the highlight suffices.)

        return frame


# ------------------------
# Example usage / demo
# ------------------------
if __name__ == "__main__":
    import time

    # Example: try to auto-locate OpenDyslexic if present in a fonts folder (optional).
    possible_paths = [
        "./OpenDyslexic-Regular.otf",
        "./OpenDyslexic3-Regular.ttf",
        os.path.expanduser("~/fonts/OpenDyslexic-Regular.otf"),
    ]
    font_path = None
    for p in possible_paths:
        if os.path.isfile(p):
            font_path = p
            break

    engine = TextDisplayEngine(
        font_path=font_path,
        font_family="OpenDyslexic",
        font_size=48,
        line_spacing=12,
        letter_spacing=2,
        max_chars_per_line=40,
        window_size=(1000, 300),
        bg_color="#FAF9F6",
        text_color="#222222",
    )

    engine.start_tk()
    # Demo sentence
    sentence = "Hello, I'm Lalit. How are you?"

    # show sentence, then highlight each word sequentially (simulate TTS)
    engine.show_sentence(sentence)
    time.sleep(1.0)

    words = sentence.split()
    for i in range(len(words)):
        engine.show_sentence(sentence, highlight_word_index=i)
        # in a real system you'd time this to TTS progress; here we just sleep
        time.sleep(0.7)

    # leave final sentence on screen
    engine.show_sentence(sentence, highlight_word_index=None)
    print("Demo running. Close the window to exit.")
    # Wait until user closes window
    while engine._running:
        time.sleep(0.3)

    engine.stop_tk()
    print("Exiting demo.")
