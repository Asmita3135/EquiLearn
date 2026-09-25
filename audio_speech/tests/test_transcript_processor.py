"""
Unit tests for transcript_processor module.
"""

from pathlib import Path
import sys
import unittest

# Ensure project root is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_speech.src.transcript_processor import (
    process_transcript_segments,
    process_transcript,
    flag_uncertain_segments,
)


class TestTranscriptProcessor(unittest.TestCase):

    def test_normal_segments_conversion(self):
        """Test processing of normal Whisper segments."""
        raw_segments = [
            {"start": 0.0, "end": 3.25, "text": "  Hello everyone  "},
            {"start": 3.25, "end": 6.80, "text": "Today we will learn math."},
        ]

        result = process_transcript_segments(raw_segments)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {"start": 0.0, "end": 3.25, "text": "Hello everyone"})
        self.assertEqual(result[1], {"start": 3.25, "end": 6.80, "text": "Today we will learn math."})

    def test_whitespace_cleaning(self):
        """Test whitespace stripping from segment text."""
        raw_segments = [
            {"start": 1.0, "end": 2.0, "text": "\n\t  Welcome to EquiLearn!   \n"}
        ]
        result = process_transcript_segments(raw_segments)
        self.assertEqual(result[0]["text"], "Welcome to EquiLearn!")

    def test_empty_segments_ignored(self):
        """Test ignoring empty or whitespace-only segments."""
        raw_segments = [
            {"start": 0.0, "end": 1.0, "text": ""},
            {"start": 1.0, "end": 2.0, "text": "   "},
            {"start": 2.0, "end": 3.0, "text": None},
            {"start": 3.0, "end": 4.0, "text": "Valid segment"},
        ]
        result = process_transcript_segments(raw_segments)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "Valid segment")

    def test_segment_order_preserved(self):
        """Test that original segment order is strictly preserved."""
        raw_segments = [
            {"start": 0.0, "end": 2.0, "text": "First segment"},
            {"start": 2.0, "end": 4.0, "text": "Second segment"},
            {"start": 4.0, "end": 6.0, "text": "Third segment"},
        ]
        result = process_transcript_segments(raw_segments)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["text"], "First segment")
        self.assertEqual(result[1]["text"], "Second segment")
        self.assertEqual(result[2]["text"], "Third segment")

    def test_empty_input_list(self):
        """Test handling of empty input list or None."""
        self.assertEqual(process_transcript_segments([]), [])
        self.assertEqual(process_transcript_segments(None), [])

    def test_full_process_transcript(self):
        """Test full asr_result dict processing."""
        raw_asr_result = {
            "text": "Hello world",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": " Hello world "}
            ],
        }
        res = process_transcript(raw_asr_result)

        self.assertEqual(res["text"], "Hello world")
        self.assertEqual(res["language"], "en")
        self.assertEqual(len(res["segments"]), 1)
        self.assertEqual(res["segments"][0]["text"], "Hello world")

    def test_flag_uncertain_segments_low_prob(self):
        """Low no_speech_prob -> needs_review=False."""
        segments = [{"start": 0.0, "end": 2.0, "text": "Clear speech", "no_speech_prob": 0.1}]
        res = flag_uncertain_segments(segments, threshold=0.5)
        self.assertFalse(res[0]["needs_review"])

    def test_flag_uncertain_segments_high_prob(self):
        """High no_speech_prob -> needs_review=True."""
        segments = [{"start": 2.0, "end": 4.0, "text": "Uncertain text", "no_speech_prob": 0.8}]
        res = flag_uncertain_segments(segments, threshold=0.5)
        self.assertTrue(res[0]["needs_review"])

    def test_flag_uncertain_segments_exact_threshold(self):
        """Exact threshold no_speech_prob == 0.5 -> needs_review=True."""
        segments = [{"start": 4.0, "end": 6.0, "text": "Boundary text", "no_speech_prob": 0.5}]
        res = flag_uncertain_segments(segments, threshold=0.5)
        self.assertTrue(res[0]["needs_review"])

    def test_flag_uncertain_segments_missing_prob(self):
        """Missing no_speech_prob is handled safely -> defaults to 0.0, needs_review=False."""
        segments = [{"start": 0.0, "end": 1.0, "text": "No prob field"}]
        res = flag_uncertain_segments(segments, threshold=0.5)
        self.assertEqual(res[0]["no_speech_prob"], 0.0)
        self.assertFalse(res[0]["needs_review"])

    def test_flag_uncertain_segments_empty_input(self):
        """Empty input list returns empty list."""
        self.assertEqual(flag_uncertain_segments([]), [])
        self.assertEqual(flag_uncertain_segments(None), [])

    def test_flag_uncertain_segments_order_preserved(self):
        """Original segment order is preserved."""
        segments = [
            {"start": 0.0, "end": 1.0, "text": "A", "no_speech_prob": 0.1},
            {"start": 1.0, "end": 2.0, "text": "B", "no_speech_prob": 0.9},
            {"start": 2.0, "end": 3.0, "text": "C", "no_speech_prob": 0.3},
        ]
        res = flag_uncertain_segments(segments, threshold=0.5)
        self.assertEqual(len(res), 3)
        self.assertEqual([r["text"] for r in res], ["A", "B", "C"])
        self.assertFalse(res[0]["needs_review"])
        self.assertTrue(res[1]["needs_review"])
        self.assertFalse(res[2]["needs_review"])


if __name__ == "__main__":
    unittest.main()

