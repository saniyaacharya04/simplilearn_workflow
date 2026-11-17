#!/usr/bin/env python3
"""
================================================================================
SIMPLILEARN OSL 3.0 MASTER POST-PRODUCTION PIPELINE RUNNER
================================================================================
Orchestrates Steps 0 through 8 sequentially from raw teacher video to
pedagogical blueprints, dynamic SME framing, asset construction, and diffusion prompts.

AUDIO & VIDEO PREPROCESSING (RAW TEACHER VIDEO):
  Step 0: Audio Cleaner & EBU R128 Normalizer (-16 LUFS)      [0_clean_audio.py]
  Step 1: Speech Transcription & Word-Level Timestamps        [1_transcribe_and_timestamp.py]
  Step 2: Clean Fillers, Retakes & Repeated Sentences         [2_clean_fillers_and_retakes.py]
  Step 3: Synchronous Audio/Video Trimmer                     [3_synchronous_av_trimmer.py]

PEDAGOGICAL & VISUAL PIPELINE (AFTER AUDIO STEPS):
  Step 4: Hook & Pedagogical Blueprint Generation             [4_generate_hook.py]
  Step 5: Instructional Storyboard Design (Dynamic SME 100/70/20) [5_instructional_design.py]
  Step 6: Asset Classification                                [6_asset_classification.py]
  Step 7: Asset Construction (Geometry & RAG Templates)       [7_asset_construction.py]
  Step 8: Image Prompt Generation (2D Flat Vector)            [8_image_prompt_generation.py]
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_stage_script(script_name: str, args_list: list):
    """Executes a pipeline stage script as an isolated subprocess."""
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Pipeline stage script not found: {script_path}")
    cmd = [sys.executable, str(script_path)] + args_list
    res = subprocess.run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Pipeline failed at stage: {script_name}")


def run_master_pipeline(
    input_media: str,
    output_dir: str,
    lesson_title: str = None,
    start_stage: int = None,
    end_stage: int = 8,
    whisper_engine: str = "auto",
    whisper_model: str = "base",
    api_provider: str = "auto"
):
    start_time = time.time()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    input_path = Path(input_media)
    base = input_path.stem.replace("_clean_transcript", "").replace("_step2", "").replace("_transcript", "")
    if not lesson_title:
        lesson_title = base.replace("_", " ").replace("-", " ").title()

    is_video = input_path.suffix.lower() in [".mp4", ".mov", ".mkv", ".avi", ".webm"]

    # Determine default start stage based on input media type
    if start_stage is None:
        start_stage = 0 if is_video else 4

    # Tracked file artifacts
    clean_audio_video   = out_path / f"{base}_step0_clean_audio.mp4"
    timestamps_json     = out_path / f"{base}_step1_timestamps.json"
    decisions_json      = out_path / f"{base}_step2_cut_decisions.json"
    clean_transcript    = out_path / f"{base}_step2_clean_transcript.json"
    trimmed_video       = out_path / f"{base}_step3_trimmed.mp4"
    hook_json           = out_path / f"{base}_hook_blueprint.json"
    blueprint_json      = out_path / f"{base}_storyboard_blueprint.json"
    assets_json         = out_path / f"{base}_classified_assets.json"
    constructed_json    = out_path / f"{base}_constructed_assets.json"
    prompts_json        = out_path / f"{base}_image_prompts.json"

    print("\n" + "=" * 78)
    print(f"🚀 SIMPLILEARN OSL 3.0 MASTER PIPELINE")
    print(f"   Input Media:       {input_media} ({'RAW TEACHER VIDEO' if is_video else 'TRANSCRIPT/CONTEXT'})")
    print(f"   Lesson Title:      {lesson_title}")
    print(f"   Output Folder:     {output_dir}")
    print(f"   Active Stages:     Step {start_stage} -> Step {end_stage}")
    print(f"   API Provider:      {api_provider}")
    print("=" * 78 + "\n")

    # =========================================================================
    # AUDIO & VIDEO PREPROCESSING (STEPS 0 TO 3)
    # =========================================================================
    if is_video:
        # STEP 0: Clean Audio & Loudness Normalization
        if start_stage <= 0 <= end_stage:
            run_stage_script("0_clean_audio.py", [
                "-i", str(input_media),
                "-o", str(clean_audio_video)
            ])

        # STEP 1: Speech Transcription & Word-Level Timestamps
        if start_stage <= 1 <= end_stage:
            media_for_step1 = str(clean_audio_video if clean_audio_video.exists() else input_media)
            run_stage_script("1_transcribe_and_timestamp.py", [
                "-i", media_for_step1,
                "-o", str(timestamps_json),
                "-e", whisper_engine,
                "-m", whisper_model
            ])

        # STEP 2: Clean Fillers, Retakes & Repeated Sentences
        if start_stage <= 2 <= end_stage:
            media_for_step2 = str(clean_audio_video if clean_audio_video.exists() else input_media)
            run_stage_script("2_clean_fillers_and_retakes.py", [
                "-i", media_for_step2,
                "-t", str(timestamps_json),
                "-d", str(decisions_json),
                "-c", str(clean_transcript)
            ])

        # STEP 3: Synchronous AV Trimmer
        if start_stage <= 3 <= end_stage:
            media_for_step3 = str(clean_audio_video if clean_audio_video.exists() else input_media)
            run_stage_script("3_synchronous_av_trimmer.py", [
                "-i", media_for_step3,
                "-d", str(decisions_json),
                "-o", str(trimmed_video)
            ])

    # Ingest source for pedagogical stages: cleaned transcript from Step 2, or input media if starting from text
    pedagogical_transcript_input = str(clean_transcript if clean_transcript.exists() else input_media)

    # =========================================================================
    # PEDAGOGICAL & VISUAL PIPELINE (STEPS 4 TO 8)
    # =========================================================================
    # STEP 4: Hook & Pedagogical Blueprint Generation
    if start_stage <= 4 <= end_stage:
        run_stage_script("4_generate_hook.py", [
            "-i", pedagogical_transcript_input,
            "-o", str(hook_json),
            "-l", lesson_title,
            "-p", api_provider
        ])

    # STEP 5: Instructional Storyboard Design (Dynamic SME Framing)
    if start_stage <= 5 <= end_stage:
        run_stage_script("5_instructional_design.py", [
            "-t", pedagogical_transcript_input,
            "-o", str(blueprint_json),
            "-l", lesson_title,
            "-p", api_provider
        ])

    # STEP 6: Asset Classification
    if start_stage <= 6 <= end_stage:
        run_stage_script("6_asset_classification.py", [
            "-b", str(blueprint_json),
            "-o", str(assets_json)
        ])

    # STEP 7: Asset Construction (Geometry & RAG Templates)
    if start_stage <= 7 <= end_stage:
        run_stage_script("7_asset_construction.py", [
            "-a", str(assets_json),
            "-b", str(blueprint_json),
            "-o", str(constructed_json),
            "-p", api_provider
        ])

    # STEP 8: Image Prompt Generation
    if start_stage <= 8 <= end_stage:
        run_stage_script("8_image_prompt_generation.py", [
            "-a", str(assets_json),
            "-o", str(prompts_json),
            "-p", api_provider
        ])

    elapsed = time.time() - start_time
    print("=" * 78)
    print(f"🎉 PIPELINE EXECUTION COMPLETED IN {elapsed:.1f}s")
    if is_video and clean_audio_video.exists():
        print(f"   0. Clean Audio Video:    {clean_audio_video}")
    if is_video and timestamps_json.exists():
        print(f"   1. Timestamps:           {timestamps_json}")
    if is_video and clean_transcript.exists():
        print(f"   2. Clean Transcript:     {clean_transcript}")
    if is_video and trimmed_video.exists():
        print(f"   3. Trimmed AV Video:     {trimmed_video}")
    if hook_json.exists():
        print(f"   4. Hook Blueprint:       {hook_json}")
    if blueprint_json.exists():
        print(f"   5. Storyboard Blueprint: {blueprint_json}")
    if assets_json.exists():
        print(f"   6. Classified Assets:    {assets_json}")
    if constructed_json.exists():
        print(f"   7. Constructed Assets:   {constructed_json}")
    if prompts_json.exists():
        print(f"   8. Image Prompts:        {prompts_json}")
    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Simplilearn Master Pipeline Runner (Steps 0 to 8)")
    parser.add_argument("-i", "--input", required=True, help="Path to raw teacher video (.mp4) or clean transcript (.json/.txt)")
    parser.add_argument("-o", "--output-dir", default="output/saniya_assigned_stages", help="Output directory")
    parser.add_argument("-l", "--lesson-title", default=None, help="Lesson title")
    parser.add_argument("--start-stage", type=int, default=None, help="Start stage index (0 to 8). Defaults to 0 for video, 4 for text")
    parser.add_argument("--end-stage", type=int, default=8, help="End stage index (0 to 8)")
    parser.add_argument("--whisper-engine", choices=["auto", "local", "groq"], default="auto", help="Whisper STT engine")
    parser.add_argument("--whisper-model", default="base", help="Whisper model size")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM provider")
    args = parser.parse_args()

    run_master_pipeline(
        input_media=args.input,
        output_dir=args.output_dir,
        lesson_title=args.lesson_title,
        start_stage=args.start_stage,
        end_stage=args.end_stage,
        whisper_engine=args.whisper_engine,
        whisper_model=args.whisper_model,
        api_provider=args.provider
    )


if __name__ == "__main__":
    main()
