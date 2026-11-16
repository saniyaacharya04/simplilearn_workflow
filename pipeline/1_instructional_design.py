#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 1: INSTRUCTIONAL STORYBOARD DESIGN
================================================================================
Strictly aligned with guidelines.md (Sections 1, 2, 4, and 8)

Transforms raw teacher lecture transcripts into a structured educational
presentation storyboard blueprint with DYNAMIC SME FRAMING.
Directly ingests 'instructional_storyboarding_guidelines.txt' to enforce:
- Dynamic SME Framing Selection Matrix (guidelines.md Section 8 & OSL 3.0 Slide 16):
    * Layout 1: 100% Full-Screen SME (Canvas 1920x1080) for opening hooks, direct address, and sign-offs.
    * Layout 3: 70% Left Rounded-Rectangle SME (w=640, h=920, r=10px, blue band #2C81FE) for
      objectives, chunked cards (2-3 items), summary takeaways, and "What's Next" teasers.
    * Layout 2: 20% Top-Right Corner PIP SME (w=384, h=216, r=10px) for wide architecture diagrams,
      multi-tier pipelines, code snippets, and demonstration workflows (lead-in x <= 1450, diagram y >= 270).
- Dynamic In-Scene Transitions & Movement (Slide 6 & Slide 12):
    * Blue band slide-out to the left when transitioning to 20% PIP.
    * 0.8s broadcast L-to-R swipe transition overlay (play_ltor_swipe) across cut points.
- Pedagogical 6-step lesson progression (Hook, Objectives, Concept, Demo, Summary, What's Next).
- Editorial & Content Editor (CE) Rules:
    * Chicago Title Casing, 5-7 words, no one-word titles, avoid "Why" in question titles.
    * Single-digit numbers (0-9) spelled out in words ("zero" through "nine").
    * No split attention; OST anchors and complements narration without verbatim duplication.
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

from pipeline.config import NEXT_TOPIC_PREFIX, SPELLED_NUMBERS, MAX_TITLE_WORDS, MIN_TITLE_WORDS

GUIDELINES_TXT_PATH = SCRIPT_DIR / "instructional_storyboarding_guidelines.txt"


def clean_narration_latex(text: str) -> str:
    """
    Cleans raw LaTeX markup and converts common mathematical LaTeX expressions 
    into natural spoken English for Text-to-Speech (TTS) narration.
    """
    if not text:
        return ""
    text = re.sub(r'\\binom\{([^}]+)\}\{([^}]+)\}', r'\1 choose \2', text)
    text = re.sub(r'\{([^}]+)\}\s*\\choose\s*\{([^}]+)\}', r'\1 choose \2', text)
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1 over \2', text)
    text = re.sub(r'\\sum_\{([^=]+)=([^}]+)\}\^\{([^}]+)\}', r'sum from \1 equals \2 to \3', text)
    text = re.sub(r'\\sum', 'sum', text)
    text = re.sub(r'\^2\b', ' squared', text)
    text = re.sub(r'\^3\b', ' cubed', text)
    text = re.sub(r'\^\{([^}]+)\}', r' raised to \1', text)
    text = re.sub(r'\^(\w+)', r' raised to \1', text)
    text = re.sub(r'_\{([^}]+)\}', r' sub \1', text)
    text = re.sub(r'_(\w+)', r' sub \1', text)
    text = text.replace(r'\cdot', ' times ')
    text = text.replace(r'\times', ' times ')
    text = text.replace(r'\pm', ' plus or minus ')
    text = text.replace(r'\leq', ' less than or equal to ')
    text = text.replace(r'\geq', ' greater than or equal to ')
    text = text.replace(r'\neq', ' not equal to ')
    text = text.replace(r'\approx', ' approximately ')
    text = text.replace(r'\infty', ' infinity ')
    text = text.replace(r'\rightarrow', ' approaches ')
    text = text.replace(r'\to', ' to ')
    text = re.sub(r'\$\$?', '', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = text.replace('{', '').replace('}', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def spell_out_numbers(text: str) -> str:
    """Spells out single digit numbers 0-9 in narrative text per guidelines.md Section 4.3."""
    pattern = re.compile(r'\b([0-9])\b')
    return pattern.sub(lambda m: SPELLED_NUMBERS.get(m.group(1), m.group(1)), text)


def format_chicago_title(title: str) -> str:
    """
    Formats title per Chicago Manual of Style, 5-7 words.
    Replaces 'Why is' / 'Why are' starters with 'Need for' per guidelines.md Section 4.2.
    """
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


def load_storyboard_guidelines() -> str:
    """Loads the official instructional storyboarding guidelines text file."""
    if GUIDELINES_TXT_PATH.exists():
        with open(GUIDELINES_TXT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "Follow Simplilearn OSL 3.0 standards, guidelines.md, and pedagogical progression with dynamic SME framing."


def resolve_dynamic_sme_framing(
    scene_type: str,
    content_text: str = "",
    card_count: int = 1,
    explicit_layout: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dynamically determines the optimal SME framing layout (100%, 70%, or 20%)
    based on the pedagogical objective, content density, and screen real-estate demands
    per guidelines.md Section 8 and instructional_storyboarding_guidelines.txt Section 3.
    """
    norm_text = content_text.lower()

    if explicit_layout in ["100", "70", "20"]:
        chosen_layout = explicit_layout
        reason = f"Explicitly requested layout {explicit_layout}%"
    else:
        # 1. Check for High Visual Density -> 20% Top-Right PIP
        wide_triggers = [
            "architecture", "pipeline", "diagram", "schematic", "workflow", "system",
            "code", "demo", "runtime", "flow", "execution", "components", "infrastructure",
            "cycle", "loop", "table", "dataset", "framework", "step 1", "step 2"
        ]
        is_wide_or_demo = (
            scene_type in ["demo_walkthrough", "concept_explanation"]
            and (any(k in norm_text for k in wide_triggers) or card_count >= 3)
        )

        # 2. Check for Direct Speaker Address -> 100% Full-Screen
        is_personal_address = (
            scene_type in ["hook_intro", "personal_hook", "conversational_pause"]
            and card_count <= 1
            and not any(k in norm_text for k in ["diagram", "pipeline", "architecture", "code"])
        )

        # 3. Determine Layout
        if is_personal_address:
            chosen_layout = "100"
            reason = "Direct speaker address / energetic opening hook; minimal on-screen graphics required."
        elif is_wide_or_demo:
            chosen_layout = "20"
            reason = "High visual density (wide architecture / code / workflow); scaled SME to 20% PIP to allocate 1814px width."
        else:
            chosen_layout = "70"
            reason = "Structured content delivery (cards / objectives / summary); balanced cropped SME on left with right-hand workspace."

    # Return full geometry payload corresponding to the dynamically chosen layout
    if chosen_layout == "100":
        return {
            "sme_layout": "100",
            "dynamic_selection_reason": reason,
            "sme_positioning": {
                "layout_type": "100_full_screen",
                "manim_geometry": {"cx": 0.0, "cy": 0.0, "w": 14.222, "h": 8.000},
                "bounding_box": {"x": 0, "y": 0, "w": 1920, "h": 1080},
                "corner_radius": 0,
                "blue_band": None,
                "description": "Full screen trainer video (guidelines.md 8.3)."
            },
            "presentation_safe_zone": {
                "allowed": False,
                "notes": "Minimal overlay text only; teacher occupies full canvas."
            }
        }
    elif chosen_layout == "20":
        return {
            "sme_layout": "20",
            "dynamic_selection_reason": reason,
            "sme_positioning": {
                "layout_type": "20_top_right_pip",
                "manim_geometry": {"cx": 5.689, "cy": 3.200, "w": 2.844, "h": 1.600, "corner_radius": 0.074},
                "bounding_box": {"x": 1536, "y": 0, "w": 384, "h": 216, "corner_radius": 10},
                "corner_radius": 10,
                "blue_band": None,
                "description": "Trainer scaled to 20% FHD in top-right corner (guidelines.md 8.4)."
            },
            "presentation_safe_zone": {
                "allowed": True,
                "bounding_box": {"x_min": 52, "x_max": 1814, "y_min": 80, "y_max": 1000},
                "collision_constraints": {
                    "lead_in_max_x": 1450,
                    "diagram_y_min": 270
                },
                "notes": "Lead-in line must terminate <= 1450px. Diagrams must stay below y = 270px."
            }
        }
    else:  # "70"
        return {
            "sme_layout": "70",
            "dynamic_selection_reason": reason,
            "sme_positioning": {
                "layout_type": "70_left_rounded_rect",
                "manim_geometry": {"cx": -3.687, "cy": -0.023, "w": 4.937, "h": 5.349, "corner_radius": 0.074},
                "bounding_box": {"x": 80, "y": 80, "w": 640, "h": 920, "corner_radius": 10},
                "corner_radius": 10,
                "blue_band": {"color": "#2C81FE", "width": 242},
                "description": "Left rounded rectangle (radius 10px) with blue accent band (guidelines.md 8.5)."
            },
            "presentation_safe_zone": {
                "allowed": True,
                "bounding_box": {"x_min": 760, "x_max": 1840, "y_min": 80, "y_max": 1000},
                "collision_constraints": {
                    "content_min_x": 760
                },
                "notes": "Right side 1080px workspace for content cards."
            }
        }


def parse_input_to_json(input_text: str) -> Dict[str, Any]:
    """
    Robust JSON parser for LLM responses.
    Handles markdown code blocks, JSON dictionaries, or structured scene text.
    """
    cleaned = input_text.strip()
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned, re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    brace_match = re.search(r'\{[\s\S]*\}', cleaned)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # Text/markdown fallback parser for Scene blocks
    output: Dict[str, Any] = {"scenes": []}
    scene_blocks = re.split(r"(?im)^\s*#*\s*Scene\s+(\d+)\b", input_text)
    if len(scene_blocks) > 1:
        for i in range(1, len(scene_blocks), 2):
            scene_num = int(scene_blocks[i])
            scene_body = scene_blocks[i + 1]

            title_m = re.search(r"(?im)^\s*Title:\s*(.+)$", scene_body)
            title = title_m.group(1).strip() if title_m else f"Scene {scene_num}"

            narration_m = re.search(r"(?im)^\s*Narration:\s*(.+?)(?=^\s*Visual Description:|\Z)", scene_body, re.DOTALL)
            raw_narr = narration_m.group(1).strip() if narration_m else ""
            clean_narr = clean_narration_latex(raw_narr)

            output["scenes"].append({
                "scene_id": scene_num,
                "title": title,
                "voiceover_narration": clean_narr,
                "scene_type": "concept_explanation" if scene_num > 2 else "hook_intro"
            })
        return output

    raise ValueError("Could not parse input text into valid JSON storyboard structure.")


class InstructionalDesign:
    """
    Stage 1: Instructional Storyboard Design.
    Translates raw transcripts into a structured, step-by-step educational
    storyboard with verified narration lines, DYNAMIC SME clearances, and visual directives.
    """

    def __init__(
        self,
        guidelines_path: Optional[str] = None,
        api_provider: str = "auto",
        api_key: Optional[str] = None
    ):
        self.guidelines_path = Path(guidelines_path) if guidelines_path else GUIDELINES_TXT_PATH
        self.api_provider = api_provider
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    def load_guidelines(self) -> str:
        """Loads instructional storyboarding guidelines."""
        if self.guidelines_path.exists():
            with open(self.guidelines_path, "r", encoding="utf-8") as f:
                return f.read()
        return load_storyboard_guidelines()

    def generate_local_blueprint(
        self,
        transcript_data: Any,
        lesson_title: str = "Simplilearn Lecture"
    ) -> Dict[str, Any]:
        """
        Deterministically constructs the OSL 3.0 presentation blueprint strictly
        adhering to guidelines.md and instructional_storyboarding_guidelines.txt.
        Applies dynamic SME framing based on scene content, pedagogical intent, and cognitive load.
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

        # Clean LaTeX expressions & spell out single digits in speech
        cleaned_full_text = clean_narration_latex(full_text)
        cleaned_full_text = spell_out_numbers(cleaned_full_text)

        # 6-Scene Time Splitting (Hook, Objectives, Concept, Demo, Summary, What's Next)
        t_hook = min(total_duration * 0.12, 30.0)
        t_obj  = min(total_duration * 0.25, t_hook + 40.0)
        t_conc = min(total_duration * 0.55, t_obj + 60.0)
        t_demo = max(t_conc + 10.0, total_duration * 0.82)
        t_sum  = min(total_duration * 0.94, t_demo + 30.0)
        t_next = total_duration

        # Extract clean narrative sentences
        raw_sentences = re.split(r'(?<=[.!?]) +', cleaned_full_text.strip())
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 8]
        if not sentences:
            sentences = ["Understanding core concepts and practical implementations."]

        s1_text = sentences[0] if len(sentences) > 0 else cleaned_full_text[:120]
        s2_text = sentences[1] if len(sentences) > 1 else "Master core architectures and design principles."
        s3_text = " ".join(sentences[2:4]) if len(sentences) > 3 else "Explore technical mechanisms and operational workflows."
        s4_text = " ".join(sentences[4:6]) if len(sentences) > 5 else "Walk through practical tool execution and step-by-step procedures."
        s5_text = sentences[-2] if len(sentences) > 6 else "Review essential principles and critical takeaways."
        s6_text = sentences[-1] if len(sentences) > 7 else "Prepare for advanced integrations."

        clean_lesson_title = format_chicago_title(lesson_title)

        # Dynamically resolve SME framing for each scene based on content and visual demands
        s1_framing = resolve_dynamic_sme_framing("hook_intro", s1_text, card_count=1)
        s2_framing = resolve_dynamic_sme_framing("learning_objectives", s2_text, card_count=3)
        s3_framing = resolve_dynamic_sme_framing("concept_explanation", s3_text, card_count=3)
        s4_framing = resolve_dynamic_sme_framing("demo_walkthrough", s4_text, card_count=3)
        s5_framing = resolve_dynamic_sme_framing("summary_takeaways", s5_text, card_count=2)
        s6_framing = resolve_dynamic_sme_framing("whats_next", s6_text, card_count=1)

        blueprint = {
            "lesson_title": clean_lesson_title,
            "total_scenes": 6,
            "estimated_duration": total_duration,
            "guidelines_reference": "guidelines.md (Sections 1, 2, 4, 6, 8) & instructional_storyboarding_guidelines.txt",
            "dynamic_sme_framing_enabled": True,
            "scenes": [
                {
                    "scene_id": 1,
                    "scene_type": "hook_intro",
                    "title": format_chicago_title(f"Introduction to {clean_lesson_title}"),
                    "start_time": 0.0,
                    "end_time": round(t_hook, 2),
                    "sme_layout": s1_framing["sme_layout"],
                    "dynamic_selection_reason": s1_framing["dynamic_selection_reason"],
                    "sme_positioning": s1_framing["sme_positioning"],
                    "presentation_safe_zone": s1_framing["presentation_safe_zone"],
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
                    "sme_layout": s2_framing["sme_layout"],
                    "dynamic_selection_reason": s2_framing["dynamic_selection_reason"],
                    "sme_positioning": s2_framing["sme_positioning"],
                    "presentation_safe_zone": s2_framing["presentation_safe_zone"],
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
                    "end_time": round(t_conc, 2),
                    "sme_layout": s3_framing["sme_layout"],
                    "dynamic_selection_reason": s3_framing["dynamic_selection_reason"],
                    "sme_positioning": s3_framing["sme_positioning"],
                    "presentation_safe_zone": s3_framing["presentation_safe_zone"],
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
                    "scene_type": "demo_walkthrough",
                    "title": format_chicago_title(f"Practical Demonstration: {clean_lesson_title}"),
                    "start_time": round(t_conc, 2),
                    "end_time": round(t_demo, 2),
                    "sme_layout": s4_framing["sme_layout"],
                    "dynamic_selection_reason": s4_framing["dynamic_selection_reason"],
                    "sme_positioning": s4_framing["sme_positioning"],
                    "presentation_safe_zone": s4_framing["presentation_safe_zone"],
                    "on_screen_text": {
                        "lead_in": "Key demonstration steps and verification:",
                        "cards": [
                            {"title": "Step 1: Setup", "body": "Initialize runtime and configure environment dependencies.", "accent_color": "#62B7E4"},
                            {"title": "Step 2: Execution", "body": s4_text[:90].rstrip(".") + ".", "accent_color": "#7EA2C8"},
                            {"title": "Step 3: Verification", "body": "Verify logs and validate expected runtime output metrics.", "accent_color": "#8ECDB7"}
                        ]
                    },
                    "voiceover_narration": s4_text
                },
                {
                    "scene_id": 5,
                    "scene_type": "summary_takeaways",
                    "title": "Lesson Summary",
                    "start_time": round(t_demo, 2),
                    "end_time": round(t_sum, 2),
                    "sme_layout": s5_framing["sme_layout"],
                    "dynamic_selection_reason": s5_framing["dynamic_selection_reason"],
                    "sme_positioning": s5_framing["sme_positioning"],
                    "presentation_safe_zone": s5_framing["presentation_safe_zone"],
                    "on_screen_text": {
                        "lead_in": "Key takeaways from this lesson:",
                        "cards": [
                            {"title": "Key Concept", "body": s5_text[:90].rstrip(".") + ".", "accent_color": "#62B7E4"},
                            {"title": "Best Practice", "body": "Structure modular workflows with clean component isolation.", "accent_color": "#7EA2C8"}
                        ]
                    },
                    "voiceover_narration": s5_text
                },
                {
                    "scene_id": 6,
                    "scene_type": "whats_next",
                    "title": "What Is Next",
                    "start_time": round(t_sum, 2),
                    "end_time": round(t_next, 2),
                    "sme_layout": s6_framing["sme_layout"],
                    "dynamic_selection_reason": s6_framing["dynamic_selection_reason"],
                    "sme_positioning": s6_framing["sme_positioning"],
                    "presentation_safe_zone": s6_framing["presentation_safe_zone"],
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
                    "voiceover_narration": s6_text
                }
            ]
        }

        return blueprint

    def generate_instructions(
        self,
        transcript_data: Any,
        lesson_title: str
    ) -> Dict[str, Any]:
        """
        Generates storyboard blueprint using available LLM API, with resilient fallback.
        Embeds instructional_storyboarding_guidelines.txt as system prompt.
        Enforces dynamic SME framing evaluation for each scene.
        """
        guidelines_text = self.load_guidelines()

        if isinstance(transcript_data, list):
            segments = transcript_data
        else:
            segments = transcript_data.get("segments", [])
        full_transcript = " ".join([s.get("text", "") for s in segments])

        dynamic_framing_instruction = (
            "DYNAMIC SME FRAMING REQUIREMENT:\n"
            "Evaluate each scene's content density and pedagogical intent to dynamically select "
            "'sme_layout' from ['100', '70', '20']:\n"
            "- Use '100' for direct speaker address, opening hook, or sign-off with no slide graphics.\n"
            "- Use '70' for structured cards, learning objectives, bullet lists, or summaries (x >= 760 safe zone).\n"
            "- Use '20' for wide horizontal architectures, multi-tier pipelines, flowcharts, code, or tool walkthroughs.\n"
            "Include 'dynamic_selection_reason' explaining each layout choice."
        )

        # Try Google Gemini
        if self.api_provider in ["auto", "gemini"] and (self.api_key or os.environ.get("GEMINI_API_KEY")):
            key = self.api_key or os.environ.get("GEMINI_API_KEY")
            try:
                import google.generativeai as genai
                genai.configure(api_key=key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                prompt = (
                    f"### SYSTEM INSTRUCTIONS & STORYBOARDING GUIDELINES:\n{guidelines_text}\n\n"
                    f"{dynamic_framing_instruction}\n\n"
                    f"### LESSON TITLE: {lesson_title}\n\n"
                    f"### TRANSCRIPT:\n{full_transcript}\n\n"
                    f"Generate a strict JSON presentation blueprint following Simplilearn guidelines.md. "
                    f"Output MUST be valid JSON containing 'lesson_title', 'total_scenes', 'dynamic_sme_framing_enabled': true, and 'scenes' array."
                )
                resp = model.generate_content(prompt)
                parsed = parse_input_to_json(resp.text)
                if "scenes" in parsed and len(parsed["scenes"]) > 0:
                    for sc in parsed["scenes"]:
                        layout = sc.get("sme_layout", "70")
                        framing = resolve_dynamic_sme_framing(sc.get("scene_type", "concept"), sc.get("voiceover_narration", ""), explicit_layout=layout)
                        if "sme_positioning" not in sc:
                            sc["sme_positioning"] = framing["sme_positioning"]
                        if "presentation_safe_zone" not in sc:
                            sc["presentation_safe_zone"] = framing["presentation_safe_zone"]
                    return parsed
            except Exception as e:
                print(f"[Stage 1] Gemini generation notice: {e}. Falling back to deterministic generator.")

        # Try Anthropic Claude
        if self.api_provider in ["auto", "claude"] and (self.api_key or os.environ.get("ANTHROPIC_API_KEY")):
            key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
            try:
                from anthropic import Anthropic
                client = Anthropic(api_key=key)
                resp = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    system=f"{guidelines_text}\n\n{dynamic_framing_instruction}",
                    messages=[
                        {"role": "user", "content": f"Topic: {lesson_title}\nTranscript:\n{full_transcript}\nGenerate JSON presentation blueprint with dynamic SME framing."}
                    ]
                )
                parsed = parse_input_to_json(resp.content[0].text)
                if "scenes" in parsed and len(parsed["scenes"]) > 0:
                    for sc in parsed["scenes"]:
                        layout = sc.get("sme_layout", "70")
                        framing = resolve_dynamic_sme_framing(sc.get("scene_type", "concept"), sc.get("voiceover_narration", ""), explicit_layout=layout)
                        if "sme_positioning" not in sc:
                            sc["sme_positioning"] = framing["sme_positioning"]
                        if "presentation_safe_zone" not in sc:
                            sc["presentation_safe_zone"] = framing["presentation_safe_zone"]
                    return parsed
            except Exception as e:
                print(f"[Stage 1] Claude generation notice: {e}. Falling back to deterministic generator.")

        # Deterministic generation adhering to guidelines.md with dynamic SME framing
        return self.generate_local_blueprint(transcript_data, lesson_title)

    def run(
        self,
        transcript_path: str,
        output_path: str,
        lesson_title: Optional[str] = None
    ) -> str:
        """Executes Stage 1 from file paths."""
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        if not lesson_title:
            base_name = Path(transcript_path).stem.replace("_step2_clean_transcript", "").replace("_transcript", "")
            lesson_title = base_name.replace("_", " ").replace("-", " ").title()

        blueprint = self.generate_instructions(transcript_data, lesson_title)

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(blueprint, f, indent=2, ensure_ascii=False)

        return str(out_file)


# --------------------------------------------------------------------------------
# Backward-compatible Module Interface
# --------------------------------------------------------------------------------

def generate_local_storyboard_blueprint(
    transcript_data: Any,
    lesson_title: str = "Simplilearn Lecture"
) -> Dict[str, Any]:
    designer = InstructionalDesign()
    return designer.generate_local_blueprint(transcript_data, lesson_title)


def generate_llm_storyboard_blueprint(
    transcript_data: Any,
    lesson_title: str,
    api_provider: str = "auto"
) -> Dict[str, Any]:
    designer = InstructionalDesign(api_provider=api_provider)
    return designer.generate_instructions(transcript_data, lesson_title)


def run_stage_1(
    transcript_json: str,
    output_blueprint_json: str,
    lesson_title: Optional[str] = None,
    api_provider: str = "auto"
) -> str:
    """Runs complete Stage 1 workflow."""
    print(f"\n==================================================================")
    print(f"STAGE 1: INSTRUCTIONAL STORYBOARD DESIGN (DYNAMIC SME FRAMING)")
    print(f"Guidelines: {GUIDELINES_TXT_PATH.name}")
    print(f"Compliance: guidelines.md Sections 1, 2, 4, 6, 8 (OSL 3.0)")
    print(f"Dynamic SME Framing: Enabled (100% / 70% / 20%)")
    print(f"==================================================================")

    designer = InstructionalDesign(api_provider=api_provider)
    out_path = designer.run(transcript_json, output_blueprint_json, lesson_title=lesson_title)

    with open(out_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"✓ Stage 1 Complete: Storyboard generated ({len(data.get('scenes', []))} scenes)")
    for sc in data.get("scenes", []):
        print(f"  - Scene {sc.get('scene_id')}: Layout {sc.get('sme_layout')}% ({sc.get('dynamic_selection_reason', '')[:65]}...)")
    print(f"  Blueprint saved -> {out_path}\n")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 1: Instructional Storyboard Design")
    parser.add_argument("-t", "--transcript", required=True, help="Cleaned transcript JSON")
    parser.add_argument("-o", "--output", required=True, help="Output presentation blueprint JSON")
    parser.add_argument("-l", "--lesson-title", default=None, help="Lesson title")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "openai", "local"])
    args = parser.parse_args()

    run_stage_1(args.transcript, args.output, lesson_title=args.lesson_title, api_provider=args.provider)
