"""
================================================================================
PIPELINE STAGE 14: IMPLEMENT CODE CORRECTIONS
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 14
   - Script Name: 14_implement_corrections.py
   - Primary Class: ImplementCodeCorrections
   - Pipeline Role:
     Applies the code-level repair directives generated in Stage 13 to produce an updated,
     corrected version of each Manim scene script in manim_extracted_codes/. In addition,
     it instruments the updated scripts with VLM keyframe probes (from feedback_functions_vlm/)
     to prepare the scenes for visual multimodal inspection in Stage 15.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 13 (13_generate_corrections.py):
       - How: Ingests correction_insights/scene_{group}/suggestions.txt via
         13_suggest_corrections_tracker.json.
       - Purpose: Contains specific code repair instructions to apply to the scene.
     * Stage 10 (10_generate_code.py):
       - How: Ingests current Manim scripts manim_codes/group_{group}.py.
       - Purpose: Baseline code to refactor and repair.
     * Stage 1, Stage 2, Stage 5:
       - How: Ingests instructions_<model>.json, detailed_instructions_<model>.json, and CGI_Input.json.
       - Purpose: Ensures timing and pedagogical structure remain preserved during refactoring.
     * Instrumentation Package:
       - How: Injects VLM probe handlers from feedback_functions_vlm/ into the topic directory.
   - Input Tracker: ppt_trackers/13_suggest_corrections_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * correction_insights/scene_{group}/suggestions.txt (Stage 13):
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights/scene_{group}/suggestions.txt
       Content: Actionable code repair instructions.
     * manim_codes/group_{group}.py (Stage 10):
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_codes/group_*.py
       Content: Current Manim scene code.
     * feedback_functions_vlm/ helper modules:
       Location: feedback_functions_vlm/
       Content: Probes for rendering step transition keyframes for VLM inspection.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Configuration specifying 'implement_corrections_api' and 'implement_corrections_model_name'.
     * Input Tracker:
       Location: ppt_trackers/13_suggest_corrections_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 13_suggest_corrections_tracker.json.
   - Step 2: Injects VLM instrumentation helpers into the topic workspace.
   - Step 3: Passes the existing Manim script and Stage 13 repair suggestions to an LLM
     (Gemini or Claude) to produce a refactored Python script.
   - Step 4: Runs the rewritten script through code_sanitizer.sanitize_file() to enforce
     anti-stacking rules, container bounds, and MathTex contrast.
   - Step 5: Saves the updated script into manim_extracted_codes/group_{n}.py.
   - Step 6: Atomically updates 14_corrections_implement_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * manim_extracted_codes/group_{n}.py:
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_extracted_codes/group_*.py
       Content: First-pass corrected Manim scene scripts, instrumented for VLM keyframe capture.
     * Output Tracker:
       Location: ppt_trackers/14_corrections_implement_tracker.json
       Content: Atomic tracker confirming completion of code correction implementation.

6. DOWNSTREAM CONSUMERS:
   - Stage 15 (15_run_manim_vlm_feedback.py): Compiles these scripts to capture visual keyframes.
   - Stage 19 & 20: Reads manim_extracted_codes/ as the base code for multimodal styling.
================================================================================
"""

import os
import sys
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)


import json
import os
import glob
from pathlib import Path
import portalocker
import time
import re
from google import genai
from google.genai import types
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
import shutil
from dotenv import load_dotenv
load_dotenv()
from code_sanitizer import sanitize_file

class ImplementCodeCorrections:
    """
    Stage 14: Implement Code Corrections.
    Applies Stage 13 repair directives to refactor Manim scripts, injects VLM keyframe
    instrumentation, and outputs updated scripts to manim_extracted_codes/.
    """

    def __init__(
        self,
        input_tracker_path,
        output_tracker_path,
        google_api_key,
        claude_api_key,
        input_folder
    ):
        # Store required class variables (placeholders allowed)
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.google_api_key = google_api_key
        self.claude_api_key = claude_api_key
        self.input_folder = input_folder
        
        # Initialize output tracker file if it doesn't exist
        if not os.path.exists(self.output_tracker_path):
            # Ensure the directory exists
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
        text = text.strip()
        fence_match = re.match(r"^```(?:python)?\s*\n(.*)\n```$", text, re.DOTALL)
        if fence_match:
            return fence_match.group(1)
        return text

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



    def generate_code_corrections(self, config_data, topic_id):
        """
        Function for the generate_code_corrections logic.
        This would typically call the LLM APIs using the API keys and prompts.
        """
        print(f"  [Simulated] Running generate_code_corrections for {topic_id} using keys: {self.google_api_key[:5]}... / {self.claude_api_key[:5]}...")
        
        base_folder = config_data['base_folder']
        meta_dir = os.path.join(base_folder, "metadata_blueprints")

        guideline_model_name = config_data['styling_model_name']
        asset_class_model_name = config_data['asset_class_model_name']

        google_client = genai.Client(api_key=self.google_api_key)

        instructions_output_file = os.path.join(meta_dir, f"enhanced_anim_{guideline_model_name}.json")
        if not os.path.exists(instructions_output_file):
            instructions_output_file = f"{base_folder}/enhanced_anim_{guideline_model_name}.json"
        if not os.path.exists(instructions_output_file):
            for cand in list(Path(meta_dir).glob("enhanced_anim_*.json")) + list(Path(base_folder).glob("enhanced_anim_*.json")):
                instructions_output_file = str(cand)
                break
        if not os.path.exists(instructions_output_file):
            for cand in list(Path(meta_dir).glob("instructions_*.json")) + list(Path(base_folder).glob("instructions_*.json")) + list(Path(meta_dir).glob("*presentation_composition*.json")) + list(Path(base_folder).glob("*presentation_composition*.json")) + list(Path(meta_dir).glob("*blueprint*.json")) + list(Path(base_folder).glob("*blueprint*.json")):
                instructions_output_file = str(cand)
                break
        scene_code_dir = f"{base_folder}/manim_codes"
        refined_scene_codes_dir = f"{base_folder}/manim_extracted_codes"
        cgi_file = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_file):
            cgi_file = f"{base_folder}/CGI_Input.json"
        asset_classification_output_file = os.path.join(meta_dir, f"asset_classification_{asset_class_model_name}.json")
        if not os.path.exists(asset_classification_output_file):
            asset_classification_output_file = f"{base_folder}/asset_classification_{asset_class_model_name}.json"
        if not os.path.exists(asset_classification_output_file):
            for cand in list(Path(meta_dir).glob("asset_classification_*.json")) + list(Path(base_folder).glob("asset_classification_*.json")) + list(Path(meta_dir).glob("*classified_assets*.json")) + list(Path(base_folder).glob("*classified_assets*.json")):
                asset_classification_output_file = str(cand)
                break

        '''
        spurious_patterns_file = "./spurious_code_patterns.txt"
        with open(spurious_patterns_file,'r') as f:
            spurious_patterns = f.read()
        '''
            
        os.makedirs(refined_scene_codes_dir,exist_ok=True)

        corrections_dir = f"{base_folder}/specific_suggestions"

        with open(instructions_output_file,'r',encoding='utf-8') as f:
            animation_instructions = json.load(f)

        if "scenes" in animation_instructions and isinstance(animation_instructions["scenes"], list):
            norm_instructions = {}
            for idx, sc in enumerate(animation_instructions["scenes"]):
                sc_id = str(sc.get("scene_id", idx + 1))
                norm_instructions[sc_id] = sc.get("composition_steps", [sc])
            animation_instructions = norm_instructions

        with open(cgi_file,'r',encoding='utf-8') as f:
            structured_cgi = json.load(f)

        asset_classification = {}
        if os.path.exists(asset_classification_output_file):
            with open(asset_classification_output_file,'r',encoding='utf-8') as f:
                asset_classification = json.load(f)


        system_prompt = f"""
        Refactor the Manim CE code to align with the storyboard (`matching_section` ↔ `## Presentation Step`) while preserving:
        - scene flow
        - storyboard intent
        - exact `run_time`

        The final code must compile and execute cleanly in Manim CE.

        ---

        ### ENGINEERING CORRECTIONS

        Fix:
        - out-of-bounds elements
        - overlaps and collisions
        - broken hierarchy/grouping
        - z-index/reveal ordering
        - invalid Manim usage
        - layout clarity issues
        - text overflow from panels and containers

        Ensure:
        - all storyboard elements are represented, including small details such as labels, ticks, timelines, indicators, and supporting annotations
        - all `ImageMobject` and its associated grouped visual systems are wrapped inside `Group` and not `VGroup`
        - `Text(..., text_alignment=...)` is never used
        - `interpolate_color` always wraps colors using `ManimColor(...)`
        - panel/container objects use solid fills with contrasting strokes
        - `ImageMobject` sizing uses `scale_to_fit_width` or `scale_to_fit_height`
        - images never receive explicit color styling. Make sure the correct image paths are used.
        - the implementation of get_elastic_grow method is not changed
        - `MathTex` is used for mathematical notation, LaTeX equations and other mathematical symbols
        - UNIFORM LATEX & NON-LATEX SIZING: MathTex must nearly match the size of surrounding text (CrispText):
          * Standalone formulas / equation cards: ALWAYS use font_size=22 to font_size=26 (or scale 0.45 to 0.55). NEVER use font_size >= 28 or scale 0.75–1.2!
          * Inline math next to labels/body text: ALWAYS use font_size=16 to font_size=18.
          * Inside any card or sub-panel, formula width MUST NEVER exceed 2.9 units! Always clamp with `if hasattr(f, "width") and f.width > max_w: f.scale_to_fit_width(max_w)`.
        - GRAPH AXES & FUNCTION PLOT LIFECYCLE: Position Axes BEFORE plotting curves (`axes.plot(...)`) or positioning annotations (`axes.c2p(...)`). Explicitly FadeOut all curves and annotations at step boundaries so they never linger into later steps!
        - STRICT UNIFORM FONT SIZING ACROSS BOXES, CARDS, TABLES & SHAPES:
          * In tables, matrices, cards, and shapes, all text MUST maintain a strictly UNIFORM base font size (13pt to 15pt).
          * NEVER call `.scale_to_fit_width(...)` on text objects to force them to fit container width, as this shrinks longer text down and creates jarring font disparities across sibling boxes.
          * When text exceeds the container width, insert explicit newline linebreaks (`\n`) so text wraps across 2 or 3 lines while keeping font size constant.
          * Containers and cards must dynamically expand their height:
            `calc_h = max(default_h, content.height + 2 * pad_y)`
            to accommodate multi-line wrapped text with a minimum internal padding of 0.25 units on all sides.
          * Text must NEVER bleed out of or touch container borders.
        - STRICT CASING & COLOR PALETTE ENFORCEMENT:
          * NO ALL-CAPS: All titles, subtitles, card headers, labels, and tags must NEVER be written in ALL CAPS. Use Title Case for titles and headers; use Sentence Case for descriptions and bullet points.
          * Text Color: Text on light cards and white canvas MUST be `#404040` (Dark Charcoal). Text on dark navy headers (#0B3C5D) must be `#FFFFFF`.
          * Approved 10-Color Palette: Sky Blue (#62B7E4), Steel Blue (#7EA2C8), Lavender (#9B99C7), Mint (#8ECDB7), Warm Amber (#E6A157), Mustard Gold (#DDB945), Coral (#E58F6D), Warm Tan (#B88968), Dusty Rose (#D98CA1), Soft Lilac (#C1A5C6).
          * Focus Highlight: #F78908 (3px stroke, 1.0s draw time). Green is strictly forbidden for containers and cards.
        - STRICT ANTI-PPT & AUTHENTIC LIVING MECHANISM MANDATE:
          * NEVER convert living vector diagrams, dials, gauges, neural cores, or network flows into rectangular PowerPoint container cards or slide boxes!
          * Maintain authentic kinetic visual mechanisms and transparent hero illustrations directly in open space.
          * Reposition, shift, or pad elements to resolve overlaps and boundary overflows without boxing diagrams into container cards.
        - SAFE SCREEN MARGINS & CLEARANCES:
          * Keep all visual elements within safe canvas bounds: x in [-6.5, 6.5], y in [-3.5, 3.5].
          * Layout 70 (Split SME): Reserve left area x < -1.20 for the SME window; content arena must stay at x >= -1.20.
          * Layout 20 (PiP): Reserve top-right corner (x >= 3.80, y >= 1.50) for the presenter window. Lead-in lines and headers must terminate at or left of x <= 3.70.
        - multi-line text with \n is centered and spaced evenly inside cards and cells
        - GLOW & STROKE OVERLAYS MUST HAVE TRANSPARENT FILLS (set_fill(opacity=0)): When creating glow, halo, pulse, or outline highlights by duplicating mobjects (`mob.copy().set_stroke(...)`), ALWAYS chain `.set_fill(opacity=0)`. NEVER leave `fill_opacity > 0` on duplicate mobjects overlaid on cards or containers as opaque fills mask underlying text.
        - CARD DESCRIPTIONS MUST BE LEFT-ALIGNED: Inside cards with icons/badges on the left, description/body text MUST be left-aligned (`align="left"`, `aligned_edge=LEFT`).
        - CONCLUDING SCENES & TAKEAWAY PEDAGOGY (NO BLANK TABLES): Step 4 must synthesize actionable insights using structured takeaway cards or comparative framework nodes. Every card must have a distinct numbered badge, title, concise single-line description, and formula tag where appropriate. Never render blank tables or placeholder grids.

        Avoid absolute placement for off-screen objects.

        If any object center exceeds:
        - `RIGHT * 5.5`
        - `LEFT * 5.5`
        - `UP * 3.5`
        - `DOWN * 3.5`

        reposition using relative layout methods such as:

        ```python
        obj.next_to(reference_obj, RIGHT, buff=0.4)
        ````

        Prefer:

        * `next_to`
        * `align_to`
        * relative anchoring over hardcoded coordinates.

        ---

        ### BACKGROUND COLOR
        Make sure that the background color of the video is always #FFFFFF. You can set it using
        self.camera.background_color = "#FFFFFF"

        ### VISUAL REFINEMENT

        Refine assets and inline constructions so they resemble believable real-world objects rather than symbolic geometry.

        Where useful:

        * improve curvature
        * add layered structural details
        * enhance proportions
        * introduce thickness/bevel cues
        * refine subcomponent separation
        * improve silhouette readability

        Do not oversimplify assets into primitive placeholders.
        Do not change the page title placement and decoration, EXCEPT when multiple overlapping titles or duplicate headers are reported in the upper margin; in that case, remove the redundant header layer to maintain exactly one clean, authoritative title.

        ### STEP BOUNDARY LIFECYCLE & TRANSIENT CLUTTER CLEANUP
        - At the start of each `## Presentation Step N`, explicitly FadeOut all transient indicators, status pills, intermediate callout cards, and directional arrows from Step N-1 before fading in new step elements.
        - Never allow previous step pills or cards to linger on screen when new cards are introduced at the same location, as this causes massive overlapping clutter.
        - Title transitions: When transitioning between step titles, ensure the outgoing title fades out before the incoming title appears, or use a clean sequential transition to avoid double-exposure ghosting.
        - For checkmarks and status ticks: NEVER use raw Unicode characters (such as "✓", "✔", "\\u2713") inside CrispText or Text. Always construct checkmarks using vector shapes (e.g. `VGroup(Line(...), Line(...))`) or `MathTex(r"\\checkmark")`.
        Prefer center alignment of Titles and Subtitles within their respective panels

        ### RUN TIME ADJUSTMENT

        Make sure the overall time budget of the individual presentation steps is aligned to that of the run_time for that step

        ### TARGETED REVIEW FEEDBACK

        You may receive section-specific repair suggestions generated from a prior scene review.

        Apply these suggestions as concrete engineering directives to eliminate collisions and container bleedings.

        Use them to:

        * apply reported coordinate shifts to eliminate overlaps
        * resize or pad containers to prevent text overflow
        * prioritize fixes based on collision severity

        Do not apply them blindly.

        Before making a change:

        * verify it is consistent with the storyboard
        * verify it improves the reported issue
        * verify it does not introduce new overlaps or off-screen elements
        * prefer a better solution if one exists

        When multiple suggestions imply the same correction (e.g. connector layering or text repositioning), consolidate the fix into the smallest robust code change.

        Prefer structural fixes over per-object patches when appropriate.

        Examples:

        * Updating a shared connector helper is preferable to modifying every connector individually.
        * Repositioning a shared text anchor is preferable to manually adjusting every replacement text instance.
        * Fixing z-order at creation time is preferable to repeatedly setting z-index later.

        If any repair suggestions conflict the storyboard guidelines, prioritize the repair suggestions


        ---

        ### EXECUTION PRIORITY

        Prioritize:

        1. visual correctness
        2. structural clarity
        3. repair suggestions
        3. storyboard fidelity
        4. code robustness

        Minor storyboard inconsistencies may be overridden if required for visual coherence or executable correctness.
        
        Return only the modified Manim code.
        No explanations.
        No comments.
        """

        user_prompt = """
        For correcting the code script of the scene, refer to the following context:
        ------------------------
        Context:
        {scene_context}
        ------------------------
        Section Specific Repair Suggestions:
        {repair_suggestions}
        """

        for group, group_data in animation_instructions.items():
            if not isinstance(group_data, list):
                continue

            skip_scenes_env = os.environ.get("SKIP_SCENES")
            if skip_scenes_env and str(group) in [s.strip() for s in skip_scenes_env.split(",")]:
                print(f"Skipping Scene {group} per SKIP_SCENES")
                src = os.path.join(scene_code_dir, f"group_{group}.py")
                dst = os.path.join(refined_scene_codes_dir, f"group_{group}.py")
                if os.path.exists(src) and (not os.path.exists(dst) or src != dst):
                    shutil.copy2(src, dst)
                continue

            target_scene_env = os.environ.get("TARGET_SCENE")
            if target_scene_env and str(group) != str(target_scene_env):
                continue

            # Remove narration_statement from each group_data dictionary item
            for item in group_data:
                if isinstance(item, dict):
                    item.pop("narration_statement", None)

            # Locate original code (handle both Code_X and group_X naming)
            code_script_file = os.path.join(scene_code_dir, f"group_{group}.py")

            if not os.path.exists(code_script_file):
                print(f"Skipping group {group}: Original code script not found.")
                continue

            with open(code_script_file, 'r',encoding='utf-8') as f:
                code_script = f.read()
            

            output_file = os.path.join(refined_scene_codes_dir, f"group_{group}.py")
            
            # A scene is a pure template only if it exclusively calls a template function and has no multi-step presentation
            has_tmpl_call = any(t in code_script for t in ["play_title_intro(", "play_learning_roadmap(", "play_topic_coverage("])
            has_multiple_steps = "## Presentation Step 2" in code_script or "## Presentation Step 3" in code_script
            is_pure_template = has_tmpl_call and not has_multiple_steps and len(code_script.splitlines()) < 80

            if is_pure_template:
                print(f"Preserving official pure Simplilearn template for Scene {group} in Stage 14...")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(code_script)
                continue

            if os.path.exists(output_file):
                print(f"Refined code for group {group} already exists.")
                continue

            corrections_path = os.path.join(corrections_dir, f"scene_{group}_suggestions.txt")
            if os.path.exists(corrections_path):
                with open(corrections_path,'r',encoding='utf-8') as f:
                    repair_suggestions = f.read()
            else:
                repair_suggestions = ""

            print(f"Refining code for group {group} using Gemini 3.1 Pro (Medium Thinking Mode)...")

            for i,pair in enumerate(group_data):
                if isinstance(pair, dict) and group in structured_cgi and i < len(structured_cgi[group]) and isinstance(structured_cgi[group][i], dict):
                    pair.update({"run_time": structured_cgi[group][i].get("run_time", 5)})
            
            if group in asset_classification:
                for i,pair in enumerate(group_data):
                    if isinstance(pair, dict) and isinstance(asset_classification[group], list) and i < len(asset_classification[group]) and isinstance(asset_classification[group][i], dict) and "image_paths" in asset_classification[group][i] and asset_classification[group][i]["image_paths"]:
                        pair.update({"image_paths": asset_classification[group][i]["image_paths"]})

            scene_context = f"Manim script to refine:\n{code_script}\n\nStoryboard:\n{json.dumps(group_data,indent=2,ensure_ascii=False)}"

            try:
                # Configure for medium thinking depth via temperature and model parameters
                formatted_user_prompt = user_prompt.format(
                    scene_context = scene_context,
                    repair_suggestions = repair_suggestions
                )

                print(f"The overall prompt:\n{system_prompt}\n\n{formatted_user_prompt}")
                #choice = input("Continue? (y/n)")
                #if choice=="n":
                #    exit(1)

                response = google_client.models.generate_content(
                    #model="gemini-3.1-pro-preview",
                    model="gemini-3.5-flash",
                    contents=system_prompt + "\n\n" + formatted_user_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=45000,
                        thinking_config=types.ThinkingConfig(thinking_level="medium")
                    )
                )

                generated_code = response.text

                print(f"Generated code response for scene {group}:\n\n{generated_code}")
                
                code_content = self.remove_code_fences(generated_code)

                # Ensure the instrumented scene import is present
                if "from feedback_functions_vlm.instrumented_scene import InstrumentedScene" not in code_content:
                    if "from feedback_functions.instrumented_scene import InstrumentedScene" in code_content:
                        code_content = code_content.replace(
                            "from feedback_functions.instrumented_scene import InstrumentedScene",
                            "from feedback_functions_vlm.instrumented_scene import InstrumentedScene"
                        )
                    else:
                        code_content = "from feedback_functions_vlm.instrumented_scene import InstrumentedScene\n" + code_content

                if "class FinalScene(InstrumentedScene" not in code_content:
                    code_content = code_content.replace(
                        "class FinalScene(MovingCameraScene)",
                        "class FinalScene(InstrumentedScene, MovingCameraScene)"
                    ).replace(
                        "class FinalScene(Scene)",
                        "class FinalScene(InstrumentedScene, MovingCameraScene)"
                    )

                with open(output_file, 'w',encoding='utf-8') as f:
                    f.write(code_content)
                try:
                    sanitize_file(output_file)
                except Exception as san_err:
                    print(f"[Sanitizer Warning] {san_err}")
                print(f"Successfully saved refined code to {output_file}")

            except Exception as e:
                print(f"Error refining group {group}: {e}")
                # Robust fallback: use original code with updated instrumented scene import
                try:
                    fallback_code = code_script.replace(
                        "from feedback_functions.instrumented_scene import InstrumentedScene",
                        "from feedback_functions_vlm.instrumented_scene import InstrumentedScene"
                    )
                    if "from feedback_functions_vlm.instrumented_scene import InstrumentedScene" not in fallback_code:
                        fallback_code = "from feedback_functions_vlm.instrumented_scene import InstrumentedScene\n" + fallback_code
                    if "class FinalScene(InstrumentedScene" not in fallback_code:
                        fallback_code = fallback_code.replace(
                            "class FinalScene(MovingCameraScene)",
                            "class FinalScene(InstrumentedScene, MovingCameraScene)"
                        ).replace(
                            "class FinalScene(Scene)",
                            "class FinalScene(InstrumentedScene, MovingCameraScene)"
                        )
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(fallback_code)
                    try:
                        sanitize_file(output_file)
                    except Exception as san_err:
                        print(f"[Sanitizer Warning] {san_err}")
                    print(f"Used original code as fallback for group {group}")
                except Exception as fb_err:
                    print(f"Failed writing fallback for group {group}: {fb_err}")
                continue
        
        # Verify all expected scene code files exist
        target_scene_env = os.environ.get("TARGET_SCENE")
        missing_scenes = []
        for grp in animation_instructions.keys():
            if target_scene_env and str(grp) != str(target_scene_env):
                continue
            expected_file = os.path.join(refined_scene_codes_dir, f"group_{grp}.py")
            if not os.path.exists(expected_file):
                missing_scenes.append(grp)
        if missing_scenes:
            raise RuntimeError(f"Refined code files missing for scenes: {missing_scenes}")

        feedback_functions_dir = os.path.join(refined_scene_codes_dir, "feedback_functions_vlm")
        os.makedirs(feedback_functions_dir, exist_ok=True)
        init_file = os.path.join(feedback_functions_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "w").close()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_vlm_dir = os.path.join(script_dir, "helpers", "feedback_functions_vlm")
        if not os.path.exists(src_vlm_dir):
            src_vlm_dir = os.path.join(script_dir, "feedback_functions_vlm")
        shutil.copy2(os.path.join(src_vlm_dir, "instrumented_scene.py"), feedback_functions_dir)
        shutil.copy2(os.path.join(src_vlm_dir, "scene_snapshot.py"), feedback_functions_dir)

        # Copy official Simplilearn templates and intro_icons into refined_scene_codes_dir
        for tmpl in ["template1_title_intro.py", "template2_learning_roadmap.py", "template3_topic_coverage.py", "template4_process_flow.py", "template5_action_flowchart.py"]:
            tmpl_src = os.path.join(script_dir, "helpers", tmpl)
            if not os.path.exists(tmpl_src):
                tmpl_src = os.path.join(os.path.dirname(script_dir), "template", tmpl)
            if os.path.exists(tmpl_src):
                shutil.copy2(tmpl_src, refined_scene_codes_dir)

        icons_src = os.path.join(script_dir, "helpers", "intro_icons")
        if not os.path.exists(icons_src):
            icons_src = os.path.join(os.path.dirname(script_dir), "template", "intro_icons")
        if os.path.exists(icons_src):
            shutil.copytree(icons_src, os.path.join(refined_scene_codes_dir, "intro_icons"), dirs_exist_ok=True)

        return refined_scene_codes_dir

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
            if not input_entry.get("processed", False):
                print(f"Skipping {topic_id}: Input not marked as processed.")
                continue

            # 2. Check output tracker (Reload to define current state)
            output_tracker = self._load_tracker(self.output_tracker_path)

            if os.environ.get("FORCE_RUN") != "1" and topic_id in output_tracker and output_tracker[topic_id].get("processed", False):
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

                # 3. Call fit_scene
                output_file_path = self.generate_code_corrections(config_data, topic_id)
                
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

if __name__=="__main__":
    workflow_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(workflow_dir)
    trackers_dir = os.path.join(parent_dir, "ppt_trackers") if os.path.exists(os.path.join(parent_dir, "ppt_trackers")) else os.path.join(parent_dir, "trackers")
    data_dir = os.path.join(parent_dir, "output") if os.path.exists(os.path.join(parent_dir, "output")) else (os.path.join(parent_dir, "data_ppt_advanced") if os.path.exists(os.path.join(parent_dir, "data_ppt_advanced")) else os.path.abspath("."))

    correction_suggestions_tracker = os.path.join(trackers_dir, "13_suggest_corrections_tracker.json")
    if not os.path.exists(correction_suggestions_tracker):
        correction_suggestions_tracker = os.path.join(trackers_dir, "suggest_corrections_tracker.json")
    correction_implement_tracker = os.path.join(trackers_dir, "14_corrections_implement_tracker.json")
    if not os.path.exists(correction_implement_tracker):
        correction_implement_tracker = os.path.join(trackers_dir, "corrections_implement_tracker.json")

    stage = ImplementCodeCorrections(
        input_tracker_path=correction_suggestions_tracker, 
        google_api_key=os.environ.get("GOOGLE_API_KEY"), 
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        output_tracker_path=correction_implement_tracker, 
        input_folder=data_dir
    )
    stage.process_files()