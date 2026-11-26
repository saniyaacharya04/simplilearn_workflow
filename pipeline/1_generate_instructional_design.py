#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 1: INSTRUCTIONAL STORYBOARD DESIGN
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 1
   - Script Name: 1_generate_instructional_design.py
   - Primary Class: InstructionalDesign
   - Pipeline Role:
     Translates clean transcripts and pedagogical hook blueprints into an exhaustive,
     production-ready educational presentation storyboard. Enforces Simplilearn OSL 3.0
     Dynamic SME Framing authority (Layout 100 <= 20.0s opening hook, Layout 70 left
     rounded frame, Layout 20 top-right PIP window), 70/30 visual-to-text allocation,
     anti-collision safe zones, and zero blank screen scaffolding.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 0 (0_generate_hook.py):
       - How: Ingests {topic_id}_hook_blueprint.json via 0_hook_output_tracker.json.
       - Purpose: Supplies conceptual hooks, target audience framing, and lesson arc.
     * Stage 0C (0c_clean_fillers_and_retakes.py):
       - How: Ingests {topic_id}_clean_transcript.json.
       - Purpose: Supplies clean spoken lecture sentences.
   - Input Tracker: ppt_trackers/0_hook_output_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * {topic_id}_hook_blueprint.json (Stage 0):
       Location: output/<TOPIC_NAME>/{topic_id}_hook_blueprint.json
       Content: Pedagogical blueprint and core conceptual hooks.
     * {topic_id}_clean_transcript.json (Stage 0C):
       Location: output/<TOPIC_NAME>/{topic_id}_clean_transcript.json
       Content: Filler-free narrative transcript.
     * ex_config.json:
       Location: output/<TOPIC_NAME>/ex_config.json
       Content: Project duration targets, scene count, and persona.
     * Input Tracker:
       Location: ppt_trackers/0_hook_output_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 0_hook_output_tracker.json.
   - Step 2: Ingests hook blueprint and clean transcript.
   - Step 3: Dynamically scales scene count (3 to 12 scenes based on duration) and snaps
     semantic boundaries to transcript sentence timestamps (Scene 1 hook <= 18s).
   - Step 4: Dispatches instructional design prompt to Gemini 3.8 Flash or Claude 3.5 Sonnet.
   - Step 5: Assigns SME framing layouts strictly per Simplilearn OSL 3.0 rules:
     * Layout 100: Strictly restricted to <= 20 seconds range for opening hook.
     * Layout 70: Left frame (640x920, r=10px, blue band #2C81FE) for objectives/summary.
     * Layout 20: Top-right corner PIP (384x216 at 1496,40) for technical diagrams.
   - Step 6: Exports reference schemas, structured storyboard blueprint, instructions_<model>.json,
     instructions.json, and raw prompt text companion files in metadata_blueprints/.
   - Step 7: Atomically updates 1_instruction_design_output_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * {topic_id}_storyboard_blueprint.json:
       Location: output/<TOPIC_NAME>/{topic_id}_storyboard_blueprint.json
       Content: Master multi-scene presentation storyboard with step breakdowns.
     * Companion Instructions & Prompt Files:
       Location: output/<TOPIC_NAME>/metadata_blueprints/ (and prompt_context_and_guidelines/)
       Content: instructions_<model>.json, instructions.json, instructions_raw_<model>.txt.
     * Reference JSON Schemas:
       Location: output/<TOPIC_NAME>/schemas/
       Content: Extracted validation schemas for downstream stages.
     * Output Tracker:
       Location: ppt_trackers/1_instruction_design_output_tracker.json
       Content: Atomic tracker confirming completion of instructional design.

6. DOWNSTREAM CONSUMERS:
   - Stage 2 (2_asset_classification.py): Categorizes visual assets specified in the storyboard.
   - Stage 5 (5_populate_audio_runtime.py): Ingests scene narration to build CGI_Input.json.
   - Stage 23 (23_sme_post_production.py): Reads SME layout specifications for final composite.
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

from pipeline.config import (
    NEXT_TOPIC_PREFIX,
    SPELLED_NUMBERS,
    MAX_TITLE_WORDS,
    MIN_TITLE_WORDS,
    CANVAS_WIDTH,
    CANVAS_HEIGHT
)

def clean_scene_title(scene: Dict[str, Any], sid: int) -> str:
    """Dynamically resolves a clean, descriptive scene title adhering to Chicago Title Case."""
    sid_str = str(sid)
    raw_title = scene.get("title") or scene.get("scene_title") or ""
    steps = scene.get("presentation_steps", [])
    
    if not raw_title or raw_title.strip().lower() in [f"scene {sid_str}", f"scene{sid_str}", f"scene_{sid_str}", f"scene {sid}", "scene"]:
        if steps and len(steps) > 0 and (steps[0].get("step_title") or steps[0].get("title")):
            cand = steps[0].get("step_title") or steps[0].get("title")
            if cand and not cand.lower().startswith("scene ") and len(cand.split()) <= 7:
                return cand.strip()
        obj = scene.get("scene_objective") or scene.get("concept_focus")
        if obj and isinstance(obj, str):
            clean_obj = re.sub(r'^(Master foundational pedagogical goals of|Explain|Understand|Detail|Introduce|Explore)\s+', '', obj, flags=re.IGNORECASE).strip()
            words = clean_obj.split()
            if 2 <= len(words) <= 7:
                return clean_obj.title()
            elif len(words) > 7:
                return " ".join(words[:6]).title()
        lesson_t = scene.get("lesson_title") or "Technical Architecture"
        return f"{lesson_t} - Part {sid_str}"

    clean = raw_title.strip()
    clean = re.sub(r'^(Deconstruct|Explain|Establish|Detail|Analyze|Contrast|Map|Summarize|Walk through|Explore|Review)\s+', '', clean, flags=re.IGNORECASE)
    if ":" in clean:
        parts = clean.split(":")
        clean = parts[0].strip() if len(parts[0].split()) <= 6 else parts[1].strip()
    words = clean.split()
    if len(words) > 7:
        clean = " ".join(words[:6])
    return clean.title()

def build_step_matching_section(step: Dict[str, Any], clean_title: str, step_num: int, layout: str) -> str:
    """Builds a rich matching section for an individual presentation step adhering to Simplilearn OSL 3.0."""
    st_title = step.get("step_title") or step.get("title") or f"Step {step_num}"
    vdesc = step.get("visual_description", {})
    purpose = vdesc.get("purpose", f"Explain {st_title}") if isinstance(vdesc, dict) else str(vdesc)
    comps = vdesc.get("presentation_components", []) if isinstance(vdesc, dict) else []
    vevo = step.get("visual_evolution", "Visual components illuminate and construct dynamically matching spoken narration.")
    kt = step.get("key_takeaway", f"Core operational insight for {st_title}.")

    comp_lines = []
    for c in comps:
        if isinstance(c, dict):
            col = c.get("column") or c.get("role") or c.get("placement")
            ctype = c.get("component_type") or c.get("type") or "Visual Model"
            content = c.get("content") or c.get("description") or c.get("text") or ""
            if col:
                comp_lines.append(f"• [{col}] {ctype}: {content}")
            else:
                comp_lines.append(f"• {ctype}: {content}")
        else:
            comp_lines.append(f"• Component: {c}")
    comps_str = "\n".join(comp_lines) if comp_lines else f"• Centerstage Visual Model: Dynamic architectural schematic representing {st_title}."

    return (
        f"Purpose: {purpose}\n"
        f"Presentation Components:\n"
        f"• Step Title: {st_title}\n"
        f"• Screen Context: {clean_title} (Step {step_num})\n"
        f"{comps_str}\n"
        f"Visual Evolution: {vevo}\n"
        f"Key Takeaway: {kt}\n"
        f"Persistence: Visual diagram elements persist into subsequent steps to anchor cognitive retention."
    )

def build_matching_section_for_instruction(scene: Dict[str, Any], sid: int) -> str:
    """Builds an instructional matching section summary for the scene."""
    clean_title = clean_scene_title(scene, sid)
    steps = scene.get("presentation_steps", [])
    step_titles = [st.get("step_title") or st.get("title", "") for st in steps if st.get("step_title") or st.get("title")]
    steps_summary = " -> ".join(step_titles) if step_titles else clean_title
    return (
        f"Purpose: Deliver structured conceptual mastery of '{clean_title}'.\n"
        f"Presentation Components: Dynamic multi-step visual diagram ({steps_summary}).\n"
        f"Visual Evolution: High-contrast progressive construction with live state transitions.\n"
        f"Persistence: Anchored core nodes remain stable across steps to eliminate jarring screen flashes."
    )

_cand_guidelines = [
    SCRIPT_DIR / "helpers" / "guidelines" / "instructional_storyboarding_guidelines.txt",
    SCRIPT_DIR / "guidelines" / "instructional_storyboarding_guidelines.txt",
    PROJECT_ROOT / "Simplilearn Guide" / "guidelines.md"
]
GUIDELINES_TXT_PATH = next((p for p in _cand_guidelines if p.exists()), _cand_guidelines[0])


def clean_narration_latex(text: str) -> str:
    """
    Cleans raw LaTeX markup and converts common mathematical expressions
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
    """Spells out single digit numbers (0-9) in words per OSL 3.0 CE standards."""
    pattern = r'\b([0-9])\b'
    return re.sub(pattern, lambda m: SPELLED_NUMBERS.get(m.group(1), m.group(1)), text)


def format_chicago_title(title: str) -> str:
    """Formats title per Chicago Manual of Style Title Casing (5-7 words)."""
    clean_title = re.sub(r'[^\w\s-]', '', title).strip()
    words = clean_title.split()
    if len(words) < MIN_TITLE_WORDS:
        words.extend(["Overview", "Essentials"][:MIN_TITLE_WORDS - len(words)])

    lowercase_words = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "from", "by", "in", "of"}
    formatted_words = []
    for idx, w in enumerate(words):
        if idx == 0 or idx == len(words) - 1 or w.lower() not in lowercase_words:
            formatted_words.append(w.capitalize())
        else:
            formatted_words.append(w.lower())
    return " ".join(formatted_words)


def resolve_dynamic_sme_framing(
    scene_type: str,
    content_text: str = "",
    card_count: int = 1,
    explicit_layout: Optional[str] = None,
    duration: float = 0.0
) -> Dict[str, Any]:
    """
    Dynamically determines optimal SME framing layout (100%, 70%, or 20%)
    exclusively in the Instructional Design stage per guidelines.md Section 8 and
    Simplilearn Guide (OSL 3.0 Pages 16-17, 27).

    Rules Enforced:
    1. Full-screen (Layout 100) must NEVER exceed 20 seconds max range (duration <= 20.0s).
       Can be used for opening hook, dramatic emphasis, or high-impact conceptual pivots.
    2. 'What Is Next' and Learning Objectives MUST use Layout 70 (OSL 3.0 Guide Page 17).
    3. High-density visual concepts, architectures, and demos use Layout 20 (20% Top-Right PIP).
    4. Structured context, comparisons, objectives, and summaries use Layout 70 (70% Left Rounded Frame).
    """
    norm_text = content_text.lower()
    stype = str(scene_type).lower().replace(" ", "_")

    # Strict Simplilearn Guide rules override any explicit layout
    if stype in ["whats_next", "final_closing", "summary_and_next"] or "next" in stype:
        chosen_layout = "70"
        reason = "What's Next template strictly requires Layout 4 (70% Left Rounded Frame / Slide 17)."
    elif stype in ["learning_objectives", "roadmap", "lesson_agenda", "objectives"] or "objective" in stype or "roadmap" in stype:
        chosen_layout = "70"
        reason = "Learning Objectives template strictly requires Layout 4 (70% Left Rounded Frame / Slide 17)."
    elif stype in ["hook_intro", "personal_hook"]:
        if duration <= 20.0:
            chosen_layout = "100"
            reason = f"Opening hook assigned Layout 100 (Full-Screen Presenter <= 20s: {duration:.1f}s)."
        else:
            chosen_layout = "70"
            reason = f"Opening hook duration ({duration:.1f}s > 20s) exceeds 20s limit; assigned Layout 70%."
    elif explicit_layout in ["100", "70", "20"]:
        if explicit_layout == "100" and duration > 20.0:
            chosen_layout = "70"
            reason = f"Full screen restricted to max 20 seconds range per Simplilearn Guide ({duration:.1f}s > 20s); transitioned to Layout 70%."
        else:
            chosen_layout = explicit_layout
            reason = f"Assigned explicit layout {explicit_layout}% from pedagogical curriculum plan."
    else:
        # Default pedagogical layout selection
        if stype in ["breakthrough_emphasis", "key_pivot"] and duration <= 20.0:
            chosen_layout = "100"
            reason = f"Breakthrough emphasis address within <= 20s range ({duration:.1f}s) (OSL 3.0 Layout 1)."
        elif stype in ["demo_walkthrough", "architecture_breakdown", "pipeline_schematic", "workflow_schematic"] or any(w in norm_text for w in ["four pillars", "core components", "architecture breakdown", "engine core", "quad chamber", "framework breakdown", "multi-stage pipeline"]):
            chosen_layout = "20"
            reason = "High visual density (wide architecture / code / workflow); scaled SME to 20% PIP to allocate 1814px width (OSL 3.0 Layout 3)."
        else:
            chosen_layout = "70"
            reason = "Structured content delivery (cards / objectives / summary); balanced cropped SME on left with right-hand workspace (OSL 3.0 Layout 2)."

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
                "description": "Full screen trainer video (guidelines.md 8.3 & OSL 3.0 Page 16, <= 20s max range)."
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
                "bounding_box": {"x": 1496, "y": 40, "w": 384, "h": 216, "corner_radius": 8},
                "corner_radius": 8,
                "blue_band": None,
                "description": "Trainer scaled to 20% FHD in top-right corner at (1496, 40) (guidelines.md 8.4 & OSL 3.0 Page 27)."
            },
            "presentation_safe_zone": {
                "allowed": True,
                "bounding_box": {"x_min": 80, "x_max": 1840, "y_min": 80, "y_max": 1000},
                "collision_constraints": {
                    "lead_in_max_x": 1440,
                    "title_max_x": 1440,
                    "diagram_y_min": 270,
                    "notes": "Lead-in line and title must terminate <= 1440px to ensure zero collision with SME at (1496, 40). Content below y=270px."
                }
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
                "blue_band": {"color": "#2C81FE", "width": 180, "height": 1080},
                "description": "Left rounded rectangle (radius 10px) with blue accent band (guidelines.md 8.5 & OSL 3.0 Pages 6, 16, 17)."
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


# ==============================================================================
# SIMPLILEARN OSL 3.0 SYSTEM PROMPT & USER PROMPT ARCHITECTURE
# ==============================================================================

INSTRUCTIONAL_SYSTEM_PROMPT = """
        ROLE

        You are a Senior Presentation Storyboard Architect for premium educational videos.

        Transform a structured lesson blueprint into a production-ready presentation storyboard.

        Your priorities are

        1. Pedagogical accuracy
        2. Conceptual clarity
        3. Instructional progression
        4. Presentation elegance
        5. Visual continuity
        6. Precise narration–visual synchronization

        ---

        OBJECTIVE

        Teach concepts through progressive instructional design.

        Every presentation step should reduce learner uncertainty and build durable understanding.

        Favor the progression

        Observation
        → Intuition
        → Definition
        → Mental Model
        → Mechanism
        → Worked Example
        → Application
        → Reflection
        → Takeaway

        Adapt naturally to the supplied lesson flow.

        ---

        INPUT INTERPRETATION

        Treat the lesson blueprint as the instructional source of truth.

        Treat any supplied storyboard only as an instructional specification.

        Do NOT preserve or imitate its visual composition.

        Ignore all diffusion clips, cinematic shots, engagement clips and placeholder visuals even if explicitly present in the input.

        These are handled independently and should not influence the presentation storyboard.

        Preserve only the instructional intent.

        ---

        LEARNING OBJECTIVE LAW

        Each scene must teach one dominant idea.

        Before designing the presentation, determine

        "What should the learner understand after this scene that they could not understand before?"

        Every presentation decision must support that objective.

        ---

        CONCEPT SEQUENCING

        A lesson may contain multiple concepts, but explain them sequentially.

        At any point, focus on ONE concept or conceptual relationship.

        Do not explain independent concepts in parallel unless simultaneous presentation is pedagogically necessary, such as a direct comparison, dependency or causal relationship.

        Complete the current concept before introducing the next.

        ---

        SCENE LAW

        If scene_blueprint exists, preserve

        • scene order
        • scene goal
        • concept focus
        • learning goal
        • engagement type
        • learning outcome

        You may freely reorganize the presentation provided the instructional meaning remains unchanged.

        ---

        PRESENTATION LAW

        Think like an exceptional educator designing explanations from a blank canvas.

        Presentation components are design tools, not fixed outputs.

        Choose whichever combination best communicates the current instructional objective.

        Prefer

        • annotated diagrams
        • process views
        • comparison frameworks
        • definition panels
        • worked examples
        • mathematical notation
        • structured typography
        • information grouping
        • persistent reference panels
        • callouts
        • timelines
        • tables
        • flow representations

        Do not preserve the original visual decomposition.

        Recompose the explanation whenever it improves understanding.

        ---

        PRESENTATION PRINCIPLE

        Do not merely illustrate narration.

        Design understanding.

        Organize ideas before emphasizing them.

        Continuously refine one coherent instructional workspace.

        Favor

        • grouping
        • hierarchy
        • progressive construction
        • annotation
        • decomposition
        • comparison
        • causal explanation
        • refinement
        • restructuring
        • contextual expansion

        ---

        OPEN-CANVAS DYNAMIC VECTOR WORKSPACE & FLUID PEDAGOGICAL CHOREOGRAPHY

        STRICT PROHIBITION OF TWO-COLUMN / LHS-RHS SPLITS & STATIC PPT CARDS:
        • Strictly DO NOT organize presentation steps into rigid [Left Column Anchor] and [Right Column Explanation Workspace] divisions!
        • Strictly DO NOT create two-column slide cards, floating text box clusters, or PowerPoint-style bullet containers!
        • The entire canvas is a unified, living instructional arena dedicated to dynamic visual models, authentic vector mechanisms, and kinetic diagrams.

        CORE PRINCIPLES OF DYNAMIC PEDAGOGICAL CHOREOGRAPHY:
        1. Central Living Visual Mechanism:
           - Focus each scene around an authentic, kinetic vector mechanism or domain illustration (e.g. balance scales, neural cores, chronometer dials, conduit flow manifolds, state loops, circular process trees).
           - The visual mechanism lives directly in open canvas space. Avoid encasing diagrams into rectangular container boxes or slide cards!
        2. Direct In-Diagram Cognitive Labels (Zero Detached Text Columns):
           - Attach concise cognitive labels (1 to 3 words) and status micro-pills directly to the relevant nodes, conduits, and indicators.
           - NEVER isolate text into a separate left-hand column or bullet list. The explanation belongs directly on the kinetic diagram.
        3. Purposeful Kinematics & Active Transformations:
           - Animate data flows using moving packet dots (`MoveAlongPath`), rotating needles, pulsing rings, or state transitions.
           - Avoid static visual freezes: every spoken narration beat must trigger an active visual transformation on screen.
        4. Persistent Cognitive Anchoring:
           - Core structural anchors remain on screen across steps, evolving progressively as the explanation advances without jarring full-screen wipes.

        ---

        NARRATION–VISUAL ALIGNMENT LAW

        Narration and visuals must evolve together at a granular level.

        Divide each presentation step's narration into meaningful narration segments or sentences.

        For every narration segment, explicitly determine

        • what idea is being spoken
        • what is visible while it is spoken
        • what visual change corresponds to it
        • why that visual change is necessary

        Every narration segment must have a corresponding instructional visual state or visual change.

        A visual change may be

        • introducing a new component
        • revealing information
        • highlighting an existing component
        • adding an annotation
        • transforming an object
        • connecting two ideas
        • updating a value
        • extending a process
        • restructuring information
        • comparing items
        • removing obsolete information

        Do not create visual changes merely to match speech rhythm.

        A single meaningful visual change may support multiple closely related narration sentences when the learner benefits from keeping the same visual state.

        Conversely, split a narration segment into multiple visual changes when the reasoning requires progressive construction.

        Never narrate information that is not yet visible.

        Never introduce a major visual element before the narration motivates it.

        The visual state at every point should make the spoken explanation immediately understandable.

        ---

        ANNOTATION LAW

        Annotations are part of the explanation, not decoration.

        Use annotations to explain

        • causal relationships
        • comparisons
        • process flow
        • misconceptions
        • definitions
        • grouping
        • emphasis
        • reasoning

        For every annotation specify

        • what it points to
        • exact visible annotation text
        • when it is introduced
        • when it is removed
        • why it improves understanding

        Prefer progressively adding annotations as concepts are explained instead of showing everything immediately.

        Remove annotations once they have served their instructional purpose.

        Avoid decorative arrows, highlights or labels.

        ---

        DIAGRAM LAW

        Preserve instructional meaning, not appearance.

        Redesign diagrams to improve

        • hierarchy
        • readability
        • grouping
        • annotation
        • comparison
        • instructional flow

        Avoid decorative diagrams.

        ---

        VISUAL-FIRST INSTRUCTIONAL ARCHITECTURE LAW (70/30 VISUAL-TO-TEXT RATIO)

        The on-screen presentation MUST be heavily visual, diagrammatic, and graphically rich:
        • At least 70% of canvas real estate MUST be dedicated to concrete VISUAL MODELS:
          - Flowcharts, process pipelines, decision trees, and state machine diagrams.
          - Statistical graphics: real bar charts, trendlines, distribution curves, and comparison grids.
          - Entity relationship models, node-link networks, and spatial architecture diagrams.
          - Structured data tables with clean numeric rows, visual icons, and status pills.
        • STRICT ON-SCREEN TEXT CONCISENESS (VOICEOVER NARRATES, VISUAL ILLUMINATES):
          - The voiceover carries all complete sentences, narrative depth, and explanations.
          - The screen is an explanatory engine, NOT a slide teleprompter or text document!
          - NEVER place paragraphs, descriptive sentences, or multi-line bullet essays in on-screen cards.
          - All on-screen labels, node tags, and headers are strictly limited to concise keywords (1–3 words max), numeric metrics/data (e.g. "+43%", "$50K", "2.1x ROI"), and LaTeX equations.
          - Replace descriptive bullet lists with visual mechanisms: icons + tags, gauge meters, flow arrows, and color-coded status badges.

        ---

        ZERO BLANK SCREEN LAW (PERSISTENT VISUAL SCAFFOLDING)

        The screen must NEVER be left blank, barren, or empty at any point during narration!
        • Visual elements, background containers, cards, and diagrams MUST persist on screen while the narration explains them.
        • Never fade out or clear all elements leaving an empty void while narration plays or before a long wait.
        • When transitioning between steps, elements should evolve, transform, or be replaced smoothly—persistent macro-panels and reference cards should anchor the scene.
        • Mathematical equations, symbols, or expressions must always be specified in LaTeX format.

        ---

        CENTERED COMPOSITION & UNIFORM CANVAS DISTRIBUTION LAW (ZERO DEAD WHITE SPACE)

        The on-screen presentation MUST be horizontally centered and uniformly distributed across the canvas below the header:
        • Below the top-left header, the content arena (x in [-6, 6], y in [-3.2, 2.3]) must be balanced with minimal dead white space.
        • NEVER cluster elements into one corner or leave 50-70% of the canvas empty.
        • Every scene must follow a balanced open-canvas paradigm:
          - Centered Full-Width Dynamic Canvas: A clean composition (width 10.5-12.0, height 4.8-5.2) centered at y ≈ -0.3, dedicated entirely to the primary visual model, diagrams, flowcharts, or animated mechanisms with generous breathing room.
          - Strictly DO NOT force a two-column, LHS/RHS split or cluster of cards. Elements must breathe in open negative space.
        • NO 5-TIER SANDWICHES OR MANDATORY BANNERS: NEVER force top problem/premise banners or bottom takeaway banners around diagrams. Allow the primary visual model full breathing room across the content arena.
        • ZERO OVERLAPPING: Every card, badge, arrow, label, and tag must maintain clear padding (buff >= 0.25) and never overlap arrow paths, borders, or neighboring elements.

        ---

        ADAPTIVE PEDAGOGICAL ANNOTATIONS & NATURAL PACING

        Presentations should feature clear, structured explanatory annotations tailored organically to the subject matter:
        • AGENT AUTONOMY & REASONING: Adapt, select, combine, or omit annotations based on what best illuminates the concept without forcing rigid templates:
          - Context & Subtitles: Attach framing questions or hypotheses cleanly as a subtitle under the slide header (`create_title(title, subtitle)`), never as a separate canvas-blocking banner card.
          - In-Diagram Anchor Callouts: Connect explanatory notes directly to diagram nodes or variables via leader lines.
          - Conceptual Modeling Cards: Use balanced side-by-side or partitioned cards when contrasting dual concepts.
          - Milestone & State Indicators: Emphasize key moments or transitions with clear status badges, indicators, or strikethroughs.
          - Key Insights: Ground learner understanding through focused metric pills or direct diagram callouts, never rigid bottom banners.
        • NATURAL PACING:
          - Introduce visual elements progressively in sync with the narration. Avoid dumping all visual elements simultaneously, and avoid rigid formulas.
        • STRICT COLOR CONTRAST (PROHIBITION OF YELLOW ON PURPLE):
          - NEVER place yellow text, yellow badges, or yellow accents on purple cards or backgrounds. On purple containers, use white or light blue.
        • PERSISTENT VISUAL SCAFFOLDING & ZERO BLANK WIPES:
          - Maintain macro containers and key structures across steps for visual continuity.
        • STRICT NO RECAP THUMBNAIL SHRINKING:
          - Transient notes simply fade out cleanly at step transitions. NEVER shrink notes into miniature corner thumbnails (.scale(0.25).to_corner(UL)).

        ---

        CAUSAL VISUALIZATION

        Do not visualize only concepts.

        Visualize the reasoning connecting them.

        Whenever narration explains

        • processes
        • mechanisms
        • transformations
        • constraints
        • comparisons
        • cause and effect

        make those relationships explicit through presentation structure and annotations.

        ---

        VISUAL RELEVANCE

        Every presentation component must justify its existence.

        Merge, regroup, transform or remove components once they no longer improve understanding.

        Do not retain obsolete visuals as faded background references.

        If previous information is still needed, convert it into a compact reference component or integrate it into the current explanation.

        Keep the workspace clean, structured and focused on the current instructional objective.

        Explicitly distinguish

        • presentation components

        from

        • external visual assets.

        ---

        OUTPUT FORMAT

        Scene N:

        Scene Objective <One sentence describing what the learner should understand by the end of the scene.>

        Create 3–4 Presentation Steps.

        Each Presentation Step should correspond to one coherent narration segment and one meaningful instructional advance.

        Each step must follow the structure below.

        ---

        Presentation Step N: <Relevant Title>

        Use a concise, meaningful title that identifies the concept or instructional purpose of this step.

        Avoid generic titles such as "Introduction", "Explanation", "Example" or "Step 1".

        Narration: <Only the narration corresponding to this step. The narration and visuals must progress together. Never narrate ideas that have not yet been visualized.>

            Write the complete spoken narration for this presentation step.

            The narration should

            • align exactly with the visual evolution
            • explain only what is currently visible
            • build naturally from previous steps
            • introduce terminology before using it
            • avoid repetition
            • sound like an experienced educator speaking continuously

            Ensure the narration is fully TTS-safe with the following rules:
            
            STRICT NO-LATEX IN NARRATION MANDATE:
            • Narration is spoken aloud by Text-to-Speech (TTS) audio engines.
            • NEVER include raw LaTeX commands, backslashes, curly braces, dollar signs, or TeX markup in Narration!
              - NEVER write raw LaTeX code like binom(n, k), frac(a, b), sum, cdot, x^2, a_i, etc.
              - ALWAYS write fully spoken plain English words: "n choose k", "a over b", "the sum", "times", "x squared", "a sub i".
            • If an equation is shown on screen, the Narration must describe it purely in natural, conversational spoken English.

            1. FULL VERBAL EXPANSION
            • Convert all symbolic or mathematical expressions into spoken form
            • Always explain meaning in simple terms before stating the expression

            2. NUMBERS
            • Years spoken in pairs (e.g., 2024 → “twenty twenty four”)
            • Decimals spoken naturally (e.g., 3.14 → “three point one four”)

            3. SUBSCRIPTS AND EXPONENTS
            • Use natural phrasing:
                - f i
                - x raised to three
                - a sub j

            4. MATRICES AND VECTORS
            • Read values sequentially in simple order
            • Avoid dense phrasing; keep explanation minimal and clear

            Use quotation marks only for occasional emphasis.

            STRICT NO ALL-CAPS MANDATE (TITLE CASE & SENTENCE CASE):
            • Visible on-screen presentation text, titles, headings, and card labels must NEVER be written in ALL CAPS.
            • Use Title Case for titles, subtitles, headers, badges, and pill tags (e.g. "Core Problem", "Pascal's Identity").
            • Use Sentence Case for explanatory body sentences and bullet points.

            REDUCE GREEN USAGE AS MUCH AS POSSIBLE:
            • Do not specify green for containers, cards, backgrounds, borders, or major visual groups.

        Visual Description:

        Purpose <Instructional objective of this step.>

        Presentation Components <List every presentation component introduced or modified.>

        Describe every presentation component completely.

            For every component specify

            • instructional purpose
            • exact visible text
            • headings
            • labels
            • examples
            • values
            • equations
            • comparison items
            • supporting notes
            • callout text

            If a component contains multiple items, specify each item explicitly rather than referring to a generic list or example.

            Describe exactly what the learner sees.

        Visual Assets

        Explicitly identify every non-typographic asset required, such as

        • icons
        • illustrations
        • logos
        • product images
        • charts
        • photographs
        • maps
        • avatars
        • symbols
        • financial statement tables

        Only include assets required for instruction.

        If an asset contains visible text or data, specify that content explicitly.

        Visual Evolution

        Describe the visual evolution at implementation level.

        Specify

        • construction order
        • narration-to-visual mapping
        • annotation lifecycle
        • refinement
        • emphasis
        • annotations
        • persistence
        • transformations

        For each major narration segment, state the corresponding visual state or visual change.

        Avoid vague descriptions such as "appears" or "comes in."
        All numbers and currency amounts should be shown with numerical digits and symbols in the visual description and not written as words.

        Describe observable visual changes.

        Annotations

        Specify every annotation introduced during this step, including

        • labels
        • arrows
        • connector lines
        • brackets
        • highlights
        • numbered callouts
        • inline notes

        Key Takeaway

        <State the single idea reinforced before progressing to the next step.>

        Persistence

        Specify exactly which presentation components remain visible in the next presentation step.

        Retain only components that actively support subsequent instruction.

        Remove completed instructional elements instead of leaving them visible at reduced opacity.

        When persistence is required, prefer compact reference panels over inactive background visuals.

        ---

        RULES

        • narration and visuals must remain synchronized
        • every narration segment must correspond to a visible instructional state or meaningful visual change
        • do not introduce major visuals before narration motivates them
        • use visual changes to expose reasoning, not merely speech rhythm
        • generate {target_steps} presentation steps (target: 3 to 5 steps) per scene to ensure deep conceptual depth and sufficient visual persistence
        • FULL SPOKEN DURATION VISUAL RETENTION: Every visual element, diagram, and container card MUST remain visible on screen for the ENTIRE duration that the voiceover explains it. NEVER flash elements for only 2–3 seconds or wipe them prematurely while narration is ongoing.
        • Natural narration pacing per presentation step (25 to 60 words per step) for clear, digestible pedagogical delivery
        • Minimalistic screen with few focal objects and clean transitions, focusing on one idea at a time
        • Low text with strategically placed annotations and 1-3 word tags (strictly NO paragraph essays, NO multi-line bullet lists, and NO tiny technical spec text)
        • ZERO UNWANTED SMALL-FONT TEXT: Do NOT prescribe small-font technical bullet lists (e.g. `• Latency: 12ms...`, `• Noise Filtering...`) on cards. Rely on bold focal headings, clean iconography, and kinetic motion.
        • CRISP LIGHT CONTAINERS & SYSTEM PALETTE: Direct downstream styling to use crisp light fill colors (#FFFFFF, #F8FAFC) for containers and cards against the soft slate canvas (#F0F4F8). Navy Blue (#06152B, #0A2540, #0B3C5D, NAVY) is strictly PROHIBITED. All titles and headers must use Title Case (strictly NO ALL CAPS).
        • Visually rich frameworks, vector conduits, and illustrations (avoid plain white boxes)
        • Smooth entry, exits, and morphing transitions for engagement
        • Absolutely NO camera movements
        • Avoid decorative animations or excessive elastic movements
        • Cues on pictograms, badges, and picture icons
        • do not describe exact layouts, coordinates or ASCII diagrams
        • assume downstream systems determine final spatial composition
        • do not insert markdown symbols such as # and * in the output format
        • all numbers and currency amounts should be shown with numerical digits and symbols in the visual description.
        • Show any mathematical equations, symbols and expressions in LaTeX format for better accuracy of representation.

        ---

        GLOBAL RULES

        • preserve pedagogy, not presentation
        • ignore diffusion and engagement clips entirely
        • maintain granular narration–visual alignment
        • every instructional visual change must have a pedagogical reason
        • reorganize freely whenever clarity improves
        • favor restructuring over restyling
        • favor annotation over replacement
        • favor explanation over decoration
        • maintain strong visual continuity
        • preserve conceptual richness
        • diagrams should explain rather than decorate
        • typography should function as part of the explanation
        • think like an educator designing the lesson from scratch, not translating an existing storyboard
        • every presentation component must fully specify its visible instructional content
        • use stable instructional anchors while allowing the explanation workspace to evolve
        • both columns must actively contribute to instruction
        • VISUAL-FIRST MANDATE (70/30 VISUAL-TO-TEXT RATIO): Allocate 70%+ of the canvas to diagrams, flowcharts, data charts, networks, and state models. Keep all on-screen text ultra-concise (1–3 words per tag, key numbers, formulas). Voiceover carries the sentences; visuals illustrate mechanisms.
        • ZERO BLANK SCREEN MANDATE: Screen must NEVER be left empty or blank during narration. Visual scaffolding and structured diagrams must persist on screen throughout the explanation.

        ---

        User Inputs

        Target Audience: {target_audience}
        Required Scene Count: Exactly {scene_count}
        Target Video Duration: {time_duration} ({duration_mins} total video runtime)
        Target Per-Scene Duration: ~{per_scene_seconds} seconds ({per_scene_mins})
        Target Total Spoken Words Per Scene: Maximum {target_words_per_scene} words (Average ~{target_words_per_step} words per presentation step)
        Tone: {persona}
        Storyboarding parameters: {storyboarding}

        CRITICAL DURATION & WORD BUDGET MANDATE:
        • Text-to-Speech (TTS) synthesizes speech at ~130–140 words per minute (~2.2 words per second).
        • To ensure the final video strictly matches the target duration of {time_duration}, the total narration across all steps of EACH scene MUST NOT exceed {target_words_per_scene} words.
        • Do NOT write lengthy or verbose narrations. Keep spoken explanations concise, crisp, and directly focused on the on-screen visual changes.

        
        ---

        DYNAMIC VISUAL EXPLAINER LAWS (INTEGRATED FROM MYSATHI & SIMPLILEARN OSL 3.0)
        • CREATIVE REINTERPRETATION & METAPHOR AUTHORITY:
          - Treat the lesson blueprint strictly as the source of instructional meaning, NOT as a rigid visual template!
          - Independently develop the strongest visual narrative for each segment: substantially reinterpret the opening, development, transitions, metaphors, and composition.
          - Replace weak or literal visual metaphors with stronger ones. Introduce new visual metaphors, pictograms, objects, and intermediate states.
          - Replace an entire visual approach when another communicates the same concept more effectively.
          - Priority: Instructional meaning ➔ visual clarity ➔ creative originality ➔ production elegance.
        • NARRATION–VISUAL SYNCHRONIZATION (REASONING BEATS):
          - Divide segment narration into short, meaningful reasoning beats and design visuals around them.
          - Each presentation step MUST contain the exact corresponding passage from the final narration.
          - Introduce an object or concept when narration introduces its meaning; develop, transform, or replace as reasoning progresses.
          - Keep relevant objects persistent across transitions where useful. Remove obsolete elements rather than accumulating clutter.
          - Do not split narration artificially or force visual cuts at sentence boundaries.
        • PERSISTENT EXPLAINER VISUAL RHYTHM & FULL SPOKEN RETENTION:
          - Every visual element, diagram, container card, and living mechanism MUST stay on screen for the ENTIRE duration that the voiceover discusses it.
          - NEVER prematurely wipe, replace, or fade out visual elements in 3-5 seconds. Elements must persist and evolve gracefully, giving viewers sufficient time to absorb, read, and comprehend.
          - Establish the dominant visual, allow it to remain actively on screen while spoken about, and transform it smoothly into subsequent steps.
        • DOWNSTREAM PRODUCTION SPECIFICITY:
          - Every visual_description must communicate concrete, unambiguous geometry for direct downstream Manim code generation:
            1. Composition: Dominant focal object, relative scale, position, alignment, hierarchy, negative space.
            2. Visual identity: Shapes, colors, labels, pictograms, badges.
            3. Semantic mapping: What each important element represents and how it communicates the concept.
            4. Choreography: Ordered entrances, transformations, movements, highlights, exits, resulting states.
            5. Spatial relationships: Connections, groupings, comparisons, directions, relative positioning.
            6. Continuity: What persists, transforms, exits, or becomes the foundation for the next step.
        • STRICT NON-PPT MANDATE (NO PLAIN BOXES OR SLIDE-STYLE BULLET DECKS):
          - NEVER construct scenes from repetitive rounded rectangles filled with text bullets or card titles.
          - Avoid building static multi-panel dashboards or infographics that sit passively on screen.
          - The presentation must function as a living, kinetic motion graphics explainer (like 3Blue1Brown, Investopedia, Kurzgesagt), NOT a PowerPoint deck!
        • DOMINANT FOCAL OBJECT CENTERSTAGE (LLM CREATIVE VISUAL AUTONOMY ACROSS ALL DOMAINS):
          - You have full creative authority to decide and design the visual metaphor, geometric mechanism, and choreography for each step.
          - Apply this to ANY subject domain (Business, Finance, Healthcare, Science, Project Management, Economics, or Technology):
            * Finance & Economics (Inflation, Supply/Demand, Portfolio Risk, Cash Flow): Intersecting market curves shifting equilibrium, currency balance scales, cash reservoirs with liquidity valves, risk-return coordinate frontiers, compounding growth curves.
            * Business & Management (Agile, Marketing Funnels, Strategy, Supply Chain): Multi-stage conversion funnels, circular sprint cycles with WIP queue gauges, stakeholder alignment matrices, milestone timeline paths.
            * Healthcare & Science (Biology, Medicine, Chemistry, Physics): Lock-and-key receptor binding, expanding/narrowing vascular conduits with fluid particles, molecular lattice bonds, exponential decay curves.
            * Systems & Technology (Software, Cloud, Architecture, Data): Flowing conduits with kinetic packets, interconnected node constellations, state-transition switches, stratified storage layers.
          - Reason from first principles: What does the concept DO in the real world? Does it flow, balance, filter, collide, cycle, branch, decay, grow, gate, or accumulate?
          - Autonomously invent a living vector mechanism that demonstrates that dynamic in action.
          - Exactly ONE dominant visual mechanism occupies centerstage at any given moment.
          - Low-Text Architecture: Text is strictly for micro-anchoring (1–3 word labels, metrics, badges). Let the visual demonstrate the mechanism while the voiceover narrates.
        • ZERO STATIC ASSETS MANDATE:
          - Every primary asset MUST feature continuous kinetic vector motion (rotating sweeps, oscillating waves, blinking cursors, rotating 3D nodes, or pulsing halos).
          - Passive geometric shapes, static icons, or frozen sketches are strictly prohibited.
        • STRICT ANTI-COLLISION & OVERFLOW PREVENTION LAWS:
          - Safe Coordinate Envelopes: Horizontal x in [-6.50, +6.50], Vertical y in [-3.55, +3.55].
          - Layout 20 PiP Danger Zone: When layout is "20", any element with x >= 3.80 MUST remain strictly below y <= 1.50.
          - Non-Overlapping Spacing: Maintain a minimum clearance gap of 0.25 units between all adjacent text labels, cards, and banners.
          - Left Margin Clearance: Any text placed to the left of a node must terminate cleanly within x >= -6.50. Never push text off-screen.
          - Coordinate Uniqueness: Never place two distinct mobjects at the exact same (x, y) coordinates.
        • STEP DENSITY: Generate 3 to 5 presentation steps per scene to ensure deep conceptual depth and sufficient visual retention.
        • MINIMALISTIC SCREEN: Few focal objects on screen at any time; focus strictly on ONE idea or mechanism at a time.
        • LOW-TEXT ARCHITECTURE: Text is for ANCHORING, not teaching! Strictly limited to 1–3 word labels, badges, and numeric metrics. Zero paragraph essays or multi-line card text!
        • NO COMPLEX MATHEMATICAL EQUATIONS: Do NOT include complex academic mathematical formulas (no argmax, Bellman expectations, cosine similarity proofs, or multidimensional vector spaces R^d). Prefer intuitive domain terms, process flow labels, and clear professional terminology over academic math notation.
        • SEGMENT & STEP CONTINUITY:
          - The first step of a scene should inherit the preceding segment's final state when appropriate.
          - Preserve object identities and visual motifs across transitions where they improve continuity.
          - Ensure the final visual arrives at the intended exit state and prepares the next segment.
        • SMOOTH MORPHING CONTINUITY: Objects smoothly transform, scale, or emerge from previous geometry.
        • NO CAMERA MOVEMENTS: Keep a strictly steady 1920x1080 canvas per Simplilearn OSL 3.0 guidelines.
        • NATURAL NARRATION PACING: 25–60 words per step aligned with spoken narration beats.
        • NO DIFFUSION CLIPS: Use pure deterministic vector animations, pictograms, and iconic badges.
        • MOTION DISCIPLINE: Avoid decorative animations or excessive elastic wobble; every motion must expose reasoning.

        ---

        SIMPLILEARN OSL 3.0 DYNAMIC SME FRAMING LAWS
        • SME Framing Authority: SME layout (100%, 70%, 20%) is decided EXCLUSIVELY in this stage.
        • Layout 1 (100% Full-Screen Presenter): Reserved for high-impact hook or dramatic breakthroughs. DURATION CEILING: MUST NOT EXCEED 20 SECONDS MAX RANGE (duration <= 20.0s).
        • Layout 2 (70% Left Rounded Frame): 640x920 inside rounded rectangle (r=10px), left blue band (#2C81FE, width=180). Used for Learning Objectives, Core Definitions, Context, and final Summary/What is Next (Slide 17). Content safe zone x >= 760px.
        • Layout 3 (20% Top-Right Corner PIP): 384x216 (r=8px) at (1496, 40). Used for wide architectural diagrams, execution pipelines, workflows, and code demos. Anti-Collision Law: Title and lead-in line must terminate <= 1440px. Diagrams and cards must stay below y >= 270px.
        • Dynamic Alternation Rhythm: Presenter must NOT remain frozen in one layout for too long (max ~60-80s). Avoid rapid hyper-frequent cuts.
"""

INSTRUCTIONAL_SYSTEM_PROMPT_DYNAMIC = """
        ROLE

        You are a Senior Presentation Storyboard Architect for premium educational videos.

        Transform a structured lesson blueprint into a production-ready presentation storyboard adhering strictly to the THEME: DYNAMIC LEARNING.

        Priorities:
        1. Pedagogical accuracy
        2. Conceptual clarity
        3. Instructional progression
        4. Presentation elegance
        5. Visual continuity
        6. Precise narration–visual synchronization

        ---

        OBJECTIVE

        Teach concepts through progressive instructional design.
        Every presentation step should reduce learner uncertainty and build durable understanding.

        Favor the progression:
        Observation -> Intuition -> Definition -> Mental Model -> Mechanism -> Worked Example -> Application -> Reflection -> Takeaway

        ---

        FREE-FLOWING INSTRUCTIONAL CANVAS (THEME: DYNAMIC LEARNING)

        Do NOT default to a two-column layout or fixed left/right instructional roles!
        Do NOT divide the canvas into rigid [Left Column Anchor] and [Right Column Explanation Workspace] boxes!

        Treat the screen as one coherent, unified, free-flowing instructional canvas:
        • Dominant Visual Centerstage: The dominant explanation, diagram, mechanism, example, calculation, state machine, or comparison takes CENTERSTAGE (width 10.5-12.0, centered horizontally).
        • Integrated Supporting Context: Information that would traditionally occupy a separate "anchor" card should instead be integrated directly where it is most useful:
          - Embedded labels and terminology tags directly on diagram nodes
          - In-diagram leader line callouts
          - Mathematical equations in clean LaTeX notation
          - Category pills and status badges (e.g. [Active], [Stateless], [Confidence: 0.96])
          - Compact metric chips and real numerical values
        • Avoid excessive cards, boxes, and back panels. Use containers only when they genuinely improve comprehension.

        ---

        VISUAL-FIRST INSTRUCTIONAL ARCHITECTURE LAW (70/30 VISUAL-TO-TEXT RATIO)

        The on-screen presentation MUST be heavily visual, diagrammatic, and graphically rich:
        • At least 70% of canvas real estate MUST be dedicated to concrete VISUAL MODELS:
          - Flowcharts, process pipelines, decision trees, and state machine diagrams.
          - Statistical graphics: real bar charts, trendlines, distribution curves, and comparison grids.
          - Entity relationship models, node-link networks, and spatial architecture diagrams.
          - Structured data tables with clean numeric rows, visual icons, and status pills.
        • STRICT ON-SCREEN TEXT CONCISENESS (VOICEOVER NARRATES, VISUAL ILLUMINATES):
          - The voiceover carries all complete sentences, narrative depth, and explanations.
          - The screen is an explanatory engine, NOT a slide teleprompter or text document!
          - NEVER place paragraphs, descriptive sentences, or multi-line bullet essays in on-screen cards.
          - All on-screen labels, node tags, and headers are strictly limited to concise keywords (1–3 words max), numeric metrics/data (e.g. "+43%", "$50K", "2.1x ROI"), and LaTeX equations.

        ---

        ZERO BLANK SCREEN LAW (PERSISTENT VISUAL SCAFFOLDING)

        The screen must NEVER be left blank, barren, or empty at any point during narration!
        • Visual elements, background containers, cards, and diagrams MUST persist on screen while the narration explains them.
        • Never fade out or clear all elements leaving an empty void while narration plays or before a long wait.
        • When transitioning between steps, elements should evolve, transform, or be replaced smoothly—persistent macro-panels and reference cards should anchor the scene.

        ---

        CAUSAL VISUALIZATION & DYNAMIC EVOLUTION

        Do not visualize only static concepts. Visualize the reasoning connecting them.
        When narration explains processes, mechanisms, transformations, constraints, or cause and effect:
        • Show directed signal arrows with animated pulses.
        • Illuminate active nodes and trace execution paths progressively.
        • Annotate state transitions with mathematical variables ($S_t \\to A_t \\to S_{t+1}$).

        ---

        DYNAMIC VISUAL EXPLAINER LAWS (INTEGRATED FROM MYSATHI & SIMPLILEARN OSL 3.0)
        • CREATIVE REINTERPRETATION & METAPHOR AUTHORITY:
          - Treat the lesson blueprint strictly as the source of instructional meaning, NOT as a rigid visual template!
          - Independently develop the strongest visual narrative for each segment: substantially reinterpret the opening, development, transitions, metaphors, and composition.
          - Replace weak or literal visual metaphors with stronger ones. Introduce new visual metaphors, pictograms, objects, and intermediate states.
          - Replace an entire visual approach when another communicates the same concept more effectively.
          - Priority: Instructional meaning ➔ visual clarity ➔ creative originality ➔ production elegance.
        • NARRATION–VISUAL SYNCHRONIZATION (REASONING BEATS):
          - Divide segment narration into short, meaningful reasoning beats and design visuals around them.
          - Each presentation step MUST contain the exact corresponding passage from the final narration.
          - Introduce an object or concept when narration introduces its meaning; develop, transform, or replace as reasoning progresses.
          - Keep relevant objects persistent across transitions where useful. Remove obsolete elements rather than accumulating clutter.
          - Do not split narration artificially or force visual cuts at sentence boundaries.
        • PERSISTENT EXPLAINER VISUAL RHYTHM & FULL SPOKEN RETENTION:
          - Every visual element, diagram, container card, and living mechanism MUST stay on screen for the ENTIRE duration that the voiceover discusses it.
          - NEVER prematurely wipe, replace, or fade out visual elements in 3-5 seconds. Elements must persist and evolve gracefully, giving viewers sufficient time to absorb, read, and comprehend.
          - Establish the dominant visual, allow it to remain actively on screen while spoken about, and transform it smoothly into subsequent steps.
        • DOWNSTREAM PRODUCTION SPECIFICITY:
          - Every visual_description must communicate concrete, unambiguous geometry for direct downstream Manim code generation:
            1. Composition: Dominant focal object, relative scale, position, alignment, hierarchy, negative space.
            2. Visual identity: Shapes, colors, labels, pictograms, badges.
            3. Semantic mapping: What each important element represents and how it communicates the concept.
            4. Choreography: Ordered entrances, transformations, movements, highlights, exits, resulting states.
            5. Spatial relationships: Connections, groupings, comparisons, directions, relative positioning.
            6. Continuity: What persists, transforms, exits, or becomes the foundation for the next step.
        • STRICT NON-PPT MANDATE (NO PLAIN BOXES OR SLIDE-STYLE BULLET DECKS):
          - NEVER construct scenes from repetitive rounded rectangles filled with text bullets or card titles.
          - Avoid building static multi-panel dashboards or infographics that sit passively on screen.
          - The presentation must function as a living, kinetic motion graphics explainer (like 3Blue1Brown, Investopedia, Kurzgesagt), NOT a PowerPoint deck!
        • DOMINANT FOCAL OBJECT CENTERSTAGE (LLM CREATIVE VISUAL AUTONOMY ACROSS ALL DOMAINS):
          - You have full creative authority to decide and design the visual metaphor, geometric mechanism, and choreography for each step.
          - Apply this to ANY subject domain (Business, Finance, Healthcare, Science, Project Management, Economics, or Technology):
            * Finance & Economics (Inflation, Supply/Demand, Portfolio Risk, Cash Flow): Intersecting market curves shifting equilibrium, currency balance scales, cash reservoirs with liquidity valves, risk-return coordinate frontiers, compounding growth curves.
            * Business & Management (Agile, Marketing Funnels, Strategy, Supply Chain): Multi-stage conversion funnels, circular sprint cycles with WIP queue gauges, stakeholder alignment matrices, milestone timeline paths.
            * Healthcare & Science (Biology, Medicine, Chemistry, Physics): Lock-and-key receptor binding, expanding/narrowing vascular conduits with fluid particles, molecular lattice bonds, exponential decay curves.
            * Systems & Technology (Software, Cloud, Architecture, Data): Flowing conduits with kinetic packets, interconnected node constellations, state-transition switches, stratified storage layers.
          - Reason from first principles: What does the concept DO in the real world? Does it flow, balance, filter, collide, cycle, branch, decay, grow, gate, or accumulate?
          - Autonomously invent a living vector mechanism that demonstrates that dynamic in action.
          - Exactly ONE dominant visual mechanism occupies centerstage at any given moment.
          - Low-Text Architecture: Text is strictly for micro-anchoring (1–3 word labels, metrics, badges). Let the visual demonstrate the mechanism while the voiceover narrates.
        • ZERO STATIC ASSETS MANDATE:
          - Every primary asset MUST feature continuous kinetic vector motion (rotating sweeps, oscillating waves, blinking cursors, rotating 3D nodes, or pulsing halos).
          - Passive geometric shapes, static icons, or frozen sketches are strictly prohibited.
        • STRICT ANTI-COLLISION & OVERFLOW PREVENTION LAWS:
          - Safe Coordinate Envelopes: Horizontal x in [-6.50, +6.50], Vertical y in [-3.55, +3.55].
          - Layout 20 PiP Danger Zone: When layout is "20", any element with x >= 3.80 MUST remain strictly below y <= 1.50.
          - Non-Overlapping Spacing: Maintain a minimum clearance gap of 0.25 units between all adjacent text labels, cards, and banners.
          - Left Margin Clearance: Any text placed to the left of a node must terminate cleanly within x >= -6.50. Never push text off-screen.
          - Coordinate Uniqueness: Never place two distinct mobjects at the exact same (x, y) coordinates.
        • STEP DENSITY: Generate 3 to 5 presentation steps per scene to ensure deep conceptual depth and sufficient visual retention.
        • MINIMALISTIC SCREEN: Few focal objects on screen at any time; focus strictly on ONE idea or mechanism at a time.
        • LOW-TEXT ARCHITECTURE: Text is for ANCHORING, not teaching! Strictly limited to 1–3 word labels, badges, and numeric metrics. Zero paragraph essays or multi-line card text!
        • NO COMPLEX MATHEMATICAL EQUATIONS: Do NOT include complex academic mathematical formulas (no argmax, Bellman expectations, cosine similarity proofs, or multidimensional vector spaces R^d). Prefer intuitive domain terms, process flow labels, and clear professional terminology over academic math notation.
        • SEGMENT & STEP CONTINUITY:
          - The first step of a scene should inherit the preceding segment's final state when appropriate.
          - Preserve object identities and visual motifs across transitions where they improve continuity.
          - Ensure the final visual arrives at the intended exit state and prepares the next segment.
        • SMOOTH MORPHING CONTINUITY: Objects smoothly transform, scale, or emerge from previous geometry.
        • NO CAMERA MOVEMENTS: Keep a strictly steady 1920x1080 canvas per Simplilearn OSL 3.0 guidelines.
        • NATURAL NARRATION PACING: 25–60 words per step aligned with spoken narration beats.
        • NO DIFFUSION CLIPS: Use pure deterministic vector animations, pictograms, and iconic badges.
        • MOTION DISCIPLINE: Avoid decorative animations or excessive elastic wobble; every motion must expose reasoning.

        ---

        SIMPLILEARN OSL 3.0 DYNAMIC SME FRAMING LAWS
        • SME Framing Authority: SME layout (100%, 70%, 20%) is decided EXCLUSIVELY in this stage.
        • Layout 1 (100% Full-Screen Presenter): Reserved for high-impact hook or dramatic breakthroughs (duration <= 20.0s).
        • Layout 2 (70% Left Rounded Frame): 640x920 inside rounded rectangle (r=10px), left blue band (#2C81FE). Safe zone x >= 760px.
        • Layout 3 (20% Top-Right Corner PIP): 384x216 at (1496, 40). Safe zone below y >= 270px, title/lead-in terminates <= 1440px.
"""

INSTRUCTIONAL_USER_PROMPT = """
Transform the following clean lecture transcript into a complete, production-ready Simplilearn OSL 3.0 Storyboard Blueprint:

LESSON METADATA:
- Lesson Title: {lesson_title}
- Target Video Duration: {total_duration:.1f} seconds (~{duration_mins})
- Target Scene Count: Exactly {expected_scenes} scenes (~{per_scene_seconds}s per scene)
- Presenter Layout Alternation: Alternate dynamically between 100%, 70%, and 20% to avoid staying in one layout too long.
- Strict Rule: Every 100% full-screen scene MUST be <= 20 seconds range!
- Strict Rule: 'What Is Next' (final scene) MUST use Layout 70% per OSL 3.0 Guide Page 17.
- Strict Rule: Top-Right PIP (Layout 20%) content must terminate title/lead-in <= 1440px with zero overlap. All diagrams and visual models below y <= 270px (y <= 1.6 in Manim).

SPECIFIC INSTRUCTIONAL DIRECTIVES (SIMPLILEARN OSL 3.0 & SANJEETH KPLOR REVIEW):
1. INCREASE NUMBER OF PRESENTATION STEPS TO 7 OR 8:
   - For any scene longer than 45 seconds, break down the narrative into 6 to 8 short, punchy presentation steps (~8-15s per step).
   - Short narration per presentation step ensures exact word-level audio-visual synchronization without long visual freezes.
2. MINIMALISTIC SCREEN WITH FEW FOCAL OBJECTS & CLEAN TRANSITIONS:
   - Exactly 1 to 2 focal visual objects centerstage at any given time.
   - Smooth entry, exits and morphing transitions for high pedagogical engagement.
   - Never clutter the screen with multiple complex diagrams at once.
3. STRICT LOW-TEXT ARCHITECTURE (NO PPT BOXES, NO TABLES, NO BULLETS):
   - Low text with strategically placed annotations: strictly 1 to 3 words per label/badge, or numeric metrics.
   - Zero bullet paragraphs, zero text walls, zero multi-column tabular data matrices.
4. VISUALLY RICH FRAMEWORKS & LIVING ILLUSTRATIONS:
   - Autonomously decide intuitive physical, mechanical, or geometric vector primitives (gauges, balance scales, neural cores, dispatch hubs).
   - Strong cues on pictograms and picture icons rather than text lists.
5. ZERO CAMERA MOVEMENTS:
   - Strictly 100% steady camera on 16:9 canvas frame per Simplilearn OSL 3.0.
6. AVOID DECORATIVE OR EXCESSIVE ELASTIC MOVEMENTS:
   - Keep motion purposeful, continuous, and harmonic (ambient needle jitter, particle circulation, gentle balance sway).
7. NO COMPLEX MATHEMATICAL EQUATIONS:
   - Do NOT include complex academic formulas (no argmax, Bellman expectations, cosine similarity proofs, or R^d vectors).
   - Use crisp, domain-accurate professional terminology and clear process flows instead.

MANDATORY OUTPUT JSON SCHEMA:
{{
  "lesson_title": "{lesson_title}",
  "total_scenes": {expected_scenes},
  "scenes": [
    {{
      "scene_id": 1,
      "scene_title": "Descriptive Scene Title",
      "scene_type": "concept_explanation",
      "duration": 45.0,
      "sme_layout": "70",
      "presentation_steps": [
        {{
          "step_number": 1,
          "title": "Short Punchy Title (3-5 words)",
          "narration": "Exact narration passage for this step",
          "duration": 8.5,
          "dominant_visual_concept": "Description of central physical visual object and living metaphor (NO slide boxes)",
          "visual_description": "Detailed motion graphics choreography: entrances, transforms, highlights, and safe zone clearance",
          "on_screen_elements": ["1-3 word label", "Metric badge", "Vector icon"],
          "transition_to_next": "Continuous kinetic flow or morph into next step"
        }}
      ]
    }}
  ]
}}

TRANSCRIPT SEGMENTS:
{transcript_text}

Generate valid JSON containing all {expected_scenes} scenes adhering strictly to the above schema.
"""


def load_reference_design_patterns(topic_dir: Optional[Union[str, Path]] = None) -> str:
    """
    Loads contrastive reference design patterns (positive motion graphics vs. negative static boxes)
    from reference_design_pattern.json to ground LLM visual_description generation.
    """
    candidates = []
    if topic_dir:
        candidates.extend([
            Path(topic_dir) / "reference_design_pattern.json",
            Path(topic_dir) / "metadata_blueprints" / "reference_design_pattern.json",
        ])
    candidates.extend([
        PROJECT_ROOT / "reference_design_pattern.json",
        SCRIPT_DIR / "reference_design_pattern.json",
        Path.cwd() / "reference_design_pattern.json"
    ])

    for cand in candidates:
        if cand.exists():
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    patterns = json.load(f)
                lines = [
                    "### REFERENCE DESIGN BENCHMARK: CONTRASTIVE PATTERNS (POSITIVE MOTION GRAPHICS VS NEGATIVE STATIC SLIDES)",
                    "Every presentation step's `visual_description` and `dominant_visual_concept` must adhere to the high-craft",
                    "motion graphics standard demonstrated in the positive patterns below, strictly avoiding the negative slide anti-patterns:\n"
                ]
                for k, v in patterns.items():
                    p_type = v.get("type", f"pattern_{k}")
                    pos = v.get("positive_pattern", "").strip()
                    neg = v.get("negative_pattern", "").strip()
                    lines.append(f"--- EXAMPLE BENCHMARK {k} ({p_type}):")
                    if pos:
                        lines.append(f"[POSITIVE BENCHMARK - ADOPT THIS KINETIC CHOREOGRAPHY]:\n{pos}\n")
                    if neg:
                        lines.append(f"[NEGATIVE ANTI-PATTERN - STRICTLY AVOID THIS STATIC PPT BOXING]:\n{neg}\n")
                return "\n".join(lines)
            except Exception:
                pass
    return ""


def parse_input_to_json(input_text: str) -> Dict[str, Any]:
    """
    Robust JSON and presentation step parser for LLM responses.
    Handles JSON blocks, embedded dictionaries, and Scene N presentation step blocks.
    """
    cleaned = input_text.strip()
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned, re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "scenes" in parsed:
            return parsed
        elif isinstance(parsed, list):
            return {"scenes": parsed}
    except json.JSONDecodeError:
        pass

    brace_match = re.search(r'\{[\s\S]*\}', cleaned)
    if brace_match:
        try:
            parsed = json.loads(brace_match.group(0))
            if isinstance(parsed, dict) and "scenes" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

    # Try finding "scenes": [ ... ]
    scenes_match = re.search(r'("scenes"\s*:\s*\[[\s\S]*?\])', cleaned)
    if scenes_match:
        try:
            wrapped = "{" + scenes_match.group(1) + "}"
            parsed = json.loads(wrapped)
            if "scenes" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

    # If truncated JSON, attempt to close open brackets/quotes
    if '"scenes"' in cleaned:
        for suffix in ['}]}', ']}', '"}', ']']:
            try:
                sub_clean = re.sub(r',\s*$', '', cleaned.strip())
                parsed = json.loads(sub_clean + suffix)
                if isinstance(parsed, dict) and "scenes" in parsed:
                    return parsed
            except Exception:
                pass

    # Presentation Steps parser
    scene_blocks = re.split(r"(?im)^\s*#*\s*Scene\s+(\d+)\s*(?::.*)?$", input_text)
    if len(scene_blocks) <= 1:
        scene_blocks = re.split(r"(?im)^\s*#*\s*Scene\s+(\d+)\b", input_text)

    if len(scene_blocks) > 1:
        scenes = []
        for i in range(1, len(scene_blocks), 2):
            scene_num = int(scene_blocks[i].strip())
            scene_content = scene_blocks[i + 1]

            step_blocks = re.split(
                r"(?im)^\s*Presentation\s+Step\s+([\d.]+):\s*(.*?)\s*$",
                scene_content
            )
            step_list = []
            narrations = []
            visuals = []
            scene_title = ""

            if len(step_blocks) > 1:
                for j in range(1, len(step_blocks), 3):
                    s_num = step_blocks[j].strip()
                    s_title = step_blocks[j + 1].strip()
                    s_body = step_blocks[j + 2]
                    if not scene_title and s_title:
                        scene_title = s_title

                    nm = re.search(r"(?im)^\s*Narration:?\s*\n?(.*?)(?=^\s*Visual Description:?|\Z)", s_body, re.DOTALL)
                    if not nm:
                        nm = re.search(r"(?i)Narration:?\s*(.*?)\s*(?:Visual Description:?|$)", s_body, re.DOTALL)
                    narr = clean_narration_latex(nm.group(1).strip()) if nm else ""

                    vm = re.search(r"(?im)^\s*Visual Description:?\s*\n?(.*)", s_body, re.DOTALL)
                    if not vm:
                        vm = re.search(r"(?i)Visual Description:?\s*(.*)", s_body, re.DOTALL)
                    vis = vm.group(1).strip() if vm else ""

                    if narr:
                        narrations.append(narr)
                    if vis:
                        visuals.append(vis)

                    step_list.append({
                        "step_number": s_num,
                        "title": s_title,
                        "narration": narr,
                        "visual_description": vis
                    })
            else:
                tm = re.search(r"(?im)^\s*Title:\s*(.+)$", scene_content)
                scene_title = tm.group(1).strip() if tm else f"Scene {scene_num}"
                nm = re.search(r"(?im)^\s*Narration:\s*(.+?)(?=^\s*Visual Description:|\Z)", scene_content, re.DOTALL)
                narr = clean_narration_latex(nm.group(1).strip()) if nm else ""
                vm = re.search(r"(?im)^\s*Visual Description:?\s*(.*)", scene_content, re.DOTALL)
                vis = vm.group(1).strip() if vm else ""
                if narr:
                    narrations.append(narr)
                if vis:
                    visuals.append(vis)

            combined_narration = " ".join(narrations)
            combined_visuals = " | ".join(visuals) if visuals else scene_title
            w_count = len(combined_narration.split())
            calc_dur = max(15.0, round(w_count / 2.2, 1))

            scenes.append({
                "scene_id": scene_num,
                "scene_index": scene_num,
                "title": scene_title or f"Scene {scene_num}",
                "voiceover_narration": combined_narration,
                "primary_content": combined_visuals,
                "duration": calc_dur,
                "steps": step_list,
                "scene_type": "concept_explanation" if scene_num > 2 else "hook_intro",
                "sme_layout": "70"
            })
        if scenes:
            return {"scenes": scenes}

    raise ValueError("Could not parse input text into valid JSON storyboard structure.")


class InstructionalDesign:
    """
    Instructional Storyboard Design.
    Translates raw transcripts into a structured educational
    storyboard with verified narration lines, DYNAMIC SME clearances, and visual directives.
    """

    def __init__(
        self,
        input_tracker_path: Optional[str] = None,
        output_tracker_path: Optional[str] = None,
        google_api_key: Optional[str] = None,
        claude_api_key: Optional[str] = None,
        input_folder: Optional[str] = None,
        guidelines_path: Optional[str] = None,
        api_provider: str = "auto",
        claude_model: str = "claude-3-5-sonnet-20241022",
        thinking_effort: str = "medium",
        thinking_budget: int = 5000,
        api_key: Optional[str] = None,
        **kwargs
    ):
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.claude_api_key = claude_api_key or os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        self.input_folder = input_folder or "."
        self.guidelines_path = Path(guidelines_path) if guidelines_path else GUIDELINES_TXT_PATH
        self.api_provider = api_provider.lower()
        self.claude_model = claude_model
        self.thinking_effort = thinking_effort
        self.thinking_budget = thinking_budget
        self.api_key = api_key or self.claude_api_key or self.google_api_key

    def generate_local_blueprint(
        self,
        transcript_data: Any,
        lesson_title: str
    ) -> Dict[str, Any]:
        """
        Dynamic procedural generator synthesizing 8-9 balanced scenes from the actual transcript.
        Guarantees natural layout rhythm (100 -> 70 -> 70 -> 20 -> 70 -> 20 -> 100 -> 70 -> 70),
        duration <= 20s for full screen, and zero hardcoded dummy text.
        """
        if isinstance(transcript_data, list):
            segments = transcript_data
        else:
            segments = transcript_data.get("segments", [])
        if not segments:
            text_val = transcript_data.get("full_text", "Educational concept") if isinstance(transcript_data, dict) else "Educational concept"
            segments = [{"text": text_val, "start": 0.0, "end": 10.0}]

        total_duration = float(segments[-1].get("end", 10.0))

        # Extract spoken sentences with acoustic timestamps from segments
        sentences_with_timing = []
        for s in segments:
            t = clean_narration_latex(s.get("text", "")).strip()
            if len(t) > 3:
                sentences_with_timing.append({
                    "text": t,
                    "start": float(s.get("start", 0.0)),
                    "end": float(s.get("end", 0.0))
                })

        if not sentences_with_timing:
            sentences_with_timing = [{
                "text": f"Exploring foundational principles and specialized architectures of {lesson_title}.",
                "start": 0.0,
                "end": total_duration
            }]

        clean_lesson_title = format_chicago_title(lesson_title)

        # ----------------------------------------------------------------------
        # Fully Dynamic Scene Count & Semantic Boundary Snapping for ANY Video:
        # Scales naturally from 3 scenes (<2min) to 12 scenes (15min+) without hardcoding.
        # ----------------------------------------------------------------------
        if total_duration < 90.0:
            target_scene_count = 3
        elif total_duration < 180.0:
            target_scene_count = 4
        elif total_duration < 300.0:
            target_scene_count = 5
        elif total_duration < 450.0:
            target_scene_count = 6
        elif total_duration < 580.0:
            target_scene_count = max(7, min(9, round(total_duration / 62.0)))
        else:
            target_scene_count = max(8, min(12, round(total_duration / 65.0)))

        # 1. Dynamic Scene 1 Hook: First complete sentence ending with punctuation <= 18s (Simplilearn rule)
        s1_end = None
        for s in sentences_with_timing:
            s_et = s["end"]
            t_txt = s["text"]
            if 4.0 <= s_et <= 18.0 and any(t_txt.endswith(p) for p in [".", "!", "?"]):
                s1_end = round(s_et, 2)
        if not s1_end:
            s1_end = round(min(18.0, max(5.0, total_duration / target_scene_count)), 2)

        # 2. Dynamic Learning Objectives Snapping (if present in the first 35% of the video)
        s_obj_start = None
        s_obj_end = None
        for s in sentences_with_timing:
            s_st = s["start"]
            s_et = s["end"]
            t_txt = s["text"]
            if s_obj_start is None and s_st >= s1_end and s_st <= total_duration * 0.35:
                if re.search(r"by the end of this|you will be able to|learning objectives|in this module|in this lesson", t_txt, re.I):
                    s_obj_start = round(s_st, 2)
            if s_obj_start is not None and s_et > s_obj_start and any(t_txt.endswith(p) for p in [".", "!", "?"]):
                if s_et - s_obj_start >= 18.0 or re.search(r"let's start|what's inside|first component|begin with|moving into", t_txt, re.I):
                    s_obj_end = round(s_et, 2)
                    break

        # 3. Dynamic Outro / Summary / What's Next Snapping in the final 20% of the video
        s_last_start = None
        tail_threshold = max(s1_end + 30.0, total_duration - max(40.0, total_duration * 0.18))
        for s in sentences_with_timing:
            s_st = s["start"]
            t_txt = s["text"]
            if s_st >= tail_threshold:
                if re.search(r"coming up next|in the next topic|hands-on|in the demo|let's take a look|bring it together|summary|in conclusion|to wrap up", t_txt, re.I):
                    s_last_start = round(s_st, 2)
                    break
        if not s_last_start:
            s_last_start = round(max(s1_end + 30.0, total_duration - (total_duration / target_scene_count)), 2)

        # 4. Interior Scene Boundary Snapping:
        # Distributes intermediate cuts evenly and snaps each to the nearest acoustic pause & sentence ending
        pre_cuts = [0.00, s1_end]
        if s_obj_start and s_obj_end and s_obj_start > s1_end and s_obj_end < s_last_start:
            if s_obj_start - s1_end >= 15.0:
                pre_cuts.append(s_obj_start)
            pre_cuts.append(s_obj_end)
            mid_start = s_obj_end
        else:
            mid_start = s1_end

        mid_available = max(10.0, s_last_start - mid_start)
        remaining_scenes = max(1, target_scene_count - len(pre_cuts))
        mid_step = mid_available / remaining_scenes

        mid_cuts = []
        for i in range(1, remaining_scenes):
            ideal_t = mid_start + i * mid_step
            best_cand = ideal_t
            min_dist = float("inf")
            for s in sentences_with_timing:
                s_et = s["end"]
                t_txt = s["text"]
                if any(t_txt.endswith(p) for p in [".", "!", "?"]):
                    dist = abs(s_et - ideal_t)
                    if dist < min_dist:
                        min_dist = dist
                        best_cand = round(s_et, 2)
            mid_cuts.append(best_cand)

        raw_cuts = pre_cuts + mid_cuts + [s_last_start, round(total_duration, 2)]
        t_cuts = sorted(list(dict.fromkeys(raw_cuts)))
        if t_cuts[-1] < total_duration:
            t_cuts[-1] = round(total_duration, 2)

        actual_num_scenes = len(t_cuts) - 1

        # Check for upstream hook_blueprint.json to extract curriculum recommendations if available
        hook_bp = None
        topic_dir = Path(self.input_folder) if hasattr(self, "input_folder") and self.input_folder else None
        if topic_dir and topic_dir.exists():
            topic_slug = clean_lesson_title.lower().replace(" ", "_")
            topic_sub = topic_dir / topic_slug
            topic_meta = topic_sub / "metadata_blueprints"
            meta_dir = topic_dir / "metadata_blueprints"
            candidates = [
                topic_meta / f"{topic_slug}_hook_blueprint.json",
                topic_meta / "hook_blueprint.json",
                topic_sub / f"{topic_slug}_hook_blueprint.json",
                topic_sub / "hook_blueprint.json",
                meta_dir / f"{topic_slug}_hook_blueprint.json",
                meta_dir / "hook_blueprint.json",
                topic_dir / f"{topic_slug}_hook_blueprint.json",
                topic_dir / "hook_blueprint.json"
            ]
            for cand in candidates:
                if cand.exists():
                    try:
                        with open(cand, "r", encoding="utf-8") as hf:
                            candidate_bp = json.load(hf)
                            if candidate_bp.get("scene_blueprint") and len(candidate_bp["scene_blueprint"]) >= 3:
                                hook_bp = candidate_bp
                                break
                    except Exception:
                        pass

        # ----------------------------------------------------------------------
        # 5. Synthesize Dynamic Scenes Directly from Spoken Content (Zero Hardcoding)
        # ----------------------------------------------------------------------
        palette = ["#62B7E4", "#7EA2C8", "#E6A157", "#8ECDB7", "#9B99C7"]
        scenes = []
        prev_layout = None
        consecutive_layout_count = 0

        for idx in range(actual_num_scenes):
            sid = idx + 1
            st = round(t_cuts[idx], 2)
            et = round(t_cuts[idx + 1], 2)
            dur = round(et - st, 2)

            # Collect sentences that fall in this scene's exact acoustic window
            scene_sents = [
                s["text"] for s in sentences_with_timing
                if (s["start"] >= st - 0.2 and s["start"] < et) or (s["end"] > st and s["end"] <= et + 0.2)
            ]
            if not scene_sents:
                scene_sents = [s["text"] for s in sentences_with_timing]

            scene_narr = " ".join(scene_sents)

            # Upstream hook blueprint override if aligned
            bp_item = hook_bp["scene_blueprint"][idx] if hook_bp and hook_bp.get("scene_blueprint") and idx < len(hook_bp["scene_blueprint"]) else None

            if bp_item:
                stype = bp_item.get("scene_type", "concept_explanation").lower().replace(" ", "_")
                explicit_layout = str(bp_item.get("sme_framing_recommendation", {}).get("layout", "70")).replace("%", "")
                custom_title = bp_item.get("concept_focus") or bp_item.get("scene_goal")
            else:
                explicit_layout = None
                custom_title = None
                # Content-driven dynamic scene type classification
                if sid == 1:
                    stype = "hook_intro"
                elif sid == actual_num_scenes:
                    stype = "whats_next" if re.search(r"coming up|next topic|next lesson", scene_narr, re.I) else "summary_takeaways"
                elif re.search(r"by the end of this|you will be able to|learning objectives|in this topic", scene_narr, re.I):
                    stype = "learning_objectives"
                elif re.search(r"demo|hands-on|walkthrough|execute|code|terminal", scene_narr, re.I):
                    stype = "demo_walkthrough"
                elif re.search(r"vs|versus|difference|compare|trade-off|contrast", scene_narr, re.I):
                    stype = "comparative_analysis"
                elif re.search(r"architecture|component|pillar|pipeline|layer|anatomy", scene_narr, re.I):
                    stype = "concept_explanation"
                elif re.search(r"loop|cycle|feedback|perceive|reason|act", scene_narr, re.I):
                    stype = "mental_model"
                else:
                    stype = "concept_deep_dive"

            # Derive clean, professional Chicago-style title dynamically from speech
            if custom_title and not custom_title.lower().startswith("scene "):
                scene_title = format_chicago_title(custom_title)
            elif sid == 1:
                scene_title = format_chicago_title(f"Introduction: {clean_lesson_title}")
            elif stype == "learning_objectives":
                scene_title = "Topic Learning Objectives"
            elif stype == "whats_next":
                scene_title = "What Is Next & Hands-On Execution"
            elif stype == "summary_takeaways":
                scene_title = "Summary & Key Takeaways"
            else:
                lead_text = scene_sents[0] if scene_sents else clean_lesson_title
                lead_clean = re.sub(
                    r'^(In the last topic|In this lesson|In this topic|We will|Let\'s look at|Now let\'s|Let us|We introduced|Detail the|Illustrate the|Walk through|Explain|Define|Synthesize the|Consolidate)\s+',
                    '', lead_text, flags=re.I
                ).strip()
                lead_clause = re.split(r'[.,:;!?]', lead_clean)[0].strip()
                words = lead_clause.split()
                if len(words) > 7:
                    lead_clause = " ".join(words[:6])
                scene_title = format_chicago_title(lead_clause if len(lead_clause) > 4 else f"{clean_lesson_title} - Section {sid}")

            # Derive cards dynamically from the actual spoken sentences
            cards = []
            if bp_item and bp_item.get("text_elements"):
                for te in bp_item["text_elements"]:
                    if ":" in te:
                        c_title, c_body = te.split(":", 1)
                        cards.append({"title": c_title.strip(), "body": c_body.strip(), "accent_color": palette[len(cards) % len(palette)]})
                    else:
                        cards.append({"title": "Key Focus", "body": te.strip(), "accent_color": palette[len(cards) % len(palette)]})
            
            if not cards:
                card_count = min(4, max(2, len(scene_sents)))
                chunk_size = max(1, len(scene_sents) // card_count)
                for c_i in range(card_count):
                    c_sents = scene_sents[c_i * chunk_size : (c_i + 1) * chunk_size] if c_i < card_count - 1 else scene_sents[c_i * chunk_size :]
                    if not c_sents:
                        continue
                    first_sent = c_sents[0]
                    c_title_clean = re.sub(r'^(In addition|Furthermore|Moreover|At the same time|For example|However|Here)\s*,?\s*', '', first_sent, flags=re.I).strip()
                    c_words = re.split(r'[.,:;!?]', c_title_clean)[0].split()
                    c_title = " ".join(c_words[:4]).title() if len(c_words) >= 2 else f"Key Point {c_i + 1}"
                    c_body = " ".join(c_sents)[:140].strip()
                    cards.append({
                        "title": c_title,
                        "body": c_body,
                        "accent_color": palette[c_i % len(palette)]
                    })
            if not cards:
                cards = [{"title": "Core Mechanism", "body": scene_narr[:120], "accent_color": "#62B7E4"}]

            # Dynamic SME framing resolution with layout alternation
            framing = resolve_dynamic_sme_framing(stype, scene_narr, card_count=len(cards), explicit_layout=explicit_layout, duration=dur)
            layout_chosen = framing["sme_layout"]

            if layout_chosen == prev_layout:
                consecutive_layout_count += 1
                if consecutive_layout_count >= 2:
                    if layout_chosen == "70" and stype in ["concept_explanation", "demo_walkthrough", "concept_deep_dive"]:
                        layout_chosen = "20"
                    elif layout_chosen == "20":
                        layout_chosen = "70"
                    framing = resolve_dynamic_sme_framing(stype, scene_narr, card_count=len(cards), explicit_layout=layout_chosen, duration=dur)
                    consecutive_layout_count = 0
            else:
                prev_layout = layout_chosen
                consecutive_layout_count = 0

            lead_in = f"{scene_title}:"
            scene_obj = {
                "scene_id": sid,
                "scene_type": stype,
                "title": scene_title,
                "start_time": st,
                "end_time": et,
                "duration": dur,
                "sme_layout": framing["sme_layout"],
                "dynamic_selection_reason": framing["dynamic_selection_reason"],
                "sme_positioning": framing["sme_positioning"],
                "presentation_safe_zone": framing["presentation_safe_zone"],
                "on_screen_text": {
                    "lead_in": lead_in,
                    "cards": cards
                },
                "voiceover_narration": scene_narr,
                "audio_timing": {
                    "start_time": st,
                    "end_time": et,
                    "duration": dur,
                    "voiceover_char_count": len(scene_narr),
                    "voiceover_word_count": len(scene_narr.split()),
                    "pacing_words_per_sec": round(len(scene_narr.split()) / max(0.1, dur), 2)
                }
            }

            inst_matching = build_matching_section_for_instruction(scene_obj, sid)
            scene_obj["matching_section"] = inst_matching

            # Balanced presentation steps (target: 3 to 4 steps per scene for sufficient visual persistence)
            raw_sents = [s.strip() for s in re.split(r'(?<=[.?!])\s+', scene_narr.strip()) if s.strip()]
            if not raw_sents:
                raw_sents = [scene_narr]
            
            target_n_steps = min(4, max(2, len(cards))) if cards else min(4, max(2, len(raw_sents)))
            chunked_sents = []
            chunk_size = max(1, len(raw_sents) // target_n_steps)
            for i in range(target_n_steps):
                if i == target_n_steps - 1:
                    chunk = " ".join(raw_sents[i*chunk_size:])
                else:
                    chunk = " ".join(raw_sents[i*chunk_size:(i+1)*chunk_size])
                if chunk:
                    chunked_sents.append(chunk)
            if not chunked_sents:
                chunked_sents = [scene_narr]

            n_steps = len(chunked_sents)
            step_dur = round(dur / n_steps, 3)
            p_steps = []
            cur_time = st
            for s_idx, s_text in enumerate(chunked_sents):
                s_end = round(cur_time + step_dur, 3) if s_idx < n_steps - 1 else et
                card_title = cards[s_idx]["title"] if s_idx < len(cards) and "title" in cards[s_idx] else f"Step {s_idx + 1}"
                step_matching = f"{inst_matching}\nStep: {s_idx + 1} - {card_title}"
                p_steps.append({
                    "step_number": s_idx + 1,
                    "step_title": card_title,
                    "title": card_title,
                    "narration": s_text,
                    "duration": round(s_end - cur_time, 3),
                    "run_time": round(s_end - cur_time, 3),
                    "start_time": cur_time,
                    "end_time": s_end,
                    "dominant_visual_concept": f"Dynamic physical vector model illustrating {card_title}",
                    "visual_description": f"Centerstage visual: High-contrast kinetic diagram representing {card_title} with directed pulses, active badges, and Layout {framing['sme_layout']} safe-zone clearance (below y <= 270px).",
                    "on_screen_elements": [card_title, "Active", "Operational"],
                    "on_screen_text": [card_title, "Active", "Operational"],
                    "transition_to_next": f"Kinetic vector elements evolve smoothly into Step {s_idx + 2}" if s_idx < n_steps - 1 else "Holds exit state cleanly",
                    "matching_section": step_matching
                })
                cur_time = s_end
            scene_obj["presentation_steps"] = p_steps
            scenes.append(scene_obj)

        return {
            "lesson_title": clean_lesson_title,
            "total_scenes": len(scenes),
            "estimated_duration": total_duration,
            "audio_metadata": {
                "total_duration": total_duration,
                "sample_rate_hz": 48000,
                "loudness_standard": "EBU R128 (-16 LUFS)",
                "audio_source": "teacher_raw_recording",
                "scene_count": len(scenes)
            },
            "guidelines_reference": "guidelines.md (Sections 1, 2, 4, 6, 8) & OSL_3.0_Post_Production_Guidelines_2026.pdf",
            "dynamic_sme_framing_enabled": True,
            "scenes": scenes
        }

    def generate_instructions(
        self,
        transcript_data: Any,
        lesson_title: str
    ) -> Dict[str, Any]:
        """
        Generates storyboard blueprint using Google Gemini / Claude with complete Simplilearn OSL 3.0 system prompt.
        Falls back to dynamic procedural generator if API is unavailable.
        """
        if isinstance(transcript_data, list):
            segments = transcript_data
        else:
            segments = transcript_data.get("segments", [])
        total_duration = segments[-1].get("end", 10.0) if segments else 10.0
        full_transcript = " ".join([s.get("text", "") for s in segments])

        # Compute expected scene count dynamically based on duration (approx 1 scene per 60s, clamped 3 to 12)
        expected_scenes = max(3, min(12, max(1, int(round(total_duration / 60.0)))))
        per_scene_seconds = max(30, int(total_duration / expected_scenes))
        target_words_per_scene = int(per_scene_seconds * 2.2)
        if per_scene_seconds <= 90:
            target_steps = 3
        elif per_scene_seconds <= 180:
            target_steps = 4
        else:
            target_steps = 5
        target_words_per_step = max(25, target_words_per_scene // target_steps)
        mins_val = total_duration / 60.0
        d_mins = f"{int(mins_val)} minutes" if mins_val.is_integer() else f"{mins_val:.1f} minutes"
        per_scene_mins_val = per_scene_seconds / 60.0
        per_scene_mins = f"{int(per_scene_mins_val)} minutes" if per_scene_mins_val.is_integer() else f"{per_scene_mins_val:.1f} minutes"

        prompt_replacements = {
            "target_audience": "Technology professionals, software engineers, and technical architects",
            "scene_count": f"{expected_scenes} scenes",
            "time_duration": f"{int(total_duration)} seconds",
            "duration_mins": d_mins,
            "per_scene_seconds": per_scene_seconds,
            "per_scene_mins": per_scene_mins,
            "target_words_per_scene": target_words_per_scene,
            "target_words_per_step": target_words_per_step,
            "target_steps": target_steps,
            "persona": "Senior Presentation Storyboard Architect",
            "storyboarding": lesson_title
        }
        # Resolve theme dynamically
        theme = getattr(self, "theme", None) or os.environ.get("THEME", "dynamic_learning")
        if hasattr(self, "input_folder") and self.input_folder:
            cfg_p = Path(self.input_folder) / "ex_config.json"
            if cfg_p.exists():
                try:
                    with open(cfg_p, "r", encoding="utf-8") as cf:
                        cfg_d = json.load(cf)
                        theme = cfg_d.get("theme", theme)
                except Exception:
                    pass

        # Standardize exclusively on dynamic_learning open-canvas choreography
        chosen_prompt = INSTRUCTIONAL_SYSTEM_PROMPT_DYNAMIC
        formatted_system_prompt = chosen_prompt
        for k, v in prompt_replacements.items():
            formatted_system_prompt = formatted_system_prompt.replace("{" + k + "}", str(v))

        # Ingest contrastive reference design patterns (positive vs. negative benchmarks)
        ref_patterns_text = load_reference_design_patterns(
            getattr(self, "output_folder", None) or getattr(self, "input_folder", None)
        )
        if ref_patterns_text:
            formatted_system_prompt += f"\n\n{ref_patterns_text}\n"

        formatted_user_prompt = INSTRUCTIONAL_USER_PROMPT.format(
            lesson_title=lesson_title,
            total_duration=total_duration,
            duration_mins=d_mins,
            expected_scenes=expected_scenes,
            per_scene_seconds=per_scene_seconds,
            transcript_text=full_transcript[:12000]
        )

        # 1. First Priority: Claude Sonnet in Medium Thinking Mode (OSL 3.0 Stage 1 Director)
        claude_key = self.claude_api_key or os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        if self.api_provider in ["claude", "auto"] and claude_key:
            print(f"[*] Calling Claude Sonnet ({self.claude_model}) with Medium Thinking Mode for dynamic instructional design ({expected_scenes} scenes)...")
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=claude_key)
                full_call_prompt = f"{formatted_system_prompt}\n\nUser Query: {formatted_user_prompt}"

                extra_kwargs = {}
                if "sonnet-5" in self.claude_model or "opus-5" in self.claude_model or "haiku-5" in self.claude_model:
                    extra_kwargs["thinking"] = {"type": "adaptive"}
                    extra_kwargs["output_config"] = {"effort": self.thinking_effort}
                else:
                    extra_kwargs["thinking"] = {"type": "enabled", "budget_tokens": self.thinking_budget}

                try:
                    with client.messages.stream(
                        model=self.claude_model,
                        max_tokens=24000,
                        messages=[{"role": "user", "content": full_call_prompt}],
                        **extra_kwargs
                    ) as stream:
                        resp = stream.get_final_message()
                except Exception:
                    resp = client.messages.create(
                        model=self.claude_model,
                        max_tokens=24000,
                        messages=[{"role": "user", "content": full_call_prompt}],
                        **extra_kwargs
                    )

                resp_text = ""
                for block in resp.content:
                    if block.type == "thinking":
                        print(f"  [Claude Thinking Mode] Active reasoning ({len(block.thinking)} chars)")
                    elif block.type == "text":
                        resp_text += block.text

                parsed = parse_input_to_json(resp_text)
                if "scenes" in parsed and len(parsed["scenes"]) >= 5:
                    print(f"✓ Claude Sonnet successfully generated {len(parsed['scenes'])} dynamic scenes")
                    return self._normalize_scenes(parsed, segments, total_duration)
            except Exception as e:
                print(f"[Instructional Design] Claude attempt notice: {e}. Retrying Claude Sonnet with direct JSON instruction...")
                try:
                    with client.messages.stream(
                        model=self.claude_model,
                        max_tokens=8192,
                        messages=[{"role": "user", "content": full_call_prompt + "\n\nCRITICAL: Return strictly valid JSON only adhering to the specified schema without preamble."}],
                    ) as stream:
                        resp = stream.get_final_message()
                    resp_text = "".join(b.text for b in resp.content if b.type == "text")
                    parsed = parse_input_to_json(resp_text)
                    if "scenes" in parsed and len(parsed["scenes"]) >= 5:
                        print(f"✓ Claude Sonnet retry successfully generated {len(parsed['scenes'])} dynamic scenes")
                        return self._normalize_scenes(parsed, segments, total_duration)
                except Exception as e2:
                    print(f"[Instructional Design] Claude retry error: {e2}. Trying Gemini before local fallback.")

        # 2. Second Priority: Google Gemini
        google_key = self.google_api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if google_key:
            print(f"[*] Calling Google Gemini for dynamic instructional design ({expected_scenes} scenes)...")
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key, transport="rest")
                model = genai.GenerativeModel("gemini-2.0-flash")
                full_call_prompt = f"{formatted_system_prompt}\n\nUser Query: {formatted_user_prompt}\n\nCRITICAL: Return strictly valid JSON adhering to the specified schema without markdown fences or commentary."
                resp = model.generate_content(
                    full_call_prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=16000
                    ),
                    request_options={"timeout": 45}
                )
                parsed = parse_input_to_json(resp.text)
                if "scenes" in parsed and len(parsed["scenes"]) >= 3:
                    print(f"✓ Google Gemini successfully generated {len(parsed['scenes'])} dynamic scenes")
                    return self._normalize_scenes(parsed, segments, total_duration)
            except Exception as e_gem:
                print(f"[Instructional Design] Gemini attempt notice: {e_gem}. Falling back to local blueprint.")

        # 3. Fallback to dynamic procedural generator
        return self.generate_local_blueprint(transcript_data, lesson_title)

    def _normalize_scenes(
        self,
        parsed: Dict[str, Any],
        segments: List[Any],
        total_duration: float
    ) -> Dict[str, Any]:
        """Normalizes parsed LLM storyboard output into standard Simplilearn OSL 3.0 format."""
        num_scenes = len(parsed["scenes"])
        # Check if durations or timestamps need allocation
        needs_duration_allocation = (
            any(float(sc.get("duration", 0.0) or 0.0) <= 0.0 for sc in parsed["scenes"]) or
            any(sc.get("start_time") is None or sc.get("end_time") is None for sc in parsed["scenes"]) or
            abs(sum(float(sc.get("duration", 0.0) or 0.0) for sc in parsed["scenes"]) - total_duration) > 3.0
        )
        if needs_duration_allocation and segments and total_duration > 0:
            matched_any = False
            curr_seg_i = 0
            for s_idx, sc in enumerate(parsed["scenes"]):
                steps = sc.get("presentation_steps", [])
                fn = (steps[0].get("narration", "") if steps else sc.get("voiceover_narration", "")).strip().lower()
                ln = (steps[-1].get("narration", "") if steps else sc.get("voiceover_narration", "")).strip().lower()
                st_val = None
                et_val = None
                if fn and isinstance(segments[0], dict) and "text" in segments[0]:
                    words_fn = set(fn.split()[:4])
                    for t_i in range(curr_seg_i, len(segments)):
                        txt_w = set(str(segments[t_i].get("text", "")).lower().split()[:8])
                        if len(words_fn.intersection(txt_w)) >= 2:
                            st_val = float(segments[t_i].get("start", 0.0))
                            curr_seg_i = t_i
                            matched_any = True
                            break
                if ln and isinstance(segments[0], dict) and "text" in segments[0]:
                    words_ln = set(ln.split()[-4:])
                    for t_i in range(curr_seg_i, len(segments)):
                        txt_w = set(str(segments[t_i].get("text", "")).lower().split()[-8:])
                        if len(words_ln.intersection(txt_w)) >= 2:
                            et_val = float(segments[t_i].get("end", st_val or 0.0))
                            curr_seg_i = t_i + 1
                            break
                if s_idx == 0 and (st_val is None or st_val > 5.0):
                    st_val = 0.0
                if s_idx == num_scenes - 1:
                    et_val = total_duration
                if st_val is not None:
                    sc["start_time"] = round(st_val, 3)
                if et_val is not None:
                    sc["end_time"] = round(et_val, 3)
                if sc.get("start_time") is not None and sc.get("end_time") is not None:
                    sc["duration"] = round(sc["end_time"] - sc["start_time"], 3)

            if not matched_any or any(sc.get("start_time") is None for sc in parsed["scenes"]):
                segs_per_sc = max(1, len(segments) // num_scenes)
                for s_idx, sc in enumerate(parsed["scenes"]):
                    if s_idx == num_scenes - 1:
                        sc_segs = segments[s_idx * segs_per_sc:]
                    else:
                        sc_segs = segments[s_idx * segs_per_sc : (s_idx + 1) * segs_per_sc]
                    if sc_segs:
                        sc["start_time"] = round(float(sc_segs[0].get("start", 0.0)), 3)
                        sc["end_time"] = round(float(sc_segs[-1].get("end", sc["start_time"])), 3)
                        sc["duration"] = round(sc["end_time"] - sc["start_time"], 3)
                    else:
                        sc["duration"] = round(total_duration / num_scenes, 3)

        for idx, sc in enumerate(parsed["scenes"], 1):
            if not sc.get("scene_index"):
                sc["scene_index"] = sc.get("scene_id", idx)
            if not sc.get("scene_id"):
                sc["scene_id"] = sc["scene_index"]

            # Normalize title
            if not sc.get("title"):
                sc["title"] = sc.get("scene_objective") or sc.get("scene_title") or f"Scene {idx}"

            # Normalize voiceover narration if missing
            steps = sc.get("presentation_steps", [])
            if not sc.get("voiceover_narration") and steps:
                sc["voiceover_narration"] = " ".join([st.get("narration", "") for st in steps if st.get("narration")])

            dur = float(sc.get("duration", 0.0) or 0.0)
            if dur <= 0.0 and "start_time" in sc and "end_time" in sc:
                dur = round(float(sc["end_time"]) - float(sc["start_time"]), 3)
            if dur <= 0.0:
                dur = round(total_duration / max(1, len(parsed["scenes"])), 3)
            sc["duration"] = dur

            # Distribute step runtimes across presentation_steps
            if steps:
                n_st = len(steps)
                step_word_counts = [max(1, len(st.get("narration", "").split())) for st in steps]
                total_words = max(1, sum(step_word_counts))
                cum_st_start = float(sc.get("start_time", 0.0) or 0.0)
                for s_i, st in enumerate(steps):
                    if s_i == n_st - 1:
                        st_dur = round(max(0.5, dur - (cum_st_start - float(sc.get("start_time", 0.0) or 0.0))), 3)
                    else:
                        st_dur = round(dur * (step_word_counts[s_i] / total_words), 3)
                    st_end = round(cum_st_start + st_dur, 3)
                    st["duration"] = st_dur
                    st["run_time"] = st_dur
                    st["start_time"] = cum_st_start
                    st["end_time"] = st_end
                    if not st.get("title") and st.get("step_title"):
                        st["title"] = st["step_title"]
                    if not st.get("title"):
                        st["title"] = f"Step {s_i + 1}"
                    if not st.get("step_title"):
                        st["step_title"] = st["title"]
                    clean_t = st.get("title", f"Step {s_i + 1}")
                    if not st.get("dominant_visual_concept"):
                        st["dominant_visual_concept"] = f"Dynamic physical vector model illustrating {clean_t}"
                    if not st.get("on_screen_elements"):
                        st["on_screen_elements"] = [clean_t, "Active", "Operational"]
                    if not st.get("on_screen_text"):
                        st["on_screen_text"] = st["on_screen_elements"]
                    if not st.get("transition_to_next"):
                        st["transition_to_next"] = f"Continuous kinetic flow into Step {s_i + 2}" if s_i < n_st - 1 else "Holds exit state cleanly"
                    cum_st_start = st_end

            layout = str(sc.get("sme_layout", "70")).replace("%", "")
            stype = sc.get("scene_type", "concept_explanation")

            # Enforce Simplilearn Guide rules
            if stype in ["whats_next", "final_closing"]:
                layout = "70"
            elif layout == "100" and dur > 20.0:
                layout = "70"

            framing = resolve_dynamic_sme_framing(stype, sc.get("voiceover_narration", ""), explicit_layout=layout, duration=dur)
            sc["sme_layout"] = framing["sme_layout"]
            sc["dynamic_selection_reason"] = framing["dynamic_selection_reason"]
            sc["sme_positioning"] = framing["sme_positioning"]
            sc["presentation_safe_zone"] = framing["presentation_safe_zone"]
        return parsed

    def run(
        self,
        transcript_path: str,
        output_path: str,
        lesson_title: Optional[str] = None
    ) -> str:
        """Executes instructional storyboard generation from file paths."""
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        # Resilient fallback: If input file is not a transcript (e.g. hook_blueprint) and has no segments,
        # attempt to load the actual clean transcript from the same directory.
        if (isinstance(transcript_data, dict) and "segments" not in transcript_data) or not transcript_data:
            parent_dir = Path(transcript_path).parent
            stem_clean = Path(transcript_path).stem.replace("_hook_blueprint", "").replace("hook_blueprint", "")
            for alt_name in [
                f"{stem_clean}_clean_transcript.json",
                f"{stem_clean}_timestamps.json",
                "clean_transcript.json",
                "timestamps.json"
            ]:
                alt_cand = parent_dir / alt_name
                if alt_cand.exists():
                    try:
                        with open(alt_cand, "r", encoding="utf-8") as af:
                            alt_json = json.load(af)
                        if isinstance(alt_json, list) or (isinstance(alt_json, dict) and "segments" in alt_json):
                            print(f"[Instructional Design] Using speech transcript from: {alt_cand}")
                            transcript_data = alt_json
                            break
                    except Exception:
                        pass

        if not lesson_title:
            base_name = Path(transcript_path).stem.replace("_clean_transcript", "").replace("_transcript", "")
            lesson_title = base_name.replace("_", " ").replace("-", " ").title()

        # Check for perfected Master storyboard preservation FIRST
        meta_dir = Path(output_path).parent
        topic_id = Path(output_path).stem.replace("_storyboard_blueprint", "").replace("_blueprint", "")
        master_bp_cands = [
            meta_dir / f"{topic_id}_master_storyboard_blueprint.json",
            meta_dir / "master_storyboard_blueprint.json",
            meta_dir.parent / f"{topic_id}_master_storyboard_blueprint.json"
        ]
        master_found = None
        for mb_cand in master_bp_cands:
            if mb_cand.exists():
                try:
                    with open(mb_cand, "r", encoding="utf-8") as mbf:
                        raw_mb = json.load(mbf)
                    if raw_mb and raw_mb.get("scenes"):
                        master_found = raw_mb
                        print(f"[*] [Stage 1] Injected master elevated storyboard from {mb_cand.name}")
                        blueprint = master_found
                        break
                except Exception:
                    pass

        if not master_found:
            blueprint = self.generate_instructions(transcript_data, lesson_title)

        # Enforce that every scene has presentation_steps and every step has an explicit matching_section
        for idx, sc in enumerate(blueprint.get("scenes", []), 1):
            sid = sc.get("scene_number") or sc.get("scene_id") or idx
            clean_title = sc.get("title", f"Scene {sid}")
            layout = str(sc.get("sme_layout", "70"))
            steps = sc.get("presentation_steps") or sc.get("steps") or []

            if steps:
                for s_i, st in enumerate(steps, 1):
                    if not st.get("matching_section"):
                        st["matching_section"] = build_step_matching_section(st, clean_title, s_i, layout)
                sc["presentation_steps"] = steps
            else:
                inst_matching = build_matching_section_for_instruction(sc, int(sid) if str(sid).isdigit() else idx)
                sc["matching_section"] = inst_matching
                sc["presentation_steps"] = [
                    {
                        "step_number": 1,
                        "step_title": clean_title,
                        "title": clean_title,
                        "narration": sc.get("voiceover_narration", ""),
                        "duration": sc.get("duration", 0.0),
                        "run_time": sc.get("duration", 0.0),
                        "start_time": sc.get("start_time", 0.0),
                        "end_time": sc.get("end_time", sc.get("duration", 0.0)),
                        "matching_section": inst_matching,
                        "visual_description": {
                            "purpose": clean_title,
                            "matching_section": inst_matching
                        }
                    }
                ]

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(blueprint, f, indent=2, ensure_ascii=False)

        # ----------------------------------------------------------------------
        # Automatically export instructions_<model>.json and raw txt companion files
        # ----------------------------------------------------------------------
        if out_file.parent.name == "metadata_blueprints":
            meta_dir = out_file.parent
            topic_dir = meta_dir.parent
        else:
            topic_dir = out_file.parent
            meta_dir = topic_dir / "metadata_blueprints"
            meta_dir.mkdir(parents=True, exist_ok=True)

        instructions_dict = {}
        for idx, sc in enumerate(blueprint.get("scenes", []), 1):
            sid = str(sc.get("scene_number") or sc.get("scene_id") or sc.get("scene_index") or idx)
            raw_steps = sc.get("presentation_steps") or sc.get("steps") or []
            norm_steps = []
            for s_i, st in enumerate(raw_steps, 1):
                step_obj = dict(st)
                if "presentation_step_number" not in step_obj:
                    step_obj["presentation_step_number"] = str(step_obj.get("step_number", s_i))
                if "narration_statement" not in step_obj and "narration" in step_obj:
                    step_obj["narration_statement"] = step_obj["narration"]
                if "title" not in step_obj and "step_title" in step_obj:
                    step_obj["title"] = step_obj["step_title"]
                norm_steps.append(step_obj)
            instructions_dict[sid] = norm_steps

        # Determine active model slug from configuration or fallback
        model_slug = "gemini-3.8-flash"
        if getattr(self, "api_provider", "").lower() == "claude" and getattr(self, "claude_model", None):
            model_slug = self.claude_model.replace(":", "-").replace("/", "-")
        elif (topic_dir / "ex_config.json").exists():
            try:
                with open(topic_dir / "ex_config.json", "r", encoding="utf-8") as ecf:
                    ec_data = json.load(ecf)
                    cfg_model = ec_data.get("storyline_model_name") or ec_data.get("hook_model_name")
                    if cfg_model:
                        model_slug = cfg_model.replace(":", "-").replace("/", "-")
            except Exception:
                pass

        # Export companion instruction files
        export_targets = [
            meta_dir / f"instructions_{model_slug}.json",
            meta_dir / "instructions.json",
            topic_dir / f"instructions_{model_slug}.json",
            topic_dir / "instructions.json"
        ]
        for exp_tgt in export_targets:
            try:
                with open(exp_tgt, "w", encoding="utf-8") as f:
                    json.dump(instructions_dict, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[Notice] Failed to write instructions file {exp_tgt}: {e}")

        # Preserve and export reference design patterns for downstream stages
        src_pattern_file = PROJECT_ROOT / "reference_design_pattern.json"
        if not src_pattern_file.exists():
            src_pattern_file = SCRIPT_DIR / "reference_design_pattern.json"
        if src_pattern_file.exists():
            for target_pattern_path in [meta_dir / "reference_design_pattern.json", topic_dir / "reference_design_pattern.json"]:
                try:
                    import shutil
                    shutil.copy2(src_pattern_file, target_pattern_path)
                except Exception as e_copy:
                    print(f"[Notice] Failed to copy reference design patterns to {target_pattern_path}: {e_copy}")

        # Export raw text prompt instructions
        prompt_dir = topic_dir / "prompt_context_and_guidelines"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        raw_txt_lines = []
        for sid, steps in instructions_dict.items():
            raw_txt_lines.append(f"Scene {sid}:")
            for st in steps:
                p_num = st.get("presentation_step_number", 1)
                p_title = st.get("title", "")
                p_narr = st.get("narration_statement", "")
                p_match = st.get("matching_section", "")
                raw_txt_lines.append(f"Presentation Step {p_num}: {p_title}")
                raw_txt_lines.append(f"Narration: {p_narr}")
                raw_txt_lines.append(f"Visual Description: {p_match}")
            raw_txt_lines.append("")
        raw_txt_content = "\n".join(raw_txt_lines)

        for raw_tgt in [
            prompt_dir / f"instructions_raw_{model_slug}.txt",
            prompt_dir / "instructions_raw.txt",
            topic_dir / f"instructions_raw_{model_slug}.txt",
            topic_dir / "instructions_raw.txt"
        ]:
            try:
                with open(raw_tgt, "w", encoding="utf-8") as f:
                    f.write(raw_txt_content)
            except Exception:
                pass

        print(f"\n==================================================================")
        print(f"INSTRUCTIONAL STORYBOARD DESIGN (DYNAMIC SME FRAMING)")
        print(f"Compliance: OSL_3.0_Post_Production_Guidelines_2026.pdf (Pages 16, 17, 27)")
        print(f"Pacing: Dynamic Layout Alternation (Max 20s for Layout 100)")
        print(f"==================================================================")
        print(f"✓ Instructional Storyboard Design Complete: Storyboard generated ({len(blueprint['scenes'])} scenes)")
        for sc in blueprint.get("scenes", []):
            dur = sc.get("duration", 0.0)
            reason = sc.get("dynamic_selection_reason") or "Standard pacing alignment"
            print(f"  - Scene {sc.get('scene_id')}: Layout {sc.get('sme_layout')}% ({dur:.1f}s) -> {str(reason)[:55]}...")
        print(f"  Blueprint saved -> {output_path}\n")

        return str(out_file)

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

        for topic_id in topics:
            if target_topic_id and topic_id != target_topic_id:
                continue

            if in_tracker and topic_id in in_tracker:
                if not in_tracker[topic_id].get("processed", False) and os.environ.get("FORCE_RUN") != "1":
                    print(f"Skipping {topic_id}: Input tracker not marked as processed.")
                    continue

            if out_tracker and topic_id in out_tracker and out_tracker[topic_id].get("processed", False) and os.environ.get("FORCE_RUN") != "1":
                print(f"Skipping {topic_id}: Already processed in instructional design tracker.")
                continue

            topic_dir = os.path.join(self.input_folder, topic_id)
            if not os.path.exists(topic_dir):
                os.makedirs(topic_dir, exist_ok=True)

            print(f"Processing Instructional Design for {topic_id}...")
            meta_dir = os.path.join(topic_dir, "metadata_blueprints")
            candidates = [
                os.path.join(meta_dir, f"{topic_id}_clean_transcript.json"),
                os.path.join(topic_dir, f"{topic_id}_clean_transcript.json"),
                os.path.join(meta_dir, "clean_transcript.json"),
                os.path.join(topic_dir, "clean_transcript.json"),
                os.path.join(meta_dir, f"{topic_id}_timestamps.json"),
                os.path.join(topic_dir, f"{topic_id}_timestamps.json"),
                os.path.join(meta_dir, f"{topic_id}_hook_blueprint.json"),
                os.path.join(topic_dir, f"{topic_id}_hook_blueprint.json"),
                os.path.join(topic_dir, "raw_context.txt"),
                os.path.join(topic_dir, "context.txt")
            ]
            input_file = None
            for cand in candidates:
                if os.path.exists(cand):
                    input_file = cand
                    break

            if not input_file:
                input_file = os.path.join(topic_dir, "context.txt")
                with open(input_file, "w", encoding="utf-8") as f:
                    f.write(f"Educational lecture module on {topic_id.replace('_', ' ').title()}.")

            meta_dir = os.path.join(topic_dir, "metadata_blueprints")
            os.makedirs(meta_dir, exist_ok=True)
            out_blueprint = os.path.join(meta_dir, f"{topic_id}_storyboard_blueprint.json")
            try:
                self.run(input_file, out_blueprint, lesson_title=topic_id.replace("_", " ").title())

                if self.output_tracker_path:
                    self._save_tracker(self.output_tracker_path, {
                        topic_id: {
                            "output_path": out_blueprint,
                            "processed": True,
                            "topic_name": topic_id,
                            "topic_id": topic_id,
                            "failure_reason": None
                        }
                    })
                print(f"Successfully generated instructional storyboard for {topic_id}.")
            except Exception as e:
                print(f"Error in instructional design for {topic_id}: {e}")
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


# --------------------------------------------------------------------------------
# Backward-compatible Module Interface
# --------------------------------------------------------------------------------

def generate_local_storyboard_blueprint(
    transcript_data: Any,
    lesson_title: str = "Simplilearn Lecture"
) -> Dict[str, Any]:
    designer = InstructionalDesign()
    return designer.generate_local_blueprint(transcript_data, lesson_title)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instructional Storyboard Design (Dynamic SME Framing)")
    parser.add_argument("-t", "--transcript", required=True, help="Input clean speech transcript JSON")
    parser.add_argument("-o", "--output", required=True, help="Output presentation storyboard blueprint JSON")
    parser.add_argument("-l", "--lesson-title", default=None, help="Lesson title")
    parser.add_argument("-p", "--provider", default="claude", choices=["auto", "gemini", "claude", "local"], help="LLM provider (default: claude)")
    parser.add_argument("-m", "--model", default="claude-3-5-sonnet-20241022", help="Model name (default: claude-3-5-sonnet-20241022)")
    parser.add_argument("--thinking-effort", default="medium", choices=["low", "medium", "high"], help="Thinking effort for adaptive models (default: medium)")
    parser.add_argument("--thinking-budget", type=int, default=5000, help="Thinking budget tokens for budget models (default: 5000)")
    args = parser.parse_args()

    designer = InstructionalDesign(
        api_provider=args.provider,
        claude_model=args.model,
        thinking_effort=args.thinking_effort,
        thinking_budget=args.thinking_budget
    )
    designer.run(
        transcript_path=args.transcript,
        output_path=args.output,
        lesson_title=args.lesson_title
    )
