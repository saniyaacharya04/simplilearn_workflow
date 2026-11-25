#!/usr/bin/env python3
"""
clean_for_fresh_run.py

Safely cleans old rendered videos, review frames, diagnostic logs, and Manim code
for fresh pipeline execution, while preserving upstream assets:
- Clean audio, transcription, and trimmed video (Stages 0A-0D)
- Hook generation (Stage 0)
- Instructional design / storyboard blueprints (Stage 1)
- Asset classification & image prompt metadata (Stages 2-4)
- CGI_Input.json and audio elements (Stage 5)
- Creative asset images (Stage 8)
- Word-level transcripts (transcripts/)
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

# Trackers to reset (Stages 10 to 23)
TRACKERS_TO_RESET = [
    "10_code_generation_tracker.json",
    "11_run_manim_feedback_tracker.json",
    "12_generate_feedback_tracker.json",
    "13_suggest_corrections_tracker.json",
    "14_corrections_implement_tracker.json",
    "15_run_manim_vlm_feedback_tracker.json",
    "16_generate_vlm_feedback_tracker.json",
    "17_generate_triangulation_tracker.json",
    "18_vlm_fix_tracker.json",
    "19_vlm_fixing_stage_tracker.json",
    "20_eng_corrections_tracker.json",
    "21_timing_adjustment_tracker.json",
    "22_final_render_tracker.json",
    "23_sme_post_production_tracker.json",
]

# Output subdirectories to delete for fresh render
OUTPUT_DIRS_TO_DELETE = [
    "audio_integrated_videos",
    "manim_time_synced_videos",
    "sme_overlaid_scenes",
    "verification_screenshots",
    "qa_verification_frames",
    "qa_sme_frames",
    "current_review_frames",
    "debug_frames",
    "correction_insights",
    "correction_insights_vlm",
    "llm_error_reports",
    "llm_error_reports_vlm",
    "specific_suggestions",
    "specific_suggestions_vlm",
    "vlm_fixing_stage",
    "vlm_inputs",
    "visual_triangulation",
    "manim_styled_codes",
    "manim_time_synced_code",
]

# Specific video files to delete in topic root
OUTPUT_FILES_TO_DELETE = [
    "*_FINAL.mp4",
    "*_FINAL_WITH_SME.mp4",
    "concat_list.txt",
]


def clean_topic_directory(topic_dir: Path, dry_run: bool = False):
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Cleaning topic folder: {topic_dir.name}")
    print("=" * 70)

    # 1. Clean subdirectories
    for d_name in OUTPUT_DIRS_TO_DELETE:
        target_dir = topic_dir / d_name
        if target_dir.exists():
            n_files = len(list(target_dir.glob("*")))
            print(f"  [-] Directory: {d_name} ({n_files} files)")
            if not dry_run:
                shutil.rmtree(target_dir, ignore_errors=True)

    # 2. Clean specific output video files
    for pat in OUTPUT_FILES_TO_DELETE:
        for f in topic_dir.glob(pat):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  [-] Video/Artifact: {f.name} ({size_mb:.1f} MB)")
            if not dry_run:
                try:
                    f.unlink()
                except Exception as e:
                    print(f"      Error removing {f.name}: {e}")

    print(f"\n[Preserved Assets]")
    preserved = [
        "audio_elements",
        "images",
        "transcripts",
        "metadata_blueprints",
        "CGI_Input.json",
        f"{topic_dir.name}_storyboard_blueprint.json",
        f"{topic_dir.name}_trimmed.mp4",
    ]
    for p in preserved:
        p_path = topic_dir / p
        if p_path.exists():
            print(f"  [+] Kept: {p}")


def reset_trackers(trackers_dir: Path, topic_id: str, dry_run: bool = False):
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Resetting trackers in: {trackers_dir}")
    print("=" * 70)

    for trk_name in TRACKERS_TO_RESET:
        trk_file = trackers_dir / trk_name
        if not trk_file.exists():
            continue
        try:
            with open(trk_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if topic_id in data:
                print(f"  [-] Removing '{topic_id}' from {trk_name}")
                if not dry_run:
                    del data[topic_id]
                    with open(trk_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"  [!] Error checking {trk_name}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean output artifacts and reset trackers for a fresh run")
    parser.add_argument("-t", "--topic", default="types_and_architectures_of_ai_agents_sme", help="Topic directory name")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without modifying files")
    parser.add_argument("--from-stage", type=int, default=10, help="Stage to reset from (default: 10)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    topic_path = repo_root / "output" / args.topic
    trackers_path = repo_root / "ppt_trackers"

    if not topic_path.exists():
        print(f"Topic directory does not exist: {topic_path}")
        sys.exit(1)

    clean_topic_directory(topic_path, dry_run=args.dry_run)
    reset_trackers(trackers_path, args.topic, dry_run=args.dry_run)
    print("\nCleanup complete! You can now run the pipeline afresh with the new settings.")
