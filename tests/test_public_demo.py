"""Offline tests for public-demo mode hardening and security controls (JARVIS_PUBLIC_DEMO=true)."""

import unittest
import os
import urllib.request
import json
import urllib.error
from jarvis_nexus.config import Config
from demo_ui import run_server


class TestPublicDemoHardening(unittest.TestCase):
    """Test suite for public-demo security hardening, rate limiting, and access controls."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["JARVIS_PUBLIC_DEMO"] = "true"
        cls.server = run_server(port=0, background=True)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls) -> None:
        if "JARVIS_PUBLIC_DEMO" in os.environ:
            del os.environ["JARVIS_PUBLIC_DEMO"]
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()

    def test_audit_export_blocked_in_public_demo(self) -> None:
        """Test that /api/audit/export is forbidden (403) in public demo mode."""
        try:
            urllib.request.urlopen(f"{self.base_url}/api/audit/export?format=json")
            self.fail("Expected HTTPError 403")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)

    def test_file_create_blocked_in_public_demo(self) -> None:
        """Test that file creation via /api/files/create is blocked in public demo mode."""
        data = json.dumps({"filename": "test_public.txt", "content": "malicious"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/files/create",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            resp = urllib.request.urlopen(req)
            res_data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("error", res_data)
        except urllib.error.HTTPError as e:
            self.assertIn(e.code, [403, 400])

    def test_state_modification_blocked_in_public_demo(self) -> None:
        """Test that mutating tasks or memories is blocked in public demo mode."""
        data = json.dumps({"title": "Hack Task", "priority": "high"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/tasks",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req)
        res_data = json.loads(resp.read().decode("utf-8"))
        self.assertIn("error", res_data)

    def test_payload_size_limit(self) -> None:
        """Test that payloads exceeding 64KB are rejected with HTTP 413."""
        large_data = json.dumps({"message": "x" * (70 * 1024)}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=large_data,
            headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(req)
            self.fail("Expected HTTPError 413")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 413)

    def test_cultural_recommendations_allowed_in_public_demo(self) -> None:
        """Test that Qloo cultural recommendation endpoints remain fully accessible in public demo mode."""
        data = json.dumps({"query": "Beautiful Boy", "seed_type": "movie", "target_type": "artist"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/recommend",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            resp = urllib.request.urlopen(req)
            self.assertEqual(resp.status, 200)
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 200)

    def test_trusted_proxy_client_ip(self) -> None:
        """Test client IP resolution when JARVIS_TRUST_PROXY=true and X-Forwarded-For is supplied."""
        from demo_ui import get_client_ip
        class DummyHandler:
            def __init__(self, headers, client_address):
                self.headers = headers
                self.client_address = client_address

        old_val = os.environ.get("JARVIS_TRUST_PROXY")
        try:
            os.environ["JARVIS_TRUST_PROXY"] = "true"
            handler = DummyHandler({"X-Forwarded-For": "203.0.113.195, 70.41.3.18"}, ("127.0.0.1", 1234))
            ip = get_client_ip(handler)
            self.assertEqual(ip, "203.0.113.195")
        finally:
            if old_val is not None:
                os.environ["JARVIS_TRUST_PROXY"] = old_val
            else:
                os.environ.pop("JARVIS_TRUST_PROXY", None)

    def test_tool_registry_blocking_in_public_demo(self) -> None:
        """Test that ToolRegistry blocks state-modifying tools like create_task and save_memory when public demo is active."""
        from jarvis_nexus.tools import ToolRegistry
        registry = ToolRegistry()
        res = registry.execute("create_task", {"title": "Malicious Tool Task"})
        self.assertIn("error", res)
        self.assertIn("disabled in Public Demo mode", res["error"])

        res_mem = registry.execute("save_memory", {"key": "hack", "value": "payload"})
        self.assertIn("error", res_mem)
        self.assertIn("disabled in Public Demo mode", res_mem["error"])


if __name__ == "__main__":
    unittest.main()
