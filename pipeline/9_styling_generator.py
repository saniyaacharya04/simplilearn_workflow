#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 9: STYLING GENERATOR
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 9
   - Script Name: 9_styling_generator.py
   - Primary Class: StylingGenerator
   - Pipeline Role:
     Injects comprehensive design system tokens, typography scales, high-contrast color
     palettes, and container styles into the Scene Animation Guidelines without altering
     structural geometry. Strictly enforces Simplilearn OSL 3.0 design compliance:
     10-color infographic pastel palette, Poppins / Open Sans typography hierarchy
     (Title 40pt Bold, Subtitle 28pt SemiBold, Body 20pt Regular), 10px rounded container
     corners, and dynamic SME layout styling (Layout 70 blue band #2C81FE, Layout 20 corner PIP).

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 7 (7_presentation_experience_planner.py):
       - How: Ingests {topic_id}_experience_planner.json via
         7_experience_planner_tracker.json.
       - Purpose: Supplies choreographed presentation step animations.
     * Stage 1 (1_generate_instructional_design.py):
       - How: Ingests {topic_id}_storyboard_blueprint.json.
       - Purpose: Provides scene context and SME layout assignments.
   - Input Tracker: ppt_trackers/7_experience_planner_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * {topic_id}_experience_planner.json (Stage 7):
       Location: output/<TOPIC_NAME>/{topic_id}_experience_planner.json
       Content: Animation sequence and reveal choreography.
     * {topic_id}_storyboard_blueprint.json (Stage 1):
       Location: output/<TOPIC_NAME>/{topic_id}_storyboard_blueprint.json
       Content: Storyboard blueprint and layout contexts.
     * Input Tracker:
       Location: ppt_trackers/7_experience_planner_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 7_experience_planner_tracker.json.
   - Step 2: Loads experience plan and storyboard blueprint.
   - Step 3: Invokes Gemini 3.8 Flash using STYLING_SYSTEM_PROMPT.
   - Step 4: Maps design system tokens onto every visual container, card, icon, and label.
   - Step 5: Enforces high-contrast color constraints (dark slate #1E293B / #404040 text on light
     cards; strictly forbids low-contrast yellow/white text).
   - Step 6: Formulates final styled animation specifications.
   - Step 7: Atomically updates 9_styling_output_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * {topic_id}_styling_specifications.json:
       Location: output/<TOPIC_NAME>/{topic_id}_styling_specifications.json
       Content: Complete design-token-annotated animation guidelines per scene.
     * styling_gemini-3.8-flash.json:
       Location: output/<TOPIC_NAME>/styling_gemini-3.8-flash.json
       Content: Mirrored copy of styling specifications.
     * Output Tracker:
       Location: ppt_trackers/9_styling_output_tracker.json
       Content: Atomic tracker confirming completion of styling generation.

6. DOWNSTREAM CONSUMERS:
   - Stage 10 (10_generate_code.py): Uses styling specifications to generate initial Manim code.
================================================================================
"""

import os
import sys
import json
import re
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

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
    MUTED_TEXT_COLOR,
    BORDER_COLOR,
    CARD_BG_COLOR,
    CANVAS_BG_COLOR,
    TITLE_FONT_SIZE,
    BODY_FONT_SIZE,
    CARD_CORNER_RADIUS,
    CARD_STROKE_WIDTH,
    HIGHLIGHT_COLOR,
    HIGHLIGHT_THICKNESS
)

SIMPLILEARN_FONT_GUIDELINES = """
Simplilearn OSL 3.0 Typography Hierarchy:
• Font Family: Open Sans (Google Fonts)
• Slide Title: Open Sans Bold, 40pt, Color #404040 (or #FFFFFF on dark backgrounds). Title Case (Strictly No ALL-CAPS).
• Subtitle / Section Lead-In: Open Sans SemiBold, 28pt, Color #5F6368. Single line, concise.
• Card / Container Heading: Open Sans SemiBold, 24pt, Color #2C81FE or #404040.
• Body Content: Open Sans Regular, 20pt, Color #404040.
• Captions / Metrics / Labels: Open Sans Regular, 16pt, Color #5F6368.
• Mathematical Expressions: Strictly preserve all LaTeX formatting ($...$ and \\[...\\]).
"""

SIMPLILEARN_COLOR_PALETTE_GUIDELINES = """
Simplilearn OSL 3.0 10-Color Infographic Palette:
1. Sky Blue: #62B7E4
2. Steel Blue: #7EA2C8
3. Lavender Periwinkle: #9B99C7
4. Mint Seafoam: #8ECDB7 (minimal accent only)
5. Warm Amber: #E6A157
6. Mustard Gold: #DDB945
7. Coral Terracotta: #E58F6D
8. Warm Tan: #B88968
9. Dusty Rose: #D98CA1
10. Soft Lilac: #C1A5C6
Primary Accent Brand Blue: #2C81FE
Dark Charcoal Text: #404040
Slate Gray Muted: #5F6368
Soft Border: #DADCE0
Card Background: #FFFFFF (10px rounded corners, stroke_width=2, stroke=#DADCE0)
Focus Highlight: #F78908 (stroke_width=3, draw_time=1.0s)
Green Restriction: Minimal green (#34A853 / #2D6A4F). NEVER style large card backgrounds or headings with green.
"""

SYSTEM_PROMPT_STYLING_GENERATOR = """
        ### ROLE
        You are a Visual Styling Integrator for Manim animation pipelines.

        Inject ONLY color, font, gradient emphasis, and typography styling into Scene Animation Guidelines.
        Do NOT change wording, structure, layout, sequencing, or meaning.

        ---

        ### INPUTS
        1) Scene Animation Guidelines  
        2) Font Usage Guidelines  
        3) Color Palette Guidelines 

        All sections must follow the same palette and font hierarchy.

        ---

        ### RULES

        #### 1. IMMUTABILITY (HARD)
        Do NOT modify:
        • text, structure, layout, geometry, sequencing, asset construction, or intent
        • any LaTeX tags to represent mathematical symbols, equations, expressions or other artefacts.
        
        Only ADD:
        • color assignments
        • font assignments
        • font sizes
        • styling descriptors
        • layout refinement recommendations (centering, spacing, symmetry only; never structural changes)

        ---

        #### 2. DESIGN SYSTEM (MANDATORY)

        Treat the Color Palette Guidelines as the canonical design system.

        Do not invent new styling patterns.

        Whenever the guidelines define styling for a component type (for example titles, knowledge checks, definition cards, examples, warnings, references, comparisons, tables, timelines or process cards), follow it exactly.

        Apply the specified

        • colors
        • fills
        • borders
        • border styles
        • corner radius
        • typography
        • emphasis rules

        consistently throughout the scene.

        Only improvise when the guidelines do not specify a component style.

        For every assigned color explicitly specify

        using <Color Name> (<hex>).

        #### 2A. COLOR HIERARCHY & GREEN RESTRICTION

        REDUCE GREEN USAGE AS MUCH AS POSSIBLE:
        • Usage of green (#06C170, #2D6A4F) must be minimized as much as possible across all scenes!
        • NEVER style cards, containers, panels, backgrounds, borders, or text using green.
        • STRICT PROHIBITION OF YELLOW ON PURPLE:
          - NEVER EVER use yellow text, yellow pills/badges, or yellow strokes/accents on purple boxes, cards, or backgrounds.
          - On darker backgrounds, always use crisp WHITE (#FFFFFF) or Sky Blue (#62B7E4).
          - NEVER use light yellow text on white/light panels. Yellow and amber are strictly reserved for standalone warning/insight accent pills with dark charcoal text (#404040).

        #### 2B. SIMPLILEARN OSL 3.0 HEADER & DYNAMIC LEARNING THEME SPECIFICATION (MANDATORY):
        For all Simplilearn topics/scenes:
        • Major Slide Title must ALWAYS be styled in Open Sans font, 40pt Bold (or 26-28pt in Manim), Title Case (Chicago Manual of Style, 5-7 words, strictly NO ALL-CAPS). Color: #404040 (Primary Dark Charcoal) or #FFFFFF (on pill/dark backgrounds). Positioned in top safe header region.
        • Header Top-Left Title Pill (in Layout 20% PiP screens): Top-left capsule pill with #2C81FE brand accent background and white Open Sans Bold text.
        • In Layout 70% screens (Split Left SME + Right Content Area): The content card header is positioned at the top of the right floating white card, with a subtle category pill badge using one of the 10 approved pastel tones (e.g., #62B7E4 Sky Blue, #8ECDB7 Mint, #9B99C7 Lavender).
        • Subtitle / Section Lead-In: Open Sans SemiBold, 28pt (or 18pt in Manim), Color #5F6368 (Slate Gray), single line concise, active voice, US English.
        • Dynamic Learning Theme Styling:
          - Dynamic Visual Rhythm: Progressive reveal across 4-phase lifecycle: Entry (FadeIn / GrowFromCenter, run_time=0.4-0.6s), Settle (anchored in card), Focus Spotlight (#F78908 3px stroke, 1.0s draw time to direct cognitive focus), and Exit (FadeOut / Dissolve).
          - Kinetic Vector Hierarchy: Components should be living vector diagrams, dials, networks, conduits, or transparent illustration mobjects. Only use container cards or panels when representing explicit physical containers (e.g. data tables, code editors, file documents). Do NOT force living vector architectures or mechanical diagrams into static white cards or PowerPoint boxes. When containers are needed, use 10px rounded corners (corner_radius = 0.074 Manim units), clean white fill (#FFFFFF), subtle border (#DADCE0, stroke_width = 1.5-2.0), and a category pill badge at top.
          - Attention-Guiding Highlights: Single active highlight at a time using Simplilearn Orange (#F78908, 3px stroke, 1.0s draw time). Dim or mute non-active elements.
          - Split-Attention Elimination: Integrate labels directly adjacent to the diagram nodes they describe.
          - 2D Flat Vector Graphics ONLY: Strictly NO 3D images, NO drop shadows, NO dotted lines, NO heavy dark borders.
          - End-of-Module Video Transition: 0.5-second dissolve to White (#FFFFFF).
        • STRICT PROHIBITION OF INSTRUCTOR NAME: NEVER display instructor name or administrative metadata on any slide.
        • ZERO BLANK SCREEN: Structural cards, containers, and models must persist during narration. Never clear the workspace leaving an empty canvas.

        #### 2C. CANVAS BALANCING, SOFT TECH CANVAS & ZERO NAVY BLUE (MANDATORY):
        • STRICT PROHIBITION OF NAVY BLUE: Navy Blue (#06152B, #0A2540, #0B3C5D, #1D3557, NAVY) is strictly PROHIBITED and is NOT part of the Simplilearn palette!
        • STRICT PROHIBITION OF ALL CAPS: All on-screen text, titles, subtitles, headers, card labels, and tags must NEVER be in ALL CAPS. Use Title Case for titles and headers; use Sentence Case for body text. Short technical acronyms only (AI, RAM, DB, API, LLM, CPU, GPU, UI, ML) may be uppercase.
        • Containers and cards must use pure white (#FFFFFF), soft card (#F8FAFC), or colors from the approved 10-pastel palette. Text on light cards/canvas MUST use Primary Dark Charcoal (#404040).
        • MINIMAL WHITE SPACE: Visual architectures, diagrams, and containers must expand to occupy the full content arena (width 11.0-13.4, height 4.8-5.6), eliminating dead space and sterile empty voids.
        • All presentation content below the header MUST be centered horizontally (set_x(0)) and vertically in the content arena (y ≈ -0.4).

        #### 2D. ZERO UNWANTED SMALL-FONT TEXT & CLEAN TYPOGRAPHIC HIERARCHY (MANDATORY):
        • ZERO PPT BULLET-POINT LISTS: Never cram diagrams with small-font technical bullet lists (e.g. `• Latency: 12ms...`, `• Protocol Decoupling...`, `• Turn History...`). Visual elements must communicate through their kinetic motion, iconography, and bold clear titles.
        • DO NOT plaster cards or panels with tiny 7.5–9pt bullet point walls of text. If text is needed, use high-level, clear, readable focal labels (11pt+) only!
        • AGENT AUTONOMY & DYNAMIC DESIGN: Choose, compose, or omit annotation elements based on what best clarifies the specific concept without forcing rigid templates:
          - Subtitles under Header: When problem framing is helpful, attach the core question or principle cleanly as a single-line subtitle centered under the slide header (`create_title(title, subtitle)`). Keep concise (under 50 characters) so it renders on a single line without wrapping. NEVER place a subtitle on the top right! NEVER force a separate wide banner card!
          - In-Diagram Callouts & Leaders: Connect explanatory text directly to diagram nodes or variables via a small dot and leader line.
          - Structured Modeling Cards: Partitioned or comparative cards modeling domain concepts with bold headers and clear definitions.
          - Dynamic State Badges & Indicators: Clean rounded pills for milestones, boundary conditions, or transitions (Red for alerts/base cases, Dark Blue for info, Light Blue for verified states).
          - Key Insights: Focused metric pills or direct diagram callouts when grounding is helpful. NEVER force a rigid bottom takeaway banner!
        • STRICT NO RECAP THUMBNAIL SHRINKING: Never scale previous notes to 0.25 into the corner! Fade out notes cleanly.
        • ZERO BLANK WIPES: Keep outer frames and macro containers persistent across steps for smooth visual continuity.

        ---

        #### 3. TYPOGRAPHY

        Follow the Font Usage Guidelines exactly.

        STRICT NO ALL-CAPS MANDATE (TITLE CASE & SENTENCE CASE):
        • Text elements must NEVER use ALL CAPS (never write "PASCAL'S IDENTITY", "TOTAL SELECTIONS", "DEFINITION", etc.).
        • All titles, subtitles, card headers, badges, and tags must use Title Case / Camel Case (e.g. "Pascal's Identity", "Total Selections", "Formula Derivation").
        • Sentences, explanations, bullet statements, and descriptions must use Sentence case (e.g. "Selecting 2 elements from a set of 6.").

        Always specify

        • font
        • weight
        • size

        Maintain a clear hierarchy.

        The scene title must always be the largest text on screen.

        Section headings must remain visually subordinate to the title.

        Body text should remain comfortably readable.

        Do not reduce hierarchy by using similar font sizes for unrelated text levels.

        ---

        #### 4. COMPONENT STYLING

        Every presentation component should follow the design system.

        Specify where applicable

        • corner radius
        • fill style
        • border style
        • border thickness
        • solid or dotted borders
        • divider styling
        • label styling
        • panel treatment

        Introduce subpanels only when they improve grouping, readability or visual hierarchy.

        Do not place every piece of content inside a panel.

        Do NOT force living physical architectures, dials, networks, or process loops into static container cards. Only use container panels when representing explicit data tables, code editors, or document windows. Vector mechanisms must live directly in open canvas space with crisp labels.

        Use solid and dotted borders only where prescribed by the design system or where they improve semantic distinction.

        NESTING PRINCIPLE — CLEAN LIGHT CANVAS & LIVING MECHANISMS

        Never place raw text or isolated content directly on large colored background regions.

        Use layered visual hierarchy:

        • Living Vector Mechanisms: Primary conceptual models (dials, decision trees, neural cores, conduits) exist in open canvas space.
        • Micro-labels: Concise 1-3 word high-contrast labels adjacent to mechanisms.
        • Standalone numbers, variables, or tags should be styled with clean pastel badge pills, not large rectangular cards.

        The visual hierarchy should generally read:
        living vector mechanism -> focused accent label -> high-contrast data.

        Micro-panels should be sized proportionally to their content and should not become unnecessary large cards.

        ---

        #### 5. VISUAL ALIGNMENT

        You may refine alignment to improve visual balance without changing the instructional composition.

        When appropriate, adjust

        • left vs. center alignment
        • alignment of related objects
        • spacing consistency
        • visual centering
        • symmetry
        • whitespace distribution

        Prefer the alignment that best supports the content.

        For example

        • center-align standalone titles, key metrics, process diagrams and balanced comparisons
        • left-align definitions, paragraphs, lists and sequential reading content
        • align related panels, icons and labels consistently
        • distribute objects evenly to avoid visual crowding

        Do not reposition components in ways that change instructional relationships or reading order.

        ---

        #### 6. TABLES & DATA

        Improve readability through:

        * header emphasis
        * row separation
        * selective highlighting
        * contrast hierarchy

        Do not aggressively color data cells.

        Focus attention only on meaningful values.

        ---

        #### 7. VISUAL CONSISTENCY

        Maintain a consistent visual language.

        Components of the same instructional type should share the same styling.

        For example

        • knowledge checks
        • definitions
        • examples
        • references
        • comparisons
        • process cards
        • timelines
        • statistic panels

        should each retain a consistent appearance throughout the lesson whenever specified by the design system.

        Distribute primary colors across the workspace so visual weight remains balanced.

        Use secondary colors to support hierarchy rather than replacing primary accents.

        Prefer consistency over novelty.

        ---

        #### 8. PANEL HIERARCHY

        Differentiate panels through styling rather than geometry.

        For example

        • primary panels
        • secondary panels
        • reference panels
        • callouts

        should be distinguishable through fill, border and typography while preserving the supplied layout.

        ---

        #### 9. VARIATION

        Across blocks in the same scene:
        • Avoid repeating identical color patterns  
        • Vary which elements carry accents
        • Swap primary/secondary usage when possible
        • Vary gradient combinations where appropriate

        ---

        #### 10. ASSETS

        • Preserve FULL construction exactly
        • Describe the asset details in paragraph format as given in the input and inject styling into:
        - fills
        - strokes
        - highlights
        - text styling where present
        • panel styling where applicable
        • border treatment
        • corner radius
        • Please also preserve references to assets as given in the input

        • Only the entities that are declared as an asset in the input (e.g., asset_1, asset_2,etc.) should be treated as an asset. Describe them in detail only once.

        Do NOT:
        • rewrite, summarize, or add structure
        • define assets that are not already present in input scene animation guidelines
        • define new asset items just for mapping colors

        ---

        #### 11. IMAGES

        Ignore image prompts for styling. Preserve references to image names as given in the input

        ---

        ### OUTPUT FORMAT (STRICT)

        Scene N:
            - Styled Block:
                - Instruction:
                    <TEXT>
                - Assets:
                    - <Construction Description text>
                
            - Styled Block:
                - Instruction:
                    <TEXT>
                - Assets:
                    - <None>

        ---

        ### RULES

        1. "Scene N:" appears exactly once and should not be preceded by any other symbol. Output for only scene is generated at a time
        2. Each Section → ONE Styled Block  
        3. Order MUST match input  
        4. Indentation MUST match exactly  
        5. Each block MUST include:
        - Instruction
        - Assets
        6. If no assets in input, always use:
        - Assets:
                - None
        7. Do not use the Assets section for specifying styling guidelines if there is no asset in the corresponding input section
        8. No extra commentary  
        9. No markdown symbols
        10. Do not skip or miss any visual element details present in the Scene Animation Guidelines (but dont create unnecessary assets)

        ---

        ### FINAL CHECK

        Ensure:
        • No structural or textual changes
        • Palette strictly followed  
        • Gradient emphasis clearly specified
        • Font sizes explicitly specified
        • No monochrome assets
        • Consistent fonts
        • Output format exact
        • Component styles consistently follow the design system
        • Scene title remains the largest typography
        • Rounded panel styling applied consistently where appropriate
        • Border styles (solid/dotted) follow the supplied design language
        • Subpanels introduced only where they improve organization
        • Primary colors use solid fills (opacity = 1)
        • Secondary emphasis uses reduced fill opacity
        • At least two primary-color elements remain visible where practical
        • Alignment refined where appropriate for visual balance
        • Consistent spacing and whitespace maintained
        • Related components share common alignment
        • Alignment changes do not alter instructional structure
        """

USER_PROMPT_STYLING_GENERATOR = """
        For generating the styled animation instructions, refer to the following:
        ------------------------
        Scene Animation Guidelines:
        {storyboard_context}
        ------------------------
        Font Usage Guidelines:
        {font_guidelines}
        ------------------------
        Color Palette Guidelines:
        {color_palette_guidelines}
        """


def parse_styling_output(input_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parses LLM styled output text into structured styled blocks.
    Matches Simplilearn styling generator parsing logic.
    """
    lines = input_text.strip().splitlines()
    output: Dict[str, List[Dict[str, Any]]] = {}
    scene_number = None

    current_block: Dict[str, Any] = {}
    current_instruction_lines: List[str] = []
    current_assets: List[str] = []
    current_image_prompts: List[str] = []
    current_mode = None

    def flush_block():
        nonlocal current_block, current_instruction_lines, current_assets, current_image_prompts, current_mode
        if current_instruction_lines:
            current_block["matching_section"] = " ".join(current_instruction_lines).strip()
        if current_assets:
            current_block["assets"] = current_assets
        if current_image_prompts:
            current_block["image_prompts"] = current_image_prompts

        if scene_number and (current_block.get("matching_section") or current_block.get("assets") or current_block.get("image_prompts")):
            if scene_number not in output:
                output[scene_number] = []
            output[scene_number].append(current_block)

        current_block = {}
        current_instruction_lines = []
        current_assets = []
        current_image_prompts = []
        current_mode = None

    def switch_mode(new_mode):
        nonlocal current_mode, current_instruction_lines, current_block
        if current_mode == "instruction" and current_instruction_lines:
            current_block["matching_section"] = " ".join(current_instruction_lines).strip()
            current_instruction_lines = []
        current_mode = new_mode

    for line in lines:
        clean_line = re.sub(r"\*\*", "", line).strip()
        if not clean_line:
            continue

        if re.match(r"-?\s*Styled\s*Block\s*:?", clean_line, re.IGNORECASE):
            flush_block()
            continue

        if re.match(r"^-?\s*Instruction(?:\s*\d+)?\s*[:.]?", clean_line, re.IGNORECASE):
            switch_mode("instruction")
            content_match = re.match(r"^-?\s*Instruction(?:\s*\d+)?\s*[:.]?\s*(.*)", clean_line, re.IGNORECASE)
            if content_match and content_match.group(1).strip():
                current_instruction_lines.append(content_match.group(1).strip())
            continue

        scene_match = re.match(r"^#*\s*Scene\s*(\d+)\s*(?::.*)?$", clean_line, re.IGNORECASE)
        if scene_match and len(clean_line) < 80:
            flush_block()
            scene_number = scene_match.group(1)
            output[scene_number] = []
            continue

        if re.match(r"-?\s*Assets\s*:?", clean_line, re.IGNORECASE):
            switch_mode("assets")
            continue

        if re.match(r"-?\s*Image\s*Prompts\s*:?", clean_line, re.IGNORECASE):
            switch_mode("image_prompts")
            continue

        if current_mode == "instruction":
            current_instruction_lines.append(clean_line)
        elif current_mode == "assets":
            item_match = re.match(r"-\s*(.+)", clean_line)
            if item_match:
                content = item_match.group(1).strip()
                if re.match(r"(asset_\d+\s*:|none\b)", content, re.IGNORECASE) or not current_assets:
                    current_assets.append(content)
                else:
                    current_assets[-1] += " | " + content
            elif current_assets:
                current_assets[-1] += " " + clean_line
        elif current_mode == "image_prompts":
            item_match = re.match(r"-\s*(.+)", clean_line)
            if item_match:
                content = item_match.group(1).strip()
                if re.match(r"(image_\d+\s*:|none\b)", content, re.IGNORECASE) or not current_image_prompts:
                    current_image_prompts.append(content)
                else:
                    current_image_prompts[-1] += " | " + content
            elif current_image_prompts:
                current_image_prompts[-1] += " " + clean_line

    flush_block()
    return output


class StylingGenerator:
    """
    Assigns design system tokens, typography scales, high-contrast color palettes,
    and container styles to all elements across scenes adhering strictly to Simplilearn OSL 3.0.
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
        self.model_name = "gemini-3.8-flash" if "3.5" in str(model_name) else model_name
        self.api_key = api_key or self.google_api_key or self.claude_api_key or os.environ.get("GEMINI_API_KEY")

    def style_scene_local(self, scene: Dict[str, Any], sid: int) -> List[Dict[str, Any]]:
        """Deterministic local styling specification adhering strictly to OSL 3.0."""
        title = scene.get("title", f"Scene {sid}")
        layout = str(scene.get("sme_layout", "70"))
        instructions = scene.get("instructions", [])

        blocks = []
        for idx, instr in enumerate(instructions, 1):
            matching = instr.get("matching_section", title)
            styled_text = (
                f"- Styled Block:\n"
                f"  - Instruction: Style slide title '{title}' in Open Sans Bold 40pt (#202124). "
                f"Kinetic vector elements and living visual mechanisms in open canvas space. "
                f"Primary accents in Sky Blue (#62B7E4) and Steel Blue (#7EA2C8). "
                f"Focus highlights in Amber (#F78908, 3px stroke). {matching}\n"
                f"  - Assets:\n    - None\n"
                f"  - Image Prompts:\n    - None"
            )
            blocks.append({
                "matching_section": styled_text,
                "assets": ["None"],
                "image_prompts": ["None"]
            })

        if not blocks:
            blocks.append({
                "matching_section": f"Styled Scene {sid}: Open Sans 40pt title, 10px rounded white containers, #2C81FE brand blue accents.",
                "assets": ["None"],
                "image_prompts": ["None"]
            })

        return blocks

    def style_all_scenes(
        self,
        experience_data: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes Gemini 3.8 Flash LLM calls to inject full styling specifications
        scene-by-scene adhering strictly to Simplilearn OSL 3.0 design system.
        """
        scenes = experience_data.get("scenes", [])
        styled_output: Dict[str, Any] = {
            "topic": experience_data.get("topic", "Technical Architecture"),
            "design_system": "Simplilearn OSL 3.0 (10-Color Pastel Infographic Palette, Open Sans)",
            "scenes": []
        }

        use_gemini = self.api_provider in ["auto", "gemini"] and self.api_key
        if use_gemini:
            print(f"[*] Generating visual styling specifications via Gemini ({self.model_name}) across {len(scenes)} scenes...")
            import google.generativeai as genai
            genai.configure(api_key=self.api_key, transport="rest")
            model = genai.GenerativeModel(self.model_name)

        # Ingest authoritative Stage 1 instructional design if present
        import glob
        instructions_map = {}
        for cand_dir in [self.input_folder, os.path.join(self.input_folder, "metadata_blueprints")]:
            if cand_dir and os.path.exists(cand_dir):
                inst_matches = glob.glob(f"{cand_dir}/instructions_*.json") or glob.glob(f"{cand_dir}/*instructions*.json")
                if inst_matches:
                    try:
                        with open(inst_matches[0], "r", encoding="utf-8") as f:
                            instructions_map = json.load(f)
                        print(f"  [StylingGenerator] Ingested {len(instructions_map)} scenes from authoritative Stage 1 instructions: {inst_matches[0]}")
                        break
                    except Exception:
                        pass

        for s_idx, scene in enumerate(scenes, 1):
            sid = str(scene.get("scene_id") or scene.get("scene_index") or s_idx)
            title = scene.get("title", f"Scene {sid}")
            layout = str(scene.get("sme_layout", "70"))
            steps = scene.get("experience_steps") or scene.get("instructions") or []
            if instructions_map and sid in instructions_map and instructions_map[sid]:
                steps = instructions_map[sid]

            storyboard_context = f"Scene {sid}:\nTitle: {title}\nLayout: {layout}%\n"
            for st in steps:
                storyboard_context += f"Instruction: {st.get('matching_section', '')}\n"

            styled_blocks = []
            if use_gemini:
                try:
                    user_prompt = USER_PROMPT_STYLING_GENERATOR.replace(
                        "{storyboard_context}", storyboard_context
                    ).replace(
                        "{font_guidelines}", SIMPLILEARN_FONT_GUIDELINES
                    ).replace(
                        "{color_palette_guidelines}", SIMPLILEARN_COLOR_PALETTE_GUIDELINES
                    )
                    resp = model.generate_content(
                        f"{SYSTEM_PROMPT_STYLING_GENERATOR}\n\nUser Query: {user_prompt}",
                        generation_config=genai.GenerationConfig(
                            temperature=0.7,
                            max_output_tokens=4000
                        )
                    )
                    parsed = parse_styling_output(resp.text)
                    if sid in parsed and parsed[sid]:
                        styled_blocks = parsed[sid]
                    else:
                        styled_blocks = self.style_scene_local(scene, int(sid))
                except Exception as e:
                    print(f"  [StylingGenerator] Scene {sid} LLM fallback: {e}")
                    styled_blocks = self.style_scene_local(scene, int(sid))
            else:
                styled_blocks = self.style_scene_local(scene, int(sid))

            styled_output["scenes"].append({
                "scene_id": int(sid),
                "title": title,
                "sme_layout": layout,
                "voiceover_narration": scene.get("voiceover_narration", ""),
                "styled_blocks": styled_blocks,
                "osl_theme": {
                    "font_family": "Open Sans",
                    "title_size": TITLE_FONT_SIZE,
                    "body_size": BODY_FONT_SIZE,
                    "card_corner_radius": CARD_CORNER_RADIUS,
                    "highlight_color": HIGHLIGHT_COLOR,
                    "primary_accent": "#2C81FE"
                }
            })

        print(f"✓ Styling Generation Complete: Styled {len(styled_output['scenes'])} scenes")
        return styled_output

    def run(
        self,
        experience_path: str,
        output_path: str,
        blueprint_path: Optional[str] = None
    ) -> str:
        with open(experience_path, "r", encoding="utf-8") as f:
            experience_data = json.load(f)

        blueprint = None
        if blueprint_path and Path(blueprint_path).exists():
            with open(blueprint_path, "r", encoding="utf-8") as f:
                blueprint = json.load(f)

        styled = self.style_all_scenes(experience_data, blueprint=blueprint)

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(styled, f, indent=2, ensure_ascii=False)

        print(f"  Styling specifications saved -> {output_path}")
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

        for topic_id in topics:
            if target_topic_id and topic_id != target_topic_id:
                continue

            if in_tracker and topic_id in in_tracker:
                if not in_tracker[topic_id].get("processed", False) and os.environ.get("FORCE_RUN") != "1":
                    print(f"Skipping {topic_id}: Input tracker not marked as processed.")
                    continue

            if out_tracker and topic_id in out_tracker and out_tracker[topic_id].get("processed", False) and os.environ.get("FORCE_RUN") != "1":
                print(f"Skipping {topic_id}: Already processed in styling generation tracker.")
                continue

            topic_dir = os.path.join(self.input_folder, topic_id)
            if not os.path.exists(topic_dir):
                continue

            print(f"Processing Styling Generation for {topic_id}...")
            meta_dir = os.path.join(topic_dir, "metadata_blueprints")
            os.makedirs(meta_dir, exist_ok=True)
            experience_file = os.path.join(meta_dir, f"{topic_id}_experience_planner.json")
            if not os.path.exists(experience_file):
                experience_file = os.path.join(topic_dir, f"{topic_id}_experience_planner.json")
            if not os.path.exists(experience_file):
                experience_file = os.path.join(topic_dir, "experience_planner.json")
            if not os.path.exists(experience_file):
                print(f"Skipping {topic_id}: Missing experience planner.")
                continue

            blueprint_file = os.path.join(meta_dir, f"{topic_id}_storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(topic_dir, f"{topic_id}_storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(meta_dir, "storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(topic_dir, "storyboard_blueprint.json")

            out_styling = os.path.join(meta_dir, f"{topic_id}_styling_specifications.json")
            try:
                self.run(
                    experience_path=experience_file,
                    output_path=out_styling,
                    blueprint_path=blueprint_file if os.path.exists(blueprint_file) else None
                )
                # Also save mirrored copy inside meta_dir
                try:
                    shutil.copy2(out_styling, os.path.join(meta_dir, "styling_gemini-3.8-flash.json"))
                except Exception:
                    pass

                if self.output_tracker_path:
                    self._save_tracker(self.output_tracker_path, {
                        topic_id: {
                            "output_path": out_styling,
                            "processed": True,
                            "topic_name": topic_id,
                            "topic_id": topic_id,
                            "failure_reason": None
                        }
                    })
                print(f"Successfully generated styling specifications for {topic_id}.")
            except Exception as e:
                print(f"Error generating styling specifications for {topic_id}: {e}")
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
    parser = argparse.ArgumentParser(description="Styling Generator (Simplilearn OSL 3.0 Architecture)")
    parser.add_argument("-e", "--experience", required=True, help="Input experience plan JSON")
    parser.add_argument("-a", "--assets", default=None, help="Optional classified assets JSON")
    parser.add_argument("-o", "--output", required=True, help="Output styling specifications JSON")
    parser.add_argument("-b", "--blueprint", default=None, help="Optional storyboard blueprint JSON")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM API provider")
    parser.add_argument("-m", "--model", default="gemini-3.8-flash", help="Model name")
    args = parser.parse_args()

    generator = StylingGenerator(
        api_provider=args.provider,
        model_name=args.model
    )
    generator.run(args.experience, args.output, blueprint_path=args.blueprint)
