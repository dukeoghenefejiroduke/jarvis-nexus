"""OpenAI-compatible client wrapper for Nebius Token Factory and NVIDIA Nemotron."""

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from jarvis_nexus.config import Config


class NebiusClient:
    """Client for interacting with NVIDIA Nemotron via Nebius Token Factory."""

    def __init__(self) -> None:
        Config.validate()
        if OpenAI is None:
            raise ImportError("The 'openai' package is required for NebiusClient. Install openai or use NebiusProvider.")
        self.client = OpenAI(
            api_key=Config.NEBIUS_API_KEY,
            base_url=Config.NEBIUS_BASE_URL,
        )
        self.model = Config.NEBIUS_MODEL

    def chat(self, prompt: str, system_prompt: str = "You are JARVIS Nexus, an advanced AI assistant.") -> str:
        """Send a chat message to NVIDIA Nemotron and return the response text."""
        if OpenAI is None:
            raise ImportError("The 'openai' package is required for NebiusClient.")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        return content if content else ""
