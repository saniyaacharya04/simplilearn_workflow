#!/usr/bin/env python3
"""
Step 3: Synchronous Audio & Video Trimmer
Executes frame-accurate cutting and seamless concatenation of keep segments.
Preserves perfect lip-sync across both audio and video streams.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import VIDEO_CODEC, VIDEO_PRESET, VIDEO_CRF, AUDIO_BITRATE


def export_keep_clips(
    video_path: str,
    keep_segments: List[Dict[str, float]],
    temp_dir: str
) -> List[str]:
    """Exports each keep interval to a temporary high-quality clip."""
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    clip_paths = []

    print(f"[Step 3] Slicing {len(keep_segments)} keep clips...")
    for idx, seg in enumerate(keep_segments):
        clip_file = Path(temp_dir) / f"clip_{idx:04d}.mp4"
        clip_paths.append(str(clip_file))

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(seg["start"]),
            "-to", str(seg["end"]),
            "-i", str(video_path),
            "-c:v", VIDEO_CODEC,
            "-preset", VIDEO_PRESET,
            "-crf", str(VIDEO_CRF),
            "-c:a", "aac",
            "-b:a", AUDIO_BITRATE,
            "-avoid_negative_ts", "make_zero",
            str(clip_file)
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Export clip {idx} failed: {res.stderr}")

    return clip_paths


def concat_clips(clip_paths: List[str], output_video: str, work_dir: str) -> str:
    """Concatenates video clips using the FFmpeg concat demuxer."""
    concat_list_file = Path(work_dir) / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            abs_path = str(Path(p).resolve().as_posix())
            safe_path = abs_path.replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    Path(output_video).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(output_video)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        cmd_reencode = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c:v", VIDEO_CODEC,
            "-preset", VIDEO_PRESET,
            "-crf", str(VIDEO_CRF),
            "-c:a", "aac",
            "-b:a", AUDIO_BITRATE,
            str(output_video)
        ]
        res_reencode = subprocess.run(cmd_reencode, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res_reencode.returncode != 0:
            raise RuntimeError(f"Concat failed: {res_reencode.stderr}")

    return str(output_video)


def run_stage_3(
    video_path: str,
    decisions_json: str,
    output_video: str,
    cleanup_temp: bool = True
) -> str:
    """Runs complete Stage 3 workflow."""
    print(f"\n==================================================================")
    print(f"STEP 3: SYNCHRONOUS FRAME-ACCURATE AUDIO & VIDEO TRIMMING")
    print(f"==================================================================")

    with open(decisions_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    keep_segments = data.get("keep_segments", [])
    if not keep_segments:
        print("[Step 3] Warning: No keep segments. Copying source as output.")
        import shutil
        shutil.copy(video_path, output_video)
        return output_video

    temp_dir = Path(output_video).parent / "temp_trim_clips"
    clip_paths = export_keep_clips(video_path, keep_segments, str(temp_dir))
    final_output = concat_clips(clip_paths, output_video, str(temp_dir))

    if cleanup_temp:
        for p in clip_paths:
            try:
                os.remove(p)
            except OSError:
                pass
        concat_file = temp_dir / "concat_list.txt"
        if concat_file.exists():
            concat_file.unlink()
        try:
            temp_dir.rmdir()
        except OSError:
            pass

    print(f"✓ Step 3 Complete: Lip-synced trimmed video -> {final_output}\n")
    return final_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 3: Synchronous Audio/Video Trimmer")
    parser.add_argument("-i", "--input", required=True, help="Input video file")
    parser.add_argument("-d", "--decisions", required=True, help="Input cut decisions JSON file")
    parser.add_argument("-o", "--output", required=True, help="Output trimmed video file")
    args = parser.parse_args()

    run_stage_3(args.input, args.decisions, args.output)
