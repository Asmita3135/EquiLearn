import unittest
from dyslexia_pipeline import run_dyslexia_pipeline
from llm_processing import LLMProcessor

class MockRefiningLLMProvider:
    """Mock LLM that simulates returning simpler text on subsequent calls."""
    def generate(self, prompt: str) -> str:
        if "REFINEMENT" in prompt or "further simplify" in prompt:
            # Returns a very simple text (grade < 8, short sentences)
            return "Plants use light to make food. This is called photosynthesis. It needs water and air."
            
        # Initial simplification
        if "Moderate" in prompt:
            # Still slightly complex
            return "Plants perform photosynthesis to harness light energy. They transform water and carbon dioxide into sugar."
        elif "Highly Complex" in prompt:
            # Remains too complex after first pass
            return "Photosynthesis is the biological mechanism where flora absorb electromagnetic radiation to synthesize glucose from carbon dioxide and water molecules."
        
        # Easy
        return "Cats are nice. They play."

class TestDyslexiaPipeline(unittest.TestCase):

    def setUp(self):
        self.processor = LLMProcessor(
            provider_func=MockRefiningLLMProvider().generate,
            model_config="MockModel-Refining"
        )

    def test_easy_text(self):
        text = "Cats are nice. They play."
        result = run_dyslexia_pipeline(text, self.processor)
        
        self.assertEqual(result.refinement_count, 0)
        self.assertFalse(result.refinement_required)
        self.assertTrue(result.final_analysis.flesch_kincaid_grade < 8.0)

    def test_moderate_text(self):
        # We inject the word "Moderate" so our mock knows what to return on the first pass
        text = "Moderate: The process by which plants use sunlight, water, and carbon dioxide to create oxygen and energy."
        result = run_dyslexia_pipeline(text, self.processor)
        
        # Depending on the exact grade of the first mock return, it might or might not refine.
        # "Plants perform photosynthesis to harness light energy. They transform water and carbon dioxide into sugar."
        # This has a grade of ~10, so it SHOULD trigger a refinement.
        self.assertTrue(result.refinement_required)
        self.assertEqual(result.refinement_count, 1)
        self.assertEqual(result.simplified_text, "Plants use light to make food. This is called photosynthesis. It needs water and air.")
        self.assertTrue(result.final_analysis.flesch_kincaid_grade < 8.0)

    def test_highly_complex_text(self):
        # We inject "Highly Complex" for the mock
        text = (
            "Highly Complex: Photosynthesis is a fundamental biological process utilized by plants to harness energy "
            "from sunlight and convert it into chemical energy via complex mechanisms."
        )
        result = run_dyslexia_pipeline(text, self.processor)
        
        # First pass returns a complex string, so it refines. Refinement returns the simple string.
        self.assertTrue(result.refinement_required)
        self.assertEqual(result.refinement_count, 1)
        self.assertTrue(result.original_analysis.flesch_kincaid_grade > 10.0)
        self.assertTrue(result.final_analysis.flesch_kincaid_grade < 8.0)

if __name__ == '__main__':
    unittest.main()
