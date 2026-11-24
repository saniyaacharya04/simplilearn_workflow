"""
================================================================================
PIPELINE STAGE 13: CORRECTION SUGGESTIONS GENERATION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 13
   - Script Name: 13_generate_corrections.py
   - Primary Class: SuggestCorrections
   - Pipeline Role:
     Translates the geometric feedback and crash diagnostics from Stage 12 into
     actionable, code-level repair directives. Prompts an LLM (Claude or Gemini)
     to review the scene's current Manim code alongside the identified collision/clipping
     issues, producing targeted recommendations (such as shift offsets, container resizing,
     or z-index reordering) before code rewriting begins.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 12 (12_generate_feedback_report.py):
       - How: Ingests correction_insights/scene_{group}/report.json via
         12_generate_feedback_tracker.json.
       - Purpose: Provides list of geometric violations, overlapping mobject pairs,
         and boundary coordinates.
     * Stage 10 (10_generate_code.py):
       - How: Ingests original Manim code manim_codes/group_{group}.py.
       - Purpose: Supplies context of how objects were constructed and positioned in code.
     * Stage 1, Stage 2, Stage 5:
       - How: Ingests instructions_<model>.json, detailed_instructions_<model>.json, and CGI_Input.json.
       - Purpose: Preserves pedagogical narrative and section timings.
   - Input Tracker: ppt_trackers/12_generate_feedback_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * correction_insights/scene_{group}/report.json (Stage 12):
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights/scene_{group}/report.json
       Content: Algorithmic collision and clipping report.
     * manim_codes/group_{group}.py (Stage 10):
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_codes/group_*.py
       Content: Current Manim script for the scene.
     * instructions_<model>.json (Stage 1), detailed_instructions_<model>.json (Stage 2), CGI_Input.json (Stage 5)
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Configuration specifying 'suggest_corrections_api' and 'suggest_corrections_model_name'.
     * Input Tracker:
       Location: ppt_trackers/12_generate_feedback_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 12_generate_feedback_tracker.json.
   - Step 2: Loads the geometric report, Manim script, and scene metadata.
   - Step 3: Checks if report.json contains any detected issues:
     * If no issues exist, outputs a "No corrections required" confirmation.
     * If issues exist, formats an LLM prompt containing the Python code and specific collision details.
   - Step 4: The LLM generates precise, line-referenced repair directives (e.g., "Shift card_b down by 0.5",
     "Reduce font size from 28 to 22", "Increase horizontal spacing buffer in VGroup").
   - Step 5: Writes suggestions into correction_insights/scene_{group}/suggestions.txt.
   - Step 6: Atomically updates 13_suggest_corrections_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * correction_insights/scene_{group}/suggestions.txt:
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights/scene_{group}/suggestions.txt
       Content: Actionable code correction instructions detailing what coordinates,
                scales, or transitions to modify.
     * Output Tracker:
       Location: ppt_trackers/13_suggest_corrections_tracker.json
       Content: Atomic tracker confirming completion of suggestion generation.

6. DOWNSTREAM CONSUMERS:
   - Stage 14 (14_implement_corrections.py): Consumes suggestions.txt to rewrite Manim code.
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
import google.generativeai as genai
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
from dotenv import load_dotenv
load_dotenv()

class SuggestCorrections:
    """
    Stage 13: Correction Suggestions.
    Synthesizes code-level repair directives from Stage 12 geometric feedback reports
    and current Manim scripts using LLM reasoning.
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


    def correction_suggestions(self, config_data, topic_id):
        """
        Function for the correction_suggestions logic.
        This would typically call the LLM APIs using the API keys and prompts.
        """
        print(f"  [Simulated] Running correction_suggestions for {topic_id} using keys: {self.google_api_key[:5]}... / {self.claude_api_key[:5]}...")
        
        guideline_model_name = config_data.get('jazzy_model_name', 'gemini-2.5-flash')
        asset_class_model_name = config_data.get('asset_class_model_name', 'gemini-2.5-flash')

        base_folder = config_data['base_folder']
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        instructions_file = os.path.join(meta_dir, f"enhanced_anim_{guideline_model_name}.json")
        if not os.path.exists(instructions_file):
            instructions_file = f"{base_folder}/enhanced_anim_{guideline_model_name}.json"
        if not os.path.exists(instructions_file):
            for cand in list(Path(meta_dir).glob("enhanced_anim_*.json")) + list(Path(base_folder).glob("enhanced_anim_*.json")) + list(Path(meta_dir).glob("*presentation_composition*.json")) + list(Path(base_folder).glob("*presentation_composition*.json")) + list(Path(meta_dir).glob("*blueprint*.json")) + list(Path(base_folder).glob("*blueprint*.json")):
                instructions_file = str(cand)
                break
        code_folder = f"{base_folder}/manim_codes"
        insights_report_dir = f"{base_folder}/llm_error_reports"
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
        correction_vendor = config_data.get("correction_vendor", "google")
        correction_model_name = config_data.get("correction_model_name", "gemini-2.5-flash")

        specific_suggestions_folder = f"{base_folder}/specific_suggestions"
        os.makedirs(specific_suggestions_folder,exist_ok=True)

        if correction_vendor == "google":
            genai.configure(api_key=self.google_api_key)

        with open(instructions_file,'r',encoding='utf-8') as f:
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

        if "scenes" in asset_classification and isinstance(asset_classification["scenes"], list):
            norm_ac = {}
            for idx, sc in enumerate(asset_classification["scenes"]):
                sc_id = str(sc.get("scene_id", idx + 1))
                norm_ac[sc_id] = [sc]
            asset_classification = norm_ac

        construction_guidelines_dict = {}
        for cand in list(Path(meta_dir).glob("construction_output_*.json")) + list(Path(base_folder).glob("construction_output_*.json")):
            try:
                with open(cand, 'r', encoding='utf-8') as cf:
                    c_data = json.load(cf)
                    if isinstance(c_data, dict):
                        for a_id, a_info in c_data.items():
                            if isinstance(a_info, dict):
                                construction_guidelines_dict[a_id] = a_info.get("construction_paragraph", "")
                        construction_guidelines_dict.update(c_data)
            except Exception:
                pass
        for cand in list(Path(meta_dir).glob("*constructed_assets*.json")) + list(Path(base_folder).glob("*constructed_assets*.json")):
            try:
                with open(cand, 'r', encoding='utf-8') as cf:
                    c_data = json.load(cf)
                    if isinstance(c_data, dict):
                        for a_id, a_info in c_data.items():
                            if isinstance(a_info, dict):
                                construction_guidelines_dict[a_id] = a_info.get("construction_paragraph", a_info.get("guidelines", ""))
                        construction_guidelines_dict.update(c_data)
            except Exception:
                pass

        system_prompt = """
        You are an expert motion graphics reviewer for Manim scenes.

        You will receive:

        1. STORYBOARD (intended visual behavior and timing)
        2. MANIM CODE (generated scene)
        3. INSIGHTS REPORT (detected issues and spatial constraints)

        Your task is to generate repair suggestions for a downstream code-modification model.

        Do NOT generate code.

        Do NOT explain Manim APIs.

        Do NOT restate the issue report.

        Use the storyboard as the source of truth.

        ## Objective

        Identify the smallest visual changes needed to make the rendered scene match the storyboard while resolving reported issues.

        ## Allowed Suggestion Types

        * Reposition objects
        * Adjust spacing between objects
        * Remove or exit objects that should no longer be visible
        * Restore missing storyboard elements
        * Correct visibility/layering issues
        * Re-anchor labels, text, nodes, or connectors

        Prefer modifying the fewest objects possible.

        ## Constraint Usage

        Use the provided constraints to avoid introducing new collisions.

        When multiple fixes are possible:

        * Prefer moving labels/text before structural objects.
        * Prefer moving objects into available whitespace before resizing or restructuring.
        * Prefer local nudges over large layout changes.
        * Preserve existing symmetry, alignment axes, radial relationships, and spacing between related objects.
        * Never solve text fitting problems by scaling text Mobjects.
        * Preserve existing scene composition whenever possible.
        * Make sure position adjustments keep objects within x ∈ [-7,7], y ∈ [-3.9,3.9].
        * When possible, move an object toward available whitespace rather than shrinking it.
        * After every repositioning, preserve the alignment, symmetry and spacing relationships of the surrounding composition.
        * When excessive overlaps happen due to clutter, prefer exiting objects with lower opacity from previous presentation steps and let the current section by enlarged and centerstaged (Even if suggested otherwise in the storyboard)
        * Where temporary overlaps occur due to Transform or ReplacementTransform or due to FadeIn and FadeOut grouped in the same self.play call, make sure the existing object is faded out before the new object is brought in through GrowFromCenter

        ## Layout Preservation Guardrails

        Preserve the visual geometry of the existing composition while making repairs.

        * Do not disturb intentional symmetry, radial alignment, common axes, or balanced spacing between related items.
        * When moving one item within a symmetric or repeated structure, preserve the alignment and spacing relationships of its peers.
        * Prefer moving objects into available whitespace over shrinking, compressing, or restructuring existing content.
        * Before changing an object's position, use available screen space around it and avoid creating new collisions.
        * Prefer local repositioning over resizing whenever possible.

        ## Text Sizing Guardrails

        Text readability and consistent visual scale are higher priority than fitting text into a constrained region.

        * Do NOT scale Text or text-like Mobjects to make them fit horizontally or vertically.
        * Do NOT independently resize text to resolve overlaps or overflow.
        * Preserve relative font-size relationships between text elements.
        * When text does not fit, prefer repositioning it or allowing it to wrap across multiple lines.
        * Preserve the intended visual prominence of headings, labels, annotations, and supporting text.
        
        ## Text Overflow & Container Bleeding Guardrails

        Text must NEVER bleed out of or touch container borders:
        * When a Text or MathTex object overflows its container/card:
          - Direct expanding the container's width or height dynamically: `card_h = max(default_h, text_mob.height + 2 * padding)` with min padding >= 0.25 units.
          - If text exceeds container width horizontally, direct inserting explicit newline breaks (`\n`) to wrap text across 2-3 balanced lines while keeping font size strictly constant.
          - NEVER resolve text fitting by calling `.scale(...)` or `.scale_to_fit_width(...)` on text objects.
        * For resolving overlaps between sibling cards or elements:
          - Specify the exact directional shift (e.g. "Shift card_b DOWN by {overlap_extent + 0.35:.2f} units") to eliminate collision completely.

        ## Simplilearn Brand, Color & Casing Guardrails

        * STRICT NO ALL-CAPS MANDATE: All titles, subtitles, card headers, labels, and tags must NEVER be written in ALL CAPS. Use Title Case for titles and card headers; use Sentence Case for descriptions and bullet points.
        * Approved Color Palette: Use the 10 approved infographic pastel tones (#62B7E4 Sky Blue, #7EA2C8 Steel Blue, #9B99C7 Lavender, #8ECDB7 Mint, #E6A157 Warm Amber, #DDB945 Mustard Gold, #E58F6D Coral, #B88968 Warm Tan, #D98CA1 Dusty Rose, #C1A5C6 Soft Lilac).
        * Text Contrast: Primary text inside light cards/canvas MUST be #404040. Header text on dark navy cards (#0B3C5D) must be #FFFFFF.
        * Focus Highlight: Use #F78908 (3px stroke, 1.0s draw time). Green is strictly forbidden for containers and cards.
        
        ## Step Lifecycle, Lingering Clutter & Symbol Guardrails

        * STEP BOUNDARY CLEANUP & CLUTTER ELIMINATION:
          - When transient indicators, pills, cards, or callouts from a previous presentation step linger into subsequent steps and cause overlaps or visual clutter, DO NOT prescribe tiny micro-shifts (0.1 units).
          - Instead, explicitly prescribe: "FadeOut lingering objects [list object names] before introducing Step N elements."
        * SINGLE HEADER AUTHORITY & NO DUPLICATE TITLES:
          - If a scene has a persistent manual header (e.g. `header_grp = Group(kicker, main_header)`) and also calls `create_title(...)` in the same corner causing double-text overlaps, explicitly prescribe: "Remove the duplicate title layer (or remove redundant create_title / header_grp) to leave exactly one clean title."
        * VECTOR SYMBOLS & NO RAW UNICODE:
          - Never suggest using raw Unicode characters (such as "✓", "✔", "\\u2713") inside CrispText or Text. Always prescribe constructing checkmarks using vector lines (e.g. `VGroup(Line(...), Line(...))`) or `MathTex(r"\\checkmark")`.
        
        ## Prioritize

        1. Off-screen objects
        2. Hidden objects
        3. Text overflow and container bleeding
        4. Major overlaps
        5. Incorrect persistence or visibility
        6. Minor spacing issues

        ## Suggestion Style

        Suggestions must be:

        * Short
        * Actionable
        * Spatially specific

        Good:

        * Move text2 with width of 3.1 and height of 2.2 downward from its current position to clear node_5 and node_15.
        * Raise label_internal with width of 0.8 and height of 1.4 above the connector region by increasing its z_index
        * Increase spacing between parent and child levels

        Bad:

        * Fix overlap.
        * Improve layout.

        ## Output Format

        Only include presentation steps that require fixes.

        Presentation Step X

        Issue: <brief and specific summary>

        Suggestions:

        * ...
        * ...
        * ...

        Do not provide implementation details.
        Do not provide reasoning.
        Only provide repair recommendations.

        """

        user_prompt = """
        Here is the original code which resulted in the error:
        ------------------------
        Code:
        {code_script}
        ------------------------
        ------------------------
        Here are the storyboarding instructions along with the run_time that had to be followed for generating the code:
        ------------------------
        Storyboard:
        {storyboarding_context}
        ------------------------
        ------------------------
        Here is an insights report on the discrepancies seen in the video to be used in feedback generation:
        ------------------------
        Insights:
        {insights_context}

        """

        suggestions_file_path = os.path.join(specific_suggestions_folder, "scene_1_suggestions.txt")

        for group, group_data in animation_instructions.items():
            if str(group).lower() in ["lesson_title", "total_scenes", "total_composed_components", "canvas_specification", "audio_metadata"]:
                continue
            skip_scenes_env = os.environ.get("SKIP_SCENES")
            if skip_scenes_env and str(group) in [s.strip() for s in skip_scenes_env.split(",")]:
                print(f"Skipping Scene {group} per SKIP_SCENES")
                continue

            target_scene_env = os.environ.get("TARGET_SCENE")
            if target_scene_env and str(group) != str(target_scene_env):
                continue

            # Remove narration_statement from each group_data dictionary item
            if isinstance(group_data, list):
                for item in group_data:
                    if isinstance(item, dict):
                        item.pop("narration_statement", None)
            elif isinstance(group_data, dict):
                group_data.pop("narration_statement", None)

            scene_file_name = f"group_{group}.py"
            scene_file_path = os.path.join(code_folder,scene_file_name)

            if not os.path.exists(scene_file_path):
                continue

            with open(scene_file_path,'r',encoding='utf-8') as f:
                code_script = f.read()

            suggestions_file_path = os.path.join(specific_suggestions_folder,f"scene_{group}_suggestions.txt")
            if os.path.exists(suggestions_file_path):
                print(f"Suggestions for group {group} already exists. So skipping it.")
                continue

            insights_report = os.path.join(insights_report_dir,f"scene_{group}_full_report.json")
            if not os.path.exists(insights_report):
                print(f"No error report found at {insights_report}. Generating default clean suggestions.")
                with open(suggestions_file_path, "w", encoding='utf-8') as f:
                    f.write("No layout discrepancies or collisions detected from instrumentation. Maintain current code layout.")
                continue
            
            with open(insights_report,'r',encoding='utf-8') as f:
                insights_context = json.load(f)

            asset_names_list = []
            asset_guidelines = []
            image_details = "\n\n------------Image Paths------------\n"

            scene_context = ""
            scene_correction_insights = "#####################################################\n"
            for i,pair in enumerate(group_data):
                scene_context += "#####################################################\n"
                scene_context += f"Presentation Step {i+1}:\n\n"
                sec_desc = pair.get("matching_section") if isinstance(pair, dict) else str(pair)
                if not sec_desc and isinstance(pair, dict):
                    sec_desc = pair.get("components") or pair.get("step_name") or str(pair)
                scene_context += f"{sec_desc}\n\n"
                
                step_rt = 5
                if group in structured_cgi and i < len(structured_cgi[group]) and isinstance(structured_cgi[group][i], dict):
                    step_rt = structured_cgi[group][i].get("run_time", 5)
                scene_context += f"Presentation Step run time:{step_rt}\n\n"

                ac_step = {}
                if group in asset_classification:
                    if isinstance(asset_classification[group], list) and i < len(asset_classification[group]):
                        ac_step = asset_classification[group][i] if isinstance(asset_classification[group][i], dict) else {}
                    elif isinstance(asset_classification[group], dict):
                        ac_step = asset_classification[group]

                if "Asset_names" in ac_step and ac_step["Asset_names"]:
                    for aname in ac_step["Asset_names"]:
                        if aname and aname not in asset_names_list:
                            asset_names_list.append(aname)
                    raw_assets = animation_instructions.get(group, [{}])[i].get("assets") if (isinstance(animation_instructions.get(group), list) and i < len(animation_instructions[group]) and isinstance(animation_instructions[group][i], dict)) else None
                    if isinstance(raw_assets, list):
                        asset_guidelines.extend(raw_assets)
                    elif isinstance(raw_assets, str):
                        asset_guidelines.append(raw_assets)

                if "image_paths" in ac_step and ac_step["image_paths"]:
                    img_names = ac_step.get("Image_names") or []
                    for img_num, img_name in enumerate(img_names):
                        if img_num < len(ac_step["image_paths"]):
                            image_path = ac_step["image_paths"][img_num]
                            image_details += f"{img_name}:{image_path}\n"

                section_index = f"{i+1}"
                if section_index not in insights_context:
                    continue

                section_issues = "\n".join(insights_context[f"{i+1}"]["issues"])
                
                if insights_context[f"{i+1}"]["part_details"]:
                    parts_summary = []
                    for k, v in insights_context[f"{i+1}"]["part_details"].items():
                        dim_str = f" which is {v['dimensions'][-1]}" if v.get("dimensions") else ""
                        pos_str = f" at position {v['current_position'][-1]}" if v.get("current_position") else ""
                        parts_summary.append(f"Constraint for {k}{dim_str}{pos_str}:\n{v.get('constraints', [])}")
                    part_constraints = "\n\n".join(parts_summary)
                else:
                    part_constraints = ""

                scene_correction_insights += f"Presentation Step {i+1}:\nKey Issues:\n{section_issues}\n\nPart Constraints:\n{part_constraints}\n\n"


            if asset_names_list:
                asset_ref = "------------Asset Construction Guidelines------------\n\n"
                for k,asset_name in enumerate(asset_names_list):
                    asset_ref += "Asset Name: "+asset_name+"\n\n"
                    guideline_text = construction_guidelines_dict.get(asset_name)
                    if not guideline_text and k < len(asset_guidelines) and len(str(asset_guidelines[k])) > 30:
                        guideline_text = asset_guidelines[k]
                    if not guideline_text:
                        guideline_text = "Render as standard visual asset."
                    asset_ref += "Asset Guidelines:\n"+str(guideline_text)+"\n\n"
                
                scene_context += asset_ref
            
            if image_details:
                scene_context += image_details

            formatted_user_prompt = user_prompt.format(
                code_script = code_script,
                storyboarding_context = scene_context,
                insights_context = scene_correction_insights
            )

            print(f"System prompt:\n{system_prompt}\n\nUser_prompt:\n{formatted_user_prompt}")
            
            #choice = input("Proceed? (y/n)")
            #if choice=="n":
            #    exit(1)
            
            formatted_system_prompt = system_prompt

            if correction_vendor=="google":
                print(f"Using google's model of gemini-3.5-flash")
                full_prompt = f"{formatted_system_prompt}\n\nUser Query: {formatted_user_prompt}"
                model_variant = f"models/{correction_model_name}" 
                model = genai.GenerativeModel(model_variant)

                response = model.generate_content(
                    contents=[{"role": "user", "parts": [full_prompt]}],
                    generation_config=genai.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=35000
                    )
                )

                generated_result = response.text

                with open(suggestions_file_path,"w",encoding='utf-8') as f:
                    f.write(generated_result)
        
        return specific_suggestions_folder

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
                
                with open(config_path, 'r',encoding='utf-8') as f:
                    config_data = json.load(f)

                # 3. Call fit_scene
                output_file_path = self.correction_suggestions(config_data, topic_id)
                
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

    generate_feedback_report = os.path.join(trackers_dir, "12_generate_feedback_tracker.json")
    if not os.path.exists(generate_feedback_report):
        generate_feedback_report = os.path.join(trackers_dir, "generate_feedback_tracker.json")
    correction_suggestions_tracker = os.path.join(trackers_dir, "13_suggest_corrections_tracker.json")
    if not os.path.exists(correction_suggestions_tracker):
        correction_suggestions_tracker = os.path.join(trackers_dir, "suggest_corrections_tracker.json")

    stage = SuggestCorrections(
        input_tracker_path=generate_feedback_report, 
        google_api_key=os.environ.get("GOOGLE_API_KEY"), 
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        output_tracker_path=correction_suggestions_tracker, 
        input_folder=data_dir
    )
    stage.process_files()