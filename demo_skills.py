"""Demonstration script for JARVIS Nexus Milestone 7 Modular Skills System."""

import os
from jarvis_nexus.agent import Agent
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.file_tools import register_file_tools
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.models import MockModelProvider


def setup_demo_workspace() -> None:
    workspace_dir = "data/workspace"
    os.makedirs(workspace_dir, exist_ok=True)

    # 1. sales.csv for Data Analyst
    csv_path = os.path.join(workspace_dir, "sales.csv")
    if not os.path.exists(csv_path):
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("product,price,units_sold\nGPU,1200.0,50\nCPU,450.0,120\nRAM,150.0,300")

    # 2. notes.md for Research Assistant
    notes_path = os.path.join(workspace_dir, "notes.md")
    if not os.path.exists(notes_path):
        with open(notes_path, "w", encoding="utf-8") as f:
            f.write("# Project Notes\n- Research topic: SIWES.\n- Architecture: Modular skills and tools.")


def main() -> None:
    print("=" * 65)
    print(" JARVIS Nexus - Milestone 7 Modular Skills System Demo")
    print("=" * 65)

    setup_demo_workspace()

    print("\n[Step 1] Initializing Agent with Skills and Tools...")
    agent = Agent(model_provider=MockModelProvider())

    # Demo queries showcasing skills & tool orchestration
    demo_prompts = [
        "What skills do you have?",
        "Analyze sales.csv.",
        "Help me understand my project.",
        "Search my project files for SIWES."
    ]

    for prompt in demo_prompts:
        print(f"\nUser > {prompt}")
        response = agent.chat(prompt)
        print(f"Assistant >\n{response}")
        print("-" * 65)

    print("\n" + "=" * 65)
    print(" SUCCESS: Modular Skills System demonstrated successfully offline!")
    print("=" * 65)


if __name__ == "__main__":
    main()
