#!/usr/bin/env python3
"""
Simplilearn Video Post-Production Master Pipeline Runner
Orchestrates Steps 0 through 9 sequentially from raw teacher video to broadcast delivery.

Pipeline Stages:
  Step 0: Audio Cleaner & EBU R128 Normalizer (-16 LUFS)      [0_clean_audio.py]
  Step 1: Speech Transcription & Word-Level Timestamps        [1_transcribe_and_timestamp.py]
  Step 2: Clean Fillers, Retakes & Repeated Sentences         [2_clean_fillers_and_retakes.py]
  Step 3: Synchronous Audio/Video Trimmer                     [3_synchronous_av_trimmer.py]
  Step 4: Voiceover Documentation Generator (DOCX & PDF)      [4_generate_voiceover_docs.py]
  Step 5: LLM Instructional Design & Blueprinting             [5_llm_instructional_design.py]
  Step 6: Presentation Slide Graphics Generator               [6_generate_slide_graphics.py]
  Step 7: SME Placement Layouts (100, 70, 20)                 [7_sme_placement_layouts.py]
  Step 8: Multi-Scene Educational Lesson Assembler            [8_multi_scene_assembler.py]
  Step 9: Simplilearn 0.5s White Dissolve Outro               [9_apply_white_dissolve_outro.py]
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
    """Executes a numbered pipeline script as an isolated subprocess."""
    script_path = SCRIPT_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args_list
    res = subprocess.run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Pipeline failed at stage: {script_name}")


def run_full_pipeline(
    input_video: str,
    output_dir: str,
    start_stage: int = 0,
    end_stage: int = 9,
    whisper_engine: str = "auto",
    whisper_model: str = "base",
    llm_provider: str = "auto"
):
    start_time = time.time()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    base = Path(input_video).stem
    lesson_title = base.replace("_", " ").replace("-", " ").title()

    # Tracked file artifacts
    clean_audio_video = out_path / f"{base}_step0_clean_audio.mp4"
    timestamps_json   = out_path / f"{base}_step1_timestamps.json"
    decisions_json    = out_path / f"{base}_step2_cut_decisions.json"
    clean_transcript  = out_path / f"{base}_step2_clean_transcript.json"
    trimmed_video     = out_path / f"{base}_step3_trimmed.mp4"
    blueprint_json    = out_path / f"{base}_step5_presentation_blueprint.json"
    slides_dir        = out_path / "generated_slides"
    assembled_video   = out_path / f"{base}_step8_assembled.mp4"
    final_output      = out_path / f"{base}_SIMPLILEARN_FINAL.mp4"

    print("\n" + "=" * 75)
    print(f"🚀 SIMPLILEARN OSL 3.0 AUTOMATED POST-PRODUCTION PIPELINE")
    print(f"   Input Media:     {input_video} (TEACHER RAW VIDEO ONLY)")
    print(f"   Output Folder:   {output_dir}")
    print(f"   Active Stages:   Step {start_stage} -> Step {end_stage}")
    print("=" * 75 + "\n")

    # STEP 0: Clean Audio
    if start_stage <= 0 <= end_stage:
        run_stage_script("0_clean_audio.py", [
            "-i", str(input_video),
            "-o", str(clean_audio_video)
        ])

    # STEP 1: Transcribe & Timestamps
    if start_stage <= 1 <= end_stage:
        input_for_step1 = str(clean_audio_video if clean_audio_video.exists() else input_video)
        run_stage_script("1_transcribe_and_timestamp.py", [
            "-i", input_for_step1,
            "-o", str(timestamps_json),
            "-e", whisper_engine,
            "-m", whisper_model
        ])

    # STEP 2: Clean Fillers & Retakes
    if start_stage <= 2 <= end_stage:
        input_for_step2 = str(clean_audio_video if clean_audio_video.exists() else input_video)
        run_stage_script("2_clean_fillers_and_retakes.py", [
            "-i", input_for_step2,
            "-t", str(timestamps_json),
            "-d", str(decisions_json),
            "-c", str(clean_transcript)
        ])

    # STEP 3: Synchronous AV Trimmer
    if start_stage <= 3 <= end_stage:
        input_for_step3 = str(clean_audio_video if clean_audio_video.exists() else input_video)
        run_stage_script("3_synchronous_av_trimmer.py", [
            "-i", input_for_step3,
            "-d", str(decisions_json),
            "-o", str(trimmed_video)
        ])

    # STEP 4: Generate Voiceover Documentation
    if start_stage <= 4 <= end_stage:
        run_stage_script("4_generate_voiceover_docs.py", [
            "-t", str(clean_transcript),
            "-o", str(out_path),
            "--title", lesson_title
        ])

    # STEP 5: LLM Instructional Design Blueprint
    if start_stage <= 5 <= end_stage:
        run_stage_script("5_llm_instructional_design.py", [
            "-t", str(clean_transcript),
            "-o", str(blueprint_json),
            "--title", lesson_title,
            "-p", llm_provider
        ])

    # STEP 6: Generate Slide Graphics
    if start_stage <= 6 <= end_stage:
        run_stage_script("6_generate_slide_graphics.py", [
            "-b", str(blueprint_json),
            "-o", str(slides_dir)
        ])

    # STEP 8: Multi-Scene Presentation Assembler
    if start_stage <= 8 <= end_stage:
        run_stage_script("8_multi_scene_assembler.py", [
            "-i", str(trimmed_video),
            "-b", str(blueprint_json),
            "-o", str(assembled_video),
            "-w", str(out_path / "temp_assembly")
        ])

    # STEP 9: Apply 0.5s White Dissolve Outro
    if start_stage <= 9 <= end_stage:
        run_stage_script("9_apply_white_dissolve_outro.py", [
            "-i", str(assembled_video),
            "-o", str(final_output)
        ])

    elapsed = time.time() - start_time
    print("\n" + "=" * 75)
    print(f"🎉 PIPELINE COMPLETED IN {elapsed:.1f}s")
    print(f"   Final Delivery Video: {final_output}")
    print(f"   Voiceover DOCX:       {out_path / f'Voiceover_Sheet_{lesson_title}.docx'}")
    print(f"   Voiceover PDF:        {out_path / f'Voiceover_Sheet_{lesson_title}.pdf'}")
    print(f"   Cut Decisions JSON:   {decisions_json}")
    print(f"   Presentation Plan:    {blueprint_json}")
    print("=" * 75 + "\n")

    return str(final_output)


def main():
    parser = argparse.ArgumentParser(description="Simplilearn Post-Production Master Orchestrator")
    parser.add_argument("-i", "--input", required=True, help="Path to raw teacher video")
    parser.add_argument("-o", "--output-dir", default="output", help="Directory to save outputs")
    parser.add_argument("--start-stage", type=int, default=0, help="Start stage index (0 to 9)")
    parser.add_argument("--end-stage", type=int, default=9, help="End stage index (0 to 9)")
    parser.add_argument("--whisper-engine", choices=["auto", "local", "groq"], default="auto", help="Whisper engine")
    parser.add_argument("--whisper-model", default="base", help="Whisper model size (tiny, base, small, medium)")
    parser.add_argument("--llm-provider", choices=["auto", "gemini", "claude", "openai"], default="auto", help="LLM provider")
    args = parser.parse_args()

    run_full_pipeline(
        input_video=args.input,
        output_dir=args.output_dir,
        start_stage=args.start_stage,
        end_stage=args.end_stage,
        whisper_engine=args.whisper_engine,
        whisper_model=args.whisper_model,
        llm_provider=args.llm_provider
    )


if __name__ == "__main__":
    main()
