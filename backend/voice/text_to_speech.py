# backend/voice/text_to_speech.py
#
# Text-to-Speech (TTS)
#
# Runs in a QThread so speaking never blocks the UI.
# Uses pyttsx3 for offline TTS in V1.
#
# To upgrade to Gemini TTS or a cloud TTS service in V2, only this file changes.

from __future__ import annotations
from PySide6.QtCore import QThread, Signal


class TextToSpeechWorker(QThread):
    """
    Background thread that converts text to speech using pyttsx3.

    Signals:
        finished()           — emitted when speech playback is complete
        error_occurred(msg)  — emitted if TTS fails
    """

    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, text: str, parent=None) -> None:
        """
        Args:
            text: Plain text to be spoken (should already be stripped of markdown).
            parent: Optional Qt parent object.
        """
        super().__init__(parent)
        self._text = text

    def run(self) -> None:
        """Main thread body — initialise engine and speak."""
        try:
            import pyttsx3
        except ImportError:
            self.error_occurred.emit(
                "pyttsx3 is not installed. Run: pip install pyttsx3"
            )
            return

        try:
            engine = pyttsx3.init()

            # Configure voice properties
            engine.setProperty("rate", 175)    # words per minute (default ~200)
            engine.setProperty("volume", 0.9)  # 0.0 – 1.0

            # Optional: pick a voice (system voices vary by OS)
            # voices = engine.getProperty("voices")
            # engine.setProperty("voice", voices[0].id)

            print(f"[TTS] Speaking: {self._text[:60]}...")
            engine.say(self._text)
            engine.runAndWait()
            engine.stop()

            self.finished.emit()

        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"TTS error: {exc}")
