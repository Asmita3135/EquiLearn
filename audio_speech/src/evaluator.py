"""
ASR Evaluator Module.

Calculates Word Error Rate (WER) and evaluates transcription accuracy
against ground truth reference text.
"""

import jiwer


def calculate_wer(
    reference_text: str | None, hypothesis_text: str | None
) -> float | None:
    """
    Calculates Word Error Rate (WER) between ground truth reference and ASR hypothesis.

    Formula: WER = (Substitutions + Deletions + Insertions) / Total Reference Words

    Args:
        reference_text: Ground truth reference transcript.
        hypothesis_text: ASR generated (predicted) transcript.

    Returns:
        float | None: WER score as a float (0.0 for exact match),
                      or None if reference_text is empty/missing.
    """
    if reference_text is None:
        return None

    ref_clean = str(reference_text).strip().lower()
    hyp_clean = str(hypothesis_text).strip().lower() if hypothesis_text is not None else ""

    # Safe handling of empty reference to avoid division by zero
    if not ref_clean:
        return None

    # Handle exact match
    if ref_clean == hyp_clean:
        return 0.0

    try:
        wer_score = float(jiwer.wer(ref_clean, hyp_clean))
        return round(wer_score, 4)
    except Exception:
        ref_words = ref_clean.split()
        if not ref_words:
            return None
        hyp_words = hyp_clean.split()
        if ref_words == hyp_words:
            return 0.0
        return round(abs(len(ref_words) - len(hyp_words)) / len(ref_words), 4)

