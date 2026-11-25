#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 6: PRESENTATION COMPOSER
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 6
   - Script Name: 6_presentation_composer.py
   - Primary Class: PresentationComposer
   - Pipeline Role:
     Converts the instructional storyboard into an exhaustive, fully-specified presentation
     composition. Recursively expands every presentation step into a deterministic visual
     specification with nested container structures, directional spreads, explicit alignment
     axes, and anti-collision safe zones. Strictly enforces Simplilearn OSL 3.0 clearances
     (Layout 100 <= 20.0s minimal lower-third, Layout 70 x >= 760px, Layout 20 corner PIP)
     and preserves 1:1 step parity with the storyboard.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 1 (1_generate_instructional_design.py):
       - How: Ingests {topic_id}_storyboard_blueprint.json via
         1_instruction_design_output_tracker.json.
       - Purpose: Provides scene blueprints, step hierarchies, and narration text.
     * Stage 2 (2_asset_classification.py):
       - How: Ingests {topic_id}_classified_assets.json.
       - Purpose: Supplies categorized visual component definitions.
     * Stage 3 (3_asset_construction.py):
       - How: Ingests {topic_id}_constructed_assets.json.
       - Purpose: Supplies class-based geometric asset construction blueprints.
     * Stage 5 (5_populate_audio_runtime.py):
       - How: Ingests CGI_Input.json via 5_audio_output_tracker.json.
       - Purpose: Supplies step duration budgets.
   - Input Tracker: ppt_trackers/5_audio_output_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * {topic_id}_storyboard_blueprint.json (Stage 1):
       Location: output/<TOPIC_NAME>/{topic_id}_storyboard_blueprint.json
       Content: Master presentation storyboard with step descriptions.
     * {topic_id}_classified_assets.json (Stage 2):
       Location: output/<TOPIC_NAME>/{topic_id}_classified_assets.json
       Content: Categorized asset catalog.
     * {topic_id}_constructed_assets.json (Stage 3):
       Location: output/<TOPIC_NAME>/{topic_id}_constructed_assets.json
       Content: Procedural asset construction paragraphs and geometries.
     * Input Tracker:
       Location: ppt_trackers/5_audio_output_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 5_audio_output_tracker.json.
   - Step 2: Loads storyboard blueprint, classified assets, and constructed assets.
   - Step 3: Invokes Gemini 3.8 Flash using SYSTEM_PROMPT_PRESENTATION_COMPOSER to expand
     every presentation step into nested container hierarchies and layout coordinates.
   - Step 4: Enforces Simplilearn OSL 3.0 clearance rules:
     * Layout 70: Left frame (640x920, r=10px, blue band #2C81FE), content safe zone x >= 760px.
     * Layout 20: Top-right PIP (384x216 at 1496,40), title width <= 1440px, diagram y >= 270px.
     * Layout 100: Full-screen presenter restricted to <= 20.0s.
   - Step 5: Preserves LaTeX mathematical expressions verbatim.
   - Step 6: Validates 1:1 step parity and writes presentation composition JSON.
   - Step 7: Atomically updates 6_presentation_composer_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * {topic_id}_presentation_composition.json:
       Location: output/<TOPIC_NAME>/{topic_id}_presentation_composition.json
       Content: Fully expanded visual layout compositions with nested containers per step.
     * raw_parameters_<model>.json:
       Location: output/<TOPIC_NAME>/raw_parameters_<model>.json
       Content: Mirrored copy of composition parameters.
     * Output Tracker:
       Location: ppt_trackers/6_presentation_composer_tracker.json
       Content: Atomic tracker confirming completion of presentation composer.

6. DOWNSTREAM CONSUMERS:
   - Stage 7 (7_presentation_experience_planner.py): Uses composition specifications
     to plan visual reveal sequences and animation choreography.
================================================================================
"""

import os
import sys
import json
import re
import glob
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

from pipeline.config import (
    COLORS,
    ACCENT_COLOR,
    TEXT_COLOR,
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    SME_LAYOUT_100,
    SME_LAYOUT_70,
    SME_LAYOUT_20
)

SYSTEM_PROMPT_PRESENTATION_COMPOSER = """
        You are a Presentation Composition Planner for educational Manim videos.
        Your responsibility is to convert an instructional storyboard into a fully specified presentation composition.

        The storyboard already defines

        • instructional sequence
        • pedagogy
        • narration alignment
        • learning objectives

        Treat it as the canonical instructional plan.

        Do NOT redesign the lesson.
        Do NOT change instructional meaning.
        Do NOT introduce new concepts.
        Do NOT think about animation, timing, highlighting or visual effects.

        Your responsibility is to determine the complete visual composition of every presentation step.

        ---

        INPUT

        One Scene containing multiple Presentation Steps.

        Each Presentation Step may include

        • Purpose
        • Presentation Components
        • Visual Assets
        • Visual Evolution
        • Annotations
        • Key Takeaway
        • Persistence

        ---

        OBJECTIVE

        Expand every presentation step into a deterministic visual specification.

        Nothing visible on screen should be left to downstream interpretation.

        Describe

        • what exists
        • how it is grouped
        • how it is organized
        • how much workspace it occupies
        • where it is positioned
        • how components relate
        • what persists

        Do NOT decide

        • colors
        • typography styling
        • animations
        • visual effects

        Those are handled later.

        ---

        OUTPUT

        Scene N:

        Instruction:
        <Expanded presentation composition for Presentation Step 1>

        Instruction:
        <Expanded presentation composition for Presentation Step 2>

        ...

        Generate exactly one Instruction for every Presentation Step.

        Keep paragraph form.

        No bullets.
        No markdown symbols such as # preceding Scene or Instruction.
        No commentary.
        Stick to the exact format.

        ---

        COMPOSITION

        Treat every presentation component as a specification rather than a finished object.

        Recursively decompose every component until all visible instructional elements are explicitly defined.

        For every component specify

        • internal composition
        • parent container
        • child components
        • grouping
        • hierarchy
        • relative placement
        • occupied screen region
        • directional spread
        • relative size
        • alignment
        • spacing
        • persistence

        The downstream renderer must not need to invent internal structure.

        Prefer geometrically consistent compositions with explicit alignment axes, consistent spacing, proportional sizing and intentional symmetry over arbitrary placement.

        ---

        COMPONENT DECOMPOSITION

        Whenever a component contains

        • examples
        • categories
        • comparisons
        • stages
        • lists
        • statistics
        • equations
        • definitions
        • properties
        • tables
        • timelines
        • matrices

        expand them completely.

        Specify every visible instructional element and how it is grouped.

        Examples should be individually represented when they carry instructional meaning rather than being described collectively.

        Do not treat complex components as atomic objects.

        ---

        CREATIVE VISUAL AUTONOMY WITH COGNITIVE ANCHORS (THE GROUP 3 STANDARD)

        Strictly avoid boring 2005-style PowerPoint text dumps (paragraphs and plain bullet walls).
        HOWEVER, "minimal text" DOES NOT MEAN ZERO TEXT! Pure animations without text are disorienting and make it impossible for the learner to follow the teacher.
        
        Follow the canonical GROUP 3 STANDARD: Rich dynamic vector visuals paired with clean, persistent COGNITIVE LABELS & LIVING METAPHORS (NO PPT CARDS):
        • Reason from first principles about how the concept actually behaves in the real world:
          - Finance & Economics: Dynamic supply/demand curves shifting equilibrium, balance scales of risk vs yield, cash reservoirs with liquidity valves, compound growth splines.
          - Business & Management: Multi-stage conversion funnels, circular sprint cycles with WIP queue gauges, value-chain process flows, decision tree branches.
          - Healthcare & Science: Molecular lock-and-key receptor binding, expanding/narrowing vessel conduits with fluid particles, exponential decay curves.
          - Systems & Technology: Fluid conduits with traveling packet dots, orbital node constellations, state-transition toggle gates.
        • Visual Design System & Kinetic Visual Choreography (Group 3 Quality Standard):
          - Dynamic Vector-Image Pairing: Whenever visual assets (transparent PNG illustrations) are generated for a scene, integrate them directly as primary hero anchors in open space. Strictly DO NOT mount them inside generic PowerPoint-style rounded container cards or slide boxes! Pair them with dynamic procedural Manim vector mechanisms (curved telemetry dials with kinetic rotating needles, glowing neural LLM cores, sprouting decision tree branches, condition-action switches, packet conduits) that visually demonstrate the concept in motion.
          - AUTHENTIC PHYSICAL/CONCEPTUAL METAPHORS (PRESERVE STORYBOARD CHOREOGRAPHY):
            * The storyboard and instructional design specify physical, mechanical, and domain-specific mechanisms (e.g., dials with moving needles dropping below threshold lines, sprouting decision trees, reflex switches, mechanical tool dispatch conduits, responsible human handoffs).
            * You MUST explicitly preserve, specify, and expand these authentic mechanisms in your composition.
            * STRICT PROHIBITION: NEVER flatten these rich conceptual mechanisms into a cluster of generic rounded-rectangle text cards or spreadsheet-style table containers!
          - Modular Kinetic Toolkit (Contextually Selected by Domain):
            * Choose or construct vector animations that genuinely reflect the semantic meaning of what is being explained:
              - Data Pipelines, Ingestion & Conduits: Moving glowing packet streams (e.g. FlowingStream or traveling packet pulses).
              - Continuous Monitoring, Signals & Telemetry: Undulating wave pulses or telemetry readouts (e.g. TelemetryWaves).
              - Alerts, Anomaly Detection & State Transitions: Radiating shockwave ripples or beacon pulses (e.g. PulsingShockwaves).
              - Optimization, Search & Scanning: Dynamic radar sweeps or field-line sweeps (e.g. DynamicRadarSweep).
              - Multi-Objective Optimization, Pareto Frontiers & Trade-offs: Mechanical rigging balance scales (e.g. BalanceScale).
              - Processing Cores, Neural Layers & Reasoning Hubs: Pulsing neural halo rings or rotating embedding constellations (e.g. NeuralHaloPulses).
              - Other Domains (Economics, Medicine, Management, Systems): Construct first-principles physical, mathematical, or mechanical animations matching the subject.
          - Cognitive Text Discipline (No Empty Visuals, No Bullet Dumps):
            * Every visual mechanism, node, or processing stage MUST carry a prominent, high-contrast, bold 1–3 word title badge (e.g. 'Data Ingest', 'Reasoning Core', 'Safety Gate', 'Optimal Policy').
            * Strictly avoid paragraph dumps, multi-line bullet walls, or long numbered lists!
            * Strictly avoid creating slide-like text boxes or cards around every label! Text should label the vector components directly.
            * Keep labels persistent on screen while the teacher explains the concept; avoid flashing or rushing.
        
        • Strict Anti-Collision Safe Zones with SME Presenter:
          - Layout 70% (Left Rounded Frame): Presenter occupies x = 80..720px (Manim x in [-7.11, -1.48]).
            ALL CGI content, arrows, and ingress streams MUST be strictly bounded within x in [-1.1, 6.2] (pixels x >= 760px)!
          - Layout 20% (Top-Right PIP): Presenter PIP occupies (x=1496, y=40, w=384, h=216) (Manim x >= +3.5 and y >= +1.8).
            ALL scene titles, badges, and top-right graphics MUST strictly terminate at x <= +3.5 whenever y >= +1.8!

        ---

        LAYOUT & SPACE UTILIZATION

        Design the workspace for maximum useful information density without crowding.

        Use the available frame deliberately.

        Always

        • center the scene title at the top
        • reserve safe margins around the frame
        • reserve approximately 1.5 units of clear space at the bottom
        • keep important content away from frame edges
        • prevent overlap
        • maintain readable spacing
        • minimize unnecessary whitespace
        • maintain symmetry and visual balance
        • align related components to common edges or axes

        For every major component explicitly state its directional extent, for example

        • spans most of the available width
        • occupies the left third
        • occupies the right half
        • centered across the main workspace
        • arranged horizontally across the middle
        • stacked vertically through the central region
        • anchored to the upper-right region
        • fills the available central workspace

        Do not use exact numerical coordinates.

        However, do not use vague descriptions such as "nearby", "around", "beside" or "appropriately positioned".

        State both WHERE an element sits and HOW FAR it should spread.

        ---

        LAYOUT RELATIONSHIPS

        Position components relative to one another, not independently.

        For each major component specify

        • anchor component
        • direction from anchor
        • alignment
        • separation
        • relative scale
        • shared boundaries or grouping
        • expected occupied region

        Prefer layouts with clear symmetry, common alignment edges and consistent spacing.

        ---

        ZERO PLACEHOLDERS MANDATE (CRITICAL)

        Do NOT generate placeholder containers, outlined placeholder boxes, dummy text, avatar placeholders, or temporary frames.
        Every visual element must be concrete, named, and fully realized with its authentic instructional title and content (e.g., "Memory Layer Substrate", "Evaluation Matrix Visual Model", never "placeholder container" or "placeholder box"). All elements displayed must represent real architectural components.

        Repeated or comparable components should have matching footprints, alignment and visual weight unless their instructional importance requires otherwise.

        If one component is primary, allow it to occupy substantially more space.

        If content is naturally sequential, prefer the direction that best communicates the sequence.

        Avoid large empty regions between related components.

        Avoid arbitrary offsets that break alignment with neighboring elements.

        ---

        PROPORTION & SYMMETRY

        Maintain deliberate geometric consistency across related components.

        • Comparable items should have comparable visual footprints.
        • Repeated visual components should use consistent scale, stroke width, and spacing.
        • Symmetric structures must have matching visual weight on opposing sides.
        • Maintain consistent gaps between repeated elements.
        • Do not stretch, compress or disproportionately scale individual items merely to fill space.
        • Preserve the intended aspect ratio of diagrams, icons and visual assets.
        • When one side of a composition mirrors another, match alignment, spacing and scale.
        • Resolve available space through redistribution before changing component proportions.

        ---

        RADIAL & CIRCULAR COMPOSITIONS

        When components are arranged radially, treat the center as the geometric anchor.

        • Distribute items symmetrically around the central anchor.
        • Maintain consistent angular spacing unless the instructional structure requires otherwise.
        • Every connector must originate and terminate at the correct component.
        • Arrows must follow the actual directional relationship between connected elements.
        • Arrowheads must point toward the intended destination.
        • Connectors must not cross unrelated elements or point toward neighboring components.
        • Maintain consistent radial distance from the center.
        • Preserve symmetry in both placement and connector geometry.
        • For circular flows, maintain a consistent clockwise or counterclockwise direction.        

        ---

        SCREEN ECONOMY

        Before finalizing a composition, mentally pack the instructional elements into the available workspace.

        Do NOT solve whitespace by shrinking all content excessively.

        Instead

        • expand major diagrams when space permits
        • distribute related elements across available width
        • use vertical stacking when horizontal space is constrained
        • use horizontal grouping when vertical space is constrained
        • consolidate closely related supporting information
        • keep primary content visually dominant
        • avoid unused corners and large blank regions unless they provide meaningful separation

        The composition should feel intentionally filled, not sparsely placed.

        ---

        VISUAL HIERARCHY

        Organize information into

        • primary focus
        • secondary content
        • supporting information
        • persistent references
        • temporary components

        Related information should be grouped.

        Independent concepts should remain separated.

        Supporting information should occupy less visual territory than the primary instructional content.

        Do not give equal visual weight to every text element.

        The most instructionally important information should receive the clearest position and greatest visual prominence.


        ---

        TEXT ORGANIZATION

        Explicitly specify every visible text element.

        Include

        • headings
        • subheadings
        • labels
        • captions
        • examples
        • equations
        • list contents
        • table contents
        • explanatory notes

        Do not summarize visible content.

        Specify exactly what the learner reads and where it belongs relative to the relevant visual.

        Please retain all LaTeX formatting of mathematical symbols, equations, expressions and other artefacts.
        Make sure any mathematical symbols, expressions and equations are formatted in LaTeX even if not explicitly specified in the input Presentation Steps

        TEXT ECONOMY

        On-screen text should complement narration, not duplicate it.

        For every text element ask whether it adds meaningful instructional value beyond what is already spoken.

        • Remove low-value or redundant text.
        • Shorten verbose statements to their essential meaning.
        • Prefer concise phrases over full explanatory sentences when narration provides the explanation.
        • Preserve definitions, labels, values, distinctions and other information that the learner needs to see.
        • Do not display narration verbatim unless the exact wording is instructionally necessary.
        • When multiple text elements communicate the same idea, consolidate them into the sharpest useful formulation.
        • All numbers and currency amounts should be shown with numerical digits and symbols; not written as words

        TEXT LISTS

        Any collection of related text items must be represented as an intentional list structure.

        Do NOT simply place multiple text statements one below another without structural indication.

        When content is a list, specify

        • a bullet or equivalent visual indicator for each item
        • the text associated with each bullet
        • a shared alignment edge
        • consistent vertical spacing
        • a common starting position
        • the overall occupied region

        Bullets should align consistently with their corresponding text.

        Related list items should share a common LEFT edge and form a clean vertical rhythm.

        Use numbered lists when sequence or ordering matters; use bullets for unordered items.

        Do not use bullets when the content is better represented as a diagram, process, comparison or other structural visual.

        TEXT ALIGNMENT

        Treat each logical text group as an alignment system, not a collection of independent objects.

        • Establish one primary alignment axis for each group.
        • Related text must share a common left edge, right edge or center axis.
        • Bullets, labels and their corresponding text must align consistently.
        • Headings must align with the content they introduce.
        • Labels and text tags must align cleanly relative to their associated visual component.
        • Repeated structures must use identical alignment, indentation and spacing.
        • Do not mix alignment modes within one logical group unless structurally required.
        • Maintain consistent vertical rhythm between sibling elements.
        • Never use arbitrary offsets to make individual elements "fit".

        ---

        VISUAL ASSETS

        Preserve every asset_<n> and image_<n> exactly.

        Specify

        • placement
        • occupied region
        • surrounding content
        • alignment
        • relationship to its parent component

        Never invent or rename identifiers.

        ---

        PERSISTENCE

        Specify exactly which components persist into subsequent presentation steps.

        If a component is minimized, specify

        • what remains
        • what is removed
        • what becomes the reference
        • where that reference is positioned
        • how much workspace it occupies

        ---

        CONSTRAINTS

        Do NOT

        • change instructional meaning
        • change sequencing
        • change narration alignment
        • invent concepts
        • modify labels
        • rewrite diagrams
        • invent assets
        • invent images
        • specify colors
        • specify typography styling
        • specify animation
        • NEVER interpret titles or concepts metaphorically (e.g., do NOT invent literal jigsaw puzzle pieces, toys, or games for figurative titles like "The Retail Capital Puzzle").
        • Strictly preserve every mathematical formula, equation, variable, and numerical parameter verbatim in LaTeX format exactly as specified in the Presentation Components (e.g., do NOT substitute Basel WCDR formulas with custom weighted averages or maturity adjustments).
        • All diagrams, tables, charts, axes, metrics, and coordinate systems specified in Presentation Components must be preserved with their exact specified axes, metrics, and labels.

        Preserve every asset_<n> and image_<n> exactly.

        The output should be a deterministic presentation composition that completely specifies the instructional workspace, including component decomposition, spatial relationships, screen footprint, directional spread and whitespace utilization, while leaving styling and animation to downstream stages.
        """

USER_PROMPT_SIMPLILEARN_COMPOSER = """
For enhancing the presentation composition, adhere strictly to the following Simplilearn OSL 3.0 Workspace Rules:
------------------------
SIMPLILEARN OSL 3.0 CLEARANCE & WORKSPACE MANDATE:
1. Dynamic SME Safe Zone Enforcement:
   - For Layout 100: Presenter occupies full 1920x1080 canvas. Minimal lower-third title card only. Duration MUST be <= 20.0s.
   - For Layout 70: Left frame (w=640, h=920, r=10px, blue accent band #2C81FE width=180px) houses the SME video. All presentation components, cards, tables, and diagrams MUST be anchored to the right-side workspace at x >= 760px (width 1080px).
   - For Layout 20: Presenter is scaled to 20% FHD (384x216, r=8px) in the top-right corner at (x=1496, y=40). Content collision constraint: title and lead-in text must terminate <= 1440px. All schematic diagrams and structural cards must stay below y >= 270px across the wide 1814px canvas.
2. Kinetic Vector Architecture & Authentic Choreography (Strict Prohibition of PPT Cards):
   - Strictly DO NOT diagram system components as isolated white cards, rounded-rectangle panels, or text boxes connected by plain lines!
   - Strictly DO NOT describe the scene as a collection of rounded-rectangle cards, panels, or spreadsheet grid tables!
   - System components MUST be represented by their physical conceptual domain mechanisms (e.g. animated dials with kinetic needles dropping below thresholds, glowing neural LLM brain nodes, sprouting decision tree branches, condition-action reflex switches, kinetic actuator conduits, continuous loops, balance scales).
   - Integrate transparent illustration assets directly as primary hero anchors in open canvas space without boxing them inside container cards.
   - Minimal on-screen text: Punchy bold labels (1-3 words max), no wall-of-text bullet lists.
   - Infuse the approved Simplilearn 10-pastel color palette (#62B7E4, #7EA2C8, #9B99C7, #8ECDB7, #E6A157, #DDB945, #E58F6D, #B88968, #D98CA1, #C1A5C6).
3. Text & LaTeX Integrity:
   - Preserve all LaTeX mathematical expressions, equations, and symbols verbatim.
   - Use Chicago title casing (5-7 words). Never write titles in all-caps.
4. PRESERVE & AMPLIFY STAGE 1 KINETIC CHOREOGRAPHY:
   - When the storyboard describes active physical mechanisms (such as dials with moving needles dropping below threshold lines, sprouting decision tree branches, flowing particle packets along curved conduits, rotating radar wedges, neural dies, or bi-directional loops), you MUST retain and explicitly describe these exact kinetic actions in your Instruction block!
   - Strictly NEVER replace physical mechanisms with "cards" or "pills". Describe the kinetic vector mechanisms, their positions, their motion, and how they evolve across beats!
------------------------
Scene Storyboard Guidelines:
{storyboard_context}
"""


def parse_composer_output(input_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parses LLM composer output text into structured scene instructions.
    Matches Simplilearn presentation composer parsing logic.
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


class PresentationComposer:
    """
    Assembles fully specified presentation compositions for every scene step,
    guaranteeing 1:1 step parity and strict Simplilearn OSL 3.0 safe zone clearance.
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
        model_name: str = "gemini-3.8-flash",
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

    def call_llm(
        self,
        user_prompt: str,
        system_prompt: str,
        model_override: Optional[str] = None,
        vendor_override: Optional[str] = None
    ) -> str:
        """Dispatches LLM generation to Claude or Gemini based on config and available keys."""
        target_model = model_override or self.model_name
        vendor = (vendor_override or self.api_provider).lower()

        # 1. Claude if requested or model contains claude
        if (vendor == "claude" or "claude" in target_model.lower()) and self.claude_api_key:
            try:
                from anthropic import Anthropic
                client = Anthropic(api_key=self.claude_api_key, timeout=800)
                m_name = target_model if "claude" in target_model.lower() else "claude-haiku-4-5-20251001"
                print(f"    -> [PresentationComposer] Invoking Claude model: {m_name}")
                message = client.messages.create(
                    max_tokens=8000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    model=m_name
                )
                if message and message.content:
                    return message.content[0].text
            except Exception as e:
                print(f"  [PresentationComposer] Claude call notice: {e}. Falling back to Gemini...")

        # 2. Gemini via google.genai
        gemini_key = self.google_api_key or self.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if gemini_key:
            g_model = target_model if ("gemini" in target_model.lower() or "flash" in target_model.lower()) else "gemini-3.8-flash"
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                print(f"    -> [PresentationComposer] Invoking Gemini (google.genai): {g_model}")
                resp = client.models.generate_content(
                    model=g_model,
                    contents=f"{system_prompt}\n\nUser Query: {user_prompt}"
                )
                if resp and resp.text:
                    return resp.text
            except Exception as e:
                print(f"  [PresentationComposer] google.genai notice: {e}. Trying google.generativeai...")
                try:
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=gemini_key, transport="rest")
                    print(f"    -> [PresentationComposer] Invoking Gemini (google.generativeai): {g_model}")
                    m = genai_legacy.GenerativeModel(g_model)
                    resp = m.generate_content(f"{system_prompt}\n\nUser Query: {user_prompt}")
                    if resp and resp.text:
                        return resp.text
                except Exception as ex:
                    print(f"  [PresentationComposer] google.generativeai failed: {ex}")

        return ""

    def compose_scene_local(self, scene: Dict[str, Any], sid: int) -> List[Dict[str, Any]]:
        """Deterministic local composition specification preserving step parity."""
        title = scene.get("title", f"Scene {sid}")
        layout = str(scene.get("sme_layout", "70"))
        narration = scene.get("voiceover_narration", "")

        if layout == "70":
            comp = (
                f"Scene {sid} Presentation Composition. Left 640x920 rounded rectangle (r=10px) with #2C81FE blue band (width 180px) "
                f"holds the presenter. Centered scene title '{title}' anchored at top-left (x=760, y=80). "
                f"Right-side content workspace spans x in [760, 1840]px. Open broadcast canvas hosts dynamic vector diagrams and kinetic visual mechanisms with pastel accents (#62B7E4, #7EA2C8)."
            )
        elif layout == "20":
            comp = (
                f"Scene {sid} Presentation Composition. Presenter scaled to 20% PIP window (384x216, r=8px) at top-right (1496, 40). "
                f"Scene title '{title}' and lead-in line terminate at x=1440px to ensure zero collision. "
                f"Wide central workspace below y=270px (width 1760px, height 700px) hosts multi-layered architectural flowchart "
                f"with horizontal state nodes and directional connectors (#2C81FE)."
            )
        else:
            comp = (
                f"Scene {sid} Presentation Composition. Presenter occupies full 1920x1080 canvas (strictly <= 20.0s). "
                f"Minimal high-contrast lower-third title card '{title}' positioned at bottom center (y=920, h=80, r=10px, fill #0F172A opacity 0.85)."
            )

        return [{"matching_section": comp}]

    def compose_all_scenes(
        self,
        blueprint: Dict[str, Any],
        classified_catalog: Optional[Dict[str, Any]] = None,
        constructed_catalog: Optional[Dict[str, Any]] = None,
        base_folder: Optional[str] = None,
        target_scene: Optional[str] = None,
        jazzy_model_name: Optional[str] = None,
        jazzy_vendor: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
        """
        Processes scenes from storyboard blueprint and instructions_<model>.json,
        calling Claude Haiku / Gemini to expand each step into a complete 2D spatial layout,
        updating enhanced_anim_<model>.json and raw_enhanced_anim_<model>.txt.
        """
        scenes = blueprint.get("scenes", [])
        topic = blueprint.get("concept") or blueprint.get("lesson_title") or "Technical Architecture"
        composed_output: Dict[str, Any] = {
            "topic": topic,
            "total_scenes": len(scenes),
            "scenes": []
        }

        model_to_use = jazzy_model_name or self.model_name
        vendor_to_use = jazzy_vendor or self.api_provider

        # Resolve raw file and enhanced anim file in base_folder if provided
        enhanced_anim_raw_file = None
        enhanced_anim_output_file = None
        existing_enhanced = {}
        if base_folder:
            enhanced_anim_output_file = os.path.join(base_folder, f"enhanced_anim_{model_to_use}.json")
            enhanced_anim_raw_file = os.path.join(base_folder, f"raw_enhanced_anim_{model_to_use}.txt")
            if os.path.exists(enhanced_anim_output_file):
                try:
                    with open(enhanced_anim_output_file, "r", encoding="utf-8") as f:
                        existing_enhanced = json.load(f)
                except Exception:
                    existing_enhanced = {}

        # Resolve construction guidelines
        construction_guidelines = {}
        if constructed_catalog:
            if isinstance(constructed_catalog, dict) and "constructed_catalog" in constructed_catalog:
                for k, v in constructed_catalog["constructed_catalog"].items():
                    construction_guidelines[k] = v.get("construction_paragraph", "")
            elif isinstance(constructed_catalog, dict):
                construction_guidelines.update(constructed_catalog)

        # Resolve asset classification dictionary {scene_id: [steps]}
        structured_asset_classification = {}
        if classified_catalog:
            if isinstance(classified_catalog, dict) and "scenes" in classified_catalog:
                for sc in classified_catalog.get("scenes", []):
                    structured_asset_classification[str(sc.get("scene_id"))] = sc.get("steps", [])
            elif isinstance(classified_catalog, dict):
                structured_asset_classification.update(classified_catalog)

        # Resolve storyboard instructions (step-by-step)
        storyboard_instructions = {}
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
                        storyboard_instructions = json.load(f)
                except Exception:
                    storyboard_instructions = {}

        # If storyboard_instructions not loaded from file, extract from blueprint
        if not storyboard_instructions and scenes:
            for s_idx, scene in enumerate(scenes, 1):
                sid = str(scene.get("scene_id") or scene.get("scene_index") or s_idx)
                steps = scene.get("presentation_steps") or scene.get("steps", [])
                if steps:
                    storyboard_instructions[sid] = steps
                else:
                    storyboard_instructions[sid] = [{
                        "presentation_step_number": "1",
                        "title": scene.get("title", f"Scene {sid}"),
                        "narration_statement": scene.get("voiceover_narration") or scene.get("narration", ""),
                        "matching_section": scene.get("primary_content") or scene.get("visual_description", "")
                    }]

        enhanced_instructions = dict(existing_enhanced)

        print(f"[*] Composing presentation layouts via {vendor_to_use} ({model_to_use}) across {len(storyboard_instructions)} scenes...")

        for sid, pairs in storyboard_instructions.items():
            if target_scene and str(sid) != str(target_scene):
                continue

            scene_title = f"Scene {sid}"
            for sc in scenes:
                if str(sc.get("scene_id")) == str(sid):
                    scene_title = sc.get("title", scene_title)
                    break

            storyboard_context = f"Scene {sid}:\n"
            for i, pair in enumerate(pairs):
                storyboard_context += "#####################################################\n"
                storyboard_context += f"Presentation Step {i+1}:\n\n"
                storyboard_context += f"Title: {pair.get('title', '')}\n"
                storyboard_context += f"{pair.get('matching_section', '')}\n\n"

                suggestions_group = {}
                if sid in structured_asset_classification and i < len(structured_asset_classification[sid]):
                    suggestions_group = structured_asset_classification[sid][i]

                if suggestions_group.get("Asset_Suggestion") and suggestions_group.get("Asset_names"):
                    storyboard_context += "Presentation Step Asset Constructions:\n\n"
                    for k, asset_name in enumerate(suggestions_group["Asset_names"]):
                        guideline = construction_guidelines.get(asset_name, "")
                        if guideline:
                            storyboard_context += f"{asset_name}: {guideline}\n\n"

                if suggestions_group.get("Image_Suggestion") and suggestions_group.get("Image_names"):
                    storyboard_context += "Presentation Step Images:\n\n"
                    for k, img_name in enumerate(suggestions_group["Image_names"]):
                        if k < len(suggestions_group["Image_Suggestion"]):
                            storyboard_context += f"{img_name}: {suggestions_group['Image_Suggestion'][k]}\n\n"

            formatted_user_prompt = USER_PROMPT_SIMPLILEARN_COMPOSER.replace("{storyboard_context}", storyboard_context)
            formatted_user_prompt += f"\n\nCRITICAL REQUIREMENT: This scene contains EXACTLY {len(pairs)} Presentation Steps. You MUST output EXACTLY {len(pairs)} 'Instruction:' blocks for this scene (one per Presentation Step). Do NOT generate fewer or more than {len(pairs)} instructions."

            print(f"  -> Generating spatial composition for Scene {sid} ({len(pairs)} steps)...")
            generated_result = self.call_llm(
                user_prompt=formatted_user_prompt,
                system_prompt=SYSTEM_PROMPT_PRESENTATION_COMPOSER,
                model_override=model_to_use,
                vendor_override=vendor_to_use
            )

            if generated_result and len(generated_result.strip()) > 50:
                if enhanced_anim_raw_file:
                    with open(enhanced_anim_raw_file, "a", encoding="utf-8") as f:
                        f.write(f"Scene {sid}:\n\n{generated_result.strip()}\n\n")

                story_element = parse_composer_output(generated_result)
                scene_steps = story_element.get(sid, [])
            else:
                print(f"  [PresentationComposer] Scene {sid} LLM returned empty, using fallback.")
                matching_scene = next((sc for sc in scenes if str(sc.get("scene_id")) == str(sid)), {"title": scene_title})
                scene_steps = self.compose_scene_local(matching_scene, int(sid) if sid.isdigit() else 1)

            # Reconcile step counts
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
            matching_scene = next((sc for sc in scenes if str(sc.get("scene_id")) == str(sid)), {"title": scene_title})
            for i, step in enumerate(scene_steps):
                narr = ""
                if i < len(pairs):
                    narr = pairs[i].get("narration_statement") or pairs[i].get("narration") or pairs[i].get("voiceover_narration", "")
                if not narr and matching_scene:
                    narr = matching_scene.get("voiceover_narration") or matching_scene.get("narration", "")
                step["narration_statement"] = narr

                suggestions_group = structured_asset_classification.get(sid, [])
                if i < len(suggestions_group) and isinstance(suggestions_group[i], dict):
                    step["assets"] = suggestions_group[i].get("Asset_names")
                else:
                    step["assets"] = None

            enhanced_instructions[sid] = scene_steps

            # Dynamically resolve layout from matching scene or blueprint
            s_layout = str(matching_scene.get("sme_layout", "70"))
            scene_vo = (
                pairs[0].get("narration_statement") or pairs[0].get("narration") or matching_scene.get("voiceover_narration", "")
                if pairs else matching_scene.get("voiceover_narration", "")
            )

            composed_output["scenes"].append({
                "scene_id": int(sid) if sid.isdigit() else sid,
                "title": scene_title,
                "sme_layout": s_layout,
                "voiceover_narration": scene_vo,
                "instructions": scene_steps
            })

        print(f"✓ Presentation Composer Complete: Formulated {len(enhanced_instructions)} scene spatial compositions")
        return composed_output, enhanced_instructions

    def run(
        self,
        blueprint_path: str,
        output_path: str,
        assets_path: Optional[str] = None,
        constructed_path: Optional[str] = None,
        base_folder: Optional[str] = None,
        target_scene: Optional[str] = None,
        jazzy_model_name: Optional[str] = None,
        jazzy_vendor: Optional[str] = None
    ) -> str:
        folder = base_folder or str(Path(blueprint_path).parent)
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
        if not jazzy_model_name:
            jazzy_model_name = ex_conf.get("jazzy_model_name", self.model_name)
        if not jazzy_vendor:
            jazzy_vendor = ex_conf.get("jazzy_vendor", "claude" if "claude" in str(jazzy_model_name).lower() else "google")

        with open(blueprint_path, "r", encoding="utf-8") as f:
            blueprint = json.load(f)

        classified = None
        if assets_path and Path(assets_path).exists():
            with open(assets_path, "r", encoding="utf-8") as f:
                classified = json.load(f)
        elif folder:
            cand = list(Path(folder).glob("*classified_assets*.json")) or list(Path(folder).glob("asset_classification_*.json"))
            if cand:
                with open(cand[0], "r", encoding="utf-8") as f:
                    classified = json.load(f)

        constructed = None
        if constructed_path and Path(constructed_path).exists():
            with open(constructed_path, "r", encoding="utf-8") as f:
                constructed = json.load(f)
        elif folder:
            cand = list(Path(folder).glob("*constructed_assets*.json")) or list(Path(folder).glob("construction_output_*.json"))
            if cand:
                with open(cand[0], "r", encoding="utf-8") as f:
                    constructed = json.load(f)

        comp, enhanced_dict = self.compose_all_scenes(
            blueprint,
            classified_catalog=classified,
            constructed_catalog=constructed,
            base_folder=folder,
            target_scene=target_scene,
            jazzy_model_name=jazzy_model_name,
            jazzy_vendor=jazzy_vendor
        )

        # 1. Write presentation composition JSON
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(comp, f, indent=2, ensure_ascii=False)

        # 2. Write authoritative enhanced_anim_<model>.json directly into metadata_blueprints
        meta_dir = Path(folder) / "metadata_blueprints"
        meta_dir.mkdir(parents=True, exist_ok=True)
        m_name = jazzy_model_name or self.model_name
        enhanced_file = meta_dir / f"enhanced_anim_{m_name}.json"
        with open(enhanced_file, "w", encoding="utf-8") as f:
            json.dump(enhanced_dict, f, indent=4, ensure_ascii=False)
        print(f"  Authoritative spatial layout saved -> {enhanced_file}")

        # Also write raw_parameters copy into meta_dir
        raw_param_file = meta_dir / f"raw_parameters_{m_name}.json"
        try:
            shutil.copy2(out, raw_param_file)
        except Exception:
            pass

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
                print(f"Skipping {topic_id}: Already processed in presentation composer tracker.")
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

            jazzy_model = ex_conf.get("jazzy_model_name", self.model_name)
            jazzy_vend = ex_conf.get("jazzy_vendor", "claude" if "claude" in jazzy_model.lower() else "google")

            print(f"Processing Presentation Composer for {topic_id}...")
            meta_dir = os.path.join(topic_dir, "metadata_blueprints")
            os.makedirs(meta_dir, exist_ok=True)
            blueprint_file = os.path.join(meta_dir, f"{topic_id}_storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(topic_dir, f"{topic_id}_storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(meta_dir, "storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(topic_dir, "storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                print(f"Skipping {topic_id}: Missing storyboard blueprint.")
                continue

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

            out_composition = os.path.join(meta_dir, f"{topic_id}_presentation_composition.json")
            try:
                self.run(
                    blueprint_path=blueprint_file,
                    output_path=out_composition,
                    assets_path=assets_file if os.path.exists(assets_file) else None,
                    constructed_path=constructed_file if os.path.exists(constructed_file) else None,
                    base_folder=topic_dir,
                    target_scene=target_scene,
                    jazzy_model_name=jazzy_model,
                    jazzy_vendor=jazzy_vend
                )

                if self.output_tracker_path:
                    self._save_tracker(self.output_tracker_path, {
                        topic_id: {
                            "output_path": out_composition,
                            "processed": True,
                            "topic_name": topic_id,
                            "topic_id": topic_id,
                            "failure_reason": None
                        }
                    })
                print(f"Successfully composed presentation for {topic_id}.")
            except Exception as e:
                print(f"Error composing presentation for {topic_id}: {e}")
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
    parser = argparse.ArgumentParser(description="Presentation Composer (Simplilearn OSL 3.0 Architecture)")
    parser.add_argument("-b", "--blueprint", required=True, help="Input storyboard blueprint JSON")
    parser.add_argument("-o", "--output", required=True, help="Output presentation composition JSON")
    parser.add_argument("-a", "--assets", default=None, help="Optional classified assets JSON")
    parser.add_argument("-c", "--constructed", default=None, help="Optional constructed assets JSON")
    parser.add_argument("-t", "--target-scene", default=None, help="Optional target scene ID to process")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM API provider")
    parser.add_argument("-m", "--model", default="gemini-3.8-flash", help="Model name")
    args = parser.parse_args()

    composer = PresentationComposer(
        api_provider=args.provider,
        model_name=args.model
    )
    composer.run(
        args.blueprint,
        args.output,
        assets_path=args.assets,
        constructed_path=args.constructed,
        target_scene=args.target_scene
    )
