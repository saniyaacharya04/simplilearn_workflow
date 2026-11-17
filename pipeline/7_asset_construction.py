#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 7: ASSET CONSTRUCTION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 7
   - Script Name: 7_asset_construction.py
   - Primary Class: AssetConstruction
   - Pipeline Role:
     Synthesizes coordinate-driven geometric asset guidelines, spatial bounding boxes,
     and Manim construction blueprints for classified visual components.
     Utilizes vector similarity matching (semantic_matcher_asset.py) against
     pre-built procedural Manim asset templates in pipeline/Creative_Assets/ to supply
     reference code snippets and exact dimensions.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Stage 6 (6_asset_classification.py): Ingests classified assets catalog.
   - Stage 5 (5_instructional_design.py): Ingests storyboard blueprint for SME layout safe zones.
   - Creative Asset Library: pipeline/Creative_Assets/ via semantic_matcher_asset.py.

3. DOWNSTREAM CONSUMERS:
   - Stage 8 (8_image_prompt_generation.py): Ingests asset catalog with construction specs.
   - Code Generation / Manim scenes: Implements procedural Manim objects using construction specs.
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

from pipeline.config import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    SME_LAYOUT_100,
    SME_LAYOUT_70,
    SME_LAYOUT_20,
    SAFE_WORK_AREA,
    COLORS,
    HIGHLIGHT_COLOR,
    HIGHLIGHT_THICKNESS,
    HIGHLIGHT_DRAW_TIME
)

try:
    from pipeline.semantic_matcher_asset import match_manim_snippets
except ImportError:
    try:
        from semantic_matcher_asset import match_manim_snippets
    except ImportError:
        def match_manim_snippets(text: str, top_k: int = 2):
            return []


def remove_code_fences(text: str) -> str:
    """Removes ```json ... ``` or ``` ... ``` wrappers from LLM responses."""
    if not text:
        return ""
    text = re.sub(r"^\s*```(?:json)?\s*\n?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\n?```\s*$", "", text.strip())
    return text.strip()


class AssetConstruction:
    """
    Synthesizes coordinate-driven geometric construction specifications and retrieves
    procedural Manim code templates for classified visual components.
    """

    def __init__(self, api_provider: str = "auto", api_key: Optional[str] = None):
        self.api_provider = api_provider.lower()
        self.api_key = api_key

    def retrieve_reference_snippets(self, asset_desc: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Queries semantic_matcher_asset for relevant procedural Manim templates."""
        try:
            matches = match_manim_snippets(asset_desc, top_k=top_k)
            retrieved = []
            for m in matches[:top_k]:
                p = Path(m["path"])
                content = ""
                if p.exists():
                    try:
                        content = p.read_text(encoding="utf-8")[:1200]
                    except Exception:
                        pass
                retrieved.append({
                    "description": m.get("description", ""),
                    "score": round(float(m.get("score", 0.0)), 3),
                    "template_path": str(p),
                    "snippet_preview": content
                })
            return retrieved
        except Exception as e:
            print(f"[Stage 7] Snippet retrieval notice: {e}")
            return []

    def build_local_construction_spec(
        self,
        asset: Dict[str, Any],
        scene_layout_context: str = "70"
    ) -> Dict[str, Any]:
        """
        Deterministic, rule-based construction specification adhering strictly to
        Simplilearn OSL 3.0 geometry, 10px rounded corners, and dynamic SME safe zones.
        """
        cat = asset.get("type") or asset.get("category") or "card"
        title = asset.get("content") or asset.get("title") or asset.get("role") or "Asset Component"
        accent = asset.get("styling", {}).get("accent_color") or asset.get("color") or "#62B7E4"
        spatial = asset.get("spatial_target", {})
        layout = spatial.get("layout_context") or scene_layout_context

        # Spatial clamping based on dynamic SME framing
        if str(layout) == "70":
            # 70% left SME frame (SME at x in [80, 720]px). Content clamped to x >= 760px.
            manim_bounds = {
                "x_min": -1.48,  # x >= 760px in Manim coords
                "x_max": 6.80,   # right edge margin
                "y_min": -3.20,
                "y_max": 2.20,
                "max_width": 7.80,
                "max_height": 5.20,
                "anchor": "RIGHT"
            }
            sme_clearance_note = "Strict clearance: x >= 760px (x >= -1.48 Manim). Right-side content canvas."
        elif str(layout) == "20":
            # 20% PIP corner (SME at top right [1496, 1880]px, y in [40, 256]px).
            manim_bounds = {
                "x_min": -6.60,
                "x_max": 6.60,
                "y_min": -3.40,
                "y_max": 2.10,   # below SME window at y >= 270px
                "max_width": 13.0,
                "max_height": 5.40,
                "anchor": "CENTER"
            }
            sme_clearance_note = "Wide canvas (1814px): Keep upper-right corner (x > 3.6, y > 2.0) clear for 20% PIP window."
        else:
            # 100% full screen presenter
            manim_bounds = {
                "x_min": -5.0,
                "x_max": 5.0,
                "y_min": -3.0,
                "y_max": -1.5,
                "max_width": 9.0,
                "max_height": 1.5,
                "anchor": "BOTTOM"
            }
            sme_clearance_note = "Presenter 100% full frame. Minimal lower third title card only."

        # RAG retrieval against Creative_Assets
        query_text = f"{title}. {asset.get('visual_role', '')}. {cat}"
        refs = self.retrieve_reference_snippets(query_text, top_k=2)

        return {
            "asset_id": asset.get("asset_id"),
            "category": cat,
            "title": title,
            "manim_class_archetype": "SimplilearnContainerCard" if cat in ["card", "container"] else "SimplilearnDiagramBlock",
            "geometry_spec": {
                "corner_radius": 10,
                "manim_corner_radius": 0.074,
                "fill_color": "#FFFFFF",
                "fill_opacity": 1.0,
                "stroke_color": "#CBD5E1",
                "stroke_width": 2,
                "accent_color": accent,
                "highlight_accent": HIGHLIGHT_COLOR,
                "highlight_thickness_px": HIGHLIGHT_THICKNESS,
                "highlight_draw_time_s": HIGHLIGHT_DRAW_TIME,
                "z_index": 20
            },
            "spatial_anchors": {
                "layout_mode": str(layout),
                "manim_bounds": manim_bounds,
                "sme_clearance_note": sme_clearance_note,
                "anti_collision_rule": "Arrows and connectors must maintain buff >= 0.35 and never intersect text content."
            },
            "structural_layers": {
                "foundation_layer": "Solid RoundedRectangle backing card (#FFFFFF) with 10px rounded corners and drop-shielded border.",
                "primary_structure": f"Header badge with accent color {accent} and Chicago Title Case label.",
                "secondary_structure": "Left-aligned body text container (Open Sans Regular 34px / #404040).",
                "detail_layer": f"Active highlight accent ({HIGHLIGHT_COLOR}) with 1.0s draw animation on step entry."
            },
            "reference_templates": refs
        }

    def construct_assets(
        self,
        classified_catalog: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Iterates over classified assets and synthesizes construction specifications."""
        scenes = classified_catalog.get("scenes", [])
        total_constructed = 0
        constructed_scenes = []

        # Map scene layouts from blueprint if available
        layout_map = {}
        if blueprint and "scenes" in blueprint:
            for sc in blueprint["scenes"]:
                layout_map[sc.get("scene_id")] = str(sc.get("sme_layout", "70"))

        for scene in scenes:
            sid = scene.get("scene_id", 1)
            layout = layout_map.get(sid, "70")
            scene_assets = scene.get("assets") or scene.get("classified_assets") or []
            constructed_assets = []

            for asset in scene_assets:
                spec = self.build_local_construction_spec(asset, scene_layout_context=layout)
                asset_copy = dict(asset)
                asset_copy["construction_spec"] = spec
                constructed_assets.append(asset_copy)
                total_constructed += 1

            constructed_scenes.append({
                "scene_id": sid,
                "scene_title": scene.get("scene_title", ""),
                "sme_layout": layout,
                "total_assets": len(constructed_assets),
                "assets": constructed_assets
            })

        return {
            "total_scenes": len(constructed_scenes),
            "total_constructed_assets": total_constructed,
            "standards_compliance": "Simplilearn OSL 3.0 (10px rounded corners, dynamic SME safe zones, pastel palette)",
            "scenes": constructed_scenes
        }

    def run(
        self,
        classified_assets_path: str,
        output_path: str,
        blueprint_path: Optional[str] = None
    ) -> str:
        """Executes Stage 7 asset construction and writes output JSON."""
        with open(classified_assets_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        blueprint_data = None
        if blueprint_path and Path(blueprint_path).exists():
            with open(blueprint_path, "r", encoding="utf-8") as f:
                blueprint_data = json.load(f)

        constructed = self.construct_assets(catalog, blueprint=blueprint_data)

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(constructed, f, indent=2, ensure_ascii=False)

        return str(out)


def run_stage_7(
    classified_assets_json: str,
    output_constructed_json: str,
    blueprint_json: Optional[str] = None,
    api_provider: str = "auto"
) -> str:
    """Entry point for executing Stage 7."""
    print(f"\n==================================================================")
    print(f"STAGE 7: ASSET CONSTRUCTION (GEOMETRY & SPATIAL ANCHORS)")
    print(f"Role: Synthesizes coordinate-driven Manim blueprints from Creative_Assets")
    print(f"Compliance: guidelines.md Sections 6.2, 6.4, 8.4, 8.5 (OSL 3.0)")
    print(f"==================================================================")

    constructor = AssetConstruction(api_provider=api_provider)
    out_path = constructor.run(
        classified_assets_json,
        output_constructed_json,
        blueprint_path=blueprint_json
    )

    with open(out_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"✓ Stage 7 Complete: {data['total_constructed_assets']} assets constructed across {data['total_scenes']} scenes")
    for sc in data.get("scenes", []):
        print(f"  - Scene {sc.get('scene_id')}: {sc.get('total_assets')} assets with Manim geometry bounds (Layout {sc.get('sme_layout')}%)")
    print(f"  Constructed Catalog saved -> {out_path}\n")
    return out_path


# Backward compatibility alias
run_stage_3 = run_stage_7


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 7: Asset Construction")
    parser.add_argument("-a", "--assets", required=True, help="Input classified assets JSON from Stage 6")
    parser.add_argument("-b", "--blueprint", default=None, help="Optional presentation blueprint JSON from Stage 5")
    parser.add_argument("-o", "--output", required=True, help="Output constructed assets JSON")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM provider")
    args = parser.parse_args()

    run_stage_7(
        args.assets,
        args.output,
        blueprint_json=args.blueprint,
        api_provider=args.provider
    )
