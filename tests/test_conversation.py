# tests/test_conversation.py
#
# Tests for ConversationManager history management.
# The Gemini API call is mocked so tests run without a real API key.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manager(fake_response: str = "Mock response"):
    """
    Create a ConversationManager with GeminiService mocked out at the class
    level so __init__ never tries to read GEMINI_API_KEY from the environment.
    Returns (manager, mock_gemini_send).
    """
    # Build a mock GeminiService instance whose send() returns fake_response
    mock_gemini_instance = MagicMock()
    mock_send = MagicMock(return_value=fake_response)
    mock_gemini_instance.send = mock_send

    # Patch GeminiService so ConversationManager() never touches the real class
    with patch("backend.assistant.conversation.GeminiService",
               return_value=mock_gemini_instance):
        from backend.assistant.conversation import ConversationManager
        manager = ConversationManager()

    return manager, mock_send


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestConversationManager:
    def test_initial_history_is_empty(self):
        manager, _ = _make_manager()
        assert manager.get_history() == []
        assert manager.message_count == 0

    def test_send_adds_user_and_model_turns(self):
        manager, _ = _make_manager("AI answer")
        manager.send("Hello EV")
        history = manager.get_history()
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello EV"}
        assert history[1] == {"role": "model", "content": "AI answer"}

    def test_send_accumulates_history(self):
        manager, _ = _make_manager("Response")
        manager.send("First message")
        manager.send("Second message")
        assert manager.message_count == 4  # 2 user + 2 model turns

    def test_send_passes_full_history_to_gemini(self):
        manager, mock_send = _make_manager("OK")
        manager.send("Tell me about black holes")
        manager.send("How are they formed?")

        # Gemini should have been called exactly twice (once per send)
        assert mock_send.call_count == 2

        # After both sends the full history is 4 items: user, model, user, model
        history = manager.get_history()
        assert len(history) == 4
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "model"
        assert history[2]["role"] == "user"
        assert "How are they formed?" in history[2]["content"]

    def test_clear_history(self):
        manager, _ = _make_manager()
        manager.send("Hello")
        assert manager.message_count == 2
        manager.clear_history()
        assert manager.message_count == 0
        assert manager.get_history() == []

    def test_blank_message_not_sent(self):
        manager, mock_send = _make_manager()
        manager.send("   ")
        mock_send.assert_not_called()
        assert manager.message_count == 0

    def test_response_ready_signal_emitted(self):
        manager, _ = _make_manager("Hello from Gemini")
        received = []
        manager.response_ready.connect(lambda d, t: received.append((d, t)))
        manager.send("Hi")
        assert len(received) == 1
        display_text, tts_text = received[0]
        assert "Hello from Gemini" in display_text

    def test_error_does_not_pollute_history(self):
        """If Gemini raises an exception, the user message should be removed."""
        manager, mock_send = _make_manager()
        mock_send.side_effect = RuntimeError("API down")

        errors = []
        manager.error_occurred.connect(lambda e: errors.append(e))

        manager.send("This will fail")

        # History should be empty — user turn must be rolled back
        assert manager.message_count == 0
        assert len(errors) == 1

    def test_get_history_returns_copy(self):
        """Modifying the returned list should not affect internal history."""
        manager, _ = _make_manager("R")
        manager.send("Q")
        h = manager.get_history()
        h.clear()
        assert manager.message_count == 2  # original still intact
