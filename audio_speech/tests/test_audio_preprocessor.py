"""
Unit tests for audio_preprocessor module.
"""

from pathlib import Path
import sys
import unittest
import numpy as np
import soundfile as sf

# Ensure project root is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_speech.src.audio_preprocessor import preprocess_audio, TARGET_SAMPLE_RATE


class TestAudioPreprocessor(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory for test audio files."""
        self.test_dir = Path(__file__).parent / "temp_preprocessor_files"
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

    def test_preprocess_normal_wav(self):
        """Test preprocessing of a standard 44.1kHz stereo WAV file."""
        # Generate synthetic 44100 Hz stereo audio (sine wave + silence)
        sr_in = 44100
        duration = 2.0
        t = np.linspace(0, duration, int(sr_in * duration), endpoint=False)
        sine_wave = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Create stereo signal (2 channels)
        stereo_audio = np.column_stack((sine_wave, sine_wave * 0.8))
        input_wav = self.test_dir / "input_stereo_44k.wav"
        sf.write(str(input_wav), stereo_audio, samplerate=sr_in)

        # Output path
        output_wav = self.test_dir / "output_mono_16k.wav"

        # Preprocess
        result_path = preprocess_audio(input_wav, output_wav)

        # Verification
        self.assertTrue(Path(result_path).exists())
        self.assertGreater(Path(result_path).stat().st_size, 0)

        # Inspect properties using soundfile
        info = sf.info(result_path)
        self.assertEqual(info.samplerate, 16000)
        self.assertEqual(info.channels, 1)

    def test_preprocess_silent_wav(self):
        """Test preprocessing of a completely silent audio file without crashing."""
        sr_in = 16000
        duration = 1.0
        silent_audio = np.zeros(int(sr_in * duration), dtype=np.float32)
        input_wav = self.test_dir / "input_silent.wav"
        sf.write(str(input_wav), silent_audio, samplerate=sr_in)

        output_wav = self.test_dir / "output_silent_processed.wav"
        result_path = preprocess_audio(input_wav, output_wav)

        self.assertTrue(Path(result_path).exists())
        info = sf.info(result_path)
        self.assertEqual(info.samplerate, 16000)
        self.assertEqual(info.channels, 1)

    def test_preprocess_file_not_found(self):
        """Test error handling when input audio file does not exist."""
        with self.assertRaises(FileNotFoundError) as ctx:
            preprocess_audio("non_existent_audio.wav")
        self.assertIn("does not exist", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
