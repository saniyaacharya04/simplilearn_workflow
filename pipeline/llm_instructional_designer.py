"""
Simplilearn LLM Instructional Designer & Presentation Storyboard Architect
Adapted from Kplor Structured Presentation Workflow (instructional_storyboard.txt & styling_generator.txt)
and tailored for Simplilearn OSL 3.0 & Learning Design (LD) / Content Editor (CE) standards.

Role:
Takes ONLY the Subject Matter Expert (SME)'s raw lecture transcript (with timestamps)
and transforms it into an end-to-end, production-ready educational presentation blueprint,
including visual cards, diagrams, layout assignments, and timestamped section breakdowns.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import (
    COLORS,
    HIGHLIGHT_COLOR,
    SME_LAYOUT_100,
    SME_LAYOUT_70,
    SME_LAYOUT_20,
    NEXT_TOPIC_PREFIX
)

# ==============================================================================
# 1. SYSTEM PROMPT (KPLOR PRESENTATION ARCHITECT + SIMPLILEARN OSL 3.0)
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
   - Grab attention, establish real-world relevance. SME speaks directly to learner.
2. Scene 2 - Learning Objectives (SME Layout: 70% Left Rounded-Rectangle)
   - Sets expectations. Right side displays 2-4 clear outcome-driven bullet cards.
   - Lead-in line: "By the end of this topic, you will be able to:"
3. Scene 3 to N-2 - Concept Breakdown, Frameworks & Demos (SME Layout: 20% Right Corner PIP or 70% Left)
   - Core teaching. 20% layout opens up the full 1080p canvas for comparison tables, process flows, or code architectures.
4. Scene N-1 - Summary & Key Takeaways (SME Layout: 70% Left Rounded-Rectangle)
   - Reinforces 2-3 key takeaways.
5. Scene N - Next Topic & Outro (SME Layout: 70% Left Rounded-Rectangle)
   - Teases the next lecture.
   - Lead-in MUST strictly follow: "In the next topic, you will learn about: <Action verb in -ing form>"

---

SIMPLILEARN OSL 3.0 & CONTENT EDITOR (CE) RULES:
1. No Split Attention (Crucial LD Rule):
   - Learners should NEVER split attention between reading and listening.
   - On-screen text (OST) must NEVER parrot or duplicate the spoken voiceover verbatim.
   - OST must display only: Keywords, Steps, Comparisons, Formulas, and Core Definitions.
2. Title Specifications:
   - Use title casing (Chicago Manual of Style).
   - Maximum 5 to 7 words (e.g. "Three Basic Prompting Techniques", "Role-Based Prompts in Practice").
3. Lead-in Line Specifications:
   - Short, active voice, US English.
   - Avoid redundancy: never start the lead-in line with the words in the slide title.
   - Complete sentences MUST have a period; incomplete phrases must NOT have a period.
4. Numbers Rule:
   - Numbers zero through nine (0-9) MUST be spelled out in words (e.g. "three components", not "3 components").
5. Emphasis Rules:
   - NEVER use single quotes or double quotation marks for emphasis on screen. Use bold or approved highlight colors instead.
6. Approved Color Palette (Infographics & Cards):
   - Primary Blue: #62B7E4
   - Steel Blue: #7EA2C8
   - Lavender: #C1A5C6
   - Soft Violet: #9B99C7
   - Terracotta: #B88968
   - Gold/Yellow: #DDB945
   - Tangerine: #E6A157
   - Coral: #E58F6D
   - Blush Rose: #D98CA1
   - Sage/Mint: #8ECDB7
   - Highlight: #F78908 (3px thickness, draw time 1.0s)
   - NEVER use green for background containers or cards.
7. Layout Geometry & Clearance:
   - In 70% layout, teacher is cropped into left rounded box (x=80 to 720, corner radius 10). Content stays in right area (x=760 to 1840).
   - In 20% layout, teacher is at top-right (x=1496, y=40, w=384, h=216). All slide lead-in lines and headers MUST keep clear of this top-right region to prevent overlap!

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
      "visual_framework": "comparison_cards" | "process_flow" | "architecture_cards" | "code_block",
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


# ==============================================================================
# 2. LLM CALLER (GEMINI / CLAUDE / OPENAI)
# ==============================================================================

def call_llm_for_presentation_blueprint(
    transcript_text: str,
    duration: float,
    provider: str = "gemini",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Invokes the LLM using the structured presentation architect prompt.
    Supports Google Gemini, Anthropic Claude, and OpenAI.
    """
    user_prompt = f"""
TOTAL LECTURE DURATION: {duration:.2f} seconds.

RAW TEACHER TRANSCRIPT (WITH TIMESTAMPS):
{transcript_text}

Transform this raw transcript into the official Simplilearn OSL 3.0 Presentation Blueprint JSON.
Ensure timestamps span smoothly from 0.0 to {duration:.2f}.
Return ONLY valid JSON.
"""

    # 1. Google Gemini (via google.genai or google.generativeai)
    if provider == "gemini":
        gemini_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

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

    # 2. Anthropic Claude
    elif provider == "claude":
        claude_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not claude_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")

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

    # 3. OpenAI
    elif provider == "openai":
        openai_key = api_key or os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")

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


# ==============================================================================
# 3. HEURISTIC BLUEPRINT GENERATOR (FALLBACK WHEN NO API KEY)
# ==============================================================================

def generate_heuristic_blueprint(
    transcript_segments: List[Dict[str, Any]],
    lesson_title: str = "Educational Topic"
) -> Dict[str, Any]:
    """
    Generates a pedagogically compliant Simplilearn OSL 3.0 blueprint directly
    from transcript segments without requiring external cloud API calls.
    """
    if not transcript_segments:
        total_duration = 300.0
    else:
        total_duration = transcript_segments[-1].get("end", 300.0)

    # Temporal chunking:
    # 0 -> 10%: Hook / Intro (100% SME)
    # 10% -> 25%: Objectives (70% SME)
    # 25% -> 80%: Core Concepts & Demos (20% PIP SME)
    # 80% -> 92%: Summary (70% SME)
    # 92% -> 100%: What's Next (70% SME)

    t_intro_end = round(total_duration * 0.10, 2)
    t_obj_end = round(total_duration * 0.25, 2)
    t_core_end = round(total_duration * 0.80, 2)
    t_summary_end = round(total_duration * 0.92, 2)

    # Extract key statements for objectives and summary
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


# ==============================================================================
# 4. SLIDE GRAPHIC RENDERER (FROM BLUEPRINT)
# ==============================================================================

def render_blueprint_slide(
    scene_data: Dict[str, Any],
    output_png: str
) -> str:
    """
    Renders an official 1920x1080 slide image for a blueprint scene.
    Respects layout space constraints (x=760 to 1840 for 70% layout;
    avoids x=1496, y=40 for 20% PIP layout).
    """
    import cv2
    import numpy as np

    canvas = np.full((1080, 1920, 3), 255, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    sme_layout = scene_data.get("sme_layout", "70")
    title = scene_data.get("title", "")
    lead_in = scene_data.get("lead_in_line", "")
    cards = scene_data.get("cards", [])

    if sme_layout == "70":
        # Right column workspace: x = 780 to 1840
        start_x = 780
        max_card_w = 1040
    elif sme_layout == "20":
        # Full screen workspace, but leave top-right corner clear (x >= 1480, y <= 270)
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

    # Draw Cards
    card_start_y = 310
    card_h = 105
    gap_y = 35

    for idx, card in enumerate(cards[:4]):
        cy1 = card_start_y + idx * (card_h + gap_y)
        cy2 = cy1 + card_h
        cx1 = start_x
        cx2 = start_x + max_card_w

        # Parse hex color
        hex_c = card.get("color_hex", "#62B7E4").lstrip("#")
        r_c = int(hex_c[0:2], 16)
        g_c = int(hex_c[2:4], 16)
        b_c = int(hex_c[4:6], 16)
        badge_bgr = (b_c, g_c, r_c)

        # Card container with light border
        cv2.rectangle(canvas, (cx1, cy1), (cx2, cy2), (248, 250, 252), -1)
        cv2.rectangle(canvas, (cx1, cy1), (cx2, cy2), (220, 228, 238), 2)

        # Left color indicator strip (radius styled)
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


# ==============================================================================
# 5. MAIN GENERATOR FUNCTION
# ==============================================================================

def generate_presentation_blueprint(
    cleaned_transcript_json: str,
    output_blueprint_json: str,
    output_slides_dir: str,
    lesson_title: str = "Educational Topic",
    provider: str = "auto",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transforms transcript into complete presentation blueprint JSON
    and renders companion 1080p slide PNGs.
    """
    with open(cleaned_transcript_json, "r", encoding="utf-8") as f:
        segments = json.load(f)

    full_text_blocks = []
    duration = 0.0
    for s in segments:
        t = s.get("cleaned_text") or s.get("text", "")
        st = s.get("start", 0.0)
        et = s.get("end", 0.0)
        duration = max(duration, et)
        full_text_blocks.append(f"[{st:.2f}s - {et:.2f}s] {t}")

    full_transcript = "\n".join(full_text_blocks)

    blueprint = None
    if provider in ("gemini", "claude", "openai") or (provider == "auto" and (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))):
        chosen_provider = provider
        if chosen_provider == "auto":
            chosen_provider = "gemini" if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) else "claude"

        try:
            print(f"[Instructional Designer] Querying LLM ({chosen_provider}) for Presentation Blueprint...")
            blueprint = call_llm_for_presentation_blueprint(full_transcript, duration, provider=chosen_provider, api_key=api_key)
        except Exception as e:
            print(f"[Instructional Designer] LLM call failed ({e}). Falling back to internal pedagogical blueprint generator.")

    if not blueprint:
        print("[Instructional Designer] Using internal pedagogical blueprint generator...")
        blueprint = generate_heuristic_blueprint(segments, lesson_title=lesson_title)

    # Save Blueprint JSON
    Path(output_blueprint_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_blueprint_json, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, indent=2, ensure_ascii=False)

    print(f"✓ Presentation Blueprint saved -> {output_blueprint_json}")

    # Render companion slide graphics for each scene
    Path(output_slides_dir).mkdir(parents=True, exist_ok=True)
    for scene in blueprint.get("scenes", []):
        sid = scene["scene_id"]
        layout = scene.get("sme_layout", "70")
        if layout in ("70", "20"):
            slide_file = Path(output_slides_dir) / f"slide_scene_{sid:02d}_{layout}.png"
            render_blueprint_slide(scene, str(slide_file))
            scene["rendered_slide_png"] = str(slide_file)
            print(f"  ✓ Rendered Scene {sid} slide ({layout}% layout) -> {slide_file.name}")

    # Re-save with slide image references
    with open(output_blueprint_json, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, indent=2, ensure_ascii=False)

    return blueprint


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python -m pipeline.llm_instructional_designer <cleaned_transcript.json> <output_blueprint.json> <output_slides_dir> [lesson_title]")
        sys.exit(1)
    title = sys.argv[4] if len(sys.argv) > 4 else "Lesson"
    generate_presentation_blueprint(sys.argv[1], sys.argv[2], sys.argv[3], lesson_title=title)

