"""
EquiLearn - Member 2: Audio & Speech Intelligence Main Entry Point.

Usage:
    python main.py <input_video_path> [output_wav_path]
"""

from pathlib import Path
import sys

# Ensure project root is in Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio_speech.src.audio_extractor import extract_audio_from_video
from audio_speech.src.audio_preprocessor import preprocess_audio


def main():
    print("==================================================")
    print("  EquiLearn: Audio & Speech Intelligence Module  ")
    print("  Step 2 & Step 3 — Extraction & Preprocessing   ")
    print("==================================================")

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python main.py <input_video_path> [output_wav_path]")
        print("\nExample:")
        print("  python main.py data/raw/sample.mp4 data/processed/sample_preprocessed.wav")
        return

    input_video = sys.argv[1]
    output_wav = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"\n[+] Step 2: Extracting Audio from Video: {input_video}")
    try:
        extracted_audio_path = extract_audio_from_video(input_video, output_wav)
        print(f"[OK] Extracted Audio: {extracted_audio_path}")

        print(f"\n[+] Step 3: Preprocessing Audio for Whisper ASR...")
        preprocessed_audio_path = preprocess_audio(extracted_audio_path)
        print(f"[OK] Preprocessed Audio Ready: {preprocessed_audio_path}")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


