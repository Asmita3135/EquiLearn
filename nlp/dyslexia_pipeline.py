from dataclasses import dataclass
from typing import List, Optional
from text_preprocessing import preprocess_text
from text_analysis import analyze_text, TextAnalysisResult
from llm_processing import LLMProcessor

@dataclass
class DyslexiaPipelineResult:
    original_text: str
    original_analysis: TextAnalysisResult
    summary: Optional[str]
    simplified_text: str
    final_analysis: TextAnalysisResult
    difficult_terms: List[str]
    refinement_count: int
    refinement_required: bool
    error: Optional[str]

REFINEMENT_PROMPT = """
You are an expert educational assistant. The previous simplification was still too complex for a reader with dyslexia.
Please further simplify the following text.
Important Rules:
1. Use extremely clear, short sentences (ideally under 15 words).
2. Use very basic everyday vocabulary where possible.
3. Preserve key technical terms: {key_terms}
4. Preserve factual meaning and accuracy.
5. Do NOT remove important information or hallucinate.

Text to further simplify:
{text}
"""

def run_dyslexia_pipeline(text: str, processor: LLMProcessor) -> DyslexiaPipelineResult:
    """
    Executes the full transformation pipeline:
    Original -> Analysis -> LLM Simplify -> Analysis -> Check -> Refine (Max 2) -> Final
    """
    preprocessed = preprocess_text(text)
    if not preprocessed.cleaned_text:
        empty_analysis = analyze_text("")
        return DyslexiaPipelineResult("", empty_analysis, None, "", empty_analysis, [], 0, False, "Empty text provided.")

    original_text = preprocessed.cleaned_text
    original_analysis = analyze_text(original_text)
    
    # 1. Initial LLM Summarization and Simplification
    try:
        summary_text = processor.summarize(original_text)
        current_simplified_text = processor.simplify(original_text, original_analysis)
    except Exception as e:
        return DyslexiaPipelineResult(
            original_text, original_analysis, None, original_text, original_analysis,
            list(original_analysis.difficult_words), 0, False, f"Initial LLM Error: {str(e)}"
        )
        
    current_analysis = analyze_text(current_simplified_text)
    
    refinement_count = 0
    refinement_required = False
    MAX_REFINEMENTS = 2
    
    # 2. Refinement Loop
    while refinement_count < MAX_REFINEMENTS:
        # Check improvement / complexity. 
        # A text might be considered "still too complex" for dyslexia if the grade level > 8
        # or if there are still overly long sentences.
        is_too_complex = (current_analysis.flesch_kincaid_grade > 8.0) or (len(current_analysis.long_sentences) > 0)
        
        if not is_too_complex:
            break # The text is sufficiently simple
            
        refinement_required = True
        refinement_count += 1
        
        # Prepare refinement prompt
        prompt = REFINEMENT_PROMPT.format(
            text=current_simplified_text,
            key_terms=", ".join(original_analysis.key_terms)
        )
        
        try:
            refined_text = processor.provider_func(prompt)
            refined_analysis = analyze_text(refined_text)
            
            # Update the current best version
            current_simplified_text = refined_text
            current_analysis = refined_analysis
        except Exception as e:
            # If refinement fails, we stop refining and keep the last good version
            break

    difficult_terms = list(current_analysis.difficult_words)
    
    return DyslexiaPipelineResult(
        original_text=original_text,
        original_analysis=original_analysis,
        summary=summary_text,
        simplified_text=current_simplified_text,
        final_analysis=current_analysis,
        difficult_terms=difficult_terms,
        refinement_count=refinement_count,
        refinement_required=refinement_required,
        error=None
    )
