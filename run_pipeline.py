#!/usr/bin/env python3
"""
================================================================================
SIMPLILEARN OSL 3.0 & KPLOR PARALLEL PIPELINE ORCHESTRATOR
================================================================================
Asynchronous, streaming multi-process pipeline orchestrator for Simplilearn
educational video post-production.

Features:
- Streaming Parallel Worker Pool: Videos and topic folders execute independently
  without global barrier lockstep. Video A can be on Stage 11 (Manim Render)
  while Video B is on Stage 5 (Audio Generation) and Video C is on Stage 1
  (Instructional Design).
- Dedicated Manim Rendering Semaphore: Limits concurrent Manim renders to
  prevent CPU/GPU saturation and thread thrashing while non-render stages
  (LLM reasoning, audio generation, image generation) run uninhibited.
- Process-Level Stage Isolation: Every stage executes inside a dedicated child
  process, ensuring zero memory leaks, process isolation, and clean crash containment.
- Concurrency-Safe Trackers: Thread-safe and process-safe atomic tracker writes
  utilizing file locking (portalocker) and atomic replace buffers.
- Video Preprocessing Pipeline (Stages 0A to 0D): Automatically handles raw
  teacher videos in input/ (audio cleaning, transcription, filler cuts, AV trim)
  and initializes topic directories.
- Presentation Stages (Stages 0 to 23): Complete 24-stage pedagogical, Manim
  code generation, VLM diagnostic review, styling correction, and SME composite assembly.
- Live Terminal Dashboard: Real-time status display monitoring worker state, active
  topic, running stage, elapsed duration, and completed/failed counts.
================================================================================
"""

import os
import re
import sys
import json
import time
import queue
import signal
import argparse
import traceback
import subprocess
import importlib.util
import multiprocessing
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path Resolutions
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
STAGES_DIR = ROOT_DIR / "pipeline"
HELPERS_DIR = STAGES_DIR / "helpers"
DEFAULT_TRACKERS_DIR = ROOT_DIR / "ppt_trackers"
DEFAULT_LOGS_DIR = ROOT_DIR / "logs"
DEFAULT_INPUT_DIR = ROOT_DIR / "input"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "data_ppt_advanced" if (ROOT_DIR / "data_ppt_advanced").exists() else ROOT_DIR / "output"

for _p in [str(HELPERS_DIR), str(STAGES_DIR), str(ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv(ROOT_DIR / ".env")
load_dotenv()

try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False


# ---------------------------------------------------------------------------
# Stage Registry (Stages 0 to 23)
# ---------------------------------------------------------------------------
STAGE_DEFINITIONS = [
    {
        "index": 0,
        "phase": "hook_generation",
        "name": "Hook Generation",
        "file": "0_generate_hook.py",
        "class_name": "HookGenerator",
        "input_tracker": "0c_clean_fillers_tracker.json",
        "output_tracker": "0_hook_output_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 1,
        "phase": "instructional_design",
        "name": "Instructional Design",
        "file": "1_generate_instructional_design.py",
        "class_name": "InstructionalDesign",
        "input_tracker": "0_hook_output_tracker.json",
        "output_tracker": "1_instruction_design_output_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 2,
        "phase": "asset_classification",
        "name": "Asset Classification",
        "file": "2_asset_classification.py",
        "class_name": "AssetClassification",
        "input_tracker": "1_instruction_design_output_tracker.json",
        "output_tracker": "2_asset_class_output_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 3,
        "phase": "asset_construction",
        "name": "Asset Construction",
        "file": "3_asset_construction.py",
        "class_name": "AssetConstruction",
        "input_tracker": "2_asset_class_output_tracker.json",
        "output_tracker": "3_asset_construct_output_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 4,
        "phase": "image_prompt_generation",
        "name": "Image Prompting",
        "file": "4_image_prompt_generation.py",
        "class_name": "ImagePrompting",
        "input_tracker": "2_asset_class_output_tracker.json",
        "output_tracker": "4_prompt_images_output_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 5,
        "phase": "audio_runtime_manifest",
        "name": "Audio Runtime Manifest Population",
        "file": "5_populate_audio_runtime.py",
        "class_name": "PopulateAudioRunTime",
        "input_tracker": "1_instruction_design_output_tracker.json",
        "output_tracker": "5_audio_output_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 6,
        "phase": "presentation_composer",
        "name": "Presentation Composer",
        "file": "6_presentation_composer.py",
        "class_name": "PresentationComposer",
        "input_tracker": "5_audio_output_tracker.json",
        "output_tracker": "6_presentation_composer_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 7,
        "phase": "presentation_experience_planner",
        "name": "Experience Planner",
        "file": "7_presentation_experience_planner.py",
        "class_name": "PresentationExperiencePlanner",
        "input_tracker": "6_presentation_composer_tracker.json",
        "output_tracker": "7_experience_planner_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 8,
        "phase": "image_generator",
        "name": "Image Generation",
        "file": "8_image_generator.py",
        "class_name": "ImageGeneration",
        "input_tracker": "7_experience_planner_tracker.json",
        "output_tracker": "8_image_generation_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 9,
        "phase": "styling_generator",
        "name": "Styling Generation",
        "file": "9_styling_generator.py",
        "class_name": "StylingGenerator",
        "input_tracker": "8_image_generation_tracker.json",
        "output_tracker": "9_styling_output_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 10,
        "phase": "manim_code_generation",
        "name": "Code Generation",
        "file": "10_generate_code.py",
        "class_name": "CodeGenerator",
        "input_tracker": "9_styling_output_tracker.json",
        "output_tracker": "10_code_generation_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 11,
        "phase": "manim_feedback_run",
        "name": "Manim Feedback Run",
        "file": "11_run_manim_for_feedback.py",
        "class_name": "RunManimForFeedback",
        "input_tracker": "10_code_generation_tracker.json",
        "output_tracker": "11_run_manim_feedback_tracker.json",
        "is_manim_render": True,
        "needs_keys": True,
    },
    {
        "index": 12,
        "phase": "feedback_report",
        "name": "Feedback Report",
        "file": "12_generate_feedback_report.py",
        "class_name": "GenerateFeedbackReport",
        "input_tracker": "11_run_manim_feedback_tracker.json",
        "output_tracker": "12_generate_feedback_tracker.json",
        "is_manim_render": False,
        "needs_keys": False,
    },
    {
        "index": 13,
        "phase": "suggest_corrections",
        "name": "Correction Suggestions",
        "file": "13_generate_corrections.py",
        "class_name": "SuggestCorrections",
        "input_tracker": "12_generate_feedback_tracker.json",
        "output_tracker": "13_suggest_corrections_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 14,
        "phase": "implement_corrections",
        "name": "Implement Corrections",
        "file": "14_implement_corrections.py",
        "class_name": "ImplementCodeCorrections",
        "input_tracker": "13_suggest_corrections_tracker.json",
        "output_tracker": "14_corrections_implement_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 15,
        "phase": "manim_vlm_feedback",
        "name": "Manim VLM Feedback Run",
        "file": "15_run_manim_vlm_feedback.py",
        "class_name": "RunManimForVLMFeedback",
        "input_tracker": "14_corrections_implement_tracker.json",
        "output_tracker": "15_run_manim_vlm_feedback_tracker.json",
        "is_manim_render": True,
        "needs_keys": True,
    },
    {
        "index": 16,
        "phase": "generate_vlm_report",
        "name": "Generate VLM Report",
        "file": "16_generate_vlm_feedback_report.py",
        "class_name": "GenerateVLMFeedbackReport",
        "input_tracker": "15_run_manim_vlm_feedback_tracker.json",
        "output_tracker": "16_generate_vlm_feedback_tracker.json",
        "is_manim_render": False,
        "needs_keys": False,
    },
    {
        "index": 17,
        "phase": "visual_triangulation",
        "name": "Visual Triangulation",
        "file": "17_generate_visual_triangulation.py",
        "class_name": "GridVisualTriangulation",
        "input_tracker": "16_generate_vlm_feedback_tracker.json",
        "output_tracker": "17_generate_triangulation_tracker.json",
        "is_manim_render": False,
        "needs_keys": False,
    },
    {
        "index": 18,
        "phase": "vlm_fix_suggestor",
        "name": "VLM Review Feedback",
        "file": "18_vlm_fix_suggestor.py",
        "class_name": "SuggestionsFromVLM",
        "input_tracker": "17_generate_triangulation_tracker.json",
        "output_tracker": "18_vlm_fix_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 19,
        "phase": "vlm_fixing_stage",
        "name": "VLM Timestamped Fix Generator",
        "file": "19_vlm_fixing_stage.py",
        "class_name": "VLMTimestampedFixStage",
        "input_tracker": "18_vlm_fix_tracker.json",
        "output_tracker": "19_vlm_fixing_stage_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 20,
        "phase": "final_styling_corrections",
        "name": "Final Styling & Code Fixes",
        "file": "20_final_styling_corrections.py",
        "class_name": "FinalStylingCorrections",
        "input_tracker": "19_vlm_fixing_stage_tracker.json",
        "output_tracker": "20_eng_corrections_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 21,
        "phase": "timing_adjustments",
        "name": "Timing Adjustments",
        "file": "21_timing_adjustments.py",
        "class_name": "GenerateTimingAdjustments",
        "input_tracker": "20_eng_corrections_tracker.json",
        "output_tracker": "21_timing_adjustment_tracker.json",
        "is_manim_render": False,
        "needs_keys": True,
    },
    {
        "index": 22,
        "phase": "final_code_run",
        "name": "Final Render",
        "file": "22_final_code_run.py",
        "class_name": "FinalCodeExecution",
        "input_tracker": "21_timing_adjustment_tracker.json",
        "output_tracker": "22_final_render_tracker.json",
        "is_manim_render": True,
        "needs_keys": True,
    },
    {
        "index": 23,
        "phase": "post_production",
        "name": "Post-Production SME Integration",
        "file": "23_sme_post_production.py",
        "class_name": "SMEPostProduction",
        "input_tracker": "22_final_render_tracker.json",
        "output_tracker": "23_sme_post_production_tracker.json",
        "is_manim_render": False,
        "needs_keys": False,
    },
]

PHASE_LOOKUP = {s["phase"]: s["index"] for s in STAGE_DEFINITIONS}


# ---------------------------------------------------------------------------
# Dynamic Class Loader
# ---------------------------------------------------------------------------
def load_class_from_file(file_path: str, class_name: str):
    """Dynamically imports a class from a file path with fallback resolution."""
    fpath = Path(file_path)
    if not fpath.is_absolute():
        candidate_stages = STAGES_DIR / file_path
        candidate_helpers = HELPERS_DIR / file_path
        if candidate_stages.exists():
            fpath = candidate_stages
        elif candidate_helpers.exists():
            fpath = candidate_helpers

    if not fpath.exists():
        fname = fpath.name
        unprefixed = re.sub(r'^\d+[a-z]?_', '', fname)
        for cand in [STAGES_DIR / unprefixed, HELPERS_DIR / unprefixed]:
            if cand.exists():
                fpath = cand
                break

    if not fpath.exists():
        raise FileNotFoundError(f"Cannot resolve pipeline stage module: {file_path}")

    mod_name = re.sub(r'\W|^(?=\d)', '_', fpath.stem)
    spec = importlib.util.spec_from_file_location(mod_name, str(fpath))
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


# ---------------------------------------------------------------------------
# Tracker Concurrency Helpers
# ---------------------------------------------------------------------------
def is_stage_completed(tracker_file_path: str, topic_id: str) -> bool:
    """Checks whether topic_id is marked processed: True in the tracker file."""
    if not os.path.exists(tracker_file_path):
        return False
    try:
        with open(tracker_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            entry = data.get(topic_id)
            if entry and isinstance(entry, dict) and (entry.get("processed") is True or entry.get("status") == "COMPLETED"):
                return True
    except Exception:
        pass
    return False


def get_stage_failure_reason(tracker_file_path: str, topic_id: str) -> Optional[str]:
    """Retrieves failure reason from tracker if present."""
    if not os.path.exists(tracker_file_path):
        return None
    try:
        with open(tracker_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            entry = data.get(topic_id)
            if entry and isinstance(entry, dict):
                return entry.get("failure_reason")
    except Exception:
        pass
    return None


def record_stage_completed(tracker_file_path: str, topic_id: str, output_path: Any, topic_name: Optional[str] = None):
    """Records a completed stage entry into tracker file with locking."""
    lock_path = tracker_file_path + ".lock"
    tracker_dir = os.path.dirname(tracker_file_path)
    if tracker_dir and not os.path.exists(tracker_dir):
        os.makedirs(tracker_dir, exist_ok=True)

    def _update():
        current = {}
        if os.path.exists(tracker_file_path):
            try:
                with open(tracker_file_path, "r", encoding="utf-8") as f:
                    current = json.load(f)
            except Exception:
                current = {}
        current[topic_id] = {
            "output_path": str(output_path),
            "processed": True,
            "topic_name": topic_name or topic_id,
            "topic_id": topic_id,
            "completed_at": datetime.now().isoformat(),
        }
        tmp = tracker_file_path + f".tmp.{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=4, ensure_ascii=False)
        os.replace(tmp, tracker_file_path)

    try:
        if HAS_PORTALOCKER:
            with portalocker.Lock(lock_path, timeout=60):
                _update()
        else:
            _update()
    except Exception as e:
        print(f"[Error] Failed to record completion to {tracker_file_path}: {e}")


def record_stage_failure(tracker_file_path: str, topic_id: str, reason: str, topic_name: Optional[str] = None):
    """Records a failure entry into tracker file with locking."""
    lock_path = tracker_file_path + ".lock"
    tracker_dir = os.path.dirname(tracker_file_path)
    if tracker_dir and not os.path.exists(tracker_dir):
        os.makedirs(tracker_dir, exist_ok=True)

    def _update():
        current = {}
        if os.path.exists(tracker_file_path):
            try:
                with open(tracker_file_path, "r", encoding="utf-8") as f:
                    current = json.load(f)
            except Exception:
                current = {}
        current[topic_id] = {
            "output_path": None,
            "processed": False,
            "topic_name": topic_name or topic_id,
            "topic_id": topic_id,
            "failure_reason": str(reason),
            "failed_at": datetime.now().isoformat(),
        }
        tmp = tracker_file_path + f".tmp.{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=4, ensure_ascii=False)
        os.replace(tmp, tracker_file_path)

    try:
        if HAS_PORTALOCKER:
            with portalocker.Lock(lock_path, timeout=60):
                _update()
        else:
            _update()
    except Exception as e:
        print(f"[Error] Failed to record failure to {tracker_file_path}: {e}")


# ---------------------------------------------------------------------------
# Topic Configuration and Workspace Preparation
# ---------------------------------------------------------------------------
def self_heal_topic_config(topic_folder: str, topic_id: Optional[str] = None, lesson_title: Optional[str] = None):
    """Ensures ex_config.json base_folder and metadata correctly point to topic folder."""
    config_file = os.path.join(topic_folder, "ex_config.json")
    expected_base = os.path.abspath(topic_folder)
    current_data = {}

    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception:
            current_data = {}

    tid = topic_id or os.path.basename(topic_folder)
    title = lesson_title or current_data.get("lesson_title") or tid.replace("_", " ").title()

    needs_update = False
    defaults = {
        "theme": "dynamic_learning",
        "scene_coding_vendor": "google",
        "scene_coding_model_name": "gemini-3.8-flash",
        "styling_vendor": "google",
        "styling_model_name": "gemini-3.8-flash",
        "asset_class_vendor": "google",
        "asset_class_model_name": "gemini-3.8-flash",
    }
    for k, v in defaults.items():
        if k not in current_data:
            current_data[k] = v
            needs_update = True

    if current_data.get("base_folder") != expected_base:
        current_data["base_folder"] = expected_base
        needs_update = True
    if "video_id" not in current_data:
        current_data["video_id"] = tid
        needs_update = True
    if "lesson_title" not in current_data:
        current_data["lesson_title"] = title
        needs_update = True

    if needs_update or not os.path.exists(config_file):
        try:
            tmp = config_file + f".tmp.{os.getpid()}"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(current_data, f, indent=4, ensure_ascii=False)
            os.replace(tmp, config_file)
        except Exception as e:
            print(f"[Config Warning] Could not write config {config_file}: {e}")


def ensure_topic_folder_structure(topic_folder: str):
    """Initializes required subdirectories for a topic."""
    subdirs = [
        "manim_codes",
        "manim_raw_videos",
        "correction_insights",
        "correction_insights_vlm",
        "llm_error_reports",
        "llm_error_reports_vlm",
        "manim_extracted_codes",
        "manim_extracted_videos",
        "manim_styled_codes",
        "manim_time_synced_code",
        "manim_time_synced_videos",
        "audio_integrated_videos",
        "audio_elements",
        "vlm_inputs",
        "visual_triangulation",
        "specific_suggestions",
        "specific_suggestions_vlm",
        "vlm_fixing_stage",
        "manim_videos",
        "images",
        "temp_audio",
        "temp_assembly",
    ]
    for d in subdirs:
        os.makedirs(os.path.join(topic_folder, d), exist_ok=True)

    ca_symlink = os.path.join(topic_folder, "Creative_Assets")
    gold_standard_ca = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline", "helpers", "Creative_Assets")
    if os.path.islink(ca_symlink) and os.readlink(ca_symlink) == "images":
        try:
            os.unlink(ca_symlink)
        except Exception:
            pass
    if not os.path.exists(ca_symlink) and os.path.exists(gold_standard_ca):
        try:
            os.symlink(gold_standard_ca, ca_symlink)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Video Preprocessing Runner (Stages 0A to 0D)
# ---------------------------------------------------------------------------
def run_video_preprocessing(
    video_path: str,
    topic_folder: str,
    topic_id: str,
    trackers_dir: str,
    api_provider: str = "auto",
    whisper_engine: str = "auto",
    whisper_model: str = "base"
) -> bool:
    """
    Executes Stages 0A through 0D on raw teacher video in an isolated flow.
    """
    clean_audio_path = os.path.join(topic_folder, f"{topic_id}_clean_audio.mp4")
    timestamps_path = os.path.join(topic_folder, f"{topic_id}_timestamps.json")
    decisions_path = os.path.join(topic_folder, f"{topic_id}_step2_decisions.json")
    clean_transcript_path = os.path.join(topic_folder, f"{topic_id}_clean_transcript.json")
    trimmed_video_path = os.path.join(topic_folder, f"{topic_id}_trimmed.mp4")

    trk_0a = os.path.join(trackers_dir, "0a_audio_cleaner_tracker.json")
    trk_0b = os.path.join(trackers_dir, "0b_transcription_tracker.json")
    trk_0c = os.path.join(trackers_dir, "0c_clean_fillers_tracker.json")
    trk_0d = os.path.join(trackers_dir, "0d_av_trimmer_tracker.json")

    def run_sub(script_name: str, args: List[str]):
        script = STAGES_DIR / script_name
        cmd = [sys.executable, str(script)] + args
        env = os.environ.copy()
        pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{STAGES_DIR}:{HELPERS_DIR}:{ROOT_DIR}:{pythonpath}".strip(":")
        res = subprocess.run(cmd, env=env, cwd=str(ROOT_DIR))
        if res.returncode != 0:
            raise RuntimeError(f"Preprocessing failed at {script_name} (code {res.returncode})")

    # 0A: Audio Cleaner
    if os.environ.get("FORCE_RUN") == "1" or not is_stage_completed(trk_0a, topic_id):
        print(f"[{topic_id}] Running Stage 0A: Audio Cleaner...")
        try:
            run_sub("0a_audio_cleaner.py", ["-i", video_path, "-o", clean_audio_path, "-p", api_provider])
            record_stage_completed(trk_0a, topic_id, clean_audio_path)
        except Exception as e:
            record_stage_failure(trk_0a, topic_id, str(e))
            raise

    # 0B: Speech Transcription
    if os.environ.get("FORCE_RUN") == "1" or not is_stage_completed(trk_0b, topic_id):
        input_media = clean_audio_path if os.path.exists(clean_audio_path) else video_path
        print(f"[{topic_id}] Running Stage 0B: Speech Transcription...")
        try:
            run_sub("0b_transcription.py", ["-i", input_media, "-o", timestamps_path, "-e", whisper_engine, "-m", whisper_model])
            record_stage_completed(trk_0b, topic_id, timestamps_path)
        except Exception as e:
            record_stage_failure(trk_0b, topic_id, str(e))
            raise

    # 0C: Clean Fillers & Retakes
    if os.environ.get("FORCE_RUN") == "1" or not is_stage_completed(trk_0c, topic_id):
        input_media = clean_audio_path if os.path.exists(clean_audio_path) else video_path
        print(f"[{topic_id}] Running Stage 0C: Clean Fillers & Retakes...")
        try:
            run_sub("0c_clean_fillers_and_retakes.py", [
                "-i", input_media,
                "-t", timestamps_path,
                "-d", decisions_path,
                "-c", clean_transcript_path,
                "-p", api_provider
            ])
            record_stage_completed(trk_0c, topic_id, clean_transcript_path)
        except Exception as e:
            record_stage_failure(trk_0c, topic_id, str(e))
            raise

    # 0D: AV Trimmer
    if os.environ.get("FORCE_RUN") == "1" or not is_stage_completed(trk_0d, topic_id):
        input_media = clean_audio_path if os.path.exists(clean_audio_path) else video_path
        print(f"[{topic_id}] Running Stage 0D: Synchronous AV Trimmer...")
        try:
            run_sub("0d_av_trimmer.py", [
                "-i", input_media,
                "-d", decisions_path,
                "-o", trimmed_video_path,
                "-p", api_provider
            ])
            record_stage_completed(trk_0d, topic_id, trimmed_video_path)
        except Exception as e:
            record_stage_failure(trk_0d, topic_id, str(e))
            raise

    # Extract raw_context.txt if needed
    raw_ctx_path = os.path.join(topic_folder, "raw_context.txt")
    if not os.path.exists(raw_ctx_path) and os.path.exists(clean_transcript_path):
        try:
            with open(clean_transcript_path, "r", encoding="utf-8") as f:
                t_data = json.load(f)
            lines = []
            if isinstance(t_data, list):
                lines = [item.get("text", "") for item in t_data if isinstance(item, dict)]
            elif isinstance(t_data, dict):
                lines = [item.get("text", "") for item in t_data.get("segments", [])]
            if lines:
                with open(raw_ctx_path, "w", encoding="utf-8") as f:
                    f.write(" ".join(lines))
        except Exception:
            pass

    return True


# ---------------------------------------------------------------------------
# Child Process Stage Runner (Process-Isolated Execution)
# ---------------------------------------------------------------------------
def _child_stage_execution(
    stage_idx: int,
    topic_id: str,
    data_dir: str,
    trackers_dir: str,
    google_key: Optional[str],
    claude_key: Optional[str],
    log_file_path: str,
    result_pipe: Any,
):
    """
    Dedicated child process worker. Redirects stdout/stderr to a topic-stage log file,
    instantiates the stage class, invokes process_files(target_topic_id=topic_id),
    and communicates completion back via result_pipe.
    """
    log_f = None
    try:
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        log_f = open(log_file_path, "a", encoding="utf-8", buffering=1)
        sys.stdout = log_f
        sys.stderr = log_f

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stage_def = STAGE_DEFINITIONS[stage_idx]
        stage_name = stage_def["name"]
        print(f"[{timestamp}] === Starting Stage {stage_idx}: {stage_name} for topic {topic_id} ===")

        file_path = STAGES_DIR / stage_def["file"]
        if not file_path.exists():
            file_path = HELPERS_DIR / stage_def["file"]
        class_name = stage_def["class_name"]

        out_tracker = os.path.join(trackers_dir, stage_def["output_tracker"])
        in_tracker = (
            os.path.join(trackers_dir, stage_def["input_tracker"])
            if stage_def["input_tracker"]
            else None
        )

        cls = load_class_from_file(str(file_path), class_name)

        if stage_idx == 0:
            stage_instance = cls(
                input_folder=data_dir,
                google_api_key=google_key,
                claude_api_key=claude_key,
                tracker_file=out_tracker,
            )
        elif not stage_def["needs_keys"]:
            stage_instance = cls(
                input_tracker_path=in_tracker,
                output_tracker_path=out_tracker,
                input_folder=data_dir,
            )
        else:
            stage_kwargs = {
                "input_tracker_path": in_tracker,
                "output_tracker_path": out_tracker,
                "google_api_key": google_key,
                "claude_api_key": claude_key,
                "input_folder": data_dir,
            }
            if stage_idx == 22 and os.environ.get("NO_REPAIR", "0") == "1":
                stage_kwargs["no_repair"] = True
            try:
                stage_instance = cls(**stage_kwargs)
            except TypeError:
                stage_kwargs.pop("no_repair", None)
                stage_instance = cls(**stage_kwargs)

        try:
            stage_instance.process_files(target_topic_id=topic_id)
        except TypeError:
            stage_instance.process_files()

        if is_stage_completed(out_tracker, topic_id):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === Stage {stage_idx} Succeeded ===")
            result_pipe.send((True, None))
        else:
            reason = get_stage_failure_reason(out_tracker, topic_id) or "Stage executed without marked completion in tracker"
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === Stage {stage_idx} Failed: {reason} ===")
            result_pipe.send((False, reason))

    except Exception as e:
        tb = traceback.format_exc()
        if log_f:
            print(f"Exception during stage execution:\n{tb}")
        result_pipe.send((False, f"{str(e)}\n{tb}"))
    finally:
        if log_f and not log_f.closed:
            log_f.flush()
            log_f.close()


def run_stage_in_isolated_process(
    stage_idx: int,
    topic_id: str,
    data_dir: str,
    trackers_dir: str,
    google_key: Optional[str],
    claude_key: Optional[str],
    log_file_path: str,
) -> Tuple[bool, Optional[str]]:
    """Spawns an isolated child process to execute one stage, waits, and collects result."""
    parent_conn, child_conn = multiprocessing.Pipe()
    p = multiprocessing.Process(
        target=_child_stage_execution,
        args=(
            stage_idx,
            topic_id,
            data_dir,
            trackers_dir,
            google_key,
            claude_key,
            log_file_path,
            child_conn,
        ),
    )
    p.start()
    p.join()

    if parent_conn.poll():
        success, err = parent_conn.recv()
        return success, err
    else:
        if p.exitcode != 0:
            return False, f"Child process crashed with exit code {p.exitcode}"
        return False, "Child process finished without reporting result"


# ---------------------------------------------------------------------------
# Priority Queue Computation
# ---------------------------------------------------------------------------
def compute_item_priority(
    item: Dict[str, Any],
    trackers_dir: str,
    start_stage: int,
    end_stage: int
) -> Dict[str, Any]:
    """Computes scheduling priority metadata for each topic/video."""
    topic_id = item["topic_id"]
    if os.environ.get("FORCE_RUN") == "1":
        highest_completed = start_stage - 1
    else:
        highest_completed = -1
        for s_idx in range(end_stage, start_stage - 1, -1):
            s_def = STAGE_DEFINITIONS[s_idx]
            out_trk = os.path.join(trackers_dir, s_def["output_tracker"])
            if is_stage_completed(out_trk, topic_id):
                highest_completed = s_idx
                break

    is_incomplete = (highest_completed < end_stage)
    is_w6 = 1 if "W6" in topic_id.upper() else 0
    next_stage = start_stage if highest_completed < start_stage else highest_completed + 1

    return {
        **item,
        "is_incomplete": is_incomplete,
        "is_w6": is_w6,
        "highest_completed": highest_completed,
        "next_stage": next_stage,
    }


# ---------------------------------------------------------------------------
# Parallel Worker Loop
# ---------------------------------------------------------------------------
def topic_worker_loop(
    worker_id: int,
    work_queue: multiprocessing.Queue,
    stage_range: Tuple[int, int],
    manim_semaphore: multiprocessing.Semaphore,
    status_dict: Dict[int, Any],
    completed_counter: multiprocessing.Value,
    failed_counter: multiprocessing.Value,
    data_dir: str,
    trackers_dir: str,
    logs_dir: str,
    google_key: Optional[str],
    claude_key: Optional[str],
    stage_retries: int = 2,
    folder_retries: int = 1,
    folder_retry_counts: Optional[Dict[str, int]] = None,
):
    """
    Pops items from work_queue and runs each through the requested pipeline stages.
    Enforces independent progression: each topic moves through stages at its own pace.
    """
    start_stage, end_stage = stage_range
    if folder_retry_counts is None:
        folder_retry_counts = {}

    while True:
        try:
            item = work_queue.get(timeout=3)
        except (queue.Empty, TimeoutError, Exception):
            break

        topic_id = item["topic_id"]
        topic_folder = item["topic_folder"]
        is_video_input = item.get("is_video", False)
        video_path = item.get("video_path")

        os.makedirs(topic_folder, exist_ok=True)
        ensure_topic_folder_structure(topic_folder)
        self_heal_topic_config(topic_folder, topic_id=topic_id)

        # Worker file lock per topic
        lock_file = os.path.join(topic_folder, ".worker_lock")
        lock_acquired = False
        if os.path.exists(lock_file):
            try:
                with open(lock_file, "r") as lf:
                    locked_pid = int(lf.read().strip())
                os.kill(locked_pid, 0)
                print(f"[Worker {worker_id}] [{topic_id}] Topic locked by active PID {locked_pid}. Deferring.")
                work_queue.put(item)
                time.sleep(2)
                continue
            except (OSError, ValueError):
                pass

        try:
            with open(lock_file, "w") as lf:
                lf.write(str(os.getpid()))
            lock_acquired = True
        except Exception:
            pass

        try:
            print(f"\n[Worker {worker_id}] >>> Claimed Topic: {topic_id} <<<")
            topic_failed = False
            requeued = False

            # Run Video Preprocessing (0A - 0D) if raw video was supplied
            if is_video_input and video_path and os.path.exists(video_path):
                trimmer_tracker = os.path.join(trackers_dir, "0d_av_trimmer_tracker.json")
                if start_stage == 0 or not is_stage_completed(trimmer_tracker, topic_id):
                    status_dict[worker_id] = {
                        "topic": topic_id,
                        "stage_idx": "0a-0d",
                        "stage_name": "Video Preprocessing",
                        "start_time": time.time(),
                        "state": "preprocessing",
                    }
                    try:
                        run_video_preprocessing(
                            video_path=video_path,
                            topic_folder=topic_folder,
                            topic_id=topic_id,
                            trackers_dir=trackers_dir,
                        )
                    except Exception as e:
                        print(f"[Worker {worker_id}] [{topic_id}] Preprocessing failed: {e}")
                        with failed_counter.get_lock():
                            failed_counter.value += 1
                        continue

            # Run Requested Pedagogical, Code, Diagnostic & Render Stages (0 to 23)
            for stage_idx in range(start_stage, end_stage + 1):
                stage_def = STAGE_DEFINITIONS[stage_idx]
                stage_name = stage_def["name"]
                out_tracker = os.path.join(trackers_dir, stage_def["output_tracker"])
                in_tracker = (
                    os.path.join(trackers_dir, stage_def["input_tracker"])
                    if stage_def["input_tracker"]
                    else None
                )

                status_dict[worker_id] = {
                    "topic": topic_id,
                    "stage_idx": stage_idx,
                    "stage_name": stage_name,
                    "start_time": time.time(),
                    "state": "running",
                }

                # Idempotency check: skip finished stages unless force
                if os.environ.get("FORCE_RUN") != "1" and is_stage_completed(out_tracker, topic_id):
                    print(f"[Worker {worker_id}] [{topic_id}] Stage {stage_idx} ({stage_name}) already completed. Skipping.")
                    continue

                # Prerequisite check
                if in_tracker and not is_stage_completed(in_tracker, topic_id):
                    err = f"Prerequisite tracker {os.path.basename(in_tracker)} not completed for {topic_id}"
                    print(f"[Worker {worker_id}] [{topic_id}] [ERROR] {err}")
                    record_stage_failure(out_tracker, topic_id, err)
                    topic_failed = True
                    break

                is_manim = stage_def["is_manim_render"]
                log_file = os.path.join(
                    logs_dir,
                    topic_id,
                    f"stage_{stage_idx:02d}_{stage_name.replace(' ', '_').lower()}.log",
                )

                stage_start_t = time.time()
                success = False
                err_msg = ""
                total_attempts = stage_retries + 1

                for attempt in range(1, total_attempts + 1):
                    if attempt > 1:
                        wait_sec = 5 * (attempt - 1)
                        print(
                            f"[Worker {worker_id}] [{topic_id}] [RETRY] Stage {stage_idx} ({stage_name}) "
                            f"failed attempt {attempt-1}. Retrying ({attempt}/{total_attempts}) in {wait_sec}s..."
                        )
                        time.sleep(wait_sec)

                    if is_manim:
                        status_dict[worker_id] = {
                            "topic": topic_id,
                            "stage_idx": stage_idx,
                            "stage_name": stage_name,
                            "start_time": time.time(),
                            "state": "waiting_manim_slot",
                        }
                        print(f"[Worker {worker_id}] [{topic_id}] Waiting for Manim render slot for Stage {stage_idx}...")
                        manim_semaphore.acquire()
                        status_dict[worker_id]["state"] = "rendering_manim"
                        print(f"[Worker {worker_id}] [{topic_id}] Acquired Manim render slot. Starting render...")

                    print(f"[Worker {worker_id}] [{topic_id}] -> Starting Stage {stage_idx}: {stage_name} (attempt {attempt}/{total_attempts})...")

                    try:
                        success, err_msg = run_stage_in_isolated_process(
                            stage_idx=stage_idx,
                            topic_id=topic_id,
                            data_dir=data_dir,
                            trackers_dir=trackers_dir,
                            google_key=google_key,
                            claude_key=claude_key,
                            log_file_path=log_file,
                        )
                    finally:
                        if is_manim:
                            manim_semaphore.release()
                            print(f"[Worker {worker_id}] [{topic_id}] Released Manim slot for Stage {stage_idx}.")

                    if success:
                        break

                elapsed = time.time() - stage_start_t
                if success:
                    print(f"[Worker {worker_id}] [{topic_id}] [SUCCESS] Stage {stage_idx} ({stage_name}) completed in {elapsed:.1f}s.")
                else:
                    print(f"[Worker {worker_id}] [{topic_id}] [FAILED] Stage {stage_idx} ({stage_name}) failed after {total_attempts} attempts ({elapsed:.1f}s).")
                    print(f"[Worker {worker_id}] [{topic_id}] Failure Reason: {err_msg}")
                    print(f"[Worker {worker_id}] [{topic_id}] Log file: {log_file}")

                    cur_retries = folder_retry_counts.get(topic_id, 0)
                    if cur_retries < folder_retries:
                        folder_retry_counts[topic_id] = cur_retries + 1
                        print(f"[Worker {worker_id}] [{topic_id}] Re-queuing topic for deferred retry pass {cur_retries + 1}/{folder_retries}...")
                        work_queue.put(item)
                        requeued = True
                        break
                    else:
                        record_stage_failure(out_tracker, topic_id, err_msg)
                        topic_failed = True
                        break

            if requeued:
                print(f"[Worker {worker_id}] Topic {topic_id} re-queued. Worker proceeding to next topic.")
            elif topic_failed:
                with failed_counter.get_lock():
                    failed_counter.value += 1
                print(f"[Worker {worker_id}] [ISOLATED] Topic {topic_id} failed after all retries and was isolated.")
            else:
                with completed_counter.get_lock():
                    completed_counter.value += 1
                print(f"\n[Worker {worker_id}] ============================================================")
                print(f"[Worker {worker_id}] ALL REQUESTED STAGES COMPLETED FOR {topic_id}!")
                print(f"[Worker {worker_id}] ============================================================\n")

        finally:
            if lock_acquired and os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except Exception:
                    pass

    status_dict[worker_id] = {
        "topic": "IDLE",
        "stage_idx": None,
        "stage_name": "Finished",
        "start_time": time.time(),
        "state": "idle",
    }


# ---------------------------------------------------------------------------
# Dashboard Monitor
# ---------------------------------------------------------------------------
def print_dashboard_banner(
    status_dict: Dict[int, Any],
    total_topics: int,
    completed_counter: multiprocessing.Value,
    failed_counter: multiprocessing.Value,
    num_workers: int,
    max_manim: Optional[int] = None,
    trackers_dir: Optional[str] = None
):
    """Renders formatted ASCII status dashboard of parallel worker progress."""
    term_width = 80
    print("\n" + "=" * term_width)
    completed = completed_counter.value
    failed = failed_counter.value
    manim_info = f" | Max Manim: {max_manim}" if max_manim is not None else ""
    print(
        f" PARALLEL PIPELINE DASHBOARD | Workers: {num_workers}{manim_info} | "
        f"Progress: {completed}/{total_topics} Completed | Failed: {failed}"
    )
    print("=" * term_width)

    for wid in sorted(status_dict.keys()):
        st = status_dict[wid]
        topic = st.get("topic", "IDLE")
        stage_name = st.get("stage_name", "")
        stage_idx = st.get("stage_idx")
        state = st.get("state", "idle")
        elapsed_sec = int(time.time() - st.get("start_time", time.time()))
        elapsed_str = f"{elapsed_sec // 60:02d}m {elapsed_sec % 60:02d}s"

        if state == "idle":
            line = f" [Worker {wid}] IDLE"
        elif state == "waiting_manim_slot":
            line = f" [Worker {wid}] {topic} -> Stage {stage_idx}: {stage_name} [WAITING FOR MANIM SLOT] ({elapsed_str})"
        elif state == "rendering_manim":
            line = f" [Worker {wid}] {topic} -> Stage {stage_idx}: {stage_name} [RENDERING MANIM] ({elapsed_str})"
        elif state == "preprocessing":
            line = f" [Worker {wid}] {topic} -> [VIDEO PREPROCESSING 0A-0D] ({elapsed_str})"
        else:
            line = f" [Worker {wid}] {topic} -> Stage {stage_idx}: {stage_name} [RUNNING] ({elapsed_str})"
        print(line[:term_width])

    if failed > 0 and trackers_dir and os.path.exists(trackers_dir):
        failures = []
        for s_idx, s_def in enumerate(STAGE_DEFINITIONS):
            tr_path = os.path.join(trackers_dir, s_def["output_tracker"])
            if os.path.exists(tr_path):
                try:
                    with open(tr_path, "r", encoding="utf-8") as f:
                        tr_data = json.load(f)
                    for top_id, top_info in tr_data.items():
                        if isinstance(top_info, dict) and top_info.get("processed") is False:
                            reason = (top_info.get("failure_reason") or "Failed").split("\n")[0][:45]
                            failures.append(f"  [FAIL] {top_id} -> Stage {s_idx} ({s_def['name']}): {reason}")
                except Exception:
                    pass
        if failures:
            print("-" * term_width)
            print(" FAILED / ISOLATED TOPICS:")
            for f_line in failures:
                print(f_line[:term_width])

    print("=" * term_width + "\n")


# ---------------------------------------------------------------------------
# Status Inspection CLI Mode
# ---------------------------------------------------------------------------
def display_tracker_status(trackers_dir: str, data_dir: str):
    """Displays structured matrix of all known topics and stage completion statuses."""
    print("=" * 80)
    print(" SIMPLILEARN PIPELINE STAGE TRACKER STATUS")
    print("=" * 80)
    if not os.path.exists(trackers_dir):
        print(f"Trackers directory not found: {trackers_dir}")
        return

    # Collect all topic IDs from trackers
    all_topics = set()
    for s_def in STAGE_DEFINITIONS:
        tr_file = os.path.join(trackers_dir, s_def["output_tracker"])
        if os.path.exists(tr_file):
            try:
                with open(tr_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                all_topics.update(data.keys())
            except Exception:
                pass

    if os.path.exists(data_dir):
        for entry in os.scandir(data_dir):
            if entry.is_dir():
                all_topics.add(entry.name)

    if not all_topics:
        print("No topics found in trackers or data directory.")
        return

    sorted_topics = sorted(all_topics)
    print(f"Total Discovered Topics: {len(sorted_topics)}")
    print("-" * 80)

    for top in sorted_topics:
        completed_stages = []
        failed_stage = None
        for s_idx, s_def in enumerate(STAGE_DEFINITIONS):
            tr_file = os.path.join(trackers_dir, s_def["output_tracker"])
            if is_stage_completed(tr_file, top):
                completed_stages.append(s_idx)
            else:
                reason = get_stage_failure_reason(tr_file, top)
                if reason and not failed_stage:
                    failed_stage = (s_idx, s_def["name"], reason)

        highest = max(completed_stages) if completed_stages else -1
        total_stg = len(STAGE_DEFINITIONS)
        status_tag = f"COMPLETED ({highest + 1}/{total_stg})" if highest == total_stg - 1 else f"Stage {highest + 1}/{total_stg}"
        print(f"Topic: {top:<36} | Progress: {status_tag:<18}")
        if failed_stage:
            print(f"   [Failure at Stage {failed_stage[0]}: {failed_stage[1]}] -> {failed_stage[2][:50]}")

    print("=" * 80)


# ---------------------------------------------------------------------------
# Main Orchestrator Entry Point
# ---------------------------------------------------------------------------
def main():
    multiprocessing.set_start_method("spawn", force=True)

    parser = argparse.ArgumentParser(
        description="High-Performance Asynchronous Parallel Pipeline Orchestrator"
    )
    parser.add_argument(
        "-i", "--input", "--folders",
        nargs="+",
        dest="input_targets",
        default=None,
        help="Input video file(s), topic folder name(s), or input directory to process",
    )
    parser.add_argument(
        "-o", "--output", "--data-dir",
        dest="data_dir",
        default=None,
        help="Custom path to output data directory (default: data_ppt_advanced/ or output/)",
    )
    parser.add_argument(
        "--trackers-dir",
        type=str,
        default=None,
        help="Custom path to ppt_trackers/ folder",
    )
    parser.add_argument(
        "--logs-dir",
        type=str,
        default=None,
        help="Custom path to output logs/ folder",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of concurrent folder/video workers (default: 4)",
    )
    parser.add_argument(
        "--max-manim",
        type=int,
        default=2,
        help="Maximum concurrent Manim renders across all workers (default: 2)",
    )
    parser.add_argument(
        "--start-stage",
        type=int,
        default=0,
        help="Stage index to start from (0 to 23, default: 0)",
    )
    parser.add_argument(
        "--end-stage",
        type=int,
        default=23,
        help="Stage index to end at (0 to 23, default: 23)",
    )
    parser.add_argument(
        "--from-phase",
        type=str,
        default=None,
        help="Phase name to start from (e.g. hook_generation, manim_code_generation)",
    )
    parser.add_argument(
        "--to-phase",
        type=str,
        default=None,
        help="Phase name to end at (e.g. final_code_run, post_production)",
    )
    parser.add_argument(
        "--stage-retries",
        type=int,
        default=2,
        help="Automatic retries per failed stage (default: 2)",
    )
    parser.add_argument(
        "--folder-retries",
        type=int,
        default=1,
        help="Automatic deferred retries for a failed topic (default: 1)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-execution of stages even if marked completed in trackers",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Display pipeline status summary for all discovered topics and exit",
    )
    parser.add_argument(
        "--no-repair",
        action="store_true",
        help="Disable iterative LLM repair in Stage 22 (fast render)",
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Skip interactive review in Stage 1 and auto-approve",
    )
    parser.add_argument(
        "--strict-vlm-gate",
        action="store_true",
        help="Treat Stage 22 VLM visual audit defects as fatal errors",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip heavy diffusion image generation in Stage 8 and use lightweight vector placeholders",
    )

    args = parser.parse_args()

    # Workspace directory resolution
    data_dir = os.path.abspath(args.data_dir) if args.data_dir else str(DEFAULT_OUTPUT_DIR)
    trackers_dir = os.path.abspath(args.trackers_dir) if args.trackers_dir else str(DEFAULT_TRACKERS_DIR)
    logs_dir = os.path.abspath(args.logs_dir) if args.logs_dir else str(DEFAULT_LOGS_DIR)

    if args.status:
        display_tracker_status(trackers_dir=trackers_dir, data_dir=data_dir)
        sys.exit(0)

    if args.force:
        os.environ["FORCE_RUN"] = "1"
    if args.no_repair:
        os.environ["NO_REPAIR"] = "1"
    if args.no_review:
        os.environ["AUTO_APPROVE_INSTRUCTIONS"] = "1"
    if args.strict_vlm_gate:
        os.environ["STRICT_VLM_GATE"] = "1"
    if args.skip_images:
        os.environ["SKIP_IMAGES"] = "1"

    start_stage = args.start_stage
    end_stage = args.end_stage
    if args.from_phase and args.from_phase in PHASE_LOOKUP:
        start_stage = PHASE_LOOKUP[args.from_phase]
    if args.to_phase and args.to_phase in PHASE_LOOKUP:
        end_stage = PHASE_LOOKUP[args.to_phase]

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(trackers_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    google_key = os.environ.get("GOOGLE_API_KEY")
    claude_key = os.environ.get("CLAUDE_API_KEY")

    # Discover candidate work items (video files or topic directories)
    candidate_items: List[Dict[str, Any]] = []

    # 1. Inspect targets passed via CLI
    if args.input_targets:
        for t in args.input_targets:
            # Check A: Direct check inside data_dir (e.g. output/types_and_architectures_of_ai_agents_sme)
            cand_data_folder = Path(data_dir) / t
            if cand_data_folder.is_dir():
                candidate_items.append({
                    "topic_id": t,
                    "topic_folder": str(cand_data_folder),
                    "is_video": False,
                    "video_path": None,
                })
                continue

            p = Path(t).resolve()
            if p.is_file() and p.suffix.lower() in [".mp4", ".mov", ".mkv", ".avi", ".webm"]:
                tid = re.sub(r'[^a-zA-Z0-9_-]+', '_', p.stem).strip('_').lower()
                candidate_items.append({
                    "topic_id": tid,
                    "topic_folder": os.path.join(data_dir, tid),
                    "is_video": True,
                    "video_path": str(p),
                })
            elif p.is_dir():
                # Check if p is an existing topic folder (contains topic structure/artifacts)
                is_topic_dir = (
                    (p / "metadata_blueprints").is_dir()
                    or (p / "audio_elements").is_dir()
                    or (p / "transcripts").is_dir()
                    or (p / "manim_codes").is_dir()
                    or (p / "ex_config.json").is_file()
                    or any(p.glob("*_blueprint.json"))
                )
                if is_topic_dir:
                    candidate_items.append({
                        "topic_id": p.name,
                        "topic_folder": str(p),
                        "is_video": False,
                        "video_path": None,
                    })
                else:
                    # Check if it is a directory containing video files (e.g. input/ batch)
                    video_files = [f for f in p.glob("*") if f.suffix.lower() in [".mp4", ".mov", ".mkv", ".avi", ".webm"]]
                    if video_files:
                        for vf in video_files:
                            tid = re.sub(r'[^a-zA-Z0-9_-]+', '_', vf.stem).strip('_').lower()
                            candidate_items.append({
                                "topic_id": tid,
                                "topic_folder": os.path.join(data_dir, tid),
                                "is_video": True,
                                "video_path": str(vf),
                            })
                    else:
                        # Treat directory as topic folder
                        candidate_items.append({
                            "topic_id": p.name,
                            "topic_folder": str(p),
                            "is_video": False,
                            "video_path": None,
                        })
            else:
                # Target is folder name inside data_dir
                cand_folder = os.path.join(data_dir, t)
                candidate_items.append({
                    "topic_id": t,
                    "topic_folder": cand_folder,
                    "is_video": False,
                    "video_path": None,
                })
    else:
        # 2. Auto-discovery: Check data_dir first for existing topic folders
        if os.path.exists(data_dir):
            for entry in os.scandir(data_dir):
                if entry.is_dir() and not entry.name.startswith("."):
                    candidate_items.append({
                        "topic_id": entry.name,
                        "topic_folder": entry.path,
                        "is_video": False,
                        "video_path": None,
                    })

        # 3. Also check input/ folder for videos if candidate_items is empty
        if not candidate_items and DEFAULT_INPUT_DIR.exists():
            for vf in DEFAULT_INPUT_DIR.glob("*"):
                if vf.is_file() and vf.suffix.lower() in [".mp4", ".mov", ".mkv", ".avi", ".webm"]:
                    tid = re.sub(r'[^a-zA-Z0-9_-]+', '_', vf.stem).strip('_').lower()
                    candidate_items.append({
                        "topic_id": tid,
                        "topic_folder": os.path.join(data_dir, tid),
                        "is_video": True,
                        "video_path": str(vf),
                    })

    if not candidate_items:
        print(f"[INFO] No candidate topics or input videos found in {data_dir} or {DEFAULT_INPUT_DIR}.")
        sys.exit(0)

    # Compute priorities and sort queue
    prioritized_items = [
        compute_item_priority(it, trackers_dir, start_stage, end_stage)
        for it in candidate_items
    ]
    prioritized_items.sort(
        key=lambda m: (
            1 if m["is_incomplete"] else 0,
            m["is_w6"],
            m["highest_completed"],
        ),
        reverse=True,
    )

    print("=" * 80)
    print(" SIMPLILEARN PARALLEL ASYNCHRONOUS PIPELINE INITIALIZATION")
    print("=" * 80)
    print(f" Data Directory     : {data_dir}")
    print(f" Trackers Directory : {trackers_dir}")
    print(f" Logs Directory     : {logs_dir}")
    print(f" Stage Range        : Stage {start_stage} -> Stage {end_stage}")
    print(f" Parallel Workers   : {args.workers}")
    print(f" Max Manim Renders  : {args.max_manim}")
    print(f" Total Topics/Items : {len(prioritized_items)}")
    for idx, item in enumerate(prioritized_items, 1):
        top = item["topic_id"]
        v_tag = f" (Video: {Path(item['video_path']).name})" if item.get("is_video") else ""
        if item["is_incomplete"]:
            prio = " [PRIORITY W6]" if item["is_w6"] else ""
            nxt = STAGE_DEFINITIONS[item["next_stage"]]["name"] if item["next_stage"] < len(STAGE_DEFINITIONS) else "Done"
            print(f"   {idx:2d}. {top:<32} [Next: Stage {item['next_stage']:02d} - {nxt}]{v_tag}{prio}")
        else:
            print(f"   {idx:2d}. {top:<32} [COMPLETED - Skip]{v_tag}")
    print("=" * 80)

    # Multiprocessing coordination setup
    manager = multiprocessing.Manager()
    work_queue = manager.Queue()
    for it in prioritized_items:
        work_queue.put(it)

    manim_semaphore = multiprocessing.Semaphore(args.max_manim)
    status_dict = manager.dict()
    folder_retry_counts = manager.dict()
    completed_counter = multiprocessing.Value("i", 0)
    failed_counter = multiprocessing.Value("i", 0)

    num_workers = min(args.workers, len(prioritized_items))
    workers = []

    for wid in range(1, num_workers + 1):
        status_dict[wid] = {
            "topic": "Queued",
            "stage_idx": None,
            "stage_name": "Starting",
            "start_time": time.time(),
            "state": "idle",
        }
        w = multiprocessing.Process(
            target=topic_worker_loop,
            args=(
                wid,
                work_queue,
                (start_stage, end_stage),
                manim_semaphore,
                status_dict,
                completed_counter,
                failed_counter,
                data_dir,
                trackers_dir,
                logs_dir,
                google_key,
                claude_key,
                args.stage_retries,
                args.folder_retries,
                folder_retry_counts,
            ),
        )
        w.start()
        workers.append(w)

    # Live Dashboard Monitoring Loop
    try:
        last_banner_time = time.time()
        while any(w.is_alive() for w in workers):
            time.sleep(5)
            if time.time() - last_banner_time >= 30:
                print_dashboard_banner(
                    status_dict,
                    len(prioritized_items),
                    completed_counter,
                    failed_counter,
                    num_workers,
                    max_manim=args.max_manim,
                    trackers_dir=trackers_dir,
                )
                last_banner_time = time.time()

        for w in workers:
            w.join()

    except KeyboardInterrupt:
        print("\n[Interrupted] Terminating all pipeline workers...")
        for w in workers:
            w.terminate()
            w.join()
        sys.exit(130)

    # Final summary banner
    print_dashboard_banner(
        status_dict,
        len(prioritized_items),
        completed_counter,
        failed_counter,
        num_workers,
        max_manim=args.max_manim,
        trackers_dir=trackers_dir,
    )
    print("=" * 80)
    print(" PARALLEL PIPELINE EXECUTION COMPLETED")
    print(f" Total Topics : {len(prioritized_items)}")
    print(f" Succeeded    : {completed_counter.value}")
    print(f" Failed       : {failed_counter.value}")
    print("=" * 80)


if __name__ == "__main__":
    main()
