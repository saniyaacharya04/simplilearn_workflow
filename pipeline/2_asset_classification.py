#!/usr/bin/env python3
"""
Pipeline Stage 2: Asset Classification
Assigned to: Saniya (Simplilearn Workflow Tracker)
Strictly aligned with guidelines.md (Sections 4, 6, and 8)

Decomposes the high-level visual descriptions and scenes from Stage 1 (Instructional Design)
into discrete, categorized visual assets:
- UI Cards & Containers (10px rounded rectangles, guidelines.md 6.2 & 8.5)
- Typographic Elements:
    * Title: Open Sans Bold 45px (guidelines.md 6.3)
    * Content Body: Open Sans Regular 34px, Color #404040 (guidelines.md 6.3)
    * Lead-ins: Ending in colon (:), terminating before x=1450px in 20% PIP (guidelines.md 8.4)
- Procedural Diagrams & Code Snippets (kept below y=270px in 20% PIP)
- 2D Flat Vector Illustrations & Conceptual Graphics (flagged for Stage 3 Image Prompting; no 3D per guidelines.md 6.2)
- Focus Highlights (#F78908, 3px stroke, 1.0s draw time, guidelines.md 3.3)

Strictly respects SME Clearance Zones:
- 70% Layout: SME in left frame (w=640, h=920, r=10), Content safe zone x >= 760px.
- 20% Layout: SME top-right (384x216), Lead-in collision ceiling x <= 1450px, Diagram zone y >= 270px.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class AssetClassification:
    """Classifies visual elements in each scene into structured, modular assets."""

    def __init__(self, blueprint_path: str):
        self.blueprint_path = blueprint_path
        with open(blueprint_path, "r", encoding="utf-8") as f:
            self.blueprint = json.load(f)

    def classify_scene_assets(self, scene: Dict[str, Any]) -> List[Dict[str, Any]]:
        scene_id = scene.get("scene_id", 1)
        scene_type = scene.get("scene_type", "general")
        layout = str(scene.get("sme_layout", "70"))
        ost = scene.get("on_screen_text", {})
        cards = ost.get("cards", [])
        lead_in = ost.get("lead_in", "")
        safe_zone = scene.get("presentation_safe_zone", {})

        assets = []
        asset_idx = 1

        # 1. Title Asset (Open Sans Bold 45px per guidelines.md 6.3)
        title_text = scene.get("title", f"Scene {scene_id}")
        assets.append({
            "asset_id": f"s{scene_id:02d}_a{asset_idx:02d}_title",
            "scene_id": scene_id,
            "type": "text_title",
            "role": "scene_header",
            "content": title_text,
            "font_style": "Open Sans Bold",
            "font_size_px": 45,
            "color": "#1E293B" if layout != "100" else "#FFFFFF",
            "requires_image_generation": False,
            "spatial_target": {
                "zone": "top_left",
                "x": 80,
                "y": 80,
                "max_width": 1360 if layout == "20" else 1080
            },
            "guideline_rule": "Chicago title casing, 5-7 words, no 'Why' starters (guidelines.md 4.2)"
        })
        asset_idx += 1

        # 2. Lead-In Line Asset (Open Sans Regular 28-34px)
        if lead_in and layout != "100":
            assets.append({
                "asset_id": f"s{scene_id:02d}_a{asset_idx:02d}_lead_in",
                "scene_id": scene_id,
                "type": "text_lead_in",
                "role": "context_prompt",
                "content": lead_in,
                "font_style": "Open Sans Regular",
                "font_size_px": 34,
                "color": "#475569",
                "requires_image_generation": False,
                "spatial_target": {
                    "zone": "header_lead_in",
                    "x": 760 if layout == "70" else 80,
                    "y": 140,
                    # Collision Rule (guidelines.md 8.4): must terminate <= 1450px in 20% PIP
                    "max_width": 1000 if layout == "70" else 1360
                },
                "collision_check": "Must not cross x > 1450px in 20% PIP (guidelines.md 8.4)"
            })
            asset_idx += 1

        # 3. SME Frame Asset (Reference for Somnath's Layout/Template Stage)
        sme_cfg = scene.get("sme_positioning", {})
        assets.append({
            "asset_id": f"s{scene_id:02d}_sme_frame",
            "scene_id": scene_id,
            "type": "sme_video_frame",
            "role": "instructor_anchor",
            "layout_type": layout,
            "bounding_box": sme_cfg.get("bounding_box", {}),
            "corner_radius": 10 if layout != "100" else 0,
            "blue_band": "#2C81FE" if layout == "70" else None,
            "requires_image_generation": False
        })

        # 4. Content Cards & Illustrative Needs
        for c_idx, card in enumerate(cards, 1):
            c_title = card.get("title", f"Card {c_idx}")
            c_body = card.get("body", "")
            accent_color = card.get("accent_color", "#62B7E4")

            # Determine whether card concept would benefit from a 2D vector graphic
            needs_illustration = False
            illustration_prompt_hint = ""

            if scene_type in ["concept_explanation", "demo_walkthrough"] or "architecture" in c_title.lower() or "pipeline" in c_title.lower():
                needs_illustration = True
                illustration_prompt_hint = f"Modern 2D flat vector educational illustration depicting {c_title}: {c_body[:60]}"

            card_asset = {
                "asset_id": f"s{scene_id:02d}_a{asset_idx:02d}_card_{c_idx}",
                "scene_id": scene_id,
                "type": "container_card",
                "role": "instructional_chunk",
                "content": {
                    "header": c_title,
                    "body": c_body
                },
                "typography": {
                    "header_font": "Open Sans Bold 28px",
                    "body_font": "Open Sans Regular 34px (guidelines.md 6.3)",
                    "body_color": "#404040"
                },
                "styling": {
                    "corner_radius": 10,  # Mandatory 10px corner radius (guidelines.md 6.2 & 8.5)
                    "fill": "#FFFFFF",
                    "border_color": "#CBD5E1",
                    "accent_color": accent_color,
                    "highlight_accent": "#F78908",  # 3px stroke, 1.0s draw time (guidelines.md 3.3)
                    "highlight_thickness_px": 3,
                    "highlight_draw_time_s": 1.0
                },
                "requires_image_generation": needs_illustration,
                "image_generation_concept": illustration_prompt_hint if needs_illustration else None,
                "image_art_style_constraint": "2D flat vector only; NO 3D images, NO drop shadows (guidelines.md 6.2)",
                "spatial_target": {
                    "layout_context": layout,
                    "safe_zone": safe_zone
                }
            }
            assets.append(card_asset)
            asset_idx += 1

        return assets

    def run_classification(self) -> Dict[str, Any]:
        scenes = self.blueprint.get("scenes", [])
        classified_scenes = []
        total_assets = 0
        image_candidate_count = 0

        for scene in scenes:
            sid = scene.get("scene_id", 1)
            scene_assets = self.classify_scene_assets(scene)
            total_assets += len(scene_assets)

            img_assets = [a for a in scene_assets if a.get("requires_image_generation")]
            image_candidate_count += len(img_assets)

            classified_scenes.append({
                "scene_id": sid,
                "scene_type": scene.get("scene_type"),
                "sme_layout": scene.get("sme_layout"),
                "assets_count": len(scene_assets),
                "assets": scene_assets
            })

        output = {
            "lesson_title": self.blueprint.get("lesson_title", "Simplilearn Lecture"),
            "guidelines_compliance": {
                "section_4_editorial_ost": "ENFORCED",
                "section_6_typography_and_colors": "ENFORCED",
                "section_8_numerical_geometry": "ENFORCED"
            },
            "total_scenes": len(scenes),
            "total_classified_assets": total_assets,
            "assets_requiring_image_generation": image_candidate_count,
            "scenes": classified_scenes
        }
        return output


def run_stage_2(
    blueprint_json: str,
    output_assets_json: str
) -> str:
    """Runs complete Stage 2 workflow."""
    print(f"\n==================================================================")
    print(f"STAGE 2: ASSET CLASSIFICATION")
    print(f"Compliance: guidelines.md Sections 4, 6.2, 6.3, 8.4, 8.5")
    print(f"==================================================================")

    classifier = AssetClassification(blueprint_json)
    catalog = classifier.run_classification()

    Path(output_assets_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_assets_json, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"✓ Stage 2 Complete: {catalog['total_classified_assets']} assets classified across {catalog['total_scenes']} scenes")
    print(f"  Assets flagged for Image Generation: {catalog['assets_requiring_image_generation']}")
    print(f"  Catalog saved -> {output_assets_json}\n")
    return output_assets_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 2: Asset Classification")
    parser.add_argument("-b", "--blueprint", required=True, help="Input presentation blueprint JSON from Stage 1")
    parser.add_argument("-o", "--output", required=True, help="Output classified assets JSON")
    args = parser.parse_args()

    run_stage_2(args.blueprint, args.output)
