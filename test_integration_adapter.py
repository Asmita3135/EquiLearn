import unittest
import sys
from pathlib import Path

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from integration_adapter import EquilearnAdapter
from input_integration import TimestampedSegment

class TestIntegrationAdapter(unittest.TestCase):

    def test_m1_only(self):
        m1_data = {
            "ocr_text": "Mitochondria text",
            "visual_description": "A cell diagram",
            "alt_text": "Diagram of mitochondria",
            "confidence": 0.95,
            "bounding_boxes": [[0,0,10,10]]
        }
        result = EquilearnAdapter.adapt("job_1", "image", m1_output=m1_data)
        
        self.assertIsNone(result.text)
        self.assertIsNone(result.member2_data)
        self.assertIsNotNone(result.member1_data)
        self.assertEqual(result.member1_data.ocr_text, "Mitochondria text")
        self.assertIn("A cell diagram", result.member1_data.visual_description)
        self.assertIn("[Alt Text: Diagram of mitochondria]", result.member1_data.visual_description)
        self.assertEqual(result.adapter_m1_metadata["confidence"], 0.95)
        self.assertEqual(result.adapter_m1_metadata["bounding_boxes"], [[0,0,10,10]])

    def test_m2_only(self):
        m2_data = {
            "transcript": "Hello world",
            "timestamps": [{"start": 0.0, "end": 1.0, "text": "Hello world"}],
            "vtt": "WEBVTT\n...",
            "language": "en-US"
        }
        result = EquilearnAdapter.adapt("job_2", "audio", m2_output=m2_data)
        
        self.assertIsNone(result.text)
        self.assertIsNone(result.member1_data)
        self.assertIsNotNone(result.member2_data)
        self.assertEqual(result.member2_data.transcript, "Hello world")
        self.assertEqual(len(result.member2_data.segments), 1)
        self.assertEqual(result.member2_data.segments[0].text, "Hello world")
        self.assertEqual(result.adapter_vtt, "WEBVTT\n...")
        self.assertEqual(result.adapter_m2_metadata["language"], "en-US")

    def test_m1_and_m2(self):
        m1_data = {"ocr_text": "Screen text"}
        m2_data = {"transcript": "Spoken text"}
        result = EquilearnAdapter.adapt("job_3", "video", m1_output=m1_data, m2_output=m2_data)
        
        self.assertIsNotNone(result.member1_data)
        self.assertIsNotNone(result.member2_data)
        self.assertEqual(result.member1_data.ocr_text, "Screen text")
        self.assertEqual(result.member2_data.transcript, "Spoken text")

    def test_raw_text_only(self):
        result = EquilearnAdapter.adapt("job_4", "text", raw_text="Plain text input")
        self.assertEqual(result.text, "Plain text input")
        self.assertIsNone(result.member1_data)
        self.assertIsNone(result.member2_data)

    def test_missing_m1(self):
        # M2 and raw text present, M1 completely missing
        m2_data = {"transcript": "Spoken text"}
        result = EquilearnAdapter.adapt("job_5", "audio", m2_output=m2_data, raw_text="Plain text input")
        self.assertIsNone(result.member1_data)
        self.assertIsNotNone(result.member2_data)
        self.assertEqual(result.text, "Plain text input")

    def test_missing_m2(self):
        # M1 and raw text present, M2 missing
        m1_data = {"ocr_text": "Screen text"}
        result = EquilearnAdapter.adapt("job_6", "image", m1_output=m1_data, raw_text="Plain text input")
        self.assertIsNone(result.member2_data)
        self.assertIsNotNone(result.member1_data)
        self.assertEqual(result.text, "Plain text input")

    def test_empty_and_malformed_input(self):
        # Pass completely malformed types
        result = EquilearnAdapter.adapt(
            "job_7", 
            "unknown", 
            m1_output="malformed string instead of dict", 
            m2_output=["malformed", "list", "instead", "of", "dict"],
            raw_text=None
        )
        self.assertIsNone(result.text)
        self.assertIsNone(result.member1_data)
        self.assertIsNone(result.member2_data)
        self.assertEqual(result.adapter_m1_metadata, {})
        self.assertEqual(result.adapter_m2_metadata, {})

    def test_avoid_duplicate_text(self):
        # Test that raw text matching transcript is dropped to avoid duplication
        m2_data = {"transcript": "Identical text"}
        result = EquilearnAdapter.adapt("job_8", "audio", m2_output=m2_data, raw_text="Identical text")
        
        self.assertIsNone(result.text) # Should be dropped
        self.assertEqual(result.member2_data.transcript, "Identical text") # Transcript kept!

if __name__ == '__main__':
    unittest.main()
