#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 20: FINAL STYLING & CODE FIXES
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 20
   - Script Name: 20_final_styling_corrections.py
   - Primary Class: FinalStylingCorrections
   - Pipeline Role:
     Applies the comprehensive brand styling guidelines, typography constraints, and
     the timestamped multimodal visual fixing directives from Stage 19 to generate
     pristine, production-ready Manim scripts in manim_styled_codes/. Strictly enforces
     the 70/30 Visual-First canvas allocation, Header Clearance Ceiling (top edge y <= 1.70),
     formula contrast enforcement (dark blue MathTex on light cards), and deterministic
     title stacking prevention.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 19 (19_vlm_fixing_stage.py):
       - How: Ingests vlm_fixing_stage/scene_{group}_timestamped_fixes.txt via
         19_vlm_fixing_stage_tracker.json.
       - Purpose: Supplies physical timestamped visual repair instructions.
     * Stage 14 (14_implement_corrections.py):
       - How: Ingests manim_extracted_codes/group_{group}.py.
       - Purpose: Base Manim scene scripts to be refactored with brand styles and fixes.
     * Stage 1 (1_generate_instructional_design.py):
       - How: Ingests instructions_<model>.json.
       - Purpose: Preserves exact step count parity and narration context.
     * Topic Style Guidelines:
       - How: Ingests font_guidelines.txt and color_palette_guidelines.txt.
       - Purpose: Enforces typography rules, Title Case, no ALL-CAPS, and brand color palette.
   - Input Tracker: ppt_trackers/19_vlm_fixing_stage_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * vlm_fixing_stage/scene_{group}_timestamped_fixes.txt (Stage 19):
       Location: data_ppt_advanced/<TOPIC_NAME>/vlm_fixing_stage/scene_{group}_timestamped_fixes.txt
       Content: Timestamped repair directives.
     * manim_extracted_codes/group_{group}.py (Stage 14):
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_extracted_codes/group_*.py
       Content: Pre-styling Manim scripts.
     * instructions_<model>.json (Stage 1):
       Location: data_ppt_advanced/<TOPIC_NAME>/instructions_<model>.json
       Content: Storyboard steps and narration.
     * font_guidelines.txt & color_palette_guidelines.txt (optional):
       Location: data_ppt_advanced/<TOPIC_NAME>/font_guidelines.txt, color_palette_guidelines.txt
       Content: Typography rules, Title Case requirements, and color matrices.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Configuration specifying 'final_styling_api' and 'final_styling_model_name'.
     * Input Tracker:
       Location: ppt_trackers/19_vlm_fixing_stage_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 19_vlm_fixing_stage_tracker.json.
   - Step 2: Reads the existing code, storyboard, style guidelines, and timestamped fixes.
   - Step 3: Prompts Gemini 3.5 Flash / Claude to refactor the Manim code:
     * Applies timestamped layout fixes (container shifting, coordinate updates).
     * Enforces the 70/30 Visual Allocation law (functional visual models dominate canvas).
     * Eliminates ALL-CAPS; enforces Title Case for titles/badges, Sentence Case for body.
     * Minimizes green (forbidden for containers, cards, and primary text).
   - Step 4: Runs refactored code through code_sanitizer.sanitize_manim_code():
     * Wipes title stacking on step transitions (injects self.remove(*self.mobjects)).
     * Automatically converts Transform(title, title2) to ReplacementTransform.
     * Clamps macro container heights (height <= 4.8) and shifts centers down to DOWN * 0.70.
     * Enforces dark charcoal color (#404040) for uncolored MathTex formulas.
   - Step 5: Writes styled Manim scripts into manim_styled_codes/group_{n}.py.
   - Step 6: Atomically updates 20_eng_corrections_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * manim_styled_codes/group_{n}.py:
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_styled_codes/group_*.py
       Content: Production-styled, visually corrected Manim Community Python scripts.
     * Output Tracker:
       Location: ppt_trackers/20_eng_corrections_tracker.json
       Content: Atomic tracker confirming completion of final styling and visual fixes.

6. DOWNSTREAM CONSUMERS:
   - Stage 21 (21_timing_adjustments.py): Synchronizes animation runtimes in these scripts to speech audio.
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
import shutil
import glob
import portalocker
import time
import re
from google import genai
from google.genai import types
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
from dotenv import load_dotenv
load_dotenv()
from code_sanitizer import sanitize_manim_code, is_executive_topic, get_visual_archetype, heal_syntax_errors

class FinalStylingCorrections:
    """
    Stage 20: Identifies unprocessed inputs and refines scene code with styling guidelines
    and timestamped VLM visual fixing directives.
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

    def remove_code_fences(self, text: str) -> str:
        """
        Removes ```python ... ``` or ``` ... ``` wrappers
        from the beginning and end of a string.
        """
        text = text.strip()
        fence_match = re.match(r"^```(?:python)?\s*\n(.*)\n```$", text, re.DOTALL)
        if fence_match:
            return fence_match.group(1)
        return text

    @staticmethod
    def replace_func_in_code(code: str, func_name: str, new_func_body: str) -> str:
        """
        Replaces the complete definition of func_name in code with new_func_body,
        preserving matching indentation level without regex backtracking risks.
        """
        lines = code.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(rf"^([ \t]*)def {func_name}\b", line)
            if match:
                indent = match.group(1)
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if not next_line.strip():
                        j += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip(" "))
                    if next_indent <= len(indent):
                        break
                    j += 1
                body_lines = [f"{indent}{l}" if l.strip() else "" for l in new_func_body.strip().splitlines()]
                lines = lines[:i] + body_lines + lines[j:]
                return "\n".join(lines)
            i += 1
        return code

    @staticmethod
    def make_scaling_conditional(code: str) -> str:
        """
        Ensures any call to .scale_to_fit_width(arg) is safely guarded by
        'if hasattr(var, "width") and var.width > (arg): var.scale_to_fit_width(arg)'.
        Idempotent: collapses any existing duplicate 'if hasattr' guards and avoids
        re-wrapping lines that are already guarded.
        """
        pattern = r'if hasattr\(([a-zA-Z0-9_]+), "width"\) and \1\.width > \(([^)]+)\):\s*if hasattr\(\1, "width"\) and \1\.width > \(\2\):'
        while re.search(pattern, code):
            code = re.sub(pattern, r'if hasattr(\1, "width") and \1.width > (\2):', code)

        lines = code.splitlines()
        new_lines = []
        for line in lines:
            if ".scale_to_fit_width(" in line:
                prefix = line.split(".scale_to_fit_width(")[0].strip()
                if "if hasattr(" in line or prefix.startswith("if "):
                    new_lines.append(line)
                else:
                    m = re.match(r"^(\s*)([a-zA-Z0-9_]+)\.scale_to_fit_width\(([^)]+)\)(.*)$", line)
                    if m:
                        indent, var, arg, trailing = m.groups()
                        new_lines.append(f'{indent}if hasattr({var}, "width") and {var}.width > ({arg}): {var}.scale_to_fit_width({arg})')
                        trailing = trailing.strip()
                        if trailing:
                            if trailing.startswith('.'):
                                new_lines.append(f'{indent}{var}{trailing}')
                            else:
                                new_lines.append(f'{indent}{trailing}')
                    else:
                        new_lines.append(line)
            else:
                new_lines.append(line)
        return "\n".join(new_lines)

    @staticmethod
    def normalize_code_typography(code: str) -> str:
        """
        Normalizes typography, layout bounds, and syntax across generated Manim code:
        1. Cleans invalid 'stretch=True/False' erroneously placed inside VGroup(...) or Group(...).
        2. Clamps oversized MathTex font_size (>24) down to 20 so formulas match non-latex body text.
        3. Scales down oversized MathTex .scale(...) (>=0.65) to .scale(0.45) so LaTeX does not tower over surrounding text.
        4. Enforces uniform minimum font size: clamps microscopic text (size < 10) up to size=11.
        5. Enforces Content Header Ceiling: ensures content panels/containers sit strictly below header (clamps UP * 2.8+ to UP * 2.3).
        6. Enforces Left-Right separation: clamps left container width (<= 4.2) to prevent center-seam bleeding.
        """
        lines = code.splitlines()
        new_lines = []
        for line in lines:
            # 1. Clean stretch in VGroup and Group
            if ("VGroup(" in line or "Group(" in line) and "stretch=" in line:
                line = re.sub(r'(VGroup|Group)\((.*?),\s*stretch\s*=\s*(?:True|False)\)', r'\1(\2)', line)
                line = re.sub(r'(VGroup|Group)\((.*?)\s*stretch\s*=\s*(?:True|False),\s*', r'\1(\2', line)
                line = re.sub(r'(VGroup|Group)\(\s*stretch\s*=\s*(?:True|False)\s*\)', r'\1()', line)

            # 2. Normalize MathTex font sizing & scaling
            if "MathTex" in line:
                if "font_size" in line:
                    def sub_fs(m):
                        fs = int(m.group(1))
                        return "font_size=20" if fs > 24 else m.group(0)
                    line = re.sub(r'font_size\s*=\s*(\d+)', sub_fs, line)
                if ".scale(" in line:
                    def sub_sc(m):
                        val = float(m.group(1))
                        return ".scale(0.45)" if val >= 0.65 else m.group(0)
                    line = re.sub(r'\.scale\(\s*([0-9]*\.?[0-9]+)\s*\)', sub_sc, line)

            # 3. Typography Uniformity: Ensure minimum readable font size (>=6.0pt) without inflating small telemetry/sublabels
            if "CrispText(" in line and "size=" in line:
                def sub_tiny_size(m):
                    try:
                        sz = float(m.group(1))
                        if sz < 6.0:
                            return "size=6.0"
                    except Exception:
                        pass
                    return m.group(0)
                line = re.sub(r'size\s*=\s*(\d+(?:\.\d+)?)', sub_tiny_size, line)

            # 4. Header Ceiling Rule: Keep content strictly below header zone (ceiling y <= 2.4)
            if any(k in line for k in ["UP * 2.8", "UP * 2.9", "UP * 3.0", "UP * 3.1", "UP * 3.2"]):
                if not any(t in line for t in ["title", "dots", "line_start", "line_end", "header", "scene_title"]):
                    line = re.sub(r'UP\s*\*\s*(?:2\.8|2\.9|3\.0|3\.1|3\.2)', 'UP * 2.3', line)

            # 5. Left panel width clamp: prevent bleeding across center gutter into right column
            if any(k in line for k in ["left_macro", "left_panel", "s3_left_panel", "s4_left_panel"]):
                line = re.sub(r'width\s*=\s*(?:4\.[4-9]|5\.[0-9])', 'width=4.0', line)

            # 6. Screen right-edge boundary clamp: prevent elements from bleeding past x = 6.4
            if "hero_slot, RIGHT" in line:
                line = re.sub(r'next_to\(storefront\.hero_slot,\s*RIGHT[^\)]*\)', 'move_to(storefront.hero_slot.get_corner(UR) + LEFT * 1.1 + DOWN * 0.4)', line)

            new_lines.append(line)
        normalized = "\n".join(new_lines)
        normalized = re.sub(r'aligned_edge\s*=\s*(?:None|CENTER)', 'aligned_edge=ORIGIN', normalized)

        # 7. Dynamic product card height enforcement (prevents text spilling over bottom border)
        if "def create_product_card(" in normalized and "height=2.4" in normalized:
            normalized = normalized.replace("height=2.4", "height=max(2.6, content.height + 0.35)")
            # also clamp image height if not present
            if 'img.scale_to_fit_height' not in normalized:
                normalized = normalized.replace(
                    'if hasattr(img, "width") and img.width > (width - 0.4): img.scale_to_fit_width(width - 0.4)',
                    'if hasattr(img, "width") and img.width > (width - 0.4): img.scale_to_fit_width(width - 0.4)\n            if hasattr(img, "height") and img.height > 1.25: img.scale_to_fit_height(1.25)'
                )

        # 8. Callout annotation non-overlap: ensure text pointing to cards sits above cards rather than across them
        if "text_a.next_to(arrow_a, UP, buff=0.15).align_to(arrow_a, LEFT)" in normalized and "card_a" in normalized:
            normalized = normalized.replace(
                "text_a.next_to(arrow_a, UP, buff=0.15).align_to(arrow_a, LEFT)",
                "text_a.next_to(card_a, UP, buff=0.25).align_to(card_a, LEFT)\n        arrow_a = Arrow(start=text_a.get_bottom(), end=card_a.get_top(), color=C_RED, stroke_width=2, buff=0.08, max_tip_length_to_length_ratio=0.15)"
            )
            normalized = normalized.replace(
                "text_b.next_to(arrow_b, UP, buff=0.15).align_to(arrow_b, LEFT)",
                "text_b.next_to(card_b, UP, buff=0.25).align_to(card_b, LEFT)\n        arrow_b = Arrow(start=text_b.get_bottom(), end=card_b.get_top(), color=C_RED, stroke_width=2, buff=0.08, max_tip_length_to_length_ratio=0.15)"
            )

        # 9. Step 2 multi-heading overlap purge: ensure heading is removed when fallacy_sub enters
        if "self.remove(def_text," in normalized and "heading" not in normalized.split("self.remove(")[1].split(")")[0]:
            normalized = normalized.replace("self.remove(def_text,", "self.remove(heading, def_text,")

        # 10. Graph axis callout collision prevention (shift callout away from x-axis tip)
        if "dash_label.next_to(dashed_line.get_end(), UP, buff=0.3).align_to(dashed_line, RIGHT).shift(LEFT * 0.2)" in normalized:
            normalized = normalized.replace(
                "dash_label.next_to(dashed_line.get_end(), UP, buff=0.3).align_to(dashed_line, RIGHT).shift(LEFT * 0.2)",
                "dash_label.next_to(dashed_line.get_center(), UP, buff=0.35).shift(RIGHT * 1.5)"
            )
        # 11. Strip thumbnail recap scaling: remove unreadable .scale(0.1-0.35).to_corner(...) on recap notes
        normalized = re.sub(
            r'\.scale\(\s*0\.[1-3]\d*\s*\)\.to_corner\(\s*(?:UL|UR|DL|DR)\s*(?:,[^)]*)?\)',
            '.set_opacity(0)',
            normalized
        )
        normalized = re.sub(
            r'\.to_corner\(\s*(?:UL|UR|DL|DR)\s*(?:,[^)]*)?\)\.scale\(\s*0\.[1-3]\d*\s*\)',
            '.set_opacity(0)',
            normalized
        )

        return normalized

    @staticmethod
    def ensure_clean_step_transitions(code: str) -> str:
        """
        Automatically purges leaked or zombie mobjects (such as table cells highlighted
        via Indicate or submobjects) while strictly protecting persistent slide titles.
        """
        lines = code.split("\n")
        new_lines = []
        i = 0
        n = len(lines)
        
        while i < n:
            line = lines[i]
            new_lines.append(line)
            
            stripped = line.strip()
            if stripped == ")" or stripped.startswith(")"):
                j = len(new_lines) - 2
                found_play = False
                has_forbidden = False
                has_fadeout = False
                indent = ""
                while j >= 0 and (len(new_lines) - 2 - j) < 35:
                    prev_line = new_lines[j]
                    if "self.play(" in prev_line:
                        found_play = True
                        indent = prev_line[:len(prev_line) - len(prev_line.lstrip())]
                        if any(k in prev_line for k in ["FadeIn(", "Create(", "Write(", "Transform(", "ReplacementTransform(", "GrowFromCenter("]):
                            has_forbidden = True
                        if "FadeOut" in prev_line:
                            has_fadeout = True
                        break
                    if any(k in prev_line for k in ["FadeIn(", "Create(", "Write(", "Transform(", "ReplacementTransform(", "GrowFromCenter("]):
                        has_forbidden = True
                    if "FadeOut(" in prev_line:
                        has_fadeout = True
                    j -= 1
                
                if found_play and has_fadeout and not has_forbidden:
                    k = i + 1
                    while k < n and lines[k].strip() == "":
                        k += 1
                    if k < n:
                        next_line_stripped = lines[k].strip()
                        if "self.remove(" not in next_line_stripped:
                            has_new_title = (
                                "create_title(" in next_line_stripped or
                                re.match(r"^[a-zA-Z0-9_]*title[a-zA-Z0-9_]*\s*=", next_line_stripped)
                            )
                            if not has_new_title:
                                for look_ahead in range(k, min(k + 8, n)):
                                    la_line = lines[look_ahead].strip()
                                    if "create_title(" in la_line or re.match(r"^[a-zA-Z0-9_]*title[a-zA-Z0-9_]*\s*=", la_line):
                                        has_new_title = True
                                        break
                                    if la_line.startswith("self.play(") or la_line.startswith("self.wait("):
                                        break

                            if (next_line_stripped.startswith("# Presentation Step") or
                                next_line_stripped.startswith("# Step") or
                                has_new_title):
                                if has_new_title:
                                    # When a new title is defined in the upcoming step, purge previous titles completely!
                                    new_lines.append(f"{indent}self.remove(*self.mobjects)")
                                else:
                                    # Purge leaked mobjects across step transitions while strictly preserving persistent title
                                    new_lines.append(f"{indent}self.remove(*[m for m in self.mobjects if not getattr(m, 'is_title', False) and getattr(m, 'name', '') != 'title_group' and not getattr(m, 'is_persistent', False)])")
            i += 1
            
        return "\n".join(new_lines)

    @staticmethod
    def clamp_extreme_shifts(code: str) -> str:
        """
        Prevents hardcoded horizontal shifts from pushing elements beyond the 16:9 camera frame boundaries.
        """
        def sub_right_shift(m):
            val = float(m.group(1))
            if val > 6.2:
                return "RIGHT * 5.8"
            return m.group(0)

        def sub_left_shift(m):
            val = float(m.group(1))
            if val > 6.2:
                return "LEFT * 5.8"
            return m.group(0)

        code = re.sub(r'RIGHT\s*\*\s*(\d+\.?\d*)', sub_right_shift, code)
        code = re.sub(r'LEFT\s*\*\s*(\d+\.?\d*)', sub_left_shift, code)
        return code

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

    def generate_styling_corrections(self, config_data, topic_id):
        """
        Refines code scripts using Gemini 3.5 Flash with high thinking depth,
        incorporating styling rules and timestamped VLM layout directives.
        """
        print(f"  [Stage 20] Running generate_styling_corrections for {topic_id} ...")
        
        base_folder = config_data['base_folder']
        theme = config_data.get('theme', '')
        creative_context = config_data.get('creative_context', '')
        is_k12 = (
            theme == "k12" 
            or creative_context == "k12" 
            or "k12" in str(base_folder).lower() 
            or "ace_" in topic_id.lower() 
            or "english" in topic_id.lower()
            or "ss_" in topic_id.lower()
            or "grade_" in topic_id.lower()
        )

        # Simplilearn OSL 3.0 Standard Presentation Architecture
        title_instructions = """### SCENE TITLE & SIMPLILEARN OSL 3.0 PRESENTATION ARCHITECTURE

        Every scene must follow the standardized Simplilearn OSL 3.0 presentation architecture:

        1. TYPOGRAPHY & FONT STANDARDS (guidelines.md Section 6.3 & 8.1):
           - Font Family: **Open Sans** exclusively (weight=BOLD for headers/titles, NORMAL/REGULAR for body).
           - Primary Content Text Color: `#404040` (Dark Charcoal).
           - Never use Poppins, Inter, or Arial.
           - NO ALL-CAPS: Titles and headers must use Title Case (5-7 words per Chicago Manual of Style). Body and bullets use Sentence Case.
           - Complete sentences end with a period (.); incomplete phrases and bullet points do NOT end with a period.

        2. PERSISTENT TITLE TREATMENT (guidelines.md Section 8):
           - In Layout 70 (Split Left SME + Right Content Area):
             Title and category header reside in the right safe content zone (`x >= -1.20`):
             `cat_pill = Text("Topic Category | Module Focus", font="Open Sans", font_size=12, weight=SEMIBOLD, color="#64748B")`
             `main_title = CrispText("<EXISTING SCENE TITLE>", size=24, font="Open Sans", weight=BOLD, color="#404040")`
             Main title is aligned consistently and remains persistent throughout the scene.
           - In Layout 20 (20% Top-Right SME PiP):
             Top-Left Title Pill at `[-6.087, 3.519, 0]` and Lead-In Box at `[0.210, 2.557, 0]`.
             COLLISION RULE: Lead-in line's right edge MUST terminate at or left of x = +4.267 so it never overlaps the 20% SME PiP at `x ∈ [+4.267, +7.111]`.
           - In Splash / Title Screen (Layout 5):
             Centered capsule pill at `(0, -0.022)`, width=11.51, height=1.384, corner_radius=0.692, Open Sans Bold 45px, White `#FFFFFF`.
           - For standard content scenes:
             Clean top title in Open Sans Bold, size=24 to 26, color `#404040` (or `#1E293B`), optionally underlined by a subtle blue band line (`#2C81FE`, stroke_width=2.5).
             STRICT PROHIBITION OF 5 ACCENT DOTS: NEVER use 5 colored dots (purple, yellow, red, light blue, dark blue) or legacy dot decorations!

        3. APPROVED 10-COLOR INFOGRAPHIC PALETTE & SYSTEM UI (guidelines.md Section 6.4):
           - 10 Approved Colors: Mint (`#8ECDB7`), Sky Blue (`#62B7E4`), Steel Blue (`#7EA2C8`), Lavender (`#9B99C7`), Mustard Gold (`#DDB945`), Warm Amber (`#E6A157`), Coral (`#E58F6D`), Warm Tan (`#B88968`), Dusty Rose (`#D98CA1`), Soft Lilac (`#C1A5C6`).
           - Focus Highlight Stroke: `#F78908` (Orange), thickness `3 px` (`stroke_width=3`), draw time `1.0 second`.
           - Left Blue Accent Band: `#2C81FE`.
           - Containers: `#FFFFFF` or soft `#F8FAFC`, corner_radius=0.074 (10 px).
           - Content Text: `#404040`.
           - NAVY BLUE PROHIBITION: Navy Blue (#0B3C5D, #06152B, #0A2540, NAVY) is strictly PROHIBITED and is NOT part of the Simplilearn palette!
           - DO NOT use 3D shapes, dotted lines, drop shadows, or thick outlines.

        4. AUDIO-VISUAL ALIGNMENT & COGNITIVE LOAD:
           - On-screen text (OST) must be distilled into keywords and short anchor phrases—never duplicate spoken sentences verbatim.
           - Only ONE highlight at a time (#F78908, 3px stroke, 1.0s draw time).

        5. CANVAS BALANCING, CARD CONTAINMENT & ZERO MINIATURE BLOBS:
           - Strict Card Border Containment: Text and images inside cards must have min 0.25 margin from card borders. Never allow text to collide with or cross card borders. Container heights must dynamically fit their text.
           - Zero Miniature Scaled Blobs: When transitioning between steps, completely fade out previous diagrams (`FadeOut(...)`). NEVER shrink complex diagrams into miniature illegible blobs (`.scale(0.20)`).
           - All presentation content below the header line MUST be centered horizontally on screen (`set_x(0)`) and centered vertically in the content arena (`y ≈ -0.45`). Never leave one half of the screen blank.
           - Maintain clear padding (`buff >= 0.25`) between all cards, badges, arrows, and labels to prevent visual overlap. Badges must NEVER be positioned with `badge.next_to(title, DOWN)` (which jams them against the left border); always center them or position them inside content cards.

        6. STRICT TEACHER OVERLAY CLEARANCE & ZERO UNSPOKEN MATHEMATICAL EQUATIONS:
           - In Layout 70 (Presenter on left: `x ∈ [-7.11, -1.22]`): ALL text, cards, titles, and diagrams MUST be positioned in the right content zone (`x >= -1.0`, centered at `x = 2.46`, max width 8.5). NEVER place any element on the left side (`x < -1.0`).
           - In Layout 20 (Presenter in top-right PiP: `x ∈ [+4.267, +7.111], y ∈ [+2.400, +4.000]`): Top-right corner must be kept completely clear. Any title or element with `y > 2.0` must stay at or left of `x = 4.20`.
           - ZERO UNSPOKEN MATHEMATICAL EQUATIONS: Remove any MathTex equations (e.g. U(a) = f(...), d(S_t, G) = ...). Replace with clean Open Sans conceptual text and visual cards.
           - REMOVE ALL UNNECESSARY CONTENT NOT SPOKEN: Never display steps, concepts, or labels that the speaker does not mention."""

        google_client = genai.Client(api_key=self.google_api_key)
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        prompt_dir = os.path.join(base_folder, "prompt_context_and_guidelines")
        storyboard_file = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(storyboard_file):
            storyboard_file = f"{base_folder}/CGI_Input.json"
        refined_scene_codes_dir = f"{base_folder}/manim_extracted_codes"

        styled_scenes_dir = f"{base_folder}/manim_styled_codes"
        font_guidelines_file = os.path.join(prompt_dir, "font_guidelines.txt")
        if not os.path.exists(font_guidelines_file):
            font_guidelines_file = f"{base_folder}/font_guidelines.txt"
        specific_suggestions_folder = f"{base_folder}/specific_suggestions_vlm"
        vlm_fixing_dir = f"{base_folder}/vlm_fixing_stage"

        font_guidelines = ""
        if os.path.exists(font_guidelines_file):
            with open(font_guidelines_file, 'r', encoding="utf-8") as f:
                font_guidelines = f.read()
        if not font_guidelines:
            alt_font = [
                f"{base_folder}/Simplilearn_font_guidelines.txt",
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "Guidelines", "Simplilearn_font_guidelines.txt")
            ]
            for cand in alt_font:
                if os.path.exists(cand):
                    with open(cand, 'r', encoding="utf-8") as f:
                        font_guidelines = f.read()
                    break

        color_palette = ""
        color_palette_file = os.path.join(prompt_dir, "color_palette_guidelines.txt")
        if not os.path.exists(color_palette_file):
            color_palette_file = f"{base_folder}/color_palette_guidelines.txt"
        if os.path.exists(color_palette_file):
            with open(color_palette_file, 'r', encoding="utf-8") as f:
                color_palette = f.read()
        if not color_palette:
            alt_color = [
                f"{base_folder}/color_guidelines.txt",
                os.path.join(os.path.dirname(__file__), "helpers", "guidelines", "color_guidelines.txt"),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "Guidelines", "color_guidelines.txt")
            ]
            for cand in alt_color:
                if os.path.exists(cand):
                    with open(cand, 'r', encoding="utf-8") as f:
                        color_palette = f.read()
                    break

        os.makedirs(styled_scenes_dir, exist_ok=True)

        with open(storyboard_file, 'r', encoding="utf-8") as f:
            storyboard = json.load(f)

        is_executive = is_executive_topic(base_folder=base_folder, topic_id=topic_id)
        archetype = get_visual_archetype(base_folder=base_folder, topic_id=topic_id)
        print(f"[Stage 20] Topic {topic_id} detected visual archetype: '{archetype}' (is_executive={is_executive})")

        if is_executive:
            layout_rules = """
        - CENTERED COMPOSITION & UNIFORM CANVAS DISTRIBUTION (EXECUTIVE STANDARD):
          1. CENTERED ARENA: All presentation content below the header MUST be centered horizontally (set_x(0)) and vertically in the main arena (bounded strictly by y in [-2.55, 1.70] and x in [-5.8, 5.8], max diagram height 3.8). Minimal dead white space: cards and visual models must be sized to fill the space cleanly and harmoniously.
          2. STRICT ANTI-OVERLAP & BUFFER MANDATE:
             * Never place badges with `badge.next_to(title, DOWN)` which jams badges into the top-left margin; center badges horizontally: `badge.move_to(UP * 2.1).set_x(0)`.
             * Arrow annotations and condition text must never overlap arrow lines. Always position them above or below arrows with `buff >= 0.25`.
             * Prevent border collisions: Text inside containers or cards must have min 0.3 internal margin.
             * No premature fadeouts: Visual context, bins, and cards must remain on screen while narration is speaking.
          3. STRICT CONTAINER WIDTH CLAMPING (MANDATORY FOR EXECUTIVE 2-COLUMN LAYOUTS):
             * Left Panel (width 4.8 to 5.2, centered ~ x = -2.8): Inside left panel, structured cards, definitions, and equations must have width <= 4.6 (or 3.3 for sub-cards).
             * Right Panel (width 4.8 to 5.2, centered ~ x = +2.8): Visual model (diagrams, bins, graphs).
             * Together, `VGroup(left_col, right_col).move_to(DOWN * 0.45)` fills the screen symmetrically without empty margins.
          4. CONTAINER CONTAINMENT & MARGINS: Any section title, sub-heading, or text inside a macro container must be positioned INSIDE the container relative to its inner bounds. Never allow text to collide with container borders.
"""
        elif archetype == "k12_education":
            layout_rules = """
        - K-12 ENGAGING NARRATIVE & OPEN-CANVAS SPATIAL RULES:
          1. OPEN CANVAS FREEDOM: Allow full-canvas, centered, or multi-element layouts for illustrations, community scenes, character callouts, and science models. Do NOT force a rigid corporate 2-column macro container unless the topic specifically presents a side-by-side comparison.
          2. LARGE LEGIBLE TYPOGRAPHY: Ensure section headings are 22-26pt and explanatory labels are 15-18pt so younger students can read effortlessly.
          3. DYNAMIC CONTAINER WIDTHS: Cards and callout bubbles can span natural widths (width 3.5 to 8.0) as needed by the content, with generous padding (min 0.2).
          4. SCREEN BOUNDS: All elements must stay strictly within safe 16:9 canvas boundaries: x in [-6.4, 6.4], y in [-3.3, 3.2].
"""
        elif archetype == "stem_math":
            layout_rules = """
        - MATHEMATICAL & GEOMETRICAL SPATIAL RULES:
          1. MAXIMIZE CANVAS FOR PLOTS & GEOMETRY: Allow Axes, NumberPlane, polygons, and geometric constructions to span up to 10.0 width and 5.5 height across the screen. Do NOT cram geometric proofs into small sub-column cards.
          2. CENTERED FIGURES: Center geometric shapes (triangles, circles, coordinate graphs) prominently in the main viewport.
          3. VERTICAL DERIVATIONS: Stack derivation lines vertically with aligned equal signs. Ensure MathTex is font_size 18-22 with clear vertical line spacing (buff=0.25).
          4. GEOMETRY LABELS: Position vertex labels, angle arcs, and callouts cleanly outside the shape boundaries with buff=0.25 to 0.35. Labels must NEVER overlap line strokes or shape interiors.
"""
        elif archetype == "promo_vertical":
            layout_rules = """
        - 9:16 MOBILE PORTRAIT RULES:
          1. Canvas is 720x1280. Elements must stay strictly within x in [-3.0, 3.0], y in [-5.5, 5.5].
          2. Single vertical stack layout with bold, centered kinetic typography and a single hero graphic in the center.
"""
        else:
            layout_rules = """
        - GENERAL BALANCED CANVAS RULES:
          1. Spatial bounds: Stay strictly within x in [-6.4, 6.4], y in [-3.3, 3.2].
          2. Generous breathing room: Keep all content strictly above DOWN * 3.3 and below UP * 3.2.
"""

        if is_executive:
            ui_architecture_section = """
        ### KINETIC VECTOR ARCHITECTURE & STRICT PROHIBITION OF PPT CARDS:
        To produce final renders that look like world-class kinetic vector animations rather than static PowerPoint slides, adhere strictly to procedural vector mechanics:

        1. STRICT PROHIBITION OF PPT CARDS & CONTAINERS:
           - Strictly DO NOT wrap statements, concepts, metrics, or comparisons in rounded-rectangle container cards, pill boxes, or floating card stacks!
           - Strictly DO NOT build vertical stacks of `create_card`, `create_yellow_card`, or `RoundedRectangle` text boxes! That looks like a 2005 PowerPoint slide!
           - Never place static cards or bullet lists on the screen.

        2. PROCEDURAL MANIM VECTOR MECHANISMS:
           - Build real, living Manim vector geometry: mechanical balance scales with swinging pans, rotating radar sweeps, conduits with flowing particles, neural halo pulses, interactive dials with oscillating needles, and branching state machines!
           - Minimal Punchy Text: Micro-labels only (1-3 words max, e.g. "Max Efficiency", "Low Cost", "Perception"). Zero paragraphs, zero walls of text, zero descriptive sentences inside boxes!
           - Continuous Motion: Infuse living motion (flowing dots along paths, pulsing rings, rotating reticles) so the screen is never frozen or static during narration.

        3. CRITICAL MANIM SIZING & SPATIAL RULES:
           - NEVER use `.set_width(w).set_height(h)` in Manim! In Manim, `.set_height()` scales BOTH width and height proportionally, overwriting width! Always set width and height in the constructor: `RoundedRectangle(width=w, height=h, corner_radius=r)` or use `.stretch_to_fit_width(w).stretch_to_fit_height(h)`!
           - LEFT COLUMN SAFE ZONE: The left column panel spans `x in [-6.4, -2.2]` (width = 4.2). Any vector elements placed in the left panel MUST NOT exceed `width = 3.3`!
           - RIGHT COLUMN BOUNDARY CLAMP: The right column safe zone spans `x in [-0.6, 6.8]` (width <= 7.4). Any diagram, composite group, or mechanism placed on the right side MUST NEVER cross left of `x = -0.6` or right of `x = 6.8`.
           - 2-COLUMN SUBPANEL CLAMP: Any sub-mechanism in the right column MUST have `width <= 3.3` each! Never use `width=3.8`!
           - If a VLM directive asks for a large buffer (e.g. `buff=2.2`) between sub-diagrams, DO NOT apply a huge buffer that pushes elements into the left column! Instead, scale down the sub-diagrams (`.scale(0.68)`), use a safe buffer (`buff=0.35` to `0.5`), and center the entire group at right_col_center (`x ~ 3.1` to `3.4`).
"""
        elif archetype == "stem_math":
            ui_architecture_section = """
        ### MATHEMATICAL & GEOMETRICAL UI ARCHITECTURE:
        1. MAXIMIZE CANVAS FOR MATHEMATICAL OBJECTS:
           - Allow geometric diagrams, proof figures, and coordinate axes (Axes, NumberPlane) to occupy full central canvas width (up to 10.0 units) and height (up to 5.5 units).
           - Do NOT compress plots into 3.3 sub-column boxes.
        2. THEOREM & FORMULA CARDS:
           - Use `create_card` for theorem statements, problem definitions, and key takeaways with dynamic width (width=4.5 to 8.5) and dynamic height fitting text.
        3. CRITICAL MANIM SIZING:
           - NEVER use `.set_width(w).set_height(h)` in Manim! Always set constructor width and height or use `.stretch_to_fit_width(w).stretch_to_fit_height(h)`.
"""
        elif archetype == "k12_education":
            ui_architecture_section = """
        ### K-12 ENGAGING STORYTELLING UI ARCHITECTURE:
        1. OPEN CANVAS & PEDAGOGICAL COMPOSITION:
           - Center narrative illustrations, community scenes, character callouts, and science models openly across the screen.
           - Avoid rigid corporate 2-column macro container splits unless directly contrasting two concepts.
        2. CALLOUT BUBBLES & NARRATIVE CARDS:
           - Use `create_card` with natural widths (3.5 to 8.0) and colorful fills, large font sizes (15-18pt body, 22-26pt headings).
        3. CRITICAL MANIM SIZING:
           - NEVER use `.set_width(w).set_height(h)` in Manim! Always set constructor width and height or use `.stretch_to_fit_width(w).stretch_to_fit_height(h)`.
"""
        elif archetype == "promo_vertical":
            ui_architecture_section = """
        ### 9:16 MOBILE PORTRAIT UI ARCHITECTURE:
        1. 9:16 CANVAS RULES:
           - Single vertical column stack with bold kinetic text.
           - Canvas is 720x1280. Elements must stay strictly within x in [-3.0, 3.0], y in [-5.5, 5.5].
"""
        else:
            ui_architecture_section = """
        ### GENERAL BALANCED UI ARCHITECTURE:
        1. SPATIAL BOUNDS & MARGINS:
           - Stay strictly within x in [-6.4, 6.4], y in [-3.3, 3.2].
        2. CRITICAL MANIM SIZING:
           - NEVER use `.set_width(w).set_height(h)` in Manim! Always set constructor width and height or use `.stretch_to_fit_width(w).stretch_to_fit_height(h)`.
"""

        system_prompt = f"""
        ### ROLE

        You are an expert Visual Debugging and Manim Refinement Engineer.

        Refine the existing Manim scene code by:
        1. Using visual reasoning and code-level intelligence to understand and resolve the underlying problems reported in the VLM review.
        2. Improving visual styling according to client branding (colors, typography, nested containers).
        3. Ensuring the resulting script is 100% executable and error-free in Manim Community.

        ---

        {title_instructions}

        ---

        ### CORE CONSTRAINTS & ARCHITECTURAL LAYOUT RULES (Archetype: {archetype}):
        - Executable correctness: The code must be 100% syntactically valid and executable in Manim Community.
        - Preserve the `## Presentation Step N` comments in the code so timing synchronization can locate each step.
        - Preserve all mathematical formulas and narrative educational content.
        - Use standard animation durations (`run_time=1` to `run_time=2`) for any added fade-outs or transitions to maintain smooth pacing.
        - Contrast & Styling: Adhere to the provided branding colors and typography guidelines.
        - NO ALL CAPS (TITLE CASE & SENTENCE CASE): All on-screen text, titles, subtitles, headers, card labels, and tags must NEVER be written in ALL CAPS. Use Title Case (Camel Case) for titles and headers; use Sentence Case for body text and descriptions.
        - REDUCE GREEN USAGE AS MUCH AS POSSIBLE: Green (#34A853 / #2D6A4F) must be minimized across all scenes. Never style large card backgrounds or headings with green. Confine green strictly to tiny micro-icons (e.g. checkmark).
        - APPROVED INFOGRAPHIC PALETTE & SYSTEM UI (guidelines.md Section 6.4):
          Use the 10 approved infographic colors: Sky Blue (#62B7E4), Steel Blue (#7EA2C8), Lavender (#9B99C7), Mint (#8ECDB7), Warm Amber (#E6A157), Mustard Gold (#DDB945), Coral (#E58F6D), Warm Tan (#B88968), Dusty Rose (#D98CA1), Soft Lilac (#C1A5C6).
          Focus Highlight Stroke: #F78908 (3 px stroke / stroke_width=3, 1.0s draw time). Left blue band: #2C81FE. Primary Content Text: #404040.
          NAVY BLUE IS STRICTLY PROHIBITED: Navy Blue (#0B3C5D, #06152B, #0A2540, NAVY) is NOT part of the palette!
        - HIGH CONTRAST & LEGIBILITY (guidelines.md Section 6.2):
          All text and MathTex formulas on light backgrounds (#F0F4F8, #FFFFFF, #F8FAFC) MUST use high-contrast dark charcoal (#404040). White text is only permitted inside verified Brand Blue (#2C81FE) or dark accent badges.
        - LINE & ARROW ROUTING RULES:
          Connecting lines and arrows must never cut through or touch text boxes, callout cards, or badges. All callout cards, badges, and pills MUST have 'fill_opacity=1.0' (opaque background) and '.set_z_index(20)' so plot curves, axis lines, and trajectories passing behind them are occluded and do not cut through card text. Maintain at least 0.35 padding from axis top/ends.

        - ADVISORY NATURE OF VISUAL LAYOUT DIRECTIVES (CRITICAL):
          Visual layout directives are purely ADVISORY (text guidance), not a compiler. They inspect visual snapshots and suggest improvements, but do not execute code or verify mathematical bounding geometry.
          THEREFORE: You must NEVER blindly apply a mechanical scale factor or coordinate shift suggested in directives if it violates layout bounds! Instead, analyze the actual visual layout problem reported, reason about the geometry, take an engineering decision, and implement visual corrections that keep all elements strictly inside their respective container panels.
{layout_rules}

        - PRESENTATION STEP SLIDE TITLES (ALWAYS VISIBLE & ANIMATED):
          * EVERY Presentation Step (Step 1, Step 2, Step 3, Step 4) MUST have a clearly visible slide title at the top left.
          * In Step 1: Initialize the title with `title_group = create_title("<STEP 1 TITLE>")` and animate it: `self.play(FadeIn(title_group, shift=DOWN*0.1), run_time=0.8)`.
          * In Subsequent Steps (Step 2, 3, 4):
            - If the step introduces a new topic/focus, seamlessly transition the title:
              `new_title_group = create_title("<NEW STEP TITLE>")`
              `self.play(FadeOut(title_group), FadeIn(new_title_group, shift=DOWN*0.1), run_time=0.4)`
              `title_group = new_title_group`
            - If the main topic remains identical, DO NOT fade out or remove `title_group`. Keep it on screen.
            - NEVER create a title variable (e.g. `title2 = create_title(...)` or `title_2 = ...`) without immediately passing it to `self.play(FadeIn(...))`! Any title variable you define MUST be animated onto the screen.

        - DYNAMIC CARD & PRODUCT CONTAINER CONTAINMENT (NO TEXT OVERFLOWING BORDERS):
          * All cards (`create_card`, `create_product_card`, `create_feature_card`) MUST dynamically calculate background height based on their children:
            `calc_h = max(height if height else 0.65, content.height + 2 * pad_y)`
          * When creating product cards with images, titles, and subtitles:
            - Clamp image size: `if hasattr(img, "height") and img.height > 1.25: img.scale_to_fit_height(1.25)` and `if hasattr(img, "width") and img.width > (width - 0.4): img.scale_to_fit_width(width - 0.4)`.
            - Set card height dynamically: `card_h = max(2.6, content.height + 0.35)`.
            - Subtitles, prices, and tags MUST NEVER spill across the bottom border of the card!

        - ANNOTATIONS & CALLOUT PLACEMENT (NO OVERLAYS ON CARDS/IMAGES):
          * Annotation text, callouts, and pointer arrows must NEVER overlap or sit on top of product cards, images, or diagram nodes!
          * Position callout text either directly ABOVE the card (`next_to(card, UP, buff=0.25)`), or outside the card's bounding box (`next_to(card, LEFT, buff=0.35)` or `next_to(card, RIGHT, buff=0.35)`).
          * NEVER align wide multi-line text to the start of an arrow pointing inward toward a card if the text width causes it to cross over the card.

        - LEFT PANEL MULTI-STEP REPLACEMENT RULE:
          * When a new presentation step updates the content inside `left_container` / `left_panel`, ALL previous headings, text, cards, and labels inside the left panel MUST be included in `FadeOut` AND explicitly removed via `self.remove(...)` before new step elements enter.
          * NEVER place new text or cards at `left_container.get_corner(UL)` without first removing the previous step's heading!

        - MANDATORY STEP LIFECYCLE FADEOUT (NO GHOST CLUTTER):
          At every `## Presentation Step N` transition, you MUST explicitly FadeOut ALL visual entities from preceding steps that are no longer part of the active step.
          Never assume elements disappear on their own! If Step 1 or 2 introduced nodes, circles, badges, arrows, connector lines, highlight boxes, or cards, and Step 3 transitions to a new concept or sub-case, EVERY one of those old objects MUST be included in the initial self.play(FadeOut(...)) call AND removed via self.remove(...). No old diagram pieces or badges from earlier steps may linger into later steps to cause clutter or collisions.
          * However, persistent structures (main title, macro background containers, or active step reference panels) MUST persist.
        - ZERO BLANK SCREEN MANDATE (NO EMPTY WHITE SCREEN DURING NARRATION):
          * The canvas must NEVER be left empty or blank during spoken narration!
          * Visual diagrams, nodes, macro containers, and structured cards MUST persist on screen while the voiceover explains the concepts.
          * NEVER call `FadeOut` or `remove` on all elements before a `self.wait(...)`.
          * If an accent element (like a temporary highlight or question mark) fades out, the underlying diagram and context cards MUST remain visible!
        - STRUCTURED TEXT CARDS ACCOMPANYING VISUAL MODELS (SAMPLE STANDARD):
          * Pair every visual model with structured text cards: Top Hypothesis/Problem Banner, Left-column formulation cards with bold headers, or Step Cards.
          * Do NOT display bare isolated geometric shapes without pedagogical textual anchors.

        - VERTICAL SCREEN BOUNDARY CLAMP & CONTENT CEILING (y in [-3.5, +1.7]):
          * The canvas vertical range is strictly y in [-4.0, +4.0].
          * CEILING: The executive title & subtitle occupy y in [1.8, 3.8] in the UL corner. Therefore, the top edge of all content panels, dashboards, containers, cards, tables, and diagrams MUST sit strictly at or below y = +1.7 (e.g. `move_to([0, -0.65, 0])`). NEVER allow any content top edge to exceed y = 1.7! If a container has height >= 4.0, position it at y <= -0.65.
          * FLOOR: Elements must stay above y = -3.5 so that brackets, footnotes, and cards are never pushed off the bottom of the screen.

        - LEFT AND RIGHT SIDES CLEANLY DISTINGUISHED (NO BLEEDING / GUTTER RULE):
          * The 16:9 canvas (14.22 width) MUST maintain a strict two-column spatial boundary with an explicit visual gutter:
            - Left Column: x in [-6.6, -2.4] (width <= 4.0, centered ~ x = -4.5). Cards width = 3.3.
            - Visual Gutter: Open buffer zone from x = -2.4 to x = -1.8 (width >= 0.6) with ZERO elements crossing.
            - Right Column: x in [-1.8, +6.4] (width <= 7.8, centered ~ x = +2.3).
            - Elements from the left column must NEVER bleed across the gutter into the right column!
            - Elements in the right column (storefronts, pills, tables) must NEVER exceed x = +6.4 (camera boundary cutoff).
          * SIDE CALLOUT BUDGET: If a central diagram has callout cards placed to its LEFT or RIGHT, the central diagram width must be <= 7.6 so side tags never clip past |x| = 6.4.
          * MULTI-COLUMN CONTAINER RULE: Inside cards, tiers, or boxes, NEVER place multiple text items (e.g. tier label AND bullet list) directly at the center with .move_to(bg). Use separate columns: e.g. label on the left, bullet column arranged vertically in the middle, and tags/timestamps on the right, or arrange them horizontally with VGroup(...).arrange(RIGHT).

        - EXPLANATORY ANNOTATION TEXT & TAKEAWAYS MANDATE (CLIENT MANDATE):
          * Every presentation step MUST feature informative annotation text, takeaway banners, or explanatory insight callouts (e.g. 1-2 line takeaway pill or card with size=14-16 font) explaining the visual demonstration or formula.
          * NEVER leave diagrams, graphs, or equations bare without textual context.
          * Ensure annotations have positive padding (buff >= 0.25) and do not overlap diagrams or borders.
        - ATOMIC HIGHLIGHT HELPER PATTERN: When creating highlight boxes, pills, or tags (e.g. amber highlight rectangles behind text/math), ALWAYS bundle both the text mobject and the background into a single VGroup (e.g., def create_highlighted_text(text, size=16, color=C_DARK_BLUE, bg_color=C_WARM_AMBER): txt = CrispText(text, size=size, color=color); bg = BackgroundRectangle(txt, color=bg_color, fill_opacity=1, buff=0.08); return VGroup(bg, txt)). NEVER instantiate a BackgroundRectangle without including its text mobject in the group!
        - STRICT MANDATE ON UNIFORM TYPOGRAPHY & MULTI-LINE TEXT WRAPPING:
          1. PROFESSIONAL FONT SIZE HIERARCHY:
             - Slide Title: 28pt bold at top-left (UL, buff=0.4).
             - Subtitles, Card Headers & Major Callouts: 16pt to 18pt bold.
             - Body Text, Descriptions & Explanations: STRICTLY 14pt to 16pt (NEVER below 13pt! Microscopic 10-12pt text is strictly forbidden).
             - Standalone Equations & Formulas (MathTex): ALWAYS specify font_size=22 to 26 (NEVER below 20pt!).
             - Inline Math: ALWAYS font_size=18 to 20 to match adjacent 14-16pt text.
             - Badges, Table Data & Status Indicators: 12pt to 13pt bold.
          2. STRICT UNIFORM FONT SIZING ACROSS SIBLING BOXES & SHAPES:
             - All text inside cards, boxes, flowchart shapes, and cells MUST have the same uniform font size (13pt–15pt).
             - NEVER scale down text to fit a narrow box while neighbor boxes remain larger, and NEVER force text to stretch across the full width of a container.
             - If any statement or explanation exceeds the width of its container, NEVER compress it on a single line using .scale_to_fit_width(...) down to tiny unreadable text!
             - ALWAYS wrap the text across 2 or 3 lines using explicit `\n` linebreaks while preserving font_size=14!
             - The enclosing card height must dynamically expand: `calc_h = max(0.65, content.height + 2 * pad_y)`.
          3. STRICT ANTI-OVERLAP CANVAS ARCHITECTURE:
             - Header Zone (y in [2.8, 3.6]): Reserved EXCLUSIVELY for the Slide Title at UL.
             - Central Content Arena (y in [-3.2, 2.7]): Dedicated workspace for diagrams, cards, comparison columns, and equations. Over 5.5 units of vertical freedom. DO NOT cram diagrams between top and bottom banners.
             - Bounding Box Clearance: Every mobject must maintain clear clearance (buff >= 0.25). Callouts must sit strictly in empty whitespace and NEVER cross through arrows, lines, or adjacent cards.
          4. MAXIMIZE CANVAS UTILIZATION (NO DEAD WHITE SPACE VOIDS): The 16:9 canvas provides 14.22 width x 8.0 height. Macro-containers, cards, and diagrams must be generously proportioned (e.g. 4.8 to 5.6 width for cards in split-screen layouts; 9.6 to 10.5 width for full tables; vertical spans from y = -2.2 to +1.8). Never leave massive empty voids on the bottom or side margins.
          5. GRAPH AXES & FUNCTION PLOT LIFECYCLE:
             - ALWAYS position Axes (e.g. `axes.move_to(...)` or arrange inside its parent VGroup) BEFORE evaluating `axes.plot(...)` or `axes.c2p(...)`. Plotting curves while axes are at ORIGIN will cause curve points to be misaligned when axes are moved later!
             - Mandatory Step Lifecycle Fadeout: When transitioning to a new step, all plotted curves (`axes.plot(...)`), annotations, and data points MUST be explicitly included in `FadeOut(...)` (or grouped together in the container `VGroup`). Never leave orphaned curves or annotations floating on screen in later steps!
          6. NO `stretch=True` INSIDE `VGroup(...)`: `stretch=True` belongs only on `SurroundingRectangle(...)` or `.surround()`, NEVER inside `VGroup(...)` which crashes with `TypeError`.
          7. CLEAN STEP TRANSITIONS (NO GHOST / ZOMBIE MOBJECTS): When transitioning between presentation steps after fading out previous step mobjects, always call `self.remove(*self.mobjects)` immediately after `self.play(FadeOut(...))` to eliminate any lingering sub-mobjects or indicated elements.
          8. TABLE HEADER CONTRAST: If table column headers use white text (`C_WHITE`), they MUST be backed by an explicit dark background rectangle (e.g. `C_DARK_BLUE` with `height=table.get_rows()[0].height + 0.18`). Never leave white header text floating on a white canvas.

{ui_architecture_section}

        - Output ONLY the raw executable Python code. No markdown fences, no introductory or concluding conversational text.

        ---

        ### OUTPUT

        Return only the modified Manim code.
        No explanations.
        No comments.
        """

        system_prompt_dynamic = f"""
        ### ROLE

        You are an expert Visual Debugging and Manim Refinement Engineer.

        Refine the existing Manim scene code by:
        1. Using visual reasoning and code-level intelligence to understand and resolve the underlying problems reported in the VLM review.
        2. Improving visual styling according to client branding (colors, typography, nested containers).
        3. Ensuring the resulting script is 100% executable and error-free in Manim Community.

        ---

        {title_instructions}

        ---

        ### CORE CONSTRAINTS & ARCHITECTURAL LAYOUT RULES:
        - Executable correctness: The code must be 100% syntactically valid and executable in Manim Community.
        - Preserve the `## Presentation Step N` comments in the code so timing synchronization can locate each step.
        - Preserve all mathematical formulas and narrative educational content.
        - Use standard animation durations (`run_time=1` to `run_time=2`) for any added fade-outs or transitions to maintain smooth pacing.
        - Contrast & Styling: Adhere to the provided branding colors and typography guidelines.
        - NO ALL CAPS (TITLE CASE & SENTENCE CASE): All on-screen text, titles, subtitles, headers, card labels, and tags must NEVER be written in ALL CAPS. Use Title Case (Camel Case) for titles and headers; use Sentence Case for body text and descriptions.
        - REDUCE GREEN USAGE AS MUCH AS POSSIBLE: Green (#34A853 / #2D6A4F) must be minimized across all scenes. Never style large card backgrounds or headings with green. Confine green strictly to tiny micro-icons (e.g. checkmark).
        - APPROVED INFOGRAPHIC PALETTE & SYSTEM UI (guidelines.md Section 6.4):
          Use the 10 approved infographic colors: Sky Blue (#62B7E4), Steel Blue (#7EA2C8), Lavender (#9B99C7), Mint (#8ECDB7), Warm Amber (#E6A157), Mustard Gold (#DDB945), Coral (#E58F6D), Warm Tan (#B88968), Dusty Rose (#D98CA1), Soft Lilac (#C1A5C6).
          Focus Highlight Stroke: #F78908 (3 px stroke / stroke_width=3, 1.0s draw time). Left blue band: #2C81FE. Primary Content Text: #404040.
          NAVY BLUE IS STRICTLY PROHIBITED: Navy Blue (#0B3C5D, #06152B, #0A2540, NAVY) is NOT part of the palette!
        - HIGH CONTRAST & LEGIBILITY (guidelines.md Section 6.2):
          All text and MathTex formulas on light backgrounds (#F0F4F8, #FFFFFF, #F8FAFC) MUST use high-contrast dark charcoal (#404040). White text is only permitted inside verified Brand Blue (#2C81FE) or dark accent badges.
        - LINE & ARROW ROUTING RULES:
          Connecting lines and arrows must never cut through or touch text boxes, callout cards, or badges. All callout cards, badges, and pills MUST have 'fill_opacity=1.0' (opaque background) and '.set_z_index(20)' so plot curves, axis lines, and trajectories passing behind them are occluded and do not cut through card text. Maintain at least 0.35 padding from axis top/ends.

        - ADVISORY NATURE OF VISUAL LAYOUT DIRECTIVES (CRITICAL):
          Visual layout directives are purely ADVISORY (text guidance), not a compiler. They inspect visual snapshots and suggest improvements, but do not execute code or verify mathematical bounding geometry.
          THEREFORE: You must NEVER blindly apply a mechanical scale factor or coordinate shift suggested in directives if it violates layout bounds! Instead, analyze the actual visual layout problem reported, reason about the geometry, take an engineering decision, and implement visual corrections that keep all elements strictly inside their respective container panels.

        - PRESENTATION STEP SLIDE TITLES (ALWAYS VISIBLE & ANIMATED):
          * EVERY Presentation Step (Step 1, Step 2, Step 3, Step 4) MUST have a clearly visible slide title at the top left.
          * In Step 1: Initialize the title with `title_group = create_title("<STEP 1 TITLE>")` and animate it: `self.play(FadeIn(title_group, shift=DOWN*0.1), run_time=0.8)`.
          * In Subsequent Steps (Step 2, 3, 4):
            - If the step introduces a new topic/focus, seamlessly transition the title:
              `new_title_group = create_title("<NEW STEP TITLE>")`
              `self.play(FadeOut(title_group), FadeIn(new_title_group, shift=DOWN*0.1), run_time=0.4)`
              `title_group = new_title_group`
            - If the main topic remains identical, DO NOT fade out or remove `title_group`. Keep it on screen.
            - NEVER create a title variable (e.g. `title2 = create_title(...)` or `title_2 = ...`) without immediately passing it to `self.play(FadeIn(...))`! Any title variable you define MUST be animated onto the screen.

        - DYNAMIC CARD & PRODUCT CONTAINER CONTAINMENT (NO TEXT OVERFLOWING BORDERS):
          * All cards (`create_card`, `create_product_card`, `create_feature_card`) MUST dynamically calculate background height based on their children:
            `calc_h = max(height if height else 0.65, content.height + 2 * pad_y)`
          * When creating product cards with images, titles, and subtitles:
            - Clamp image size: `if hasattr(img, "height") and img.height > 1.25: img.scale_to_fit_height(1.25)` and `if hasattr(img, "width") and img.width > (width - 0.4): img.scale_to_fit_width(width - 0.4)`.
            - Set card height dynamically: `card_h = max(2.6, content.height + 0.35)`.
            - Subtitles, prices, and tags MUST NEVER spill across the bottom border of the card!

        - ANNOTATIONS & CALLOUT PLACEMENT (NO OVERLAYS ON CARDS/IMAGES):
          * Annotation text, callouts, and pointer arrows must NEVER overlap or sit on top of product cards, images, or diagram nodes!
          * Position callout text either directly ABOVE the card (`next_to(card, UP, buff=0.25)`), or outside the card's bounding box (`next_to(card, LEFT, buff=0.35)` or `next_to(card, RIGHT, buff=0.35)`).
          * NEVER align wide multi-line text to the start of an arrow pointing inward toward a card if the text width causes it to cross over the card.

        - MANDATORY STEP LIFECYCLE FADEOUT (NO GHOST CLUTTER):
          At every `## Presentation Step N` transition, you MUST explicitly FadeOut ALL visual entities from preceding steps that are no longer part of the active step.
          Never assume elements disappear on their own! If Step 1 or 2 introduced nodes, circles, badges, arrows, connector lines, highlight boxes, or cards, and Step 3 transitions to a new concept or sub-case, EVERY one of those old objects MUST be included in the initial self.play(FadeOut(...)) call AND removed via self.remove(...). No old diagram pieces or badges from earlier steps may linger into later steps to cause clutter or collisions.

        - VERTICAL SCREEN BOUNDARY CLAMP & CONTENT CEILING (y in [-3.5, +2.2]):
          * The canvas vertical range is strictly y in [-4.0, +4.0].
          * CEILING: The top edge of all content panels, containers, cards, tables, diagrams, and section headers MUST sit strictly at or below y = +2.2 (e.g. `move_to([0, -0.45, 0])` or `next_to(title_group, DOWN, buff=0.45).set_x(0)`). CRITICAL: NEVER place content with `next_to(title_group, DOWN)` without `.set_x(0)` because `title_group` is anchored to the top-left, which shifts content horizontally to x ≈ -3.5, clipping it off-screen and leaving massive empty white space on the right! ALWAYS center content across the canvas.
          * FLOOR: Elements must stay above y = -3.5 so that brackets, footnotes, and cards are never pushed off the bottom of the screen.


        - ATOMIC HIGHLIGHT HELPER PATTERN: When creating highlight boxes, pills, or tags (e.g. yellow highlight rectangles behind text/math), ALWAYS bundle both the text mobject and the background into a single VGroup (e.g., def create_highlighted_text(text, size=16, color=C_DARK_BLUE, bg_color=C_YELLOW): txt = CrispText(text, size=size, color=color); bg = BackgroundRectangle(txt, color=bg_color, fill_opacity=1, buff=0.08); return VGroup(bg, txt)). NEVER instantiate a BackgroundRectangle without including its text mobject in the group!
        - STRICT MANDATE ON UNIFORM TEXT SIZING & NO TEXT STRETCHING:
          1. STRICT UNIFORM FONT SIZES ACROSS SIBLING BOXES, CARDS & CELLS: In cards, boxes, flowchart shapes, and tables, all text contents must maintain a strictly uniform font size (13pt to 15pt). NEVER instruct or call `.scale_to_fit_width(...)` on text objects, which forces text to span the container width or shrinks long text down into tiny fonts compared to sibling boxes. Always wrap longer text across multiple lines using '\n' or max_width and allow containers to adjust height dynamically.
          2. MULTI-LINE CENTER ALIGNMENT: All multi-line explanatory text, note blocks, hub nodes, and table cells must have their lines centered (`\n` lines arranged with `aligned_edge=ORIGIN`).
          3. MAXIMIZE CANVAS UTILIZATION (NO DEAD WHITE SPACE VOIDS): The 16:9 canvas provides 14.22 width x 8.0 height. Macro-containers, cards, and diagrams must be generously proportioned (e.g. 4.8 to 5.6 width for cards in split-screen layouts; 9.6 to 10.5 width for full tables; vertical spans from y = -2.2 to +1.8). Never leave massive empty voids on the bottom or side margins.
          4. UNIFORM LATEX & NON-LATEX SIZING: In Manim Community, default MathTex font_size is 48, which renders equations 3x to 4x taller than normal text! All LaTeX formatted text (MathTex, Tex) MUST nearly match the size of surrounding non-latex text (CrispText):
             - Standard equations and formulas: ALWAYS specify `font_size=22` to `26` (or scale 0.45 to 0.55). NEVER use font_size >= 28 or .scale(0.75 - 1.2)!
             - Inline math next to labels/body text: ALWAYS use `font_size=16` to `18` so mathematical symbols match the exact height of the adjacent text.
             - Formula width clamping: Inside any card or sub-panel, formula width MUST NEVER exceed 2.9 units! Always clamp with `if hasattr(f, "width") and f.width > max_w: f.scale_to_fit_width(max_w)`.
          5. GRAPH AXES & FUNCTION PLOT LIFECYCLE:
             - ALWAYS position Axes (e.g. `axes.move_to(...)` or arrange inside its parent VGroup) BEFORE evaluating `axes.plot(...)` or `axes.c2p(...)`. Plotting curves while axes are at ORIGIN will cause curve points to be misaligned when axes are moved later!
             - Mandatory Step Lifecycle Fadeout: When transitioning to a new step, all plotted curves (`axes.plot(...)`), annotations, and data points MUST be explicitly included in `FadeOut(...)` (or grouped together in the container `VGroup`). Never leave orphaned curves or annotations floating on screen in later steps!
          6. NO `stretch=True` INSIDE `VGroup(...)`: `stretch=True` belongs only on `SurroundingRectangle(...)` or `.surround()`, NEVER inside `VGroup(...)` which crashes with `TypeError`.
          7. CLEAN STEP TRANSITIONS (NO GHOST / ZOMBIE MOBJECTS): When transitioning between presentation steps after fading out previous step mobjects, always call `self.remove(*self.mobjects)` immediately after `self.play(FadeOut(...))` to eliminate any lingering sub-mobjects or indicated elements.
          8. TABLE HEADER CONTRAST: If table column headers use white text (`C_WHITE`), they MUST be backed by an explicit dark background rectangle (e.g. `C_DARK_BLUE` with `height=table.get_rows()[0].height + 0.18`). Never leave white header text floating on a white canvas.

        ### KINETIC VECTOR ARCHITECTURE & STRICT PROHIBITION OF PPT CARDS:
        To produce final renders that look like world-class kinetic vector animations rather than static PowerPoint slides, adhere strictly to procedural vector mechanics:

        1. STRICT PROHIBITION OF PPT CARDS & CONTAINERS:
           - Strictly DO NOT wrap statements, concepts, metrics, or comparisons in rounded-rectangle container cards, pill boxes, or floating card stacks!
           - Strictly DO NOT build vertical stacks of `create_card`, `create_yellow_card`, or `RoundedRectangle` text boxes! That looks like a 2005 PowerPoint slide!
           - Never place static cards or bullet lists on the screen.

        2. PROCEDURAL MANIM VECTOR MECHANISMS:
           - Build real, living Manim vector geometry: mechanical balance scales with swinging pans, rotating radar sweeps, conduits with flowing particles, neural halo pulses, interactive dials with oscillating needles, and branching state machines!
           - Minimal Punchy Text: Micro-labels only (1-3 words max, e.g. "Max Efficiency", "Low Cost", "Perception"). Zero paragraphs, zero walls of text, zero descriptive sentences inside boxes!
           - Continuous Motion: Infuse living motion (flowing dots along paths, pulsing rings, rotating reticles) so the screen is never frozen or static during narration.

        3. CRITICAL MANIM SIZING & SPATIAL RULES:
           - NEVER use `.set_width(w).set_height(h)` in Manim! In Manim, `.set_height()` scales BOTH width and height proportionally, overwriting width! Always set width and height in the constructor: `RoundedRectangle(width=w, height=h, corner_radius=r)` or use `.stretch_to_fit_width(w).stretch_to_fit_height(h)`!
           
        - Output ONLY the raw executable Python code. No markdown fences, no introductory or concluding conversational text.

        ---

        ### OUTPUT

        Return only the modified Manim code.
        No explanations.
        No comments.
        """

        user_prompt = """
        Here are the inputs required for styling and fixing the code:
        --------------------------------------------------
        Existing Manim code:
        {code_script}
        --------------------------------------------------
        Client styling/color guidelines:
        {branding_guidelines}
        --------------------------------------------------
        Timestamped visual layout fixing directives (M:SS format):
        {engineering_suggestions}

        --------------------------------------------------
        CRITICAL EXECUTION INSTRUCTIONS:

        You MUST dynamically implement EVERY visual correction identified in the "Timestamped visual layout fixing directives" into the Python/Manim code.

        IMPORTANT: Do NOT treat the directives as a rigid list of mechanical operations. You must use visual reasoning and code-level intelligence to understand the underlying problem described at each timestamp and determine the correct implementation.

        For EACH timestamped directive:

        1. Identify the corresponding Presentation Step / Scene / Animation block in the code.

        2. Analyze the actual visual layout and determine the ROOT CAUSE of the reported issue.
           - Do not blindly apply the wording of the directive.
           - Infer what object, group, coordinate, animation, layout constraint, or timing is actually causing the problem.
           - Consider surrounding elements and the overall composition before making the change.

        3. Dynamically determine the appropriate code-level fix.
           The fix may involve, but is NOT limited to:
           - fading out or removing objects
           - repositioning objects
           - shifting or scaling groups
           - increasing boundary clearance
           - restoring missing text
           - modifying text content or wrapping
           - adjusting line/arrow start and end points
           - resizing containers
           - changing spacing between elements
           - correcting alignment
           - changing animation timing
           - modifying object dimensions
           - changing z-order/layering
           - adjusting camera framing
           - restructuring the affected layout when necessary

        4. Implement the fix directly in the executable code.
           Do not merely describe what should be changed.
           Do not add comments saying that a change should be made without actually implementing it.

        5. Preserve the intended visual design and animation flow.
           A fix must not create new overlaps, clipping, off-screen elements, broken arrows, inconsistent spacing, or animation errors elsewhere in the scene.

        6. When the directive is ambiguous, use the surrounding code, object relationships, scene structure, and visual context to infer the most appropriate correction rather than asking for clarification.

        7. Prefer robust, dynamic solutions over hard-coded patches.
           For example:
           - If an object is too close to a boundary, calculate its position relative to the boundary instead of blindly using a fixed coordinate.
           - If text overlaps another object, adjust the relevant group's layout/spacing rather than arbitrarily moving one element.
           - If an arrow becomes misaligned after an object moves, update the arrow endpoints based on the object's actual position.
           - If a container no longer fits its contents, derive its dimensions from the contents instead of using an arbitrary fixed size.

        8. The final code must remain fully executable.
           Check that:
           - all referenced objects exist
           - all variables are defined before use
           - all animations are valid
           - all coordinates and dimensions are valid
           - no object is unintentionally duplicated
           - no required text or visual element is accidentally removed
           - the modified scene remains syntactically and logically correct

        9. MANDATORY EXECUTION OF VLM DIRECTIVES (CRITICAL):
           - Every concrete defect, coordinate repositioning, and color adjustment identified by VLM QA must be strictly implemented in code.
           - If a directive specifies repositioning a column, header, badge, or formula to a specific coordinate (e.g. RIGHT * 8.0, color=C_DARK_BLUE), you MUST apply that adjustment directly.
           - Cross-check your final code against every single timestamped directive before returning it.

        10. Multi-Column Spacing & Table Layout:
           - In 3-column tables, Column 1 is near get_left() + RIGHT * 0.4, Column 2 at get_left() + RIGHT * 3.8, and Column 3 at get_left() + RIGHT * 8.0 (with dividers at 3.4 and 7.2). NEVER place Column 3 between 5.5 and 6.5 where it touches or overlaps Column 2 data!
           - Guarantee at least 2.4 units of horizontal clearance between columns.

        11. Formula Contrast & Card Legibility:
           - MathTex formulas inside light or low-opacity cards or on the canvas MUST explicitly specify color=C_DARK_BLUE (#404040). NEVER leave formulas white on light cards!
           - Never place opaque white BackgroundRectangle on light/colored cards.

        12. Safe Boundary Clamping & Contrast:
           - Ensure all elements remain within horizontal bounds (x in [-6.4, 6.4]) and vertical bounds (y in [-3.5, 2.2]).
           - Ensure high-contrast dark charcoal (#404040) text on light cards/canvas and bright white text on dark solid containers.

        Your goal is to eliminate 100% of detected visual defects by strictly incorporating all VLM fixes with flawless mathematical precision.

        FINAL REQUIREMENT:
        Return ONLY the complete executable Python code.
        Do not return explanations, analysis, summaries, markdown, or pseudocode.
        """

        for group, group_data in storyboard.items():
            skip_scenes_env = os.environ.get("SKIP_SCENES")
            if skip_scenes_env and str(group) in [s.strip() for s in skip_scenes_env.split(",")]:
                print(f"Skipping Scene {group} per SKIP_SCENES")
                src = os.path.join(refined_scene_codes_dir, f"group_{group}.py")
                dst = os.path.join(styled_scenes_dir, f"group_{group}.py")
                if os.path.exists(src) and (not os.path.exists(dst) or src != dst):
                    shutil.copy2(src, dst)
                continue
            section_timing = {}
            total_scene_time = 0
            for section_id, item in enumerate(group_data):
                key_time = f"section_{section_id+1}_start_time"
                key_narration = f"section_{section_id+1}_narration"
                section_timing.update(
                    {
                        key_time: total_scene_time,
                        key_narration: item.get("narration_statement", "")
                    }
                )
                total_scene_time += item.get("run_time", 0)
                item.pop("narration_statement", None)
                item.pop("run_time", None)

            # Locate original code
            code_script_file = os.path.join(refined_scene_codes_dir, f"group_{group}.py")
            if not os.path.exists(code_script_file):
                print(f"Skipping group {group}: Original code script not found.")
                continue

            with open(code_script_file, 'r', encoding="utf-8") as f:
                code_script = f.read()

            output_file = os.path.join(styled_scenes_dir, f"group_{group}.py")

            # A scene is a pure template only if it exclusively calls a template function and has no multi-step presentation
            has_tmpl_call = any(t in code_script for t in ["play_title_intro(", "play_learning_roadmap(", "play_topic_coverage("])
            has_multiple_steps = "## Presentation Step 2" in code_script or "## Presentation Step 3" in code_script
            is_pure_template = has_tmpl_call and not has_multiple_steps and len(code_script.splitlines()) < 80

            if is_pure_template:
                print(f"Preserving official pure Simplilearn template for Scene {group} in Stage 20...")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(code_script)
                continue

            if os.path.exists(output_file) and os.path.getsize(output_file) > 0 and os.environ.get("FORCE_REWRITE") != "1":
                print(f"Styled code for group {group} already exists. Skipping.")
                continue

            # Load timestamped fixes first, fallback to consolidated suggestions
            vlm_fixing_file = os.path.join(vlm_fixing_dir, f"scene_{group}_timestamped_fixes.txt")
            mirror_fixing_file = os.path.join(specific_suggestions_folder, f"scene_{group}_timestamped_fixes.txt")
            legacy_suggestions_file = os.path.join(specific_suggestions_folder, f"scene_{group}_suggestions_consolidated.txt")

            specific_scene_suggestions = ""
            if os.path.exists(vlm_fixing_file):
                with open(vlm_fixing_file, 'r', encoding="utf-8") as f:
                    specific_scene_suggestions = f.read()
                print(f"Loaded timestamped fixes from {vlm_fixing_file}")
            elif os.path.exists(mirror_fixing_file):
                with open(mirror_fixing_file, 'r', encoding="utf-8") as f:
                    specific_scene_suggestions = f.read()
                print(f"Loaded timestamped fixes from {mirror_fixing_file}")
            elif os.path.exists(legacy_suggestions_file):
                with open(legacy_suggestions_file, 'r', encoding="utf-8") as f:
                    specific_scene_suggestions = f.read()
                print(f"Loaded legacy consolidated suggestions from {legacy_suggestions_file}")

            universal_anti_defect_rules = """
=== MANDATORY UNIVERSAL ANTI-DEFECT RULES ===
1. HEADER CLEARANCE: Strictly reserve the upper quadrant (y >= 1.8) for the slide title. Keep all containers, graphs, and cards strictly at or below y = 1.7. Never render two slide titles simultaneously.
2. LINE & ARROW ROUTING: Connecting lines and arrows must NEVER cut through or touch text boxes, callout cards, or badges. All callout cards and badges MUST have fill_opacity=1.0 and .set_z_index(20). Route curved arrows cleanly around cards.
3. COLOR CONTRAST & MATHTEX:
   - NAVY BLUE IS STRICTLY FORBIDDEN: Do NOT create navy blue containers (#0B3C5D, #06152B, #0A2540, NAVY).
   - On canvas or light cards (#F0F4F8, #FFFFFF, #F8FAFC, light tones): ALL text and MathTex formulas MUST be dark charcoal (#404040 / C_TEXT). Never render white text on light cards.
   - NO ALL CAPS: All on-screen text, titles, subtitles, headers, card labels, and tags must NEVER be in ALL CAPS. Use Title Case for titles and headers; use Sentence Case for body text. Short technical acronyms only (AI, RAM, DB, API, LLM, CPU, GPU, UI, ML) may be uppercase.
   - FOCUS HIGHLIGHTS: Must strictly use vibrant orange (#F78908) with 3px stroke (stroke_width=3) and 1.0s draw time. Only ONE highlight active at a time.
4. BORDER CLAMPING & PADDING: Ensure all text, badges, and callouts remain strictly inside card borders (with >= 0.25 padding) and within screen margins (|x| <= 6.4, |y| <= 3.5).
5. MULTI-COLUMN SEPARATION: Maintain at least 2.4 units horizontal clearance between table columns. Never crowd Column 2 and Column 3 together.
6. NO EMPTY CONTAINERS: Every container, card, or box must contain legible, informative content.
7. STEP-BOUNDARY CLUTTER PURGE & LIFECYCLE FADEOUTS (P0 COMPILER DIRECTIVE):
   When transitioning between presentation steps/sections, every temporary element, diagram, branch line, arrow, or callout created in Step N MUST be explicitly faded out (`self.play(FadeOut(mobj1), FadeOut(mobj2), ...)`) before or during the introduction of Step N+1 elements. NEVER leave old diagrams, cards, or annotations floating underneath or colliding with new step elements.
8. VECTOR CHECKMARKS & NO RAW UNICODE (P0 COMPILER DIRECTIVE):
   NEVER render raw unicode checkmarks, crosses, or glyph symbols (such as '✓', '✔', '\\u2713', '\\u2714', '✗', '✘') in CrispText/Text. On Windows Manim rendering pipelines without Open Sans fallback fonts, raw unicode characters produce broken missing-glyph fallback boxes with numbers (e.g. '27 13'). ALWAYS construct checkmarks and crossmarks using vector shapes via helper functions:
   `create_checkmark(color="#107C41", size=0.35)` using a vector VMobject with two lines, and `create_crossmark(color="#C5221F", size=0.35)` using two intersecting lines.
9. SEQUENTIAL TITLE CROSSFADES & SINGLE HEADER AUTHORITY (P0 COMPILER DIRECTIVE):
   Never render duplicate main slide headers. Main slide titles must remain persistent or update cleanly. Do NOT use `ReplacementTransform(title_group, new_title_group)` or simultaneous `FadeOut` + `FadeIn` in the same animation call because they create ghost double-exposure overlaps. ALWAYS execute sequential transitions: `self.play(FadeOut(title_group), run_time=0.3)` followed by `self.play(FadeIn(new_title_group), run_time=0.4)`.
10. MANDATORY EXECUTION OF STAGE 19 TIMESTAMPED DIRECTIVES (P0 COMPILER DIRECTIVE):
   The timestamped fixing directives above from Stage 19 are verified Art Director layout repairs. Every single coordinate shift, boundary clamp, card encapsulation, and cleanup instruction MUST be faithfully implemented with 100% fidelity. Do not disregard or weaken Stage 19 directives.
"""
            if not specific_scene_suggestions.strip() or specific_scene_suggestions.strip().startswith("# No visual triage issues"):
                specific_scene_suggestions = universal_anti_defect_rules
            else:
                specific_scene_suggestions = specific_scene_suggestions.strip() + "\n\n" + universal_anti_defect_rules
            print(f"Injected Universal Anti-Defect Rules into specific suggestions for group {group}.")

            success = False
            last_syntax_error = None
            for attempt in range(1, 4):
                try:
                    if config_data.get("theme") == "dynamic_learning":
                        formatted_system_prompt = system_prompt_dynamic
                    else:
                        formatted_system_prompt = system_prompt
                    formatted_user_prompt = user_prompt.format(
                        code_script=code_script,
                        branding_guidelines=color_palette + "\n\n" + font_guidelines,
                        engineering_suggestions=specific_scene_suggestions,
                    )
                    if last_syntax_error:
                        formatted_user_prompt += (
                            f"\n\nCRITICAL FIX (Retry after Syntax Error): Your previous output failed syntax compilation:\n"
                            f"{last_syntax_error}\n"
                            f"Ensure all raw strings r'...' have properly escaped backslashes, quotes are closed, and Python syntax is 100% valid!"
                        )

                    print(f"Refining group {group} (attempt {attempt}/3)...")

                    response = google_client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=formatted_system_prompt + "\n\n" + formatted_user_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=60000,
                            thinking_config=types.ThinkingConfig(thinking_level="high")
                        )
                    )

                    generated_code = response.text or ""
                    print(f"Generated code response for scene {group}")

                    code_content = self.remove_code_fences(generated_code)
                    code_content = re.sub(
                        r'try:\s*\n\s*from feedback_functions(?:_vlm)?\.instrumented_scene import InstrumentedScene\s*\n\s*except[^\n]*:\s*\n(?:\s*try:[\s\S]*?except[^\n]*:\s*\n)?(?:\s*class InstrumentedScene[\s\S]*?pass\s*\n|\s*InstrumentedScene\s*=\s*[^\n]+\n|\s*pass\s*\n)',
                        '',
                        code_content
                    )
                    code_content = re.sub(r'^\s*from feedback_functions(?:_vlm)?\.instrumented_scene import InstrumentedScene\s*\n', '', code_content, flags=re.MULTILINE)
                    code_content = re.sub(r'try:\s*\n(?=\s*except|\s*finally)', 'try:\n    pass\n', code_content)
                    code_content = code_content.replace(
                        "class FinalScene(InstrumentedScene, MovingCameraScene)",
                        "class FinalScene(MovingCameraScene)"
                    )
                    code_content = code_content.replace(
                        "class FinalScene(InstrumentedScene)",
                        "class FinalScene(MovingCameraScene)"
                    )
                    code_content = code_content.replace('aligned_edge=CENTER', 'aligned_edge=ORIGIN')
                    code_content = code_content.replace('aligned_edge=None', 'aligned_edge=ORIGIN')
                    code_content = re.sub(r'if\s+["\']\\n["\']\s+in\s+str\(text\)\s+and\s+["\']alignment["\']\s+not\s+in\s+kwargs:\s*\n\s*kwargs\[["\']alignment["\']\]\s*=\s*["\']center["\']\s*\n', '', code_content)
                    
                    # Automatically convert chained .set_width(W).set_height(H) to .stretch_to_fit_width(W).stretch_to_fit_height(H)
                    # to prevent Manim from proportionally crushing mobject width
                    code_content = re.sub(
                        r"\.set_width\(([^)]+)\)\.set_height\(([^)]+)\)",
                        r".stretch_to_fit_width(\1).stretch_to_fit_height(\2)",
                        code_content
                    )
                    code_content = re.sub(
                        r"\.set_height\(([^)]+)\)\.set_width\(([^)]+)\)",
                        r".stretch_to_fit_width(\2).stretch_to_fit_height(\1)",
                        code_content
                    )

                    # Automatically add stretch=True to .surround(...) calls on rectangles
                    # to prevent Manim from scaling height proportionally into gigantic boxes
                    def _add_stretch_to_surround(code_text: str) -> str:
                        idx = 0
                        out = []
                        pattern = ".surround("
                        while True:
                            pos = code_text.find(pattern, idx)
                            if pos == -1:
                                out.append(code_text[idx:])
                                break
                            out.append(code_text[idx:pos])
                            start_paren = pos + len(pattern)
                            depth = 1
                            curr = start_paren
                            while curr < len(code_text) and depth > 0:
                                if code_text[curr] == '(':
                                    depth += 1
                                elif code_text[curr] == ')':
                                    depth -= 1
                                curr += 1
                            if depth == 0:
                                args = code_text[start_paren:curr-1].strip()
                                if "stretch=" in args:
                                    out.append(code_text[pos:curr])
                                elif args:
                                    out.append(f".surround({args}, stretch=True)")
                                else:
                                    out.append(".surround(stretch=True)")
                                idx = curr
                            else:
                                out.append(code_text[pos:pos+len(pattern)])
                                idx = start_paren
                        return "".join(out)

                    code_content = _add_stretch_to_surround(code_content)
                    
                    # Programmatic clamping: Ensure cards and sub-panels do not exceed width 3.3 for 2-column layouts
                    if is_executive:
                        code_content = re.sub(r'create_card\(([^)]*?)width\s*=\s*(?:3\.8|3\.6|4\.0)', r'create_card(\1width=3.3', code_content)
                        code_content = re.sub(r'create_yellow_card\(([^)]*?)width\s*=\s*(?:3\.8|3\.6|4\.0)', r'create_yellow_card(\1width=3.3', code_content)
                        code_content = re.sub(r'RoundedRectangle\(width=(?:3\.8|3\.6|4\.0),\s*height=(?:3\.8|3\.4|3\.6|3\.2|2\.8)', r'RoundedRectangle(width=3.3, height=3.2', code_content)

                    # Replace create_card, create_yellow_card, and create_note with bulletproof implementations
                    robust_create_card = """def create_card(content_or_text, *args, **kwargs):
    width = 3.3
    height = None
    fill_color = None
    stroke_color = None
    stroke_width = 1.5
    corner_radius = 0.12
    pad_x = 0.2
    pad_y = 0.12
    align = kwargs.get("align", "left")
    z_index = kwargs.get("z_index", 5)

    c_white = globals().get("C_WHITE", "#FFFFFF")
    c_dark_blue = globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))
    c_black = globals().get("C_BLACK", "#000000")

    if isinstance(content_or_text, str) and len(args) > 0 and isinstance(args[0], str) and ("\\n" in args[0] or ":" in args[0] or len(args[0].split()) > 2):
        primary = content_or_text
        secondary = args[0]
        border_color = args[1] if len(args) > 1 else kwargs.get("border_color", kwargs.get("stroke_color", globals().get("C_SKY_BLUE", "#62B7E4")))
        border_width = args[2] if len(args) > 2 else kwargs.get("border_width", kwargs.get("stroke_width", 1.5))
        border_opacity = kwargs.get("border_opacity", 1.0)
        p = CrispText(primary, size=14, color=c_white, weight=BOLD, align="center")
        if hasattr(p, "width") and p.width > 3.4: p.scale_to_fit_width(3.4)
        s = CrispText(secondary, size=12, color=globals().get("C_SKY_BLUE", "#62B7E4"), weight=NORMAL, align="center")
        if hasattr(s, "width") and s.width > 3.4: s.scale_to_fit_width(3.4)
        content = VGroup(p, s).arrange(DOWN, buff=0.2)
        bg = RoundedRectangle(width=3.6, height=content.height + 0.6, corner_radius=0.15, fill_color=c_dark_blue, fill_opacity=1, stroke_color=border_color, stroke_width=border_width, stroke_opacity=border_opacity)
        content.move_to(bg.get_center())
        return VGroup(bg, content).set_z_index(z_index)

    if len(args) > 0 and isinstance(args[0], (list, tuple)):
        items_list = args[0]
        bg_col = args[1] if len(args) > 1 else kwargs.get("bg_color", kwargs.get("fill_color", c_dark_blue))
        fill_color = bg_col
        title_color = kwargs.get("title_color", c_white)
        content_color = kwargs.get("content_color", c_white)
        t_mob = CrispText(str(content_or_text), size=kwargs.get("title_size", 16), weight=BOLD, color=title_color)
        mobs = [t_mob]
        for it in items_list:
            if isinstance(it, str):
                mobs.append(CrispText(it, size=kwargs.get("item_size", 13), color=content_color))
            elif isinstance(it, Mobject):
                mobs.append(it)
        items_grp = VGroup(*mobs).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        content_or_text = items_grp
        width = kwargs.get("width", 3.6)
        if len(args) > 2 and isinstance(args[2], (int, float)):
            width = args[2]
    elif len(args) > 0:
        first_arg = args[0]
        if isinstance(first_arg, str) and not first_arg.replace('.', '', 1).isdigit():
            fill_color = first_arg
            if len(args) > 1:
                if isinstance(args[1], (int, float)):
                    width = args[1]
                    if len(args) > 2 and isinstance(args[2], str):
                        stroke_color = args[2]
                elif isinstance(args[1], str):
                    stroke_color = args[1]
                    if len(args) > 2 and isinstance(args[2], (int, float)):
                        width = args[2]
            if len(args) > 2 and isinstance(args[2], (int, float)) and width == 3.3:
                stroke_width = args[2]
            if len(args) > 3 and isinstance(args[3], (int, float)):
                corner_radius = args[3]
        elif isinstance(first_arg, (int, float)):
            width = first_arg
            if len(args) > 1 and (isinstance(args[1], (int, float)) or args[1] is None):
                height = args[1]
            if len(args) > 2:
                fill_color = args[2]
            if len(args) > 3:
                stroke_color = args[3]

    if "width" in kwargs:
        width = kwargs["width"]
    if "height" in kwargs:
        height = kwargs["height"]
    if "fill_color" in kwargs:
        fill_color = kwargs["fill_color"]
    elif "fill" in kwargs:
        fill_color = kwargs["fill"]
    elif "bg_color" in kwargs:
        fill_color = kwargs["bg_color"]

    if "stroke_color" in kwargs:
        stroke_color = kwargs["stroke_color"]
    elif "stroke" in kwargs:
        stroke_color = kwargs["stroke"]
    elif "border_color" in kwargs:
        stroke_color = kwargs["border_color"]

    if "stroke_width" in kwargs:
        stroke_width = kwargs["stroke_width"]
    elif "border_width" in kwargs:
        stroke_width = kwargs["border_width"]

    if "corner_radius" in kwargs:
        corner_radius = kwargs["corner_radius"]
    elif "radius" in kwargs:
        corner_radius = kwargs["radius"]

    if "padding" in kwargs:
        pad_x = pad_y = kwargs["padding"]
    elif "pad" in kwargs:
        pad_x = pad_y = kwargs["pad"]
    if "buff" in kwargs:
        pad_x = pad_y = kwargs["buff"]
    if "buff_x" in kwargs:
        pad_x = kwargs["buff_x"]
    if "buff_y" in kwargs:
        pad_y = kwargs["buff_y"]

    if fill_color is None:
        fill_color = c_white
    if stroke_color is None:
        stroke_color = c_dark_blue

    explicit_color = kwargs.get("text_color", kwargs.get("color", kwargs.get("font_color", None)))
    if explicit_color is not None:
        final_text_color = explicit_color
    else:
        dark_set = {"#0b3c5d", "#2c81fe", "#404040", "#2b2c6c", "#7651a2", "#ea212a", "#000000", "#2d6a4f", "#1e293b", "#0f172a", "#111827", "#3b0764", "#831843", "black", "c_dark_blue", "c_purple", "c_red", "c_black"}
        fc_str = str(fill_color).lower()
        is_dark = (fc_str in dark_set)
        if not is_dark and fc_str.startswith("#") and len(fc_str) == 7:
            try:
                r = int(fc_str[1:3], 16)
                g = int(fc_str[3:5], 16)
                b = int(fc_str[5:7], 16)
                lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                is_dark = (lum < 0.55)
            except Exception:
                is_dark = False

        if is_dark:
            final_text_color = c_white
        else:
            if fc_str in {"#f9c72c", "c_yellow", "#ffff00", "yellow"}:
                final_text_color = c_black
            elif fc_str in {"#73c2e5", "c_light_blue"}:
                final_text_color = globals().get("TEXT_COLOR", "#404040")
            elif fc_str in {"#ffffff", "c_white", "white"}:
                sc_str = str(stroke_color).lower()
                final_text_color = stroke_color if (sc_str in dark_set or (sc_str.startswith("#") and len(sc_str) == 7 and int(sc_str[1:3], 16) * 0.299 + int(sc_str[3:5], 16) * 0.587 + int(sc_str[5:7], 16) * 0.114 < 140)) else globals().get("TEXT_COLOR", "#404040")
            else:
                final_text_color = globals().get("TEXT_COLOR", "#404040")

    f_size = kwargs.get("font_size", kwargs.get("text_size", kwargs.get("size", 14)))
    f_weight = kwargs.get("font_weight", kwargs.get("weight", NORMAL))
    f_font = kwargs.get("font", "Open Sans")

    if isinstance(content_or_text, str):
        raw_str = content_or_text
        if "\\n" not in raw_str and "\n" not in raw_str and len(raw_str) > 28:
            import textwrap
            chars_per_line = max(20, int(max(float(width), 3.0) * 8.5))
            raw_str = textwrap.fill(raw_str, width=chars_per_line)
        content = CrispText(raw_str, size=f_size, color=final_text_color, weight=f_weight, font=f_font, autowrap=False)
    else:
        content = content_or_text
        if explicit_color is not None and hasattr(content, "set_color"):
            content.set_color(explicit_color)

    target_card_w = width
    max_content_w = max(target_card_w - (2 * pad_x), 0.1)

    if hasattr(content, "width") and content.width > max_content_w:
        needed_w = content.width + (2 * pad_x)
        if needed_w <= 6.2:
            target_card_w = needed_w
            max_content_w = target_card_w - (2 * pad_x)
        else:
            ratio = max_content_w / content.width
            if ratio < 0.88: ratio = 0.88
            content.scale(ratio)

    min_required_h = getattr(content, "height", 0.5) + (2 * pad_y)
    if height is not None:
        # Dynamically accommodate content height without shrinking/squishing font below readable scale
        calc_h = max(float(height), min_required_h)
    else:
        calc_h = max(0.65, min_required_h)

    card_bg = RoundedRectangle(
        width=target_card_w,
        height=calc_h,
        corner_radius=corner_radius,
        color=stroke_color,
        fill_color=fill_color,
        fill_opacity=1,
        stroke_width=stroke_width
    )

    content.move_to(card_bg.get_center())
    if align == "left":
        content.align_to(card_bg, LEFT).shift(RIGHT * pad_x)
    elif align == "right":
        content.align_to(card_bg, RIGHT).shift(LEFT * pad_x)

    return VGroup(card_bg, content).set_z_index(z_index)"""

                    robust_create_yellow_card = """def create_yellow_card(content_or_text, width=3.3, height=None, stroke_color=None, pad_x=0.2, pad_y=0.12, align="left", z_index=5, **kwargs):
    cr = kwargs.pop("radius", kwargs.pop("corner_radius", 0.074))
    sw = kwargs.pop("stroke_width", 1.5)
    stroke = kwargs.pop("stroke_color", kwargs.pop("stroke", stroke_color or globals().get("C_AMBER", "#D97706")))
    fill = kwargs.pop("fill_color", kwargs.pop("fill", globals().get("C_WARM_AMBER", "#FEF3C7")))
    return create_card(content_or_text, width=width, height=height, fill_color=fill, stroke_color=stroke, stroke_width=sw, corner_radius=cr, pad_x=pad_x, pad_y=pad_y, align=align, z_index=z_index, **kwargs)"""

                    robust_create_note = """def create_note(text, width=2.4, height=None, font_size=12, font_color=None, bg_color=None, z_index=5):
    c_yellow = globals().get("C_WARM_AMBER", globals().get("C_YELLOW", "#E6A157"))
    c_black = globals().get("C_BLACK", "#000000")
    if font_color is None:
        font_color = c_black
    if bg_color is None:
        bg_color = c_yellow
    pad_x = 0.22
    pad_y = 0.15
    max_w = max(width - (2 * pad_x), 0.1)
    txt_str = str(text)
    if "\\n" not in txt_str and "\n" not in txt_str and len(txt_str) > 22:
        import textwrap
        txt_str = textwrap.fill(txt_str, width=22)
    txt = CrispText(txt_str, size=font_size, color=font_color, autowrap=False)
    if hasattr(txt, "width") and txt.width > max_w:
        ratio = max_w / txt.width
        if ratio < 0.88: ratio = 0.88
        txt.scale(ratio)
    calc_h = max(height if height else 0.65, txt.height + 2 * pad_y)
    if height is not None and hasattr(txt, "height") and txt.height > (height - 2 * pad_y):
        txt.scale_to_fit_height(max(height - 2 * pad_y, 0.1))
    bg = RoundedRectangle(corner_radius=0.12, width=width, height=calc_h, fill_color=bg_color, fill_opacity=1, stroke_width=0)
    border = DashedVMobject(RoundedRectangle(corner_radius=0.12, width=width, height=calc_h, stroke_color=c_black, stroke_width=1.5), num_dashes=30)
    txt.move_to(bg.get_center())
    return VGroup(bg, border, txt).set_z_index(z_index)"""

                    robust_crisp_text = r"""def CrispText(text, size=24, font="Open Sans", **kwargs):
    if "font_size" in kwargs:
        size = kwargs.pop("font_size")
    try:
        size = float(size)
    except (ValueError, TypeError):
        size = 24.0
    if 0.0 < size <= 1.0:
        if size >= 0.28:
            size = 26.0
        elif size >= 0.19:
            size = 18.0
        elif size >= 0.14:
            size = 14.0
        else:
            size = 12.0
    elif size < 10.0:
        size = 12.0
    align = kwargs.pop("align", "center")
    autowrap_val = kwargs.pop("autowrap", kwargs.pop("wrap", None))
    disable_wrap_val = kwargs.pop("disable_wrap", kwargs.pop("disable_autowrap", False))
    max_w = kwargs.pop("max_width", kwargs.pop("wrap_width", None))
    for bad_k in ("alignment", "max_len", "line_spacing", "title_size", "item_size"):
        kwargs.pop(bad_k, None)
    slant_val = kwargs.pop("slant", NORMAL)
    weight_val = kwargs.pop("weight", NORMAL)
    if isinstance(weight_val, str):
        weight_val = weight_val.upper()
        if weight_val == "REGULAR":
            weight_val = "NORMAL"
    color_val = kwargs.pop("color", None)
    if color_val is None:
        color_val = globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))
    elif str(color_val).upper() in ("#F9C72C", "C_YELLOW", "YELLOW", "#FFF9E6", "#FFFF00"):
        color_val = globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))
    
    text_str = str(text)
    NL = chr(10)
    split_lines = [l for l in text_str.split(NL)] if NL in text_str else ([l for l in text_str.split(r"\n")] if r"\n" in text_str else None)
    if split_lines is None:
        should_autowrap = False
        wrap_chars = 34
        if max_w is not None:
            try:
                wrap_chars = max(18, int(float(max_w) / 0.115))
                should_autowrap = True
            except Exception:
                wrap_chars = 34
        elif autowrap_val is True:
            should_autowrap = True
        elif autowrap_val is False or disable_wrap_val:
            should_autowrap = False
        else:
            should_autowrap = (len(text_str) > 36 and " " in text_str and size <= 16)
        if should_autowrap:
            words = text_str.split()
            lines = []
            curr_line = []
            curr_len = 0
            for w in words:
                if curr_len + len(w) + 1 > wrap_chars:
                    if curr_line:
                        lines.append(" ".join(curr_line))
                    curr_line = [w]
                    curr_len = len(w)
                else:
                    curr_line.append(w)
                    curr_len += len(w) + 1
            if curr_line:
                lines.append(" ".join(curr_line))
            split_lines = lines
        else:
            split_lines = [text_str]
    if len(split_lines) > 1:
        line_mobs = []
        for line in split_lines:
            line_mob = Text(line, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **kwargs)
            line_mobs.append(line_mob)
        aligned_edge = ORIGIN if align == "center" else (LEFT if align == "left" else RIGHT)
        mob = VGroup(*line_mobs).arrange(DOWN, buff=0.18, aligned_edge=aligned_edge).scale(0.25)
    else:
        mob = Text(text_str, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **kwargs).scale(0.25)
    orig_scale = mob.scale_to_fit_width
    def safe_scale_width(tw):
        if hasattr(mob, "width") and mob.width > 0:
            ratio = tw / mob.width
            if ratio < 0.88: ratio = 0.88
            if ratio > 1.0: ratio = 1.0
            return mob.scale(ratio)
        return orig_scale(tw)
    mob.scale_to_fit_width = safe_scale_width
    return mob"""

                    code_content = self.replace_func_in_code(code_content, "CrispText", robust_crisp_text)
                    code_content = self.replace_func_in_code(code_content, "create_card", robust_create_card)
                    code_content = self.replace_func_in_code(code_content, "create_yellow_card", robust_create_yellow_card)
                    code_content = self.replace_func_in_code(code_content, "create_note", robust_create_note)

                    if "check_badge(" in code_content and "def check_badge" not in code_content:
                        badge_def = """def check_badge(radius=0.17):
    c = Circle(radius=radius, color=globals().get("C_GREEN", "#2D6A4F"), fill_color=globals().get("C_GREEN", "#2D6A4F"), fill_opacity=1, stroke_width=0)
    tick = Text("✓", font="Open Sans", font_size=int(radius*80), color=globals().get("C_WHITE", "#FFFFFF"))
    tick.move_to(c)
    return VGroup(c, tick).set_z_index(6)
"""
                        code_content = badge_def + "\n" + code_content

                    if "cross_badge(" in code_content and "def cross_badge" not in code_content:
                        badge_def = """def cross_badge(radius=0.17):
    c = Circle(radius=radius, color=globals().get("C_RED", "#E58F6D"), fill_color=globals().get("C_RED", "#E58F6D"), fill_opacity=1, stroke_width=0)
    x_mark = Text("✕", font="Open Sans", font_size=int(radius*80), color=globals().get("C_WHITE", "#FFFFFF"))
    x_mark.move_to(c)
    return VGroup(c, x_mark).set_z_index(6)
"""
                        code_content = badge_def + "\n" + code_content

                    if "create_premise_box(" in code_content and "def create_premise_box" not in code_content:
                        premise_def = """def create_premise_box(text_str, width=10.8, height=0.70):
    c_dark = globals().get("TEXT_COLOR", "#404040")
    c_lavender = globals().get("C_LAVENDER", "#9B99C7")
    t = CrispText(text_str, size=14, font="Open Sans", weight=BOLD, color=c_dark, align="center")
    if hasattr(t, "width") and t.width > (width - 0.4): t.scale_to_fit_width(width - 0.4)
    bg = RoundedRectangle(corner_radius=0.074, width=width, height=max(height, t.height + 0.22), fill_color="#F8FAFC", fill_opacity=0.9, stroke_color=c_lavender, stroke_width=1.5)
    t.move_to(bg.get_center())
    return VGroup(bg, t).move_to(UP * 2.22).set_x(0)
"""
                        code_content = premise_def + "\n" + code_content

                    if "create_leader_callout(" in code_content and "def create_leader_callout" not in code_content:
                        callout_def = """def create_leader_callout(target_mob, text_str, direction=UP, line_len=0.9):
    c_dark = globals().get("TEXT_COLOR", "#404040")
    c_sky = globals().get("C_SKY_BLUE", "#62B7E4")
    c_white = globals().get("C_WHITE", "#FFFFFF")
    dot = Dot(radius=0.06, color=c_dark)
    dot.move_to(target_mob.get_edge_center(direction))
    line_end = dot.get_center() + direction * line_len
    line = Line(dot.get_center(), line_end, stroke_width=1.5, color=c_dark)
    txt = CrispText(text_str, size=14, font="Open Sans", weight=BOLD, color=c_dark)
    txt.next_to(line_end, direction, buff=0.15)
    bg = RoundedRectangle(corner_radius=0.074, width=txt.width + 0.28, height=txt.height + 0.18, fill_color=c_white, fill_opacity=1, stroke_color=c_sky, stroke_width=1.2)
    bg.move_to(txt.get_center())
    return VGroup(dot, line, bg, txt)
"""
                        code_content = callout_def + "\n" + code_content

                    if "create_state_badge(" in code_content and "def create_state_badge" not in code_content:
                        state_def = """def create_state_badge(text_str, badge_type="violation", width=None):
    c_coral = globals().get("C_CORAL", "#E58F6D")
    c_dark = globals().get("TEXT_COLOR", "#404040")
    c_white = globals().get("C_WHITE", "#FFFFFF")
    col = c_coral if badge_type == "violation" else (c_dark if badge_type == "info" else "#2D6A4F")
    txt = CrispText(text_str, size=13, font="Open Sans", weight=BOLD, color=c_white, align="center")
    w = max(width if width else 0, txt.width + 0.4)
    bg = RoundedRectangle(corner_radius=0.074, width=w, height=txt.height + 0.2, fill_color=col, fill_opacity=1, stroke_width=0)
    txt.move_to(bg.get_center())
    return VGroup(bg, txt).set_z_index(6)
"""
                        code_content = state_def + "\n" + code_content

                    if "create_takeaway_banner(" in code_content and "def create_takeaway_banner" not in code_content:
                        takeaway_def = """def create_takeaway_banner(text_str, width=11.2, height=0.75):
    c_dark = globals().get("TEXT_COLOR", "#404040")
    t = CrispText(text_str, size=15, font="Open Sans", weight=BOLD, color=c_dark, align="center")
    if hasattr(t, "width") and t.width > (width - 0.4): t.scale_to_fit_width(width - 0.4)
    bg = RoundedRectangle(corner_radius=0.074, width=width, height=max(height, t.height + 0.25), fill_color="#FEF3C7", fill_opacity=1, stroke_color="#E6A157", stroke_width=1.5)
    t.move_to(bg.get_center())
    return VGroup(bg, t).move_to(DOWN * 3.0).set_x(0)
"""
                        code_content = takeaway_def + "\n" + code_content

                    if "create_strikethrough(" in code_content and "def create_strikethrough" not in code_content:
                        strike_def = """def create_strikethrough(target_mob, color=None, stroke_width=3):
    c_coral = globals().get("C_CORAL", "#E58F6D")
    col = color if color is not None else c_coral
    line = Line(target_mob.get_corner(DL) + LEFT * 0.1, target_mob.get_corner(UR) + RIGHT * 0.1, color=col, stroke_width=stroke_width)
    return line.set_z_index(10)
"""
                        code_content = strike_def + "\n" + code_content

                    # Convert unconditional cell text scaling to conditional clamp (prevents giant text distortion in tables)
                    code_content = self.make_scaling_conditional(code_content)

                    # Normalize typography: regulate LaTeX sizing, clean VGroup stretch
                    code_content = self.normalize_code_typography(code_content)

                    # Purge leaked/zombie mobjects at step transitions
                    code_content = self.ensure_clean_step_transitions(code_content)

                    # Clamp extreme screen coordinate shifts (keeps elements within visible 16:9 safe zone)
                    code_content = self.clamp_extreme_shifts(code_content)
                    code_content = sanitize_manim_code(code_content, script_path=output_file)
                    code_content = heal_syntax_errors(code_content)

                    # Validate syntax before writing
                    try:
                        compile(code_content, f"group_{group}.py", "exec")
                    except SyntaxError as syn_err:
                        print(f"Syntax validation failed on attempt {attempt}: {syn_err}")
                        last_syntax_error = syn_err
                        raise syn_err

                    with open(output_file, 'w', encoding="utf-8") as f:
                        f.write(code_content)
                    print(f"Successfully saved refined and verified code to {output_file}")

                    # Invalidate downstream stale files for this group
                    downstream_paths = [
                        os.path.join(base_folder, "manim_time_synced_code", f"group_{group}.py"),
                        os.path.join(base_folder, "manim_time_synced_videos", f"group_{group}.mp4"),
                        os.path.join(base_folder, "audio_integrated_videos", f"group_{group}_final.mp4")
                    ]
                    for dp in downstream_paths:
                        if os.path.exists(dp):
                            try:
                                os.remove(dp)
                                print(f"  [Invalidated] Removed stale downstream file: {dp}")
                            except Exception as del_err:
                                print(f"  [Warn] Failed to remove {dp}: {del_err}")

                    success = True
                    break

                except Exception as e:
                    print(f"Error refining group {group} on attempt {attempt}: {e}")
                    if "Forbidden" in str(e) or "not allowed by policy" in str(e):
                        break
                    if attempt < 3:
                        time.sleep(5)

            if not success:
                print(f"Applying fallback to input code for group {group}")
                try:
                    fallback_code = re.sub(
                        r'try:\s*\n\s*from feedback_functions(?:_vlm)?\.instrumented_scene import InstrumentedScene\s*\n\s*except[^\n]*:\s*\n(?:\s*try:[\s\S]*?except[^\n]*:\s*\n)?(?:\s*class InstrumentedScene[\s\S]*?pass\s*\n|\s*InstrumentedScene\s*=\s*[^\n]+\n|\s*pass\s*\n)',
                        '',
                        code_script
                    )
                    fallback_code = re.sub(r'^\s*from feedback_functions(?:_vlm)?\.instrumented_scene import InstrumentedScene\s*\n', '', fallback_code, flags=re.MULTILINE)
                    fallback_code = fallback_code.replace(
                        "class FinalScene(InstrumentedScene, MovingCameraScene)",
                        "class FinalScene(MovingCameraScene)"
                    )
                    fallback_code = fallback_code.replace(
                        "class FinalScene(InstrumentedScene)",
                        "class FinalScene(MovingCameraScene)"
                    )
                    fallback_code = sanitize_manim_code(fallback_code, script_path=output_file)
                    with open(output_file, 'w', encoding="utf-8") as f:
                        f.write(fallback_code)
                    print(f"Saved fallback code for group {group} to {output_file}")

                    # Invalidate downstream stale files for this group even on fallback
                    downstream_paths = [
                        os.path.join(base_folder, "manim_time_synced_code", f"group_{group}.py"),
                        os.path.join(base_folder, "manim_time_synced_videos", f"group_{group}.mp4"),
                        os.path.join(base_folder, "audio_integrated_videos", f"group_{group}_final.mp4")
                    ]
                    for dp in downstream_paths:
                        if os.path.exists(dp):
                            try:
                                os.remove(dp)
                                print(f"  [Invalidated] Removed stale downstream file: {dp}")
                            except Exception as del_err:
                                print(f"  [Warn] Failed to remove {dp}: {del_err}")
                except Exception as fb_err:
                    print(f"Failed to write fallback for group {group}: {fb_err}")

        # Verify all expected scene code files exist
        missing_scenes = []
        for grp in storyboard.keys():
            expected_file = os.path.join(styled_scenes_dir, f"group_{grp}.py")
            if not os.path.exists(expected_file):
                missing_scenes.append(grp)
        if missing_scenes:
            raise RuntimeError(f"Styled code files missing for scenes: {missing_scenes}")

        # Copy official Simplilearn templates and intro_icons into styled_scenes_dir
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for tmpl in ["template1_title_intro.py", "template2_learning_roadmap.py", "template3_topic_coverage.py", "template4_process_flow.py", "template5_action_flowchart.py", "vector_primitives.py"]:
            tmpl_src = os.path.join(script_dir, "helpers", tmpl)
            if not os.path.exists(tmpl_src):
                tmpl_src = os.path.join(os.path.dirname(script_dir), "template", tmpl)
            if os.path.exists(tmpl_src):
                shutil.copy2(tmpl_src, styled_scenes_dir)

        icons_src = os.path.join(script_dir, "helpers", "intro_icons")
        if not os.path.exists(icons_src):
            icons_src = os.path.join(os.path.dirname(script_dir), "template", "intro_icons")
        if os.path.exists(icons_src):
            shutil.copytree(icons_src, os.path.join(styled_scenes_dir, "intro_icons"), dirs_exist_ok=True)

        return styled_scenes_dir

    def process_files(self, target_topic_id=None):
        """Main logic to process unprocessed files."""
        input_tracker = self._load_tracker(self.input_tracker_path)
        if not input_tracker:
            print(f"Input tracker is empty or missing: {self.input_tracker_path}")
            return

        print(f"Found {len(input_tracker)} items in input tracker.")

        for topic_id, input_entry in input_tracker.items():
            if target_topic_id and topic_id != target_topic_id:
                continue
            if not input_entry.get("processed", False):
                continue

            output_tracker = self._load_tracker(self.output_tracker_path)
            if topic_id in output_tracker and output_tracker[topic_id].get("processed", False):
                continue

            print(f"Processing {topic_id}...")
            base_folder = os.path.join(self.input_folder, topic_id)
            config_path = os.path.join(base_folder, "ex_config.json")
            
            if not os.path.exists(config_path):
                continue
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                output_file_path = self.generate_styling_corrections(config_data, topic_id)
                
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": output_file_path,
                    "processed": True,
                    "topic_name": topic_id,
                    "topic_id": topic_id,
                    "failure_reason": None
                }
                self._save_tracker(self.output_tracker_path, tracker)

                # Reset downstream trackers so stages 21 and 22 are guaranteed to run
                tracker_dir = os.path.dirname(self.output_tracker_path)
                downstream_trackers = [
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

                print(f"Successfully processed {topic_id}.")

            except Exception as e:
                print(f"Error processing {topic_id}: {e}")
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

    vlm_fixing_stage_tracker = os.path.join(trackers_dir, "19_vlm_fixing_stage_tracker.json")
    eng_correction_styling_tracker = os.path.join(trackers_dir, "20_eng_corrections_tracker.json")
    stage = FinalStylingCorrections(
        input_tracker_path=vlm_fixing_stage_tracker, 
        google_api_key=os.environ.get("GOOGLE_API_KEY"), 
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        output_tracker_path=eng_correction_styling_tracker, 
        input_folder=data_dir
    )
    stage.process_files()
