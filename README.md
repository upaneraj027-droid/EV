# EV — Personal AI Assistant

EV is a minimal futuristic desktop AI assistant powered by Google Gemini. It supports both text and voice interaction and maintains conversation context.

---

## Features (Version 1 — MVP)

- 💬 Text conversation with Gemini AI
- 🎙️ Voice input (push-to-talk) via microphone
- 🔊 Voice output (text-to-speech)
- 🧠 Conversation context (multi-turn)
- 🖥️ Dark futuristic desktop UI
- 📊 Status indicator (IDLE / LISTENING / THINKING / SPEAKING / ERROR)

---

## Requirements

- Python 3.12 (required — PySide6 does not yet support Python 3.14)
- macOS, Windows, or Linux
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### macOS Audio Setup

Voice input requires `portaudio`. Install it with Homebrew:

```bash
brew install portaudio
```

---

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd EV
```

### 2. Create a virtual environment

```bash
# macOS with Homebrew Python 3.12
/opt/homebrew/bin/python3.12 -m venv venv
source venv/bin/activate

# Windows (if Python 3.12 is on PATH)
# python3.12 -m venv venv
# venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

```bash
cp .env.example .env
```

Open `.env` and replace `your_gemini_api_key_here` with your actual Gemini API key:

```
GEMINI_API_KEY=AIza...
```

---

## Running EV

```bash
python backend/main.py
```

---

## Usage

| Action | How |
|---|---|
| Send a text message | Type in the input box and press **Enter** or click **Send** |
| Voice input | Click the **🎙️** microphone button, speak, then click again to stop |
| Clear conversation | Click the **✕ Clear** button in the top bar |

---

## Project Structure

```
EV/
├── backend/
│   ├── main.py               # App entry point
│   ├── assistant/
│   │   ├── conversation.py   # Conversation manager
│   │   ├── state.py          # State machine (IDLE/LISTENING/THINKING/SPEAKING/ERROR)
│   │   └── response.py       # Response formatting
│   ├── ai/
│   │   └── gemini.py         # Gemini API service
│   ├── voice/
│   │   ├── speech_to_text.py # Microphone capture + STT
│   │   └── text_to_speech.py # TTS output
│   └── skills/
│       ├── base.py           # Abstract skill base (V2+ extension point)
│       └── registry.py       # Skill registry (V2+ extension point)
│
├── frontend/
│   ├── app.py                # Main PySide6 window
│   ├── components/           # UI widgets
│   └── styles/theme.qss      # Dark futuristic Qt stylesheet
│
├── tests/                    # Unit tests
├── .env.example              # API key template
├── requirements.txt
└── README.md
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Roadmap

| Version | Feature |
|---|---|
| ✅ V1 — MVP | Text + Voice + Gemini + Context |
| 🔵 V2 — Skills | Google Search, Browser automation, Study tools |
| 🟣 V3 — Always On | Background operation, System tray, Wake word |
| 🔴 V4 — Agentic | Research mode, Multi-step task execution |

---

## Troubleshooting

**`PyAudio` install fails on macOS**
```bash
brew install portaudio
pip install pyaudio
```

**Gemini API error: `INVALID_API_KEY`**
- Check that your `.env` file exists and contains a valid key.
- The key should start with `AIza`.

**No microphone detected**
- Check System Preferences → Security & Privacy → Microphone and ensure the app has access.
