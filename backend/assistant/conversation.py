# backend/assistant/conversation.py
#
# Conversation Manager
#
# The single source of truth for all conversation state. It owns the message
# history, calls the GeminiService, and formats responses. The UI should never
# talk to Gemini directly — it always goes through ConversationManager.

from __future__ import annotations
from PySide6.QtCore import QObject, Signal

from backend.ai.gemini import GeminiService
from backend.assistant.response import ResponseFormatter
from backend.skills.registry import SkillRegistry


class ConversationManager(QObject):
    """
    Manages the full conversation lifecycle.

    Responsibilities:
    - Maintains message history (list of role/content dicts)
    - Routes user messages → SkillRegistry → GeminiService
    - Formats and returns responses
    - Emits Qt signals so the UI stays reactive without polling

    Signals:
        response_ready(display_text, tts_text)  — fired when a response is ready
        error_occurred(message)                  — fired on any error
    """

    # str: display-ready text, str: TTS-ready text
    response_ready = Signal(str, str)

    # str: human-readable error message
    error_occurred = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._history: list[dict[str, str]] = []
        self._gemini = GeminiService()
        self._skill_registry = SkillRegistry()
        # V2: register skills here, e.g. self._skill_registry.register(BrowserSkill())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, user_message: str) -> tuple[str, str]:
        """
        Process a user message, emit response_ready, and return (display_text, tts_text).
        """
        try:
            display_text, tts_text = self.send_sync(user_message)
            if display_text:
                self.response_ready.emit(display_text, tts_text)
            return display_text, tts_text
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            return "", ""

    def send_sync(self, user_message: str) -> tuple[str, str]:
        """
        Process a user message and return (display_text, tts_text) directly.

        This is the thread-safe version called from ConversationWorker (QThread).
        It returns values directly rather than emitting signals, avoiding Qt's
        queued-connection deadlock when called from a non-main thread.

        Args:
            user_message: The raw text typed or spoken by the user.

        Returns:
            Tuple of (display_text, tts_text).

        Raises:
            RuntimeError: If Gemini returns an error or empty response.
        """
        user_message = user_message.strip()
        if not user_message:
            return "", ""

        # Add user turn to history
        self._history.append({"role": "user", "content": user_message})

        try:
            # V2+: Intent detection → SkillRegistry.route(intent)
            # For V1, skill routing is disabled (route always returns None).
            raw_response = self._gemini.send(self._history)

            # Store assistant response in history
            self._history.append({"role": "model", "content": raw_response})

            display_text = ResponseFormatter.for_display(raw_response)
            tts_text = ResponseFormatter.for_tts(raw_response)
            return display_text, tts_text

        except Exception as exc:  # noqa: BLE001
            # Roll back the user message so history stays consistent
            self._history.pop()
            raise RuntimeError(f"Error communicating with Gemini: {exc}") from exc



    def clear_history(self) -> None:
        """
        Clear the conversation history.

        The next message will start a fresh conversation without any prior
        context. Useful for switching topics or resetting EV.
        """
        self._history.clear()
        print("[ConversationManager] Conversation history cleared.")

    def get_history(self) -> list[dict[str, str]]:
        """
        Return a copy of the current conversation history.

        Returns:
            list of dicts with keys 'role' and 'content'.
        """
        return list(self._history)

    @property
    def message_count(self) -> int:
        """Number of messages (user + model) in the current conversation."""
        return len(self._history)
