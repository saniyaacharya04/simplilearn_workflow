#!/usr/bin/env python3
"""
Step 6: Presentation Slide Graphics Generator
Adapted from Kplor Presentation Composer (6_presentation_composer.py & 9_styling_generator.py).
Renders official 1920x1080 slide assets for each scene in the presentation blueprint.
Guarantees geometric clearance for both 70% left box and 20% top-right corner SME layouts.
"""

import os
import sys
import json
import argparse
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import CANVAS_WIDTH, CANVAS_HEIGHT, COLORS


def render_scene_slide(scene_data: Dict[str, Any], output_png: str) -> str:
    """
    Renders an official 1920x1080 slide image for a scene.
    - 70% Layout: Teacher is at x=80 to 720. Slide content stays in right area (x >= 780).
    - 20% Layout: Teacher is at top-right (x >= 1496, y <= 260). Slide content stays clear of top-right.
    """
    canvas = np.full((CANVAS_HEIGHT, CANVAS_WIDTH, 3), 255, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    sme_layout = str(scene_data.get("sme_layout", "70"))
    title = scene_data.get("title", "")
    lead_in = scene_data.get("lead_in_line", "")
    cards = scene_data.get("cards", [])

    if sme_layout == "70":
        start_x = 780
        max_card_w = 1040
    elif sme_layout == "20":
        start_x = 120
        max_card_w = 1320
    else:
        # Full screen 100% has no slide graphics
        cv2.imwrite(output_png, canvas)
        return output_png

    # Title
    cv2.putText(canvas, title[:40], (start_x, 150), font, 1.25, (64, 64, 64), 2, cv2.LINE_AA)

    # Lead-in Line
    if lead_in:
        cv2.putText(canvas, lead_in[:65], (start_x, 225), font, 0.82, (100, 100, 100), 2, cv2.LINE_AA)

    # Cards
    card_start_y = 310
    card_h = 105
    gap_y = 35

    for idx, card in enumerate(cards[:4]):
        cy1 = card_start_y + idx * (card_h + gap_y)
        cy2 = cy1 + card_h
        cx1 = start_x
        cx2 = start_x + max_card_w

        # Parse color
        hex_c = card.get("color_hex", "#62B7E4").lstrip("#")
        try:
            r_c = int(hex_c[0:2], 16)
            g_c = int(hex_c[2:4], 16)
            b_c = int(hex_c[4:6], 16)
            badge_bgr = (b_c, g_c, r_c)
        except Exception:
            badge_bgr = (228, 183, 98)

        # Container
        cv2.rectangle(canvas, (cx1, cy1), (cx2, cy2), (248, 250, 252), -1)
        cv2.rectangle(canvas, (cx1, cy1), (cx2, cy2), (220, 228, 238), 2)

        # Left color indicator
        cv2.rectangle(canvas, (cx1, cy1), (cx1 + 10, cy2), badge_bgr, -1)

        # Number circle badge
        cv2.circle(canvas, (cx1 + 45, cy1 + 52), 18, badge_bgr, -1, cv2.LINE_AA)
        cv2.putText(canvas, str(idx + 1), (cx1 + 38, cy1 + 58), font, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

        # Card Title
        c_title = card.get("card_title", "")
        if c_title:
            cv2.putText(canvas, c_title[:30], (cx1 + 80, cy1 + 42), font, 0.75, (43, 60, 93), 2, cv2.LINE_AA)
            body_y = cy1 + 75
        else:
            body_y = cy1 + 58

        # Card Body Text
        c_text = card.get("card_text", "")
        cv2.putText(canvas, c_text[:75], (cx1 + 80, body_y), font, 0.68, (64, 64, 64), 1, cv2.LINE_AA)

    Path(output_png).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_png, canvas)
    return output_png


def run_stage_6(blueprint_json: str, output_slides_dir: str) -> List[str]:
    """Runs complete Stage 6 workflow."""
    print(f"\n==================================================================")
    print(f"STEP 6: GENERATE 1080P PRESENTATION SLIDE GRAPHICS")
    print(f"==================================================================")

    with open(blueprint_json, "r", encoding="utf-8") as f:
        blueprint = json.load(f)

    Path(output_slides_dir).mkdir(parents=True, exist_ok=True)
    rendered_slides = []

    for scene in blueprint.get("scenes", []):
        sid = scene.get("scene_id", 1)
        layout = str(scene.get("sme_layout", "70"))

        if layout in ("70", "20"):
            slide_file = Path(output_slides_dir) / f"slide_scene_{sid:02d}_{layout}.png"
            render_scene_slide(scene, str(slide_file))
            scene["rendered_slide_png"] = str(slide_file)
            rendered_slides.append(str(slide_file))
            print(f"✓ Rendered Slide {sid} ({layout}% Layout) -> {slide_file.name}")

    # Update blueprint JSON with rendered slide paths
    with open(blueprint_json, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Step 6 Complete: {len(rendered_slides)} slides created in {output_slides_dir}\n")
    return rendered_slides


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 6: Generate Presentation Slide Graphics")
    parser.add_argument("-b", "--blueprint", required=True, help="Input presentation blueprint JSON")
    parser.add_argument("-o", "--output-dir", required=True, help="Output directory for slide PNGs")
    args = parser.parse_args()

    run_stage_6(args.blueprint, args.output_dir)

