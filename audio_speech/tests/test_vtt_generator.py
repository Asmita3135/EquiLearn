"""
Unit tests for vtt_generator module.
"""

from pathlib import Path
import sys
import unittest

# Ensure project root is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_speech.src.vtt_generator import (
    format_vtt_timestamp,
    generate_vtt,
    save_vtt,
)


class TestVTTGenerator(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory for test VTT output."""
        self.test_dir = Path(__file__).parent / "temp_vtt_files"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary test VTT files."""
        if self.test_dir.exists():
            for f in self.test_dir.iterdir():
                try:
                    f.unlink()
                except Exception:
                    pass
            try:
                self.test_dir.rmdir()
            except Exception:
                pass

    def test_format_vtt_timestamp(self):
        """Test timestamp conversion to HH:MM:SS.mmm format."""
        self.assertEqual(format_vtt_timestamp(0.0), "00:00:00.000")
        self.assertEqual(format_vtt_timestamp(3.25), "00:00:03.250")
        self.assertEqual(format_vtt_timestamp(65.5), "00:01:05.500")
        self.assertEqual(format_vtt_timestamp(3661.125), "01:01:01.125")

    def test_vtt_starts_with_header(self):
        """Test that generated VTT content starts with WEBVTT."""
        segments = [{"start": 0.0, "end": 2.0, "text": "Test segment"}]
        content = generate_vtt(segments)
        self.assertTrue(content.startswith("WEBVTT"))

    def test_multiple_caption_blocks_and_order(self):
        """Test generation of multiple caption blocks in correct order."""
        segments = [
            {"start": 0.0, "end": 3.25, "text": "Hello everyone"},
            {"start": 3.25, "end": 6.80, "text": "Today we will learn."},
        ]

        content = generate_vtt(segments)

        expected = (
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:03.250\n"
            "Hello everyone\n\n"
            "00:00:03.250 --> 00:00:06.800\n"
            "Today we will learn.\n"
        )

        self.assertEqual(content, expected)

    def test_empty_segments_list(self):
        """Test that empty segments list produces valid WEBVTT document header."""
        content_empty_list = generate_vtt([])
        self.assertEqual(content_empty_list.strip(), "WEBVTT")

        content_none = generate_vtt(None)
        self.assertEqual(content_none.strip(), "WEBVTT")

    def test_save_vtt_file(self):
        """Test saving VTT content to file."""
        segments = [{"start": 0.0, "end": 1.5, "text": "Saving test"}]
        vtt_content = generate_vtt(segments)

        output_file = self.test_dir / "sample_caption.vtt"
        saved_path = save_vtt(vtt_content, output_file)

        self.assertTrue(Path(saved_path).exists())
        read_content = Path(saved_path).read_text(encoding="utf-8")
        self.assertEqual(read_content, vtt_content)


if __name__ == "__main__":
    unittest.main()
