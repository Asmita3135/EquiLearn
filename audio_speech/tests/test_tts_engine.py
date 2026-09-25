"""
Unit tests for tts_engine module.
"""

from pathlib import Path
import sys
import unittest

# Ensure project root is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_speech.src.tts_engine import text_to_speech, synthesize_speech


class TestTTSEngine(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory for test audio files."""
        self.test_dir = Path(__file__).parent / "temp_tts_files"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary test audio files."""
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

    def test_empty_text_rejected(self):
        """Test error handling when text is empty or None."""
        output_file = self.test_dir / "empty_test.mp3"

        with self.assertRaises(ValueError) as ctx:
            text_to_speech("", output_file)
        self.assertIn("cannot be empty", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            text_to_speech("   ", output_file)
        self.assertIn("cannot be empty", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            text_to_speech(None, output_file)
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_output_path_handling(self):
        """Test parent directory creation and output path formatting."""
        nested_output = self.test_dir / "subfolder" / "nested_tts.mp3"
        
        # Test real generation or catch network error
        try:
            res_path = text_to_speech("Test path handling.", nested_output)
            self.assertTrue(Path(res_path).exists())
            self.assertGreater(Path(res_path).stat().st_size, 0)
        except RuntimeError as e:
            # If offline / network error occurs, ensure parent directory was still created
            self.assertTrue(nested_output.parent.exists())
            print(f"\n[Note] gTTS network synthesis skipped due to network status: {e}")

    def test_real_gtts_generation(self):
        """Test real gTTS audio generation with short sentence."""
        text = "Hello, welcome to EquiLearn."
        output_file = self.test_dir / "equilearn_welcome.mp3"

        try:
            res_path = text_to_speech(text, output_file)

            self.assertTrue(Path(res_path).exists())
            self.assertGreater(Path(res_path).stat().st_size, 0)
            self.assertEqual(Path(res_path).suffix.lower(), ".mp3")
            print(f"\n[OK] Real gTTS audio generated successfully: {res_path} ({Path(res_path).stat().st_size} bytes)")
        except RuntimeError as e:
            print(f"\n[Note] Real gTTS request failed (network status): {e}")
            # If network error, skip test gracefully without failing build environment
            self.skipTest(f"Network unavailable for gTTS API request: {e}")


if __name__ == "__main__":
    unittest.main()
