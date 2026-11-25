#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 19: VLM TIMESTAMPED FIX GENERATOR
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 19
   - Script Name: 19_vlm_fixing_stage.py
   - Primary Class: VLMTimestampedFixStage
   - Pipeline Role:
     Acts as the multimodal reasoning bridge between visual QA analysis and code
     refactoring. Takes 2 representative visual keyframes per section (peak error
     action frame + settled composition frame), cumulative section timestamps (M:SS),
     error insights, and the existing Manim code. Calls Gemini 3.8 Flash to synthesize
     concrete, timestamped physical fixing directives (e.g., "0:40 <directive>", "1:23 <directive>")
     that Stage 20 uses to repair code.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 18 (18_vlm_fix_suggestor.py):
       - How: Ingests vlm_inputs/scene_{group}/sec_*_aesthetic.json via
         18_vlm_fix_tracker.json.
       - Purpose: Supplies aesthetic quality assessments, flagged contrast errors, and layout hints.
     * Stage 17 (17_generate_visual_triangulation.py):
       - How: Ingests vlm_inputs/scene_{group}/manifest.json.
       - Purpose: Consumes the triangulation manifest to obtain exact code block boundaries (start_line to end_line),
         Set-of-Marks object identities, and grid coordinates for surgical code repairs.
     * Stage 14 (14_implement_corrections.py):
       - How: Ingests corrected Manim code manim_extracted_codes/group_{group}.py.
       - Purpose: Provides the exact Python code context for LLM code repair reasoning.
     * Stage 5 (5_populate_audio_runtime.py):
       - How: Ingests CGI_Input.json.
       - Purpose: Computes cumulative section timestamps in exact M:SS format.
     * Stage 15/17 Visual Keyframes:
       - How: Reads PNG keyframe images from vlm_inputs/ or correction_insights_vlm/
         (with direct FFmpeg extraction fallback from manim_extracted_videos/).
   - Input Tracker: ppt_trackers/18_vlm_fix_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * vlm_inputs/scene_{group}/manifest.json (Stage 17):
       Location: data_ppt_advanced/<TOPIC_NAME>/vlm_inputs/scene_{group}/manifest.json
       Content: Triangulation manifest linking grids to exact section line boundaries and visual objects.
     * vlm_inputs/scene_{group}/ (Stage 17 & 18):
       Location: data_ppt_advanced/<TOPIC_NAME>/vlm_inputs/scene_{group}/
       Content: Aesthetic reports and triangulated keyframe images.
     * manim_extracted_codes/group_{group}.py (Stage 14):
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_extracted_codes/group_*.py
       Content: Current instrumented Manim scene script.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Storyboard audio runtimes and cumulative start/end timestamps.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/18_vlm_fix_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 18_vlm_fix_tracker.json.
   - Step 2: Gathers 2 visual screenshots per section:
     * Peak/active transition frame.
     * Settled composition frame.
     * Automatically extracts keyframes via FFmpeg if snapshot images are missing.
   - Step 3: Computes exact cumulative timestamps (M:SS) from CGI_Input.json for each section.
   - Step 4: Dispatches multimodal prompt to Gemini 3.8 Flash combining:
     * The 2 screenshot images.
     * Code context from manim_extracted_codes/.
     * Cumulative M:SS section timestamp.
     * Aesthetic and geometric violation notes.
   - Step 5: The VLM emits strict timestamped physical repair directives:
     e.g., "0:40 Shift container down by 0.6 to clear header title at y=1.70"
           "1:23 Set MathTex color to C_TEXT (#404040) for contrast on white panel"
   - Step 6: Saves directives to vlm_fixing_stage/scene_{group}_timestamped_fixes.txt
     and mirrors in correction_insights/scene_{group}/.
   - Step 7: Atomically updates 19_vlm_fixing_stage_tracker.json and invalidates downstream stages
     (20_eng_corrections_tracker.json, 21_timing_adjustment_tracker.json, 22_final_render_tracker.json).

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * vlm_fixing_stage/scene_{group}_timestamped_fixes.txt:
       Location: data_ppt_advanced/<TOPIC_NAME>/vlm_fixing_stage/scene_{group}_timestamped_fixes.txt
       Content: Plaintext timestamped fixing instructions for the scene.
     * Mirrored fixing file:
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights/scene_{group}/scene_{group}_timestamped_fixes.txt
     * Output Tracker:
       Location: ppt_trackers/19_vlm_fixing_stage_tracker.json
       Content: Atomic tracker confirming completion of timestamped fix generation.

6. DOWNSTREAM CONSUMERS:
   - Stage 20 (20_final_styling_corrections.py): Applies these timestamped fixing directives
     directly into final Manim code.
================================================================================
"""

import os
import sys
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_HELPERS_DIR = os.path.join(_CURRENT_DIR, "helpers")
_ROOT_DIR = os.path.dirname(_CURRENT_DIR)
for _p in [_HELPERS_DIR, _CURRENT_DIR, _ROOT_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import json
import portalocker
import math
import argparse
from glob import glob
from collections import defaultdict
from pathlib import Path
import shutil
import subprocess
import re
import time
import sys
from dotenv import load_dotenv
load_dotenv()

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

from code_sanitizer import is_executive_topic, get_visual_archetype
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.8-flash"
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


class VLMTimestampedFixStage:
    """
    Stage 19: Generates timestamped physical fixing directives per section (0:40, 1:23, etc.)
    using 2 screenshots per section and diagnostic insights from flagged errors.
    """

    def __init__(
        self,
        input_tracker_path,
        output_tracker_path,
        google_api_key,
        claude_api_key,
        input_folder
    ):
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.google_api_key = google_api_key
        self.claude_api_key = claude_api_key
        self.input_folder = input_folder

        # Initialize output tracker file if it doesn't exist
        if not os.path.exists(self.output_tracker_path):
            tracker_dir = os.path.dirname(self.output_tracker_path)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
            with open(self.output_tracker_path, 'w', encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False)

    # ---------------------------------------------------------
    # UTILITIES & FILE I/O
    # ---------------------------------------------------------

    def _load_tracker(self, filepath):
        """Load a JSON tracker with a shared lock (read lock)."""
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                portalocker.lock(f, portalocker.LOCK_SH)
                try:
                    content = f.read()
                    if not content:
                        return {}
                    data = json.loads(content)
                except json.JSONDecodeError:
                    data = {}
                finally:
                    portalocker.unlock(f)
            return data
        except Exception as e:
            print(f"Error loading tracker {filepath}: {e}")
            return {}

    def _save_tracker(self, filepath, data):
        """Save a JSON tracker with an exclusive lock (write lock)."""
        lock_path = filepath + ".lock"
        try:
            with portalocker.Lock(lock_path, timeout=60):
                current = {}
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            current = json.load(f)
                    except Exception:
                        current = {}
                current.update(data)
                temp_file = filepath + f".tmp.{os.getpid()}"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(current, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, filepath)
        except Exception as e:
            print(f"Error saving tracker {filepath}: {e}")

    def load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _strip_fences(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text).strip()
        return text

    # ---------------------------------------------------------
    # TIMESTAMPS & ERROR INSIGHTS
    # ---------------------------------------------------------

    def compute_section_timings(self, sections_data):
        """
        Calculates cumulative elapsed time per section and formats into M:SS strings.
        Returns list of dicts with: section_id, duration, cum_time, timestamp_str
        """
        timings = []
        cum_time = 0.0
        for idx, sec in enumerate(sections_data, start=1):
            dur = float(sec.get("run_time", 0.0))
            cum_time += dur
            mins = int(cum_time // 60)
            secs = int(round(cum_time % 60))
            if secs == 60:
                mins += 1
                secs = 0
            timings.append({
                "section_id": idx,
                "duration": dur,
                "cum_time": cum_time,
                "timestamp_str": f"{mins}:{secs:02d}"
            })
        return timings

    def load_error_insights(self, base_folder, scene_number):
        """
        Loads flagged error insights from:
        1. llm_error_reports_vlm/scene_{scene_number}_full_report.json
        2. specific_suggestions_vlm/scene_{scene_number}_suggestions_consolidated.txt
        """
        insights_by_sec = defaultdict(list)
        report_file = os.path.join(base_folder, "llm_error_reports_vlm", f"scene_{scene_number}_full_report.json")
        full_report = {}
        if os.path.exists(report_file):
            try:
                full_report = self.load_json(report_file)
                for sec_key, sec_val in full_report.items():
                    sec_id = int(sec_val.get("section", sec_key))
                    for iss in sec_val.get("issues", []):
                        desc = iss.get("description") or f"Issue on objects {iss.get('objects')} ({iss.get('type')})"
                        insights_by_sec[sec_id].append(f"[{iss.get('type', 'layout_error')}] {desc}")
            except Exception as e:
                print(f"  [WARN] Failed to load full report {report_file}: {e}")

        # Also load prior consolidated suggestions for additional context
        suggestions_file = os.path.join(base_folder, "specific_suggestions_vlm", f"scene_{scene_number}_suggestions_consolidated.txt")
        prior_suggestions = ""
        if os.path.exists(suggestions_file):
            try:
                with open(suggestions_file, 'r', encoding='utf-8') as f:
                    prior_suggestions = f.read().strip()
            except Exception:
                pass

        return full_report, insights_by_sec, prior_suggestions

    # ---------------------------------------------------------
    # 2 SCREENSHOTS PER SECTION EXTRACTION
    # ---------------------------------------------------------

    def select_two_screenshots_per_section(self, base_folder, scene_number, full_report, section_timings):
        """
        Selects exactly 2 screenshots per section:
        - Screenshot 1: Action / Peak Error Frame (worst issue moment or mid-point of section animation)
        - Screenshot 2: Settled Composition Frame (final stable composition near section end)
        """
        scene_snap_dir = Path(base_folder) / "correction_insights_vlm" / f"scene_{scene_number}"
        vlm_inputs_dir = Path(base_folder) / "vlm_inputs" / f"scene_{scene_number}"

        # Discover all available snapshot frames and their timestamps
        snapshots = {}
        if scene_snap_dir.is_dir():
            for json_file in sorted(scene_snap_dir.glob("snapshot_*.json")):
                m = re.match(r"snapshot_(\d+)\.json", json_file.name)
                if not m:
                    continue
                f_num = int(m.group(1))
                png_path = scene_snap_dir / f"snapshot_{f_num:04d}.png"
                if png_path.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            s_data = json.load(f)
                        raw_ts = s_data.get("timestamp")
                        ts = float(raw_ts) if raw_ts is not None else 0.0
                        snapshots[f_num] = {
                            "frame": f_num,
                            "timestamp": ts,
                            "png_path": str(png_path)
                        }
                    except Exception:
                        pass

        # Frame selection per section
        selected_frames_by_sec = {}
        all_frame_nums = sorted(snapshots.keys())

        def _get_extent(item):
            if not isinstance(item, dict):
                return 0.0
            ext = item.get("extent")
            if ext is None:
                return 0.0
            try:
                return float(ext)
            except (ValueError, TypeError):
                return 0.0

        # If snapshots exist in correction_insights_vlm
        for sec_meta in section_timings:
            sec_id = sec_meta["section_id"]
            sec_str = str(sec_id)
            sec_report = full_report.get(sec_str, {})
            frame_range = sec_report.get("frame_range")
            issues = sec_report.get("issues", [])

            f1 = None
            f2 = None

            # Determine frame range for this section
            if frame_range and len(frame_range) == 2 and frame_range[0] is not None and frame_range[1] is not None:
                start_frame, end_frame = int(frame_range[0]), int(frame_range[1])
            else:
                # Approximate from timestamps
                t_end = sec_meta["cum_time"]
                t_start = t_end - sec_meta["duration"]
                matching_frames = [fn for fn, meta in snapshots.items() if t_start <= (meta.get("timestamp") or 0.0) <= t_end + 0.5]
                start_frame = min(matching_frames) if matching_frames else (all_frame_nums[0] if all_frame_nums else 0)
                end_frame = max(matching_frames) if matching_frames else (all_frame_nums[-1] if all_frame_nums else 0)

            # Frame 1: Peak error frame if any issue has a frame number, else ~45% action frame
            if issues:
                sorted_issues = sorted(issues, key=_get_extent, reverse=True)
                for iss in sorted_issues:
                    if isinstance(iss, dict) and iss.get("frame") is not None and iss["frame"] in snapshots:
                        f1 = iss["frame"]
                        break

            if f1 is None:
                # Mid-animation frame (~45% of section)
                mid_target = start_frame + int((end_frame - start_frame) * 0.45)
                # Find closest available frame
                f1 = min(all_frame_nums, key=lambda fn: abs(fn - mid_target)) if all_frame_nums else None

            # Frame 2: Settled composition frame near section end (end_frame - 2)
            settled_target = max(start_frame, end_frame - 2)
            f2 = min(all_frame_nums, key=lambda fn: abs(fn - settled_target)) if all_frame_nums else None

            # Ensure f1 and f2 are distinct if possible
            if f1 == f2 and end_frame > start_frame and len(all_frame_nums) > 1:
                alt_frames = [fn for fn in all_frame_nums if fn >= start_frame and fn <= end_frame and fn != f2]
                if alt_frames:
                    f1 = alt_frames[0]

            # Frame 0: Ingress frame (~22% of section) for sections with duration >= 7.0s
            f_ingress = None
            if sec_meta.get("duration", 0.0) >= 7.0 and end_frame > start_frame:
                ingress_target = start_frame + int((end_frame - start_frame) * 0.22)
                f_ingress = min(all_frame_nums, key=lambda fn: abs(fn - ingress_target)) if all_frame_nums else None
                if f_ingress in (f1, f2):
                    f_ingress = None

            # Collect image paths
            img_ingress = snapshots.get(f_ingress, {}).get("png_path") if f_ingress is not None else None
            img1 = snapshots.get(f1, {}).get("png_path") if f1 is not None else None
            img2 = snapshots.get(f2, {}).get("png_path") if f2 is not None else None

            # Fallback to vlm_inputs if snapshots are missing
            if not img1 or not img2:
                vlm_grids = sorted(vlm_inputs_dir.glob(f"sec_{sec_id}_frame_*_grid.png"))
                if len(vlm_grids) >= 2:
                    img1 = img1 or str(vlm_grids[0])
                    img2 = img2 or str(vlm_grids[-1])
                elif len(vlm_grids) == 1:
                    img1 = img1 or str(vlm_grids[0])
                    img2 = img2 or str(vlm_grids[0])

            # Direct video keyframe extraction fallback if still missing
            if not img1 or not img2:
                video_file = Path(base_folder) / "manim_extracted_videos" / f"group_{scene_number}.mp4"
                if not video_file.exists():
                    video_file = Path(base_folder) / "manim_time_synced_videos" / f"group_{scene_number}.mp4"
                if video_file.exists():
                    vlm_inputs_dir.mkdir(parents=True, exist_ok=True)
                    t_mid = max(0.5, t_start + 0.45 * sec_meta["duration"])
                    t_settled = max(0.5, t_start + 0.95 * sec_meta["duration"])
                    fb1 = vlm_inputs_dir / f"sec_{sec_id}_mid_{t_mid:.1f}s.png"
                    fb2 = vlm_inputs_dir / f"sec_{sec_id}_settled_{t_settled:.1f}s.png"
                    subprocess.run(["ffmpeg", "-y", "-ss", str(t_mid), "-i", str(video_file), "-frames:v", "1", str(fb1)], capture_output=True, check=False)
                    subprocess.run(["ffmpeg", "-y", "-ss", str(t_settled), "-i", str(video_file), "-frames:v", "1", str(fb2)], capture_output=True, check=False)
                    if fb1.exists():
                        img1 = img1 or str(fb1)
                    if fb2.exists():
                        img2 = img2 or str(fb2)

            selected_frames_by_sec[sec_id] = {
                "frame_ingress": f_ingress,
                "frame_1": f1,
                "frame_2": f2,
                "img_ingress_path": img_ingress,
                "img1_path": img1,
                "img2_path": img2,
            }

        return selected_frames_by_sec

    # ---------------------------------------------------------
    # PROMPT CONSTRUCTION & GEMINI VLM CALL
    # ---------------------------------------------------------

    def build_vlm_fix_prompt(self, scene_number, section_timings, insights_by_sec, prior_suggestions, code_content, base_folder=None, theme=None, manifest_data=None):
        """
        Builds the multimodal prompt instructing Gemini 3.8 Flash to identify layout errors
        and synthesize fixing instructions in the exact timestamped format:
          0:40 <actionable visual repair instructions...>
          1:23 <actionable visual repair instructions...>
        Dynamically adapts rules for executive presentations vs K-12, STEM math, or Promo.
        """
        archetype = get_visual_archetype(base_folder=base_folder, code_content=code_content)
        print(f"[Stage 19] Scene {scene_number} detected visual archetype: '{archetype}'")

        lines = [
            'You are an expert Visual Art Director and Manim Layout Reviewer.',
            'You are reviewing a Manim animation scene section by section to identify physical visual defects',
            'and output concrete layout, positioning, alignment, and sizing fixes.',
            '',
            'You are provided:',
            '1. SCREENSHOTS PER SECTION (in chronological sequence):',
            '   - Ingress Frame (for sections >= 7s): Captures element entrances and motion paths',
            '   - Frame A: Active / peak animation state (shows elements during motion / potential collisions)',
            '   - Frame B: Settled final composition (shows the final resting layout before section transition)',
            '2. Flagged structural & geometric error insights from automated collision detectors.',
            '3. Original Manim Python source code for variable references and mobject names.',
            '4. Cumulative section timestamps in M:SS format.',
            '',
            '==================================================',
            'SECTION TIMESTAMPS & FLAGGED ERROR INSIGHTS:',
            '=================================================='
        ]

        for s in section_timings:
            sec_id = s["section_id"]
            ts = s["timestamp_str"]
            dur = s["duration"]
            lines.append(f"\n### Section / Presentation Step {sec_id} (Timestamp: {ts}, Duration: {dur:.1f}s) ###")
            if manifest_data:
                sec_mf = manifest_data.get(str(sec_id)) or manifest_data.get(f"scene_{scene_number}", {}).get(str(sec_id), {})
                if sec_mf:
                    lines.append(f"Mapped Source Code Lines: {sec_mf.get('start_line', '?')} to {sec_mf.get('end_line', '?')}")
                    if sec_mf.get("objects"):
                        lines.append(f"Identified Python Variables: {', '.join(sec_mf['objects'])}")
            errors = insights_by_sec.get(sec_id, [])
            if errors:
                lines.append("Flagged Diagnostic Issues:")
                for err in errors:
                    lines.append(f"  - {err}")
            else:
                lines.append("Diagnostic Issues: No collision detected, but review visual balance, padding, margins, and text container fitting.")

        if prior_suggestions:
            lines.append("\n==================================================")
            lines.append("PRIOR HIGH-LEVEL ENGINEERING INSIGHTS:")
            lines.append("==================================================")
            lines.append(prior_suggestions)

        if code_content:
            lines.append("\n==================================================")
            lines.append("MANIM SOURCE CODE CONTEXT:")
            lines.append("==================================================")
            lines.append(code_content)  # provide full code context for complete variable and structure references
            lines.append("==================================================\n")

        # Select archetype-specific layout rules (Strict Prohibition of Static PPT Cards & Two-Column Splits)
        if archetype == "executive":
            rules_1_and_2 = """
1. OPEN-CANVAS DYNAMIC VECTOR & DIAGRAM AUDIT DISCIPLINE (ZERO PPT CARDS / ZERO TWO-COLUMN SPLIT):
   Audit the scene for authentic, dynamic vector mechanisms and open-canvas diagrams:
   - STRICT PROHIBITION OF TWO-COLUMN & CARD BOXES:
     * Strictly DO NOT recommend dividing the canvas into rigid [Left Column Anchor] and [Right Column Explanation Workspace] divisions!
     * Strictly DO NOT recommend encapsulating statements into stacked rectangular cards (`create_yellow_card`, `create_card`) or PowerPoint-style bullet boxes!
     * If a scene suffers from static slide cards or rectangular boxes, direct removing the container boxes and letting the living vector mechanism breathe directly in open canvas space.
   - VECTOR MECHANISMS & DYNAMIC DIAGRAMS AUDIT:
     * Check that central focal mechanisms (e.g. balance scales, neural cores, dials, flow conduits, state loops) are clearly visible, properly scaled, and centered.
     * Check spatial bounds: In Layout 70, elements must stay within x in [-0.8, 6.4], y in [-3.2, 2.2]. In full-canvas scenes, x in [-6.4, 6.4].
     * Check connectors & conduits: Conduits, arrows, and particle paths must connect cleanly to node perimeters without piercing centers or colliding with text.

2. OPEN-CANVAS SPATIAL CLEARANCE & BALANCED MARGINS:
   - Allow diagrams and visual mechanisms full breathing room across the content arena without encasing them in border boxes.
   - Enforce page-edge clearance: Neither visual mechanisms nor labels should touch outer screen edges. Maintain generous breathing room above the bottom margin (keep content strictly above DOWN * 3.3).
   - Ensure multi-element groups maintain uniform scaling and harmonic spacing.
"""
            rule_4 = """
4. DIRECT IN-DIAGRAM LABELS & STATUS INDICATORS (STRICT PROHIBITION OF CARD STACKS):
   - DIRECT ATTACHMENT: Labels and status pills (1-3 words) must attach directly to diagram nodes, conduits, and indicators, never as detached bullet-point cards.
   - MICRO-PILLS & STATUS BADGES: Use subtle micro-pills (`height=0.45`, `corner_radius=0.074`) with `#FFFFFF` or `#F8FAFC` soft fills and clean 1.5px pastel borders, attached directly to components.
   - ZERO VERTICAL CARD STACKS: Strictly NEVER direct creating vertical stacks of rectangular cards containing bulleted sentences (`VGroup(card1, card2).arrange(DOWN)`). Deliverables and summaries must be sleek vector indicators (status dials, checkmark rings, metric badges).
   - ACTIONABLE DIRECTIVES:
     * When text is floating awkwardly or colliding with an animation, formulate a concrete directive to adjust label positioning, font size, or attach it cleanly to the focal node with leader lines.
"""
        elif archetype == "stem_math":
            rules_1_and_2 = """
1. MATHEMATICAL & GEOMETRICAL SPATIAL DISCIPLINE:
   - Maximize canvas area for geometric figures and coordinate axes: Allow Axes, NumberPlane, polygons, and geometric constructions to span up to 10.0 width and 5.5 height across the screen. Do NOT cram geometric proofs into small sub-column cards.
   - Center geometric shapes (triangles, circles, coordinate graphs) prominently in the main viewport.
   - Step-by-step mathematical derivations: Stack derivation lines vertically with aligned equal signs. Ensure MathTex is font_size 18-22 with clear vertical line spacing (buff=0.25).

2. GEOMETRY LABELS, ANGLE ARCS & POINTER TOPOLOGY:
   - Position vertex labels, angle arcs, and coordinate callouts cleanly outside the shape boundaries with buff=0.25 to 0.35. Labels must NEVER overlap line strokes or shape interiors.
   - Keep all math plots and labels within safe canvas bounds: x in [-6.4, 6.4], y in [-3.3, 3.2].
"""
            rule_4 = """
4. FORMULA CARDS & THEOREM HIGHLIGHTS:
   - Theorems, key formulas, and problem statements should be enclosed in clean formula cards (e.g. create_card) with high contrast.
   - Always ensure MathTex width is clamped to card width so long derivations wrap or break across lines rather than exceeding boundaries.
"""
        else:
            rules_1_and_2 = """
1. OPEN-CANVAS DYNAMIC LEARNING VISUAL DISCIPLINE:
   - Keep elements cleanly organized with generous margins and clear visual hierarchy.
   - Spatial bounds: Stay strictly within x in [-6.4, 6.4], y in [-3.3, 3.2].
   - Strictly avoid static cards or stacked rectangular boxes; allow living vector mechanisms to breathe in open canvas negative space.
"""
            rule_4 = """
4. DIRECT IN-DIAGRAM ANNOTATIONS:
   - Attach concise labels (1-3 words) and status pills directly to focal elements.
"""

        format_spec = f"""
### TASK & INSTRUCTIONS:
You are reviewing a Manim presentation animation section by section.
Your job is to identify EVERY genuine visual defect, layout collision, clipping, or component flaw and synthesize concrete, code-level fixing directives in timestamped format.

CRITICAL REQUIREMENT - MANDATORY FUSION OF PRIOR INSIGHTS & VISUAL REASONING:
The "PRIOR HIGH-LEVEL ENGINEERING INSIGHTS" and "Flagged Diagnostic Issues" above contain verified defect discoveries from collision detectors and prior visual passes.
You MUST integrate these findings with your visual inspection of the screenshots and full Manim source code:
- Every concrete defect described in the prior suggestions (such as missing text in highlight boxes, overlapping arrowheads, branch lines piercing nodes, or elements colliding with coordinate axes/containers) MUST be explicitly addressed and translated into precise, actionable instructions in your timestamped directives.
- In addition, visually audit the screenshots against the comprehensive production standards below.

SYSTEMATIC 12-DIMENSIONAL VISUAL AUDIT (Archetype: {archetype}):
{rules_1_and_2}
3. ELIMINATE EMPTY / DEAD WHITESPACE (ACTIVE CANVAS & CONTAINER SPANNING RULE):
   - Whenever a scene, container, or side of the screen appears sparse, bare, or has excessive empty whitespace:
     * ENLARGE CONTAINERS: Expand container width and height so they comfortably span the frame and eliminate dead space between or around boxes.
     * SCALE UP INTERNAL CONTENT: Enlarge diagrams, graphs, tables, formula cards, and typography (bump text size 2–4 points) so elements fill the container with strong visual presence rather than floating as tiny, cramped islands.
     * SPANNING DISTRIBUTION: Space out child cards, bullet rows, and badges evenly across the available height and width (e.g. increase vertical buffering between cards so they span from top to bottom margin of the container).
     * BALANCED GRIDS: If multiple items exist in a spacious container, rearrange them into an even 2x2 grid or wide multi-column layout instead of leaving one side completely vacant.
     * If an illustration or table sits alone in a box, center it boldly and scale it up to occupy 70–85% of the container's interior space.
{rule_4}

5. TITLE PLACEMENT, TYPOGRAPHY & MULTI-LINE WRAPPING:
   - Section titles must be bold, legible, and placed INSIDE the container with explicit inner margin (e.g., move_to(container.get_corner(UL) + RIGHT * 0.6 + DOWN * 0.55, aligned_edge=UL)).
   - Titles must never collide with or touch the container's top-left rounded border, screen title, or decorative underline.
   - TEXT MUST NEVER TOUCH OR BLEED PAST CONTAINER BORDERS. Whenever text approaches boundary edges, instruct breaking it into two-liners or three-liners with proper line buffering.
   - STRICT NO ALL-CAPS MANDATE (TITLE CASE & SENTENCE CASE): Instruct that all on-screen titles, headings, and labels must NEVER use ALL CAPS (no "CORE PROBLEM", "TOTAL SELECTIONS", "DEFINITION"). Require converting ALL CAPS text into Title Case (Camel Case) for headings/cards/badges and Sentence case for body text.
   - Maintain unified alignment: Left-align lists, paragraph blocks, and bullet cards cleanly along a common vertical guide.
   - STRICT UNIFORM FONT SIZING ACROSS CARDS, BOXES, SHAPES & PILLS: All text inside cards, boxes, shapes, badges, and pills across the scene MUST maintain a single, strictly uniform font size (13pt–15pt). NEVER scale down text to fit a narrow box while neighbor boxes remain larger, and NEVER force text to stretch across the full width of a container. Always wrap longer text across multiple lines using '\n' or max_width and expand container height dynamically.
   - Numerical/currency conventions: Throughout videos, write large numbers such as 'crore' cleanly as 'Cr' (e.g., 'Rs. 198.34 Cr'), ensure symbols like '₹' / 'Rs.' are clear, and fix any misspelled domain keywords (e.g. ensure 'SUCCESS' has two S's).

6. MATHEMATICAL FORMULAS & LATEX TYPOGRAPHY (UNIFORM SIZING & CONTAINER-BOUNDED RULE):
   - In Manim Community, default MathTex font_size is 48, which renders equations 3x to 4x taller than normal text!
   - ALL LaTeX formatted text (MathTex, Tex) MUST nearly match the size of surrounding non-latex text (CrispText):
     * Standalone formulas & equation cards: Instruct `font_size=22` to `font_size=26` (or scale 0.45 to 0.55). NEVER instruct font_size >= 28 or scale 0.75–1.2!
     * Inline math next to labels/body text: Instruct `font_size=16` to `font_size=18` so mathematical symbols match the exact height of the adjacent text.
     * CONTAINER-BOUNDED CLAMP (MANDATORY): Formulas inside cards, left panel, or 2-column right sub-panels MUST NEVER exceed width 2.9 units! NEVER instruct scaling up an equation if it causes the formula or card to exceed width 3.3 or collide with neighbor columns.
   - For long formulas, derivations, or multi-term equations, ALWAYS instruct breaking them across multiple lines (e.g. using align or split environments) or scaling them to fit the container (.scale_to_fit_width(2.9)). NEVER instruct scaling long equations up blindly!
   - Card padding & safety: Ensure subscripts and superscripts have at least 0.15 vertical padding and never touch container strokes.

7. TABLES & STRUCTURED MATRIX CELLS:
   - STRICT UNIFORM FONT SIZES & MULTI-LINE CENTER ALIGNMENT: All cell contents and headers must maintain a single, strictly uniform base font size (13pt to 15pt). NEVER instruct or allow `.scale_to_fit_width(...)` on cell text or box text, which causes jarring uneven font sizing across cells. Longer cell text MUST be wrapped across multiple lines using '\n' with center alignment so all cells share the exact same font size.
   - CELL BACKGROUND FILLS OVER TEXT HIGHLIGHTERS: Never use sloppy text highlighter strips or BackgroundRectangles that bleed outside cells or partially cover text. Instead, apply clean full-cell background fills (e.g., solid blue, green, or light violet cells) with visible separator grid lines between rows and columns.
   - Table Sizing & White Space Maximization: Enlarge tables and their contents so they cover maximum white space across the canvas without looking cramped or compressed.
   - Ensure column titles are clear, bold, and distinct from data rows. Give equal spacing between rows.

8. ARROWS, FLOW CONNECTORS & ROUTING TOPOLOGY:
   - Arrows between horizontal or vertical steps must be clean and straight (or clean orthogonal elbows), not awkward slanting diagonals.
   - PROPORTIONAL ARROWHEADS: Arrowheads must be proportional (decrease arrowhead size whenever arrowheads look oversized, bloated, or obscure target points).
   - NO TEXT COLLISIONS: Arrows must NEVER cross or collide with text, equations, or callout cards. Direct routing arrows around obstacles with corner elbows or shifting text to clear negative space.
   - Precise Connections: Arrows must originate cleanly from the source perimeter and terminate cleanly at the target perimeter without piercing node bodies or floating disconnected.
   - If backward or returning arrows are curved, ensure the curve arcs away from neighboring branch lines rather than slicing across them.

9. DIAGRAMS, GRAPHS & SPATIAL DISTRIBUTION:
   - GRAPH AXES & FUNCTION PLOT LIFECYCLE: Always position Axes (e.g. `axes.move_to(...)` or arrange inside its parent VGroup) BEFORE evaluating `axes.plot(...)` or `axes.c2p(...)`. Plotting curves while axes are at ORIGIN causes curve points to be misaligned when axes are moved later!
   - Mandatory Step Lifecycle Fadeout: When transitioning to a new step, all plotted curves (`axes.plot(...)`), annotations, and data points MUST be explicitly included in `FadeOut(...)` (or grouped together in the container `VGroup`). Never leave orphaned curves or annotations floating on screen in later steps!
   - Never place `stretch=True` inside `VGroup(...)` (only valid on `SurroundingRectangle`).
   - Center graphs, trees, and geometric diagrams within their respective container box.
   - Coordinate Axes & Labels: Axes must be high-contrast (dark/black on light backgrounds, never white on white). All axis labels (e.g. 'Project Value (V)', 'Time') must remain completely inside container boundaries and clear of ticks and callouts.
   - Node Topology: In tree, lattice, or network diagrams, shorten branch lines to terminate cleanly at node circumferences (never piercing into circle centers). Separate converging or diverging arrowheads to prevent overlapping blobs.
   - Equal Component Spanning: Distribute child cards or steps evenly across the box height/width (e.g., 2x2 grid or evenly spaced vertical stack) so elements do not bunch up at the top or leave dead space at the bottom.

10. HIGHLIGHT CARDS, CALLOUT BOXES & CONTRAST:
    - Replace raw text highlighter strips with elegant, rounded pill/card containers or BackgroundRectangles that fully enclose the text with uniform padding.
    - REDUCE GREEN USAGE AS MUCH AS POSSIBLE: Green (#34A853 / #2D6A4F) must be minimized across all scenes. Never instruct styling cards, containers, panels, or nodes in green. Direct using the approved 10-color infographic palette (Sky Blue #62B7E4, Steel Blue #7EA2C8, Lavender #9B99C7, Mint #8ECDB7, Warm Amber #E6A157, etc.).
    - High Contrast: Never use light font on light backgrounds. Ensure high-contrast dark charcoal (#404040) text on light cards/canvas and white text on dark containers.
    - APPROVED HIGHLIGHT SPECIFICATION (guidelines.md Section 3.3 & 6.4): Focus highlights must use vibrant orange (#F78908) with 3px stroke (stroke_width=3) and 1.0s draw time. Only ONE highlight at a time.
    - Z-Ordering / Visibility: Bundle text mobjects together with their BackgroundRectangle in a VGroup so text renders visibly on top with high contrast and never disappears behind opaque cards.

11. TEMPORAL LIFECYCLE & TRANSITION CLEANSING:
    - NO FLASH APPEARANCES: Elements must never appear for a fraction of a second (<1s) and vanish abruptly. Ensure visual objects remain visible for sufficient duration (at least 2–3s) in sync with narration.
    - STEP TRANSITION CLEANSING: When Step N ends, all temporary elements from that step (lists, diagrams, callouts, arrows, highlight rectangles) must explicitly fade out before Step N+1 enters to prevent multi-step overlapping text and ghost clutter.
    - SCENE END GRACE PERIOD: The scene must not abruptly terminate the instant the final element enters. Keep final conclusions, summary cards, and results visible for at least 1.5–2 seconds before the scene ends.
    - Opacity & Dimming: Do not allow key diagrams, graphs, or formula cards to become excessively faded, translucent, or dimmed while narration is referencing them.

12. CONCRETE, CODE-LEVEL ACTIONABILITY & NO MANIM SCALING TRAPS:
    - Formulate every fix as a concrete directive mentioning specific Manim object names, coordinate shifts (e.g., UP * 0.4, RIGHT * 0.6), scale adjustments, wrapping, or VGroup bundling.
    - NEVER instruct chaining .set_width(w).set_height(h) because Manim rescales aspect ratio proportionally on .set_height(), destroying width. Instruct setting constructor parameters RoundedRectangle(width=w, height=h, corner_radius=r) or using .stretch_to_fit_width(w).stretch_to_fit_height(h).
    - Avoid vague generalities like "improve layout". State exactly what to shift, scale, wrap, color, or fade out.

13. ZERO OVERFLOW, PERSISTENT TITLES, EXACT DELTAS & BOUNDARY CLAMPING:
    - EXACT NUMERIC COORDINATES: For every repositioning or resize directive, state the exact numeric coordinate or delta (e.g. "shift left by dx = -0.8 to target x = 5.6", "clamp card width to 3.4", "set card height to max(1.8, content.height + 0.5)"). Avoid vague qualitative phrases like "slightly shift" or "make smaller".
    - PERSISTENT MAIN TITLE (SAFE MARGINS & SHORT DIVIDER): The main slide title must sit at top-left safe zone (`UL, buff=0.42`, clamped to width <= 6.4) with its accent divider line extending only 2.0 units to the right of dots (never beyond x = -3.5). It must remain static across all steps. Never instruct FadeOut(title) followed by FadeIn(new_title) in a multi-step scene.
    - NO RIGID 5-TIER SANDWICH / BANNER CROWDING:
      * DO NOT force separate premise banners or takeaway banners when central visual models, diagrams, or cards are present!
      * Dedicate the central arena (y in [-3.2, 2.7]) entirely to the primary diagram, flowchart, or comparison cards so elements never overlap or collide.
      * If a premise or framing question is helpful, attach it as a clean subtitle under title_group (`create_title(title, subtitle)`), never as a massive 11-unit wide banner blocking the diagram!
    - ZERO MINIATURE SCALED BLOBS: When transitioning steps, completely fade out previous diagrams (`FadeOut(...)`). NEVER instruct shrinking complex diagrams into miniature illegible blobs (`.scale(0.20)`).
    - CONTAINER PURGE ON STEP TRANSITION: When Step N+1 introduces new content in a container (e.g., left_container), instruct explicitly removing or fading out all prior headings, text, or cards from Step N so text does not draw directly on top of old text.
    - SCREEN BOUNDARY CLAMPING: In a 16:9 canvas (visible width 14.22), elements must stay strictly within x in [-6.4, 6.4] and y in [-3.3, 3.2].
    - DYNAMIC CARD SIZING: Cards must size dynamically based on their content: `height = max(min_height, content.height + 2 * pad_y)`. Product card images must be clamped to height <= 1.25 so title and price never spill over card bottom borders.
    - CALLOUT & ARROW PLACEMENT: Callouts pointing to cards must sit strictly ABOVE the card (`next_to(card, UP, buff=0.25)`) or clearly outside, never aligned to arrows in a way that causes text to overlap the card graphic.
    - STRICT UNIFORM FONT SIZING & LINE WRAPPING MANDATE: Text inside cards, boxes, shapes, or cells must maintain uniform font size (13pt–15pt). When text overflows container boundaries or is longer than neighbor cards, NEVER shrink font size or force text to stretch across the full width of a container. Instruct inserting explicit '\\n' line breaks or max_width wrapping and dynamically expanding container height, so all sibling cards/boxes display text at the exact same font size.

14. CRITICAL VISUAL DEFECT PURGES & ZERO-TOLERANCE CODE DEFECTS:
    - MISSING FONT GLYPH BOX INSPECTION (27 13 DEFECT):
      Inspect screenshots carefully for tiny stacked rectangular fallback boxes with numbers (such as '27 13' or empty squares) appearing beside or inside text. These are broken unicode checkmarks ('\\u2713') caused by missing glyph fonts on Windows Manim renderers. Whenever a checkmark or crossmark is needed, EXPLICITLY DIRECT replacing raw unicode with vector shapes: `create_checkmark(color='#107C41', size=0.35)` and `create_crossmark(color='#C5221F', size=0.35)`.
    - STEP-BOUNDARY CLUTTER PURGE & LIFECYCLE FADEOUTS:
      When moving from one presentation step to the next, instruct EXPLICIT, NAMED `FadeOut` calls for ALL previous step mobjects, diagrams, arrows, and tags: e.g. `self.play(FadeOut(bad), FadeOut(good), FadeOut(upd), FadeOut(esc), run_time=0.5)`. NEVER leave old step diagrams, cards, or annotations floating under new elements!
    - SINGLE HEADER AUTHORITY & SEQUENTIAL TITLE CROSSFADES:
      Never render duplicate slide headers. Main slide titles must remain persistent or update cleanly. Do NOT allow `ReplacementTransform(title_group, new_title_group)` or simultaneous `FadeOut` and `FadeIn` in the same animation call because they create ghost double-exposure text. Direct clean sequential transitions: `self.play(FadeOut(title_group), run_time=0.3)` followed by `self.play(FadeIn(new_title_group), run_time=0.4)`.
    - STRICT BRAND COLOR CONSTRAINTS:
      Never style cards, panels, containers, or nodes in green (#34A853 / #2D6A4F). Focus highlights must strictly use vibrant orange (#F78908) with 3px stroke and 1.0s draw time. All text must be Title Case or Sentence Case—strictly ZERO ALL-CAPS.

### OUTPUT FORMAT:
Output MUST be formatted as timestamped directives.
For each section, start with the section's cumulative timestamp in M:SS format (e.g. 0:25, 0:50, 1:15), followed by the complete instruction paragraph detailing the required visual and layout repairs.
Separate each timestamp entry with a blank line.
Do NOT use markdown headers, bold prefixes (like **0:30**), bullet symbols (* or -), or code fences.
Output plain text only.

Format Structure:
M:SS <Imperative, actionable instructions describing the visual adjustments, repositioning, element sizing, cleanup, and styling fixes required for this section.>

M:SS <Imperative, actionable instructions describing the visual adjustments, repositioning, element sizing, cleanup, and styling fixes required for this section.>
"""
        format_spec_dynamic = """
### TASK & INSTRUCTIONS:
You are reviewing a Manim presentation animation section by section.
Your job is to identify EVERY genuine visual defect, layout collision, clipping, or component flaw and synthesize concrete, code-level fixing directives in timestamped format.

CRITICAL REQUIREMENT - MANDATORY FUSION OF PRIOR INSIGHTS & VISUAL REASONING:
The "PRIOR HIGH-LEVEL ENGINEERING INSIGHTS" and "Flagged Diagnostic Issues" above contain verified defect discoveries from collision detectors and prior visual passes.
You MUST integrate these findings with your visual inspection of the screenshots and full Manim source code:
- Every concrete defect described in the prior suggestions (such as missing text in highlight boxes, overlapping arrowheads, branch lines piercing nodes, or elements colliding with coordinate axes/containers) MUST be explicitly addressed and translated into precise, actionable instructions in your timestamped directives.
- In addition, visually audit the screenshots against the comprehensive 8-dimensional production standards below.

SYSTEMATIC 11-DIMENSIONAL VISUAL AUDIT:

1. ELIMINATE EMPTY / DEAD WHITESPACE (ACTIVE CANVAS & CONTAINER SPANNING RULE):
   - Whenever a scene, container, or side of the screen appears sparse, bare, or has excessive empty whitespace:
     * ENLARGE CONTAINERS: Expand container width and height so they comfortably span the frame and eliminate dead space between or around boxes.
     * SCALE UP INTERNAL CONTENT: Enlarge diagrams, graphs, tables, formula cards, and typography (bump text size 2–4 points) so elements fill the container with strong visual presence rather than floating as tiny, cramped islands.
     * SPANNING DISTRIBUTION: Space out child cards, bullet rows, and badges evenly across the available height and width (e.g. increase vertical buffering between cards so they span from top to bottom margin of the container).
     * BALANCED GRIDS: If multiple items exist in a spacious container, rearrange them into an even 2x2 grid or wide multi-column layout instead of leaving one side completely vacant.
     * If an illustration or table sits alone in a box, center it boldly and scale it up to occupy 70–85% of the container's interior space.

2. RECOMMENDED STATEMENT ENCAPSULATION & SUB-PANEL CARDS (EXECUTIVE POLISH GUIDELINES):
   - RECOMMENDATION, NOT RIGID MANDATE: Encapsulating statements into sub-panel cards is a powerful polish technique for lists, parameters, comparison rows, and key takeaways. Use your visual intelligence to decide when encapsulation enhances clarity versus when an open, mathematical, or diagram-first presentation is more natural.
   - DEDICATED SUB-PANELS / CARDS: When appropriate, encapsulate statements, parameter rows, or bullet items into rounded sub-panel cards (e.g. `create_yellow_card`, `create_colored_card`, or `create_card` with width 3.2–3.3 [max 3.3 for left panel and 2-column workspaces], height ~0.52–0.90, corner_radius ~0.10–0.14, and internal horizontal padding 0.18–0.25).
   - VISUAL HIERARCHY & BADGES:
     * Inside each sub-panel, use bold lead-in tags (e.g., 'Input: ', 'Source: ', 'Logic: ', 'Strategy: ') with high contrast against the card background.
     * Integrate semantic status badges: Green check badges (`check_badge`) for optimal choices, red cross badges (`cross_badge`) for limitations, or colored pills for variables where helpful.
   - VERTICAL CARD STACKS:
     * Group statement cards into a vertical stack: `VGroup(card1, card2, card3).arrange(DOWN, buff=0.12–0.18)`, positioned neatly under the panel heading, and set `z_index=5` so cards render crisply above container backgrounds.
     * Buffer and span the cards so they fill the container height gracefully and eliminate vacant voids.
   - EXPLICIT ACTIONABLE DIRECTIVE REQUIREMENT:
     * Whenever a section has naked, scattered text lines that make the layout look unfinished, formulate a concrete directive recommending card encapsulation:
       e.g.: "Subgroup each statement into its own dedicated card container (width 3.3, height 0.65, corner_radius 0.12) with [yellow/white/accent] fill and 0.2 horizontal padding. Stack the cards vertically with buff=0.15 and z_index=5 so each point is encapsulated in a distinct sub-panel, replacing raw floating text."

3. TITLE PLACEMENT, TYPOGRAPHY & MULTI-LINE WRAPPING:
   - Section titles must be bold, legible, and placed INSIDE the container with explicit inner margin (e.g., move_to(container.get_corner(UL) + RIGHT * 0.6 + DOWN * 0.55, aligned_edge=UL)).
   - Titles must never collide with or touch the container's top-left rounded border, screen title, or decorative underline.
   - TEXT MUST NEVER TOUCH OR BLEED PAST CONTAINER BORDERS. Whenever text approaches boundary edges, instruct breaking it into two-liners or three-liners with proper line buffering.
   - STRICT NO ALL-CAPS MANDATE (TITLE CASE & SENTENCE CASE): Instruct that all on-screen titles, headings, and labels must NEVER use ALL CAPS (no "CORE PROBLEM", "TOTAL SELECTIONS", "DEFINITION"). Require converting ALL CAPS text into Title Case (Camel Case) for headings/cards/badges and Sentence case for body text.
   - Maintain unified alignment: Left-align lists, paragraph blocks, and bullet cards cleanly along a common vertical guide.
   - STRICT UNIFORM FONT SIZING ACROSS CARDS, BOXES, SHAPES & PILLS: All text inside cards, boxes, shapes, badges, and pills across the scene MUST maintain a single, strictly uniform font size (13pt–15pt). NEVER scale down text to fit a narrow box while neighbor boxes remain larger, and NEVER force text to stretch across the full width of a container. Always wrap longer text across multiple lines using '\n' or max_width and expand container height dynamically.
   - Numerical/currency conventions: Throughout videos, write large numbers such as 'crore' cleanly as 'Cr' (e.g., 'Rs. 198.34 Cr'), ensure symbols like '₹' / 'Rs.' are clear, and fix any misspelled domain keywords (e.g. ensure 'SUCCESS' has two S's).

4. MATHEMATICAL FORMULAS & LATEX TYPOGRAPHY (UNIFORM SIZING & CONTAINER-BOUNDED RULE):
   - In Manim Community, default MathTex font_size is 48, which renders equations 3x to 4x taller than normal text!
   - ALL LaTeX formatted text (MathTex, Tex) MUST nearly match the size of surrounding non-latex text (CrispText):
     * Standalone formulas & equation cards: Instruct `font_size=22` to `font_size=26` (or scale 0.45 to 0.55). NEVER instruct font_size >= 28 or scale 0.75–1.2!
     * Inline math next to labels/body text: Instruct `font_size=16` to `font_size=18` so mathematical symbols match the exact height of the adjacent text.
     * CONTAINER-BOUNDED CLAMP (MANDATORY): Formulas inside cards, left panel, or 2-column right sub-panels MUST NEVER exceed width 2.9 units! NEVER instruct scaling up an equation if it causes the formula or card to exceed width 3.3 or collide with neighbor columns.
   - For long formulas, derivations, or multi-term equations, ALWAYS instruct breaking them across multiple lines (e.g. using align or split environments) or scaling them to fit the container (.scale_to_fit_width(2.9)). NEVER instruct scaling long equations up blindly!
   - Card padding & safety: Ensure subscripts and superscripts have at least 0.15 vertical padding and never touch container strokes.

5. TABLES & STRUCTURED MATRIX CELLS:
   - STRICT UNIFORM FONT SIZES & MULTI-LINE CENTER ALIGNMENT: All cell contents and headers must maintain a single, strictly uniform base font size (13pt to 15pt). NEVER instruct or allow `.scale_to_fit_width(...)` on cell text or box text, which causes jarring uneven font sizing across cells. Longer cell text MUST be wrapped across multiple lines using '\n' with center alignment so all cells share the exact same font size.
   - CELL BACKGROUND FILLS OVER TEXT HIGHLIGHTERS: Never use sloppy text highlighter strips or BackgroundRectangles that bleed outside cells or partially cover text. Instead, apply clean full-cell background fills (e.g., solid blue, green, or light violet cells) with visible separator grid lines between rows and columns.
   - Table Sizing & White Space Maximization: Enlarge tables and their contents so they cover maximum white space across the canvas without looking cramped or compressed.
   - Ensure column titles are clear, bold, and distinct from data rows. Give equal spacing between rows.

6. ARROWS, FLOW CONNECTORS & ROUTING TOPOLOGY:
   - Arrows between horizontal or vertical steps must be clean and straight (or clean orthogonal elbows), not awkward slanting diagonals.
   - PROPORTIONAL ARROWHEADS: Arrowheads must be proportional (decrease arrowhead size whenever arrowheads look oversized, bloated, or obscure target points).
   - NO TEXT COLLISIONS: Arrows must NEVER cross or collide with text, equations, or callout cards. Direct routing arrows around obstacles with corner elbows or shifting text to clear negative space.
   - Precise Connections: Arrows must originate cleanly from the source perimeter and terminate cleanly at the target perimeter without piercing node bodies or floating disconnected.
   - If backward or returning arrows are curved, ensure the curve arcs away from neighboring branch lines rather than slicing across them.

7. DIAGRAMS, GRAPHS & SPATIAL DISTRIBUTION:
   - GRAPH AXES & FUNCTION PLOT LIFECYCLE: Always position Axes (e.g. `axes.move_to(...)` or arrange inside its parent VGroup) BEFORE evaluating `axes.plot(...)` or `axes.c2p(...)`. Plotting curves while axes are at ORIGIN causes curve points to be misaligned when axes are moved later!
   - Mandatory Step Lifecycle Fadeout: When transitioning to a new step, all plotted curves (`axes.plot(...)`), annotations, and data points MUST be explicitly included in `FadeOut(...)` (or grouped together in the container `VGroup`). Never leave orphaned curves or annotations floating on screen in later steps!
   - Never place `stretch=True` inside `VGroup(...)` (only valid on `SurroundingRectangle`).
   - Center graphs, trees, and geometric diagrams within their respective container box.
   - Coordinate Axes & Labels: Axes must be high-contrast (dark/black on light backgrounds, never white on white). All axis labels (e.g. 'Project Value (V)', 'Time') must remain completely inside container boundaries and clear of ticks and callouts.
   - Node Topology: In tree, lattice, or network diagrams, shorten branch lines to terminate cleanly at node circumferences (never piercing into circle centers). Separate converging or diverging arrowheads to prevent overlapping blobs.
   - Equal Component Spanning: Distribute child cards or steps evenly across the box height/width (e.g., 2x2 grid or evenly spaced vertical stack) so elements do not bunch up at the top or leave dead space at the bottom.

8. HIGHLIGHT CARDS, CALLOUT BOXES & CONTRAST:
    - Replace raw text highlighter strips with elegant, rounded pill/card containers or BackgroundRectangles that fully enclose the text with uniform padding.
    - REDUCE GREEN USAGE AS MUCH AS POSSIBLE: Green (#34A853 / #2D6A4F) must be minimized across all scenes. Never instruct styling cards, containers, panels, or nodes in green. Direct using the approved 10-color infographic palette (Sky Blue #62B7E4, Steel Blue #7EA2C8, Lavender #9B99C7, Mint #8ECDB7, Warm Amber #E6A157, etc.).
    - High Contrast: Never use light font on light backgrounds. Ensure high-contrast dark charcoal (#404040) text on light cards/canvas and white text on dark containers.
    - APPROVED HIGHLIGHT SPECIFICATION (guidelines.md Section 3.3 & 6.4): Focus highlights must use vibrant orange (#F78908) with 3px stroke (stroke_width=3) and 1.0s draw time. Only ONE highlight at a time.
    - Z-Ordering / Visibility: Bundle text mobjects together with their BackgroundRectangle in a VGroup so text renders visibly on top with high contrast and never disappears behind opaque cards.

9. TEMPORAL LIFECYCLE & TRANSITION CLEANSING:
    - NO FLASH APPEARANCES: Elements must never appear for a fraction of a second (<1s) and vanish abruptly. Ensure visual objects remain visible for sufficient duration (at least 2–3s) in sync with narration.
    - STEP TRANSITION CLEANSING: When Step N ends, all temporary elements from that step (lists, diagrams, callouts, arrows, highlight rectangles) must explicitly fade out before Step N+1 enters to prevent multi-step overlapping text and ghost clutter.
    - SCENE END GRACE PERIOD: The scene must not abruptly terminate the instant the final element enters. Keep final conclusions, summary cards, and results visible for at least 1.5–2 seconds before the scene ends.
    - Opacity & Dimming: Do not allow key diagrams, graphs, or formula cards to become excessively faded, translucent, or dimmed while narration is referencing them.

10. CONCRETE, CODE-LEVEL ACTIONABILITY & NO MANIM SCALING TRAPS:
    - Formulate every fix as a concrete directive mentioning specific Manim object names, coordinate shifts (e.g., UP * 0.4, RIGHT * 0.6), scale adjustments, wrapping, or VGroup bundling.
    - NEVER instruct chaining .set_width(w).set_height(h) because Manim rescales aspect ratio proportionally on .set_height(), destroying width. Instruct setting constructor parameters RoundedRectangle(width=w, height=h, corner_radius=r) or using .stretch_to_fit_width(w).stretch_to_fit_height(h).
    - Avoid vague generalities like "improve layout". State exactly what to shift, scale, wrap, color, or fade out.

11. ZERO OVERFLOW, PERSISTENT TITLES, EXACT DELTAS & BOUNDARY CLAMPING:
    - EXACT NUMERIC COORDINATES: For every repositioning or resize directive, state the exact numeric coordinate or delta (e.g. "shift left by dx = -0.8 to target x = 5.6", "clamp card width to 3.4", "set card height to max(1.8, content.height + 0.5)"). Avoid vague qualitative phrases like "slightly shift" or "make smaller".
    - PERSISTENT MAIN TITLE (NO CROSSFADE GHOSTING): The main slide title at UP * 3.3 must remain static across all steps. Never instruct FadeOut(title) followed by FadeIn(new_title) in a multi-step scene—it creates blurry double-exposure ghost text. Step sub-topics must only update the section subtitle inside the container below y = 2.2.
    - CONTAINER PURGE ON STEP TRANSITION: When Step N+1 introduces new content in a container (e.g., left_container), instruct explicitly removing or fading out all prior headings, text, or cards from Step N so text does not draw directly on top of old text.
    - SCREEN BOUNDARY CLAMPING: In a 16:9 canvas (visible width 14.22), elements must stay strictly within x in [-6.4, 6.4]. Never place pills, callouts, or tags to the right of an already wide storefront or container (e.g. next_to(storefront, RIGHT)) as they will be clipped by the camera edge.
    - DYNAMIC CARD SIZING: Cards must size dynamically based on their content: height = max(min_height, content.height + 2 * pad_y). Product card images must be clamped to height <= 1.25 so title and price never spill over card bottom borders.
    - CALLOUT & ARROW PLACEMENT: Callouts pointing to cards must sit strictly ABOVE the card (next_to(card, UP, buff=0.25)) or clearly outside, never aligned to arrows in a way that causes text to overlap the card graphic.
    - STRICT UNIFORM FONT SIZING & LINE WRAPPING MANDATE: Text inside cards, boxes, shapes, or cells must maintain uniform font size (13pt–15pt). When text overflows container boundaries or is longer than neighbor cards, NEVER shrink font size or force text to stretch across the full width of a container. Instruct inserting explicit '\\n' line breaks or max_width wrapping and dynamically expanding container height, so all sibling cards/boxes display text at the exact same font size.

12. CRITICAL VISUAL DEFECT PURGES & ZERO-TOLERANCE CODE DEFECTS:
    - MISSING FONT GLYPH BOX INSPECTION (27 13 DEFECT):
      Inspect screenshots carefully for tiny stacked rectangular fallback boxes with numbers (such as '27 13' or empty squares) appearing beside or inside text. These are broken unicode checkmarks ('\\u2713') caused by missing glyph fonts on Windows Manim renderers. Whenever a checkmark or crossmark is needed, EXPLICITLY DIRECT replacing raw unicode with vector shapes: `create_checkmark(color='#107C41', size=0.35)` and `create_crossmark(color='#C5221F', size=0.35)`.
    - STEP-BOUNDARY CLUTTER PURGE & LIFECYCLE FADEOUTS:
      When moving from one presentation step to the next, instruct EXPLICIT, NAMED `FadeOut` calls for ALL previous step mobjects, diagrams, arrows, and tags: e.g. `self.play(FadeOut(bad), FadeOut(good), FadeOut(upd), FadeOut(esc), run_time=0.5)`. NEVER leave old step diagrams, cards, or annotations floating under new elements!
    - SINGLE HEADER AUTHORITY & SEQUENTIAL TITLE CROSSFADES:
      Never render duplicate slide headers. Main slide titles must remain persistent or update cleanly. Do NOT allow `ReplacementTransform(title_group, new_title_group)` or simultaneous `FadeOut` and `FadeIn` in the same animation call because they create ghost double-exposure text. Direct clean sequential transitions: `self.play(FadeOut(title_group), run_time=0.3)` followed by `self.play(FadeIn(new_title_group), run_time=0.4)`.
    - STRICT BRAND COLOR CONSTRAINTS:
      Never style cards, panels, containers, or nodes in green (#34A853 / #2D6A4F). Focus highlights must strictly use vibrant orange (#F78908) with 3px stroke and 1.0s draw time. All text must be Title Case or Sentence Case—strictly ZERO ALL-CAPS.

### OUTPUT FORMAT:
Output MUST be formatted as timestamped directives.
For each section, start with the section's cumulative timestamp in M:SS format (e.g. 0:25, 0:50, 1:15), followed by the complete instruction paragraph detailing the required visual and layout repairs.
Separate each timestamp entry with a blank line.
Do NOT use markdown headers, bold prefixes (like **0:30**), bullet symbols (* or -), or code fences.
Output plain text only.

Format Structure:
M:SS <Imperative, actionable instructions describing the visual adjustments, repositioning, element sizing, cleanup, and styling fixes required for this section.>

M:SS <Imperative, actionable instructions describing the visual adjustments, repositioning, element sizing, cleanup, and styling fixes required for this section.>
"""
        if theme == "dynamic_learning":
            lines.append(format_spec_dynamic)
        else:
            lines.append(format_spec)
        return "\n".join(lines)

    def call_gemini_vlm(self, prompt_text, image_paths, model=MODEL_NAME):
        """Calls Gemini Multimodal using google.genai Client."""
        client = genai.Client(api_key=self.google_api_key)
        contents = [prompt_text]

        valid_images = [p for p in image_paths if p and os.path.exists(p)]
        for p in valid_images:
            try:
                contents.append(types.Part.from_bytes(data=Path(p).read_bytes(), mime_type="image/png"))
            except Exception as e:
                print(f"  [WARN] Failed to load image {p}: {e}")

        print(f"  [VLM Call] Sending {len(valid_images)} images to {model} ...")

        last_err = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                        max_output_tokens=8000,
                    )
                )
                text = response.text or ""
                return self._strip_fences(text)
            except Exception as e:
                last_err = e
                print(f"  [WARN] Gemini VLM call failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        raise RuntimeError(f"Gemini VLM call failed after {MAX_RETRIES} attempts: {last_err}")

    # ---------------------------------------------------------
    # DIRECTIVE VALIDATION & SANITIZATION
    # ---------------------------------------------------------

    def validate_and_sanitize_directives(self, vlm_output: str, section_timings: list, code_content: str = "") -> str:
        """
        Parses, normalizes, and sanitizes VLM timestamped fix output to ensure 100% adherence to
        the 'M:SS <directive>' contract and strictly purge hallucinations or brand violations.
        """
        if not vlm_output:
            return ""

        # 1. Strip markdown fences or preambles
        clean_text = self._strip_fences(vlm_output).strip()

        # 2. Extract timestamped directives using regex
        # Matches timestamps formatted as M:SS or MM:SS
        ts_pattern = re.compile(r'(?:^|\n)\s*(?:\*\*)?(\d+:\d{2})(?:\*\*)?\s*[:\-–]?\s*(.*?)(?=(?:\n\s*(?:\*\*)?\d+:\d{2}(?:\*\*)?\b)|\Z)', re.DOTALL)
        matches = ts_pattern.findall(clean_text)

        parsed_directives = {}
        for ts, body in matches:
            clean_body = re.sub(r'[\r\t]', ' ', body)
            clean_body = re.sub(r'^\s*[-*#]+\s*', '', clean_body, flags=re.MULTILINE)
            clean_body = ' '.join(clean_body.split())
            if clean_body:
                parsed_directives[ts] = clean_body

        # 3. Sanitize content for critical brand rules and Manim anti-patterns
        sanitized_directives = {}
        for ts, body in parsed_directives.items():
            s_body = body
            # Brand Rule: Eliminate green card/container/panel recommendations
            s_body = re.sub(r'\b(green\s+(?:card|container|box|panel|background|sub-panel))\b', 'subtle pastel card (#62B7E4 or #E6A157)', s_body, flags=re.IGNORECASE)
            s_body = re.sub(r'#34A853|#2D6A4F', '#62B7E4', s_body)
            # Anti-Defect: Convert raw unicode checkmarks to vector constructor instructions
            s_body = re.sub(r"['\"]?[✓✔\u2713\u2714]['\"]?", "vector checkmark (create_checkmark)", s_body)
            s_body = re.sub(r"['\"]?[✗✘\u2717\u2718]['\"]?", "vector crossmark (create_crossmark)", s_body)
            # Anti-Defect: Replace ReplacementTransform suggestions with sequential FadeOut then FadeIn
            s_body = re.sub(r'ReplacementTransform\s*\(([^,]+),\s*([^)]+)\)', r'sequential FadeOut(\1) followed by FadeIn(\2)', s_body)
            # Anti-Defect: Ensure focus highlight instructions specify vibrant orange #F78908
            s_body = re.sub(r'\bfocus\s+highlight\b(?!\s+(?:with\s+)?(?:#F78908|orange))', 'focus highlight with vibrant orange #F78908', s_body, flags=re.IGNORECASE)
            sanitized_directives[ts] = s_body

        # 4. Guarantee complete section coverage
        final_directives = []
        for s in section_timings:
            ts = s["timestamp_str"]
            sec_id = s.get("section_id", 1)
            dur = s.get("duration", 0.0)
            if ts in sanitized_directives:
                directive_text = sanitized_directives[ts]
            else:
                directive_text = (
                    f"Audit Step {sec_id} (duration {dur:.1f}s) for visual balance and container margin clearance. "
                    f"Ensure all temporary diagrams, labels, and callout arrows from prior steps are explicitly faded out. "
                    f"Clamp all cards and text within screen boundaries (x in [-6.4, 6.4], y in [-3.3, 1.7]) with uniform "
                    f"typography and no green containers."
                )
            final_directives.append(f"{ts} {directive_text}")

        # If any extra timestamps exist, preserve them
        known_ts = {s["timestamp_str"] for s in section_timings}
        for ts, body in sanitized_directives.items():
            if ts not in known_ts:
                final_directives.append(f"{ts} {body}")

        return "\n\n".join(final_directives) + "\n"

    # ---------------------------------------------------------
    # MAIN SCENE PROCESSING
    # ---------------------------------------------------------

    def generate_scene_timestamped_fixes(self, base_folder, scene_number, cgi_data, force=False):
        """Processes a single scene group and generates timestamped fixes file."""
        output_dir = Path(base_folder) / "vlm_fixing_stage"
        output_dir.mkdir(parents=True, exist_ok=True)
        mirror_dir = Path(base_folder) / "specific_suggestions_vlm"
        mirror_dir.mkdir(parents=True, exist_ok=True)

        target_file = output_dir / f"scene_{scene_number}_timestamped_fixes.txt"
        mirror_file = mirror_dir / f"scene_{scene_number}_timestamped_fixes.txt"

        if target_file.exists() and not force and target_file.stat().st_size > 0:
            print(f"  [Info] Timestamped fixes already exist for scene {scene_number}. Skipping.")
            return str(output_dir)

        if str(scene_number).strip() in ("1", "2", "9") or str(scene_number).strip() == str(len(cgi_data)):
            print(f"  [Info] Scene {scene_number} is an official Simplilearn template. Emitting template pass-through.")
            template_notice = f"0:00 Scene {scene_number} uses the official Simplilearn template. Maintain existing layout and timing structure without modification.\n"
            target_file.write_text(template_notice, encoding="utf-8")
            mirror_file.write_text(template_notice, encoding="utf-8")
            return str(output_dir)

        # 1. Compute section timings
        group_sections = cgi_data.get(str(scene_number), [])
        if not group_sections:
            print(f"  [WARN] No sections found in CGI_Input for scene {scene_number}")
            return str(output_dir)

        section_timings = self.compute_section_timings(group_sections)

        # 2. Load error insights
        full_report, insights_by_sec, prior_suggestions = self.load_error_insights(base_folder, scene_number)

        # 3. Select 2-3 screenshots per section (ingress for >=7s, peak motion f1, settled f2)
        frames_dict = self.select_two_screenshots_per_section(base_folder, scene_number, full_report, section_timings)

        # Flatten image list in order (ingress frame if any, frame 1, frame 2 for each section)
        ordered_images = []
        for s in section_timings:
            sec_id = s["section_id"]
            sec_frames = frames_dict.get(sec_id, {})
            if sec_frames.get("img_ingress_path"):
                ordered_images.append(sec_frames["img_ingress_path"])
            if sec_frames.get("img1_path"):
                ordered_images.append(sec_frames["img1_path"])
            if sec_frames.get("img2_path") and sec_frames["img2_path"] not in (sec_frames.get("img1_path"), sec_frames.get("img_ingress_path")):
                ordered_images.append(sec_frames["img2_path"])

        # 4. Load scene source code
        code_file = Path(base_folder) / "manim_extracted_codes" / f"group_{scene_number}.py"
        if not code_file.exists():
            code_file = Path(base_folder) / "manim_codes" / f"group_{scene_number}.py"
        code_content = ""
        if code_file.exists():
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    code_content = f.read()
            except Exception:
                pass

        # 5. Load Set-of-Marks manifest bindings if available
        manifest_data = None
        manifest_file = Path(base_folder) / "vlm_inputs" / f"scene_{scene_number}" / "manifest.json"
        if not manifest_file.exists():
            manifest_file = Path(base_folder) / "vlm_inputs" / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as mf:
                    manifest_data = json.load(mf)
            except Exception as e:
                print(f"  [WARN] Failed to load manifest {manifest_file}: {e}")

        config_file = Path(base_folder) / "ex_config.json"
        theme = "dynamic_learning"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    theme = config_data.get("theme", "dynamic_learning")
            except Exception:
                pass

        prompt = self.build_vlm_fix_prompt(scene_number, section_timings, insights_by_sec, prior_suggestions, code_content, base_folder=base_folder, theme=theme, manifest_data=manifest_data)
        vlm_output = self.call_gemini_vlm(prompt, ordered_images, model=MODEL_NAME)

        # 6. Validate, sanitize, and save outputs
        vlm_output_clean = self.validate_and_sanitize_directives(vlm_output, section_timings, code_content=code_content)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(vlm_output_clean)
        with open(mirror_file, 'w', encoding='utf-8') as f:
            f.write(vlm_output_clean)

        # Invalidate downstream files for this scene
        downstream_paths = [
            os.path.join(base_folder, "manim_styled_codes", f"group_{scene_number}.py"),
            os.path.join(base_folder, "manim_time_synced_code", f"group_{scene_number}.py"),
            os.path.join(base_folder, "manim_time_synced_videos", f"group_{scene_number}.mp4"),
            os.path.join(base_folder, "audio_integrated_videos", f"group_{scene_number}_final.mp4"),
        ]
        for dp in downstream_paths:
            if os.path.exists(dp):
                try:
                    os.remove(dp)
                    print(f"  [Invalidated] Removed stale downstream file: {dp}")
                except Exception as del_err:
                    print(f"  [Warn] Failed to remove {dp}: {del_err}")

        print(f"  [SUCCESS] Wrote validated timestamped fixes to {target_file}")
        return str(output_dir)

    def process_topic(self, base_folder, topic_id, force=False):
        """Processes all scenes for a given topic folder."""
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        cgi_input_path = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_input_path):
            cgi_input_path = os.path.join(base_folder, "CGI_Input.json")
        if not os.path.exists(cgi_input_path):
            raise FileNotFoundError(f"Missing CGI_Input.json in {meta_dir} or {base_folder}")

        cgi_data = self.load_json(cgi_input_path)
        last_out = None
        skip_scenes_env = os.environ.get("SKIP_SCENES")
        skip_list = [s.strip() for s in skip_scenes_env.split(",")] if skip_scenes_env else []
        for group in cgi_data.keys():
            if str(group) in skip_list:
                print(f"Skipping Scene {group} per SKIP_SCENES")
                continue
            last_out = self.generate_scene_timestamped_fixes(base_folder, group, cgi_data, force=force)

        return last_out

    def process_files(self, target_topic_id=None, force=False):
        """Main batch processing logic iterating through input tracker."""
        input_tracker = self._load_tracker(self.input_tracker_path)
        if not input_tracker:
            print(f"Input tracker {self.input_tracker_path} empty or missing.")
            return

        for topic_id, input_entry in input_tracker.items():
            if target_topic_id and topic_id != target_topic_id:
                continue
            if not input_entry.get("processed", False):
                continue

            output_tracker = self._load_tracker(self.output_tracker_path)
            if not force and topic_id in output_tracker and output_tracker[topic_id].get("processed", False):
                continue

            print(f"\n[Stage 19] Processing Topic: {topic_id} ...")
            base_folder = os.path.join(self.input_folder, topic_id)
            config_path = os.path.join(base_folder, "ex_config.json")

            if not os.path.exists(config_path):
                print(f"  [Skip] Missing ex_config.json in {base_folder}")
                continue

            try:
                out_path = self.process_topic(base_folder, topic_id, force=force)

                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": out_path,
                    "processed": True,
                    "topic_name": topic_id,
                    "topic_id": topic_id,
                    "failure_reason": None
                }
                self._save_tracker(self.output_tracker_path, tracker)

                # Reset downstream trackers so downstream stages are guaranteed to execute
                tracker_dir = os.path.dirname(self.output_tracker_path)
                downstream_trackers = [
                    os.path.join(tracker_dir, "20_eng_corrections_tracker.json"),
                    os.path.join(tracker_dir, "21_timing_adjustment_tracker.json"),
                    os.path.join(tracker_dir, "22_final_render_tracker.json")
                ]
                for dt_path in downstream_trackers:
                    if os.path.exists(dt_path):
                        try:
                            d_tracker = self._load_tracker(dt_path)
                            if topic_id in d_tracker:
                                d_tracker[topic_id]["processed"] = False
                                self._save_tracker(dt_path, d_tracker)
                                print(f"  [Tracker] Reset downstream tracker {os.path.basename(dt_path)} for {topic_id}")
                        except Exception as dt_err:
                            print(f"  [Warn] Could not reset downstream tracker {dt_path}: {dt_err}")

                print(f"[Stage 19] Successfully completed {topic_id}.")

            except Exception as e:
                print(f"[Stage 19 Error] Failed processing {topic_id}: {e}")
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": None,
                    "processed": False,
                    "topic_name": topic_id,
                    "topic_id": topic_id,
                    "failure_reason": str(e)
                }
                self._save_tracker(self.output_tracker_path, tracker)


if __name__ == "__main__":
    workflow_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(workflow_dir)
    trackers_dir = os.path.join(parent_dir, "ppt_trackers") if os.path.exists(os.path.join(parent_dir, "ppt_trackers")) else os.path.join(parent_dir, "trackers")
    data_dir = os.path.join(parent_dir, "output") if os.path.exists(os.path.join(parent_dir, "output")) else (os.path.join(parent_dir, "data_ppt_advanced") if os.path.exists(os.path.join(parent_dir, "data_ppt_advanced")) else os.path.abspath("."))

    vlm_fix_tracker = os.path.join(trackers_dir, "18_vlm_fix_tracker.json")
    vlm_fixing_stage_tracker = os.path.join(trackers_dir, "19_vlm_fixing_stage_tracker.json")
    stage = VLMTimestampedFixStage(
        input_tracker_path=vlm_fix_tracker,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        output_tracker_path=vlm_fixing_stage_tracker,
        input_folder=data_dir
    )
    stage.process_files()
