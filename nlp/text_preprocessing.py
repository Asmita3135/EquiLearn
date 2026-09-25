import re
import unicodedata
from dataclasses import dataclass
from typing import List

@dataclass
class PreprocessedText:
    original_text: str
    cleaned_text: str
    paragraphs: List[str]
    sentences: List[str]
    word_count: int
    sentence_count: int

def preprocess_text(text: str) -> PreprocessedText:
    """
    Preprocesses educational text for NLP pipelines.
    Handles unicode normalization, noise removal, whitespace normalization,
    and basic paragraph/sentence segmentation.
    """
    if not text or not text.strip():
        return PreprocessedText(text, "", [], [], 0, 0)
    
    # 1. Unicode normalization (NFKC normalizes characters like ligatures)
    text_normalized = unicodedata.normalize('NFKC', text)
    
    # 2. Remove obvious unwanted noise (control characters except newlines/tabs)
    text_no_noise = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text_normalized)
    
    # 3. Normalize whitespace and 5. Preserve paragraph boundaries
    # Split by two or more newlines to identify paragraphs
    paragraphs_raw = re.split(r'\n\s*\n+', text_no_noise)
    paragraphs = []
    
    for p in paragraphs_raw:
        # Normalize spaces/tabs to a single space
        p_clean = re.sub(r'[ \t]+', ' ', p).strip()
        # Replace single newlines within a paragraph with a space
        p_clean = re.sub(r'\n', ' ', p_clean)
        # Re-clean spaces just in case
        p_clean = re.sub(r'[ \t]+', ' ', p_clean).strip()
        if p_clean:
            paragraphs.append(p_clean)
            
    cleaned_text = '\n\n'.join(paragraphs)
    
    # 6. Split text into sentences where useful
    sentences = []
    for p in paragraphs:
        # Basic regex-based sentence splitting that handles basic punctuation
        # Avoids splitting on common abbreviations like Dr., Mr., etc. (simple heuristic)
        p_sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+', p)
        for s in p_sentences:
            s_clean = s.strip()
            if s_clean:
                sentences.append(s_clean)
                
    # Basic word and sentence counts
    word_count = len(re.findall(r'\b\w+\b', cleaned_text))
    sentence_count = len(sentences)
    
    return PreprocessedText(
        original_text=text,
        cleaned_text=cleaned_text,
        paragraphs=paragraphs,
        sentences=sentences,
        word_count=word_count,
        sentence_count=sentence_count
    )
