# backend/assistant/response.py
#
# Response post-processing
#
# Cleans up Gemini's raw text before it is displayed in the UI and before
# it is sent to TTS. Also provides a hook for future response routing
# (e.g., detecting if a skill should handle the response in V2).

import re


class ResponseFormatter:
    """
    Cleans and prepares AI responses for display and speech.

    The formatter:
    - Strips markdown code fences (``` blocks) from TTS text
    - Strips leading/trailing whitespace
    - Removes excessive blank lines
    - Provides a plain-text version (for TTS) alongside the display version
    """

    # Matches ```lang\n ... \n``` blocks
    _CODE_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

    # Matches inline `code` spans
    _INLINE_CODE_RE = re.compile(r"`([^`]+)`")

    # Matches markdown headers (## Heading)
    _HEADER_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)

    # Matches bold **text** or __text__
    _BOLD_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")

    # Matches italic *text* or _text_
    _ITALIC_RE = re.compile(r"\*(.+?)\*|_(.+?)_")

    @classmethod
    def for_display(cls, raw_text: str) -> str:
        """
        Return the text as-is for display in the chat UI.
        The UI renders markdown, so we leave it intact.

        Args:
            raw_text: Raw response string from Gemini.

        Returns:
            Cleaned string ready for display.
        """
        return raw_text.strip()

    @classmethod
    def for_tts(cls, raw_text: str) -> str:
        """
        Return a plain-text version of the response suitable for TTS.
        Removes markdown formatting that would be spoken literally.

        Args:
            raw_text: Raw response string from Gemini.

        Returns:
            Plain text string suitable for text-to-speech.
        """
        text = raw_text

        # Replace code fences with a spoken placeholder
        text = cls._CODE_FENCE_RE.sub(r"[code block] \1", text)

        # Strip inline code backticks (keep the code text)
        text = cls._INLINE_CODE_RE.sub(r"\1", text)

        # Strip markdown headers (#, ##, etc.)
        text = cls._HEADER_RE.sub("", text)

        # Strip bold markers
        text = cls._BOLD_RE.sub(lambda m: m.group(1) or m.group(2), text)

        # Strip italic markers
        text = cls._ITALIC_RE.sub(lambda m: m.group(1) or m.group(2), text)

        # Collapse multiple blank lines into one
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()
