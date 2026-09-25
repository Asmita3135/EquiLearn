"""
Audio Preprocessor Module.

Preprocesses audio signals for Whisper ASR:
1. Validates input audio file existence and readable format.
2. Resamples audio to 16000 Hz.
3. Converts multi-channel (stereo) audio to 1-channel mono.
4. Safely normalizes amplitude to avoid clipping.
5. Trims leading and trailing silence without truncating speech.
6. Saves as 16 kHz mono WAV file suitable for Whisper speech recognition.
"""

from pathlib import Path
import librosa
import numpy as np
import soundfile as sf

TARGET_SAMPLE_RATE = 16000


def preprocess_audio(
    input_audio_path: str | Path,
    output_audio_path: str | Path | None = None,
    target_sr: int = TARGET_SAMPLE_RATE,
    top_db: float = 30.0,
) -> str:
    """
    Preprocesses an audio file into a 16kHz mono, normalized, silence-trimmed WAV file.

    Args:
        input_audio_path: Path to raw input audio file.
        output_audio_path: Optional destination path for the preprocessed WAV file.
                           If None, appends '_preprocessed.wav' to the input filename.
        target_sr: Target sample rate in Hz (default 16000 Hz).
        top_db: Silence threshold in decibels for trimming (default 30.0 dB).

    Returns:
        str: Absolute file path to the preprocessed WAV audio file.

    Raises:
        FileNotFoundError: If the input audio file does not exist.
        ValueError: If input path is not a file or audio format is invalid.
        RuntimeError: If librosa/soundfile fails to read or write the audio file.
    """
    input_p = Path(input_audio_path).resolve()

    # 1. Input validation
    if not input_p.exists():
        raise FileNotFoundError(
            f"Input Error: Audio file does not exist at '{input_audio_path}'."
        )

    if not input_p.is_file():
        raise ValueError(
            f"Input Error: Provided path '{input_audio_path}' is a directory, not a file."
        )

    # 2 & 3. Load audio with resampling to target_sr and mono conversion
    try:
        y, sr = librosa.load(str(input_p), sr=target_sr, mono=True)
    except Exception as e:
        raise RuntimeError(
            f"Audio Read Error: Failed to read audio file '{input_p.name}': {e}"
        )

    # Handle completely empty audio array
    if y is None or len(y) == 0:
        y = np.zeros(int(target_sr * 0.5), dtype=np.float32)

    # 4. Silence trimming (leading & trailing silence)
    try:
        y_trimmed, _ = librosa.effects.trim(y, top_db=top_db)
        if len(y_trimmed) > 0:
            y = y_trimmed
    except Exception:
        pass

    # 5. Safe amplitude normalization
    max_val = np.max(np.abs(y))
    if max_val > 1e-6:
        y = y / max_val * 0.95

    # 6. Determine output file path
    if output_audio_path is None:
        out_p = input_p.with_name(f"{input_p.stem}_preprocessed.wav")
    else:
        out_p = Path(output_audio_path).resolve()

    # Ensure parent directory exists
    try:
        out_p.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(
            f"Output Error: Failed to create output directory '{out_p.parent}': {e}"
        )

    # Save as 16 kHz mono PCM WAV
    try:
        sf.write(str(out_p), y, samplerate=target_sr, subtype="PCM_16")
    except Exception as e:
        raise RuntimeError(
            f"Audio Write Error: Failed to write output WAV file '{out_p.name}': {e}"
        )

    if not out_p.exists() or out_p.stat().st_size == 0:
        raise RuntimeError(
            f"Output Error: Preprocessed file '{out_p.name}' was not created or is empty."
        )

    return str(out_p)

