#!/usr/bin/env python3
"""
================================================================================
MANIM COMMUNITY BATCH COMPILER FOR SIMPLILEARN OSL 3.0
================================================================================
Compiles all generated scene scripts (group_1.py, group_2.py, ...) in manim_codes/
using the Manim Community conda environment into pristine vector animation MP4s.
Saves rendered animations into manim_videos/group_{n}.mp4.
================================================================================
"""

import os
import sys
import glob
import shutil
import re
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

MANIM_BIN = "/opt/homebrew/Caskroom/miniforge/base/envs/manim/bin/manim"
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent


def compile_single_scene(script_path: Path, output_dir: Path, quality: str = "qm") -> Path:
    """Compiles one Manim script (group_N.py) to MP4."""
    group_name = script_path.stem  # e.g. "group_1"
    target_mp4 = output_dir / f"{group_name}.mp4"

    if target_mp4.exists() and target_mp4.stat().st_size > 10000:
        print(f"  ✓ [{group_name}] Already rendered -> {target_mp4.name}")
        return target_mp4

    media_dir = output_dir / "media"
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = "/tmp/matplotlib"
    topic_dir = output_dir.parent
    env["CORRECTION_INSIGHTS_DIR"] = str(topic_dir / "correction_insights")
    env["CORRECTION_INSIGHTS_VLM_DIR"] = str(topic_dir / "correction_insights_vlm")
    if (topic_dir / "ex_config.json").exists():
        env["EX_CONFIG_PATH"] = str(topic_dir / "ex_config.json")

    cmd = [
        MANIM_BIN,
        f"-{quality}",
        "--disable_caching",
        str(script_path),
        "FinalScene",
        "--media_dir", str(media_dir),
        "-o", f"{group_name}.mp4"
    ]

    print(f"  [*] Rendering [{group_name}] via Manim Community ({quality})...")
    res = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if res.returncode != 0:
        print(f"  ⚠️ [{group_name}] Compile notice: {res.stderr[-300:] if res.stderr else 'Unknown'}")
        # Try fallback with MovingCameraScene / TestScene if FinalScene had class name difference
        cmd_fallback = [
            MANIM_BIN, f"-{quality}", "--disable_caching",
            str(script_path), "--media_dir", str(media_dir), "-o", f"{group_name}.mp4"
        ]
        res_fallback = subprocess.run(cmd_fallback, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res_fallback.returncode != 0:
            raise RuntimeError(f"Manim render failed for {script_path.name}")

    # Locate rendered MP4 in media directory
    found = glob.glob(str(media_dir / "**" / f"{group_name}.mp4"), recursive=True)
    if not found:
        # Check for FinalScene.mp4
        found = glob.glob(str(media_dir / "**" / "FinalScene.mp4"), recursive=True)

    if found:
        shutil.copy2(found[0], target_mp4)
        print(f"  ✓ [{group_name}] Successfully rendered ({target_mp4.stat().st_size / (1024*1024):.2f} MB)")
        return target_mp4
    else:
        raise FileNotFoundError(f"Rendered video not found in media tree for {group_name}")


def compile_all_manim_scenes(
    codes_dir: str,
    videos_dir: str,
    quality: str = "qm",
    workers: int = 2
) -> List[Path]:
    """Compiles all group_*.py in codes_dir to videos_dir."""
    c_dir = Path(codes_dir)
    v_dir = Path(videos_dir)
    v_dir.mkdir(parents=True, exist_ok=True)

    # Ensure feedback_functions is in codes_dir
    ff_dst = c_dir / "feedback_functions"
    ff_dst.mkdir(exist_ok=True)
    src_ff = SCRIPT_DIR / "helpers" / "feedback_functions"
    if src_ff.exists():
        for f in ["instrumented_scene.py", "scene_snapshot.py"]:
            src_file = src_ff / f
            if src_file.exists():
                shutil.copy2(src_file, ff_dst / f)

    script_files = sorted(
        c_dir.glob("group_*.py"),
        key=lambda p: int(re.search(r'\d+', p.stem).group()) if re.search(r'\d+', p.stem) else 0
    )

    if not script_files:
        print(f"[Manim Compiler] No group_*.py scripts found in {codes_dir}")
        return []

    print(f"\n==================================================================")
    print(f"MANIM COMMUNITY 0.21.0 BATCH RENDERING ({len(script_files)} SCENES)")
    print(f"Codes: {codes_dir} -> Videos: {videos_dir} (Quality: {quality})")
    print(f"==================================================================")

    rendered = []
    # Render sequentially to preserve CPU / GPU bandwidth and prevent font cache contention
    for sf in script_files:
        try:
            out_file = compile_single_scene(sf, v_dir, quality=quality)
            rendered.append(out_file)
        except Exception as e:
            print(f"  ❌ Failed rendering {sf.name}: {e}")

    print(f"\n✓ Completed rendering {len(rendered)}/{len(script_files)} Manim scenes.\n")
    return rendered


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch Manim Community Scene Compiler")
    parser.add_argument("-i", "--codes-dir", required=True, help="Directory containing group_*.py")
    parser.add_argument("-o", "--videos-dir", required=True, help="Output directory for rendered MP4s")
    parser.add_argument("-q", "--quality", default="qm", choices=["ql", "qm", "qh", "qk"], help="Render quality (ql: 480p, qm: 720p, qh: 1080p)")
    args = parser.parse_args()

    compile_all_manim_scenes(
        codes_dir=args.codes_dir,
        videos_dir=args.videos_dir,
        quality=args.quality
    )
