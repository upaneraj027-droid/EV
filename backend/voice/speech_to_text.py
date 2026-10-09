# backend/voice/speech_to_text.py
#
# Speech-to-Text (STT)
#
# Runs in a QThread so the UI never freezes while waiting for microphone input.
# Uses the `speech_recognition` library with Google's free web STT service.
#
# To swap in a different STT engine (Whisper, Deepgram, etc.) in a future
# version, only this file needs to change.

from __future__ import annotations
from PySide6.QtCore import QThread, Signal


class SpeechToTextWorker(QThread):
    """
    Background thread that captures microphone audio and transcribes it.

    Runs in push-to-talk mode for V1 (MVP):
    - start() activates the microphone immediately
    - The thread listens until speech ends or timeout occurs
    - result_ready is emitted with the transcribed text
    - error_occurred is emitted if something goes wrong

    Signals:
        result_ready(text)   — transcribed text from the user's speech
        error_occurred(msg)  — human-readable error message
    """

    result_ready = Signal(str)
    error_occurred = Signal(str)

    def run(self) -> None:
        """Main thread body — capture and transcribe audio."""
        try:
            import speech_recognition as sr
        except ImportError:
            self.error_occurred.emit(
                "speech_recognition is not installed. Run: pip install speechrecognition"
            )
            return

        recognizer = sr.Recognizer()

        # Sensitive thresholds so speech is captured instantly without clipping the first words
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_damping = 0.15
        recognizer.dynamic_energy_ratio = 1.5
        recognizer.pause_threshold = 0.8  # 0.8s silence completes speech
        recognizer.non_speaking_duration = 0.4

        try:
            with sr.Microphone() as source:
                print("[STT] Microphone opened. Listening now...")
                # listen() blocks until speech is detected and finished
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=20)
                print("[STT] Audio captured, sending to recognizer...")

        except sr.WaitTimeoutError:
            print("[STT] WaitTimeoutError: No speech detected.")
            self.error_occurred.emit("No speech detected. Please press the mic and speak clearly.")
            return
        except OSError as exc:
            print(f"[STT] Microphone OSError: {exc}")
            self.error_occurred.emit(
                f"Microphone access error: {exc}. Please check your Mac audio input settings."
            )
            return
        except Exception as exc:  # noqa: BLE001
            print(f"[STT] Audio capture error: {exc}")
            self.error_occurred.emit(f"Microphone error: {exc}")
            return

        # Transcribe audio
        print("[STT] Transcribing audio with Google Speech...")
        try:
            text = recognizer.recognize_google(audio)
            print(f"[STT] Transcribed successfully: {text!r}")
            self.result_ready.emit(text)
        except sr.UnknownValueError:
            print("[STT] UnknownValueError: audio was not recognized.")
            self.error_occurred.emit(
                "Could not understand audio. Please speak a little louder or closer to the mic."
            )
        except sr.RequestError as exc:
            print(f"[STT] Google STT RequestError: {exc}")
            self.error_occurred.emit(
                f"Speech recognition service error: {exc}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[STT] Transcription error: {exc}")
            self.error_occurred.emit(f"Speech recognition error: {exc}")
