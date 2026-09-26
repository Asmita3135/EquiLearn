import sys
import unittest
from pathlib import Path

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from main_pipeline import run_member3_pipeline
from input_integration import UnifiedInput, TimestampedSegment
from llm_processing import LLMProcessor
from accessibility_rules import UserProfile

# Import our Integration Adapter
from integration_adapter import EquilearnAdapter

class MockLLMProvider:
    def generate(self, prompt: str) -> str:
        if "REFINEMENT" in prompt or "further simplify" in prompt:
            return "Plants make food using the sun. This is photosynthesis."
        return "Photosynthesis is the process where plants convert sunlight into chemical energy."

class TestAdapterToM3Integration(unittest.TestCase):
    def setUp(self):
        self.processor = LLMProcessor(
            provider_func=MockLLMProvider().generate,
            model_config="Mock-Adapter-Test-Model"
        )
        
    def test_text_to_m3(self):
        unified_input = EquilearnAdapter.adapt("job_1", "text", raw_text="Photosynthesis is the fundamental biological process utilized by plants to harness energy from sunlight, which is extremely complicated and requires simplification for dyslexia profiles.")
        result = run_member3_pipeline(unified_input, self.processor)
        
        # Verify M3 outputs
        self.assertIsNotNone(result.pipeline_result)
        self.assertIn("photosynthesis", result.pipeline_result.original_analysis.key_terms)
        self.assertIsNotNone(result.pipeline_result.simplified_text)
        self.assertIn("Plants make food", result.pipeline_result.simplified_text)
        
        # Verify metadata wasn't lost
        self.assertEqual(result.unified_input.adapter_job_id, "job_1")
        self.assertEqual(result.unified_input.adapter_input_type, "text")
        
    def test_m1_output_to_adapter_to_m3(self):
        m1_data = {
            "ocr_text": "Photosynthesis process.",
            "visual_description": "A diagram of a plant.",
            "alt_text": "Plant diagram",
            "metadata": {"confidence": 0.99}
        }
        unified_input = EquilearnAdapter.adapt("job_2", "image", m1_output=m1_data)
        result = run_member3_pipeline(unified_input, self.processor)
        
        # Check M3 Processing
        self.assertIn("Photosynthesis", result.pipeline_result.original_text)
        self.assertIn("diagram of a plant", result.representations[UserProfile.BLIND].tts_ready_text.lower())
        
        # Check Adapter Preservation
        self.assertTrue(hasattr(result.unified_input, "adapter_m1_metadata"))
        self.assertEqual(result.unified_input.adapter_m1_metadata["confidence"], 0.99)
        self.assertIn("[Alt Text: Plant diagram]", result.unified_input.member1_data.visual_description)

    def test_m2_output_to_adapter_to_m3(self):
        m2_data = {
            "transcript": "Let's learn about plants.",
            "timestamps": [{"start": 0.0, "end": 2.0, "text": "Let's learn about plants."}],
            "vtt": "WEBVTT\n...",
            "metadata": {"format": "mp3"}
        }
        unified_input = EquilearnAdapter.adapt("job_3", "audio", m2_output=m2_data)
        result = run_member3_pipeline(unified_input, self.processor)
        
        # Check M3 Processing
        deaf_rep = result.representations[UserProfile.DEAF]
        self.assertEqual(len(deaf_rep.transcript_segments), 1)
        self.assertEqual(deaf_rep.transcript_segments[0].start_time, 0.0)
        
        # Check Adapter Preservation
        self.assertEqual(result.unified_input.adapter_vtt, "WEBVTT\n...")
        self.assertEqual(result.unified_input.adapter_m2_metadata["format"], "mp3")
        
    def test_m1_and_m2_output_to_adapter_to_m3(self):
        m1_data = {
            "ocr_text": "Text on screen",
            "metadata": {"confidence": 0.95}
        }
        m2_data = {
            "transcript": "Spoken text",
            "vtt": "WEBVTT...",
            "metadata": {"language": "en"}
        }
        
        unified_input = EquilearnAdapter.adapt(
            "job_4", "video", 
            m1_output=m1_data, 
            m2_output=m2_data, 
            raw_text="Text on screen"
        )
        result = run_member3_pipeline(unified_input, self.processor)
        
        # Verify text was combined for NLP processing
        self.assertIn("Text on screen", result.pipeline_result.original_text)
        self.assertIn("Spoken text", result.pipeline_result.original_text)
        
        # Verify deduplication
        self.assertIsNone(result.unified_input.text)
        
        # M3 Accessibility Outputs exist
        self.assertIsNotNone(result.representations[UserProfile.DYSLEXIA].primary_text)
        
        # Verify full metadata payload survived
        self.assertEqual(result.unified_input.adapter_m1_metadata["confidence"], 0.95)
        self.assertEqual(result.unified_input.adapter_vtt, "WEBVTT...")
        self.assertEqual(result.unified_input.adapter_m2_metadata["language"], "en")

if __name__ == '__main__':
    unittest.main()
