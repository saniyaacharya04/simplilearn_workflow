"""
Simplilearn Voice Cleaner & Audio Normalization Engine
Reference: OSL_3.0_Post_Production_Guidelines_2026.pdf (Pages 5-6)
Requirements: Free from background noise, studio quality, consistent loudness.
"""

import os
import subprocess
import json
from pathlib import Path
from .config import (
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


def clean_voice(
    input_audio: str,
    output_audio: str,
    denoise_db: float = 18.0,
    normalize_loudness: bool = True
) -> str:
    """
    Cleans background noise, applies vocal EQ, and normalizes audio to EBU R128 (-16 LUFS).
    
    Audio processing chain:
    1. Highpass filter @ 80Hz (eliminates HVAC, mic handling, room rumble).
    2. Lowpass filter @ 14kHz (removes high-frequency hiss).
    3. afftdn (Adaptive FFT de-noising).
    4. acompressor (Smooths dynamics for clear educator delivery).
    5. loudnorm (EBU R128 broadcast learning standards).
    """
    out_path = Path(output_audio)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build audio filter chain
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

    filter_str = ",".join(audio_filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_audio),
        "-af", filter_str,
        "-ar", str(AUDIO_SAMPLE_RATE),
        "-ac", "2"
    ]

    if str(output_audio).lower().endswith(".wav"):
        cmd.extend(["-c:a", "pcm_s16le", str(output_audio)])
    else:
        cmd.extend(["-c:a", "aac", "-b:a", AUDIO_BITRATE, str(output_audio)])

    print(f"[Voice Cleaner] Processing audio -> {output_audio}")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg audio cleaning failed: {res.stderr}")

    return str(output_audio)


def replace_video_audio(input_video: str, clean_audio_path: str, output_video: str) -> str:
    """Combines original video stream with cleaned audio track without re-encoding video."""
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


def process_video_voice_cleaning(input_video: str, output_video: str, work_dir: str = None) -> str:
    """Full workflow: extract raw audio -> clean voice & normalize -> mux back into video."""
    if work_dir is None:
        work_dir = Path(output_video).parent / "temp_audio"
    work_path = Path(work_dir)
    work_path.mkdir(parents=True, exist_ok=True)

    base = Path(input_video).stem
    raw_wav = work_path / f"{base}_raw.wav"
    clean_wav = work_path / f"{base}_clean.wav"

    print(f"\n--- [Step 1] Extracting raw audio: {input_video} ---")
    extract_audio(input_video, str(raw_wav))

    print(f"--- [Step 2] Cleaning background noise & normalizing (-16 LUFS) ---")
    clean_voice(str(raw_wav), str(clean_wav))

    print(f"--- [Step 3] Muxing clean audio into output video: {output_video} ---")
    replace_video_audio(input_video, str(clean_wav), output_video)

    print(f"✓ Audio cleaning complete: {output_video}\n")
    return str(output_video)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m pipeline.1_voice_cleaner <input_video> <output_video>")
        sys.exit(1)
    process_video_voice_cleaning(sys.argv[1], sys.argv[2])
