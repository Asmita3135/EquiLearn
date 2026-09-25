from dataclasses import dataclass
from typing import Optional, Callable
from text_preprocessing import preprocess_text
from text_analysis import analyze_text, TextAnalysisResult

@dataclass
class LLMResult:
    original_text: str
    summary: Optional[str]
    simplified_text: Optional[str]
    model_config: str
    error: Optional[str]

# Explicit prompt templates enforcing the required constraints
SUMMARIZATION_PROMPT = """
You are an expert educational assistant. Summarize the following educational text concisely.
Important Rules:
1. Preserve the core meaning and factual accuracy.
2. Preserve key technical terminology.
3. Do NOT add any information not present in the text (no hallucination).
4. Keep the summary concise but informative.

Text to summarize:
{text}
"""

SIMPLIFICATION_PROMPT = """
You are an expert educational assistant. Simplify the following educational text to make it easier to understand.
Important Rules:
1. Shorten unnecessarily long sentences.
2. Use simpler vocabulary where appropriate.
3. Preserve key technical terms.
4. Preserve factual meaning and accuracy.
5. Do NOT remove important information.
6. Do NOT add unsupported information or change the meaning.

Text to simplify:
{text}

Context about the text (Stage 2 Analysis):
Complexity Level: {complexity}
Key Terms to Preserve: {key_terms}
"""

class LLMProcessor:
    def __init__(self, provider_func: Callable[[str], str], model_config: str):
        """
        Initializes the LLM processor with a generic provider function.
        This keeps the LLM provider (OpenAI, Gemini, local, etc.) fully configurable.
        
        Args:
            provider_func: A callable that takes a text prompt and returns the LLM's text response.
            model_config: A string describing the model/configuration being used.
        """
        self.provider_func = provider_func
        self.model_config = model_config
        
    def summarize(self, text: str) -> str:
        prompt = SUMMARIZATION_PROMPT.format(text=text)
        return self.provider_func(prompt)
        
    def simplify(self, text: str, analysis: TextAnalysisResult) -> str:
        prompt = SIMPLIFICATION_PROMPT.format(
            text=text,
            complexity=analysis.complexity_indicator,
            key_terms=", ".join(analysis.key_terms)
        )
        return self.provider_func(prompt)

def process_text_with_llm(text: str, processor: LLMProcessor) -> LLMResult:
    """
    Coordinates Stage 1 preprocessing, Stage 2 analysis, and Stage 3 LLM generation.
    """
    preprocessed = preprocess_text(text)
    if not preprocessed.cleaned_text:
        return LLMResult(text, None, None, processor.model_config, "Empty text provided.")
        
    analysis = analyze_text(preprocessed.cleaned_text)
    
    summary = None
    simplified = None
    error = None
    
    try:
        summary = processor.summarize(preprocessed.cleaned_text)
        simplified = processor.simplify(preprocessed.cleaned_text, analysis)
    except Exception as e:
        error = f"LLM Generation Error: {str(e)}"
        
    return LLMResult(
        original_text=preprocessed.cleaned_text,
        summary=summary,
        simplified_text=simplified,
        model_config=processor.model_config,
        error=error
    )
