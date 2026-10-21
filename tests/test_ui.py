"""Tests for JARVIS Nexus Demo UI and API endpoints (Milestone 11)."""

import tempfile
import os

import atexit

_temp_dir = tempfile.TemporaryDirectory()
atexit.register(_temp_dir.cleanup)
os.environ["JARVIS_TASK_DB"] = os.path.join(_temp_dir.name, "tasks.db")
os.environ["JARVIS_MEMORY_DB"] = os.path.join(_temp_dir.name, "memory.db")
os.environ["JARVIS_WORKSPACE"] = os.path.join(_temp_dir.name, "workspace")

import unittest
import urllib.request
import json
import threading
from jarvis_nexus.config import Config
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager
from jarvis_nexus.context import ContextManager
from jarvis_nexus.tools import ToolRegistry
from jarvis_nexus.agent import Agent
from jarvis_nexus.models import MockModelProvider
from jarvis_nexus.protocols import ProtocolEngine
import demo_ui
from demo_ui import run_server


class TestDemoUI(unittest.TestCase):
    """Test suite for Demo UI HTTP server and API endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["JARVIS_TASK_DB"] = os.path.join(_temp_dir.name, "tasks.db")
        os.environ["JARVIS_MEMORY_DB"] = os.path.join(_temp_dir.name, "memory.db")
        os.environ["JARVIS_WORKSPACE"] = os.path.join(_temp_dir.name, "workspace")
        # Re-bind demo_ui global stores to temporary paths to guarantee isolation
        demo_ui.memory_store = MemoryStore(db_path=os.environ["JARVIS_MEMORY_DB"])
        demo_ui.task_store = TaskStore(db_path=os.environ["JARVIS_TASK_DB"])
        demo_ui.file_manager = FileManager(workspace_dir=os.environ["JARVIS_WORKSPACE"])
        demo_ui.context_manager = ContextManager(
            memory_store=demo_ui.memory_store,
            task_store=demo_ui.task_store,
            file_manager=demo_ui.file_manager,
            skill_registry=demo_ui.skill_registry
        )
        demo_ui.tool_registry = ToolRegistry(
            memory_store=demo_ui.memory_store,
            task_store=demo_ui.task_store,
            context_manager=demo_ui.context_manager
        )
        demo_ui.agent = Agent(
            model_provider=MockModelProvider(),
            memory_store=demo_ui.memory_store,
            tool_registry=demo_ui.tool_registry,
            context_manager=demo_ui.context_manager
        )
        demo_ui.protocol_engine = ProtocolEngine(demo_ui.memory_store, demo_ui.task_store, demo_ui.file_manager)

        # Pre-seed sample workspace files expected by tests in temporary workspace
        os.makedirs(demo_ui.file_manager.workspace_dir, exist_ok=True)
        try:
            with open(os.path.join(demo_ui.file_manager.workspace_dir, "notes.md"), "w") as f:
                f.write("# Test Notes\n- Sample note content.")
            with open(os.path.join(demo_ui.file_manager.workspace_dir, "sales.csv"), "w") as f:
                f.write("item,qty,price\nWidget,10,9.99\nGadget,5,19.99")
            with open(os.path.join(demo_ui.file_manager.workspace_dir, "project.json"), "w") as f:
                f.write(json.dumps({"name": "Test Project", "status": "active"}, indent=2))
        except Exception:
            pass

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
            if hasattr(cls.server, "_server_thread") and cls.server._server_thread:
                cls.server._server_thread.join(timeout=2.0)
        _temp_dir.cleanup()
        os.environ.pop("JARVIS_TASK_DB", None)
        os.environ.pop("JARVIS_MEMORY_DB", None)
        os.environ.pop("JARVIS_WORKSPACE", None)
        demo_ui.memory_store = MemoryStore()
        demo_ui.task_store = TaskStore()
        demo_ui.file_manager = FileManager()
        demo_ui.context_manager = ContextManager(
            memory_store=demo_ui.memory_store,
            task_store=demo_ui.task_store,
            file_manager=demo_ui.file_manager,
            skill_registry=demo_ui.skill_registry
        )
        demo_ui.tool_registry = ToolRegistry(
            memory_store=demo_ui.memory_store,
            task_store=demo_ui.task_store,
            context_manager=demo_ui.context_manager
        )
        demo_ui.agent = Agent(
            model_provider=MockModelProvider(),
            memory_store=demo_ui.memory_store,
            tool_registry=demo_ui.tool_registry,
            context_manager=demo_ui.context_manager
        )
        demo_ui.protocol_engine = ProtocolEngine(demo_ui.memory_store, demo_ui.task_store, demo_ui.file_manager)

    def test_database_isolation(self) -> None:
        """Verify that UI tests use an isolated temporary database and do not write to production."""
        self.assertIn(_temp_dir.name, demo_ui.task_store.db_path)
        self.assertNotIn("data/jarvis_tasks.db", demo_ui.task_store.db_path)

    def test_index_page(self) -> None:
        """Test index page loads successfully."""
        req = urllib.request.urlopen(f"{self.base_url}/")
        self.assertEqual(req.status, 200)
        html = req.read().decode("utf-8")
        self.assertIn("JARVIS Nexus", html)
        self.assertIn("</script>", html)
        self.assertNotIn("</style>\n</body>", html)

    def test_index_page_escapes_dynamic_action_values(self) -> None:
        """Regression test for quoted values in dynamically generated action handlers."""
        req = urllib.request.urlopen(f"{self.base_url}/")
        html = req.read().decode("utf-8")
        self.assertIn("function escapeJsString", html)
        self.assertIn('.replace(/\\\\/g, "\\\\\\\\")', html)
        self.assertIn("deleteMemory('${escapeJsString(m.key)}')", html)
        self.assertIn("viewFile('${escapeJsString(f.name)}')", html)

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

    def test_api_invalid_task_payload_returns_json_error(self) -> None:
        """Invalid task data should not abort the HTTP connection."""
        payload = json.dumps({"title": "Bad Task", "priority": "urgent"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/tasks",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertIn("error", data)

    def test_api_rejects_non_object_json_payload(self) -> None:
        """POST endpoints expect JSON objects so handlers can safely use dict access."""
        payload = json.dumps(["not", "an", "object"]).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(data["error"], "JSON request body must be an object.")

    def test_api_task_actions(self) -> None:
        """Test task creation, completion, and deletion."""
        payload = json.dumps({"title": "Complete Me", "priority": "medium", "status": "pending"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/tasks",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        task_id = data["task_id"]
        self.assertGreater(task_id, 0)

        # Complete task
        comp_payload = json.dumps({"id": task_id}).encode("utf-8")
        req_comp = urllib.request.Request(
            f"{self.base_url}/api/tasks/complete",
            data=comp_payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp_comp = urllib.request.urlopen(req_comp)
        comp_data = json.loads(resp_comp.read().decode("utf-8"))
        self.assertTrue(comp_data["success"])

        # Delete task
        req_del = urllib.request.Request(
            f"{self.base_url}/api/tasks?id={task_id}",
            method="DELETE"
        )
        resp_del = urllib.request.urlopen(req_del)
        del_data = json.loads(resp_del.read().decode("utf-8"))
        self.assertTrue(del_data["success"])

    def test_api_file_inspection(self) -> None:
        """Test file read, CSV inspection, and JSON inspection APIs."""
        payload = json.dumps({"filename": "notes.md"}).encode("utf-8")
        req_read = urllib.request.Request(
            f"{self.base_url}/api/files/read",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp_read = urllib.request.urlopen(req_read)
        read_data = json.loads(resp_read.read().decode("utf-8"))
        self.assertEqual(read_data["status"], "success")

        payload_csv = json.dumps({"filename": "sales.csv"}).encode("utf-8")
        req_csv = urllib.request.Request(
            f"{self.base_url}/api/files/inspect_csv",
            data=payload_csv,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp_csv = urllib.request.urlopen(req_csv)
        csv_data = json.loads(resp_csv.read().decode("utf-8"))
        self.assertEqual(csv_data["status"], "success")

        payload_json = json.dumps({"filename": "project.json"}).encode("utf-8")
        req_json = urllib.request.Request(
            f"{self.base_url}/api/files/inspect_json",
            data=payload_json,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp_json = urllib.request.urlopen(req_json)
        json_data = json.loads(resp_json.read().decode("utf-8"))
        self.assertEqual(json_data["status"], "success")

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

    def test_api_chat_tool_attribution_non_cumulative(self) -> None:
        """Verify via actual HTTP /api/chat requests that tool usage is non-cumulative."""
        # 1. "List my tasks" -> should use 'list_tasks'
        req1 = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps({"message": "List my tasks"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp1 = urllib.request.urlopen(req1)
        data1 = json.loads(resp1.read().decode("utf-8"))
        tools1 = [t["tool"] for t in data1.get("tool_activity", [])]
        self.assertEqual(tools1, ["list_tasks"])

        # 2. "Hello JARVIS, please introduce yourself." -> should use no tools ([])
        req2 = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps({"message": "Hello JARVIS, please introduce yourself."}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp2 = urllib.request.urlopen(req2)
        data2 = json.loads(resp2.read().decode("utf-8"))
        tools2 = [t["tool"] for t in data2.get("tool_activity", [])]
        self.assertEqual(tools2, [])
        self.assertNotIn("list_tasks", tools2)

        # 3. "What is 27 * 14?" -> should use 'calculator' only
        req3 = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps({"message": "What is 27 * 14?"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp3 = urllib.request.urlopen(req3)
        data3 = json.loads(resp3.read().decode("utf-8"))
        tools3 = [t["tool"] for t in data3.get("tool_activity", [])]
        self.assertEqual(tools3, ["calculator"])
        self.assertNotIn("list_tasks", tools3)

    def test_audit_export_json_and_markdown(self) -> None:
        """Test audit export endpoints for JSON and Markdown formats returning HTTP 200."""
        with urllib.request.urlopen(f"{self.base_url}/api/audit/export?format=json") as req_json:
            self.assertEqual(req_json.status, 200)
            self.assertIn("application/json", req_json.headers.get("Content-Type", ""))
            data = json.loads(req_json.read().decode("utf-8"))
            self.assertIn("events", data)

        with urllib.request.urlopen(f"{self.base_url}/api/audit/export?format=markdown") as req_md:
            self.assertEqual(req_md.status, 200)
            self.assertIn("text/markdown", req_md.headers.get("Content-Type", ""))
            md_text = req_md.read().decode("utf-8")
            self.assertIn("# JARVIS Nexus Local Audit Trail", md_text)

    def test_audit_export_invalid_format_400(self) -> None:
        """Test invalid audit export format returns HTTP 400."""
        import urllib.error
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            with urllib.request.urlopen(f"{self.base_url}/api/audit/export?format=xml") as resp:
                pass
        self.assertEqual(ctx.exception.code, 400)
        ctx.exception.close()


def tearDownModule():
    try:
        _temp_dir.cleanup()
    except Exception:
        pass


if __name__ == "__main__":
    unittest.main()
