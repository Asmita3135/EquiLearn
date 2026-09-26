import sys
import unittest

# Reuse the mocks created previously for these tests
from test_m1_connector import M1Pipeline
from test_m2_connector import M2Pipeline
from test_adapter_to_m3 import MockLLMProvider

from pathlib import Path

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from llm_processing import LLMProcessor
from orchestrator import run_equilearn_job

class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.m1 = M1Pipeline()
        self.m2 = M2Pipeline()
        self.m3 = LLMProcessor(
            provider_func=MockLLMProvider().generate,
            model_config="Orchestrator-Test"
        )
        
    def test_text_route(self):
        result = run_equilearn_job(
            job_id="O1",
            input_type="TEXT",
            content="Biology text.",
            m3_processor=self.m3
        )
        self.assertEqual(result.status, "SUCCESS")
        self.assertIsNotNone(result.final_output)
        self.assertIn("biology", result.final_output.pipeline_result.original_analysis.key_terms)

    def test_image_pdf_route(self):
        # Image
        result = run_equilearn_job(
            job_id="O2",
            input_type="IMAGE",
            content="normal_text",
            m1_pipeline=self.m1,
            m3_processor=self.m3
        )
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.final_output.unified_input.adapter_m1_metadata["confidence"], 0.98)
        
        # PDF
        result_pdf = run_equilearn_job(
            job_id="O2_pdf",
            input_type="PDF",
            content="diagram",
            m1_pipeline=self.m1,
            m3_processor=self.m3
        )
        self.assertEqual(result_pdf.status, "SUCCESS")

    def test_audio_video_route(self):
        # Audio
        result_audio = run_equilearn_job(
            job_id="O3",
            input_type="AUDIO",
            content="clean_audio",
            m2_pipeline=self.m2,
            m3_processor=self.m3
        )
        self.assertEqual(result_audio.status, "SUCCESS")
        self.assertEqual(result_audio.final_output.unified_input.adapter_m2_metadata["format"], "mp3")
        
        # Video
        result_video = run_equilearn_job(
            job_id="O4",
            input_type="VIDEO",
            content="video",
            m2_pipeline=self.m2,
            m3_processor=self.m3
        )
        self.assertEqual(result_video.status, "SUCCESS")
        self.assertEqual(result_video.final_output.unified_input.adapter_m2_metadata["has_video_track"], True)

    def test_multimodal_route(self):
        content = {
            "visual": "diagram",
            "audio": "clean_audio"
        }
        result = run_equilearn_job(
            job_id="O5",
            input_type="MULTIMODAL",
            content=content,
            m1_pipeline=self.m1,
            m2_pipeline=self.m2,
            m3_processor=self.m3
        )
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.final_output.unified_input.adapter_m1_metadata["confidence"], 0.90)
        self.assertEqual(result.final_output.unified_input.adapter_m2_metadata["format"], "mp3")

    def test_failure_handling(self):
        # Missing M1 pipeline
        result = run_equilearn_job(
            job_id="O6",
            input_type="IMAGE",
            content="normal_text",
            m3_processor=self.m3
            # m1_pipeline missing
        )
        self.assertEqual(result.status, "ERROR")
        self.assertIn("M1 Pipeline required", result.error_message)
        
        # Missing M3 pipeline
        result2 = run_equilearn_job(
            job_id="O7",
            input_type="TEXT",
            content="Test text",
            m3_processor=None
        )
        self.assertEqual(result2.status, "ERROR")
        self.assertIn("M3 LLMProcessor is required", result2.error_message)

        # Invalid type
        result3 = run_equilearn_job(
            job_id="O8",
            input_type="UNKNOWN_TYPE",
            content="data",
            m3_processor=self.m3
        )
        self.assertEqual(result3.status, "ERROR")
        self.assertIn("Unsupported input type", result3.error_message)

    def test_multimodal_warnings(self):
        # Pass multimodal but missing visual key
        content = {"audio": "clean_audio"}
        result = run_equilearn_job(
            job_id="O9",
            input_type="MULTIMODAL",
            content=content,
            m1_pipeline=self.m1,
            m2_pipeline=self.m2,
            m3_processor=self.m3
        )
        self.assertEqual(result.status, "SUCCESS")
        self.assertIn("Multimodal missing visual content.", result.warnings)
        self.assertEqual(result.final_output.unified_input.adapter_warnings[0], "Multimodal missing visual content.")

if __name__ == '__main__':
    unittest.main()
