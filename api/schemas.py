"""
EquiLearn Backend – API layer schemas.
Only Pydantic request/response models. No AI logic here.
"""
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


# ─── Health ────────────────────────────────────────────────────────────────── #

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ComponentStatus(BaseModel):
    name: str
    status: str          # "available" | "unavailable"
    detail: Optional[str] = None


class ModelsHealthResponse(BaseModel):
    overall: str         # "healthy" | "degraded" | "unavailable"
    components: list[ComponentStatus]


# ─── Jobs ──────────────────────────────────────────────────────────────────── #

class AccessibilityProfile(str, Enum):
    BLIND      = "blind"
    DEAF       = "deaf"
    LOW_VISION = "low_vision"
    DYSLEXIA   = "dyslexia"


class InputType(str, Enum):
    TEXT       = "text"
    IMAGE      = "image"
    PDF        = "pdf"
    AUDIO      = "audio"
    VIDEO      = "video"
    MULTIMODAL = "multimodal"


class JobStatus(str, Enum):
    QUEUED     = "queued"
    PROCESSING = "processing"
    DONE       = "done"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED     = "failed"


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    input_type: InputType
    profile: AccessibilityProfile
    message: str
    warnings: List[str] = []


class JobRecord(BaseModel):
    """Internal in-memory record; not exposed directly to the client."""
    job_id: str
    status: JobStatus
    input_type: InputType
    profile: AccessibilityProfile
    raw_text: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    created_at: str
    warnings: List[str] = []
    result: Optional[dict] = None
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Public response for GET /api/v1/jobs/{job_id}."""
    job_id: str
    status: JobStatus
    input_type: InputType
    profile: AccessibilityProfile
    created_at: str
    warnings: List[str] = []
    error: Optional[str] = None
    result: Optional[dict] = None


class AccessibilityPackage(BaseModel):
    """Final output schema matching the EquiLearn Accessibility Package contract."""
    job_id: str
    status: str
    input_type: str
    profile: str
    raw_text: Optional[str] = None
    alt_text: Optional[str] = None
    transcript: Optional[str] = None
    captions_vtt: Optional[str] = None
    summary: Optional[str] = None
    simplified_text: Optional[str] = None
    complexity_score: Optional[float] = None
    key_terms: List[str] = []
    reading_time: Optional[str] = None
    recommended_representations: dict = {}
    tts_audio_url: Optional[str] = None
    warnings: List[str] = []
    model_metadata: dict = {}
