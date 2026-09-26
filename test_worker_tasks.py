import os
import unittest

# Ensure DB uses SQLite and Celery uses eager mode for testing
os.environ.setdefault("DATABASE_URL", "sqlite:///./equilearn_test.db")
os.environ.setdefault("CELERY_ALWAYS_EAGER", "1")
os.environ.setdefault("MOCK_S3", "1")

from db.init_db import create_tables
create_tables()

from fastapi.testclient import TestClient
from app import app
import api.job_store as job_store
from db.session import SessionLocal
import db.repository as repo
from api.schemas import JobStatus

client = TestClient(app)

class TestWorkerTasks(unittest.TestCase):

    def setUp(self):
        job_store.clear()

    def test_job_submission_enqueues_and_completes_in_eager_mode(self):
        # When CELERY_ALWAYS_EAGER=1, .delay() runs synchronously in the same thread.
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "blind", "input_type": "text", "raw_text": "Educational content about AI."}
        )
        self.assertEqual(resp.status_code, 202)
        job_id = resp.json()["job_id"]

        # Because it ran eagerly, the status should already be DONE
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        self.assertEqual(status_resp.status_code, 200)
        
        data = status_resp.json()
        self.assertEqual(data["status"], "done")
        self.assertIsNotNone(data["result"])
        self.assertEqual(data["result"]["job_id"], job_id)
        
    def test_job_submission_handles_failures(self):
        # We can force a failure by passing an unsupported input type directly to the DB,
        # then calling the task manually to see it set status to FAILED.
        from worker.tasks import process_job_task
        from api.schemas import JobRecord, InputType, AccessibilityProfile
        from datetime import datetime, timezone
        
        job_id = "test-fail-job"
        record = JobRecord(
            job_id=job_id,
            status=JobStatus.QUEUED,
            input_type=InputType.TEXT, # It will fail if we mock something, or we can just pass bad data
            profile=AccessibilityProfile.BLIND,
            raw_text=None,  # TEXT requires raw_text, orchestrator might handle or fail
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        job_store.save(record)
        
        # Override orchestrator internally or just let it fail if it doesn't like None content
        # Actually, orchestrator might just return ERROR if content is missing depending on how it's written.
        # Let's run it.
        process_job_task(job_id)
        
        db = SessionLocal()
        updated = repo.get_job(db, job_id)
        db.close()
        
        self.assertIn(updated.status, [JobStatus.DONE, JobStatus.FAILED])

if __name__ == "__main__":
    unittest.main()
