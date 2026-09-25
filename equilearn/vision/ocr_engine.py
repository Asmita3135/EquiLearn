"""
M1-STAGE 3 — OCR & Fallback Engine Implementation
Primary: PaddleOCR. Fallback: Tesseract.
Pipeline Flow: preprocessing → OCR → bounding boxes & confidence scores
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np
from PIL import Image

from equilearn.core.schemas import OCRResult, OCRWord, BoundingBox

try:
    import pytesseract
    from pytesseract import Output
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

try:
    from paddleocr import PaddleOCR
    HAS_PADDLEOCR = True
except ImportError:
    HAS_PADDLEOCR = False


class OCREngine:
    """Class for primary PaddleOCR execution with Tesseract fallback and confidence handling."""

    def __init__(
        self,
        confidence_threshold: float = 0.75,
        lang: str = "en",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.lang = lang
        self.config = config or {}
        self._paddle_ocr_instance: Optional[Any] = None

    def _get_paddle_instance(self) -> Any:
        if self._paddle_ocr_instance is None and HAS_PADDLEOCR:
            try:
                self._paddle_ocr_instance = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                    show_log=False,
                )
            except Exception:
                self._paddle_ocr_instance = None
        return self._paddle_ocr_instance

    def _to_numpy(self, image: Any) -> np.ndarray:
        """Converts image input to a valid 3-channel RGB numpy array copy."""
        if image is None:
            raise ValueError("Image input cannot be None.")

        if isinstance(image, (str, Path)):
            path = Path(image)
            if not path.is_file():
                raise FileNotFoundError(f"Image file not found: {image}")
            import cv2
            arr = cv2.imread(str(path))
            if arr is None:
                raise ValueError(f"Could not read image file: {image}")
            return cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        elif isinstance(image, Image.Image):
            return np.array(image.convert("RGB"))
        elif isinstance(image, np.ndarray):
            if image.size == 0:
                raise ValueError("Input image array is empty.")
            if len(image.shape) == 2:
                import cv2
                return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif len(image.shape) == 3 and image.shape[2] == 4:
                import cv2
                return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            return image.copy()
        else:
            raise ValueError(f"Unsupported image format: {type(image)}")

    def run_paddle_ocr(self, image: Any) -> OCRResult:
        """Runs primary PaddleOCR text detection and recognition."""
        warnings: List[str] = []
        errors: List[str] = []

        try:
            arr = self._to_numpy(image)
        except (FileNotFoundError, ValueError) as exc:
            errors.append(str(exc))
            return OCRResult(
                text="",
                blocks=[],
                average_confidence=0.0,
                engine_used="paddleocr",
                warnings=warnings,
                errors=errors,
            )

        paddle_inst = self._get_paddle_instance()
        if not HAS_PADDLEOCR and paddle_inst is None:
            warnings.append("PaddleOCR runtime is not installed or available in this environment.")
            return OCRResult(
                text="",
                blocks=[],
                average_confidence=0.0,
                engine_used="paddleocr",
                warnings=warnings,
                errors=errors,
            )

        if paddle_inst is None:
            warnings.append("PaddleOCR instance initialization failed.")
            return OCRResult(
                text="",
                blocks=[],
                average_confidence=0.0,
                engine_used="paddleocr",
                warnings=warnings,
                errors=errors,
            )

        try:
            results = paddle_inst.ocr(arr, cls=True)
        except Exception as exc:
            errors.append(f"PaddleOCR execution error: {str(exc)}")
            return OCRResult(
                text="",
                blocks=[],
                average_confidence=0.0,
                engine_used="paddleocr",
                warnings=warnings,
                errors=errors,
            )

        blocks: List[OCRWord] = []
        conf_scores: List[float] = []

        if results and isinstance(results, list):
            page_res = results[0] if len(results) > 0 and isinstance(results[0], list) else results
            for line in page_res:
                if not line or len(line) < 2:
                    continue
                bbox_points, (text_str, conf) = line[0], line[1]
                if not text_str or not text_str.strip():
                    continue

                xs = [p[0] for p in bbox_points]
                ys = [p[1] for p in bbox_points]
                bbox = BoundingBox(x_min=min(xs), y_min=min(ys), x_max=max(xs), y_max=max(ys))
                conf_val = float(conf)

                blocks.append(OCRWord(text=text_str.strip(), confidence=conf_val, bbox=bbox))
                conf_scores.append(conf_val)

        avg_conf = float(np.mean(conf_scores)) if conf_scores else 0.0
        combined_text = " ".join([b.text for b in blocks])

        return OCRResult(
            text=combined_text,
            blocks=blocks,
            average_confidence=avg_conf,
            fallback_used=False,
            engine_used="paddleocr",
            warnings=warnings,
            errors=errors,
        )

    def run_tesseract_fallback(self, image: Any) -> OCRResult:
        """Runs Tesseract OCR as a fallback engine when PaddleOCR confidence threshold is unmet."""
        warnings: List[str] = []
        errors: List[str] = []

        try:
            arr = self._to_numpy(image)
        except (FileNotFoundError, ValueError) as exc:
            errors.append(str(exc))
            return OCRResult(
                text="",
                blocks=[],
                average_confidence=0.0,
                engine_used="tesseract",
                fallback_used=True,
                warnings=warnings,
                errors=errors,
            )

        if not HAS_PYTESSERACT:
            errors.append("Tesseract fallback unavailable: pytesseract module not installed.")
            return OCRResult(
                text="",
                blocks=[],
                average_confidence=0.0,
                engine_used="tesseract",
                fallback_used=True,
                warnings=warnings,
                errors=errors,
            )

        try:
            pil_img = Image.fromarray(arr)
            data = pytesseract.image_to_data(pil_img, output_type=Output.DICT)
        except Exception as exc:
            errors.append(f"Tesseract execution failed: {str(exc)}")
            return OCRResult(
                text="",
                blocks=[],
                average_confidence=0.0,
                engine_used="tesseract",
                fallback_used=True,
                warnings=warnings,
                errors=errors,
            )

        blocks: List[OCRWord] = []
        conf_scores: List[float] = []

        n_boxes = len(data.get("text", []))
        for i in range(n_boxes):
            word_text = data["text"][i].strip()
            raw_conf = data["conf"][i]

            if word_text and raw_conf > 0:
                x = float(data["left"][i])
                y = float(data["top"][i])
                w = float(data["width"][i])
                h = float(data["height"][i])
                conf_val = float(raw_conf) / 100.0

                bbox = BoundingBox(x_min=x, y_min=y, x_max=x + w, y_max=y + h)
                blocks.append(OCRWord(text=word_text, confidence=conf_val, bbox=bbox))
                conf_scores.append(conf_val)

        avg_conf = float(np.mean(conf_scores)) if conf_scores else 0.0
        combined_text = " ".join([b.text for b in blocks])

        return OCRResult(
            text=combined_text,
            blocks=blocks,
            average_confidence=avg_conf,
            fallback_used=True,
            engine_used="tesseract",
            warnings=warnings,
            errors=errors,
        )

    def process_image(self, image: Any) -> OCRResult:
        """Executes primary OCR and automatically triggers Tesseract fallback if needed."""
        primary_result = self.run_paddle_ocr(image)

        if primary_result.average_confidence >= self.confidence_threshold and len(primary_result.blocks) > 0:
            return primary_result

        # Determine fallback reason
        if primary_result.errors:
            reason = f"Primary OCR error: {primary_result.errors[0]}"
        elif len(primary_result.blocks) == 0:
            reason = "Primary OCR detected no text blocks"
        else:
            reason = (
                f"Average confidence ({primary_result.average_confidence:.4f}) "
                f"below threshold ({self.confidence_threshold:.4f})"
            )

        fallback_result = self.run_tesseract_fallback(image)
        fallback_result.fallback_used = True
        fallback_result.fallback_reason = reason
        fallback_result.primary_result = primary_result

        # Transfer primary warnings if present
        for w in primary_result.warnings:
            if w not in fallback_result.warnings:
                fallback_result.warnings.append(w)

        # If fallback produced no text or failed, but primary had text, return primary with fallback noted
        if not fallback_result.text.strip() and primary_result.text.strip():
            primary_result.fallback_used = True
            primary_result.fallback_reason = f"{reason} (Tesseract fallback yielded no text)"
            for e in fallback_result.errors:
                if e not in primary_result.errors:
                    primary_result.errors.append(e)
            for w in fallback_result.warnings:
                if w not in primary_result.warnings:
                    primary_result.warnings.append(w)
            return primary_result

        return fallback_result
