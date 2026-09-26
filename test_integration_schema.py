import sys
import os
import unittest
from pathlib import Path

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from integration_schema import IntegrationContract
from input_integration import Member1Input, Member2Input, TimestampedSegment

class TestIntegrationContract(unittest.TestCase):
    
    def test_text_only_data(self):
        contract = IntegrationContract(
            job_id="job_001",
            input_type="text",
            raw_text="Hello world"
        )
        self.assertEqual(contract.job_id, "job_001")
        self.assertEqual(contract.input_type, "text")
        self.assertEqual(contract.raw_text, "Hello world")
        self.assertIsNone(contract.ocr_text)
        self.assertIsNone(contract.transcript)

    def test_m1_only_data(self):
        m1 = Member1Input(ocr_text="Found text", visual_description="A picture")
        contract = IntegrationContract(
            job_id="job_002",
            input_type="image",
            m1_data=m1,
            ocr_metadata_confidence={"confidence": 0.99},
            alt_text="Dog image"
        )
        self.assertEqual(contract.ocr_text, "Found text")
        self.assertEqual(contract.visual_description, "A picture")
        self.assertEqual(contract.ocr_metadata_confidence["confidence"], 0.99)
        self.assertEqual(contract.alt_text, "Dog image")
        self.assertIsNone(contract.transcript)

    def test_m2_only_data(self):
        m2 = Member2Input(
            transcript="Audio speech here", 
            segments=[TimestampedSegment(0.0, 1.0, "Audio speech here")]
        )
        contract = IntegrationContract(
            job_id="job_003",
            input_type="audio",
            m2_data=m2,
            vtt="WEBVTT\n\n00:00.000 --> 00:01.000\nAudio speech here"
        )
        self.assertEqual(contract.transcript, "Audio speech here")
        self.assertEqual(len(contract.timestamps), 1)
        self.assertIsNotNone(contract.vtt)
        self.assertIsNone(contract.ocr_text)

    def test_m1_and_m2_data(self):
        m1 = Member1Input(ocr_text="On-screen text")
        m2 = Member2Input(transcript="Spoken words")
        contract = IntegrationContract(
            job_id="job_004",
            input_type="video",
            m1_data=m1,
            m2_data=m2
        )
        self.assertEqual(contract.ocr_text, "On-screen text")
        self.assertEqual(contract.transcript, "Spoken words")

    def test_missing_optional_fields(self):
        contract = IntegrationContract(
            job_id="job_005",
            input_type="unknown"
        )
        # Verify default optionals
        self.assertIsNone(contract.raw_text)
        self.assertIsNone(contract.m1_data)
        self.assertIsNone(contract.m2_data)
        self.assertIsNone(contract.ocr_text)
        self.assertIsNone(contract.ocr_metadata_confidence)
        self.assertIsNone(contract.alt_text)
        self.assertIsNone(contract.transcript)
        self.assertIsNone(contract.timestamps)
        self.assertIsNone(contract.vtt)
        self.assertEqual(contract.source_metadata, {})
        self.assertEqual(contract.warnings, [])

    def test_empty_input(self):
        # Python dataclasses will throw a TypeError if required fields (job_id, input_type) are missing
        with self.assertRaises(TypeError):
            IntegrationContract()

if __name__ == '__main__':
    unittest.main()
