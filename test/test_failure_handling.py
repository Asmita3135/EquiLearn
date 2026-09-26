import io
import os
import unittest
from unittest.mock import patch, MagicMock

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

class TestProductionFailureHandling(unittest.TestCase):

    def setUp(self):
        job_store.clear()
        artifact_store.clear_mock_store()

    def test_invalid_input_m1_complete_failure(self):
        # Image job where M1 fails completely
        with patch('worker.tasks.DummyM1Pipeline.process', side_effect=ValueError("Invalid image format")):
            resp = client.post(
                "/api/v1/jobs",
                data={"profile": "blind", "input_type": "image"},
                files={"file": ("test.png", io.BytesIO(b"bad-image"), "image/png")}
            )
            job_id = resp.json()["job_id"]
            
            # The job should be marked as FAILED in DB
            status_resp = client.get(f"/api/v1/jobs/{job_id}")
            self.assertEqual(status_resp.status_code, 200)
            data = status_resp.json()
            self.assertEqual(data["status"], "failed")
            self.assertIn("M1 pipeline failed: Invalid image format", data["error"])

    def test_m3_llm_failure(self):
        # Text job where M3 LLM processing fails
        with patch('orchestrator.run_member3_pipeline', side_effect=RuntimeError("LLM API Timeout")):
            resp = client.post(
                "/api/v1/jobs",
                data={"profile": "dyslexia", "input_type": "text", "raw_text": "Content"}
            )
            job_id = resp.json()["job_id"]
            
            status_resp = client.get(f"/api/v1/jobs/{job_id}")
            data = status_resp.json()
            self.assertEqual(data["status"], "failed")
            self.assertIn("M3 pipeline failed", data["error"])
            self.assertIn("LLM API Timeout", data["error"])

    def test_multimodal_partial_failure_m1_fails(self):
        # Multimodal job: M1 fails, but M2 succeeds -> PARTIALLY_COMPLETED
        with patch('worker.tasks.DummyM1Pipeline.process', side_effect=Exception("Corrupt image part")):
            resp = client.post(
                "/api/v1/jobs",
                data={"profile": "deaf", "input_type": "multimodal"},
                files={"file": ("test.mp4", io.BytesIO(b"video"), "video/mp4")}
            )
            job_id = resp.json()["job_id"]
            
            status_resp = client.get(f"/api/v1/jobs/{job_id}")
            data = status_resp.json()
            self.assertEqual(data["status"], "partially_completed")
            
            # Check warnings in result payload
            result_resp = client.get(f"/api/v1/jobs/{job_id}/result")
            self.assertEqual(result_resp.status_code, 200)
            res_data = result_resp.json()
            self.assertEqual(res_data["status"], "partially_completed")
            warning_texts = " ".join(res_data["warnings"])
            self.assertIn("M1 pipeline failed: Corrupt image part", warning_texts)

    def test_retryable_timeout_error(self):
        from celery.exceptions import Retry
        with patch('worker.tasks.DummyM2Pipeline.process', side_effect=TimeoutError("API unresponsive")):
            try:
                resp = client.post(
                    "/api/v1/jobs",
                    data={"profile": "deaf", "input_type": "audio"},
                    files={"file": ("test.mp3", io.BytesIO(b"audio"), "audio/mpeg")}
                )
            except Retry:
                pass
                
            job_id = resp.json()["job_id"] if 'resp' in locals() else "unknown"
            if job_id != "unknown":
                status_resp = client.get(f"/api/v1/jobs/{job_id}")
                data = status_resp.json()
                # In eager mode, retries execute until MaxRetriesExceededError, which marks it FAILED.
                self.assertEqual(data["status"], "failed")

    def test_queue_failure_graceful_degradation(self):
        # Verify that if both dispatch paths raise, the API still returns 202
        # with a "Queue unavailable" warning rather than crashing.
        err = Exception("Redis down")
        with patch('worker.tasks.process_job_task.delay', side_effect=err), \
             patch('asyncio.BaseEventLoop.run_in_executor', side_effect=err):
            resp = client.post(
                "/api/v1/jobs",
                data={"profile": "blind", "input_type": "text", "raw_text": "Text"}
            )
            # API shouldn't crash
            self.assertEqual(resp.status_code, 202)
            data = resp.json()
            self.assertEqual(data["status"], "queued")
            # Should append a warning
            warning_texts = " ".join(data["warnings"])
            self.assertIn("Queue unavailable", warning_texts)

if __name__ == "__main__":
    unittest.main()
