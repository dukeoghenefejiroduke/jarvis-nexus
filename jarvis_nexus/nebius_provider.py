"""Nebius Token Factory model provider adapter implementing BaseModelProvider using standard library urllib."""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from jarvis_nexus.config import Config
from jarvis_nexus.models import BaseModelProvider, ModelResponse, ToolCall, ToolDefinition, ChatMessage
from jarvis_nexus.security import redact_secrets


class NebiusProvider(BaseModelProvider):
    """OpenAI-compatible adapter for Nebius Token Factory (NVIDIA Nemotron) using standard library."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ) -> None:
        self.api_key = api_key or Config.NEBIUS_API_KEY
        self.base_url = base_url or Config.NEBIUS_BASE_URL
        self.model = model or Config.NEBIUS_MODEL

    def _sanitize(self, text: str) -> str:
        """Redact API key or secrets from error messages."""
        if not text:
            return ""
        s = redact_secrets(text)
        if self.api_key and len(self.api_key) > 4 and self.api_key in s:
            s = s.replace(self.api_key, "[REDACTED]")
        return s

    def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: str,
        tools: Optional[List[ToolDefinition]] = None
    ) -> ModelResponse:
        """Send chat completion request to Nebius Token Factory via urllib and return structured ModelResponse with transparent fallback."""
        if not self.api_key or self.api_key in ("your_api_key_here", "your_actual_nebius_api_key_here"):
            print("[Notice] NEBIUS_API_KEY is missing or set to placeholder. Transparently falling back to Offline Fallback mode.")
            from jarvis_nexus.models import MockModelProvider
            res = MockModelProvider().generate(messages, system_prompt, tools)
            res.provider_mode = "Offline Fallback (Mock Simulation - Missing API Key)"
            return res

        base = self.base_url.rstrip("/")
        url = f"{base}/chat/completions"

        # Format messages for OpenAI-compatible API
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

        # Format tools for OpenAI-compatible API
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        if tools:
            payload["tools"] = [
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
            payload["tool_choice"] = "auto"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_bytes = resp.read()
                data = json.loads(resp_bytes.decode("utf-8"))

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})

            content = message.get("content")
            raw_tool_calls = message.get("tool_calls")
            tool_calls = []

            if raw_tool_calls:
                for tc in raw_tool_calls:
                    tc_id = tc.get("id", "call_unknown")
                    func = tc.get("function", {})
                    func_name = func.get("name", "")
                    func_args_str = func.get("arguments", "{}")
                    try:
                        args = json.loads(func_args_str) if isinstance(func_args_str, str) else func_args_str
                    except Exception:
                        args = {}
                    tool_calls.append(
                        ToolCall(
                            id=tc_id,
                            name=func_name,
                            arguments=args
                        )
                    )

            return ModelResponse(content=content, tool_calls=tool_calls, provider_mode="Active (Nebius Token Factory / NVIDIA Nemotron)")

        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as e:
            print(f"[Notice] Nebius Token Factory connection failed or timed out ({e}). Transparently falling back to Offline Fallback mode.")
            from jarvis_nexus.models import MockModelProvider
            res = MockModelProvider().generate(messages, system_prompt, tools)
            res.provider_mode = f"Offline Fallback (Mock Simulation - {str(e)[:40]})"
            return res
