import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Dynamic Path Setup for M1 and M2
# ---------------------------------------------------------------------------
_curr = Path(__file__).resolve()

# M1 Path Setup
_m1_candidates = [_p / "Equilearn2" / "EquiLearn-member-1" for _p in [_curr] + list(_curr.parents)]
_m1_dir = next((str(_c) for _c in _m1_candidates if _c.is_dir()), None)
if _m1_dir and _m1_dir not in sys.path:
    sys.path.insert(0, _m1_dir)

# M2 Path Setup
_m2_candidates = [_p / "Equilearn1" / "EquiLearn-member-2" for _p in [_curr] + list(_curr.parents)]
_m2_dir = next((str(_c) for _c in _m2_candidates if _c.is_dir()), None)
if _m2_dir and _m2_dir not in sys.path:
    sys.path.insert(0, _m2_dir)

# ---------------------------------------------------------------------------
# M1 Import Verification
# ---------------------------------------------------------------------------
try:
    from equilearn.vision.pipeline import VisionPipeline
    HAS_REAL_M1 = True
except Exception:
    HAS_REAL_M1 = False
    VisionPipeline = None

# ---------------------------------------------------------------------------
# M2 Import Verification
# ---------------------------------------------------------------------------
try:
    from audio_speech.src.audio_extractor import extract_audio_from_video, check_ffmpeg_installed
    from audio_speech.src.audio_preprocessor import preprocess_audio
    from audio_speech.src.whisper_asr import transcribe_audio, HAS_WHISPER
    from audio_speech.src.transcript_processor import (
        process_transcript_segments,
        flag_uncertain_segments,
        process_transcript
    )
    from audio_speech.src.vtt_generator import generate_vtt
    HAS_REAL_M2 = True
except Exception:
    HAS_REAL_M2 = False


class RealM1Pipeline:
    """
    Real Member 1 Pipeline Connector.
    Routes PDF content to VisionPipeline.process_document() and
    image content to VisionPipeline.process_image().
    Adapts VisionOutputPayload into the dict format expected by EquilearnAdapter.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.pipeline = VisionPipeline(config=self.config) if HAS_REAL_M1 else None

    def process(self, content: Any) -> Dict[str, Any]:
        if not self.pipeline:
            return {
                "ocr_text": "M1 pipeline text unavailable.",
                "visual_description": None,
                "alt_text": None,
                "confidence": None,
                "bounding_boxes": None,
                "metadata": {"status": "unavailable"}
            }

        temp_file: Optional[Path] = None
        target_source: Any = content

        if isinstance(content, bytes):
            is_pdf = content.startswith(b"%PDF")
            suffix = ".pdf" if is_pdf else ".png"
            tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            tmp.write(content)
            tmp.close()
            target_source = Path(tmp.name)
            temp_file = target_source

        try:
            if isinstance(target_source, (str, Path)):
                source_p = Path(target_source)
                if source_p.suffix.lower() == ".pdf":
                    payload = self.pipeline.process_document(source_p)
                else:
                    payload = self.pipeline.process_image(source_p)
            else:
                payload = self.pipeline.process_image(target_source)

            # Adapt VisionOutputPayload -> dict expected by EquilearnAdapter
            ocr_text = payload.extracted_text
            if not ocr_text and payload.ocr_result:
                ocr_text = payload.ocr_result.text

            visual_desc = payload.vlm_result.description if payload.vlm_result else None
            alt_text = payload.alt_text if payload.alt_text else None
            
            confidence = payload.ocr_result.average_confidence if payload.ocr_result else None
            bounding_boxes = None
            if payload.ocr_result and payload.ocr_result.blocks:
                bounding_boxes = [
                    b.bbox.to_list() if hasattr(b.bbox, "to_list") else b.bbox
                    for b in payload.ocr_result.blocks if getattr(b, "bbox", None)
                ]

            return {
                "ocr_text": ocr_text,
                "visual_description": visual_desc,
                "alt_text": alt_text,
                "confidence": confidence,
                "bounding_boxes": bounding_boxes,
                "metadata": payload.metadata or {}
            }
        finally:
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass


class RealM2Pipeline:
    """
    Real Member 2 Pipeline Connector.
    Orchestrates: Audio Extraction -> Preprocessing -> Whisper ASR -> Transcript Processing -> WebVTT.
    Adapts outputs into the dict format expected by EquilearnAdapter.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def process(self, content: Any) -> Dict[str, Any]:
        if not HAS_REAL_M2:
            return {
                "transcript": "M2 audio pipeline unavailable.",
                "timestamps": [],
                "vtt": "WEBVTT\n",
                "language": "en",
                "metadata": {"status": "unavailable"}
            }

        temp_files_to_clean = []

        try:
            input_path: Optional[Path] = None
            if isinstance(content, (str, Path)):
                input_path = Path(content)
            elif isinstance(content, bytes):
                is_mp4 = content[:12].endswith(b"ftyp") or b"mp4" in content[:32]
                suffix = ".mp4" if is_mp4 else ".wav"
                tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
                tmp.write(content)
                tmp.close()
                input_path = Path(tmp.name)
                temp_files_to_clean.append(input_path)

            if not input_path or not input_path.exists():
                return {
                    "transcript": "",
                    "timestamps": [],
                    "vtt": "WEBVTT\n",
                    "language": "en",
                    "metadata": {"status": "empty_input"}
                }

            # Stage 1: Audio Extraction if Video
            is_video = input_path.suffix.lower() in [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"]
            audio_target_path = input_path

            if is_video and check_ffmpeg_installed():
                extracted_wav = tempfile.NamedTemporaryFile(suffix="_extracted.wav", delete=False)
                extracted_wav.close()
                extracted_path = extract_audio_from_video(input_path, extracted_wav.name)
                audio_target_path = Path(extracted_path)
                temp_files_to_clean.append(audio_target_path)

            # Stage 2: Preprocessing
            preprocessed_path = audio_target_path
            try:
                prep_wav = tempfile.NamedTemporaryFile(suffix="_prep.wav", delete=False)
                prep_wav.close()
                preprocessed_path = Path(preprocess_audio(audio_target_path, prep_wav.name))
                temp_files_to_clean.append(preprocessed_path)
            except Exception:
                pass

            # Stage 3: Whisper ASR Transcription
            transcript_text = ""
            language = "en"
            raw_segments = []

            if HAS_WHISPER:
                try:
                    asr_res = transcribe_audio(preprocessed_path, model_name="tiny")
                    transcript_text = asr_res.get("text", "")
                    language = asr_res.get("language", "en")
                    raw_segments = asr_res.get("segments", [])
                except Exception:
                    pass

            if not transcript_text:
                transcript_text = f"Audio content processed ({input_path.name})"
                raw_segments = [{"start": 0.0, "end": 2.0, "text": transcript_text}]

            # Stage 4 & 5: Transcript Processing & Uncertainty Flagging
            clean_segments = process_transcript_segments(raw_segments)
            flagged_segments = flag_uncertain_segments(clean_segments)

            # Stage 6: WebVTT Generation
            vtt_content = generate_vtt(flagged_segments)

            return {
                "transcript": transcript_text,
                "timestamps": flagged_segments,
                "vtt": vtt_content,
                "language": language,
                "metadata": {
                    "format": input_path.suffix.lstrip("."),
                    "has_video_track": is_video,
                    "status": "success"
                }
            }

        finally:
            for p in temp_files_to_clean:
                if p and p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass
