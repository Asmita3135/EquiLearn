"""
Unit tests for M1 Stage 2 — OCR Engine (PaddleOCR + Tesseract Fallback)
Tests:
1. normal PaddleOCR
2. high confidence (no fallback)
3. low confidence → Tesseract fallback
4. mixed confidence
5. empty OCR (no fabricated text)
6. Tesseract unavailable/fails
7. malformed/invalid image
"""

import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from equilearn.core.schemas import OCRResult, OCRWord, BoundingBox
from equilearn.vision.ocr_engine import OCREngine


class TestOCREngine(unittest.TestCase):
    """Test suite for primary PaddleOCR execution, confidence thresholding, and Tesseract fallback."""

    def setUp(self) -> None:
        self.engine = OCREngine(confidence_threshold=0.75)
        self.blank_image = np.ones((100, 100, 3), dtype=np.uint8) * 255

    def _create_mock_paddle_result(self, lines: list):
        """Helper to create structured PaddleOCR return format."""
        # PaddleOCR returns [[[bbox, (text, conf)], ...]]
        res_lines = []
        for text, conf, bbox in lines:
            x1, y1, x2, y2 = bbox
            poly = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            res_lines.append([poly, (text, conf)])
        return [res_lines]

    def test_1_normal_paddle_ocr(self) -> None:
        """1. Test normal PaddleOCR execution returning structured text, blocks, and confidence."""
        mock_paddle = MagicMock()
        mock_paddle.ocr.return_value = self._create_mock_paddle_result([
            ("EquiLearn", 0.95, [10, 10, 50, 30]),
            ("Accessibility", 0.90, [60, 10, 120, 30]),
        ])

        with patch.object(self.engine, "_get_paddle_instance", return_value=mock_paddle):
            result = self.engine.run_paddle_ocr(self.blank_image)
            self.assertIsInstance(result, OCRResult)
            self.assertEqual(result.text, "EquiLearn Accessibility")
            self.assertEqual(len(result.blocks), 2)
            self.assertAlmostEqual(result.average_confidence, 0.925, places=3)
            self.assertEqual(result.engine_used, "paddleocr")
            self.assertFalse(result.fallback_used)

    def test_2_high_confidence_no_fallback(self) -> None:
        """2. Test high confidence result (>= 0.75) returns primary result without triggering fallback."""
        mock_paddle = MagicMock()
        mock_paddle.ocr.return_value = self._create_mock_paddle_result([
            ("High Confidence Text", 0.92, [10, 10, 100, 30]),
        ])

        with patch.object(self.engine, "_get_paddle_instance", return_value=mock_paddle):
            with patch.object(self.engine, "run_tesseract_fallback") as mock_fallback:
                result = self.engine.process_image(self.blank_image)
                mock_fallback.assert_not_called()
                self.assertEqual(result.text, "High Confidence Text")
                self.assertFalse(result.fallback_used)
                self.assertEqual(result.engine_used, "paddleocr")

    def test_3_low_confidence_triggers_tesseract_fallback(self) -> None:
        """3. Test low confidence (< 0.75) triggers Tesseract fallback and preserves primary result."""
        mock_paddle = MagicMock()
        mock_paddle.ocr.return_value = self._create_mock_paddle_result([
            ("Low Conf Text", 0.40, [10, 10, 100, 30]),
        ])

        fallback_result = OCRResult(
            text="Fallback Recovered Text",
            blocks=[
                OCRWord(
                    text="Fallback Recovered Text",
                    confidence=0.88,
                    bbox=BoundingBox(10, 10, 100, 30),
                )
            ],
            average_confidence=0.88,
            engine_used="tesseract",
            fallback_used=True,
        )

        with patch.object(self.engine, "_get_paddle_instance", return_value=mock_paddle):
            with patch.object(self.engine, "run_tesseract_fallback", return_value=fallback_result):
                result = self.engine.process_image(self.blank_image)
                self.assertTrue(result.fallback_used)
                self.assertIsNotNone(result.fallback_reason)
                self.assertIn("0.4000", result.fallback_reason)
                self.assertEqual(result.text, "Fallback Recovered Text")
                self.assertIsNotNone(result.primary_result)
                self.assertEqual(result.primary_result.text, "Low Conf Text")

    def test_4_mixed_confidence(self) -> None:
        """4. Test mixed confidence blocks where average is below threshold triggers fallback."""
        mock_paddle = MagicMock()
        mock_paddle.ocr.return_value = self._create_mock_paddle_result([
            ("Good Block", 0.95, [10, 10, 50, 30]),
            ("Poor Block", 0.35, [60, 10, 100, 30]),  # avg = 0.65 < 0.75
        ])

        fallback_result = OCRResult(
            text="Good Block Poor Block Refined",
            blocks=[
                OCRWord(text="Good Block", confidence=0.92, bbox=BoundingBox(10, 10, 50, 30)),
                OCRWord(text="Poor Block Refined", confidence=0.85, bbox=BoundingBox(60, 10, 120, 30)),
            ],
            average_confidence=0.885,
            engine_used="tesseract",
            fallback_used=True,
        )

        with patch.object(self.engine, "_get_paddle_instance", return_value=mock_paddle):
            with patch.object(self.engine, "run_tesseract_fallback", return_value=fallback_result):
                result = self.engine.process_image(self.blank_image)
                self.assertTrue(result.fallback_used)
                self.assertAlmostEqual(result.primary_result.average_confidence, 0.65)
                self.assertEqual(result.text, "Good Block Poor Block Refined")

    def test_5_empty_ocr(self) -> None:
        """5. Test image with no text returns empty text/blocks and 0 confidence without text fabrication."""
        mock_paddle = MagicMock()
        mock_paddle.ocr.return_value = [[]]

        fallback_result = OCRResult(
            text="",
            blocks=[],
            average_confidence=0.0,
            engine_used="tesseract",
            fallback_used=True,
        )

        with patch.object(self.engine, "_get_paddle_instance", return_value=mock_paddle):
            with patch.object(self.engine, "run_tesseract_fallback", return_value=fallback_result):
                result = self.engine.process_image(self.blank_image)
                self.assertEqual(result.text, "")
                self.assertEqual(result.blocks, [])
                self.assertEqual(result.average_confidence, 0.0)

    def test_6_tesseract_unavailable_or_fails(self) -> None:
        """6. Test missing or failing Tesseract engine handles gracefully without crashing."""
        mock_paddle = MagicMock()
        mock_paddle.ocr.return_value = self._create_mock_paddle_result([
            ("Marginal Text", 0.60, [10, 10, 50, 30]),
        ])

        failing_fallback = OCRResult(
            text="",
            blocks=[],
            average_confidence=0.0,
            engine_used="tesseract",
            fallback_used=True,
            errors=["Tesseract executable not found on system path."],
        )

        with patch.object(self.engine, "_get_paddle_instance", return_value=mock_paddle):
            with patch.object(self.engine, "run_tesseract_fallback", return_value=failing_fallback):
                result = self.engine.process_image(self.blank_image)
                self.assertTrue(result.fallback_used)
                self.assertEqual(result.text, "Marginal Text")
                self.assertIn("Tesseract executable not found", result.errors[0])

    def test_7_malformed_or_invalid_image(self) -> None:
        """7. Test malformed or invalid image inputs return empty result with recorded error."""
        res_none = self.engine.process_image(None)
        self.assertEqual(res_none.text, "")
        self.assertEqual(res_none.average_confidence, 0.0)
        self.assertIn("cannot be None", res_none.errors[0])

        res_invalid_path = self.engine.process_image("non_existent_image.png")
        self.assertEqual(res_invalid_path.text, "")
        self.assertEqual(res_invalid_path.average_confidence, 0.0)
        self.assertIn("not found", res_invalid_path.errors[0])

        res_empty_arr = self.engine.process_image(np.array([]))
        self.assertEqual(res_empty_arr.text, "")
        self.assertEqual(res_empty_arr.average_confidence, 0.0)
        self.assertIn("array is empty", res_empty_arr.errors[0])


if __name__ == "__main__":
    unittest.main()
