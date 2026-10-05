"""Unit tests for NebiusProvider using mocked API responses (offline testing)."""

import unittest
from unittest.mock import MagicMock, patch
from jarvis_nexus.nebius_provider import NebiusProvider
from jarvis_nexus.models import ChatMessage, ToolDefinition, ToolCall

try:
    from openai import APIError, APITimeoutError, APIConnectionError
    OPENAI_INSTALLED = True
except ImportError:
    OPENAI_INSTALLED = False
    APIError = Exception
    APITimeoutError = Exception
    APIConnectionError = Exception


class TestNebiusProvider(unittest.TestCase):
    """Test suite for NebiusProvider with mocked OpenAI client requests."""

    def test_provider_initialization_defaults(self) -> None:
        provider = NebiusProvider(api_key="test-key")
        self.assertEqual(provider.api_key, "test-key")
        self.assertEqual(provider.base_url, "https://api.tokenfactory.nebius.com/v1/")
        self.assertEqual(provider.model, "nvidia/Nemotron-3_5-Lightning")

    def test_missing_api_key_handling(self) -> None:
        provider = NebiusProvider(api_key="")
        res = provider.generate([ChatMessage(role="user", content="Hello")], system_prompt="Test")
        self.assertIn("Error", res.content)

    @unittest.skipUnless(OPENAI_INSTALLED, "openai package not installed")
    @patch("jarvis_nexus.nebius_provider.OpenAI")
    def test_normal_model_response_parsing(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from Nemotron!"
        mock_choice.message.tool_calls = None
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        provider = NebiusProvider(api_key="fake-secret-key")
        res = provider.generate([ChatMessage(role="user", content="Hi")], system_prompt="Test")

        self.assertEqual(res.content, "Hello from Nemotron!")
        self.assertEqual(res.tool_calls, [])

    @unittest.skipUnless(OPENAI_INSTALLED, "openai package not installed")
    @patch("jarvis_nexus.nebius_provider.OpenAI")
    def test_tool_call_response_parsing(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_tc = MagicMock()
        mock_tc.id = "call_123"
        mock_tc.function.name = "get_current_time"
        mock_tc.function.arguments = "{}"

        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tc]
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        provider = NebiusProvider(api_key="fake-secret-key")
        tool_def = ToolDefinition(name="get_current_time", description="Get time", parameters={})
        res = provider.generate([ChatMessage(role="user", content="What time is it?")], system_prompt="Test", tools=[tool_def])

        self.assertIsNone(res.content)
        self.assertEqual(len(res.tool_calls), 1)
        self.assertEqual(res.tool_calls[0].name, "get_current_time")
        self.assertEqual(res.tool_calls[0].id, "call_123")

    @unittest.skipUnless(OPENAI_INSTALLED, "openai package not installed")
    @patch("jarvis_nexus.nebius_provider.OpenAI")
    def test_timeout_handling(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())

        provider = NebiusProvider(api_key="fake-secret-key")
        res = provider.generate([ChatMessage(role="user", content="Hi")], system_prompt="Test")
        self.assertIn("timed out", res.content)

    @unittest.skipUnless(OPENAI_INSTALLED, "openai package not installed")
    @patch("jarvis_nexus.nebius_provider.OpenAI")
    def test_api_error_and_secret_redaction(self, mock_openai_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        
        secret_key = "secret_nebius_abc123"
        mock_client.chat.completions.create.side_effect = APIError(
            message=f"Invalid api key {secret_key} provided",
            request=MagicMock(),
            body=None
        )

        provider = NebiusProvider(api_key=secret_key)
        res = provider.generate([ChatMessage(role="user", content="Hi")], system_prompt="Test")
        
        self.assertIn("Nebius API Error", res.content)
        self.assertNotIn(secret_key, res.content)
        self.assertIn("[REDACTED]", res.content)


if __name__ == "__main__":
    unittest.main()
