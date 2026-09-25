"""
Unit tests for M1-STAGE 1 — PDF / Document Processor
Tests digital text extraction, page number preservation, source type classification ('digital_text' vs 'requires_ocr'),
selective page rendering, multi-page PDFs, scanned page detection, and error handling (invalid PDF, non-existent file).
"""

import tempfile
import unittest
from pathlib import Path
import numpy as np
import pymupdf

from equilearn.vision.document_processor import DocumentProcessor


class TestDocumentProcessor(unittest.TestCase):
    """Test suite for DocumentProcessor digital PDF classification, extraction, and page rendering."""

    def setUp(self) -> None:
        self.processor = DocumentProcessor()

    def _create_minimal_pdf(self, pages_text: list) -> bytes:
        """Helper using PyMuPDF to create valid single/multi-page PDFs for testing."""
        doc = pymupdf.open()
        for text in pages_text:
            page = doc.new_page(width=612, height=792)
            if text:
                page.insert_text((50, 50), text)
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    def test_valid_digital_pdf_processing(self) -> None:
        """Tests that a valid digital PDF page is recognized as 'digital_text' without rendering."""
        pdf_content = self._create_minimal_pdf(["EquiLearn Digital Document Test"])
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name

        try:
            result = self.processor.process_pdf(tmp_path)
            self.assertIn("pages", result)
            self.assertEqual(len(result["pages"]), 1)

            page = result["pages"][0]
            self.assertEqual(page["page_number"], 1)
            self.assertEqual(page["source_type"], "digital_text")
            self.assertFalse(page["requires_ocr"])
            self.assertEqual(page["warnings"], [])
            self.assertEqual(page["errors"], [])
            self.assertIn("EquiLearn Digital Document Test", page["text"])
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_multi_page_pdf(self) -> None:
        """Tests processing a multi-page PDF with mixed digital text and scanned pages."""
        pdf_content = self._create_minimal_pdf(["Page 1 Digital Text", ""])
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name

        try:
            result = self.processor.process_pdf(tmp_path, render_ocr_pages=True)
            pages = result["pages"]
            self.assertEqual(len(pages), 2)

            self.assertEqual(pages[0]["page_number"], 1)
            self.assertEqual(pages[0]["source_type"], "digital_text")
            self.assertFalse(pages[0]["requires_ocr"])

            self.assertEqual(pages[1]["page_number"], 2)
            self.assertEqual(pages[1]["source_type"], "requires_ocr")
            self.assertTrue(pages[1]["requires_ocr"])
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_scanned_pdf_rendering(self) -> None:
        """Tests that empty/scanned pages are rendered to images only when requires_ocr is True."""
        pdf_content = self._create_minimal_pdf([""])
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name

        try:
            result = self.processor.process_pdf(tmp_path, render_ocr_pages=True)
            page = result["pages"][0]
            self.assertEqual(page["source_type"], "requires_ocr")
            self.assertTrue(page["requires_ocr"])

            rendered_images = self.processor.render_pdf_to_images(tmp_path)
            self.assertEqual(len(rendered_images), 1)
            self.assertIsInstance(rendered_images[0], np.ndarray)
            self.assertGreater(rendered_images[0].shape[0], 0)
            self.assertGreater(rendered_images[0].shape[1], 0)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_prd_document_extraction(self) -> None:
        """Tests processing on the repository PRD document if present."""
        prd_path = Path("EquiLearn_Core_AI_ML_PRD.pdf")
        if prd_path.exists():
            result = self.processor.process_pdf(prd_path)
            self.assertGreater(len(result["pages"]), 0)
            for page in result["pages"]:
                self.assertIn("page_number", page)
                self.assertIn("source_type", page)
                self.assertIn("requires_ocr", page)
                self.assertIn("warnings", page)
                self.assertIn("errors", page)

    def test_non_existent_file_raises_error(self) -> None:
        """Tests that passing a non-existent path raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            self.processor.process_pdf("non_existent_file_xyz.pdf")

    def test_invalid_pdf_raises_error(self) -> None:
        """Tests that a corrupted/invalid PDF file raises ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"Not a real PDF file content")
            tmp_path = tmp.name

        try:
            with self.assertRaises(ValueError):
                self.processor.process_pdf(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_invalid_page_number_rendering(self) -> None:
        """Tests that rendering an out-of-range page number raises ValueError."""
        pdf_content = self._create_minimal_pdf(["Single page"])
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name

        try:
            with self.assertRaises(ValueError):
                self.processor.render_single_page(tmp_path, page_number=999)
        finally:
            Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
