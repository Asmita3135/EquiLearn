"""
Unit tests for Whisper ASR model loading and speech-to-text transcription.
"""

from pathlib import Path
import sys
import unittest

# Ensure project root is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_speech.src.whisper_asr import load_whisper_model, transcribe_audio


class TestWhisperASRSetup(unittest.TestCase):

    def test_whisper_model_loading(self):
        """Verify OpenAI Whisper model can be loaded successfully."""
        model_name = "tiny"
        print(f"\n[+] Loading Whisper '{model_name}' model...")
        model = load_whisper_model(model_name)

        self.assertIsNotNone(model)
        print(f"[OK] Whisper '{model_name}' model loaded successfully!")

    def test_whisper_transcription_real_audio(self):
        """Test real Whisper transcription on sample_preprocessed.wav."""
        sample_audio = (
            Path(__file__).parent.parent
            / "data"
            / "processed"
            / "sample_preprocessed.wav"
        )
        if not sample_audio.exists():
            self.skipTest(
                "data/processed/sample_preprocessed.wav does not exist"
            )

        print(
            f"\n[+] Running Whisper 'tiny' transcription on: {sample_audio.name}"
        )
        result = transcribe_audio(sample_audio, model_name="tiny")

        # 1. Verify result structure
        self.assertIsInstance(result, dict)

        # 2. Verify text output is a string and not None
        self.assertIn("text", result)
        self.assertIsNotNone(result["text"])
        self.assertIsInstance(result["text"], str)

        # 3. Verify language field exists
        self.assertIn("language", result)
        self.assertIsNotNone(result["language"])

        print(f"[OK] Transcription completed successfully!")
        print(f"     Model: tiny")
        print(f"     Audio: {sample_audio.name}")
        print(f"     Detected language: {result['language']}")
        print(f"     Transcript: '{result['text']}'")

    def test_transcribe_audio_file_not_found(self):
        """Test error handling when input audio file does not exist."""
        with self.assertRaises(FileNotFoundError) as ctx:
            transcribe_audio("non_existent_audio.wav", model_name="tiny")
        self.assertIn("does not exist", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

