"""
WebVTT Generator Module.

Converts timestamped transcript segments into WebVTT (.vtt) caption format
for Deaf/Hard-of-Hearing accessibility.
"""

from pathlib import Path


def format_vtt_timestamp(seconds: float) -> str:
    """
    Formats numeric seconds into WebVTT timestamp format (HH:MM:SS.mmm).

    Args:
        seconds: Time in seconds as float or int.

    Returns:
        str: Formatted WebVTT timestamp string (e.g. '00:00:03.250').
    """
    if seconds is None or seconds < 0:
        seconds = 0.0

    total_millis = int(round(float(seconds) * 1000))
    hours = total_millis // (3600 * 1000)
    total_millis %= (3600 * 1000)

    minutes = total_millis // (60 * 1000)
    total_millis %= (60 * 1000)

    secs = total_millis // 1000
    millis = total_millis % 1000

    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def generate_vtt(segments: list | None) -> str:
    """
    Generates WebVTT caption document content from processed transcript segments.

    Args:
        segments: List of segment dictionaries containing 'start', 'end', and 'text'.

    Returns:
        str: Complete WebVTT document string starting with WEBVTT header.
    """
    vtt_lines = ["WEBVTT\n"]

    if not segments:
        return "\n".join(vtt_lines)

    for seg in segments:
        if not isinstance(seg, dict):
            continue

        start_time = float(seg.get("start", 0.0))
        end_time = float(seg.get("end", 0.0))
        text = str(seg.get("text", "")).strip()

        if not text:
            continue

        start_str = format_vtt_timestamp(start_time)
        end_str = format_vtt_timestamp(end_time)

        vtt_lines.append(f"{start_str} --> {end_str}")
        vtt_lines.append(f"{text}\n")

    return "\n".join(vtt_lines).strip() + "\n"


def save_vtt(vtt_content: str, output_path: str | Path) -> str:
    """
    Saves WebVTT content to a UTF-8 encoded .vtt file.

    Args:
        vtt_content: Complete WebVTT formatted string.
        output_path: Destination path for the .vtt file.

    Returns:
        str: Absolute file path to saved .vtt file.
    """
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    out_p.write_text(vtt_content, encoding="utf-8")
    return str(out_p)

