"""Unit tests for JARVIS Nexus ToolRegistry."""

import os
import tempfile
import unittest
from unittest.mock import patch
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tools import ToolRegistry


class TestToolRegistry(unittest.TestCase):
    """Test suite for tool registry and secure tool execution."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_tools.db")
        self.memory = MemoryStore(db_path=self.db_path)
        self.registry = ToolRegistry(memory_store=self.memory)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_get_current_time(self) -> None:
        result = self.registry.execute("get_current_time", {})
        self.assertIn("formatted", result)
        self.assertIn("iso", result)

    def test_calculator_valid(self) -> None:
        result = self.registry.execute("calculator", {"expression": "2 + 3 * 4"})
        self.assertEqual(result["result"], 14)

    def test_calculator_invalid_syntax(self) -> None:
        result = self.registry.execute("calculator", {"expression": "import os; os.system('ls')"})
        self.assertIn("error", result)

    def test_memory_tools(self) -> None:
        save_res = self.registry.execute("save_memory", {"key": "agent", "value": "JARVIS"})
        self.assertEqual(save_res["status"], "success")

        search_res = self.registry.execute("search_memory", {"query": "JARVIS"})
        self.assertEqual(search_res["count"], 1)
        self.assertEqual(search_res["results"][0]["key"], "agent")

    @patch("jarvis_nexus.qloo_tools.handle_cultural_trending")
    def test_qloo_trending_tool(self, mock_trending) -> None:
        mock_trending.return_value = {"recommendations": [{"name": "Trending Movie"}]}
        result = self.registry.execute("qloo_trending", {"category": "movie"})
        self.assertIn("recommendations", result)
        self.assertEqual(result["recommendations"][0]["name"], "Trending Movie")


if __name__ == "__main__":
    unittest.main()
