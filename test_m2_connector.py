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

class M2Pipeline:
    """
    Simulates the EXISTING Member 2 pipeline.
    Do not modify this internal logic.
    """
    def process(self, audio_type: str) -> dict:
        if audio_type == "clean_audio":
            return {
                "transcript": "Hello, welcome to the course.",
                "timestamps": [
                    {"start": 0.0, "end": 1.5, "text": "Hello,"},
                    {"start": 1.5, "end": 3.0, "text": "welcome to the course."}
                ],
                "vtt": "WEBVTT\n\n00:00.000 --> 00:01.500\nHello,\n\n00:01.500 --> 00:03.000\nwelcome to the course.",
                "language": "en",
                "metadata": {"format": "mp3", "sample_rate": 44100}
            }
        elif audio_type == "video":
            return {
                "transcript": "This is a video presentation.",
                "timestamps": [
                    {"start": 0.0, "end": 2.5, "text": "This is a video presentation."}
                ],
                "vtt": "WEBVTT\n\n00:00.000 --> 00:02.500\nThis is a video presentation.",
                "language": "en",
                "metadata": {"format": "mp4", "has_video_track": True}
            }
        elif audio_type == "missing_vtt":
            return {
                "transcript": "No VTT provided.",
                "timestamps": [
                    {"start": 0.0, "end": 1.0, "text": "No VTT provided."}
                ],
                "language": "en",
                "metadata": {"format": "wav"}
            }
        elif audio_type == "empty_transcript":
            return {
                "transcript": "",
                "timestamps": [],
                "vtt": "",
                "language": "en",
                "metadata": {"format": "wav", "silence": True}
            }
        return {}

class TestM2Connection(unittest.TestCase):
    def setUp(self):
        self.m2 = M2Pipeline()

    def test_clean_audio(self):
        m2_out = self.m2.process("clean_audio")
        result = EquilearnAdapter.adapt("job_1", "audio", m2_output=m2_out)
        
        self.assertEqual(result.member2_data.transcript, "Hello, welcome to the course.")
        self.assertEqual(len(result.member2_data.segments), 2)
        self.assertEqual(result.member2_data.segments[0].start_time, 0.0)
        self.assertEqual(result.adapter_vtt, m2_out["vtt"])
        self.assertEqual(result.adapter_m2_metadata["language"], "en")
        self.assertEqual(result.adapter_m2_metadata["format"], "mp3")

    def test_video(self):
        m2_out = self.m2.process("video")
        result = EquilearnAdapter.adapt("job_2", "video", m2_output=m2_out)
        
        self.assertEqual(result.member2_data.transcript, "This is a video presentation.")
        self.assertEqual(len(result.member2_data.segments), 1)
        self.assertEqual(result.adapter_vtt, m2_out["vtt"])
        self.assertEqual(result.adapter_m2_metadata["has_video_track"], True)

    def test_transcript_with_timestamps(self):
        m2_out = self.m2.process("clean_audio")
        result = EquilearnAdapter.adapt("job_3", "audio", m2_output=m2_out)
        
        seg = result.member2_data.segments[1]
        self.assertEqual(seg.start_time, 1.5)
        self.assertEqual(seg.end_time, 3.0)
        self.assertEqual(seg.text, "welcome to the course.")

    def test_missing_vtt(self):
        m2_out = self.m2.process("missing_vtt")
        result = EquilearnAdapter.adapt("job_4", "audio", m2_output=m2_out)
        
        self.assertEqual(result.member2_data.transcript, "No VTT provided.")
        self.assertIsNone(result.adapter_vtt)

    def test_empty_transcript(self):
        m2_out = self.m2.process("empty_transcript")
        result = EquilearnAdapter.adapt("job_5", "audio", m2_output=m2_out)
        
        self.assertIsNone(result.member2_data)
        self.assertEqual(result.adapter_m2_metadata["silence"], True)
        self.assertEqual(result.adapter_vtt, "")

if __name__ == '__main__':
    unittest.main()
