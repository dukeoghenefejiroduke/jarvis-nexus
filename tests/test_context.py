"""Tests for Advanced Context and Memory Intelligence in JARVIS Nexus (Milestone 9)."""

import os
import tempfile
import unittest
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.skills.registry import SkillRegistry
from jarvis_nexus.context import ContextManager
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.agent import Agent
from jarvis_nexus.models import MockModelProvider, ChatMessage


class TestContextIntelligence(unittest.TestCase):
    """Test suite for ContextManager, tools, agent integration, and memory/task/file relevance."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_fd, self.mem_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.task_db_fd, self.task_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.task_db_fd)

        self.memory_store = MemoryStore(db_path=self.mem_db_path)
        self.task_store = TaskStore(db_path=self.task_db_path)
        self.file_manager = FileManager(workspace_dir=self.temp_dir.name)
        self.skill_registry = SkillRegistry()

        self.context_manager = ContextManager(
            memory_store=self.memory_store,
            task_store=self.task_store,
            file_manager=self.file_manager,
            skill_registry=self.skill_registry,
            max_history_messages=5,
            max_memories=3,
            max_tasks=3,
            max_files=3
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        if os.path.exists(self.mem_db_path):
            os.remove(self.mem_db_path)
        if os.path.exists(self.task_db_path):
            os.remove(self.task_db_path)

    def test_context_manager_initialization(self) -> None:
        """Test ContextManager initializes with stores and configuration."""
        self.assertEqual(self.context_manager.max_history_messages, 5)
        self.assertEqual(self.context_manager.max_memories, 3)
        self.assertIsNotNone(self.context_manager.skill_registry)
        self.assertTrue(len(self.context_manager.skill_registry.list_skills()) > 0)

    def test_memory_relevance_and_scoring(self) -> None:
        """Test deterministic memory relevance scoring and category matching."""
        self.memory_store.save_memory("project_name", "JARVIS Nexus", category="project")
        self.memory_store.save_memory("hackathon", "Nebius x NVIDIA Global AI Hackathon 2026", category="hackathon")
        self.memory_store.save_memory("user_name", "Alice", category="identity")
        self.memory_store.save_memory("favorite_color", "Blue", category="preferences")

        relevant = self.context_manager.get_relevant_memories(query="What hackathon is JARVIS Nexus for?", limit=2)
        self.assertTrue(len(relevant) <= 2)
        keys = [m["key"] for m in relevant]
        self.assertIn("hackathon", keys)
        self.assertIn("project_name", keys)

    def test_task_context_and_priority(self) -> None:
        """Test task context retrieval with priority ordering."""
        self.task_store.create_task(title="Low task", priority="low", description="Do later")
        self.task_store.create_task(title="High task", priority="high", description="Do now")
        self.task_store.create_task(title="Medium task", priority="medium", description="Do soon")

        tasks = self.context_manager.get_relevant_tasks(status="pending", limit=2)
        self.assertEqual(len(tasks), 2)
        # High priority should come first
        self.assertEqual(tasks[0]["priority"], "high")
        self.assertEqual(tasks[0]["title"], "High task")

    def test_file_context_and_snippets(self) -> None:
        """Test file context and search snippet retrieval."""
        test_file_path = os.path.join(self.temp_dir.name, "notes.md")
        with open(test_file_path, "w") as f:
            f.write("# Project Notes\nBuilding JARVIS Nexus with Nebius and NVIDIA technologies.")

        file_info = self.context_manager.get_relevant_files(query="Nexus")
        self.assertIn("files", file_info)
        self.assertIn("search_snippets", file_info)
        self.assertTrue(len(file_info["files"]) > 0)
        self.assertTrue(len(file_info["search_snippets"]) > 0)

    def test_project_context_aggregation(self) -> None:
        """Test aggregating project context (memories, tasks, files, skills)."""
        self.memory_store.save_memory("project_name", "JARVIS Nexus", category="project")
        self.task_store.create_task(title="Core task", priority="high")

        ctx = self.context_manager.get_project_context(query="JARVIS Nexus project")
        self.assertEqual(ctx["query"], "JARVIS Nexus project")
        self.assertTrue(len(ctx["memories"]) > 0)
        self.assertTrue(len(ctx["pending_tasks"]) > 0)
        self.assertIsInstance(ctx["workspace_files"], list)
        self.assertIsInstance(ctx["available_skills"], list)

        prompt_str = self.context_manager.assemble_context_prompt("JARVIS Nexus")
        self.assertIn("JARVIS Nexus", prompt_str)
        self.assertIn("Core task", prompt_str)

    def test_conversation_history_trimming(self) -> None:
        """Test conversation history trimming respects max history messages."""
        messages = [
            ChatMessage(role="system", content="System Prompt"),
            ChatMessage(role="user", content="Msg 1"),
            ChatMessage(role="assistant", content="Msg 2"),
            ChatMessage(role="user", content="Msg 3"),
            ChatMessage(role="assistant", content="Msg 4"),
            ChatMessage(role="user", content="Msg 5"),
            ChatMessage(role="assistant", content="Msg 6"),
        ]
        trimmed = self.context_manager.trim_history(messages)
        # Should preserve system message + last 5 non-system messages
        self.assertEqual(trimmed[0].role, "system")
        self.assertEqual(len(trimmed), 1 + 5)

    def test_context_tool_registration(self) -> None:
        """Test tool registration and execution of get_project_context."""
        tool_registry = ToolRegistry(
            memory_store=self.memory_store,
            task_store=self.task_store,
            context_manager=self.context_manager
        )
        definitions = tool_registry.get_definitions()
        tool_names = [d.name for d in definitions]
        self.assertIn("get_project_context", tool_names)

        result = tool_registry.execute("get_project_context", {"query": "project"})
        self.assertIn("memories", result)
        self.assertIn("pending_tasks", result)

    def test_agent_integration_and_mock_model(self) -> None:
        """Test Agent and MockModelProvider handling context queries."""
        self.memory_store.save_memory("project_name", "JARVIS Nexus", category="project")
        self.task_store.create_task(title="Test Milestone 9", priority="high")

        agent = Agent(
            model_provider=MockModelProvider(),
            memory_store=self.memory_store,
            context_manager=self.context_manager
        )

        response = agent.chat("What am I working on?")
        self.assertTrue(len(response) > 0)

        response2 = agent.chat("What should I work on next?")
        self.assertTrue(len(response2) > 0)

        response3 = agent.chat("What do you know about this project?")
        self.assertTrue(len(response3) > 0)

    def test_missing_information_behavior(self) -> None:
        """Test behavior when requested information is missing."""
        ctx = self.context_manager.get_project_context(query="nonexistent_topic_xyz")
        self.assertIsInstance(ctx["memories"], list)
        self.assertIsInstance(ctx["pending_tasks"], list)
        # Even if empty, returns structured results without crashing
        self.assertEqual(ctx["query"], "nonexistent_topic_xyz")
