import sys
from typing import Optional

from worker.celery_app import celery_app
import api.job_store as job_store
from api.schemas import JobStatus
from db.session import SessionLocal
import db.repository as repo
from orchestrator import run_equilearn_job
from package_builder import build_accessibility_package

# Make sure M3 path is available
from pathlib import Path
_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from accessibility_rules import UserProfile
from llm_processing import LLMProcessor


from m1_m2_connectors import RealM1Pipeline, RealM2Pipeline

# Retain backward compatibility aliases for test mocks
DummyM1Pipeline = RealM1Pipeline
DummyM2Pipeline = RealM2Pipeline


def dummy_provider(prompt: str) -> str:
    return "Dummy LLM response."


@celery_app.task(bind=True, max_retries=3)
def process_job_task(self, job_id: str):
    """
    Async Celery task to process an EquiLearn job.
    1. Loads job from DB.
    2. Updates status to PROCESSING.
    3. Runs Orchestrator (M1/M2 -> Adapter -> M3).
    4. Builds accessibility package.
    5. Updates DB to DONE (with result) or FAILED (with error).
    """
    db = SessionLocal()
    try:
        record = repo.get_job(db, job_id)
        if not record:
            return

        # 1. Update status to PROCESSING
        repo.update_job_status(db, job_id, JobStatus.PROCESSING)

        # 2. Extract inputs from DB record
        input_type = record.input_type.value
        raw_text = record.raw_text
        profile_str = record.profile.value

        import api.artifact_store as artifact_store

        # Fetch file from MinIO if not purely text
        content = raw_text
        if input_type != "TEXT":
            file_bytes, content_type = artifact_store.get_artifact(job_id, "input")
            if file_bytes:
                content = file_bytes
            else:
                content = raw_text if raw_text else b"" # Fallback

        # Map to UserProfile enum from M3
        try:
            profile_enum = UserProfile[profile_str.upper()]
        except KeyError:
            profile_enum = UserProfile.BLIND

        # 3. Call existing Orchestrator with real M1/M2 pipelines
        m3_processor = LLMProcessor(provider_func=dummy_provider, model_config="dummy-model")
        
        orch_result = run_equilearn_job(
            job_id=job_id,
            input_type=input_type,
            content=content,
            m1_pipeline=RealM1Pipeline(),
            m2_pipeline=RealM2Pipeline(),
            m3_processor=m3_processor,
            raw_text_override=raw_text
        )

        if orch_result.status == "ERROR":
            repo.update_job_status(
                db, job_id, JobStatus.FAILED,
                error=orch_result.error_message
            )
            return

        # 4. Build Accessibility Package
        package = build_accessibility_package(orch_result, profile_enum)

        # 5. Store generated artifacts
        if package.get("captions_vtt"):
            artifact_store.save_artifact(job_id, "vtt", package["captions_vtt"].encode("utf-8"), "text/vtt")
        
        # In a real scenario, we might have TTS audio or OCR images
        if package.get("alt_text"):
            artifact_store.save_artifact(job_id, "ocr", package["alt_text"].encode("utf-8"), "text/plain")

        # 6. Update DB to DONE with result
        final_status = JobStatus.DONE
        if orch_result.status == "PARTIAL_SUCCESS":
            final_status = JobStatus.PARTIALLY_COMPLETED
            package["status"] = "partially_completed"
            
        repo.update_job_status(db, job_id, final_status, result=package)

    except Exception as exc:
        from celery.exceptions import Retry
        if isinstance(exc, Retry):
            db.close()
            raise
            
        # Determine if it's retryable (e.g. timeout, connection error)
        retryable_errors = (ConnectionError, TimeoutError)
        is_retryable = isinstance(exc, retryable_errors)
        
        # If it's a known non-retryable error, don't retry.
        if is_retryable:
            db.close()
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
            
        # Non-retryable
        db = SessionLocal()
        repo.update_job_status(db, job_id, JobStatus.FAILED, error=str(exc))
        db.close()
    finally:
        if 'db' in locals() and hasattr(db, 'close'):
            db.close()
