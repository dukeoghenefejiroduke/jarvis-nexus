"""Unit tests for GeminiProvider and Nebius fallback to Gemini using mocked urllib.request responses."""

import unittest
from unittest.mock import MagicMock, patch
import json
import urllib.error
from io import BytesIO
from jarvis_nexus.gemini_provider import GeminiProvider
from jarvis_nexus.nebius_provider import NebiusProvider
from jarvis_nexus.models import ChatMessage, ToolDefinition, ToolCall


class TestGeminiProvider(unittest.TestCase):
    """Test suite for GeminiProvider and fallback behavior."""

    def test_provider_initialization_defaults(self) -> None:
        provider = GeminiProvider(api_key="test-gemini-key")
        self.assertEqual(provider.api_key, "test-gemini-key")
        self.assertEqual(provider.base_url, "https://generativelanguage.googleapis.com/v1beta/openai/")
        self.assertEqual(provider.model, "gemini-1.5-flash")

    @patch("jarvis_nexus.gemini_provider.Config.GEMINI_API_KEY", "")
    def test_missing_api_key_handling(self) -> None:
        provider = GeminiProvider(api_key="")
        res = provider.generate([ChatMessage(role="user", content="Hello")], system_prompt="Test")
        self.assertIn("I understand", res.content)
        self.assertIn("Missing Gemini API Key", res.provider_mode)

    @patch("urllib.request.urlopen")
    def test_normal_model_response_parsing(self, mock_urlopen: MagicMock) -> None:
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Hello from Google Gemini via OpenAI-compatible endpoint!",
                        "tool_calls": None
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        provider = GeminiProvider(api_key="fake-gemini-key")
        res = provider.generate([ChatMessage(role="user", content="Hi")], system_prompt="Test")

        self.assertEqual(res.content, "Hello from Google Gemini via OpenAI-compatible endpoint!")
        self.assertEqual(res.tool_calls, [])
        self.assertEqual(res.provider_mode, "Active (Google Gemini API)")
        mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_tool_call_response_parsing(self, mock_urlopen: MagicMock) -> None:
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_gemini_1",
                                "type": "function",
                                "function": {
                                    "name": "get_current_time",
                                    "arguments": "{}"
                                }
                            }
                        ]
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        provider = GeminiProvider(api_key="fake-gemini-key")
        tool_def = ToolDefinition(name="get_current_time", description="Get time", parameters={})
        res = provider.generate([ChatMessage(role="user", content="What time is it?")], system_prompt="Test", tools=[tool_def])

        self.assertIsNone(res.content)
        self.assertEqual(len(res.tool_calls), 1)
        self.assertEqual(res.tool_calls[0].name, "get_current_time")
        self.assertEqual(res.tool_calls[0].id, "call_gemini_1")

    @patch("jarvis_nexus.gemini_provider.Config.GEMINI_API_KEY", "gemini-key")
    @patch("urllib.request.urlopen")
    def test_nebius_fallback_to_gemini(self, mock_urlopen: MagicMock) -> None:
        # Nebius request fails with URLError
        mock_urlopen.side_effect = urllib.error.URLError("Nebius connection refused")

        # Gemini succeeds
        gemini_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Fallback response from Gemini API!",
                        "tool_calls": None
                    }
                }
            ]
        }
        mock_gemini_resp = MagicMock()
        mock_gemini_resp.read.return_value = json.dumps(gemini_response_data).encode("utf-8")
        mock_gemini_resp.__enter__.return_value = mock_gemini_resp

        # We patch urlopen behavior or GeminiProvider.generate
        with patch("jarvis_nexus.gemini_provider.GeminiProvider.generate") as mock_gemini_gen:
            mock_gemini_gen.return_value = MagicMock(content="Fallback response from Gemini API!", provider_mode="Active (Google Gemini API)")

            nebius_provider = NebiusProvider(api_key="nebius-key")
            res = nebius_provider.generate([ChatMessage(role="user", content="Hi")], system_prompt="Test")

            self.assertEqual(res.content, "Fallback response from Gemini API!")
            mock_gemini_gen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
