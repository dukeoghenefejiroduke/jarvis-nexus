"""Tests for scripts/verify_deployment.py (used by the monitor_live_service CI job)."""

import importlib.util
import json
import http.client
import os
import tempfile
import unittest
import urllib.parse
import urllib.request
from pathlib import Path
from unittest import mock

_temp_dir = tempfile.TemporaryDirectory()
os.environ["JARVIS_TASK_DB"] = os.path.join(_temp_dir.name, "tasks.db")
os.environ["JARVIS_MEMORY_DB"] = os.path.join(_temp_dir.name, "memory.db")
os.environ["JARVIS_WORKSPACE"] = os.path.join(_temp_dir.name, "workspace")

import demo_ui
from demo_ui import run_server
from jarvis_nexus.memory import MemoryStore
from jarvis_nexus.tasks import TaskStore
from jarvis_nexus.file_manager import FileManager

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "verify_deployment.py"
_spec = importlib.util.spec_from_file_location("verify_deployment", _SCRIPT)
vd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vd)

SHA_A = "a" * 40
SHA_B = "b" * 40
BASE = "https://jarvis-nexus-amazon.onrender.com"


def _health(sha=SHA_A, version="1.0.0", status="healthy"):
    return {"status": status, "service": "jarvis-nexus-amazon", "version": version, "commit_sha": sha}


def _runtime(sha=SHA_A, version="1.0.0", status="online"):
    return {"status": status, "provider": "mock", "memories": 0, "tasks": 0, "files": 3,
            "version": version, "commit_sha": sha}


class FakeService:
    """Scripted fetcher: maps path -> list of (status, body) responses (last one repeats)."""

    def __init__(self, routes):
        self.routes = {k: list(v) for k, v in routes.items()}
        self.calls = []

    def __call__(self, url, timeout):
        path = url.replace(BASE, "")
        self.calls.append(path)
        queue = self.routes[path]
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, Exception):
            raise item
        return item


def ok(payload):
    return (200, json.dumps(payload))


class TestVerify(unittest.TestCase):
    def _run(self, fetcher, attempts=3, sha=SHA_A):
        logs = []
        sleeps = []
        code = vd.verify(BASE, sha, "1.0.0", attempts=attempts, delay=0, fetcher=fetcher,
                         sleep=sleeps.append, out=logs.append)
        return code, "\n".join(logs), sleeps

    def test_accepts_matching_sha_and_version(self) -> None:
        svc = FakeService({"/health": [ok(_health())], "/api/status": [ok(_runtime())]})
        code, log, sleeps = self._run(svc)
        self.assertEqual(code, 0)
        self.assertIn("VERIFICATION PASSED", log)
        self.assertEqual(sleeps, [])

    def test_rejects_mismatched_sha_immediately_without_retry(self) -> None:
        svc = FakeService({"/health": [ok(_health(sha=SHA_B))], "/api/status": [ok(_runtime(sha=SHA_B))]})
        code, log, sleeps = self._run(svc, attempts=12)
        self.assertEqual(code, 1)
        self.assertEqual(sleeps, [], "permanent SHA mismatch must not be retried")
        self.assertEqual(svc.calls.count("/health"), 1)
        self.assertIn(f"expected='{SHA_A}' actual='{SHA_B}'", log)
        self.assertIn("not retrying", log)

    def test_rejects_when_only_one_endpoint_mismatches(self) -> None:
        for health_sha, runtime_sha, culprit in ((SHA_B, SHA_A, "health"), (SHA_A, SHA_B, "api_status")):
            with self.subTest(culprit=culprit):
                svc = FakeService({"/health": [ok(_health(sha=health_sha))],
                                   "/api/status": [ok(_runtime(sha=runtime_sha))]})
                code, log, sleeps = self._run(svc)
                self.assertEqual(code, 1)
                self.assertEqual(sleeps, [])
                self.assertIn(f"{culprit}: commit_sha mismatch", log)

    def test_rejects_unknown_or_missing_sha_immediately(self) -> None:
        for bad in ("unknown", "", None):
            with self.subTest(sha=bad):
                health = _health()
                if bad is None:
                    del health["commit_sha"]
                else:
                    health["commit_sha"] = bad
                svc = FakeService({"/health": [ok(health)], "/api/status": [ok(_runtime())]})
                code, log, sleeps = self._run(svc, attempts=12)
                self.assertEqual(code, 1)
                self.assertEqual(sleeps, [])
                self.assertIn("deployment identity unavailable", log)

    def test_rejects_version_mismatch_immediately(self) -> None:
        svc = FakeService({"/health": [ok(_health(version="9.9.9"))], "/api/status": [ok(_runtime())]})
        code, log, sleeps = self._run(svc, attempts=12)
        self.assertEqual(code, 1)
        self.assertEqual(sleeps, [])
        self.assertIn("version mismatch; expected='1.0.0' actual='9.9.9'", log)

    def test_retries_transient_failures_then_succeeds(self) -> None:
        svc = FakeService({
            "/health": [OSError("connection refused"), (503, "starting"), (200, "<html>not json</html>"), ok(_health())],
            "/api/status": [ok(_runtime())],
        })
        code, log, sleeps = self._run(svc, attempts=5)
        self.assertEqual(code, 0)
        self.assertEqual(len(sleeps), 3)
        self.assertIn("Transient failure", log)

    def test_transient_failures_are_bounded(self) -> None:
        svc = FakeService({"/health": [(503, "down")], "/api/status": [ok(_runtime())]})
        code, log, sleeps = self._run(svc, attempts=4)
        self.assertEqual(code, 1)
        self.assertEqual(svc.calls.count("/health"), 4)
        self.assertEqual(len(sleeps), 3)
        self.assertIn("after 4 attempts", log)

    def test_non_200_on_status_endpoint_is_failure(self) -> None:
        svc = FakeService({"/health": [ok(_health())], "/api/status": [(500, "boom")]})
        code, log, _ = self._run(svc, attempts=2)
        self.assertEqual(code, 1)
        self.assertIn("api_status: expected HTTP 200, got HTTP 500", log)

    def test_non_object_json_is_failure(self) -> None:
        svc = FakeService({"/health": [(200, "[]")], "/api/status": [ok(_runtime())]})
        code, log, _ = self._run(svc, attempts=2)
        self.assertEqual(code, 1)
        self.assertIn("expected an object", log)

    def test_wrong_status_field_is_transient_failure(self) -> None:
        svc = FakeService({"/health": [ok(_health(status="degraded"))], "/api/status": [ok(_runtime())]})
        code, log, sleeps = self._run(svc, attempts=2)
        self.assertEqual(code, 1)
        self.assertEqual(len(sleeps), 1)
        self.assertIn("expected status 'healthy'", log)


class TestMain(unittest.TestCase):
    def test_missing_or_empty_ci_commit_sha_is_config_error(self) -> None:
        for env in ({}, {"CI_COMMIT_SHA": ""}, {"CI_COMMIT_SHA": "   "}):
            with self.subTest(env=env):
                logs = []
                fetcher = mock.Mock()
                code = vd.main([], env=env, fetcher=fetcher, out=logs.append)
                self.assertEqual(code, 2)
                fetcher.assert_not_called()
                self.assertIn("CI_COMMIT_SHA", "\n".join(logs))

    def test_main_reads_configuration_from_environment(self) -> None:
        svc = FakeService({"/health": [ok(_health())], "/api/status": [ok(_runtime())]})
        env = {"CI_COMMIT_SHA": SHA_A, "MONITOR_BASE_URL": BASE, "EXPECTED_VERSION": "1.0.0"}
        self.assertEqual(vd.main([], env=env, fetcher=svc, out=lambda _m: None), 0)

    def test_main_rejects_mismatch(self) -> None:
        svc = FakeService({"/health": [ok(_health())], "/api/status": [ok(_runtime())]})
        env = {"CI_COMMIT_SHA": SHA_B, "MONITOR_BASE_URL": BASE}
        self.assertEqual(vd.main(["--attempts", "5"], env=env, fetcher=svc, sleep=lambda _s: None,
                                 out=lambda _m: None), 1)


class TestVerifierAgainstRealServer(unittest.TestCase):
    """End-to-end: the verifier against the real demo_ui handler on localhost."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._temp_dir = tempfile.TemporaryDirectory()
        os.environ["JARVIS_TASK_DB"] = os.path.join(cls._temp_dir.name, "tasks.db")
        os.environ["JARVIS_MEMORY_DB"] = os.path.join(cls._temp_dir.name, "memory.db")
        os.environ["JARVIS_WORKSPACE"] = os.path.join(cls._temp_dir.name, "workspace")
        demo_ui.memory_store = MemoryStore(db_path=os.environ["JARVIS_MEMORY_DB"])
        demo_ui.task_store = TaskStore(db_path=os.environ["JARVIS_TASK_DB"])
        demo_ui.file_manager = FileManager(workspace_dir=os.environ["JARVIS_WORKSPACE"])
        cls.server = run_server(port=0, background=True)
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()
            if hasattr(cls.server, "_server_thread") and cls.server._server_thread:
                cls.server._server_thread.join(timeout=2.0)
        cls._temp_dir.cleanup()
        os.environ.pop("JARVIS_TASK_DB", None)
        os.environ.pop("JARVIS_MEMORY_DB", None)
        os.environ.pop("JARVIS_WORKSPACE", None)
        demo_ui.memory_store = MemoryStore()
        demo_ui.task_store = TaskStore()
        demo_ui.file_manager = FileManager()

    def _verify(self, expected_sha, **env):
        clean = {k: v for k, v in os.environ.items()
                 if k not in ("RENDER", "RENDER_GIT_COMMIT", "APP_COMMIT_SHA", "APP_VERSION")}
        clean.update(env)
        with mock.patch.dict(os.environ, clean, clear=True):
            return vd.verify(BASE, expected_sha, "1.0.0", attempts=2, delay=0,
                             fetcher=self._local_fetch, sleep=lambda _s: None, out=lambda _m: None)

    def _local_fetch(self, url, timeout):
        """Map an allow-listed Render URL onto the local test server (no real network)."""
        vd.validate_endpoint_url(url)
        path = urllib.parse.urlsplit(url).path
        with urllib.request.urlopen(self.url + path, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")

    def test_accepts_matching_render_deployment(self) -> None:
        self.assertEqual(self._verify(SHA_A, RENDER="true", RENDER_GIT_COMMIT=SHA_A, APP_VERSION="1.0.0"), 0)

    def test_rejects_different_render_deployment(self) -> None:
        self.assertEqual(self._verify(SHA_A, RENDER="true", RENDER_GIT_COMMIT=SHA_B, APP_VERSION="1.0.0"), 1)

    def test_rejects_render_without_commit_even_if_manual_sha_matches(self) -> None:
        self.assertEqual(self._verify(SHA_A, RENDER="true", APP_COMMIT_SHA=SHA_A, APP_VERSION="1.0.0"), 1)


HOST = "jarvis-nexus-amazon.onrender.com"


class TestUrlAllowlist(unittest.TestCase):
    """SSRF protection (CWE-918): only https://<render host>[:443] is acceptable."""

    def test_expected_https_render_host_is_accepted(self) -> None:
        for url in (BASE, BASE + "/", f"https://{HOST}:443", f"HTTPS://{HOST.upper()}"):
            with self.subTest(url=url):
                self.assertEqual(vd.validate_base_url(url), BASE)

    def test_endpoint_urls_for_known_paths_are_accepted(self) -> None:
        self.assertEqual(vd.validate_endpoint_url(BASE + "/health"), "/health")
        self.assertEqual(vd.validate_endpoint_url(BASE + "/api/status"), "/api/status")

    def test_unknown_endpoint_paths_are_rejected(self) -> None:
        for path in ("/", "/admin", "/health/..", "/health/extra", "//evil.com/health"):
            with self.subTest(path=path):
                with self.assertRaises(vd.UnsafeURLError):
                    vd.validate_endpoint_url(BASE + path)

    def test_file_urls_are_rejected(self) -> None:
        for url in ("file:///etc/passwd", f"file://{HOST}/health", "FILE:///proc/self/environ"):
            with self.subTest(url=url):
                with self.assertRaises(vd.UnsafeURLError):
                    vd.validate_base_url(url)

    def test_http_and_other_schemes_are_rejected(self) -> None:
        for url in (f"http://{HOST}", f"http://{HOST}:443", f"ftp://{HOST}", f"//{HOST}", HOST):
            with self.subTest(url=url):
                with self.assertRaises(vd.UnsafeURLError):
                    vd.validate_base_url(url)

    def test_unexpected_hosts_are_rejected(self) -> None:
        for url in (
            "https://localhost",
            "https://127.0.0.1",
            "https://127.1",
            "https://[::1]",
            "https://0.0.0.0",
            "https://10.0.0.5",
            "https://172.16.0.1",
            "https://192.168.1.1",
            "https://169.254.169.254",
            "https://example.invalid",
            "https://evil.example.com",
            f"https://{HOST}.evil.com",
            f"https://evil{HOST}",
            f"https://sub.{HOST}",
            f"https://{HOST}.",
            f"https://evil.com/?{HOST}",
            f"https://evil.com/{HOST}",
        ):
            with self.subTest(url=url):
                with self.assertRaises(vd.UnsafeURLError):
                    vd.validate_base_url(url)

    def test_unexpected_ports_are_rejected(self) -> None:
        for port in ("80", "0", "8080", "8443", "10000", "65535", "abc", "99999"):
            with self.subTest(port=port):
                with self.assertRaises(vd.UnsafeURLError):
                    vd.validate_base_url(f"https://{HOST}:{port}")

    def test_urls_with_credentials_are_rejected(self) -> None:
        for url in (
            f"https://user:pass@{HOST}",
            f"https://user@{HOST}",
            f"https://:pass@{HOST}",
            f"https://{HOST}@evil.com",
            f"https://{HOST}:443@evil.com",
            f"https://user:pass@evil.com",
        ):
            with self.subTest(url=url):
                with self.assertRaises(vd.UnsafeURLError):
                    vd.validate_base_url(url)

    def test_paths_queries_fragments_and_odd_characters_are_rejected(self) -> None:
        for url in (
            BASE + "/some/path",
            BASE + "/?next=http://evil.com",
            BASE + "?x=1",
            BASE + "#frag",
            BASE + "\n",
            BASE + " ",
            f"https:\\\\{HOST}",
            "",
        ):
            with self.subTest(url=url):
                with self.assertRaises(vd.UnsafeURLError):
                    vd.validate_base_url(url)

    def test_verify_rejects_unsafe_base_url_before_any_request(self) -> None:
        for url in ("file:///etc/passwd", f"http://{HOST}", "https://localhost",
                    f"https://{HOST}:8443", f"https://u:p@{HOST}"):
            with self.subTest(url=url):
                fetcher = mock.Mock()
                logs = []
                code = vd.verify(url, SHA_A, "1.0.0", attempts=3, delay=0, fetcher=fetcher,
                                 sleep=lambda _s: None, out=logs.append)
                self.assertEqual(code, 2)
                fetcher.assert_not_called()
                self.assertIn("unsafe base URL", "\n".join(logs))

    def test_main_rejects_unsafe_url_from_env_or_flag_before_any_request(self) -> None:
        for env_url, argv in (
            ("file:///etc/passwd", []),
            (f"http://{HOST}", []),
            (BASE, ["--base-url", "https://127.0.0.1"]),
            (BASE, ["--base-url", f"https://{HOST}:8443"]),
        ):
            with self.subTest(env_url=env_url, argv=argv):
                fetcher = mock.Mock()
                env = {"CI_COMMIT_SHA": SHA_A, "MONITOR_BASE_URL": env_url}
                code = vd.main(argv, env=env, fetcher=fetcher, sleep=lambda _s: None,
                               out=lambda _m: None)
                self.assertEqual(code, 2)
                fetcher.assert_not_called()

    def test_default_base_url_is_the_allowlisted_host(self) -> None:
        self.assertEqual(vd.DEFAULT_BASE_URL, BASE)
        self.assertEqual(vd.validate_base_url(vd.DEFAULT_BASE_URL), BASE)


class FakeResponse:
    def __init__(self, status=200, body=b"{}", headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {}

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def read(self, amt=None):
        return self.body if amt is None else self.body[:amt]


class FakeConnection:
    """Stand-in for http.client.HTTPSConnection; records what would hit the network."""

    instances = []
    response = FakeResponse()
    error = None

    def __init__(self, host, port=None, timeout=None, context=None):
        self.host = host
        self.port = port
        self.requests = []
        self.closed = False
        FakeConnection.instances.append(self)

    def request(self, method, path, headers=None):
        self.requests.append((method, path))

    def getresponse(self):
        if FakeConnection.error is not None:
            raise FakeConnection.error
        return FakeConnection.response

    def close(self):
        self.closed = True


class TestFetchTransport(unittest.TestCase):
    """fetch() validates first, pins the connection, and never follows redirects."""

    def setUp(self) -> None:
        FakeConnection.instances = []
        FakeConnection.response = FakeResponse()
        FakeConnection.error = None
        patcher = mock.patch.object(vd.http.client, "HTTPSConnection", FakeConnection)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_fetch_connects_only_to_pinned_host_and_port(self) -> None:
        FakeConnection.response = FakeResponse(200, b'{"status": "healthy"}')
        status, body = vd.fetch(BASE + "/health", timeout=3)
        self.assertEqual((status, body), (200, '{"status": "healthy"}'))
        self.assertEqual(len(FakeConnection.instances), 1)
        conn = FakeConnection.instances[0]
        self.assertEqual((conn.host, conn.port), (HOST, 443))
        self.assertEqual(conn.requests, [("GET", "/health")])
        self.assertTrue(conn.closed)

    def test_fetch_rejects_disallowed_urls_without_opening_a_connection(self) -> None:
        for url in (
            "file:///etc/passwd",
            f"http://{HOST}/health",
            "https://127.0.0.1/health",
            "https://localhost/health",
            "https://evil.example.com/health",
            f"https://{HOST}:8443/health",
            f"https://user:pw@{HOST}/health",
            f"{BASE}/admin",
        ):
            with self.subTest(url=url):
                with self.assertRaises(vd.UnsafeURLError):
                    vd.fetch(url)
        self.assertEqual(FakeConnection.instances, [], "no connection may be made")

    def test_redirects_are_not_followed(self) -> None:
        for code in (301, 302, 303, 307, 308):
            for location in ("http://169.254.169.254/latest/meta-data/", "https://evil.example.com/health",
                             "file:///etc/passwd", f"http://{HOST}/health"):
                with self.subTest(code=code, location=location):
                    FakeConnection.instances = []
                    FakeConnection.response = FakeResponse(code, b"", {"Location": location})
                    with self.assertRaises(vd.RedirectBlockedError):
                        vd.fetch(BASE + "/health")
                    # Exactly one connection, to the pinned host: the redirect target was never contacted.
                    self.assertEqual(len(FakeConnection.instances), 1)
                    conn = FakeConnection.instances[0]
                    self.assertEqual((conn.host, conn.port), (HOST, 443))
                    self.assertEqual(conn.requests, [("GET", "/health")])
                    self.assertTrue(conn.closed)

    def test_verify_fails_immediately_on_redirect_without_retry(self) -> None:
        FakeConnection.response = FakeResponse(302, b"", {"Location": "https://evil.example.com/"})
        logs, sleeps = [], []
        code = vd.verify(BASE, SHA_A, "1.0.0", attempts=12, delay=0, sleep=sleeps.append, out=logs.append)
        self.assertEqual(code, 1)
        self.assertEqual(sleeps, [], "a blocked redirect must not be retried")
        self.assertEqual(len(FakeConnection.instances), 1)
        self.assertIn("blocked by host allowlist", "\n".join(logs))

    def test_verify_never_calls_fetcher_with_an_off_allowlist_url(self) -> None:
        seen = []

        def spy(url, timeout):
            seen.append(url)
            return ok(_health() if url.endswith("/health") else _runtime())

        code = vd.verify(BASE, SHA_A, "1.0.0", attempts=1, delay=0, fetcher=spy,
                         sleep=lambda _s: None, out=lambda _m: None)
        self.assertEqual(code, 0)
        self.assertEqual(seen, [BASE + "/health", BASE + "/api/status"])

    def test_error_status_is_returned_not_raised(self) -> None:
        FakeConnection.response = FakeResponse(503, b"starting")
        self.assertEqual(vd.fetch(BASE + "/api/status"), (503, "starting"))

    def test_protocol_errors_become_retryable_oserror(self) -> None:
        FakeConnection.error = http.client.RemoteDisconnected("closed")
        with self.assertRaises(OSError):
            vd.fetch(BASE + "/health")
        self.assertTrue(FakeConnection.instances[0].closed)

        logs, sleeps = [], []
        code = vd.verify(BASE, SHA_A, "1.0.0", attempts=3, delay=0, sleep=sleeps.append, out=logs.append)
        self.assertEqual(code, 1)
        self.assertEqual(len(sleeps), 2)


def tearDownModule():
    try:
        _temp_dir.cleanup()
    except Exception:
        pass


if __name__ == "__main__":
    unittest.main()
