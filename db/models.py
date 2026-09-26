"""
SQLAlchemy ORM model for the jobs table.
No AI logic – pure persistence schema only.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JobDB(Base):
    __tablename__ = "jobs"

    # Primary key
    job_id          = Column(String(36),  primary_key=True, index=True)

    # Classification
    profile         = Column(String(20),  nullable=False)
    input_type      = Column(String(20),  nullable=False)
    status          = Column(String(20),  nullable=False, default="queued")

    # Payload metadata (file bytes NOT stored; only descriptors)
    raw_text        = Column(Text,        nullable=True)
    file_name       = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer,     nullable=True)

    # JSON-encoded lists/dicts stored as text (avoids DB-specific JSON types)
    warnings_json   = Column(Text,        nullable=True)   # json.dumps([...])
    result_json     = Column(Text,        nullable=True)   # json.dumps({...})

    # Diagnostics
    error           = Column(Text,        nullable=True)

    # Timestamps (UTC)
    created_at      = Column(DateTime,    nullable=False, default=datetime.utcnow)
    updated_at      = Column(DateTime,    nullable=False, default=datetime.utcnow,
                             onupdate=datetime.utcnow)
