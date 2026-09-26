import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from accessibility_rules import UserProfile
from orchestrator import OrchestrationResult
from dataclasses import asdict

def serialize_val(val: Any) -> Any:
    """Helper to ensure complex objects (like TimestampedSegment) are recursively JSON serializable."""
    if hasattr(val, '__dataclass_fields__'):
        return asdict(val)
    elif isinstance(val, list):
        return [serialize_val(x) for x in val]
    elif isinstance(val, dict):
        return {k: serialize_val(v) for k, v in val.items()}
    return val

def build_accessibility_package(
    orchestration_result: OrchestrationResult,
    profile: UserProfile
) -> Dict[str, Any]:
    """
    Builds the final standardized, JSON-serializable EquiLearn Accessibility Package
    tailored for a specific user profile.
    """
    # Safe fallback if the orchestrator entirely failed before producing final_output
    if not orchestration_result.final_output:
        return {
            "job_id": getattr(orchestration_result, "job_id", "unknown"),
            "status": orchestration_result.status,
            "warnings": orchestration_result.warnings,
            "error": orchestration_result.error_message
        }

    final_out = orchestration_result.final_output
    unified_in = final_out.unified_input
    pipeline_res = final_out.pipeline_result
    
    # Safe attribute extraction
    job_id = getattr(unified_in, "adapter_job_id", orchestration_result.job_id)
    input_type = getattr(unified_in, "adapter_input_type", "UNKNOWN")
    
    # M1 extraction
    alt_text = None
    if unified_in.member1_data:
        alt_text = unified_in.member1_data.visual_description
        
    # M2 extraction
    transcript = None
    if unified_in.member2_data:
        transcript = unified_in.member2_data.transcript
        
    captions_vtt = getattr(unified_in, "adapter_vtt", None)
    
    # Merge nested metadata
    model_metadata = {
        "m1": getattr(unified_in, "adapter_m1_metadata", {}),
        "m2": getattr(unified_in, "adapter_m2_metadata", {}),
        "m3_metrics": final_out.evaluation_metrics
    }
    
    # Analyze reading time (Avg human: 200 words/min)
    word_count = pipeline_res.original_analysis.total_words if pipeline_res.original_analysis else 0
    reading_time_mins = round(word_count / 200.0, 1) if word_count else 0.0
    
    # Extract the exact representation for the requested user profile
    rep_obj = final_out.representations.get(profile)
    recommended_reps = {}
    if rep_obj:
        raw_rep_dict = serialize_val(rep_obj)
        # Drop keys that have None values to keep the payload tight
        for k, v in raw_rep_dict.items():
            if v is not None:
                recommended_reps[k] = v
                
    # Safely aggregate all warnings from orchestration -> adapter -> NLP
    warnings = list(orchestration_result.warnings)
    adapter_warns = getattr(unified_in, "adapter_warnings", [])
    for w in adapter_warns:
        if w not in warnings:
            warnings.append(w)
    if pipeline_res.error:
        warnings.append(f"M3 Pipeline Error: {pipeline_res.error}")

    package = {
        "job_id": job_id,
        "status": orchestration_result.status,
        "input_type": input_type,
        "profile": profile.name if hasattr(profile, "name") else str(profile),
        "raw_text": pipeline_res.original_text,
        "alt_text": alt_text,
        "transcript": transcript,
        "captions_vtt": captions_vtt,
        "summary": pipeline_res.summary,
        "simplified_text": pipeline_res.simplified_text,
        "complexity_score": pipeline_res.original_analysis.flesch_kincaid_grade if pipeline_res.original_analysis else None,
        "key_terms": pipeline_res.original_analysis.key_terms if pipeline_res.original_analysis else [],
        "reading_time": f"{reading_time_mins} minutes",
        "recommended_representations": recommended_reps,
        "tts_audio_url": None, # Placeholder for future external TTS linkage
        "warnings": warnings,
        "model_metadata": model_metadata
    }
    
    return package
