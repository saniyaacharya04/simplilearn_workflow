"""
Simplilearn SME (Trainer) Placement & Layout Engine
Reference: SimpliLearn.pdf & OSL_3.0_Post_Production_Guidelines_2026.pdf (Pages 6, 16, 27)

Client Guideline Specification:
The client guidelines define exactly 3 SME Placement Layouts (NO green screen, NO AI matting):
1. 100% Full Screen Layout:
   - Full 1920x1080 trainer video (used for Intro, Hook, Topic Intros, and Outro/Closing).
2. 70% Cropped Area Layout (Left-Aligned Rounded Rectangle):
   - Trainer video cropped to 640x920 inside a rounded rectangle with corner radius = 10 px.
   - Left blue accent band (#1A73E8).
   - Positioned at (x=80, y=80).
   - Used for Learning Objectives, Concept Intro, and What's Next templates.
3. 20% Right Corner PIP Layout:
   - Scaled to 384x216 (20% of Full HD 1080p).
   - Positioned in the top-right corner (x=1496, y=40) with 8-10px rounded corners.
   - Leaves ample room for the slide lead-in line and demo/slide graphics without overlap.
"""

import os
import subprocess
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

from .config import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    FRAME_RATE,
    VIDEO_CODEC,
    VIDEO_PRESET,
    VIDEO_CRF,
    AUDIO_BITRATE,
    SME_LAYOUT_100,
    SME_LAYOUT_70,
    SME_LAYOUT_20
)


# ==============================================================================
# 1. ROUNDED RECTANGLE ALPHA MASK GENERATOR
# ==============================================================================

def generate_rounded_rect_mask(
    width: int,
    height: int,
    radius: int = 10,
    output_png: Optional[str] = None
) -> np.ndarray:
    """
    Creates an 8-bit anti-aliased rounded rectangle mask.
    Corner radius defaults to 10 as specified in OSL 3.0 Page 6.
    """
    mask = np.zeros((height, width), dtype=np.uint8)

    # Core rectangles
    cv2.rectangle(mask, (radius, 0), (width - radius, height), 255, -1)
    cv2.rectangle(mask, (0, radius), (width, height - radius), 255, -1)

    # 4 anti-aliased rounded corners
    cv2.circle(mask, (radius, radius), radius, 255, -1, lineType=cv2.LINE_AA)
    cv2.circle(mask, (width - radius, radius), radius, 255, -1, lineType=cv2.LINE_AA)
    cv2.circle(mask, (radius, height - radius), radius, 255, -1, lineType=cv2.LINE_AA)
    cv2.circle(mask, (width - radius, height - radius), radius, 255, -1, lineType=cv2.LINE_AA)

    if output_png:
        Path(output_png).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(output_png, mask)

    return mask


# ==============================================================================
# 2. OFFICIAL LAYOUT 1: 100% FULL SCREEN
# ==============================================================================

def render_sme_layout_100(
    teacher_video: str,
    output_video: str
) -> str:
    """
    Layout 1: 100% Full-Screen Layout (OSL 3.0 Page 16).
    Scales/crops raw trainer video to Full HD 1920x1080 30fps.
    Used for Hook, Topic Introduction, and Final Closing.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", str(teacher_video),
        "-vf", (
            f"scale={CANVAS_WIDTH}:{CANVAS_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={CANVAS_WIDTH}:{CANVAS_HEIGHT}"
        ),
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        str(output_video)
    ]
    print(f"\n[SME Placement] Rendering 100% Full-Screen -> {output_video}")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg 100% Layout failed: {res.stderr}")

    return output_video


# ==============================================================================
# 3. OFFICIAL LAYOUT 2: 70% CROPPED AREA (ROUNDED RECTANGLE, RADIUS = 10)
# ==============================================================================

def render_sme_layout_70(
    teacher_video: str,
    slide_background: str,
    output_video: str,
    work_dir: Optional[str] = None
) -> str:
    """
    Layout 2: 70% Cropped Area Layout (OSL 3.0 Page 6, 16 & 17).
    - Trainer video cropped to 640x920 inside a rounded rectangle with corner radius = 10 px.
    - Positioned at (x=80, y=80).
    - Left blue vertical accent band (#1A73E8, width=180, height=1080).
    - Right area (x=760 to 1920) reserved for slide title, learning objectives, and content.
    - Raw room/office background of trainer is preserved inside the rounded frame (NO green screen / NO AI matting).
    """
    if work_dir is None:
        work_dir = Path(output_video).parent / "temp_masks"
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    cfg = SME_LAYOUT_70
    w, h, r = cfg["width"], cfg["height"], cfg["corner_radius"]
    mask_png = Path(work_dir) / f"mask_{w}x{h}_r{r}.png"
    generate_rounded_rect_mask(w, h, radius=r, output_png=str(mask_png))

    filter_complex = (
        # 1. Scale background slide to Full HD 1920x1080
        f"[0:v]scale={CANVAS_WIDTH}:{CANVAS_HEIGHT},format=yuva420p[bg];"
        # 2. Draw Left Blue Accent Bar (width=180, height=1080, color=#1A73E8)
        f"[bg]drawbox=x=0:y=0:w={cfg['blue_bar_width']}:h={CANVAS_HEIGHT}:color={cfg['blue_bar_color']}:t=fill[bg_blue];"
        # 3. Center crop and scale teacher video to 640x920
        f"[1:v]scale=-1:{h},crop={w}:{h},format=yuva420p[sme_crop];"
        # 4. Apply rounded rectangle alpha mask (radius 10)
        f"[2:v]format=yuva420p[mask];"
        f"[sme_crop][mask]alphamerge[sme_rounded];"
        # 5. Overlay teacher rounded box onto canvas at (80, 80)
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

    print(f"\n[SME Placement] Rendering 70% Layout (Rounded Rect r=10) -> {output_video}")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg 70% Layout failed: {res.stderr}")

    return output_video


# ==============================================================================
# 4. OFFICIAL LAYOUT 3: 20% TOP-RIGHT CORNER PIP
# ==============================================================================

def render_sme_layout_20(
    teacher_video: str,
    slide_or_demo_video: str,
    output_video: str,
    work_dir: Optional[str] = None
) -> str:
    """
    Layout 3: 20% Right Corner PIP Layout (OSL 3.0 Page 16 & 27).
    - Scaled to 384x216 (20% of 1080p FHD).
    - Positioned at top-right (x=1496, y=40).
    - Framed with subtle rounded corners (radius = 8 px).
    - Leaves ample room for the slide lead-in line and demo screen without overlap.
    - Raw room background of trainer is preserved inside the frame (NO green screen / NO AI matting).
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
    if str(slide_or_demo_video).lower().endswith((".png", ".jpg", ".jpeg")):
        cmd.extend(["-loop", "1"])
    cmd.extend([
        "-i", str(slide_or_demo_video),
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

    print(f"\n[SME Placement] Rendering 20% Top-Right Corner PIP -> {output_video}")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg 20% Layout failed: {res.stderr}")

    return output_video


# ==============================================================================
# PIPELINE DISPATCHER
# ==============================================================================

def apply_sme_layout(
    layout_type: str,
    teacher_video: str,
    output_video: str,
    background_media: Optional[str] = None
) -> str:
    """Applies one of the 3 official Simplilearn placement layouts."""
    if layout_type == "100":
        return render_sme_layout_100(teacher_video, output_video)
    elif layout_type == "70":
        if not background_media:
            raise ValueError("70% Layout requires a background slide image or video.")
        return render_sme_layout_70(teacher_video, background_media, output_video)
    elif layout_type == "20":
        if not background_media:
            raise ValueError("20% Layout requires a background slide/demo image or video.")
        return render_sme_layout_20(teacher_video, background_media, output_video)
    else:
        raise ValueError(f"Unknown layout: {layout_type}. Official layouts: '100', '70', '20'.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python -m pipeline.teacher_cutout_and_placement <100|70|20> <teacher_video> <output_video> [background_media]")
        sys.exit(1)
    apply_sme_layout(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
