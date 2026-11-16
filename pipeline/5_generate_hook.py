#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 5: HOOK & PEDAGOGICAL BLUEPRINT GENERATION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 5
   - Script Name: 5_generate_hook.py
   - Primary Class: HookGenerator
   - Pipeline Role:
     Transforms the cleaned transcript resulting from audio processing stages 0-4
     (or raw lecture curriculum/slide markdown) into a structured pedagogical blueprint,
     extracting:
       * Motivational Hook (Problem, Observation, Surprising Fact, Failure Scenario)
       * Lesson Metadata (Motivation, Learning Goals, Evergreen Classification)
       * Context & Core Problem (Why it exists, where used, misconceptions)
       * Concept Breakdown & Dependency Hierarchy
       * Modular Scene Blueprint with initial Dynamic SME Framing assignments
         (Layout 1: 100% full screen for hook; Layout 3: 70% left slide for LOs;
          Layout 2: 20% PIP corner for architectural deep-dives & demos).

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Stage 2 / Stage 4: Ingests the cleaned transcript (e.g. *_step2_clean_transcript.json)
     derived directly from the raw teacher video after filler & retake removal.

3. DOWNSTREAM CONSUMERS:
   - Stage 6 (6_instructional_design.py): Ingests the hook blueprint to produce
     granular, step-by-step presentation storyboards with exact Manim coordinate bounds.
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

from pipeline.config import CANVAS_WIDTH, CANVAS_HEIGHT, COLORS


def remove_code_fences(text: str) -> str:
    """Removes ```json ... ``` or ``` ... ``` wrappers from text."""
    if not text:
        return ""
    text = re.sub(r"^\s*```(?:json)?\s*\n?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\n?```\s*$", "", text.strip())
    return text.strip()


def parse_llm_json(text: str) -> Dict[str, Any]:
    """Robustly parses LLM JSON outputs with sanitization and fallback fixes."""
    cleaned = remove_code_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Common LLM glitch repair: trailing commas or unescaped inner quotes
        repaired = re.sub(r',\s*([\]}])', r'\1', cleaned)
        repaired = re.sub(r'""\s*,', '",', repaired)
        return json.loads(repaired)


class HookGenerator:
    """
    Transforms lecture content into a structured pedagogical blueprint
    featuring conceptual hooks, learning objectives, and initial scene framing.
    """

    def __init__(self, api_provider: str = "auto", api_key: Optional[str] = None):
        self.api_provider = api_provider.lower()
        self.api_key = api_key

    def extract_raw_text(self, transcript_input: Union[str, Path, Dict, List]) -> str:
        """Extracts continuous narrative text from transcript JSON, text files, lists, or dictionaries."""
        if isinstance(transcript_input, list):
            texts = []
            for item in transcript_input:
                if isinstance(item, dict):
                    t = item.get("text") or item.get("voiceover_narration") or item.get("sentence") or ""
                    if t:
                        texts.append(t.strip())
                elif isinstance(item, str):
                    texts.append(item.strip())
            return " ".join(texts)

        if isinstance(transcript_input, dict):
            # Check for standard transcript formats
            if "sentences" in transcript_input:
                return " ".join([s.get("text", "").strip() for s in transcript_input["sentences"] if s.get("text")])
            if "scenes" in transcript_input:
                texts = []
                for sc in transcript_input["scenes"]:
                    narration = sc.get("voiceover_narration") or sc.get("narration") or ""
                    if narration:
                        texts.append(narration)
                return " ".join(texts)
            return json.dumps(transcript_input)

        path = Path(transcript_input)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            try:
                data = json.loads(content)
                return self.extract_raw_text(data)
            except json.JSONDecodeError:
                return content

        return str(transcript_input)

    def generate_local_hook(self, raw_text: str, lesson_title: str) -> Dict[str, Any]:
        """
        Deterministic, offline generation of pedagogical hook blueprint 
        strictly following Simplilearn guidelines and dynamic framing.
        """
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_text) if s.strip()]
        if not sentences:
            sentences = [f"This lecture provides a comprehensive guide to understanding {lesson_title}."]

        first_sentence = sentences[0]
        second_sentence = sentences[1] if len(sentences) > 1 else first_sentence
        middle_sentence = sentences[len(sentences) // 2] if len(sentences) > 2 else first_sentence
        final_sentence = sentences[-1] if len(sentences) > 3 else "Key operational takeaways conclude this module."

        return {
            "concept": lesson_title,
            "hook": {
                "type": "Problem",
                "statement": first_sentence,
                "purpose": f"Motivates learner curiosity by highlighting the real-world operational challenges in {lesson_title}.",
                "visual_direction": "Clean, structured typography with high-contrast accent cards introducing core system variables without decorative distractions.",
                "sme_framing": {
                    "layout": "100",
                    "description": "100% Full-Screen Presenter",
                    "reason": "Direct human presenter engagement establishes authority and motivates lesson relevance."
                }
            },
            "lesson_metadata": {
                "motivation": f"Understanding {lesson_title} is essential for modern technical architecture and efficient execution.",
                "learning_goal": f"Master the architectural models, key trade-offs, and practical execution patterns of {lesson_title}.",
                "classification": "Evergreen"
            },
            "context": {
                "problem": f"Traditional implementations often struggle with complexity and scalability without {lesson_title}.",
                "why_it_exists": f"Engineered to systematically decouple operational concerns and ensure consistent reliability.",
                "where_it_is_used": [
                    "Enterprise Production Environments",
                    "Distributed Multi-Service Pipelines",
                    "Scalable High-Throughput Workflows"
                ],
                "common_misconception": f"Assuming {lesson_title} requires rigid overhead rather than modular, composable building blocks."
            },
            "concept_breakdown": [
                {
                    "title": "Foundational Principles",
                    "importance": "Establishes baseline terminology and operational constraints.",
                    "depends_on": []
                },
                {
                    "title": "Architectural Components",
                    "importance": "Details component interaction, data flow, and boundary contracts.",
                    "depends_on": ["Foundational Principles"]
                },
                {
                    "title": "Execution & Verification",
                    "importance": "Provides practical execution patterns and metric verification steps.",
                    "depends_on": ["Architectural Components"]
                }
            ],
            "scene_blueprint": [
                {
                    "scene_index": 1,
                    "scene_type": "Context / Hook",
                    "scene_goal": f"Introduce core motivation and high-level relevance of {lesson_title}.",
                    "sme_framing_recommendation": {
                        "layout": "100",
                        "description": "100% Full-Screen Presenter",
                        "reason": "Establishes direct learner rapport during the opening problem statement."
                    },
                    "text_elements": [
                        f"Mastering {lesson_title}",
                        "Operational Context & Challenge"
                    ],
                    "visual_elements": [
                        "Subtle title card with high-contrast dark blue accents",
                        "Clean presenter full-frame video window"
                    ],
                    "learning_outcome": "Learners understand why this topic is immediately relevant to real-world workflows."
                },
                {
                    "scene_index": 2,
                    "scene_type": "Learning Objectives",
                    "scene_goal": "Outline measurable milestones achieved throughout the module.",
                    "sme_framing_recommendation": {
                        "layout": "70",
                        "description": "70% Left Rounded-Rectangle Frame",
                        "reason": "Balances trainer presence with dedicated right-side canvas for structured objectives list."
                    },
                    "text_elements": [
                        "By the end of this topic, you will be able to:",
                        f"1. Explain the architectural foundations of {lesson_title}",
                        "2. Configure modular components and validation rules",
                        "3. Evaluate performance trade-offs and error scenarios"
                    ],
                    "visual_elements": [
                        "Three numbered pastel cards (#62B7E4, #7EA2C8, #9B99C7)",
                        "Left 70% rounded-rectangle SME frame with 10px corner radius"
                    ],
                    "learning_outcome": "Clear roadmap of three concrete technical competencies."
                },
                {
                    "scene_index": 3,
                    "scene_type": "Core Concept Breakdown",
                    "scene_goal": "Explain internal operational mechanics and structural workflow.",
                    "sme_framing_recommendation": {
                        "layout": "20",
                        "description": "20% Top-Right Corner Picture-In-Picture",
                        "reason": "Maximizes canvas area (1814px) for architectural diagrams and component cards."
                    },
                    "text_elements": [
                        f"Architectural Topology: {lesson_title}",
                        "Primary Components & Data Boundaries"
                    ],
                    "visual_elements": [
                        "Multi-column process flow diagram",
                        "Top-right 20% PIP window with 10px rounded corners"
                    ],
                    "learning_outcome": "Thorough grasp of internal data flow and component responsibilities."
                },
                {
                    "scene_index": 4,
                    "scene_type": "Practical Implementation & Demo",
                    "scene_goal": "Demonstrate practical configuration and verification patterns.",
                    "sme_framing_recommendation": {
                        "layout": "20",
                        "description": "20% Top-Right Corner Picture-In-Picture",
                        "reason": "Unlocks full canvas width for step-by-step code execution and data tables."
                    },
                    "text_elements": [
                        "Practical Verification & Execution",
                        "Input Validation -> Transformation -> Target Output"
                    ],
                    "visual_elements": [
                        "Step-by-step sequential cards with highlighted verification checkmarks"
                    ],
                    "learning_outcome": "Ability to implement and verify configurations independently."
                },
                {
                    "scene_index": 5,
                    "scene_type": "Summary & Key Takeaways",
                    "scene_goal": "Synthesize key rules, trade-offs, and next learning steps.",
                    "sme_framing_recommendation": {
                        "layout": "70",
                        "description": "70% Left Rounded-Rectangle Frame",
                        "reason": "Provides structured closure and transitions cleanly to the next topic."
                    },
                    "text_elements": [
                        "Summary Takeaways",
                        "1. Modularity over monolithic design",
                        "2. Continuous validation prevents silent failures",
                        "In the next topic, you will learn about: Advanced Optimization Strategies"
                    ],
                    "visual_elements": [
                        "Two high-impact summary cards",
                        "Next topic teaser card with orange focus highlight"
                    ],
                    "learning_outcome": "Consolidated understanding of best practices and readiness for next lesson."
                }
            ]
        }

    def generate_hook(self, transcript_input: Any, lesson_title: Optional[str] = None) -> Dict[str, Any]:
        """Orchestrates hook generation across Gemini, Claude, or deterministic fallback."""
        raw_text = self.extract_raw_text(transcript_input)
        if not lesson_title:
            first_line = raw_text.splitlines()[0] if raw_text else "Technical Concept"
            lesson_title = re.sub(r'^[#*\s-]+', '', first_line)[:50].strip() or "Digital Learning Module"

        # Try Google Gemini if available
        if self.api_provider in ["auto", "gemini"]:
            key = self.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    prompt = f"""
You are an expert instructional designer and curriculum architect for Simplilearn OSL 3.0 digital learning courses.
Transform the following lecture transcript/text into a structured pedagogical blueprint.

Output MUST be valid JSON adhering strictly to this schema:
{{
  "concept": "{lesson_title}",
  "hook": {{
    "type": "Problem | Observation | Surprising Fact | Failure Scenario",
    "statement": "<opening motivational hook statement>",
    "purpose": "<why this engages learners>",
    "visual_direction": "<visual treatment without decorative distractions>",
    "sme_framing": {{
      "layout": "100",
      "description": "100% Full-Screen Presenter",
      "reason": "Direct human-to-human engagement for the motivational hook."
    }}
  }},
  "lesson_metadata": {{
    "motivation": "<real-world importance>",
    "learning_goal": "<concrete learner competency>",
    "classification": "Evergreen | Slowly Changing | Time Sensitive"
  }},
  "context": {{
    "problem": "<problem this concept solves>",
    "why_it_exists": "<why it was developed>",
    "where_it_is_used": ["<app 1>", "<app 2>"],
    "common_misconception": "<largest beginner misconception>"
  }},
  "concept_breakdown": [
    {{
      "title": "<subconcept>",
      "importance": "<why it matters>",
      "depends_on": ["<prerequisite>"]
    }}
  ],
  "scene_blueprint": [
    {{
      "scene_index": 1,
      "scene_type": "Context / Hook",
      "scene_goal": "<goal>",
      "sme_framing_recommendation": {{
        "layout": "100",
        "description": "100% Full-Screen Presenter",
        "reason": "<reason>"
      }},
      "text_elements": ["<heading>", "<point>"],
      "visual_elements": ["<visual structure>"],
      "learning_outcome": "<takeaway>"
    }}
  ]
}}

Raw Material:
{raw_text[:8000]}
"""
                    resp = model.generate_content(prompt)
                    parsed = parse_llm_json(resp.text)
                    if "hook" in parsed and "scene_blueprint" in parsed:
                        return parsed
                except Exception as e:
                    print(f"[Stage 0] Gemini hook generation notice: {e}. Falling back to deterministic generator.")

        # Try Anthropic Claude if available
        if self.api_provider in ["auto", "claude"]:
            key = self.api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
            if key:
                try:
                    from anthropic import Anthropic
                    client = Anthropic(api_key=key)
                    resp = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=4096,
                        system="You are an expert instructional designer for Simplilearn OSL 3.0 digital learning courses. Output strictly valid JSON.",
                        messages=[
                            {"role": "user", "content": f"Topic: {lesson_title}\nText:\n{raw_text[:8000]}\nGenerate structured hook blueprint JSON with scene breakdowns and SME framing."}
                        ]
                    )
                    parsed = parse_llm_json(resp.content[0].text)
                    if "hook" in parsed and "scene_blueprint" in parsed:
                        return parsed
                except Exception as e:
                    print(f"[Stage 0] Claude hook generation notice: {e}. Falling back to deterministic generator.")

        # Local deterministic fallback
        return self.generate_local_hook(raw_text, lesson_title)

    def run(self, input_path: str, output_path: str, lesson_title: Optional[str] = None) -> str:
        """Executes Stage 0 and writes the generated blueprint JSON to disk."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        blueprint = self.generate_hook(input_path, lesson_title=lesson_title)

        with open(out, "w", encoding="utf-8") as f:
            json.dump(blueprint, f, indent=2, ensure_ascii=False)

        return str(out)


def run_stage_5(
    input_file: str,
    output_file: str,
    lesson_title: Optional[str] = None,
    api_provider: str = "auto"
) -> str:
    """Entry point for executing Stage 5."""
    print(f"\n==================================================================")
    print(f"STAGE 5: HOOK & PEDAGOGICAL BLUEPRINT GENERATION")
    print(f"Role: Pedagogical Blueprint - Follows Audio Stages 0-4 from Raw Video")
    print(f"Dynamic SME Framing: Enabled (Initial layout assignments)")
    print(f"==================================================================")

    generator = HookGenerator(api_provider=api_provider)
    out_path = generator.run(input_file, output_file, lesson_title=lesson_title)

    with open(out_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"✓ Stage 5 Complete: Pedagogical blueprint created for '{data.get('concept', 'Lesson')}'")
    print(f"  - Hook Type: {data.get('hook', {}).get('type')}")
    print(f"  - Hook Opening: {data.get('hook', {}).get('statement', '')[:75]}...")
    print(f"  - Total Scenes Planned: {len(data.get('scene_blueprint', []))}")
    for sc in data.get("scene_blueprint", []):
        sme = sc.get("sme_framing_recommendation", {})
        print(f"    * Scene {sc.get('scene_index')}: Layout {sme.get('layout')}% ({sme.get('description')})")
    print(f"  Blueprint saved -> {out_path}\n")
    return out_path


# Backward compatibility alias
run_stage_0 = run_stage_5


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 5: Hook & Pedagogical Blueprint Generation")
    parser.add_argument("-i", "--input", required=True, help="Input transcript JSON or raw context text file")
    parser.add_argument("-o", "--output", required=True, help="Output hook blueprint JSON file")
    parser.add_argument("-l", "--lesson-title", default=None, help="Lesson title")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM provider")
    args = parser.parse_args()

    run_stage_5(args.input, args.output, lesson_title=args.lesson_title, api_provider=args.provider)
