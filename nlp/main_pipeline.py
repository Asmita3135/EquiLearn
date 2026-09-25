from dataclasses import dataclass
from typing import Dict

from input_integration import UnifiedInput, process_integrated_input, Member1Input, Member2Input, TimestampedSegment
from accessibility_rules import get_accessibility_representation, UserProfile, AccessibilityRepresentation
from llm_processing import LLMProcessor
from dyslexia_pipeline import DyslexiaPipelineResult

@dataclass
class Member3FinalOutput:
    """
    The complete final output package from Member 3's NLP & Accessibility Intelligence module.
    Contains the original inputs, the core NLP pipeline results, and the specific 
    accessibility representations for frontend consumption.
    """
    unified_input: UnifiedInput
    pipeline_result: DyslexiaPipelineResult
    representations: Dict[UserProfile, AccessibilityRepresentation]
    evaluation_metrics: Dict[str, str]

def run_member3_pipeline(input_data: UnifiedInput, processor: LLMProcessor) -> Member3FinalOutput:
    """
    The master pipeline function connecting all Stage 1-6 modules.
    
    Flow:
    1. Member 1/2 Input Integration
    2. Text Preprocessing
    3. Readability & Complexity Analysis
    4. Key Terms Extraction
    5. LLM Summarization & Simplification
    6. Dyslexia Refinement Loop
    7. Rule-Based Accessibility Representation Mapping
    """
    
    # 1-6: Process unified inputs and run full NLP + Dyslexia refinement pipeline
    integration_result = process_integrated_input(input_data, processor)
    pipeline_result = integration_result.pipeline_result
    
    # 7: Generate rule-based accessibility representations for all supported profiles
    representations = {}
    for profile in UserProfile:
        representations[profile] = get_accessibility_representation(profile, integration_result)
        
    # Standard metrics are calculated, but comparative metrics require reference datasets
    evaluation_metrics = {
        "Flesch_Reading_Ease": str(pipeline_result.final_analysis.flesch_reading_ease),
        "Flesch_Kincaid_Grade": str(pipeline_result.final_analysis.flesch_kincaid_grade),
        "ROUGE": "N/A (No reference summary dataset available for comparison)",
        "BERTScore": "N/A (No reference summary dataset available for comparison)",
        "SARI": "N/A (No reference simplification dataset available for comparison)"
    }
        
    return Member3FinalOutput(
        unified_input=input_data,
        pipeline_result=pipeline_result,
        representations=representations,
        evaluation_metrics=evaluation_metrics
    )
