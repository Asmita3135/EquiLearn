import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

_curr = Path(__file__).resolve()
_backend_dir = next((str(_p) for _p in [_curr] + list(_curr.parents) if _p.name == "backend" and _p.is_dir()), None)
if _backend_dir and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

M3_PATH = next((str(_p / "Equilearn3" / "nlp") for _p in [_curr] + list(_curr.parents) if (_p / "Equilearn3" / "nlp").is_dir()), str((_curr.parent.parent / "Equilearn3" / "nlp").resolve()))
if M3_PATH not in sys.path:
    sys.path.insert(0, M3_PATH)

from main_pipeline import run_member3_pipeline, Member3FinalOutput
from llm_processing import LLMProcessor
from integration_adapter import EquilearnAdapter

@dataclass
class OrchestrationResult:
    job_id: str
    status: str
    final_output: Optional[Member3FinalOutput] = None
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

def run_equilearn_job(
    job_id: str,
    input_type: str,
    content: Any,
    m1_pipeline: Any = None,
    m2_pipeline: Any = None,
    m3_processor: Optional[LLMProcessor] = None,
    raw_text_override: Optional[str] = None
) -> OrchestrationResult:
    """
    Core Orchestration Function for EquiLearn.
    Routes inputs dynamically based on `input_type`.
    Valid types: 'TEXT', 'IMAGE', 'PDF', 'AUDIO', 'VIDEO', 'MULTIMODAL'
    """
    warnings = []
    input_type = input_type.upper()
    
    m1_output = None
    m2_output = None
    raw_text = raw_text_override
    
    try:
        if input_type == "TEXT":
            raw_text = content if not raw_text else raw_text
            
        elif input_type in ["IMAGE", "PDF"]:
            if not m1_pipeline:
                raise ValueError("M1 Pipeline required for IMAGE/PDF processing.")
            try:
                m1_output = m1_pipeline.process(content)
            except Exception as exc:
                raise RuntimeError(f"M1 pipeline failed: {exc}")
            
        elif input_type in ["AUDIO", "VIDEO"]:
            if not m2_pipeline:
                raise ValueError(f"M2 Pipeline required for {input_type} processing.")
            try:
                m2_output = m2_pipeline.process(content)
            except Exception as exc:
                raise RuntimeError(f"M2 pipeline failed: {exc}")
            
        elif input_type == "MULTIMODAL":
            if not m1_pipeline or not m2_pipeline:
                raise ValueError("Both M1 and M2 pipelines required for MULTIMODAL processing.")
            # Assume content is a dict containing multiple references
            content_m1 = content.get("visual") if isinstance(content, dict) else content
            content_m2 = content.get("audio") if isinstance(content, dict) else content
            
            if content_m1:
                try:
                    m1_output = m1_pipeline.process(content_m1)
                except Exception as exc:
                    warnings.append(f"M1 pipeline failed: {exc}")
            else:
                warnings.append("Multimodal missing visual content.")
                
            if content_m2:
                try:
                    m2_output = m2_pipeline.process(content_m2)
                except Exception as exc:
                    warnings.append(f"M2 pipeline failed: {exc}")
            else:
                warnings.append("Multimodal missing audio content.")
                
            if not m1_output and not m2_output:
                raise RuntimeError("Both M1 and M2 pipelines failed or had missing content for MULTIMODAL processing.")
                
        else:
            raise ValueError(f"Unsupported input type: {input_type}")

        # Integration Adapter
        unified_input = EquilearnAdapter.adapt(
            job_id=job_id,
            input_type=input_type,
            m1_output=m1_output,
            m2_output=m2_output,
            raw_text=raw_text
        )
        
        # Attach any routing-level warnings to the unified input safely
        if warnings:
            if not hasattr(unified_input, "adapter_warnings"):
                setattr(unified_input, "adapter_warnings", [])
            getattr(unified_input, "adapter_warnings").extend(warnings)

        # Ensure M3 Processor is provided
        if not m3_processor:
            raise ValueError("M3 LLMProcessor is required.")

        # Final M3 NLP & Accessibility processing
        try:
            final_output = run_member3_pipeline(unified_input, m3_processor)
        except Exception as exc:
            # If M3 fails, we can't build the package
            raise RuntimeError(f"M3 pipeline failed: {exc}")
        
        status_to_return = "SUCCESS"
        if any("pipeline failed" in w for w in warnings):
            status_to_return = "PARTIAL_SUCCESS"

        return OrchestrationResult(
            job_id=job_id,
            status=status_to_return,
            final_output=final_output,
            warnings=warnings
        )
        
    except Exception as e:
        return OrchestrationResult(
            job_id=job_id,
            status="ERROR",
            error_message=str(e),
            warnings=warnings
        )
