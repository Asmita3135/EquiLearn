import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from input_integration import (
    UnifiedInput, Member1Input, Member2Input, TimestampedSegment,
    process_integrated_input
)
from llm_processing import LLMProcessor

class MockIntegrationLLMProvider:
    def generate(self, prompt: str) -> str:
        return "This is a simplified mock output for the integrated text."

class TestInputIntegration(unittest.TestCase):

    def setUp(self):
        self.processor = LLMProcessor(
            provider_func=MockIntegrationLLMProvider().generate,
            model_config="Mock-Integration-Model"
        )

    def test_member1_ocr_and_vlm(self):
        # MOCK INPUT from Member 1 (Vision)
        m1_input = Member1Input(
            ocr_text="MITOCHONDRIA: THE POWERHOUSE OF THE CELL.",
            visual_description="A diagram showing a cross-section of a mitochondrion with folded inner membranes."
        )
        unified_in = UnifiedInput(member1_data=m1_input)
        
        result = process_integrated_input(unified_in, self.processor)
        
        # Verify unified text contains both elements cleanly
        self.assertIn("[Visual Description: A diagram showing", result.unified_text)
        self.assertIn("MITOCHONDRIA: THE POWERHOUSE OF THE CELL.", result.unified_text)
        # Verify pipeline ran
        self.assertIsNotNone(result.pipeline_result)
        self.assertIn("simplified mock output", result.pipeline_result.simplified_text)

    def test_member2_transcript_with_timestamps(self):
        # MOCK INPUT from Member 2 (Speech)
        m2_input = Member2Input(
            transcript="Welcome class. Today we discuss cell biology.",
            segments=[
                TimestampedSegment(0.0, 2.5, "Welcome class."),
                TimestampedSegment(2.5, 6.0, "Today we discuss cell biology.")
            ]
        )
        unified_in = UnifiedInput(member2_data=m2_input)
        
        result = process_integrated_input(unified_in, self.processor)
        
        self.assertIn("[Transcript]", result.unified_text)
        self.assertIn("Welcome class. Today we discuss cell biology.", result.unified_text)
        
        # Verify timestamps are preserved unmodified
        self.assertIsNotNone(result.timestamps)
        self.assertEqual(len(result.timestamps), 2)
        self.assertEqual(result.timestamps[0].start_time, 0.0)

    def test_combined_content(self):
        # MOCK INPUT showing all components combined
        m1_input = Member1Input(
            ocr_text="Equation: E = mc^2"
        )
        m2_input = Member2Input(
            transcript="As you can see on the board, energy equals mass times the speed of light squared."
        )
        unified_in = UnifiedInput(
            text="Physics Lesson 4",
            member1_data=m1_input,
            member2_data=m2_input
        )
        
        result = process_integrated_input(unified_in, self.processor)
        
        # Check that all domains are combined with separators
        self.assertIn("Physics Lesson 4", result.unified_text)
        self.assertIn("Equation: E = mc^2", result.unified_text)
        self.assertIn("[Transcript]", result.unified_text)
        self.assertIn("energy equals mass times", result.unified_text)
        
        # Pipeline must have successfully run on the combined text
        self.assertIsNotNone(result.pipeline_result)

if __name__ == '__main__':
    unittest.main()

