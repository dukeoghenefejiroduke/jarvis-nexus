"""Tests for JARVIS Nexus Demo UI and API endpoints (Milestone 11)."""

import unittest
import urllib.request
import json
import threading
from jarvis_nexus.config import Config
from demo_ui import run_server


class TestDemoUI(unittest.TestCase):
    """Test suite for Demo UI HTTP server and API endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        # Start server on ephemeral port (0) in background thread
        cls.server = run_server(port=0, background=True)
        # Get assigned port
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()

    def test_index_page(self) -> None:
        """Test index page loads successfully."""
        req = urllib.request.urlopen(f"{self.base_url}/")
        self.assertEqual(req.status, 200)
        html = req.read().decode("utf-8")
        self.assertIn("JARVIS Nexus", html)

    def test_api_status(self) -> None:
        """Test /api/status endpoint."""
        req = urllib.request.urlopen(f"{self.base_url}/api/status")
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertEqual(data["status"], "online")
        self.assertIn("memories", data)
        self.assertIn("tasks", data)

    def test_api_memories(self) -> None:
        """Test memory CRUD via API endpoints."""
        # Save memory
        payload = json.dumps({"key": "ui_test_key", "value": "ui_test_val", "category": "project"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/memories",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(data["success"])

        # List memories
        req_get = urllib.request.urlopen(f"{self.base_url}/api/memories?query=ui_test_key")
        get_data = json.loads(req_get.read().decode("utf-8"))
        self.assertTrue(len(get_data["memories"]) > 0)

        # Delete memory
        req_del = urllib.request.Request(
            f"{self.base_url}/api/memories?key=ui_test_key",
            method="DELETE"
        )
        resp_del = urllib.request.urlopen(req_del)
        del_data = json.loads(resp_del.read().decode("utf-8"))
        self.assertTrue(del_data["success"])

    def test_api_tasks(self) -> None:
        """Test task creation and listing via API endpoints."""
        payload = json.dumps({"title": "UI Test Task", "priority": "high", "status": "pending"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/tasks",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertGreater(data["task_id"], 0)

        # List tasks
        req_get = urllib.request.urlopen(f"{self.base_url}/api/tasks")
        get_data = json.loads(req_get.read().decode("utf-8"))
        self.assertTrue(len(get_data["tasks"]) > 0)

    def test_api_files_skills_context(self) -> None:
        """Test files, skills, and context endpoints."""
        req_files = urllib.request.urlopen(f"{self.base_url}/api/files")
        self.assertEqual(req_files.status, 200)

        req_skills = urllib.request.urlopen(f"{self.base_url}/api/skills")
        self.assertEqual(req_skills.status, 200)
        skills_data = json.loads(req_skills.read().decode("utf-8"))
        self.assertTrue(len(skills_data["skills"]) > 0)

        req_ctx = urllib.request.urlopen(f"{self.base_url}/api/context")
        self.assertEqual(req_ctx.status, 200)

    def test_api_chat(self) -> None:
        """Test chat API endpoint with MockModelProvider."""
        payload = json.dumps({"message": "Hello JARVIS"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)
