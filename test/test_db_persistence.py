"""
Direct DB layer tests – exercises repository and init_db against SQLite.
No FastAPI TestClient here; tests the persistence layer in isolation.
"""
import os
import unittest
from datetime import datetime, timezone

# Point at a test SQLite DB before importing anything that reads DATABASE_URL
os.environ["DATABASE_URL"] = "sqlite:///./equilearn_test.db"

from db.init_db import create_tables, drop_tables
from db.session import SessionLocal
from db.repository import save_job, get_job, update_job_status, delete_all
from api.schemas import JobRecord, JobStatus, InputType, AccessibilityProfile


def _make_record(
    job_id: str = "test-job-1",
    profile: str = "blind",
    input_type: str = "text",
    raw_text: str = "Test content about photosynthesis.",
) -> JobRecord:
    return JobRecord(
        job_id=job_id,
        status=JobStatus.QUEUED,
        input_type=InputType(input_type),
        profile=AccessibilityProfile(profile),
        raw_text=raw_text,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


class TestDBRepository(unittest.TestCase):

    def setUp(self):
        create_tables()
        db = SessionLocal()
        delete_all(db)
        db.close()

    def tearDown(self):
        drop_tables()

    # --- save / get round-trip ---
    def test_save_and_retrieve(self):
        db = SessionLocal()
        rec = _make_record()
        save_job(db, rec)
        fetched = get_job(db, rec.job_id)
        db.close()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.job_id, "test-job-1")
        self.assertEqual(fetched.status, JobStatus.QUEUED)

    def test_profile_persisted(self):
        db = SessionLocal()
        rec = _make_record(profile="dyslexia")
        save_job(db, rec)
        fetched = get_job(db, rec.job_id)
        db.close()
        self.assertEqual(fetched.profile, AccessibilityProfile.DYSLEXIA)

    def test_input_type_persisted(self):
        db = SessionLocal()
        rec = _make_record(input_type="audio")
        save_job(db, rec)
        fetched = get_job(db, rec.job_id)
        db.close()
        self.assertEqual(fetched.input_type, InputType.AUDIO)

    def test_raw_text_persisted(self):
        db = SessionLocal()
        rec = _make_record(raw_text="Photosynthesis produces oxygen.")
        save_job(db, rec)
        fetched = get_job(db, rec.job_id)
        db.close()
        self.assertEqual(fetched.raw_text, "Photosynthesis produces oxygen.")

    def test_warnings_persisted(self):
        db = SessionLocal()
        rec = _make_record()
        rec.warnings = ["Short text warning.", "Low confidence."]
        save_job(db, rec)
        fetched = get_job(db, rec.job_id)
        db.close()
        self.assertEqual(fetched.warnings, ["Short text warning.", "Low confidence."])

    def test_get_nonexistent_returns_none(self):
        db = SessionLocal()
        result = get_job(db, "does-not-exist")
        db.close()
        self.assertIsNone(result)

    # --- status update ---
    def test_update_status_to_processing(self):
        db = SessionLocal()
        rec = _make_record()
        save_job(db, rec)
        updated = update_job_status(db, rec.job_id, JobStatus.PROCESSING)
        db.close()
        self.assertEqual(updated.status, JobStatus.PROCESSING)

    def test_update_status_to_done(self):
        db = SessionLocal()
        rec = _make_record()
        save_job(db, rec)
        updated = update_job_status(db, rec.job_id, JobStatus.DONE,
                                     result={"key": "value"})
        db.close()
        self.assertEqual(updated.status, JobStatus.DONE)
        self.assertEqual(updated.result, {"key": "value"})

    def test_update_status_to_failed_with_error(self):
        db = SessionLocal()
        rec = _make_record()
        save_job(db, rec)
        updated = update_job_status(db, rec.job_id, JobStatus.FAILED,
                                     error="Something went wrong.")
        db.close()
        self.assertEqual(updated.status, JobStatus.FAILED)
        self.assertEqual(updated.error, "Something went wrong.")

    def test_update_nonexistent_job_returns_none(self):
        db = SessionLocal()
        result = update_job_status(db, "ghost-job", JobStatus.DONE)
        db.close()
        self.assertIsNone(result)

    # --- upsert ---
    def test_save_twice_upserts(self):
        db = SessionLocal()
        rec = _make_record()
        save_job(db, rec)
        rec.status = JobStatus.PROCESSING
        save_job(db, rec)           # second save = upsert
        fetched = get_job(db, rec.job_id)
        db.close()
        self.assertEqual(fetched.status, JobStatus.PROCESSING)

    # --- multiple records ---
    def test_multiple_distinct_jobs(self):
        db = SessionLocal()
        for i in range(3):
            save_job(db, _make_record(job_id=f"job-{i}"))
        results = [get_job(db, f"job-{i}") for i in range(3)]
        db.close()
        self.assertTrue(all(r is not None for r in results))
        self.assertEqual(len({r.job_id for r in results}), 3)


if __name__ == "__main__":
    unittest.main()
