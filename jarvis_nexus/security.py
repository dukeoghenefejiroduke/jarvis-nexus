"""Security and secret redaction utilities for JARVIS Nexus."""

import re
import os
from typing import Any


def is_public_demo() -> bool:
    """Check if public demo hardening mode is enabled via environment variable."""
    return os.getenv("JARVIS_PUBLIC_DEMO", "").lower() in ("true", "1", "yes")


def redact_secrets(text: str) -> str:
    """Redact sensitive information such as API keys, bearer tokens, and credentials from text."""
    if not isinstance(text, str):
        text = str(text)

    # Redact Authorization Bearer tokens
    text = re.sub(r'bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer [REDACTED]', text, flags=re.IGNORECASE)

    # Redact common API key assignment patterns (e.g., api_key=..., NEBIUS_API_KEY: ...)
    text = re.sub(r'(api[_-]?key|token|secret|password)[=:\s]+[\'"]?[a-zA-Z0-9_\-\.]{8,}[\'"]?', r'\1: [REDACTED]', text, flags=re.IGNORECASE)

    # Redact Nebius API key patterns if accidentally exposed
    text = re.sub(r'nebius[_-]?api[_-]?key[=:\s]+[^\s]+', 'NEBIUS_API_KEY: [REDACTED]', text, flags=re.IGNORECASE)

    return text


def safe_exception_message(exc: Exception) -> str:
    """Return an exception message with all potential secrets redacted."""
    return redact_secrets(str(exc))
