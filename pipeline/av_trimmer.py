"""
Simplilearn Synchronous Audio & Video Trimmer
Executes frame-accurate trimming and stitching of audio/video using keep segments.
Maintains perfect lip-sync across all cut boundaries.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from .config import VIDEO_CODEC, VIDEO_PRESET, VIDEO_CRF, AUDIO_BITRATE


def export_keep_clips(
    video_path: str,
    keep_segments: List[Dict[str, float]],
    temp_dir: str
) -> List[str]:
    """Exports each keep interval to a temporary high-quality clip."""
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    clip_paths = []

    print(f"\n[AV Trimmer] Exporting {len(keep_segments)} clips to {temp_dir}...")
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
            raise RuntimeError(f"Failed exporting clip {idx}: {res.stderr}")

    return clip_paths


def concat_clips(clip_paths: List[str], output_video: str, work_dir: str) -> str:
    """Concatenates video clips using the FFmpeg concat demuxer."""
    concat_list_file = Path(work_dir) / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            # Escape single quotes for ffmpeg concat demuxer
            abs_path = str(Path(p).resolve().as_posix())
            safe_path = abs_path.replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    Path(output_video).parent.mkdir(parents=True, exist_ok=True)

    print(f"[AV Trimmer] Concatenating clips into -> {output_video}")
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
        # Fallback to re-encoding concat if stream copy fails
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


def trim_media_from_decisions(
    video_path: str,
    decisions_json: str,
    output_video: str,
    cleanup_temp: bool = True
) -> str:
    """Full workflow: loads keep segments, exports clips, stitches into trimmed media."""
    with open(decisions_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    keep_segments = data.get("keep_segments", [])
    if not keep_segments:
        print("[AV Trimmer] Warning: No keep segments found. Copying input as output.")
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

    print(f"✓ Audio & Video synchronously trimmed -> {final_output}\n")
    return final_output


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python -m pipeline.4_av_trimmer <video_path> <decisions_json> <output_video>")
        sys.exit(1)
    trim_media_from_decisions(sys.argv[1], sys.argv[2], sys.argv[3])
