"""Demonstration script for JARVIS Nexus Milestone 4 Model-Driven Memory Persistence."""

import os
from jarvis_nexus.agent import Agent
from jarvis_nexus.memory import MemoryStore


def main() -> None:
    db_path = "data/jarvis_memory.db"
    print("=" * 65)
    print(" JARVIS Nexus - Milestone 4 Model-Driven Memory Demonstration")
    print("=" * 65)

    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print(f"\n[Step 1] Initializing Agent Instance #1 with database: {db_path}")
    memory_store_1 = MemoryStore(db_path=db_path)
    agent_1 = Agent(memory_store=memory_store_1)

    print("\n[Step 2] Agent #1 saves user identity memory...")
    prompt_1 = "Remember that my name is Duke"
    print(f"User > {prompt_1}")
    res_1 = agent_1.chat(prompt_1)
    print(f"Assistant > {res_1}\n")

    print("-" * 65)
    print("[Step 3] Shutting down Agent Instance #1.")
    print("[Step 4] Starting NEW Agent Instance #2 pointing to the exact same SQLite DB...")
    print("-" * 65)

    memory_store_2 = MemoryStore(db_path=db_path)
    agent_2 = Agent(memory_store=memory_store_2)

    print("\n[Step 5] Agent #2 retrieves memory across agent instance boundary...")
    prompt_2 = "What is my name?"
    print(f"User > {prompt_2}")
    res_2 = agent_2.chat(prompt_2)
    print(f"Assistant > {res_2}\n")

    # Verify persistence check
    retrieved_memory = memory_store_2.get_memory("user_name")
    print(f"Direct DB Query (Instance #2) for 'user_name': {retrieved_memory}")

    print("\n" + "=" * 65)
    if retrieved_memory and retrieved_memory.get("value") == "Duke":
        print(" SUCCESS: Memory successfully survived across separate Agent instances with natural responses!")
    else:
        print(" FAILED: Memory persistence check failed.")
    print("=" * 65)


if __name__ == "__main__":
    main()
