# backend/ai/gemini.py
#
# Gemini AI Service
#
# Wraps the google-genai SDK. The rest of the application never imports
# google-genai directly — it always goes through GeminiService. This means
# we can swap models or SDKs in the future without touching any other file.

from __future__ import annotations
import os
from dotenv import load_dotenv

# Load .env before anything else so the API key is available
load_dotenv()


class GeminiService:
    """
    Thin wrapper around the Google Gemini API.

    Uses the google-genai SDK (the modern replacement for google-generativeai).
    Sends the full conversation history on each request so Gemini has context.

    Configuration:
        GEMINI_API_KEY  — must be set in .env or the environment
        GEMINI_MODEL    — optional, defaults to 'gemini-2.0-flash'
    """

    DEFAULT_MODEL = "gemini-3.6-flash"

    # System prompt that gives EV its personality
    SYSTEM_PROMPT = (
        "You are EV, a helpful, intelligent, and concise personal AI assistant. "
        "You have a calm, professional, and slightly futuristic personality. "
        "Keep responses clear and to the point — avoid unnecessary filler. "
        "When answering follow-up questions, use the conversation context to "
        "give accurate, coherent answers."
    )

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. "
                "Copy .env.example to .env and add your API key."
            )

        model_name = os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)

        # Import here so that missing google-genai gives a clear error message
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError as exc:
            raise ImportError(
                "google-genai is not installed. Run: pip install google-genai"
            ) from exc

        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name
        self._genai_types = genai_types
        print(f"[GeminiService] Initialized with model: {model_name}")

    def send(self, history: list[dict[str, str]]) -> str:
        """
        Send the full conversation history to Gemini and return the response text.

        The history format matches what ConversationManager maintains:
            [{"role": "user", "content": "..."}, {"role": "model", "content": "..."}, ...]

        Args:
            history: Full conversation history including the latest user message.

        Returns:
            The assistant's response as a plain string.

        Raises:
            RuntimeError: If the API call fails or returns an empty response.
        """
        # Convert our internal history format to the google-genai Content format
        contents = []
        for turn in history:
            role = turn["role"]   # "user" or "model"
            text = turn["content"]
            contents.append(
                self._genai_types.Content(
                    role=role,
                    parts=[self._genai_types.Part(text=text)],
                )
            )

        config = self._genai_types.GenerateContentConfig(
            system_instruction=self.SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=2048,
        )

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

        # Extract text from response
        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        return response.text
