import os
import sys
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)
#!/usr/bin/env python3
"""
================================================================================
SIMPLILEARN OSL 3.0 & KPLOR STAGE TRACKER MANAGER
================================================================================
Provides thread-safe and process-safe atomic tracker management for all
24 pipeline stages (Video Preprocessing -> Pedagogical Design -> Manim Code ->
Feedback & Diagnostics -> VLM Review -> Timing Adjustments -> Final Render ->
SME Post-Production Composite).

Follows exact compatibility with Kplor ppt_trackers architecture.
================================================================================
"""

import os
import sys
import json
import portalocker
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Locate root and default trackers directory
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_TRACKERS_DIR = PROJECT_ROOT / "ppt_trackers"


# Master Stage Definitions with 1:1 Tracker Mapping
TRACKER_STAGES = [
    # Video Preprocessing (Raw Video Input)
    {
        "phase": "audio_cleaner",
        "stage_num": "0a",
        "name": "Audio Cleaner & Normalizer",
        "input_tracker": None,
        "output_tracker": "0a_audio_cleaner_tracker.json",
        "output_pattern": "{base}_clean_audio.mp4"
    },
    {
        "phase": "transcription",
        "stage_num": "0b",
        "name": "Speech Transcription",
        "input_tracker": "0a_audio_cleaner_tracker.json",
        "output_tracker": "0b_transcription_tracker.json",
        "output_pattern": "{base}_timestamps.json"
    },
    {
        "phase": "clean_fillers",
        "stage_num": "0c",
        "name": "Clean Fillers & Retakes",
        "input_tracker": "0b_transcription_tracker.json",
        "output_tracker": "0c_clean_fillers_tracker.json",
        "output_pattern": "{base}_clean_transcript.json"
    },
    {
        "phase": "av_trimmer",
        "stage_num": "0d",
        "name": "Synchronous AV Trimmer",
        "input_tracker": "0c_clean_fillers_tracker.json",
        "output_tracker": "0d_av_trimmer_tracker.json",
        "output_pattern": "{base}_trimmed.mp4"
    },

    # Pedagogical Storyboard & Design (Stages 0 to 10 matching Kplor)
    {
        "phase": "hook_generation",
        "stage_num": 0,
        "name": "Hook Generation",
        "input_tracker": "0c_clean_fillers_tracker.json",
        "output_tracker": "0_hook_output_tracker.json",
        "output_pattern": "{base}_hook_blueprint.json"
    },
    {
        "phase": "instructional_design",
        "stage_num": 1,
        "name": "Instructional Design",
        "input_tracker": "0_hook_output_tracker.json",
        "output_tracker": "1_instruction_design_output_tracker.json",
        "output_pattern": "instructions_gemini-3.8-flash.json"
    },
    {
        "phase": "asset_classification",
        "stage_num": 2,
        "name": "Asset Classification",
        "input_tracker": "1_instruction_design_output_tracker.json",
        "output_tracker": "2_asset_class_output_tracker.json",
        "output_pattern": "asset_classification_gemini-3.8-flash.json"
    },
    {
        "phase": "asset_construction",
        "stage_num": 3,
        "name": "Asset Construction",
        "input_tracker": "2_asset_class_output_tracker.json",
        "output_tracker": "3_asset_construct_output_tracker.json",
        "output_pattern": "{base}_constructed_assets.json"
    },
    {
        "phase": "image_prompt_generation",
        "stage_num": 4,
        "name": "Image Prompt Generation",
        "input_tracker": "2_asset_class_output_tracker.json",
        "output_tracker": "4_prompt_images_output_tracker.json",
        "output_pattern": "image_prompt_gemini-3.8-flash.json"
    },
    {
        "phase": "audio_generation",
        "stage_num": 5,
        "name": "Audio Generation / CGI Manifest",
        "input_tracker": "1_instruction_design_output_tracker.json",
        "output_tracker": "5_audio_output_tracker.json",
        "output_pattern": "CGI_Input.json"
    },
    {
        "phase": "presentation_composer",
        "stage_num": 6,
        "name": "Presentation Composer",
        "input_tracker": "5_audio_output_tracker.json",
        "output_tracker": "6_presentation_composer_tracker.json",
        "output_pattern": "enhanced_anim_claude-haiku-4-5-20251001.json"
    },
    {
        "phase": "presentation_experience_planner",
        "stage_num": 7,
        "name": "Experience Planner",
        "input_tracker": "6_presentation_composer_tracker.json",
        "output_tracker": "7_experience_planner_tracker.json",
        "output_pattern": "experience_plan_gemini-3.6-flash.json"
    },
    {
        "phase": "image_generator",
        "stage_num": 8,
        "name": "Image Generation",
        "input_tracker": "7_experience_planner_tracker.json",
        "output_tracker": "8_image_generation_tracker.json",
        "output_pattern": "images"
    },
    {
        "phase": "styling_generator",
        "stage_num": 9,
        "name": "Styling Generator",
        "input_tracker": "8_image_generation_tracker.json",
        "output_tracker": "9_styling_output_tracker.json",
        "output_pattern": "styling_gemini-3.8-flash.json"
    },
    {
        "phase": "manim_code_generation",
        "stage_num": 10,
        "name": "Manim Code Generation",
        "input_tracker": "9_styling_output_tracker.json",
        "output_tracker": "10_code_generation_tracker.json",
        "output_pattern": "manim_codes"
    },

    # Feedback, Diagnostics, VLM Review & Corrections (Stages 11 to 22)
    {
        "phase": "manim_feedback_run",
        "stage_num": 11,
        "name": "Manim Feedback Run",
        "input_tracker": "10_code_generation_tracker.json",
        "output_tracker": "11_run_manim_feedback_tracker.json",
        "output_pattern": "manim_raw_videos"
    },
    {
        "phase": "feedback_report",
        "stage_num": 12,
        "name": "Feedback Report",
        "input_tracker": "11_run_manim_feedback_tracker.json",
        "output_tracker": "12_generate_feedback_tracker.json",
        "output_pattern": "correction_insights"
    },
    {
        "phase": "suggest_corrections",
        "stage_num": 13,
        "name": "Suggest Corrections",
        "input_tracker": "12_generate_feedback_tracker.json",
        "output_tracker": "13_suggest_corrections_tracker.json",
        "output_pattern": "correction_insights"
    },
    {
        "phase": "implement_corrections",
        "stage_num": 14,
        "name": "Implement Corrections",
        "input_tracker": "13_suggest_corrections_tracker.json",
        "output_tracker": "14_corrections_implement_tracker.json",
        "output_pattern": "manim_codes"
    },
    {
        "phase": "manim_vlm_feedback",
        "stage_num": 15,
        "name": "Manim VLM Feedback Run",
        "input_tracker": "14_corrections_implement_tracker.json",
        "output_tracker": "15_run_manim_vlm_feedback_tracker.json",
        "output_pattern": "manim_raw_videos_vlm"
    },
    {
        "phase": "generate_vlm_report",
        "stage_num": 16,
        "name": "Generate VLM Report",
        "input_tracker": "15_run_manim_vlm_feedback_tracker.json",
        "output_tracker": "16_generate_vlm_feedback_tracker.json",
        "output_pattern": "keyframe_context_vlm"
    },
    {
        "phase": "visual_triangulation",
        "stage_num": 17,
        "name": "Visual Triangulation",
        "input_tracker": "16_generate_vlm_feedback_tracker.json",
        "output_tracker": "17_generate_triangulation_tracker.json",
        "output_pattern": "visual_triangulation"
    },
    {
        "phase": "vlm_fix_suggestor",
        "stage_num": 18,
        "name": "VLM Fix Suggestor",
        "input_tracker": "17_generate_triangulation_tracker.json",
        "output_tracker": "18_vlm_fix_tracker.json",
        "output_pattern": "vlm_suggestions"
    },
    {
        "phase": "vlm_fixing_stage",
        "stage_num": 19,
        "name": "VLM Fixing Stage",
        "input_tracker": "18_vlm_fix_tracker.json",
        "output_tracker": "19_vlm_fixing_stage_tracker.json",
        "output_pattern": "vlm_fixes"
    },
    {
        "phase": "final_styling_corrections",
        "stage_num": 20,
        "name": "Final Styling & Code Fixes",
        "input_tracker": "19_vlm_fixing_stage_tracker.json",
        "output_tracker": "20_eng_corrections_tracker.json",
        "output_pattern": "eng_corrections"
    },
    {
        "phase": "timing_adjustments",
        "stage_num": 21,
        "name": "Timing Adjustments",
        "input_tracker": "20_eng_corrections_tracker.json",
        "output_tracker": "21_timing_adjustment_tracker.json",
        "output_pattern": "manim_time_synced_videos"
    },
    {
        "phase": "final_code_run",
        "stage_num": 22,
        "name": "Final Render",
        "input_tracker": "21_timing_adjustment_tracker.json",
        "output_tracker": "22_final_render_tracker.json",
        "output_pattern": "manim_videos"
    },

    # Post-Production SME Composite
    {
        "phase": "post_production",
        "stage_num": 23,
        "name": "Post-Production SME Integration",
        "input_tracker": "22_final_render_tracker.json",
        "output_tracker": "23_sme_post_production_tracker.json",
        "output_pattern": "{base}_FINAL.mp4"
    }
]

PHASE_TO_STAGE = {s["phase"]: s for s in TRACKER_STAGES}


class TrackerManager:
    """Thread-safe and process-safe tracker controller."""

    def __init__(self, trackers_dir: Optional[os.PathLike] = None):
        self.trackers_dir = Path(trackers_dir) if trackers_dir else DEFAULT_TRACKERS_DIR
        self.trackers_dir.mkdir(parents=True, exist_ok=True)
        self.init_all_trackers()

    def get_tracker_path(self, tracker_name: str) -> Path:
        """Returns the absolute Path for a tracker file."""
        return self.trackers_dir / tracker_name

    def load_tracker(self, tracker_name_or_path: str) -> Dict[str, Any]:
        """Loads a tracker JSON file with a shared lock (read lock)."""
        path = Path(tracker_name_or_path)
        if not path.is_absolute():
            path = self.trackers_dir / tracker_name_or_path

        if not path.exists():
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                portalocker.lock(f, portalocker.LOCK_SH)
                try:
                    content = f.read().strip()
                    if not content:
                        return {}
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {}
                finally:
                    portalocker.unlock(f)
        except Exception as e:
            return {}

    def save_tracker(self, tracker_name_or_path: str, data: Dict[str, Any]) -> bool:
        """Saves a tracker JSON file atomically with an exclusive lock."""
        path = Path(tracker_name_or_path)
        if not path.is_absolute():
            path = self.trackers_dir / tracker_name_or_path

        path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = str(path) + ".lock"

        try:
            with portalocker.Lock(lock_path, timeout=60):
                current = {}
                if path.exists():
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            current = json.load(f)
                    except Exception:
                        current = {}

                current.update(data)
                temp_file = str(path) + f".tmp.{os.getpid()}"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(current, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, str(path))
            return True
        except Exception as e:
            print(f"[TrackerManager Error] Failed saving tracker {path.name}: {e}")
            return False

    def is_stage_completed(self, tracker_name_or_path: str, topic_id: str) -> bool:
        """Returns True if topic_id is marked processed=True in the tracker."""
        tracker_data = self.load_tracker(tracker_name_or_path)
        entry = tracker_data.get(topic_id)
        if entry and isinstance(entry, dict):
            return entry.get("processed") is True
        return False

    def get_stage_output_path(self, tracker_name_or_path: str, topic_id: str) -> Optional[str]:
        """Returns the registered output_path from tracker."""
        tracker_data = self.load_tracker(tracker_name_or_path)
        entry = tracker_data.get(topic_id)
        if entry and isinstance(entry, dict):
            return entry.get("output_path")
        return None

    def record_stage_completed(
        self,
        tracker_name_or_path: str,
        topic_id: str,
        output_path: Optional[str] = None,
        topic_name: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Records a successful stage completion."""
        entry = {
            "output_path": str(output_path) if output_path else None,
            "processed": True,
            "topic_name": topic_name or topic_id,
            "topic_id": topic_id,
            "failure_reason": None
        }
        if extra_fields:
            entry.update(extra_fields)
        return self.save_tracker(tracker_name_or_path, {topic_id: entry})

    def record_stage_failed(
        self,
        tracker_name_or_path: str,
        topic_id: str,
        failure_reason: str,
        topic_name: Optional[str] = None
    ) -> bool:
        """Records a stage failure with failure reason."""
        entry = {
            "output_path": None,
            "processed": False,
            "topic_name": topic_name or topic_id,
            "topic_id": topic_id,
            "failure_reason": str(failure_reason)
        }
        return self.save_tracker(tracker_name_or_path, {topic_id: entry})

    def init_all_trackers(self):
        """Ensures that all standard tracker JSON files exist in trackers_dir."""
        for s in TRACKER_STAGES:
            t_path = self.trackers_dir / s["output_tracker"]
            if not t_path.exists():
                try:
                    with open(t_path, "w", encoding="utf-8") as f:
                        json.dump({}, f, indent=4)
                except Exception:
                    pass

    def get_topic_progress(self, topic_id: str) -> Dict[str, Any]:
        """Summarizes progress across all stages for a topic."""
        report = []
        completed_count = 0
        for s in TRACKER_STAGES:
            done = self.is_stage_completed(s["output_tracker"], topic_id)
            out_p = self.get_stage_output_path(s["output_tracker"], topic_id)
            if done:
                completed_count += 1
            report.append({
                "stage": s["stage_num"],
                "phase": s["phase"],
                "name": s["name"],
                "tracker": s["output_tracker"],
                "completed": done,
                "output_path": out_p
            })
        return {
            "topic_id": topic_id,
            "total_stages": len(TRACKER_STAGES),
            "completed_stages": completed_count,
            "percentage": (completed_count / len(TRACKER_STAGES)) * 100,
            "stages": report
        }


# Global singleton instance
_tracker_manager = None

def get_tracker_manager(trackers_dir: Optional[os.PathLike] = None) -> TrackerManager:
    global _tracker_manager
    if _tracker_manager is None or trackers_dir is not None:
        _tracker_manager = TrackerManager(trackers_dir)
    return _tracker_manager
