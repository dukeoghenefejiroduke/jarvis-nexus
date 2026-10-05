"""Unit tests for JARVIS Nexus enhanced MemoryStore (Milestone 3)."""

import os
import tempfile
import unittest
from jarvis_nexus.memory import MemoryStore


class TestMemoryStoreMilestone3(unittest.TestCase):
    """Test suite for structured SQLite memory store with categories, update, delete, and upsert."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_memory_m3.db")
        self.memory = MemoryStore(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_structured_memory_record(self) -> None:
        self.memory.save_memory("username", "Alice", category="identity")
        record = self.memory.get_memory("username")
        
        self.assertIsNotNone(record)
        self.assertEqual(record["key"], "username")
        self.assertEqual(record["value"], "Alice")
        self.assertEqual(record["category"], "identity")
        self.assertIn("created_at", record)
        self.assertIn("updated_at", record)
        self.assertIn("id", record)

    def test_upsert_prevents_duplicates(self) -> None:
        self.memory.save_memory("theme", "dark", category="preference")
        self.memory.save_memory("theme", "light", category="preference") # duplicate key upsert
        
        memories = self.memory.list_memories()
        self.assertEqual(len(memories), 1)
        self.assertEqual(self.memory.get_memory("theme")["value"], "light")

    def test_update_memory(self) -> None:
        self.memory.save_memory("goal", "Learn AI", category="task")
        success = self.memory.update_memory("goal", value="Master AI and Nemotron", category="project")
        self.assertTrue(success)

        record = self.memory.get_memory("goal")
        self.assertEqual(record["value"], "Master AI and Nemotron")
        self.assertEqual(record["category"], "project")

    def test_delete_memory(self) -> None:
        self.memory.save_memory("temp", "data")
        self.assertIsNotNone(self.memory.get_memory("temp"))

        deleted = self.memory.delete_memory("temp")
        self.assertTrue(deleted)
        self.assertIsNone(self.memory.get_memory("temp"))

    def test_category_filtering(self) -> None:
        self.memory.save_memory("lang", "Python", category="preference")
        self.memory.save_memory("project_name", "JARVIS", category="project")

        prefs = self.memory.list_memories(category="preference")
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0]["key"], "lang")

        search_res = self.memory.search_memory("Python", category="preference")
        self.assertEqual(len(search_res), 1)


if __name__ == "__main__":
    unittest.main()
