"""Unit tests for JARVIS Nexus File and Data Intelligence (Milestone 6)."""

import os
import tempfile
import unittest
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.file_tools import register_file_tools
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.agent import Agent
from jarvis_nexus.models import MockModelProvider


class TestFileIntelligence(unittest.TestCase):
    """Test suite for FileManager, security constraints, and file intelligence tools."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_dir = os.path.join(self.temp_dir.name, "workspace")
        self.fm = FileManager(workspace_dir=self.workspace_dir)

        # Create sample test files
        self.txt_path = os.path.join(self.workspace_dir, "notes.md")
        with open(self.txt_path, "w", encoding="utf-8") as f:
            f.write("# Project Notes\nImportant keyword: SIWES.\nSecond line.")

        self.csv_path = os.path.join(self.workspace_dir, "sales.csv")
        with open(self.csv_path, "w", encoding="utf-8") as f:
            f.write("item,price,quantity\nApple,1.5,10\nBanana,0.8,20\nOrange,1.2,15")

        self.json_path = os.path.join(self.workspace_dir, "project.json")
        with open(self.json_path, "w", encoding="utf-8") as f:
            f.write('{"name": "JARVIS Nexus", "version": "1.0", "active": true}')

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_workspace_creation_and_listing(self) -> None:
        files = self.fm.list_files()
        self.assertEqual(len(files), 3)
        filenames = {f["name"] for f in files}
        self.assertIn("notes.md", filenames)
        self.assertIn("sales.csv", filenames)
        self.assertIn("project.json", filenames)

    def test_read_valid_file(self) -> None:
        res = self.fm.read_file("notes.md")
        self.assertEqual(res["status"], "success")
        self.assertIn("SIWES", res["content"])

    def test_read_missing_file(self) -> None:
        res = self.fm.read_file("missing.txt")
        self.assertEqual(res["status"], "error")
        self.assertIn("not found", res["message"])

    def test_inspect_csv(self) -> None:
        res = self.fm.inspect_csv("sales.csv")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["row_count"], 3)
        self.assertEqual(res["column_count"], 3)
        self.assertIn("item", res["column_names"])
        self.assertIn("price", res["numeric_statistics"])
        self.assertAlmostEqual(res["numeric_statistics"]["price"]["mean"], 1.16666, places=4)

    def test_inspect_json(self) -> None:
        res = self.fm.inspect_json("project.json")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["data_type"], "dict")
        self.assertIn("name", res["top_level_keys"])
        self.assertIn("JARVIS Nexus", res["preview"])

    def test_search_files(self) -> None:
        results = self.fm.search_files("SIWES")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["filename"], "notes.md")
        self.assertIn("SIWES", results[0]["snippet"])

    def test_path_traversal_prevention(self) -> None:
        with self.assertRaises(ValueError):
            self.fm._sanitize_path("../../etc/passwd")

    def test_absolute_path_outside_workspace_rejection(self) -> None:
        with self.assertRaises(ValueError):
            self.fm._sanitize_path("/etc/passwd")

    def test_unsupported_extension_handling(self) -> None:
        bad_path = os.path.join(self.workspace_dir, "script.py")
        with open(bad_path, "w") as f:
            f.write("print('hello')")
        res = self.fm.read_file("script.py")
        self.assertEqual(res["status"], "error")
        self.assertIn("Unsupported file extension", res["message"])

    def test_agent_tool_integration_for_files(self) -> None:
        registry = ToolRegistry()
        register_file_tools(registry, file_manager=self.fm)
        agent = Agent(tool_registry=registry, model_provider=MockModelProvider())

        # Test listing files through agent
        resp1 = agent.chat("What files do I have?")
        self.assertIn("notes.md", resp1)

        # Test inspecting CSV through agent
        resp2 = agent.chat("What's inside sales.csv?")
        self.assertIn("sales.csv", resp2)

        # Test searching notes through agent
        resp3 = agent.chat("Search my notes for SIWES")
        self.assertIn("notes.md", resp3)


if __name__ == "__main__":
    unittest.main()
