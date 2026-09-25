"""
End-to-End Integration Test for Member 2 Audio & Speech Intelligence Module.

Pipeline:
Video File
  └─> 1. FFmpeg Audio Extraction (audio_extractor)
  └─> 2. 16kHz Mono Preprocessing (audio_preprocessor)
  └─> 3. Whisper ASR Speech-to-Text (whisper_asr)
  └─> 4. Transcript & Timestamp Processing (transcript_processor)
  └─> 5. ASR Uncertainty Flagging (transcript_processor)
  └─> 6. WebVTT Caption Generation (vtt_generator)
  └─> 7. UTF-8 WebVTT File Output (vtt_generator)
"""

from pathlib import Path
import sys
import unittest

# Ensure project root is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from audio_speech.src.audio_extractor import extract_audio_from_video
from audio_speech.src.audio_preprocessor import preprocess_audio
from audio_speech.src.whisper_asr import transcribe_audio
from audio_speech.src.transcript_processor import (
    process_transcript_segments,
    flag_uncertain_segments,
)
from audio_speech.src.vtt_generator import generate_vtt, save_vtt


class TestEndToEndPipeline(unittest.TestCase):

    def test_full_audio_speech_pipeline(self):
        """Executes full end-to-end audio/speech pipeline on real speech video input."""
        raw_dir = Path(__file__).parent.parent / "data" / "raw"
        processed_dir = Path(__file__).parent.parent / "data" / "processed"
        output_dir = Path(__file__).parent.parent / "data" / "output"

        # Prioritize real speech sample
        input_video = raw_dir / "speech_sample.mp4"
        if not input_video.exists():
            input_video = raw_dir / "sample.mp4"

        if not input_video.exists():
            self.skipTest("No input video file found in data/raw for end-to-end test.")

        print(f"\n==================================================")
        print(f"  END-TO-END INTEGRATION TEST: MEMBER 2 PIPELINE ")
        print(f"==================================================")
        print(f"[+] Input Video: {input_video.name}")

        # Stage 1: Audio Extraction
        extracted_wav = processed_dir / f"{input_video.stem}_e2e_extracted.wav"
        extracted_path = extract_audio_from_video(input_video, extracted_wav)
        self.assertTrue(Path(extracted_path).exists())
        self.assertGreater(Path(extracted_path).stat().st_size, 0)
        print(f"[OK] Stage 1 - Extracted Audio WAV: {Path(extracted_path).name}")

        # Stage 2: Audio Preprocessing
        preprocessed_wav = processed_dir / f"{input_video.stem}_e2e_preprocessed.wav"
        preprocessed_path = preprocess_audio(extracted_path, preprocessed_wav)
        self.assertTrue(Path(preprocessed_path).exists())
        self.assertGreater(Path(preprocessed_path).stat().st_size, 0)
        print(f"[OK] Stage 2 - Preprocessed Audio WAV (16kHz mono): {Path(preprocessed_path).name}")

        # Stage 3: Whisper ASR Transcription
        model_name = "tiny"
        print(f"[+] Stage 3 - Running Whisper ASR ('{model_name}')...")
        asr_result = transcribe_audio(preprocessed_path, model_name=model_name)
        
        self.assertIsInstance(asr_result, dict)
        self.assertIn("text", asr_result)
        self.assertIsInstance(asr_result["text"], str)
        self.assertIn("segments", asr_result)

        detected_lang = asr_result.get("language", "unknown")
        raw_text = asr_result.get("text", "")
        raw_segments = asr_result.get("segments", [])
        print(f"[OK] Stage 3 - Whisper Transcription Completed.")
        print(f"    - Detected Language: {detected_lang}")
        print(f"    - Recognized Transcript: '{raw_text}'")

        # Stage 4: Transcript Segment & Timestamp Processing
        clean_segments = process_transcript_segments(raw_segments)
        self.assertIsInstance(clean_segments, list)
        print(f"[OK] Stage 4 - Processed {len(clean_segments)} timestamped transcript segments.")

        # Stage 5: Uncertainty Flagging
        flagged_segments = flag_uncertain_segments(clean_segments, threshold=0.5)
        self.assertEqual(len(flagged_segments), len(clean_segments))
        print(f"[OK] Stage 5 - ASR Uncertainty Flagging Completed.")

        # Stage 6: WebVTT Caption Generation
        vtt_content = generate_vtt(flagged_segments)
        self.assertTrue(vtt_content.startswith("WEBVTT"))
        print(f"[OK] Stage 6 - WebVTT Caption Content Generated.")

        # Stage 7: Save WebVTT Output File
        vtt_output_path = output_dir / f"{input_video.stem}.vtt"
        saved_vtt_path = save_vtt(vtt_content, vtt_output_path)

        self.assertTrue(Path(saved_vtt_path).exists())
        self.assertGreater(Path(saved_vtt_path).stat().st_size, 0)
        print(f"[OK] Stage 7 - WebVTT File Saved: {Path(saved_vtt_path).name}")


        # End-to-End Summary Output
        print(f"\n==================================================")
        print(f"  END-TO-END PIPELINE SUCCESSFUL                  ")
        print(f"==================================================")
        print(f"Input video:        {input_video.name}")
        print(f"Whisper model:      {model_name}")
        print(f"Detected language:  {detected_lang}")
        print(f"Transcript:         '{raw_text}'")
        print(f"Number of segments: {len(clean_segments)}")
        print(f"VTT output:         {saved_vtt_path}")


if __name__ == "__main__":
    unittest.main()
