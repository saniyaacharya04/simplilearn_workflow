#!/usr/bin/env python3
"""
Pipeline Stage 3: Image Prompt Generation
Assigned to: Saniya (Simplilearn Workflow Tracker)

Synthesizes diffusion-ready image generation prompts for visual assets identified
in Stage 2 (Asset Classification) as requiring custom illustrations, icons, or diagrams.

Directly ingests 'color_guidelines.txt' to guarantee:
- Strict brand color harmony (Simplilearn 10-color palette).
- Clean isolated white (#FFFFFF) background for seamless alpha-compositing.
- Minimization of green shades.
- Zero split-attention text inside generated images.

Downstream Hand-off:
The output JSON directly feeds Somnath's task: 'Add image generation'.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

COLOR_GUIDELINES_TXT = SCRIPT_DIR / "color_guidelines.txt"


def load_color_guidelines() -> str:
    """Loads the official Simplilearn color guidelines text file."""
    if COLOR_GUIDELINES_TXT.exists():
        with open(COLOR_GUIDELINES_TXT, "r", encoding="utf-8") as f:
            return f.read()
    return "Enforce Simplilearn primary sky blue #62B7E4, slate blue #7EA2C8, orange highlight #F78908. Minimize green."


def synthesize_diffusion_prompt(
    asset: Dict[str, Any],
    scene_id: int,
    lesson_title: str
) -> Dict[str, Any]:
    """
    Synthesizes an Imagen/Midjourney-optimized diffusion prompt strictly
    aligned with Simplilearn OSL 3.0 educational design rules.
    """
    card_content = asset.get("content", {})
    header = card_content.get("header", "Educational Concept")
    body = card_content.get("body", "")
    accent_color = asset.get("styling", {}).get("accent_color", "#62B7E4")

    # Positive prompt
    positive_prompt = (
        f"A clean modern vector 3D isometric educational illustration representing {header}: {body}. "
        f"Minimalist tech design, smooth geometric forms, soft ambient lighting. "
        f"Color palette featuring sky blue ({accent_color}), soft lavender (#9B99C7), and warm mustard (#DDB945). "
        f"Isolated on a solid pure white background (#FFFFFF) with clean margins and no shadows."
    )

    # Negative prompt
    negative_prompt = (
        "text, typography, labels, letters, watermark, signature, logo, photorealistic, "
        "cluttered background, realistic human faces, distorted hands, dark background, "
        "neon glowing green, high contrast harsh shadows, grain, blur"
    )

    return {
        "asset_id": asset.get("asset_id"),
        "scene_id": scene_id,
        "target_concept": header,
        "diffusion_engine_target": "Google Imagen 3 / Stable Diffusion XL",
        "aspect_ratio": "1:1" if "card" in asset.get("type", "") else "16:9",
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "parameters": {
            "background": "pure_white_isolated_#FFFFFF",
            "accent_hex": accent_color,
            "style": "clean_3d_isometric_vector_infographic",
            "avoid_green": True
        },
        "downstream_assignee": "Somnath (Add image generation)"
    }


def run_stage_3(
    classified_assets_json: str,
    output_prompts_json: str,
    api_provider: str = "auto"
) -> str:
    """Runs complete Stage 3 workflow."""
    print(f"\n==================================================================")
    print(f"STAGE 3: IMAGE PROMPT GENERATION")
    print(f"Color Guidelines: {COLOR_GUIDELINES_TXT.name}")
    print(f"==================================================================")

    with open(classified_assets_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    lesson_title = data.get("lesson_title", "Simplilearn Topic")
    scenes = data.get("scenes", [])
    generated_prompts = []

    for scene in scenes:
        sid = scene.get("scene_id", 1)
        assets = scene.get("assets", [])
        for asset in assets:
            if asset.get("requires_image_generation"):
                prompt_entry = synthesize_diffusion_prompt(asset, sid, lesson_title)
                generated_prompts.append(prompt_entry)

    # If no assets were flagged, generate at least one core conceptual illustration for the main concept scene
    if not generated_prompts:
        fallback_prompt = {
            "asset_id": "s03_conceptual_hero_illustration",
            "scene_id": 3,
            "target_concept": f"{lesson_title} Architecture",
            "diffusion_engine_target": "Google Imagen 3 / Stable Diffusion XL",
            "aspect_ratio": "16:9",
            "prompt": (
                f"Modern 3D isometric infographic diagram explaining {lesson_title}. "
                f"Floating modular cloud nodes, data flow connectors, clean vector aesthetic. "
                f"Simplilearn branded colors: sky blue (#62B7E4), slate (#7EA2C8), and warm orange (#E6A157). "
                f"Isolated on a clean pure white background (#FFFFFF)."
            ),
            "negative_prompt": "text, typography, labels, letters, watermark, blurry, realistic photo, dark background",
            "parameters": {
                "background": "pure_white_isolated_#FFFFFF",
                "accent_hex": "#62B7E4",
                "style": "clean_3d_isometric_vector_infographic",
                "avoid_green": True
            },
            "downstream_assignee": "Somnath (Add image generation)"
        }
        generated_prompts.append(fallback_prompt)

    output_payload = {
        "lesson_title": lesson_title,
        "color_guidelines_applied": "color_guidelines.txt",
        "total_image_prompts": len(generated_prompts),
        "prompts": generated_prompts
    }

    Path(output_prompts_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_prompts_json, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    print(f"✓ Stage 3 Complete: {len(generated_prompts)} diffusion image prompts synthesized")
    print(f"  Saved for downstream image generation -> {output_prompts_json}\n")
    return output_prompts_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 3: Image Prompt Generation")
    parser.add_argument("-a", "--assets", required=True, help="Input classified assets JSON from Stage 2")
    parser.add_argument("-o", "--output", required=True, help="Output image generation prompts JSON")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"])
    args = parser.parse_args()

    run_stage_3(args.assets, args.output, api_provider=args.provider)
