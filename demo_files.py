"""Demonstration script for JARVIS Nexus Milestone 6 File and Data Intelligence."""

import os
import json
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.file_tools import register_file_tools
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.agent import Agent
from jarvis_nexus.models import MockModelProvider


def setup_sample_workspace(workspace_dir: str = "data/workspace") -> None:
    os.makedirs(workspace_dir, exist_ok=True)

    # 1. notes.md
    with open(os.path.join(workspace_dir, "notes.md"), "w", encoding="utf-8") as f:
        f.write("# Hackathon Notes\n- Build high performance AI assistant.\n- Implement secure file inspection.\n- Key focus: SIWES and NVIDIA Nemotron.")

    # 2. sales.csv
    with open(os.path.join(workspace_dir, "sales.csv"), "w", encoding="utf-8") as f:
        f.write("product,price,units_sold\nGPU,1200.0,50\nCPU,450.0,120\nRAM,150.0,300")

    # 3. project.json
    with open(os.path.join(workspace_dir, "project.json"), "w", encoding="utf-8") as f:
        json.dump({
            "project_name": "JARVIS Nexus",
            "hackathon": "Nebius x NVIDIA Global AI Hackathon 2026",
            "model": "nvidia/Nemotron-3_5-Lightning",
            "status": "Active Development"
        }, f, indent=2)


def main() -> None:
    print("=" * 65)
    print(" JARVIS Nexus - Milestone 6 File and Data Intelligence Demo")
    print("=" * 65)

    workspace_path = "data/workspace"
    print(f"\n[Step 1] Setting up sample files in workspace: {workspace_path}")
    setup_sample_workspace(workspace_path)

    print("\n[Step 2] Initializing Agent with File Intelligence Tools...")
    fm = FileManager(workspace_dir=workspace_path)
    registry = ToolRegistry()
    register_file_tools(registry, file_manager=fm)
    agent = Agent(tool_registry=registry, model_provider=MockModelProvider())

    # Demo queries
    queries = [
        "What files do I have?",
        "What's inside sales.csv?",
        "Search my notes for SIWES",
        "Read project.json"
    ]

    for q in queries:
        print(f"\nUser > {q}")
        response = agent.chat(q)
        print(f"Assistant >\n{response}")
        print("-" * 65)

    print("\n" + "=" * 65)
    print(" SUCCESS: File intelligence demonstrated successfully offline!")
    print("=" * 65)


if __name__ == "__main__":
    main()
