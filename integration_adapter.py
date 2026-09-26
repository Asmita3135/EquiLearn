import sys
from pathlib import Path
from typing import Dict, Any, Optional

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from input_integration import UnifiedInput, Member1Input, Member2Input, TimestampedSegment
from integration_schema import IntegrationContract

class EquilearnAdapter:
    @staticmethod
    def adapt(
        job_id: str,
        input_type: str,
        m1_output: Optional[Any] = None,
        m2_output: Optional[Any] = None,
        raw_text: Optional[str] = None
    ) -> UnifiedInput:
        """
        Receives disparate outputs from M1, M2, and raw text.
        Normalizes and combines them into exactly the input structure expected by M3.
        Does not execute any AI processing.
        """
        
        # --- Safely Handle Malformed or Missing Data ---
        m1 = m1_output if isinstance(m1_output, dict) else {}
        m2 = m2_output if isinstance(m2_output, dict) else {}

        # --- Extract M1 Information ---
        ocr_text = m1.get("ocr_text")
        visual_description = m1.get("visual_description")
        alt_text = m1.get("alt_text")
        
        # Build M1 metadata carefully
        ocr_metadata = m1.get("metadata", {})
        if not isinstance(ocr_metadata, dict):
            ocr_metadata = {}
            
        confidence = m1.get("confidence")
        if confidence is not None:
            ocr_metadata["confidence"] = confidence
            
        bounding_boxes = m1.get("bounding_boxes")
        if bounding_boxes is not None:
            ocr_metadata["bounding_boxes"] = bounding_boxes

        # Preserve visual description & alt_text (do not overwrite OCR text)
        combined_vd = visual_description
        if alt_text:
            alt_str = f"[Alt Text: {alt_text}]"
            combined_vd = f"{combined_vd}\n{alt_str}" if combined_vd else alt_str

        m1_input = None
        if ocr_text or combined_vd:
            m1_input = Member1Input(ocr_text=ocr_text, visual_description=combined_vd)

        # --- Extract M2 Information ---
        transcript = m2.get("transcript")
        raw_segments = m2.get("timestamps")
        vtt = m2.get("vtt")
        
        m2_metadata = m2.get("metadata", {})
        if not isinstance(m2_metadata, dict):
            m2_metadata = {}
            
        language = m2.get("language")
        if language:
            m2_metadata["language"] = language

        # Normalize timestamps safely
        segments = None
        if raw_segments and isinstance(raw_segments, list):
            segments = []
            for seg in raw_segments:
                try:
                    if isinstance(seg, dict):
                        segments.append(TimestampedSegment(float(seg.get("start", 0.0)), float(seg.get("end", 0.0)), str(seg.get("text", ""))))
                    elif isinstance(seg, TimestampedSegment):
                        segments.append(seg)
                    elif isinstance(seg, (list, tuple)) and len(seg) >= 3:
                        segments.append(TimestampedSegment(float(seg[0]), float(seg[1]), str(seg[2])))
                except (ValueError, TypeError):
                    continue # Skip invalid segment gracefully

        m2_input = None
        if transcript: # Never overwrite transcript with OCR text
            m2_input = Member2Input(transcript=transcript, segments=segments)

        # --- Avoid Duplicate Text ---
        final_raw_text = raw_text
        if final_raw_text:
            # If the provided raw text is identical to transcript or OCR, it is redundant
            if transcript and final_raw_text.strip() == transcript.strip():
                final_raw_text = None
            elif ocr_text and final_raw_text and final_raw_text.strip() == ocr_text.strip():
                final_raw_text = None

        # --- Produce Exactly the Input Structure Expected by M3 ---
        unified_input = UnifiedInput(
            text=final_raw_text,
            member1_data=m1_input,
            member2_data=m2_input
        )

        # --- Preserve Important Metadata Safely ---
        # We attach the extended attributes safely to the resulting M3 object 
        # so they are not lost for potential downstream processing or auditing.
        setattr(unified_input, "adapter_job_id", job_id)
        setattr(unified_input, "adapter_input_type", input_type)
        setattr(unified_input, "adapter_vtt", vtt)
        setattr(unified_input, "adapter_m1_metadata", ocr_metadata)
        setattr(unified_input, "adapter_m2_metadata", m2_metadata)

        return unified_input
