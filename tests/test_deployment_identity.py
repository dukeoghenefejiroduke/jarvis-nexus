"""Tests for deployment identity reporting (Render commit verification)."""

import json
import os
import tempfile
import unittest
import urllib.request
from unittest import mock

import atexit

_temp_dir = tempfile.TemporaryDirectory()
atexit.register(_temp_dir.cleanup)
os.environ["JARVIS_TASK_DB"] = os.path.join(_temp_dir.name, "tasks.db")
os.environ["JARVIS_MEMORY_DB"] = os.path.join(_temp_dir.name, "memory.db")
os.environ["JARVIS_WORKSPACE"] = os.path.join(_temp_dir.name, "workspace")

import demo_ui
from demo_ui import get_deployment_info, run_server
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager

SHA_A = "a" * 40
SHA_B = "b" * 40


class TestGetDeploymentInfo(unittest.TestCase):
    """Unit tests for the pure resolver."""

    def test_render_uses_render_git_commit(self) -> None:
        info = get_deployment_info({"RENDER": "true", "RENDER_GIT_COMMIT": SHA_A, "APP_VERSION": "1.0.0"})
        self.assertEqual(info["commit_sha"], SHA_A)
        self.assertEqual(info["commit_source"], "RENDER_GIT_COMMIT")
        self.assertEqual(info["deployment_platform"], "render")
        self.assertTrue(info["deployment_identity_available"])
        self.assertEqual(info["version"], "1.0.0")

    def test_render_ignores_manual_app_commit_sha(self) -> None:
        info = get_deployment_info({"RENDER": "true", "RENDER_GIT_COMMIT": SHA_A, "APP_COMMIT_SHA": SHA_B})
        self.assertEqual(info["commit_sha"], SHA_A)

    def test_render_missing_commit_is_unknown_without_fallback(self) -> None:
        info = get_deployment_info({"RENDER": "true", "APP_COMMIT_SHA": SHA_B, "APP_VERSION": "1.0.0"})
        self.assertEqual(info["commit_sha"], "unknown")
        self.assertEqual(info["commit_source"], "unavailable")
        self.assertFalse(info["deployment_identity_available"])
        self.assertEqual(info["deployment_platform"], "render")

    def test_render_blank_or_malformed_commit_is_unknown(self) -> None:
        for bad in ("", "   ", "not-a-sha", "abc", "g" * 40):
            with self.subTest(value=bad):
                info = get_deployment_info({"RENDER": "true", "RENDER_GIT_COMMIT": bad, "APP_COMMIT_SHA": SHA_B})
                self.assertEqual(info["commit_sha"], "unknown")
                self.assertFalse(info["deployment_identity_available"])

    def test_render_detected_from_commit_variable_alone(self) -> None:
        info = get_deployment_info({"RENDER_GIT_COMMIT": SHA_A})
        self.assertEqual(info["deployment_platform"], "render")
        self.assertEqual(info["commit_sha"], SHA_A)

    def test_local_fallback_to_app_commit_sha(self) -> None:
        info = get_deployment_info({"APP_COMMIT_SHA": SHA_B})
        self.assertEqual(info["deployment_platform"], "local")
        self.assertEqual(info["commit_sha"], SHA_B)
        self.assertEqual(info["commit_source"], "APP_COMMIT_SHA")

    def test_local_without_any_sha_is_unknown(self) -> None:
        info = get_deployment_info({})
        self.assertEqual(info["commit_sha"], "unknown")
        self.assertEqual(info["version"], "unknown")
        self.assertFalse(info["deployment_identity_available"])


class TestEndpointsReportSameIdentity(unittest.TestCase):
    """Integration tests against the real HTTP handler."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["JARVIS_TASK_DB"] = os.path.join(_temp_dir.name, "tasks.db")
        os.environ["JARVIS_MEMORY_DB"] = os.path.join(_temp_dir.name, "memory.db")
        os.environ["JARVIS_WORKSPACE"] = os.path.join(_temp_dir.name, "workspace")
        demo_ui.memory_store = MemoryStore(db_path=os.environ["JARVIS_MEMORY_DB"])
        demo_ui.task_store = TaskStore(db_path=os.environ["JARVIS_TASK_DB"])
        demo_ui.file_manager = FileManager(workspace_dir=os.environ["JARVIS_WORKSPACE"])
        cls.server = run_server(port=0, background=True)
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

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

    def _get(self, path: str) -> dict:
        with urllib.request.urlopen(f"{self.base_url}{path}") as resp:
            self.assertEqual(resp.status, 200)
            return json.loads(resp.read().decode("utf-8"))

    def _env(self, **values: str):
        # Start from a clean slate so the host environment cannot influence results.
        clean = {k: v for k, v in os.environ.items() if k not in ("RENDER", "RENDER_GIT_COMMIT", "APP_COMMIT_SHA", "APP_VERSION")}
        clean.update(values)
        return mock.patch.dict(os.environ, clean, clear=True)

    def test_both_endpoints_report_same_render_sha_and_version(self) -> None:
        with self._env(RENDER="true", RENDER_GIT_COMMIT=SHA_A, APP_VERSION="1.0.0", APP_COMMIT_SHA=SHA_B):
            health = self._get("/health")
            status = self._get("/api/status")
        self.assertEqual(health["commit_sha"], SHA_A)
        self.assertEqual(status["commit_sha"], SHA_A)
        self.assertEqual(health["version"], "1.0.0")
        self.assertEqual(status["version"], "1.0.0")
        for key in ("commit_source", "deployment_platform", "deployment_identity_available"):
            self.assertEqual(health[key], status[key])

    def test_missing_render_sha_reported_unknown_on_both_endpoints(self) -> None:
        with self._env(RENDER="true", APP_VERSION="1.0.0", APP_COMMIT_SHA=SHA_B):
            health = self._get("/health")
            status = self._get("/api/status")
        for payload in (health, status):
            self.assertEqual(payload["commit_sha"], "unknown")
            self.assertFalse(payload["deployment_identity_available"])
        # The service itself must still be healthy/online (no crash).
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(status["status"], "online")

    def test_existing_fields_preserved(self) -> None:
        with self._env(APP_VERSION="1.0.0"):
            health = self._get("/health")
            status = self._get("/api/status")
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["service"], "jarvis-nexus-nebius")
        for key in ("status", "provider", "memories", "tasks", "files", "version", "commit_sha"):
            self.assertIn(key, status)
        self.assertEqual(status["status"], "online")


def tearDownModule():
    try:
        _temp_dir.cleanup()
    except Exception:
        pass


if __name__ == "__main__":
    unittest.main()
