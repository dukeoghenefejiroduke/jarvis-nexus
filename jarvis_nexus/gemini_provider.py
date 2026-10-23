"""Google Gemini API model provider adapter implementing BaseModelProvider using standard library urllib (OpenAI-compatible endpoint)."""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from jarvis_nexus.config import Config
from jarvis_nexus.models import BaseModelProvider, ModelResponse, ToolCall, ToolDefinition, ChatMessage
from jarvis_nexus.security import redact_secrets


class GeminiProvider(BaseModelProvider):
    """OpenAI-compatible adapter for Google Gemini API using standard library urllib."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ) -> None:
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.base_url = base_url or Config.GEMINI_BASE_URL
        self.model = model or Config.GEMINI_MODEL

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
        """Send chat completion request to Google Gemini API via urllib and return structured ModelResponse with transparent fallback."""
        if not self.api_key or self.api_key in ("your_gemini_api_key_here", "your_api_key_here"):
            print("[Notice] GEMINI_API_KEY is missing or set to placeholder. Transparently falling back to Offline Fallback mode.")
            from jarvis_nexus.models import MockModelProvider
            res = MockModelProvider().generate(messages, system_prompt, tools)
            res.provider_mode = "Offline Fallback (Mock Simulation - Missing Gemini API Key)"
            return res

        base = self.base_url.rstrip("/")
        url = f"{base}/chat/completions"

        # Format messages for OpenAI-compatible API
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = msg.role
            content = msg.content or ""
            if role == "tool":
                role = "user"
                content = f"Tool result for '{msg.name}': {content}"

            m_dict = {"role": role, "content": content}
            if msg.name and role != "user":
                m_dict["name"] = msg.name
            if msg.tool_call_id and role != "user":
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

            with urllib.request.urlopen(req, timeout=30) as resp:
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

            return ModelResponse(content=content, tool_calls=tool_calls, provider_mode="Active (Google Gemini API)")

        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as e:
            print(f"[Notice] Google Gemini API connection failed or timed out ({e}). Transparently falling back to Offline Fallback mode.")
            from jarvis_nexus.models import MockModelProvider
            res = MockModelProvider().generate(messages, system_prompt, tools)
            res.provider_mode = f"Offline Fallback (Mock Simulation - Gemini Error: {str(e)[:40]})"
            return res
