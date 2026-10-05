"""Demonstration script for JARVIS Nexus Nebius Token Factory & NVIDIA Nemotron integration."""

import os
from jarvis_nexus.config import Config
from jarvis_nexus.nebius_provider import NebiusProvider
from jarvis_nexus.agent import Agent


def main() -> None:
    print("=" * 65)
    print(" JARVIS Nexus - Nebius Token Factory & NVIDIA Nemotron Demo")
    print("=" * 65)

    api_key = Config.NEBIUS_API_KEY
    if not api_key:
        print("\n[Notice] NEBIUS_API_KEY is not set in your environment or .env file.")
        print("This demo refuses gracefully when credentials are absent.")
        print("To run with Nebius Token Factory, set NEBIUS_API_KEY and MODEL_PROVIDER=nebius.")
        print("Current running mode remains offline (Mock Provider default).")
        return

    print("\n[Status] NEBIUS_API_KEY detected securely.")
    print(f"Endpoint: {Config.NEBIUS_BASE_URL}")
    print(f"Model: {Config.NEBIUS_MODEL}")

    try:
        provider = NebiusProvider(api_key=api_key)
        agent = Agent(model_provider=provider)

        prompt = "Hello NVIDIA Nemotron! Please confirm you are online and tell me what time it is."
        print(f"\nUser > {prompt}")
        
        response = agent.chat(prompt)
        print(f"\nNemotron > {response}")

    except Exception as e:
        print(f"\nError executing Nebius demo: {e}")


if __name__ == "__main__":
    main()
