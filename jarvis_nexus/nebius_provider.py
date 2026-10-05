"""Nebius Token Factory model provider adapter implementing BaseModelProvider."""

import json
from typing import Any, Dict, List, Optional
from jarvis_nexus.config import Config
from jarvis_nexus.models import BaseModelProvider, ModelResponse, ToolCall, ToolDefinition, ChatMessage

try:
    from openai import OpenAI, APIError, APITimeoutError, APIConnectionError
except ImportError:
    OpenAI = None
    APIError = Exception
    APITimeoutError = Exception
    APIConnectionError = Exception


class NebiusProvider(BaseModelProvider):
    """OpenAI-compatible adapter for Nebius Token Factory (NVIDIA Nemotron)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ) -> None:
        self.api_key = api_key or Config.NEBIUS_API_KEY
        self.base_url = base_url or Config.NEBIUS_BASE_URL
        self.model = model or Config.NEBIUS_MODEL

    def _get_client(self) -> Any:
        """Initialize OpenAI client pointing to Nebius Token Factory endpoint."""
        if not OpenAI:
            raise ImportError("The 'openai' package is not installed. Install requirements or use MODEL_PROVIDER=mock.")
        if not self.api_key:
            raise ValueError(
                "NEBIUS_API_KEY is missing. Please set NEBIUS_API_KEY in your environment or .env file."
            )
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: str,
        tools: Optional[List[ToolDefinition]] = None
    ) -> ModelResponse:
        """Send chat completion request to Nebius Token Factory and return structured ModelResponse."""
        try:
            client = self._get_client()
        except (ValueError, ImportError) as e:
            return ModelResponse(content=f"Configuration/Import Error: {str(e)}", tool_calls=[])

        # Format messages for OpenAI API
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            m_dict = {"role": msg.role, "content": msg.content or ""}
            if msg.name:
                m_dict["name"] = msg.name
            if msg.tool_call_id:
                m_dict["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                m_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}
                    }
                    for tc in msg.tool_calls
                ]
            api_messages.append(m_dict)

        # Format tools for OpenAI API
        api_tools = None
        if tools:
            api_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                }
                for tool in tools
            ]

        try:
            kwargs = {
                "model": self.model,
                "messages": api_messages,
                "temperature": 0.7,
            }
            if api_tools:
                kwargs["tools"] = api_tools
                kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message

            content = message.content
            tool_calls = []

            if hasattr(message, "tool_calls") and message.tool_calls:
                for tc in message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}
                    tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            name=tc.function.name,
                            arguments=args
                        )
                    )

            return ModelResponse(content=content, tool_calls=tool_calls)

        except APITimeoutError:
            return ModelResponse(content="Error: Request to Nebius Token Factory timed out.", tool_calls=[])
        except APIConnectionError:
            return ModelResponse(content="Error: Failed to connect to Nebius Token Factory network endpoint.", tool_calls=[])
        except APIError as e:
            err_msg = str(e)
            if self.api_key and self.api_key in err_msg:
                err_msg = err_msg.replace(self.api_key, "[REDACTED]")
            return ModelResponse(content=f"Nebius API Error: {err_msg}", tool_calls=[])
        except Exception as e:
            err_msg = str(e)
            if self.api_key and self.api_key in err_msg:
                err_msg = err_msg.replace(self.api_key, "[REDACTED]")
            return ModelResponse(content=f"Unexpected Error communicating with Nebius: {err_msg}", tool_calls=[])
