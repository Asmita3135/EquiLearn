import re
from dataclasses import dataclass
from typing import List, Set
from collections import Counter
from text_preprocessing import preprocess_text, PreprocessedText

# A minimal list of standard English stop words for key-term extraction
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll",
    "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd",
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves", "can", "will", "just"
}

@dataclass
class TextAnalysisResult:
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    avg_sentence_length: float
    total_words: int
    total_sentences: int
    long_sentences: List[str]
    difficult_words: Set[str]
    complexity_indicator: str
    key_terms: List[str]

def count_syllables(word: str) -> int:
    """A heuristic rule-based syllable counter."""
    word = word.lower()
    # Remove trailing punctuation
    word = re.sub(r'[^a-z]', '', word)
    if not word:
        return 0
        
    count = 0
    vowels = "aeiouy"
    
    # Handle first letter
    if word[0] in vowels:
        count += 1
        
    # Handle rest of the word
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
            
    # Handle silent 'e'
    if word.endswith("e") and count > 1 and not word.endswith("le"):
        count -= 1
        
    if count == 0:
        count = 1
        
    return count

def correct_ocr_token(token: str) -> str:
    """
    Lightweight, conservative OCR noise handler.
    Targets specific digit-for-letter substitutions (0->o, 1->l, 5->s, 8->b)
    only when they are flanked by letters.
    """
    if not re.search(r'\d', token):
        return token
        
    corrected = re.sub(r'(?<=[a-zA-Z])0(?=[a-zA-Z])', 'o', token)
    corrected = re.sub(r'(?<=[a-zA-Z])1(?=[a-zA-Z])', 'l', corrected)
    corrected = re.sub(r'(?<=[a-zA-Z])5(?=[a-zA-Z])', 's', corrected)
    corrected = re.sub(r'(?<=[a-zA-Z])8(?=[a-zA-Z])', 'b', corrected)
    
    if corrected != token:
        # High confidence check: if it now looks like a normal word (letters + optional hyphens)
        if corrected.replace('-', '').isalpha():
            return corrected
            
    # If confidence is low or no standard changes were made, leave unchanged
    return token

def analyze_text(text: str) -> TextAnalysisResult:
    """
    Analyzes the text for readability, complexity, and key terms.
    Returns a heuristic-based structural analysis.
    """
    preprocessed = preprocess_text(text)
    
    # Edge case: Empty or too short text
    if preprocessed.word_count == 0 or preprocessed.sentence_count == 0:
        return TextAnalysisResult(0.0, 0.0, 0.0, 0, 0, [], set(), "Unknown", [])
        
    # Extract tokens that contain at least one letter (allowing numbers and hyphens)
    raw_tokens = re.findall(r'\b[a-zA-Z0-9-]+\b', preprocessed.cleaned_text)
    tokens = [t for t in raw_tokens if re.search(r'[a-zA-Z]', t)]
    
    # Generate separate normalized representation for analysis
    words = [correct_ocr_token(t) for t in tokens]
    
    total_words = len(words)
    total_sentences = preprocessed.sentence_count
    
    # Ensure minimum 1 for division safety
    total_words = max(total_words, 1)
    
    total_syllables = sum(count_syllables(w) for w in words)
    
    # 1. Readability Scores
    # Flesch Reading Ease
    flesch_ease = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
    # Flesch-Kincaid Grade Level
    flesch_grade = 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59
    
    avg_sentence_length = total_words / total_sentences
    
    # 2. Complexity Analysis
    long_sentences = []
    for sentence in preprocessed.sentences:
        sentence_words = re.findall(r'\b\w+\b', sentence)
        if len(sentence_words) > 20: # Arbitrary heuristic for long sentences
            long_sentences.append(sentence)
            
    difficult_words = set()
    for word in words:
        if count_syllables(word) >= 3:
            difficult_words.add(word.lower())
            
    # Derive an overall complexity heuristic
    percent_difficult = len(difficult_words) / total_words if total_words > 0 else 0
    if flesch_grade >= 12 or percent_difficult > 0.15:
        complexity_indicator = "High (College/Professional Level)"
    elif flesch_grade >= 8:
        complexity_indicator = "Medium (High School Level)"
    else:
        complexity_indicator = "Low (Middle School or below)"
        
    # 3. Key-term Extraction
    # Frequency-based extraction ignoring stop words
    term_frequencies = Counter()
    for word in words:
        w_lower = word.lower()
        if w_lower not in STOP_WORDS and len(w_lower) > 2:
            # Preserve original casing if mostly technical
            term_frequencies[w_lower] += 1
            
    # Get top 5-10 terms as key terms
    key_terms = [term for term, _ in term_frequencies.most_common(10)]
    
    return TextAnalysisResult(
        flesch_reading_ease=round(flesch_ease, 2),
        flesch_kincaid_grade=round(flesch_grade, 2),
        avg_sentence_length=round(avg_sentence_length, 2),
        total_words=total_words,
        total_sentences=total_sentences,
        long_sentences=long_sentences,
        difficult_words=difficult_words,
        complexity_indicator=complexity_indicator,
        key_terms=key_terms
    )
