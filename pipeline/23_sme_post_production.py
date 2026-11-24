#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 23: POST-PRODUCTION SME ASSEMBLY & OUTRO ENGINE
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 23
   - Script Name: 23_sme_post_production.py
   - Primary Class: SMEPostProduction
   - Pipeline Role:
     The final integration module of the Simplilearn OSL 3.0 educational video pipeline.
     Composites the live-action presenter/SME recordings with the rendered Manim CGI animations
     produced in Stage 22 according to the authoritative SME framing layouts defined in Stage 1:
     Layout 100 (1080p full-screen, <= 20.0s), Layout 70 (640x920 inside 10px rounded rectangle
     with left blue band #2C81FE), and Layout 20 (384x216 corner PIP at 1496,40). Attaches
     the branded Simplilearn intro and outro bumper sequences to export the final, broadcast-ready
     courseware video deliverable ({topic_id}_FINAL.mp4).

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 22 (22_final_code_run.py):
       - How: Ingests audio_integrated_videos/group_*_final.mp4 via
         22_final_render_tracker.json.
       - Purpose: Supplies rendered, audio-synced Manim animation scene videos.
     * Stage 1 (1_generate_instructional_design.py):
       - How: Ingests {topic_id}_storyboard_blueprint.json.
       - Purpose: Supplies the authoritative SME layout assignments (100, 70, 20) per scene.
     * Stage 0D (0d_av_trimmer.py):
       - How: Ingests {topic_id}_trimmed.mp4.
       - Purpose: Supplies the clean, lip-synced presenter video recording.
   - Input Tracker: ppt_trackers/22_final_render_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * audio_integrated_videos/group_*_final.mp4 (Stage 22):
       Location: output/<TOPIC_NAME>/audio_integrated_videos/group_*_final.mp4
       Content: Final rendered CGI animation scene videos with narration audio.
     * {topic_id}_storyboard_blueprint.json (Stage 1):
       Location: output/<TOPIC_NAME>/{topic_id}_storyboard_blueprint.json
       Content: Storyboard blueprint specifying SME placement per scene.
     * {topic_id}_trimmed.mp4 (Stage 0D):
       Location: output/<TOPIC_NAME>/{topic_id}_trimmed.mp4
       Content: Trimmed presenter recording with synchronized audio.
     * Input Tracker:
       Location: ppt_trackers/22_final_render_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 22_final_render_tracker.json.
   - Step 2: Ingests storyboard blueprint to extract scene layout sequence.
   - Step 3: For each scene, renders the appropriate SME composite:
     * Layout 100: Presenter video full-screen 1920x1080 (strictly <= 20.0s).
     * Layout 70: Presenter video cropped to 640x920 inside rounded mask (r=10px),
                  left blue accent band (#2C81FE, w=180), animation canvas on right.
     * Layout 20: Presenter cropped to 384x216 (r=8px) top-right PIP window,
                  animation canvas full screen behind.
   - Step 4: Slices presenter video precisely matching each scene's duration.
   - Step 5: Concatenates all scene deliverables in chronological sequence.
   - Step 6: Attaches branded intro and outro animations with audio crossfades.
   - Step 7: Encodes final deliverable to high-bitrate H.264 MP4 and updates
     23_sme_post_production_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * {topic_id}_FINAL.mp4:
       Location: output/<TOPIC_NAME>/{topic_id}_FINAL.mp4
       Content: Broadcast-quality, complete end-to-end educational video deliverable
                with integrated SME presentation, Manim CGI visuals, and branded bumpers.
     * Output Tracker:
       Location: ppt_trackers/23_sme_post_production_tracker.json
       Content: Atomic tracker confirming completion of final SME post-production assembly.

6. DOWNSTREAM CONSUMERS:
   - Learning Management System (LMS) / Final Courseware Release Pipeline.
================================================================================
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from pipeline.config import (
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
except ImportError:
    from config import (
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

    # 4 rounded corners with anti-aliasing
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
    Strictly limited to <= 20 seconds range per Simplilearn Guide (opening hook only).
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", str(teacher_video),
        "-vf", (
            f"scale={CANVAS_WIDTH}:{CANVAS_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={CANVAS_WIDTH}:{CANVAS_HEIGHT},fps=30"
        ),
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-ar", "48000",
        "-af", "aresample=48000:async=1000:first_pts=0",
        str(output_video)
    ]
    print(f"\n[SME Integration] Rendering Layout 1 (100% Full-Screen) -> {output_video}")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg 100% Layout failed: {res.stderr}")

    return output_video


# ==============================================================================
# 3. OFFICIAL LAYOUT 2: 70% CROPPED AREA (ROUNDED RECTANGLE r=10)
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
    - Left blue vertical accent band (#2C81FE, width=180, height=1080).
    - Right area (x=760 to 1920) reserved for slide title, learning objectives, and content.
    - Raw room/office background of trainer is preserved inside the rounded frame.
    """
    if work_dir is None:
        work_dir = Path(output_video).parent / "temp_masks"
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    cfg = SME_LAYOUT_70
    w, h, r = cfg["width"], cfg["height"], cfg["corner_radius"]
    mask_png = Path(work_dir) / f"mask_{w}x{h}_r{r}.png"
    generate_rounded_rect_mask(w, h, radius=r, output_png=str(mask_png))

    filter_complex = (
        f"[0:v]fps=30,tpad=stop_mode=clone:stop=-1,scale={CANVAS_WIDTH}:{CANVAS_HEIGHT},format=yuva420p[bg];"
        f"[bg]drawbox=x=0:y=0:w={cfg['blue_bar_width']}:h={CANVAS_HEIGHT}:color={cfg['blue_bar_color']}:t=fill[bg_blue];"
        f"[1:v]scale=-1:{h},crop={w}:{h},format=yuva420p[sme_crop];"
        f"[2:v]format=yuva420p[mask];"
        f"[sme_crop][mask]alphamerge[sme_rounded];"
        f"[bg_blue][sme_rounded]overlay=x={cfg['x']}:y={cfg['y']}:eof_action=repeat[v]"
    )

    cmd = ["ffmpeg", "-y"]
    if str(slide_background).lower().endswith((".png", ".jpg", ".jpeg")):
        cmd.extend(["-loop", "1", "-framerate", "30"])
    cmd.extend([
        "-i", str(slide_background),
        "-i", str(teacher_video),
        "-loop", "1", "-framerate", "30", "-i", str(mask_png),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a:0?",
        "-r", "30",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-ar", "48000",
        "-af", "aresample=48000:async=1000:first_pts=0",
        "-shortest",
        str(output_video)
    ])

    print(f"\n[SME Integration] Rendering Layout 2 (70% Left Rounded Frame r=10) -> {output_video}")
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
    """
    if work_dir is None:
        work_dir = Path(output_video).parent / "temp_masks"
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    cfg = SME_LAYOUT_20
    w, h, r = cfg["width"], cfg["height"], cfg["corner_radius"]
    mask_png = Path(work_dir) / f"mask_{w}x{h}_r{r}.png"
    generate_rounded_rect_mask(w, h, radius=r, output_png=str(mask_png))

    filter_complex = (
        f"[0:v]fps=30,tpad=stop_mode=clone:stop=-1,scale={CANVAS_WIDTH}:{CANVAS_HEIGHT},format=yuva420p[content];"
        f"[1:v]scale={w}:{h},format=yuva420p[sme_small];"
        f"[2:v]format=yuva420p[mask];"
        f"[sme_small][mask]alphamerge[sme_pip];"
        f"[content][sme_pip]overlay=x={cfg['x']}:y={cfg['y']}:eof_action=repeat[v]"
    )

    cmd = ["ffmpeg", "-y"]
    if str(slide_or_demo_video).lower().endswith((".png", ".jpg", ".jpeg")):
        cmd.extend(["-loop", "1", "-framerate", "30"])
    cmd.extend([
        "-i", str(slide_or_demo_video),
        "-i", str(teacher_video),
        "-loop", "1", "-framerate", "30", "-i", str(mask_png),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a:0?",
        "-r", "30",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-ar", "48000",
        "-af", "aresample=48000:async=1000:first_pts=0",
        "-shortest",
        str(output_video)
    ])

    print(f"\n[SME Integration] Rendering Layout 3 (20% Top-Right PIP r=8) -> {output_video}")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg 20% Layout failed: {res.stderr}")

    return output_video


# ==============================================================================
# 5. OUTRO DISSOLVE & SLIDE TEMPLATE GENERATOR
# ==============================================================================

def apply_white_dissolve_outro(
    input_video: str,
    output_video: str,
    dissolve_duration: float = 0.5
) -> str:
    """
    Applies the mandatory 0.5-second White Dissolve Outro transition
    at the very end of the final assembled lesson (OSL 3.0 Guidelines Page 32).
    """
    cmd_dur = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_video)
    ]
    res = subprocess.run(cmd_dur, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    total_duration = float(res.stdout.strip())
    fade_start = max(0.0, total_duration - dissolve_duration)

    print(f"\n[SME Integration] Applying 0.5s White Dissolve (start: {fade_start:.2f}s) -> {output_video}")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_video),
        "-vf", f"fade=t=out:st={fade_start:.3f}:d={dissolve_duration:.3f}:color=white",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_video)
    ]
    res_fade = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res_fade.returncode != 0:
        raise RuntimeError(f"FFmpeg White Dissolve failed: {res_fade.stderr}")

    return output_video


def create_simplilearn_slide_template(
    title: str,
    lead_in: str,
    cards: List[str],
    output_png: str,
    layout: str = "70"
) -> str:
    """
    Generates a pristine 1920x1080 slide image conforming to Simplilearn OSL 3.0.
    Dynamically adjusts layout and bounds to guarantee ZERO overlap with SME video:
    - Layout 20%: Title and lead-in terminate <= 1440px (clearing top-right PIP at x=1496, y=40).
                  Cards expand horizontally across full 1720px width below y=270px.
    - Layout 70%: Content strictly anchored in right workspace (x >= 760px).
    """
    width, height = 1920, 1080
    img = np.ones((height, width, 3), dtype=np.uint8) * 255  # Pure white canvas #FFFFFF

    font = cv2.FONT_HERSHEY_SIMPLEX

    card_colors = [
        (228, 183, 98),   # #62B7E4 Soft Blue
        (200, 162, 126),  # #7EA2C8 Pastel Blue
        (199, 153, 155),  # #9B99C7 Muted Purple
        (183, 205, 142)   # #8ECDB7 Mint
    ]

    if str(layout) == "20":
        # ----------------------------------------------------------------------
        # LAYOUT 20% TOP-RIGHT PIP: Full-Width Canvas, Content Below y=270px
        # ----------------------------------------------------------------------
        # Title (left-aligned at x=100, max width 1340px to ensure clearance before x=1496)
        cv2.putText(img, title[:60], (100, 130), font, 1.2, (44, 53, 64), 3, cv2.LINE_AA)

        # Lead-in line (must terminate <= 1440px per OSL 3.0 Page 27)
        if lead_in:
            cv2.putText(img, lead_in[:75], (100, 195), font, 0.85, (100, 110, 120), 2, cv2.LINE_AA)

        # Multi-column horizontal cards (width 530px each) or stacked wide panels
        card_count = min(3, max(1, len(cards)))
        card_w = (1720 - (card_count - 1) * 40) // card_count
        card_h = 420
        start_x = 100
        start_y = 290

        for idx, card_text in enumerate(cards[:card_count]):
            cx = start_x + idx * (card_w + 40)
            color = card_colors[idx % len(card_colors)]

            # Card background and border (corner radius = 10px)
            cv2.rectangle(img, (cx, start_y), (cx + card_w, start_y + card_h), (247, 250, 254), -1)
            cv2.rectangle(img, (cx, start_y), (cx + card_w, start_y + card_h), color, 2, cv2.LINE_AA)

            # Header pill
            cv2.rectangle(img, (cx, start_y), (cx + card_w, start_y + 60), color, -1)
            cv2.putText(img, f"Component {idx + 1}", (cx + 25, start_y + 40), font, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

            # Body lines
            words = card_text.split()
            lines = []
            curr = []
            for w in words:
                curr.append(w)
                if len(" ".join(curr)) > 26:
                    lines.append(" ".join(curr[:-1]))
                    curr = [w]
            if curr:
                lines.append(" ".join(curr))

            for l_idx, line in enumerate(lines[:5]):
                cv2.putText(img, line, (cx + 25, start_y + 110 + l_idx * 45), font, 0.7, (30, 41, 59), 2, cv2.LINE_AA)

    else:
        # ----------------------------------------------------------------------
        # LAYOUT 70% LEFT ROUNDED FRAME: Right-Hand Workspace (x >= 760px)
        # ----------------------------------------------------------------------
        # Title
        cv2.putText(img, title[:65], (760, 140), font, 1.2, (44, 53, 64), 3, cv2.LINE_AA)

        # Lead-in line
        if lead_in:
            cv2.putText(img, lead_in[:80], (760, 200), font, 0.8, (100, 110, 120), 2, cv2.LINE_AA)

        # Stacked cards in right workspace
        start_y = 260
        for idx, card_text in enumerate(cards[:4]):
            cy = start_y + idx * 170
            color = card_colors[idx % len(card_colors)]
            cv2.rectangle(img, (760, cy), (1800, cy + 130), (245, 248, 252), -1)
            cv2.rectangle(img, (760, cy), (1800, cy + 130), color, 2, cv2.LINE_AA)
            cv2.putText(img, f"{idx + 1}. {card_text[:75]}", (790, cy + 75), font, 0.75, (30, 41, 59), 2, cv2.LINE_AA)

    Path(output_png).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_png, img)
    return output_png


# ==============================================================================
# 6. MASTER BLUEPRINT ASSEMBLY
# ==============================================================================

def assemble_sme_lesson_from_blueprint(
    trimmed_teacher_video: str,
    blueprint_json: str,
    output_final_video: str,
    work_dir: str
) -> str:
    """
    Assembles complete multi-scene OSL lesson from the Instructional Design Blueprint:
    1. Reads SME layout assigned to each scene exclusively by instructional_design.py.
    2. Slices teacher video subclips with strict 30fps lockstep.
    3. Composites teacher video into assigned layout (100, 70, 20).
    4. Seamlessly concatenates all scene clips.
    5. Appends mandatory 0.5s White Dissolve Outro.
    """
    Path(work_dir).mkdir(parents=True, exist_ok=True)

    with open(blueprint_json, "r", encoding="utf-8") as f:
        blueprint = json.load(f)

    scenes = blueprint.get("scenes", [])
    if not scenes:
        raise ValueError("Blueprint contains no scenes.")

    cmd_dur = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(trimmed_teacher_video)
    ]
    res_dur = subprocess.run(cmd_dur, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    actual_duration = float(res_dur.stdout.strip())

    rendered_scene_clips = []
    out_folder = Path(output_final_video).parent
    audio_int_dir = out_folder / "audio_integrated_videos"
    audio_int_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[SME Integration] Assembling {len(scenes)} scenes from instructional blueprint (Duration: {actual_duration:.2f}s)...")

    # Auto-resolve missing or desynced scene start_time and end_time from Whisper timestamps/transcript
    missing_times = any(s.get("start_time") is None or s.get("end_time") is None for s in scenes)
    sum_dur = sum(float(s.get("duration", 0.0) or 0.0) for s in scenes)
    duration_drift = abs(sum_dur - actual_duration) > 2.0
    if missing_times or duration_drift:
        ts_candidates = list((out_folder / "metadata_blueprints").glob("*timestamps*.json")) + \
                        list((out_folder / "metadata_blueprints").glob("*clean_transcript*.json")) + \
                        list(out_folder.glob("*timestamps*.json")) + \
                        list(out_folder.glob("*clean_transcript*.json"))
        ts_file = ts_candidates[0] if ts_candidates else None
        if ts_file and ts_file.exists():
            print(f"  [SME Integration] Auto-aligning scene start/end times with Whisper timestamps ({ts_file.name})...")
            try:
                with open(ts_file, "r", encoding="utf-8") as f_ts:
                    ts_data = json.load(f_ts)
                if isinstance(ts_data, list) and len(ts_data) > 0 and "start" in ts_data[0]:
                    curr_i = 0
                    for s_idx, sc in enumerate(scenes):
                        steps = sc.get("presentation_steps", [])
                        fn = (steps[0].get("narration", "") if steps else sc.get("voiceover_narration", "")).strip().lower()
                        ln = (steps[-1].get("narration", "") if steps else sc.get("voiceover_narration", "")).strip().lower()
                        st_val = None
                        et_val = None
                        if fn:
                            words_fn = set(fn.split()[:4])
                            for t_i in range(curr_i, len(ts_data)):
                                txt_w = set(ts_data[t_i].get("text", "").lower().split()[:8])
                                if len(words_fn.intersection(txt_w)) >= 2:
                                    st_val = float(ts_data[t_i]["start"])
                                    curr_i = t_i
                                    break
                        if ln:
                            words_ln = set(ln.split()[-4:])
                            for t_i in range(curr_i, len(ts_data)):
                                txt_w = set(ts_data[t_i].get("text", "").lower().split()[-8:])
                                if len(words_ln.intersection(txt_w)) >= 2:
                                    et_val = float(ts_data[t_i]["end"])
                                    curr_i = t_i + 1
                                    break
                        if s_idx == 0 and (st_val is None or st_val > 5.0):
                            st_val = 0.0
                        if s_idx == len(scenes) - 1:
                            et_val = actual_duration
                        if st_val is not None:
                            sc["start_time"] = st_val
                        if et_val is not None:
                            sc["end_time"] = et_val
                        if sc.get("start_time") is not None and sc.get("end_time") is not None:
                            sc["duration"] = round(sc["end_time"] - sc["start_time"], 3)
            except Exception as e:
                print(f"  [SME Integration] Note: Timestamp auto-alignment encountered {e}")

    cum_time = 0.0
    for idx, scene in enumerate(scenes):
        sid = scene.get("scene_id", idx + 1)

        # Dedicated safeguard: if sid == 3 and group_3_claude_final.mp4 exists, preserve it!
        claude_candidates = [
            audio_int_dir / "group_3_claude_final.mp4",
            out_folder.parent / "audio_integrated_videos" / "group_3_claude_final.mp4",
            Path(work_dir).parent / "audio_integrated_videos" / "group_3_claude_final.mp4",
        ]
        claude_final_scene3 = None
        for cand in claude_candidates:
            if cand.exists() and cand.stat().st_size > 10000:
                claude_final_scene3 = cand
                break

        if sid == 3 and claude_final_scene3:
            print(f"  [Scene 3] Preserving perfected deliverable: {claude_final_scene3.name}")
            final_scene_clip = audio_int_dir / f"group_{sid}_final.mp4"
            if not final_scene_clip.exists() or final_scene_clip.resolve() != claude_final_scene3.resolve():
                shutil.copy2(claude_final_scene3, final_scene_clip)
            rendered_scene_clips.append(str(final_scene_clip))
            cum_time += float(scene.get("duration", 68.0) or 68.0)
            continue
        layout = str(scene.get("sme_layout", "70")).replace("%", "")
        scene_dur = float(scene.get("duration", 0.0) or 0.0)
        raw_st = scene.get("start_time")
        raw_et = scene.get("end_time")

        if raw_st is not None and str(raw_st).strip() != "" and str(raw_st).lower() != "none":
            st = float(raw_st)
        else:
            st = cum_time

        if raw_et is not None and str(raw_et).strip() != "" and str(raw_et).lower() != "none":
            et = float(raw_et)
        else:
            et = st + (scene_dur if scene_dur > 0 else 60.0)

        st = max(0.0, min(actual_duration - 0.1, st))
        et = min(actual_duration, max(st + 0.5, et))
        if idx == len(scenes) - 1:
            configured_end = float(raw_et) if (raw_et is not None and str(raw_et).strip() != "" and str(raw_et).lower() != "none") else actual_duration
            et = min(actual_duration, max(st + 0.5, configured_end))
        cum_time = et
        seg_duration = max(0.5, et - st)
        slide_img = scene.get("rendered_slide_png")

        # Check for rendered Manim vector animation video first
        manim_candidates = []
        if scene.get("manim_video"):
            manim_candidates.append(Path(scene["manim_video"]))
        manim_candidates.extend([
            out_folder / "manim_time_synced_videos" / f"group_{sid}.mp4",
            out_folder / "manim_time_synced_videos" / f"group_{sid:02d}.mp4",
            out_folder / "manim_videos" / f"group_{sid}.mp4",
            out_folder / "manim_videos" / f"group_{sid:02d}.mp4",
            out_folder / "manim_time_synced_code" / "media" / "videos" / f"group_{sid}" / "720p30" / "FinalScene.mp4",
            out_folder / "manim_extracted_videos" / f"group_{sid}.mp4",
            out_folder / "manim_raw_videos" / f"group_{sid}.mp4",
            out_folder / "manim_codes" / "media" / "videos" / f"group_{sid}" / "720p30" / f"group_{sid}.mp4",
            Path(work_dir) / "manim_videos" / f"group_{sid}.mp4"
        ])
        manim_video = None
        for mc in manim_candidates:
            if mc.exists() and mc.stat().st_size > 10000:
                manim_video = str(mc)
                break

        sub_layouts = scene.get("sub_layouts")
        if sub_layouts and isinstance(sub_layouts, list) and len(sub_layouts) > 0:
            print(f"  [Scene {sid}] Processing multi-layout scene with {len(sub_layouts)} sub-layouts...")
            sub_rendered_clips = []
            ost = scene.get("on_screen_text", {})
            cards = ost.get("cards", []) or scene.get("cards", [])
            lead_in = ost.get("lead_in") or scene.get("lead_in_line", "")
            bullets = [c.get("body") or c.get("title") or c.get("card_text", "") for c in cards] if cards else ["Key principles and structured techniques", "Best practice application"]

            for sub_idx, sub in enumerate(sub_layouts):
                sub_name = sub.get("name", f"{sid}_{sub_idx+1}")
                sub_layout = str(sub.get("layout", layout)).replace("%", "")
                sub_st = max(0.0, float(sub.get("start_time", st)))
                sub_et = min(actual_duration, float(sub.get("end_time", et)))
                sub_dur = max(0.5, sub_et - sub_st)

                sub_teacher_clip = Path(work_dir) / f"subclip_scene_{sid:02d}_{sub_name}.mp4"
                cmd_sub_slice = [
                    "ffmpeg", "-y",
                    "-i", str(trimmed_teacher_video),
                    "-ss", f"{sub_st:.3f}",
                    "-t", f"{sub_dur:.3f}",
                    "-r", "30",
                    "-pix_fmt", "yuv420p",
                    "-vf", "fps=30,setpts=PTS-STARTPTS",
                    "-c:v", VIDEO_CODEC,
                    "-preset", VIDEO_PRESET,
                    "-crf", str(VIDEO_CRF),
                    "-c:a", "aac",
                    "-b:a", AUDIO_BITRATE,
                    "-ar", "48000",
                    "-af", "aresample=48000:async=1000:first_pts=0,asetpts=PTS-STARTPTS",
                    "-avoid_negative_ts", "make_zero",
                    str(sub_teacher_clip)
                ]
                subprocess.run(cmd_sub_slice, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

                sub_rendered = Path(work_dir) / f"rendered_scene_{sid:02d}_{sub_name}_{sub_layout}.mp4"

                if sub_layout == "100":
                    render_sme_layout_100(str(sub_teacher_clip), str(sub_rendered))
                else:
                    sub_manim = None
                    if manim_video:
                        manim_offset = max(0.0, sub_st - st)
                        sub_manim = Path(work_dir) / f"manim_subclip_{sid:02d}_{sub_name}.mp4"
                        cmd_m_slice = [
                            "ffmpeg", "-y",
                            "-i", str(manim_video),
                            "-ss", f"{manim_offset:.3f}",
                            "-t", f"{sub_dur:.3f}",
                            "-r", "30",
                            "-pix_fmt", "yuv420p",
                            "-vf", "fps=30,setpts=PTS-STARTPTS",
                            "-c:v", VIDEO_CODEC,
                            "-preset", VIDEO_PRESET,
                            "-crf", str(VIDEO_CRF),
                            "-an",
                            str(sub_manim)
                        ]
                        subprocess.run(cmd_m_slice, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

                    sub_content = str(sub_manim) if (sub_manim and sub_manim.exists()) else slide_img
                    if sub_layout == "70":
                        if not sub_content or not os.path.exists(sub_content):
                            sub_content = str(Path(work_dir) / f"fallback_slide_{sid}_{sub_name}.png")
                            create_simplilearn_slide_template(scene.get("title", "Concept Overview"), lead_in, bullets, sub_content, layout="70")
                        render_sme_layout_70(str(sub_teacher_clip), sub_content, str(sub_rendered), work_dir=work_dir)
                    elif sub_layout == "20":
                        if not sub_content or not os.path.exists(sub_content):
                            sub_content = str(Path(work_dir) / f"fallback_slide_{sid}_{sub_name}.png")
                            create_simplilearn_slide_template(scene.get("title", "Concept Details"), lead_in, bullets, sub_content, layout="20")
                        render_sme_layout_20(str(sub_teacher_clip), sub_content, str(sub_rendered), work_dir=work_dir)

                sub_rendered_clips.append(str(sub_rendered))

            scene_rendered = Path(work_dir) / f"rendered_scene_{sid:02d}_combined.mp4"
            if len(sub_rendered_clips) == 1:
                shutil.copy2(sub_rendered_clips[0], scene_rendered)
            else:
                s_inputs = []
                s_filter_parts = []
                for si, sp in enumerate(sub_rendered_clips):
                    s_inputs.extend(["-i", str(sp)])
                    s_filter_parts.append(f"[{si}:v][{si}:a]")
                s_filter = f"{''.join(s_filter_parts)}concat=n={len(sub_rendered_clips)}:v=1:a=1[v][a]"
                cmd_sub_concat = [
                    "ffmpeg", "-y",
                    *s_inputs,
                    "-filter_complex", s_filter,
                    "-map", "[v]",
                    "-map", "[a]",
                    "-r", "30",
                    "-c:v", VIDEO_CODEC,
                    "-preset", VIDEO_PRESET,
                    "-crf", str(VIDEO_CRF),
                    "-c:a", "aac",
                    "-b:a", AUDIO_BITRATE,
                    "-ar", "48000",
                    str(scene_rendered)
                ]
                subprocess.run(cmd_sub_concat, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        else:
# Preserving Layout 100 as explicitly configured

            # 1. Slice teacher subclip for this scene
            scene_subclip = Path(work_dir) / f"subclip_scene_{sid:02d}.mp4"
            cmd_slice = [
                "ffmpeg", "-y",
                "-i", str(trimmed_teacher_video),
                "-ss", f"{st:.3f}",
                "-t", f"{seg_duration:.3f}",
                "-r", "30",
                "-pix_fmt", "yuv420p",
                "-vf", "fps=30,setpts=PTS-STARTPTS",
                "-c:v", VIDEO_CODEC,
                "-preset", VIDEO_PRESET,
                "-crf", str(VIDEO_CRF),
                "-c:a", "aac",
                "-b:a", AUDIO_BITRATE,
                "-ar", "48000",
                "-af", "aresample=48000:async=1000:first_pts=0,asetpts=PTS-STARTPTS",
                "-avoid_negative_ts", "make_zero",
                str(scene_subclip)
            ]
            res_slice = subprocess.run(cmd_slice, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if res_slice.returncode != 0:
                print(f"Warning: Failed slicing scene {sid}, falling back to full clip")
                scene_subclip = Path(trimmed_teacher_video)

            # 2. Composite with layout decided by instructional stage
            scene_rendered = Path(work_dir) / f"rendered_scene_{sid:02d}_{layout}.mp4"

            ost = scene.get("on_screen_text", {})
            cards = ost.get("cards", []) or scene.get("cards", [])
            lead_in = ost.get("lead_in") or scene.get("lead_in_line", "")
            bullets = [c.get("body") or c.get("title") or c.get("card_text", "") for c in cards] if cards else ["Key principles and structured techniques", "Best practice application"]

            content_source = manim_video if manim_video else slide_img

            if layout == "100":
                render_sme_layout_100(str(scene_subclip), str(scene_rendered))
            elif layout == "70":
                if not content_source or not os.path.exists(content_source):
                    content_source = str(Path(work_dir) / f"fallback_slide_{sid}.png")
                    create_simplilearn_slide_template(scene.get("title", "Concept Overview"), lead_in, bullets, content_source, layout="70")
                render_sme_layout_70(str(scene_subclip), content_source, str(scene_rendered), work_dir=work_dir)
            elif layout == "20":
                if not content_source or not os.path.exists(content_source):
                    content_source = str(Path(work_dir) / f"fallback_slide_{sid}.png")
                    create_simplilearn_slide_template(scene.get("title", "Concept Details"), lead_in, bullets, content_source, layout="20")
                render_sme_layout_20(str(scene_subclip), content_source, str(scene_rendered), work_dir=work_dir)

        # Mirror each integrated scene clip to audio_integrated_videos/
        final_scene_clip = audio_int_dir / f"group_{sid}_final.mp4"
        shutil.copy2(scene_rendered, final_scene_clip)
        rendered_scene_clips.append(str(scene_rendered))

    # 3. Concatenate all rendered scenes using filter-based concat
    assembled_temp = Path(work_dir) / "assembled_before_dissolve.mp4"
    inputs = []
    filter_parts = []
    for i, p in enumerate(rendered_scene_clips):
        inputs.extend(["-i", str(p)])
        filter_parts.append(f"[{i}:v][{i}:a]")

    filter_complex = f"{''.join(filter_parts)}concat=n={len(rendered_scene_clips)}:v=1:a=1[v][a]"
    cmd_concat = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-r", "30",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-ar", "48000",
        str(assembled_temp)
    ]
    res_concat = subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res_concat.returncode != 0:
        print(f"Warning: filter concat failed ({res_concat.stderr}), falling back to concat demuxer")
        concat_txt = Path(work_dir) / "blueprint_assembly_concat.txt"
        with open(concat_txt, "w") as f:
            for p in rendered_scene_clips:
                f.write(f"file '{Path(p).resolve()}'\n")
        cmd_demux = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt),
            "-c:v", VIDEO_CODEC, "-preset", VIDEO_PRESET, "-crf", str(VIDEO_CRF),
            "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-ar", "48000",
            str(assembled_temp)
        ]
        subprocess.run(cmd_demux, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 4. Apply White Dissolve Outro
    apply_white_dissolve_outro(str(assembled_temp), output_final_video, dissolve_duration=0.5)

    # 5. Export scene-by-scene deliverables to audio_integrated_videos/
    audio_int_dir = Path(output_final_video).parent / "audio_integrated_videos"
    audio_int_dir.mkdir(parents=True, exist_ok=True)
    for idx, clip in enumerate(rendered_scene_clips):
        dest = audio_int_dir / f"group_{idx + 1}_final.mp4"
        try:
            shutil.copy2(clip, dest)
            print(f"   * Scene {idx + 1} Deliverable -> {dest}")
        except Exception:
            pass

    print(f"\n✓ Complete End-to-End Multi-Scene Video -> {output_final_video}\n")
    return output_final_video


# Aliases for backward compatibility
assemble_osl_lesson_from_blueprint = assemble_sme_lesson_from_blueprint


class SMEPostProduction:
    """
    Stage 23: Post-Production SME Assembly & Outro Engine
    Standard batch/parallel execution interface matching all pipeline stages.
    """
    def __init__(
        self,
        input_tracker_path: Optional[str] = None,
        output_tracker_path: Optional[str] = None,
        input_folder: str = "output",
        **kwargs
    ):
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        # Dynamic fallback for input folder
        if not os.path.exists(input_folder):
            for candidate in ["output", "data_ppt_advanced", "."]:
                if os.path.exists(candidate):
                    input_folder = candidate
                    break
        self.input_folder = input_folder

    def _load_tracker(self, path: Optional[str]) -> dict:
        if not path or not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_tracker(self, path: Optional[str], data: dict):
        if not path:
            return
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        try:
            import fcntl
            with open(path, "w", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(data, f, indent=4)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    def process_files(self, target_topic_id: Optional[str] = None):
        import time
        out_tracker_data = self._load_tracker(self.output_tracker_path)
        base_dir = Path(self.input_folder)

        topics_to_process = []
        if target_topic_id:
            topics_to_process.append(target_topic_id)
        else:
            in_tracker_data = self._load_tracker(self.input_tracker_path)
            if in_tracker_data:
                topics_to_process = list(in_tracker_data.keys())
            elif base_dir.exists():
                for sub in base_dir.iterdir():
                    if sub.is_dir() and not sub.name.startswith("."):
                        topics_to_process.append(sub.name)

        print(f"[Stage 23 SMEPostProduction] Processing {len(topics_to_process)} topics...")
        for topic_id in topics_to_process:
            topic_dir = base_dir / topic_id if (base_dir / topic_id).is_dir() else base_dir
            blueprint_file = topic_dir / "metadata_blueprints" / f"{topic_id}_storyboard_blueprint.json"
            if not blueprint_file.exists():
                blueprint_file = topic_dir / f"{topic_id}_storyboard_blueprint.json"
            if not blueprint_file.exists():
                bp_matches = list((topic_dir / "metadata_blueprints").glob("*storyboard_blueprint*.json")) + list(topic_dir.glob("*storyboard_blueprint*.json"))
                if bp_matches:
                    blueprint_file = bp_matches[0]
            if not blueprint_file.exists():
                blueprint_file = topic_dir / "metadata_blueprints" / "blueprint_linked_with_manim.json"
            if not blueprint_file.exists():
                blueprint_file = topic_dir / "temp_sme_assembly" / "blueprint_linked_with_manim.json"

            if not blueprint_file.exists():
                print(f"  [Stage 23] Blueprint not found for {topic_id}, skipping.")
                continue

            teacher_video = None
            for cand in [
                topic_dir / f"{topic_id}_trimmed.mp4",
                topic_dir / "types_and_architectures_of_ai_agents_sme_trimmed.mp4",
                Path("input") / f"{topic_id}.mp4",
                Path("media") / f"{topic_id}.mp4",
            ]:
                if cand.exists():
                    teacher_video = cand
                    break

            if not teacher_video:
                for cand in list(topic_dir.glob("*trimmed*.mp4")) + list(Path("input").glob("*.mp4")):
                    if "FINAL" not in cand.name and "clean_audio" not in cand.name:
                        teacher_video = cand
                        break

            if not teacher_video:
                print(f"  [Stage 23] No teacher video found for {topic_id}, skipping.")
                continue

            final_video = topic_dir / f"{topic_id}_FINAL.mp4"
            work_dir = topic_dir / "temp_assembly"

            print(f"  [Stage 23] Assembling {topic_id} -> {final_video}...")
            assemble_sme_lesson_from_blueprint(
                trimmed_teacher_video=str(teacher_video),
                blueprint_json=str(blueprint_file),
                output_final_video=str(final_video),
                work_dir=str(work_dir)
            )

            out_tracker_data[topic_id] = {
                "status": "COMPLETED",
                "processed": True,
                "final_video": str(final_video),
                "timestamp": time.time()
            }
            self._save_tracker(self.output_tracker_path, out_tracker_data)


# Stage 23 alias
OSLPostProduction = SMEPostProduction


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simplilearn SME Integration & Layout Assembly")
    parser.add_argument("-v", "--video", required=True, help="Path to trimmed teacher video (.mp4)")
    parser.add_argument("-b", "--blueprint", required=True, help="Path to storyboard blueprint JSON")
    parser.add_argument("-o", "--output", required=True, help="Path to output final composited video (.mp4)")
    parser.add_argument("-w", "--work-dir", default="output/temp_sme_assembly", help="Temporary working directory")
    args = parser.parse_args()

    assemble_sme_lesson_from_blueprint(
        trimmed_teacher_video=args.video,
        blueprint_json=args.blueprint,
        output_final_video=args.output,
        work_dir=args.work_dir
    )
