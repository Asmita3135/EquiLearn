"""
Unit tests for M1 Stage 8 — Evaluation Module (VisionEvaluator)
Tests:
- CER calculation
- BLEU calculation
- ROUGE-1/2/L calculation
- OCR confidence statistics
- Hallucination tracking
- Benchmark runner and EvaluationReport generation
"""

import unittest
from equilearn.core.schemas import OCRResult, OCRWord, VLMResult, BoundingBox
from equilearn.vision.evaluator import (
    VisionEvaluator,
    HumanRating,
    HallucinationCase,
    EvaluationReport,
)
from equilearn.vision.pipeline import VisionPipeline


class TestVisionEvaluator(unittest.TestCase):
    """Test suite for VisionEvaluator metrics, CER, BLEU, ROUGE, and benchmark runners."""

    def setUp(self) -> None:
        self.evaluator = VisionEvaluator()

    def test_cer_calculation(self) -> None:
        """Tests Character Error Rate (CER) calculation."""
        # Exact match
        self.assertEqual(self.evaluator.calculate_cer("EquiLearn", "EquiLearn"), 0.0)
        # 1 substitution in 9 chars -> 1/9 ~ 0.1111
        cer = self.evaluator.calculate_cer("EquiLearm", "EquiLearn")
        self.assertAlmostEqual(cer, 1 / 9.0, places=4)
        # Empty hypothesis on non-empty reference -> 1.0
        self.assertEqual(self.evaluator.calculate_cer("", "EquiLearn"), 1.0)
        # Both empty -> 0.0
        self.assertEqual(self.evaluator.calculate_cer("", ""), 0.0)

    def test_bleu_calculation(self) -> None:
        """Tests sentence BLEU calculation."""
        ref = "A diagram showing planetary orbits around the sun."
        cand_exact = "A diagram showing planetary orbits around the sun."
        cand_partial = "A diagram showing planetary orbits."
        cand_empty = ""

        self.assertAlmostEqual(self.evaluator.calculate_bleu(cand_exact, [ref]), 1.0, places=4)
        self.assertGreater(self.evaluator.calculate_bleu(cand_partial, [ref]), 0.0)
        self.assertEqual(self.evaluator.calculate_bleu(cand_empty, [ref]), 0.0)

    def test_rouge_calculation(self) -> None:
        """Tests ROUGE-1, ROUGE-2, and ROUGE-L calculation."""
        ref = "Diagram illustrating water cycle stages."
        cand = "Diagram illustrating key water cycle stages."

        rouge = self.evaluator.calculate_rouge(cand, ref)
        self.assertIn("rouge1", rouge)
        self.assertIn("rouge2", rouge)
        self.assertIn("rougeL", rouge)
        self.assertGreater(rouge["rouge1"], 0.7)
        self.assertGreater(rouge["rougeL"], 0.7)

    def test_ocr_confidence_statistics(self) -> None:
        """Tests OCR confidence statistics calculation."""
        ocr = OCRResult(
            text="Word1 Word2",
            blocks=[
                OCRWord("Word1", 0.90, BoundingBox(0, 0, 10, 10)),
                OCRWord("Word2", 0.80, BoundingBox(10, 0, 20, 10)),
            ],
        )

        stats = self.evaluator.evaluate_ocr_result(ocr)
        self.assertEqual(stats["block_count"], 2)
        self.assertAlmostEqual(stats["average_confidence"], 0.85)
        self.assertEqual(stats["min_confidence"], 0.80)
        self.assertEqual(stats["max_confidence"], 0.90)

    def test_hallucination_detection(self) -> None:
        """Tests tracking of hallucinated/fabricated visual elements."""
        vlm = VLMResult(
            description="Cell diagram",
            visual_elements=["nucleus", "mitochondria", "alien_spaceship"],
        )
        gt_elements = ["nucleus", "mitochondria", "ribosome"]

        h_case = self.evaluator.detect_hallucinations(vlm, gt_elements)
        self.assertIn("alien_spaceship", h_case.fabricated_elements)
        self.assertEqual(h_case.severity, "medium")

    def test_benchmark_runner(self) -> None:
        """Tests running evaluation benchmark suite across 10 val + 5 unseen test samples."""
        pipeline = VisionPipeline()
        report = self.evaluator.evaluate_benchmark(pipeline, is_real_execution=False)

        self.assertIsInstance(report, EvaluationReport)
        self.assertEqual(report.sample_count, 15)
        self.assertEqual(report.validation_count, 10)
        self.assertEqual(report.unseen_count, 5)
        self.assertFalse(report.is_real_execution)
        self.assertIn("FRAMEWORK EVALUATION", report.execution_notes)


if __name__ == "__main__":
    unittest.main()
