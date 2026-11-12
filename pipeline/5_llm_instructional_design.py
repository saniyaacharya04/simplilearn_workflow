#!/usr/bin/env python3
"""
Step 5: LLM Instructional Design & Presentation Storyboard Blueprint
Adapted from Kplor Structured Presentation Workflow (instructional_storyboard.txt)
and tailored for Simplilearn OSL 3.0 & Learning Design (LD) / Content Editor (CE) standards.

Takes ONLY the raw teacher speech transcript and transforms it into
a structured multi-scene educational blueprint JSON.
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

from pipeline.config import NEXT_TOPIC_PREFIX

# ==============================================================================
# 1. SYSTEM PROMPT
# ==============================================================================

SIMPLILEARN_INSTRUCTIONAL_PROMPT = """
ROLE:
You are a Senior Presentation Storyboard Architect and Instructional Designer for Simplilearn OSL 3.0 educational courses.

TASK:
You are given ONLY the raw spoken transcript and timestamps of an expert teacher.
Transform this spoken monologue into a complete, structured, multi-scene visual presentation blueprint.
Every presentation step must reduce learner cognitive load, eliminate attention-splitting, and build durable understanding.

---

PEDAGOGICAL PROGRESSION (LEARNING DESIGN LAW):
Structure the video into discrete, logical scenes following this exact flow:
1. Scene 1 - Hook & Overview (SME Layout: 100% Full Screen)
   - Grab attention, establish real-world relevance. Teacher speaks directly to learner.
2. Scene 2 - Learning Objectives (SME Layout: 70% Left Rounded-Rectangle)
   - Sets expectations. Right side displays 2-4 clear outcome-driven bullet cards.
   - Lead-in line: "By the end of this topic, you will be able to:"
3. Scene 3 to N-2 - Concept Breakdown, Frameworks & Demos (SME Layout: 20% Top-Right Corner PIP)
   - Core teaching. 20% layout opens up the full 1080p canvas for comparison tables, process flows, or code architectures.
4. Scene N-1 - Summary & Key Takeaways (SME Layout: 70% Left Rounded-Rectangle)
   - Reinforces 2-3 key takeaways.
5. Scene N - Next Topic & Outro (SME Layout: 70% Left Rounded-Rectangle)
   - Teases the next lecture.
   - Lead-in MUST strictly follow: "In the next topic, you will learn about: <Action verb in -ing form>"

---

SIMPLILEARN OSL 3.0 & CONTENT EDITOR (CE) RULES:
1. No Split Attention: Learners should never split attention between reading and listening.
   On-screen text (OST) must NEVER duplicate the spoken voiceover verbatim.
   OST displays only: Keywords, Steps, Comparisons, and Core Definitions.
2. Title Specifications: Title casing (Chicago Manual of Style), 5 to 7 words maximum.
3. Lead-in Line Specifications: Short, active voice, US English. Never repeat words in the title.
   Complete sentences must have a period; incomplete phrases must not.
4. Numbers Rule: Numbers zero through nine (0-9) MUST be spelled out in words.
5. Emphasis Rules: NEVER use single or double quotes for emphasis on screen; use bold or brand color highlights.
6. Approved Color Palette:
   - Primary Blue: #62B7E4 | Steel Blue: #7EA2C8 | Lavender: #C1A5C6 | Soft Violet: #9B99C7
   - Terracotta: #B88968  | Gold/Yellow: #DDB945 | Tangerine: #E6A157 | Coral: #E58F6D
   - Blush Rose: #D98CA1  | Sage/Mint: #8ECDB7   | Highlight: #F78908 (3px thickness, draw time 1.0s)
   - NEVER use green for background containers or cards (green is reserved for tiny icons).
7. Layout Geometry & Clearance:
   - In 70% layout: Teacher is in the left rounded box (x=80 to 720, corner radius 10).
     Right canvas (x=760 to 1840) is the slide workspace.
   - In 20% layout: Teacher is at top-right (x=1496, y=40, w=384, h=216).
     All slide lead-in lines and card titles MUST stay clear of this top-right corner to prevent overlap.

---

OUTPUT FORMAT:
Return ONLY a valid, parseable JSON object matching this schema:
{
  "lesson_title": "string (5-7 words, Title Case)",
  "learning_outcome": "string",
  "scenes": [
    {
      "scene_id": 1,
      "scene_type": "hook_intro",
      "sme_layout": "100",
      "start_time": 0.0,
      "end_time": float,
      "title": "string",
      "lead_in_line": "",
      "cards": []
    },
    {
      "scene_id": 2,
      "scene_type": "learning_objectives",
      "sme_layout": "70",
      "start_time": float,
      "end_time": float,
      "title": "Learning Objectives",
      "lead_in_line": "By the end of this topic, you will be able to:",
      "cards": [
        {
          "card_index": 1,
          "card_title": "string",
          "card_text": "string (active verb phrase, spelled numbers)",
          "color_hex": "#62B7E4"
        }
      ]
    },
    {
      "scene_id": 3,
      "scene_type": "concept_explanation",
      "sme_layout": "20",
      "start_time": float,
      "end_time": float,
      "title": "string",
      "lead_in_line": "string",
      "visual_framework": "comparison_cards",
      "cards": [
        {
          "card_index": 1,
          "card_title": "string",
          "card_text": "string",
          "color_hex": "#E6A157"
        }
      ]
    },
    {
      "scene_id": 4,
      "scene_type": "summary_takeaways",
      "sme_layout": "70",
      "start_time": float,
      "end_time": float,
      "title": "Key Takeaways",
      "lead_in_line": "Essential points to remember:",
      "cards": [
        {
          "card_index": 1,
          "card_title": "string",
          "card_text": "string",
          "color_hex": "#8ECDB7"
        }
      ]
    },
    {
      "scene_id": 5,
      "scene_type": "whats_next",
      "sme_layout": "70",
      "start_time": float,
      "end_time": float,
      "title": "What Is Next",
      "lead_in_line": "In the next topic, you will learn about:",
      "cards": [
        {
          "card_index": 1,
          "card_title": "Next Topic Preview",
          "card_text": "Exploring <topic in gerund -ing form>",
          "color_hex": "#62B7E4"
        }
      ]
    }
  ]
}
"""


def call_llm(
    transcript_text: str,
    duration: float,
    provider: str = "gemini",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Calls selected LLM (Gemini, Claude, or OpenAI)."""
    user_prompt = f"""
TOTAL LECTURE DURATION: {duration:.2f} seconds.

RAW TEACHER TRANSCRIPT (WITH TIMESTAMPS):
{transcript_text}

Transform this raw transcript into the official Simplilearn OSL 3.0 Presentation Blueprint JSON.
Return ONLY valid JSON.
"""

    if provider == "gemini":
        gemini_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY / GOOGLE_API_KEY not found.")

        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SIMPLILEARN_INSTRUCTIONAL_PROMPT,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=gemini_key)
            model = legacy_genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=SIMPLILEARN_INSTRUCTIONAL_PROMPT
            )
            response = model.generate_content(user_prompt)
            clean_json = re.sub(r"^```(?:json)?\s*", "", response.text.strip(), flags=re.MULTILINE)
            clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.MULTILINE)
            return json.loads(clean_json)

    elif provider == "claude":
        claude_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not claude_key:
            raise ValueError("ANTHROPIC_API_KEY not found.")

        import anthropic
        client = anthropic.Anthropic(api_key=claude_key)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0.2,
            system=SIMPLILEARN_INSTRUCTIONAL_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )
        resp_text = message.content[0].text.strip()
        clean_json = re.sub(r"^```(?:json)?\s*", "", resp_text, flags=re.MULTILINE)
        clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.MULTILINE)
        return json.loads(clean_json)

    elif provider == "openai":
        openai_key = api_key or os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY not found.")

        import openai
        client = openai.OpenAI(api_key=openai_key)
        completion = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            temperature=0.2,
            messages=[
                {"role": "system", "content": SIMPLILEARN_INSTRUCTIONAL_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        return json.loads(completion.choices[0].message.content)

    else:
        raise ValueError(f"Unsupported provider: {provider}")


def generate_heuristic_blueprint(
    transcript_segments: List[Dict[str, Any]],
    lesson_title: str = "Educational Topic"
) -> Dict[str, Any]:
    """Generates a compliant blueprint locally without external API keys."""
    total_duration = transcript_segments[-1].get("end", 300.0) if transcript_segments else 300.0

    t_intro_end = round(total_duration * 0.10, 2)
    t_obj_end = round(total_duration * 0.25, 2)
    t_core_end = round(total_duration * 0.80, 2)
    t_summary_end = round(total_duration * 0.92, 2)

    sample_texts = [s.get("cleaned_text") or s.get("text", "") for s in transcript_segments if len(s.get("text", "").split()) > 4]

    obj_1 = sample_texts[0][:60] if len(sample_texts) > 0 else "Understand foundational concepts and syntax"
    obj_2 = sample_texts[1][:60] if len(sample_texts) > 1 else "Implement structured techniques for reliable performance"
    obj_3 = sample_texts[2][:60] if len(sample_texts) > 2 else "Analyze real-world examples and best practices"

    return {
        "lesson_title": lesson_title,
        "learning_outcome": f"Master the principles of {lesson_title}",
        "scenes": [
            {
                "scene_id": 1,
                "scene_type": "hook_intro",
                "sme_layout": "100",
                "start_time": 0.0,
                "end_time": t_intro_end,
                "title": lesson_title,
                "lead_in_line": "",
                "cards": []
            },
            {
                "scene_id": 2,
                "scene_type": "learning_objectives",
                "sme_layout": "70",
                "start_time": t_intro_end,
                "end_time": t_obj_end,
                "title": "Learning Objectives",
                "lead_in_line": "By the end of this topic, you will be able to:",
                "cards": [
                    {"card_index": 1, "card_title": "Foundations", "card_text": obj_1, "color_hex": "#62B7E4"},
                    {"card_index": 2, "card_title": "Application", "card_text": obj_2, "color_hex": "#7EA2C8"},
                    {"card_index": 3, "card_title": "Analysis", "card_text": obj_3, "color_hex": "#9B99C7"}
                ]
            },
            {
                "scene_id": 3,
                "scene_type": "concept_explanation",
                "sme_layout": "20",
                "start_time": t_obj_end,
                "end_time": t_core_end,
                "title": f"Core Principles: {lesson_title}",
                "lead_in_line": "Key components and operational frameworks:",
                "visual_framework": "comparison_cards",
                "cards": [
                    {"card_index": 1, "card_title": "Input Structure", "card_text": "Establishing clear instructions and contextual constraints", "color_hex": "#E6A157"},
                    {"card_index": 2, "card_title": "Model Processing", "card_text": "Guiding reasoning patterns through sequential demonstrations", "color_hex": "#B88968"},
                    {"card_index": 3, "card_title": "Output Evaluation", "card_text": "Verifying accuracy against required learning objectives", "color_hex": "#DDB945"}
                ]
            },
            {
                "scene_id": 4,
                "scene_type": "summary_takeaways",
                "sme_layout": "70",
                "start_time": t_core_end,
                "end_time": t_summary_end,
                "title": "Key Takeaways",
                "lead_in_line": "Essential points to remember:",
                "cards": [
                    {"card_index": 1, "card_title": "Core Takeaway", "card_text": "Structured prompting yields repeatable and deterministic results", "color_hex": "#8ECDB7"},
                    {"card_index": 2, "card_title": "Best Practice", "card_text": "Iteratively refine instructions to eliminate cognitive ambiguity", "color_hex": "#62B7E4"}
                ]
            },
            {
                "scene_id": 5,
                "scene_type": "whats_next",
                "sme_layout": "70",
                "start_time": t_summary_end,
                "end_time": total_duration,
                "title": "What Is Next",
                "lead_in_line": NEXT_TOPIC_PREFIX,
                "cards": [
                    {"card_index": 1, "card_title": "Next Lesson", "card_text": f"Exploring advanced applications and practical workflows in {lesson_title}", "color_hex": "#62B7E4"}
                ]
            }
        ]
    }


def run_stage_5(
    transcript_json: str,
    output_blueprint_json: str,
    lesson_title: str = "Educational Topic",
    provider: str = "auto",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Runs complete Stage 5 workflow."""
    print(f"\n==================================================================")
    print(f"STEP 5: LLM INSTRUCTIONAL DESIGN & STORYBOARD BLUEPRINT")
    print(f"==================================================================")

    with open(transcript_json, "r", encoding="utf-8") as f:
        segments = json.load(f)

    full_blocks = []
    duration = 0.0
    for s in segments:
        t = s.get("cleaned_text") or s.get("text", "")
        st = s.get("start", 0.0)
        et = s.get("end", 0.0)
        duration = max(duration, et)
        full_blocks.append(f"[{st:.2f}s - {et:.2f}s] {t}")

    full_transcript = "\n".join(full_blocks)

    blueprint = None
    if provider in ("gemini", "claude", "openai") or (provider == "auto" and (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))):
        chosen_provider = provider
        if chosen_provider == "auto":
            chosen_provider = "gemini" if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) else "claude"

        try:
            print(f"[Step 5] Querying LLM ({chosen_provider}) for Presentation Blueprint...")
            blueprint = call_llm(full_transcript, duration, provider=chosen_provider, api_key=api_key)
        except Exception as e:
            print(f"[Step 5] LLM call failed ({e}). Falling back to local blueprint generator.")

    if not blueprint:
        print("[Step 5] Using internal pedagogical blueprint generator...")
        blueprint = generate_heuristic_blueprint(segments, lesson_title=lesson_title)

    Path(output_blueprint_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_blueprint_json, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, indent=2, ensure_ascii=False)

    print(f"✓ Step 5 Complete: Blueprint generated ({len(blueprint.get('scenes', []))} scenes) -> {output_blueprint_json}\n")
    return blueprint


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 5: LLM Instructional Design Blueprint")
    parser.add_argument("-t", "--transcript", required=True, help="Input cleaned transcript JSON")
    parser.add_argument("-o", "--output", required=True, help="Output presentation blueprint JSON")
    parser.add_argument("--title", default="Educational Topic", help="Lesson / Topic Title")
    parser.add_argument("-p", "--provider", choices=["auto", "gemini", "claude", "openai"], default="auto", help="LLM Provider")
    args = parser.parse_args()

    run_stage_5(args.transcript, args.output, lesson_title=args.title, provider=args.provider)

