"""
Text-To-Speech (TTS) Engine Module.

Handles Text-to-Speech synthesis using Google Text-to-Speech (gTTS)
to produce spoken audio files for blind/low-vision accessibility.
"""

from pathlib import Path
from gtts import gTTS


def text_to_speech(
    text: str | None, output_path: str | Path, language: str = "en"
) -> str:
    """
    Synthesizes text into an audio file using gTTS.

    Args:
        text: Input text string to synthesize.
        output_path: Path where the output audio file (e.g. .mp3) should be saved.
        language: Language code for synthesis (default 'en').

    Returns:
        str: Absolute file path to the generated audio file.

    Raises:
        ValueError: If input text is empty or None.
        RuntimeError: If gTTS synthesis or file saving fails.
    """
    if text is None:
        raise ValueError("TTS Error: Input text cannot be empty.")

    clean_text = str(text).strip()
    if not clean_text:
        raise ValueError("TTS Error: Input text cannot be empty or whitespace-only.")

    out_p = Path(output_path).resolve()

    # Ensure parent output directory exists
    try:
        out_p.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(
            f"TTS Output Error: Failed to create output directory '{out_p.parent}': {e}"
        )

    # Perform gTTS synthesis
    try:
        tts = gTTS(text=clean_text, lang=language)
        tts.save(str(out_p))
    except Exception as e:
        raise RuntimeError(f"gTTS Synthesis Failed: {e}")

    # Check output file existence & size
    if not out_p.exists() or out_p.stat().st_size == 0:
        raise RuntimeError(
            f"TTS Error: Generated audio file '{out_p.name}' was not created or is empty."
        )

    return str(out_p)


def synthesize_speech(
    text: str | None, output_path: str | Path, lang: str = "en"
) -> str:
    """Alias for text_to_speech function."""
    return text_to_speech(text=text, output_path=output_path, language=lang)

