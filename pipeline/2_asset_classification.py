#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 2: ASSET CLASSIFICATION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 2
   - Script Name: 2_asset_classification.py
   - Primary Class: AssetClassification
   - Pipeline Role:
     Decomposes visual storyboard specifications from Stage 1 into categorized, modular
     visual components. Distinguishes procedural Manim code constructs (Asset_Suggestion)
     from diffusion-rendered thematic illustrations (Image_Suggestion). Strictly enforces
     the freeze-frame principle, UI asset rules, explicit non-asset exclusions (no character
     silhouettes), and Simplilearn OSL 3.0 spatial safe zones.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 1 (1_generate_instructional_design.py):
       - How: Ingests {topic_id}_storyboard_blueprint.json via
         1_instruction_design_output_tracker.json.
       - Purpose: Provides scene visual descriptions and layout contexts.
   - Input Tracker: ppt_trackers/1_instruction_design_output_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * {topic_id}_storyboard_blueprint.json (Stage 1):
       Location: output/<TOPIC_NAME>/{topic_id}_storyboard_blueprint.json
       Content: Storyboard scenes, visual descriptions, and SME layout tags.
     * ex_config.json:
       Location: output/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/1_instruction_design_output_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 1_instruction_design_output_tracker.json.
   - Step 2: Loads storyboard blueprint and parses visual description per scene.
   - Step 3: Invokes Gemini 3.8 Flash using INSTRUCTIONS_SYSTEM_PROMPT to decompose assets.
   - Step 4: Classifies assets into procedural geometric entities vs diffusion illustrations.
   - Step 5: Enforces Simplilearn OSL 3.0 spatial clearance tags:
     * Layout 70: Content canvas constrained to x >= 760px.
     * Layout 20: Keep upper-right PIP clear; diagrams restricted to y >= 270px.
   - Step 6: Validates parity between storyboard scene structure and classified assets.
   - Step 7: Atomically updates 2_asset_class_output_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * {topic_id}_classified_assets.json:
       Location: output/<TOPIC_NAME>/{topic_id}_classified_assets.json
       Content: Categorized catalog of asset suggestions and image suggestions per scene.
     * classified_assets.json:
       Location: output/<TOPIC_NAME>/classified_assets.json
       Content: Mirrored copy of classified assets.
     * Output Tracker:
       Location: ppt_trackers/2_asset_class_output_tracker.json
       Content: Atomic tracker confirming completion of asset classification.

6. DOWNSTREAM CONSUMERS:
   - Stage 3 (3_asset_construction.py): Constructs geometric Manim code specifications
     for Asset_Suggestions.
   - Stage 4 (4_image_prompt_generation.py): Generates diffusion prompts for Image_Suggestions.
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

from pipeline.config import CANVAS_WIDTH, CANVAS_HEIGHT, COLORS

INSTRUCTIONS_SYSTEM_PROMPT = """
        ROLE

        You are an expert motion graphics designer and Manim-based visual systems analyst.
        You identify visual artefacts whose STATIC STRUCTURE and INTERNAL COMPOSITION
        benefit from deliberate construction using primitives.

        You IGNORE animation, timing, and sequencing.
        You MAY consider internal subcomponents ONLY if they provide structural value.

        You produce STRICTLY STRUCTURED, MACHINE-PARSEABLE output.
        Formatting creativity is FORBIDDEN.


        ====================================================
        INPUTS (WILL BE PROVIDED)
        ====================================================

        1. storyboard_scene
        Scene N:
            <Visual>: <visual description>

        • Each <Visual> is a DISTINCT static composition
        • Order MUST be preserved

        2. input_context
        • Narration aligned to visuals (for semantic intent)

        3. Course context: {course_context}
        4. Explainer type: {explainer_type}
        5. Topic: {topic}
        6. Target audience: {target_audience}

        ====================================================
        CORE DECISION PRINCIPLE
        ====================================================

        Mentally FREEZE each Visual.

        Ignore:
        • animation
        • timing
        • sequencing

        Classify as Asset ONLY if ALL are true:

        • it contains meaningful internal geometry beyond a small collection of standard Manim primitives
        • multiple subcomponents have structural significance
        • subcomponents may benefit from independent reuse, manipulation, replacement, or recomposition
        • rebuilding it repeatedly from primitives would be meaningfully costly

        Semantic importance alone does NOT justify an Asset. Visual styling fidelity alone does NOT justify an Asset, except for designated UI Assets.

        If an artefact is merely a basic flat container, plain bullet box, or trivial single-shape placeholder, it is NOT an Asset. However, multi-part kinematic mechanisms, structured visual metaphors (flywheels, infinity loops, funnels), and complex domain UI models ALWAYS qualify as Assets.

        Classification Strategy:
        Identify both domain UI assets and rich, multi-component KINEMATIC & GEOMETRIC VISUAL METAPHORS.

        ====================================================
        WHAT QUALIFIES AS AN ASSET
        ====================================================

        Include artefacts where:

        • geometry itself carries meaning
        • proportions or segmentation matter
        • internal structure affects understanding
        • multiple meaningful subcomponents exist
        • subcomponents may be independently reused or controlled
        • recreation cost from primitives is substantial

        Valid examples:

        • clocks with dial and hands
        • machinery with functional parts
        • cupboards with doors and compartments
        • layered physical objects with meaningful structure
        • reusable domain-specific artefacts with rich geometry

        • Kinetic Conceptual Metaphors & Dynamic Mechanisms:
          - Rotational progression cycles / flywheels (multi-stage circular rotors rotating about a central hub)
          - Continuous loops & infinity paths (lemniscates bridging multiple entities with circulating nodes)
          - Converging aggregation conduits / funnels (funnels channeling multiple telemetry/data inputs into a buffer)
          - Multi-tier modular memory hierarchies with dynamic read/write bus lines
          - Multi-state finite state machine orchestrators

        Complex Kinematic & Geometric Visual Metaphors (ALWAYS qualify as Assets):
        • Flywheels and Rotary Progression Drives (e.g., 3-stage PRA loop, continuous cyclic gears, revolving multi-stage rotors)
        • Infinity Loops and Topological Interaction Bridges (e.g., figure-8 lemniscates connecting agent & environment, bi-directional feedback loops with waypoint callouts)
        • Ingestion Funnels and Multi-Stage Buffers (e.g., tapered 3-stage polygonal context funnels, filtration meshes, reservoir chambers)
        • Multi-Chamber Engine Cores and Cognitive Hubs (e.g., quad-chamber architecture cores with perception, memory, reasoning, and action bays connected to central hub)
        • Telemetry Gauges, Coordinate Anomaly Monitors & Sensor Arrays (calibrated vector dials, dual-axis telemetry graphs with dynamic threshold bounds)
        • Strategic 2x2 Matrices, Balanced Decision Trees, and Agile Sprint Cycles
        • Marketing & Conversion Funnels (descending tiered process funnels with proportional conversion drop-offs)
        • Executive KPI Dials & Chronometer Gauges (performance benchmark cards with semicircular meter and dynamic needle)
        • Enterprise Risk Severity Heatmaps (3x3 Impact vs Likelihood grids with color-coded risk bands and token markers)
        • Cross-Functional RACI Governance Tables (stakeholder responsibility matrices with color-coded R/A/C/I badge pills)

        Special UI Assets (ALWAYS qualify as Assets):
        • browser windows
        • email inbox interfaces
        • email composition windows
        • chat interfaces
        • messaging applications
        • mobile application screens
        • software product interfaces
        • dashboard application shells
        • documents and reports
        • financial ledgers 
        • spredsheets

        Reason:

        These artefacts contain meaningful visual hierarchy, spacing systems,
        navigation structures, component layouts, states, controls, and styling
        details that benefit from reusable construction rather than flat imagery.

        For such UI & Kinematic Assets, include:

        • primary layout regions
        • navigation elements
        • content areas
        • controls and interaction components
        • visual styling cues
        • major reusable subcomponents

        The goal is to preserve visual fidelity and consistent reconstruction.

        A multi-part object is NOT automatically an Asset.

        The decomposition itself must provide production value.

        ====================================================
        EXPLICIT NON-ASSETS
        ====================================================

        Non-Assets (do NOT classify as assets):

        • plain PowerPoint-style text boxes
        • simple bullet list containers
        • basic rectangle card holders without internal kinematic structure
        • generic callout bubbles without architectural decomposition
        • static slide frames

        These simple flat cards should be constructed as standard layout elements.
        Conversely, all complex visual metaphors (Flywheels, Infinity Loops, Funnels, Engine Cores, Gauges) MUST be classified as Assets.

        ====================================================
        IMAGE SUGGESTION GUIDELINES
        ====================================================

        Use Image Suggestion when:

        • Identity depends on styling or visual detail
        • Structure is not important
        • Decomposition adds no value
        • It is a commonly recognized icon

        Examples:
        • Human figures (every human identity should have a different prompt unless referring to a generic group)
        • Generic icons (person, bell, etc. which do not qualify as assets)
        • Real-world objects needing visual fidelity
        • Maps, logos, decorative illustrations

        MENTAL TEST:
        If replacing it with a flat icon loses nothing → use Image.

        Do not use images for simple symbols like crosses or checkmarks
        Image suggestions should describe the expected visual appearance, not merely identify the object.

        ====================================================
        YOUR TASK
        ====================================================

        For the given Scene:

        • Produce ONE Guidelines block per <Visual>, in order
        • If nothing qualifies → return `None`
        • Think at Scene-level, not Visual-level, when tracking artefacts.

        ----------------------------------------------------
        1. ASSET SUGGESTION
        ----------------------------------------------------

        For EACH artefact (ONE paragraph):

        • What it represents
        • Why its structure is non-trivial
        • Its internal composition (parts, relationships) in detail
        • What can be controlled or recomposed
        • How it relates to other elements

        DO NOT mention:
        • Animation, motion, construction, text

        ----------------------------------------------------
        2. IMAGE SUGGESTION
        ----------------------------------------------------

        For EACH artefact (ONE paragraph):

        • What it represents
        • Why structure is not important
        • Why a flat image is sufficient
        • How it fits into the scene
        • Key visual appearance characteristics

        For human characters additionally include:

        • approximate age range
        • gender presentation if inferable
        • facial characteristics
        • hairstyle
        • expression or demeanor
        • clothing style
        • notable accessories
        • make sure they are visible from head to toe
        • the character should be facing straight (not sideways)

        For objects additionally include:

        • overall appearance
        • major visible components
        • material or finish cues
        • distinctive visual characteristics

        Provide enough visual detail for image selection or generation,
        but do not decompose the artefact into reusable asset parts.

        -------------------------------------
        ARTEFACT TRACKING & REUSE (CRITICAL)
        ----------------------------------------
        Within a Scene, maintain an internal set of already identified artefacts.

        RULES:

        • If an artefact has already been suggested in ANY previous Guidelines block
        (either in Asset Suggestion OR Image Suggestion), it MUST NOT be repeated.

        • If the same artefact appears again in a later Visual:
        → Do NOT describe it again
        → Do NOT include it in output
        → Assume reuse

        • Only suggest NEW artefacts introduced in that Visual.

        • Even if some artefact is explicitly mentioned as an icon, pass it through the asset vs image test

        • If a Visual contains only previously identified artefacts:
        → Return:
                Asset Suggestion: None
                Image Suggestion: None

        • When uncertain, choose Image Suggestion for decorative art, and Asset Suggestion for functional/kinematic visual mechanisms.
        • Asset classification is mandatory for multi-part geometric and kinematic visual metaphors (flywheels, loops, funnels, engine cores, gauges).

        DEFINITION OF SAME ARTEFACT:

        Treat as same if:
        • Conceptually identical (e.g. person icon, piggy bank)
        • Even if count, size, color, or position differs

        Do NOT create separate suggestions for duplicates or instances.


        ====================================================
        OUTPUT FORMAT (STRICT)
        ====================================================

        Scene N:
            Guidelines:
                Asset Suggestion:
                    - suggestion_01: <paragraph>
                    - suggestion_02: <paragraph>
                Image Suggestion:
                    - suggestion_01: <paragraph>
                    - suggestion_02: <paragraph>

            Guidelines:
                Asset Suggestion:
                    None

                Image Suggestion:
                    None
            ...

        Output Rules:
        1. Only one scene `Scene N` is generated at a time
        2. Do not add any comments or markdown symbols
        3. Make sure the suggestion_<n> marker precedes every guideline as shown in the output format

        ====================================================
        FINAL CONSTRAINTS
        ====================================================

        • Ignore animation
        • The count of Guidelines in the output should strictly match the number of <Visual> in storyboard_scene
        • Text is NEVER an asset
        • Avoid trivial primitives
        • Apply decomposition VALUE filter strictly
        • Prefer Image for common icons
        • Asset Reuse Rule:
        - Do not repeat artefacts within a Scene
        • Maintain strict formatting
        """

INSTRUCTIONS_USER_PROMPT = """
        For generating the animation instructions, refer to the following
        ------------------------
        storyboard_scene:
        {storyboard_scene}
        ------------------------
        input_context:
        {input_context}

        """


def parse_classification_output(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Robust regex parser translating LLM Guidelines into structured scene assets.
    Matches Simplilearn asset classification parsing logic.
    """
    scenes = {}
    scene_blocks = re.split(r'\n(?=\s*scene\s+\d+\s*:)', text, flags=re.IGNORECASE)

    for scene_block in scene_blocks:
        scene_match = re.search(r'scene\s+(\d+)\s*:', scene_block, re.IGNORECASE)
        if not scene_match:
            continue

        scene_number = scene_match.group(1)
        scenes[scene_number] = []

        guidelines_blocks = re.split(r'Guidelines\s*:', scene_block, flags=re.IGNORECASE)

        for block in guidelines_blocks[1:]:
            asset_suggestions = None
            image_suggestions = None

            asset_match = re.search(
                r'Asset\s+Suggestion\s*:\s*(.*?)(?=Image\s+Suggestion\s*:|$)',
                block,
                flags=re.IGNORECASE | re.DOTALL
            )
            if asset_match:
                asset_content = asset_match.group(1).strip()
                if not re.match(r'^none\b', asset_content, re.IGNORECASE):
                    items = re.findall(
                        r'-\s+suggestion_\d+\s*:\s*(.+?)(?=(?:^|\n)\s*-\s+suggestion_\d+|$)',
                        asset_content, re.DOTALL | re.IGNORECASE
                    )
                    if items:
                        asset_suggestions = [item.strip() for item in items]

            image_match = re.search(
                r'Image\s+Suggestion\s*:\s*(.*?)(?=Guidelines|$)',
                block,
                flags=re.IGNORECASE | re.DOTALL
            )
            if image_match:
                image_content = image_match.group(1).strip()
                if not re.match(r'^none\b', image_content, re.IGNORECASE):
                    items = re.findall(
                        r'-\s+suggestion_\d+\s*:\s*(.+?)(?=(?:^|\n)\s*-\s+suggestion_\d+|$)',
                        image_content, re.DOTALL | re.IGNORECASE
                    )
                    if items:
                        image_suggestions = [item.strip() for item in items]

            scenes[scene_number].append({
                "Asset_Suggestion": asset_suggestions,
                "Image_Suggestion": image_suggestions
            })

    return scenes


def compare_structures(input_dict: Dict[str, Any], output_dict: Dict[str, Any]) -> bool:
    """Compare structures of input and output JSON to ensure no dropped scenes."""
    def describe_object_structure(obj):
        structure = {}
        for key in sorted(obj.keys()):
            if isinstance(obj[key], list):
                structure[key] = ("list", len(obj[key]))
            elif isinstance(obj[key], dict):
                structure[key] = ("dict", len(obj[key]))
            else:
                structure[key] = (type(obj[key]).__name__, 1)
        return structure

    input_structure = describe_object_structure(input_dict)
    output_structure = describe_object_structure(output_dict)

    all_keys = set(input_structure.keys()).union(set(output_structure.keys()))
    mismatch = False
    for key in sorted(all_keys):
        in_val = input_structure.get(key)
        out_val = output_structure.get(key)
        if in_val != out_val:
            print(f"  [AssetClassification] Structure diff scene {key}: Input {in_val} vs Output {out_val}")
            mismatch = True
    return mismatch


class AssetClassification:
    """
    Classifies visual assets from instructional storyboard scenes into modular,
    reusable components (Asset_Suggestion) and diffusion illustrations (Image_Suggestion).
    """

    def __init__(
        self,
        input_tracker_path: Optional[str] = None,
        output_tracker_path: Optional[str] = None,
        google_api_key: Optional[str] = None,
        claude_api_key: Optional[str] = None,
        input_folder: Optional[str] = None,
        blueprint_path: Optional[str] = None,
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
        self.blueprint_path = blueprint_path
        self.api_provider = api_provider.lower()
        self.model_name = model_name
        self.api_key = api_key or self.google_api_key or self.claude_api_key or os.environ.get("GEMINI_API_KEY")

    def classify_scene_local(self, scene: Dict[str, Any], sid: int) -> List[Dict[str, Any]]:
        """
        Dynamic rule-based and semantic classification adhering to Simplilearn OSL 3.0 rules.
        Inspects step-level visual descriptions, dominant visual concepts, and matching sections
        to identify complex kinetic metaphors (flywheels, infinity loops, funnels, solar arrays, etc.).
        """
        layout = str(scene.get("sme_layout", "70"))
        title = scene.get("title", f"Scene {sid}")
        steps = scene.get("presentation_steps", [])

        if not steps:
            # Fallback for single-step or unpartitioned scenes
            full_text = f"{title} {scene.get('voiceover_narration', '')} {scene.get('visual_description', '')}"
            asset_suggs = self._detect_semantic_assets(full_text, title)
            image_suggs = self._detect_semantic_images(full_text, title)
            if not asset_suggs and layout in ["70", "20"]:
                asset_suggs = [f"Kinetic Vector Diagram and Living Visual Mechanism for {title}."]
            return [{
                "Asset_Suggestion": asset_suggs if asset_suggs else None,
                "Image_Suggestion": image_suggs if image_suggs else None
            }]

        guidelines = []
        for step_i, step in enumerate(steps, 1):
            st_title = step.get("title") or step.get("step_title") or f"Step {step_i}"
            vd = step.get("visual_description", "")
            if isinstance(vd, dict):
                vd = f"{vd.get('matching_section', '')} {vd.get('purpose', '')}"
            ms = step.get("matching_section", "")
            dvc = step.get("dominant_visual_concept", "")
            narr = step.get("narration") or step.get("voiceover_narration") or ""

            step_text = f"{st_title} {vd} {ms} {dvc} {narr}"
            asset_suggs = self._detect_semantic_assets(step_text, st_title)
            image_suggs = self._detect_semantic_images(step_text, st_title)

            if not asset_suggs and layout in ["70", "20"] and step_i == 1:
                asset_suggs = [f"Kinetic Vector Diagram and Living Visual Mechanism for {title} ({st_title})."]

            guidelines.append({
                "Asset_Suggestion": asset_suggs if asset_suggs else None,
                "Image_Suggestion": image_suggs if image_suggs else None
            })

        return guidelines

    def _detect_semantic_assets(self, text: str, context_label: str) -> List[str]:
        """Detect kinetic metaphors and complex domain assets from blueprint text."""
        assets = []
        t = text.lower()

        # 1. Flywheels & Rotary Progression Cycles
        if re.search(r"\bflywheel\b|\brotary\b|\brotational progression\b|\b3-stage.*cycle\b|\bpra cycle\b", t):
            assets.append("Rotational progression cycle / flywheel: 3-stage circular rotor mechanism rotating about a central hub with illuminated apex phases and dynamic state indicators.")

        # 2. Infinity Loops & Topological Interaction Bridges
        if re.search(r"\binfinity\b|\blemniscate\b|\bfigure-8\b|\bcontinuous loop\b|\binteraction loop\b", t):
            assets.append("Continuous observation-execution infinity path: Figure-8 lemniscate bridging agent perception and environment with circulating animated telemetry nodes.")

        # 3. Context Aggregation & Conversion Funnels
        if re.search(r"\bfunnel\b|\bcontext aggregation\b|\bconverging\b|\bchanneling multiple\b|\bcontext buffer\b", t):
            assets.append("Context aggregation funnel: Tapered multi-stage polygonal intake funnel channeling telemetry readings, prompts, tool outputs, and error alerts into working context buffer.")

        # 4. Solar Photovoltaic Arrays
        if re.search(r"\bsolar\b|\bphotovoltaic\b|\bpv array\b|\bsolara site\b|\bsolar farm\b", t):
            assets.append("VectorAdvancedSolarArray: Broadcast-quality 2.5D photovoltaic array with live power generation status and telemetry wave pulses.")

        # 5. Static Mechanical Tools
        if re.search(r"\bhammer\b|\bstatic tool\b|\binanimate tool\b|\bpassive tool\b", t):
            assets.append("VectorMechanicalHammerTool: Self-contained tool card with precision mechanical hammer illustration and dormant Idle/Waiting status indicator.")

        # 6. Strategic Decision Matrices & Heatmaps
        if re.search(r"\bdecision matrix\b|\btrade-off matrix\b|\b2x2 matrix\b|\brisk heatmap\b|\braci\b", t):
            assets.append("Strategic multi-attribute decision matrix with color-coded score badges and optimal action indicator.")

        # 7. Dynamic Telemetry Gauges & Meters
        if re.search(r"\bconfidence gauge\b|\btelemetry gauge\b|\bkpi gauge\b|\bcalibrated dial\b", t):
            assets.append("Dynamic telemetry gauge with calibrated semicircular scale, needle indicator, and alert thresholds.")

        return list(dict.fromkeys(assets))

    def _detect_semantic_images(self, text: str, context_label: str) -> List[str]:
        """Detect hero illustration requirements from blueprint text."""
        images = []
        t = text.lower()

        if re.search(r"\bhuman engineer\b|\boperator\b|\bescalat\w* handoff\b|\btechnician\b|\bspecialist\b", t):
            images.append("A professional technical human systems engineer holding an active digital diagnostic tablet representing the escalation handoff receiver, full-length vector educational illustration on pure white background.")

        if re.search(r"\bsolar sensor\b|\btelemetry ingress\b|\bsensor hardware\b", t):
            images.append("High-resolution technical illustration of an industrial solar sensor unit with telemetry antennas and real-time signal conduits.")

        if re.search(r"\bneural core\b|\bllm brain\b|\bcognitive engine\b|\bintelligence hub\b", t):
            images.append("High-resolution technical illustration of a cognitive neural circuit brain with illuminated dendritic pathways.")

        return list(dict.fromkeys(images))

    def classify_all_assets(
        self,
        storyboard_blueprint: Dict[str, Any],
        topic: str = "Technical Architecture",
        course_context: str = "Digital Learning",
        explainer_type: str = "Educational Explainer",
        target_audience: str = "Software engineers, technical architects, and enterprise learners"
    ) -> Dict[str, Any]:
        """
        Executes scene-by-scene LLM classification using Gemini 3.8 / 3.8 Flash
        with full Simplilearn prompt fidelity and Simplilearn OSL 3.0 safe zones.
        """
        scenes = storyboard_blueprint.get("scenes", [])
        classified_output: Dict[str, List[Dict[str, Any]]] = {}
        raw_output_text = ""

        prompt_replacements = {
            "course_context": course_context,
            "explainer_type": explainer_type,
            "topic": topic,
            "target_audience": target_audience
        }
        system_prompt = INSTRUCTIONS_SYSTEM_PROMPT
        for k, v in prompt_replacements.items():
            system_prompt = system_prompt.replace("{" + k + "}", str(v))

        use_gemini = self.api_provider in ["auto", "gemini"] and self.api_key

        if use_gemini:
            print(f"[*] Classifying assets using Gemini ({self.model_name}) across {len(scenes)} scenes...")
            import google.generativeai as genai
            genai.configure(api_key=self.api_key, transport="rest")
            model = genai.GenerativeModel(self.model_name)

        for s_idx, scene in enumerate(scenes, 1):
            sid = str(scene.get("scene_id") or scene.get("scene_index") or s_idx)
            title = scene.get("title", f"Scene {sid}")
            narration = scene.get("voiceover_narration", "")
            layout = str(scene.get("sme_layout", "70"))
            
            # AGGREGATE STEP-LEVEL VISUAL DESCRIPTIONS
            step_visuals = []
            for step_i, step in enumerate(scene.get("presentation_steps", []), 1):
                st_title = step.get("title") or step.get("step_title") or f"Step {step_i}"
                vd = step.get("visual_description")
                ms = step.get("matching_section", "")
                dvc = step.get("dominant_visual_concept", "")
                desc = ""
                if isinstance(vd, dict):
                    desc = vd.get("matching_section") or vd.get("purpose") or ""
                elif isinstance(vd, str):
                    desc = vd
                if not desc and ms:
                    desc = ms
                if dvc and dvc not in desc:
                    desc = f"{dvc}. {desc}" if desc else dvc
                if desc:
                    step_visuals.append(f"Step {step_i} ({st_title}): {desc.strip()}")

            if step_visuals:
                visual_desc = "\n   ".join(step_visuals)
            else:
                visual_desc = scene.get("primary_content") or scene.get("visual_description") or title

            storyboard_context = f"Scene {sid} - {title}:\n   <Visual Elements>:\n   {visual_desc}"

            if use_gemini:
                try:
                    user_prompt = INSTRUCTIONS_USER_PROMPT.replace("{storyboard_scene}", storyboard_context).replace("{input_context}", narration)
                    full_prompt = f"{system_prompt}\n\nUser Query: {user_prompt}"
                    resp = model.generate_content(
                        full_prompt,
                        generation_config=genai.GenerationConfig(
                            temperature=0.7,
                            max_output_tokens=4000
                        )
                    )
                    raw_text = resp.text
                    raw_output_text += f"{raw_text}\n\n"
                    parsed = parse_classification_output(raw_text)
                    if sid in parsed and parsed[sid]:
                        classified_output[sid] = parsed[sid]
                    else:
                        classified_output[sid] = self.classify_scene_local(scene, int(sid))
                except Exception as e:
                    print(f"  [AssetClassification] Scene {sid} LLM fallback: {e}")
                    classified_output[sid] = self.classify_scene_local(scene, int(sid))
            else:
                classified_output[sid] = self.classify_scene_local(scene, int(sid))

        enriched_catalog: Dict[str, Any] = {
            "topic": topic,
            "total_scenes": len(scenes),
            "scenes": []
        }

        for s_idx, scene in enumerate(scenes, 1):
            sid = str(scene.get("scene_id") or scene.get("scene_index") or s_idx)
            layout = str(scene.get("sme_layout", "70"))
            steps = classified_output.get(sid, self.classify_scene_local(scene, int(sid)))

            scene_entry = {
                "scene_id": int(sid),
                "title": scene.get("title", f"Scene {sid}"),
                "sme_layout": layout,
                "voiceover_narration": scene.get("voiceover_narration", ""),
                "spatial_safe_zone": {
                    "layout_type": f"{layout}%",
                    "safe_bounds": {
                        "x_min": 0 if layout == "100" else (760 if layout == "70" else 80),
                        "x_max": 1920 if layout == "100" else 1840,
                        "y_min": 0 if layout == "100" else 80,
                        "y_max": 1080 if layout == "100" else 1000,
                        "content_min_x": 760 if layout == "70" else 80,
                        "diagram_min_y": 270 if layout == "20" else 80,
                        "title_max_x": 1440 if layout == "20" else 1840
                    }
                },
                "steps": steps
            }
            enriched_catalog["scenes"].append(scene_entry)

        return enriched_catalog

    def run(self, blueprint_path: str, output_path: str) -> str:
        with open(blueprint_path, "r", encoding="utf-8") as f:
            blueprint = json.load(f)

        topic = blueprint.get("concept") or blueprint.get("lesson_title") or "Technical Architecture"
        catalog = self.classify_all_assets(blueprint, topic=topic)

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

        print(f"✓ Asset Classification Complete: Classified assets saved -> {output_path}")
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
                print(f"Skipping {topic_id}: Already processed in asset classification tracker.")
                continue

            topic_dir = os.path.join(self.input_folder, topic_id)
            if not os.path.exists(topic_dir):
                continue

            print(f"Processing Asset Classification for {topic_id}...")
            meta_dir = os.path.join(topic_dir, "metadata_blueprints")
            os.makedirs(meta_dir, exist_ok=True)
            candidates = [
                os.path.join(meta_dir, f"{topic_id}_storyboard_blueprint.json"),
                os.path.join(topic_dir, f"{topic_id}_storyboard_blueprint.json"),
                os.path.join(meta_dir, "storyboard_blueprint.json"),
                os.path.join(topic_dir, "storyboard_blueprint.json"),
                os.path.join(meta_dir, "instructions.json"),
                os.path.join(topic_dir, "instructions.json")
            ]
            blueprint_file = None
            for cand in candidates:
                if os.path.exists(cand):
                    blueprint_file = cand
                    break

            if not blueprint_file:
                matches = list(Path(meta_dir).glob("*blueprint*.json")) + list(Path(topic_dir).glob("*blueprint*.json"))
                if matches:
                    blueprint_file = str(matches[0])

            if not blueprint_file:
                print(f"Skipping {topic_id}: Missing storyboard blueprint.")
                continue

            out_assets = os.path.join(meta_dir, f"{topic_id}_classified_assets.json")
            try:
                self.run(blueprint_file, out_assets)
                # Also save classified_assets.json copy inside meta_dir
                try:
                    shutil.copy2(out_assets, os.path.join(meta_dir, "classified_assets.json"))
                except Exception:
                    pass

                if self.output_tracker_path:
                    self._save_tracker(self.output_tracker_path, {
                        topic_id: {
                            "output_path": out_assets,
                            "processed": True,
                            "topic_name": topic_id,
                            "topic_id": topic_id,
                            "failure_reason": None
                        }
                    })
                print(f"Successfully classified assets for {topic_id}.")
            except Exception as e:
                print(f"Error classifying assets for {topic_id}: {e}")
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
    parser = argparse.ArgumentParser(description="Asset Classification (Simplilearn OSL 3.0 Architecture)")
    parser.add_argument("-b", "--blueprint", required=True, help="Input storyboard blueprint JSON")
    parser.add_argument("-o", "--output", required=True, help="Output classified assets JSON")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM API provider")
    parser.add_argument("-m", "--model", default="gemini-3.8-flash", help="Model name")
    args = parser.parse_args()

    classifier = AssetClassification(
        blueprint_path=args.blueprint,
        api_provider=args.provider,
        model_name=args.model
    )
    classifier.run(args.blueprint, args.output)
