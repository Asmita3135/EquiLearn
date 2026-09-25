"""
Unit tests for Member 1 Stage 3 — VLM Visual Understanding
Tests:
1. normal VLM response
2. objects/scenes
3. diagram/relationships
4. empty/invalid image
5. model unavailable (real environment check)
6. inference failure
7. OCR + VLM result preservation (separate independent payloads)
"""

import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from equilearn.core.schemas import OCRResult, VLMResult, VisionOutputPayload
from equilearn.vision.vlm_engine import (
    VLMEngine,
    QwenVLLocalAdapter,
    MockVLMAdapter,
)


class TestVLMEngine(unittest.TestCase):
    """Test suite for VLMEngine visual understanding, adapter patterns, and schema preservation."""

    def setUp(self) -> None:
        self.blank_image = np.ones((100, 100, 3), dtype=np.uint8) * 255

    def test_1_normal_vlm_response(self) -> None:
        """1. Test normal VLM response containing description, visual_elements, and relationships."""
        adapter = MockVLMAdapter(
            description="A high school physics diagram.",
            visual_elements=["circuit", "battery", "resistor"],
            relationships=["resistor is connected in series with battery"],
        )
        engine = VLMEngine(adapter=adapter)
        result = engine.analyze_visual(self.blank_image)

        self.assertIsInstance(result, VLMResult)
        self.assertEqual(result.description, "A high school physics diagram.")
        self.assertEqual(result.visual_elements, ["circuit", "battery", "resistor"])
        self.assertEqual(result.relationships, ["resistor is connected in series with battery"])
        self.assertEqual(result.errors, [])

        # Verify to_dict output format
        d = result.to_dict()
        self.assertIn("description", d)
        self.assertIn("visual_elements", d)
        self.assertIn("relationships", d)
        self.assertIn("warnings", d)
        self.assertIn("errors", d)

    def test_2_objects_scenes(self) -> None:
        """2. Test visual understanding of objects and scene descriptions."""
        adapter = MockVLMAdapter(
            description="A photo of a classroom with students.",
            visual_elements=["students", "desks", "blackboard", "teacher"],
            relationships=["teacher stands in front of blackboard"],
        )
        engine = VLMEngine(adapter=adapter)
        result = engine.analyze_visual(self.blank_image)

        self.assertEqual(len(result.visual_elements), 4)
        self.assertIn("students", result.visual_elements)
        self.assertIn("blackboard", result.visual_elements)

    def test_3_diagram_relationships(self) -> None:
        """3. Test diagram parsing and spatial relationship extraction."""
        adapter = MockVLMAdapter(
            description="Flowchart depicting water cycle stages.",
            visual_elements=["Evaporation node", "Condensation node", "Precipitation node"],
            relationships=[
                "Evaporation node points up to Condensation node",
                "Condensation node points right to Precipitation node",
            ],
        )
        engine = VLMEngine(adapter=adapter)
        result = engine.analyze_visual(self.blank_image)

        self.assertEqual(len(result.relationships), 2)
        self.assertIn("Evaporation node points up to Condensation node", result.relationships)

    def test_4_empty_invalid_image(self) -> None:
        """4. Test empty/invalid image inputs return structured errors without hallucinating output."""
        engine = VLMEngine()

        res_none = engine.analyze_visual(None)
        self.assertEqual(res_none.description, "")
        self.assertEqual(res_none.visual_elements, [])
        self.assertIn("cannot be None", res_none.errors[0])

        res_file = engine.analyze_visual("non_existent_image.png")
        self.assertEqual(res_file.description, "")
        self.assertIn("not found", res_file.errors[0])

        res_empty = engine.analyze_visual(np.array([]))
        self.assertEqual(res_empty.description, "")
        self.assertIn("array is empty", res_empty.errors[0])

    def test_5_model_unavailable_real_environment(self) -> None:
        """5. REAL UNMOCKED TEST: Test QwenVLLocalAdapter in current host environment (PyTorch/CUDA missing)."""
        adapter = QwenVLLocalAdapter()
        engine = VLMEngine(adapter=adapter)

        # Real execution on host system without mocking
        result = engine.analyze_visual(self.blank_image)
        self.assertEqual(result.description, "")
        self.assertEqual(result.visual_elements, [])
        self.assertEqual(result.relationships, [])
        self.assertGreater(len(result.errors), 0)
        self.assertIn("Model execution unsupported", result.errors[0])

    def test_6_inference_failure(self) -> None:
        """6. Test handling of VLM inference exception returns structured error payload."""
        adapter = MockVLMAdapter(raise_error=True)
        engine = VLMEngine(adapter=adapter)
        result = engine.analyze_visual(self.blank_image)

        self.assertEqual(result.description, "")
        self.assertEqual(result.visual_elements, [])
        self.assertEqual(result.errors, ["Simulated VLM inference failure."])

    def test_7_ocr_plus_vlm_result_preservation(self) -> None:
        """7. Test that VisionOutputPayload preserves both OCR and VLM outputs independently."""
        ocr_res = OCRResult(text="Diagram 1: Photosynthesis", average_confidence=0.96)
        vlm_res = VLMResult(
            description="Diagram illustrating light reactions in photosynthesis.",
            visual_elements=["chloroplast", "sunlight_arrow", "water_molecule"],
            relationships=["sunlight_arrow points to chloroplast"],
        )

        payload = VisionOutputPayload(
            document_id="doc_test.pdf",
            extracted_text="Diagram 1: Photosynthesis",
            ocr_result=ocr_res,
            vlm_result=vlm_res,
        )

        d = payload.to_dict()
        self.assertIn("ocr", d)
        self.assertIn("visual", d)

        # OCR output must not be overwritten by VLM
        self.assertEqual(d["ocr"]["text"], "Diagram 1: Photosynthesis")
        self.assertEqual(d["ocr"]["average_confidence"], 0.96)

        # VLM output must remain separate and independent
        self.assertEqual(d["visual"]["description"], "Diagram illustrating light reactions in photosynthesis.")
        self.assertEqual(d["visual"]["visual_elements"], ["chloroplast", "sunlight_arrow", "water_molecule"])


if __name__ == "__main__":
    unittest.main()
