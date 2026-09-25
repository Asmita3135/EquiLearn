"""
Data schemas for Vision & Document AI outputs (Member 1).
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class PageProcessingResult:
    """Represents text extraction and source type classification for a single PDF page or image."""
    source: str = ""
    page_number: int = 1
    source_type: str = "digital_text"  # "digital_text", "scanned_page", "image", "requires_ocr"
    text: str = ""
    requires_ocr: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    image: Optional[Any] = None
    ocr_result: Optional[OCRResult] = None
    vlm_result: Optional[VLMResult] = None
    alt_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "page_number": self.page_number,
            "source_type": self.source_type,
            "text": self.text,
            "requires_ocr": self.requires_ocr,
            "ocr": self.ocr_result.to_dict() if self.ocr_result else None,
            "visual": self.vlm_result.to_dict() if self.vlm_result else None,
            "alt_text": self.alt_text,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class DocumentProcessingResult:
    """Represents the complete page-by-page extraction result for a PDF document."""
    pages: List[PageProcessingResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pages": [page.to_dict() for page in self.pages]
        }


@dataclass
class BoundingBox:
    """Represents bounding box coordinates [x_min, y_min, x_max, y_max]."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def to_list(self) -> List[float]:
        return [float(self.x_min), float(self.y_min), float(self.x_max), float(self.y_max)]


@dataclass
class OCRWord:
    """Represents a single recognized word or text block with bounding box and confidence."""
    text: str
    confidence: float
    bbox: Optional[BoundingBox] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "bbox": self.bbox.to_list() if self.bbox else [0.0, 0.0, 0.0, 0.0],
            "confidence": round(float(self.confidence), 4),
        }


@dataclass
class OCRResult:
    """Result payload from OCR processing (PaddleOCR primary / Tesseract fallback)."""
    text: str = ""
    blocks: List[OCRWord] = field(default_factory=list)
    average_confidence: float = 0.0
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    engine_used: str = "paddleocr"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    primary_result: Optional[Any] = None

    def __init__(
        self,
        text: str = "",
        blocks: Optional[List[OCRWord]] = None,
        average_confidence: float = 0.0,
        fallback_used: bool = False,
        fallback_reason: Optional[str] = None,
        engine_used: str = "paddleocr",
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        primary_result: Optional[Any] = None,
        raw_text: Optional[str] = None,
        words: Optional[List[OCRWord]] = None,
        is_fallback_triggered: Optional[bool] = None,
    ) -> None:
        self.text = raw_text if raw_text is not None else text
        self.blocks = words if words is not None else (blocks or [])
        self.average_confidence = average_confidence
        self.fallback_used = is_fallback_triggered if is_fallback_triggered is not None else fallback_used
        self.fallback_reason = fallback_reason
        self.engine_used = engine_used
        self.warnings = warnings or []
        self.errors = errors or []
        self.primary_result = primary_result

    @property
    def raw_text(self) -> str:
        return self.text

    @raw_text.setter
    def raw_text(self, val: str) -> None:
        self.text = val

    @property
    def words(self) -> List[OCRWord]:
        return self.blocks

    @words.setter
    def words(self, val: List[OCRWord]) -> None:
        self.blocks = val

    @property
    def is_fallback_triggered(self) -> bool:
        return self.fallback_used

    @is_fallback_triggered.setter
    def is_fallback_triggered(self, val: bool) -> None:
        self.fallback_used = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "blocks": [b.to_dict() if hasattr(b, "to_dict") else b for b in self.blocks],
            "average_confidence": round(float(self.average_confidence), 4),
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "engine_used": self.engine_used,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class VLMResult:
    """Result payload from Vision-Language Model (VLM) visual understanding."""
    description: str = ""
    visual_elements: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    raw_vlm_response: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    model_name: str = "Qwen2.5-VL-3B-Instruct"

    def __init__(
        self,
        description: str = "",
        visual_elements: Optional[List[str]] = None,
        relationships: Optional[List[str]] = None,
        raw_vlm_response: Optional[str] = None,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        model_name: str = "Qwen2.5-VL-3B-Instruct",
        detected_objects: Optional[List[str]] = None,
        spatial_relationships: Optional[List[str]] = None,
    ) -> None:
        self.description = description
        self.visual_elements = detected_objects if detected_objects is not None else (visual_elements or [])
        self.relationships = spatial_relationships if spatial_relationships is not None else (relationships or [])
        self.raw_vlm_response = raw_vlm_response
        self.warnings = warnings or []
        self.errors = errors or []
        self.model_name = model_name

    @property
    def detected_objects(self) -> List[str]:
        return self.visual_elements

    @detected_objects.setter
    def detected_objects(self, val: List[str]) -> None:
        self.visual_elements = val

    @property
    def spatial_relationships(self) -> List[str]:
        return self.relationships

    @spatial_relationships.setter
    def spatial_relationships(self, val: List[str]) -> None:
        self.relationships = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "visual_elements": list(self.visual_elements),
            "relationships": list(self.relationships),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class VisionOutputPayload:
    """Combined Vision & Document AI output for Member 3 consumption."""
    document_id: str
    extracted_text: str
    pages: List[PageProcessingResult] = field(default_factory=list)
    ocr_result: Optional[OCRResult] = None
    vlm_result: Optional[VLMResult] = None
    alt_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "extracted_text": self.extracted_text,
            "pages": [p.to_dict() for p in self.pages],
            "ocr": self.ocr_result.to_dict() if self.ocr_result else None,
            "visual": self.vlm_result.to_dict() if self.vlm_result else None,
            "alt_text": self.alt_text,
            "metadata": self.metadata,
        }
