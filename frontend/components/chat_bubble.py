# frontend/components/chat_bubble.py
#
# Chat Bubble Widgets
#
# Two variants:
#   UserBubble  — right-aligned, dark cyan background
#   EVBubble    — left-aligned, dark surface background
#
# Both support multiline text and auto-resize to fit content.

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy


class _BubbleBase(QWidget):
    """Internal base for a single chat bubble with sender label and text."""

    def __init__(
        self,
        text: str,
        sender: str,
        bubble_object_name: str,
        sender_color: str,
        align: Qt.AlignmentFlag,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # Outer layout — controls left/right alignment of bubble
        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 4, 8, 4)
        outer.setSpacing(0)

        # The bubble frame
        frame = QFrame()
        frame.setObjectName(bubble_object_name)

        inner = QVBoxLayout(frame)
        inner.setContentsMargins(14, 10, 14, 10)
        inner.setSpacing(4)

        # Sender label ("You" / "EV")
        sender_label = QLabel(sender)
        sender_label.setObjectName("bubbleSender")
        sender_label.setStyleSheet(f"color: {sender_color};")
        inner.addWidget(sender_label)

        # Message text — wraps naturally
        text_label = QLabel(text)
        text_label.setObjectName("bubbleText")
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        # Cap max width so bubbles don't stretch across the full window
        text_label.setMaximumWidth(520)
        inner.addWidget(text_label)

        # Align bubble to the correct side
        if align == Qt.AlignRight:
            outer.addStretch()
            outer.addWidget(frame)
        else:
            outer.addWidget(frame)
            outer.addStretch()


class UserBubble(_BubbleBase):
    """Right-aligned bubble for user messages."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(
            text=text,
            sender="You",
            bubble_object_name="userBubble",
            sender_color="#00d4ff",
            align=Qt.AlignRight,
            parent=parent,
        )


class EVBubble(_BubbleBase):
    """Left-aligned bubble for EV responses."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(
            text=text,
            sender="EV",
            bubble_object_name="evBubble",
            sender_color="#00ff88",
            align=Qt.AlignLeft,
            parent=parent,
        )
