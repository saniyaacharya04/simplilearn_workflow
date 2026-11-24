import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

from groq import Groq
from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================
load_dotenv()

def get_groq_client(api_key: Optional[str] = None) -> Groq:
    """Returns an authenticated Groq client."""
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY environment variable not set. Please set it in .env")
    return Groq(api_key=key)

# =========================================================
# CORE WORD-LEVEL TRANSCRIBE FUNCTION
# =========================================================
def transcribe_audio(
    audio_path: str,
    output_json: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribes audio using Groq cloud whisper-large-v3 with word-level
    and segment-level timestamps.
    
    Returns structured dict:
    {
        "audio_file": str,
        "duration": float,
        "segments": [{"id": ..., "start": ..., "end": ..., "text": ...}],
        "words": [{"word": ..., "start": ..., "end": ..., "probability": ...}]
    }
    """
    audio_path_obj = Path(audio_path)
    if not audio_path_obj.exists() or audio_path_obj.stat().st_size == 0:
        raise FileNotFoundError(f"Audio file not found or empty: {audio_path}")

    print(f"[Transcribe] Processing: {audio_path_obj.name} via Groq whisper-large-v3...")

    client = get_groq_client(api_key=api_key)

    with open(audio_path_obj, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(
                audio_path_obj.name,
                file.read()
            ),
            model="whisper-large-v3",
            temperature=0,
            response_format="verbose_json",
            timestamp_granularities=[
                "word",
                "segment"
            ]
        )

    tr_dict = transcription if isinstance(transcription, dict) else (
        transcription.model_dump() if hasattr(transcription, "model_dump") else transcription.__dict__
    )

    raw_words = tr_dict.get("words", [])
    raw_segments = tr_dict.get("segments", [])

    # Calculate total duration from last timestamp or segment
    total_dur = 0.0
    if raw_words:
        total_dur = max(total_dur, float(raw_words[-1].get("end", 0.0)))
    if raw_segments:
        total_dur = max(total_dur, float(raw_segments[-1].get("end", 0.0)))

    cleaned_segments = []
    for s in raw_segments:
        text = str(s.get("text", "")).strip()
        if not text:
            continue
        cleaned_segments.append({
            "id": s.get("id"),
            "start": round(float(s.get("start", 0.0)), 3),
            "end": round(float(s.get("end", 0.0)), 3),
            "duration": round(float(s.get("end", 0.0)) - float(s.get("start", 0.0)), 3),
            "text": text
        })

    cleaned_words = []
    for w in raw_words:
        w_text = str(w.get("word", "")).strip()
        if not w_text:
            continue
        w_item = {
            "word": w_text,
            "start": round(float(w.get("start", 0.0)), 3),
            "end": round(float(w.get("end", 0.0)), 3),
        }
        if "probability" in w:
            w_item["probability"] = round(float(w.get("probability", 1.0)), 3)
        cleaned_words.append(w_item)

    output_data = {
        "audio_file": audio_path_obj.name,
        "duration": round(total_dur, 3),
        "segments": cleaned_segments,
        "words": cleaned_words
    }

    if output_json:
        out_p = Path(output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"[Transcribe] Successfully saved word-level timestamps to: {output_json}")

    return output_data


# =========================================================
# BATCH DIRECTORY TRANSCRIBE FUNCTION
# =========================================================
def transcribe_directory(
    audio_dir: str,
    output_dir: str,
    pattern: str = "*.wav",
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Transcribes all matching audio files in audio_dir into output_dir."""
    audio_dir_p = Path(audio_dir)
    output_dir_p = Path(output_dir)
    output_dir_p.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(audio_dir_p.glob(pattern))
    if not wav_files:
        print(f"[Transcribe] No files matching '{pattern}' in '{audio_dir}'")
        return []

    print(f"\n[Transcribe] Found {len(wav_files)} files in '{audio_dir}':")
    for f in wav_files:
        print(f"  - {f.name}")

    results = []
    for wav_file in wav_files:
        out_json = output_dir_p / f"{wav_file.stem}_word_level.json"
        try:
            data = transcribe_audio(str(wav_file), str(out_json), api_key=api_key)
            results.append(data)
        except Exception as e:
            print(f"[Transcribe] Error processing {wav_file}: {e}")

    print(f"\n[Transcribe] Completed {len(results)}/{len(wav_files)} transcriptions.")
    return results


# =========================================================
# CLI ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="High-resolution word-level speech transcription using Groq Whisper Large v3"
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        default=None,
        help="Input audio file or directory containing audio files"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output JSON file path (for single file) or directory (for batch)"
    )
    parser.add_argument(
        "-p", "--pattern",
        type=str,
        default="*.wav",
        help="Glob pattern for audio files when transcribing a directory (default: *.wav)"
    )

    args = parser.parse_args()

    # Determine input path
    input_path = args.input
    if not input_path:
        # Auto-detect sensible default
        if Path("merged_audio").exists() and list(Path("merged_audio").glob("*.wav")):
            input_path = "merged_audio"
        else:
            # Check for output topic audio_elements
            candidates = list(Path("output").glob("*/audio_elements"))
            if candidates:
                input_path = str(candidates[0])
            else:
                input_path = "merged_audio"

    input_p = Path(input_path)

    if input_p.is_file():
        out_file = args.output or f"transcripts/{input_p.stem}_word_level.json"
        transcribe_audio(str(input_p), out_file)
    elif input_p.is_dir():
        out_dir = args.output or (str(input_p.parent / "transcripts") if "output" in str(input_p) else "transcripts")
        transcribe_directory(str(input_p), out_dir, pattern=args.pattern)
    else:
        print(f"Error: Specified input path does not exist: {input_path}")
        print("Usage:")
        print("  python3 transcribe.py -i path/to/audio.wav -o transcripts/audio_word_level.json")
        print("  python3 transcribe.py -i path/to/audio_elements/ -o transcripts/")
