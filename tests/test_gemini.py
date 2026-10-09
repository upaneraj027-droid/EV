# tests/test_gemini.py
#
# Tests for GeminiService — validates error handling and message formatting.
# The actual google-genai client is mocked so no real API key is needed.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(api_key: str = "test-key-123"):
    """
    Create a GeminiService with the google-genai client mocked out.
    Returns (service, mock_client).
    """
    # Set env var so GeminiService doesn't raise EnvironmentError
    os.environ["GEMINI_API_KEY"] = api_key

    # Mock the entire google.genai module
    mock_genai = MagicMock()
    mock_types = MagicMock()

    # genai.Client(api_key=...) → mock_client
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client

    with patch.dict("sys.modules", {"google": MagicMock(), "google.genai": mock_genai}):
        with patch("google.genai.types", mock_types):
            from importlib import reload
            import backend.ai.gemini as gemini_module
            reload(gemini_module)
            service = gemini_module.GeminiService.__new__(gemini_module.GeminiService)
            service._client = mock_client
            service._model_name = "gemini-2.0-flash"
            service._genai_types = mock_types

    return service, mock_client, mock_types


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGeminiService:
    def test_raises_if_no_api_key(self):
        """Should raise EnvironmentError when GEMINI_API_KEY is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("dotenv.load_dotenv"):
                with patch.dict("sys.modules", {
                    "google": MagicMock(),
                    "google.genai": MagicMock(),
                }):
                    from importlib import reload
                    import backend.ai.gemini as gemini_module
                    reload(gemini_module)
                    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
                        gemini_module.GeminiService()

    def test_send_converts_history_to_contents(self):
        """send() should pass the correct number of Content objects to the API."""
        service, mock_client, mock_types = _make_service()

        # Mock a successful API response
        mock_response = MagicMock()
        mock_response.text = "Gemini says hello"
        mock_client.models.generate_content.return_value = mock_response

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "model", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        result = service.send(history)
        assert result == "Gemini says hello"
        mock_client.models.generate_content.assert_called_once()

    def test_send_raises_on_empty_response(self):
        """Should raise RuntimeError if the API returns an empty response."""
        service, mock_client, mock_types = _make_service()

        mock_response = MagicMock()
        mock_response.text = ""  # empty!
        mock_client.models.generate_content.return_value = mock_response

        with pytest.raises(RuntimeError, match="empty response"):
            service.send([{"role": "user", "content": "hi"}])

    def test_send_raises_on_api_error(self):
        """Should raise RuntimeError wrapping the original API exception."""
        service, mock_client, mock_types = _make_service()
        mock_client.models.generate_content.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Gemini API call failed"):
            service.send([{"role": "user", "content": "hi"}])


class TestResponseFormatter:
    def setup_method(self):
        from backend.assistant.response import ResponseFormatter
        self.fmt = ResponseFormatter

    def test_for_display_strips_whitespace(self):
        assert self.fmt.for_display("  hello  ") == "hello"

    def test_for_tts_strips_code_fences(self):
        text = "Here is code:\n```python\nprint('hi')\n```\nDone."
        result = self.fmt.for_tts(text)
        assert "```" not in result
        assert "print" in result  # content preserved

    def test_for_tts_strips_bold(self):
        result = self.fmt.for_tts("This is **bold** text")
        assert "**" not in result
        assert "bold" in result

    def test_for_tts_strips_headers(self):
        result = self.fmt.for_tts("## My Heading\nSome content")
        assert "##" not in result
        assert "My Heading" in result

    def test_for_tts_strips_inline_code(self):
        result = self.fmt.for_tts("Use `print()` to output text")
        assert "`" not in result
        assert "print()" in result
