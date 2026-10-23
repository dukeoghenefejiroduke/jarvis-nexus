"""Unit tests for NebiusProvider using mocked urllib.request responses (offline testing)."""

import unittest
from unittest.mock import MagicMock, patch
import json
import urllib.error
from io import BytesIO
from jarvis_nexus.nebius_provider import NebiusProvider
from jarvis_nexus.models import ChatMessage, ToolDefinition, ToolCall


class TestNebiusProvider(unittest.TestCase):
    """Test suite for NebiusProvider with mocked urllib.request calls."""

    def test_provider_initialization_defaults(self) -> None:
        provider = NebiusProvider(api_key="test-key")
        self.assertEqual(provider.api_key, "test-key")
        self.assertEqual(provider.base_url, "https://api.tokenfactory.nebius.com/v1/")
        self.assertEqual(provider.model, "nvidia/Nemotron-3_5-Lightning")

    @patch("jarvis_nexus.nebius_provider.Config.NEBIUS_API_KEY", "")
    @patch("jarvis_nexus.nebius_provider.Config.GEMINI_API_KEY", "")
    def test_missing_api_key_handling(self) -> None:
        provider = NebiusProvider(api_key="")
        res = provider.generate([ChatMessage(role="user", content="Hello")], system_prompt="Test")
        # Should transparently fall back to MockModelProvider
        self.assertIn("I understand", res.content)

    @patch("urllib.request.urlopen")
    def test_normal_model_response_parsing(self, mock_urlopen: MagicMock) -> None:
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Hello from Nemotron via urllib!",
                        "tool_calls": None
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        provider = NebiusProvider(api_key="fake-secret-key")
        res = provider.generate([ChatMessage(role="user", content="Hi")], system_prompt="Test")

        self.assertEqual(res.content, "Hello from Nemotron via urllib!")
        self.assertEqual(res.tool_calls, [])
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
                                "id": "call_abc123",
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

        provider = NebiusProvider(api_key="fake-secret-key")
        tool_def = ToolDefinition(name="get_current_time", description="Get time", parameters={})
        res = provider.generate([ChatMessage(role="user", content="What time is it?")], system_prompt="Test", tools=[tool_def])

        self.assertIsNone(res.content)
        self.assertEqual(len(res.tool_calls), 1)
        self.assertEqual(res.tool_calls[0].name, "get_current_time")
        self.assertEqual(res.tool_calls[0].id, "call_abc123")

    @patch("urllib.request.urlopen")
    def test_timeout_handling(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = urllib.error.URLError("timed out")

        provider = NebiusProvider(api_key="fake-secret-key")
        res = provider.generate([ChatMessage(role="user", content="Hi")], system_prompt="Test")
        # Should transparently fall back to MockModelProvider on timeout
        self.assertIn("I understand", res.content)

    @patch("urllib.request.urlopen")
    def test_api_error_fallback(self, mock_urlopen: MagicMock) -> None:
        secret_key = "nebius_secret_token_xyz987"
        fp = BytesIO(f"Invalid api key {secret_key}".encode("utf-8"))
        err = urllib.error.HTTPError(
            url="https://api.tokenfactory.nebius.com/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=fp
        )
        mock_urlopen.side_effect = err

        provider = NebiusProvider(api_key=secret_key)
        res = provider.generate([ChatMessage(role="user", content="Hi")], system_prompt="Test")
        err.close()
        
        # Should transparently fall back to MockModelProvider on HTTP error
        self.assertIn("I understand", res.content)


if __name__ == "__main__":
    unittest.main()
