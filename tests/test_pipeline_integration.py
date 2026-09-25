"""
Integration tests for Member 1 Stage 5 — Top-Level VisionPipeline Orchestration
Tests:
1. digital PDF
2. scanned PDF
3. standalone image
4. multi-page mixed PDF
5. OCR fallback
6. VLM unavailable
7. both OCR/VLM failure
8. partial-result preservation
9. invalid input
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pymupdf

from equilearn.core.schemas import OCRResult, OCRWord, VLMResult, VisionOutputPayload
from equilearn.vision import (
    VisionPipeline,
    DocumentProcessor,
    ImagePreprocessor,
    OCREngine,
    VLMEngine,
    AltTextGenerator,
)
from equilearn.vision.vlm_engine import MockVLMAdapter


class TestVisionPipelineIntegration(unittest.TestCase):
    """Integration test suite for VisionPipeline end-to-end document and image processing."""

    def setUp(self) -> None:
        self.pipeline = VisionPipeline()

    def _create_test_pdf(self, pages_text: list) -> str:
        """Helper to generate a temporary PDF with custom text on specified pages."""
        doc = pymupdf.open()
        for text in pages_text:
            page = doc.new_page(width=612, height=792)
            if text:
                page.insert_text((50, 50), text)
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(doc.tobytes())
        tmp.close()
        doc.close()
        return tmp.name

    def test_1_digital_pdf(self) -> None:
        """1. Test digital PDF page uses native extracted text without running OCR."""
        pdf_path = self._create_test_pdf(["Digital Text Page Content"])

        try:
            payload = self.pipeline.process_document(pdf_path)
            self.assertIsInstance(payload, VisionOutputPayload)
            self.assertIn("Digital Text Page Content", payload.extracted_text)
            self.assertEqual(len(payload.pages), 1)

            page = payload.pages[0]
            self.assertEqual(page.source_type, "digital_text")
            self.assertFalse(page.requires_ocr)
            self.assertIsNone(page.ocr_result)  # OCR skipped for digital text page

            # Verify dictionary output schema
            d = payload.to_dict()
            self.assertIn("ocr", d)
            self.assertIn("visual", d)
            self.assertIn("pages", d)
            self.assertEqual(d["pages"][0]["source_type"], "digital_text")
        finally:
            Path(pdf_path).unlink(missing_ok=True)

    def test_2_scanned_pdf(self) -> None:
        """2. Test scanned PDF page (no digital text) triggers page rasterization, OCR, VLM, and alt-text."""
        pdf_path = self._create_test_pdf([""])  # empty text stream

        mock_vlm_adapter = MockVLMAdapter(
            description="Scanned textbook diagram.",
            visual_elements=["chart_box"],
            relationships=["box connects to header"],
        )
        mock_ocr = OCREngine()
        mock_vlm = VLMEngine(adapter=mock_vlm_adapter)
        custom_pipeline = VisionPipeline(ocr_engine=mock_ocr, vlm_engine=mock_vlm)

        try:
            payload = custom_pipeline.process_document(pdf_path)
            self.assertEqual(len(payload.pages), 1)
            page = payload.pages[0]

            self.assertEqual(page.source_type, "scanned_page")
            self.assertTrue(page.requires_ocr)
            self.assertIsNotNone(page.vlm_result)
            self.assertEqual(page.vlm_result.description, "Scanned textbook diagram.")
            self.assertIn("Scanned textbook diagram", page.alt_text)
        finally:
            Path(pdf_path).unlink(missing_ok=True)

    def test_3_standalone_image(self) -> None:
        """3. Test standalone image input processes through preprocessing, OCR, VLM, and alt-text."""
        arr = np.ones((150, 150, 3), dtype=np.uint8) * 255
        mock_vlm_adapter = MockVLMAdapter(
            description="Photo of laboratory experiment.",
            visual_elements=["beaker", "burner"],
        )
        custom_pipeline = VisionPipeline(vlm_engine=VLMEngine(adapter=mock_vlm_adapter))

        payload = custom_pipeline.process_document(arr)
        self.assertEqual(payload.metadata["source_type"], "image")
        self.assertEqual(len(payload.pages), 1)

        page = payload.pages[0]
        self.assertEqual(page.source_type, "image")
        self.assertIsNotNone(page.vlm_result)
        self.assertEqual(page.vlm_result.description, "Photo of laboratory experiment.")

    def test_4_multi_page_mixed_pdf(self) -> None:
        """4. Test multi-page mixed PDF preserves page order, page numbers, native text, and OCR outputs."""
        pdf_path = self._create_test_pdf(["Chapter 1 Digital Intro", ""])  # Page 1 digital, Page 2 scanned

        try:
            payload = self.pipeline.process_document(pdf_path)
            self.assertEqual(len(payload.pages), 2)

            page1 = payload.pages[0]
            self.assertEqual(page1.page_number, 1)
            self.assertEqual(page1.source_type, "digital_text")
            self.assertFalse(page1.requires_ocr)

            page2 = payload.pages[1]
            self.assertEqual(page2.page_number, 2)
            self.assertEqual(page2.source_type, "scanned_page")
            self.assertTrue(page2.requires_ocr)
        finally:
            Path(pdf_path).unlink(missing_ok=True)

    def test_5_ocr_fallback_integration(self) -> None:
        """5. Test pipeline integration with low confidence OCR triggering Tesseract fallback."""
        arr = np.ones((100, 100, 3), dtype=np.uint8) * 255

        mock_ocr = MagicMock()
        mock_ocr.process_image.return_value = OCRResult(
            text="Recovered Fallback Text",
            blocks=[],
            average_confidence=0.88,
            fallback_used=True,
            fallback_reason="Primary OCR low confidence",
            engine_used="tesseract",
        )

        pipeline = VisionPipeline(ocr_engine=mock_ocr)
        payload = pipeline.process_image(arr)

        self.assertTrue(payload.ocr_result.fallback_used)
        self.assertEqual(payload.ocr_result.text, "Recovered Fallback Text")

    def test_6_vlm_unavailable_integration(self) -> None:
        """6. Test pipeline execution when VLM is unavailable preserves OCR text and OCR-only alt-text."""
        arr = np.ones((100, 100, 3), dtype=np.uint8) * 255

        failing_vlm_adapter = MockVLMAdapter(raise_error=True)
        mock_ocr = MagicMock()
        mock_ocr.process_image.return_value = OCRResult(
            text="Cell Diagram",
            blocks=[OCRWord("Nucleus", 0.99)],
            average_confidence=0.99,
        )

        pipeline = VisionPipeline(ocr_engine=mock_ocr, vlm_engine=VLMEngine(adapter=failing_vlm_adapter))
        payload = pipeline.process_image(arr)

        self.assertEqual(payload.extracted_text, "Cell Diagram")
        self.assertIn("Image containing text labels: Nucleus", payload.alt_text)
        self.assertIn("Simulated VLM inference failure", payload.vlm_result.errors[0])

    def test_7_both_ocr_vlm_failure(self) -> None:
        """7. Test pipeline when both OCR and VLM fail returns structured errors without crashing."""
        arr = np.ones((100, 100, 3), dtype=np.uint8) * 255

        mock_ocr = MagicMock()
        mock_ocr.process_image.side_effect = Exception("OCR Engine Hardware Crash")
        mock_vlm = MagicMock()
        mock_vlm.analyze_visual.side_effect = Exception("VLM Out of Memory")

        pipeline = VisionPipeline(ocr_engine=mock_ocr, vlm_engine=mock_vlm)
        payload = pipeline.process_image(arr)

        page = payload.pages[0]
        self.assertEqual(page.text, "")
        self.assertIn("Image content unavailable", page.alt_text)
        self.assertGreater(len(page.errors), 0)

    def test_8_partial_result_preservation(self) -> None:
        """8. Test partial result preservation when VLM fails but OCR succeeds."""
        arr = np.ones((100, 100, 3), dtype=np.uint8) * 255

        mock_ocr = MagicMock()
        mock_ocr.process_image.return_value = OCRResult(
            text="Preserved OCR Output",
            blocks=[OCRWord("Preserved", 0.95)],
            average_confidence=0.95,
        )
        mock_vlm = MagicMock()
        mock_vlm.analyze_visual.side_effect = Exception("VLM Timeout")

        pipeline = VisionPipeline(ocr_engine=mock_ocr, vlm_engine=mock_vlm)
        payload = pipeline.process_image(arr)

        self.assertEqual(payload.extracted_text, "Preserved OCR Output")
        self.assertEqual(payload.ocr_result.text, "Preserved OCR Output")
        self.assertIsNotNone(payload.ocr_result)

    def test_9_invalid_input(self) -> None:
        """9. Test invalid inputs (non-existent file, unsupported format) return clean error payloads."""
        payload_missing = self.pipeline.process_document("non_existent_file.pdf")
        self.assertEqual(payload_missing.metadata["status"], "error")
        self.assertIn("not found", payload_missing.metadata["errors"][0])

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"Text file content")
            tmp_path = tmp.name

        try:
            payload_unsupported = self.pipeline.process_document(tmp_path)
            self.assertEqual(payload_unsupported.metadata["status"], "error")
            self.assertIn("Unsupported file format", payload_unsupported.metadata["errors"][0])
        finally:
            Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
