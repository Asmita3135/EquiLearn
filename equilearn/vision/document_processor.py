"""
M1-STAGE 1 — Document Processing Implementation
Handles PDF page opening, digital text extraction, page number preservation,
page type classification ('digital_text' vs 'requires_ocr'), and selective page rasterization.
Pipeline Flow: PDF/Image → extraction
"""

from pathlib import Path
from typing import Dict, Any, List, Union, Optional
import numpy as np
import pypdf
from pypdf.errors import PdfReadError

try:
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

from equilearn.core.schemas import PageProcessingResult, DocumentProcessingResult


class DocumentProcessor:
    """Class for PDF page classification, digital text extraction, and OCR page rendering."""

    def __init__(
        self,
        min_text_length: int = 1,
        dpi: int = 200,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.min_text_length = min_text_length
        self.dpi = dpi
        self.config = config or {}

    def process_pdf(
        self,
        pdf_path: Union[str, Path],
        render_ocr_pages: bool = True,
    ) -> Dict[str, Any]:
        """
        Opens a PDF document, extracts text page by page, and classifies each page:
        - 'digital_text': page contains usable digital text (requires_ocr=False)
        - 'requires_ocr': page is empty or scanned without usable digital text (requires_ocr=True)

        Renders only pages requiring OCR when render_ocr_pages is True.

        Returns dict structure:
        {
            "pages": [
                {
                    "page_number": 1,
                    "source_type": "digital_text",
                    "text": "...",
                    "requires_ocr": False,
                    "warnings": [],
                    "errors": []
                },
                ...
            ]
        }

        Raises FileNotFoundError if pdf_path does not exist.
        Raises ValueError if pdf_path is invalid or corrupted.
        """
        path = Path(pdf_path)
        if not path.is_file():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            reader = pypdf.PdfReader(str(path))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    pass
        except Exception as exc:
            raise ValueError(f"Invalid or corrupted PDF file: {pdf_path}") from exc

        pages_data: List[PageProcessingResult] = []

        for index, page in enumerate(reader.pages):
            page_number = index + 1
            warnings: List[str] = []
            errors: List[str] = []
            extracted = ""

            try:
                extracted = page.extract_text() or ""
            except Exception as e:
                warnings.append(f"Text extraction failed on page {page_number}: {str(e)}")

            cleaned_text = extracted.strip()

            if len(cleaned_text) >= self.min_text_length:
                source_type = "digital_text"
                requires_ocr = False
                page_text = cleaned_text
                rendered_img = None
            else:
                source_type = "requires_ocr"
                requires_ocr = True
                page_text = ""
                rendered_img = None

                if render_ocr_pages:
                    try:
                        rendered_img = self.render_single_page(path, page_number)
                    except Exception as e:
                        errors.append(f"Failed to render page {page_number}: {str(e)}")

            page_res = PageProcessingResult(
                page_number=page_number,
                source_type=source_type,
                text=page_text,
                requires_ocr=requires_ocr,
                warnings=warnings,
                errors=errors,
                image=rendered_img,
            )
            pages_data.append(page_res)

        doc_result = DocumentProcessingResult(pages=pages_data)
        return doc_result.to_dict()

    def render_single_page(
        self,
        pdf_path: Union[str, Path],
        page_number: int,
        dpi: Optional[int] = None,
    ) -> Optional[np.ndarray]:
        """Renders a single 1-indexed page of a PDF to an RGB numpy image array."""
        path = Path(pdf_path)
        if not path.is_file():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        render_dpi = dpi or self.dpi

        if HAS_PYMUPDF:
            doc = pymupdf.open(str(path))
            try:
                page_idx = page_number - 1
                if page_idx < 0 or page_idx >= len(doc):
                    raise ValueError(f"Page number {page_number} out of range for PDF with {len(doc)} pages.")
                page = doc.load_page(page_idx)
                pix = page.get_pixmap(dpi=render_dpi)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                if pix.n == 4:
                    import cv2
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                elif pix.n == 1:
                    import cv2
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                return img
            finally:
                doc.close()
        else:
            raise RuntimeError("PyMuPDF is required for PDF page rendering.")

    def render_pdf_to_images(
        self,
        pdf_path: Union[str, Path],
        page_numbers: Optional[List[int]] = None,
        dpi: Optional[int] = None,
    ) -> List[np.ndarray]:
        """
        Renders requested page numbers (or pages requiring OCR if omitted) to RGB numpy arrays.
        Returns empty list if file is invalid or no pages rendered.
        """
        path = Path(pdf_path)
        if not path.is_file():
            return []

        if page_numbers is None:
            try:
                doc_info = self.process_pdf(path, render_ocr_pages=False)
                page_numbers = [
                    p["page_number"] for p in doc_info.get("pages", []) if p.get("requires_ocr", False)
                ]
            except Exception:
                return []

        images = []
        for p_num in page_numbers:
            try:
                img = self.render_single_page(path, p_num, dpi=dpi)
                if img is not None:
                    images.append(img)
            except Exception:
                continue
        return images

    def is_scanned_pdf(self, pdf_path: Union[str, Path]) -> bool:
        """Determines whether all pages in a PDF require OCR."""
        res = self.process_pdf(pdf_path, render_ocr_pages=False)
        pages = res.get("pages", [])
        if not pages:
            return True
        return all(p.get("requires_ocr", False) for p in pages)

    def extract_digital_text(self, pdf_path: Union[str, Path]) -> str:
        """Extracts combined native digital text from all digital text pages in a PDF."""
        res = self.process_pdf(pdf_path, render_ocr_pages=False)
        texts = [p.get("text", "") for p in res.get("pages", []) if p.get("source_type") == "digital_text"]
        return "\n\n".join(t for t in texts if t)
