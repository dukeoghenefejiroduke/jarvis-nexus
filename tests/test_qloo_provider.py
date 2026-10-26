"""Offline tests for the Qloo API client."""

import json
import unittest
from unittest.mock import patch

from urllib.error import URLError

from jarvis_nexus.qloo_provider import QlooProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class TestQlooProvider(unittest.TestCase):
    def test_missing_key_fails_without_network(self):
        provider = QlooProvider(api_key="")
        with self.assertRaisesRegex(ValueError, "QLOO_API_KEY"):
            provider.search("Afrobeats")

    def test_search_uses_expected_endpoint_and_auth_header(self):
        provider = QlooProvider(
            api_key="test-secret",
            base_url="https://hackathon.api.qloo.com",
        )

        with patch(
            "jarvis_nexus.qloo_provider.urlopen",
            return_value=FakeResponse({"results": []}),
        ) as mocked:
            result = provider.search("Afrobeats")

        self.assertEqual(result, {"results": []})
        request = mocked.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://hackathon.api.qloo.com/v2/search?query=Afrobeats",
        )
        self.assertEqual(request.get_header("X-api-key"), "test-secret")

    def test_insights_uses_v2_endpoint(self):
        provider = QlooProvider(api_key="test-secret")

        with patch(
            "jarvis_nexus.qloo_provider.urlopen",
            return_value=FakeResponse({"success": True}),
        ) as mocked:
            result = provider.insights(**{"filter.type": "urn:entity:artist"})

        self.assertTrue(result["success"])
        self.assertIn("/v2/insights?", mocked.call_args.args[0].full_url)

    def test_empty_search_is_rejected(self):
        provider = QlooProvider(api_key="test-secret")
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            provider.search("  ")

    def test_insights_without_parameters_is_rejected(self):
        provider = QlooProvider(api_key="test-secret")
        with self.assertRaisesRegex(ValueError, "require valid"):
            provider.insights()

    def test_http_error_does_not_leak_api_key(self):
        from urllib.error import HTTPError

        secret = "test-secret"
        provider = QlooProvider(api_key=secret)

        error = HTTPError(
            "https://example.invalid/path",
            401,
            "Unauthorized",
            {},
            None,
        )

        with patch(
            "jarvis_nexus.qloo_provider.urlopen",
            side_effect=error,
        ):
            with self.assertRaises(RuntimeError) as caught:
                provider.search("Afrobeats")

        self.assertNotIn(secret, str(caught.exception))
        self.assertIn("HTTP 401", str(caught.exception))

    def test_network_error_is_sanitized(self):
        provider = QlooProvider(api_key="test-secret")

        with patch(
            "jarvis_nexus.qloo_provider.urlopen",
            side_effect=URLError("network unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "internet connection"):
                provider.search("Afrobeats")

    def test_convenience_methods(self):
        provider = QlooProvider(api_key="test-secret")

        with patch("jarvis_nexus.qloo_provider.urlopen", return_value=FakeResponse({"ok": True})) as mocked:
            provider.trending(category="movie")
            self.assertIn("bias.trends=high", mocked.call_args.args[0].full_url)

        with patch("jarvis_nexus.qloo_provider.urlopen", return_value=FakeResponse({"ok": True})) as mocked:
            provider.audience(seed_entity_id="ent_123", target_type="artist")
            self.assertIn("signal.interests.entities=ent_123", mocked.call_args.args[0].full_url)

        with patch("jarvis_nexus.qloo_provider.urlopen", return_value=FakeResponse({"ok": True})) as mocked:
            provider.geographic(location="Tokyo", seed_entity_id="ent_123", target_type="destination")
            self.assertIn("filter.location.query=Tokyo", mocked.call_args.args[0].full_url)

        with patch("jarvis_nexus.qloo_provider.urlopen", return_value=FakeResponse({"ok": True})) as mocked:
            provider.compare(entity_ids=["ent_1", "ent_2"], target_type="movie")
            self.assertIn("signal.interests.entities=ent_1", mocked.call_args.args[0].full_url)

    def test_rate_limit_error_handling(self):
        from urllib.error import HTTPError
        provider = QlooProvider(api_key="test-secret")
        error = HTTPError("https://example.invalid/path", 429, "Rate Limit", {}, None)
        with patch("jarvis_nexus.qloo_provider.urlopen", side_effect=error):
            with self.assertRaisesRegex(RuntimeError, "rate limit exceeded"):
                provider.search("Afrobeats")


if __name__ == "__main__":
    unittest.main()
