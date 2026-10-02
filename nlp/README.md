# EquiLearn - Member 3: NLP & Accessibility Intelligence

This package is responsible for the core text processing, NLP simplification, and deterministic accessibility routing for the EquiLearn platform.

## 1. What Member 3's Module Does
This module transforms complex, multimodal educational text into clean, structured, and accessible formats tailored for specific user needs (Blind, Deaf/Hard-of-Hearing, Low Vision, Dyslexia). It handles noise removal, readability scoring, LLM-based text simplification, and dynamic content representation.

## 2. Pipeline
The single entry point is `run_member3_pipeline` in `main_pipeline.py`. 
The pipeline executes sequentially:
1. **Input Integration**: Merges text, OCR, Visual Descriptions, and Transcripts cleanly.
2. **Preprocessing**: Normalizes unicode, removes noise, and formats whitespace.
3. **Readability & Complexity**: Calculates Flesch-Kincaid grades, syllable counts, and key terms.
4. **LLM Simplification**: Uses a configurable LLM to summarize and simplify text.
5. **Dyslexia Refinement**: Evaluates the LLM output. If the reading grade is > 8.0, it triggers a refinement loop (Max 2) to force simpler sentences.
6. **Accessibility Rules**: Deterministically packages the content uniquely for each user profile.

## 3. Inputs
The module expects a `UnifiedInput` object, which optionally contains:
- `text` (Base text)
- `member1_data` (Vision data: `ocr_text`, `visual_description`)
- `member2_data` (Audio data: `transcript`, `segments` with timestamps)

## 4. Outputs
It returns a `Member3FinalOutput` object containing:
- `unified_input`: The original preserved inputs.
- `pipeline_result`: The full analysis containing `original_text`, `simplified_text`, readability grades, and `difficult_terms`.
- `representations`: A dictionary mapping each `UserProfile` Enum to a specific `AccessibilityRepresentation` object dictating exactly what the UI should render and read aloud.
- `evaluation_metrics`: Calculated metrics (like Flesch-Kincaid) and placeholders for comparative ML metrics (SARI, ROUGE) for when a reference dataset is provided.

## 5. Modules
- `text_preprocessing.py`: Stage 1. Normalization and cleaning.
- `text_analysis.py`: Stage 2. Heuristic readability and key-term extraction.
- `llm_processing.py`: Stage 3. LLM dependency injection and prompt templates.
- `dyslexia_pipeline.py`: Stage 4. Evaluation and refinement loop.
- `input_integration.py`: Stage 5. Member 1 and Member 2 data wrappers.
- `accessibility_rules.py`: Stage 6. Profile routing logic.
- `main_pipeline.py`: Stage 7. The master coordinator.

## 6. How to Run Tests
The test suite utilizes Python's built-in `unittest` framework and uses Mock LLM providers to run rapidly without requiring API keys.
To test all components:
```bash
python -m unittest discover pattern="test_*.py"
```

## 7. Connecting Member 1 (Computer Vision) Later
When Member 1 completes the OCR and VLM modules, they simply map their outputs to the `Member1Input` dataclass:
```python
from input_integration import Member1Input, UnifiedInput

# Member 1 code produces:
m1_data = Member1Input(
    ocr_text="Found text from PDF",
    visual_description="An image of a cell."
)
unified = UnifiedInput(member1_data=m1_data)
# Pass `unified` to run_member3_pipeline
```

## 8. Connecting Member 2 (Speech Processing) Later
When Member 2 completes the Whisper/transcription modules, they map their outputs to `Member2Input`, ensuring they preserve timestamps:
```python
from input_integration import Member2Input, TimestampedSegment, UnifiedInput

# Member 2 code produces:
segments = [TimestampedSegment(0.0, 2.0, "Hello")]
m2_data = Member2Input(
    transcript="Hello",
    segments=segments
)
unified = UnifiedInput(member2_data=m2_data)
# Pass `unified` to run_member3_pipeline
```
