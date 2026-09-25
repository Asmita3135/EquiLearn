"""
Unit tests for evaluator module.
"""

from pathlib import Path
import sys
import unittest

# Ensure project root is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_speech.src.evaluator import calculate_wer


class TestEvaluator(unittest.TestCase):

    def test_identical_transcripts_zero_wer(self):
        """Test identical reference and prediction produces WER = 0.0."""
        ref = "hello world"
        hyp = "hello world"
        self.assertEqual(calculate_wer(ref, hyp), 0.0)

    def test_substitution_wer(self):
        """Test one word substitution out of two words produces WER = 0.5."""
        ref = "hello world"
        hyp = "hello word"
        self.assertEqual(calculate_wer(ref, hyp), 0.5)

    def test_deletion_wer(self):
        """Test one word deletion out of two words produces WER = 0.5."""
        ref = "hello world"
        hyp = "hello"
        self.assertEqual(calculate_wer(ref, hyp), 0.5)

    def test_insertion_wer(self):
        """Test one word insertion into two words produces WER = 0.5."""
        ref = "hello world"
        hyp = "hello world test"
        self.assertEqual(calculate_wer(ref, hyp), 0.5)

    def test_empty_reference_returns_none(self):
        """Test empty reference string returns None without crashing or division by zero."""
        self.assertIsNone(calculate_wer("", "hello world"))
        self.assertIsNone(calculate_wer("   ", "hello world"))
        self.assertIsNone(calculate_wer(None, "hello world"))

    def test_case_and_whitespace_insensitivity(self):
        """Test case and extra whitespace differences do not cause false errors."""
        ref = "  Hello World  "
        hyp = "hello world\n"
        self.assertEqual(calculate_wer(ref, hyp), 0.0)


if __name__ == "__main__":
    unittest.main()
