"""
Core data models and schemas shared across EquiLearn modules.
"""

from .schemas import (
    PageProcessingResult,
    DocumentProcessingResult,
    BoundingBox,
    OCRWord,
    OCRResult,
    VLMResult,
    VisionOutputPayload,
)

__all__ = [
    "PageProcessingResult",
    "DocumentProcessingResult",
    "BoundingBox",
    "OCRWord",
    "OCRResult",
    "VLMResult",
    "VisionOutputPayload",
]
