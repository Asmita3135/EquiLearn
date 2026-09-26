/**
 * Data structures mirroring Member 2 (audio_speech) Python pipeline outputs.
 * Inspected from: EquiLearn-Mmber 2/audio_speech/src/
 */

export interface Member2WhisperSegment {
  start: number;           // Start timestamp in seconds (rounded to 2 decimals)
  end: number;             // End timestamp in seconds (rounded to 2 decimals)
  text: string;            // Recognized and cleaned transcript string
  no_speech_prob?: number; // Segment uncertainty probability (0.0 to 1.0)
  needs_review?: boolean;  // Flag set if no_speech_prob >= 0.5
}

export interface Member2ASRResult {
  text: string;            // Full combined transcript text
  language: string;        // Detected language code (e.g. 'en')
  segments: Member2WhisperSegment[]; // Segment list from transcript_processor.py
}

export interface Member2PipelineResult {
  extractedAudioPath?: string;   // Output path from audio_extractor.py
  preprocessedAudioPath?: string;// Output path from audio_preprocessor.py (16kHz mono WAV)
  asrResult: Member2ASRResult;   // Result from whisper_asr.py & transcript_processor.py
  vttContent: string;            // WebVTT formatted document string from vtt_generator.py
  ttsAudioUrl?: string;          // Output path/URL from tts_engine.py (gTTS synthesized audio)
}
