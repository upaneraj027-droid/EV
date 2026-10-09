# backend/assistant/state.py
#
# EV State Machine
#
# Tracks the assistant's current state and emits a Qt signal whenever
# the state changes so the UI can update the visual indicator.

from enum import Enum, auto
from PySide6.QtCore import QObject, Signal


class AssistantState(Enum):
    """
    All possible states EV can be in at any moment.

    IDLE      — waiting for input
    LISTENING — microphone is active, capturing voice
    THINKING  — request sent to Gemini, waiting for response
    SPEAKING  — TTS is playing the response
    ERROR     — something went wrong (shown briefly before returning to IDLE)
    """
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    ERROR = auto()


# Human-readable labels shown in the status bar
STATE_LABELS: dict[AssistantState, str] = {
    AssistantState.IDLE: "IDLE",
    AssistantState.LISTENING: "LISTENING",
    AssistantState.THINKING: "THINKING",
    AssistantState.SPEAKING: "SPEAKING",
    AssistantState.ERROR: "ERROR",
}


class StateManager(QObject):
    """
    Manages EV's current state and broadcasts changes via Qt signals.

    The UI connects to `state_changed` to update the visual indicator,
    status label, and enable/disable controls appropriately.
    """

    # Emitted whenever the state changes; carries the new AssistantState
    state_changed = Signal(object)  # object = AssistantState

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state = AssistantState.IDLE

    @property
    def current(self) -> AssistantState:
        """Return the current state."""
        return self._state

    def set_state(self, new_state: AssistantState) -> None:
        """
        Transition to a new state and emit state_changed signal.

        Args:
            new_state: The AssistantState to transition to.
        """
        if new_state != self._state:
            print(f"[StateManager] {self._state.name} → {new_state.name}")
            self._state = new_state
            self.state_changed.emit(new_state)

    def label(self) -> str:
        """Return the human-readable label for the current state."""
        return STATE_LABELS.get(self._state, "UNKNOWN")
