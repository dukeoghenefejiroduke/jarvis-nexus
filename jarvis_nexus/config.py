"""Configuration management for JARVIS Nexus."""

import os
from jarvis_nexus.security import redact_secrets

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """Configuration loaded from environment variables with security validation."""
    NEBIUS_API_KEY: str = os.getenv("NEBIUS_API_KEY", "")
    NEBIUS_BASE_URL: str = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
    NEBIUS_MODEL: str = os.getenv("NEBIUS_MODEL", "nvidia/Nemotron-3_5-Lightning")
    MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER", "mock").lower()

    @classmethod
    def validate_nebius(cls) -> None:
        """Ensure required Nebius configuration is present and valid without leaking secrets."""
        if cls.MODEL_PROVIDER != "nebius":
            return

        if not cls.NEBIUS_API_KEY or cls.NEBIUS_API_KEY == "your_actual_nebius_api_key_here":
            raise ValueError(
                "NEBIUS_API_KEY environment variable is missing or set to placeholder. "
                "Please configure a valid Nebius API key in your environment or .env file."
            )

        if not cls.NEBIUS_BASE_URL or not cls.NEBIUS_BASE_URL.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid NEBIUS_BASE_URL: {redact_secrets(cls.NEBIUS_BASE_URL)}. Must be a valid HTTP/HTTPS URL."
            )

        if not cls.NEBIUS_MODEL:
            raise ValueError("NEBIUS_MODEL environment variable cannot be empty when MODEL_PROVIDER=nebius.")
