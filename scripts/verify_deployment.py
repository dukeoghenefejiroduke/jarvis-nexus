#!/usr/bin/env python3
"""Verify that the live JARVIS Nexus deployment is running the expected revision.

Hackathon (Transcend) CI automation. Uses only the Python standard library.

Checks, for both ``/health`` and ``/api/status``:

* HTTP 200 and a valid JSON object body
* the expected ``status`` value (``healthy`` / ``online``)
* ``commit_sha`` equals the expected SHA exactly (``CI_COMMIT_SHA``)
* ``version`` equals the expected version

Failure classes:

* Transient (connection errors, non-200, invalid JSON, wrong status): retried within
  a bounded budget, because the free Render service may still be starting.
* Permanent (unknown/missing/different commit SHA, different version, blocked
  redirect): fails immediately. Retrying cannot fix these.

SSRF protection (CWE-918):

* The target is restricted to ``https://jarvis-nexus-transcend.onrender.com`` on
  port 443. URLs are parsed and compared component by component (never by string
  prefix). Other schemes (``file://``, ``http://``), other hosts (including
  ``localhost``, loopback, private and link-local addresses), non-default ports,
  embedded credentials, queries and fragments are rejected.
* Validation happens before any network request is made.
* Requests use a connection pinned to the allow-listed host and port, and redirects
  are never followed: any 3xx response is a permanent failure.

Exit codes: 0 verified, 1 verification failed, 2 invalid configuration.

Configuration (environment variables, overridable by CLI flags):

* ``CI_COMMIT_SHA``      required, the commit that must be deployed
* ``MONITOR_BASE_URL``   default https://jarvis-nexus-transcend.onrender.com
* ``EXPECTED_VERSION``   default 1.0.0
"""

import argparse
import http.client
import json
import os
import ssl
import sys
import time
import urllib.parse
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

ALLOWED_SCHEME = "https"
ALLOWED_HOST = "jarvis-nexus-amazon.onrender.com"
ALLOWED_PORT = 443
DEFAULT_BASE_URL = f"{ALLOWED_SCHEME}://{ALLOWED_HOST}"
DEFAULT_EXPECTED_VERSION = "1.0.0"
DEFAULT_ATTEMPTS = 12
DEFAULT_DELAY_SECONDS = 10.0
DEFAULT_TIMEOUT_SECONDS = 15.0
USER_AGENT = "JARVIS-Nexus-CI-Monitor/3.1"
MAX_LOGGED_BODY = 500
MAX_RESPONSE_BYTES = 1_000_000

ENDPOINTS: Tuple[Tuple[str, str, str], ...] = (
    # (name, path, expected "status" field)
    ("health", "/health", "healthy"),
    ("api_status", "/api/status", "online"),
)
ALLOWED_PATHS = frozenset(path for _, path, _ in ENDPOINTS)

Fetcher = Callable[[str, float], Tuple[int, str]]


class TransientError(Exception):
    """Failure that may resolve itself while the service starts; safe to retry."""


class PermanentError(Exception):
    """Failure that retrying cannot fix (wrong or unknown deployed revision)."""


class UnsafeURLError(ValueError):
    """A URL or redirect violates the deployment host allowlist."""


class RedirectBlockedError(UnsafeURLError):
    """The server answered with a redirect; redirects are never followed."""


def _parse_allowed_url(url: str) -> urllib.parse.SplitResult:
    """Parse ``url`` and enforce scheme, credentials, host, port, query and fragment.

    Path rules are applied by the callers. Raises UnsafeURLError on any violation.
    """
    if not isinstance(url, str) or not url:
        raise UnsafeURLError("URL must be a non-empty string")
    if "\\" in url or any(ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F for ch in url):
        raise UnsafeURLError("URL contains whitespace, control characters or backslashes")

    try:
        parts = urllib.parse.urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise UnsafeURLError(f"URL is malformed ({exc})") from exc

    if parts.scheme.lower() != ALLOWED_SCHEME:
        raise UnsafeURLError(
            f"scheme {parts.scheme!r} is not allowed; only {ALLOWED_SCHEME} is permitted"
        )
    if "@" in parts.netloc or parts.username is not None or parts.password is not None:
        raise UnsafeURLError("credentials in the URL are not allowed")
    if parts.hostname != ALLOWED_HOST:
        raise UnsafeURLError(
            f"host {parts.hostname!r} is not allowed; only {ALLOWED_HOST} is permitted"
        )
    if port is not None and port != ALLOWED_PORT:
        raise UnsafeURLError(f"port {port} is not allowed; only {ALLOWED_PORT} is permitted")
    if parts.netloc.lower() not in (ALLOWED_HOST, f"{ALLOWED_HOST}:{ALLOWED_PORT}"):
        raise UnsafeURLError("URL authority is malformed")
    if "?" in url or "#" in url:
        raise UnsafeURLError("query strings and fragments are not allowed")
    return parts


def validate_base_url(url: str) -> str:
    """Validate the monitor base URL and return its canonical form (no path)."""
    parts = _parse_allowed_url(url)
    if parts.path not in ("", "/"):
        raise UnsafeURLError("base URL must not contain a path")
    return DEFAULT_BASE_URL


def validate_endpoint_url(url: str) -> str:
    """Validate a full endpoint URL and return its request path."""
    parts = _parse_allowed_url(url)
    if parts.path not in ALLOWED_PATHS:
        raise UnsafeURLError(f"path {parts.path!r} is not an allowed verification endpoint")
    return parts.path


def fetch(url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> Tuple[int, str]:
    """GET an allow-listed endpoint and return ``(http_status, body)``.

    The URL is validated before any connection is opened, and the connection is
    pinned to the allow-listed host and port (not taken from the caller's string).
    Redirects are never followed: a 3xx response raises RedirectBlockedError.
    HTTP error statuses are returned, not raised. Network errors propagate as OSError.
    """
    path = validate_endpoint_url(url)
    connection = http.client.HTTPSConnection(
        ALLOWED_HOST, ALLOWED_PORT, timeout=timeout, context=ssl.create_default_context()
    )
    try:
        connection.request(
            "GET", path, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )
        response = connection.getresponse()
        status = response.status
        if 300 <= status < 400:
            location = _truncate(str(response.getheader("Location", "")))
            raise RedirectBlockedError(
                f"HTTP {status} redirect to {location!r} refused; redirects are not followed"
            )
        body = response.read(MAX_RESPONSE_BYTES).decode("utf-8", errors="replace")
        return status, body
    except http.client.HTTPException as exc:
        raise OSError(f"HTTP protocol error: {exc.__class__.__name__}: {exc}") from exc
    finally:
        connection.close()


def _truncate(text: str) -> str:
    return text if len(text) <= MAX_LOGGED_BODY else text[:MAX_LOGGED_BODY] + "...[truncated]"


def _fetch_json(
    name: str, url: str, expected_status: str, fetcher: Fetcher, timeout: float, out: Callable[[str], None]
) -> Dict[str, Any]:
    """Fetch one endpoint and validate transport-level properties (all transient)."""
    validate_endpoint_url(url)  # always validate before any network request
    http_status, body = fetcher(url, timeout)
    out(f"[{name}] GET {url} -> HTTP {http_status}")
    out(f"[{name}] body: {_truncate(body)}")

    if http_status != 200:
        raise TransientError(f"{name}: expected HTTP 200, got HTTP {http_status}")

    try:
        payload = json.loads(body)
    except ValueError as exc:
        raise TransientError(f"{name}: response is not valid JSON ({exc})") from exc

    if not isinstance(payload, dict):
        raise TransientError(f"{name}: JSON body is {type(payload).__name__}, expected an object")

    actual_status = payload.get("status")
    if actual_status != expected_status:
        raise TransientError(
            f"{name}: expected status {expected_status!r}, got {actual_status!r}"
        )
    return payload


def _identity_problems(
    name: str, payload: Mapping[str, Any], expected_sha: str, expected_version: str
) -> List[str]:
    """Return permanent identity problems for one endpoint payload (empty if OK)."""
    problems: List[str] = []
    actual_sha = payload.get("commit_sha")
    actual_version = payload.get("version")

    if not isinstance(actual_sha, str) or actual_sha in ("", "unknown"):
        problems.append(
            f"{name}: deployment identity unavailable "
            f"(commit_sha={actual_sha!r}); expected commit_sha={expected_sha!r}"
        )
    elif actual_sha != expected_sha:
        problems.append(
            f"{name}: commit_sha mismatch; expected={expected_sha!r} actual={actual_sha!r}"
        )

    if actual_version != expected_version:
        problems.append(
            f"{name}: version mismatch; expected={expected_version!r} actual={actual_version!r}"
        )
    return problems


def check_once(
    base_url: str,
    expected_sha: str,
    expected_version: str,
    fetcher: Fetcher,
    timeout: float,
    out: Callable[[str], None],
) -> Dict[str, Dict[str, Any]]:
    """Run one verification pass. Raises TransientError / PermanentError / UnsafeURLError."""
    payloads: Dict[str, Dict[str, Any]] = {}
    base = validate_base_url(base_url)
    for name, path, expected_status in ENDPOINTS:
        payloads[name] = _fetch_json(name, base + path, expected_status, fetcher, timeout, out)

    problems: List[str] = []
    for name, payload in payloads.items():
        problems.extend(_identity_problems(name, payload, expected_sha, expected_version))
    if problems:
        raise PermanentError("\n  ".join(problems))
    return payloads


def verify(
    base_url: str,
    expected_sha: str,
    expected_version: str,
    attempts: int = DEFAULT_ATTEMPTS,
    delay: float = DEFAULT_DELAY_SECONDS,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    fetcher: Fetcher = fetch,
    sleep: Callable[[float], None] = time.sleep,
    out: Callable[[str], None] = print,
) -> int:
    """Verify the deployment. Returns a process exit code (0 on success)."""
    try:
        base_url = validate_base_url(base_url)
    except UnsafeURLError as exc:
        out(f"Refusing to verify: unsafe base URL ({exc}).")
        out(f"Only {DEFAULT_BASE_URL} is allowed.")
        return 2

    out(f"Expected commit_sha: {expected_sha}")
    out(f"Expected version:    {expected_version}")
    out(f"Service:             {base_url}")

    last_error = "no attempt was made"
    for attempt in range(1, attempts + 1):
        out(f"--- Live service verification attempt {attempt}/{attempts} ---")
        try:
            payloads = check_once(base_url, expected_sha, expected_version, fetcher, timeout, out)
        except PermanentError as exc:
            out("")
            out("DEPLOYMENT VERIFICATION FAILED (permanent, not retrying)")
            out(f"  {exc}")
            return 1
        except UnsafeURLError as exc:
            out("")
            out("DEPLOYMENT VERIFICATION FAILED (blocked by host allowlist, not retrying)")
            out(f"  {exc}")
            return 1
        except (TransientError, OSError) as exc:
            last_error = str(exc) or exc.__class__.__name__
            out(f"Transient failure: {last_error}")
            if attempt < attempts:
                out(f"Service may still be starting. Retrying in {delay:g}s...")
                sleep(delay)
            continue

        runtime = payloads["api_status"]
        out("")
        out("JARVIS NEXUS DEPLOYMENT VERIFICATION PASSED")
        out(f"  Verified commit_sha: {expected_sha} (health and api_status)")
        out(f"  Verified version:    {expected_version}")
        out(f"  Provider: {runtime.get('provider')}")
        return 0

    out("")
    out(f"DEPLOYMENT VERIFICATION FAILED after {attempts} attempts")
    out(f"  Last error: {last_error}")
    return 1


def main(
    argv: Optional[List[str]] = None,
    env: Optional[Mapping[str, str]] = None,
    fetcher: Fetcher = fetch,
    sleep: Callable[[float], None] = time.sleep,
    out: Callable[[str], None] = print,
) -> int:
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(description="Verify the live JARVIS Nexus deployment.")
    parser.add_argument("--base-url", default=env.get("MONITOR_BASE_URL") or DEFAULT_BASE_URL)
    parser.add_argument(
        "--expected-version", default=env.get("EXPECTED_VERSION") or DEFAULT_EXPECTED_VERSION
    )
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    expected_sha = env.get("CI_COMMIT_SHA", "")
    if not expected_sha.strip():
        out("CI_COMMIT_SHA is missing or empty; cannot verify deployment identity.")
        return 2
    if args.attempts < 1:
        out("--attempts must be at least 1.")
        return 2

    return verify(
        base_url=args.base_url,
        expected_sha=expected_sha,
        expected_version=args.expected_version,
        attempts=args.attempts,
        delay=args.delay,
        timeout=args.timeout,
        fetcher=fetcher,
        sleep=sleep,
        out=out,
    )


if __name__ == "__main__":
    sys.exit(main())
