import unittest
import sys

# M1 Mock simulating the "EXISTING" M1 pipeline
class M1Pipeline:
    """
    Simulates the EXISTING Member 1 pipeline.
    Do not modify this internal logic as per instructions.
    """
    def process(self, image_type: str) -> dict:
        if image_type == "normal_text":
            return {
                "ocr_text": "The quick brown fox",
                "confidence": 0.98,
                "bounding_boxes": [[10, 10, 100, 20]],
                "visual_description": "A page of text.",
                "alt_text": "Page with text",
                "metadata": {"source": "pdf"}
            }
        elif image_type == "noisy_text":
            return {
                "ocr_text": "Th$ qv!ck br0wn f*x",
                "confidence": 0.45,
                "bounding_boxes": [[10, 10, 100, 20]],
                "visual_description": "A blurry page of text.",
                "alt_text": "Blurry text",
                "metadata": {"source": "scanned_pdf"}
            }
        elif image_type == "diagram":
            return {
                "ocr_text": "Mitochondria",
                "confidence": 0.90,
                "bounding_boxes": [[50, 50, 120, 30]],
                "visual_description": "A diagram of a cell.",
                "alt_text": "Cell diagram",
                "metadata": {"source": "textbook_image"}
            }
        elif image_type == "missing_visual":
            return {
                "ocr_text": "Just plain text here",
                "confidence": 0.99,
                "bounding_boxes": [[0, 0, 50, 10]],
                "metadata": {"source": "screenshot"}
            }
        return {}

from integration_adapter import EquilearnAdapter

class TestM1Connection(unittest.TestCase):
    def setUp(self):
        self.m1 = M1Pipeline()

    def test_normal_text(self):
        m1_out = self.m1.process("normal_text")
        result = EquilearnAdapter.adapt("job_1", "image", m1_output=m1_out)
        
        self.assertEqual(result.member1_data.ocr_text, "The quick brown fox")
        self.assertIn("A page of text.", result.member1_data.visual_description)
        self.assertIn("[Alt Text: Page with text]", result.member1_data.visual_description)
        self.assertEqual(result.adapter_m1_metadata["confidence"], 0.98)
        self.assertEqual(result.adapter_m1_metadata["bounding_boxes"], [[10, 10, 100, 20]])

    def test_noisy_text(self):
        m1_out = self.m1.process("noisy_text")
        result = EquilearnAdapter.adapt("job_2", "image", m1_output=m1_out)
        
        self.assertEqual(result.member1_data.ocr_text, "Th$ qv!ck br0wn f*x")
        self.assertIn("A blurry page of text.", result.member1_data.visual_description)
        self.assertIn("[Alt Text: Blurry text]", result.member1_data.visual_description)
        self.assertEqual(result.adapter_m1_metadata["confidence"], 0.45)
        self.assertEqual(result.adapter_m1_metadata["bounding_boxes"], [[10, 10, 100, 20]])

    def test_diagram(self):
        m1_out = self.m1.process("diagram")
        result = EquilearnAdapter.adapt("job_3", "image", m1_output=m1_out)
        
        self.assertEqual(result.member1_data.ocr_text, "Mitochondria")
        self.assertIn("A diagram of a cell.", result.member1_data.visual_description)
        self.assertIn("[Alt Text: Cell diagram]", result.member1_data.visual_description)
        self.assertEqual(result.adapter_m1_metadata["confidence"], 0.90)
        self.assertEqual(result.adapter_m1_metadata["bounding_boxes"], [[50, 50, 120, 30]])

    def test_missing_visual(self):
        m1_out = self.m1.process("missing_visual")
        result = EquilearnAdapter.adapt("job_4", "image", m1_output=m1_out)
        
        self.assertEqual(result.member1_data.ocr_text, "Just plain text here")
        self.assertIsNone(result.member1_data.visual_description)
        self.assertEqual(result.adapter_m1_metadata["confidence"], 0.99)
        self.assertEqual(result.adapter_m1_metadata["bounding_boxes"], [[0, 0, 50, 10]])

if __name__ == '__main__':
    unittest.main()
