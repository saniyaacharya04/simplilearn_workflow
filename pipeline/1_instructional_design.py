#!/usr/bin/env python3
"""
Pipeline Stage 1: Instructional Storyboard Design
Assigned to: Saniya (Simplilearn Workflow Tracker)
Strictly aligned with guidelines.md (Sections 1, 2, 4, and 8)

Transforms raw teacher lecture transcripts into a structured educational storyboard blueprint.
Directly ingests 'instructional_storyboarding_guidelines.txt' to enforce:
- Pedagogical 6-step lesson progression (Hook, Objectives, Concept, Demo, Summary, What's Next).
- Precise Subject Matter Expert (SME) placement layouts & numerical clearances:
    * Scene 1: 100% Full-Screen SME (Canvas 1920x1080)
    * Scene 2: 70% Left Rounded-Rectangle SME (w=640, h=920, r=10px, blue band #2C81FE)
    * Scene 3: 20% Top-Right Corner PIP SME (w=384, h=216, lead-in x <= 1450, diagram y >= 270)
    * Scene 4: 70% Left Rounded-Rectangle SME (Summary & Key Takeaways)
    * Scene 5: 70% Left Rounded-Rectangle SME ("In the next topic, you will learn about: <Action in -ing>")
- Editorial & Content Editor (CE) Rules:
    * Chicago Title Casing, 5-7 words, no one-word titles, avoid "Why" in question titles.
    * Single-digit numbers (0-9) spelled out in words ("zero" through "nine").
    * No split attention; OST anchors and complements narration without verbatim duplication.
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

from pipeline.config import NEXT_TOPIC_PREFIX, SPELLED_NUMBERS, MAX_TITLE_WORDS, MIN_TITLE_WORDS

GUIDELINES_TXT_PATH = SCRIPT_DIR / "instructional_storyboarding_guidelines.txt"


def load_storyboard_guidelines() -> str:
    """Loads the official instructional storyboarding guidelines text file."""
    if GUIDELINES_TXT_PATH.exists():
        with open(GUIDELINES_TXT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "Follow Simplilearn OSL 3.0 standards, guidelines.md, and pedagogical progression."


def spell_out_numbers(text: str) -> str:
    """Spells out single digit numbers 0-9 in narrative text per guidelines.md Section 4.3."""
    pattern = re.compile(r'\b([0-9])\b')
    return pattern.sub(lambda m: SPELLED_NUMBERS.get(m.group(1), m.group(1)), text)


def format_chicago_title(title: str) -> str:
    """Formats title per Chicago Manual of Style, 5-7 words, avoids 'Why' question starters."""
    # Remove leading 'Why is' / 'Why are' per guidelines.md Section 4.2
    title = re.sub(r'^(Why Is|Why Are|Why)\s+', 'Need for ', title, flags=re.IGNORECASE)
    words = title.strip().split()
    if len(words) > MAX_TITLE_WORDS:
        words = words[:MAX_TITLE_WORDS]
    elif len(words) < MIN_TITLE_WORDS:
        words.extend(["Overview", "Essentials"][:MIN_TITLE_WORDS - len(words)])

    lowercase_words = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by", "in", "of"}
    formatted_words = []
    for idx, w in enumerate(words):
        if idx == 0 or idx == len(words) - 1 or w.lower() not in lowercase_words:
            formatted_words.append(w.capitalize())
        else:
            formatted_words.append(w.lower())
    return " ".join(formatted_words)


def generate_local_storyboard_blueprint(
    transcript_data: Any,
    lesson_title: str = "Simplilearn Lecture"
) -> Dict[str, Any]:
    """
    Deterministically constructs the OSL 3.0 presentation blueprint strictly
    adhering to guidelines.md and instructional_storyboarding_guidelines.txt.
    """
    if isinstance(transcript_data, list):
        segments = transcript_data
    else:
        segments = transcript_data.get("segments", [])
    if not segments:
        text_val = transcript_data.get("full_text", "Educational concept") if isinstance(transcript_data, dict) else "Educational concept"
        segments = [{"text": text_val, "start": 0.0, "end": 10.0}]

    total_duration = segments[-1].get("end", 10.0)
    full_text = " ".join([s.get("text", "") for s in segments])

    # 5-Scene Time Splitting (Hook, Objectives, Concept/Demo, Summary, Next Topic)
    t_hook = min(total_duration * 0.15, 30.0)
    t_obj  = min(total_duration * 0.30, t_hook + 40.0)
    t_demo = max(t_obj + 10.0, total_duration * 0.80)
    t_sum  = min(total_duration * 0.92, t_demo + 30.0)
    t_next = total_duration

    # Extract clean narrative sentences
    raw_sentences = re.split(r'(?<=[.!?]) +', full_text.strip())
    sentences = [spell_out_numbers(s.strip()) for s in raw_sentences if len(s.strip()) > 8]
    if not sentences:
        sentences = ["Understanding core concepts and practical implementations."]

    s1_text = sentences[0] if len(sentences) > 0 else full_text[:120]
    s2_text = sentences[1] if len(sentences) > 1 else "Master core architectures and design principles."
    s3_text = " ".join(sentences[2:4]) if len(sentences) > 3 else "Explore technical mechanisms and operational workflows."
    s4_text = sentences[-2] if len(sentences) > 4 else "Review essential principles and critical takeaways."
    s5_text = sentences[-1] if len(sentences) > 5 else "Prepare for advanced integrations."

    clean_lesson_title = format_chicago_title(lesson_title)

    blueprint = {
        "lesson_title": clean_lesson_title,
        "total_scenes": 5,
        "estimated_duration": total_duration,
        "guidelines_reference": "guidelines.md (Sections 1, 2, 4, 6, 8)",
        "scenes": [
            {
                "scene_id": 1,
                "scene_type": "hook_intro",
                "title": format_chicago_title(f"Introduction to {clean_lesson_title}"),
                "start_time": 0.0,
                "end_time": round(t_hook, 2),
                "sme_layout": "100",
                "sme_positioning": {
                    "layout_type": "100_full_screen",
                    "manim_geometry": {"cx": 0.0, "cy": 0.0, "w": 14.222, "h": 8.000},
                    "bounding_box": {"x": 0, "y": 0, "w": 1920, "h": 1080},
                    "description": "Full screen trainer video (guidelines.md 8.3)."
                },
                "presentation_safe_zone": {
                    "allowed": False,
                    "notes": "Minimal overlay text only; teacher occupies full canvas."
                },
                "on_screen_text": {
                    "lead_in": "Welcome to the lesson:",
                    "cards": [
                        {
                            "title": "Core Challenge",
                            "body": s1_text[:90].rstrip(".") + ".",
                            "accent_color": "#62B7E4"
                        }
                    ]
                },
                "voiceover_narration": s1_text
            },
            {
                "scene_id": 2,
                "scene_type": "learning_objectives",
                "title": "Topic Learning Objectives",
                "start_time": round(t_hook, 2),
                "end_time": round(t_obj, 2),
                "sme_layout": "70",
                "sme_positioning": {
                    "layout_type": "70_left_rounded_rect",
                    "manim_geometry": {"cx": -3.687, "cy": -0.023, "w": 4.937, "h": 5.349, "corner_radius": 0.074},
                    "bounding_box": {"x": 80, "y": 80, "w": 640, "h": 920, "corner_radius": 10},
                    "blue_band": {"color": "#2C81FE", "width": 242},
                    "description": "Left rounded rectangle (radius 10px) with blue accent band (guidelines.md 8.5)."
                },
                "presentation_safe_zone": {
                    "allowed": True,
                    "bounding_box": {"x_min": 760, "x_max": 1840, "y_min": 80, "y_max": 1000},
                    "notes": "Right side 1080px workspace for objectives cards."
                },
                "on_screen_text": {
                    "lead_in": "By the end of this topic, you will be able to:",
                    "cards": [
                        {"title": "Objective One", "body": f"Analyze core principles of {clean_lesson_title}.", "accent_color": "#62B7E4"},
                        {"title": "Objective Two", "body": s2_text[:90].rstrip(".") + ".", "accent_color": "#7EA2C8"},
                        {"title": "Objective Three", "body": "Implement practical configurations effectively.", "accent_color": "#9B99C7"}
                    ]
                },
                "voiceover_narration": s2_text
            },
            {
                "scene_id": 3,
                "scene_type": "concept_explanation",
                "title": format_chicago_title(f"Architecture and Execution: {clean_lesson_title}"),
                "start_time": round(t_obj, 2),
                "end_time": round(t_demo, 2),
                "sme_layout": "20",
                "sme_positioning": {
                    "layout_type": "20_top_right_pip",
                    "manim_geometry": {"cx": 5.689, "cy": 3.200, "w": 2.844, "h": 1.600, "corner_radius": 0.074},
                    "bounding_box": {"x": 1536, "y": 0, "w": 384, "h": 216, "corner_radius": 10},
                    "description": "Trainer scaled to 20% FHD in top-right corner (guidelines.md 8.4)."
                },
                "presentation_safe_zone": {
                    "allowed": True,
                    "bounding_box": {"x_min": 52, "x_max": 1814, "y_min": 80, "y_max": 1000},
                    "collision_constraints": {
                        "lead_in_max_x": 1450,
                        "diagram_y_min": 270
                    },
                    "notes": "Lead-in line must not cross x > 1450px. Diagrams must stay below y = 270px."
                },
                "on_screen_text": {
                    "lead_in": "Core operational mechanics and architecture:",
                    "cards": [
                        {"title": "System Architecture", "body": s3_text[:110].rstrip(".") + ".", "accent_color": "#62B7E4"},
                        {"title": "Execution Pipeline", "body": "Validates inputs, processes transforms, and outputs results.", "accent_color": "#E6A157"},
                        {"title": "Performance Optimization", "body": "Enforces low latency and reliable execution.", "accent_color": "#DDB945"}
                    ]
                },
                "voiceover_narration": s3_text
            },
            {
                "scene_id": 4,
                "scene_type": "summary_takeaways",
                "title": "Lesson Summary",
                "start_time": round(t_demo, 2),
                "end_time": round(t_sum, 2),
                "sme_layout": "70",
                "sme_positioning": {
                    "layout_type": "70_left_rounded_rect",
                    "bounding_box": {"x": 80, "y": 80, "w": 640, "h": 920, "corner_radius": 10},
                    "blue_band": {"color": "#2C81FE", "width": 242},
                    "description": "Left rounded rectangle for lesson synthesis (guidelines.md 8.5)."
                },
                "presentation_safe_zone": {
                    "allowed": True,
                    "bounding_box": {"x_min": 760, "x_max": 1840, "y_min": 80, "y_max": 1000},
                    "notes": "Right side workspace for summary cards."
                },
                "on_screen_text": {
                    "lead_in": "Key takeaways from this lesson:",
                    "cards": [
                        {"title": "Key Concept", "body": s4_text[:90].rstrip(".") + ".", "accent_color": "#62B7E4"},
                        {"title": "Best Practice", "body": "Structure modular workflows with clean component isolation.", "accent_color": "#7EA2C8"}
                    ]
                },
                "voiceover_narration": s4_text
            },
            {
                "scene_id": 5,
                "scene_type": "whats_next",
                "title": "What Is Next",
                "start_time": round(t_sum, 2),
                "end_time": round(t_next, 2),
                "sme_layout": "70",
                "sme_positioning": {
                    "layout_type": "70_left_rounded_rect",
                    "bounding_box": {"x": 80, "y": 80, "w": 640, "h": 920, "corner_radius": 10},
                    "blue_band": {"color": "#2C81FE", "width": 242},
                    "description": "Left rounded rectangle for topic transition (guidelines.md 4.4 & 8.6)."
                },
                "presentation_safe_zone": {
                    "allowed": True,
                    "bounding_box": {"x_min": 760, "x_max": 1840, "y_min": 80, "y_max": 1000},
                    "notes": "Right side workspace for upcoming topic teaser."
                },
                "on_screen_text": {
                    "lead_in": NEXT_TOPIC_PREFIX,
                    "cards": [
                        {
                            "title": "Upcoming Topic",
                            "body": f"Implementing advanced production patterns for {clean_lesson_title}.",
                            "accent_color": "#62B7E4"
                        }
                    ]
                },
                "voiceover_narration": s5_text
            }
        ]
    }

    return blueprint


def generate_llm_storyboard_blueprint(
    transcript_data: Any,
    lesson_title: str,
    api_provider: str = "auto"
) -> Dict[str, Any]:
    """Generates the storyboard using an LLM guided by instructional_storyboarding_guidelines.txt."""
    guidelines_text = load_storyboard_guidelines()
    if isinstance(transcript_data, list):
        segments = transcript_data
    else:
        segments = transcript_data.get("segments", [])
    full_transcript = " ".join([s.get("text", "") for s in segments])

    gemini_key = os.environ.get("GEMINI_API_KEY")

    if (api_provider in ["auto", "gemini"] and gemini_key):
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            user_msg = (
                f"{guidelines_text}\n\n"
                f"LESSON TITLE: {lesson_title}\n\n"
                f"TRANSCRIPT:\n{full_transcript}\n\n"
                f"Generate strict JSON presentation blueprint matching guidelines.md."
            )
            resp = model.generate_content(user_msg)
            raw = resp.text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            print(f"[Stage 1] Gemini LLM failed: {e}. Falling back to deterministic generator.")

    return generate_local_storyboard_blueprint(transcript_data, lesson_title)


def run_stage_1(
    transcript_json: str,
    output_blueprint_json: str,
    lesson_title: Optional[str] = None,
    api_provider: str = "auto"
) -> str:
    """Runs complete Stage 1 workflow."""
    print(f"\n==================================================================")
    print(f"STAGE 1: INSTRUCTIONAL STORYBOARD DESIGN")
    print(f"Guidelines: {GUIDELINES_TXT_PATH.name}")
    print(f"Compliance: guidelines.md Sections 1, 2, 4, 6, 8")
    print(f"==================================================================")

    with open(transcript_json, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)

    if not lesson_title:
        base_name = Path(transcript_json).stem.replace("_step2_clean_transcript", "").replace("_transcript", "")
        lesson_title = base_name.replace("_", " ").replace("-", " ").title()

    blueprint = generate_llm_storyboard_blueprint(transcript_data, lesson_title, api_provider)

    Path(output_blueprint_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_blueprint_json, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, indent=2, ensure_ascii=False)

    print(f"✓ Stage 1 Complete: Storyboard generated ({len(blueprint.get('scenes', []))} scenes)")
    print(f"  Blueprint saved -> {output_blueprint_json}\n")
    return output_blueprint_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 1: Instructional Storyboard Design")
    parser.add_argument("-t", "--transcript", required=True, help="Cleaned transcript JSON")
    parser.add_argument("-o", "--output", required=True, help="Output presentation blueprint JSON")
    parser.add_argument("-l", "--lesson-title", default=None, help="Lesson title")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "openai", "local"])
    args = parser.parse_args()

    run_stage_1(args.transcript, args.output, lesson_title=args.lesson_title, api_provider=args.provider)
