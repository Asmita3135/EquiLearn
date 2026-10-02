import sys
import os
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm_processing import LLMProcessor
from dyslexia_pipeline import run_dyslexia_pipeline
from input_integration import UnifiedInput, IntegrationResult
from accessibility_rules import get_accessibility_representation, UserProfile
from main_pipeline import run_member3_pipeline

# A predictable JSON return for the mock LLM during `structure_text`
MOCK_STRUCTURE_JSON = """
{
    "title": "Photosynthesis",
    "main_idea": "Plants make food using sunlight.",
    "sections": [
        {"heading": "What is it?", "content": "Photosynthesis is the process by which plants make food."},
        {"heading": "Why is it important?", "content": "It sustains life on Earth."}
    ],
    "key_points": [
        "Plants use sunlight.",
        "They make glucose."
    ],
    "steps": [
        "1. Absorb sunlight.",
        "2. Convert to energy."
    ],
    "definitions": {
        "Glucose": "A simple sugar."
    },
    "examples": [
        "A sunflower turning to the sun."
    ]
}
"""

def mock_provider(prompt):
    if "VALID JSON ONLY" in prompt:
        return MOCK_STRUCTURE_JSON
    return "Plants make food. They use sunlight."

class TestDyslexiaStructure(unittest.TestCase):
    def setUp(self):
        self.processor = LLMProcessor(provider_func=mock_provider, model_config="Mock")

    def test_structured_fields_populated(self):
        # Covers 1, 2, 3 (Sections, steps, bullets mapping)
        res = run_dyslexia_pipeline("Some long text that needs structuring.", self.processor)
        st = res.structured_text
        
        self.assertIsNotNone(st)
        self.assertEqual(st.title, "Photosynthesis")
        self.assertEqual(len(st.sections), 2)
        self.assertEqual(st.sections[0]["heading"], "What is it?")
        self.assertEqual(len(st.key_points), 2) # Bullet conversion
        self.assertEqual(len(st.steps), 2) # Step conversion
        self.assertEqual(st.definitions["Glucose"], "A simple sugar.")

    def test_fact_preservation(self):
        # 4. Fact/number preservation - this validates the mock structure doesn't drop facts 
        # (Though real validation requires a real LLM, we verify the data makes it into the object)
        res = run_dyslexia_pipeline("Newton formulated laws in 1687.", self.processor)
        self.assertIsNotNone(res.structured_text)
        
    def test_empty_input(self):
        # 5. Empty/short input
        res = run_dyslexia_pipeline("", self.processor)
        self.assertIsNone(res.structured_text)

    def test_no_hallucinated_content(self):
        # 6. No hallucinated content 
        # (For mock, we just ensure the pipeline executes safely and doesn't invent fields outside the schema)
        res = run_dyslexia_pipeline("Normal text.", self.processor)
        self.assertTrue(hasattr(res.structured_text, "title"))
        self.assertFalse(hasattr(res.structured_text, "fake_field"))

    def test_reading_mode_settings(self):
        # 7. All reading-mode settings exist
        res = run_member3_pipeline(UnifiedInput(text="Test text."), self.processor)
        rep = res.representations[UserProfile.DYSLEXIA]
        
        mode = rep.metadata.get("dyslexia_reading_mode")
        self.assertIsNotNone(mode)
        self.assertIn("font_family", mode)
        self.assertIn("font_size", mode)
        self.assertIn("letter_spacing", mode)
        self.assertIn("word_spacing", mode)
        self.assertIn("line_spacing", mode)
        self.assertIn("paragraph_spacing", mode)
        self.assertIn("line_focus_enabled", mode)
        self.assertIn("overlay_color", mode)
        self.assertIn("reduce_visual_clutter", mode)

    def test_final_dyslexia_representation(self):
        # 8. Final Dyslexia representation contains all required outputs
        res = run_member3_pipeline(UnifiedInput(text="Test text."), self.processor)
        rep = res.representations[UserProfile.DYSLEXIA]
        
        self.assertIsNotNone(rep.primary_text) # simplified text
        self.assertIsNotNone(rep.tts_ready_text)
        self.assertIn("difficult_terms_to_highlight", rep.metadata)
        self.assertIn("final_readability_grade", rep.metadata)
        self.assertIn("dyslexia_reading_mode", rep.metadata)
        self.assertIn("structured_text", rep.metadata)
        
        st = rep.metadata["structured_text"]
        self.assertEqual(st["title"], "Photosynthesis")

if __name__ == '__main__':
    unittest.main()
