#!/usr/bin/env python3
"""
Step 2: Content, Filler Words & Repeated Sentences Cleaner
Reference: Simplilearn OSL 3.0 Guidelines (Page 6 & 26)
Detects and removes:
- Unnecessary filler words ("uh", "um", "like", "you know", "मतलब", etc.)
- Verbal retake triggers ("sorry cut", "let me start again", "wait", etc.)
- Repeated sentences & false starts (using sequence similarity)
- Dead pauses (> 1.0s, -35dB)
Generates keep_segments.json and cut_decisions.json for synchronized AV trimming.
"""

import os
import sys
import json
import re
import difflib
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import (
    FILLER_WORDS_EN,
    FILLER_WORDS_HI,
    RETAKE_KEYWORDS,
    NOISE_FLOOR_DB,
    MIN_SILENCE_DURATION,
    CUT_PADDING_SECONDS,
    MERGE_GAP_THRESHOLD
)


def clean_filler_words_from_text(text: str) -> Tuple[str, bool]:
    """Removes filler words while preserving grammatical meaning."""
    words = text.split()
    if not words:
        return "", True

    all_fillers = set(w.lower() for w in FILLER_WORDS_EN + FILLER_WORDS_HI)
    filtered = []
    filler_count = 0

    for w in words:
        clean_w = re.sub(r"[^\w\s]", "", w).lower()
        if clean_w in all_fillers:
            filler_count += 1
        else:
            filtered.append(w)

    is_pure_filler = (len(filtered) == 0) or (filler_count / len(words) >= 0.75)
    cleaned_text = " ".join(filtered).strip()
    return cleaned_text, is_pure_filler


def compute_similarity(text1: str, text2: str) -> float:
    """Computes normalized text similarity between two phrases."""
    t1 = re.sub(r"[^\w\s]", "", text1.lower()).strip()
    t2 = re.sub(r"[^\w\s]", "", text2.lower()).strip()
    if not t1 or not t2:
        return 0.0
    return difflib.SequenceMatcher(None, t1, t2).ratio()


def detect_repeated_sentences(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identifies false starts and repeated sentences.
    Flags earlier botched attempts for cutting and retains the final clean take.
    """
    retake_cuts = []
    n = len(segments)

    for i in range(n - 1):
        curr = segments[i]
        nxt = segments[i + 1]

        t_curr = curr.get("text", "").strip()
        t_nxt = nxt.get("text", "").strip()

        # Check explicit verbal retake cues
        curr_lower = t_curr.lower()
        if any(kw in curr_lower for kw in RETAKE_KEYWORDS):
            retake_cuts.append({
                "start": curr["start"],
                "end": curr["end"],
                "reason": f"Verbal retake keyword detected ('{t_curr}')"
            })
            continue

        # Check semantic repetition / restart
        sim = compute_similarity(t_curr, t_nxt)
        words_curr = t_curr.split()
        words_nxt = t_nxt.split()

        is_prefix = False
        if len(words_curr) >= 2 and len(words_nxt) >= len(words_curr):
            prefix_match = (
                " ".join(words_curr[:min(4, len(words_curr))]).lower() ==
                " ".join(words_nxt[:min(4, len(words_curr))]).lower()
            )
            if prefix_match:
                is_prefix = True

        if sim > 0.60 or is_prefix:
            retake_cuts.append({
                "start": curr["start"],
                "end": curr["end"],
                "reason": f"Repeated take before: '{t_nxt[:40]}...'"
            })

    return retake_cuts


def detect_audio_silences(
    media_path: str,
    noise_db: float = NOISE_FLOOR_DB,
    min_duration: float = MIN_SILENCE_DURATION
) -> List[Dict[str, float]]:
    """Runs FFmpeg silencedetect to locate prolonged dead pauses."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(media_path),
        "-af", f"silencedetect=n={noise_db}dB:d={min_duration}",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    output = res.stderr

    silence_starts = []
    silence_ends = []

    for line in output.splitlines():
        if "silence_start:" in line:
            try:
                silence_starts.append(float(line.split("silence_start:")[1].strip()))
            except ValueError:
                pass
        elif "silence_end:" in line:
            try:
                silence_ends.append(float(line.split("silence_end:")[1].split("|")[0].strip()))
            except ValueError:
                pass

    silences = []
    for s, e in zip(silence_starts, silence_ends):
        if e > s:
            silences.append({
                "start": round(s, 3),
                "end": round(e, 3),
                "duration": round(e - s, 3)
            })

    return silences


def get_media_duration(media_path: str) -> float:
    """Retrieves exact media duration in seconds."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(media_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    return float(res.stdout.strip())


def merge_and_pad_cuts(
    cuts: List[Dict[str, Any]],
    total_duration: float,
    padding: float = CUT_PADDING_SECONDS,
    gap_threshold: float = MERGE_GAP_THRESHOLD
) -> List[Dict[str, Any]]:
    """Merges adjacent cut intervals and applies safety padding."""
    if not cuts:
        return []

    padded = []
    for c in cuts:
        padded.append({
            "start": max(0.0, c["start"] - padding),
            "end": min(total_duration, c["end"] + padding),
            "reason": c.get("reason", "cut")
        })

    padded.sort(key=lambda x: x["start"])

    merged = [padded[0]]
    for curr in padded[1:]:
        prev = merged[-1]
        if curr["start"] - prev["end"] <= gap_threshold:
            prev["end"] = max(prev["end"], curr["end"])
            prev["reason"] += " + " + curr["reason"]
        else:
            merged.append(curr)

    return merged


def build_keep_segments(
    cuts: List[Dict[str, Any]],
    total_duration: float
) -> List[Dict[str, float]]:
    """Inverts cut intervals into valid keep intervals."""
    keep_segments = []
    current_time = 0.0

    for cut in cuts:
        if cut["start"] > current_time:
            keep_segments.append({
                "start": round(current_time, 3),
                "end": round(cut["start"], 3),
                "duration": round(cut["start"] - current_time, 3)
            })
        current_time = max(current_time, cut["end"])

    if current_time < total_duration:
        keep_segments.append({
            "start": round(current_time, 3),
            "end": round(total_duration, 3),
            "duration": round(total_duration - current_time, 3)
        })

    return [k for k in keep_segments if k["duration"] >= 0.2]


def run_stage_2(
    media_path: str,
    transcript_json: str,
    output_decisions_json: str,
    output_clean_transcript_json: str
) -> Dict[str, Any]:
    """Runs complete Stage 2 workflow."""
    total_duration = get_media_duration(media_path)

    print(f"\n==================================================================")
    print(f"STEP 2: CLEAN FILLERS, DETECT RETAKES & REPEATED SENTENCES")
    print(f"==================================================================")

    with open(transcript_json, "r", encoding="utf-8") as f:
        segments = json.load(f)

    cuts = []
    cleaned_transcript = []

    # 1. Filler words
    for seg in segments:
        text = seg.get("text", "")
        cleaned_text, is_filler = clean_filler_words_from_text(text)

        if is_filler and seg.get("duration", 0) < 2.5:
            cuts.append({
                "start": seg["start"],
                "end": seg["end"],
                "reason": f"Pure filler ('{text}')"
            })
        else:
            seg_copy = dict(seg)
            seg_copy["cleaned_text"] = cleaned_text
            cleaned_transcript.append(seg_copy)

    # 2. Repeated sentences & false starts
    repetition_cuts = detect_repeated_sentences(segments)
    cuts.extend(repetition_cuts)

    # 3. Dead silences
    silences = detect_audio_silences(media_path)
    for s in silences:
        cuts.append({
            "start": s["start"],
            "end": s["end"],
            "reason": f"Dead silence ({s['duration']}s)"
        })

    # 4. Merge & build keep segments
    merged_cuts = merge_and_pad_cuts(cuts, total_duration)
    keep_segments = build_keep_segments(merged_cuts, total_duration)

    summary = {
        "media_path": str(media_path),
        "total_duration": total_duration,
        "trimmed_duration": round(sum(k["duration"] for k in keep_segments), 3),
        "time_saved": round(total_duration - sum(k["duration"] for k in keep_segments), 3),
        "cut_count": len(merged_cuts),
        "cuts": merged_cuts,
        "keep_segments": keep_segments
    }

    Path(output_decisions_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_decisions_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    Path(output_clean_transcript_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_clean_transcript_json, "w", encoding="utf-8") as f:
        json.dump(cleaned_transcript, f, indent=2, ensure_ascii=False)

    print(f"✓ Total Duration: {total_duration:.2f}s -> Trimmed Duration: {summary['trimmed_duration']:.2f}s")
    print(f"✓ Removed: {summary['time_saved']:.2f}s across {len(merged_cuts)} cuts")
    print(f"✓ Decisions saved -> {output_decisions_json}")
    print(f"✓ Cleaned transcript saved -> {output_clean_transcript_json}\n")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 2: Clean Fillers, Retakes & Repetitions")
    parser.add_argument("-i", "--input", required=True, help="Input media file")
    parser.add_argument("-t", "--transcript", required=True, help="Input transcript JSON file")
    parser.add_argument("-d", "--decisions", required=True, help="Output cut decisions JSON file")
    parser.add_argument("-c", "--clean-transcript", required=True, help="Output cleaned transcript JSON file")
    args = parser.parse_args()

    run_stage_2(args.input, args.transcript, args.decisions, args.clean_transcript)

