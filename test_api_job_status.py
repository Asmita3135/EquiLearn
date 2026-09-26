"""
API tests for GET /api/v1/jobs/{job_id}.
Uses TestClient; SQLite DB is used via the default DATABASE_URL.
"""
import io
import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///./equilearn_test.db")
os.environ.setdefault("CELERY_ALWAYS_EAGER", "1")

# Ensure tables exist before the TestClient (and its lifespan) initialises
from db.init_db import create_tables
create_tables()

from fastapi.testclient import TestClient
import api.job_store as job_store
from app import app

client = TestClient(app)


def _create_text_job(text: str = "Educational content about cell biology.",
                     profile: str = "blind") -> str:
    """Helper: POST a text job and return job_id."""
    resp = client.post(
        "/api/v1/jobs",
        data={"profile": profile, "input_type": "text", "raw_text": text},
    )
    assert resp.status_code == 202, resp.text
    return resp.json()["job_id"]


class TestGetJobStatus(unittest.TestCase):

    def setUp(self):
        job_store.clear()

    def test_get_job_status(self):
        job_id = _create_text_job()
        resp = client.get(f"/api/v1/jobs/{job_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["job_id"], job_id)
        # Because CELERY_ALWAYS_EAGER=1, it will be done (or failed) immediately
        self.assertIn(data["status"], ["done", "failed"])

    def test_get_job_has_correct_profile(self):
        job_id = _create_text_job(profile="dyslexia")
        data = client.get(f"/api/v1/jobs/{job_id}").json()
        self.assertEqual(data["profile"], "dyslexia")

    def test_get_job_has_correct_input_type(self):
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "deaf", "input_type": "audio"},
            files={"file": ("clip.mp3", io.BytesIO(b"audio"), "audio/mpeg")},
        )
        job_id = resp.json()["job_id"]
        data = client.get(f"/api/v1/jobs/{job_id}").json()
        self.assertEqual(data["input_type"], "audio")

    def test_get_job_has_created_at(self):
        job_id = _create_text_job()
        data = client.get(f"/api/v1/jobs/{job_id}").json()
        self.assertIn("created_at", data)
        self.assertTrue(len(data["created_at"]) > 0)

    def test_get_job_warnings_preserved(self):
        # Very short text triggers a warning
        job_id = _create_text_job(text="Hi.")
        data = client.get(f"/api/v1/jobs/{job_id}").json()
        self.assertTrue(any("short" in w.lower() for w in data["warnings"]))

    def test_get_nonexistent_job_returns_404(self):
        resp = client.get("/api/v1/jobs/does-not-exist-000")
        self.assertEqual(resp.status_code, 404)

    def test_get_nonexistent_job_error_message(self):
        resp = client.get("/api/v1/jobs/ghost-id")
        self.assertIn("not found", resp.json()["detail"].lower())

    def test_job_is_persisted_across_separate_get_calls(self):
        job_id = _create_text_job()
        r1 = client.get(f"/api/v1/jobs/{job_id}").json()
        r2 = client.get(f"/api/v1/jobs/{job_id}").json()
        self.assertEqual(r1["job_id"], r2["job_id"])
        self.assertEqual(r1["status"],  r2["status"])

    def test_multiple_jobs_stored_independently(self):
        id1 = _create_text_job(profile="blind")
        id2 = _create_text_job(profile="deaf")
        d1 = client.get(f"/api/v1/jobs/{id1}").json()
        d2 = client.get(f"/api/v1/jobs/{id2}").json()
        self.assertNotEqual(d1["job_id"], d2["job_id"])
        self.assertEqual(d1["profile"], "blind")
        self.assertEqual(d2["profile"], "deaf")


if __name__ == "__main__":
    unittest.main()
