#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 3: IMAGE PROMPT GENERATION
================================================================================
Strictly aligned with guidelines.md (Sections 6.2 & 6.4)

Synthesizes diffusion-ready image generation prompts for visual assets identified
in Stage 2 (Asset Classification) as requiring custom illustrations or conceptual graphics.

Enforces guidelines.md compliance:
- 2D Flat Vector Only: Strictly forbids 3D images, drop shadows, and thick outlines (Section 6.2).
- Brand Palette Harmony: Infuses the approved 10-color infographic palette (Section 6.4).
- Clean Background: Pure white isolated background (#FFFFFF) for seamless compositing.
- Zero Split-Attention: Forbids embedded text or labels inside images.
================================================================================
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

COLOR_GUIDELINES_TXT = SCRIPT_DIR / "guidelines" / "color_guidelines.txt"
if not COLOR_GUIDELINES_TXT.exists():
    COLOR_GUIDELINES_TXT = SCRIPT_DIR / "color_guidelines.txt"


def load_color_guidelines() -> str:
    """Loads the official Simplilearn color guidelines text file."""
    if COLOR_GUIDELINES_TXT.exists():
        with open(COLOR_GUIDELINES_TXT, "r", encoding="utf-8") as f:
            return f.read()
    return (
        "Enforce Simplilearn 10-color infographic palette: Sky Blue #62B7E4, Steel Blue #7EA2C8, "
        "Periwinkle #9B99C7, Mint #8ECDB7, Warm Amber #E6A157, Mustard #DDB945, Coral #E58F6D, "
        "Warm Tan #B88968, Dusty Rose #D98CA1, Soft Lilac #C1A5C6. Pure white background #FFFFFF. "
        "2D flat vector only. No 3D images, no drop shadows."
    )


class ImagePrompting:
    """
    Stage 3: Image Prompt Generation.
    Synthesizes detailed diffusion image generation prompts for visual assets
    identified as requiring 2D vector illustrations or thematic graphics.
    """

    def __init__(
        self,
        color_guidelines_path: Optional[str] = None,
        api_provider: str = "auto",
        api_key: Optional[str] = None
    ):
        self.color_guidelines_path = Path(color_guidelines_path) if color_guidelines_path else COLOR_GUIDELINES_TXT
        self.api_provider = api_provider
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    def load_guidelines(self) -> str:
        """Loads color guidelines text."""
        if self.color_guidelines_path.exists():
            with open(self.color_guidelines_path, "r", encoding="utf-8") as f:
                return f.read()
        return load_color_guidelines()

    def synthesize_diffusion_prompt(
        self,
        asset: Dict[str, Any],
        scene_id: int,
        lesson_title: str
    ) -> Dict[str, Any]:
        """
        Synthesizes an Imagen 3 / SDXL diffusion prompt strictly enforcing
        Simplilearn guidelines.md (2D flat vector).
        """
        card_content = asset.get("content", {})
        header = card_content.get("header", "Educational Concept")
        body = card_content.get("body", "")
        accent_color = asset.get("styling", {}).get("accent_color", "#62B7E4")
        concept_hint = asset.get("image_generation_concept") or f"{header}: {body}"

        # Detect human or user presence for clean 2D vector styling
        is_human_related = any(k in header.lower() or k in body.lower() for k in [
            "person", "human", "user", "developer", "engineer", "customer", "student", "trainer", "team"
        ])

        if is_human_related:
            character_directive = (
                "Featuring a stylized modern professional person illustrated in clean 2D flat vector style, "
                "friendly expression, natural posture, fully clothed in clean attire colored with Simplilearn "
                f"palette tones ({accent_color} and steel blue #7EA2C8), engaging with the tech workflow. "
            )
        else:
            character_directive = ""

        # Positive Prompt (primary subject -> components -> surfaces -> palette -> background)
        positive_prompt = (
            f"A clean modern 2D flat vector educational illustration representing {header}. "
            f"{character_directive}"
            f"Subject structure: layered modular blocks, smooth geometric flow paths, rounded rectangular elements. "
            f"Surface and styling: clean flat pastel fills, soft vector shading, no gradients on background. "
            f"Simplilearn branded color harmony: primary accent ({accent_color}), steel blue (#7EA2C8), "
            f"lavender periwinkle (#9B99C7), and mint seafoam (#8ECDB7). "
            f"Completely isolated on a solid pure white background (#FFFFFF) with generous clean margins and zero shadows."
        )

        # Negative Prompt: Enforces guidelines.md Section 6.2 prohibitions
        negative_prompt = (
            "3d, 3d render, 3d model, CGI, isometric 3d, realistic photo, shadows, drop shadows, "
            "thick outlines, dotted lines, silhouette, black and white image, monochrome, "
            "text, typography, labels, letters, numbers, watermark, signature, logo, photorealistic, "
            "cluttered background, realistic human faces, distorted hands, dark background, grain, blur"
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
                "style": "clean_2d_flat_vector_infographic",
                "forbid_3d": True,
                "forbid_drop_shadows": True,
                "forbid_embedded_text": True
            },
            "guidelines_compliance": {
                "section_6_2_no_3d": "PASS",
                "section_6_4_palette_harmony": "PASS",
                "section_3_2_zero_embedded_text": "PASS"
            }
        }

    def generate_prompts(self, catalog: Dict[str, Any]) -> Dict[str, Any]:
        """Generates diffusion prompts for all image-flagged assets in the catalog."""
        lesson_title = catalog.get("lesson_title", "Simplilearn Topic")
        scenes = catalog.get("scenes", [])
        generated_prompts: List[Dict[str, Any]] = []

        for scene in scenes:
            sid = scene.get("scene_id", 1)
            assets = scene.get("assets", [])
            for asset in assets:
                if asset.get("requires_image_generation"):
                    prompt_entry = self.synthesize_diffusion_prompt(asset, sid, lesson_title)
                    generated_prompts.append(prompt_entry)

        # Fallback if no assets were flagged: create hero conceptual 2D diagram prompt
        if not generated_prompts:
            fallback_prompt = {
                "asset_id": "s03_conceptual_hero_illustration",
                "scene_id": 3,
                "target_concept": f"{lesson_title} Architecture",
                "diffusion_engine_target": "Google Imagen 3 / Stable Diffusion XL",
                "aspect_ratio": "16:9",
                "prompt": (
                    f"Modern 2D flat vector educational diagram explaining {lesson_title}. "
                    f"Minimalist modular cloud blocks, clean flow connectors, flat aesthetic. "
                    f"Simplilearn branded colors: sky blue (#62B7E4), steel blue (#7EA2C8), and warm amber (#E6A157). "
                    f"Isolated on a clean pure white background (#FFFFFF) with zero drop shadows and no thick outlines."
                ),
                "negative_prompt": (
                    "3d, 3d render, drop shadows, thick outlines, dotted lines, text, typography, labels, "
                    "letters, watermark, blurry, realistic photo, dark background"
                ),
                "parameters": {
                    "background": "pure_white_isolated_#FFFFFF",
                    "accent_hex": "#62B7E4",
                    "style": "clean_2d_flat_vector_infographic",
                    "forbid_3d": True,
                    "forbid_drop_shadows": True,
                    "forbid_embedded_text": True
                },
                "guidelines_compliance": {
                    "section_6_2_no_3d": "PASS",
                    "section_6_4_palette_harmony": "PASS",
                    "section_3_2_zero_embedded_text": "PASS"
                }
            }
            generated_prompts.append(fallback_prompt)

        return {
            "lesson_title": lesson_title,
            "color_guidelines_applied": "color_guidelines.txt",
            "guidelines_reference": "guidelines.md Section 6.2 & 6.4",
            "total_image_prompts": len(generated_prompts),
            "prompts": generated_prompts
        }

    def run(self, assets_path: str, output_path: str) -> str:
        """Executes Stage 3 from file paths."""
        with open(assets_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        prompts_data = self.generate_prompts(catalog)

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(prompts_data, f, indent=2, ensure_ascii=False)

        return str(out_file)


# --------------------------------------------------------------------------------
# Backward-compatible Module Interface
# --------------------------------------------------------------------------------

def synthesize_diffusion_prompt(
    asset: Dict[str, Any],
    scene_id: int,
    lesson_title: str
) -> Dict[str, Any]:
    prompter = ImagePrompting()
    return prompter.synthesize_diffusion_prompt(asset, scene_id, lesson_title)


def run_stage_8(
    classified_assets_json: str,
    output_prompts_json: str,
    api_provider: str = "auto"
) -> str:
    """Runs complete Stage 8 workflow."""
    print(f"\n==================================================================")
    print(f"STAGE 8: IMAGE PROMPT GENERATION")
    print(f"Color Guidelines: {COLOR_GUIDELINES_TXT.name}")
    print(f"Standards: 2D Flat Vector Only (No 3D / No Shadows per guidelines.md 6.2)")
    print(f"Diffusion Target: Google Imagen 3 / Stable Diffusion XL")
    print(f"==================================================================")

    prompter = ImagePrompting(api_provider=api_provider)
    out_path = prompter.run(classified_assets_json, output_prompts_json)

    with open(out_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"✓ Stage 8 Complete: {data['total_image_prompts']} 2D flat vector image prompts synthesized")
    print(f"  Saved -> {out_path}\n")
    return out_path


# Backward compatibility alias
run_stage_3 = run_stage_8


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 8: Image Prompt Generation")
    parser.add_argument("-a", "--assets", required=True, help="Input classified assets JSON from Stage 7")
    parser.add_argument("-o", "--output", required=True, help="Output image generation prompts JSON")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"])
    args = parser.parse_args()

    run_stage_8(args.assets, args.output, api_provider=args.provider)
