#!/usr/bin/env python3
"""
Step 1: Speech-To-Text Transcription & Word-Level Timestamping
Adapted from KPLOR Transcribe Engine & Timestamp Experiments.
Generates structured JSON with word-level and segment-level start/end timings.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any


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
    from faster_whisper import WhisperModel

    print(f"[Step 1] Loading local faster-whisper model '{model_size}'...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    print(f"[Step 1] Detected language: {info.language} (Confidence: {info.language_probability:.2f})")

    results = []
    seg_id = 1
    for seg in segments:
        words_data = []
        if seg.words:
            for w in seg.words:
                words_data.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3)
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
    """Transcribes audio using Groq cloud whisper-large-v3 API."""
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
            temperature=0,
            response_format="verbose_json"
        )

    results = []
    seg_id = 1
    for seg in getattr(transcription, "segments", []):
        seg_dict = seg if isinstance(seg, dict) else seg.__dict__
        results.append({
            "id": seg_id,
            "start": round(seg_dict.get("start", 0.0), 3),
            "end": round(seg_dict.get("end", 0.0), 3),
            "duration": round(seg_dict.get("end", 0.0) - seg_dict.get("start", 0.0), 3),
            "text": seg_dict.get("text", "").strip(),
            "words": seg_dict.get("words", [])
        })
        seg_id += 1

    return results


def run_stage_1(
    media_path: str,
    output_json: str,
    engine: str = "auto",
    model_size: str = "base"
) -> List[Dict[str, Any]]:
    """Runs complete Stage 1 workflow."""
    out_json_path = Path(output_json)
    out_json_path.parent.mkdir(parents=True, exist_ok=True)

    temp_wav = out_json_path.parent / f"{Path(media_path).stem}_16k.wav"

    print(f"\n==================================================================")
    print(f"STEP 1: SPEECH TRANSCRIPTION & WORD-LEVEL TIMESTAMPS")
    print(f"==================================================================")
    extract_audio_16k(media_path, str(temp_wav))

    segments = None
    if engine == "groq" or (engine == "auto" and os.getenv("GROQ_API_KEY")):
        try:
            print("[Step 1] Attempting Groq Whisper API...")
            segments = transcribe_groq_whisper(str(temp_wav))
        except Exception as e:
            print(f"[Step 1] Groq unavailable ({e}), using local faster-whisper...")

    if segments is None:
        segments = transcribe_local_whisper(str(temp_wav), model_size=model_size)

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    if temp_wav.exists():
        temp_wav.unlink()

    print(f"✓ Step 1 Complete: {len(segments)} segments saved -> {output_json}\n")
    return segments


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 1: Speech-To-Text Transcription & Timestamps")
    parser.add_argument("-i", "--input", required=True, help="Input media file (video or audio)")
    parser.add_argument("-o", "--output", required=True, help="Output JSON timestamps file")
    parser.add_argument("-e", "--engine", choices=["auto", "local", "groq"], default="auto", help="Transcription engine")
    parser.add_argument("-m", "--model", default="base", help="Whisper model size (tiny, base, small, medium)")
    args = parser.parse_args()

    run_stage_1(args.input, args.output, engine=args.engine, model_size=args.model)

