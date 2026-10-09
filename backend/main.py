# backend/main.py
#
# EV — Application Entry Point
#
# Boots the PySide6 application, loads the stylesheet, and opens the main window.
# Run this file to launch EV:
#
#     python backend/main.py

from __future__ import annotations
import sys
import os

# Ensure the project root (EV/) is on the Python path so both `backend`
# and `frontend` packages can be imported from anywhere.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load environment variables before any other imports so the API key is
# available to GeminiService when it is first imported.
from dotenv import load_dotenv
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from frontend.app import EVWindow


def load_stylesheet(app: QApplication) -> None:
    """Load and apply the dark futuristic Qt stylesheet."""
    qss_path = os.path.join(_PROJECT_ROOT, "frontend", "styles", "theme.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"[main] Warning: stylesheet not found at {qss_path}")


def main() -> int:
    """Create the QApplication, build the window, and start the event loop."""

    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("EV")
    app.setApplicationDisplayName("EV — Personal AI Assistant")
    app.setApplicationVersion("1.0.0")

    # Set a clean base font
    font = QFont("SF Pro Display")
    if not font.exactMatch():
        font = QFont("Segoe UI")
        if not font.exactMatch():
            font = QFont("Inter")
    font.setPointSize(13)
    app.setFont(font)

    load_stylesheet(app)

    window = EVWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
