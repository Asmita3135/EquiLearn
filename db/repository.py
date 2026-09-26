"""
CRUD operations for the jobs table.
All DB interaction lives here – routes and job_store call these helpers.
"""
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from db.models import JobDB
from api.schemas import (
    JobRecord, JobStatus, InputType, AccessibilityProfile,
)


# ─── helpers ──────────────────────────────────────────────────────────────── #

def _to_db(record: JobRecord) -> JobDB:
    """Convert a Pydantic JobRecord → SQLAlchemy JobDB row."""
    # created_at is an ISO string in JobRecord; store as datetime
    try:
        created_dt = datetime.fromisoformat(record.created_at)
    except (ValueError, AttributeError):
        created_dt = datetime.now(timezone.utc)

    return JobDB(
        job_id          = record.job_id,
        profile         = record.profile.value,
        input_type      = record.input_type.value,
        status          = record.status.value,
        raw_text        = record.raw_text,
        file_name       = record.file_name,
        file_size_bytes = record.file_size_bytes,
        warnings_json   = json.dumps(record.warnings),
        error           = record.error,
        result_json     = json.dumps(record.result) if record.result else None,
        created_at      = created_dt,
        updated_at      = datetime.now(timezone.utc),
    )


def _from_db(row: JobDB) -> JobRecord:
    """Convert a SQLAlchemy JobDB row → Pydantic JobRecord."""
    return JobRecord(
        job_id          = row.job_id,
        profile         = AccessibilityProfile(row.profile),
        input_type      = InputType(row.input_type),
        status          = JobStatus(row.status),
        raw_text        = row.raw_text,
        file_name       = row.file_name,
        file_size_bytes = row.file_size_bytes,
        created_at      = row.created_at.isoformat() if row.created_at else "",
        warnings        = json.loads(row.warnings_json) if row.warnings_json else [],
        error           = row.error,
        result          = json.loads(row.result_json) if row.result_json else None,
    )


# ─── public API ────────────────────────────────────────────────────────────── #

def save_job(db: Session, record: JobRecord) -> None:
    """Insert or replace a job record (upsert via merge)."""
    db_row = _to_db(record)
    db.merge(db_row)
    db.commit()


def get_job(db: Session, job_id: str) -> Optional[JobRecord]:
    """Return a JobRecord by job_id, or None if not found."""
    row = db.query(JobDB).filter(JobDB.job_id == job_id).first()
    return _from_db(row) if row else None


def update_job_status(
    db: Session,
    job_id: str,
    status: JobStatus,
    error: Optional[str] = None,
    result: Optional[dict] = None,
) -> Optional[JobRecord]:
    """Update status (and optionally error/result) for an existing job."""
    row = db.query(JobDB).filter(JobDB.job_id == job_id).first()
    if row is None:
        return None
    row.status     = status.value
    row.updated_at = datetime.now(timezone.utc)
    if error is not None:
        row.error = error
    if result is not None:
        row.result_json = json.dumps(result)
    db.commit()
    db.refresh(row)
    return _from_db(row)


def delete_all(db: Session) -> None:
    """Test helper – truncate jobs table."""
    db.query(JobDB).delete()
    db.commit()
