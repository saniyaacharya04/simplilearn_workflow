"""
Simplilearn OSL 3.0 Post-Production Assembly & Outro Engine
Reference: OSL_3.0_Post_Production_Guidelines_2026.pdf (Pages 6, 21-30)

Features:
- Mandatory 0.5-second Dissolve to White (#FFFFFF) at video conclusion.
- Multi-scene dynamic lesson assembler (Hook 100% -> Objectives 70% -> Core Demo 20% -> Summary 70% -> Next Topic 70% -> Outro).
"""

import os
import json
import subprocess
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any

from .config import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    FRAME_RATE,
    VIDEO_CODEC,
    VIDEO_PRESET,
    VIDEO_CRF,
    AUDIO_BITRATE,
    OUTRO_DISSOLVE_COLOR,
    OUTRO_DISSOLVE_DURATION,
    COLORS
)
from .teacher_cutout_and_placement import (
    render_sme_layout_100,
    render_sme_layout_70,
    render_sme_layout_20
)


def apply_white_dissolve_outro(
    input_video: str,
    output_video: str,
    dissolve_seconds: float = OUTRO_DISSOLVE_DURATION
) -> str:
    """
    Applies the mandatory Simplilearn 0.5-second dissolve to white (#FFFFFF)
    at the end of the video segment (OSL 3.0 Page 30).
    """
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

    print(f"\n[OSL Post-Production] Applying 0.5s White Dissolve (start: {fade_start:.2f}s) -> {output_video}")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"White dissolve filter failed: {res.stderr}")

    return output_video


def create_simplilearn_slide_template(
    title: str,
    lead_in: str,
    bullets: List[str],
    output_png: str,
    template_type: str = "objectives"
) -> str:
    """
    Generates an official Simplilearn styled 1920x1080 slide background (PNG).
    """
    canvas = np.full((CANVAS_HEIGHT, CANVAS_WIDTH, 3), 255, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    cv2.putText(canvas, title, (780, 160), font, 1.2, (64, 64, 64), 2, cv2.LINE_AA)

    if lead_in:
        cv2.putText(canvas, lead_in, (780, 240), font, 0.85, (100, 100, 100), 2, cv2.LINE_AA)

    start_y = 320
    for idx, bullet in enumerate(bullets):
        card_y = start_y + idx * 140
        card_x1, card_y1 = 780, card_y
        card_x2, card_y2 = 1820, card_y + 100

        cv2.rectangle(canvas, (card_x1, card_y1), (card_x2, card_y2), (245, 247, 250), -1)
        cv2.rectangle(canvas, (card_x1, card_y1), (card_x2, card_y2), (210, 220, 235), 2)

        cv2.circle(canvas, (card_x1 + 35, card_y1 + 50), 16, (232, 115, 26), -1, cv2.LINE_AA)
        cv2.putText(canvas, str(idx + 1), (card_x1 + 29, card_y1 + 56), font, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, bullet[:65], (card_x1 + 75, card_y1 + 58), font, 0.75, (64, 64, 64), 2, cv2.LINE_AA)

    Path(output_png).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_png, canvas)
    return output_png


def assemble_osl_lesson_from_blueprint(
    trimmed_teacher_video: str,
    blueprint_json: str,
    output_final_video: str,
    work_dir: str
) -> str:
    """
    Assembles complete multi-scene OSL lesson from LLM Presentation Blueprint:
    1. Iterates through blueprint scenes (Hook 100% -> Objectives 70% -> Core 20% -> Summary 70% -> Next 70%).
    2. Slices teacher video to scene [start_time, end_time].
    3. Composites teacher video into assigned layout (100, 70, 20) with generated slide graphics.
    4. Seamlessly concatenates all scenes.
    5. Appends mandatory 0.5s White Dissolve Outro.
    """
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    with open(blueprint_json, "r", encoding="utf-8") as f:
        blueprint = json.load(f)

    scenes = blueprint.get("scenes", [])
    if not scenes:
        raise ValueError("Blueprint contains no scenes.")

    # Measure actual trimmed video duration
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
    print(f"\n[OSL Post-Production] Assembling {len(scenes)} blueprint scenes (Duration: {actual_duration:.2f}s)...")

    for idx, scene in enumerate(scenes):
        sid = scene.get("scene_id", idx + 1)
        layout = str(scene.get("sme_layout", "70"))
        raw_st = scene.get("start_time", 0.0)
        raw_et = scene.get("end_time", actual_duration)

        # Scale and clamp strictly to actual duration
        st = max(0.0, min(actual_duration - 0.2, raw_st * time_scale))
        et = min(actual_duration, max(st + 0.5, raw_et * time_scale))
        seg_duration = max(0.5, et - st)
        slide_img = scene.get("rendered_slide_png")

        # 1. Slice teacher subclip for this scene (input first for accurate frame decode)
        scene_subclip = Path(work_dir) / f"subclip_scene_{sid:02d}.mp4"
        seg_duration = max(0.5, et - st)
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
        res_slice = subprocess.run(cmd_slice, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res_slice.returncode != 0:
            print(f"Warning: Failed slicing scene {sid}, falling back to full clip")
            scene_subclip = Path(trimmed_teacher_video)

        # 2. Composite with layout
        scene_rendered = Path(work_dir) / f"rendered_scene_{sid:02d}_{layout}.mp4"

        if layout == "100":
            render_sme_layout_100(str(scene_subclip), str(scene_rendered))
        elif layout == "70":
            if not slide_img or not os.path.exists(slide_img):
                slide_img = str(Path(work_dir) / f"fallback_slide_{sid}.png")
                create_simplilearn_slide_template(scene.get("title", "Concept Overview"), scene.get("lead_in_line", ""), ["Key principles and structured techniques", "Best practice application"], slide_img)
            render_sme_layout_70(str(scene_subclip), slide_img, str(scene_rendered), work_dir=work_dir)
        elif layout == "20":
            if not slide_img or not os.path.exists(slide_img):
                slide_img = str(Path(work_dir) / f"fallback_slide_{sid}.png")
                create_simplilearn_slide_template(scene.get("title", "Concept Details"), scene.get("lead_in_line", ""), ["Component architecture", "Operational analysis"], slide_img)
            render_sme_layout_20(str(scene_subclip), slide_img, str(scene_rendered), work_dir=work_dir)

        rendered_scene_clips.append(str(scene_rendered))

    # 3. Concatenate all rendered scenes
    concat_txt = Path(work_dir) / "blueprint_assembly_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in rendered_scene_clips:
            safe = p.replace("'", "'\\''")
            f.write(f"file '{safe}'\n")

    assembled_temp = Path(work_dir) / "assembled_before_dissolve.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(assembled_temp)
    ]
    res_c = subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res_c.returncode != 0:
        # Fallback to re-encoding concat
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
            str(assembled_temp)
        ]
        subprocess.run(cmd_concat_re, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 4. Apply 0.5s White Dissolve Outro
    apply_white_dissolve_outro(str(assembled_temp), output_final_video)

    print(f"\n✓ Complete End-to-End Multi-Scene Video -> {output_final_video}\n")
    return output_final_video


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m pipeline.osl_post_production <input_video> <output_video>")
        sys.exit(1)
    apply_white_dissolve_outro(sys.argv[1], sys.argv[2])
