#!/usr/bin/env python3
"""
Simplilearn OSL 3.0 Pipeline Runner
Reference: Simplilearn Workflow Standards & Pedagogical Architecture

Integrated Pipeline Stages:
  0. Hook & Pedagogical Blueprint Generation           [0_generate_hook.py]
     - Extracts opening motivational hook, learning goals, problem context, and initial framing.
  1. Instructional Storyboard Design                  [1_instructional_design.py]
     - Accounts for dynamic SME positioning (100% Full, 70% Left Rounded Rect, 20% PIP Corner).
     - Governed by: instructional_storyboarding_guidelines.txt
  2. Asset Classification                              [2_asset_classification.py]
     - Categorizes cards, text blocks, diagrams, and illustration needs.
  3. Image Prompt Generation                           [3_image_prompt_generation.py / 4_image_prompt_generation.py]
     - Generates diffusion prompts for assets using color_guidelines.txt and 2D flat vector style.
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
    """Executes a pipeline script as an isolated subprocess."""
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Pipeline stage script not found: {script_path}")
    cmd = [sys.executable, str(script_path)] + args_list
    res = subprocess.run(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Pipeline failed at stage: {script_name}")


def run_assigned_pipeline(
    input_transcript: str,
    output_dir: str,
    lesson_title: str = None,
    api_provider: str = "auto",
    start_stage: int = 0,
    end_stage: int = 3
):
    start_time = time.time()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    base = Path(input_transcript).stem.replace("_clean_transcript", "").replace("_step2", "").replace("_transcript", "")
    if not lesson_title:
        lesson_title = base.replace("_", " ").replace("-", " ").title()

    # Tracked output artifacts
    hook_json      = out_path / f"{base}_hook_blueprint.json"
    blueprint_json = out_path / f"{base}_storyboard_blueprint.json"
    assets_json    = out_path / f"{base}_classified_assets.json"
    prompts_json   = out_path / f"{base}_image_prompts.json"

    print("\n" + "=" * 75)
    print(f"🚀 SIMPLILEARN OSL 3.0 PIPELINE")
    print(f"   Input Transcript:  {input_transcript}")
    print(f"   Lesson Title:      {lesson_title}")
    print(f"   Output Folder:     {output_dir}")
    print(f"   Stages:            Stage {start_stage} -> Stage {end_stage}")
    print(f"   API Provider:      {api_provider}")
    print("=" * 75 + "\n")

    # STAGE 0: Hook & Pedagogical Blueprint Generation
    if start_stage <= 0 <= end_stage:
        run_stage_script("0_generate_hook.py", [
            "-i", str(input_transcript),
            "-o", str(hook_json),
            "-l", lesson_title,
            "-p", api_provider
        ])

    # STAGE 1: Instructional Storyboard Design
    if start_stage <= 1 <= end_stage:
        run_stage_script("1_instructional_design.py", [
            "-t", str(input_transcript),
            "-o", str(blueprint_json),
            "-l", lesson_title,
            "-p", api_provider
        ])

    # STAGE 2: Asset Classification
    if start_stage <= 2 <= end_stage:
        run_stage_script("2_asset_classification.py", [
            "-b", str(blueprint_json),
            "-o", str(assets_json)
        ])

    # STAGE 3 / 4: Image Prompt Generation
    if start_stage <= 3 <= end_stage or start_stage <= 4 <= end_stage:
        prompt_script = "3_image_prompt_generation.py" if (SCRIPT_DIR / "3_image_prompt_generation.py").exists() else "4_image_prompt_generation.py"
        run_stage_script(prompt_script, [
            "-a", str(assets_json),
            "-o", str(prompts_json),
            "-p", api_provider
        ])

    elapsed = time.time() - start_time
    print("=" * 75)
    print(f"🎉 PIPELINE EXECUTION COMPLETED IN {elapsed:.1f}s")
    if hook_json.exists():
        print(f"   0. Hook Blueprint:       {hook_json}")
    if blueprint_json.exists():
        print(f"   1. Storyboard Blueprint: {blueprint_json}")
    if assets_json.exists():
        print(f"   2. Classified Assets:    {assets_json}")
    if prompts_json.exists():
        print(f"   3. Image Prompts:        {prompts_json}")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Simplilearn Pipeline Runner (Stages 0 to 4)")
    parser.add_argument("-i", "--input-transcript", required=True, help="Cleaned transcript JSON or text file")
    parser.add_argument("-o", "--output-dir", default="output/saniya_assigned_stages", help="Output directory")
    parser.add_argument("-l", "--lesson-title", default=None, help="Lesson title")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM provider")
    parser.add_argument("--start-stage", type=int, default=0, help="Initial stage to run (default: 0)")
    parser.add_argument("--end-stage", type=int, default=3, help="Terminal stage to run (default: 3)")
    args = parser.parse_args()

    run_assigned_pipeline(
        input_transcript=args.input_transcript,
        output_dir=args.output_dir,
        lesson_title=args.lesson_title,
        api_provider=args.provider,
        start_stage=args.start_stage,
        end_stage=args.end_stage
    )


if __name__ == "__main__":
    main()
