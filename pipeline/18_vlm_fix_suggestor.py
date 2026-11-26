#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 18: VLM REVIEW FEEDBACK (AESTHETIC & STRUCTURAL EVALUATION)
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 18
   - Script Name: 18_vlm_fix_suggestor.py
   - Primary Class: SuggestionsFromVLM
   - Pipeline Role:
     Executes multimodal visual evaluation using Gemini 3.8 Flash on the triangulated
     keyframe images produced in Stage 17. Evaluates aesthetic quality, visual balance,
     readability, formula contrast, container padding, and typography hierarchy.
     Outputs structured per-frame aesthetic feedback JSON files with cell-targeted
     relocation suggestions.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 17 (17_generate_visual_triangulation.py):
       - How: Ingests vlm_inputs/scene_{group}/ and vlm_inputs/scene_{group}/manifest.json via
         17_generate_triangulation_tracker.json.
       - Purpose: Consumes manifest.json to bind grid screenshots directly to sliced code blocks (lines, snippet),
         Set-of-Marks badge legends, and visible visual objects, eliminating VLM variable hallucination.
     * Stage 6 (6_presentation_composer.py):
       - How: Ingests enhanced_animation_instructions_<model>.json.
       - Purpose: Retrieves original intended spatial design specifications.
     * Stage 5 (5_populate_audio_runtime.py):
       - How: Ingests CGI_Input.json.
       - Purpose: Correlates frames with narration sections.
   - Input Tracker: ppt_trackers/17_generate_triangulation_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * vlm_inputs/scene_{group}/manifest.json (Stage 17):
       Location: data_ppt_advanced/<TOPIC_NAME>/vlm_inputs/scene_{group}/manifest.json
       Content: Centralized scene triangulation manifest mapping each grid image to its exact Python code block
                (start_line, end_line, snippet), Set-of-Marks markers, and visible visual objects.
     * vlm_inputs/scene_{group}/ keyframe artifacts (Stage 17):
       Location: data_ppt_advanced/<TOPIC_NAME>/vlm_inputs/scene_{group}/
       Content: sec_{s}_frame_{f}_triangulated.png (or sec_*_grid.png), sec_{s}_frame_{f}_cellmap.json,
                sec_{s}_frame_{f}_triangulated.json.
     * enhanced_animation_instructions_<model>.json (Stage 6):
       Location: data_ppt_advanced/<TOPIC_NAME>/enhanced_animation_instructions_<model>.json
       Content: Composed design specifications.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Master storyboard timings.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Configuration and model settings.
     * Input Tracker:
       Location: ppt_trackers/17_generate_triangulation_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 17_generate_triangulation_tracker.json.
   - Step 2: Gathers all triangulated keyframe images and manifest.json for each scene.
   - Step 3: Sends multimodal prompts to Gemini 3.8 Flash (google.genai):
     * Consumes manifest.json to inject the exact code block for the presentation step alongside the grid image.
     * Passes the Set-of-Marks badge legend so the VLM references exact Python variable names.
     * Passes the cellmap and attached issue list.
     * Evaluates against the 4 Core Visual Rules: Header Clearance (top <= 1.70),
       Border Clamping (|x| <= 6.4), In-Box Multi-Column collisions, and High Contrast.
   - Step 4: The VLM provides structured visual judgments and cell-level relocation coordinates.
   - Step 5: Writes sec_{s}_frame_{f}_aesthetic.json for each evaluated keyframe.
   - Step 6: Atomically updates 18_vlm_fix_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * vlm_inputs/scene_{group}/sec_{s}_frame_{f}_aesthetic.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/vlm_inputs/scene_{group}/
       Content: Aesthetic and structural evaluation JSON detailing layout defects,
                contrast issues, and proposed cell-based repairs.
     * Output Tracker:
       Location: ppt_trackers/18_vlm_fix_tracker.json
       Content: Atomic tracker confirming completion of VLM fix evaluation.

6. DOWNSTREAM CONSUMERS:
   - Stage 19 (19_vlm_fixing_stage.py): Synthesizes timestamped physical code directives from these reports.
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
import os
import portalocker
import math
import argparse
from glob import glob
from collections import defaultdict
from pathlib import Path
import subprocess
import re
import time
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
MODEL_NAME = "gemini-3.8-flash"
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5
DESIGN_SPEC_MAX_CHARS = 2500

_PREFIX_RE = re.compile(r"^sec_(?P<section>.+?)_frame_(?P<frame>\d{4})_(?P<reason>error\+aesthetic|error|aesthetic)$")
_SECTION_MARK_RE = re.compile(r"^\s*##\s*Presentation Step\s+(\d+)\b", re.IGNORECASE)

class SuggestionsFromVLM:
    """
    Stage 18: VLM Review Feedback.
    Invokes Gemini 3.8 Flash Multimodal on grid-overlaid keyframes to evaluate visual
    balance, readability, and contrast, emitting structured aesthetic JSON reports.
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
        self.input_folder = input_folder
        self.google_api_key = google_api_key
        self.claude_api_key = claude_api_key
        self.input_folder = input_folder
        self.h_extent=7
        self.v_extent=3.9

        # Internal cache for line-numbered code and code slices
        self._code_cache = {}

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
        """
        Load a JSON tracker with a shared lock (read lock).
        """
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
        """
        Save a JSON tracker with an exclusive lock (write lock).
        """
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

    # --------------------------------------------------------------------------
    # Code Loading & Slicing
    # --------------------------------------------------------------------------

    def _find_scene_code(self, base, scene_number, code_path=None):
        candidates = [Path(code_path)] if code_path else [
            base / f"group_{scene_number}.py",
            base / "manim_codes" / f"group_{scene_number}.py",
            base / "manim_extracted_codes" / f"group_{scene_number}.py",
        ]
        return next((p for p in candidates if p.is_file()), None)

    def load_scene_code(self, path):
        """Line-numbered scene source for the CODE-AWARE ANALYSIS prompt block."""
        with open(path, encoding="utf-8") as f:
            src = f.read()
        return "\n".join(f"{i + 1:4d} | {line}"
                        for i, line in enumerate(src.splitlines()))

    

    def _is_fence(self, line):
        s = line.strip()
        return bool(s) and set(s) <= set("#=-")

    def slice_scene_code_for_section(self, path, section_id=None):
        """
        Line-numbered slice of a generated scene file for the CODE-AWARE prompt.
        """
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()

        def num(segment, start_idx):
            return "\n".join(f"{start_idx + j + 1:4d} | {l}"
                            for j, l in enumerate(segment))

        marks = [(i, m.group(1)) for i, l in enumerate(lines)
                for m in [_SECTION_MARK_RE.match(l)] if m]
        if not marks:
            return num(lines, 0)

        first = marks[0][0]
        pre_end = first - 1 if first > 0 and self._is_fence(lines[first - 1]) else first
        preamble = num(lines[:pre_end], 0)
        if section_id is None:
            return preamble

        sid = str(section_id)
        for k, (i, s) in enumerate(marks):
            if s != sid:
                continue
            start = i - 1 if i > 0 and self._is_fence(lines[i - 1]) else i
            end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
            if end > start and self._is_fence(lines[end - 1]):
                end -= 1  # leave the next section's opening fence out
            block = num(lines[start:end], start)
            return (preamble
                    + "\n     | ... (other sections omitted) ...\n"
                    + block)

        return num(lines, 0)

    def get_section_block_only(self, path, section_id):
        """Extracts only the unique section block code, omitting the preamble."""
        full_slice = self.slice_scene_code_for_section(path, section_id)
        preamble = self.slice_scene_code_for_section(path, None)
        
        divider = "\n     | ... (other sections omitted) ...\n"
        if full_slice.startswith(preamble):
            block_part = full_slice[len(preamble):]
            if block_part.startswith(divider):
                block_part = block_part[len(divider):]
            return block_part
        return full_slice
    
    def discover_sections(self,vlm_input_dir):
        """Returns {section_id: [frame_meta, ...]} ordered narratively."""
        vlm_input_dir = Path(vlm_input_dir)
        by_section = defaultdict(list)

        for json_path in sorted(vlm_input_dir.glob("sec_*_frame_*.json")):
            stem = json_path.stem
            m = _PREFIX_RE.match(stem)
            if not m:
                continue
            section_id = m.group("section")
            frame_number = int(m.group("frame"))
            
            png_path = vlm_input_dir / f"{stem}_grid.png"
            if not png_path.exists():
                print(f"  [WARN] {stem}: missing grid png, skipping")
                continue

            by_section[section_id].append({
                "frame_number": frame_number,
                "reason": m.group("reason"),
                "json_path": json_path,
                "png_path": png_path,
                "cellmap_path": vlm_input_dir / f"{stem}_cellmap.json",
            })

        for section_id in by_section:
            by_section[section_id].sort(key=lambda f: f["frame_number"])

        return dict(sorted(by_section.items(), key=lambda kv: kv[1][0]["frame_number"]))


    def load_design_specs(self, enhanced_anim_path, scene_number):
        if not enhanced_anim_path or not os.path.exists(enhanced_anim_path):
            return ""
        try:
            with open(enhanced_anim_path, 'r', encoding="utf-8") as f:
                specs = f.read()
            return specs
        except Exception:
            return ""


    def load_frame_payload(self,frame_meta):
        with open(frame_meta["json_path"],"r", encoding="utf-8") as f:
            snap = json.load(f)

        # Note: Modern pre-computed text completely overrides raw objects dicts.
        return {
            "frame_number": frame_meta["frame_number"],
            "reason": frame_meta["reason"],
            "timestamp": snap.get("timestamp", 0.0),
            "issues": snap.get("filtered_issues_for_vlm", []),
            "som_markers": snap.get("som_markers", {}),
            "grid_context_text": snap.get("grid_context_text", ""),
            "png_path": frame_meta["png_path"],
        }

    # --------------------------------------------------------------------------
    # Prompt Builders
    # --------------------------------------------------------------------------

    def build_section_group_prompt(self,group_ids, payloads_by_section, design_specs, code_file, code_scope):
        """
        Monolithic prompt that passes the master instructions alongside 
        dynamically injected data for a group of 1 to N sections.
        """
        lines = [
            'You are an expert Manim layout reviewer (an "art director") for educational animations.',
            'You will be shown frames from one or more sections of a scene. Each frame has a grid ',
            'overlay (columns A,B,C... / rows 1,2,3...) for reasoning about position ONLY (never ',
            'repeat cell IDs in your output) plus PRECOMPUTED grid-coverage text for every object -- the cell percentages are exact math from bounding boxes, so',
            'trust them over your own visual estimation. ',
            'Objects involved in flagged issues are OUTLINED ',
            'with numbered badges -- use the badge legend in the text below to identify them by ',
            'their exact variable name with certainty.',
            'Also look for the mentioned error flags even when the objects that may be involved are not outlined'
        ]

        # Inject SHARED scene code blocks ONCE at the top level of the prompt
        if code_file:
            lines.append("==================================================")
            lines.append("SHARED CODE CONTEXT (helpers, imports, and variables):")
            lines.append("==================================================")
            if code_scope == "full":
                lines.append(self.load_scene_code(str(code_file)))
            else:
                lines.append(self.slice_scene_code_for_section(str(code_file), None))
            lines.append("==================================================\n")

        # Inject data for each section in this group
        for sid in group_ids:
            lines.append(f"\n### Presentation Step {sid} ###\n")
            
            #if sid in design_specs:
            #    lines.append(f"DESIGN INTENT:\n{design_specs[sid]}\n")
                
            # If using "section" scope, show only the section-specific sliced code block
            if code_file and code_scope == "section":
                lines.append(f"ORIGINAL CODE BLOCK FOR Presentation step {sid}:")
                lines.append(self.get_section_block_only(str(code_file), sid))
                lines.append("")

            for fp in payloads_by_section[sid]:
                lines.append(f"--- Frame {fp['frame_number']} (t={fp['timestamp']:.2f}s, reason={fp['reason']}) ---")
                
                if fp["issues"]:
                    lines.append("Confirmed structural issues (must be addressed or explicitly waived):")
                    for issue in fp["issues"]:
                        if isinstance(issue, dict):
                            desc = issue.get('description', '')
                            issue_id = issue.get('id', '?')
                        else:
                            desc = str(issue)
                            issue_id = '?'
                        lines.append(f"  - [{issue_id}] {desc}")
                else:
                    lines.append("Structural issues are not explicitly flagged here -- however, look for deviations from expected.")

                if fp.get("som_markers"):
                    lines.append("Badge Legend (Badge Number -> Exact Variable Name):")
                    for k in sorted(fp["som_markers"], key=int):
                        lines.append(f"  {k} -> {fp['som_markers'][k]}")

                if fp.get("grid_context_text"):
                    lines.append(fp["grid_context_text"])
                    
                lines.append("")

        lines.append(f"Brand guidelines:\n{design_specs}")

        OUTPUT_FORMAT_OLD = f"""
        OUTPUT FORMAT (exactly; plain text only)
        Issue: <1-3 sentences describing the underlying layout/design/branding problem. Explain why the composition breaks from the design specs or layout principles.>

        Suggestions:
        * <one actionable repair per bullet>
        * <reference objects ONLY by their exact variable names>
        * <give concrete target values (width, height, scale, font sizes, offsets, colors)>
        * <order from highest-impact/root-cause to lowest-impact/fine-tuning>

        VISUAL REVIEW
        Evaluate every frame. Report only genuine issues. 

        1. Real-Estate Utilization & Safe Zones
        - Safe Zones: Keep top corners and the bottom edge completely clear for future captions. Do not position elements flush against these boundaries.
        - Primary visuals should intentionally fill available space while preserving comfortable margins. Avoid sparse, empty layouts and microscopic/collapsed elements.

        2. Branding, Color & Design Fidelity (Simplilearn OSL 3.0)
        - Palette Governance: Strictly enforce Simplilearn approved 10-color infographic pastel palette (#62B7E4, #7EA2C8, #9B99C7, #8ECDB7, #E6A157, #DDB945, #E58F6D, #B88968, #D98CA1, #C1A5C6). Primary text is Dark Charcoal (#404040).
        - Focus Highlight: Orange (#F78908) with stroke_width=3.0 and draw_time=1.0s (maximum 1 active highlight at a time).
        - Color Restraints: Strictly minimize green (NEVER green cards or titles). STRICTLY NO yellow text on light panels. STRICTLY NO 3D imagery, drop shadows, or thick black borders (2D flat vector educational styling only).
        - Macro/Micro Containment: Check that layout regions (macro-containers) alternate intelligently between Solid White cards (#FFFFFF) and subtle pastel category pills. Content inside them must sit on distinct contrasting cards (micro-grouping, 10px / 0.074 corner radius). 
        - Data Pills: Flag floating numbers, variables, or list items. They must be encapsulated in solid micro-panels (e.g., rounded pills).
        - Typography Hierarchy: Open Sans exclusively. Major titles: 28pt Bold in Title Case (5-7 words, no ALL-CAPS). Subtitles: 18-20pt SemiBold. Body: 14-16pt Regular (#404040).

        3. Layout Consistency & Symmetry
        - Clean alignment for rows/columns. Consistent spacing for related objects.
        - Text must be centered inside its container unless intentionally offset. Bullet/icon indicators must perfectly align with companion text.
        - Font Size Uniformity: Text elements sharing a screen must maintain uniform sizes. Flag text that has been arbitrarily scaled to fit boundaries. 
        - Symmetry: Repeated structures (cards, timelines, comparison matrices) must share exact relative alignment, anchoring, spacing, and visual weight. 

        4. Containment
        - No text, graphics, or borders extending outside intended boundaries.
        - Text should not overflow out of its pill or background panel
        - For fill-bars/meters: the fill must stay strictly inside the track on all edges and grow from the correct anchored edge. 
        - Verify parent containers provide enough space before enlarging any child object.

        CODE-AWARE ANALYSIS
        You are given:
        - Rendered frames (grid-overlaid; issue-involved objects OUTLINED with numbered badges -- trust the badge legend for exact variable names)
        - Object metadata with PRECOMPUTED grid coverage 
        - Grid geometry
        - Original Manim code (line-numbered)

        Prefer structural layout causes, such as:
        - Scaling text blocks to fit containers instead of wrapping lines via newline ('\n').
        - Restrictive parent layouts, excessive arrange() buffers, or parent transformations shrinking descendants.
        - Missing micro-containers for text/data.
        Prefer fixing the highest-level cause over compensating downstream symptoms (e.g., fix the parent VGroup spacing instead of shifting 10 child objects).

        REPAIR PRIORITY
        1. Safe-zone breaches & Root layout structure
        2. Branding violations (Palette, Typography size mismatch, Floating Data)
        3. Parent group sizing/arrangement
        4. Container constraints and sibling spacing
        5. Alignment and Symmetry
        6. Cosmetic adjustments

        RULES
        - Never invent object names.
        - Never recommend gradients for text.
        - Never recommend implementation APIs/code snippets (express repairs as design/layout changes).
        - Every flagged issue must be addressed by a suggestion or explicitly waived with justification.
        - Do NOT use references to frame numbers in the output.
        - Assume screen bounds x in [-{self.h_extent}, {self.h_extent}], y in [-{self.v_extent}, {self.v_extent}].
        - Do not instruct recreating elements missing only from the final frame (they likely faded out correctly).
        - CARD WIDTH CLAMP: Inside left panel or 2-column workspaces, card widths MUST NOT exceed 3.3 units. Max interior content width is 2.9.
        - FORMULA SCALING LIMIT: Never suggest scaling formulas or text if they would exceed card boundaries. Long equations must be wrapped or scaled to fit width, NOT arbitrarily enlarged.
        - STEP CLEANUP: Always recommend explicitly fading out previous step visual elements upon entering a new Presentation Step to eliminate visual clutter.
        - DYNAMIC ARRANGEMENT: For lists and stacked cards, recommend vertical grouping with VGroup.arrange(DOWN, buff=0.2) rather than manual coordinate offsets.
        - NO ALL CAPS MANDATE: Flag any on-screen text or titles written in ALL CAPS. Recommend Title Case (Camel Case) for titles, headers, badges, and card tags, and Sentence case for body text.
        - REDUCE GREEN USAGE AS MUCH AS POSSIBLE: Flag any prominent green cards, boxes, panels, or node fills and recommend replacing them with Dark Blue, Light Blue, Purple, or Yellow.
        """

        OUTPUT_FORMAT = f"""
        OUTPUT FORMAT (exactly; plain text only)

        Issue: <1-3 sentences describing the underlying layout/design/branding problem. Explain why the composition breaks from the design specs or layout principles.>

        Suggestions:
        * <one actionable repair per bullet>
        * <reference objects ONLY by their exact variable names>
        * <give concrete target values (width, height, scale, font sizes, offsets, colors)>
        * <order from highest-impact/root-cause to lowest-impact/fine-tuning>

        VISUAL REVIEW

        Evaluate every frame. Report only genuine issues.

        1. Real-Estate Utilization & Safe Zones
        - Keep top corners and bottom edge completely clear for future captions.
        - Do not position elements flush against frame boundaries.
        - Primary visuals should intentionally use available space while preserving comfortable margins.
        - Avoid both sparse layouts and microscopic/collapsed elements.

        2. Branding, Color & Design Fidelity (Simplilearn OSL 3.0)
        - Palette Governance: Simplilearn approved 10-color infographic pastel palette (#62B7E4, #7EA2C8, #9B99C7, #8ECDB7, #E6A157, #DDB945, #E58F6D, #B88968, #D98CA1, #C1A5C6) on pure white (#FFFFFF) cards.
        - Focus Highlight: Orange (#F78908) with stroke_width=3.0 and draw_time=1.0s (max 1 active at a time).
        - Color Restraints: Strictly minimize green. NO yellow text on light panels. NO 3D imagery, drop shadows, or thick black borders.
        - Macro-containers should use clean white cards with 10px (0.074) rounded corners and subtle category pills.
        - Floating numbers, variables, or list items should be contained in appropriate micro-panels/pills.
        - Typography: Open Sans exclusively. Major titles should be in Title Case (5-7 words, no ALL-CAPS) with #404040 primary text.

        3. TEXT LAYOUT & HIERARCHY
        - Text sizing is a primary review criterion.
        - Flag text that is visibly too small, too large, arbitrarily scaled, vertically compressed, or inconsistent with nearby text serving the same role.
        - Preserve consistent font sizes for text sharing the same semantic role.
        - Never solve text overflow primarily by shrinking the font.
        - Prefer restructuring the text into multiple lines or individual text elements while preserving the intended hierarchy.
        - Text blocks must have deliberate structure: related lines should share a common alignment, spacing and vertical rhythm.
        - Do not allow independent text fragments to appear as an unstructured collection.
        - Lists, sequences, key drivers, steps and repeated items must use clear vertical structure and consistent spacing.
        - When bullets or equivalent indicators are appropriate, align them consistently with their companion text.
        - Multi-line text should normally be left-aligned when functioning as a list, explanation, definition or repeated item.
        - Avoid centering body text merely because its parent container is centered.
        - Titles and headings may be centered when visually appropriate; explanatory/body content should use the alignment that best communicates structure.

        4. LAYOUT CONSISTENCY & SYMMETRY
        - Clean alignment for rows and columns.
        - Consistent spacing for related objects.
        - Text must be centered inside its container only when the design calls for centered text; otherwise use intentional left alignment.
        - Repeated structures must share exact relative alignment, anchoring, spacing and visual weight.
        - Related text elements should share a common left edge when forming a vertical structure.
        - Check vertical rhythm between headings, body text, bullets and annotations.
        - Flag uneven or arbitrary vertical placement of related text elements.

        5. CONTAINMENT
        - No text, graphics, or borders extending outside intended boundaries.
        - Containers must provide sufficient width and height for their contents.
        - Do not enlarge a child to solve a parent sizing problem.
        - For fill-bars/meters: the fill must stay strictly inside the track on all edges and grow from the correct anchored edge.

        6. TEXT WRAPPING & LINE BREAKS
        - Do NOT rely on scaling a single text object to fit a narrow container.
        - When text needs wrapping, prefer multiple individual text mobjects representing deliberate lines/items.
        - Vertically stack related text mobjects with consistent spacing and align their left edges using `aligned_edge=LEFT`.
        - Each line/item should retain the appropriate semantic hierarchy and font size.
        - Use explicit line breaks only when they create a deliberate textual unit; do not use arbitrary wrapping to force text into a container.
        - For lists, definitions, explanations and repeated items, prefer separate text mobjects over one large auto-wrapped text block.
        - Flag cases where a single text object appears visually cramped, unevenly wrapped, or difficult to scan.

        CODE-AWARE ANALYSIS

        You are given:
        - Rendered frames (grid-overlaid; issue-involved objects OUTLINED with numbered badges -- trust the badge legend for exact variable names)
        - Object metadata with PRECOMPUTED grid coverage
        - Grid geometry
        - Original Manim code (line-numbered)

        Prefer structural layout causes over downstream positional compensation.

        For text-related issues, inspect whether the root cause is:
        - incorrect font size
        - inappropriate text scaling
        - a single text object being forced into a narrow container
        - missing explicit line breaks
        - missing individual text mobjects for structured content
        - inconsistent `aligned_edge`
        - uneven `.arrange()` spacing
        - restrictive parent dimensions
        - excessive arrange buffers
        - parent transformations shrinking descendants
        - text being centered when left alignment is required
        - missing bullets or other structural indicators
        - independent text objects lacking a common alignment anchor

        Prefer fixing the highest-level structural cause over shifting individual text objects.

        Example:
        If several lines form a list but have inconsistent left edges, fix the shared alignment/arrangement rather than recommending separate x-offsets for every line.

        REPAIR PRIORITY

        1. Safe-zone breaches & root layout structure
        2. Text sizing, hierarchy & readability
        3. Text structure, wrapping & alignment
        4. Branding violations
        5. Parent group sizing/arrangement
        6. Container constraints and sibling spacing
        7. Alignment and symmetry
        8. Cosmetic adjustments

        RULES

        - Never invent object names.
        - Never recommend gradients for text.
        - Never recommend implementation APIs/code snippets; express repairs as design/layout changes.
        - Every flagged issue must be addressed by a suggestion or explicitly waived with justification.
        - Do NOT use references to frame numbers in the output.
        - Assume screen bounds x in [-{self.h_extent}, {self.h_extent}], y in [-{self.v_extent}, {self.v_extent}].
        - Do not instruct recreating elements missing only from the final frame; they likely faded out correctly.
        - Do not recommend shrinking text when restructuring or wrapping can solve the problem.
        - Do not recommend arbitrary per-object offsets when a shared alignment or parent-layout fix can solve the issue.
        - When related text forms a list, sequence, definition set or repeated structure, prefer a common left edge and consistent vertical rhythm.
        - Treat text alignment and sizing as structural layout properties, not cosmetic details.
        - EXACT NUMERIC TARGET MANDATE (CRITICAL): Every suggestion bullet MUST state exact target values, numeric coordinate offsets, or specific dimensions (e.g., "Shift dash_label left by dx = -0.8 units (target x = 5.6) to clear arrow tip", "Set card width to 3.4", "Set font_size = 18"). NEVER use vague qualitative phrases like "slightly shift", "adjust position", or "make smaller".
        - UNIFORM FONT SIZING ACROSS SIBLING BOXES & SHAPES (CRITICAL):
          All sibling cards, comparison boxes, quadrant cards, flowchart nodes, and table cells MUST maintain a single, strictly uniform font size (13pt-14pt).
          NEVER recommend scaling text down to container width (e.g. `scale_to_fit_width`) or reducing font size on individual boxes/cards when sibling boxes have larger font sizes.
          When text in one box exceeds container boundaries, ALWAYS instruct inserting explicit `\n` linebreaks to wrap into 2 lines and expanding the container height, or widening the container, NEVER shrinking the font size!
        - LINE BREAKS OVER FONT SHRINKING: When text overflows card boundaries, NEVER recommend shrinking font size below readable scale (14pt). ALWAYS mandate inserting explicit newline breaks ('\\n') or wrapping into separate text lines.
        - PERSISTENT MAIN SLIDE TITLE: The main slide title (top left at UP * 3.3) must remain STATIC throughout the scene. Flag any transition where FadeOut(title) and FadeIn(new_title) run concurrently, causing blurry ghost text or double-exposure. Sub-topics must only update section subtitles inside containers below y=2.2.
        - STEP TRANSITION PURGING (NO TEXT COLLISION/STACKING): When Step N introduces new text or cards in a container (e.g. left_container), all previous step headings, cards, annotations, and text inside that container must be completely removed/faded out. Flag any overlapping text or stacked titles where step 1 text persists underneath step 2 text.
        - CAMERA BOUNDS CLAMPING: In a 16:9 canvas, rightmost visual boundary must not exceed x = 6.4 (camera edge is 7.11). Flag any badges, pills, or cards positioned next_to(storefront, RIGHT) or pushed off-screen.
        - DYNAMIC CARD AND PRODUCT CONTAINER SIZING: Flag any product card where text spills across the bottom border. Cards must size dynamically (height = max(height, content.height + 2 * pad_y)) and images inside cards must be clamped (scale_to_fit_height <= 1.25).
        - CALLOUT AND ANNOTATION PLACEMENT: Callouts pointing to cards must sit strictly ABOVE the card (next_to(card, UP, buff=0.25)) or clearly to the outside, NEVER overlapping diagrams, curves, nodes, or card graphics.
        """

        return "\n".join(lines)+"\n"+OUTPUT_FORMAT


    def build_consolidation_prompt(self,all_sections_text, helper_code=None):
        """Separate prompt dedicated purely to consolidating the output."""
        parts = [
            'You are editing a Manim layout review report made of "Presentation Step N / Issue / Suggestions" blocks.',
            '',
            'Many blocks may describe THE SAME underlying root-cause bug recurring across several presentation steps ',
            '(e.g., a table-positioning bug happening in presentation steps 1, 2, and 3 due to a shared function).',
            '',
            'Rewrite this report so that:',
            '1. Presentation steps sharing a recurring root cause are merged into ONE block. Put all Presentation step numbers ',
            '   in the header (e.g. "Presentation Step 1, 2, 3") and provide ONE generalized fix addressing the root.',
            '2. Presentation steps with genuinely distinct issues stay in their own separate blocks.',
            '3. Keep the exact same format: "Presentation Step <N, N...>", "Issue: ...", "Suggestions: ..."',
            '4. Do not lose presentation step-specific details. If merged, state the shared fix, then add a bullet ',
            '   for the presentation step-specific detail tagged with that presentation step number.',
            ''
        ]
        if helper_code:
            parts.append("SHARED HELPER CODE CONTEXT (look here for recurring root causes):")
            parts.append(helper_code)
            parts.append("")
            
        parts.append("RAW REPORT TO REWRITE:\n")
        parts.append(all_sections_text)
        return "\n".join(parts)

    # --------------------------------------------------------------------------
    # API Calls
    # --------------------------------------------------------------------------

    def _strip_fences(self,text):
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"```$", "", text).strip()
        return text

    def call_gemini(self,prompt_text, image_paths=None, model=MODEL_NAME, max_retries=MAX_RETRIES):
        client = genai.Client(api_key=self.google_api_key)
        contents = [prompt_text]
        
        #print(f"The prompt for vlm review:\n{prompt_text}")
        
        
        for p in (image_paths or []):
            contents.append(types.Part.from_bytes(data=Path(p).read_bytes(), mime_type="image/png"))

        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(model=model, contents=contents)
                usage = getattr(response, "usage_metadata", None)
                if usage:
                    print(f"    [tokens] prompt={usage.prompt_token_count} "
                        f"output={usage.candidates_token_count} "
                        f"total={usage.total_token_count}")
                return self._strip_fences(response.text)
            except Exception as e:
                last_err = e
                print(f"  [WARN] Gemini call failed (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
        raise RuntimeError(f"Gemini call failed after {max_retries} attempts: {last_err}")

    # --------------------------------------------------------------------------
    # Execution
    # --------------------------------------------------------------------------

    def review_section_group(self, group_ids, sections_dict, design_specs, code_file, code_scope, model):
        payloads_by_section = {sid: [self.load_frame_payload(fm) for fm in sections_dict[sid]] for sid in group_ids}
        
        # Collect all image paths in the exact order the text prompt expects them
        image_paths = []
        for sid in group_ids:
            for fp in payloads_by_section[sid]:
                image_paths.append(fp["png_path"])
                
        prompt = self.build_section_group_prompt(group_ids, payloads_by_section, design_specs, code_file, code_scope)
        
        print(f"  [reviewing group] Sections {group_ids} ({len(image_paths)} frames sent) ...")
        return self.call_gemini(prompt, image_paths, model=model)


    def run_vlm_review(self,scene_number, base_dir=".", group_size=1, model=MODEL_NAME,
                    design_spec_path=None, code_path=None, code_scope="section"):
        base = Path(base_dir)
        vlm_input_dir = base / "vlm_inputs" / f"scene_{scene_number}"
        output_dir = base / "specific_suggestions_vlm"
        output_dir.mkdir(parents=True, exist_ok=True)

        vlm_input_dir.mkdir(parents=True, exist_ok=True)
        sections = self.discover_sections(vlm_input_dir)
        if not sections:
            print(f"  [NOTICE] No keyframes found in {vlm_input_dir} -- extracting fallback keyframes directly from video.")
            video_file = base / "manim_extracted_videos" / f"group_{scene_number}.mp4"
            if not video_file.exists():
                video_file = base / "manim_time_synced_videos" / f"group_{scene_number}.mp4"
            if video_file.exists():
                meta_dir = base / "metadata_blueprints"
                cgi_file = meta_dir / "CGI_Input.json" if (meta_dir / "CGI_Input.json").exists() else (base / "CGI_Input.json")
                sec_list = []
                if cgi_file.exists():
                    try:
                        with open(cgi_file, "r", encoding="utf-8") as f:
                            sec_list = json.load(f).get(str(scene_number), [])
                    except Exception:
                        pass
                if not sec_list:
                    sec_list = [{"run_time": 10.0}]
                running_t = 0.0
                for s_idx, s_info in enumerate(sec_list, start=1):
                    s_dur = float(s_info.get("run_time", 8.0))
                    t_mid = running_t + 0.45 * s_dur
                    t_end = max(t_mid + 1.0, running_t + 0.95 * s_dur)
                    running_t += s_dur
                    for t_sample, r_label in [(t_mid, "error"), (t_end, "aesthetic")]:
                        f_num = int(t_sample * 15)
                        stem = f"sec_{s_idx}_frame_{f_num:04d}_{r_label}"
                        raw_png = vlm_input_dir / f"{stem}_grid.png"
                        dest_json = vlm_input_dir / f"{stem}.json"
                        cellmap_path = vlm_input_dir / f"{stem}_cellmap.json"
                        cmd = ["ffmpeg", "-y", "-ss", str(max(0.0, t_sample)), "-i", str(video_file), "-frames:v", "1", str(raw_png)]
                        subprocess.run(cmd, capture_output=True, check=False)
                        with open(dest_json, "w", encoding="utf-8") as f:
                            json.dump({
                                "frame_number": f_num,
                                "timestamp": t_sample,
                                "filtered_issues_for_vlm": [f"Visual review for Presentation Step {s_idx}"],
                                "grid_context_text": f"Step {s_idx} keyframe at {t_sample:.1f}s",
                                "som_markers": {}
                            }, f, indent=2)
                        with open(cellmap_path, "w", encoding="utf-8") as f:
                            json.dump({"timestamp": t_sample}, f, indent=2)

                sections = self.discover_sections(vlm_input_dir)

        design_specs = self.load_design_specs(design_spec_path, scene_number)
        
        # --- SURGICAL FIX START (Code Loading) ---
        code_file = self._find_scene_code(base, scene_number, code_path)
        if code_file:
            print(f"Loaded scene code from {code_file}")
        else:
            print("  [WARN] scene source not found -- code-aware analysis disabled.")

        consolidated_path = output_dir / f"scene_{scene_number}_suggestions_consolidated.txt"

        if consolidated_path.exists():
            print(f"Suggestions for scene {scene_number} already exists. So skipping it")
            return output_dir

        # Determine consolidation helper context (Preamble or Full)
        helper_code = None
        if code_file:
            helper_code = (self.load_scene_code(str(code_file)) if code_scope == "full" 
                           else self.slice_scene_code_for_section(str(code_file), None))

        section_ids = list(sections.keys())
        raw_results = []
        
        for i in range(0, len(section_ids), group_size):
            group = section_ids[i:i + group_size]
            text_output = self.review_section_group(group, sections, design_specs, code_file, code_scope, model)
            raw_results.append(text_output)
            
        raw_text = "\n\n".join(raw_results) + "\n"
        out_path = output_dir / f"scene_{scene_number}_suggestions_raw.txt"
        out_path.write_text(raw_text, encoding="utf-8")
        print(f"Wrote {out_path}")

        print("  [consolidate] Merging recurring root-cause suggestions across sections...")
        # PASS helper_code HERE
        consolidation_prompt = self.build_consolidation_prompt(raw_text, helper_code=helper_code)
        consolidated_text = self.call_gemini(consolidation_prompt, image_paths=None, model=model)
        
        
        consolidated_path.write_text(consolidated_text.strip() + "\n", encoding="utf-8")
        print(f"Wrote {consolidated_path}")
        return output_dir

    def generated_vlm_suggestions(self,config_data, topic_id):
        base_folder = config_data.get('base_folder', '')
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        prompt_dir = os.path.join(base_folder, "prompt_context_and_guidelines")
        jazzy_model_name = config_data.get('jazzy_model_name', MODEL_NAME)
        cgi_input_file = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_input_file):
            cgi_input_file = f"{base_folder}/CGI_Input.json"
        design_spec_file = os.path.join(prompt_dir, "color_palette_guidelines.txt")
        if not os.path.exists(design_spec_file):
            design_spec_file = f"{base_folder}/color_palette_guidelines.txt"
        if not os.path.exists(design_spec_file):
            alt_candidates = [
                f"{base_folder}/color_guidelines.txt",
                os.path.join(os.path.dirname(__file__), "helpers", "guidelines", "color_guidelines.txt"),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "Guidelines", "color_guidelines.txt")
            ]
            for cand in alt_candidates:
                if os.path.exists(cand):
                    design_spec_file = cand
                    break
        cgi_input = self.load_json(cgi_input_file)
        theme = config_data.get("theme", "default")
        if theme=="promo":
            self.h_extent=3.9
            self.v_extent=7.0
        else:
            self.h_extent=7.0
            self.v_extent=3.9
        skip_scenes_env = os.environ.get("SKIP_SCENES")
        skip_list = [s.strip() for s in skip_scenes_env.split(",")] if skip_scenes_env else []
        for group in cgi_input.keys():
            if str(group) in skip_list:
                print(f"Skipping Scene {group} per SKIP_SCENES")
                continue
            code_path = f"{base_folder}/manim_extracted_codes/group_{group}.py"
            self.run_vlm_review(scene_number=group,base_dir=base_folder,group_size=2,model=MODEL_NAME,design_spec_path=design_spec_file,code_path=code_path,code_scope="section")
        return f"{base_folder}/specific_suggestions_vlm"

    def process_files(self, target_topic_id=None):
        input_tracker = self._load_tracker(self.input_tracker_path)
        if not input_tracker: return

        for topic_id, input_entry in input_tracker.items():
            if target_topic_id and topic_id != target_topic_id:
                continue
            if not input_entry.get("processed", False): continue

            output_tracker = self._load_tracker(self.output_tracker_path)
            if topic_id in output_tracker and output_tracker[topic_id].get("processed", False): continue

            print(f"Processing {topic_id}...")
            base_folder = os.path.join(self.input_folder, topic_id)
            config_path = os.path.join(base_folder, "ex_config.json")
            
            if not os.path.exists(config_path): continue
            
            try:
                with open(config_path, 'r', encoding="utf-8") as f:
                    config_data = json.load(f)

                output_file_path = self.generated_vlm_suggestions(config_data, topic_id)
                
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": output_file_path, "processed": True,
                    "topic_name": topic_id, "topic_id": topic_id, "failure_reason": None
                }
                self._save_tracker(self.output_tracker_path, tracker)
                print(f"Successfully processed {topic_id}.")

            except Exception as e:
                print(f"Error processing {topic_id}: {e}")
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": None, "processed": False,
                    "topic_name": topic_id, "topic_id": topic_id, "failure_reason": str(e)
                }
                self._save_tracker(self.output_tracker_path, tracker)

if __name__=="__main__":
    workflow_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(workflow_dir)
    trackers_dir = os.path.join(parent_dir, "ppt_trackers") if os.path.exists(os.path.join(parent_dir, "ppt_trackers")) else os.path.join(parent_dir, "trackers")
    data_dir = os.path.join(parent_dir, "output") if os.path.exists(os.path.join(parent_dir, "output")) else (os.path.join(parent_dir, "data_ppt_advanced") if os.path.exists(os.path.join(parent_dir, "data_ppt_advanced")) else os.path.abspath("."))

    generate_triangulation_tracker = os.path.join(trackers_dir, "17_generate_triangulation_tracker.json")
    if not os.path.exists(generate_triangulation_tracker):
        generate_triangulation_tracker = os.path.join(trackers_dir, "generate_triangulation_tracker.json")
    vlm_fix_tracker = os.path.join(trackers_dir, "18_vlm_fix_tracker.json")
    if not os.path.exists(vlm_fix_tracker):
        vlm_fix_tracker = os.path.join(trackers_dir, "vlm_fix_tracker.json")

    stage = SuggestionsFromVLM(
        input_tracker_path=generate_triangulation_tracker, 
        google_api_key=os.environ.get("GOOGLE_API_KEY"), 
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        output_tracker_path=vlm_fix_tracker, 
        input_folder=data_dir
    )
    stage.process_files()