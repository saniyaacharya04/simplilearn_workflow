#!/usr/bin/env python3
"""
Step 7: SME (Trainer) Placement Layouts (WITHOUT Green Screen)
Reference: SimpliLearn.pdf & OSL_3.0_Post_Production_Guidelines_2026.pdf (Pages 6, 16, 27)

Implements the 3 official layouts:
1. 100% Full Screen
2. 70% Cropped Area (Left-Aligned Rounded Rectangle, Corner Radius = 10 px) + Left Blue Accent Band
3. 20% Right Corner PIP (Top-Right Corner, scaled to 20% FHD)
"""

import os
import sys
import argparse
import subprocess
import cv2
import numpy as np
from pathlib import Path
from typing import Optional

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
    AUDIO_BITRATE,
    SME_LAYOUT_100,
    SME_LAYOUT_70,
    SME_LAYOUT_20
)


def generate_rounded_rect_mask(
    width: int,
    height: int,
    radius: int = 10,
    output_png: Optional[str] = None
) -> np.ndarray:
    """Creates an anti-aliased rounded rectangle mask."""
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.rectangle(mask, (radius, 0), (width - radius, height), 255, -1)
    cv2.rectangle(mask, (0, radius), (width, height - radius), 255, -1)
    cv2.circle(mask, (radius, radius), radius, 255, -1, lineType=cv2.LINE_AA)
    cv2.circle(mask, (width - radius, radius), radius, 255, -1, lineType=cv2.LINE_AA)
    cv2.circle(mask, (radius, height - radius), radius, 255, -1, lineType=cv2.LINE_AA)
    cv2.circle(mask, (width - radius, height - radius), radius, 255, -1, lineType=cv2.LINE_AA)

    if output_png:
        Path(output_png).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(output_png, mask)

    return mask


def render_layout_100(teacher_video: str, output_video: str) -> str:
    """Layout 1: 100% Full Screen."""
    Path(output_video).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(teacher_video),
        "-vf", f"scale={CANVAS_WIDTH}:{CANVAS_HEIGHT}:force_original_aspect_ratio=increase,crop={CANVAS_WIDTH}:{CANVAS_HEIGHT}",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        str(output_video)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"100% Layout failed: {res.stderr}")
    return output_video


def render_layout_70(
    teacher_video: str,
    slide_background: str,
    output_video: str,
    work_dir: Optional[str] = None
) -> str:
    """
    Layout 2: 70% Cropped Area Layout (OSL 3.0 Page 6 & 16).
    Left rounded rectangle (radius 10) with blue accent band.
    """
    if work_dir is None:
        work_dir = Path(output_video).parent / "temp_masks"
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    cfg = SME_LAYOUT_70
    w, h, r = cfg["width"], cfg["height"], cfg["corner_radius"]
    mask_png = Path(work_dir) / f"mask_{w}x{h}_r{r}.png"
    generate_rounded_rect_mask(w, h, radius=r, output_png=str(mask_png))

    filter_complex = (
        f"[0:v]scale={CANVAS_WIDTH}:{CANVAS_HEIGHT},format=yuva420p[bg];"
        f"[bg]drawbox=x=0:y=0:w={cfg['blue_bar_width']}:h={CANVAS_HEIGHT}:color={cfg['blue_bar_color']}:t=fill[bg_blue];"
        f"[1:v]scale=-1:{h},crop={w}:{h},format=yuva420p[sme_crop];"
        f"[2:v]format=yuva420p[mask];"
        f"[sme_crop][mask]alphamerge[sme_rounded];"
        f"[bg_blue][sme_rounded]overlay=x={cfg['x']}:y={cfg['y']}:shortest=1[v]"
    )

    cmd = ["ffmpeg", "-y"]
    if str(slide_background).lower().endswith((".png", ".jpg", ".jpeg")):
        cmd.extend(["-loop", "1"])
    cmd.extend([
        "-i", str(slide_background),
        "-i", str(teacher_video),
        "-loop", "1", "-i", str(mask_png),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a:0?",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-shortest",
        str(output_video)
    ])

    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"70% Layout failed: {res.stderr}")
    return output_video


def render_layout_20(
    teacher_video: str,
    slide_or_demo_media: str,
    output_video: str,
    work_dir: Optional[str] = None
) -> str:
    """
    Layout 3: 20% Right Corner PIP Layout (OSL 3.0 Page 16 & 27).
    Scaled to 20% FHD in top-right corner without overlapping lead-in lines.
    """
    if work_dir is None:
        work_dir = Path(output_video).parent / "temp_masks"
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    cfg = SME_LAYOUT_20
    w, h, r = cfg["width"], cfg["height"], cfg["corner_radius"]
    mask_png = Path(work_dir) / f"mask_{w}x{h}_r{r}.png"
    generate_rounded_rect_mask(w, h, radius=r, output_png=str(mask_png))

    filter_complex = (
        f"[0:v]scale={CANVAS_WIDTH}:{CANVAS_HEIGHT},format=yuva420p[content];"
        f"[1:v]scale={w}:{h},format=yuva420p[sme_small];"
        f"[2:v]format=yuva420p[mask];"
        f"[sme_small][mask]alphamerge[sme_pip];"
        f"[content][sme_pip]overlay=x={cfg['x']}:y={cfg['y']}:shortest=1[v]"
    )

    cmd = ["ffmpeg", "-y"]
    if str(slide_or_demo_media).lower().endswith((".png", ".jpg", ".jpeg")):
        cmd.extend(["-loop", "1"])
    cmd.extend([
        "-i", str(slide_or_demo_media),
        "-i", str(teacher_video),
        "-loop", "1", "-i", str(mask_png),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a:0?",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-shortest",
        str(output_video)
    ])

    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"20% Layout failed: {res.stderr}")
    return output_video


# Aliases for compatibility
render_sme_layout_100 = render_layout_100
render_sme_layout_70 = render_layout_70
render_sme_layout_20 = render_layout_20


def run_stage_7(
    layout: str,
    teacher_video: str,
    output_video: str,
    background_media: Optional[str] = None
) -> str:
    """Runs complete Stage 7 workflow."""
    print(f"\n==================================================================")
    print(f"STEP 7: SME PLACEMENT LAYOUT '{layout}' (WITHOUT GREEN SCREEN)")
    print(f"==================================================================")

    if layout == "100":
        render_layout_100(teacher_video, output_video)
    elif layout == "70":
        if not background_media:
            raise ValueError("70% Layout requires background slide image/video.")
        render_layout_70(teacher_video, background_media, output_video)
    elif layout == "20":
        if not background_media:
            raise ValueError("20% Layout requires background slide/demo image/video.")
        render_layout_20(teacher_video, background_media, output_video)
    else:
        raise ValueError(f"Unknown layout: {layout}. Must be 100, 70, or 20.")

    print(f"✓ Step 7 Complete: Rendered layout '{layout}' -> {output_video}\n")
    return output_video


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 7: SME Placement Layouts (No Green Screen)")
    parser.add_argument("-l", "--layout", choices=["100", "70", "20"], required=True, help="SME layout type")
    parser.add_argument("-i", "--input", required=True, help="Teacher video file")
    parser.add_argument("-o", "--output", required=True, help="Output composited video")
    parser.add_argument("-b", "--background", default=None, help="Background slide image or video")
    args = parser.parse_args()

    run_stage_7(args.layout, args.input, args.output, background_media=args.background)
