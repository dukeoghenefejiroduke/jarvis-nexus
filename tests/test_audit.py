"""Tests for JARVIS Nexus Local Audit Log and Export Manager."""

import os
import tempfile
import unittest
from jarvis_nexus.audit import AuditManager


class TestAuditManager(unittest.TestCase):
    """Test suite for AuditManager."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "audit.json")
        self.audit_manager = AuditManager(log_path=self.log_file)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_record_and_retrieve_event(self) -> None:
        """Verify recording and retrieving audit events."""
        ev = self.audit_manager.record_event("protocol", "Morning Briefing", {"status": "success"}, status="success")
        self.assertEqual(ev["event_type"], "protocol")
        self.assertEqual(ev["action"], "Morning Briefing")

        events = self.audit_manager.get_audit_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["action"], "Morning Briefing")

    def test_export_json(self) -> None:
        """Verify JSON export format."""
        self.audit_manager.record_event("task", "Create Task", {"title": "Test Task"})
        json_str = self.audit_manager.export_json()
        self.assertIn("Create Task", json_str)
        self.assertIn("total_events", json_str)

    def test_export_markdown(self) -> None:
        """Verify Markdown export format."""
        self.audit_manager.record_event("memory", "Save Memory", {"key": "test_key"})
        md_str = self.audit_manager.export_markdown()
        self.assertIn("JARVIS Nexus Local Audit Trail", md_str)
        self.assertIn("Save Memory", md_str)
        self.assertIn("test_key", md_str)

    def test_secret_redaction(self) -> None:
        """Verify sensitive tokens or secrets are redacted in audit records."""
        secret_key = "nebius_secret_key_12345"
        os.environ["NEBIUS_API_KEY"] = secret_key
        ev = self.audit_manager.record_event("config", "Check API", {"key": secret_key})
        self.assertNotIn(secret_key, ev["details"]["key"])
        self.assertIn("[REDACTED]", ev["details"]["key"])
        os.environ.pop("NEBIUS_API_KEY", None)


if __name__ == "__main__":
    unittest.main()
