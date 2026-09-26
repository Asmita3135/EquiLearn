# EquiLearn Integration Stage 1 Report

Based on an inspection of the existing M3 (NLP & Accessibility Intelligence) repository located in the `Equilearn3` directory, here is the assessment of the current interfaces, mismatches, and required integration points.

## 1. M1 Input/Output
**Current defined output (in M3's `Member1Input`):**
- `ocr_text` (Optional[str])
- `visual_description` (Optional[str])

**Required Output (to Adapter):** 
- OCR text, confidence, bounding boxes, visual description, alt-text, and relevant metadata.

## 2. M2 Input/Output
**Current defined output (in M3's `Member2Input`):**
- `transcript` (str)
- `segments` (Optional[List[TimestampedSegment]] containing start_time, end_time, text)

**Required Output (to Adapter):**
- Transcript, timestamps, VTT, language, and relevant metadata.

## 3. M3 Input/Output
**Entry Point:** `run_member3_pipeline(input_data: UnifiedInput, processor: LLMProcessor) -> Member3FinalOutput` in `main_pipeline.py`.
**Exact Input:** `UnifiedInput` dataclass containing `text`, `member1_data` (Member1Input), and `member2_data` (Member2Input).
**Exact Output:** `Member3FinalOutput` dataclass containing `unified_input`, `pipeline_result` (DyslexiaPipelineResult), `representations` (Dict of UserProfile to AccessibilityRepresentation), and `evaluation_metrics`.

**Required Input (from Adapter):**
- Raw text + OCR text + visual context + transcript + timestamps + metadata (only where available).

## 4. Interface Mismatches
1. **M1 Dataclass Deficiencies:** M3's current `Member1Input` is missing fields for `confidence`, `bounding_boxes`, `alt_text`, and `metadata`.
2. **M2 Dataclass Deficiencies:** M3's current `Member2Input` is missing fields for `VTT`, `language`, and `metadata`.
3. **M3 Unified Input Deficiencies:** `UnifiedInput` does not currently accept or process the general `metadata` required by the adapter, and `process_integrated_input` drops these additional properties rather than passing them through to the final output package.

## 5. Files that Should be Involved in Integration
- `Equilearn3/nlp/input_integration.py`: To update the schemas (`Member1Input`, `Member2Input`, `UnifiedInput`) and the `process_integrated_input` integration logic.
- `Equilearn3/nlp/main_pipeline.py`: To ensure M3 correctly receives and routes the new data points (like metadata and alt-text) to the final `Member3FinalOutput`.
- `Equilearn3/nlp/test/test_input_integration.py` & `test_main_pipeline.py`: To add test coverage for the newly integrated fields.
- (New) `backend/integration_adapter.py`: A new orchestration file to accept the raw outputs from M1/M2 and instantiate the updated `UnifiedInput` for M3.
