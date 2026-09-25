"""
Whisper ASR Module.

Handles automatic speech recognition using OpenAI Whisper pretrained model.
Generates full transcript, segment timestamps, and detected language.
"""

from pathlib import Path
import whisper


def load_whisper_model(model_name: str = "tiny"):
    """
    Loads pretrained OpenAI Whisper model.

    Args:
        model_name: Whisper model size ('tiny', 'base', 'small', 'medium', 'large-v3').

    Returns:
        Loaded Whisper model instance.
    """
    try:
        model = whisper.load_model(model_name)
        return model
    except Exception as e:
        raise RuntimeError(f"Whisper Model Load Error ('{model_name}'): {e}")


def transcribe_audio(
    audio_path: str | Path, model_name: str = "tiny"
) -> dict:
    """
    Transcribes audio file using OpenAI Whisper ASR model.

    Args:
        audio_path: Path to preprocessed 16kHz mono audio file.
        model_name: Whisper model size name (default 'tiny').

    Returns:
        dict: Dictionary containing:
              - 'text': Recognized text string (stripped)
              - 'language': Detected language code (e.g., 'en')
              - 'segments': Raw segment list with timestamps
              - 'raw_result': Complete Whisper output dictionary

    Raises:
        FileNotFoundError: If the audio file does not exist.
        ValueError: If audio_path is a directory or invalid file.
        RuntimeError: If Whisper transcription fails.
    """
    audio_p = Path(audio_path).resolve()

    # 1. Input validation
    if not audio_p.exists():
        raise FileNotFoundError(
            f"Input Error: Audio file does not exist at '{audio_path}'."
        )

    if not audio_p.is_file():
        raise ValueError(
            f"Input Error: Provided path '{audio_path}' is a directory, not a file."
        )

    # 2. Load model
    model = load_whisper_model(model_name)

    # 3. Perform transcription
    try:
        raw_result = model.transcribe(str(audio_p))
    except Exception as e:
        raise RuntimeError(
            f"Whisper Transcription Error for '{audio_p.name}': {e}"
        )

    text = raw_result.get("text", "").strip()
    language = raw_result.get("language", "unknown")
    segments = raw_result.get("segments", [])

    return {
        "text": text,
        "language": language,
        "segments": segments,
        "raw_result": raw_result,
    }


