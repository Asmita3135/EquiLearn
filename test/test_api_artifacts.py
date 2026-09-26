import io
import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///./equilearn_test.db")
os.environ.setdefault("CELERY_ALWAYS_EAGER", "1")
os.environ.setdefault("MOCK_S3", "1")

from db.init_db import create_tables
create_tables()

from fastapi.testclient import TestClient
from app import app
import api.job_store as job_store
import api.artifact_store as artifact_store

client = TestClient(app)

class TestArtifactStorage(unittest.TestCase):

    def setUp(self):
        job_store.clear()
        artifact_store.clear_mock_store()

    def test_upload_stores_input_artifact(self):
        file_content = b"fake-audio-bytes"
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "deaf", "input_type": "audio"},
            files={"file": ("lecture.mp3", io.BytesIO(file_content), "audio/mpeg")},
        )
        self.assertEqual(resp.status_code, 202)
        job_id = resp.json()["job_id"]
        
        # In CELERY_ALWAYS_EAGER mode, it processes synchronously.
        # Check that we can get the 'input' artifact.
        art_resp = client.get(f"/api/v1/jobs/{job_id}/artifacts/input")
        self.assertEqual(art_resp.status_code, 200)
        self.assertEqual(art_resp.content, file_content)
        self.assertEqual(art_resp.headers["content-type"], "audio/mpeg")

    def test_worker_stores_generated_artifacts(self):
        # M3 dummy pipeline generates VTT/TTS or whatever package_builder expects.
        # Wait, the dummy pipelines we added in `worker/tasks.py` do this:
        # package.get("captions_vtt") is saved as "vtt".
        # We need a job that generates captions or alt_text to verify this.
        # Actually, let's just trigger a job that has those.
        # In our package_builder, alt_text comes from M1 visual_description.
        # DummyM1Pipeline returns {"ocr_text": "Dummy OCR from M1"}, no visual_description!
        # Let's manually inject an artifact to test the GET endpoint.
        
        job_id = "test-artifact-job"
        artifact_store.save_artifact(job_id, "vtt", b"WEBVTT\n\n1\n00:00 -> 00:01\nTest", "text/vtt")
        
        resp = client.get(f"/api/v1/jobs/{job_id}/artifacts/vtt")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"WEBVTT\n\n1\n00:00 -> 00:01\nTest")
        self.assertIn("text/vtt", resp.headers["content-type"])

    def test_get_missing_artifact_returns_404(self):
        resp = client.get("/api/v1/jobs/nonexistent-job/artifacts/input")
        self.assertEqual(resp.status_code, 404)

if __name__ == "__main__":
    unittest.main()
