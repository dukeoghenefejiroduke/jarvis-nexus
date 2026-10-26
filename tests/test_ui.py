"""Tests for JARVIS Nexus Demo UI and API endpoints (Milestone 11)."""

import unittest
from unittest.mock import patch
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
        import time
        payload = json.dumps({"title": f"UI Test Task {time.time()}", "priority": "high", "status": "pending"}).encode("utf-8")
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

    @patch("jarvis_nexus.cultural_studio.QlooProvider")
    def test_api_cultural_recommend_success(self, mock_qloo_cls) -> None:
        """Test successful cultural recommendations via API route."""
        mock_instance = mock_qloo_cls.return_value
        mock_instance.search.return_value = {
            "results": {
                "entities": [{"name": "Burna Boy", "entity_id": "artist_123"}]
            }
        }
        mock_instance.insights.return_value = {
            "results": {
                "entities": [{"name": "Wizkid", "entity_id": "artist_456"}]
            }
        }

        payload = json.dumps({
            "query": "Burna Boy",
            "seed_type": "artist",
            "target_type": "artist"
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/recommend",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(data["seed"]["name"], "Burna Boy")
        self.assertEqual(data["seed"]["entity_id"], "artist_123")
        self.assertEqual(len(data["recommendations"]), 1)
        self.assertEqual(data["recommendations"][0]["name"], "Wizkid")

    def test_api_cultural_recommend_missing_query(self) -> None:
        """Test validation error when query is empty."""
        payload = json.dumps({"query": "", "seed_type": "artist", "target_type": "artist"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/recommend",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertIn("error", data)
        self.assertIn("Enter an interest", data["error"])

    def test_api_cultural_recommend_invalid_category(self) -> None:
        """Test validation error when category is unsupported."""
        payload = json.dumps({"query": "Test", "seed_type": "invalid_cat", "target_type": "artist"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/recommend",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertIn("error", data)
        self.assertIn("Unsupported entity category", data["error"])

    @patch("jarvis_nexus.cultural_studio.QlooProvider")
    def test_api_cultural_recommend_no_matching_entity(self, mock_qloo_cls) -> None:
        """Test error handling when Qloo finds no matching entity."""
        mock_instance = mock_qloo_cls.return_value
        mock_instance.search.return_value = {"results": {"entities": []}}

        payload = json.dumps({"query": "UnknownXYZ", "seed_type": "artist", "target_type": "artist"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/recommend",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertIn("error", data)
        self.assertIn("no matching entity", data["error"])

    @patch("jarvis_nexus.cultural_studio.QlooProvider")
    def test_api_cultural_recommend_api_failure(self, mock_qloo_cls) -> None:
        """Test error handling when Qloo API raises an exception."""
        mock_instance = mock_qloo_cls.return_value
        mock_instance.search.side_effect = RuntimeError("Qloo API unavailable")

        payload = json.dumps({"query": "Burna Boy", "seed_type": "artist", "target_type": "artist"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/recommend",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertIn("error", data)
        self.assertIn("Qloo API unavailable", data["error"])

    @patch("jarvis_nexus.cultural_studio.QlooProvider")
    def test_api_cultural_multi_interest_and_explainability(self, mock_qloo_cls) -> None:
        """Test multi-interest recommendation and explainability feature."""
        mock_instance = mock_qloo_cls.return_value
        mock_instance.search.return_value = {
            "results": {"entities": [{"name": "Seed Entity", "entity_id": "s_1"}]}
        }
        mock_instance.insights.return_value = {
            "results": {
                "entities": [{"name": "Result Entity", "entity_id": "r_1", "explainability": "Matched shared genres"}]
            }
        }

        payload = json.dumps({
            "queries": ["Burna Boy", "Wizkid"],
            "seed_type": "artist",
            "target_type": "movie",
            "explainability": True
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/recommend",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(data["seeds"]), 2)
        self.assertEqual(len(data["recommendations"]), 1)
        self.assertEqual(data["recommendations"][0]["explainability"], "Matched shared genres")

    @patch("jarvis_nexus.cultural_studio.QlooProvider")
    def test_api_cultural_trending(self, mock_qloo_cls) -> None:
        """Test trending API route."""
        mock_instance = mock_qloo_cls.return_value
        mock_instance.trending.return_value = {
            "results": {"entities": [{"name": "Trending Movie", "entity_id": "t_1"}]}
        }
        payload = json.dumps({"category": "movie"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/trending",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(data["recommendations"]), 1)
        self.assertEqual(data["recommendations"][0]["name"], "Trending Movie")

    @patch("jarvis_nexus.cultural_studio.QlooProvider")
    def test_api_cultural_geographic(self, mock_qloo_cls) -> None:
        """Test geographic insights API route."""
        mock_instance = mock_qloo_cls.return_value
        mock_instance.geographic.return_value = {
            "results": {"entities": [{"name": "Tokyo Spot", "entity_id": "g_1"}]}
        }
        payload = json.dumps({"location": "Tokyo", "seed_entity_id": "s_1", "target_type": "destination"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/geographic",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(data["recommendations"]), 1)
        self.assertEqual(data["recommendations"][0]["name"], "Tokyo Spot")

    @patch("jarvis_nexus.cultural_studio.QlooProvider")
    def test_api_cultural_compare(self, mock_qloo_cls) -> None:
        """Test entity comparison API route."""
        mock_instance = mock_qloo_cls.return_value
        mock_instance.compare.return_value = {
            "results": {"entities": [{"name": "Cross Over", "entity_id": "c_1"}]}
        }
        payload = json.dumps({"entity_ids": ["e_1", "e_2"], "target_type": "movie"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/cultural/compare",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(data["recommendations"]), 1)
        self.assertEqual(data["recommendations"][0]["name"], "Cross Over")

    def test_api_cultural_favorites_crud(self) -> None:
        """Test saving, listing, and deleting cultural favorites."""
        entity = {"entity_id": "fav_test_99", "name": "Favorite Film", "type": "urn:entity:movie"}
        payload = json.dumps({"entity": entity}).encode("utf-8")
        req_save = urllib.request.Request(
            f"{self.base_url}/api/cultural/favorites",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp_save = urllib.request.urlopen(req_save)
        data_save = json.loads(resp_save.read().decode("utf-8"))
        self.assertTrue(data_save["success"])

        # List favorites
        req_list = urllib.request.urlopen(f"{self.base_url}/api/cultural/favorites")
        data_list = json.loads(req_list.read().decode("utf-8"))
        self.assertTrue(any(f["entity_id"] == "fav_test_99" for f in data_list["favorites"]))

        # Delete favorite
        req_del = urllib.request.Request(
            f"{self.base_url}/api/cultural/favorites?entity_id=fav_test_99",
            method="DELETE"
        )
        resp_del = urllib.request.urlopen(req_del)
        data_del = json.loads(resp_del.read().decode("utf-8"))
        self.assertTrue(data_del["success"])

    def test_entity_type_normalization_and_serialization(self) -> None:
        from jarvis_nexus.cultural_studio import serialize_entity
        raw_item = {
            "entity_id": "ent_999",
            "name": "Breaking Bad",
            "type": "urn:entity:tv_show",
            "properties": {
                "image": {"url": "http://en.wikipedia.org/wiki/test.jpg"},
                "release_year": "2008"
            },
            "tags": [{"name": "Drama", "type": "genre"}],
            "explainability": "Shared audience affinity"
        }
        serialized = serialize_entity(raw_item)
        self.assertEqual(serialized["type"], "TV Show")
        self.assertEqual(serialized["type_urn"], "urn:entity:tv_show")
        self.assertEqual(serialized["properties"]["image"], "https://en.wikipedia.org/wiki/test.jpg")
        self.assertEqual(serialized["explainability"], "Shared audience affinity")
        self.assertEqual(len(serialized["tags"]), 1)
        self.assertEqual(serialized["tags"][0]["name"], "Drama")

    def test_api_status_includes_qloo_mode(self) -> None:
        """Test that /api/status endpoint includes Qloo configuration status."""
        resp = urllib.request.urlopen(f"{self.base_url}/api/status")
        data = json.loads(resp.read().decode("utf-8"))
        self.assertIn("qloo_configured", data)
        self.assertIn("qloo_mode", data)
