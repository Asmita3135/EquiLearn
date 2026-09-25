import unittest
from text_analysis import analyze_text, count_syllables

class TestTextAnalysis(unittest.TestCase):

    def test_syllable_counter(self):
        self.assertEqual(count_syllables("Photosynthesis"), 5)
        self.assertEqual(count_syllables("cat"), 1)
        self.assertEqual(count_syllables("temperature"), 4)

    def test_simple_educational_text(self):
        text = "The quick brown fox jumps over the lazy dog. Dogs are very friendly pets. They love to play."
        result = analyze_text(text)
        
        # Simple text should have low complexity
        self.assertTrue(result.flesch_reading_ease > 60)
        self.assertTrue(result.flesch_kincaid_grade < 8)
        self.assertEqual(result.total_sentences, 3)
        self.assertEqual(len(result.long_sentences), 0)
        self.assertIn("Low", result.complexity_indicator)

    def test_complex_educational_text(self):
        text = (
            "Photosynthesis is a fundamental biological process utilized by plants, algae, and certain bacteria "
            "to harness energy from sunlight and convert it into chemical energy. "
            "This complex mechanism involves the transformation of carbon dioxide and water into glucose and oxygen, "
            "facilitated by the green pigment chlorophyll."
        )
        result = analyze_text(text)
        
        # Complex text should have high complexity indicators
        self.assertTrue(result.flesch_kincaid_grade > 10)
        self.assertTrue(len(result.difficult_words) > 5)
        self.assertIn("biological", result.difficult_words)
        self.assertIn("photosynthesis", result.difficult_words)
        self.assertTrue(len(result.long_sentences) >= 1) # First sentence is long
        
        # Check key terms
        self.assertTrue(any("energy" in t for t in result.key_terms))
        self.assertTrue(any("photosynthesis" in t for t in result.key_terms))
        
    def test_key_term_extraction_preserves_technical(self):
        text = "Mitochondria are the powerhouse of the cell. Mitochondria generate ATP. ATP is essential."
        result = analyze_text(text)
        
        # Key terms should include technical words
        self.assertIn("mitochondria", result.key_terms)
        self.assertIn("atp", result.key_terms)
        self.assertIn("cell", result.key_terms)

    def test_ocr_noise_handling(self):
        # OCR corrupted text + technical terms
        text = "The chl0roplast performs Ph0t0synthesis. It uses nnU-Net and H2O. It is related to COVID-19."
        result = analyze_text(text)
        
        # Check that corrupted words were corrected to their proper forms
        self.assertIn("chloroplast", result.key_terms)
        self.assertIn("photosynthesis", result.key_terms)
        
        # Technical terms with numbers should be left intact
        # (they won't be modified by our conservative OCR replacement)
        words = result.difficult_words | set(result.key_terms)
        self.assertIn("nnu-net", words) # Lowercased in sets
        
        # Note: COVID-19 or H2O might not be in key_terms due to stop words/frequency, 
        # but they should not crash or be improperly substituted.
        # Let's ensure H2O is counted correctly without modification.
        # We can test `correct_ocr_token` directly for isolation.
        from text_analysis import correct_ocr_token
        self.assertEqual(correct_ocr_token("Ph0t0synthesis"), "Photosynthesis")
        self.assertEqual(correct_ocr_token("chl0roplast"), "chloroplast")
        self.assertEqual(correct_ocr_token("nnU-Net"), "nnU-Net")
        self.assertEqual(correct_ocr_token("H2O"), "H2O")
        self.assertEqual(correct_ocr_token("COVID-19"), "COVID-19")
        self.assertEqual(correct_ocr_token("b1ood"), "blood") # 1->l

if __name__ == '__main__':
    unittest.main()
