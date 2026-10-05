"""Demonstration of Advanced Context and Memory Intelligence in JARVIS Nexus (Milestone 9)."""

import os
import tempfile
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.skills.registry import SkillRegistry
from jarvis_nexus.context import ContextManager
from jarvis_nexus.agent import Agent
from jarvis_nexus.models import MockModelProvider


def main() -> None:
    print("=" * 60)
    print("JARVIS Nexus — Milestone 9 Demo: Advanced Context Intelligence")
    print("=" * 60)

    # Initialize storage and context manager
    memory_store = MemoryStore()
    task_store = TaskStore()
    file_manager = FileManager()
    skill_registry = SkillRegistry()

    # Seed persistent memories
    memory_store.save_memory("project_name", "JARVIS Nexus", category="project")
    memory_store.save_memory("hackathon", "Nebius x NVIDIA Global AI Hackathon 2026", category="hackathon")
    memory_store.save_memory("language", "Python 3.14", category="tech")

    # Seed pending tasks with priorities
    task_store.create_task(title="Implement Advanced Context Manager", description="Build ContextManager for multi-source intelligence", priority="high")
    task_store.create_task(title="Write Milestone 9 Unit Tests", description="Ensure 100% test coverage for context intelligence", priority="high")
    task_store.create_task(title="Update Documentation", description="Document ContextManager architecture in README", priority="medium")

    # Create workspace file
    os.makedirs("data/workspace", exist_ok=True)
    with open("data/workspace/project.json", "w") as f:
        f.write('{"project": "JARVIS Nexus", "milestone": 9, "status": "active"}\n')

    # Initialize ContextManager and Agent
    context_manager = ContextManager(
        memory_store=memory_store,
        task_store=task_store,
        file_manager=file_manager,
        skill_registry=skill_registry
    )

    agent = Agent(
        model_provider=MockModelProvider(),
        memory_store=memory_store,
        context_manager=context_manager
    )

    # 1. Ask: "What am I working on?"
    print("\n[User]: What am I working on?")
    resp1 = agent.chat("What am I working on?")
    print(f"[JARVIS]: {resp1}")

    # 2. Ask: "What are my current priorities?"
    print("\n[User]: What are my current priorities?")
    resp2 = agent.chat("What are my current priorities?")
    print(f"[JARVIS]: {resp2}")

    # 3. Ask: "What should I work on next?"
    print("\n[User]: What should I work on next?")
    resp3 = agent.chat("What should I work on next?")
    print(f"[JARVIS]: {resp3}")

    # 4. Ask: "What do you know about this project?"
    print("\n[User]: What do you know about this project?")
    resp4 = agent.chat("What do you know about this project?")
    print(f"[JARVIS]: {resp4}")

    print("\n" + "=" * 60)
    print("Demo completed successfully. All context gathered from local stores offline!")
    print("=" * 60)


if __name__ == "__main__":
    main()
