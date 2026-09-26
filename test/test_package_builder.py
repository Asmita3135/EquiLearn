import unittest
import sys
import json

from pathlib import Path

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from accessibility_rules import UserProfile
from orchestrator import run_equilearn_job
from test_m1_connector import M1Pipeline
from test_m2_connector import M2Pipeline
from test_adapter_to_m3 import MockLLMProvider
from llm_processing import LLMProcessor
from package_builder import build_accessibility_package

class TestPackageBuilder(unittest.TestCase):
    def setUp(self):
        self.m1 = M1Pipeline()
        self.m2 = M2Pipeline()
        self.m3 = LLMProcessor(
            provider_func=MockLLMProvider().generate,
            model_config="Package-Test"
        )
        
        # Create a multimodal run to get a rich final output
        # Utilizing my mocks returning complex structure
        content = {
            "visual": "diagram",
            "audio": "clean_audio"
        }
        self.result = run_equilearn_job(
            job_id="P1",
            input_type="MULTIMODAL",
            content=content,
            m1_pipeline=self.m1,
            m2_pipeline=self.m2,
            m3_processor=self.m3
        )
        
    def test_json_serializable(self):
        package = build_accessibility_package(self.result, UserProfile.BLIND)
        try:
            json_str = json.dumps(package)
            self.assertIn("job_id", json_str)
        except Exception as e:
            self.fail(f"Package is not JSON serializable: {e}")

    def test_blind_profile(self):
        package = build_accessibility_package(self.result, UserProfile.BLIND)
        self.assertEqual(package["profile"], "BLIND")
        self.assertIn("tts_ready_text", package["recommended_representations"])
        self.assertIn("cell", package["recommended_representations"]["tts_ready_text"].lower())
        self.assertIsNotNone(package["alt_text"])

    def test_deaf_hoh_profile(self):
        package = build_accessibility_package(self.result, UserProfile.DEAF)
        self.assertEqual(package["profile"], "DEAF")
        self.assertIn("transcript_segments", package["recommended_representations"])
        segments = package["recommended_representations"]["transcript_segments"]
        self.assertEqual(len(segments), 2)
        self.assertIsNotNone(package["captions_vtt"])
        self.assertIn("WEBVTT", package["captions_vtt"])

    def test_low_vision_profile(self):
        package = build_accessibility_package(self.result, UserProfile.LOW_VISION)
        self.assertEqual(package["profile"], "LOW_VISION")
        # M3 LOW_VISION rule: metadata["presentation_mode"] = "high_contrast_magnifiable"
        reps = package["recommended_representations"]
        self.assertIn("metadata", reps)
        self.assertEqual(reps["metadata"]["presentation_mode"], "high_contrast_magnifiable")
        # tts_ready_text must be populated (M3 sets it to original_text for low_vision)
        self.assertIn("tts_ready_text", reps)
        self.assertIsNotNone(reps["tts_ready_text"])

    def test_dyslexia_profile(self):
        package = build_accessibility_package(self.result, UserProfile.DYSLEXIA)
        self.assertEqual(package["profile"], "DYSLEXIA")
        self.assertIn("primary_text", package["recommended_representations"])
        # Dyslexia primary text should be the simplified text
        self.assertEqual(package["recommended_representations"]["primary_text"], package["simplified_text"])

    def test_missing_data_resilience(self):
        # Test that a failing or empty result still builds gracefully
        failed_result = run_equilearn_job("P2", "UNKNOWN", "err")
        package = build_accessibility_package(failed_result, UserProfile.BLIND)
        self.assertEqual(package["status"], "ERROR")
        self.assertIn("error", package)
        self.assertIn("Unsupported input type", package["error"])

if __name__ == '__main__':
    unittest.main()
