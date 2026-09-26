"""
POST /api/v1/jobs
Accepts educational input and an accessibility profile.
Validates, creates a queued job record, and returns immediately.
M1 / M2 / M3 are NOT called here.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Form, UploadFile, File, HTTPException, status

from api.schemas import (
    AccessibilityProfile,
    InputType,
    JobStatus,
    JobCreateResponse,
    JobStatusResponse,
    JobRecord,
)
import api.job_store as job_store

router = APIRouter()

# ─── Constants ──────────────────────────────────────────────────────────────── #

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024   # 50 MB

# Maps accepted MIME type prefixes → canonical InputType
_MIME_TO_TYPE: dict[str, InputType] = {
    "image/":       InputType.IMAGE,
    "application/pdf": InputType.PDF,
    "audio/":       InputType.AUDIO,
    "video/":       InputType.VIDEO,
}

# ─── Helpers ────────────────────────────────────────────────────────────────── #

def _detect_input_type(
    input_type_raw: str,
    file: Optional[UploadFile],
    raw_text: Optional[str],
) -> InputType:
    """
    Resolve the canonical InputType.
    Priority: explicit input_type field > file content-type > raw_text presence.
    An unrecognised explicit value is always rejected with 422.
    """
    normalized = input_type_raw.strip().lower()

    # 1. Try direct enum match first – explicit always wins
    try:
        return InputType(normalized)
    except ValueError:
        pass  # not a recognised value; check if we can derive from the file

    # 2. Only attempt MIME-based derivation when no explicit type was given
    #    (i.e. the caller passed an empty / whitespace string)
    if not normalized:
        if file and file.content_type:
            ct = file.content_type.lower()
            for prefix, itype in _MIME_TO_TYPE.items():
                if ct.startswith(prefix):
                    return itype
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file type '{file.content_type}'. "
                       f"Accepted: image, pdf, audio, video.",
            )
        if raw_text:
            return InputType.TEXT

    # 3. Explicit but unrecognised value → always reject
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Unsupported input_type '{input_type_raw}'. "
               f"Accepted: text, image, pdf, audio, video, multimodal.",
    )


def _validate_file_size(file_bytes: bytes, file_name: str) -> None:
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        mb = len(file_bytes) / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{file_name}' is {mb:.1f} MB. Maximum allowed is 50 MB.",
        )


def _validate_text_or_file(
    input_type: InputType,
    raw_text: Optional[str],
    file: Optional[UploadFile],
) -> None:
    """Ensure the payload matches what the input_type actually needs."""
    text_types = {InputType.TEXT}
    file_types  = {InputType.IMAGE, InputType.PDF, InputType.AUDIO, InputType.VIDEO}

    if input_type in text_types and not (raw_text and raw_text.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="input_type='text' requires a non-empty 'raw_text' field.",
        )
    if input_type in file_types and file is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"input_type='{input_type.value}' requires a file upload.",
        )
    if input_type == InputType.MULTIMODAL and not (file or (raw_text and raw_text.strip())):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="input_type='multimodal' requires at least a file or raw_text.",
        )


# ─── Route ──────────────────────────────────────────────────────────────────── #

@router.post(
    "/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Jobs"],
    summary="Submit an educational content job for accessibility transformation",
)
async def create_job(
    profile: AccessibilityProfile = Form(..., description="Target accessibility profile"),
    input_type: str = Form(..., description="One of: text, image, pdf, audio, video, multimodal"),
    raw_text: Optional[str] = Form(None, description="Plain text content (required for input_type=text)"),
    file: Optional[UploadFile] = File(None, description="File upload for image/pdf/audio/video"),
) -> JobCreateResponse:
    """
    Accepts educational content and queues an accessibility transformation job.
    Returns a job_id immediately; processing happens asynchronously.
    """
    warnings: list[str] = []

    # 1. Resolve & validate input type
    resolved_type = _detect_input_type(input_type, file, raw_text)

    # 2. Cross-validate payload vs input type
    _validate_text_or_file(resolved_type, raw_text, file)

    # 5. Generate unique job_id
    job_id = str(uuid.uuid4())

    # 3. Handle file constraints
    file_name: Optional[str] = None
    file_size: Optional[int] = None

    if file is not None:
        file_bytes = await file.read()
        _validate_file_size(file_bytes, file.filename or "upload")
        file_name = file.filename
        file_size = len(file_bytes)

        if file_size == 0:
            warnings.append("Uploaded file is empty – processing may produce no output.")
        else:
            import api.artifact_store as artifact_store
            artifact_store.save_artifact(job_id, "input", file_bytes, file.content_type)

    # 4. Text-only: warn if suspiciously short
    if resolved_type == InputType.TEXT and raw_text and len(raw_text.strip()) < 10:
        warnings.append("Provided text is very short – output quality may be limited.")

    # 6. Create internal job record (status = queued)
    #    This is the bridge to the orchestrator contract – no AI runs here.
    record = JobRecord(
        job_id=job_id,
        status=JobStatus.QUEUED,
        input_type=resolved_type,
        profile=profile,
        raw_text=raw_text.strip() if raw_text else None,
        file_name=file_name,
        file_size_bytes=file_size,
        created_at=datetime.now(timezone.utc).isoformat(),
        warnings=warnings,
    )
    job_store.save(record)

    # 7. Enqueue the async job.
    #    • Redis available  → .delay() publishes to queue; returns instantly.
    #    • No Redis (eager) → run the task in a background thread so the 202
    #      response is returned immediately (not blocked by M3 processing).
    #      We verify the callable is reachable first so mocks / errors surface.
    import asyncio
    from worker.tasks import process_job_task
    from worker.celery_app import celery_app as _celery_app

    try:
        if _celery_app.conf.task_always_eager:
            # Validate the callable is accessible (raises if mocked to fail)
            _fn = process_job_task.run
            if not callable(_fn):
                raise RuntimeError("process_job_task.run is not callable")
            # Fire-and-forget in a background thread; response returns immediately.
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, _fn, job_id)
        else:
            process_job_task.delay(job_id)
    except Exception as e:
        warnings.append(f"Queue unavailable: job saved but not yet enqueued ({type(e).__name__})")

    return JobCreateResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        input_type=resolved_type,
        profile=profile,
        message="Job queued successfully. Use the job_id to poll for results.",
        warnings=warnings,
    )


# ─── GET /api/v1/jobs/{job_id} ──────────────────────────────────────────────── #

@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    tags=["Jobs"],
    summary="Get the current status of a submitted job",
)
def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Returns the persisted status of a previously submitted job.
    Does not trigger any AI processing.
    """
    record = job_store.get(job_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    return JobStatusResponse(
        job_id=record.job_id,
        status=record.status,
        input_type=record.input_type,
        profile=record.profile,
        created_at=record.created_at,
        warnings=record.warnings,
        error=record.error,
        result=record.result,
    )


# ─── GET /api/v1/jobs/{job_id}/result ───────────────────────────────────────── #

from api.schemas import AccessibilityPackage

@router.get(
    "/jobs/{job_id}/result",
    response_model=AccessibilityPackage,
    tags=["Jobs"],
    summary="Get the final accessibility package of a completed job",
)
def get_job_result(job_id: str) -> AccessibilityPackage:
    """
    Returns the final, transformed Accessibility Package if the job is done.
    """
    record = job_store.get(job_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    if record.status not in (JobStatus.DONE, JobStatus.PARTIALLY_COMPLETED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job '{job_id}' is not completed yet. Current status: {record.status.value}",
        )
    if record.result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job '{job_id}' is marked as DONE but has no result payload.",
        )

    # Validate the stored result dictionary against the AccessibilityPackage schema
    try:
        return AccessibilityPackage(**record.result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema mismatch in stored package: {str(e)}",
        )

# ─── GET /api/v1/jobs/{job_id}/artifacts/{artifact_type} ────────────────────── #

from fastapi.responses import Response

@router.get(
    "/jobs/{job_id}/artifacts/{artifact_type}",
    tags=["Jobs"],
    summary="Get a binary artifact associated with a job (e.g., input, OCR, VTT, TTS)",
)
def get_job_artifact(job_id: str, artifact_type: str):
    """
    Returns the binary content of a requested artifact if available.
    """
    import api.artifact_store as artifact_store
    content, content_type = artifact_store.get_artifact(job_id, artifact_type)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_type}' for job '{job_id}' not found.",
        )
    return Response(content=content, media_type=content_type)
