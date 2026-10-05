"""Test script to verify NVIDIA Nemotron connectivity via Nebius Token Factory."""

import sys
from jarvis_nexus.client import NebiusClient
from jarvis_nexus.config import Config


def main() -> None:
    print("Initializing JARVIS Nexus client...")
    try:
        client = NebiusClient()
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        print("Please ensure NEBIUS_API_KEY is set in your environment or .env file.", file=sys.stderr)
        sys.exit(1)

    prompt = "Hello JARVIS Nexus! Please confirm you are online and running NVIDIA Nemotron via Nebius Token Factory."
    print(f"\nSending prompt to model ({Config.NEBIUS_MODEL}):\n> {prompt}\n")

    try:
        response = client.chat(prompt)
        print("Response from Nemotron:")
        print("-" * 60)
        print(response)
        print("-" * 60)
    except Exception as e:
        print(f"Error communicating with Nebius API: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
