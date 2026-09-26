"""
Tests for POST /api/v1/jobs.

Covers:
  - valid text input
  - valid file upload (image, audio)
  - invalid / unknown profile
  - unsupported input type
  - missing input (no text, no file)
  - empty file upload
  - very short text warning
  - 202 status on success
  - job_id uniqueness
  - internal store record matches response
"""
import io
import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///./equilearn_test.db")
os.environ.setdefault("CELERY_ALWAYS_EAGER", "1")
os.environ.setdefault("MOCK_S3", "1")

# Ensure tables exist before anything touches the DB
from db.init_db import create_tables
create_tables()

import api.job_store as job_store
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def _post_text(text: str, profile: str = "blind", input_type: str = "text"):
    return client.post(
        "/api/v1/jobs",
        data={"profile": profile, "input_type": input_type, "raw_text": text},
    )


def _post_file(filename: str, content: bytes, content_type: str,
               profile: str = "deaf", input_type: str = "audio"):
    return client.post(
        "/api/v1/jobs",
        data={"profile": profile, "input_type": input_type},
        files={"file": (filename, io.BytesIO(content), content_type)},
    )


class TestJobCreationValid(unittest.TestCase):

    def setUp(self):
        job_store.clear()

    # --- text ---
    def test_valid_text_returns_202(self):
        resp = _post_text("Photosynthesis is a biological process in plants.")
        self.assertEqual(resp.status_code, 202)

    def test_valid_text_response_fields(self):
        resp = _post_text("Photosynthesis is a biological process in plants.")
        data = resp.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "queued")
        self.assertEqual(data["input_type"], "text")
        self.assertEqual(data["profile"], "blind")
        self.assertIn("message", data)

    def test_valid_text_stored_in_job_store(self):
        resp = _post_text("Cell biology is important.", profile="dyslexia")
        job_id = resp.json()["job_id"]
        record = job_store.get(job_id)
        self.assertIsNotNone(record)
        # With CELERY_ALWAYS_EAGER=1, status changes to "done" immediately.
        # But we check for either to be safe if tests run without eager mode.
        self.assertIn(record.status, ["queued", "done", "failed"])
        self.assertEqual(record.raw_text, "Cell biology is important.")

    # --- files ---
    def test_valid_image_upload(self):
        resp = _post_file("diagram.png", b"fake-png-bytes", "image/png",
                          profile="low_vision", input_type="image")
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.json()["input_type"], "image")

    def test_valid_audio_upload(self):
        resp = _post_file("lecture.mp3", b"fake-audio-bytes", "audio/mpeg",
                          profile="deaf", input_type="audio")
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.json()["input_type"], "audio")

    def test_valid_pdf_upload(self):
        resp = _post_file("notes.pdf", b"fake-pdf-bytes", "application/pdf",
                          profile="dyslexia", input_type="pdf")
        self.assertEqual(resp.status_code, 202)

    def test_all_profiles_accepted(self):
        for profile in ["blind", "deaf", "low_vision", "dyslexia"]:
            resp = _post_text("Some educational content here.", profile=profile)
            self.assertEqual(resp.status_code, 202, f"Failed for profile: {profile}")

    def test_job_ids_are_unique(self):
        ids = set()
        for _ in range(5):
            r = _post_text("Biology is the study of living organisms.")
            ids.add(r.json()["job_id"])
        self.assertEqual(len(ids), 5)

    def test_file_size_stored(self):
        payload = b"audio-content" * 100
        resp = _post_file("clip.wav", payload, "audio/wav",
                          profile="deaf", input_type="audio")
        job_id = resp.json()["job_id"]
        record = job_store.get(job_id)
        self.assertEqual(record.file_size_bytes, len(payload))
        self.assertEqual(record.file_name, "clip.wav")


class TestJobCreationInvalid(unittest.TestCase):

    def setUp(self):
        job_store.clear()

    def test_invalid_profile_rejected(self):
        resp = _post_text("Some text.", profile="superhero")
        self.assertEqual(resp.status_code, 422)

    def test_unsupported_input_type_rejected(self):
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "blind", "input_type": "hologram", "raw_text": "text"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_missing_raw_text_for_text_type(self):
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "blind", "input_type": "text"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_empty_raw_text_for_text_type(self):
        resp = _post_text("   ", profile="blind")
        self.assertEqual(resp.status_code, 422)

    def test_missing_file_for_image_type(self):
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "low_vision", "input_type": "image"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_missing_file_for_audio_type(self):
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "deaf", "input_type": "audio"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_empty_file_produces_warning(self):
        resp = _post_file("empty.mp3", b"", "audio/mpeg",
                          profile="deaf", input_type="audio")
        self.assertEqual(resp.status_code, 202)
        self.assertIn("empty", resp.json()["warnings"][0].lower())

    def test_short_text_produces_warning(self):
        resp = _post_text("Hi.", profile="dyslexia")
        self.assertEqual(resp.status_code, 202)
        warnings = resp.json()["warnings"]
        self.assertTrue(any("short" in w.lower() for w in warnings))

    def test_missing_profile_field_rejected(self):
        resp = client.post(
            "/api/v1/jobs",
            data={"input_type": "text", "raw_text": "Some educational content."},
        )
        self.assertEqual(resp.status_code, 422)

    def test_missing_input_type_field_rejected(self):
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "blind", "raw_text": "Some content."},
        )
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
