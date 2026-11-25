#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 22: FINAL RENDER, AUDIO MUXING & QA AUDIT
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 22
   - Script Name: 22_final_code_run.py
   - Primary Class: FinalCodeExecution
   - Pipeline Role:
     The culmination and final production deliverable stage of the 23-stage pipeline.
     Compiles the audio-synchronized Manim scripts from Stage 21 under semaphore to
     generate pristine animation-only MP4 videos. Normalizes TTS narration audio
     loudness (EBU R128) and muxes video with audio via FFmpeg into production MP4s.
     Automatically extracts high-resolution statement transition verification keyframes
     into verification_screenshots/ alongside manifest.json.
     Performs an automated multimodal VLM QA audit (vlm_qa_report.json) using Gemini 3.5 Flash,
     auditing Header Clearance, Border Clamping, In-Box Collision, and Legibility.
     CLOSED-LOOP VISUAL SELF-HEALING: If visual layout defects are detected, automatically
     repairs the code via Gemini 3.5 Flash (repair_visual_defects) while strictly preserving
     all self.wait(...) audio synchronization timings, re-renders the scene, re-merges
     audio, updates verification screenshots, and re-audits.
     Automatically mirrors all final deliverables to data_ppt_final_outputs/<TOPIC_NAME>/.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 21 (21_timing_adjustments.py):
       - How: Ingests time-synchronized Manim scripts from manim_time_synced_code/group_{group}.py
         via 21_timing_adjustment_tracker.json.
       - Purpose: Executes final synchronized rendering.
     * Stage 5 (5_populate_audio_runtime.py):
       - How: Ingests synthesized narration WAV files from audio_elements/ and CGI_Input.json.
       - Purpose: Audio tracks to normalize and mux with rendered video.
   - Input Tracker: ppt_trackers/21_timing_adjustment_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * manim_time_synced_code/group_{group}.py (Stage 21):
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_time_synced_code/group_*.py
       Content: Final, time-synchronized Manim Python scripts.
     * audio_elements/ (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/audio_elements/*.wav
       Content: Statement and scene-level narration audio files.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Master time-coded storyboard manifest with exact statement start/end times.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/21_timing_adjustment_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 21_timing_adjustment_tracker.json.
   - Step 2: Executes final Manim render (`manim -qm --disable_caching`) under the Manim
     semaphore in the dedicated Conda 'manim' environment.
     * Video-only MP4 is saved to manim_time_synced_videos/group_{n}.mp4.
     * If compile fails, attempts automated self-healing via repair_code_with_llm().
   - Step 3: Audio Normalization & Muxing:
     * Ingests scene audio from audio_elements/scene_{n}_combined.wav.
     * Normalizes loudness using FFmpeg loudnorm filter (EBU R128).
     * Muxes video stream and normalized audio into audio_integrated_videos/group_{n}_final.mp4.
   - Step 4: Automated Verification Keyframe Extraction:
     * Extracts PNG keyframe screenshots at every narration statement transition into
       verification_screenshots/group_{n}/ alongside manifest.json.
   - Step 5: Automated Multimodal VLM QA Audit & Closed-Loop Visual Repair:
     * Audits extracted keyframes using Gemini 3.5 Flash against universal layout rules
       (Header Clearance, Border Clamping, In-Box Text Collisions, and Legibility).
     * Writes comprehensive audit verdicts to verification_screenshots/group_{n}/vlm_qa_report.json.
     * CLOSED-LOOP SELF-HEALING: If visual defects are detected, automatically triggers
       repair_visual_defects() using Gemini 3.5 Flash to fix layout issues while strictly
       preserving all self.wait(...) audio sync timings, re-renders the scene, re-merges
       audio, and updates the verification report.
   - Step 6: Automated Production Export:
     * Automatically mirrors final videos and verification screenshots into
       data_ppt_final_outputs/<TOPIC_NAME>/.
   - Step 7: Atomically updates 22_final_render_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * manim_time_synced_videos/group_{n}.mp4:
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_time_synced_videos/
       Content: Raw animation-only MP4 video files.
     * audio_integrated_videos/group_{n}_final.mp4:
       Location: data_ppt_advanced/<TOPIC_NAME>/audio_integrated_videos/
       Content: Final delivered presentation MP4 videos with synchronized audio.
     * verification_screenshots/group_{n}/:
       Location: data_ppt_advanced/<TOPIC_NAME>/verification_screenshots/group_*/
       Content: Statement transition PNG keyframes, manifest.json, and vlm_qa_report.json.
     * data_ppt_final_outputs/<TOPIC_NAME>/:
       Location: data_ppt_final_outputs/<TOPIC_NAME>/
       Content: Export package containing production MP4s and verification screenshots.
     * Output Tracker:
       Location: ppt_trackers/22_final_render_tracker.json
       Content: Atomic tracker confirming completion of final render and deliverable packaging.

6. DOWNSTREAM CONSUMERS:
   - End-User / Production Deliverables:
     The pipeline is complete. Output videos in audio_integrated_videos/ and
     data_ppt_final_outputs/ are ready for educational broadcast or LMS deployment.
================================================================================
"""

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

try:
    from moviepy import AudioFileClip, concatenate_audioclips, VideoFileClip
except ImportError:
    from moviepy.editor import AudioFileClip, concatenate_audioclips, VideoFileClip
from pathlib import Path
import subprocess
import sys

try:
    from PIL import Image
    from google import genai
    from google.genai import types
except ImportError:
    Image = None
    genai = None
    types = None

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_HELPERS_DIR = os.path.join(_CURRENT_DIR, "helpers")
_ROOT_DIR = os.path.dirname(_CURRENT_DIR)
for _p in [_HELPERS_DIR, _CURRENT_DIR, _ROOT_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_CURRENT_DIR, ".env"))
    load_dotenv(os.path.join(os.path.dirname(_CURRENT_DIR), ".env"))
    load_dotenv()
except ImportError:
    pass

from code_sanitizer import sanitize_file, sanitize_manim_code, repair_code_with_llm, extract_code_from_response, apply_programmatic_timing_sync


class FinalCodeExecution:
    """
    Stage 22: Final Render, Audio Muxing & QA Audit.
    Compiles final Manim scenes, muxes normalized audio, extracts statement transition
    screenshots, performs automated Gemini QA audits, and exports final deliverables.
    """

    def __init__(
        self,
        input_tracker_path,
        output_tracker_path,
        google_api_key=None,
        claude_api_key=None,
        input_folder=None,
        no_repair=False
    ):
        # Store required class variables (placeholders allowed)
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        self.claude_api_key = claude_api_key or os.environ.get("CLAUDE_API_KEY")
        self.input_folder = input_folder
        self.no_repair = no_repair or (os.environ.get("NO_REPAIR", "0") in ("1", "true", "True"))
        self.max_repair_attempts = int(os.environ.get("MAX_VLM_REPAIR_ATTEMPTS", "4"))
        self.unresolved_defects = {}
        # Initialize output tracker file if it doesn't exist
        if not os.path.exists(self.output_tracker_path):
            # Ensure the directory exists
            tracker_dir = os.path.dirname(self.output_tracker_path)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
                
            with open(self.output_tracker_path, 'w', encoding="utf-8") as f:
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


    def sort_key(self,k):
        match = re.search(r"group_(\d+).py", k)
        if match:
            group_num = int(match.group(1))
            return group_num
        return float('inf')
    
    def audio_sort_key(self,file_path):
        match = re.search(r"group_(\d+)_pair_(\d+)_statement(\d+)\.wav", file_path.name)
        if match:
            group = int(match.group(1))
            pair = int(match.group(2))
            statement = int(match.group(3))
            return (group, pair, statement)
        return (float('inf'), float('inf'), float('inf'))
    
    def increase_audio_volume(self, input_path, output_path=None, volume_factor=2.0):
        """
        Increases the volume of an audio file using a direct ffmpeg call for robustness.
        """
        try:
            input_p = Path(input_path).resolve()
            if output_path is None:
                output_p = input_p.with_name(f"tmp_amp_{input_p.name}")
                overwrite = True
            else:
                output_p = Path(output_path).resolve()
                overwrite = False

            if not input_p.exists():
                print(f"❌ Error: Input file not found at {input_p}")
                return

            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_p),
                "-filter:a", f"volume={volume_factor}",
                str(output_p)
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True, shell=False)

            if overwrite:
                output_p.replace(input_p)
                print(f"✅ Volume increased for {input_p.name}")
            else:
                print(f"✅ Successfully saved volume-adjusted audio to {output_p.name}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error increasing audio volume for {input_p.name}: FFmpeg failed.")
        except Exception as e:
            print(f"❌ An unexpected error occurred while increasing audio volume for {input_path}: {e}")
    
    def combine_video_with_audio(self, group_num, audio_files, script_dir, final_video_path, base_folder, allow_repair=True):
        final_output_folder = Path(f"{base_folder}/audio_integrated_videos")
        final_output_folder.mkdir(exist_ok=True)
        final_output_path = final_output_folder / f"group_{group_num}_final.mp4"

        # Fast reuse: if audio-integrated video already exists, is intact and up to date, skip expensive re-mux ONLY if VLM QA passed (or repair is disabled)
        is_forced = (os.environ.get("FORCE_RUN", "0") == "1")
        vlm_report = Path(base_folder) / "verification_screenshots" / f"group_{group_num}" / "vlm_qa_report.json"
        vlm_clean = True
        if vlm_report.exists():
            try:
                with open(vlm_report, "r", encoding="utf-8") as rf:
                    r_data = json.load(rf)
                    r_entries = r_data if isinstance(r_data, list) else [r_data] if isinstance(r_data, dict) else []
                    if any(isinstance(e, dict) and (e.get("overall_status") == "DEFECT_DETECTED" or e.get("defects_detected")) for e in r_entries):
                        vlm_clean = False
            except Exception:
                pass

        if not is_forced and final_output_path.exists() and final_output_path.stat().st_size > 1000 and final_output_path.stat().st_mtime >= Path(final_video_path).stat().st_mtime and vlm_report.exists() and (vlm_clean or not allow_repair or self.no_repair):
            print(f"[REUSE] Using existing final audio-integrated video for group {group_num}: {final_output_path}")
            return final_output_path

        print(f"--- Combining video and audio for group {group_num} ---")

        concat_scene_audio_output = Path(script_dir) / f"group_{group_num}_audio.wav"

        # Check video duration
        ffprobe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(final_video_path)
        ]
        video_dur_res = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
        try:
            video_duration = float(video_dur_res.stdout.strip())
        except Exception:
            video_duration = 0.0

        meta_dir = Path(base_folder) / "metadata_blueprints"
        manifest_file = meta_dir / "narration_manifest.json"
        if not manifest_file.exists():
            manifest_file = Path(base_folder) / "narration_manifest.json"
        manifest_used = False

        if manifest_file.exists():
            try:
                from pydub import AudioSegment
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)

                group_data = manifest.get("groups", {}).get(str(group_num))
                if group_data:
                    manifest_dur = group_data.get("duration", 0.0)
                    target_dur = max(video_duration, manifest_dur)
                    timeline = AudioSegment.silent(duration=int((target_dur + 0.5) * 1000))
                    audio_dir = Path(base_folder) / "audio_elements"
                    has_audio_clips = False
                    all_stmts = []
                    for pid, pinfo in group_data.get("pairs", {}).items():
                        all_stmts.extend(pinfo.get("statements", []))

                    # Guard against echo/overlap: check if statements point to a single combined scene audio file
                    unique_files = list(dict.fromkeys([st.get("file") for st in all_stmts if st.get("file")]))
                    if len(unique_files) == 1:
                        st_fname = unique_files[0]
                        st_file = audio_dir / st_fname
                        if st_file.is_file():
                            clip = AudioSegment.from_file(st_file)
                            timeline = timeline.overlay(clip, position=0)
                            has_audio_clips = True
                    else:
                        for st in all_stmts:
                            st_fname = st.get("file")
                            if st_fname:
                                st_file = audio_dir / st_fname
                                if st_file.is_file():
                                    clip = AudioSegment.from_file(st_file)
                                    pos_ms = int(st["start"] * 1000)
                                    timeline = timeline.overlay(clip, position=pos_ms)
                                    has_audio_clips = True

                    if has_audio_clips:
                        # Keep full spoken audio: only trim trailing silence if video is longer than manifest
                        if video_duration >= manifest_dur and video_duration > 0:
                            timeline = timeline[:int(video_duration * 1000)]
                        elif manifest_dur > 0:
                            timeline = timeline[:int(manifest_dur * 1000)]

                        timeline.export(str(concat_scene_audio_output), format="wav")
                        self.increase_audio_volume(concat_scene_audio_output, volume_factor=2.0)
                        print(f"Manifest-timed scene audio saved to: {concat_scene_audio_output}")
                        manifest_used = True
            except Exception as e:
                print(f"Failed to build manifest-timed audio: {e}")

        if not manifest_used:
            group_audio_files = [
                f for f in audio_files 
                if re.match(rf"^group_{group_num}_pair_\d+_statement\d+\.wav$", f.name)
            ]
            sorted_group_audio = sorted(group_audio_files, key=self.audio_sort_key)

            if not sorted_group_audio:
                print(f"[WARNING] No audio files found for group {group_num}.")
                return

            audio_clips = []
            for audio_file in sorted_group_audio:
                audio_clips.append(AudioFileClip(str(audio_file)))

            if audio_clips:
                scene_audio = concatenate_audioclips(audio_clips)
                scene_audio.write_audiofile(str(concat_scene_audio_output), fps=44100)
                for clip in audio_clips:
                    clip.close()
                scene_audio.close()
                self.increase_audio_volume(concat_scene_audio_output, volume_factor=2.0)
                print(f"Concatenated scene audio saved to: {concat_scene_audio_output}")

        # Merge with video
        final_output_folder = Path(f"{base_folder}/audio_integrated_videos")
        final_output_folder.mkdir(exist_ok=True)

        final_output_path = final_output_folder / f"group_{group_num}_final.mp4"

        # Check actual audio duration
        ffprobe_audio_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(concat_scene_audio_output)
        ]
        audio_dur_res = subprocess.run(ffprobe_audio_cmd, capture_output=True, text=True)
        try:
            audio_duration = float(audio_dur_res.stdout.strip())
        except Exception:
            audio_duration = 0.0

        # Audio fade filter to ensure smooth transitions without abrupt pops/cuts
        fade_out_st = max(0.0, audio_duration - 0.02)
        smooth_audio_filter = f"aresample=48000:first_pts=0,afade=t=in:ss=0:d=0.015,afade=t=out:st={fade_out_st:.3f}:d=0.02"

        if video_duration > 0 and audio_duration > video_duration and (audio_duration - video_duration) > 0.05:
            pad_dur = audio_duration - video_duration
            print(f"[PAD] Video ({video_duration:.2f}s) is shorter than audio ({audio_duration:.2f}s). Freezing last frame by {pad_dur:.2f}s to avoid cutting audio.")
            merge_cmd = [
                "ffmpeg", "-y",
                "-i", str(final_video_path),
                "-i", str(concat_scene_audio_output),
                "-filter_complex", f"[0:v]tpad=stop_mode=clone:stop_duration={pad_dur:.3f}[v]",
                "-map", "[v]",
                "-map", "1:a",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-af", smooth_audio_filter,
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "48000",
                str(final_output_path)
            ]
        elif video_duration > 0 and audio_duration > 0 and (video_duration - audio_duration) > 0.05:
            print(f"[TRIM-VIDEO] Video ({video_duration:.2f}s) is longer than audio ({audio_duration:.2f}s). Trimming video to match exact audio length ({audio_duration:.2f}s).")
            merge_cmd = [
                "ffmpeg", "-y",
                "-i", str(final_video_path),
                "-i", str(concat_scene_audio_output),
                "-t", f"{audio_duration:.3f}",
                "-c:v", "copy",
                "-af", smooth_audio_filter,
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "48000",
                str(final_output_path)
            ]
        else:
            merge_cmd = [
                "ffmpeg", "-y",
                "-i", str(final_video_path),
                "-i", str(concat_scene_audio_output),
                "-c:v", "copy",
                "-af", smooth_audio_filter,
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "48000",
                str(final_output_path)
            ]

        merge_result = subprocess.run(merge_cmd, capture_output=True, text=True, shell=False)

        if merge_result.returncode == 0:
            print(f"[SUCCESS] Created final video with audio: {final_output_path}")
            if allow_repair:
                self.extract_verification_screenshots(group_num, final_output_path, base_folder)
                self.audit_verification_screenshots(
                    group_num=group_num,
                    base_folder=base_folder,
                    script_dir=script_dir,
                    final_video_path=final_video_path,
                    final_output_path=final_output_path,
                    audio_files=audio_files,
                    can_repair=allow_repair
                )
        else:
            print(f"[ERROR] FFmpeg video/audio merge failed:\n{merge_result.stderr}")

        concat_scene_audio_output.unlink(missing_ok=True)
        return final_output_path

    def extract_verification_screenshots(self, group_num, video_path, base_folder):
        """
        Automatically extracts verification keyframes at statement/step transitions
        and regular intervals into verification_screenshots/group_{group_num}/ for visual QA.
        """
        try:
            screenshots_dir = Path(base_folder) / "verification_screenshots" / f"group_{group_num}"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            meta_dir = Path(base_folder) / "metadata_blueprints"
            manifest_file = meta_dir / "narration_manifest.json"
            if not manifest_file.exists():
                manifest_file = Path(base_folder) / "narration_manifest.json"
            timestamps = []

            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    group_data = manifest.get("groups", {}).get(str(group_num), {})
                    for pid, pinfo in group_data.get("pairs", {}).items():
                        for st in pinfo.get("statements", []):
                            st_time = float(st.get("start", 0.0))
                            st_dur = float(st.get("duration", 0.0))
                            if st_dur >= 2.5:
                                extract_time = st_time + min(st_dur - 0.4, max(1.8, st_dur * 0.70))
                            else:
                                extract_time = st_time + max(0.4, st_dur * 0.75)
                            st_text = st.get("text", "")[:35]
                            timestamps.append((extract_time, f"step_{pid}_{extract_time:.1f}s", st_text))
                except Exception as e:
                    print(f"Could not read manifest for timestamps: {e}")

            if not timestamps:
                ffprobe_cmd = [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(video_path)
                ]
                res = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
                try:
                    dur = float(res.stdout.strip())
                except Exception:
                    dur = 60.0
                step = max(8.0, dur / 8.0)
                cur = 2.0
                idx = 1
                while cur < dur - 1.0:
                    timestamps.append((cur, f"frame_{idx:02d}_{cur:.1f}s", f"Sample at {cur:.1f}s"))
                    cur += step
                    idx += 1

            saved_frames = []
            for t_sec, label, desc in timestamps:
                out_img = screenshots_dir / f"{label}.png"
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", str(max(0.0, t_sec)),
                    "-i", str(video_path),
                    "-frames:v", "1",
                    str(out_img)
                ]
                subprocess.run(cmd, capture_output=True, text=True, check=False)
                if out_img.exists():
                    saved_frames.append({
                        "timestamp": t_sec,
                        "file": str(out_img.relative_to(base_folder)),
                        "label": label,
                        "description": desc
                    })

            index_path = screenshots_dir / "manifest.json"
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(saved_frames, f, indent=2)

            print(f"📸 Extracted {len(saved_frames)} verification screenshots into {screenshots_dir}")
        except Exception as e:
            print(f"Warning: Screenshot extraction failed for group {group_num}: {e}")

    def audit_verification_screenshots(
        self,
        group_num,
        base_folder,
        script_dir=None,
        final_video_path=None,
        final_output_path=None,
        audio_files=None,
        can_repair=True,
        repair_attempt=0,
        max_repair_attempts=None
    ):
        """
        Closed-loop VLM evaluation on final rendered keyframe screenshots.
        Sends extracted verification keyframes to Gemini 3.5 Flash Multimodal
        to audit Header Clearance, Margin Clamping, and Text Collision.
        If defects are detected and can_repair is True, automatically repairs
        the code and re-renders the scene across up to max_repair_attempts.
        """
        if Image is None or genai is None or types is None:
            return

        if max_repair_attempts is None:
            max_repair_attempts = getattr(self, "max_repair_attempts", 3)

        screenshots_dir = Path(base_folder) / "verification_screenshots" / f"group_{group_num}"
        manifest_path = screenshots_dir / "manifest.json"
        if not manifest_path.exists():
            return

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_frames = json.load(f)
        except Exception:
            return

        if not manifest_frames:
            return

        # Sample keyframes evenly across scene (default 6 for full statement transition coverage, configurable)
        max_sample = int(os.environ.get("VLM_SAMPLE_FRAMES", "6"))
        sample_indices = [0]
        if len(manifest_frames) > 1:
            step = max(1, len(manifest_frames) // max(1, max_sample - 1))
            for idx in range(step, len(manifest_frames), step):
                if idx not in sample_indices and idx < len(manifest_frames):
                    sample_indices.append(idx)
            if (len(manifest_frames) - 1) not in sample_indices:
                sample_indices.append(len(manifest_frames) - 1)

        valid_images = []
        for idx in sample_indices[:max_sample]:
            frame_item = manifest_frames[idx]
            frame_file = Path(base_folder) / frame_item["file"]
            if frame_file.exists():
                try:
                    img = Image.open(frame_file)
                    valid_images.append((frame_item["label"], img))
                except Exception:
                    pass

        if not valid_images or not getattr(self, "google_api_key", None):
            return

        attempt_label = f" (Attempt {repair_attempt + 1}/{max_repair_attempts + 1})" if repair_attempt > 0 else ""
        print(f"🤖 [VLM QA] Auditing {len(valid_images)} final keyframes for Scene {group_num}{attempt_label} with Gemini Flash...")
        vlm_prompt = """
You are a Lead Motion Graphic Quality Assurance Auditor inspecting final rendered 1080p Manim keyframes.
Evaluate these final video frames against the Universal Layout Rules:

1. HEADER CLEARANCE:
   - Is the slide title in the upper-left corner completely clear of any content collisions?
   - Do any diagrams, containers, cards, or math formulas invade the header area (top 20% of canvas)?
2. BORDER CLAMPING:
   - Are any text labels, badges, or callouts clipped or pushed past the left or right edges of the screen?
3. IN-BOX COLLISION & OVERLAPPING:
   - Does any text collide or overlap inside cards, badges, or containers?
   - In multi-column layouts and tables, is there sufficient horizontal spacing between columns? Do Column 2 and Column 3 text overlap or touch?
   - Is there any title stacking (multiple slide titles overlaid simultaneously)?
   - Do any connecting lines or arrows cut through or collide with text labels or callout cards?
4. LEGIBILITY & CONTRAST:
   - Is all text crisp, high-contrast, and effortlessly readable?
   - Are any mathematical formulas (MathTex) invisible, faint, or rendered in white on light backgrounds or low-opacity cards?
   - Are there any opaque white rectangular artifacts or badges masking card borders or content?
   - Is any text white-on-white, light-on-light, or dark-on-dark?
5. NO DUPLICATE STACKED BADGES:
   - Are there identical static badges or callouts stacked or duplicated in loops?
6. TEACHER OVERLAY CLEARANCE:
   - For Layout 70 scenes (Presenter on left: x in [-7.11, -1.22]): Is all text and content positioned strictly in the right safe workspace (x >= -1.0)? Any title or element extending into the left teacher area is a CRITICAL DEFECT.
   - For Layout 20 scenes (Presenter in top-right PiP: x in [+4.267, +7.111], y in [+2.400, +4.000]): Is the top-right corner completely clear of text, titles, badges, and cards? Any element in x > 4.20 and y > 2.0 is a CRITICAL DEFECT.
7. UNSPOKEN MATHEMATICAL NOTATION:
   - Are there mathematical equations or formulas displayed (e.g. U(a) = f(...), d(S_t, G) = ...) that are not spoken in narration? Unspoken equations must be flagged as defects and replaced with clean conceptual text/cards.

Provide your evaluation as a concise JSON report with:
- "scene": number
- "overall_status": "PASSED" or "DEFECT_DETECTED"
- "issues": list of detected visual defects (empty if none)
- "recommendations": concise code adjustments if any issues exist
"""
        defects_found = False
        detected_issues = []
        recommendations = ""

        if os.environ.get("SKIP_VLM_QA") == "1":
            print(f"Skipping VLM QA audit for Scene {group_num} (SKIP_VLM_QA=1)")
            return

        client = genai.Client(api_key=self.google_api_key)
        contents = [vlm_prompt]
        for label, img in valid_images:
            contents.append(f"Keyframe: {label}")
            contents.append(img)

        resp = None
        max_vlm_retries = 3
        for vlm_ret in range(1, max_vlm_retries + 1):
            try:
                resp = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
                break
            except Exception as e:
                print(f"Warning: VLM QA audit attempt {vlm_ret}/{max_vlm_retries} failed: {e}")
                if vlm_ret < max_vlm_retries:
                    time.sleep(3 * vlm_ret)
                else:
                    print(f"Warning: VLM QA audit skipped after {max_vlm_retries} attempts: {e}")
                    return

        report_text = resp.text or "{}" if resp else "{}"
        report_path = screenshots_dir / "vlm_qa_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"✅ [VLM QA Report] Saved to {report_path}")
        try:
            rep_json = json.loads(report_text)
            if isinstance(rep_json, list):
                for item in rep_json:
                    s_idx = item.get("scene", group_num)
                    st = item.get("overall_status", "UNKNOWN")
                    iss = item.get("issues", [])
                    print(f"🔍 [VLM Verdict Scene {group_num} (Keyframe/Step {s_idx})]: {st}")
                    if st != "PASSED" or iss:
                        defects_found = True
                        if iss:
                            detected_issues.extend(iss if isinstance(iss, list) else [iss])
                        if item.get("recommendations"):
                            recommendations += "\n" + str(item.get("recommendations"))
                        print(f"   Detected issues: {iss}")
            elif isinstance(rep_json, dict):
                status = rep_json.get("overall_status", "UNKNOWN")
                iss = rep_json.get("issues", [])
                print(f"🔍 [VLM Verdict Scene {group_num}]: {status}")
                if status != "PASSED" or iss:
                    defects_found = True
                    if iss:
                        detected_issues.extend(iss if isinstance(iss, list) else [iss])
                    if rep_json.get("recommendations"):
                        recommendations = str(rep_json.get("recommendations"))
                    print(f"   Detected issues: {iss}")
        except Exception:
            pass

        topic_name = os.path.basename(str(base_folder))
        # Trigger Visual Self-Healing if defects were detected and repair attempts remain
        if defects_found and can_repair and not getattr(self, "no_repair", False) and repair_attempt < max_repair_attempts and script_dir and final_video_path and final_output_path and getattr(self, "google_api_key", None):
            next_attempt = repair_attempt + 1
            print(f"🔧 [VLM Self-Healing] Visual defects detected in final output for Scene {group_num} (Triggering repair {next_attempt}/{max_repair_attempts})!")
            print(f"🔧 [VLM Self-Healing] Initiating closed-loop visual repair...")
            self.repair_visual_defects(
                group_num=group_num,
                script_dir=script_dir,
                final_video_path=final_video_path,
                final_output_path=final_output_path,
                audio_files=audio_files,
                base_folder=base_folder,
                issues=detected_issues,
                recommendations=recommendations,
                valid_images=valid_images,
                repair_attempt=next_attempt,
                max_repair_attempts=max_repair_attempts
            )
        elif not defects_found:
            print(f"🎉 [VLM QA] Scene {group_num} passed all visual QA checks! Zero defects detected.")
            if topic_name in self.unresolved_defects and str(group_num) in self.unresolved_defects[topic_name]:
                del self.unresolved_defects[topic_name][str(group_num)]
            if script_dir:
                bak_file = Path(script_dir) / f"group_{group_num}.py.vlm_bak"
                if bak_file.exists():
                    try:
                        bak_file.unlink()
                    except Exception:
                        pass
        else:
            print(f"❌ [VLM QA FAIL] Scene {group_num} has unresolved visual defects after {repair_attempt} repair attempts!")
            self.unresolved_defects.setdefault(topic_name, {})[str(group_num)] = detected_issues

    def repair_visual_defects(
        self,
        group_num,
        script_dir,
        final_video_path,
        final_output_path,
        audio_files,
        base_folder,
        issues,
        recommendations,
        valid_images,
        repair_attempt=1,
        max_repair_attempts=None
    ):
        """
        Closed-loop visual self-healing:
        Applies code adjustments for defects identified by VLM audit,
        compiles, re-renders the scene, re-merges audio, and re-audits keyframes.
        """
        if max_repair_attempts is None:
            max_repair_attempts = getattr(self, "max_repair_attempts", 3)
        script_path = Path(script_dir) / f"group_{group_num}.py"
        if not script_path.exists():
            print(f"[VLM Self-Healing] Script {script_path} not found.")
            return False

        try:
            with open(script_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            issues_text = "\n".join(f"- {issue}" for issue in issues) if isinstance(issues, list) else str(issues)
            rec_text = recommendations or "Fix all header clearance, boundary clamping, and overlapping text issues."

            # Construct targeted surgical layout directives
            surgical_directives = []
            iss_text_combined = " ".join(str(i) for i in issues).lower()

            if any(w in iss_text_combined for w in ["title", "header", "stacking", "stacked", "double-exposure"]):
                surgical_directives.append(
                    "TITLE & HEADER CLEARANCE RULES (CRITICAL):\n"
                    "- Only ONE title mobject may exist in the top-left quadrant (UL) at any time.\n"
                    "- If 'header_group = create_title(...)' is defined in the setup, you MUST DELETE any redundant 'title_group = create_title(...)' or 'self.play(FadeIn(title_group))' in Step 1.\n"
                    "- NEVER define 'title_group = create_title(...)' or animate FadeIn(title_group) twice in the same step! Ensure there is only one create_title call per step.\n"
                    "- If changing slide titles between steps, always fade out or remove the old title (e.g. self.remove(old_title)) before introducing the new one.\n"
                    "- Never fade out a title in the middle of a step; keep the header title visible throughout each presentation step."
                )

            if any(w in iss_text_combined for w in ["line", "arrow", "intersects", "crosses", "through", "divider", "bisect", "axis"]):
                surgical_directives.append(
                    "LINE & ARROW ROUTING RULES (CRITICAL):\n"
                    "- Connecting lines and arrows must never cut through or touch text boxes, callout cards, or badges.\n"
                    "- All callout cards, badges, and pills MUST have 'fill_opacity=1.0' (opaque background) and '.set_z_index(20)' so plot curves, axis lines, and trajectories passing behind them are occluded and do not cut through card text.\n"
                    "- Axis lines must never cut through axis labels or callout badges. Use next_to(axis, DOWN, buff=0.35) or shift horizontally/vertically away from the axis.\n"
                    "- In multi-row diagrams or trees, connect nodes hierarchically (e.g. Line(top_card.get_bottom(), bot_card.get_top())) or route around intermediate cards with CurvedArrow/path_arc.\n"
                    "- If a callout badge or text sits between connected nodes, reposition it below or above the connection line so the line path is completely unobstructed."
                )

            if any(w in iss_text_combined for w in ["badge", "pill", "card", "overlap", "collides", "crowd", "formula", "obscures", "border", "breach", "table", "column", "divider"]):
                surgical_directives.append(
                    "SPATIAL SEPARATION, COLLISION & TABLE LAYOUT RULES (CRITICAL):\n"
                    "- Never place two annotations/badges at identical or overlapping coordinates (e.g. 'Distance = Frequency' and 'Height = AOV'). Group them vertically with arrange(DOWN, buff=0.25) or place them on opposite sides.\n"
                    "- MULTI-COLUMN & TABLE SPACING: In 3-column tables, Column 1 is anchored near get_left() + RIGHT * 0.4, Column 2 at get_left() + RIGHT * 3.8, and Column 3 at get_left() + RIGHT * 8.0 (with vertical dividers at RIGHT * 3.4 and RIGHT * 7.2). NEVER place Column 3 between 5.5 and 6.5 where it touches or overlaps Column 2 data! Guarantee at least 2.4 units of horizontal clearance between columns.\n"
                    "- Never render a container card directly on top of an active math formula. Position cards clearly outside formula bounds.\n"
                    "- Ensure text inside badges, pills, and dashed callout cards has sufficient padding (buff >= 0.35 horizontally, buff >= 0.20 vertically) and scale down font size slightly (e.g. font_size=12 or .scale(0.85)) so text never touches or is bisected by border lines.\n"
                    "- All callouts and badges must remain clamped strictly within slide margins (x between -5.6 and 5.6, y between -3.4 and 1.8) and inside container card borders.\n"
                    "- Maintain at least 0.25 vertical buffer between badges and container labels or neighboring cards.\n"
                    "- Badges must NEVER overlap card outer borders (e.g. 'Urgent Churn Risk' overlapping 'At-Risk' card border).\n"
                    "- Connecting arrows between cards must route cleanly around cards or be positioned behind foreground text cards (card.set_z_index(2), arrow.set_z_index(0))."
                )

            if any(w in iss_text_combined for w in ["contrast", "legibility", "invisible", "faint", "pale", "unreadable", "white-on-white", "dark", "purple", "mathtex", "formula", "white box", "bounding box"]):
                surgical_directives.append(
                    "COLOR CONTRAST & LEGIBILITY RULES (CRITICAL - guidelines.md Section 6.2 & 6.4):\n"
                    "- White text (#FFFFFF) or light gray on white/light backgrounds is STRICTLY FORBIDDEN.\n"
                    "- All text, axis labels, and formulas on white or light backgrounds MUST use high-contrast dark charcoal (#404040).\n"
                    "- NAVY BLUE PROHIBITION: Navy Blue (#0B3C5D, #06152B, #0A2540, NAVY) is strictly PROHIBITED and is NOT part of the Simplilearn palette! Do NOT use dark navy containers, headers, or backgrounds.\n"
                    "- NO ALL CAPS: All on-screen text, titles, subtitles, headers, card labels, and tags must NEVER be written in ALL CAPS. Use Title Case for titles and headers; use Sentence Case for body text and descriptions. Short technical acronyms only (AI, RAM, DB, API, LLM, CPU, GPU, UI, ML) may be uppercase.\n"
                    "- MATHTEX FORMULAS ON LIGHT CARDS: If a card or container is light, white, or has low fill opacity (e.g. fill_opacity=0.10 or <= 0.45), ALL text and MathTex formulas MUST explicitly specify color=C_TEXT (#404040). NEVER use white text or white formulas on light containers or white canvas!\n"
                    "- NEVER place dark text inside a dark container or light text inside a light container.\n"
                    "- NO OPAQUE WHITE BOX ARTIFACTS: Never place opaque white BackgroundRectangle on light/colored cards. Set fill_opacity=0."
                )

            if any(w in iss_text_combined for w in ["empty", "unpopulated", "blank", "orphan"]):
                surgical_directives.append(
                    "POPULATED CONTAINER RULES (CRITICAL):\n"
                    "- Every background card or rectangle MUST contain readable text, numbers, or chart elements.\n"
                    "- If a card or container is unpopulated or orphaned, either add the appropriate informative label/content or remove the empty container entirely."
                )

            surgical_text = "\n\n".join(surgical_directives) if surgical_directives else ""

            repair_prompt = f"""You are a Lead Motion Graphic Animation Engineer performing automated layout repair on a Manim community presentation scene.
The scene has already been timed and rendered, but visual QA inspection detected layout defects that must be resolved.

DETECTED VISUAL DEFECTS:
{issues_text}

AUDITOR RECOMMENDATIONS:
{rec_text}

{surgical_text}

MANDATORY RULES:
1. HEADER CLEARANCE:
   - Ensure the slide title in the upper-left corner is completely uninvaded and has zero double-exposure stacking.
   - If both create_title(...) and create_header(...) exist in Step 1, DELETE the redundant create_title(...) call and keep only ONE header mobject!
   - When transitioning between steps, if introducing a new title, always remove or fade out the old title (e.g. self.remove(old_title)) so titles never stack.
   - Any containers, cards, diagrams, badges, or math formulas must have their top bound <= UP * 2.2 (y <= 2.2).
2. BORDER CLAMPING:
   - Ensure all elements stay comfortably within horizontal canvas bounds (x between -6.4 and 6.4).
   - Ensure cards and boxes do not exceed screen boundaries.
3. IN-BOX COLLISION & OVERLAPPING:
   - Eliminate any overlapping text labels, badges, or colliding shapes.
   - Multi-column tables MUST have Column 3 at get_left() + RIGHT * 8.0 with dividers at 7.2 (never crowded under 6.5).
   - Reduce font sizes slightly if text exceeds card bounds or overlaps (e.g. reduce size by 2-4pt).
   - Ensure container heights fit their contents with >= 0.25 padding.
   - Ensure connecting lines route cleanly around text callouts.
   - Badges must NOT intersect outer borders of cards.
4. AXIS AND CONNECTOR CLEARANCE:
   - Axis labels and formulas must NEVER be cut through by horizontal or vertical axis lines or arrow tips. Guarantee at least 0.35 padding from axis top/ends.
   - Connecting lines and arrows between cards must route cleanly around cards or be positioned behind foreground text cards (card.set_z_index(10) with fill_opacity=1.0, arrow.set_z_index(0)).
5. NO EMPTY CONTAINERS:
   - Ensure no background cards or badges are rendered empty without text.
6. COLOR CONTRAST & CASING (guidelines.md Section 4.2, 4.3, 6.2, 6.4):
   - NAVY BLUE PROHIBITION: Navy Blue (#0B3C5D, #06152B, #0A2540, NAVY) is strictly PROHIBITED and is NOT part of the Simplilearn palette!
   - NO ALL CAPS: All on-screen text, titles, subtitles, headers, card labels, and tags must NEVER be written in ALL CAPS. Use Title Case for titles and headers; use Sentence Case for body text. Short technical acronyms only (AI, RAM, DB, API, LLM, CPU, GPU, UI, ML) may be uppercase.
   - Text and MathTex formulas on light cards or canvas MUST be dark charcoal (#404040 / C_TEXT).
   - Never render white formulas on light containers or dark text on dark containers.
7. CRITICAL: PRESERVE EXACT AUDIO TIMING & SYNCHRONIZATION:
   - YOU MUST NOT MODIFY, ADD, OR DELETE ANY self.sync_to(...) CALLS OR self.wait(...) DURATIONS!
   - Every self.sync_to(TIMESTAMP) call represents exact millisecond synchronization with spoken audio narration.
   - Preserving all self.sync_to(...) calls, their target timestamps, and progressive reveal ordering is 100% MANDATORY.
   - Never clump all animations at the beginning of a step.
   - Keep the FinalScene method def sync_to(self, target_time): completely intact.
8. CODE INTEGRITY:
   - Return ONLY the complete, executable Python code with all imports and helpers included.
   - Do NOT omit any sections or use ellipsis/placeholders.
   - Preserve the class name FinalScene.

CURRENT PYTHON SCRIPT:
```python
{source_code}
```
"""
            client = genai.Client(api_key=self.google_api_key)
            contents = [repair_prompt]
            max_defect_imgs = int(os.environ.get("VLM_DEFECT_IMGS", "4"))
            for label, img in valid_images[:max_defect_imgs]:
                contents.append(f"Visual Defect Screenshot: {label}")
                contents.append(img)

            vlm_thinking_level = os.environ.get("VLM_THINKING_LEVEL", "high")
            print(f"🤖 [VLM Self-Healing] Requesting Gemini layout repair for Scene {group_num} (attempt {repair_attempt}/{max_repair_attempts}) with high-thinking mode (thinking_level='{vlm_thinking_level}')...")
            resp = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=65000,
                    thinking_config=types.ThinkingConfig(thinking_level=vlm_thinking_level),
                )
            )

            repaired_code = extract_code_from_response(resp.text or "")
            if not repaired_code.strip():
                print(f"[VLM Self-Healing] Empty code response from Gemini for Scene {group_num}.")
                return False

            # Ensure sync_to method exists in FinalScene if repaired code dropped it
            if "def sync_to(" not in repaired_code and "class FinalScene" in repaired_code:
                repaired_code = re.sub(
                    r"(class FinalScene\s*\([^)]*\)\s*:\n)",
                    r"\1    def sync_to(self, target_time):\n        current_time = getattr(getattr(self, 'renderer', None), 'time', 0.0)\n        if target_time > current_time:\n            self.wait(target_time - current_time)\n\n",
                    repaired_code,
                    count=1
                )

            # Timing synchronization safety check: ensure repair did not strip self.sync_to calls
            orig_syncs = re.findall(r"self\.sync_to\(\s*[\d\.]+\s*\)", source_code)
            repaired_syncs = re.findall(r"self\.sync_to\(\s*[\d\.]+\s*\)", repaired_code)
            if orig_syncs and len(repaired_syncs) < len(orig_syncs) * 0.6:
                print(f"⚠️ [VLM Self-Healing] Warning: Layout repair stripped sync_to calls ({len(repaired_syncs)} vs {len(orig_syncs)} originally). Rejecting repair to preserve audio-video timing synchronization!")
                return False

            # Sanitize and compile
            repaired_code = sanitize_manim_code(repaired_code, str(script_path))
            compile(repaired_code, str(script_path), "exec")

            # Backup original
            backup_path = script_path.with_suffix(".py.vlm_bak")
            if not backup_path.exists():
                with open(backup_path, "w", encoding="utf-8") as bf:
                    bf.write(source_code)

            # Write repaired code
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(repaired_code)
            sanitize_file(str(script_path))
            print(f"✅ [VLM Self-Healing] Repaired code saved to {script_path.name}. Re-rendering scene...")

            # Determine theme
            conf_file = Path(base_folder) / "ex_config.json"
            theme = "default"
            if conf_file.exists():
                try:
                    with open(conf_file, "r", encoding="utf-8") as cf:
                        theme = json.load(cf).get("theme", "default")
                except Exception:
                    pass

            # Re-render scene
            render_ok = self.render_single_scene(
                absolute_script_path=str(script_path),
                final_video_path=final_video_path,
                theme=theme,
                manim_fps=15
            )
            if not render_ok:
                print(f"[VLM Self-Healing] Re-render failed for Scene {group_num}. Restoring backup.")
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(source_code)
                return False

            # Re-merge audio with allow_repair=False so combine_video_with_audio does not re-audit directly
            print(f"🔄 [VLM Self-Healing] Re-merging audio for Scene {group_num}...")
            final_out = self.combine_video_with_audio(
                group_num=group_num,
                audio_files=audio_files,
                script_dir=script_dir,
                final_video_path=final_video_path,
                base_folder=base_folder,
                allow_repair=False
            )

            # Re-extract verification screenshots from the newly rendered video
            self.extract_verification_screenshots(group_num, final_out, base_folder)

            # Closed loop: Re-audit the newly extracted screenshots to confirm whether defects were resolved!
            print(f"🔍 [VLM Self-Healing] Re-auditing keyframes after repair (attempt {repair_attempt}/{max_repair_attempts})...")
            self.audit_verification_screenshots(
                group_num=group_num,
                base_folder=base_folder,
                script_dir=script_dir,
                final_video_path=final_video_path,
                final_output_path=final_output_path,
                audio_files=audio_files,
                can_repair=(repair_attempt < max_repair_attempts),
                repair_attempt=repair_attempt,
                max_repair_attempts=max_repair_attempts
            )
            print(f"🎉 [VLM Self-Healing] Closed-loop visual repair cycle completed for Scene {group_num}!")
            return True

        except Exception as e:
            print(f"[VLM Self-Healing] Error repairing Scene {group_num}: {e}")
            return False

    def render_single_scene(self, absolute_script_path, final_video_path, theme="default", manim_fps=15):
        """
        Renders a single Manim scene script to MP4 using conda environment.
        Includes self-healing compiler retry loop.
        Returns True if successful, False otherwise.
        """
        script_dir = os.path.dirname(os.path.abspath(absolute_script_path))
        code_file = os.path.basename(absolute_script_path)

        conda_env_name = os.environ.get(
            "CONDA_MANIM_ENV",
            "render" if os.path.exists("/opt/homebrew/Caskroom/miniforge/base/envs/render") else "manim"
        )
        conda_bin = shutil.which("conda") or "/opt/homebrew/Caskroom/miniforge/base/condabin/conda"

        # Deterministic AST & regex sanitation prior to rendering
        if sanitize_file(absolute_script_path):
            print(f"[Sanitizer] Applied automatic AST/regex fixes to {code_file}")

        if theme == "promo":
            pixel_width = 720
            pixel_height = 1280
        else:
            pixel_width = 1280
            pixel_height = 720

        scene_name = "FinalScene"
        manim_direct_bin = f"/opt/homebrew/Caskroom/miniforge/base/envs/{conda_env_name}/bin/manim"
        if os.path.exists(manim_direct_bin):
            command = [
                manim_direct_bin, "render",
                "-qm",
                "--progress_bar", "none",
                "--frame_rate", str(manim_fps),
                "--verbosity", "ERROR",
                "--resolution", f"{pixel_width},{pixel_height}",
                "--disable_caching",
                str(absolute_script_path),
                scene_name
            ]
        else:
            command = [
                conda_bin, "run", "-n", conda_env_name,
                "manim", "render",
                "-qm",
                "--progress_bar", "none",
                "--frame_rate", str(manim_fps),
                "--verbosity", "ERROR",
                "--resolution", f"{pixel_width},{pixel_height}",
                "--disable_caching",
                str(absolute_script_path),
                scene_name
            ]

        max_heal_attempts = 2
        render_success = False

        for attempt in range(max_heal_attempts + 1):
            attempt_str = f" (attempt {attempt + 1}/{max_heal_attempts + 1})" if attempt > 0 else ""
            run_env = os.environ.copy()
            workflow_dir = os.path.abspath(os.path.dirname(__file__))
            helpers_dir = os.path.join(workflow_dir, "helpers")
            parent_dir = os.path.dirname(workflow_dir)
            run_env["PYTHONPATH"] = f"{helpers_dir}:{workflow_dir}:{parent_dir}:{run_env.get('PYTHONPATH', '')}"
            result = subprocess.run(command, cwd=script_dir, text=True, shell=False, capture_output=True, env=run_env)

            if result.stdout and result.stdout.strip():
                print("--- Manim Standard Output ---")
                print(result.stdout)
                print("-----------------------------")
            if result.stderr and result.stderr.strip():
                print("--- Manim Standard Error ---")
                print(result.stderr)
                print("----------------------------")

            if result.returncode == 0:
                render_success = True
                break

            print(f"--- Manim Rendering Failed for {code_file}{attempt_str} ---")

            if attempt < max_heal_attempts and self.google_api_key:
                print(f"[Self-Healing] Triggering automated repair for {code_file}...")
                error_output = (result.stdout or "") + "\n" + (result.stderr or "")
                try:
                    with open(absolute_script_path, "r", encoding="utf-8") as f:
                        source_code = f.read()

                    repaired_code = repair_code_with_llm(
                        source_code=source_code,
                        error_output=error_output,
                        filename=code_file,
                        google_api_key=self.google_api_key
                    )

                    if repaired_code:
                        with open(absolute_script_path, "w", encoding="utf-8") as f:
                            f.write(repaired_code)
                        sanitize_file(absolute_script_path)
                        print(f"[Self-Healing] Repaired and sanitized code saved to {code_file}. Retrying render...")
                        continue
                    else:
                        print(f"[Self-Healing] LLM repair attempt yielded no valid code for {code_file}.")
                        break
                except Exception as e:
                    print(f"[Self-Healing] Exception during repair process: {e}")
                    break
            else:
                break

        if not render_success:
            print(f"--- Giving up on rendering {code_file} after {attempt + 1} attempt(s) ---")
            return False

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
                    raise FileNotFoundError("Manim rendering finished, but no output video file was found.")
                rendered_video_path = all_videos[0]

        print(f"Moving rendered video from '{rendered_video_path}' to '{final_video_path}'")
        shutil.move(str(rendered_video_path), str(final_video_path))
        # Mirror to manim_videos for downstream assembly stages
        try:
            parent_topic_folder = Path(final_video_path).parent.parent
            manim_vids_dir = parent_topic_folder / "manim_videos"
            manim_vids_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(final_video_path), str(manim_vids_dir / Path(final_video_path).name))
        except Exception:
            pass
        shutil.rmtree(media_dir, ignore_errors=True)
        return True

    def execute_script(self, script_dir, base_folder, conf_file, force=False, target_group=None):
        """
        Placeholder for execution logic. To be populated later.
        """
        with open(conf_file,'r', encoding="utf-8") as f:
            config_data = json.load(f)

        base_folder = config_data['base_folder']
        theme = config_data['theme']

        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        cgi_input = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_input):
            cgi_input = f"{base_folder}/CGI_Input.json"
        with open(cgi_input,'r', encoding="utf-8") as f:
            cgi_data = json.load(f)

        manim_adjusted_codes_folder = script_dir
        if not manim_adjusted_codes_folder or not os.path.isdir(str(manim_adjusted_codes_folder)):
            for fallback in [
                os.path.join(base_folder, "manim_time_synced_code"),
                os.path.join(base_folder, "manim_styled_codes"),
                os.path.join(base_folder, "manim_codes")
            ]:
                if os.path.isdir(fallback):
                    manim_adjusted_codes_folder = fallback
                    script_dir = fallback
                    break
        raw_videos_folder = Path(f"{base_folder}/manim_time_synced_videos")
        os.makedirs(raw_videos_folder,exist_ok=True)

        conda_env_name = os.environ.get(
            "CONDA_MANIM_ENV",
            "render" if os.path.exists("/opt/homebrew/Caskroom/miniforge/base/envs/render") else "manim"
        )
        conda_bin = shutil.which("conda") or "/opt/homebrew/Caskroom/miniforge/base/condabin/conda"

        raw_audio_clips_folder = Path(f"{base_folder}/audio_elements")
        audio_files = list(raw_audio_clips_folder.glob('*.wav'))

        code_file_names = os.listdir(manim_adjusted_codes_folder)
        sorted_code_file_names = sorted(code_file_names,key=self.sort_key)

        input_scripts_count = len([f for f in code_file_names if re.match(r"^group_\d+\.py$", f)])
        raw_videos_count = 0
        final_videos_count = 0

        manim_fps = 15

        
        for code_file in sorted_code_file_names:
            
            if not code_file.endswith(".py") or code_file.endswith((".bak", ".vlm_bak", ".tmp")):
                continue

            match = re.match(r"^group_(\d+)\.py$", code_file)
            if match:
                group_num = int(match.group(1))
            else:
                print(f"Skipping non-standard script file: {code_file}")
                continue

            absolute_script_path = os.path.abspath(os.path.join(manim_adjusted_codes_folder,code_file))
            final_video_name = f"{code_file.split('.')[0]}.mp4"
            final_video_path = raw_videos_folder/final_video_name
            script_dir = os.path.dirname(absolute_script_path)

            final_audio_integrated = Path(base_folder) / "audio_integrated_videos" / f"group_{group_num}_final.mp4"
            if not final_audio_integrated.exists():
                final_audio_integrated = Path(base_folder) / "audio_integrated_videos" / f"group_{group_num}_claude_final.mp4"

            if target_group is not None and group_num != target_group:
                if final_video_path.exists():
                    raw_videos_count += 1
                else:
                    input_scripts_count -= 1
                if final_audio_integrated.exists():
                    final_videos_count += 1
                continue

            skip_scenes_env = os.environ.get("SKIP_SCENES")
            if skip_scenes_env and str(group_num) in [s.strip() for s in skip_scenes_env.split(",")]:
                print(f"Skipping Scene {group_num} per SKIP_SCENES")
                if final_video_path.exists():
                    raw_videos_count += 1
                else:
                    input_scripts_count -= 1
                if final_audio_integrated.exists():
                    final_videos_count += 1
                continue

            # CRITICAL TIMING GUARD: Ensure script contains audio-sync beats (self.sync_to)
            # If the script lacks timing synchronization beats (e.g. from an untimed fallback copy),
            # automatically apply programmatic timing synchronization from narration_manifest.json before rendering
            # so all elements in a presentation step are strictly synchronized with audio narration.
            try:
                if os.path.exists(absolute_script_path):
                    with open(absolute_script_path, "r", encoding="utf-8") as sc_f:
                        current_script_code = sc_f.read()
                    if "self.sync_to(" not in current_script_code:
                        print(f"⚠️ [Timing Guard] {code_file} lacks self.sync_to beats! Checking narration manifest...")
                        manifest_path = os.path.join(meta_dir, "narration_manifest.json")
                        if not os.path.exists(manifest_path):
                            manifest_path = os.path.join(base_folder, "narration_manifest.json")
                        if os.path.exists(manifest_path):
                            with open(manifest_path, "r", encoding="utf-8") as mf:
                                manifest_data = json.load(mf)
                            gm = manifest_data.get("groups", {}).get(str(group_num))
                            if gm:
                                synced_code = apply_programmatic_timing_sync(current_script_code, gm)
                                if "self.sync_to(" in synced_code:
                                    compile(synced_code, absolute_script_path, "exec")
                                    with open(absolute_script_path, "w", encoding="utf-8") as sc_f:
                                        sc_f.write(synced_code)
                                    print(f"✅ [Timing Guard] Successfully injected programmatic timing sync into {code_file} prior to rendering.")
            except Exception as e:
                print(f"⚠️ [Timing Guard] Notice for {code_file}: {e}")

            is_group_forced = force or (target_group is not None and group_num == target_group)
            if not is_group_forced and final_video_path.exists() and os.path.getmtime(str(final_video_path)) >= os.path.getmtime(absolute_script_path):
                raw_videos_count += 1
                #Continue to the next item but add a check to make sure that the video file timing tallies against its respective run time
                run_time = sum(item["run_time"] for item in cgi_data[str(group_num)])
                video_clip = VideoFileClip(str(final_video_path))
                video_duration = video_clip.duration
                video_clip.close()
                video_audio_delta = abs(video_duration - run_time)
                print(f"The video differs from the audio duration by {video_audio_delta} seconds.")
                if video_audio_delta > 4.0:
                    print(f"A large mismatch of {video_audio_delta} seconds has been detected for {final_video_path}")
                
                final_video_path_n = self.combine_video_with_audio(group_num, audio_files, script_dir, final_video_path, base_folder)
                if final_video_path_n and os.path.exists(final_video_path_n):
                    final_videos_count += 1
                continue
            
            print(f"Creating animation for {code_file}")
            render_success = self.render_single_scene(
                absolute_script_path=absolute_script_path,
                final_video_path=final_video_path,
                theme=theme,
                manim_fps=manim_fps
            )
            if not render_success:
                continue
            
            if final_video_path.exists():
                raw_videos_count += 1

            #Add a check to make sure that the video file timing tallies against its respective run time
            run_time = sum(item["run_time"] for item in cgi_data[str(group_num)])
            video_clip = VideoFileClip(str(final_video_path))
            video_duration = video_clip.duration
            video_clip.close()
            video_audio_delta = abs(video_duration - run_time)
            print(f"The video differs from the audio duration by {video_audio_delta} seconds.")
            if video_audio_delta > 4.0:
                print(f"A large mismatch of {video_audio_delta} seconds has been detected for {final_video_path}")
            
            final_video_path_n = self.combine_video_with_audio(group_num, audio_files, script_dir, final_video_path, base_folder)
            if final_video_path_n and os.path.exists(final_video_path_n):
                final_videos_count += 1

            print(f"--- Manim scene FinalScene rendered and file moved successfully! ---")

        return str(raw_videos_folder), input_scripts_count, raw_videos_count, final_videos_count

    def process_files(self, target_topic_id=None, force=False, target_group=None):
        """
        Main logic to process unprocessed files.
        """
        force = force or os.environ.get("FORCE_RUN", "0") == "1"
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

            if not force and target_group is None and topic_id in output_tracker and output_tracker[topic_id].get("processed", False):
                print(f"Skipping {topic_id}: Already processed in output tracker.")
                continue

            print(f"Processing {topic_id}...")
            
            base_folder = os.path.join(self.input_folder, topic_id)
            
            # Define expected file paths
            config_path = os.path.join(base_folder, "ex_config.json")
            
            if not os.path.exists(config_path):
                print(f"Skipping {topic_id}: Missing context.txt or ex_config.json.")
                continue
            
            output_path = None
            try:
                script_dir = input_entry.get("output_path")
                if not script_dir or not os.path.isdir(str(script_dir)):
                    for fallback in [
                        os.path.join(base_folder, "manim_time_synced_code"),
                        os.path.join(base_folder, "manim_styled_codes"),
                        os.path.join(base_folder, "manim_codes")
                    ]:
                        if os.path.isdir(fallback):
                            script_dir = fallback
                            break

                output_path, input_scripts_count, raw_videos_count, final_videos_count = self.execute_script(
                    script_dir=script_dir,
                    base_folder=base_folder,
                    conf_file=config_path,
                    force=force,
                    target_group=target_group
                )

                # 4. Update tracker (Success)
                # Re-load tracker to minimize race conditions
                tracker = self._load_tracker(self.output_tracker_path)
                
                if target_group is not None and output_path:
                    actual_raw = len(list(Path(output_path).glob("group_*.mp4")))
                    actual_final = len(list((Path(base_folder) / "audio_integrated_videos").glob("group_*_final.mp4")))
                    if actual_raw >= input_scripts_count:
                        raw_videos_count = actual_raw
                        final_videos_count = actual_final

                topic_defects = {str(k): list(v) if isinstance(v, list) else [str(v)] for k, v in self.unresolved_defects.get(topic_id, {}).items()}
                # Cross-reference with on-disk VLM QA reports
                verif_dir = Path(base_folder) / "verification_screenshots"
                if verif_dir.exists():
                    for report_path in sorted(verif_dir.glob("group_*/vlm_qa_report.json")):
                        try:
                            with open(report_path, "r", encoding="utf-8") as rf:
                                report_data = json.load(rf)
                                entries = report_data if isinstance(report_data, list) else [report_data] if isinstance(report_data, dict) else []
                                grp_key = str(report_path.parent.name.replace("group_", ""))
                                
                                grp_issues = []
                                has_defect = False
                                for entry in entries:
                                    if not isinstance(entry, dict):
                                        continue
                                    if entry.get("overall_status") == "DEFECT_DETECTED" or entry.get("defects_detected"):
                                        has_defect = True
                                        issues = entry.get("issues", [])
                                        if issues:
                                            if isinstance(issues, list):
                                                grp_issues.extend(issues)
                                            else:
                                                grp_issues.append(str(issues))
                                
                                if has_defect:
                                    unique_issues = list(dict.fromkeys(grp_issues)) if grp_issues else topic_defects.get(grp_key, ["Visual defect detected by VLM QA"])
                                    topic_defects[grp_key] = unique_issues
                                elif entries and all(isinstance(e, dict) and e.get("overall_status") == "PASSED" for e in entries):
                                    topic_defects.pop(grp_key, None)
                        except Exception:
                            pass

                strict_gate = (os.environ.get("STRICT_VLM_GATE", "1") in ("1", "true", "True")) and not self.no_repair
                if strict_gate and topic_defects:
                    defect_summary = "; ".join(f"Scene {g}: {len(d)} defect(s)" for g, d in sorted(topic_defects.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0]))
                    print(f"❌ [VLM QA GATING] Topic {topic_id} has unresolved visual defects: {defect_summary}")
                    tracker[topic_id] = {
                        "output_path": output_path,
                        "topic_name": topic_id,
                        "topic_id": topic_id,
                        "processed": False,
                        "failure_reason": f"Unresolved visual defects remaining after VLM QA repair attempts: {defect_summary}",
                        "unresolved_defects": topic_defects,
                        "input_scripts_count": input_scripts_count,
                        "raw_videos_count": raw_videos_count,
                        "final_videos_count": final_videos_count
                    }
                    self._save_tracker(self.output_tracker_path, tracker)
                elif raw_videos_count < input_scripts_count:
                    tracker[topic_id] = {
                        "output_path": output_path,
                        "topic_name": topic_id,
                        "topic_id": topic_id,
                        "processed": False,
                        "failure_reason": f"{input_scripts_count-raw_videos_count} code scripts failed during raw video creation",
                        "input_scripts_count": input_scripts_count,
                        "raw_videos_count": raw_videos_count,
                        "final_videos_count": final_videos_count
                    }
                    self._save_tracker(self.output_tracker_path, tracker)
                else:
                    tracker[topic_id] = {
                        "output_path": output_path,
                        "topic_name": topic_id,
                        "topic_id": topic_id,
                        "processed": True,
                        "failure_reason": None,
                        "input_scripts_count": input_scripts_count,
                        "raw_videos_count": raw_videos_count,
                        "final_videos_count": final_videos_count
                    }
                    if topic_defects:
                        tracker[topic_id]["unresolved_defects"] = topic_defects
                        defect_summary = "; ".join(f"Scene {g}: {len(d)} defect(s)" for g, d in sorted(topic_defects.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0]))
                        print(f"⚠️ [VLM QA ADVISORY] Topic {topic_id} processed successfully with non-blocking visual advisories: {defect_summary}")
                    else:
                        if "unresolved_defects" in tracker[topic_id]:
                            del tracker[topic_id]["unresolved_defects"]
                        print(f"Successfully processed {topic_id} with ZERO visual defects.")
                    self._save_tracker(self.output_tracker_path, tracker)

                    if raw_videos_count >= input_scripts_count and input_scripts_count > 0:
                        self.auto_export_deliverables(topic_id)

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
                    "raw_videos_count": 0,
                    "final_videos_count": 0
                }
                self._save_tracker(self.output_tracker_path, tracker)

    def auto_export_deliverables(self, topic_id):
        """
        Automatically exports final deliverables (videos, screenshots, storyboards)
        to data_ppt_final_outputs so deliverables are never out of sync.
        """
        try:
            workflow_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(workflow_dir)
            exporter_name = "copy_pipeline_outputs.py"
            exporter_path = os.path.join(workflow_dir, exporter_name)
            if not os.path.exists(exporter_path):
                exporter_path = os.path.join(parent_dir, exporter_name)
            if os.path.exists(exporter_path):
                print(f"📦 Auto-syncing final outputs and screenshots for {topic_id}...")
                subprocess.run([sys.executable, exporter_path, "--topic", str(topic_id)], check=False)
        except Exception as e:
            print(f"Warning: Auto-export failed for {topic_id}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 22: Final Manim Render & Audio Integration")
    parser.add_argument("--topic", type=str, default=None, help="Target specific topic ID")
    parser.add_argument("--group", type=int, default=None, help="Target specific group number (e.g. 2)")
    parser.add_argument("--force", action="store_true", help="Force re-rendering even if already marked processed")
    parser.add_argument("--no-repair", action="store_true", help="Disable LLM self-healing repair loop")
    parser.add_argument("--strict-vlm-gate", action="store_true", help="Treat VLM QA visual defects as fatal blocking failures")
    args = parser.parse_args()

    if args.strict_vlm_gate:
        os.environ["STRICT_VLM_GATE"] = "1"
    else:
        os.environ.setdefault("STRICT_VLM_GATE", "0")

    workflow_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(workflow_dir)
    timing_adjustment_tracker = os.path.join(parent_dir, "ppt_trackers", "21_timing_adjustment_tracker.json")
    final_render_tracker = os.path.join(parent_dir, "ppt_trackers", "22_final_render_tracker.json")
    data_dir = os.path.join(parent_dir, "output") if os.path.exists(os.path.join(parent_dir, "output")) else (os.path.join(parent_dir, "data_ppt_advanced") if os.path.exists(os.path.join(parent_dir, "data_ppt_advanced")) else os.path.abspath("."))
    stage = FinalCodeExecution(
        input_tracker_path=timing_adjustment_tracker,
        output_tracker_path=final_render_tracker,
        input_folder=data_dir,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        no_repair=args.no_repair
    )
    stage.process_files(target_topic_id=args.topic, force=args.force, target_group=args.group)