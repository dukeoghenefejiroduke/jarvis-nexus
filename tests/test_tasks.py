"""Unit tests for JARVIS Nexus Task and Workflow Automation (Milestone 8)."""

import os
import tempfile
import unittest
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.task_tools import register_task_tools
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.agent import Agent
from jarvis_nexus.models import MockModelProvider
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.file_tools import register_file_tools


class TestTaskAutomation(unittest.TestCase):
    """Test suite for TaskStore, task tools, persistence, validation, and workflows."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_tasks.db")
        self.task_store = TaskStore(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_get_task(self) -> None:
        tid = self.task_store.create_task("Finish README", description="Document hackathon project", priority="high")
        self.assertGreater(tid, 0)

        task = self.task_store.get_task(tid)
        self.assertIsNotNone(task)
        self.assertEqual(task["title"], "Finish README")
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["status"], "pending")

    def test_invalid_status_and_priority_rejection(self) -> None:
        with self.assertRaises(ValueError):
            self.task_store.create_task("Bad Task", priority="super_urgent")

        tid = self.task_store.create_task("Good Task", priority="medium")
        with self.assertRaises(ValueError):
            self.task_store.update_task(tid, status="flying")

    def test_update_and_complete_task(self) -> None:
        tid = self.task_store.create_task("Test task")
        success = self.task_store.complete_task(tid)
        self.assertTrue(success)

        task = self.task_store.get_task(tid)
        self.assertEqual(task["status"], "completed")
        self.assertIsNotNone(task["completed_at"])

    def test_delete_task(self) -> None:
        tid = self.task_store.create_task("Temporary task")
        deleted = self.task_store.delete_task(tid)
        self.assertTrue(deleted)
        self.assertIsNone(self.task_store.get_task(tid))

    def test_listing_and_filtering_tasks(self) -> None:
        self.task_store.create_task("Task 1", priority="low", status="pending")
        self.task_store.create_task("Task 2", priority="high", status="pending")
        self.task_store.create_task("Task 3", priority="critical", status="completed")

        pending_tasks = self.task_store.list_tasks(status="pending")
        self.assertEqual(len(pending_tasks), 2)

        high_tasks = self.task_store.list_tasks(priority="high")
        self.assertEqual(len(high_tasks), 1)

    def test_search_tasks(self) -> None:
        self.task_store.create_task("Review Nemotron client code")
        results = self.task_store.search_tasks("Nemotron")
        self.assertEqual(len(results), 1)
        self.assertIn("Nemotron", results[0]["title"])

    def test_persistence_across_agent_instances(self) -> None:
        reg1 = ToolRegistry(task_store=self.task_store)
        agent1 = Agent(tool_registry=reg1, model_provider=MockModelProvider())

        agent1.chat("Create a task to finish my hackathon README")

        # New agent instance using same store
        reg2 = ToolRegistry(task_store=self.task_store)
        agent2 = Agent(tool_registry=reg2, model_provider=MockModelProvider())

        tasks = self.task_store.list_tasks()
        self.assertGreaterEqual(len(tasks), 1)

    def test_multi_step_workflow_behavior(self) -> None:
        workspace = os.path.join(self.temp_dir.name, "workspace")
        os.makedirs(workspace, exist_ok=True)
        csv_p = os.path.join(workspace, "sales.csv")
        with open(csv_p, "w", encoding="utf-8") as f:
            f.write("product,price\nGPU,1200.0")

        fm = FileManager(workspace_dir=workspace)
        tool_reg = ToolRegistry(task_store=self.task_store)
        register_file_tools(tool_reg, file_manager=fm)

        agent = Agent(tool_registry=tool_reg, model_provider=MockModelProvider())
        resp = agent.chat("Analyze sales.csv and save the key result as a task")
        
        tasks = self.task_store.list_tasks()
        self.assertGreaterEqual(len(tasks), 1)
        self.assertIn("sales.csv", tasks[0]["title"])


if __name__ == "__main__":
    unittest.main()
