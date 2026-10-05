"""OpenAI-compatible client wrapper for Nebius Token Factory and NVIDIA Nemotron."""

from openai import OpenAI
from jarvis_nexus.config import Config


class NebiusClient:
    """Client for interacting with NVIDIA Nemotron via Nebius Token Factory."""

    def __init__(self) -> None:
        Config.validate()
        self.client = OpenAI(
            api_key=Config.NEBIUS_API_KEY,
            base_url=Config.NEBIUS_BASE_URL,
        )
        self.model = Config.NEBIUS_MODEL

    def chat(self, prompt: str, system_prompt: str = "You are JARVIS Nexus, an advanced AI assistant powered by NVIDIA Nemotron.") -> str:
        """Send a chat message to NVIDIA Nemotron and return the response text."""
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
