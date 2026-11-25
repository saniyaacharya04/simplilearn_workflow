#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 0B: SPEECH TRANSCRIPTION & WORD-LEVEL TIMESTAMPING
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 0B
   - Script Name: 0b_transcription.py
   - Primary Class: SpeechTranscriptionEngine (CLI Subprocess Module)
   - Pipeline Role:
     Executes automatic speech recognition (ASR) on the cleaned lecture audio.
     Extracts high-resolution segment-level and word-level timestamps (start time,
     end time, word confidence) using Whisper (local Whisper, faster-whisper, or Groq API).
     Forms the time-coded lexical foundation for filler word excision, retake detection,
     and instructional alignment.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 0A (0a_audio_cleaner.py):
       - How: Ingests normalized WAV audio via 0a_audio_cleaner_tracker.json.
       - Purpose: Ensures high transcription accuracy without noise interference.
   - Input Tracker: ppt_trackers/0a_audio_cleaner_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * Clean Audio WAV (Stage 0A):
       Location: output/<TOPIC_NAME>/{topic_id}_clean.wav
       Content: High-fidelity 16kHz/48kHz clean speech audio.
     * CLI Parameters:
       Input media (-i), output timestamps JSON (-o), engine (-e), model size (-m).

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates existence of cleaned audio file.
   - Step 2: Downsamples/resamples to 16kHz mono PCM for optimal acoustic feature extraction.
   - Step 3: Invokes Whisper ASR model with word-level timestamping flags enabled.
   - Step 4: Parses segment objects, words array, start/end floats, and probability scores.
   - Step 5: Compiles structured JSON timestamp manifest with cumulative text.
   - Step 6: Atomically updates 0b_transcription_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * {topic_id}_timestamps.json:
       Location: output/<TOPIC_NAME>/{topic_id}_timestamps.json
       Content: Word-level and segment-level timestamped transcription JSON.
     * Output Tracker:
       Location: ppt_trackers/0b_transcription_tracker.json
       Content: Atomic tracker confirming completion of speech transcription.

6. DOWNSTREAM CONSUMERS:
   - Stage 0C (0c_clean_fillers_and_retakes.py): Consumes word timestamps to detect
     stumbles, retakes, and clapper slates.
   - Stage 5 (5_populate_audio_runtime.py): Uses timestamp ranges to verify sentence durations and align spoken step audio.
================================================================================
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add project root to sys.path and load environment variables
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv()
except ImportError:
    pass


def extract_audio_16k(media_path: str, output_wav: str) -> str:
    """Extracts 16kHz mono audio optimized for Whisper models."""
    Path(output_wav).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(media_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(output_wav)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(output_wav)


def transcribe_local_whisper(
    audio_path: str,
    model_size: str = "base"
) -> List[Dict[str, Any]]:
    """Transcribes audio locally using faster-whisper with word timestamps."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError(
            "Local Whisper dependency 'faster-whisper' is not installed.\n"
            "Options to resolve:\n"
            "  1. Install faster-whisper:  py -3.10 -m pip install faster-whisper\n"
            "  2. Or use Groq Whisper (free & fast): ensure GROQ_API_KEY is defined in .env"
        )

    print(f"[Transcription] Loading local faster-whisper model '{model_size}'...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        temperature=0.2,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    print(f"[Transcription] Detected language: {info.language} (Confidence: {info.language_probability:.2f})")

    results = []
    seg_id = 1
    for seg in segments:
        words_data = []
        if seg.words:
            for w in seg.words:
                w_str = w.word.strip()
                w_dur = round(w.end - w.start, 3)
                is_elongated = (w_dur >= 1.0) or (w_dur >= 0.85 and len(w_str) <= 4)
                words_data.append({
                    "word": w_str,
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "duration": w_dur,
                    "probability": round(w.probability, 3),
                    "elongated": is_elongated
                })

        clean_text = seg.text.strip()
        if not clean_text:
            continue

        results.append({
            "id": seg_id,
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "duration": round(seg.end - seg.start, 3),
            "text": clean_text,
            "words": words_data
        })
        seg_id += 1

    return results


def transcribe_groq_whisper(audio_path: str, api_key: str = None) -> List[Dict[str, Any]]:
    """Transcribes audio using Groq cloud whisper-large-v3 API with word-level timestamps."""
    from groq import Groq

    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set.")

    client = Groq(api_key=api_key)
    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(Path(audio_path).name, f.read()),
            model="whisper-large-v3",
            temperature=0.2,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"]
        )

    tr_dict = transcription if isinstance(transcription, dict) else (
        transcription.model_dump() if hasattr(transcription, "model_dump") else transcription.__dict__
    )
    raw_segments = tr_dict.get("segments", [])
    raw_words = tr_dict.get("words", [])

    results = []
    seg_id = 1
    w_idx = 0
    num_words = len(raw_words)

    for seg in raw_segments:
        seg_dict = seg if isinstance(seg, dict) else seg.__dict__
        s_start = round(float(seg_dict.get("start", 0.0)), 3)
        s_end = round(float(seg_dict.get("end", 0.0)), 3)
        clean_text = seg_dict.get("text", "").strip()
        if not clean_text:
            continue

        seg_words = []
        while w_idx < num_words:
            w = raw_words[w_idx]
            w_dict = w if isinstance(w, dict) else w.__dict__
            w_start = round(float(w_dict.get("start", 0.0)), 3)
            w_end = round(float(w_dict.get("end", 0.0)), 3)
            if w_start <= s_end or w_end <= s_end + 0.15:
                w_str = str(w_dict.get("word", "")).strip()
                w_dur = round(w_end - w_start, 3)
                is_elongated = (w_dur >= 1.0) or (w_dur >= 0.85 and len(w_str) <= 4)
                seg_words.append({
                    "word": w_str,
                    "start": w_start,
                    "end": w_end,
                    "duration": w_dur,
                    "probability": round(float(w_dict.get("probability", 1.0)), 3) if "probability" in w_dict else 1.0,
                    "elongated": is_elongated
                })
                w_idx += 1
            else:
                break

        # Synthesize fallback word timestamps if word timestamps were absent
        if not seg_words and clean_text:
            tokens = clean_text.split()
            dur = max(0.1, s_end - s_start)
            step = dur / len(tokens)
            for i, tok in enumerate(tokens):
                seg_words.append({
                    "word": tok,
                    "start": round(s_start + i * step, 3),
                    "end": round(s_start + (i + 1) * step, 3),
                    "probability": 1.0
                })

        results.append({
            "id": seg_id,
            "start": s_start,
            "end": s_end,
            "duration": round(s_end - s_start, 3),
            "text": clean_text,
            "words": seg_words
        })
        seg_id += 1

    return results


def transcribe_audio(
    media_path: str,
    output_json: str,
    engine: str = "auto",
    model_size: str = "base"
) -> List[Dict[str, Any]]:
    """Runs complete speech transcription and timestamping workflow."""
    out_json_path = Path(output_json)
    out_json_path.parent.mkdir(parents=True, exist_ok=True)

    if out_json_path.exists() and out_json_path.stat().st_size > 1000:
        print(f"\n==================================================================")
        print(f"SPEECH TRANSCRIPTION & WORD-LEVEL TIMESTAMPS")
        print(f"==================================================================")
        with open(out_json_path, "r", encoding="utf-8") as f:
            segments = json.load(f)
        has_words = any(len(s.get("words", [])) > 0 for s in segments)
        if has_words:
            print(f"✓ Timestamps already exist: {len(segments)} segments loaded -> {output_json}\n")
            return segments
        print(f"[*] Timestamps exist but lack word-level timestamps ({len(segments)} segments, 0 words). Re-transcribing with word timestamps...")

    temp_wav = out_json_path.parent / f"{Path(media_path).stem}_16k.wav"

    print(f"\n==================================================================")
    print(f"SPEECH TRANSCRIPTION & WORD-LEVEL TIMESTAMPS")
    print(f"==================================================================")
    extract_audio_16k(media_path, str(temp_wav))

    segments = None
    if engine == "groq" or (engine == "auto" and os.getenv("GROQ_API_KEY")):
        try:
            print("[Transcription] Attempting Groq Whisper API...")
            segments = transcribe_groq_whisper(str(temp_wav))
        except Exception as e:
            print(f"[Transcription] Groq unavailable ({e}), using local faster-whisper...")

    if segments is None:
        segments = transcribe_local_whisper(str(temp_wav), model_size=model_size)

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    if temp_wav.exists():
        temp_wav.unlink()

    print(f"✓ Transcription Complete: {len(segments)} segments saved -> {output_json}\n")
    return segments


run_transcription = transcribe_audio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Speech-To-Text Transcription & Timestamps")
    parser.add_argument("-i", "--input", required=True, help="Input media file (video or audio)")
    parser.add_argument("-o", "--output", required=True, help="Output JSON timestamps file")
    parser.add_argument("-e", "--engine", choices=["auto", "local", "groq"], default="auto", help="Transcription engine")
    parser.add_argument("-m", "--model", default="base", help="Whisper model size (tiny, base, small, medium)")
    args = parser.parse_args()

    transcribe_audio(args.input, args.output, engine=args.engine, model_size=args.model)

