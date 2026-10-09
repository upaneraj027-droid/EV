# frontend/app.py
#
# EV Main Window
#
# The root PySide6 window. Owns the UI layout and connects user actions
# (typing, microphone) to backend services via Qt signals/slots.
#
# Architecture:
#   EVWindow listens for user input →
#   dispatches to ConversationWorker (QThread) →
#   ConversationManager.send_sync() →
#   GeminiService →
#   (display_text, tts_text) returned directly →
#   EVWindow updates UI + triggers TTS

from __future__ import annotations
import sys
import os

from PySide6.QtCore import Qt, QThread, Signal, QObject, QSize
from PySide6.QtGui import QKeySequence, QShortcut, QFont, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QScrollArea, QLabel,
    QFrame, QSizePolicy, QApplication,
)

from backend.assistant.conversation import ConversationManager
from backend.assistant.state import AssistantState, StateManager
from backend.voice.speech_to_text import SpeechToTextWorker
from backend.voice.text_to_speech import TextToSpeechWorker
from frontend.components.ev_core import EVCoreWidget
from frontend.components.chat_bubble import UserBubble, EVBubble
from frontend.components.status_bar import StatusLabel


# ---------------------------------------------------------------------------
# Worker: runs ConversationManager.send_sync() in a background thread.
# Using a direct return value (not cross-thread signal interception) avoids
# the Qt queued-connection deadlock that caused the 30-minute hang.
# ---------------------------------------------------------------------------

class ConversationWorker(QThread):
    """
    Runs the Gemini API call in a background thread so the UI stays responsive.
    Calls ConversationManager.send_sync() which returns directly (no signals).
    """
    finished = Signal(str, str)   # display_text, tts_text
    errored = Signal(str)         # error message

    def __init__(self, manager: ConversationManager, message: str) -> None:
        super().__init__()
        self._manager = manager
        self._message = message

    def run(self) -> None:
        try:
            display_text, tts_text = self._manager.send_sync(self._message)
            self.finished.emit(display_text, tts_text)
        except Exception as exc:  # noqa: BLE001
            self.errored.emit(str(exc))


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class EVWindow(QMainWindow):
    """
    EV's main application window.

    Layout (top → bottom):
        Title bar (EV  ·  version  ·  Clear button)
        EV Core visual + Status label
        Chat scroll area
        Input bar (mic button + text input + send button)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("EV — Personal AI Assistant")
        self.setMinimumSize(700, 600)
        self.resize(800, 680)

        # ── Backend services ──
        self._state_manager = StateManager(self)
        self._conversation = ConversationManager(self)
        self._stt_worker: SpeechToTextWorker | None = None
        self._tts_worker: TextToSpeechWorker | None = None
        self._conv_worker: ConversationWorker | None = None

        # ── Build UI ──
        self._build_ui()
        self._connect_signals()

        # Load welcome message
        self._add_ev_bubble(
            "Hello. I'm EV — your personal AI assistant.\n"
            "How can I help you today?"
        )

    # -----------------------------------------------------------------------
    # UI Construction
    # -----------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_title_bar())
        root.addWidget(self._build_ev_section())
        root.addWidget(self._build_divider())
        root.addWidget(self._build_chat_area(), stretch=1)
        root.addWidget(self._build_divider())
        root.addWidget(self._build_input_bar())

    def _build_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(48)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("E V")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        version = QLabel("v1.0")
        version.setObjectName("versionLabel")
        layout.addWidget(version)

        layout.addStretch()

        clear_btn = QPushButton("✕  Clear")
        clear_btn.setObjectName("clearButton")
        clear_btn.setToolTip("Clear conversation history")
        clear_btn.clicked.connect(self._clear_conversation)
        layout.addWidget(clear_btn)

        return bar

    def _build_ev_section(self) -> QWidget:
        container = QWidget()
        container.setFixedHeight(190)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        self._ev_core = EVCoreWidget()
        layout.addWidget(self._ev_core, alignment=Qt.AlignCenter)

        self._status_label = StatusLabel()
        layout.addWidget(self._status_label, alignment=Qt.AlignCenter)

        return container

    def _build_chat_area(self) -> QScrollArea:
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._chat_container = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(12, 12, 12, 12)
        self._chat_layout.setSpacing(6)
        self._chat_layout.addStretch()

        self._scroll_area.setWidget(self._chat_container)
        return self._scroll_area

    def _build_input_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(72)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Microphone button (checkable = push-to-talk toggle)
        self._mic_btn = QPushButton("🎙")
        self._mic_btn.setObjectName("micButton")
        self._mic_btn.setCheckable(True)
        self._mic_btn.setToolTip("Hold to speak")
        layout.addWidget(self._mic_btn)

        # Text input
        self._input = QLineEdit()
        self._input.setObjectName("messageInput")
        self._input.setPlaceholderText("Ask EV anything...")
        self._input.setFixedHeight(44)
        layout.addWidget(self._input, stretch=1)

        # Send button
        self._send_btn = QPushButton("Send")
        self._send_btn.setObjectName("sendButton")
        self._send_btn.setFixedHeight(44)
        layout.addWidget(self._send_btn)

        return bar

    @staticmethod
    def _build_divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        return line

    # -----------------------------------------------------------------------
    # Signal Connections
    # -----------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # Input
        self._send_btn.clicked.connect(self._on_send)
        self._input.returnPressed.connect(self._on_send)
        self._mic_btn.toggled.connect(self._on_mic_toggled)

        # State → UI
        self._state_manager.state_changed.connect(self._on_state_changed)

    # -----------------------------------------------------------------------
    # Slots — User Actions
    # -----------------------------------------------------------------------

    def _on_send(self) -> None:
        """Send the typed message."""
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._submit_message(text)

    def _on_mic_toggled(self, active: bool) -> None:
        """Start or stop the STT worker based on mic button state."""
        if active:
            self._start_listening()
        else:
            self._stop_listening()

    def _clear_conversation(self) -> None:
        """Clear history and chat bubbles."""
        self._conversation.clear_history()
        # Remove all bubble widgets from the chat layout (keep the stretch)
        while self._chat_layout.count() > 1:
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._add_ev_bubble("Conversation cleared. How can I help you?")

    # -----------------------------------------------------------------------
    # Voice
    # -----------------------------------------------------------------------

    def _start_listening(self) -> None:
        self._state_manager.set_state(AssistantState.LISTENING)
        self._set_inputs_enabled(False)

        self._stt_worker = SpeechToTextWorker()
        self._stt_worker.result_ready.connect(self._on_stt_result)
        self._stt_worker.error_occurred.connect(self._on_stt_error)
        self._stt_worker.finished.connect(self._on_stt_done)
        self._stt_worker.start()

    def _stop_listening(self) -> None:
        """Mic button untoggled before STT finished — worker will finish naturally."""
        pass  # The worker runs to completion; result_ready will fire

    def _on_stt_result(self, text: str) -> None:
        """STT returned a transcription — put it in the input and send."""
        self._mic_btn.setChecked(False)
        self._submit_message(text)

    def _on_stt_error(self, error: str) -> None:
        self._mic_btn.setChecked(False)
        self._show_error(error)
        self._set_inputs_enabled(True)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2500, lambda: self._state_manager.set_state(AssistantState.IDLE))

    def _on_stt_done(self) -> None:
        """STT thread finished."""
        self._mic_btn.setChecked(False)
        if self._state_manager.current == AssistantState.LISTENING:
            self._state_manager.set_state(AssistantState.IDLE)
            self._set_inputs_enabled(True)


    # -----------------------------------------------------------------------
    # Message Submission
    # -----------------------------------------------------------------------

    def _submit_message(self, text: str) -> None:
        """Add user bubble and dispatch to Gemini via a background thread."""
        self._add_user_bubble(text)
        self._set_inputs_enabled(False)
        self._state_manager.set_state(AssistantState.THINKING)

        self._conv_worker = ConversationWorker(self._conversation, text)
        self._conv_worker.finished.connect(self._on_response)
        self._conv_worker.errored.connect(self._on_response_error)
        self._conv_worker.start()

    def _on_response(self, display_text: str, tts_text: str) -> None:
        """Gemini responded — show it and speak it."""
        self._add_ev_bubble(display_text)
        self._speak(tts_text)

    def _on_response_error(self, error: str) -> None:
        self._show_error(error)
        self._state_manager.set_state(AssistantState.ERROR)
        self._set_inputs_enabled(True)
        # Return to IDLE after a brief pause
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2500, lambda: self._state_manager.set_state(AssistantState.IDLE))

    # -----------------------------------------------------------------------
    # TTS
    # -----------------------------------------------------------------------

    def _speak(self, text: str) -> None:
        self._state_manager.set_state(AssistantState.SPEAKING)
        self._tts_worker = TextToSpeechWorker(text)
        self._tts_worker.finished.connect(self._on_tts_done)
        self._tts_worker.error_occurred.connect(self._on_tts_error)
        self._tts_worker.start()

    def _on_tts_done(self) -> None:
        self._state_manager.set_state(AssistantState.IDLE)
        self._set_inputs_enabled(True)

    def _on_tts_error(self, error: str) -> None:
        print(f"[TTS] {error}")
        # TTS error is non-fatal — still return to IDLE
        self._state_manager.set_state(AssistantState.IDLE)
        self._set_inputs_enabled(True)

    # -----------------------------------------------------------------------
    # State Updates
    # -----------------------------------------------------------------------

    def _on_state_changed(self, state: AssistantState) -> None:
        self._ev_core.set_state(state)
        self._status_label.on_state_changed(state)

    # -----------------------------------------------------------------------
    # UI Helpers
    # -----------------------------------------------------------------------

    def _add_user_bubble(self, text: str) -> None:
        bubble = UserBubble(text)
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def _add_ev_bubble(self, text: str) -> None:
        bubble = EVBubble(text)
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self._scroll_area.verticalScrollBar().setValue(
            self._scroll_area.verticalScrollBar().maximum()
        ))

    def _set_inputs_enabled(self, enabled: bool) -> None:
        self._input.setEnabled(enabled)
        self._send_btn.setEnabled(enabled)
        if enabled:
            self._input.setFocus()

    def _show_error(self, message: str) -> None:
        self._add_ev_bubble(f"⚠ {message}")
        self._state_manager.set_state(AssistantState.ERROR)
