#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 15: MANIM VLM FEEDBACK RUN (RENDER KEYFRAME SNAPSHOTS)
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 15
   - Script Name: 15_run_manim_vlm_feedback.py
   - Primary Class: RunManimForVLMFeedback
   - Pipeline Role:
     Executes a full compilation of the corrected Manim scripts from Stage 14 under
     the Manim semaphore (--max-manim). While rendering, the VLM probe hooks embedded
     in the scripts capture high-resolution visual keyframes (PNG screenshots) and
     detailed mobject bounding box JSON metadata at each presentation step. These
     form the primary visual inputs for multimodal inspection in subsequent stages.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 14 (14_implement_corrections.py):
       - How: Ingests corrected and instrumented Manim scripts in manim_extracted_codes/group_{n}.py
         via 14_corrections_implement_tracker.json.
       - Purpose: Executes the corrected code to capture step keyframes and validation videos.
     * Stage 5 (5_populate_audio_runtime.py):
       - How: Ingests CGI_Input.json.
       - Purpose: References timing boundaries to ensure all step transitions are captured.
   - Input Tracker: ppt_trackers/14_corrections_implement_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * manim_extracted_codes/group_{n}.py (Stage 14):
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_extracted_codes/group_*.py
       Content: Instrumented, corrected Manim Python scripts.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Master time-coded storyboard manifest.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/14_corrections_implement_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 14_corrections_implement_tracker.json.
   - Step 2: Executes Manim render in subprocess (`manim -qm --disable_caching`) under semaphore.
   - Step 3: During rendering, the embedded probe captures step snapshots:
     * Generates a PNG keyframe image at settled composition states.
     * Generates a JSON snapshot containing names, coordinates, and bounding boxes of all active mobjects.
   - Step 4: Saves outputs into correction_insights_vlm/scene_{group}/.
   - Step 5: Stores compiled video into manim_extracted_videos/.
   - Step 6: Atomically updates 15_run_manim_vlm_feedback_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * manim_extracted_videos/ directory:
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_extracted_videos/
       Content: Rendered intermediate MP4 animation videos.
     * correction_insights_vlm/scene_{group}/:
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights_vlm/scene_{group}/
       Content: Step transition PNG screenshots and companion bounding box snapshot JSONs.
     * Output Tracker:
       Location: ppt_trackers/15_run_manim_vlm_feedback_tracker.json
       Content: Atomic tracker confirming completion of VLM keyframe capture render.

6. DOWNSTREAM CONSUMERS:
   - Stage 16 (16_generate_vlm_feedback_report.py): Reads snapshots for geometric layout report.
   - Stage 17 (17_generate_visual_triangulation.py): Overlays coordinate grids onto snapshots.
   - Stage 19 (19_vlm_fixing_stage.py): Multimodal Gemini prompt uses keyframe screenshots.
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
import glob
import portalocker
import time
import re
import random
import shutil
import textwrap
from filelock import FileLock
from openai import OpenAI
import sys
try:
    from moviepy import AudioFileClip, concatenate_audioclips, VideoFileClip
except ImportError:
    from moviepy.editor import AudioFileClip, concatenate_audioclips, VideoFileClip
from pathlib import Path
import subprocess
import google.generativeai as genai
from code_sanitizer import sanitize_file

class RunManimForVLMFeedback:
    """
    Stage 15: Manim VLM Feedback Run.
    Compiles Stage 14 corrected Manim scripts under semaphore, rendering intermediate
    videos and capturing step keyframe PNG screenshots and bounding box JSONs.
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
                
            with open(self.output_tracker_path, 'w', encoding='utf-8') as f:
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


    def parse_error(self, output: str, filename: str) -> tuple[int | None, str]:
        """
        Best-effort traceback parsing.

        - error_line: the DEEPEST line number reported against `filename` in the
        traceback (i.e. closest to where things actually broke). We read the
        real source file for the code -- never the (possibly wrapped/
        truncated) code shown inside rich's boxed traceback.
        - error_message: last "SomeError: message" style line found, scanning
        from the bottom of the output upward.
        """
        # Strip rich's box-drawing borders and stray pipes so plain-text
        # regexes aren't thrown off, e.g. "│  98 │   │   teal_sector = ..."
        cleaned_lines = [re.sub(r"[│╭╮╰╯─]", " ", l) for l in output.splitlines()]
        cleaned = "\n".join(cleaned_lines)

        # Format 1: manim's rich-boxed runtime traceback -> "yourfile.py:98 in construct"
        line_matches = re.findall(re.escape(filename) + r":(\d+)", cleaned)
        # Format 2: plain Python traceback (e.g. SyntaxError at import time) ->
        #           'File ".../yourfile.py", line 44'
        line_matches += re.findall(
            r'File\s+"[^"]*' + re.escape(filename) + r'",\s*line\s+(\d+)', cleaned
        )
        error_line = max((int(n) for n in line_matches), default=None)

        error_message = ""
        for line in reversed(cleaned_lines):
            stripped = line.strip()
            if re.match(r"^[A-Za-z_.]*[A-Za-z_]Error\b.*:", stripped) or re.match(
                r"^[A-Za-z_.]*Exception\b.*:", stripped
            ):
                error_message = stripped
                break

        return error_line, error_message

    def build_prompt(self,source_code: str, error_line: int | None, error_message: str,
                  mode: str, raw_traceback_tail: str) -> str:
        lines = source_code.splitlines()

        if mode == "truncated" and error_line:
            snippet = "\n".join(lines[:error_line])
            code_desc = f"Only lines 1-{error_line} are included (up to and including the line that errored)."
        else:
            snippet = source_code
            code_desc = "The FULL file is included below."

        prompt = f"""You are fixing a Manim Community (manim) Python scene file that was \
        originally generated by an LLM and fails to render.

        {code_desc}

        --- CODE ---
        ```python
        {snippet}
        ```

        --- ERROR ---
        Line reported inside this file (best guess): {error_line}
        Exception: {error_message}

        Raw traceback tail for context:
        {raw_traceback_tail}

        Fix the reported error above. In ADDITION, carefully read through the ENTIRE \
        file (not just the reported line) and fix any other syntactical problems you \
        notice along the way -- these LLM-generated files often contain more than one \
        latent bug that simply hasn't been triggered yet, e.g. stray/mismatched \
        brackets or quotes, malformed numeric literals (e.g. "0=05" or "1..0"), typos \
        in identifiers, indentation issues, or invalid escape sequences. Only fix \
        actual syntax/typo problems this way -- do not change correct code, and do not \
        alter animation logic, timings, colors, or visual intent; only fix bugs.
        CRITICAL ARCHITECTURE REQUIREMENT:
        You MUST preserve the exact import at the top:
        from feedback_functions_vlm.instrumented_scene import InstrumentedScene
        and the class declaration:
        class FinalScene(InstrumentedScene, MovingCameraScene):
        Do NOT rename the class to anything other than FinalScene, and do NOT remove InstrumentedScene.

        Return the COMPLETE corrected Python file and nothing else: no explanations, \
        no markdown code fences, just raw Python source starting from the first \
        import statement.
        """

        return prompt

    def extract_code_from_response(self, text: str) -> str:
        """Strip markdown fences and any commentary before or after."""
        text = text.strip()
        fence_match = re.search(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
        if fence_match:
            return fence_match.group(1).strip()
        fence_match = re.match(r"^```(?:python)?\s*\n(.*)\n```$", text, re.DOTALL)
        if fence_match:
            return fence_match.group(1).strip()
        return text

    def build_syntax_repair_prompt(self, code_str: str, error_message: str) -> str:
        """Prompt to repair Python syntax errors directly."""
        return f"""The following Python code failed syntax validation with error:
{error_message}

Fix the syntax error and return the COMPLETE valid Python code.
Do not include any explanations, Markdown formatting, or backticks.
Return only the raw valid Python code.

Code:
{code_str}
"""

    
    def call_corrector(self,prompt: str, model: str,
                   max_tokens: int = 150000) -> tuple[str, str]:
        """Returns (code, finish_reason). finish_reason == 'length' means the
        response was cut off before the model was actually done -- the caller
        MUST treat that as a failed call, not a usable fix."""
        
        genai.configure(api_key=self.google_api_key)
        clean_model = "gemini-3.8-flash" if ("3.5" in str(model) or "2.5" in str(model)) else model
        model_variant = f"models/{clean_model}"
        model = genai.GenerativeModel(model_variant)

        response = model.generate_content(
            contents=[{"role": "user", "parts": [prompt]}],
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=35000
            )
        )
        choice = response.text
                
        return self.extract_code_from_response(choice), "None"

    def sort_key(self,k):
        match = re.search(r"group_(\d+).py", k)
        if match:
            group_num = int(match.group(1))
            return group_num
        return float('inf')

    def execute_script(self, script_dir, base_folder, conf_file, timeout_seconds: int = 1200):
        """
        Placeholder for execution logic. To be populated later.
        """
        with open(conf_file,'r',encoding='utf-8') as f:
            config_data = json.load(f)

        base_folder = config_data['base_folder']
        theme = config_data['theme']

        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        cgi_input = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_input):
            cgi_input = f"{base_folder}/CGI_Input.json"
        cgi_data = {}
        if os.path.exists(cgi_input):
            with open(cgi_input, 'r', encoding='utf-8') as f:
                cgi_data = json.load(f)

        manim_adjusted_codes_folder = script_dir
        raw_videos_folder = Path(f"{base_folder}/manim_extracted_videos")
        os.makedirs(raw_videos_folder,exist_ok=True)

        conda_env_name = os.environ.get(
            "CONDA_MANIM_ENV",
            "render" if os.path.exists("/opt/homebrew/Caskroom/miniforge/base/envs/render") else "manim"
        )
        conda_bin = shutil.which("conda") or "/opt/homebrew/Caskroom/miniforge/base/condabin/conda"

        code_file_names = os.listdir(manim_adjusted_codes_folder)
        sorted_code_file_names = sorted(code_file_names,key=self.sort_key)

        input_scripts_count = len([f for f in code_file_names if re.match(r"^group_\d+\.py$", f)])
        raw_videos_count = 0
        manim_fps = 15
        
        for code_file in sorted_code_file_names:
            
            #Just extract the group number first
            match = re.search(r"group_(\d+).py", code_file)
            if match:
                group_num = int(match.group(1))
            else:
                print("Invalid file found. Continuing now to the next item")
                continue

            absolute_script_path = os.path.abspath(os.path.join(manim_adjusted_codes_folder,code_file))
            final_video_name = f"{code_file.split('.')[0]}.mp4"
            final_video_path = raw_videos_folder/final_video_name
            script_dir = os.path.dirname(absolute_script_path)

            target_scene_env = os.environ.get("TARGET_SCENE")
            if target_scene_env and str(group_num) != str(target_scene_env):
                if final_video_path.exists():
                    raw_videos_count += 1
                else:
                    input_scripts_count -= 1
                continue

            skip_scenes_env = os.environ.get("SKIP_SCENES")
            if skip_scenes_env and str(group_num) in [s.strip() for s in skip_scenes_env.split(",")]:
                print(f"Skipping Scene {group_num} per SKIP_SCENES")
                if final_video_path.exists():
                    raw_videos_count += 1
                else:
                    input_scripts_count -= 1
                continue

            scene_snap_dir = Path(base_folder) / "correction_insights_vlm" / f"scene_{group_num}"
            has_snapshots = scene_snap_dir.is_dir() and len(list(scene_snap_dir.glob("snapshot_*.json"))) > 0

            if final_video_path.exists() and has_snapshots and os.environ.get("FORCE_RUN") != "1" and not target_scene_env:
                raw_videos_count += 1
                continue
            
            print(f"Creating animation for {code_file}")

            # Deterministic AST & regex sanitation prior to rendering
            if sanitize_file(absolute_script_path):
                print(f"[Sanitizer] Applied automatic AST/regex fixes to {code_file}")

            # The scene name is 'FinalScene' as generated by manim_code_generator.py
            scene_name = "FinalScene"
            manim_direct_bin = f"/opt/homebrew/Caskroom/miniforge/base/envs/{conda_env_name}/bin/manim"
            system_manim = shutil.which("manim")
            
            if theme=="promo":
                print("Use the promo theme for rendering")
                pixel_width = 540
                pixel_height = 960
                if os.path.exists(manim_direct_bin):
                    command = [
                        manim_direct_bin, "render",
                        "-qm",  # production quality, medium
                        "--progress_bar", "none",
                        "--frame_rate", str(manim_fps),
                        #"--verbosity", "ERROR",
                        "--resolution", f"{pixel_width},{pixel_height}",
                        "--disable_caching",
                        absolute_script_path,
                        scene_name
                    ]
                elif system_manim:
                    command = [
                        system_manim, "render",
                        "-qm",  # production quality, medium
                        "--progress_bar", "none",
                        "--frame_rate", str(manim_fps),
                        #"--verbosity", "ERROR",
                        "--resolution", f"{pixel_width},{pixel_height}",
                        "--disable_caching",
                        absolute_script_path,
                        scene_name
                    ]
                else:
                    command = [
                        conda_bin, "run", "-n", conda_env_name,
                        "manim", "render",
                        "-qm",  # production quality, medium
                        "--progress_bar", "none",
                        "--frame_rate", str(manim_fps),
                        #"--verbosity", "ERROR",
                        "--resolution", f"{pixel_width},{pixel_height}",
                        "--disable_caching",
                        absolute_script_path,
                        scene_name
                    ]
            else:
                pixel_width = 640
                pixel_height = 360
                if os.path.exists(manim_direct_bin):
                    command = [
                        manim_direct_bin, "render",
                        "-qm",  # production quality, medium
                        "--progress_bar", "none",
                        "--frame_rate", str(manim_fps),
                        #"--verbosity", "ERROR",
                        "--disable_caching",
                        absolute_script_path,
                        scene_name
                    ]
                elif system_manim:
                    command = [
                        system_manim, "render",
                        "-qm",  # production quality, medium
                        "--progress_bar", "none",
                        "--frame_rate", str(manim_fps),
                        #"--verbosity", "ERROR",
                        "--disable_caching",
                        absolute_script_path,
                        scene_name
                    ]
                else:
                    command = [
                        conda_bin, "run", "-n", conda_env_name,
                        "manim", "render",
                        "-qm",  # production quality, medium
                        "--progress_bar", "none",
                        "--frame_rate", str(manim_fps),
                        #"--verbosity", "ERROR",
                        "--disable_caching",
                        absolute_script_path,
                        scene_name
                    ]
            

            print(f"Running command: {' '.join(command)}")
            stdout, stderr, returncode = "", "", 0
            timed_out = False

            render_env = os.environ.copy()
            render_env["CORRECTION_INSIGHTS_VLM_DIR"] = str(Path(base_folder) / "correction_insights_vlm")
            render_env["EX_CONFIG_PATH"] = str(Path(base_folder) / "ex_config.json")
            workflow_dir = os.path.abspath(os.path.dirname(__file__))
            helpers_dir = os.path.join(workflow_dir, "helpers")
            parent_dir = os.path.dirname(workflow_dir)
            render_env["PYTHONPATH"] = f"{helpers_dir}:{workflow_dir}:{parent_dir}:{render_env.get('PYTHONPATH', '')}"

            try:
                # Use capture_output=True to retrieve stdout/stderr programmatically
                result = subprocess.run(
                    command,
                    cwd=script_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    shell=False,
                    env=render_env
                )
                stdout = result.stdout or ""
                stderr = result.stderr or ""
                returncode = result.returncode
            except subprocess.TimeoutExpired as e:
                timed_out = True
                returncode = -1
                # Grab whatever was printed to output streams before the process timed out
                stdout = e.stdout or ""
                stderr = e.stderr or ""
                print(f"    [!] Render timed out after {timeout_seconds} seconds.")

            # Print Captured Outputs
            if stdout.strip():
                print("--- Manim Standard Output ---")
                print(stdout)
                print("-----------------------------")
            if stderr.strip():
                print("--- Manim Standard Error ---")
                print(stderr)
                print("----------------------------")

            # Check if execution failed or timed out
            if returncode != 0 or timed_out:
                print(f"--- Manim Rendering Failed or Timed Out for {code_file} ---")
                combined_output = stdout + "\n" + stderr
                error_line, error_message = self.parse_error(combined_output, code_file)

                if timed_out and not error_message:
                    error_message = f"Process timed out after {timeout_seconds} seconds. Possible infinite loop or rendering hang."

                print(f"Parsed error: Line {error_line}, Message: {error_message}")

                # Begin AI repair (Single attempt)
                try:
                    source_code = Path(absolute_script_path).read_text(encoding="utf-8")
                except Exception as e:
                    print(f"    Could not read source code: {e}")
                    continue

                raw_tail = combined_output[-4000:]
                prompt = self.build_prompt(source_code, error_line, error_message, "full", raw_tail)
                
                print(f"    Sending code to gemini for a fix...")
                fixed_code, finish_reason = self.call_corrector(prompt, model="gemini-3.8-flash")

                if finish_reason == "length" and error_line:
                    print("    [!] Full-file response truncated; trying truncated fallback mode...")
                    prompt = self.build_prompt(source_code, error_line, error_message, "truncated", raw_tail)
                    fixed_code, finish_reason = self.call_corrector(prompt, model="gemini-3.8-flash")

                if finish_reason == "length":
                    print("    [!] AI response still truncated. Skipping fix attempt.")
                    continue

                if not fixed_code.strip():
                    print("    [!] Received empty response from AI. Skipping.")
                    continue

                # Local validation to check if the returned code compiles
                valid_syntax = False
                for syntax_attempt in range(1, 3):
                    try:
                        compile(fixed_code, absolute_script_path, "exec")
                        valid_syntax = True
                        break
                    except SyntaxError as e:
                        print(f"    [syntax-check] attempt {syntax_attempt}/2 failed: {e}")
                        if syntax_attempt == 2:
                            break
                        repair_prompt = self.build_syntax_repair_prompt(fixed_code, str(e))
                        fixed_code, repair_finish_reason = self.call_corrector(repair_prompt, model="gemini-3.8-flash")
                        if repair_finish_reason == "length":
                            break

                if not valid_syntax:
                    print("    [!] Code validation failed. Keeping original file on disk.")
                    continue

                # Write fixed code back to path
                try:
                    Path(absolute_script_path).write_text(fixed_code, encoding="utf-8")
                    sanitize_file(absolute_script_path)
                    print(f"    Successfully wrote corrected code back to {code_file}")
                except Exception as e:
                    print(f"    Failed writing to file: {e}")
                    continue

                # Retry rendering the script
                print(f"Retrying execution for corrected script: {code_file}...")
                try:
                    result = subprocess.run(
                        command,
                        cwd=script_dir,
                        capture_output=True,
                        text=True,
                        timeout=timeout_seconds,
                        shell=False,
                        env=render_env
                    )
                    stdout = result.stdout or ""
                    stderr = result.stderr or ""
                    returncode = result.returncode
                except subprocess.TimeoutExpired as e:
                    returncode = -1
                    stdout = e.stdout or ""
                    stderr = e.stderr or ""
                    print(f"    [!] Retried process timed out again.")

                if returncode != 0:
                    print(f"--- Retry failed for {code_file}. Skipping to next file. ---")
                    continue

            media_dir = Path(script_dir) / "media"
            scene_videos = [f for f in media_dir.glob(f"**/{scene_name}.mp4") if "partial_movie_files" not in f.parts]
            if scene_videos:
                rendered_video_path = sorted(scene_videos, key=lambda f: f.stat().st_mtime, reverse=True)[0]
            else:
                non_partial = [f for f in media_dir.glob("**/*.mp4") if "partial_movie_files" not in f.parts]
                if non_partial:
                    rendered_video_path = sorted(non_partial, key=lambda f: f.stat().st_mtime, reverse=True)[0]
                else:
                    all_videos = sorted(media_dir.glob("**/*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
                    if not all_videos:
                        print(f"Error: Manim rendering finished, but output video file was not found.")
                        continue
                    rendered_video_path = all_videos[0]
            print(f"Moving rendered video from '{rendered_video_path}' to '{final_video_path}'")
            try:
                shutil.move(str(rendered_video_path), str(final_video_path))
                shutil.rmtree(media_dir)
            except Exception as e:
                print(f"Failed managing output files: {e}")
                continue

            if final_video_path.exists():
                raw_videos_count += 1

            print(f"--- Manim scene {scene_name} rendered and file moved successfully! ---")

        return str(raw_videos_folder), input_scripts_count, raw_videos_count

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
            
            output_path = input_entry.get("output_path", "")
            try:
                script_dir = input_entry.get("output_path")

                output_path, input_scripts_count, raw_videos_count = self.execute_script(
                    script_dir=script_dir,
                    base_folder=base_folder,
                    conf_file=config_path
                )

                # 4. Update tracker (Success)
                # Re-load tracker to minimize race conditions
                tracker = self._load_tracker(self.output_tracker_path)
                
                if raw_videos_count < input_scripts_count:
                    tracker[topic_id] = {
                        "output_path": output_path,
                        "topic_name": topic_id,
                        "topic_id": topic_id,
                        "processed": False,
                        "failure_reason": f"{input_scripts_count-raw_videos_count} code scripts failed during raw video creation",
                        "input_scripts_count": input_scripts_count,
                        "raw_videos_count": raw_videos_count
                    }
                else:
                    tracker[topic_id] = {
                        "output_path": output_path,
                        "topic_name": topic_id,
                        "topic_id": topic_id,
                        "processed": True,
                        "failure_reason": None,
                        "input_scripts_count": input_scripts_count,
                        "raw_videos_count": raw_videos_count
                    }
                
                self._save_tracker(self.output_tracker_path,tracker)
                print(f"Successfully processed {topic_id}.")

            except Exception as e:
                print(f"Error processing {topic_id}: {e}")
                # 5. Update tracker (Failure)
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": output_path,
                    "topic_name": topic_id,
                    "topic_id": topic_id,
                    "processed": False,
                    "failure_reason": str(e),
                    "input_scripts_count": 0,
                    "raw_videos_count": 0
                }
                self._save_tracker(self.output_tracker_path,tracker)

if __name__=="__main__":
    workflow_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(workflow_dir)
    trackers_dir = os.path.join(parent_dir, "ppt_trackers") if os.path.exists(os.path.join(parent_dir, "ppt_trackers")) else os.path.join(parent_dir, "trackers")
    data_dir = os.path.join(parent_dir, "output") if os.path.exists(os.path.join(parent_dir, "output")) else (os.path.join(parent_dir, "data_ppt_advanced") if os.path.exists(os.path.join(parent_dir, "data_ppt_advanced")) else os.path.abspath("."))

    correction_implement_tracker = os.path.join(trackers_dir, "14_corrections_implement_tracker.json")
    if not os.path.exists(correction_implement_tracker):
        correction_implement_tracker = os.path.join(trackers_dir, "corrections_implement_tracker.json")
    feedback_vlm_manim_tracker = os.path.join(trackers_dir, "15_run_manim_vlm_feedback_tracker.json")
    if not os.path.exists(feedback_vlm_manim_tracker):
        feedback_vlm_manim_tracker = os.path.join(trackers_dir, "run_manim_vlm_feedback_tracker.json")

    stage = RunManimForVLMFeedback(
        input_tracker_path=correction_implement_tracker, 
        google_api_key=os.environ.get("GOOGLE_API_KEY"), 
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        output_tracker_path=feedback_vlm_manim_tracker, 
        input_folder=data_dir
    )
    stage.process_files()