# frontend/components/status_bar.py
#
# Status Label
#
# Displays the current EV state as text (IDLE / LISTENING / THINKING / SPEAKING / ERROR).
# Updates automatically by connecting to StateManager.state_changed.

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from backend.assistant.state import AssistantState, STATE_LABELS

# State → stylesheet object name for QSS theming
_STATE_STYLE: dict[AssistantState, str] = {
    AssistantState.IDLE:      "statusLabel",
    AssistantState.LISTENING: "statusLabelError",   # red for active recording
    AssistantState.THINKING:  "statusLabel",
    AssistantState.SPEAKING:  "statusLabel",
    AssistantState.ERROR:     "statusLabelError",
}


class StatusLabel(QLabel):
    """
    A QLabel that shows the assistant's current state.

    Connect StateManager.state_changed to this widget's on_state_changed slot.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("statusLabel")
        self.setAlignment(Qt.AlignCenter)
        self.on_state_changed(AssistantState.IDLE)

    def on_state_changed(self, state: AssistantState) -> None:
        """
        Update label text and style for the new state.

        Args:
            state: The new AssistantState.
        """
        label_text = STATE_LABELS.get(state, "UNKNOWN")
        self.setText(f"● {label_text}")

        # Swap object name to change QSS styling
        style_name = _STATE_STYLE.get(state, "statusLabel")
        self.setObjectName(style_name)

        # Force Qt to re-apply the stylesheet for the new object name
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
