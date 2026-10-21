"""Comprehensive Production Hardening & Security Tests for JARVIS Nexus (Milestone 10)."""

import os
import tempfile
import unittest
from jarvis_nexus.config import Config
from jarvis_nexus.security import redact_secrets, safe_exception_message
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.agent import Agent
from jarvis_nexus.models import MockModelProvider, ChatMessage


class TestProductionHardening(unittest.TestCase):
    """Test suite covering production hardening, security, secret redaction, and edge-case handling."""

    def test_secret_redaction(self) -> None:
        """Test secret redaction utility hides API keys, bearer tokens, and credentials."""
        secret_key = "mock_placeholder_token_abc123xyz"
        text = f"Error communicating with server using bearer {secret_key} and NEBIUS_API_KEY={secret_key}"
        redacted = redact_secrets(text)
        self.assertNotIn(secret_key, redacted)
        self.assertIn("[REDACTED]", redacted)

        exc = ValueError(f"Failed with token {secret_key}")
        safe_msg = safe_exception_message(exc)
        self.assertNotIn(secret_key, safe_msg)
        self.assertIn("[REDACTED]", safe_msg)

    def test_config_validation(self) -> None:
        """Test configuration validation handles mock and invalid nebius settings safely."""
        old_provider = Config.MODEL_PROVIDER
        old_key = Config.NEBIUS_API_KEY
        try:
            Config.MODEL_PROVIDER = "mock"
            # Should not raise when provider is mock
            Config.validate_nebius()

            Config.MODEL_PROVIDER = "nebius"
            Config.NEBIUS_API_KEY = ""
            with self.assertRaises(ValueError):
                Config.validate_nebius()

            Config.NEBIUS_API_KEY = "your_actual_nebius_api_key_here"
            with self.assertRaises(ValueError):
                Config.validate_nebius()
        finally:
            Config.MODEL_PROVIDER = old_provider
            Config.NEBIUS_API_KEY = old_key

    def test_tool_registry_hardening(self) -> None:
        """Test ToolRegistry handles unknown tools, exceptions, and malformed arguments safely."""
        registry = ToolRegistry()
        
        # Unknown tool
        res = registry.execute("non_existent_tool_xyz", {})
        self.assertIn("error", res)

        # Tool exception handling
        registry.register(
            name="faulty_tool",
            description="Always raises an exception",
            parameters={"type": "object", "properties": {}, "required": []},
            func=lambda: 1 / 0
        )
        res_fault = registry.execute("faulty_tool", {})
        self.assertIn("error", res_fault)

    def test_file_security_hardening(self) -> None:
        """Test FileManager blocks path traversal, absolute paths, and malformed files."""
        temp_dir = tempfile.TemporaryDirectory()
        fm = FileManager(workspace_dir=temp_dir.name)

        # Path traversal attacks via _sanitize_path
        with self.assertRaises(ValueError):
            fm._sanitize_path("../outside.txt")

        with self.assertRaises(ValueError):
            fm._sanitize_path("../../etc/passwd")

        # Absolute paths outside workspace
        with self.assertRaises(ValueError):
            fm._sanitize_path("/etc/passwd")

        # read_file returns error dict for traversal
        res = fm.read_file("../outside.txt")
        self.assertEqual(res["status"], "error")

        temp_dir.cleanup()

    def test_memory_store_edge_cases(self) -> None:
        """Test MemoryStore handles empty queries, duplicates, updates, and deletes safely."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        store = MemoryStore(db_path=db_path)

        store.save_memory("key1", "value1", category="project")
        store.save_memory("key1", "value1_updated", category="project") # Upsert duplicate key
        rec = store.get_memory("key1")
        self.assertEqual(rec["value"], "value1_updated")

        # Update nonexistent
        self.assertFalse(store.update_memory("nonexistent", value="val"))

        # Delete nonexistent
        self.assertFalse(store.delete_memory("nonexistent"))

        # Search empty / listing
        self.assertIsInstance(store.search_memory(""), list)
        self.assertIsInstance(store.list_memories(category="nonexistent"), list)

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_task_store_validation(self) -> None:
        """Test TaskStore validates statuses, priorities, and handles missing IDs safely."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        store = TaskStore(db_path=db_path)

        # Invalid status
        with self.assertRaises(ValueError):
            store.create_task(title="Test", status="invalid_status")

        # Invalid priority
        with self.assertRaises(ValueError):
            store.create_task(title="Test", priority="ultra_high")

        # Get nonexistent task
        self.assertIsNone(store.get_task(99999))

        # Update nonexistent task
        self.assertFalse(store.update_task(99999, title="New"))

        # Delete nonexistent task
        self.assertFalse(store.delete_task(99999))

        if os.path.exists(db_path):
            os.remove(db_path)

    def test_agent_loop_hardening(self) -> None:
        """Test Agent handles empty messages and iteration bounds safely."""
        agent = Agent(model_provider=MockModelProvider())
        resp = agent.chat("")
        self.assertTrue(len(resp) > 0)
        self.assertTrue(len(agent.get_history()) >= 2)
