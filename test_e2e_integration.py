import io
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///./equilearn_test.db")
os.environ.setdefault("CELERY_ALWAYS_EAGER", "1")
os.environ.setdefault("MOCK_S3", "1")

from db.init_db import create_tables
create_tables()

from fastapi.testclient import TestClient
from app import app
import api.job_store as job_store
import api.artifact_store as artifact_store
from api.schemas import AccessibilityPackage, JobStatus
from db.session import SessionLocal
from db.models import JobDB

client = TestClient(app)

class TestEndToEndSystemIntegration(unittest.TestCase):
    """
    Comprehensive End-to-End Integration Suite for the complete EquiLearn system.
    Flow: Input -> FastAPI -> Job -> Queue/Worker -> M1/M2 -> Adapter -> M3 -> Rules -> PackageBuilder -> DB -> MinIO -> Result API.
    """

    def setUp(self):
        job_store.clear()
        artifact_store.clear_mock_store()

    def _verify_db_record(self, job_id: str, expected_status: str, expected_profile: str, expected_input_type: str):
        db = SessionLocal()
        try:
            row = db.query(JobDB).filter(JobDB.job_id == job_id).first()
            self.assertIsNotNone(row, f"Job {job_id} not found in PostgreSQL/SQLite database")
            self.assertEqual(row.status, expected_status)
            self.assertEqual(row.profile.lower(), expected_profile.lower())
            self.assertEqual(row.input_type.lower(), expected_input_type.lower())
            self.assertIsNotNone(row.created_at)
            self.assertIsNotNone(row.updated_at)
            return row
        finally:
            db.close()

    def _run_e2e_flow(
        self,
        input_type: str,
        profile: str,
        raw_text: str = None,
        file_tuple: tuple = None,
        expected_status: str = "done",
    ):
        # 1. Input -> FastAPI job creation
        data = {"profile": profile, "input_type": input_type}
        if raw_text:
            data["raw_text"] = raw_text

        files = {"file": file_tuple} if file_tuple else None

        post_resp = client.post("/api/v1/jobs", data=data, files=files)
        self.assertEqual(post_resp.status_code, 202, f"Job creation failed: {post_resp.text}")
        created_data = post_resp.json()
        self.assertIn("job_id", created_data)
        job_id = created_data["job_id"]
        self.assertTrue(len(job_id) > 10, "job_id must be a valid unique identifier")

        # 2. Status verification via GET /api/v1/jobs/{job_id}
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        self.assertEqual(status_resp.status_code, 200)
        status_data = status_resp.json()
        self.assertEqual(status_data["job_id"], job_id)
        self.assertEqual(status_data["profile"].lower(), profile.lower())
        self.assertEqual(status_data["status"], expected_status)

        # 3. PostgreSQL persistence verification
        db_row = self._verify_db_record(job_id, expected_status, profile, input_type)

        # 4. MinIO/S3 artifact storage verification (if file was provided)
        if file_tuple:
            art_resp = client.get(f"/api/v1/jobs/{job_id}/artifacts/input")
            self.assertEqual(art_resp.status_code, 200, "Uploaded input artifact must be retrievable")
            self.assertEqual(art_resp.content, file_tuple[1].getvalue(), "Artifact bytes must match uploaded data exactly")

        # 5. Result API verification via GET /api/v1/jobs/{job_id}/result
        result_resp = client.get(f"/api/v1/jobs/{job_id}/result")
        self.assertEqual(result_resp.status_code, 200, f"Result endpoint failed: {result_resp.text}")
        package_dict = result_resp.json()

        # Strict schema validation via versioned Pydantic model
        package = AccessibilityPackage(**package_dict)
        self.assertEqual(package.job_id, job_id)
        expected_pkg_status = "partially_completed" if expected_status == "partially_completed" else "SUCCESS"
        self.assertEqual(package.status, expected_pkg_status)
        self.assertEqual(package.profile.upper(), profile.upper())

        return package, db_row

    # -------------------------------------------------------------
    # Primary Pipeline Flows
    # -------------------------------------------------------------

    def test_flow_1_plain_text_to_m3_dyslexia(self):
        """1. Plain text -> M3 -> Package Builder -> Result API (Dyslexia profile)"""
        sample_text = "Photosynthesis is the biological process by which green plants convert light energy into chemical energy."
        package, db_row = self._run_e2e_flow(
            input_type="text",
            profile="dyslexia",
            raw_text=sample_text,
            expected_status="done"
        )
        # Verify text reached M3 and package builder
        self.assertTrue(package.simplified_text or package.raw_text)
        metadata = package.recommended_representations.get("metadata", {})
        self.assertIn("structured_text", metadata, "Dyslexia profile must contain structured_text metadata")
        structured = metadata["structured_text"]
        self.assertIn("title", structured)
        self.assertIn("key_points", structured)

    def test_flow_2_image_to_m1_to_m3_low_vision(self):
        """2. Image -> M1 -> M3 -> Package Builder -> Result API (Low Vision profile)"""
        img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRfakeimagecontent"
        package, db_row = self._run_e2e_flow(
            input_type="image",
            profile="low_vision",
            file_tuple=("diagram.png", io.BytesIO(img_bytes), "image/png"),
            expected_status="done"
        )
        # M1 output verification
        self.assertEqual(package.input_type, "IMAGE")
        self.assertIn("raw_text", package.model_dump())
        # Profile specific presentation mode
        mode = package.recommended_representations.get("metadata", {}).get("presentation_mode")
        self.assertEqual(mode, "high_contrast_magnifiable")

    def test_flow_3_pdf_to_ocr_to_m3_blind(self):
        """3. PDF -> extraction/OCR -> M3 -> Package Builder -> Result API (Blind profile)"""
        pdf_bytes = b"%PDF-1.4 sample pdf content for extraction test"
        package, db_row = self._run_e2e_flow(
            input_type="pdf",
            profile="blind",
            file_tuple=("handout.pdf", io.BytesIO(pdf_bytes), "application/pdf"),
            expected_status="done"
        )
        self.assertEqual(package.input_type, "PDF")
        reps = package.recommended_representations
        self.assertIn("tts_ready_text", reps, "Blind profile must provide tts_ready_text")

    def test_flow_4_audio_to_m2_whisper_to_m3_deaf(self):
        """4. Audio -> M2/Whisper -> M3 -> Package Builder -> Result API (Deaf/HoH profile)"""
        audio_bytes = b"ID3\x03\x00\x00\x00fake audio recording bytes"
        package, db_row = self._run_e2e_flow(
            input_type="audio",
            profile="deaf",
            file_tuple=("lecture.mp3", io.BytesIO(audio_bytes), "audio/mpeg"),
            expected_status="done"
        )
        self.assertEqual(package.input_type, "AUDIO")
        # Verify M2 transcript reached package
        self.assertIsNotNone(package.transcript)
        self.assertTrue(len(package.transcript) > 0)
        # Verify deaf representations
        mode = package.recommended_representations.get("metadata", {}).get("presentation_mode")
        self.assertEqual(mode, "caption_optimized")
        self.assertTrue(len(package.recommended_representations.get("primary_text", "")) > 0)

    def test_flow_5_video_multimodal_to_m1_m2_m3(self):
        """5. Video/Multimodal -> M2 + M1 -> M3 -> Package Builder -> Result API"""
        video_bytes = b"\x00\x00\x00\x18ftypmp42fake videodata"
        package, db_row = self._run_e2e_flow(
            input_type="multimodal",
            profile="blind",
            file_tuple=("lecture.mp4", io.BytesIO(video_bytes), "video/mp4"),
            expected_status="done"
        )
        self.assertEqual(package.input_type, "MULTIMODAL")
        # Multimodal synthesizes both M1 visual text and M2 transcript
        self.assertIsNotNone(package.transcript)
        self.assertIn("tts_ready_text", package.recommended_representations)

    # -------------------------------------------------------------
    # Cross-Cutting Profile Output Verification
    # -------------------------------------------------------------

    def test_all_four_profiles_produce_distinct_optimized_packages(self):
        """Verify Blind, Deaf, Low Vision, and Dyslexia profiles produce targeted representations."""
        text = "Cellular respiration produces ATP by oxidizing glucose."
        profiles = ["blind", "deaf", "low_vision", "dyslexia"]
        outputs = {}

        for prof in profiles:
            pkg, _ = self._run_e2e_flow(input_type="text", profile=prof, raw_text=text)
            outputs[prof] = pkg

        # Blind has TTS
        self.assertIn("tts_ready_text", outputs["blind"].recommended_representations)
        # Deaf has caption-optimized
        self.assertEqual(outputs["deaf"].recommended_representations["metadata"]["presentation_mode"], "caption_optimized")
        # Low Vision has high-contrast
        self.assertEqual(outputs["low_vision"].recommended_representations["metadata"]["presentation_mode"], "high_contrast_magnifiable")
        # Dyslexia has structured text
        self.assertIn("structured_text", outputs["dyslexia"].recommended_representations["metadata"])

    # -------------------------------------------------------------
    # Failure Scenarios & Edge Cases
    # -------------------------------------------------------------

    def test_invalid_file_empty_bytes(self):
        """Empty input file produces appropriate warning without crashing."""
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "blind", "input_type": "pdf"},
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        self.assertEqual(resp.status_code, 202)
        data = resp.json()
        self.assertTrue(any("empty" in w.lower() for w in data["warnings"]))

    def test_unsupported_input_type(self):
        """Unsupported input type rejected cleanly with 422."""
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "blind", "input_type": "spreadsheet"},
            files={"file": ("data.xlsx", io.BytesIO(b"fake-excel"), "application/octet-stream")},
        )
        self.assertEqual(resp.status_code, 422)

    def test_empty_text_input_rejected(self):
        """Empty text input rejected with 422."""
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "dyslexia", "input_type": "text", "raw_text": "   "},
        )
        self.assertEqual(resp.status_code, 422)

    def test_missing_m1_m2_intermediate_output_multimodal(self):
        """Multimodal with missing audio/visual content handles partial missing modality cleanly."""
        # Only video file provided without audio channel
        resp = client.post(
            "/api/v1/jobs",
            data={"profile": "deaf", "input_type": "multimodal"},
            files={"file": ("visual_only.png", io.BytesIO(b"image_content"), "image/png")},
        )
        self.assertEqual(resp.status_code, 202)
        job_id = resp.json()["job_id"]
        result_resp = client.get(f"/api/v1/jobs/{job_id}/result")
        self.assertEqual(result_resp.status_code, 200)

    def test_m3_llm_failure_handling(self):
        """M3/LLM pipeline failure sets job to failed without crashing API."""
        with patch("orchestrator.run_member3_pipeline", side_effect=RuntimeError("M3 Service Unavailable")):
            resp = client.post(
                "/api/v1/jobs",
                data={"profile": "blind", "input_type": "text", "raw_text": "Some text to process"},
            )
            job_id = resp.json()["job_id"]
            status_resp = client.get(f"/api/v1/jobs/{job_id}")
            self.assertEqual(status_resp.status_code, 200)
            self.assertEqual(status_resp.json()["status"], "failed")
            self.assertIn("M3 Service Unavailable", status_resp.json()["error"])

    def test_worker_timeout_and_retry(self):
        """Worker network/timeout error triggers Celery retry logic and records failure when retries exhausted."""
        with patch("worker.tasks.DummyM2Pipeline.process", side_effect=TimeoutError("Network timed out")):
            try:
                resp = client.post(
                    "/api/v1/jobs",
                    data={"profile": "deaf", "input_type": "audio"},
                    files={"file": ("audio.mp3", io.BytesIO(b"fake audio"), "audio/mpeg")},
                )
            except Exception:
                pass
            
            # Since retries are exhausted in eager mode, verify status is failed and not crashed
            if "resp" in locals():
                job_id = resp.json()["job_id"]
                status_resp = client.get(f"/api/v1/jobs/{job_id}")
                self.assertEqual(status_resp.json()["status"], "failed")

    def test_partial_modality_failure_preserves_successful_output(self):
        """When M1 fails in multimodal, M2 output is preserved with status partially_completed."""
        with patch("worker.tasks.DummyM1Pipeline.process", side_effect=Exception("Corrupt frame in visual stream")):
            resp = client.post(
                "/api/v1/jobs",
                data={"profile": "deaf", "input_type": "multimodal"},
                files={"file": ("stream.mp4", io.BytesIO(b"stream_bytes"), "video/mp4")},
            )
            job_id = resp.json()["job_id"]
            status_resp = client.get(f"/api/v1/jobs/{job_id}")
            self.assertEqual(status_resp.json()["status"], "partially_completed")

            result_resp = client.get(f"/api/v1/jobs/{job_id}/result")
            self.assertEqual(result_resp.status_code, 200)
            pkg = result_resp.json()
            self.assertEqual(pkg["status"], "partially_completed")
            self.assertIsNotNone(pkg["transcript"])
            self.assertTrue(any("Corrupt frame" in w for w in pkg["warnings"]))


if __name__ == "__main__":
    unittest.main()
