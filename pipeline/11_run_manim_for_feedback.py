#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 11: MANIM FEEDBACK RUN (FIRST-PASS COMPILE & DIAGNOSTICS)
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 11
   - Script Name: 11_run_manim_for_feedback.py
   - Primary Class: RunManimForFeedback
   - Pipeline Role: 
     Executes a test compilation pass of the initial Manim Python scripts (generated
     in Stage 10) inside the dedicated Conda 'manim' environment. Operates under an
     inter-process semaphore (--max-manim) to throttle heavy Cairo/OpenGL rendering.
     Captures raw diagnostic videos, logs compiler crash tracebacks, and dumps
     frame snapshot JSON metadata recording the bounding boxes of all on-screen objects.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 10 (10_generate_code.py):
       - How: Ingests initial Manim scripts from manim_codes/group_{n}.py via
         10_code_generation_tracker.json.
       - Purpose: Compiles the generated Python code to verify syntax and runtime stability.
     * Stage 5 (5_populate_audio_runtime.py):
       - How: Ingests CGI_Input.json.
       - Purpose: Verifies section runtimes and scene counts.
   - Input Tracker: ppt_trackers/10_code_generation_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * manim_codes/group_{n}.py (Stage 10):
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_codes/group_*.py
       Content: Initial Manim Python scene scripts.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Narration manifest with section timing.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/10_code_generation_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 10_code_generation_tracker.json.
   - Step 2: Loops through each scene group (group_1, group_2, ...).
   - Step 3: Invokes `manim -qm --disable_caching` in a subprocess inside the Conda environment.
   - Step 4: If execution succeeds:
     * Saves raw diagnostic video to feedback_videos/ or media cache.
     * The embedded instrumentation automatically emits frame snapshots into correction_insights/.
   - Step 5: If execution fails:
     * Intercepts stderr/stdout and logs the complete crash traceback to error_logs/group_{n}_errors.txt.
   - Step 6: Atomically updates 11_run_manim_feedback_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * feedback_videos/ directory:
       Location: data_ppt_advanced/<TOPIC_NAME>/feedback_videos/
       Content: Rendered first-pass diagnostic animation MP4s.
     * correction_insights/scene_{n}/:
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights/scene_{n}/
       Content: JSON snapshots containing coordinates, names, and bounding boxes
                of active mobjects at transition keyframes.
     * error_logs/group_{n}_errors.txt:
       Location: data_ppt_advanced/<TOPIC_NAME>/error_logs/
       Content: Manim compile error logs and Python stack traces if render crashed.
     * Output Tracker:
       Location: ppt_trackers/11_run_manim_feedback_tracker.json
       Content: Atomic tracker confirming first-pass Manim execution status.

6. DOWNSTREAM CONSUMERS:
   - Stage 12 (12_generate_feedback_report.py): Analyzes bounding box snapshots and errors.
   - Stage 13 (13_generate_corrections.py): Uses crash logs to formulate code repairs.
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
import glob
try:
    import portalocker
except ImportError:
    portalocker = None
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
try:
    from pipeline.helpers.code_sanitizer import sanitize_file
except ImportError:
    try:
        from code_sanitizer import sanitize_file
    except ImportError:
        def sanitize_file(path):
            return False

try:
    import importlib.util
    _sme_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "23_sme_post_production.py")
    if not os.path.exists(_sme_file):
        _sme_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sme_integration.py")
    _spec = importlib.util.spec_from_file_location("sme_post_prod", _sme_file)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    assemble_sme_lesson_from_blueprint = getattr(_mod, "assemble_sme_lesson_from_blueprint")
except Exception as e:
    def assemble_sme_lesson_from_blueprint(*args, **kwargs):
        raise RuntimeError(f"SME post-production module failed to load: {e}")

class RunManimForFeedback:
    """
    Stage 11: Manim Feedback Run.
    Test-compiles initial Manim scripts under semaphore to produce diagnostic videos,
    capture crash tracebacks, and dump bounding box snapshot data.
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
                if portalocker:
                    portalocker.lock(f, portalocker.LOCK_SH)
                try:
                    content = f.read()
                    if not content:
                        return {}
                    data = json.loads(content)
                except json.JSONDecodeError:
                    data = {}
                finally:
                    if portalocker:
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
            lock_ctx = portalocker.Lock(lock_path, timeout=60) if portalocker else FileLock(lock_path, timeout=60)
            with lock_ctx:
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

        Fix the reported error above.

        Then inspect the ENTIRE file and proactively fix any additional bugs that would likely fail during rendering. Only fix actual bugs—do not redesign the animation or change timings, layout, colors, sequencing, or instructional intent.

        In addition to ordinary syntax/typing mistakes, enforce these Manim-specific rules:

        Every ImageMobject must be wrapped inside a Group before being added to larger hierarchies. Any hierarchy containing an ImageMobject must itself use Group (not VGroup). VGroup is acceptable elsewhere.
        Table has get_horizontal_lines() and get_vertical_lines(); never use get_lines().
        Rectangle does not support corner_radius. Replace with RoundedRectangle whenever corner_radius is used.
        MoveAlongPath must always use rate_func=ease_out_cubic. Replace any other rate function.
        Never use Transform or ReplacementTransform on a Group or ImageMobject (or hierarchies containing ImageMobjects). Replace with an equivalent combination of self.add()/self.remove(), FadeIn/FadeOut, or other safe operations while preserving the visual result.
        CrispText does not accept weight=REGULAR. Replace with a supported weight.

        Also fix any other latent issues you find, including mismatched brackets/quotes, malformed numeric literals, identifier typos, indentation problems, invalid escape sequences, incorrect API names, invalid keyword arguments, or similar rendering-time errors.

        Retype every line carefully. Do not introduce new typos or modify correct code.

        Return the COMPLETE corrected Python file and nothing else: no explanations, no markdown fences, just raw Python source beginning with the first import statement.
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
        
        '''
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            sys.exit("ERROR: set DEEPSEEK_API_KEY in your environment.")

        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            max_tokens=max_tokens,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}}
        )

        usage = response.usage
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        '''
        genai.configure(api_key=self.google_api_key)
        clean_model = "gemini-2.5-flash" if "3.5" in str(model) else model
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

        '''
        finish_reason = getattr(choice, "finish_reason", "") or ""
        if finish_reason == "length":
            print(f"    [!] response was TRUNCATED (hit max_tokens={max_tokens}) -- "
                f"this is NOT a complete/usable file.")
        '''
                
        return self.extract_code_from_response(choice), "None"

    def sort_key(self,k):
        match = re.search(r"group_(\d+).py", k)
        if match:
            group_num = int(match.group(1))
            return group_num
        return float('inf')

    def execute_script(self, script_dir, base_folder, conf_file, timeout_seconds: int = 900):
        """
        Placeholder for execution logic. To be populated later.
        """
        with open(conf_file,'r',encoding='utf-8') as f:
            config_data = json.load(f)

        base_folder = config_data.get('base_folder', '')
        topic_id = config_data.get('topic_id') or os.path.basename(base_folder)
        theme = config_data.get('theme', 'dynamic_learning')

        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        cgi_input = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_input):
            cgi_input = f"{base_folder}/CGI_Input.json"
        with open(cgi_input,'r',encoding='utf-8') as f:
            cgi_data = json.load(f)

        manim_adjusted_codes_folder = script_dir
        raw_videos_folder = Path(f"{base_folder}/manim_raw_videos")
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
        
        target_scene_env = os.environ.get("TARGET_SCENE")
        
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

            if final_video_path.exists() and os.environ.get("FORCE_RUN") != "1" and not target_scene_env:
                raw_videos_count += 1
                continue
            
            print(f"Creating animation for {code_file}")

            # Deterministic AST & regex sanitation prior to rendering
            if sanitize_file(absolute_script_path):
                print(f"[Sanitizer] Applied automatic AST/regex fixes to {code_file}")

            if theme=="promo":
                print("Use the promo theme for rendering")
                pixel_width = 540
                pixel_height = 960
            else:
                pixel_width = 640
                pixel_height = 360

            # The scene name is 'FinalScene' as generated by manim_code_generator.py
            scene_name = "FinalScene"

            manim_direct_bin = f"/opt/homebrew/Caskroom/miniforge/base/envs/{conda_env_name}/bin/manim"
            system_manim = shutil.which("manim")
            if os.path.exists(manim_direct_bin):
                command = [
                    manim_direct_bin, "render",
                    "-ql",  # production quality, high
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
                    "-ql",  # production quality, high
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
                    "-ql",  # production quality, high
                    "--progress_bar", "none",
                    "--frame_rate", str(manim_fps),
                    #"--verbosity", "ERROR",
                    "--resolution", f"{pixel_width},{pixel_height}",
                    "--disable_caching",
                    absolute_script_path,
                    scene_name
                ]

            print(f"Running command: {' '.join(command)}")
            stdout, stderr, returncode = "", "", 0
            timed_out = False

            render_env = os.environ.copy()
            render_env["CORRECTION_INSIGHTS_DIR"] = str(Path(base_folder) / "correction_insights")
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

                print(f"    Parsed error: Line {error_line}, Message: {error_message}")

                # Begin AI repair (Single attempt)
                try:
                    source_code = Path(absolute_script_path).read_text(encoding="utf-8")
                except Exception as e:
                    print(f"    Could not read source code: {e}")
                    continue

                raw_tail = combined_output[-4000:]
                prompt = self.build_prompt(source_code, error_line, error_message, "full", raw_tail)
                
                print(f"    Sending code to gemini for a fix...")
                fixed_code, finish_reason = self.call_corrector(prompt,model="gemini-3.5-flash")

                if finish_reason == "length" and error_line:
                    print("    [!] Full-file response truncated; trying truncated fallback mode...")
                    prompt = self.build_prompt(source_code, error_line, error_message, "truncated", raw_tail)
                    fixed_code, finish_reason = self.call_corrector(prompt, model="gemini-3.5-flash")

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
                        fixed_code, repair_finish_reason = self.call_corrector(repair_prompt,model="gemini-3.5-flash")
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

        # ------------------------------------------------------------------
        # SME VIDEO INTEGRATION (OSL 3.0 MULTI-SCENE COMPOSITING)
        # ------------------------------------------------------------------
        final_composited_video = None
        if raw_videos_count > 0 and os.environ.get("SKIP_SME", "0") != "1":
            print("\n" + "=" * 66)
            print("[SME Integration] Compiling final composited video from blueprint")
            print("=" * 66)
            try:
                # 1. Resolve teacher video path
                teacher_video = None
                teacher_candidates = [
                    os.path.join(base_folder, f"{topic_id}_trimmed.mp4"),
                    config_data.get("trimmed_teacher_video"),
                    config_data.get("teacher_video"),
                    config_data.get("trainer_video"),
                    config_data.get("video_path"),
                    os.path.join(base_folder, "trimmed_teacher.mp4"),
                    os.path.join(base_folder, "teacher_video.mp4"),
                    os.path.join(base_folder, "teacher.mp4"),
                ]
                for c in teacher_candidates:
                    if c and os.path.exists(c):
                        teacher_video = os.path.abspath(c)
                        break

                if not teacher_video:
                    for mp4 in glob.glob(os.path.join(base_folder, "*trimmed*.mp4")):
                        base_n = os.path.basename(mp4).lower()
                        if "final" not in base_n and "assembled" not in base_n and "rendered" not in base_n and "clean_audio" not in base_n:
                            teacher_video = os.path.abspath(mp4)
                            break

                if not teacher_video:
                    # Check common Simplilearn video fallbacks
                    workspace_dir = Path(__file__).resolve().parent.parent
                    for fallback in [
                        str(workspace_dir / "input" / "Types and Architectures of AI Agents SME.mp4"),
                        str(workspace_dir / "Simplilearn Guide" / "2.02_Basic_Prompting_Techniques.mp4"),
                        str(workspace_dir / "Simplilearn Guide" / "2.04_Python_Syntax_and_Code_Structure.mp4"),
                        r"D:\Kplor\Simplilearn\Documents\2.02_Basic_Prompting_Techniques.mp4",
                        r"D:\Kplor\Simplilearn\2.02_Basic_Prompting_Techniques.mp4",
                    ]:
                        if os.path.exists(fallback):
                            teacher_video = os.path.abspath(fallback)
                            break

                # 2. Resolve instructional storyboard blueprint JSON
                blueprint_json = None
                blueprint_candidates = [
                    config_data.get("blueprint_json"),
                    config_data.get("storyboard_blueprint"),
                    config_data.get("instructional_blueprint"),
                    config_data.get("blueprint_file"),
                    config_data.get("blueprint_path"),
                    os.path.join(base_folder, "storyboard_blueprint.json"),
                    os.path.join(base_folder, "instructional_blueprint.json"),
                    os.path.join(base_folder, "blueprint.json"),
                ]
                for c in blueprint_candidates:
                    if c and os.path.exists(c):
                        blueprint_json = os.path.abspath(c)
                        break

                if not blueprint_json:
                    for pattern in ["*storyboard_blueprint*.json", "*instructional_blueprint*.json", "*blueprint*.json"]:
                        matches = glob.glob(os.path.join(base_folder, "metadata_blueprints", pattern)) + glob.glob(os.path.join(base_folder, pattern))
                        if matches:
                            blueprint_json = os.path.abspath(matches[0])
                            break

                if not blueprint_json:
                    for fallback in [
                        os.path.join(base_folder, f"{topic_id}_storyboard_blueprint.json"),
                        os.path.join(base_folder, "metadata_blueprints", f"{topic_id}_storyboard_blueprint.json"),
                        os.path.join(base_folder, "metadata_blueprints", "storyboard_blueprint.json"),
                    ]:
                        if os.path.exists(fallback):
                            blueprint_json = os.path.abspath(fallback)
                            break

                if teacher_video and blueprint_json:
                    print(f"[SME Integration] Ingesting teacher video: {teacher_video}")
                    print(f"[SME Integration] Ingesting instructional blueprint: {blueprint_json}")
                    
                    sme_work_dir = os.path.join(base_folder, "temp_sme_assembly")
                    os.makedirs(sme_work_dir, exist_ok=True)
                    
                    final_videos_dir = os.path.join(base_folder, "final_composited_videos")
                    os.makedirs(final_videos_dir, exist_ok=True)
                    output_final_video = os.path.join(final_videos_dir, "final_sme_composited_lesson.mp4")

                    if os.path.exists(output_final_video) and os.environ.get("FORCE_SME") != "1":
                        print(f"✓ Final Composited Video already exists: {output_final_video}")
                        final_composited_video = output_final_video
                    else:
                        # Load blueprint and link rendered Manim scene videos
                        with open(blueprint_json, "r", encoding="utf-8") as bf:
                            bp_data = json.load(bf)

                        for idx, sc in enumerate(bp_data.get("scenes", [])):
                            s_id = sc.get("scene_id", idx + 1)
                            for cand_name in [f"group_{s_id}.mp4", f"group_{s_id:02d}.mp4", f"scene_{s_id}.mp4"]:
                                m_path = raw_videos_folder / cand_name
                                if m_path.exists():
                                    sc["rendered_slide_png"] = str(m_path)
                                    sc["rendered_video"] = str(m_path)
                                    sc["manim_video"] = str(m_path)
                                    break

                        linked_bp_path = os.path.join(sme_work_dir, "blueprint_linked_with_manim.json")
                        with open(linked_bp_path, "w", encoding="utf-8") as bf:
                            json.dump(bp_data, bf, indent=2, ensure_ascii=False)

                        # Invoke assemble_sme_lesson_from_blueprint
                        result_video = assemble_sme_lesson_from_blueprint(
                            trimmed_teacher_video=teacher_video,
                            blueprint_json=linked_bp_path,
                            output_final_video=output_final_video,
                            work_dir=sme_work_dir
                        )

                        if result_video and os.path.exists(result_video):
                            final_composited_video = result_video
                            print(f"✓ Final Composited Video Generated: {final_composited_video}")
                else:
                    if not teacher_video:
                        print("[SME Integration Notice] Teacher video not located. Skipping SME overlay compositing.")
                    if not blueprint_json:
                        print("[SME Integration Notice] Instructional blueprint not located. Skipping SME overlay compositing.")
            except Exception as e:
                print(f"[SME Integration Error] SME video compositing failed: {e}")

        output_result = final_composited_video if (final_composited_video and os.path.exists(final_composited_video)) else str(raw_videos_folder)
        return output_result, input_scripts_count, raw_videos_count

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

            if topic_id in output_tracker and output_tracker[topic_id].get("processed", False) and os.environ.get("FORCE_RUN") != "1" and not os.environ.get("TARGET_SCENE"):
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
    
    code_gen_tracker = os.path.join(trackers_dir, "10_code_generation_tracker.json")
    if not os.path.exists(code_gen_tracker):
        code_gen_tracker = os.path.join(trackers_dir, "code_generation_tracker.json")
    feedback_manim_tracker = os.path.join(trackers_dir, "11_run_manim_feedback_tracker.json")
    if not os.path.exists(feedback_manim_tracker):
        feedback_manim_tracker = os.path.join(trackers_dir, "run_manim_feedback_tracker.json")
        
    stage = RunManimForFeedback(
        input_tracker_path=code_gen_tracker, 
        google_api_key=os.environ.get("GOOGLE_API_KEY"), 
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        output_tracker_path=feedback_manim_tracker, 
        input_folder=data_dir
    )
    stage.process_files()