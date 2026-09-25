"""
Unit tests for Member 1 Stage 4 — Alt-Text and Diagram Understanding
Tests:
1. image with OCR + VLM
2. diagram with labels + relationships
3. OCR-only fallback
4. VLM-only fallback
5. both unavailable
6. empty/invalid input
7. no fabricated information
8. important OCR labels preserved
"""

import unittest
from equilearn.core.schemas import OCRResult, OCRWord, VLMResult, BoundingBox
from equilearn.vision.alt_text import AltTextGenerator


class TestAltTextGenerator(unittest.TestCase):
    """Test suite for AltTextGenerator accessibility description and diagram explanation logic."""

    def setUp(self) -> None:
        self.generator = AltTextGenerator()

    def test_1_image_with_ocr_plus_vlm(self) -> None:
        """1. Test image with both OCR and VLM data produces fused alt-text."""
        ocr = OCRResult(
            text="Solar System Model",
            blocks=[OCRWord("Sun", 0.99), OCRWord("Earth", 0.95)],
        )
        vlm = VLMResult(
            description="A diagram showing planetary orbits around the sun.",
            visual_elements=["Sun", "Planets", "Orbit paths"],
            relationships=["Planets orbit around central Sun"],
        )

        alt = self.generator.generate_alt_text(vlm_result=vlm, ocr_result=ocr)
        self.assertIn("A diagram showing planetary orbits", alt)
        self.assertIn("Visual elements: Sun, Planets, Orbit paths", alt)
        self.assertIn("Relationships: Planets orbit around central Sun", alt)
        self.assertIn("Text labels: Sun, Earth", alt)

    def test_2_diagram_with_labels_plus_relationships(self) -> None:
        """2. Test structured diagram extraction combining title, labels, components, connections, and spatial relationships."""
        ocr = OCRResult(
            text="Water Cycle Diagram",
            blocks=[
                OCRWord("Evaporation", 0.98),
                OCRWord("Condensation", 0.97),
                OCRWord("Precipitation", 0.96),
            ],
        )
        vlm = VLMResult(
            description="Diagram illustrating the three main stages of the water cycle.",
            visual_elements=["Evaporation node", "Condensation node", "Precipitation node"],
            relationships=[
                "Evaporation node points up to Condensation node",
                "Condensation node points right to Precipitation node",
            ],
        )
        context = {"title": "Figure 4.1: Water Cycle"}

        explanation = self.generator.generate_diagram_explanation(
            vlm_result=vlm, ocr_result=ocr, context=context
        )

        self.assertEqual(explanation["title"], "Figure 4.1: Water Cycle")
        self.assertEqual(explanation["labels"], ["Evaporation", "Condensation", "Precipitation"])
        self.assertEqual(explanation["components"], ["Evaporation node", "Condensation node", "Precipitation node"])
        self.assertEqual(len(explanation["connections"]), 2)
        self.assertEqual(len(explanation["spatial_relationships"]), 2)
        self.assertIn("Figure 4.1: Water Cycle", explanation["alt_text"])

    def test_3_ocr_only_fallback(self) -> None:
        """3. Test OCR-only fallback when VLM is unavailable/failed."""
        vlm_failed = VLMResult(description="", errors=["VLM model unavailable in environment"])
        ocr = OCRResult(
            text="Chapter 3: Cell Structure",
            blocks=[OCRWord("Nucleus", 0.98), OCRWord("Mitochondria", 0.97)],
        )

        alt = self.generator.generate_alt_text(vlm_result=vlm_failed, ocr_result=ocr)
        self.assertIn("Image containing text labels: Nucleus, Mitochondria", alt)

    def test_4_vlm_only_fallback(self) -> None:
        """4. Test VLM-only fallback when OCR is unavailable/failed."""
        ocr_failed = OCRResult(text="", blocks=[], errors=["OCR detected no text"])
        vlm = VLMResult(
            description="A photograph of a mountain range at sunset.",
            visual_elements=["mountains", "sunset sky"],
            relationships=["sun sets behind mountain peak"],
        )

        alt = self.generator.generate_alt_text(vlm_result=vlm, ocr_result=ocr_failed)
        self.assertIn("A photograph of a mountain range at sunset", alt)
        self.assertNotIn("Text labels:", alt)

    def test_5_both_unavailable(self) -> None:
        """5. Test when both VLM and OCR are unavailable/failed, returning empty alt-text."""
        vlm_failed = VLMResult(description="", errors=["VLM model unavailable"])
        ocr_failed = OCRResult(text="", blocks=[], errors=["OCR failed"])

        alt = self.generator.generate_alt_text(vlm_result=vlm_failed, ocr_result=ocr_failed)
        self.assertEqual(alt, "")

    def test_6_empty_invalid_input(self) -> None:
        """6. Test None and empty inputs return clean empty output."""
        self.assertEqual(self.generator.generate_alt_text(None, None), "")
        exp = self.generator.generate_diagram_explanation(None, None)
        self.assertEqual(exp["alt_text"], "")
        self.assertEqual(exp["labels"], [])
        self.assertEqual(exp["components"], [])

    def test_7_no_fabricated_information(self) -> None:
        """7. Verify no fake visual descriptions or text labels are fabricated."""
        vlm_empty = VLMResult(description="", visual_elements=[], relationships=[])
        ocr_empty = OCRResult(text="", blocks=[])

        alt = self.generator.generate_alt_text(vlm_result=vlm_empty, ocr_result=ocr_empty)
        self.assertEqual(alt, "")

    def test_8_important_ocr_labels_preserved(self) -> None:
        """8. Test that important OCR technical terms and formulas are preserved in output."""
        ocr = OCRResult(
            text="Photosynthesis Formula: 6CO2 + 6H2O -> C6H12O6 + 6O2",
            blocks=[
                OCRWord("Photosynthesis", 0.99),
                OCRWord("Formula", 0.98),
                OCRWord("6CO2", 0.95),
                OCRWord("6H2O", 0.95),
            ],
        )
        vlm = VLMResult(description="Chemical equation for plant energy conversion.")

        alt = self.generator.generate_alt_text(vlm_result=vlm, ocr_result=ocr)
        self.assertIn("Photosynthesis", alt)
        self.assertIn("Formula", alt)
        self.assertIn("6CO2", alt)
        self.assertIn("6H2O", alt)


if __name__ == "__main__":
    unittest.main()
