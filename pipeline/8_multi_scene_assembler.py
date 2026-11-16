#!/usr/bin/env python3
"""
Step 8: Multi-Scene Educational Lesson Assembler
Assembles the complete multi-scene OSL lesson from the Presentation Blueprint.
- Scene 1: Hook / Intro (100% Full Screen)
- Scene 2: Learning Objectives (70% Left Rounded-Rectangle + Objectives Slide)
- Scene 3: Core Concepts / Demos (20% Top-Right Corner PIP + Slide Workspace)
- Scene 4: Summary / Key Takeaways (70% Left Rounded-Rectangle + Recap Slide)
- Scene 5: What's Next (70% Left Rounded-Rectangle + Next Topic Slide)
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

from pipeline.config import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    VIDEO_CODEC,
    VIDEO_PRESET,
    VIDEO_CRF,
    AUDIO_BITRATE
)
import importlib

# Import layout functions from 7_sme_placement_layouts
_sme_layouts = importlib.import_module("pipeline.7_sme_placement_layouts")
render_sme_layout_100 = getattr(_sme_layouts, "render_sme_layout_100")
render_sme_layout_70 = getattr(_sme_layouts, "render_sme_layout_70")
render_sme_layout_20 = getattr(_sme_layouts, "render_sme_layout_20")


def run_stage_8(
    trimmed_teacher_video: str,
    blueprint_json: str,
    output_assembled_video: str,
    work_dir: str = None
) -> str:
    """Runs complete Stage 8 workflow."""
    if work_dir is None:
        work_dir = Path(output_assembled_video).parent / "temp_assembly"
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n==================================================================")
    print(f"STEP 8: MULTI-SCENE PRESENTATION ASSEMBLY")
    print(f"==================================================================")

    with open(blueprint_json, "r", encoding="utf-8") as f:
        blueprint = json.load(f)

    scenes = blueprint.get("scenes", [])
    if not scenes:
        raise ValueError("Blueprint contains no scenes.")

    # Measure actual video duration
    cmd_dur = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(trimmed_teacher_video)
    ]
    res_dur = subprocess.run(cmd_dur, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    actual_duration = float(res_dur.stdout.strip())

    blueprint_max_time = scenes[-1].get("end_time", actual_duration)
    time_scale = (actual_duration / blueprint_max_time) if blueprint_max_time > 0 else 1.0

    rendered_scene_clips = []
    print(f"[Step 8] Slicing and compositing {len(scenes)} scenes (Duration: {actual_duration:.2f}s)...")

    for idx, scene in enumerate(scenes):
        sid = scene.get("scene_id", idx + 1)
        layout = str(scene.get("sme_layout", "70"))
        raw_st = scene.get("start_time", 0.0)
        raw_et = scene.get("end_time", actual_duration)

        st = max(0.0, min(actual_duration - 0.2, raw_st * time_scale))
        et = min(actual_duration, max(st + 0.5, raw_et * time_scale))
        seg_duration = max(0.5, et - st)
        slide_img = scene.get("rendered_slide_png")

        # 1. Slice teacher subclip (input first for accurate decoding)
        scene_subclip = Path(work_dir) / f"subclip_scene_{sid:02d}.mp4"
        cmd_slice = [
            "ffmpeg", "-y",
            "-i", str(trimmed_teacher_video),
            "-ss", str(st),
            "-t", str(seg_duration),
            "-c:v", VIDEO_CODEC,
            "-preset", VIDEO_PRESET,
            "-crf", str(VIDEO_CRF),
            "-c:a", "aac",
            "-b:a", AUDIO_BITRATE,
            "-avoid_negative_ts", "make_zero",
            str(scene_subclip)
        ]
        subprocess.run(cmd_slice, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 2. Composite with layout
        scene_rendered = Path(work_dir) / f"rendered_scene_{sid:02d}_{layout}.mp4"
        if layout == "100":
            render_sme_layout_100(str(scene_subclip), str(scene_rendered))
        elif layout == "70":
            render_sme_layout_70(str(scene_subclip), slide_img, str(scene_rendered), work_dir=work_dir)
        elif layout == "20":
            render_sme_layout_20(str(scene_subclip), slide_img, str(scene_rendered), work_dir=work_dir)

        rendered_scene_clips.append(str(scene_rendered))
        print(f"  ✓ Scene {sid} ({layout}% layout, {st:.1f}s - {et:.1f}s) -> {scene_rendered.name}")

    # 3. Concatenate all rendered scenes
    concat_txt = Path(work_dir) / "assembly_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in rendered_scene_clips:
            abs_path = str(Path(p).resolve().as_posix())
            safe = abs_path.replace("'", "'\\''")
            f.write(f"file '{safe}'\n")

    Path(output_assembled_video).parent.mkdir(parents=True, exist_ok=True)
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(output_assembled_video)
    ]
    res_c = subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res_c.returncode != 0:
        cmd_concat_re = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c:v", VIDEO_CODEC,
            "-preset", VIDEO_PRESET,
            "-crf", str(VIDEO_CRF),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            str(output_assembled_video)
        ]
        subprocess.run(cmd_concat_re, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"✓ Step 8 Complete: Assembled lecture video -> {output_assembled_video}\n")
    return output_assembled_video


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 8: Multi-Scene Educational Lesson Assembler")
    parser.add_argument("-i", "--input", required=True, help="Input trimmed teacher video")
    parser.add_argument("-b", "--blueprint", required=True, help="Input presentation blueprint JSON")
    parser.add_argument("-o", "--output", required=True, help="Output assembled video")
    parser.add_argument("-w", "--work-dir", default=None, help="Working folder for scene clips")
    args = parser.parse_args()

    run_stage_8(args.input, args.blueprint, args.output, work_dir=args.work_dir)
