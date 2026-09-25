import unittest
from text_preprocessing import preprocess_text

class TestTextPreprocessing(unittest.TestCase):

    def test_normal_educational_text(self):
        text = "Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to create oxygen and energy in the form of sugar. This process is vital for life on Earth."
        result = preprocess_text(text)
        
        self.assertEqual(result.sentence_count, 2)
        self.assertEqual(len(result.paragraphs), 1)
        self.assertEqual(result.paragraphs[0], text)
        self.assertTrue(result.word_count > 10)

    def test_text_with_extra_spaces_and_noise(self):
        text = "Here   is some text.\n\n\nIt has  way   too   many spaces.\tAnd some weird tabs."
        result = preprocess_text(text)
        
        expected_cleaned = "Here is some text.\n\nIt has way too many spaces. And some weird tabs."
        self.assertEqual(result.cleaned_text, expected_cleaned)
        self.assertEqual(len(result.paragraphs), 2)
        self.assertEqual(result.sentence_count, 3)

    def test_technical_terminology(self):
        text = "The quick brown fox jumps over the lazy dog. The specific gravity of H2O is 1.0 at 4°C! What about E=mc^2?"
        result = preprocess_text(text)
        
        self.assertEqual(result.sentence_count, 3)
        self.assertIn("H2O is 1.0", result.cleaned_text)
        self.assertIn("E=mc^2", result.cleaned_text)

    def test_multiple_paragraphs(self):
        text = "Paragraph 1 is here. It has two sentences.\n\nThis is paragraph 2. It also has two sentences."
        result = preprocess_text(text)
        
        self.assertEqual(len(result.paragraphs), 2)
        self.assertEqual(result.sentence_count, 4)
        self.assertEqual(result.paragraphs[0], "Paragraph 1 is here. It has two sentences.")
        self.assertEqual(result.paragraphs[1], "This is paragraph 2. It also has two sentences.")

if __name__ == '__main__':
    unittest.main()
