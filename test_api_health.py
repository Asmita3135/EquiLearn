"""
Tests for /api/v1/health and /api/v1/models/health endpoints.
Uses FastAPI TestClient (httpx-backed) – no live server needed.
"""
import sys
import unittest
from pathlib import Path

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestServiceHealth(unittest.TestCase):

    def test_health_status_ok(self):
        resp = client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)

    def test_health_response_fields(self):
        data = client.get("/api/v1/health").json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "EquiLearn Backend")
        self.assertIn("version", data)

    def test_root_redirect(self):
        resp = client.get("/", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")


class TestModelsHealth(unittest.TestCase):

    def setUp(self):
        self.data = client.get("/api/v1/models/health").json()

    def test_status_code(self):
        resp = client.get("/api/v1/models/health")
        self.assertEqual(resp.status_code, 200)

    def test_overall_field_present(self):
        self.assertIn("overall", self.data)
        self.assertIn(self.data["overall"], ["healthy", "degraded", "unavailable"])

    def test_components_is_list(self):
        self.assertIsInstance(self.data["components"], list)
        self.assertGreater(len(self.data["components"]), 0)

    def test_each_component_has_name_and_status(self):
        for comp in self.data["components"]:
            self.assertIn("name", comp)
            self.assertIn("status", comp)

    def test_m3_components_available(self):
        names = {c["name"] for c in self.data["components"]}
        self.assertIn("M3 (NLP/Accessibility)", names)
        self.assertIn("Integration Adapter", names)
        self.assertIn("Orchestrator", names)

    def test_m1_m2_reported(self):
        names = {c["name"] for c in self.data["components"]}
        self.assertIn("M1 (Computer Vision / OCR)", names)
        self.assertIn("M2 (Speech-to-Text)", names)

    def test_m3_core_is_available(self):
        m3 = next(c for c in self.data["components"] if c["name"] == "M3 (NLP/Accessibility)")
        self.assertEqual(m3["status"], "available")

    def test_overall_healthy_when_no_unavailable(self):
        unavailable = [c for c in self.data["components"] if c["status"] == "unavailable"]
        if not unavailable:
            self.assertEqual(self.data["overall"], "healthy")


if __name__ == "__main__":
    unittest.main()
