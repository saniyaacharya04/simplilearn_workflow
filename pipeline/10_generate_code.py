#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 10: MANIM CODE GENERATION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 10
   - Script Name: 10_generate_code.py
   - Primary Class: CodeGenerator
   - Pipeline Role:
     Synthesizes initial, executable Manim Community Python scripts (group_1.py,
     group_2.py, etc.) inside the manim_codes/ directory. Integrates narration timing
     from CGI_Input.json, styles from Stage 9, and asset geometry. Automatically
     embeds diagnostic feedback instrumentation (feedback_functions/) and runs code
     through the AST code sanitizer (code_sanitizer.py) to resolve syntax hazards,
     prevent title stacking, clamp macro containers, and enforce formula contrast.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 9 (9_styling_generator.py):
       - How: Ingests styling_instructions_<model>.json via 9_styling_output_tracker.json.
       - Purpose: Provides exact hex color palettes, font sizes, container dimensions,
         and visual hierarchy for each scene element.
     * Stage 5 (5_populate_audio_runtime.py):
       - How: Ingests CGI_Input.json.
       - Purpose: Matches code animation sections to audio durations and statement keys.
     * Stage 2 (2_asset_classification.py):
       - How: Ingests detailed_instructions_<model>.json.
       - Purpose: Supplies classified asset inventories and image paths.
     * Stage 1 (1_generate_instructional_design.py):
       - How: Ingests instructions_<model>.json.
       - Purpose: Spoken narration and pedagogical step context.
     * Instrumentation Package:
       - How: Copies helper modules from feedback_functions/ (feedback_config.py,
         layout_feedback.py) into the topic directory to record object positions.
   - Input Tracker: ppt_trackers/9_styling_output_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * styling_instructions_<model>.json (Stage 9):
       Location: data_ppt_advanced/<TOPIC_NAME>/styling_instructions_<model>.json
       Content: Styling specifications for all scenes.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Time-coded narration manifest with audio durations.
     * detailed_instructions_<model>.json (Stage 2):
       Location: data_ppt_advanced/<TOPIC_NAME>/detailed_instructions_<model>.json
       Content: Classified visual assets.
     * instructions_<model>.json (Stage 1):
       Location: data_ppt_advanced/<TOPIC_NAME>/instructions_<model>.json
       Content: Step narration statements.
     * feedback_functions/ helper templates:
       Location: feedback_functions/
       Content: Instrumentation probes for recording element bounding boxes during render.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Configuration specifying 'coding_api' and 'coding_model_name'.
     * Input Tracker:
       Location: ppt_trackers/9_styling_output_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 9_styling_output_tracker.json.
   - Step 2: Injects instrumentation helpers (feedback_config.py, layout_feedback.py) into folder.
   - Step 3: Generates prompt payload combining style tokens, timing constraints, asset specs,
     and Manim best practices.
   - Step 4: Dispatches code synthesis requests to LLM (Gemini, Claude, or Groq/Together).
   - Step 5: Extracts raw python code from markdown code fences.
   - Step 6: Passes generated code through code_sanitizer.sanitize_file():
     * Unwraps nested animations (FadeIn(UpdateFromAlphaFunc(...))).
     * Replaces Transform(title, title2) with ReplacementTransform to prevent duplicate titles.
     * Injects self.remove(*self.mobjects) on step title transitions to eliminate header title stacking.
     * Clamps macro containers (height <= 4.8, top edge y <= 1.70) to prevent header slicing.
     * Auto-assigns C_DARK_BLUE to uncolored MathTex to prevent contrast washout.
   - Step 7: Writes finalized executable scripts into manim_codes/group_{n}.py.
   - Step 8: Atomically updates 10_code_generation_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * manim_codes/ directory:
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_codes/
       Content: Executable Python Manim scene scripts (group_1.py, group_2.py, etc.).
     * Instrumentation files:
       Location: data_ppt_advanced/<TOPIC_NAME>/feedback_config.py, layout_feedback.py
       Content: Runtime probe helpers for bounding box and layout state logging.
     * Output Tracker:
       Location: ppt_trackers/10_code_generation_tracker.json
       Content: Atomic tracker confirming initial Manim code generation.

6. DOWNSTREAM CONSUMERS:
   - Stage 11 (11_run_manim_for_feedback.py): Test-compiles generated scripts in Manim.
   - Stage 13 & 14: Uses original scripts as baseline for syntax & layout error fixes.
================================================================================
"""

import json
import os
import sys
import glob
import portalocker
import time
import shutil
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dotenv import load_dotenv
load_dotenv()

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from google import genai
from google.genai import types
from anthropic import Anthropic
try:
    from together import Together
except ImportError:
    Together = None

# Scene titles are resolved dynamically from presentation composition, storyboard blueprint, or styling specs
TOPIC_SCENE_TITLES = {}

try:
    from groq import Groq
except ImportError:
    Groq = None
from dotenv import load_dotenv
load_dotenv()
try:
    from pipeline.code_sanitizer import sanitize_file
except ImportError:
    from code_sanitizer import sanitize_file


def load_reference_design_patterns(topic_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Loads contrastive reference design patterns (positive motion graphics vs. negative static boxes)
    from reference_design_pattern.json to ground Manim code generation in dynamic vector choreography.
    """
    candidates = []
    if topic_dir:
        candidates.extend([
            Path(topic_dir) / "reference_design_pattern.json",
            Path(topic_dir) / "metadata_blueprints" / "reference_design_pattern.json",
        ])
    candidates.extend([
        PROJECT_ROOT / "reference_design_pattern.json",
        SCRIPT_DIR / "reference_design_pattern.json",
        Path.cwd() / "reference_design_pattern.json"
    ])

    for cand in candidates:
        if cand.exists():
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    patterns = json.load(f)
                lines = [
                    "\n### CONTRASTIVE MOTION GRAPHICS BENCHMARKS (CODE GENERATION GUIDELINES):",
                    "Study the contrastive benchmarks below to implement dynamic kinetic vector choreography instead of static PPT slide containers:\n"
                ]
                for k, v in patterns.items():
                    p_type = v.get("type", f"pattern_{k}")
                    pos = v.get("positive_pattern", "").strip()
                    neg = v.get("negative_pattern", "").strip()
                    lines.append(f"--- BENCHMARK EXAMPLE {k} ({p_type}):")
                    if pos:
                        lines.append(f"[POSITIVE BENCHMARK - ADOPT THIS KINETIC CHOREOGRAPHY]:\n{pos}\n")
                    if neg:
                        lines.append(f"[NEGATIVE ANTI-PATTERN - STRICTLY AVOID THIS STATIC PPT BOXING]:\n{neg}\n")
                return "\n".join(lines)
            except Exception:
                pass
    return ""


def generate_simplilearn_manim_template(
    group: str,
    layout: str = "70",
    title: str = "Technical Architecture",
    lead_in: str = "",
    cards: Optional[List[Dict[str, Any]]] = None,
    run_time: float = 20.0
) -> str:
    """
    Synthesizes broadcast-grade Manim Community 0.21.0 Python scripts in 100% compliance
    with Simplilearn OSL 3.0 Guidelines:
      - 100% Open Sans typography (Bold 40-45px headings, Regular 20-34px body)
      - Simplilearn Brand Blue Band (#2C81FE) and Dark Slate/Charcoal text (#0F172A / #404040)
      - 10-Color Pastel Infographic Palette (Sky Blue #62B7E4, Steel Blue #7EA2C8, Lavender #9B99C7,
        Mint #8ECDB7, Warm Amber #E6A157, Mustard Gold #DDB945, Coral #E58F6D, Tan #B88968,
        Dusty Rose #D98CA1, Soft Lilac #C1A5C6)
      - Corner Radius = 10px (0.074 Manim scene units)
      - Vibrant Focus Highlight (#F78908, 3.5px stroke, fill_opacity=0)
      - Zero Green containers or cards
      - Zero 3D elements, zero drop shadows
      - Frame-accurate audio sync matching scene run_time
    """
    clean_title = re.sub(r'["\n\r]', '', str(title)).strip()[:55]
    clean_lead = re.sub(r'["\n\r]', '', str(lead_in)).strip()[:70] if lead_in else ""

    def parse_card(c: Any, idx: int) -> Dict[str, str]:
        if isinstance(c, str):
            c_title = f"Component {idx + 1}"
            c_body = c
        elif isinstance(c, dict):
            c_title = c.get("title") or c.get("card_title") or c.get("heading") or c.get("name") or f"Component {idx + 1}"
            c_body = c.get("body") or c.get("card_text") or c.get("text") or c.get("description") or "Autonomous system execution and verification."
        else:
            c_title = f"Component {idx + 1}"
            c_body = "Autonomous system execution and verification."

        c_title = re.sub(r'["\n\r]', '', str(c_title)).strip()[:36]
        c_body = re.sub(r'["\r]', '', str(c_body)).strip()

        words = c_body.split()
        lines = []
        curr = []
        for w in words:
            curr.append(w)
            if len(" ".join(curr)) > 38:
                lines.append(" ".join(curr[:-1]))
                curr = [w]
        if curr:
            lines.append(" ".join(curr))
        wrapped_body = "\\n".join(lines[:2])
        return {"title": c_title, "body": wrapped_body}

    raw_cards = cards or []
    parsed_cards = [parse_card(c, idx) for idx, c in enumerate(raw_cards)]
    while len(parsed_cards) < 3:
        idx = len(parsed_cards)
        defaults = [
            {"title": "Perception Stream", "body": "Receives multi-modal inputs\\nand telemetry data."},
            {"title": "Reasoning Core", "body": "Executes state planning and\\ndeliberative cycles."},
            {"title": "Tool Execution", "body": "Dispatches validated actions\\nwith safety guarantees."}
        ]
        parsed_cards.append(defaults[idx % len(defaults)])

    color_palette = ["#62B7E4", "#7EA2C8", "#9B99C7", "#E6A157", "#8ECDB7", "#DDB945", "#E58F6D", "#B88968"]

    # Check for Simplilearn OSL 3.0 Standard Canonical Pure Template Cases
    grp_str = str(group).strip()
    norm_t = clean_title.lower()
    
    # Title template is for Scene 1 or dedicated title intro splash
    is_title_template = (grp_str == "1" or "title splash" in norm_t or "introduction" in norm_t or "topic intro" in norm_t)
    
    # Roadmap template is for Scene 3 or learning objectives / roadmap scenes
    is_roadmap_template = (grp_str == "3" or any(kw in norm_t for kw in ["learning objectives", "learning outcomes", "roadmap", "what you will learn"]))
    
    # What's next template is for Scene 9 or next topic / closing transition scenes
    is_whats_next_template = (grp_str == "9" or any(kw in norm_t for kw in ["what is next", "what's next", "next topic", "next steps", "demo launch", "hands-on"]))

    if is_title_template:
        eff_runtime = max(3.0, float(run_time))
        return f'''from manim import *
from feedback_functions.instrumented_scene import InstrumentedScene
from template1_title_intro import play_title_intro, CrispText

class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        play_title_intro(
            self,
            topic_title="{clean_title}",
            course_name="Artificial Intelligence and Agentic Workflows",
            duration={eff_runtime:.2f},
        )
'''

    if is_roadmap_template:
        bullets_list = [f"{c['title']}: {c['body'].replace(chr(92)+'n', ' ')}" for c in parsed_cards[:4]]
        per_bullet = round(max(2.5, (float(run_time) - 2.0) / max(1, len(bullets_list))), 2)
        durations_list = [per_bullet] * len(bullets_list)
        return f'''from manim import *
from feedback_functions.instrumented_scene import InstrumentedScene
from template2_learning_roadmap import play_learning_roadmap, CrispText

class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        play_learning_roadmap(
            self,
            bullets={bullets_list!r},
            header_text="By the end of this topic, you will be able to:",
            bullet_durations={durations_list!r},
            hold_duration=2.5,
        )
'''

    if is_whats_next_template:
        bullets_list = [f"{c['title']}: {c['body'].replace(chr(92)+'n', ' ')}" for c in parsed_cards[:3]]
        per_bullet = round(max(2.5, (float(run_time) - 2.5) / max(1, len(bullets_list))), 2)
        durations_list = [per_bullet] * len(bullets_list)
        return f'''from manim import *
from feedback_functions.instrumented_scene import InstrumentedScene
from template3_topic_coverage import play_topic_coverage, CrispText

class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        play_topic_coverage(
            self,
            bullets={bullets_list!r},
            header_text="In the next topic, you will learn about:",
            bullet_durations={durations_list!r},
            hold_duration=2.5,
            dissolve_to_white=True,
        )
'''

    # For all other scenes that are not pure canonical templates, return None
    # to guarantee 100% full LLM synthesis (gemini-3.8-flash) with living vector mechanics.
    return None


class CodeGenerator:
    """
    Stage 10: Manim Code Generation.
    Synthesizes initial executable Manim Community Python scripts (group_1.py ... group_N.py)
    in manim_codes/, incorporating design styles, audio durations, and instrumentation.
    """

    def __init__(
        self,
        input_tracker_path=None,
        output_tracker_path=None,
        google_api_key=None,
        claude_api_key=None,
        input_folder=None
    ):
        # Store required class variables
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        self.claude_api_key = claude_api_key or os.environ.get("CLAUDE_API_KEY")
        self.input_folder = input_folder
        
        # Initialize output tracker file if specified and doesn't exist
        if self.output_tracker_path and not os.path.exists(self.output_tracker_path):
            tracker_dir = os.path.dirname(self.output_tracker_path)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
                
            with open(self.output_tracker_path, 'w',encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

    def remove_code_fences(self, text: str) -> str:
        """
        Removes ```python ... ``` or ``` ... ``` wrappers
        from the beginning and end of a string.
        """
        return re.sub(
            r"^\s*```(?:python)?\s*\n?(.*?)\n?```\s*$",
            r"\1",
            text,
            flags=re.DOTALL
        )

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



    def parse_input_to_json(self,input_text):
        lines = input_text.strip().splitlines()
        output = {}
        scene_number = None
        current_instruction_lines = []

        def flush_instruction():
            nonlocal current_instruction_lines
            if not current_instruction_lines:
                return
            
            content = " ".join(current_instruction_lines).strip()
            if content and scene_number:
                if scene_number not in output:
                    output[scene_number] = []
                output[scene_number].append({"matching_section": content})
            current_instruction_lines = []

        for line in lines:
            # Normalize
            line = re.sub(r"\*\*", "", line).strip()
            
            if not line:
                continue

            # --- Instruction header ---
            if re.match(r"^-?\s*Instruction(?:\s*\d+)?\s*[:.]", line, re.IGNORECASE):
                flush_instruction()
                content_match = re.match(r"^-?\s*Instruction(?:\s*\d+)?\s*[:.]\s*(.*)", line, re.IGNORECASE)
                if content_match and content_match.group(1).strip():
                    current_instruction_lines.append(content_match.group(1).strip())
                continue

            # --- Scene header ---
            scene_match = re.search(r"\bScene\s*(\d+)\b", line, re.IGNORECASE)
            if scene_match:
                flush_instruction()
                scene_number = scene_match.group(1)
                output[scene_number] = []
                continue

            # --- Content lines ---
            if scene_number is not None:
                current_instruction_lines.append(line)

        flush_instruction()
        return output


    def compare_structures(self,input_dict, output_dict):
        """Compare structures of input and output JSON"""
        def describe_object_structure(obj, obj_name):
            structure = {}
            for key in sorted(obj.keys()):
                if isinstance(obj[key], list):
                    structure[key] = ("list", len(obj[key]))
                elif isinstance(obj[key], dict):
                    structure[key] = ("dict", len(obj[key]))
                else:
                    structure[key] = (type(obj[key]).__name__, 1)
            return structure
        
        input_structure = describe_object_structure(input_dict, "Input")
        output_structure = describe_object_structure(output_dict, "Output")
        
        all_keys = set(input_structure.keys()).union(set(output_structure.keys()))
        
        mismatch = False
        for key in sorted(all_keys):
            input_val = input_structure.get(key)
            output_val = output_structure.get(key)
            
            if input_val is None:
                print(f"🆕 Key '{key}' only in Narration Section → Type: {output_val[0]}, Elements: {output_val[1]}")
                mismatch = True
            elif output_val is None:
                print(f"🗑️ Key '{key}' only in Matching Section → Type: {input_val[0]}, Elements: {input_val[1]}")
                mismatch = True
            elif input_val != output_val:
                print(f"⚠️ Key '{key}' differs:")
                print(f"   Matching Section → Type: {input_val[0]}, Elements: {input_val[1]}")
                print(f"   Narration Section → Type: {output_val[0]}, Elements: {output_val[1]}")
                mismatch = True
            else:
                print(f"✅ Key '{key}' is identical → Type: {input_val[0]}, Elements: {input_val[1]}")
        return mismatch

    def generate_code(self, config_data, topic_id, theme):
        """
        Function for the generate_code logic.
        This would typically call the LLM APIs using the API keys and prompts.
        """
        print(f"  [Simulated] Running generate_code for {topic_id} using keys: {self.google_api_key[:5]}... / {self.claude_api_key[:5]}...")
        
        base_folder = config_data.get('base_folder', os.getcwd())
        asset_class_model_name = config_data.get('asset_class_model_name', 'gemini-3.8-flash')
        asset_builder_model_name = config_data.get('asset_builder_model_name', 'gemini-3.8-flash')

        scene_coding_vendor = config_data.get('scene_coding_vendor', 'google')
        scene_coding_model_name = config_data.get('scene_coding_model_name', 'gemini-3.8-flash')
        guideline_vendor = config_data.get('styling_vendor', 'google')
        guideline_model_name = config_data.get('styling_model_name', 'gemini-3.8-flash')
        theme = config_data.get('theme', 'dynamic_learning')
        clean_lesson_title = config_data.get('lesson_title') or config_data.get('topic_name') or topic_id.replace('_', ' ').title()

        google_client = None
        g_key = self.google_api_key or os.environ.get("GOOGLE_API_KEY")
        if g_key:
            try:
                google_client = genai.Client(api_key=g_key)
            except Exception:
                pass

        if scene_coding_vendor in ["google", "gemini"]:
            if not google_client and g_key:
                google_client = genai.Client(api_key=g_key)
        elif scene_coding_vendor == "claude":
            client = Anthropic(
                api_key=self.claude_api_key,
                timeout=800
            )
        elif scene_coding_vendor == "moonshot":
            os.environ["TOGETHER_API_KEY"] = "8f20540c213354bc6b03aa42901af2bd99b8bea6b704a0ca0a882facd2878299"
            client_kimi = Together()
        elif scene_coding_vendor == "qwen":
            client_qwen = Groq(
                api_key=os.environ.get("GROQ_API_KEY"),
            )

        #All helper functions

        crisp_text_rules = """- Use `CrispText(text, size=24, font="Open Sans", weight=BOLD, color=...)` for all non-math text (available in global scope; 100% Open Sans family).
        - Multi-line text: Include `\\n` in the text string with optional `align="center"`, `"left"`, or `"right"`.
        - Never embed LaTeX inside `CrispText`."""

        table_rules = """- Represent structured tabular data using `MobjectTable(table_content, col_labels=col_labels)`:
          * Outline & Grid: Set `include_outer_lines=True` with `line_config={"stroke_color": C_LIGHT_BLUE, "stroke_width": 1.5}`, `h_buff=0.4`, `v_buff=0.25`.
          * Background & Contrast: Add an opaque white background rectangle (`opacity=1.0`, `z_index=-2`) and an explicit dark header rectangle (`C_DARK_BLUE`, `z_index=-1`) behind row 0 so table headers have bold contrast."""

        code_rules = """- Represent source code snippets using Manim's `Code()` construct:
          * Configuration: `Code(code_string=..., language=..., tab_width=4, background="window", formatter_style="monokai", add_line_numbers=True)`.
          * Styling: Container background should use `#010308` with a dark stroke (`#111827`, width 2, corner_radius 0.22) and readable typography (`paragraph_config={"font_size": 24}`)."""

        # Core prompt: dynamic system prompt exclusively used
        system_prompt_dynamic = """
        ## ROLE

        Convert a structured presentation storyboard into executable Manim Community Edition code.

        The storyboard (including narration, styling, assets, and SME framing layout) is the source of truth.

        Produce clean, deterministic presentation code.

        ---

        ## OUTPUT

        - Single class: `FinalScene(InstrumentedScene, MovingCameraScene)`
        - All logic inside `construct()`
        - Use `## Presentation Step <n>` markers
        - Return only Python code

        ---

        ## FIDELITY

        Preserve exactly:
        - instructional sequence
        - beat boundaries
        - narration alignment
        - layouts and safe placement areas
        - diagrams and data structures
        - styling and color assignments
        - typography hierarchy
        - object persistence

        Only make small spacing, scaling or timing adjustments required for rendering.
        Do not redesign the presentation.

        ---

        ## SAFE MARGINS & SCENE BOUNDARIES (OSL GUIDELINES)

        All animations and visual layouts MUST strictly comply with the Simplilearn OSL 16:9 safe margin and geometry specifications:
        
        - CAMERA & COORDINATE FRAME (1920x1080 Full HD):
          * Camera frame width: W = 128 / 9 ≈ 14.222 units (x ∈ [-7.111, +7.111]).
          * Camera frame height: H = 8.000 units (y ∈ [-4.000, +4.000]).
          * Origin (0, 0) is at the center of the screen.
          * Scale factor: 1 Manim unit = 135 pixels (1 pixel ≈ 0.007407 units).
        
        - GLOBAL SAFE WORK AREA (Layout 0):
          * Left Safe Boundary: x_min = -6.727 (2.7% margin, 52px). Action safe limit: x >= -6.40.
          * Right Safe Boundary: x_max = +6.717 (2.8% margin, 53px). Action safe limit: x <= +6.40.
          * Bottom Safe Boundary: y_min = -3.664 (4.2% margin, 45px). Safe content floor: y >= -3.50.
          * Top Clearance: y_max = +3.381 (7.7% margin, 84px).
          * Safe Content Box: width = 13.44 u, height = 7.04 u, centered at (-0.005, -0.142).
          * All non-edge-bleed content (text, cards, diagrams, tables, pills) must stay strictly inside x ∈ [-6.40, +6.40] and y ∈ [-3.50, +3.38].

        - HEADER ZONE & CONTENT CEILING (STRICT CEILING RULE):
          * Slide Title / Header Zone: y ∈ [2.40, 3.40] is reserved exclusively for the Slide Title and header indicators.
          * CONTENT CEILING (y <= 2.20): The top edge of ALL content panels, containers, cards, tables, diagrams, and section headers MUST sit strictly at or below y = 2.20 (and at or below y = 2.00 when a lead-in line is present).
          * CONTENT FLOOR (y >= -3.50): The bottom edge of any visual element must remain above y = -3.50.
          * NEVER allow content elements to collide with, cross, or crowd the top header zone!

        - STRICT BOUNDARY ENFORCEMENT & OVERFLOW PREVENTION:
          * Zero Out-of-Bounds Bleed: Under no circumstances may text, icons, cards, or diagrams extend past |x| > 6.40 or |y| > 3.60.
          * Multi-line Text Wrapping: Wrap text using explicit newlines (`\n`) to preserve uniform font sizes without horizontal spill.
          * Dynamic Card Height: All cards and container shapes MUST dynamically expand their height based on text content (`box_h = max(min_h, text_mob.height + 2 * padding)`). NEVER call `.scale_to_fit_width()` on text.
          * Spacing & Visual Gutters: Maintain clear padding (`buff >= 0.25` to `0.35`) between all cards, badges, arrows, and labels to prevent visual collision.

        ---

        ## SME (INSTRUCTOR) WINDOW PLACEHOLDER & DYNAMIC FRAMING

        Every scene in the storyboard specifies an SME layout archetype (`sme_layout` or `sme_positioning`).
        You MUST respect the reserved rectangular placeholder for the instructor video feed and prevent any content from overlapping the SME:

        1. LAYOUT 3: 70% LEFT SPLIT (`sme_layout == "70"` / `70_left_rounded_rect`):
           - Instructor Window: The left side of the screen is strictly reserved for the SME feed and blue accent band:
             * Left Blue Band: x ∈ [-7.111, -5.322], width ≈ 1.79, height = 8.00 (center x ≈ -6.22, color `#2C81FE`).
             * Cropped SME Rounded Rect: center (-3.687, -0.023), width = 4.937, height = 5.349 (bounds x ∈ [-6.155, -1.218], y ∈ [-2.698, +2.651]), corner_radius = 0.074 (10px).
           - MANDATORY RESERVED PLACEHOLDER: Keep the entire left region (x <= -1.48) completely open and clear for the instructor video feed.
           - PRESENTATION SAFE WORKSPACE: All instructional graphics (cards, diagrams, bullet points, flowcharts, tables, takeaway notes) MUST live strictly in the right 60% safe area:
             * Safe Content Workspace: x ∈ [-0.80, +6.40], y ∈ [-3.60, +2.20]. Center x ≈ +2.80.
           - TITLE & SUBTITLE SAFE ALIGNMENT:
             * Slide Title: Left-anchor at x = -0.80 (`create_title` automatically positions header_grp with left edge at -0.80).
             * Subtitle: MUST be left-aligned to `header_grp` (`aligned_edge=LEFT`) at x = -0.80, with maximum width <= 7.0 units. NEVER center subtitles at screen center x = 0.0!
           - ZERO CONTENT OVERLAP: Absolutely NO presentation content may be placed to the left of x = -0.80! Never place full-width diagrams or center-aligned full-screen panels in a 70% SME layout.

        2. LAYOUT 2: 20% TOP-RIGHT PiP (`sme_layout == "20"` / `20_top_right_pip`):
           - Instructor Window: The top-right corner is strictly reserved for the 20% SME trainer window (384x216 at 1496, 40):
             * 20% SME PiP Box: bounds x ∈ [+3.800, +7.111], y ∈ [+2.000, +4.000].
           - MANDATORY RESERVED PLACEHOLDER: The top-right quadrant (x >= +3.500 and y >= +1.800) is strictly off-limits for presentation graphics and text.
           - HEADER & LEAD-IN COLLISION RULE: Scene headers, kickers, lead-in boxes, and banners MUST strictly terminate at or left of x <= +3.500 so they NEVER overlap the 20% SME PiP box.
           - MAIN DIAGRAM WORKSPACE: Position diagrams and content in the lower area: x ∈ [-6.727, +6.717], strictly below y <= 1.800.
           - ZERO CONTENT OVERLAP: Absolutely NO presentation element may enter x > +3.500 when y > +1.800.

        ---

        ## VISUAL EXCELLENCE: HERO ILLUSTRATIONS & LIVING KINETIC VECTORS

        Strictly avoid static PowerPoint-style slides (plain rectangular text boxes, dense bullet lists, and static card layouts).
        A scene must NEVER be a flat static slide!
        Follow the canonical DYNAMIC VISUAL STANDARD:
        1. Mandatory Hero Illustration Asset Integration:
           - Whenever image paths are provided under `------------Image Paths------------` (e.g. character illustrations, sensor panels, neural cores, tool hubs), you MUST load and display them using `ImageMobject(image_path).scale_to_fit_height(...)` mounted cleanly with balanced typography plinths.
           - NEVER ignore provided image assets or replace them with crude stick figures or basic line sketches!
           - Always wrap image assets in `Group(...)` (not `VGroup`) and anchor them as hero visual centerpieces.
        2. Procedural Manim Vector Mechanisms & Living Schematics (NEVER STATIC):
           - Surround hero images and core concepts with dynamic, kinetic Manim vector mechanics:
             * Rotating mechanical cogs and planetary gear trains (for action execution and tool actuation).
             * Continuous rotating radar sweeps (`DynamicRadarSweep`) with active scan lines and pulsing concentric rings (for perception and monitoring).
             * Pulsing neural halo clusters (`NeuralHaloPulses`) with glowing core nodes and kinetic dendrites (for LLM reasoning and cognition hubs).
             * Isometric multi-tier database disk stacks (for short-term context and long-term memory storage).
             * Dynamic continuous loops with animated dashed trajectories and flowing data packets (for agent-environment interaction loops).
             * Live telemetry dials, sweeping gauges, and responsive meters (for monitoring and threshold alerts).
             * Continuous updaters (`add_updater`) to keep background grids, orbital nodes, flow indicators, and telemetry sweeps continuously moving throughout the entire scene duration.
        3. Semantic Kinetic Vector Animation Toolkit:
           - Run live procedural Manim vector animations over or alongside cards, contextually selected by semantic domain:
             * `FlowingStream` / Dynamic Conduits (for data pipelines, network streams, and component messaging).
             * `TelemetryWaves` / Waveforms (for sensor telemetry, time-series signals, and continuous monitoring).
             * `PulsingShockwaves` / Beacon Pulses (for alerts, anomaly notifications, and threshold crossings).
             * `NeuralHaloPulses` / `DynamicRadarSweep` (for computational deliberation, AI reasoning hubs, and scanning loops).
             * `BalanceScale` / Rigging Assemblies (for multi-objective trade-offs, Pareto optimizations, and risk vs return).
             * Or construct custom procedural physical/mathematical animations tailored to the topic domain.
        3. Minimal Bold Cognitive Anchors & Clean Typography:
           - Every card, stage, or component has an explicit, high-contrast, bold title badge (1–3 words max, e.g. 'Data Ingest', 'Memory Layer', 'Safety Gate', 'Execute Action').
           - NO dense multi-line bullet lists. Zero text clutter!
        4. Calm Pacing & Narration Synchronization:
           - Use `self.sync_to(t)` with exact voiceover timestamps so elements stay persistent while the teacher speaks. Avoid rushing or flashing.

        3. LAYOUT 1: 100% FULL-SCREEN PRESENTER (`sme_layout == "100"` / `100_full_screen`):
           - Instructor Window: The SME occupies the full screen (x ∈ [-7.111, +7.111], y ∈ [-4.000, +4.000]).
           - MINIMAL OVERLAY ONLY: Teacher occupies the full canvas. No intrusive diagrams, cards, tables, or opaque panels. Minimal on-screen text only (e.g. subtle lower-third takeaway banner or clean caption).

        4. LAYOUT 0: 0% FULL CONTENT ARENA (`sme_layout == "0"` / full slide):
           - No instructor video feed on screen.
           - Full central arena (|x| <= 6.40, y ∈ [-3.60, +2.20]) is available for diagrams, horizontal pipelines, comparison columns, or tables, centered horizontally at x = 0.

        5. LAYOUT 4: LEARNING OBJECTIVE & WHAT'S NEXT TEMPLATE:
           - Left SME Placeholder: Full-height vertical region on left (x ∈ [-7.111, -2.431]).
           - Right Floating White Card: center (+2.037, -0.425), width = 8.936, height = 5.674 (bounds x ∈ [-2.431, +6.505], y ∈ [-3.262, +2.412]).

        ---

        ## STYLING & DESIGN SYSTEM (OSL 3.0 & STYLING GENERATOR COMPLIANCE)

        The storyboard and Styling Generator specifications are the authoritative sources of truth for visual design.
        When `Styling Generator Specifications` or `styled_blocks` are provided in the Scene Context, you MUST strictly implement the exact styling tokens, colors, typography, container shapes, and focus highlights defined:

        - CANVAS THEME & BACKGROUND (MODERN SOFT TECH SLATE):
          * Read `Background Color` from Styling Generator specifications:
            - Standard Infographic Canvas (`canvas_theme: light_infographic_canvas`): Strictly set `self.camera.background_color = "#FFFFFF"` (Pure Crisp White Canvas per Simplilearn guidelines).
            - Full-Screen Trainer Canvas (`canvas_theme: full_screen_trainer`, Layout 100): Set `self.camera.background_color = "#0F172A"`. Text colors invert to `#FFFFFF`.
          * PROHIBITED: Do NOT create giant full-screen RoundedRectangle or macro background container boxes boxing the entire scene.

        - 10-COLOR INFOGRAPHIC PASTEL PALETTE:
          * Visual components, pill tags, node badges, and diagram paths MUST use the assigned colors from the approved 10-color infographic pastel palette:
            - Sky Blue: `#62B7E4`
            - Steel Blue: `#7EA2C8`
            - Lavender Periwinkle: `#9B99C7`
            - Mint Seafoam: `#8ECDB7`
            - Warm Amber: `#E6A157`
            - Mustard Yellow: `#DDB945`
            - Coral Peach: `#E58F6D`
            - Warm Tan: `#B88968`
            - Dusty Rose: `#D98CA1`
            - Soft Lilac: `#C1A5C6`
          * Strictly assign each component its specified `border_color` / `accent_color` from this palette.

        - STRICT GREEN COLOR MINIMIZATION (CLIENT MANDATE):
          * Zero green cards, containers, pills, backgrounds, borders, or body text!
          * Green (`#06C170`, `#2D6A4F`, `C_GREEN`) is strictly prohibited. Only tiny micro-icons (like a small checkmark) may use green if indispensable.

        - INSTRUCTIONAL PROMPTING GUIDELINES (STRICT COMPLIANCE MANDATE):
          * MINIMALISTIC SCREEN: Exactly 1 to 2 focal objects centerstage at any given time. Never clutter the screen with multiple complex diagrams at once.
          * LOW TEXT ARCHITECTURE: Use low text with strategically placed annotations (1 to 3 words per label/badge). STRICTLY ZERO tabular grids, ZERO multi-column data matrices, ZERO paragraphs.
          * CUES ON PICTOGRAMS & ICONS: Rely on rich vector pictograms, symbols, and picture icons rather than text lists.
          * VISUALLY RICH FRAMEWORKS: Build or instantiate living vector primitives:
            - `VectorFlywheelMechanism`: Revolving 3-stage PRA cycle (Perception, Reasoning, Action) with gear rim, feedback flow arcs, and continuous rotation.
            - `VectorInfinityLoopBridge`: Parametric figure-8 lemniscate bridging Agent and Environment with waypoint callouts (Observe, Decide, Execute, Re-evaluate) and continuous traveling packet dots.
            - `VectorContextFunnel`: 3-stage tapered ingestion funnel with intake nozzles and working context buffer reservoir.
            - `VectorQuadChamberCore`: Expansive 4-chamber engine core spanning full Layout 20 canvas with continuous orbital synchronization ring.
            - `VectorMarketingFunnel`: Descending 4-tier conversion funnel with continuous particle trickle flow updater.
            - `Vector2x2Matrix`: 4-quadrant executive matrix (Impact vs Effort, SWOT) with quadrant focus bounds and project coordinate plotting.
            - `VectorKPIGaugeCard`: Executive metric dial card with semicircular meter, live needle oscillation, and prominent numerical counter readout.
            - `VectorRiskHeatmap`: 3x3 Impact vs Likelihood severity grid with pastel zones, coordinate axes, and critical attention pulse border.
            - `VectorAgileSprintCycle`: Continuous circular sprint loop with 4 milestone pods and traveling orbit dot.
            - `VectorRACIMatrix`: Structured table with role headers, deliverable rows, and color-coded R/A/C/I pills.
            - `VectorAdvancedSolarArray`: High-fidelity 2.5D photovoltaic array with 3x2 silicon wafer cells, silver busbars, animated glass reflection glare sheen sweep, aluminum trusses, and live inverter telemetry LED.
            - `VectorMechanicalHammerTool`: Realistic 2D forged steel hammer tool resting on a pedestal with grip ribs and a dormant passive status indicator.
            - `VectorTelemetryChart`, `PremiumBalanceScale`, `PrecisionChronometerGauge`, `NeuralReasoningCore`, `ActionDispatchHub`, `VectorGoalTarget`, `VectorOperatorStation`.
          * SMOOTH MORPHING TRANSITIONS: Evolve and transform focal objects smoothly between steps; avoid abrupt cutaways or static wipes.
          * NO CAMERA MOVEMENTS: Maintain 100% steady camera framing on the 16:9 canvas per Simplilearn OSL 3.0.
          * SHORT NARRATION AUDIO-VISUAL SYNC: Keep presentation steps granular (8-15s per beat) so every spoken sentence triggers an active visual event.
          * NO DECORATIVE ELASTIC JITTER: Keep kinematics purposeful and harmonic (ambient needle jitter, particle circulation, gentle balance sway).

        - LLM CREATIVE VISUAL AUTONOMY WITH COGNITIVE ANCHORS (THE GROUP 3 STANDARD):
          * Strictly avoid boring 2005-style PowerPoint text dumps (paragraphs and bullet walls).
          * HOWEVER, "minimal text" DOES NOT MEAN ZERO TEXT OR PURE MOVING GEOMETRY!
            Pure abstract geometric shapes without labels make it impossible for learners to connect what the teacher is saying to the screen.
          * Strictly FORBID "Ghost Animations" (unlabeled abstract moving shapes).
          * Follow the canonical GROUP 3 STANDARD:
            - Pair every dynamic vector animation (sweeping radar, telemetry waves, neural halo, moving dot streams, balance scales, scanning laser) with a clean, high-contrast, brand-tinted anchor label or transparent hero illustration.
            - Kinetic Anchors & Focal Nodes: Pair dynamic mechanisms with compact focal nodes, badges, or transparent hero illustration assets. Avoid boxing living diagrams or conceptual mechanisms into rectangular PowerPoint container cards! Use floating labels, subtle micro-pills, or open vector geometry.
            - Bold Legible Typography: `CrispText(name, size=12 to 16, weight=BOLD, color=COLOR_NAVY_TITLE)`.
            - Concrete Data / Status Badges: Add sub-labels or status pills (e.g. `> "Audit Site Output"`, `Capacity: 32K Tokens`, `★ Selected Action`).
            - Text Persistence: Keep component labels visible on screen throughout the explanation of that concept. Do NOT fade them out after 0.3s.
          * When labels, badges, or tags are needed:
            - Clean Micro-Pills: Use compact rounded tags (`height=0.45`, `corner_radius=0.074`) with `#FFFFFF` or `#F8FAFC` soft fills, paired with 1.5px pastel stroke (`#62B7E4`, `#2C81FE`, `#E6A157`).
            - Bold Legible Typography: `CrispText(..., size=13 to 16, weight=BOLD, color="#404040")`.
            - Zero Dead Space: Keep diagrams compact, centered, and tightly grouped.

        - STRICT PROHIBITION OF NAVY BLUE (CLIENT MANDATE):
          * Navy Blue (#06152B, #0A2540, #0B3C5D, #1E3A8A, NAVY) is strictly PROHIBITED and is NOT part of the Simplilearn palette!
          * NEVER style visual elements, pills, badges, banners, or text with dark navy blue!
          * Badges and pills must use pure white (#FFFFFF), soft canvas (#F8FAFC), or colors from the approved 10-pastel palette. Text on light elements/canvas MUST use Primary Dark Charcoal (#404040).

        - STRICT PROHIBITION OF ALL CAPS (CLIENT MANDATE):
          * ALL CAPS is NEVER permitted anywhere on screen!
          * All titles, subtitles, headers, labels, state names, node tags, and pills MUST use Title Case (e.g. "Perception", "Agent Core", "Instant Response", "Static Tool: Passive").
          * Body descriptions and bullet points MUST use Sentence case.
          * Only standard 2-4 letter domain acronyms (e.g. "ROI", "KPI", "PMP", "CAGR", "DNA", "AI", "RAM", "DB", "API", "GDP", "EBITDA") may be uppercase.

        - FOCAL ATTENTION HIGHLIGHTS (RULE 5 & OSL 3.0 SPEC):
          * When `focus_highlight` is active (`active: True`) for an element or component:
            - Highlight Color: `HIGHLIGHT_COLOR = "#F78908"` (Warm Orange).
            - Highlight Stroke Width: `stroke_width = 3` (or `3.5`).
            - Animation: When narration directs attention to an element, animate a temporary highlight around it:
              `highlight = element.copy().set_fill(opacity=0).set_stroke(color="#F78908", width=3.5)`
              `self.play(Create(highlight), run_time=0.6)`
              Fade out cleanly when narration transitions to subsequent elements.

        - TYPOGRAPHY HIERARCHY (OPEN SANS SCALE):
          * Standard font family: `Open Sans` (100% Open Sans family across all slides and elements).
          * Slide Title (`scene_title`): `font="Open Sans"`, `weight=BOLD`, size ~28–32pt (45px line-height, ~0.33 Manim units), color `#1E293B` on light or `#FFFFFF` on dark. Title Case (Strictly NO ALL-CAPS).
          * Lead-In Line (`lead_in_line`): `font="Open Sans"`, `weight=NORMAL`, size ~20–24pt (34px line-height, ~0.25 Manim units), color `#475569`. Sentence case.
          * Component Header (`header_typography`): `font="Open Sans"`, `weight=BOLD` or `SEMIBOLD`, size ~18–20pt (28px line-height, ~0.21 Manim units), color `#1E293B`. Title Case (Strictly NO ALL-CAPS).
          * Body / Metric Tag (`body_typography`): `font="Open Sans"`, `weight=NORMAL`, size ~14–16pt (22px line-height, ~0.16 Manim units), color `#334155`. Sentence case.

        - STRICT CASING ENFORCEMENT:
          * Titles, Card Headers, and Labels: Strictly Title Case (NO ALL-CAPS, e.g. "Autonomous Execution", NEVER "AUTONOMOUS EXECUTION").
          * Lead-in lines, Bullet points, Descriptions: Strictly Sentence case.

        ---

        ## TEXT & MATH (CORE FORMATTING RULES)

        - Use `CrispText(text, size=24, font="Open Sans", weight=BOLD, color=...)` for all non-math text (available in global scope; 100% Open Sans family).
        - Multi-line text: Include `\n` in the text string with optional `align="center"`, `"left"`, or `"right"`.
        - Never embed LaTeX inside `CrispText`.
        
        - Use `MathTex` only for mathematical notation, LaTeX equations, and mathematical symbols:
          * Standalone formulas / equation cards: ALWAYS specify `font_size=18` to `font_size=22` (or scale 0.40 to 0.48). NEVER use font_size >= 28 or .scale(0.75 - 1.2)!
          * Inline math next to labels/body text: ALWAYS use `font_size=16` to `font_size=18` so mathematical symbols match adjacent text height.
          * Formula width clamping: Inside any card or sub-panel, formula width MUST NEVER exceed 2.9 units! Clamp with:
            `if hasattr(f, "width") and f.width > max_w: f.scale_to_fit_width(max_w)`
          * Formula Contrast: All `MathTex` formulas on light cards or white canvas MUST explicitly specify dark color: `color="#404040"` (or `C_TEXT`). NEVER render white formulas on light containers or white canvas!

        - STRICT UNIFORM FONT SIZING ACROSS BOXES, SHAPES & CARDS:
          * NEVER force text to fit or stretch across the width of a box using `.scale_to_fit_width(...)`. Scaling text causes jarring font disparities across sibling cards.
          * ALL related boxes, cards, flowchart shapes, comparison columns, metric blocks, and table cells MUST maintain a single UNIFORM font size (STRICTLY font_size=18 to 22, matching across all items; NEVER below 16!).
          * MULTI-LINE WRAPPING MANDATE: Whenever text exceeds the container's horizontal budget (over 28-34 characters depending on card width), insert explicit newline linebreaks (`\n`) so text wraps across 2 or 3 balanced lines while preserving base font size.
          * MICRO-PILL HEIGHT EXPANSION: Badges and micro-pills must dynamically size height and width to fit text:
            `pill_h = max(default_h, text_mob.height + 2 * pad_y)`
            Never scale text to fit; keep typography crisp. Do NOT create full-screen or half-screen slide cards or box containers for diagrams!
          * ZERO SCALING ON TEXT: Never call `.scale_to_fit_width(...)` on text objects.

        - EXECUTIVE TYPOGRAPHY HIERARCHY:
          * Slide Super-Title: 32pt to 36pt bold at top.
          * Section / Panel Header: 24pt to 28pt bold.
          * Card Titles / Container Labels: 22pt to 26pt bold.
          * Status Badges / Pills / Tags: 14pt to 16pt bold.
          * Body Statements / Descriptions / List Cards / Table Cells: STRICTLY 18pt to 20pt (NEVER below 16pt!).
          * Standalone Formulas (MathTex): ALWAYS font_size=24 to font_size=28.
          * Inline Math: 18pt to 20pt (matching adjacent text height).

        - HIGH CONTRAST & LEGIBILITY GUARANTEE (guidelines.md Section 6.2 & 6.4):
          * Never use dark text on dark backgrounds, and never use white text on light backgrounds.
          * Text on light cards/canvas MUST be dark charcoal (`#404040` / `C_TEXT`).
          * Navy blue (#0B3C5D, #06152B, #0A2540) is strictly PROHIBITED and is NOT part of the Simplilearn palette!
          * REDUCE GREEN USAGE: Avoid green for containers, cards, backgrounds, borders, or lines. Use the 10 approved infographic colors: `#8ECDB7`, `#62B7E4`, `#7EA2C8`, `#9B99C7`, `#DDB945`, `#E6A157`, `#E58F6D`, `#B88968`, `#D98CA1`, `#C1A5C6`.
          * Focus Highlight: Use `#F78908` with 3px stroke (`stroke_width=3`, draw time `1.0s`).

        - NO RAW LATEX IN CRISPTEXT:
          * Never embed raw LaTeX notation with dollar signs (e.g. `$a_n$`, `$O(n)$`) inside `CrispText`. All formulas and symbols MUST be created using `MathTex`.

        - STRICT NO ALL-CAPS MANDATE:
          * Text strings passed to `CrispText` or headers must NEVER be written in ALL CAPS.
          * Always use Title Case for headers, titles, cards, labels, and tags; use Sentence Case for body sentences and descriptions.

        - CARD DESCRIPTIONS LEFT-ALIGNED:
          * Description / body text MUST be left-aligned (`align="left"`, `aligned_edge=LEFT`). Never center explanatory text or bullet points inside cards.

        - GLOW & STROKE OVERLAYS TRANSPARENT FILL:
          * When creating glow, halo, or pulse highlights with `mob.copy().set_stroke(...)`:
          * ALWAYS chain `.set_fill(opacity=0)` on the copy:
            `glow = mob.copy().set_fill(opacity=0).set_stroke(color=..., width=...)`

        ---

        ## SLIDE TITLES (UNIVERSAL HEADER RULES)

        - Slide Title Placement:
          * Every scene / presentation step should have a clearly visible, standardized slide title in the upper header zone (y ∈ [2.4, 3.4]).
          * Position: Top-left safe zone (`UL, buff=0.42` or `[-6.0, 3.2, 0]`) or centered at top (`UP * 3.2`).
          * Initialize in Step 1: `title_group = create_title("<STEP 1 TITLE>")` and animate with `self.play(FadeIn(title_group, shift=DOWN*0.1), run_time=0.8)` or `Write(title_group)`.
          * Subsequent Steps: If the step introduces a new topic, seamlessly transition the title:
            `new_title_group = create_title("<NEW STEP TITLE>")`
            `self.play(FadeOut(title_group), FadeIn(new_title_group, shift=DOWN*0.1), run_time=0.4)`
            `title_group = new_title_group`
            If topic remains identical, keep `title_group` on screen.
          * CEILING RULE: All slide content MUST sit strictly below the header line at or below y <= 2.20.

        ---

        ## TABLES (CORE FORMATTING RULES)

        - Represent structured tabular data using `MobjectTable(table_content, col_labels=col_labels)`:
          * Outline & Grid: Set `include_outer_lines=True` with `line_config={"stroke_color": C_LIGHT_BLUE, "stroke_width": 1.5}`, `h_buff=0.4`, `v_buff=0.25`.
          * Background & Contrast: Add an opaque white background rectangle (`opacity=1.0`, `z_index=-2`) and an explicit dark header rectangle (`C_DARK_BLUE`, `z_index=-1`) behind row 0 so table headers have bold contrast.
          * Multi-Column Clearance: Guarantee >= 2.4 units of horizontal clearance between table columns. Never crowd adjacent column data.
          * Concluding steps must never render blank tables or placeholder grids without data.

        ---

        ## CODE (CORE FORMATTING RULES)

        - Represent source code snippets using Manim's `Code()` construct:
          * Configuration: `Code(code_string=..., language=..., tab_width=4, background="window", formatter_style="monokai", add_line_numbers=True)`.
          * Styling: Container background should use `#010308` with a dark stroke (`#111827`, width 2, corner_radius 0.22) and readable typography (`paragraph_config={"font_size": 24}`).

        ---

        ## IMAGES

        - Use `ImageMobject`
        - Preserve aspect ratio
        - Size using `scale_to_fit_width()` or `scale_to_fit_height()`
        - Never recolor images
        - Dynamic card containment: When placing images inside product/feature cards:
          `if hasattr(img, "height") and img.height > 1.25: img.scale_to_fit_height(1.25)`
          `if hasattr(img, "width") and img.width > (width - 0.4): img.scale_to_fit_width(width - 0.4)`
          `card_h = max(2.6, content.height + 0.35)`

        ---

        ## ANIMATION

        Motion should reinforce narration.
        Visual changes should occur when the corresponding narration discusses them, even if exact timing is not explicitly stated.

        ### Animation Granularity

        Animate instructional mobjects progressively, not as clustered groups:
        - Each meaningful sub-mobject must be introduced through its own animation call.
        - Do not animate an entire `VGroup`, `Group` or collection in a single entry animation when its children represent distinct instructional elements.
        - A group may be used for layout, positioning, persistence or transformation, but its instructional children must still be animated individually.
        - Prefer sequential `self.play()` calls for independently meaningful elements.
        - Combine elements in one animation call only when they form a single inseparable visual unit or are explicitly intended to appear simultaneously.
        - Never use `FadeIn(group)`, `GrowFromCenter(group)`, `Write(group)` or equivalent group-level entry animation merely for convenience when the group's children can be synchronized independently.
        - Preserve the storyboard's presentation order at the individual-mobject level.
        - This granularity is required so downstream audio synchronization can independently align each visual element with narration.

        Default entry animations:
        - Write or AddTextLetterByLetter for titles, headings and important text
        - GrowFromCenter for major diagrams, panels and figures
        - FadeIn (with subtle shift) for secondary elements
        - Create for lines, arrows and annotations

        Default transitions:
        - Transform, ReplacementTransform, AnimationGroup, LaggedStart, Succession, FadeOut, ShrinkToCenter.
        - Avoid decorative animation: bounce, wobble, overshoot, elastic motion, unnecessary scaling.

        ### SIMPLILEARN OUTPUT STANDARD MOTION & VISUAL BENCHMARK (HIGH QUALITY):
        To match the high-craft animation quality demonstrated in the reference output standards (e.g. simplilearn_output_standard/scene_5_6.py):

        1. ACTIVE MOTION GRAPHICS & DIAGRAM FLOW (NO STATIC SLIDE TEMPLATES):
           - In Layout 70 and Layout 20, do NOT fill the screen with static PowerPoint-style nested cards or generic container templates!
           - Build dynamic, programmatic motion graphic diagrams: flowchart nodes, directed signal arrows (Arrow, CurvedArrow), cyclical feedback loops (Perceive -> Reason -> Act), state transition matrices, and data pipeline streams.
           - Place the clean slide title in the upper header zone above the content diagram. NEVER use "Scene 1", "Scene 2", "Scene 3", etc. as title text!

        2. HIGH-CONTRAST TYPOGRAPHY & ZERO WASH-OUT:
           - Headers and Titles on light backgrounds MUST use high-contrast `#0F172A` (Dark Slate) or `#1E293B`.
           - Body text and descriptions MUST use `#334155` (Slate) or `#404040`.
           - STRICTLY NEVER render white text on light cards or light grey text on white canvas.
           - Ensure clear font hierarchy: Titles (24-28pt), Headers (18-20pt), Body (14-16pt), Pills/Badges (12-13pt).

        3. NUMBERED BULLET CARDS & BADGES:
           - For lists, takeaways, or procedural steps, wrap each item in an individual elevated sub-card (fill_color="#FFFFFF", stroke_color="#E2E8F0", corner_radius=0.074).
           - Left badge: Circular disc with number ("01", "02", "03" or "1", "2", "3") filled with theme color (#62B7E4 Sky Blue, #8ECDB7 Mint, #7EA2C8 Steel Blue), white bold text inside.
           - Right badge: Small vector line icon or status pill.

        4. WORKFLOW LOOPS & KINETIC PARTICLES:
           - For cyclical workflows, feedback loops, or directed data flows (e.g. Perceive -> Reason -> Act, Ingestion Streams, Tool Dispatch), use Arrow or CurvedArrow.
           - Animate an indicator particle (Dot(color="#F78908", radius=0.08)) traveling along the path using `MoveAlongPath(dot, arrow, rate_func=smooth, run_time=0.7)` followed by `self.remove(dot)`.

        5. RICH PROCEDURAL VECTOR GLYPHS:
           - Always construct detailed, multi-part vector glyphs rather than primitive single-shape dots or arcs:
             * Database: 3-tier stacked cylinder with subtle ellipse tops, horizontal dividing rings, and vertical depth.
             * Microchip: Silicon die with central processor core, internal circuit lines, and dual-sided connector pins.
             * Tool Execution: Interlocking vector gear paired with wrench or tool accent.
             * Sensor Waves: Concentric radar wave pulses radiating outward from a sensory transmitter disc.
             * External World: Vector globe with latitude/longitude grid rings.

        6. DYNAMIC FOCAL SPOTLIGHT & PULSE:
           - Highlight active card/node using a vibrant orange border (`#F78908`, 3.5px stroke / `stroke_width=3.5`, corner_radius matching card, 0.8s draw time) during its corresponding voiceover beat:
             `pulse = active_card.copy().set_fill(opacity=0).set_stroke(color="#F78908", width=3.5)`
             `self.play(Create(pulse), run_time=0.6)`
             `self.play(FadeOut(pulse), run_time=0.4)`

        7. SINGLE MORPHING HEADER & ZERO DUPLICATE TITLES:
           - Maintain exactly ONE slide header `title_group = create_title("<TITLE>", "<SUBTITLE>")` in the top-left safe corner.
           - Morph seamlessly between steps: `self.play(ReplacementTransform(title_group, new_title_group), run_time=0.6)`.
           - STRICT PROHIBITION: NEVER render duplicate centered titles (`create_title_centered`) or floating title badges that collide with the header zone!

        8. BALANCED MULTI-PILLAR ARCHITECTURE & SAFE MARGIN CLAMPING:
           - For multi-pillar or side-by-side diagrams (e.g. 3 or 4 pillars), arrange in a single horizontal group:
             `pillars_group = VGroup(*pillars).arrange(RIGHT, buff=0.35)`
             `pillars_group.scale_to_fit_width(12.0).move_to(DOWN * 0.3)`
           - Ensure Pillar 1 left edge never clips past `x = -6.40` and Pillar 4 right edge stays within `x = +6.40`.

        9. ABSOLUTE PROHIBITION OF DUMMY/PLACEHOLDER TEXT & TITLES:
           - NEVER render "Scene 1", "Scene 2", "Scene 3", etc. as on-screen titles or visible text! Use the real descriptive Scene Title / Step Title.
           - NEVER write "Lorem ipsum", "Panel Header", "Category 1", or generic filler text anywhere! All text on screen MUST be real technical domain terminology from the narration and visual components.
           - NEVER draw empty, plain PowerPoint card layouts. Animate actual motion graphic diagrams representing the instructional concepts.

        10. ZERO UNWANTED SMALL-FONT TEXT & NO PPT BULLET-POINT WALLS (EXECUTIVE DIRECTIVE):
           - Strictly prohibit dense bullet-point walls in micro fonts (<10pt or <14pt), such as technical specification bullet lists ("• Latency: 12ms", "• Protocol Decoupling", "• State Loss: 0.00%").
           - Micro-font bullet clutter resembles unstyled presentation slides and severely compromises broadcast production value.
           - Clutter is strictly prohibited. Keep on-screen typography bold, clean, and punchy. Use concise Title Case labels, high-visibility status pills, and active kinetic motion graphics rather than PowerPoint-style bullet walls.

        11. STRICT PROHIBITION OF NAVY BLUE (CLIENT MANDATE):
           - Navy Blue (#06152B, #0A2540, #0B3C5D, #1E3A8A, NAVY) is strictly PROHIBITED and is NOT part of the Simplilearn palette!
           - NEVER style containers, pills, cards, banners, or text with dark navy blue!
           - Containers and cards must use pure white (#FFFFFF), soft card (#F8FAFC), or colors from the approved 10-pastel palette (#62B7E4 Sky Blue, #7EA2C8 Steel Blue, #8ECDB7 Mint, #9B99C7 Lavender, #E6A157 Warm Amber, #DDB945 Mustard Gold, #E58F6D Coral, #B88968 Warm Tan, #D98CA1 Dusty Rose, #C1A5C6 Soft Lilac).
           - Text and labels on light containers/canvas MUST use Primary Dark Charcoal (#404040).
           - Expansive visual diagrams ($13.44 \times 5.66$ in Layout 20) must generously occupy the safe workspace, anchoring the screen and eliminating sterile, empty space.

        ---

        ## TIMING

        - Respect presentation step boundaries
        - Spread runtime naturally
        - Set `run_time` inside every `self.play()`
        - Avoid long waits
        - Avoid `self.play()` and `self.wait()` inside loops
        - Every `self.wait()` should have an explicit timing duration associated with it.

        ---

        ## OBJECT CONTINUITY

        - Maintain one evolving instructional workspace.
        - Prefer `Transform`, `ReplacementTransform`, `.animate` over destroying and recreating objects.
        - Preserve group structure for layout and continuity, but animate meaningful child mobjects individually whenever independent synchronization is useful.
        - Persistent Macro Scaffolding & Zero Void Wipes:
          * The canvas must NEVER be left empty or blank during spoken narration!
          * Visual diagrams, nodes, macro containers, and structured cards MUST persist on screen while the voiceover explains the concepts.
          * NEVER call `FadeOut` or `remove` on all elements before a `self.wait(...)`.
          * If an accent element fades out, underlying diagrams and context cards MUST remain visible!
        - Remove obsolete objects once they are no longer instructionally useful. Clean with `self.remove()`.

        ---

        ## UPDATERS & CAMERA

        - Avoid updaters. Use `ValueTracker` only when it substantially simplifies implementation.
        - Clear temporary trackers.
        - Keep the camera static. Do not move or zoom camera unless explicitly required by storyboard.

        ---

        ## ASSETS

        - Build reusable assets using helper classes.
        - Reuse existing objects whenever possible.
        - Make sure assets simulate real-world artefacts as specified in construction guidelines.
        - Preserve every `asset_<n>` and `image_<n>` reference exactly.

        ---

        ## ROBUSTNESS

        Ensure:
        - ImageMobjects are wrapped inside `Group`
        - Groups containing images remain `Group`
        - Pure vector collections may use `VGroup`
        - `interpolate_color()` always wraps colors with `ManimColor`
        - Images use `scale_to_fit_width()` or `scale_to_fit_height()`; never recolor images
        - Removed objects are cleaned using `self.remove()`
        - Temporary trackers are cleared
        - `Text(..., text_alignment=...)` is never used
        - Never use Transform or ReplacementTransform on a Group or ImageMobject (or hierarchies containing ImageMobjects). Use self.add()/self.remove(), FadeIn/FadeOut instead.
        - `corner_radius` should never be a parameter inside `Rectangle` (only `RoundedRectangle`).
        - Connecting lines and arrows must never cut through or touch text boxes, callout cards, or badges. Callout cards and pills must have `fill_opacity=1.0` and `.set_z_index(20)` to prevent background lines from cutting through card text.

        ---

        ## EXECUTION

        Generate efficient, maintainable Manim CE code that faithfully implements the storyboard.
        Every visual change should correspond to narration.
        Every layout should remain clean and readable.
        Every color and typography decision should follow the supplied styling.
        Do not redesign, merge or reorder beats.
        """

        # Deprecated alias to ensure backwards compatibility
        system_prompt = system_prompt_dynamic

        user_prompt = """
        Generate the Manim Community Edition code script for this scene following the supplied specifications.

        CRITICAL STYLING & COMPONENT REQUIREMENTS:
        1. Canvas Background: Strictly set `self.camera.background_color = "#FFFFFF"` (Pure Crisp White Canvas per Simplilearn guidelines) upfront in construct() for all infographic scenes (or "#0F172A" only if full_screen_trainer Layout 100 is explicitly requested).
        2. Slide Title Header: Construct the on-screen title using the exact Scene Title specified in Scene Context.
           - SINGLE HEADER: Maintain a single top-left header `title_group = create_title(...)` and morph it with `ReplacementTransform`.
           - STRICT PROHIBITION: NEVER render "Scene 1", "Scene 2", "Scene 3", etc. as visible screen text or slide titles! Strictly NEVER create duplicate centered titles (`create_title_centered`) colliding with the top header!
        3. STRICT PROHIBITION OF PPT-STYLE BOXES & STACKED RECTANGULAR CARDS (CRITICAL):
           - Strictly DO NOT diagram system architectures, workflows, or inputs/outputs as stacks or columns of RoundedRectangle cards, pills, or text boxes!
           - Strictly DO NOT create a cluster of floating cards, panels, or boxes with labels. That looks like a 2005 PowerPoint slide!
           - Zero Bulleted Cards: NEVER draw a card or document shape containing bullet points (`• Item 1`). Deliverables, plans, and summaries must be sleek vector indicators (status dials, illuminated checkmark rings, pulsing metric badges), NEVER slide cards with bulleted sentences!
           - Input & Signal Streams: Diagram input data streams, user requests, tool results, and telemetry as open-space conduits with glowing moving particle packets (`Dot()`, `FlowingStream`), NEVER as stacked rectangular cards or pills (e.g., `wc_frame`, stacked card boxes)!
           - Text budget: Micro-labels and metric badges only (1-3 words). Never put descriptive sentences inside shapes or cards!
        4. CREATIVE VECTOR IMPLEMENTATION (LLM DECIDES THE VISUAL MECHANISM ACROSS ANY DOMAIN):
           - You have full creative autonomy to decide and construct the optimal living vector mechanism for the concept described in the storyboard, whether the topic is Finance, Business Strategy, Healthcare, Science, Project Management, Economics, or Technology.
           - Reason from first principles about how the concept behaves: Does it shift, balance, funnel, route, oscillate, branch, decay, grow, gate, synchronize, or transform?
           - Build rich, living Manim geometry from first principles:
             * Finance & Economics: Shifting coordinate curves (supply/demand), balance scales (risk vs return, liquidity vs solvency), cash reservoirs with valves, compounding growth splines.
             * Business & Strategy: Tapered conversion funnels, circular iterative cycles, swimlane process queues, stakeholder alignment matrices.
             * Science & Healthcare: Pulsing anatomical vessels, lock-and-key receptors, branching tree structures, decaying exponential curves.
             * Engineering & Technology: Conduits with particle packets, node clusters with telemetry waves, state machine gates.
           - Infuse the scene with continuous kinetic motion:
             * Data or entity movement: `MoveAlongPath(Dot(), path)` or flowing particle streams.
             * Active processes: rotating halos (`Rotate`), pulsing rings (`PulsingShockwaves`), or oscillating waves (`TelemetryWaves`).
             * State transitions: morphing paths, illuminating active routes, dynamic value updates.
           - Pre-defined vector classes are available in global scope if helpful (`VectorFlywheelMechanism`, `VectorInfinityLoopBridge`, `VectorContextFunnel`, `VectorQuadChamberCore`, `VectorTelemetryChart`, `VectorAPIGateway`, `Vector2x2Matrix`, `VectorMarketingFunnel`, `VectorAgileSprintCycle`, `VectorSecurityShield`, `VectorAdvancedSolarArray`, `VectorMechanicalHammerTool`, `VectorKPIGaugeCard`, `VectorRiskHeatmap`, `VectorRACIMatrix`, `PremiumBalanceScale`, `PrecisionChronometerGauge`, `NeuralReasoningCore`, `ActionDispatchHub`, `PulsingNode`, `FlowingStream`, `BalanceScale`, `TelemetryWaves`, `PulsingShockwaves`, `NeuralHaloPulses`, `DynamicRadarSweep`), OR feel free to construct any custom Manim VGroup geometry that best demonstrates the lesson!
           - ARCHITECTURAL VECTOR MECHANICS MANDATE (QUALITY REQUIREMENT):
             * For conceptual mechanisms like weighing trade-offs, analytical balance scales, chronometer dials, utility gauges, cognitive reasoning cores, action dispatch hubs, flywheels, infinity loops, and context funnels, ALWAYS use pure Manim vector primitives (`VectorFlywheelMechanism`, `VectorInfinityLoopBridge`, `VectorContextFunnel`, `VectorQuadChamberCore`, `VectorTelemetryChart`, `PremiumBalanceScale`, `PrecisionChronometerGauge`, `NeuralReasoningCore`, `ActionDispatchHub`).
             * For simple flowchart connectors or UI icons, build living Manim vector geometry rather than generic bitmap icons.
             * MANDATORY HERO ILLUSTRATIONS: When high-resolution concept illustration PNG assets are listed in 'Image Paths' or exist in 'images/' for this scene (e.g. solar power plant facility, human enterprise engineer, real-world equipment), you MUST load and display them using `ImageMobject(img_path)` per Section 13 below as hero anchors!
             * Judicial boxing: Avoid heavy PPT square container boxes. Let the apparatus breathe in open canvas negative space, using boxes only as micro-pills or base plinths.
             * Fixed 16:9 camera: Strictly maintain a steady camera frame (no zooming or camera panning per Simplilearn OSL 3.0).
        5. High-Contrast Typography Hierarchy:
           - Titles & element headers: #0F172A (bold dark slate). Body text: #334155 (slate). Never use white text on light elements/canvas or low-contrast gray.
           - Font sizes: Titles (24-28), Headers (18-20), Body (14-16), Badges/Pills (12-13).
        6. Focus Highlights: When a node or element has focus_highlight active, animate a 3.5px highlight stroke using color "#F78908" when spoken in narration (`pulse = element.copy().set_fill(opacity=0).set_stroke(color="#F78908", width=3.5)`).
        7. Multi-Pillar Balancing: Fit multi-pillar diagrams within safe width 12.0 so pillar 1 never clips the left margin (x >= -6.40).
        8. SME Layout & Screen Space Utilization:
           - Layout 20 (Corner PiP): SME is strictly confined to the top-right corner. The entire main screen (x in [-6.0, 6.0], y in [-3.2, 1.4]) is available for content! Center diagrams (e.g. CX=0) and expand them across the horizontal canvas. NEVER push content to the far right leaving the entire left 50% blank!
           - Layout 70 (Left Frame): SME is on the left. Content occupies the right 60% (x in [0.5, 6.5]). Scale diagrams and cards generously to fill this area without leaving awkward voids.
           - Strictly preserve the reserved SME window placeholder (keep x <= -1.20 for Layout 70 or top-right quadrant for Layout 20 clear). Strictly DO NOT draw any visible mock camera placeholder frames or placeholder labels!
        9. STRICT PROHIBITION OF ALL CAPS (CLIENT MANDATE):
           - ALL CAPS is NEVER permitted anywhere on screen!
           - All titles, subtitles, headers, labels, state names, node tags, and pills MUST use Title Case (e.g. "Asset Allocation", "Sprint Review", "Receptor Binding", "Cash Reserve").
           - Body descriptions and bullet points MUST use Sentence case.
           - Only standard 2-4 letter domain acronyms (e.g. "ROI", "KPI", "PMP", "CAGR", "DNA", "AI", "RAM", "DB", "API", "GDP", "EBITDA") may be uppercase.
        10. STRICT PROHIBITION OF NAVY BLUE & GREEN (CLIENT MANDATE):
           - Navy Blue (#0B3C5D, #06152B, #0A2540, #1E3A8A, NAVY) is strictly PROHIBITED and is NOT part of the Simplilearn palette!
           - Green (#34A853, #2D6A4F) is strictly PROHIBITED on containers, cards, and text.
           - Containers and cards must use pure white (#FFFFFF), soft card (#F8FAFC), or colors from the approved 10-pastel palette (#62B7E4 Sky Blue, #7EA2C8 Steel Blue, #8ECDB7 Mint, #9B99C7 Lavender, #E6A157 Warm Amber, #DDB945 Mustard Gold, #E58F6D Coral, #B88968 Warm Tan, #D98CA1 Dusty Rose, #C1A5C6 Soft Lilac).
           - Text on light cards/canvas must always be #404040 (Primary Dark Charcoal).
        11. ABSOLUTE PROHIBITION OF DUMMY/PLACEHOLDER TEXT:
            - Strictly NEVER write "Lorem ipsum", "Panel Header", "Category 1", or generic filler text anywhere!
            - All text on screen MUST be real domain terminology extracted directly from the Step Title, Visual Components, and Spoken Narration.
        12. ZERO SMALL-FONT CLUTTER & NO PPT BULLET-POINT WALLS (EXECUTIVE MANDATE):
            - Strictly do NOT generate dense bullet-point walls or micro-font text lists (<10pt or <14pt).
            - Eliminate PowerPoint-style bullet clutter. Keep on-screen typography bold, clean, punchy, and legible.
        13. MANDATORY HERO ILLUSTRATION ASSET INTEGRATION (EXECUTIVE CLIENT MANDATE):
            - Whenever transparent illustration PNG assets are listed in 'Image Paths' or exist in 'images/' for this scene (e.g., scene_<group>_*.png), you MUST load and display them as the primary hero visual anchors on screen using `ImageMobject(img_path)` wrapped inside `Group`.
            - STRICT PROHIBITION: NEVER substitute or downgrade high-resolution illustration assets into generic primitive shapes, plain empty circles, or text-heavy RoundedRectangle cards!
            - Sizing & Placement:
              * Hero centerpieces (such as brain, solar plant, actuator hub, engineer operator, decision matrix, terminal lab) MUST be scaled to fit height 1.8 to 2.4.
              * Socket icons, tool badges, and secondary markers MUST be scaled to fit height 0.65 to 1.0.
            - Robust Animation Rules for Images:
              * ALWAYS wrap `ImageMobject` inside `Group` (never `VGroup`).
              * Use `FadeIn(img_grp)`, `FadeOut(img_grp)`, or `img_grp.animate.shift(...)` / `img_grp.animate.scale(...)`.
              * NEVER use `Transform()` or `ReplacementTransform()` directly on an `ImageMobject` or a `Group` containing an `ImageMobject` (this raises a Manim interpolation crash!). Use FadeOut/FadeIn or move_to animations instead.
        14. EXECUTE AUTHENTIC CINEMATIC VISUAL CHOREOGRAPHY (DO NOT FLATTEN INTO CARDS):
            - The Visual Choreography in Scene Context specifies living, physical, and domain-specific visual mechanisms:
              * Animated dials with kinetic needles dropping below threshold lines, triggering red alert pulses.
              * Branching decision trees sprouting from agent nodes with glowing candidate paths.
              * Dormant gray static tools with blinking cursors vs. living circulating loops.
              * Multi-channel data streams flowing into perception receptors.
              * Decision matrices with dynamic utility sliders and optimization curves.
              * Human escalation handoff paths activating when confidence drops.
            - Strictly execute THESE EXACT CINEMATIC MECHANISMS as active Manim geometry, particle flows, and transparent illustration assets!
            - Strictly DO NOT replace living mechanisms with static RoundedRectangle cards or bullet boxes!
        15. CONTINUOUS LIVING MOTION & AMBIENT ANIMATION (MANDATORY TO AVOID STATIC VIDEO):
            - Every scene MUST be continuously alive and kinetic during narration!
            - During long intervals where the narrator speaks (up to 10-30 seconds per step), DO NOT let the screen sit as a frozen still frame!
            - Attach continuous updaters (`add_updater`, `always_redraw`, or `ValueTracker`) to core visual elements:
              * Ambient rotating rings, gears, or halos: `mob.add_updater(lambda m, dt: m.rotate(0.3 * dt))`
              * Continuous particle streams traveling along conduits: `FlowingStream` with active particle updaters
              * Telemetry signals or breathing waves: `TelemetryWaves`, `PulsingShockwaves`
              * Dynamic gauges with dithering or reactive needles: `ValueTracker`
            - Because these updaters run smoothly during `self.wait()` and `self.sync_to()`, the video remains dynamic, living, and visually captivating at all times!

        16. CANONICAL SIMPLILEARN OSL 3.0 TEMPLATES & MODULAR BEAT INTEGRATION:
            - Reusable Simplilearn templates are available in local scope if a step calls for them:
              * Title Intro: `from template1_title_intro import play_title_intro, CrispText`
              * Learning Roadmap: `from template2_learning_roadmap import play_learning_roadmap, create_checkmark_badge, CrispText`
              * Topic Coverage: `from template3_topic_coverage import play_topic_coverage, CrispText`
            - Integration Rules for Mixed / Composite Scenes:
              * Learning Objectives / Outcomes Step (e.g. Step 3 in Scene 2): Call `play_learning_roadmap(self, bullets=[...], bullet_durations=[...], header_text="By the end of this topic, you will be able to:")` OR construct the official blue circular checkmark badges (`create_checkmark_badge(radius=0.17, color="#0D6EFD")`) progressively revealed in sync with narration.
              * Outro / What's Next Step (e.g. concluding What's Next beat in the final scene): Call `play_topic_coverage(self, bullets=[...], header_text="In the next topic, you will learn about:", bullet_durations=[...], hold_duration=2.5, dissolve_to_white=True)`.
              * Pure Content Steps and Content Scenes (Scenes 3 through 8): Must NEVER use template cards or static boxes. They must strictly execute living vector mechanics (planetary gears, radar sweeps, telemetry waveforms, particle loops, and hero illustration images) exactly as specified in the Visual Choreography.

        ------------------------
        Scene Context:
        {scene_context}
        """

        # Resolve styling specifications file (supports Styling Generator output as well as legacy styling files)
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        styling_file = None
        candidates = [
            config_data.get('styling_specifications_file'),
            config_data.get('styling_file'),
            f"{meta_dir}/{topic_id}_styling_specifications.json",
            f"{meta_dir}/styling_specifications.json",
            f"{base_folder}/styling_specifications.json",
            f"{base_folder}/styling_{guideline_model_name}.json",
            f"{base_folder}/styling_instructions_{guideline_model_name}.json",
        ]
        for c in candidates:
            if c and os.path.exists(c):
                styling_file = c
                break
        if not styling_file:
            matches = glob.glob(f"{meta_dir}/*styling*.json") or glob.glob(f"{base_folder}/*styling_specifications*.json") or glob.glob(f"{base_folder}/*styling*.json")
            if matches:
                styling_file = matches[0]

        styling_data = {}
        if styling_file and os.path.exists(styling_file):
            print(f"Loading styling specifications from: {styling_file}")
            with open(styling_file, 'r', encoding='utf-8') as f:
                styling_data = json.load(f)

        # Detect format: Styling Generator format has "scenes" list and/or "color_rules"
        is_styling_generator_format = isinstance(styling_data, dict) and ("scenes" in styling_data or "color_rules" in styling_data)
        
        styling_scenes_map = {}
        global_color_rules = {}
        if is_styling_generator_format:
            global_color_rules = styling_data.get("color_rules", {})
            for sc in styling_data.get("scenes", []):
                styling_scenes_map[str(sc.get("scene_id"))] = sc
        else:
            # Check if there is a separate styling_specifications file in base_folder or meta_dir
            alt_styling_matches = glob.glob(f"{meta_dir}/*styling_specifications*.json") or glob.glob(f"{base_folder}/*styling_specifications*.json")
            if alt_styling_matches:
                try:
                    with open(alt_styling_matches[0], 'r', encoding='utf-8') as f:
                        alt_data = json.load(f)
                    if isinstance(alt_data, dict) and ("scenes" in alt_data or "color_rules" in alt_data):
                        global_color_rules = alt_data.get("color_rules", {})
                        for sc in alt_data.get("scenes", []):
                            styling_scenes_map[str(sc.get("scene_id"))] = sc
                except Exception as e:
                    print(f"Notice loading alt styling specifications: {e}")

        # Structured CGI & Asset classification
        cgi_file = f"{meta_dir}/CGI_Input.json"
        if not os.path.exists(cgi_file):
            cgi_file = f"{base_folder}/CGI_Input.json"
        if not os.path.exists(cgi_file):
            cgi_matches = glob.glob(f"{meta_dir}/*CGI_Input*.json") or glob.glob(f"{base_folder}/*CGI_Input*.json")
            if cgi_matches:
                cgi_file = cgi_matches[0]

        structured_cgi = {}
        if os.path.exists(cgi_file):
            with open(cgi_file, 'r', encoding='utf-8') as f:
                structured_cgi = json.load(f)

        # Presentation composition (Stage 6) containing detailed visual descriptions & instructions
        comp_file = f"{meta_dir}/{topic_id}_presentation_composition.json"
        if not os.path.exists(comp_file):
            comp_file = f"{base_folder}/{topic_id}_presentation_composition.json"
        if not os.path.exists(comp_file):
            comp_file = f"{meta_dir}/presentation_composition.json"
        if not os.path.exists(comp_file):
            comp_file = f"{base_folder}/presentation_composition.json"
        if not os.path.exists(comp_file):
            comp_matches = (
                glob.glob(f"{meta_dir}/*presentation_composition*.json") or
                glob.glob(f"{meta_dir}/*presentation_composer*.json") or
                glob.glob(f"{base_folder}/*presentation_composition*.json") or
                glob.glob(f"{base_folder}/*presentation_composer*.json")
            )
            if comp_matches:
                comp_file = comp_matches[0]

        composition_scenes_map = {}
        if os.path.exists(comp_file):
            try:
                with open(comp_file, 'r', encoding='utf-8') as f:
                    comp_data = json.load(f)
                for sc in comp_data.get("scenes", []):
                    composition_scenes_map[str(sc.get("scene_id", sc.get("scene_index", "")))] = sc
                print(f"Loaded presentation composition with {len(composition_scenes_map)} scenes from: {comp_file}")
            except Exception as e:
                print(f"Notice loading presentation composition: {e}")

        # Ingest instructions_<model>.json (Stage 1 / Stage 2 step specifications)
        instructions_data = {}
        inst_matches = (
            glob.glob(f"{meta_dir}/instructions_*.json") or
            glob.glob(f"{base_folder}/instructions_*.json") or
            glob.glob(f"{meta_dir}/*instructions*.json") or
            glob.glob(f"{base_folder}/*instructions*.json")
        )
        if inst_matches:
            try:
                with open(inst_matches[0], 'r', encoding='utf-8') as f:
                    instructions_data = json.load(f)
                print(f"Loaded {len(instructions_data)} scene instructions from: {inst_matches[0]}")
            except Exception as e:
                print(f"Notice loading instructions: {e}")

        # Ingest enhanced_anim_<model>.json (Stage 6 authoritative spatial layouts)
        enhanced_anim_data = {}
        enh_matches = (
            glob.glob(f"{meta_dir}/enhanced_anim_*.json") or
            glob.glob(f"{base_folder}/enhanced_anim_*.json")
        )
        if enh_matches:
            try:
                with open(enh_matches[0], 'r', encoding='utf-8') as f:
                    enhanced_anim_data = json.load(f)
                print(f"Loaded {len(enhanced_anim_data)} scene enhanced animations from: {enh_matches[0]}")
            except Exception as e:
                print(f"Notice loading enhanced animations: {e}")

        asset_classification_output_file = f"{meta_dir}/{topic_id}_classified_assets.json"
        if not os.path.exists(asset_classification_output_file):
            asset_classification_output_file = f"{base_folder}/asset_classification_{asset_class_model_name}.json"
        if not os.path.exists(asset_classification_output_file):
            asset_matches = (
                glob.glob(f"{meta_dir}/*classified_assets*.json") or
                glob.glob(f"{meta_dir}/*asset_classification*.json") or
                glob.glob(f"{base_folder}/*asset_classification*.json") or
                glob.glob(f"{base_folder}/*classified_assets*.json")
            )
            if asset_matches:
                asset_classification_output_file = asset_matches[0]

        asset_classification = {}
        if os.path.exists(asset_classification_output_file):
            with open(asset_classification_output_file, 'r', encoding='utf-8') as f:
                asset_classification = json.load(f)

        # Load asset construction output
        construction_guidelines_dict = {}
        construction_guidelines_by_scene = {}
        construction_candidates = [
            f"{meta_dir}/{topic_id}_constructed_assets.json",
            f"{meta_dir}/constructed_assets.json",
            f"{base_folder}/{topic_id}_constructed_assets.json",
            f"{base_folder}/constructed_assets.json",
            f"{meta_dir}/construction_output_{asset_builder_model_name}.json",
            f"{base_folder}/construction_output_{asset_builder_model_name}.json"
        ]
        # Include any dynamic construction output matching pattern
        construction_candidates.extend(str(p) for p in Path(meta_dir).glob("construction_output_*.json"))
        construction_candidates.extend(str(p) for p in Path(base_folder).glob("construction_output_*.json"))
        for cc in construction_candidates:
            if os.path.exists(cc):
                try:
                    with open(cc, 'r', encoding='utf-8') as f:
                        c_data = json.load(f)
                    if isinstance(c_data, dict):
                        if "constructed_catalog" in c_data:
                            for a_id, a_info in c_data["constructed_catalog"].items():
                                construction_guidelines_dict[a_id] = a_info.get("construction_paragraph", "")
                                if "asset_name" in a_info:
                                    construction_guidelines_dict[a_info["asset_name"]] = a_info.get("construction_paragraph", "")
                                sc_id = str(a_info.get("scene_id", ""))
                                if sc_id:
                                    construction_guidelines_by_scene.setdefault(sc_id, []).append({
                                        "asset_id": a_id,
                                        "name": a_info.get("asset_name", a_id),
                                        "guideline": a_info.get("construction_paragraph", ""),
                                        "suggestion": a_info.get("asset_suggestion", "")
                                    })
                        else:
                            construction_guidelines_dict.update(c_data)
                    print(f"Loaded {len(construction_guidelines_dict)} asset construction blueprints from: {cc}")
                    break
                except Exception as e:
                    print(f"Notice loading construction output: {e}")

        scene_code_path = f"{base_folder}/manim_codes"
        os.makedirs(scene_code_path, exist_ok=True)

        partition_type = "Presentation Step"

        # Determine all scene groups to process
        scene_groups = set()
        if structured_cgi:
            scene_groups.update([str(k) for k in structured_cgi.keys()])
        if styling_scenes_map:
            scene_groups.update([str(k) for k in styling_scenes_map.keys()])
        if composition_scenes_map:
            scene_groups.update([str(k) for k in composition_scenes_map.keys()])
        if isinstance(styling_data, dict) and not is_styling_generator_format:
            scene_groups.update([str(k) for k in styling_data.keys()])

        all_scene_groups = sorted(scene_groups, key=lambda x: int(x) if str(x).isdigit() else str(x))
        all_last_group = str(all_scene_groups[-1]) if all_scene_groups else "9"
        sorted_groups = list(all_scene_groups)
        target_scene_env = os.environ.get("TARGET_SCENE")
        if target_scene_env:
            sorted_groups = [g for g in sorted_groups if str(g) == str(target_scene_env)]

        skip_scenes_env = os.environ.get("SKIP_SCENES")
        if skip_scenes_env:
            skip_list = [s.strip() for s in skip_scenes_env.split(",") if s.strip()]
            sorted_groups = [g for g in sorted_groups if str(g) not in skip_list]

        for group in sorted_groups:
            asset_names_list = []
            asset_guidelines = []
            image_details = "\n\n------------Image Paths------------\n"
            scene_file_name = f"group_{group}.py"
            scene_file_path = os.path.join(scene_code_path, scene_file_name)
            if os.path.exists(scene_file_path) and not config_data.get("force", False) and os.environ.get("FORCE_RUN") != "1" and not target_scene_env:
                continue
            
            print(f"Starting to process assets and images for Scene {group}")
            sc_styling = styling_scenes_map.get(str(group))
            comp_scene = composition_scenes_map.get(str(group))

            clean_topic_title = ""
            if sc_styling and sc_styling.get("title") and not sc_styling.get("title").lower().startswith("scene "):
                clean_topic_title = sc_styling.get("title")
            elif comp_scene and comp_scene.get("title") and not comp_scene.get("title").lower().startswith("scene "):
                clean_topic_title = comp_scene.get("title")
            elif comp_scene and comp_scene.get("scene_title") and not comp_scene.get("scene_title").lower().startswith("scene "):
                clean_topic_title = comp_scene.get("scene_title")
            elif str(group) in TOPIC_SCENE_TITLES:
                clean_topic_title = TOPIC_SCENE_TITLES[str(group)]
            else:
                # Dynamically inspect steps
                st_steps = comp_scene.get("presentation_steps", []) if comp_scene else []
                if st_steps and (st_steps[0].get("title") or st_steps[0].get("step_title")):
                    cand = st_steps[0].get("title") or st_steps[0].get("step_title")
                    if cand and not cand.lower().startswith("scene ") and len(cand.split()) <= 7:
                        clean_topic_title = cand.strip()
                if not clean_topic_title:
                    clean_topic_title = f"{clean_lesson_title} - Part {group}"

            scene_context = f"Scene {group}:\n"
            scene_context += f"Scene Title (MANDATORY ON-SCREEN TITLE): \"{clean_topic_title}\"\n"

            # Ingest Styling Generator Specifications (OSL 3.0 Design System)
            if sc_styling or global_color_rules:
                scene_context += "------------Styling Generator Specifications (OSL 3.0)------------\n"
                if sc_styling:
                    canvas_th = sc_styling.get('canvas_theme', 'light_infographic_canvas')
                    bg_col = sc_styling.get('background_color_hex', '#FFFFFF')
                    if not bg_col:
                        bg_col = '#FFFFFF'
                    scene_context += f"Canvas Theme: {canvas_th}\n"
                    scene_context += f"Background Color: {bg_col}\n"
                    scene_context += f"SME Layout: {sc_styling.get('sme_layout', '70')}%\n"
                if global_color_rules:
                    scene_context += "Global Design Tokens:\n"
                    scene_context += f"  - Palette Family: {global_color_rules.get('palette_family', '10-color infographic pastel palette')}\n"
                    scene_context += f"  - Green Prohibition: {global_color_rules.get('green_prohibition', 'Zero green containers/cards')}\n"
                    scene_context += f"  - Casing Mandate: {global_color_rules.get('all_caps_prohibition', 'Strictly Title Case for headings, Sentence case for body')}\n"
                    if not (instructions_data and str(group) in instructions_data):
                        scene_context += f"  - Card Corner Radius: {global_color_rules.get('corner_radius_px', 10)}px (0.074 Manim units)\n"
                    else:
                        scene_context += "  - Visual Architecture: Living kinetic vector mechanisms and hero illustrations in open canvas space (strictly NO generic PPT cards)\n"
                    scene_context += f"  - Focus Highlight: {global_color_rules.get('highlight_color_hex', '#F78908')} (stroke_width=3)\n"
                
                has_stage1_instr = bool(instructions_data and str(group) in instructions_data)
                if sc_styling and sc_styling.get("styled_blocks"):
                    blocks = sc_styling.get("styled_blocks", [])
                    scene_context += f"Styled Component Blocks ({len(blocks)} blocks):\n"
                    for b in blocks:
                        b_id = b.get("block_id", "")
                        c_type = b.get("component_type", "")
                        if b_id or c_type:
                            scene_context += f"  * [{b_id}] Component: {c_type}\n"
                        # Only include matching_section from styling if instructions_data is not available,
                        # to prevent card-based prose from overriding authentic cinematic visual choreography
                        if b.get("matching_section") and not has_stage1_instr:
                            scene_context += f"  * Visual Styling & Instructions: {b.get('matching_section')}\n"
                        typo = b.get("typography")
                        if typo:
                            scene_context += f"    - Typography: font={typo.get('font_family', 'Open Sans')}, weight={typo.get('font_weight')}, size={typo.get('font_size_px')}px, color={typo.get('color_hex')}, casing={typo.get('casing')}\n"
                        lay = b.get("layout")
                        if lay:
                            scene_context += f"    - Layout: position={lay.get('position')}, safe_zone={lay.get('safe_zone')}, coordinates={lay.get('coordinates')}\n"
                        # Suppress generic container styling if authentic Stage 1 kinetic choreography is present
                        cont = b.get("container_styling")
                        if cont and not has_stage1_instr:
                            scene_context += f"    - Container: fill={cont.get('fill_color', '#F8FAFC')}, opacity={cont.get('fill_opacity', 0.95)}, border_color={cont.get('border_color')} ({cont.get('accent_name')}), border_width={cont.get('border_width_px', 2)}px, radius={cont.get('corner_radius_px', 10)}px (0.074 u)\n"
                        h_typo = b.get("header_typography")
                        if h_typo:
                            scene_context += f"    - Header: \"{h_typo.get('text', '')}\" (font={h_typo.get('font_family', 'Open Sans')}, weight={h_typo.get('font_weight')}, size={h_typo.get('font_size_px')}px, color={h_typo.get('color_hex')})\n"
                        b_typo = b.get("body_typography")
                        if b_typo:
                            scene_context += f"    - Body: \"{b_typo.get('text', '')}\" (font={b_typo.get('font_family', 'Open Sans')}, weight={b_typo.get('font_weight')}, size={b_typo.get('font_size_px')}px, color={b_typo.get('color_hex')})\n"
                        fh = b.get("focus_highlight")
                        if fh and fh.get("active"):
                            scene_context += f"    - Focus Highlight: active=True, color={fh.get('color_hex', '#F78908')}, stroke_width={fh.get('stroke_width_px', 3)}px\n"
                scene_context += "------------------------------------------------------------------\n\n"

            # Ingest steps from structured CGI manifest, composition instructions, and legacy instructions
            cgi_scene_steps = structured_cgi.get(group, []) if structured_cgi else []
            legacy_scene_steps = styling_data.get(group, []) if (isinstance(styling_data, dict) and not is_styling_generator_format and group in styling_data) else []
            # Prioritize the authoritative, kinetic vector choreography from enhanced_anim_data (Stage 6)
            # which defines authentic dynamic diagrams, particle conduits, and loops without container cards
            if enhanced_anim_data and str(group) in enhanced_anim_data:
                legacy_scene_steps = enhanced_anim_data[str(group)]
            elif instructions_data and str(group) in instructions_data:
                legacy_scene_steps = instructions_data[str(group)]
            elif comp_scene and comp_scene.get("instructions"):
                legacy_scene_steps = comp_scene.get("instructions", [])

            num_steps = max(len(cgi_scene_steps), len(legacy_scene_steps), 1)
            for i in range(num_steps):
                scene_context += "#####################################################\n"
                scene_context += f"{partition_type} {i+1}:\n\n"

                # Step title / matching section
                matching = ""
                if i < len(legacy_scene_steps) and isinstance(legacy_scene_steps[i], dict):
                    matching = legacy_scene_steps[i].get('matching_section', '')
                elif i < len(cgi_scene_steps) and isinstance(cgi_scene_steps[i], dict):
                    matching = cgi_scene_steps[i].get('title', '')
                if not matching and str(group) in instructions_data and i < len(instructions_data[str(group)]):
                    matching = instructions_data[str(group)][i].get('matching_section', '') or instructions_data[str(group)][i].get('title', '')
                if not matching and comp_scene:
                    matching = comp_scene.get("title", "")
                if matching:
                    # Strip any legacy card-forcing directives from older blueprint stages
                    clean_matching = re.sub(r"Container cards styled with 10px rounded corners[^.]*\.", "Living kinetic vector mechanisms and transparent hero illustrations in open canvas space.", matching, flags=re.IGNORECASE)
                    clean_matching = re.sub(r"mount them inside sleek container cards[^\n.]*", "integrate directly as authentic kinetic vector mechanisms in open canvas space", clean_matching, flags=re.IGNORECASE)
                    scene_context += f"{clean_matching}\n\n"

                # Step runtime
                r_time = None
                if i < len(cgi_scene_steps) and isinstance(cgi_scene_steps[i], dict) and len(cgi_scene_steps) > 1:
                    r_time = cgi_scene_steps[i].get('run_time') or cgi_scene_steps[i].get('duration')
                elif i < len(legacy_scene_steps) and isinstance(legacy_scene_steps[i], dict) and group in structured_cgi and i < len(structured_cgi[group]) and len(structured_cgi[group]) > 1:
                    r_time = structured_cgi[group][i].get('run_time')
                elif comp_scene and comp_scene.get("duration"):
                    tot_d = float(comp_scene.get("duration", 20.0))
                    r_time = round(tot_d / max(num_steps, 1), 2)
                elif i < len(cgi_scene_steps) and isinstance(cgi_scene_steps[i], dict):
                    tot_d = float(cgi_scene_steps[i].get('run_time') or cgi_scene_steps[i].get('duration') or 20.0)
                    r_time = round(tot_d / max(num_steps, 1), 2)
                if r_time is not None:
                    scene_context += f"{partition_type} run time:{r_time}\n\n"

                # Step narration text
                narration = ""
                if i < len(legacy_scene_steps) and isinstance(legacy_scene_steps[i], dict):
                    narration = legacy_scene_steps[i].get('narration_statement') or legacy_scene_steps[i].get('voiceover_narration') or legacy_scene_steps[i].get('narration', '')
                if not narration and str(group) in instructions_data and i < len(instructions_data[str(group)]):
                    narration = instructions_data[str(group)][i].get('narration_statement', '')
                if not narration and comp_scene:
                    narration = comp_scene.get("voiceover_narration", "")
                if not narration and sc_styling:
                    narration = sc_styling.get("voiceover_narration") or sc_styling.get("narration", "")
                if not narration and i < len(cgi_scene_steps) and isinstance(cgi_scene_steps[i], dict):
                    narration = cgi_scene_steps[i].get('narration_statement') or cgi_scene_steps[i].get('voiceover_narration', '')
                if narration:
                    scene_context += f"Narration Text: {narration}\n\n"

                # Step visual structure and evolution
                if i < len(cgi_scene_steps) and isinstance(cgi_scene_steps[i], dict):
                    st_step = cgi_scene_steps[i]
                    st_title = st_step.get("step_title") or st_step.get("title")
                    if st_title and st_title != matching:
                        scene_context += f"Step Title: {st_title}\n"
                    v_desc = st_step.get("visual_description")
                    if v_desc:
                        if isinstance(v_desc, dict):
                            p = v_desc.get("purpose")
                            if p:
                                scene_context += f"Visual Purpose: {p}\n"
                            comps = v_desc.get("presentation_components", [])
                            if comps:
                                scene_context += "Visual Components:\n"
                                for comp in comps:
                                    comp_t = comp.get('component_type', 'Mechanism')
                                    if comp_t.lower() == 'card':
                                        comp_t = 'Kinetic Mechanism'
                                    scene_context += f"  - [{comp.get('column', 'Workspace')}] {comp_t}: {comp.get('content', '')}\n"
                        elif isinstance(v_desc, str):
                            scene_context += f"Visual Description: {v_desc}\n"
                    v_evo = st_step.get("visual_evolution")
                    if v_evo:
                        scene_context += f"Visual Evolution: {v_evo}\n"
                    kt = st_step.get("key_takeaway")
                    if kt:
                        scene_context += f"Key Takeaway: {kt}\n"
                    scene_context += "\n"

                # Classified assets and image paths
                scene_assets = None
                if isinstance(asset_classification, dict):
                    if group in asset_classification:
                        scene_assets = asset_classification[group]
                    elif "scenes" in asset_classification:
                        for sc in asset_classification.get("scenes", []):
                            if str(sc.get("scene_id")) == str(group):
                                scene_assets = sc.get("steps", [])
                                break

                if scene_assets and i < len(scene_assets) and isinstance(scene_assets[i], dict):
                    st_asset_entry = scene_assets[i]
                    if st_asset_entry.get("Asset_names"):
                        for aname in st_asset_entry["Asset_names"]:
                            if aname and aname not in asset_names_list:
                                asset_names_list.append(aname)
                    if st_asset_entry.get("Asset_Suggestion"):
                        suggs = st_asset_entry["Asset_Suggestion"]
                        if isinstance(suggs, str):
                            suggs = [suggs]
                        for s in suggs:
                            if s and s not in asset_guidelines:
                                asset_guidelines.append(s)
                    if i < len(legacy_scene_steps) and isinstance(legacy_scene_steps[i], dict) and "assets" in legacy_scene_steps[i]:
                        raw_legacy_assets = legacy_scene_steps[i]["assets"]
                        if isinstance(raw_legacy_assets, list):
                            asset_guidelines.extend(raw_legacy_assets)
                        elif isinstance(raw_legacy_assets, str):
                            asset_guidelines.append(raw_legacy_assets)
                    if st_asset_entry.get("image_paths") and os.environ.get("SKIP_IMAGES") != "1":
                        for img_num, img_name in enumerate(st_asset_entry.get("Image_names", [])):
                            if img_num < len(st_asset_entry["image_paths"]):
                                image_path = st_asset_entry["image_paths"][img_num]
                                image_details += f"{img_name}:{image_path}\n"

            # Ingest scene-level constructed catalog blueprints if available
            if str(group) in construction_guidelines_by_scene:
                for c_item in construction_guidelines_by_scene[str(group)]:
                    c_name = c_item.get("name") or c_item.get("asset_id")
                    if c_name and c_name not in asset_names_list:
                        asset_names_list.append(c_name)
                    if c_item.get("guideline") and c_item["guideline"] not in asset_guidelines:
                        asset_guidelines.append(c_item["guideline"])

            # Auto-discover scene images from images/ folder if not already explicitly added
            if os.environ.get("SKIP_IMAGES") != "1":
                img_dir = os.path.join(base_folder, "images")
                if os.path.exists(img_dir):
                    group_int = int(group) if str(group).isdigit() else None
                    scene_patterns = [
                        f"scene_{group}_*.png", f"scene_{group}_*.jpg",
                        f"s{group}_*.png", f"s{group}_*.jpg",
                    ]
                    if group_int is not None:
                        scene_patterns.extend([
                            f"s{group_int:02d}_*.png", f"s{group_int:02d}_*.jpg",
                            f"scene_{group_int:02d}_*.png", f"scene_{group_int:02d}_*.jpg",
                        ])
                    scene_img_matches = []
                    for pat in scene_patterns:
                        scene_img_matches.extend(glob.glob(os.path.join(img_dir, pat)))
                    scene_img_matches = sorted(list(set(scene_img_matches)))
                    for simg in scene_img_matches:
                        simg_name = os.path.splitext(os.path.basename(simg))[0]
                        if simg_name not in image_details:
                            image_details += f"{simg_name}:{simg}\n"

            if asset_names_list:
                asset_ref = "------------Asset Construction Guidelines------------\n\n"
                for k, asset_name in enumerate(asset_names_list):
                    asset_ref += "Asset Name: " + asset_name + "\n\n"
                    guideline_text = construction_guidelines_dict.get(asset_name)
                    if not guideline_text and k < len(asset_guidelines) and len(str(asset_guidelines[k])) > 30:
                        guideline_text = asset_guidelines[k]
                    if not guideline_text:
                        guideline_text = "Render as standard visual asset."
                    asset_ref += "Asset Guidelines:\n" + guideline_text + "\n\n"
                scene_context += asset_ref

            if image_details.strip() != "------------Image Paths------------":
                scene_context += image_details

            print(f"Processing Scene {group}:\n\n{scene_context}")

            # Dynamic system prompt is exclusively used across all themes
            formatted_system_prompt = system_prompt_dynamic

            ref_patterns = load_reference_design_patterns(base_folder)
            if ref_patterns:
                formatted_system_prompt += f"\n\n{ref_patterns}\n"

            formatted_user_prompt = user_prompt.format(
                scene_context=scene_context
            )

            # Check for Simplilearn OSL 3.0 Standard Template Cases
            # Pure templates are ONLY used for standalone single-beat scenes (e.g., dedicated <= 12s title splash or pure 1-step outro).
            # Mixed/composite scenes (e.g. Scene 1 with 48s narration, Scene 2 with Solara+Objectives, Scene 9 with Key Takeaways)
            # MUST be synthesized dynamically with deep cinematic LLM reasoning (gemini-3.8-flash) to avoid freezing or destroying content.
            grp_s = str(group).strip()
            norm_t = clean_topic_title.lower()
            use_tmpl_env = os.environ.get("USE_MANIM_TEMPLATES", "true").lower() in ("true", "1", "yes")

            sc_title = clean_topic_title
            sc_layout = str(sc_styling.get("sme_layout", "70")).replace("%", "") if sc_styling else "70"
            sc_lead = sc_styling.get("lead_in", "") if sc_styling else ""
            sc_cards = sc_styling.get("styled_blocks") or sc_styling.get("cards") if sc_styling else []
            sc_runtime = 20.0
            num_steps = 1
            if structured_cgi and group in structured_cgi and structured_cgi[group]:
                sc_runtime = sum(float(st.get("run_time", 20.0)) for st in structured_cgi[group])
                num_steps = len(structured_cgi[group])
                sc_cards = [{"title": st.get("title") or st.get("step_title", f"Point {idx+1}"), "body": st.get("narration_statement", "")} for idx, st in enumerate(structured_cgi[group])]

            is_pure_title = (grp_s == "1" or any(kw in norm_t for kw in ["title splash", "topic intro"]))
            is_pure_roadmap = (grp_s == "3" or any(kw in norm_t for kw in ["learning objectives", "learning outcomes", "roadmap"]))
            is_pure_outro = (grp_s == all_last_group or any(kw in norm_t for kw in ["what's next", "what is next", "next topic", "demo launch", "synthesis"]))

            is_tmpl = use_tmpl_env and (is_pure_title or is_pure_roadmap or is_pure_outro)

            generated_result = None
            if is_tmpl:
                print(f"    -> Using official Simplilearn OSL 3.0 template for pure template scene {group} ({clean_topic_title})...")
                generated_result = generate_simplilearn_manim_template(
                    group=str(group),
                    layout=sc_layout,
                    title=sc_title,
                    lead_in=sc_lead,
                    cards=sc_cards,
                    run_time=sc_runtime
                )

            if generated_result is not None:
                print(f"    -> Successfully applied Simplilearn canonical template for Scene {group}.")
            elif scene_coding_vendor in ["google", "gemini"]:
                target_model = scene_coding_model_name or "gemini-3.8-flash"
                print(f"Attempting LLM code synthesis with {target_model} for Scene {group}...")
                full_prompt = f"{formatted_system_prompt}\n\nUser Query: {formatted_user_prompt}"
                generated_result = None
                max_retries = 5

                # Configure deep spatial reasoning for Pro models
                gen_config = types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=50000,
                )
                if "pro" in target_model.lower() or "3.1" in target_model or "2.5-pro" in target_model:
                    try:
                        gen_config.thinking_config = types.ThinkingConfig(thinking_level="high")
                    except Exception:
                        pass

                for attempt in range(1, max_retries + 1):
                    try:
                        if hasattr(google_client, 'models'):
                            response = google_client.models.generate_content(
                                model=target_model,
                                contents=full_prompt,
                                config=gen_config,
                            )
                            generated_result = response.text
                            break
                    except Exception as e:
                        print(f"\n    -> [API Attempt {attempt}/{max_retries}] Notice: {e}")
                        if attempt == max_retries:
                            if target_model != "gemini-3.8-flash":
                                print(f"    -> Falling back to gemini-3.8-flash for Scene {group}...")
                                try:
                                    fallback_resp = google_client.models.generate_content(
                                        model="gemini-3.8-flash",
                                        contents=full_prompt,
                                        config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=30000),
                                    )
                                    generated_result = fallback_resp.text
                                    break
                                except Exception as fe:
                                    print(f"    -> [Fallback Notice] {fe}")
                            print(f"    -> Triggering dynamic Simplilearn OSL 3.0 procedural vector generator.")
                        else:
                            wait_time = 2 ** attempt
                            print(f"    -> Retrying generation in {wait_time}s...")
                            time.sleep(wait_time)
            elif scene_coding_vendor=="claude":
                print(f"Using claude's model of {scene_coding_model_name}")
                claude_kwargs = {
                    "max_tokens": 24000,
                    "system": formatted_system_prompt,
                    "messages": [
                        {"role": "user", "content": formatted_user_prompt}
                    ],
                    "model": scene_coding_model_name
                }
                if "sonnet-5" in str(scene_coding_model_name) or "opus-5" in str(scene_coding_model_name):
                    claude_kwargs["thinking"] = {"type": "adaptive"}
                    claude_kwargs["output_config"] = {"effort": "medium"}
                try:
                    message = client.messages.create(**claude_kwargs)
                    generated_result = "".join(
                        block.text
                        for block in message.content
                        if block.type == "text"
                    )
                except Exception as e:
                    print(f"    -> [Claude API Notice] {e}")
                    if google_client and hasattr(google_client, 'models'):
                        print(f"    -> Falling back to Gemini (gemini-3.8-flash) for Scene {group}...")
                        try:
                            full_prompt = f"{formatted_system_prompt}\n\nUser Query: {formatted_user_prompt}"
                            response = google_client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=full_prompt,
                            )
                            generated_result = response.text
                        except Exception as ge:
                            print(f"    -> [Gemini Fallback Notice] {ge}")
                            print(f"    -> Triggering dynamic Simplilearn OSL 3.0 procedural vector generator.")
                    else:
                        print(f"    -> Triggering dynamic Simplilearn OSL 3.0 procedural vector generator.")
            elif scene_coding_vendor=="moonshot":
                print(f"Using moonshot's model of {scene_coding_model_name}")
                response = client_kimi.chat.completions.create(
                    model=f"moonshotai/{scene_coding_model_name}",
                    messages=[
                        {"role": "user", "content": formatted_system_prompt},
                        {"role": "user", "content": formatted_user_prompt}
                    ],
                    max_tokens=50000,   # Set this to your desired limit
                    temperature=0.2     # Optional
                )
                generated_result = response.choices[0].message.content
            elif scene_coding_vendor=="qwen":
                print(f"Using qwen's model of {scene_coding_model_name}")
                response = client_qwen.chat.completions.create(
                    model=f"qwen/{scene_coding_model_name}",
                    messages=[
                        {"role": "user", "content": formatted_system_prompt},
                        {"role": "user", "content": formatted_user_prompt}
                    ],
                    max_tokens=32000,   # Set this to your desired limit
                    temperature=0.7     # Optional
                )
                generated_result = response.choices[0].message.content
            
            # If LLM generation was empty, failed, or skipped, generate procedural Simplilearn OSL 3.0 template
            if not generated_result or len(generated_result.strip()) < 100:
                print(f"    -> Synthesizing Simplilearn OSL 3.0 vector Manim script for scene {group}...")
                sc_title = sc_styling.get("title", f"Concept Overview: Scene {group}") if sc_styling else f"Scene {group}"
                sc_layout = str(sc_styling.get("sme_layout", "70")).replace("%", "") if sc_styling else "70"
                sc_lead = sc_styling.get("lead_in", "") if sc_styling else ""
                sc_cards = sc_styling.get("styled_blocks") or sc_styling.get("cards") if sc_styling else []
                sc_runtime = 20.0
                if structured_cgi and group in structured_cgi and structured_cgi[group]:
                    step0 = structured_cgi[group][0]
                    sc_runtime = sum(float(st.get("run_time", 20.0)) for st in structured_cgi[group])
                    if not sc_title or sc_title.startswith("Scene"):
                        sc_title = step0.get("title", sc_title)

                code_content = generate_simplilearn_manim_template(
                    group=str(group),
                    layout=sc_layout,
                    title=sc_title,
                    lead_in=sc_lead,
                    cards=sc_cards,
                    run_time=sc_runtime
                )
            else:
                code_content = self.remove_code_fences(generated_result)

            # Add instrumented scene import if missing
            instrumented_import = "from feedback_functions.instrumented_scene import InstrumentedScene"
            if instrumented_import not in code_content:
                code_content = instrumented_import + "\n" + code_content

            # Fix Manim Sector keyword argument hazard (Sector takes radius, not outer_radius)
            code_content = re.sub(r'\bSector\s*\(\s*outer_radius\s*=', 'Sector(radius=', code_content)

            # Ensure FinalScene inherits from InstrumentedScene as requested
            if "class FinalScene(InstrumentedScene," not in code_content:
                code_content = code_content.replace(
                    "class FinalScene(MovingCameraScene)",
                    "class FinalScene(InstrumentedScene, MovingCameraScene)"
                )
            # Ensure CrispText is defined in code
            if "def CrispText" not in code_content:
                crisp_def = r"""from manim import *
import numpy as np
try:
    from vector_primitives import *
except ImportError:
    pass
import manim.utils.rate_functions as _rf
for _k in dir(_rf):
    if not _k.startswith("_"):
        globals()[_k] = getattr(_rf, _k)

def CrispText(text, size=24, font="Open Sans", **kwargs):
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
    max_w_param = kwargs.pop("max_width", kwargs.pop("wrap_width", None))
    for bad_k in ("alignment", "max_len", "line_spacing", "title_size", "item_size"):
        kwargs.pop(bad_k, None)
    slant_val = kwargs.pop("slant", NORMAL)
    weight_val = kwargs.pop("weight", NORMAL)
    if isinstance(weight_val, str):
        weight_clean = weight_val.upper().replace("-", "").replace("_", "").replace(" ", "")
        if weight_clean == "REGULAR":
            weight_val = NORMAL
        elif weight_clean in ("SEMIBOLD", "SEMI_BOLD"):
            weight_val = SEMIBOLD
        elif weight_clean == "BOLD":
            weight_val = BOLD
        elif weight_clean == "LIGHT":
            weight_val = LIGHT
        elif weight_clean in ("NORMAL", "BOOK"):
            weight_val = NORMAL
        else:
            weight_val = NORMAL
    color_val = kwargs.pop("color", None)
    if color_val is None:
        color_val = globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))
    elif str(color_val).upper() in ("#F9C72C", "C_YELLOW", "YELLOW", "#FFF9E6", "#FFFF00"):
        color_val = globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))
    raw_str = str(text)
    NL = chr(10)
    split_lines = [l for l in raw_str.split(NL)] if NL in raw_str else ([l for l in raw_str.split(r"\n")] if r"\n" in raw_str else None)
    if split_lines is None:
        should_autowrap = False
        wrap_target_chars = 34
        if max_w_param is not None:
            try:
                mw = float(max_w_param)
                wrap_target_chars = max(16, int(mw / (size * 0.0082)))
                should_autowrap = (" " in raw_str and len(raw_str) > wrap_target_chars)
            except Exception:
                pass
        if not should_autowrap:
            if autowrap_val is True:
                should_autowrap = True
                wrap_target_chars = 34
            elif autowrap_val is False or disable_wrap_val:
                should_autowrap = False
            else:
                should_autowrap = (len(raw_str) > 36 and " " in raw_str and size <= 16)
                wrap_target_chars = 34
        if should_autowrap:
            words = raw_str.split()
            lines = []
            curr_line = []
            curr_len = 0
            for w in words:
                sep = 1 if curr_line else 0
                if curr_len + len(w) + sep > wrap_target_chars:
                    if curr_line:
                        lines.append(" ".join(curr_line))
                    curr_line = [w]
                    curr_len = len(w)
                else:
                    curr_line.append(w)
                    curr_len += len(w) + sep
            if curr_line:
                lines.append(" ".join(curr_line))
            split_lines = lines
        else:
            split_lines = [raw_str]
    clean_kwargs = {k: v for k, v in kwargs.items() if k in ("tab_width", "t2c", "t2f", "t2s", "t2w", "l2g", "gradient", "fill_opacity", "stroke_width", "stroke_color")}
    if len(split_lines) > 1:
        line_mobs = [Text(l, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **clean_kwargs) for l in split_lines]
        aligned_edge = ORIGIN if align == "center" else (LEFT if align == "left" else RIGHT)
        mob = VGroup(*line_mobs).arrange(DOWN, buff=0.18, aligned_edge=aligned_edge).scale(0.25)
    else:
        mob = Text(raw_str, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **clean_kwargs).scale(0.25)
    orig_scale = mob.scale_to_fit_width
    def safe_scale_width(tw):
        if hasattr(mob, "width") and mob.width > 0:
            ratio = tw / mob.width
            if ratio > 1.0:
                return mob
            if ratio < 0.88:
                ratio = 0.88
            return orig_scale(mob.width * ratio)
        return orig_scale(tw)
    mob.scale_to_fit_width = safe_scale_width
    return mob

class PulsingShockwaves(VGroup):
    def __init__(self, center, color="#E6A157", max_radius=1.1, num_rings=3, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.color = color
        self.max_radius = max_radius
        self.num_rings = num_rings
        self.rings = [Circle(radius=0.2 + i * 0.3, color=color, stroke_width=2.0).move_to(self.center_pt) for i in range(num_rings)]
        self.add(*self.rings)
        self.t = 0.0
        def update_waves(mob, dt):
            mob.t += dt
            for i, ring in enumerate(mob.rings):
                phase = (mob.t * 0.9 + i / float(mob.num_rings)) % 1.0
                r = 0.25 + phase * (mob.max_radius - 0.25)
                ring.become(Circle(radius=r, color=mob.color, stroke_width=2.5 * (1.0 - phase)).move_to(mob.center_pt))
                ring.set_stroke(opacity=max(0.0, 1.0 - phase))
        self.add_updater(update_waves)

class TelemetryWaves(VGroup):
    def __init__(self, center, color="#8ECDB7", **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.arcs = [
            Arc(radius=0.45 + i * 0.22, start_angle=-PI/3, angle=2*PI/3, color=color, stroke_width=2.2).move_to(self.center_pt + RIGHT * 0.50)
            for i in range(3)
        ]
        self.add(*self.arcs)
        self.t = 0.0
        def update_telemetry(mob, dt):
            mob.t += dt
            for i, arc in enumerate(mob.arcs):
                phase = (mob.t * 1.3 + i / 3.0) % 1.0
                arc.set_stroke(opacity=max(0.1, 1.0 - phase), width=2.6 * (1.0 - phase * 0.4))
        self.add_updater(update_telemetry)

class NeuralHaloPulses(VGroup):
    def __init__(self, center, color="#9B99C7", **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.h1 = Circle(radius=0.85, color=color, stroke_width=1.6).move_to(self.center_pt)
        self.nodes = [
            Dot(self.center_pt + np.array([np.cos(a)*0.65, np.sin(a)*0.65, 0]), radius=0.045, color=color)
            for a in np.linspace(0, 2*PI, 6, endpoint=False)
        ]
        self.lines = [Line(self.center_pt, n.get_center(), color=color, stroke_width=1.0, stroke_opacity=0.6) for n in self.nodes]
        self.add(self.h1, *self.lines, *self.nodes)
        self.t = 0.0
        def update_halo(mob, dt):
            mob.t += dt
            s = 1.0 + 0.07 * np.sin(mob.t * 3.0)
            mob.h1.become(Circle(radius=0.85 * s, color=color, stroke_width=1.6).move_to(mob.center_pt))
            mob.h1.set_stroke(opacity=0.4 + 0.4 * np.sin(mob.t * 3.0))
        self.add_updater(update_halo)

class DynamicRadarSweep(VGroup):
    def __init__(self, center, radius=1.0, color="#62B7E4", speed=3.0, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.radius = radius
        self.speed = speed
        self.dish = Circle(radius=radius, fill_color="#DCEEF9", fill_opacity=0.85, stroke_width=0).move_to(self.center_pt)
        self.bezel = Circle(radius=radius, color=color, stroke_width=2.2).move_to(self.center_pt)
        self.r1 = Circle(radius=radius*0.45, color=color, stroke_width=1.0, stroke_opacity=0.5).move_to(self.center_pt)
        self.cross_h = Line(self.center_pt - np.array([radius, 0, 0]), self.center_pt + np.array([radius, 0, 0]), color="#BACAD8", stroke_width=0.8, stroke_opacity=0.6)
        self.cross_v = Line(self.center_pt - np.array([0, radius, 0]), self.center_pt + np.array([0, radius, 0]), color="#BACAD8", stroke_width=0.8, stroke_opacity=0.6)
        self.sweep_line = Line(self.center_pt, self.center_pt + np.array([radius, 0, 0]), color="#F78908", stroke_width=2.4)
        self.blip = Dot(self.center_pt + np.array([0.45*radius, 0.4*radius, 0]), radius=0.05, color="#F78908")
        self.add(self.dish, self.bezel, self.r1, self.cross_h, self.cross_v, self.blip, self.sweep_line)
        self.angle = 0.0
        def update_sweep(mob, dt):
            mob.angle = (mob.angle + mob.speed * dt) % (2 * PI)
            end_pt = mob.center_pt + mob.radius * np.array([np.cos(mob.angle), np.sin(mob.angle), 0])
            mob.sweep_line.set_points_by_ends(mob.center_pt, end_pt)
            d = (mob.angle - 0.7) % (2 * PI)
            mob.blip.set_opacity(max(0.2, 1.0 - d * 0.5))
        self.add_updater(update_sweep)

class FlowingStream(VGroup):
    def __init__(self, start_pt, end_pt, color="#62B7E4", num_dots=4, speed=1.2, **kwargs):
        super().__init__(**kwargs)
        self.p0 = np.array(start_pt)
        self.p1 = np.array(end_pt)
        self.color = color
        self.num_dots = num_dots
        self.speed = speed
        self.rail = Line(self.p0, self.p1, color=color, stroke_width=1.5, stroke_opacity=0.4)
        self.dots = [Dot(radius=0.055, color=color) for _ in range(num_dots)]
        self.add(self.rail, *self.dots)
        self.t = 0.0
        def update_stream(mob, dt):
            mob.t += dt
            for i, dot in enumerate(mob.dots):
                alpha = (mob.t * mob.speed + i / float(mob.num_dots)) % 1.0
                dot.move_to(mob.p0 + alpha * (mob.p1 - mob.p0))
                dot.set_opacity(np.sin(alpha * PI))
        self.add_updater(update_stream)

class PulsingNode(VGroup):
    def __init__(self, center, radius=0.45, color="#2C81FE", label="", **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.radius = radius
        self.color = color
        self.core = Circle(radius=radius, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=color, stroke_width=2.5).move_to(self.center_pt)
        self.halo = Circle(radius=radius * 1.3, color=color, stroke_width=1.5).move_to(self.center_pt)
        self.add(self.core, self.halo)
        if label:
            self.lbl = CrispText(label, size=11, weight=BOLD, color="#404040").move_to(self.center_pt)
            self.add(self.lbl)
        self.t = 0.0
        def update_node(mob, dt):
            mob.t += dt
            s = 1.0 + 0.12 * np.sin(mob.t * 3.0)
            mob.halo.become(Circle(radius=mob.radius * 1.3 * s, color=mob.color, stroke_width=1.5).move_to(mob.center_pt))
            mob.halo.set_stroke(opacity=max(0.1, 0.6 + 0.4 * np.sin(mob.t * 3.0)))
        self.add_updater(update_node)

class BalanceScale(VGroup):
    def __init__(self, center, tilt_angle=0.12, beam_len=3.2, color="#404040", **kwargs):
        super().__init__(**kwargs)
        c = np.array(center)
        self.fulcrum = Polygon(c, c + np.array([-0.3, -0.5, 0]), c + np.array([0.3, -0.5, 0]), color=color, fill_color="#E5EDF4", fill_opacity=1.0, stroke_width=2.0)
        p_left = c + np.array([-np.cos(tilt_angle)*beam_len/2, -np.sin(tilt_angle)*beam_len/2, 0])
        p_right = c + np.array([np.cos(tilt_angle)*beam_len/2, np.sin(tilt_angle)*beam_len/2, 0])
        self.beam = Line(p_left, p_right, color=color, stroke_width=3.0)
        self.pivot = Dot(c, radius=0.07, color="#F78908")
        self.string_l = Line(p_left, p_left + DOWN * 0.5, color=color, stroke_width=1.2)
        self.tray_l = Arc(radius=0.45, start_angle=PI, angle=PI, color=color, stroke_width=2.0).move_to(p_left + DOWN * 0.72)
        self.string_r = Line(p_right, p_right + DOWN * 0.5, color=color, stroke_width=1.2)
        self.tray_r = Arc(radius=0.45, start_angle=PI, angle=PI, color=color, stroke_width=2.0).move_to(p_right + DOWN * 0.72)
        self.add(self.fulcrum, self.beam, self.pivot, self.string_l, self.tray_l, self.string_r, self.tray_r)
"""
                code_content = crisp_def + "\n\n" + code_content

            # Ensure clean step transitions without zombie mobject leaks
            code_content = self.ensure_clean_step_transitions(code_content)

            # Ensure authoritative SME layout constant is explicitly declared at module top
            if "SME_LAYOUT" not in code_content:
                layout_val = sc_layout if "sc_layout" in locals() and sc_layout else "70"
                code_content = f"SME_LAYOUT = '{layout_val}'\n" + code_content

            with open(scene_file_path,'w', encoding='utf-8') as f:
                f.write(code_content)

            try:
                sanitize_file(scene_file_path)
            except Exception as e:
                print(f"[Sanitizer Warning] Failed sanitizing {scene_file_path}: {e}")

        
        feedback_functions_dir = os.path.join(base_folder,"manim_codes/feedback_functions")
        os.makedirs(feedback_functions_dir,exist_ok=True)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_ff_dir = os.path.join(script_dir, "helpers", "feedback_functions")
        if not os.path.exists(src_ff_dir):
            src_ff_dir = os.path.join(script_dir, "feedback_functions")
        if not os.path.exists(src_ff_dir):
            src_ff_dir = os.path.abspath("feedback_functions")

        if os.path.exists(src_ff_dir):
            for ff in ["instrumented_scene.py", "scene_snapshot.py"]:
                f_path = os.path.join(src_ff_dir, ff)
                if os.path.exists(f_path):
                    shutil.copy2(f_path, feedback_functions_dir)

        # Copy Simplilearn OSL 3.0 reusable templates and intro icons into manim_codes
        manim_codes_dir = os.path.join(base_folder, "manim_codes")
        for tmpl in [
            "template1_title_intro.py",
            "template2_learning_roadmap.py",
            "template3_topic_coverage.py",
            "template4_process_flow.py",
            "template5_action_flowchart.py",
            "vector_primitives.py"
        ]:
            tmpl_src = os.path.join(script_dir, "helpers", tmpl)
            if not os.path.exists(tmpl_src):
                tmpl_src = os.path.join(PROJECT_ROOT, "template", tmpl)
            if not os.path.exists(tmpl_src):
                tmpl_src = os.path.join(script_dir, tmpl)
            if os.path.exists(tmpl_src):
                shutil.copy2(tmpl_src, manim_codes_dir)

        icons_src = os.path.join(script_dir, "helpers", "intro_icons")
        if not os.path.exists(icons_src):
            icons_src = os.path.join(PROJECT_ROOT, "template", "intro_icons")
        if not os.path.exists(icons_src):
            icons_src = os.path.join(script_dir, "intro_icons")
        icons_dst = os.path.join(manim_codes_dir, "intro_icons")
        if os.path.exists(icons_src):
            shutil.copytree(icons_src, icons_dst, dirs_exist_ok=True)
        
        return scene_code_path

    def process_files(self, target_topic_id=None):
        """
        Main logic to process unprocessed files.
        """
        input_tracker = self._load_tracker(self.input_tracker_path)
        if not input_tracker:
            print(f"Input tracker is empty or missing: {self.input_tracker_path}")
            return

        print(f"Found {len(input_tracker)} items in input tracker.")

        for topic_id, input_entry in input_tracker.items():
            if target_topic_id and topic_id != target_topic_id:
                continue
            # 1. Skip if input processed is False
            # We cannot process a narration if the previous stage (storyboard) failed or isn't done.
            if not input_entry.get("processed", False) and os.environ.get("FORCE_RUN") != "1":
                print(f"Skipping {topic_id}: Input not marked as processed.")
                continue

            # 2. Check output tracker (Reload to define current state)
            output_tracker = self._load_tracker(self.output_tracker_path)

            if topic_id in output_tracker and output_tracker[topic_id].get("processed", False) and os.environ.get("FORCE_RUN") != "1":
                print(f"Skipping {topic_id}: Already processed in output tracker.")
                continue

            print(f"Processing {topic_id}...")
            
            base_folder = os.path.join(self.input_folder, topic_id)
            
            # Define expected file paths
            config_path = os.path.join(base_folder, "ex_config.json")
            
            if not os.path.exists(config_path):
                print(f"Skipping {topic_id}: Missing context.txt or ex_config.json.")
                continue
            
            try:
                # Read input files
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                theme = config_data.get("theme", "dynamic_learning")
                # 3. Call fit_scene
                output_file_path = self.generate_code(config_data, topic_id, theme)
                
                # 4. Update tracker (Success)
                # Re-load tracker to minimize race conditions
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": output_file_path,
                    "processed": True,
                    "topic_name": topic_id,
                    "topic_id": topic_id,
                    "failure_reason": None
                }
                self._save_tracker(self.output_tracker_path,tracker)
                print(f"Successfully processed {topic_id}.")

            except Exception as e:
                print(f"Error processing {topic_id}: {e}")
                # 5. Update tracker (Failure)
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": None,
                    "processed": False,
                    "topic_name": topic_id,
                    "topic_id": topic_id,
                    "failure_reason": str(e)
                }
                self._save_tracker(self.output_tracker_path,tracker)

    def generate_for_folder(
        self,
        folder_path: str,
        topic_name: Optional[str] = None,
        provider: str = "gemini",
        model_name: str = "gemini-3.8-flash",
        force: bool = False
    ) -> str:
        folder = Path(folder_path)
        topic = topic_name or folder.name
        vendor = "google" if provider in ["auto", "gemini"] else provider

        config_data = {}
        ex_config_file = folder / "ex_config.json"
        if ex_config_file.exists():
            try:
                with open(ex_config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                pass

        config_data.update({
            "base_folder": str(folder),
            "asset_class_model_name": config_data.get("asset_class_model_name", "gemini-3.8-flash"),
            "asset_builder_model_name": config_data.get("asset_builder_model_name", "gemini-3.8-flash"),
            "scene_coding_vendor": config_data.get("scene_coding_vendor", vendor),
            "scene_coding_model_name": model_name if model_name != "gemini-3.8-flash" else config_data.get("scene_coding_model_name", "gemini-3.8-flash"),
            "styling_vendor": config_data.get("styling_vendor", "google"),
            "styling_model_name": config_data.get("styling_model_name", "gemini-3.8-flash"),
            "theme": config_data.get("theme", "dynamic"),
            "force": force
        })
        return self.generate_code(config_data, topic, theme="dynamic")


if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 10: Manim Community Code Generation")
    parser.add_argument("-i", "--input-folder", default=None, help="Directory containing stage JSONs")
    parser.add_argument("-o", "--output-folder", default=None, help="Output directory for manim_codes")
    parser.add_argument("-p", "--provider", default="gemini", choices=["auto", "gemini", "claude", "local"], help="Coding LLM provider")
    parser.add_argument("-m", "--model", default="gemini-3.8-flash", help="Coding LLM model name")
    parser.add_argument("-t", "--topic", default=None, help="Topic identifier")
    parser.add_argument("-s", "--scene", default=None, help="Target scene ID (e.g. 3)")
    parser.add_argument("-f", "--force", action="store_true", help="Force regenerate existing manim codes")
    args = parser.parse_args()

    if args.scene:
        os.environ["TARGET_SCENE"] = str(args.scene)

    if args.input_folder:
        folder = Path(args.input_folder).resolve()
        topic = args.topic or folder.name
        generator = CodeGenerator(
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            claude_api_key=os.environ.get("CLAUDE_API_KEY"),
            input_folder=str(folder.parent)
        )
        generator.generate_for_folder(
            folder_path=str(folder),
            topic_name=topic,
            provider=args.provider,
            model_name=args.model,
            force=args.force
        )
    else:
        styling_generation_tracker = "../ppt_trackers/styling_output_tracker.json"
        code_gen_tracker = "../ppt_trackers/code_generation_tracker.json"
        stage = CodeGenerator(
            input_tracker_path=styling_generation_tracker, 
            google_api_key=os.environ.get("GOOGLE_API_KEY"), 
            claude_api_key=os.environ.get("CLAUDE_API_KEY"),
            output_tracker_path=code_gen_tracker, 
            input_folder=os.path.abspath("../data_ppt_advanced")
        )
        stage.process_files()