# tests/test_state.py
#
# Tests for the StateManager (IDLE/LISTENING/THINKING/SPEAKING/ERROR)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import MagicMock

# PySide6 requires a QApplication to exist before any QObject is created.
# We create a minimal one here for testing purposes.
from PySide6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

from backend.assistant.state import StateManager, AssistantState, STATE_LABELS


class TestAssistantState:
    def test_all_states_defined(self):
        """All five states must be defined."""
        states = list(AssistantState)
        assert AssistantState.IDLE in states
        assert AssistantState.LISTENING in states
        assert AssistantState.THINKING in states
        assert AssistantState.SPEAKING in states
        assert AssistantState.ERROR in states

    def test_all_states_have_labels(self):
        """Every state must have a corresponding label string."""
        for state in AssistantState:
            assert state in STATE_LABELS
            assert isinstance(STATE_LABELS[state], str)
            assert len(STATE_LABELS[state]) > 0


class TestStateManager:
    def test_initial_state_is_idle(self):
        manager = StateManager()
        assert manager.current == AssistantState.IDLE

    def test_set_state_changes_current(self):
        manager = StateManager()
        manager.set_state(AssistantState.THINKING)
        assert manager.current == AssistantState.THINKING

    def test_set_state_emits_signal(self):
        manager = StateManager()
        received = []
        manager.state_changed.connect(lambda s: received.append(s))

        manager.set_state(AssistantState.LISTENING)
        assert len(received) == 1
        assert received[0] == AssistantState.LISTENING

    def test_same_state_does_not_emit(self):
        """Setting the same state twice should not emit a second signal."""
        manager = StateManager()
        received = []
        manager.state_changed.connect(lambda s: received.append(s))

        manager.set_state(AssistantState.IDLE)  # already IDLE
        assert len(received) == 0

    def test_label_returns_string(self):
        manager = StateManager()
        for state in AssistantState:
            manager.set_state(state)
            label = manager.label()
            assert isinstance(label, str)
            assert len(label) > 0

    def test_full_cycle(self):
        """Cycle through all states and verify each transition."""
        manager = StateManager()
        cycle = [
            AssistantState.LISTENING,
            AssistantState.THINKING,
            AssistantState.SPEAKING,
            AssistantState.IDLE,
        ]
        received = []
        manager.state_changed.connect(lambda s: received.append(s))

        for state in cycle:
            manager.set_state(state)

        assert received == cycle
