# frontend/components/ev_core.py
#
# EV Core Visual Widget
#
# The central animated visual element — a pulsing ring with "EV" text.
# Changes appearance based on the assistant's current state:
#
#   IDLE      — slow dim pulse, grey ring
#   LISTENING — fast pulse, red ring
#   THINKING  — medium rotating arc, cyan ring
#   SPEAKING  — gentle wave pulse, green ring
#   ERROR     — steady red ring (no pulse)

from __future__ import annotations
import math
from PySide6.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient
from PySide6.QtWidgets import QWidget

from backend.assistant.state import AssistantState

# State → (ring color, glow color, pulse speed ms, use_arc)
_STATE_CONFIG: dict[AssistantState, tuple[str, str, int, bool]] = {
    AssistantState.IDLE:      ("#2a2a4a", "#00d4ff", 3000, False),
    AssistantState.LISTENING: ("#ff4466", "#ff2244", 600,  False),
    AssistantState.THINKING:  ("#00d4ff", "#00aacc", 1200, True),
    AssistantState.SPEAKING:  ("#00ff88", "#00cc66", 900,  False),
    AssistantState.ERROR:     ("#ff4466", "#ff2244", 0,    False),
}


class EVCoreWidget(QWidget):
    """
    Custom-painted widget that renders EV's central visual indicator.

    Draws:
    - An outer glow ring
    - An animated pulse ring
    - A rotating arc (THINKING state)
    - "EV" text in the centre
    """

    SIZE = 140  # Widget width and height in pixels

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._state = AssistantState.IDLE
        self._pulse_value = 0.0   # 0.0 → 1.0 for ring opacity/scale
        self._arc_angle = 0       # rotating arc position (degrees)
        self._pulse_direction = 1

        # Animation timer — drives all visual effects
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)  # ~33 fps

    def set_state(self, state: AssistantState) -> None:
        """Update the visual state and restart animation."""
        self._state = state
        self._pulse_value = 0.0
        self._pulse_direction = 1
        self.update()

    def _tick(self) -> None:
        """Called by the timer every ~30ms to update animation values."""
        config = _STATE_CONFIG[self._state]
        speed_ms = config[2]
        use_arc = config[3]

        if speed_ms > 0:
            step = 30.0 / speed_ms  # fraction of full pulse per tick
            self._pulse_value += step * self._pulse_direction
            if self._pulse_value >= 1.0:
                self._pulse_value = 1.0
                self._pulse_direction = -1
            elif self._pulse_value <= 0.0:
                self._pulse_value = 0.0
                self._pulse_direction = 1

        if use_arc:
            self._arc_angle = (self._arc_angle + 4) % 360

        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        config = _STATE_CONFIG[self._state]
        ring_color = QColor(config[0])
        glow_color = QColor(config[1])
        use_arc = config[3]

        cx = self.SIZE / 2
        cy = self.SIZE / 2
        outer_r = 54
        inner_r = 42

        # ── Glow halo ──
        glow_alpha = int(40 + 80 * self._pulse_value)
        glow = QRadialGradient(cx, cy, outer_r + 16)
        glow.setColorAt(0.0, QColor(glow_color.red(), glow_color.green(),
                                     glow_color.blue(), glow_alpha))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        halo_r = outer_r + 16
        painter.drawEllipse(QRectF(cx - halo_r, cy - halo_r, halo_r * 2, halo_r * 2))

        # ── Outer ring ──
        ring_alpha = int(120 + 135 * self._pulse_value)
        pen_color = QColor(ring_color.red(), ring_color.green(),
                           ring_color.blue(), ring_alpha)
        pen = QPen(pen_color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - outer_r, cy - outer_r,
                                   outer_r * 2, outer_r * 2))

        # ── Pulse ring (scales out) ──
        if _STATE_CONFIG[self._state][2] > 0:
            pulse_r = outer_r + 10 * self._pulse_value
            pulse_alpha = int(80 * (1.0 - self._pulse_value))
            pulse_pen = QPen(
                QColor(glow_color.red(), glow_color.green(),
                       glow_color.blue(), pulse_alpha), 1
            )
            painter.setPen(pulse_pen)
            painter.drawEllipse(
                QRectF(cx - pulse_r, cy - pulse_r, pulse_r * 2, pulse_r * 2)
            )

        # ── Rotating arc (THINKING) ──
        if use_arc:
            arc_pen = QPen(glow_color, 3)
            arc_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(arc_pen)
            # Qt uses 1/16th degree units; start angle from top (90°)
            start = (90 - self._arc_angle) * 16
            painter.drawArc(
                QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2),
                start,
                100 * 16,   # 100° arc span
            )

        # ── Inner filled circle ──
        inner_bg = QColor(10, 10, 20, 230)
        painter.setBrush(inner_bg)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - inner_r, cy - inner_r,
                                   inner_r * 2, inner_r * 2))

        # ── "EV" text ──
        font = QFont("SF Pro Display", 22, QFont.Bold)
        painter.setFont(font)
        text_color = QColor(glow_color)
        text_color.setAlpha(220)
        painter.setPen(text_color)
        painter.drawText(
            QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2),
            Qt.AlignCenter,
            "EV",
        )

        painter.end()
