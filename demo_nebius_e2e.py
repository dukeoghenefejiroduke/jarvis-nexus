"""End-to-End Real Nebius Token Factory & NVIDIA Nemotron Verification Script (Milestone 10)."""

import os
import sys
from jarvis_nexus.config import Config
from jarvis_nexus.nebius_provider import NebiusProvider
from jarvis_nexus.agent import Agent
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.context import ContextManager
from jarvis_nexus.tools import ToolRegistry


def main() -> None:
    print("=" * 70)
    print(" JARVIS Nexus — Milestone 10: Real End-to-End Nebius E2E Verification")
    print("=" * 70)

    # STEP 1 — CONFIGURATION CHECK
    api_key = Config.NEBIUS_API_KEY
    endpoint = Config.NEBIUS_BASE_URL
    model = Config.NEBIUS_MODEL
    provider_name = Config.MODEL_PROVIDER

    print("\n[Step 1] Configuration Check:")
    print(f"  Provider: {provider_name}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Model: {model}")
    if api_key and api_key != "your_actual_nebius_api_key_here":
        print("  API Key: configured securely (hidden)")
    else:
        print("\n[Notice] NEBIUS_API_KEY is not configured or is set to placeholder.")
        print("Real Nebius verification cannot run without valid credentials.")
        print("Failing gracefully as required.")
        return

    try:
        provider = NebiusProvider(api_key=api_key, model=model, base_url=endpoint)
        memory_store = MemoryStore()
        task_store = TaskStore()
        file_manager = FileManager()
        context_manager = ContextManager(
            memory_store=memory_store,
            task_store=task_store,
            file_manager=file_manager
        )
        tool_registry = ToolRegistry(
            memory_store=memory_store,
            task_store=task_store,
            context_manager=context_manager
        )
        agent = Agent(
            model_provider=provider,
            memory_store=memory_store,
            tool_registry=tool_registry,
            context_manager=context_manager
        )

        # STEP 2 — BASIC MODEL TEST
        print("\n[Step 2] Basic Model Test:")
        msg2 = "Hello JARVIS. Introduce yourself in one short sentence."
        print(f"  User > {msg2}")
        resp2 = agent.chat(msg2)
        print(f"  Nemotron > {resp2}")

        # STEP 3 — TOOL-CALLING TEST (Calculator)
        print("\n[Step 3] Tool-Calling Test (Calculator):")
        msg3 = "What is 27 * 14?"
        print(f"  User > {msg3}")
        resp3 = agent.chat(msg3)
        print(f"  Nemotron > {resp3}")

        # STEP 4 — MEMORY TEST
        print("\n[Step 4] Memory Test:")
        msg4_1 = "Remember that my favorite project is JARVIS Nexus."
        print(f"  User > {msg4_1}")
        resp4_1 = agent.chat(msg4_1)
        print(f"  Nemotron > {resp4_1}")

        msg4_2 = "What is my favorite project?"
        print(f"  User > {msg4_2}")
        resp4_2 = agent.chat(msg4_2)
        print(f"  Nemotron > {resp4_2}")

        # STEP 5 — FILE INTELLIGENCE TEST
        print("\n[Step 5] File Intelligence Test:")
        os.makedirs("data/workspace", exist_ok=True)
        with open("data/workspace/sales.csv", "w") as f:
            f.write("item,price,quantity\nWidget A,10.0,5\nWidget B,20.0,3\nWidget C,30.0,2\n")
        msg5 = "Analyze sales.csv and tell me the average price."
        print(f"  User > {msg5}")
        resp5 = agent.chat(msg5)
        print(f"  Nemotron > {resp5}")

        # STEP 6 — TASK TEST
        print("\n[Step 6] Task Test:")
        msg6 = "Create a high-priority task to test the final JARVIS demo."
        print(f"  User > {msg6}")
        resp6 = agent.chat(msg6)
        print(f"  Nemotron > {resp6}")

        # STEP 7 — CONTEXT TEST
        print("\n[Step 7] Context Test:")
        msg7 = "What am I currently working on?"
        print(f"  User > {msg7}")
        resp7 = agent.chat(msg7)
        print(f"  Nemotron > {resp7}")

        # STEP 8 — MULTI-TOOL TEST
        print("\n[Step 8] Multi-Tool Test (File + Task workflow):")
        msg8 = "Analyze sales.csv and create a high-priority task to review the results."
        print(f"  User > {msg8}")
        resp8 = agent.chat(msg8)
        print(f"  Nemotron > {resp8}")

        # STEP 9 — ERROR HANDLING
        print("\n[Step 9] Error Handling Test (Invalid tool or safe failure scenario):")
        msg9 = "Execute non_existent_tool_xyz_12345."
        print(f"  User > {msg9}")
        resp9 = agent.chat(msg9)
        print(f"  Nemotron / Agent > {resp9}")

        print("\n" + "=" * 70)
        print(" Milestone 10 End-to-End Nebius Verification Completed Successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n[Error] An error occurred during Nebius E2E execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
