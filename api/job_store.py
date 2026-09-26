"""
Job store – thin facade over the DB repository.
Preserves the original in-memory interface so all existing callers
(routes, tests) continue to work without modification.
"""
from typing import Optional, List
from api.schemas import JobRecord
from db.session import SessionLocal
import db.repository as repo


def save(record: JobRecord) -> None:
    db = SessionLocal()
    try:
        repo.save_job(db, record)
    finally:
        db.close()


def get(job_id: str) -> Optional[JobRecord]:
    db = SessionLocal()
    try:
        return repo.get_job(db, job_id)
    finally:
        db.close()


def exists(job_id: str) -> bool:
    return get(job_id) is not None


def all_jobs() -> List[JobRecord]:
    # Extend in a later stage with pagination
    raise NotImplementedError("Use GET /api/v1/jobs (coming in a later stage)")


def clear() -> None:
    """Test helper – wipes all jobs from the DB (creates tables if needed)."""
    from db.init_db import create_tables
    create_tables()          # idempotent; safe to call even if tables exist
    db = SessionLocal()
    try:
        repo.delete_all(db)
    finally:
        db.close()
