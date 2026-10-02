from dataclasses import dataclass
from typing import List, Optional
from dyslexia_pipeline import run_dyslexia_pipeline, DyslexiaPipelineResult
from llm_processing import LLMProcessor

@dataclass
class TimestampedSegment:
    start_time: float
    end_time: float
    text: str

@dataclass
class Member1Input:
    ocr_text: Optional[str] = None
    visual_description: Optional[str] = None

@dataclass
class Member2Input:
    transcript: str
    segments: Optional[List[TimestampedSegment]] = None

@dataclass
class UnifiedInput:
    text: Optional[str] = None
    member1_data: Optional[Member1Input] = None
    member2_data: Optional[Member2Input] = None

@dataclass
class IntegrationResult:
    unified_text: str
    pipeline_result: DyslexiaPipelineResult
    timestamps: Optional[List[TimestampedSegment]] = None

def unify_member1_content(member1: Member1Input) -> str:
    """
    Combines OCR text and Visual Description into a unified textual representation
    for Member 1 (Computer Vision) inputs.
    """
    parts = []
    if member1.visual_description and member1.visual_description.strip():
        parts.append(f"[Visual Description: {member1.visual_description.strip()}]")
    if member1.ocr_text and member1.ocr_text.strip():
        parts.append(member1.ocr_text.strip())
    
    return "\n\n".join(parts)

def generate_unified_text(input_data: UnifiedInput) -> str:
    """
    Extracts and logically combines all relevant textual information from the unified input object.
    """
    parts = []
    
    # Base text
    if input_data.text and input_data.text.strip():
        parts.append(input_data.text.strip())
        
    # Member 1 (Vision/OCR)
    if input_data.member1_data:
        m1_text = unify_member1_content(input_data.member1_data)
        if m1_text:
            parts.append(m1_text)
            
    # Member 2 (Speech/Audio)
    if input_data.member2_data:
        if input_data.member2_data.transcript and input_data.member2_data.transcript.strip():
            parts.append(f"[Transcript]\n{input_data.member2_data.transcript.strip()}")
            
    return "\n\n---\n\n".join(parts)

def process_integrated_input(input_data: UnifiedInput, processor: LLMProcessor) -> IntegrationResult:
    """
    1. Consolidates multi-modal text inputs into a unified representation.
    2. Runs the dyslexia transformation pipeline on the unified text.
    3. Preserves transcript timestamps.
    """
    unified_text = generate_unified_text(input_data)
    
    pipeline_result = run_dyslexia_pipeline(unified_text, processor)
    
    timestamps = None
    if input_data.member2_data and input_data.member2_data.segments:
        timestamps = input_data.member2_data.segments
        
    return IntegrationResult(
        unified_text=unified_text,
        pipeline_result=pipeline_result,
        timestamps=timestamps
    )
