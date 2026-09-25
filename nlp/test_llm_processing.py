import unittest
from llm_processing import LLMProcessor, process_text_with_llm
from text_analysis import analyze_text

class MockLLMProvider:
    """A mock LLM provider to test the logic without actual API calls/keys."""
    def __init__(self, simulate_error=False):
        self.simulate_error = simulate_error
        
    def generate(self, prompt: str) -> str:
        if self.simulate_error:
            raise ConnectionError("Mock connection timeout to API.")
            
        if "Summarize" in prompt:
            return "This is a mock summary preserving technical terms."
        elif "Simplify" in prompt:
            return "This is a mock simplification using easier words and shorter sentences."
        return "Unknown prompt."

class TestLLMProcessing(unittest.TestCase):

    def setUp(self):
        self.mock_provider = MockLLMProvider()
        self.processor = LLMProcessor(
            provider_func=self.mock_provider.generate,
            model_config="MockModel-1.0 (Testing Mode)"
        )
        self.sample_text = (
            "Photosynthesis is a fundamental biological process utilized by plants to harness energy "
            "from sunlight and convert it into chemical energy."
        )

    def test_successful_llm_processing(self):
        result = process_text_with_llm(self.sample_text, self.processor)
        
        self.assertIsNone(result.error)
        self.assertEqual(result.model_config, "MockModel-1.0 (Testing Mode)")
        self.assertIn("mock summary", result.summary)
        self.assertIn("mock simplification", result.simplified_text)
        
        # Verify readability metrics change conceptually (using our mock outputs)
        original_analysis = analyze_text(self.sample_text)
        simplified_analysis = analyze_text(result.simplified_text)
        
        # Simplified text should ideally have a lower reading grade level
        self.assertTrue(simplified_analysis.flesch_kincaid_grade < original_analysis.flesch_kincaid_grade)

    def test_llm_error_handling(self):
        error_provider = MockLLMProvider(simulate_error=True)
        error_processor = LLMProcessor(
            provider_func=error_provider.generate,
            model_config="MockModel-1.0 (Testing Mode)"
        )
        
        result = process_text_with_llm(self.sample_text, error_processor)
        
        self.assertIsNotNone(result.error)
        self.assertIn("LLM Generation Error", result.error)
        self.assertIn("Mock connection timeout", result.error)
        self.assertIsNone(result.summary)
        self.assertIsNone(result.simplified_text)

if __name__ == '__main__':
    unittest.main()
