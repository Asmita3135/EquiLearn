import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from main_pipeline import run_member3_pipeline
from input_integration import UnifiedInput
from llm_processing import LLMProcessor
from accessibility_rules import UserProfile

class FocusedSummaryMock:
    def generate(self, prompt: str) -> str:
        if "Summarize" in prompt:
            return "THIS IS THE PRESERVED SUMMARY."
        elif "Simplify" in prompt or "simplify" in prompt:
            return "This is the preserved simplified text."
        return "Unknown"

class TestSummaryFlow(unittest.TestCase):

    def test_summary_preservation_flow(self):
        processor = LLMProcessor(provider_func=FocusedSummaryMock().generate, model_config="Focus-Test")
        unified_in = UnifiedInput(text="This is a highly complex original text about biology and photosynthesis that requires summarization and simplification.")
        
        result = run_member3_pipeline(unified_in, processor)
        
        # 1. Check generated summary is in pipeline_result
        self.assertIsNotNone(result.pipeline_result.summary)
        self.assertEqual(result.pipeline_result.summary, "THIS IS THE PRESERVED SUMMARY.")
        
        # 2. Check original text and simplified text are still preserved separately
        self.assertIn("highly complex original text", result.pipeline_result.original_text)
        self.assertEqual(result.pipeline_result.simplified_text, "This is the preserved simplified text.")
        
        # 3. Check summary reaches Member3FinalOutput via pipeline_result
        self.assertEqual(result.pipeline_result.summary, "THIS IS THE PRESERVED SUMMARY.")
        
        # 4. Check summary is available to accessibility representations
        blind_rep = result.representations[UserProfile.BLIND]
        self.assertEqual(blind_rep.summary, "THIS IS THE PRESERVED SUMMARY.")
        
        dyslexia_rep = result.representations[UserProfile.DYSLEXIA]
        self.assertEqual(dyslexia_rep.summary, "THIS IS THE PRESERVED SUMMARY.")

if __name__ == '__main__':
    unittest.main()

