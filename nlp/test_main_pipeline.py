import unittest
from main_pipeline import run_member3_pipeline
from input_integration import UnifiedInput, Member1Input, Member2Input, TimestampedSegment
from llm_processing import LLMProcessor
from accessibility_rules import UserProfile

class MockFinalLLMProvider:
    def generate(self, prompt: str) -> str:
        if "REFINEMENT" in prompt or "further simplify" in prompt:
            return "Plants make food using the sun. This is photosynthesis."
        return "Photosynthesis is the process where plants convert sunlight into chemical energy."

class TestFinalIntegration(unittest.TestCase):

    def setUp(self):
        self.processor = LLMProcessor(
            provider_func=MockFinalLLMProvider().generate,
            model_config="Mock-Final-Model"
        )
        
        # Construct a full multimodal mock input from all hypothetical members
        self.m1_in = Member1Input(
            ocr_text="PHOTOSYNTHESIS EXPLAINED.",
            visual_description="Diagram of a plant absorbing sunlight."
        )
        self.m2_in = Member2Input(
            transcript="Today we will learn that photosynthesis is the fundamental biological process utilized by plants to harness energy from sunlight.",
            segments=[
                TimestampedSegment(0.0, 3.0, "Today we will learn that photosynthesis"),
                TimestampedSegment(3.0, 6.0, "is the fundamental biological process utilized by plants"),
                TimestampedSegment(6.0, 9.0, "to harness energy from sunlight.")
            ]
        )
        self.unified_in = UnifiedInput(
            text="Chapter 1: Biology",
            member1_data=self.m1_in,
            member2_data=self.m2_in
        )

    def test_full_pipeline_execution(self):
        # Run the single master function
        result = run_member3_pipeline(self.unified_in, self.processor)
        
        # 1. Preprocessing & Integration verify
        self.assertIn("PHOTOSYNTHESIS EXPLAINED.", result.pipeline_result.original_text)
        self.assertIn("Diagram of a plant", result.pipeline_result.original_text)
        self.assertIn("fundamental biological process", result.pipeline_result.original_text)
        
        # 2. Readability, Key Terms & Complexity verify
        original_analysis = result.pipeline_result.original_analysis
        self.assertGreater(original_analysis.total_words, 20)
        self.assertIn("photosynthesis", original_analysis.key_terms)
        self.assertIn("photosynthesis", original_analysis.difficult_words)
        
        # 3. LLM Simplification & Dyslexia Refinement verify
        final_analysis = result.pipeline_result.final_analysis
        self.assertTrue(result.pipeline_result.refinement_required) # Triggered because first pass was complex
        self.assertIn("Plants make food", result.pipeline_result.simplified_text)
        
        # 4. Accessibility Profiles verify
        blind_rep = result.representations[UserProfile.BLIND]
        self.assertIn("Diagram of a plant", blind_rep.tts_ready_text)
        
        deaf_rep = result.representations[UserProfile.DEAF]
        self.assertIsNotNone(deaf_rep.transcript_segments)
        self.assertEqual(len(deaf_rep.transcript_segments), 3)
        
        dyslexia_rep = result.representations[UserProfile.DYSLEXIA]
        self.assertEqual(dyslexia_rep.primary_text, result.pipeline_result.simplified_text)
        self.assertIn("photosynthesis", dyslexia_rep.metadata["difficult_terms_to_highlight"])
        
        # 5. Evaluation metrics verify limitations are stated
        metrics = result.evaluation_metrics
        self.assertIn("N/A", metrics["ROUGE"])
        self.assertIn("N/A", metrics["SARI"])
        self.assertTrue(float(metrics["Flesch_Kincaid_Grade"]) < 10.0)

if __name__ == '__main__':
    unittest.main()
