"""Demonstration script for JARVIS Nexus Milestone 8 Task and Workflow Automation."""

import os
from jarvis_nexus.agent import Agent
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.task_tools import register_task_tools
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.file_tools import register_file_tools
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.models import MockModelProvider


def setup_demo_workspace() -> None:
    workspace_dir = "data/workspace"
    os.makedirs(workspace_dir, exist_ok=True)
    csv_path = os.path.join(workspace_dir, "sales.csv")
    if not os.path.exists(csv_path):
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("product,price,units_sold\nGPU,1200.0,50\nCPU,450.0,120")


def main() -> None:
    print("=" * 65)
    print(" JARVIS Nexus - Milestone 8 Task & Workflow Automation Demo")
    print("=" * 65)

    setup_demo_workspace()
    db_path = "data/jarvis_tasks.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    print(f"\n[Step 1] Initializing Agent Instance #1 with task store: {db_path}")
    task_store_1 = TaskStore(db_path=db_path)
    tool_reg_1 = ToolRegistry()
    register_task_tools(tool_reg_1, task_store=task_store_1)
    agent_1 = Agent(tool_registry=tool_reg_1, model_provider=MockModelProvider())

    # 1. Create tasks
    prompts = [
        "Remind me to finish my hackathon README.",
        "Create a task to test Nemotron integration."
    ]
    for p in prompts:
        print(f"\nUser > {p}")
        res = agent_1.chat(p)
        print(f"Assistant > {res}")

    # 2. List pending tasks
    print("\nUser > What tasks do I have?")
    res = agent_1.chat("What tasks do I have?")
    print(f"Assistant >\n{res}")

    # 3. Filter high-priority tasks
    print("\nUser > Show me my high-priority tasks.")
    res = agent_1.chat("Show me my high-priority tasks.")
    print(f"Assistant >\n{res}")

    # 4. Complete a task
    print("\nUser > Mark the README task complete.")
    res = agent_1.chat("Mark the README task complete.")
    print(f"Assistant > {res}")

    print("\n" + "-" * 65)
    print("[Step 2] Shutting down Agent Instance #1.")
    print("[Step 3] Starting NEW Agent Instance #2 pointing to the same SQLite task DB...")
    print("-" * 65)

    task_store_2 = TaskStore(db_path=db_path)
    tool_reg_2 = ToolRegistry()
    register_task_tools(tool_reg_2, task_store=task_store_2)
    fm = FileManager(workspace_dir="data/workspace")
    register_file_tools(tool_reg_2, file_manager=fm)
    agent_2 = Agent(tool_registry=tool_reg_2, model_provider=MockModelProvider())

    print("\n[Step 4] Verifying task persistence across instances...")
    print("User > What tasks do I have?")
    res = agent_2.chat("What tasks do I have?")
    print(f"Assistant >\n{res}")

    print("\n[Step 5] Demonstrating Multi-Step Workflow (File Inspection -> Task Creation)...")
    wf_prompt = "Analyze sales.csv and save the key result as a task"
    print(f"User > {wf_prompt}")
    res = agent_2.chat(wf_prompt)
    print(f"Assistant > {res}")

    print("\nFinal Task List:")
    for t in task_store_2.list_tasks():
        print(f" - #{t.get('id')} {t.get('title')} [{t.get('status').upper()}]")

    print("\n" + "=" * 65)
    print(" SUCCESS: Task & Workflow Automation demonstrated successfully offline!")
    print("=" * 65)


if __name__ == "__main__":
    main()
