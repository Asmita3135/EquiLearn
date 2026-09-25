"""
Member 1: Vision & Document AI Module
Pipeline Flow:
PDF/Image → extraction → preprocessing → OCR → VLM → visual information → alt-text → evaluation
"""

from .document_processor import DocumentProcessor
from .preprocessor import ImagePreprocessor
from .ocr_engine import OCREngine
from .vlm_engine import VLMEngine
from .alt_text import AltTextGenerator
from .evaluator import VisionEvaluator
from .pipeline import VisionPipeline

__all__ = [
    "DocumentProcessor",
    "ImagePreprocessor",
    "OCREngine",
    "VLMEngine",
    "AltTextGenerator",
    "VisionEvaluator",
    "VisionPipeline",
]
