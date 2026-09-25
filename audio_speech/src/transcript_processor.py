"""
Transcript Processor Module.

Formats raw Whisper output segments into clean timestamped transcript segments,
cleans whitespace, ignores empty segments, flags uncertain speech segments,
and prepares structured data for captioning.
"""


def flag_uncertain_segments(
    whisper_segments: list | None, threshold: float = 0.5
) -> list[dict]:
    """
    Flags transcript segments that have a high 'no_speech_prob' for human review.

    Args:
        whisper_segments: List of Whisper segment dictionaries.
        threshold: Floating point threshold for no_speech_prob (default 0.5).

    Returns:
        list[dict]: List of segment dictionaries updated with 'no_speech_prob'
                    and boolean 'needs_review' flag.
    """
    if not whisper_segments:
        return []

    flagged_segments = []

    for seg in whisper_segments:
        if not isinstance(seg, dict):
            continue

        raw_prob = seg.get("no_speech_prob", 0.0)
        try:
            prob = float(raw_prob) if raw_prob is not None else 0.0
        except (ValueError, TypeError):
            prob = 0.0

        needs_review = prob >= threshold

        item = dict(seg)
        item["no_speech_prob"] = round(prob, 4)
        item["needs_review"] = needs_review

        flagged_segments.append(item)

    return flagged_segments


def process_transcript_segments(whisper_segments: list | None) -> list[dict]:
    """
    Processes raw Whisper transcript segments into a clean, structured list.

    Args:
        whisper_segments: List of segment dictionaries returned by Whisper.
                          Each segment typically has 'start', 'end', and 'text'.

    Returns:
        list[dict]: Cleaned list of segment dictionaries with:
                    - 'start': float (start time in seconds)
                    - 'end': float (end time in seconds)
                    - 'text': str (cleaned transcript text)
    """
    if not whisper_segments:
        return []

    processed_segments = []

    for seg in whisper_segments:
        if not isinstance(seg, dict):
            continue

        raw_text = seg.get("text", "")
        if raw_text is None:
            continue

        clean_text = str(raw_text).strip()

        # Ignore empty or whitespace-only transcript segments
        if not clean_text:
            continue

        try:
            start_time = float(seg.get("start", 0.0))
        except (ValueError, TypeError):
            start_time = 0.0

        try:
            end_time = float(seg.get("end", 0.0))
        except (ValueError, TypeError):
            end_time = start_time

        item = {
            "start": round(start_time, 2),
            "end": round(end_time, 2),
            "text": clean_text,
        }

        if "no_speech_prob" in seg:
            try:
                prob = float(seg["no_speech_prob"])
                item["no_speech_prob"] = round(prob, 4)
                item["needs_review"] = prob >= 0.5
            except (ValueError, TypeError):
                pass

        processed_segments.append(item)

    return processed_segments


def process_transcript(asr_result: dict) -> dict:
    """
    Processes full Whisper ASR result dictionary into clean transcript data.

    Args:
        asr_result: Raw or structured dictionary from Whisper ASR.

    Returns:
        dict: Processed transcript dictionary with cleaned text and segments.
    """
    if not isinstance(asr_result, dict):
        return {"text": "", "language": "unknown", "segments": []}

    raw_text = asr_result.get("text", "").strip()
    language = asr_result.get("language", "unknown")
    raw_segments = asr_result.get("segments", [])

    clean_segments = process_transcript_segments(raw_segments)

    return {
        "text": raw_text,
        "language": language,
        "segments": clean_segments,
    }


