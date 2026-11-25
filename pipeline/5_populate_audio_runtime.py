#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 5: AUDIO RUNTIME EXTRACTION & DURATION MANIFEST
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 5
   - Script Name: 5_populate_audio_runtime.py
   - Primary Class: PopulateAudioRunTime
   - Pipeline Role:
     Extracts, verifies, and populates spoken narration durations into the master CGI
     manifest (CGI_Input.json). Eliminates synthetic TTS generation by reading pre-existing
     audio recordings (e.g., SME recordings, voiceover files, or video scratch audio) and
     transcript timestamps. In the absence of audio files, calculates deterministic
     syllabic durations (150 WPM + punctuation pauses) to establish the authoritative
     timing timeline for all visual and CGI animation stages.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 1 (1_generate_instructional_design.py):
       - How: Ingests {topic_id}_storyboard_blueprint.json via
         1_instruction_design_output_tracker.json.
       - Purpose: Supplies narration statements and presentation step definitions.
     * Stage 0B / 0C (Audio Preprocessing):
       - How: Reads timestamps and audio recordings from audio_elements/ or topic folder.
       - Purpose: Provides acoustic waveforms to measure exact statement durations.
   - Input Tracker: ppt_trackers/1_instruction_design_output_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * {topic_id}_storyboard_blueprint.json (Stage 1):
       Location: output/<TOPIC_NAME>/{topic_id}_storyboard_blueprint.json
       Content: Multi-scene storyboard with spoken narration text and step titles.
     * Audio Elements Directory:
       Location: output/<TOPIC_NAME>/audio_elements/
       Content: Pre-recorded WAV/MP3 statement audio files.
     * ex_config.json:
       Location: output/<TOPIC_NAME>/ex_config.json
       Content: Base folder and topic metadata.
     * Input Tracker:
       Location: ppt_trackers/1_instruction_design_output_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 1_instruction_design_output_tracker.json.
   - Step 2: Cleans narration statements and strips LaTeX formatting into spoken prose.
   - Step 3: Checks for unified scene audio (group_{sid}_pair_1_statement1.wav / group_{sid}_pair_1.wav)
     or probes individual statement audio files in audio_elements/ via wave and FFprobe.
   - Step 4: Parses explicit timestamps or time-range metadata where audio files are absent.
   - Step 5: Applies natural speech rate estimation (~150 wpm + punctuation pauses) as fallback.
   - Step 6: Computes exact run_time, start_time, and end_time for each presentation step.
   - Step 7: Allocates timing via Whisper timestamp snapping or proportional word split, records
     audio_file / audio_path metadata, and writes master CGI_Input.json and avatar_strategy.json.
   - Step 8: Atomically updates 5_audio_output_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * CGI_Input.json:
       Location: output/<TOPIC_NAME>/CGI_Input.json
       Content: Master time-coded storyboard manifest detailing step runtimes, cumulative
                timestamps, and narration text for Manim CGI generation.
     * avatar_strategy.json:
       Location: output/<TOPIC_NAME>/avatar_strategy.json
       Content: Segment duration map for presenter webcam and avatar synchronization.
     * Output Tracker:
       Location: ppt_trackers/5_audio_output_tracker.json
       Content: Atomic tracker confirming completion of audio duration extraction.

6. DOWNSTREAM CONSUMERS:
   - Stage 6 (6_presentation_composer.py): Uses runtimes to allocate animation budgets.
   - Stage 10 (10_generate_code.py): Uses statement timings to generate initial Manim code.
   - Stage 19 (19_vlm_fixing_stage.py): Uses cumulative M:SS timestamps for physical fix directives.
   - Stage 21 (21_timing_adjustments.py): Uses statement runtimes for precision sync_to injection.
   - Stage 22 (22_final_code_run.py): Uses audio runtimes to mux final audio and video tracks.
================================================================================
"""

import os
import sys
import json
import re
import copy
import wave
import subprocess
from pathlib import Path
from typing import Optional, Union, Tuple, List, Dict, Any
from filelock import FileLock

# Optional imports for audio handling (graceful fallback if not present)
try:
    from moviepy import AudioFileClip, concatenate_audioclips
except ImportError:
    try:
        from moviepy.editor import AudioFileClip, concatenate_audioclips
    except ImportError:
        AudioFileClip = None
        concatenate_audioclips = None


# ==============================================================================
# Text & LaTeX Cleaning Utility
# ==============================================================================
def clean_narration_latex(text: str) -> str:
    """
    Cleans raw LaTeX markup and converts common mathematical expressions
    into natural spoken English for accurate timing and visual synchronization.
    """
    if not text:
        return ""
    text = re.sub(r'\\binom\{([^}]+)\}\{([^}]+)\}', r'\1 choose \2', text)
    text = re.sub(r'\{([^}]+)\}\s*\\choose\s*\{([^}]+)\}', r'\1 choose \2', text)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1 over \2', text)
    text = re.sub(r'\\sum_\{([^=]+)=([^}]+)\}\^\{([^}]+)\}', r'sum from \1 equals \2 to \3', text)
    text = re.sub(r'\\sum', 'sum', text)
    text = re.sub(r'\^2\b', ' squared', text)
    text = re.sub(r'\^3\b', ' cubed', text)
    text = re.sub(r'\^\{([^}]+)\}', r' raised to \1', text)
    text = re.sub(r'\^(\w+)', r' raised to \1', text)
    text = re.sub(r'_\{([^}]+)\}', r' sub \1', text)
    text = re.sub(r'_(\w+)', r' sub \1', text)
    text = text.replace(r'\cdot', ' times ')
    text = text.replace(r'\times', ' times ')
    text = text.replace(r'\pm', ' plus or minus ')
    text = text.replace(r'\leq', ' less than or equal to ')
    text = text.replace(r'\geq', ' greater than or equal to ')
    text = text.replace(r'\neq', ' not equal to ')
    text = text.replace(r'\approx', ' approximately ')
    text = text.replace(r'\infty', ' infinity ')
    text = text.replace(r'\rightarrow', ' approaches ')
    text = text.replace(r'\to', ' to ')
    text = re.sub(r'\$\$?', '', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = text.replace('{', '').replace('}', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ==============================================================================
# Timestamp Parsing & Duration Utilities
# ==============================================================================
def parse_timestamp_to_seconds(val: Any) -> Optional[float]:
    """
    Converts various timestamp formats into floating-point seconds.
    Examples:
        4.46 -> 4.46
        "04.5" -> 4.5
        "01:23.5" -> 83.5
        "01:02:03" -> 3723.0
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return round(float(val), 3)
    val_str = str(val).strip().strip("[]()")
    try:
        return round(float(val_str), 3)
    except ValueError:
        pass

    parts = val_str.split(":")
    try:
        if len(parts) == 2:
            return round(float(parts[0]) * 60.0 + float(parts[1]), 3)
        elif len(parts) == 3:
            return round(float(parts[0]) * 3600.0 + float(parts[1]) * 60.0 + float(parts[2]), 3)
    except ValueError:
        pass
    return None


def parse_timestamp_range(val: Any) -> Optional[Tuple[float, float]]:
    """
    Extracts start and end seconds from a timestamp range.
    Examples:
        "[0:04.5 -> 0:20]" -> (4.5, 20.0)
        "0:00 - 0:15.5" -> (0.0, 15.5)
        [4.5, 20.0] -> (4.5, 20.0)
    """
    if isinstance(val, (list, tuple)) and len(val) >= 2:
        s = parse_timestamp_to_seconds(val[0])
        e = parse_timestamp_to_seconds(val[1])
        if s is not None and e is not None and e >= s:
            return s, e

    if isinstance(val, str):
        match = re.search(
            r'\[?(\d+:\d+(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:->|–|-|to)\s*(\d+:\d+(?:\.\d+)?|\d+(?:\.\d+)?)\]?',
            val
        )
        if match:
            s = parse_timestamp_to_seconds(match.group(1))
            e = parse_timestamp_to_seconds(match.group(2))
            if s is not None and e is not None and e >= s:
                return s, e
    return None


def probe_audio_duration(file_path: Union[str, Path]) -> float:
    """
    Rapidly probes the precise duration in seconds of an audio or video file
    using wave (instant stdlib for WAV), ffprobe, or moviepy.
    """
    path_obj = Path(file_path).resolve()
    if not path_obj.exists() or path_obj.stat().st_size == 0:
        return 0.0

    # 1. Fast WAV header inspection
    if path_obj.suffix.lower() == ".wav":
        try:
            with wave.open(str(path_obj), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return round(float(frames) / float(rate), 3)
        except Exception:
            pass

    # 2. Universal fast ffprobe
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path_obj)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        dur_str = result.stdout.strip()
        if dur_str:
            return round(float(dur_str), 3)
    except Exception:
        pass

    # 3. MoviePy fallback
    if AudioFileClip is not None:
        try:
            clip = AudioFileClip(str(path_obj))
            dur = clip.duration
            clip.close()
            if dur and dur > 0:
                return round(float(dur), 3)
        except Exception:
            pass

    return 0.0


def estimate_speech_duration(text: str, wpm: float = 140.0) -> float:
    """
    Estimates natural narration duration when neither an audio recording nor an
    explicit timestamp is present. Uses standard conversational pace (~140 wpm,
    or ~2.33 words/sec) plus realistic punctuation pauses.
    """
    clean_text = clean_narration_latex(text).strip()
    if not clean_text or clean_text.lower() in ("<silence>", "silence"):
        return 1.0

    words = [w for w in clean_text.split() if w]
    word_count = len(words)
    sec_per_word = 60.0 / wpm
    base_duration = word_count * sec_per_word

    # Additional pause for punctuation (0.2s for commas/semicolons, 0.4s for full stops)
    commas = len(re.findall(r'[,;:]', clean_text))
    stops = len(re.findall(r'[.?!]', clean_text))
    pause_time = (commas * 0.20) + (stops * 0.40)

    total_est = base_duration + pause_time
    return round(max(1.5, total_est), 3)


# ==============================================================================
# Class: PopulateAudioRunTime
# ==============================================================================
class PopulateAudioRunTime:
    """
    Stage 5: Audio Runtime Extraction & Duration Manifest.
    Eliminates synthetic TTS generation by reading existing audio files and statement
    timestamps, verifying runtimes, and populating CGI_Input.json for visual synthesis.
    """

    def __init__(
        self,
        input_tracker_path: Optional[str] = None,
        output_tracker_path: Optional[str] = None,
        google_api_key: Optional[str] = None,
        claude_api_key: Optional[str] = None,
        input_folder: str = "."
    ):
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.google_api_key = google_api_key
        self.claude_api_key = claude_api_key
        self.input_folder = input_folder

        if self.output_tracker_path and not os.path.exists(self.output_tracker_path):
            tracker_dir = os.path.dirname(self.output_tracker_path)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
            self._write_json(self.output_tracker_path, {})

    # --------------------------------------------------------------------------
    # JSON & Tracker Helpers
    # --------------------------------------------------------------------------
    def _load_json(self, path: str) -> Any:
        if not path or not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading JSON from {path}: {e}")
            return {}

    def _write_json(self, path: str, data: Any):
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _safe_update_output_tracker(
        self,
        item_id: str,
        topic_name: str,
        audio_folder_path: str,
        concatenated_audio_path: Optional[str],
        timed_storyboard_path: str,
        processed: bool,
        failure_reason: str = ""
    ):
        if not self.output_tracker_path:
            return
        lock_path = self.output_tracker_path + ".lock"
        with FileLock(lock_path):
            tracker = self._load_json(self.output_tracker_path)
            tracker[item_id] = {
                "audio_folder_path": audio_folder_path,
                "topic_name": topic_name,
                "concatenated_audio_path": concatenated_audio_path or "",
                "timed_storyboard_path": timed_storyboard_path,
                "processed": processed,
                "failure_reason": failure_reason
            }
            self._write_json(self.output_tracker_path, tracker)

    def process_audio_file(self, file_path: str) -> float:
        """Probes the runtime of an existing audio or video file."""
        return probe_audio_duration(file_path)

    def increase_audio_volume(self, input_path: Optional[str], output_path: str, volume_factor: float = 1.5):
        """Adjusts the volume of an existing audio file via FFmpeg."""
        if not input_path or not os.path.exists(input_path):
            return
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-filter:a", f"volume={volume_factor}",
                str(output_path)
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except Exception as e:
            print(f"⚠️ Volume adjustment failed for {input_path}: {e}")

    # --------------------------------------------------------------------------
    # Statement Timing & Duration Extraction
    # --------------------------------------------------------------------------
    def extract_statement_timing(
        self,
        group: str,
        pair_idx: int,
        stmt_idx: int,
        total_stmts: int,
        statement_text: str,
        speech_content_pair: dict,
        audio_element_dir: str,
        all_statements: Optional[List[str]] = None,
        allocated_so_far: float = 0.0
    ) -> Tuple[float, str, Optional[str]]:
        """
        Determines the exact runtime of an individual narration statement.
        Hierarchy of truth:
          1. Existing statement audio file on disk (WAV/MP3).
          2. Explicit statements list or statement-level timestamp in the storyboard.
          3. Section-level duration/range allocated proportionally to this statement.
          4. Conversational speech-rate fallback (~140 wpm).

        Returns:
            (runtime_seconds, basis_description, audio_file_path_or_none)
        """
        # Handle silence marker
        if statement_text.strip().strip("<>").lower() == "silence":
            return 1.0, "Explicit Silence (1.0s)", None

        # ----------------------------------------------------------------------
        # Check 1: Existing Audio File on Disk
        # ----------------------------------------------------------------------
        audio_candidates = [
            os.path.join(audio_element_dir, f"group_{group}_pair_{pair_idx}_statement{stmt_idx}.wav"),
            os.path.join(audio_element_dir, f"group_{group}_pair_{pair_idx}_statement{stmt_idx}.mp3"),
            os.path.join(audio_element_dir, f"group_{group}_pair_{pair_idx}.wav"),
            os.path.join(audio_element_dir, f"group_{group}_pair_{pair_idx}.mp3"),
            os.path.join(audio_element_dir, f"scene_{group}_statement_{stmt_idx}.wav"),
            os.path.join(audio_element_dir, f"scene_{group}_pair_{pair_idx}.wav"),
            os.path.join(audio_element_dir, f"scene_{group}.wav"),
        ]
        if speech_content_pair.get("audio_file"):
            audio_candidates.insert(0, speech_content_pair["audio_file"])
            audio_candidates.insert(1, os.path.join(audio_element_dir, speech_content_pair["audio_file"]))
        if speech_content_pair.get("audio_path"):
            audio_candidates.insert(0, speech_content_pair["audio_path"])

        for cand in audio_candidates:
            if cand and os.path.exists(cand) and os.path.getsize(cand) > 0:
                dur = probe_audio_duration(cand)
                if dur > 0:
                    basis = f"Existing Audio File: {os.path.basename(cand)}"
                    return dur, basis, cand

        # ----------------------------------------------------------------------
        # Check 2: Statement-level timestamps / statements inside speech_content_pair
        # ----------------------------------------------------------------------
        # Check explicit statements list in speech_content_pair
        existing_stmts = speech_content_pair.get("statements")
        if isinstance(existing_stmts, list) and len(existing_stmts) >= stmt_idx:
            entry = existing_stmts[stmt_idx - 1]
            if isinstance(entry, dict):
                for k in ["runtime", "run_time", "duration"]:
                    if k in entry:
                        dur = parse_timestamp_to_seconds(entry[k])
                        if dur and dur > 0:
                            return dur, f"Statement Metadata Entry ({dur}s)", None
                if "start" in entry and "end" in entry:
                    s = parse_timestamp_to_seconds(entry["start"])
                    e = parse_timestamp_to_seconds(entry["end"])
                    if s is not None and e is not None and e > s:
                        return round(e - s, 3), f"Statement Range [{s}s -> {e}s]", None

        timestamps_list = speech_content_pair.get("timestamps") or speech_content_pair.get("statement_timestamps")
        if isinstance(timestamps_list, list) and len(timestamps_list) >= stmt_idx:
            entry = timestamps_list[stmt_idx - 1]
            if isinstance(entry, dict):
                for k in ["runtime", "run_time", "duration"]:
                    if k in entry:
                        dur = parse_timestamp_to_seconds(entry[k])
                        if dur and dur > 0:
                            return dur, f"Statement Timestamp Entry ({dur}s)", None
                if "start" in entry and "end" in entry:
                    s = parse_timestamp_to_seconds(entry["start"])
                    e = parse_timestamp_to_seconds(entry["end"])
                    if s is not None and e is not None and e > s:
                        return round(e - s, 3), f"Statement Range [{s}s -> {e}s]", None
            else:
                rng = parse_timestamp_range(entry)
                if rng:
                    dur = round(rng[1] - rng[0], 3)
                    return dur, f"Statement Range [{rng[0]}s -> {rng[1]}s]", None
                single_dur = parse_timestamp_to_seconds(entry)
                if single_dur and single_dur > 0:
                    return single_dur, f"Statement Timestamp Entry ({single_dur}s)", None

        # ----------------------------------------------------------------------
        # Check 3: Audio Timing Metadata block (Instructional Design Standard)
        # ----------------------------------------------------------------------
        audio_timing = speech_content_pair.get("audio_timing")
        if isinstance(audio_timing, dict):
            at_dur = parse_timestamp_to_seconds(audio_timing.get("duration"))
            if at_dur is None and "start_time" in audio_timing and "end_time" in audio_timing:
                s = parse_timestamp_to_seconds(audio_timing["start_time"])
                e = parse_timestamp_to_seconds(audio_timing["end_time"])
                if s is not None and e is not None and e > s:
                    at_dur = round(e - s, 3)
            if at_dur and at_dur > 0:
                if total_stmts == 1:
                    return at_dur, f"Audio Timing Metadata ({at_dur}s)", None
                else:
                    if all_statements:
                        full_words = max(1, sum(max(1, len(s.split())) for s in all_statements))
                    else:
                        full_text = speech_content_pair.get("narration_statement") or speech_content_pair.get("voiceover_narration", "")
                        full_words = max(1, len(full_text.split()))
                    stmt_words = max(1, len(statement_text.split()))

                    if stmt_idx == total_stmts and allocated_so_far > 0:
                        prop_dur = round(max(0.1, at_dur - allocated_so_far), 3)
                        return prop_dur, f"Proportional Audio Metadata Remainder ({prop_dur}s of {at_dur}s)", None
                    else:
                        prop_dur = round(at_dur * (stmt_words / full_words), 3)
                        return prop_dur, f"Proportional Audio Metadata ({prop_dur}s of {at_dur}s)", None

        # ----------------------------------------------------------------------
        # Check 4: Section-level runtime or timestamp range
        # ----------------------------------------------------------------------
        section_dur = None
        if "run_time" in speech_content_pair:
            section_dur = parse_timestamp_to_seconds(speech_content_pair["run_time"])
        elif "duration" in speech_content_pair:
            section_dur = parse_timestamp_to_seconds(speech_content_pair["duration"])

        # Check section start_time & end_time
        if section_dur is None:
            if "start_time" in speech_content_pair and "end_time" in speech_content_pair:
                s = parse_timestamp_to_seconds(speech_content_pair["start_time"])
                e = parse_timestamp_to_seconds(speech_content_pair["end_time"])
                if s is not None and e is not None and e > s:
                    section_dur = round(e - s, 3)

        # Check section time_range or embedded timestamp in visuals/title
        if section_dur is None:
            for field in ["time_range", "timestamp", "visuals", "title"]:
                val = speech_content_pair.get(field)
                if val:
                    rng = parse_timestamp_range(val)
                    if rng:
                        section_dur = round(rng[1] - rng[0], 3)
                        break

        if section_dur is not None and section_dur > 0:
            if total_stmts == 1:
                return section_dur, f"Section Runtime Allocation ({section_dur}s)", None
            else:
                if all_statements:
                    full_words = max(1, sum(max(1, len(s.split())) for s in all_statements))
                else:
                    full_text = speech_content_pair.get("narration_statement") or speech_content_pair.get("voiceover_narration", "")
                    full_words = max(1, len(full_text.split()))
                stmt_words = max(1, len(statement_text.split()))

                if stmt_idx == total_stmts and allocated_so_far > 0:
                    prop_dur = round(max(0.1, section_dur - allocated_so_far), 3)
                    return prop_dur, f"Proportional Section Remainder ({prop_dur}s of {section_dur}s)", None
                else:
                    prop_dur = round(section_dur * (stmt_words / full_words), 3)
                    return prop_dur, f"Proportional Section Allocation ({prop_dur}s of {section_dur}s)", None

        # ----------------------------------------------------------------------
        # Check 5: Speech-rate Fallback
        # ----------------------------------------------------------------------
        est_dur = estimate_speech_duration(statement_text)
        return est_dur, f"Speech Rate Estimation ({est_dur}s @ ~140 WPM)", None

    # --------------------------------------------------------------------------
    # Core Pipeline Generation Logic
    # --------------------------------------------------------------------------
    def generate_audio(
        self,
        narration_file: str,
        base_folder: str,
        config_file: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Extracts narration runtimes and constructs the master CGI manifest (CGI_Input.json).
        Does NOT invoke TTS synthesis; directly checks existing audio files and statement
        timestamps, ensuring all visual sections have accurate runtimes populated.

        Parameters:
            narration_file: Path to input narration storyboard (JSON).
            base_folder: Working directory for output manifest.
            config_file: Optional path to ex_config.json.

        Returns:
            (concatenated_audio_path_or_None, path_to_CGI_Input.json)
        """
        # Resolve base_folder and config
        if config_file and os.path.exists(config_file):
            try:
                config_data = self._load_json(config_file)
                cfg_base = config_data.get("base_folder")
                if cfg_base and cfg_base != ".":
                    base_folder = cfg_base
            except Exception:
                pass

        base_folder = os.path.abspath(base_folder)
        audio_element_dir = os.path.join(base_folder, "audio_elements")
        audio_concat_scene_dir = os.path.join(base_folder, "audio_concat_dir")
        os.makedirs(audio_element_dir, exist_ok=True)
        os.makedirs(audio_concat_scene_dir, exist_ok=True)

        # Load narration script
        if not os.path.exists(narration_file):
            alt_candidates = [
                os.path.join(base_folder, "sample_storyboard.json"),
                os.path.join(base_folder, "CGI_Input.json"),
                os.path.join(base_folder, "instructions.json"),
                os.path.join(base_folder, "narration.json"),
            ]
            for cand in alt_candidates:
                if os.path.exists(cand):
                    narration_file = cand
                    break

        if not os.path.exists(narration_file):
            raise FileNotFoundError(f"Narration file not found: {narration_file}")

        print(f"\n" + "=" * 78)
        print(f"   RUNTIME & DURATION MANIFEST GENERATION")
        print(f"   Source Script: {narration_file}")
        print(f"   Target Folder: {base_folder}")
        print("=" * 78)

        raw_script = self._load_json(narration_file)
        if not raw_script:
            raise ValueError(f"Narration file is empty or invalid JSON: {narration_file}")

        # Normalize narration_script into a standard dict: {scene_key: [speech_content_pairs]}
        # Supports:
        # 1. Instructional Design Output: {"lesson_title": ..., "scenes": [...]}
        # 2. List of scenes: [{...}, {...}]
        # 3. Direct grouped dictionary: {"1": [...], "2": [...]}
        grouped_script: Dict[str, List[dict]] = {}

        if isinstance(raw_script, dict) and "scenes" in raw_script and isinstance(raw_script["scenes"], list):
            for idx, sc in enumerate(raw_script["scenes"]):
                sid = str(sc.get("scene_id", idx + 1))
                # If a unified scene audio file exists (group_{sid}_pair_1_statement1.wav), preserve scene as single pair
                scene_audio_candidates = [
                    os.path.join(audio_element_dir, f"group_{sid}_pair_1_statement1.wav"),
                    os.path.join(audio_element_dir, f"group_{sid}_pair_1.wav"),
                    os.path.join(audio_element_dir, f"scene_{sid}.wav")
                ]
                has_scene_audio = any(os.path.exists(cand) and os.path.getsize(cand) > 0 for cand in scene_audio_candidates)
                
                steps = sc.get("presentation_steps")
                if isinstance(steps, list) and len(steps) > 0 and not has_scene_audio:
                    expanded_steps = []
                    for s_idx, st in enumerate(steps):
                        st_copy = dict(st)
                        st_copy.setdefault("scene_id", sid)
                        st_copy.setdefault("scene_number", sc.get("scene_number", idx + 1))
                        st_copy.setdefault("scene_index", sc.get("scene_index", idx + 1))
                        st_copy.setdefault("sme_layout", sc.get("sme_layout", "70"))
                        st_copy.setdefault("sme_positioning", sc.get("sme_positioning"))
                        st_copy.setdefault("presentation_safe_zone", sc.get("presentation_safe_zone"))
                        if not st_copy.get("title") and st_copy.get("step_title"):
                            st_copy["title"] = st_copy["step_title"]
                        if "narration_statement" not in st_copy and "narration" in st_copy:
                            st_copy["narration_statement"] = st_copy["narration"]
                        expanded_steps.append(st_copy)
                    grouped_script[sid] = expanded_steps
                else:
                    sc_copy = dict(sc)
                    if "narration_statement" not in sc_copy and "voiceover_narration" in sc_copy:
                        sc_copy["narration_statement"] = sc_copy["voiceover_narration"]
                    grouped_script[sid] = [sc_copy]
        elif isinstance(raw_script, list):
            for idx, item in enumerate(raw_script):
                sid = str(item.get("scene_id", item.get("group", idx + 1)))
                if "narration_statement" not in item and "voiceover_narration" in item:
                    item["narration_statement"] = item["voiceover_narration"]
                grouped_script.setdefault(sid, []).append(item)
        elif isinstance(raw_script, dict):
            # Check if keys are scene IDs or metadata
            is_scene_dict = any(k.isdigit() for k in raw_script.keys())
            if is_scene_dict:
                for k, v in raw_script.items():
                    if isinstance(v, list):
                        grouped_script[k] = v
                    elif isinstance(v, dict):
                        grouped_script[k] = [v]
            else:
                # Top level metadata dictionary without 'scenes' key: treat as scene 1
                grouped_script["1"] = [raw_script]
        else:
            raise TypeError("Narration script must be a dictionary or list.")

        cgi_data = copy.deepcopy(grouped_script)
        avatar_strategy: Dict[str, Any] = {}
        audio_clips = []

        cumulative_timeline_sec = 0.0
        print(f"\n{'Scene':<7} | {'Step':<5} | {'Duration':<10} | {'Timeline Range':<18} | {'Runtime Basis'}")
        print("-" * 78)

        # Sort scene keys numerically if possible
        sorted_scene_keys = sorted(
            grouped_script.keys(),
            key=lambda k: int(k) if str(k).isdigit() else 9999
        )

        for group in sorted_scene_keys:
            speech_content_pairs = grouped_script[group]
            if not isinstance(speech_content_pairs, list):
                continue

            for i, speech_content_pair in enumerate(speech_content_pairs):
                # Resolve narration content
                narration_content = speech_content_pair.get("narration_statement")
                if not narration_content:
                    narration_content = speech_content_pair.get("voiceover_narration", "")
                if not narration_content:
                    narration_content = speech_content_pair.get("narration", "")

                cleaned_narration = clean_narration_latex(narration_content)
                run_times: List[float] = []
                step_bases: List[str] = []
                statements_list: List[Dict[str, Any]] = []

                if cleaned_narration.strip().strip("<>").lower() == "silence":
                    dur = 1.0
                    run_times.append(dur)
                    step_bases.append("Silence marker (1.0s)")
                    avatar_strategy[f"group_{group}_pair_{i+1}_silence"] = {"run_time": dur, "position": "no"}
                    statements_list.append({
                        "statement": "<silence>",
                        "runtime": dur
                    })
                else:
                    # 1. Check if statements are explicitly provided in speech_content_pair
                    raw_stmts = speech_content_pair.get("statements")
                    statements_info = []
                    if isinstance(raw_stmts, list) and len(raw_stmts) > 0:
                        for entry in raw_stmts:
                            if isinstance(entry, dict) and "statement" in entry:
                                s_text = clean_narration_latex(entry["statement"]).strip()
                                if s_text:
                                    statements_info.append(s_text)
                            elif isinstance(entry, str) and entry.strip():
                                statements_info.append(clean_narration_latex(entry).strip())

                    # 2. Otherwise, split statements by phonetic/bracket markers or sentence punctuation
                    if not statements_info:
                        parts = re.split(r'(<[^>]+>)', cleaned_narration)
                        for part in parts:
                            if not part:
                                continue
                            if part.startswith('<') and part.endswith('>'):
                                statements_info.append(part.strip('<>').strip())
                            else:
                                sub_parts = re.split(r'(?<=[.?!])\s+', part)
                                for sp in sub_parts:
                                    if sp.strip():
                                        statements_info.append(sp.strip())

                    if not statements_info:
                        statements_info = [cleaned_narration] if cleaned_narration else ["Statement"]

                    total_stmts = len(statements_info)
                    unified_audio = os.path.join(audio_element_dir, f"group_{group}_pair_{i+1}_statement1.wav")
                    unified_trans = os.path.join(base_folder, "transcripts", f"group_{group}_pair_{i+1}_statement1_word_level.json")

                    if os.path.exists(unified_audio) and os.path.exists(unified_trans):
                        pair_dur = probe_audio_duration(unified_audio)
                        try:
                            with open(unified_trans, "r", encoding="utf-8") as tf:
                                trans_segs = json.load(tf)
                        except Exception:
                            trans_segs = []

                        if trans_segs and len(trans_segs) > 0:
                            statements_list = []
                            run_times = []
                            step_bases = []
                            for idx_s, seg in enumerate(trans_segs):
                                s_text = seg.get("text", "").strip()
                                s_dur = round(float(seg.get("end", 0.0)) - float(seg.get("start", 0.0)), 3)
                                statements_list.append({
                                    "statement": s_text,
                                    "runtime": s_dur,
                                    "start": seg.get("start"),
                                    "end": seg.get("end")
                                })
                                run_times.append(s_dur)
                                step_bases.append(f"Whisper Transcript Timestamp ({s_dur}s)")
                            total_section_time = pair_dur
                            if AudioFileClip is not None:
                                try:
                                    audio_clips.append(AudioFileClip(unified_audio))
                                except Exception:
                                    pass
                        else:
                            # Proportional allocation of pair_dur across statements_info
                            total_words = max(1, sum(max(1, len(s.split())) for s in statements_info))
                            statements_list = []
                            run_times = []
                            step_bases = []
                            alloc_sum = 0.0
                            for j, stmt in enumerate(statements_info):
                                w_cnt = max(1, len(stmt.split()))
                                if j == total_stmts - 1:
                                    s_dur = round(max(0.1, pair_dur - alloc_sum), 3)
                                else:
                                    s_dur = round(pair_dur * (w_cnt / total_words), 3)
                                alloc_sum += s_dur
                                run_times.append(s_dur)
                                step_bases.append(f"Proportional Audio Split ({s_dur}s)")
                                statements_list.append({"statement": stmt, "runtime": s_dur})
                            total_section_time = pair_dur
                            if AudioFileClip is not None:
                                try:
                                    audio_clips.append(AudioFileClip(unified_audio))
                                except Exception:
                                    pass
                    else:
                        allocated_so_far = 0.0
                        for j, stmt in enumerate(statements_info):
                            dur, basis, audio_path = self.extract_statement_timing(
                                group=str(group),
                                pair_idx=i + 1,
                                stmt_idx=j + 1,
                                total_stmts=total_stmts,
                                statement_text=stmt,
                                speech_content_pair=speech_content_pair,
                                audio_element_dir=audio_element_dir,
                                all_statements=statements_info,
                                allocated_so_far=allocated_so_far
                            )
                            dur = round(float(dur), 3)
                            allocated_so_far = round(allocated_so_far + dur, 3)
                            run_times.append(dur)
                            step_bases.append(basis)

                            key_name = os.path.basename(audio_path) if audio_path else f"group_{group}_pair_{i+1}_stmt{j+1}"
                            avatar_strategy[key_name] = {"run_time": dur, "position": "no"}

                            statements_list.append({
                                "statement": stmt,
                                "runtime": dur
                            })

                            if audio_path and os.path.exists(audio_path):
                                if AudioFileClip is not None:
                                    try:
                                        audio_clips.append(AudioFileClip(audio_path))
                                    except Exception:
                                        pass

                        total_section_time = round(sum(run_times), 3)

                # Ensure standard fields in cgi_data
                if "narration_statement" not in cgi_data[group][i]:
                    cgi_data[group][i]["narration_statement"] = cleaned_narration

                # Clean up matching_section formatting if present
                if "matching_section" in cgi_data[group][i]:
                    orig_match = cgi_data[group][i]["matching_section"]
                    cleaned_match = re.sub(r'^(Visual:\s*)+', '', orig_match)
                    cgi_data[group][i]["matching_section"] = cleaned_match

                # Populate exact timecodes
                start_sec = round(cumulative_timeline_sec, 3)
                end_sec = round(start_sec + total_section_time, 3)
                cumulative_timeline_sec = end_sec

                cgi_data[group][i]["run_time"] = total_section_time
                cgi_data[group][i]["duration"] = total_section_time
                cgi_data[group][i]["start_time"] = start_sec
                cgi_data[group][i]["end_time"] = end_sec
                cgi_data[group][i]["statements"] = statements_list
                if os.path.exists(unified_audio):
                    cgi_data[group][i]["audio_file"] = os.path.basename(unified_audio)
                    cgi_data[group][i]["audio_path"] = os.path.abspath(unified_audio)

                if "audio_timing" in cgi_data[group][i] and isinstance(cgi_data[group][i]["audio_timing"], dict):
                    cgi_data[group][i]["audio_timing"]["start_time"] = start_sec
                    cgi_data[group][i]["audio_timing"]["end_time"] = end_sec
                    cgi_data[group][i]["audio_timing"]["duration"] = total_section_time

                # Display summary row
                primary_basis = step_bases[0] if step_bases else "Duration Extracted"
                if len(step_bases) > 1:
                    primary_basis += f" (+{len(step_bases)-1} statements)"
                time_range_str = f"[{start_sec:05.1f}s -> {end_sec:05.1f}s]"
                print(f"Scene {group:<1} | #{i+1:<4} | {total_section_time:>5.2f}s     | {time_range_str:<18} | {primary_basis}")
                if len(statements_list) > 1:
                    for s_idx, s_entry in enumerate(statements_list, 1):
                        s_text = (s_entry["statement"][:42] + "...") if len(s_entry["statement"]) > 42 else s_entry["statement"]
                        print(f"   ↳ Stmt {s_idx}: {s_entry['runtime']:>5.2f}s | {s_text}")

        print("-" * 78)
        print(f"⏱️ Total Estimated Video Duration: {cumulative_timeline_sec:.2f}s ({cumulative_timeline_sec/60:.2f} min)")

        # Concatenate audio files if present on disk
        final_output_path = None
        if audio_clips and concatenate_audioclips is not None:
            try:
                concat_audio = os.path.join(audio_concat_scene_dir, "output_low_volume.mp3")
                scene_audio = concatenate_audioclips(audio_clips)
                scene_audio.write_audiofile(concat_audio, fps=44100, logger=None)
                for clip in audio_clips:
                    clip.close()
                scene_audio.close()

                final_output_path = os.path.join(audio_concat_scene_dir, "final_output.mp3")
                self.increase_audio_volume(concat_audio, final_output_path, volume_factor=1.5)
                print(f"✅ Stitched scene audio saved to: {final_output_path}")
            except Exception as e:
                print(f"⚠️ Audio concatenation skipped: {e}")
    

        # Save CGI_Input.json directly inside metadata_blueprints
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        os.makedirs(meta_dir, exist_ok=True)
        timed_storyboard_file = os.path.join(meta_dir, "CGI_Input.json")
        self._write_json(timed_storyboard_file, cgi_data)
        print(f"✅ CGI Input timing manifest written to: {timed_storyboard_file}")

        # Save avatar_strategy.json directly inside metadata_blueprints
        avatar_strategy_file = os.path.join(meta_dir, "avatar_strategy.json")
        self._write_json(avatar_strategy_file, avatar_strategy)
        print(f"✅ Avatar strategy timing map written to: {avatar_strategy_file}")

        # Auto-generate word-level transcripts for all scene audios via transcribe.py
        try:
            from word_transcriber import get_or_create_word_transcript
            for gid in cgi_data.keys():
                get_or_create_word_transcript(base_folder, gid)
        except Exception as e:
            print(f"ℹ️ Word-level transcription hook: {e}")

        return final_output_path, timed_storyboard_file

    # --------------------------------------------------------------------------
    # Multi-topic Pipeline Runner
    # --------------------------------------------------------------------------
    def process_files(self, target_topic_id: Optional[str] = None):
        """
        Executes timing manifest generation across all topics listed in the tracker,
        or processes local directory files if no pipeline tracker is configured.
        """
        if self.input_tracker_path and os.path.exists(self.input_tracker_path):
            input_tracker = self._load_json(self.input_tracker_path)
            if input_tracker:
                print(f"Found {len(input_tracker)} topics in input tracker.")
                for topic_id, input_entry in input_tracker.items():
                    if target_topic_id and topic_id != target_topic_id:
                        continue
                    if not input_entry.get("processed", False):
                        continue

                    output_tracker = self._load_json(self.output_tracker_path) if self.output_tracker_path else {}
                    if topic_id in output_tracker and output_tracker[topic_id].get("processed", False):
                        print(f"Skipping {topic_id}: Already processed.")
                        continue

                    print(f"\nProcessing {topic_id}...")
                    base_folder = os.path.join(self.input_folder, topic_id)
                    config_path = os.path.join(base_folder, "ex_config.json")

                    try:
                        final_audio_path, timed_storyboard_path = self.generate_audio(
                            narration_file=input_entry.get("output_path", os.path.join(base_folder, "CGI_Input.json")),
                            base_folder=base_folder,
                            config_file=config_path if os.path.exists(config_path) else None
                        )
                        audio_folder_path = os.path.join(base_folder, "audio_elements")
                        self._safe_update_output_tracker(
                            item_id=topic_id,
                            topic_name=input_entry.get("topic_name", topic_id),
                            audio_folder_path=audio_folder_path,
                            concatenated_audio_path=final_audio_path,
                            timed_storyboard_path=timed_storyboard_path,
                            processed=True,
                            failure_reason=""
                        )
                    except Exception as e:
                        print(f"❌ Error processing {topic_id}: {e}")
                        self._safe_update_output_tracker(
                            item_id=topic_id,
                            topic_name=input_entry.get("topic_name", topic_id),
                            audio_folder_path="",
                            concatenated_audio_path="",
                            timed_storyboard_path="",
                            processed=False,
                            failure_reason=str(e)
                        )
                return

        # Standalone local directory fallback
        curr_dir = os.path.abspath(self.input_folder)
        local_candidates = [
            os.path.join(curr_dir, "sample_storyboard.json"),
            os.path.join(curr_dir, "CGI_Input.json"),
            os.path.join(curr_dir, "instructions.json"),
            os.path.join(curr_dir, "narration.json"),
        ]
        target_file = next((f for f in local_candidates if os.path.exists(f)), None)
        if target_file:
            config_path = os.path.join(curr_dir, "ex_config.json")
            self.generate_audio(
                narration_file=target_file,
                base_folder=curr_dir,
                config_file=config_path if os.path.exists(config_path) else None
            )
        else:
            print(f"ℹ️ No storyboard files found in {curr_dir}. Specify --narration or --base-folder.")

    # Method aliases for semantic clarity
    populate_runtime = generate_audio
    populate_manifest = generate_audio


# Backward-compatibility alias
GenerateAudio = PopulateAudioRunTime


# ==============================================================================
# CLI Entry Point
# ==============================================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Audio Runtime & Duration Manifest")
    parser.add_argument("--topic", type=str, default=None, help="Target specific topic ID")
    parser.add_argument("--narration", type=str, default=None, help="Path to narration/storyboard JSON")
    parser.add_argument("--base-folder", type=str, default=None, help="Path to project base folder")
    parser.add_argument("--config", type=str, default=None, help="Path to ex_config.json")
    args = parser.parse_args()

    workflow_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(workflow_dir)
    narration_tracker = os.path.join(parent_dir, "ppt_trackers", "1_instruction_design_output_tracker.json")
    audio_tracker = os.path.join(parent_dir, "ppt_trackers", "5_audio_output_tracker.json")

    base_dir = args.base_folder or workflow_dir

    if args.narration:
        stage = PopulateAudioRunTime(output_tracker_path=audio_tracker, input_folder=base_dir)
        stage.generate_audio(
            narration_file=args.narration,
            base_folder=base_dir,
            config_file=args.config or os.path.join(base_dir, "ex_config.json")
        )
    else:
        stage = PopulateAudioRunTime(
            input_tracker_path=narration_tracker,
            output_tracker_path=audio_tracker,
            input_folder=base_dir
        )
        stage.process_files(target_topic_id=args.topic)

# Alias for backward-compatibility with pipeline runners
GenerateAudio = PopulateAudioRunTime

