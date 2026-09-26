import os
import unittest
import io

os.environ.setdefault("DATABASE_URL", "sqlite:///./equilearn_test.db")
os.environ.setdefault("CELERY_ALWAYS_EAGER", "1")
os.environ.setdefault("MOCK_S3", "1")

# Ensure tables exist
from db.init_db import create_tables
create_tables()

from fastapi.testclient import TestClient
from app import app
import api.job_store as job_store

client = TestClient(app)


class TestJobResultEndpoint(unittest.TestCase):

    def setUp(self):
        job_store.clear()

    def _submit_and_get_result(self, input_type: str, profile: str, raw_text: str = None, file: tuple = None):
        """Helper to submit a job and fetch its final result."""
        data = {"profile": profile, "input_type": input_type}
        if raw_text:
            data["raw_text"] = raw_text
        
        files = None
        if file:
            files = {"file": file}
            
        post_resp = client.post("/api/v1/jobs", data=data, files=files)
        self.assertEqual(post_resp.status_code, 202, post_resp.text)
        
        job_id = post_resp.json()["job_id"]
        
        # Because CELERY_ALWAYS_EAGER=1, it should be done already
        result_resp = client.get(f"/api/v1/jobs/{job_id}/result")
        
        # Note: If it failed due to internal error, it would return 400 not completed
        if result_resp.status_code == 400:
            status_resp = client.get(f"/api/v1/jobs/{job_id}").json()
            if status_resp["status"] == "failed":
                self.fail(f"Job failed during processing: {status_resp.get('error')}")
                
        self.assertEqual(result_resp.status_code, 200, result_resp.text)
        return result_resp.json()

    # --- Profile Tests ---
    
    def test_blind_profile(self):
        result = self._submit_and_get_result(
            input_type="text",
            profile="blind",
            raw_text="The quick brown fox jumps over the lazy dog."
        )
        self.assertEqual(result["profile"], "BLIND")
        self.assertIn("recommended_representations", result)
        # Blind profile should get tts_ready_text from M3 representations
        self.assertIn("tts_ready_text", result["recommended_representations"])

    def test_deaf_hoh_profile(self):
        result = self._submit_and_get_result(
            input_type="audio",
            profile="deaf",
            file=("test.mp3", io.BytesIO(b"audio"), "audio/mpeg")
        )
        self.assertEqual(result["profile"], "DEAF")
        # Ensure transcript was preserved from M2Pipeline
        self.assertTrue(bool(result["transcript"]))
        self.assertIn("primary_text", result["recommended_representations"])
        self.assertTrue(bool(result["recommended_representations"]["primary_text"]))
        self.assertEqual(
            result["recommended_representations"]["metadata"]["presentation_mode"],
            "caption_optimized"
        )

    def test_low_vision_profile(self):
        result = self._submit_and_get_result(
            input_type="text",
            profile="low_vision",
            raw_text="Some text that should be magnified."
        )
        self.assertEqual(result["profile"], "LOW_VISION")
        self.assertIn("metadata", result["recommended_representations"])
        self.assertEqual(
            result["recommended_representations"]["metadata"].get("presentation_mode"),
            "high_contrast_magnifiable"
        )

    def test_dyslexia_profile_preserves_structured_output(self):
        result = self._submit_and_get_result(
            input_type="text",
            profile="dyslexia",
            raw_text="A very long and complicated sentence that definitely has a high grade level and needs simplifying by M3."
        )
        self.assertEqual(result["profile"], "DYSLEXIA")
        
        # M3 structured output is inside metadata -> structured_text
        metadata = result["recommended_representations"].get("metadata", {})
        self.assertIn("structured_text", metadata)
        
        struct = metadata["structured_text"]
        for expected_key in ["title", "main_idea", "sections", "key_points", "steps"]:
            self.assertIn(expected_key, struct)
            
    # --- Edge Cases & Partial Modalities ---
    
    def test_job_not_found(self):
        resp = client.get("/api/v1/jobs/missing-job-123/result")
        self.assertEqual(resp.status_code, 404)

    def test_job_not_completed_yet(self):
        from api.schemas import JobRecord, JobStatus, InputType, AccessibilityProfile
        from datetime import datetime, timezone
        job_id = "test-queued-job"
        record = JobRecord(
            job_id=job_id,
            status=JobStatus.QUEUED,
            input_type=InputType.TEXT,
            profile=AccessibilityProfile.BLIND,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        job_store.save(record)
        
        resp = client.get(f"/api/v1/jobs/{job_id}/result")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not completed", resp.json()["detail"].lower())

    def test_multimodal_job_succeeds_gracefully(self):
        # Submit a multimodal job with missing audio file (only visual)
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "blind", "input_type": "multimodal"},
            files={"file": ("test.png", io.BytesIO(b"image"), "image/png")}
        )
        job_id = resp.json()["job_id"]
        
        # Check result
        result_resp = client.get(f"/api/v1/jobs/{job_id}/result")
        self.assertEqual(result_resp.status_code, 200)
        data = result_resp.json()
        
        # Verify it didn't crash and returned a valid package
        self.assertEqual(data["job_id"], job_id)
        self.assertIn(data["status"], ["done", "SUCCESS"])

if __name__ == "__main__":
    unittest.main()
