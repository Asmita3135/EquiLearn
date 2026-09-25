"""
Unit tests for Member 1: Vision & Document AI modules.
Pipeline Flow: PDF/Image → extraction → preprocessing → OCR → VLM → visual information → alt-text → evaluation
"""

import unittest
from pathlib import Path
import numpy as np
from PIL import Image

from equilearn.core.schemas import (
    BoundingBox,
    OCRWord,
    OCRResult,
    VLMResult,
    VisionOutputPayload,
    PageProcessingResult,
)
from equilearn.vision import (
    DocumentProcessor,
    ImagePreprocessor,
    OCREngine,
    VLMEngine,
    AltTextGenerator,
    VisionEvaluator,
    VisionPipeline,
)


class TestMember1Foundation(unittest.TestCase):
    """Test case suite for Member 1 foundation classes, image preprocessing, and schemas."""

    def test_schemas(self):
        page_res = PageProcessingResult(
            page_number=1,
            source_type="requires_ocr",
            text="",
            requires_ocr=True,
            warnings=["sample warning"],
            errors=[],
        )
        d = page_res.to_dict()
        self.assertEqual(d["page_number"], 1)
        self.assertEqual(d["source_type"], "requires_ocr")
        self.assertTrue(d["requires_ocr"])
        self.assertEqual(d["warnings"], ["sample warning"])

        bbox = BoundingBox(x_min=0.0, y_min=0.0, x_max=10.0, y_max=10.0)
        word = OCRWord(text="test", confidence=0.95, bbox=bbox)
        ocr_res = OCRResult(raw_text="test", words=[word], average_confidence=0.95)
        vlm_res = VLMResult(description="A sample diagram")
        payload = VisionOutputPayload(
            document_id="doc1",
            extracted_text="test",
            ocr_result=ocr_res,
            vlm_result=vlm_res,
            alt_text="A sample diagram showing test",
        )

        self.assertEqual(payload.document_id, "doc1")
        self.assertEqual(payload.ocr_result.average_confidence, 0.95)
        self.assertEqual(payload.vlm_result.description, "A sample diagram")

    def test_document_processor(self):
        processor = DocumentProcessor()
        prd_path = "EquiLearn_Core_AI_ML_PRD.pdf"
        if Path(prd_path).exists():
            res = processor.process_pdf(prd_path)
            self.assertIn("pages", res)
            self.assertGreater(len(res["pages"]), 0)
            self.assertEqual(res["pages"][0]["source_type"], "digital_text")
            self.assertFalse(processor.is_scanned_pdf(prd_path))
            self.assertIn("EquiLearn", processor.extract_digital_text(prd_path))

    def test_image_preprocessor_pipeline(self):
        preprocessor = ImagePreprocessor(max_dim=100)
        # Create a test synthetic RGB image (200x200 pixels)
        arr = np.zeros((200, 200, 3), dtype=np.uint8)
        arr[50:150, 50:150] = 255  # white square
        orig_copy = arr.copy()

        # Run complete preprocessing pipeline
        processed = preprocessor.preprocess_pipeline(arr)
        self.assertIsInstance(processed, np.ndarray)
        # Verify resize down to max_dim=100
        self.assertLessEqual(max(processed.shape[:2]), 100)
        # Verify original input array was preserved (not mutated in place)
        np.testing.assert_array_equal(arr, orig_copy)

    def test_image_preprocessor_pil_and_grayscale(self):
        preprocessor = ImagePreprocessor()
        # Test PIL Image input
        pil_img = Image.new("RGB", (150, 150), color="white")
        res_pil = preprocessor.resize(pil_img, max_dim=100)
        self.assertIsInstance(res_pil, Image.Image)
        self.assertEqual(res_pil.size, (100, 100))

        # Test Grayscale numpy array input
        gray_arr = np.zeros((100, 100), dtype=np.uint8)
        denoised = preprocessor.denoise(gray_arr)
        self.assertEqual(denoised.shape, (100, 100))

    def test_image_preprocessor_invalid_inputs(self):
        preprocessor = ImagePreprocessor()

        # Test None input
        with self.assertRaises(ValueError):
            preprocessor.preprocess_pipeline(None)

        # Test non-existent file path
        with self.assertRaises(FileNotFoundError):
            preprocessor.preprocess_pipeline("non_existent_image.png")

        # Test invalid input type
        with self.assertRaises(ValueError):
            preprocessor.preprocess_pipeline(12345)

        # Test empty numpy array
        with self.assertRaises(ValueError):
            preprocessor.preprocess_pipeline(np.array([]))

    def test_ocr_engine_stub(self):
        engine = OCREngine(confidence_threshold=0.8)
        result = engine.process_image("dummy_image")
        self.assertIsInstance(result, OCRResult)
        self.assertTrue(result.is_fallback_triggered)
        self.assertEqual(result.engine_used, "tesseract")

    def test_vlm_engine_stub(self):
        engine = VLMEngine()
        result = engine.analyze_visual("dummy_image")
        self.assertIsInstance(result, VLMResult)

    def test_alt_text_generator(self):
        generator = AltTextGenerator()
        vlm_res = VLMResult(description="Diagram of solar system")
        alt_text = generator.generate_alt_text(vlm_res)
        self.assertEqual(alt_text, "Diagram of solar system")

    def test_evaluator(self):
        evaluator = VisionEvaluator()
        self.assertEqual(evaluator.calculate_cer("test", "test"), 0.0)
        self.assertEqual(evaluator.calculate_bleu("test", ["test"]), 1.0)
        rouge = evaluator.calculate_rouge("test", "test")
        self.assertIn("rougeL", rouge)

    def test_vision_pipeline_stub(self):
        pipeline = VisionPipeline()
        prd_path = "EquiLearn_Core_AI_ML_PRD.pdf"
        if Path(prd_path).exists():
            payload = pipeline.process_document(prd_path)
            self.assertIsInstance(payload, VisionOutputPayload)
            self.assertEqual(payload.document_id, "EquiLearn_Core_AI_ML_PRD.pdf")
            self.assertIn("EquiLearn", payload.extracted_text)


if __name__ == "__main__":
    unittest.main()
