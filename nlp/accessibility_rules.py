import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from input_integration import IntegrationResult, TimestampedSegment

class UserProfile(Enum):
    BLIND = "blind"
    DEAF = "deaf"
    LOW_VISION = "low_vision"
    DYSLEXIA = "dyslexia"

@dataclass
class DyslexiaReadingMode:
    font_family: str = "OpenDyslexic, Comic Sans MS, Arial"
    font_size: str = "18px"
    letter_spacing: str = "0.12em"
    word_spacing: str = "0.4em"
    line_spacing: str = "1.5"
    paragraph_spacing: str = "2.0em"
    line_focus_enabled: bool = False
    overlay_color: str = "#FAFAFA"
    reduce_visual_clutter: bool = True

@dataclass
class AccessibilityRepresentation:
    """
    A structured container detailing what content to present to a specific user profile.
    """
    primary_text: str
    secondary_text: Optional[str] = None
    summary: Optional[str] = None
    visual_descriptions: List[str] = field(default_factory=list)
    key_terms: List[str] = field(default_factory=list)
    tts_ready_text: Optional[str] = None
    transcript_segments: Optional[List[TimestampedSegment]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

def get_accessibility_representation(
    profile: UserProfile, 
    integration_result: IntegrationResult
) -> AccessibilityRepresentation:
    """
    Deterministic rule-based system.
    Selects and organizes the pre-calculated NLP outputs into the optimal 
    representation format for the given user profile.
    """
    
    pipeline = integration_result.pipeline_result
    unified_text = integration_result.unified_text
    original_text = pipeline.original_text
    simplified_text = pipeline.simplified_text
    key_terms = pipeline.original_analysis.key_terms
    timestamps = integration_result.timestamps
    
    # Extract embedded visual descriptions that were formatted in Stage 5
    visual_descriptions = re.findall(r'\[Visual Description:\s*(.*?)\]', unified_text)
    
    rep = AccessibilityRepresentation(
        primary_text="",
        summary=pipeline.summary,
        visual_descriptions=visual_descriptions,
        key_terms=key_terms
    )
    
    if profile == UserProfile.BLIND:
        # BLIND: Needs full text + explicit visual descriptions + optimized TTS string
        rep.primary_text = original_text
        
        if visual_descriptions:
            rep.secondary_text = "Visual Elements: " + " | ".join(visual_descriptions)
            # Combine content and visual descriptions logically for a Screen Reader / TTS
            rep.tts_ready_text = f"Text Content: {original_text} Image Description: {' '.join(visual_descriptions)}"
        else:
            rep.tts_ready_text = original_text
            
        rep.metadata["presentation_mode"] = "screen_reader_optimized"

    elif profile == UserProfile.DEAF:
        # DEAF / HARD OF HEARING: Needs raw text + exact transcript timings for captions
        rep.primary_text = original_text
        rep.transcript_segments = timestamps
        rep.metadata["presentation_mode"] = "caption_optimized"
        rep.metadata["has_synchronized_captions"] = bool(timestamps)

    elif profile == UserProfile.LOW_VISION:
        # LOW VISION: Needs standard text (rendered large on frontend) + visual descriptions + optional TTS
        rep.primary_text = original_text
        if visual_descriptions:
            rep.secondary_text = "Visual Elements: " + " | ".join(visual_descriptions)
            
        rep.tts_ready_text = original_text
        rep.metadata["presentation_mode"] = "high_contrast_magnifiable"

    elif profile == UserProfile.DYSLEXIA:
        # DYSLEXIA: Needs the LLM-simplified text + readability metrics + key terms focused
        rep.primary_text = simplified_text
        # Keep original text accessible just in case
        rep.secondary_text = "Original Text Available: " + original_text
        # TTS string uses simplified text to make audio-tracking easier
        rep.tts_ready_text = simplified_text
        
        rep.metadata["presentation_mode"] = "simplified_reading"
        rep.metadata["final_readability_grade"] = pipeline.final_analysis.flesch_kincaid_grade
        rep.metadata["difficult_terms_to_highlight"] = pipeline.difficult_terms
        
        # New dyselxia features
        rep.metadata["dyslexia_reading_mode"] = DyslexiaReadingMode().__dict__
        if pipeline.structured_text:
            rep.metadata["structured_text"] = pipeline.structured_text.__dict__

    return rep
