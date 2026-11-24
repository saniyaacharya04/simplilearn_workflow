#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 7: PRESENTATION EXPERIENCE PLANNER
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 7
   - Script Name: 7_presentation_experience_planner.py
   - Primary Class: PresentationExperiencePlanner
   - Pipeline Role:
     Transforms static spatial presentation compositions into dynamic instructional viewing
     experiences. Determines animation construction order, object lifecycles, instructional
     reveals, focal highlight pulses (#F78908), annotations, visual continuity, and restrained
     motion transitions (0.8s broadcast swipe) without altering the established spatial layout.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 6 (6_presentation_composer.py):
       - How: Ingests {topic_id}_presentation_composition.json via
         6_presentation_composer_tracker.json.
       - Purpose: Provides the authoritative spatial canvas layout and container tree.
     * Stage 1 (1_generate_instructional_design.py):
       - How: Ingests {topic_id}_storyboard_blueprint.json.
       - Purpose: Supplies pedagogical emphasis goals and narrative flow.
   - Input Tracker: ppt_trackers/6_presentation_composer_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * {topic_id}_presentation_composition.json (Stage 6):
       Location: output/<TOPIC_NAME>/{topic_id}_presentation_composition.json
       Content: Spatial layout specifications and nested container bounds.
     * {topic_id}_storyboard_blueprint.json (Stage 1):
       Location: output/<TOPIC_NAME>/{topic_id}_storyboard_blueprint.json
       Content: Instructional storyboard blueprint.
     * Input Tracker:
       Location: ppt_trackers/6_presentation_composer_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 6_presentation_composer_tracker.json.
   - Step 2: Ingests presentation composition JSON.
   - Step 3: Invokes Gemini 3.5 Flash using presentation experience system prompts.
   - Step 4: Choreographs presentation step sequences: entrance reveals, active focus states,
     retention anchors, and exit transitions.
   - Step 5: Injects Simplilearn OSL 3.0 dynamic focus highlights: #F78908, 3px stroke,
     1.0s draw time.
   - Step 6: Establishes broadcast swipe transition timings (0.8s left-to-right).
   - Step 7: Writes experience planner JSON and atomically updates 7_experience_planner_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * {topic_id}_experience_planner.json:
       Location: output/<TOPIC_NAME>/{topic_id}_experience_planner.json
       Content: Detailed temporal choreography and reveal plans per presentation step.
     * experience_plan_gemini-3.6-flash.json:
       Location: output/<TOPIC_NAME>/experience_plan_gemini-3.6-flash.json
       Content: Mirrored copy of experience plan.
     * Output Tracker:
       Location: ppt_trackers/7_experience_planner_tracker.json
       Content: Atomic tracker confirming completion of experience planning.

6. DOWNSTREAM CONSUMERS:
   - Stage 9 (9_styling_generator.py): Ingests experience plans to inject design tokens.
================================================================================
"""

import os
import sys
import json
import re
import shutil
import argparse
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from pipeline.config import (
    HIGHLIGHT_COLOR,
    HIGHLIGHT_THICKNESS,
    HIGHLIGHT_DRAW_TIME,
    CANVAS_WIDTH,
    CANVAS_HEIGHT
)

SYSTEM_PROMPT_EXPERIENCE_PLANNER = """
        You are a Presentation Experience Planner for educational Manim videos.

        Your task is to transform a presentation composition into an instructional viewing experience.

        The instructional storyboard defines the pedagogy.
        The presentation composition defines the visual workspace.

        Treat both as canonical.

        Do NOT redesign the lesson.
        Do NOT modify the presentation composition.

        Your responsibility is to determine

        • construction order
        • object lifecycle
        • instructional emphasis
        • annotations
        • visual continuity
        • restrained motion
        • transitions

        that maximize learner understanding.

        ---

        INPUT

        1. Presentation Composition

        This input corresponds to exactly one scene.

        ---

        OBJECTIVE

        Describe how the learner experiences the presentation.

        The visual workspace is already designed and is a spatial contract.

        Preserve every spatial detail from the Presentation Composition, including:
        • occupied regions
        • relative proportions
        • anchors
        • alignments
        • spacing
        • directional relationships
        • grouping
        • hierarchy
        • safe margins
        • persistence
        • internal component geometry

        You determine WHEN components appear and evolve, not WHERE they are designed to be.

        Determine

        • what appears first
        • what appears next
        • what remains visible
        • what receives emphasis
        • what becomes annotated
        • how attention moves
        • how ideas connect
        • what transforms
        • what exits
        • how the workspace evolves

        Every visual change must correspond to genuine conceptual progress.

        ---

        OUTPUT

        Scene N:

        Instruction:

        <Presentation Step 1 experience>

        Instruction:

        <Presentation Step 2 experience>

        ...

        Exactly one Instruction for every Presentation Step.
        Make sure the correct scene number as specified in the input is used.

        Keep paragraph form.
        The detail level must exceed the Presentation Composition.
        Do not leave open references to either input.

        No bullets.
        No markdown symbols such as # preceding Scene or Instruction.
        No commentary.

        ---

        PROGRESSIVE REVEAL

        Treat every Presentation Step as an explicit sequence of workspace states, not merely a description of the final state.

        For every instructional component specify its lifecycle:

        1. ENTRY — how and when it is introduced.
        2. SETTLE — its resulting position and relationship to surrounding content.
        3. ACTIVE STATE — when/how it is emphasized, annotated or transformed.
        4. TRANSITION — what happens when attention moves elsewhere.
        5. EXIT — whether it is removed, transformed, repositioned or retained.

        Do not assume that multiple objects appear simultaneously, but do not simplify their spatial specification when determining their reveal order.
        Progressive reveal changes visibility, not composition.

        Unless simultaneous construction is instructionally necessary, reveal related objects sequentially in the order they are explained.

        Within each sequence explicitly distinguish:

        • first object
        • subsequent objects
        • dependent objects
        • annotations introduced after the target exists
        • emphasis applied after the relevant concept is visible
        • objects removed before the next major concept is introduced

        Never describe an effect before the object it acts upon exists.

        Never introduce an annotation before its target is visible.

        Never describe an exit without specifying what remains afterward.

        ---

        COMPOSITION FIDELITY

        Treat the Presentation Composition as immutable.

        When describing each experience sequence, carry forward the composition's spatial specifications verbatim or with equivalent precision.

        Do NOT:
        • generalize precise spatial descriptions
        • replace occupied regions with vague positioning
        • omit internal component relationships
        • collapse multiple specified elements into one
        • change relative scale or footprint
        • alter alignment or spacing
        • relocate components for convenience
        • infer a simpler layout

        Every component specified in the composition must remain represented in the experience plan, including its internal children, text, assets, annotations and spatial relationships.

        If a component is introduced progressively, preserve its final specified position and internal arrangement.

        If only part of a component is visible at a given moment, specify which part is visible while retaining its defined spatial relationship to the complete component.

        The experience plan may change visibility, emphasis and lifecycle, but must not redesign the spatial composition.

        ---

        OBJECT ENTRY

        For every newly introduced visual, state

        • what enters first
        • what follows
        • what it is anchored to
        • where it settles relative to existing components
        • whether it is constructed independently or derived from an existing object

        Use implementation-oriented language such as

        "First..., then..., after..., once..., finally..."

        Avoid ambiguous phrases such as

        • appears
        • comes in
        • emerges
        • animates naturally
        • builds dynamically
        • floods
        • expands across

        unless the exact visual change is also specified.

        Do not imply that an entire complex component appears as one atomic object when its internal elements are intended to be revealed progressively.

        ---

        OBJECT EXIT & TRANSITION

        Explicitly determine what happens when an instructional idea is complete.

        Prefer, in order:

        • transform completed content into the next related concept
        • remove obsolete content
        • reposition a compact useful reference
        • retain only genuinely necessary context

        Before introducing a new major concept, ensure the workspace has sufficient visual space.

        Do not layer new instructional content over completed content merely for continuity.

        Do not retain obsolete visuals at reduced opacity.

        When an object exits, state what replaces its visual role, if anything.
        Please do not miss out on any textual elements specified in the presentation composition. Do not remove any textual details assuming downstream renderers will figure it out.

        ---

        ZERO PLACEHOLDERS MANDATE (CRITICAL)

        Do NOT plan or describe placeholder containers, outlined placeholder boxes, dummy text, avatar placeholders, or temporary frames.
        All elements entered and transformed must be concrete, authentic, named components (e.g., 'Memory Layer sub-container', 'Knowledge Retrieval Panel', never 'placeholder container').

        ---

        SPATIAL SPECIFICATION

        For every newly introduced, transformed or persistent component, preserve and explicitly restate its spatial specification from the Presentation Composition.

        Do not substitute a detailed spatial specification with a generic phrase such as "in the right column" when the input specifies internal positions, proportions, spacing or alignment.

        Preserve nested spatial relationships recursively: parent → child → sub-child.

        • placement within the available workspace using relative direction
        • alignment relative to existing components
        • spacing from neighboring components
        • approximate occupied screen region
        • construction order
        • transformation source, if any
        • persistence
        • removal/minimization behavior

        Avoid vague spatial descriptions such as

        • nearby
        • beside
        • below
        • around
        • expands naturally

        Describe the intended instructional arrangement explicitly.

        ---

        ATTENTION

        At every instructional moment make it obvious

        • what changed
        • where to look
        • why it matters
        • how it relates to previous content

        Only one primary instructional focus should receive strong emphasis at a time.

        Do not introduce multiple simultaneous emphasis effects unless the comparison itself is the learning objective.

        ---

        ANNOTATIONS

        Use annotations to explain relationships rather than decorate the screen.

        Whenever useful introduce

        • labels
        • arrows
        • brackets
        • connector lines
        • highlights
        • emphasis boxes
        • comparison markers
        • temporary notes

        For every annotation specify

        • exact target
        • exact annotation text
        • entry point in the sequence
        • what it explains
        • how long it remains
        • what causes it to disappear or transform

        Introduce annotations only after their target exists.

        Prefer progressive annotation over displaying all explanatory markers simultaneously.

        ---

        EMPHASIS

        Use restrained emphasis.

        Prefer

        • border emphasis
        • temporary highlights
        • subtle scaling
        • progressive disclosure

        Avoid relying on reduced opacity to preserve old content.

        Reserve stronger emphasis for

        • key definitions
        • misconceptions
        • comparisons
        • causal relationships
        • important conclusions

        Avoid repeating the same emphasis construct when another mechanism communicates the distinction more clearly.

        ---

        VISUAL EVOLUTION

        Describe the actual workspace state after each meaningful change.

        For every transition explicitly state

        • what enters
        • what remains fixed
        • what is emphasized
        • what is annotated
        • what moves or transforms
        • what exits
        • what the learner should now perceive

        Do not describe only the final arrangement.

        The reader must be able to reconstruct the complete visual sequence without inventing intermediate states.

        ---

        CONTINUITY

        Maintain one evolving instructional workspace.

        Prefer

        • extending existing components
        • transforming related objects
        • repositioning useful references
        • collapsing completed content into compact summaries

        Avoid persistent background clutter.

        Do NOT leave previous instructional elements visible at reduced opacity.

        If previous material remains necessary, use a clearly defined compact reference representation.

        Otherwise remove it before introducing the next major instructional structure.

        ---

        PEDAGOGICAL FLOW

        The explanation should unfold naturally.

        Each reveal must build upon previous understanding.

        Introduce terminology before emphasizing it.

        Explain relationships before presenting conclusions.

        Whenever possible

        • compare
        • connect
        • reinforce
        • summarize visually

        rather than introducing disconnected elements.

        The visual sequence should follow the narration's conceptual order.

        Do not reveal the conclusion before the reasoning that supports it.

        ---

        WORKSPACE ECONOMY

        Keep the workspace clean and intentionally composed.

        Avoid introducing new components into crowded regions.

        When a new concept requires substantial space:

        • remove completed instructional elements
        • collapse only genuinely useful references
        • reposition compact references when necessary

        The learner should always perceive one primary instructional focus.

        ---

        CONSTRAINTS

        Do NOT

        • redesign layouts
        • modify composition
        • change visible text
        • alter instructional meaning
        • change narration alignment
        • invent assets
        • rename asset_<n>
        • rename image_<n>

        Preserve every asset_<n> and image_<n> exactly.

        Do NOT preserve obsolete components using reduced opacity unless explicitly required by the storyboard.

        Most importantly, preserve the Presentation Composition as a spatial contract while specifying the complete instructional lifecycle: what enters, in what order, where it settles according to the defined composition, what receives attention, what gets annotated, what transforms, what exits, and what remains for the next step.

        Never trade spatial precision for brevity.

        Retain all LaTeX formatting of mathematical symbols, equations, expressions and other artefacts.
        Make sure any mathematical symbols, expressions and equations are formatted in LaTeX even if not explicitly specified in the input Presentation Steps

        The output should be an implementation-ready experience plan that allows a downstream renderer to reproduce the intended viewing sequence without making assumptions about progressive reveal, object lifecycle or transition behavior.
        """

USER_PROMPT_EXPERIENCE_PLANNER = """
        For designing the correct experience, refer to the following:
        ------------------------
        Presentation Composition:
        {presentation_composition}
        """


def parse_experience_output(input_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parses LLM experience output text into structured scene instructions.
    Matches Simplilearn presentation experience planner parsing logic.
    """
    lines = input_text.strip().splitlines()
    output: Dict[str, List[Dict[str, Any]]] = {}
    scene_number = None
    current_instruction_lines: List[str] = []

    def flush_instruction():
        nonlocal current_instruction_lines
        if not current_instruction_lines:
            return
        content = " ".join(current_instruction_lines).strip()
        if content and scene_number:
            if scene_number not in output:
                output[scene_number] = []
            output[scene_number].append({"matching_section": content})
        current_instruction_lines = []

    for line in lines:
        line_clean = re.sub(r"\*\*", "", line).strip()
        if not line_clean:
            continue

        if re.match(r"^-?\s*Instruction(?:\s*\d+)?\s*[:.]", line_clean, re.IGNORECASE):
            flush_instruction()
            content_match = re.match(r"^-?\s*Instruction(?:\s*\d+)?\s*[:.]\s*(.*)", line_clean, re.IGNORECASE)
            if content_match and content_match.group(1).strip():
                current_instruction_lines.append(content_match.group(1).strip())
            continue

        scene_match = re.match(r"^#*\s*Scene\s*(\d+)\s*(?::.*)?$", line_clean, re.IGNORECASE)
        if scene_match and len(line_clean) < 80:
            flush_instruction()
            scene_number = scene_match.group(1)
            output[scene_number] = []
            continue

        if scene_number is not None:
            current_instruction_lines.append(line_clean)

    flush_instruction()
    return output


class PresentationExperiencePlanner:
    """
    Plans visual reveals, focal highlights, and animation timing for every scene step.
    """

    def __init__(
        self,
        input_tracker_path: Optional[str] = None,
        output_tracker_path: Optional[str] = None,
        google_api_key: Optional[str] = None,
        claude_api_key: Optional[str] = None,
        input_folder: Optional[str] = None,
        api_provider: str = "auto",
        api_key: Optional[str] = None,
        model_name: str = "gemini-3.5-flash",
        **kwargs
    ):
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        self.claude_api_key = claude_api_key or os.environ.get("CLAUDE_API_KEY")
        self.input_folder = input_folder or "."
        self.api_provider = api_provider.lower()
        self.model_name = model_name
        self.api_key = api_key or self.google_api_key or self.claude_api_key or os.environ.get("GEMINI_API_KEY")

    def plan_scene_local(self, scene: Dict[str, Any], sid: int) -> List[Dict[str, Any]]:
        """Deterministic local experience plan adhering to Simplilearn OSL 3.0."""
        title = scene.get("title", f"Scene {sid}")
        layout = str(scene.get("sme_layout", "70"))
        instructions = scene.get("instructions", [])

        steps = []
        for idx, instr in enumerate(instructions, 1):
            matching = instr.get("matching_section", title)
            step_desc = (
                f"Instruction: In Step {idx}, smoothly fade in the scene title '{title}' with a subtle upward drift. "
                f"Introduce living vector mechanism and transparent hero illustration with smooth reveal. "
                f"Progressively reveal content components aligned with spoken narration. "
                f"At the key takeaway phrase, apply dynamic focus highlight ({HIGHLIGHT_COLOR}, thickness {HIGHLIGHT_THICKNESS}px, duration {HIGHLIGHT_DRAW_TIME}s) "
                f"to draw visual attention without moving elements out of place. {matching}"
            )
            steps.append({"matching_section": step_desc})

        if not steps:
            steps.append({
                "matching_section": (
                    f"Instruction: Smoothly reveal '{title}' with high-contrast accenting, apply {HIGHLIGHT_COLOR} focus highlight on primary concept, "
                    f"and persist all visual scaffolding throughout spoken narration."
                )
            })

        return steps

    def call_llm(
        self,
        user_prompt: str,
        system_prompt: str,
        model_override: Optional[str] = None,
        vendor_override: Optional[str] = None
    ) -> str:
        """Dispatches LLM generation to Gemini or Claude based on config and available keys."""
        target_model = model_override or self.model_name
        vendor = (vendor_override or self.api_provider).lower()

        # 1. Claude if requested or model contains claude
        if (vendor == "claude" or "claude" in target_model.lower()) and self.claude_api_key:
            try:
                from anthropic import Anthropic
                client = Anthropic(api_key=self.claude_api_key, timeout=800)
                m_name = target_model if "claude" in target_model.lower() else "claude-haiku-4-5-20251001"
                print(f"    -> [ExperiencePlanner] Invoking Claude model: {m_name}")
                message = client.messages.create(
                    max_tokens=8000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    model=m_name
                )
                if message and message.content:
                    return message.content[0].text
            except Exception as e:
                print(f"  [ExperiencePlanner] Claude call notice: {e}. Falling back to Gemini...")

        # 2. Gemini via google.genai
        gemini_key = self.google_api_key or self.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if gemini_key:
            g_model = target_model if ("gemini" in target_model.lower() or "flash" in target_model.lower()) else "gemini-3.6-flash"
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=gemini_key)
                print(f"    -> [ExperiencePlanner] Invoking Gemini (google.genai): {g_model}")
                resp = client.models.generate_content(
                    model=g_model,
                    contents=f"{system_prompt}\n\nUser Query: {user_prompt}",
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=8000
                    )
                )
                if resp and resp.text:
                    return resp.text
            except Exception as e:
                print(f"  [ExperiencePlanner] google.genai notice: {e}. Trying fallback models...")
                for fallback_m in ["gemini-2.5-flash", "gemini-1.5-flash"]:
                    try:
                        print(f"    -> [ExperiencePlanner] Trying fallback: {fallback_m}")
                        resp = client.models.generate_content(
                            model=fallback_m,
                            contents=f"{system_prompt}\n\nUser Query: {user_prompt}"
                        )
                        if resp and resp.text:
                            return resp.text
                    except Exception:
                        pass
                try:
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=gemini_key, transport="rest")
                    print(f"    -> [ExperiencePlanner] Invoking Gemini (google.generativeai): {g_model}")
                    m = genai_legacy.GenerativeModel(g_model)
                    resp = m.generate_content(f"{system_prompt}\n\nUser Query: {user_prompt}")
                    if resp and resp.text:
                        return resp.text
                except Exception as ex:
                    print(f"  [ExperiencePlanner] google.generativeai failed: {ex}")

        return ""

    def plan_all_experiences(
        self,
        composition_data: Optional[Dict[str, Any]] = None,
        blueprint: Optional[Dict[str, Any]] = None,
        classified_catalog: Optional[Dict[str, Any]] = None,
        constructed_catalog: Optional[Dict[str, Any]] = None,
        base_folder: Optional[str] = None,
        target_scene: Optional[str] = None,
        exp_model_name: Optional[str] = None,
        exp_vendor: Optional[str] = None,
        jazzy_model_name: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
        """
        Processes each scene composition, executing Gemini / Claude LLM calls
        to synthesize granular, synchronized presentation viewing experiences.
        Ingests enhanced_anim_<model>.json and outputs experience_plan_<model>.json.
        """
        model_to_use = exp_model_name or self.model_name
        vendor_to_use = exp_vendor or self.api_provider

        # 1. Resolve raw and experience plan output file in base_folder if provided
        raw_experience_planner_file = None
        experience_planner_output_file = None
        existing_experience = {}
        if base_folder:
            raw_experience_planner_file = os.path.join(base_folder, f"raw_experience_plan_{model_to_use}.txt")
            experience_planner_output_file = os.path.join(base_folder, f"experience_plan_{model_to_use}.json")
            if os.path.exists(experience_planner_output_file):
                try:
                    with open(experience_planner_output_file, "r", encoding="utf-8") as f:
                        existing_experience = json.load(f)
                except Exception:
                    existing_experience = {}

        # 2. Ingest presentation composition (authoritative 2D spatial layout from Stage 6 enhanced_anim)
        presentation_composer: Dict[str, List[Dict[str, Any]]] = {}
        if base_folder:
            meta_dir = os.path.join(base_folder, "metadata_blueprints")
            jazzy_candidates = []
            if jazzy_model_name:
                jazzy_candidates.append(os.path.join(meta_dir, f"enhanced_anim_{jazzy_model_name}.json"))
                jazzy_candidates.append(os.path.join(base_folder, f"enhanced_anim_{jazzy_model_name}.json"))
            jazzy_candidates.extend(glob.glob(f"{meta_dir}/enhanced_anim_*.json"))
            jazzy_candidates.extend(glob.glob(f"{base_folder}/enhanced_anim_*.json"))
            for cand in jazzy_candidates:
                if os.path.exists(cand):
                    try:
                        with open(cand, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                presentation_composer = data
                                print(f"  [ExperiencePlanner] Ingested spatial composition from: {os.path.basename(cand)}")
                                break
                    except Exception as e:
                        print(f"  [ExperiencePlanner] Notice loading {cand}: {e}")

        # Fallback to composition_data if file not found
        if not presentation_composer and composition_data:
            if isinstance(composition_data, dict) and "scenes" in composition_data:
                for sc in composition_data["scenes"]:
                    sid = str(sc.get("scene_id") or sc.get("scene_index") or len(presentation_composer) + 1)
                    presentation_composer[sid] = sc.get("instructions", [])
            elif isinstance(composition_data, dict):
                presentation_composer = composition_data

        # 3. Resolve storyboard instructions (step-by-step for title/narration)
        prelim_storyboard: Dict[str, List[Dict[str, Any]]] = {}
        if base_folder:
            meta_dir = os.path.join(base_folder, "metadata_blueprints")
            inst_matches = (
                glob.glob(f"{meta_dir}/instructions_*.json") or
                glob.glob(f"{base_folder}/instructions_*.json") or
                glob.glob(f"{meta_dir}/*instructions*.json") or
                glob.glob(f"{base_folder}/*instructions*.json")
            )
            if inst_matches:
                try:
                    with open(inst_matches[0], "r", encoding="utf-8") as f:
                        prelim_storyboard = json.load(f)
                except Exception:
                    prelim_storyboard = {}

        if not prelim_storyboard and blueprint:
            for s_idx, scene in enumerate(blueprint.get("scenes", []), 1):
                sid = str(scene.get("scene_id") or scene.get("scene_index") or s_idx)
                steps = scene.get("presentation_steps") or scene.get("steps", [])
                if steps:
                    prelim_storyboard[sid] = steps

        # 4. Resolve structured asset classification
        structured_asset_classification: Dict[str, List[Dict[str, Any]]] = {}
        if classified_catalog:
            if isinstance(classified_catalog, dict) and "scenes" in classified_catalog:
                for sc in classified_catalog.get("scenes", []):
                    structured_asset_classification[str(sc.get("scene_id"))] = sc.get("steps", [])
            elif isinstance(classified_catalog, dict):
                structured_asset_classification.update(classified_catalog)
        elif base_folder:
            cand = list(Path(base_folder).glob("asset_classification_*.json")) or list(Path(base_folder).glob("*classified_assets*.json"))
            if cand:
                try:
                    with open(cand[0], "r", encoding="utf-8") as f:
                        c_data = json.load(f)
                        if isinstance(c_data, dict) and "scenes" in c_data:
                            for sc in c_data["scenes"]:
                                structured_asset_classification[str(sc.get("scene_id"))] = sc.get("steps", [])
                        elif isinstance(c_data, dict):
                            structured_asset_classification.update(c_data)
                except Exception:
                    pass

        # 5. Resolve construction guidelines
        construction_guidelines: Dict[str, str] = {}
        if constructed_catalog:
            if isinstance(constructed_catalog, dict) and "constructed_catalog" in constructed_catalog:
                for k, v in constructed_catalog["constructed_catalog"].items():
                    construction_guidelines[k] = v.get("construction_paragraph", "")
            elif isinstance(constructed_catalog, dict):
                construction_guidelines.update(constructed_catalog)
        elif base_folder:
            cand = list(Path(base_folder).glob("construction_output_*.json")) or list(Path(base_folder).glob("*constructed_assets*.json"))
            if cand:
                try:
                    with open(cand[0], "r", encoding="utf-8") as f:
                        c_data = json.load(f)
                        if isinstance(c_data, dict) and "constructed_catalog" in c_data:
                            for k, v in c_data["constructed_catalog"].items():
                                construction_guidelines[k] = v.get("construction_paragraph", "")
                        elif isinstance(c_data, dict):
                            construction_guidelines.update(c_data)
                except Exception:
                    pass

        topic = "Technical Architecture"
        if blueprint:
            topic = blueprint.get("concept") or blueprint.get("lesson_title") or topic

        experience_output: Dict[str, Any] = {
            "topic": topic,
            "total_scenes": len(presentation_composer),
            "scenes": []
        }

        experience_planner = dict(existing_experience)

        print(f"[*] Planning presentation viewing experiences via {vendor_to_use} ({model_to_use}) across {len(presentation_composer)} scenes...")

        for group, pairs in presentation_composer.items():
            if target_scene and str(group) != str(target_scene):
                continue

            scene_title = f"Scene {group}"
            if blueprint:
                for sc in blueprint.get("scenes", []):
                    if str(sc.get("scene_id")) == str(group):
                        scene_title = sc.get("title", scene_title)
                        break

            # Build present_composition containing canonical 2D spatial layouts and asset contexts
            present_composition = f"Scene {group}:\n"
            for i, pair in enumerate(pairs):
                present_composition += "#####################################################\n"
                present_composition += f"Presentation Step {i+1}:\n\n"
                step_title = ""
                if str(group) in prelim_storyboard and i < len(prelim_storyboard[str(group)]):
                    step_title = prelim_storyboard[str(group)][i].get("title", "")
                present_composition += f"Title: {step_title}\n"
                present_composition += f"{pair.get('matching_section', '')}\n\n"

                suggestions_group = structured_asset_classification.get(str(group), [])
                step_assets = suggestions_group[i] if (i < len(suggestions_group) and isinstance(suggestions_group[i], dict)) else {}

                if step_assets.get("Asset_Suggestion") and step_assets.get("Asset_names"):
                    present_composition += "Presentation Step Asset Constructions:\n\n"
                    for k, asset_name in enumerate(step_assets["Asset_names"]):
                        guideline = construction_guidelines.get(asset_name, "")
                        if guideline:
                            present_composition += f"{asset_name}: {guideline}\n\n"

                if step_assets.get("Image_Suggestion") and step_assets.get("Image_names"):
                    present_composition += "Presentation Step Images:\n\n"
                    for k, img_name in enumerate(step_assets["Image_names"]):
                        if k < len(step_assets.get("Image_Suggestion", [])):
                            present_composition += f"{img_name}: {step_assets['Image_Suggestion'][k]}\n\n"

            formatted_user_prompt = USER_PROMPT_EXPERIENCE_PLANNER.replace("{presentation_composition}", present_composition)
            formatted_user_prompt += f"\n\nCRITICAL REQUIREMENT: This scene contains EXACTLY {len(pairs)} Presentation Steps. You MUST output EXACTLY {len(pairs)} 'Instruction:' blocks for this scene (one per Presentation Step). Do NOT generate fewer or more than {len(pairs)} instructions."

            print(f"  -> Generating temporal experience plan for Scene {group} ({len(pairs)} steps)...")
            generated_result = self.call_llm(
                user_prompt=formatted_user_prompt,
                system_prompt=SYSTEM_PROMPT_EXPERIENCE_PLANNER,
                model_override=model_to_use,
                vendor_override=vendor_to_use
            )

            if generated_result and len(generated_result.strip()) > 50:
                if raw_experience_planner_file:
                    with open(raw_experience_planner_file, "a", encoding="utf-8") as f:
                        f.write(f"Scene {group}:\n\n{generated_result.strip()}\n\n")

                story_element = parse_experience_output(generated_result)
                scene_steps = story_element.get(str(group), [])
            else:
                print(f"  [ExperiencePlanner] Scene {group} LLM returned empty, using fallback.")
                matching_scene = {"title": scene_title, "instructions": pairs, "sme_layout": "70"}
                scene_steps = self.plan_scene_local(matching_scene, int(group) if str(group).isdigit() else 1)

            # Reconcile step counts to guarantee 100% structural parity with spatial composition
            target_len = len(pairs)
            if len(scene_steps) > target_len:
                merged_tail = "\n\n".join(
                    it.get("matching_section", "") for it in scene_steps[target_len - 1:] if it.get("matching_section")
                )
                scene_steps[target_len - 1]["matching_section"] = merged_tail
                scene_steps = scene_steps[:target_len]
            elif len(scene_steps) < target_len:
                for idx in range(len(scene_steps), target_len):
                    scene_steps.append({"matching_section": pairs[idx].get("matching_section", "")})

            # Enrich steps with narration and assets
            for i, step in enumerate(scene_steps):
                narration = ""
                if str(group) in prelim_storyboard and i < len(prelim_storyboard[str(group)]):
                    narration = (
                        prelim_storyboard[str(group)][i].get("narration_statement") or
                        prelim_storyboard[str(group)][i].get("narration") or
                        prelim_storyboard[str(group)][i].get("voiceover_narration", "")
                    )
                elif i < len(pairs):
                    narration = pairs[i].get("narration_statement") or pairs[i].get("narration") or pairs[i].get("voiceover_narration", "")
                if not narration and str(group) in blueprint_scenes_map:
                    narration = blueprint_scenes_map[str(group)].get("voiceover_narration") or blueprint_scenes_map[str(group)].get("narration", "")
                step["narration_statement"] = narration

                suggestions_group = structured_asset_classification.get(str(group), [])
                if i < len(suggestions_group) and isinstance(suggestions_group[i], dict):
                    step["assets"] = suggestions_group[i].get("Asset_names")
                else:
                    step["assets"] = None

            experience_planner[str(group)] = scene_steps

            # Dynamically resolve layout from composition or blueprint
            matching_comp_sc = next((sc for sc in composition_data.get("scenes", []) if str(sc.get("scene_id")) == str(group)), {}) if isinstance(composition_data, dict) else {}
            s_layout = str(matching_comp_sc.get("sme_layout") or (blueprint_scenes_map.get(str(group), {}).get("sme_layout")) or "70")
            scene_vo = (
                pairs[0].get("narration_statement") or pairs[0].get("narration") or matching_comp_sc.get("voiceover_narration") or ""
                if pairs else matching_comp_sc.get("voiceover_narration", "")
            )

            experience_output["scenes"].append({
                "scene_id": int(group) if str(group).isdigit() else group,
                "title": scene_title,
                "sme_layout": s_layout,
                "voiceover_narration": scene_vo,
                "experience_steps": scene_steps
            })

        print(f"✓ Presentation Experience Planning Complete: Choreographed {len(experience_planner)} scene experiences")
        return experience_output, experience_planner

    def run(
        self,
        composition_path: str,
        output_path: str,
        blueprint_path: Optional[str] = None,
        assets_path: Optional[str] = None,
        constructed_path: Optional[str] = None,
        base_folder: Optional[str] = None,
        target_scene: Optional[str] = None,
        exp_model_name: Optional[str] = None,
        exp_vendor: Optional[str] = None,
        jazzy_model_name: Optional[str] = None
    ) -> str:
        folder = base_folder or str(Path(composition_path).parent)
        config_path = os.path.join(folder, "ex_config.json")
        ex_conf = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as cf:
                    ex_conf = json.load(cf)
            except Exception:
                ex_conf = {}

        if not target_scene:
            target_scene = os.environ.get("TARGET_SCENE")
        if not exp_model_name:
            exp_model_name = ex_conf.get("exp_model_name", self.model_name)
        if not exp_vendor:
            exp_vendor = ex_conf.get("exp_vendor", "google")
        if not jazzy_model_name:
            jazzy_model_name = ex_conf.get("jazzy_model_name", "claude-haiku-4-5-20251001")

        composition_data = None
        if os.path.exists(composition_path):
            with open(composition_path, "r", encoding="utf-8") as f:
                composition_data = json.load(f)

        blueprint = None
        if blueprint_path and Path(blueprint_path).exists():
            with open(blueprint_path, "r", encoding="utf-8") as f:
                blueprint = json.load(f)

        classified = None
        if assets_path and Path(assets_path).exists():
            with open(assets_path, "r", encoding="utf-8") as f:
                classified = json.load(f)

        constructed = None
        if constructed_path and Path(constructed_path).exists():
            with open(constructed_path, "r", encoding="utf-8") as f:
                constructed = json.load(f)

        plan_output, experience_dict = self.plan_all_experiences(
            composition_data=composition_data,
            blueprint=blueprint,
            classified_catalog=classified,
            constructed_catalog=constructed,
            base_folder=folder,
            target_scene=target_scene,
            exp_model_name=exp_model_name,
            exp_vendor=exp_vendor,
            jazzy_model_name=jazzy_model_name
        )

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(plan_output, f, indent=2, ensure_ascii=False)

        # Write authoritative experience_plan_<model>.json directly inside meta_dir
        meta_dir = Path(folder) / "metadata_blueprints"
        meta_dir.mkdir(parents=True, exist_ok=True)
        m_name = exp_model_name or self.model_name
        experience_file = meta_dir / f"experience_plan_{m_name}.json"
        with open(experience_file, "w", encoding="utf-8") as f:
            json.dump(experience_dict, f, indent=4, ensure_ascii=False)
        print(f"  Authoritative experience plan saved -> {experience_file}")

        # Authoritative experience plan saved inside meta_dir

        print(f"  Experience plan saved -> {output_path}")
        return str(out)

    def _load_tracker(self, filepath):
        if not filepath or not os.path.exists(filepath):
            return {}
        try:
            try:
                import portalocker
                with open(filepath, 'r', encoding='utf-8') as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    try:
                        content = f.read()
                        data = json.loads(content) if content else {}
                    except json.JSONDecodeError:
                        data = {}
                    finally:
                        portalocker.unlock(f)
                return data
            except ImportError:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading tracker {filepath}: {e}")
            return {}

    def _save_tracker(self, filepath, data):
        if not filepath:
            return
        lock_path = filepath + ".lock"
        try:
            try:
                import portalocker
                with portalocker.Lock(lock_path, timeout=60):
                    current = {}
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                current = json.load(f)
                        except Exception:
                            current = {}
                    current.update(data)
                    temp_file = filepath + f".tmp.{os.getpid()}"
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(current, f, indent=4, ensure_ascii=False)
                    os.replace(temp_file, filepath)
            except ImportError:
                current = {}
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            current = json.load(f)
                    except Exception:
                        current = {}
                current.update(data)
                temp_file = filepath + f".tmp.{os.getpid()}"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(current, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, filepath)
        except Exception as e:
            print(f"Error saving tracker {filepath}: {e}")

    def process_files(self, target_topic_id=None):
        """Processes topic folders based on input tracker or topic folders."""
        in_tracker = self._load_tracker(self.input_tracker_path) if self.input_tracker_path else {}
        out_tracker = self._load_tracker(self.output_tracker_path) if self.output_tracker_path else {}

        if in_tracker:
            topics = [target_topic_id] if target_topic_id else list(in_tracker.keys())
        elif os.path.exists(self.input_folder):
            subdirs = [d for d in os.listdir(self.input_folder) if os.path.isdir(os.path.join(self.input_folder, d))]
            topics = [target_topic_id] if target_topic_id else sorted(subdirs)
        else:
            topics = [target_topic_id] if target_topic_id else []

        target_scene = os.environ.get("TARGET_SCENE")

        for topic_id in topics:
            if target_topic_id and topic_id != target_topic_id:
                continue

            if in_tracker and topic_id in in_tracker:
                if not in_tracker[topic_id].get("processed", False) and os.environ.get("FORCE_RUN") != "1":
                    print(f"Skipping {topic_id}: Input tracker not marked as processed.")
                    continue

            if out_tracker and topic_id in out_tracker and out_tracker[topic_id].get("processed", False) and os.environ.get("FORCE_RUN") != "1" and not target_scene:
                print(f"Skipping {topic_id}: Already processed in presentation experience planner tracker.")
                continue

            topic_dir = os.path.join(self.input_folder, topic_id)
            if not os.path.exists(topic_dir):
                continue

            # Load ex_config.json if present
            config_path = os.path.join(topic_dir, "ex_config.json")
            ex_conf = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as cf:
                        ex_conf = json.load(cf)
                except Exception:
                    ex_conf = {}

            exp_model = ex_conf.get("exp_model_name", self.model_name)
            exp_vend = ex_conf.get("exp_vendor", "google")
            jazzy_model = ex_conf.get("jazzy_model_name", "claude-haiku-4-5-20251001")

            print(f"Processing Presentation Experience Planner for {topic_id}...")
            meta_dir = os.path.join(topic_dir, "metadata_blueprints")
            os.makedirs(meta_dir, exist_ok=True)
            composition_file = os.path.join(meta_dir, f"{topic_id}_presentation_composition.json")
            if not os.path.exists(composition_file):
                composition_file = os.path.join(topic_dir, f"{topic_id}_presentation_composition.json")
            if not os.path.exists(composition_file):
                composition_file = os.path.join(topic_dir, "presentation_composition.json")

            blueprint_file = os.path.join(meta_dir, f"{topic_id}_storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(topic_dir, f"{topic_id}_storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(meta_dir, "storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(topic_dir, "storyboard_blueprint.json")

            assets_file = os.path.join(meta_dir, f"{topic_id}_classified_assets.json")
            if not os.path.exists(assets_file):
                assets_file = os.path.join(topic_dir, f"{topic_id}_classified_assets.json")
            if not os.path.exists(assets_file):
                assets_file = os.path.join(topic_dir, "classified_assets.json")

            constructed_file = os.path.join(meta_dir, f"{topic_id}_constructed_assets.json")
            if not os.path.exists(constructed_file):
                constructed_file = os.path.join(topic_dir, f"{topic_id}_constructed_assets.json")
            if not os.path.exists(constructed_file):
                constructed_file = os.path.join(topic_dir, "constructed_assets.json")

            out_experience = os.path.join(meta_dir, f"{topic_id}_experience_planner.json")
            try:
                self.run(
                    composition_path=composition_file,
                    output_path=out_experience,
                    blueprint_path=blueprint_file if os.path.exists(blueprint_file) else None,
                    assets_path=assets_file if os.path.exists(assets_file) else None,
                    constructed_path=constructed_file if os.path.exists(constructed_file) else None,
                    base_folder=topic_dir,
                    target_scene=target_scene,
                    exp_model_name=exp_model,
                    exp_vendor=exp_vend,
                    jazzy_model_name=jazzy_model
                )

                if self.output_tracker_path:
                    self._save_tracker(self.output_tracker_path, {
                        topic_id: {
                            "output_path": out_experience,
                            "processed": True,
                            "topic_name": topic_id,
                            "topic_id": topic_id,
                            "failure_reason": None
                        }
                    })
                print(f"Successfully planned presentation experience for {topic_id}.")
            except Exception as e:
                print(f"Error planning presentation experience for {topic_id}: {e}")
                if self.output_tracker_path:
                    self._save_tracker(self.output_tracker_path, {
                        topic_id: {
                            "output_path": None,
                            "processed": False,
                            "topic_name": topic_id,
                            "topic_id": topic_id,
                            "failure_reason": str(e)
                        }
                    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Presentation Experience Planner (Simplilearn OSL 3.0 Architecture)")
    parser.add_argument("-c", "--composition", required=True, help="Input presentation composition JSON")
    parser.add_argument("-o", "--output", required=True, help="Output experience plan JSON")
    parser.add_argument("-b", "--blueprint", default=None, help="Optional storyboard blueprint JSON")
    parser.add_argument("-a", "--assets", default=None, help="Optional classified assets JSON")
    parser.add_argument("-k", "--constructed", default=None, help="Optional constructed assets JSON")
    parser.add_argument("-t", "--target-scene", default=None, help="Optional target scene ID")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM API provider")
    parser.add_argument("-m", "--model", default="gemini-3.6-flash", help="Model name")
    args = parser.parse_args()

    planner = PresentationExperiencePlanner(
        api_provider=args.provider,
        model_name=args.model
    )
    planner.run(
        args.composition,
        args.output,
        blueprint_path=args.blueprint,
        assets_path=args.assets,
        constructed_path=args.constructed,
        target_scene=args.target_scene
    )
