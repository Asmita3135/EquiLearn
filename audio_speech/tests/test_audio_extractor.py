"""
Unit tests for audio_extractor module using standard library unittest.
"""

from pathlib import Path
import sys
import unittest

# Ensure project root is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_speech.src.audio_extractor import (
    extract_audio_from_video,
    check_ffmpeg_installed,
)


class TestAudioExtractor(unittest.TestCase):

    def test_check_ffmpeg_installed(self):
        """Verify FFmpeg is installed and detected."""
        self.assertTrue(check_ffmpeg_installed())

    def test_extract_audio_success(self):
        """Test successful audio extraction from valid video file."""
        sample_video = (
            Path(__file__).parent.parent / "data" / "raw" / "sample.mp4"
        )
        if not sample_video.exists():
            self.skipTest("data/raw/sample.mp4 does not exist")

        output_wav = (
            Path(__file__).parent.parent / "data" / "processed" / "test_output.wav"
        )
        result_path = extract_audio_from_video(sample_video, output_wav)

        self.assertTrue(Path(result_path).exists())
        self.assertGreater(Path(result_path).stat().st_size, 0)
        self.assertEqual(Path(result_path).suffix.lower(), ".wav")

        # Clean up temporary test file
        if Path(result_path).exists():
            Path(result_path).unlink()

    def test_extract_audio_file_not_found(self):
        """Test error handling when video file does not exist."""
        with self.assertRaises(FileNotFoundError) as ctx:
            extract_audio_from_video("non_existent_file.mp4")
        self.assertIn("does not exist", str(ctx.exception))

    def test_extract_audio_unsupported_format(self):
        """Test error handling for unsupported video extensions."""
        invalid_file = Path(__file__).parent / "temp_doc.txt"
        invalid_file.write_text("dummy text content")

        try:
            with self.assertRaises(ValueError) as ctx:
                extract_audio_from_video(invalid_file)
            self.assertIn("not a recognized video format", str(ctx.exception))
        finally:
            if invalid_file.exists():
                invalid_file.unlink()


if __name__ == "__main__":
    unittest.main()
