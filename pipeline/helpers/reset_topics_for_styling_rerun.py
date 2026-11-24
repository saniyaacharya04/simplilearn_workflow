#!/usr/bin/env python3
"""
reset_topics_for_styling_rerun.py

Resets tracker entries and downstream output directories for specified topics
so that Stages 18–22 (or 20–22) can re-execute cleanly with updated styling
and layout constraints.
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

STAGE_TRACKER_MAP = {
    0: "0_hook_output_tracker.json",
    1: "1_instruction_design_output_tracker.json",
    2: "2_asset_class_output_tracker.json",
    3: "3_asset_construct_output_tracker.json",
    4: "4_prompt_images_output_tracker.json",
    5: "5_audio_output_tracker.json",
    6: "6_presentation_composer_tracker.json",
    7: "7_experience_planner_tracker.json",
    8: "8_image_generation_tracker.json",
    9: "9_styling_output_tracker.json",
    10: "10_code_generation_tracker.json",
    11: "11_run_manim_feedback_tracker.json",
    12: "12_generate_feedback_tracker.json",
    13: "13_suggest_corrections_tracker.json",
    14: "14_corrections_implement_tracker.json",
    15: "15_run_manim_vlm_feedback_tracker.json",
    16: "16_generate_vlm_feedback_tracker.json",
    17: "17_generate_triangulation_tracker.json",
    18: "18_vlm_fix_tracker.json",
    19: "19_vlm_fixing_stage_tracker.json",
    20: "20_eng_corrections_tracker.json",
    21: "21_timing_adjustment_tracker.json",
    22: "22_final_render_tracker.json",
    23: "23_sme_post_production_tracker.json",
}

STAGE_DIR_MAP = {
    5: ["audio_elements", "audio_concat_dir"],
    8: ["images"],
    10: ["manim_codes"],
    11: ["manim_raw_videos"],
    12: ["llm_error_reports"],
    13: ["specific_suggestions"],
    14: ["manim_extracted_codes"],
    15: ["manim_extracted_videos"],
    16: ["llm_error_reports_vlm"],
    17: ["correction_insights", "correction_insights_vlm"],
    18: ["vlm_inputs", "specific_suggestions_vlm"],
    19: ["vlm_fixing_stage"],
    20: ["manim_styled_codes"],
    21: ["manim_time_synced_code", "manim_time_synced_videos", "manim_code_timing_extract"],
    22: ["audio_integrated_videos", "verification_screenshots"],
    23: ["final_composited_videos", "temp_sme_assembly"],
}

STAGE_FILE_PATTERNS_MAP = {
    0: ["raw_parameters_*.json", "raw_parameters_*.txt"],
    1: ["instructions_*.json", "instructions_raw_*.txt"],
    2: ["asset_classification_*.json", "asset_classification_raw_*.txt"],
    3: ["construction_output_*.json"],
    4: ["image_prompt_*.json"],
    5: ["CGI_Input.json", "avatar_strategy.json", "narration_manifest.json"],
    6: ["enhanced_anim_*.json", "enhanced_anim_temp_*.json", "raw_enhanced_anim_*.txt"],
    7: ["experience_plan_*.json", "experience_plan_temp_*.json", "raw_experience_plan_*.txt"],
    9: [
        "styling_*.json",
        "styling_temp_*.json",
        "raw_styling_*.txt",
    ],
}

def main():
    # Dynamically find repo root regardless of CWD (standalone repo vs monorepo parent)
    script_dir = Path(__file__).resolve().parent
    parent_dir = script_dir.parent
    if (parent_dir / "ppt_trackers").exists() and not (script_dir / "ppt_trackers").exists():
        repo_root = parent_dir
    else:
        repo_root = script_dir
    default_trackers_dir = str(repo_root / "ppt_trackers")
    default_data_dir = str(repo_root / "data_ppt_advanced")

    parser = argparse.ArgumentParser(description="Reset topic trackers and artifact dirs for styling/pipeline re-run.")
    parser.add_argument("--folders", nargs="+", required=True, help="Topic folders to reset")
    parser.add_argument("--from-stage", type=int, default=18, choices=list(range(24)), help="Stage to reset from (0-23, default: 18)")
    parser.add_argument("--keep-audio", action="store_true", help="Preserve audio files (audio_elements, audio_concat_dir, CGI_Input.json, avatar_strategy.json) and Stage 5 audio tracker")
    parser.add_argument("--keep-images", action="store_true", help="Preserve generated images in images/ and Stage 8 tracker")
    parser.add_argument("--trackers-dir", type=str, default=default_trackers_dir, help="Trackers directory")
    parser.add_argument("--data-dir", type=str, default=default_data_dir, help="Data directory")
    args = parser.parse_args()

    trackers_dir = Path(args.trackers_dir).resolve()
    data_dir = Path(args.data_dir).resolve()

    print(f"=== Resetting Topics for Stages {args.from_stage}->23 ===")
    print(f"Topics: {args.folders}")
    print(f"Keep Audio: {args.keep_audio}")
    print(f"Keep Images: {args.keep_images}")
    print(f"Trackers Directory: {trackers_dir}")
    print(f"Data Directory: {data_dir}")

    # Determine stages to clean
    stages_to_reset = [stg for stg in range(args.from_stage, 24)]
    if args.keep_audio:
        if 5 in stages_to_reset:
            stages_to_reset.remove(5)
            print("  [Audio Preserved] Skipping Stage 5 (audio generation) reset.")
        if 1 in stages_to_reset and args.from_stage <= 1:
            # Preserving narration text because existing audio files were synthesized from it
            stages_to_reset.remove(1)
            print("  [Audio Preserved] Preserving Stage 1 narration instructions so audio stays in sync.")
    if args.keep_images:
        if 8 in stages_to_reset:
            stages_to_reset.remove(8)
            print("  [Images Preserved] Skipping Stage 8 (image generation) reset.")

    # 1. Clean folders inside data_dir
    dirs_to_clean = set()
    for stg, dir_list in STAGE_DIR_MAP.items():
        if stg in stages_to_reset:
            dirs_to_clean.update(dir_list)

    # Clean intermediate files inside data_dir
    file_patterns_to_clean = []
    for stg, pat_list in STAGE_FILE_PATTERNS_MAP.items():
        if stg in stages_to_reset:
            file_patterns_to_clean.extend(pat_list)

    for topic in args.folders:
        topic_dir = data_dir / topic
        if not topic_dir.exists():
            # Check if topic exists as a subfolder in data_dir
            sub_matches = list(data_dir.glob(f"*/{topic}"))
            if sub_matches and sub_matches[0].exists():
                topic_dir = sub_matches[0]
            else:
                print(f"[WARN] Topic directory not found: {topic_dir}")
                continue

        for folder_name in dirs_to_clean:
            target_path = topic_dir / folder_name
            if target_path.is_symlink():
                try:
                    target_path.unlink()
                    print(f"  [Cleaned Symlink] {topic}/{folder_name}")
                except Exception as e:
                    print(f"  [WARN] Failed to delete symlink {target_path}: {e}")
            elif target_path.exists():
                try:
                    if target_path.is_dir():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()
                    print(f"  [Cleaned Dir] {topic}/{folder_name}")
                except Exception as e:
                    print(f"  [WARN] Failed to delete {target_path}: {e}")

        for pattern in file_patterns_to_clean:
            for matched_file in topic_dir.glob(pattern):
                try:
                    matched_file.unlink()
                    print(f"  [Cleaned File] {topic}/{matched_file.name}")
                except Exception as e:
                    print(f"  [WARN] Failed to delete file {matched_file}: {e}")

    # 2. Reset tracker files
    for stg in stages_to_reset:
        tracker_filename = STAGE_TRACKER_MAP.get(stg)
        if not tracker_filename:
            continue
        tracker_file = trackers_dir / tracker_filename
        if not tracker_file.exists():
            continue

        try:
            with open(tracker_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            modified = False
            for topic in args.folders:
                if topic in data:
                    del data[topic]
                    modified = True
                    print(f"  [Tracker] Removed {topic} from {tracker_filename}")

            if modified:
                with open(tracker_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"  [WARN] Error resetting {tracker_file}: {e}")

    effective_start = args.from_stage
    if args.keep_audio and args.from_stage == 5:
        effective_start = 6

    print("\n[OK] Reset completed successfully. You can now re-run the pipeline with:")
    print(f"python3 run_pipeline.py --workers 3 --max-manim 2 --start-stage {effective_start} --end-stage 22 --folders {' '.join(args.folders)}")

if __name__ == "__main__":
    main()
