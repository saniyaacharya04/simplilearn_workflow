#!/usr/bin/env python3
"""
Step 0: Audio Cleaner & EBU R128 Loudness Normalizer
Reference: Simplilearn OSL 3.0 Guidelines (Pages 5-6)
Requirements: Remove background noise/rumble, normalize to -16 LUFS.
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
    AUDIO_SAMPLE_RATE,
    AUDIO_BITRATE,
    TARGET_I_LUFS,
    TARGET_TP_DB,
    TARGET_LRA,
    HIGHPASS_FREQ
)


def extract_audio(input_video: str, output_wav: str) -> bool:
    """Extracts raw 48kHz audio from input video."""
    Path(output_wav).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_video),
        "-vn",
        "-ac", "2",
        "-ar", str(AUDIO_SAMPLE_RATE),
        "-c:a", "pcm_s16le",
        str(output_wav)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    return res.returncode == 0


def clean_voice_audio(
    input_audio: str,
    output_audio: str,
    denoise_db: float = 18.0,
    normalize_loudness: bool = True
) -> str:
    """
    Cleans background noise, applies vocal EQ, and normalizes audio to EBU R128 (-16 LUFS).
    Filter chain: Highpass 80Hz -> Lowpass 14kHz -> afftdn -> acompressor -> loudnorm.
    """
    out_path = Path(output_audio)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    audio_filters = [
        f"highpass=f={HIGHPASS_FREQ}",
        "lowpass=f=14000",
        f"afftdn=nr={denoise_db}:nf=-40:tn=1",
        "acompressor=threshold=-18dB:ratio=3:attack=10:release=100:makeup=2dB"
    ]

    if normalize_loudness:
        audio_filters.append(
            f"loudnorm=I={TARGET_I_LUFS}:TP={TARGET_TP_DB}:LRA={TARGET_LRA}:print_format=summary"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_audio),
        "-af", ",".join(audio_filters),
        "-ar", str(AUDIO_SAMPLE_RATE),
        "-ac", "2"
    ]

    if str(output_audio).lower().endswith(".wav"):
        cmd.extend(["-c:a", "pcm_s16le", str(output_audio)])
    else:
        cmd.extend(["-c:a", "aac", "-b:a", AUDIO_BITRATE, str(output_audio)])

    print(f"[Step 0] Cleaning audio -> {output_audio}")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg audio cleaning failed: {res.stderr}")

    return str(output_audio)


def mux_clean_audio_into_video(input_video: str, clean_audio_path: str, output_video: str) -> str:
    """Combines original video stream with cleaned audio without re-encoding video."""
    Path(output_video).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_video),
        "-i", str(clean_audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(output_video)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Muxing clean audio failed: {res.stderr}")
    return str(output_video)


def run_stage_0(input_video: str, output_video: str, temp_dir: str = None) -> str:
    """Runs complete Stage 0 workflow."""
    if temp_dir is None:
        temp_dir = Path(output_video).parent / "temp_audio"
    work_path = Path(temp_dir)
    work_path.mkdir(parents=True, exist_ok=True)

    base = Path(input_video).stem
    raw_wav = work_path / f"{base}_raw.wav"
    clean_wav = work_path / f"{base}_clean.wav"

    print(f"\n==================================================================")
    print(f"STEP 0: VOICE CLEANER & EBU R128 NORMALIZATION (-16 LUFS)")
    print(f"==================================================================")
    print(f"1. Extracting raw audio: {input_video}")
    extract_audio(input_video, str(raw_wav))

    print(f"2. De-noising & normalising loudness: {clean_wav}")
    clean_voice_audio(str(raw_wav), str(clean_wav))

    print(f"3. Muxing clean audio into output: {output_video}")
    mux_clean_audio_into_video(input_video, str(clean_wav), output_video)

    print(f"✓ Step 0 Complete -> {output_video}\n")
    return str(output_video)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 0: Clean Voice & Normalize Audio")
    parser.add_argument("-i", "--input", required=True, help="Input video file")
    parser.add_argument("-o", "--output", required=True, help="Output video file with clean audio")
    parser.add_argument("-t", "--temp-dir", default=None, help="Temporary audio working folder")
    args = parser.parse_args()

    run_stage_0(args.input, args.output, args.temp_dir)

