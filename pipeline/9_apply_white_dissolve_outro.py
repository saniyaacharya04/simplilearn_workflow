#!/usr/bin/env python3
"""
Step 9: Standard Video End Animation (0.5s White Dissolve)
Reference: Simplilearn OSL 3.0 Guidelines (Page 30)
Mandate: "Dissolve the edited topic video to White #FFFFFF (0.5s duration)."
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import (
    VIDEO_CODEC,
    VIDEO_PRESET,
    VIDEO_CRF,
    OUTRO_DISSOLVE_DURATION
)


def run_stage_9(
    input_video: str,
    output_video: str,
    dissolve_seconds: float = OUTRO_DISSOLVE_DURATION
) -> str:
    """Runs complete Stage 9 workflow."""
    print(f"\n==================================================================")
    print(f"STEP 9: APPLY SIMPLILEARN 0.5s WHITE DISSOLVE OUTRO")
    print(f"==================================================================")

    cmd_dur = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_video)
    ]
    res_dur = subprocess.run(cmd_dur, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    duration = float(res_dur.stdout.strip())

    fade_start = max(0.0, duration - dissolve_seconds)
    filter_str = f"fade=t=out:st={fade_start:.3f}:d={dissolve_seconds:.3f}:color=white"

    Path(output_video).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_video),
        "-vf", filter_str,
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_video)
    ]

    print(f"[Step 9] Applying 0.5s White Dissolve (start: {fade_start:.2f}s) -> {output_video}")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"White dissolve filter failed: {res.stderr}")

    print(f"✓ Step 9 Complete: Final broadcast video -> {output_video}\n")
    return output_video


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 9: Apply 0.5s White Dissolve Outro")
    parser.add_argument("-i", "--input", required=True, help="Input assembled video")
    parser.add_argument("-o", "--output", required=True, help="Output final delivery video")
    parser.add_argument("-d", "--duration", type=float, default=OUTRO_DISSOLVE_DURATION, help="Dissolve duration in seconds")
    args = parser.parse_args()

    run_stage_9(args.input, args.output, dissolve_seconds=args.duration)

