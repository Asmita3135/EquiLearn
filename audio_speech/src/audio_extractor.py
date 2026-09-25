"""
Audio Extractor Module.

Extracts raw audio tracks from video files using FFmpeg.
"""

from pathlib import Path
import shutil
import subprocess

SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".flv",
    ".wmv",
    ".webm",
    ".m4v",
}


def check_ffmpeg_installed() -> bool:
    """
    Checks if FFmpeg executable is available on the system PATH.

    Returns:
        bool: True if FFmpeg is installed and accessible, False otherwise.
    """
    return shutil.which("ffmpeg") is not None


def extract_audio_from_video(
    video_path: str | Path, output_audio_path: str | Path | None = None
) -> str:
    """
    Extracts the audio track from a video file and saves it as a WAV file using FFmpeg.

    Args:
        video_path: Path to the input video file (e.g., sample.mp4).
        output_audio_path: Optional destination path for the extracted WAV audio file.
                           If None, saves alongside the video file with a .wav extension.

    Returns:
        str: Absolute file path to the extracted WAV audio file.

    Raises:
        FileNotFoundError: If the input video file does not exist.
        EnvironmentError: If FFmpeg is not installed on the system.
        ValueError: If the file extension is not a supported video format.
        RuntimeError: If FFmpeg fails, video lacks an audio stream, or output fails.
    """
    # 1. Verify FFmpeg installation
    if not check_ffmpeg_installed():
        raise EnvironmentError(
            "FFmpeg Error: 'ffmpeg' executable was not found on your system PATH.\n"
            "Please ensure FFmpeg is installed and added to your System Environment Variables."
        )

    video_p = Path(video_path).resolve()

    # 2. Verify input file existence
    if not video_p.exists():
        raise FileNotFoundError(
            f"Input Error: The specified video file does not exist at '{video_path}'."
        )

    if not video_p.is_file():
        raise FileNotFoundError(
            f"Input Error: The specified path '{video_path}' is a directory, not a file."
        )

    # 3. Verify supported format
    if video_p.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
        supported_str = ", ".join(sorted(SUPPORTED_VIDEO_EXTENSIONS))
        raise ValueError(
            f"Format Error: '{video_p.suffix}' is not a recognized video format.\n"
            f"Supported video extensions are: {supported_str}"
        )

    # 4. Determine output audio path
    if output_audio_path is None:
        out_p = video_p.with_suffix(".wav")
    else:
        out_p = Path(output_audio_path).resolve()

    # Ensure output parent directory exists
    try:
        out_p.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(
            f"Output Error: Failed to create output directory '{out_p.parent}': {e}"
        )

    # 5. Execute FFmpeg audio extraction command
    cmd = [
        "ffmpeg",
        "-y",             # Overwrite output file without asking
        "-i", str(video_p),# Input video file
        "-vn",            # Disable video stream (audio extraction only)
        str(out_p),       # Output WAV path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except Exception as e:
        raise RuntimeError(
            f"Execution Error: Failed to run FFmpeg process: {e}"
        )

    # 6. Process FFmpeg errors and check for missing audio stream
    if result.returncode != 0:
        stderr_msg = result.stderr.strip()
        lower_err = stderr_msg.lower()

        if "does not contain any stream" in lower_err or "matches no streams" in lower_err:
            raise RuntimeError(
                f"Audio Error: Video file '{video_p.name}' contains no audio streams to extract."
            )
        
        raise RuntimeError(
            f"FFmpeg Extraction Failed for video '{video_p.name}':\n{stderr_msg}"
        )

    # 7. Check output file existence & size
    if not out_p.exists() or out_p.stat().st_size == 0:
        raise RuntimeError(
            f"Extraction Error: Extracted audio file '{out_p.name}' was not created or is empty."
        )

    return str(out_p)

