import unittest
from accessibility_rules import get_accessibility_representation, UserProfile
from input_integration import IntegrationResult, TimestampedSegment
from dyslexia_pipeline import DyslexiaPipelineResult
from text_analysis import TextAnalysisResult

class TestAccessibilityRules(unittest.TestCase):

    def setUp(self):
        # Create a mock integration result representing a fully processed educational lesson
        # This simulates outputs from Stages 1-5
        original_text = "Photosynthesis is the complex biological process where plants harness solar energy."
        simplified_text = "Plants use sunlight to make their food. This is called photosynthesis."
        
        original_analysis = TextAnalysisResult(
            flesch_reading_ease=30.0, flesch_kincaid_grade=12.0, avg_sentence_length=12.0, 
            total_words=12, total_sentences=1, long_sentences=[], 
            difficult_words={"photosynthesis", "biological"}, complexity_indicator="High", 
            key_terms=["photosynthesis", "energy", "plants"]
        )
        
        final_analysis = TextAnalysisResult(
            flesch_reading_ease=80.0, flesch_kincaid_grade=4.5, avg_sentence_length=6.0, 
            total_words=12, total_sentences=2, long_sentences=[], 
            difficult_words={"photosynthesis"}, complexity_indicator="Low", 
            key_terms=["photosynthesis", "plants"]
        )
        
        pipeline_result = DyslexiaPipelineResult(
            original_text=original_text,
            original_analysis=original_analysis,
            summary="Mock Summary",
            simplified_text=simplified_text,
            final_analysis=final_analysis,
            difficult_terms=["photosynthesis"],
            refinement_count=1,
            refinement_required=True,
            error=None
        )
        
        unified_text = (
            "[Visual Description: A diagram of a leaf absorbing sunlight and carbon dioxide.]\n\n---\n\n"
            + original_text
        )
        
        timestamps = [
            TimestampedSegment(0.0, 3.0, "Photosynthesis is the complex biological process"),
            TimestampedSegment(3.0, 6.0, "where plants harness solar energy.")
        ]
        
        self.mock_result = IntegrationResult(
            unified_text=unified_text,
            pipeline_result=pipeline_result,
            timestamps=timestamps
        )

    def test_blind_profile(self):
        rep = get_accessibility_representation(UserProfile.BLIND, self.mock_result)
        
        self.assertEqual(rep.primary_text, self.mock_result.pipeline_result.original_text)
        self.assertIn("A diagram of a leaf", rep.secondary_text)
        self.assertIn("Image Description: A diagram of a leaf", rep.tts_ready_text)
        self.assertEqual(rep.metadata["presentation_mode"], "screen_reader_optimized")

    def test_deaf_profile(self):
        rep = get_accessibility_representation(UserProfile.DEAF, self.mock_result)
        
        self.assertEqual(rep.primary_text, self.mock_result.pipeline_result.original_text)
        self.assertIsNotNone(rep.transcript_segments)
        self.assertEqual(len(rep.transcript_segments), 2)
        self.assertTrue(rep.metadata["has_synchronized_captions"])
        self.assertEqual(rep.metadata["presentation_mode"], "caption_optimized")

    def test_low_vision_profile(self):
        rep = get_accessibility_representation(UserProfile.LOW_VISION, self.mock_result)
        
        self.assertEqual(rep.primary_text, self.mock_result.pipeline_result.original_text)
        self.assertIn("A diagram of a leaf", rep.secondary_text)
        # TTS doesn't necessarily need visual description inline unless requested, but we provide base text
        self.assertEqual(rep.tts_ready_text, self.mock_result.pipeline_result.original_text)
        self.assertEqual(rep.metadata["presentation_mode"], "high_contrast_magnifiable")

    def test_dyslexia_profile(self):
        rep = get_accessibility_representation(UserProfile.DYSLEXIA, self.mock_result)
        
        # Core feature: Dyslexia profile gets the SIMPLIFIED text as primary
        self.assertEqual(rep.primary_text, self.mock_result.pipeline_result.simplified_text)
        self.assertIn(self.mock_result.pipeline_result.original_text, rep.secondary_text)
        
        # TTS gets simplified text
        self.assertEqual(rep.tts_ready_text, self.mock_result.pipeline_result.simplified_text)
        
        # Check specific metadata
        self.assertEqual(rep.metadata["final_readability_grade"], 4.5)
        self.assertIn("photosynthesis", rep.metadata["difficult_terms_to_highlight"])
        self.assertEqual(rep.metadata["presentation_mode"], "simplified_reading")

if __name__ == '__main__':
    unittest.main()
