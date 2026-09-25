"""
Member 1: Vision & Document AI Integrated Pipeline
Complete Processing Pipeline:
PDF/Image → document extraction → scanned-page rendering → preprocessing → PaddleOCR → confidence check → Tesseract fallback → VLM visual analysis → alt-text/diagram fusion
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import numpy as np

from equilearn.core.schemas import (
    VisionOutputPayload,
    PageProcessingResult,
    OCRResult,
    VLMResult,
)
from equilearn.vision.document_processor import DocumentProcessor
from equilearn.vision.preprocessor import ImagePreprocessor
from equilearn.vision.ocr_engine import OCREngine
from equilearn.vision.vlm_engine import VLMEngine
from equilearn.vision.alt_text import AltTextGenerator
from equilearn.vision.evaluator import VisionEvaluator


class VisionPipeline:
    """
    Top-level processing orchestrator for Member 1 (Vision & Document AI).
    Flow: PDF/Image → extraction → preprocessing → OCR → VLM → alt-text fusion
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        document_processor: Optional[DocumentProcessor] = None,
        preprocessor: Optional[ImagePreprocessor] = None,
        ocr_engine: Optional[OCREngine] = None,
        vlm_engine: Optional[VLMEngine] = None,
        alt_text_generator: Optional[AltTextGenerator] = None,
    ) -> None:
        self.config = config or {}
        self.document_processor = document_processor or DocumentProcessor(config=self.config.get("document_processor"))
        self.preprocessor = preprocessor or ImagePreprocessor(config=self.config.get("preprocessor"))
        self.ocr_engine = ocr_engine or OCREngine(config=self.config.get("ocr_engine"))
        self.vlm_engine = vlm_engine or VLMEngine(config=self.config.get("vlm_engine"))
        self.alt_text_generator = alt_text_generator or AltTextGenerator(config=self.config.get("alt_text"))
        self.evaluator = VisionEvaluator(config=self.config.get("evaluator"))

    def _is_image_file(self, path: Path) -> bool:
        return path.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]

    def process_image(self, image_source: Union[str, Path, Any], source_name: str = "standalone_image") -> VisionOutputPayload:
        """Processes a single standalone image through preprocessing → OCR → VLM → Alt-Text fusion."""
        warnings: List[str] = []
        errors: List[str] = []

        if isinstance(image_source, (str, Path)):
            source_path = Path(image_source)
            source_name = source_path.name
            if not source_path.exists():
                errors.append(f"Image file not found: {image_source}")
                return VisionOutputPayload(
                    document_id=source_name,
                    extracted_text="",
                    pages=[],
                    metadata={"status": "error", "errors": errors},
                )

        # 1. Preprocess image
        try:
            preprocessed_img = self.preprocessor.preprocess_pipeline(image_source)
        except Exception as exc:
            errors.append(f"Image preprocessing failed: {str(exc)}")
            preprocessed_img = image_source

        # 2. Run OCR
        ocr_res = None
        try:
            ocr_res = self.ocr_engine.process_image(preprocessed_img)
            if ocr_res.warnings:
                warnings.extend(ocr_res.warnings)
            if ocr_res.errors:
                errors.extend(ocr_res.errors)
        except Exception as exc:
            errors.append(f"OCR processing failed: {str(exc)}")
            ocr_res = OCRResult(text="", blocks=[], errors=[f"OCR processing failed: {str(exc)}"])

        # 3. Run VLM Visual Understanding
        vlm_res = None
        try:
            vlm_res = self.vlm_engine.analyze_visual(preprocessed_img)
            if vlm_res.warnings:
                warnings.extend(vlm_res.warnings)
            if vlm_res.errors:
                errors.extend(vlm_res.errors)
        except Exception as exc:
            errors.append(f"VLM visual analysis failed: {str(exc)}")
            vlm_res = VLMResult(description="", errors=[f"VLM visual analysis failed: {str(exc)}"])

        # 4. Generate Alt-Text
        alt_text = self.alt_text_generator.generate_alt_text(
            vlm_result=vlm_res,
            ocr_result=ocr_res,
            context={"title": source_name},
        )

        text_content = ocr_res.text if ocr_res else ""

        page_result = PageProcessingResult(
            source=source_name,
            page_number=1,
            source_type="image",
            text=text_content,
            requires_ocr=True,
            ocr_result=ocr_res,
            vlm_result=vlm_res,
            alt_text=alt_text,
            warnings=list(set(warnings)),
            errors=list(set(errors)),
        )

        return VisionOutputPayload(
            document_id=source_name,
            extracted_text=text_content,
            pages=[page_result],
            ocr_result=ocr_res,
            vlm_result=vlm_res,
            alt_text=alt_text,
            metadata={"source_type": "image", "status": "success" if not errors else "partial_success"},
        )

    def process_document(self, input_source: Union[str, Path, Any]) -> VisionOutputPayload:
        """
        Executes top-level Member 1 document processing pipeline.
        PDF/Image → document extraction → scanned-page rendering → preprocessing → PaddleOCR → confidence check → Tesseract fallback → VLM visual analysis → alt-text fusion
        """
        if not isinstance(input_source, (str, Path)):
            # Direct array / PIL Image input
            return self.process_image(input_source)

        path = Path(input_source)
        if not path.exists():
            return VisionOutputPayload(
                document_id=path.name,
                extracted_text="",
                pages=[],
                metadata={"status": "error", "errors": [f"File not found: {input_source}"]},
            )

        if self._is_image_file(path):
            return self.process_image(path)

        if path.suffix.lower() != ".pdf":
            return VisionOutputPayload(
                document_id=path.name,
                extracted_text="",
                pages=[],
                metadata={"status": "error", "errors": [f"Unsupported file format: {path.suffix}"]},
            )

        # Process PDF Document
        try:
            doc_classification = self.document_processor.process_pdf(path, render_ocr_pages=True)
        except Exception as exc:
            return VisionOutputPayload(
                document_id=path.name,
                extracted_text="",
                pages=[],
                metadata={"status": "error", "errors": [f"PDF document processing failed: {str(exc)}"]},
            )

        processed_pages: List[PageProcessingResult] = []
        combined_texts: List[str] = []
        primary_ocr: Optional[OCRResult] = None
        primary_vlm: Optional[VLMResult] = None
        primary_alt: str = ""

        raw_pages = doc_classification.get("pages", [])

        for p_info in raw_pages:
            p_num = p_info.get("page_number", 1)
            src_type = p_info.get("source_type", "digital_text")
            native_text = p_info.get("text", "")
            req_ocr = p_info.get("requires_ocr", False)
            page_warnings: List[str] = list(p_info.get("warnings", []))
            page_errors: List[str] = list(p_info.get("errors", []))

            ocr_res: Optional[OCRResult] = None
            vlm_res: Optional[VLMResult] = None
            alt_text: str = ""
            final_page_text = native_text

            if req_ocr or src_type == "requires_ocr":
                # Render scanned PDF page
                rendered_img = None
                try:
                    rendered_img = self.document_processor.render_single_page(path, p_num)
                except Exception as exc:
                    page_errors.append(f"Page {p_num} rasterization failed: {str(exc)}")

                if rendered_img is not None:
                    # Preprocess
                    try:
                        prep_img = self.preprocessor.preprocess_pipeline(rendered_img)
                    except Exception as exc:
                        page_warnings.append(f"Page {p_num} preprocessing warning: {str(exc)}")
                        prep_img = rendered_img

                    # Run OCR
                    try:
                        ocr_res = self.ocr_engine.process_image(prep_img)
                        if ocr_res.warnings:
                            page_warnings.extend(ocr_res.warnings)
                        if ocr_res.errors:
                            page_errors.extend(ocr_res.errors)
                        if ocr_res.text.strip():
                            final_page_text = ocr_res.text.strip()
                    except Exception as exc:
                        page_errors.append(f"Page {p_num} OCR failed: {str(exc)}")
                        ocr_res = OCRResult(text="", blocks=[], errors=[str(exc)])

                    # Run VLM Visual Analysis
                    try:
                        vlm_res = self.vlm_engine.analyze_visual(prep_img)
                        if vlm_res.warnings:
                            page_warnings.extend(vlm_res.warnings)
                        if vlm_res.errors:
                            page_errors.extend(vlm_res.errors)
                    except Exception as exc:
                        page_errors.append(f"Page {p_num} VLM analysis failed: {str(exc)}")
                        vlm_res = VLMResult(description="", errors=[str(exc)])

                    # Fuse Alt-Text
                    alt_text = self.alt_text_generator.generate_alt_text(
                        vlm_result=vlm_res,
                        ocr_result=ocr_res,
                        context={"title": path.name, "page_number": p_num},
                    )

                src_type_label = "scanned_page"
            else:
                src_type_label = "digital_text"

            if final_page_text:
                combined_texts.append(final_page_text)

            page_result = PageProcessingResult(
                source=path.name,
                page_number=p_num,
                source_type=src_type_label,
                text=final_page_text,
                requires_ocr=req_ocr,
                ocr_result=ocr_res,
                vlm_result=vlm_res,
                alt_text=alt_text,
                warnings=list(set(page_warnings)),
                errors=list(set(page_errors)),
            )

            processed_pages.append(page_result)

            if primary_ocr is None and ocr_res is not None:
                primary_ocr = ocr_res
            if primary_vlm is None and vlm_res is not None:
                primary_vlm = vlm_res
            if not primary_alt and alt_text:
                primary_alt = alt_text

        overall_text = "\n\n".join(combined_texts)

        return VisionOutputPayload(
            document_id=path.name,
            extracted_text=overall_text,
            pages=processed_pages,
            ocr_result=primary_ocr,
            vlm_result=primary_vlm,
            alt_text=primary_alt,
            metadata={"page_count": len(processed_pages), "status": "success"},
        )
