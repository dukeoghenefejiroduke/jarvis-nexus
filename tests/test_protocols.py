"""Unit tests for understandable system protocols and TelemetryManager."""

import unittest
import os
import tempfile
from jarvis_nexus.protocols import ProtocolEngine
from jarvis_nexus.telemetry import TelemetryManager
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager


class TestSystemProtocolsAndTelemetry(unittest.TestCase):
    """Test suite for system protocols and device telemetry."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_mem = os.path.join(self.temp_dir.name, "mem.db")
        self.db_task = os.path.join(self.temp_dir.name, "task.db")
        self.workspace = os.path.join(self.temp_dir.name, "workspace")
        os.makedirs(self.workspace, exist_ok=True)

        self.memory = MemoryStore(db_path=self.db_mem)
        self.tasks = TaskStore(db_path=self.db_task)
        self.files = FileManager(workspace_dir=self.workspace)
        self.protocols = ProtocolEngine(self.memory, self.tasks, self.files)
        self.telemetry = TelemetryManager()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_reset_session_protocol(self) -> None:
        res = self.protocols.execute_protocol("reset_session")
        self.assertEqual(res["status"], "success")
        self.assertIn("Reset Session", res["protocol"])

    def test_workspace_audit_protocol(self) -> None:
        # Create a sample file
        self.files.write_file("test.md", "# Test")
        res = self.protocols.execute_protocol("workspace_audit")
        self.assertEqual(res["status"], "success")
        self.assertIn("Workspace Audit", res["protocol"])

    def test_workspace_audit_idempotency_and_new_files(self) -> None:
        # Create initial file
        self.files.write_file("doc1.md", "# Doc 1")

        # Run audit first time
        res1 = self.protocols.execute_protocol("workspace_audit")
        self.assertEqual(res1["status"], "success")
        self.assertEqual(res1["tasks_created"], 1)
        self.assertEqual(res1["tasks_reused"], 0)

        # Run audit second time (should reuse existing pending task)
        res2 = self.protocols.execute_protocol("workspace_audit")
        self.assertEqual(res2["status"], "success")
        self.assertEqual(res2["tasks_created"], 0)
        self.assertEqual(res2["tasks_reused"], 1)

        # Verify total pending tasks for doc1.md is exactly 1
        pending = self.tasks.list_tasks(status="pending")
        doc1_tasks = [t for t in pending if "doc1.md" in t["title"]]
        self.assertEqual(len(doc1_tasks), 1)

        # Add a new file and run audit again (should create 1 new task, reuse 1 existing)
        self.files.write_file("doc2.md", "# Doc 2")
        res3 = self.protocols.execute_protocol("house_party") # test alias as well
        self.assertEqual(res3["status"], "success")
        self.assertEqual(res3["tasks_created"], 1)
        self.assertEqual(res3["tasks_reused"], 1)

    def test_system_diagnostics_protocol(self) -> None:
        res = self.protocols.execute_protocol("system_diagnostics")
        self.assertEqual(res["status"], "success")
        self.assertIn("vitals", res)

    def test_morning_briefing_protocol_populated(self) -> None:
        self.tasks.create_task(title="Review Hackathon Submission", description="Check criteria", priority="high", status="pending")
        self.memory.save_memory("project_name", "JARVIS Nexus", category="project")
        self.files.write_file("notes.md", "# Notes")
        res = self.protocols.execute_protocol("morning_briefing")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["protocol"], "Morning Briefing")
        self.assertIn("briefing", res)
        self.assertEqual(res["briefing"]["pending_tasks_count"], 1)
        self.assertEqual(res["briefing"]["memory_count"], 1)
        self.assertEqual(res["briefing"]["file_count"], 1)

    def test_morning_briefing_protocol_empty_and_alias(self) -> None:
        res = self.protocols.execute_protocol("briefing") # test alias
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["briefing"]["pending_tasks_count"], 0)
        self.assertEqual(res["briefing"]["memory_count"], 0)
        self.assertEqual(res["briefing"]["file_count"], 0)

    def test_unknown_protocol(self) -> None:
        res = self.protocols.execute_protocol("unknown_protocol")
        self.assertEqual(res["status"], "error")

    def test_telemetry_manager(self) -> None:
        tel = self.telemetry.get_telemetry()
        self.assertIn("cpu_percent", tel)
        self.assertIn("memory_rss_mb", tel)
        self.assertIn("core_temperature_c", tel)
        self.telemetry.record_request(100)
        tel2 = self.telemetry.get_telemetry()
        self.assertEqual(tel2["requests_handled"], tel["requests_handled"] + 1)


if __name__ == "__main__":
    unittest.main()
