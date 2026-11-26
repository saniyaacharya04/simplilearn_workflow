#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 3: ASSET CONSTRUCTION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 3
   - Script Name: 3_asset_construction.py
   - Primary Class: AssetConstruction
   - Pipeline Role:
     Synthesizes class-based, reusable Manim visual asset construction blueprints from
     geometric primitives. Builds every asset across 4 structural layers (Foundation,
     Primary structure, Secondary structure, Detail layer) using semantic VGroup hierarchies
     and relative coordinates. Employs vector RAG retrieval against Creative_Assets/
     to adapt established Manim asset patterns and enforces Simplilearn OSL 3.0 geometry tokens
     (10px corner radius, Layout 70 x >= 760px, Layout 20 y >= 270px).

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 2 (2_asset_classification.py):
       - How: Ingests {topic_id}_classified_assets.json via
         2_asset_class_output_tracker.json.
       - Purpose: Supplies the categorized catalog of Asset_Suggestions.
     * Stage 1 (1_generate_instructional_design.py):
       - How: Ingests {topic_id}_storyboard_blueprint.json.
       - Purpose: Supplies scene layout contexts and visual evolution goals.
   - Input Tracker: ppt_trackers/2_asset_class_output_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * {topic_id}_classified_assets.json (Stage 2):
       Location: output/<TOPIC_NAME>/{topic_id}_classified_assets.json
       Content: Procedural asset suggestions per scene.
     * {topic_id}_storyboard_blueprint.json (Stage 1):
       Location: output/<TOPIC_NAME>/{topic_id}_storyboard_blueprint.json
       Content: Storyboard scene blueprints and layout assignments.
     * Input Tracker:
       Location: ppt_trackers/2_asset_class_output_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 2_asset_class_output_tracker.json.
   - Step 2: Queries Creative_Assets/ library for reference Manim code implementations.
   - Step 3: Invokes Gemini 3.8 Flash using CONSTRUCTION_SYSTEM_PROMPT to build detailed
     class architectures for each asset.
   - Step 4: Maps bounding boxes to Manim screen coordinate systems based on SME layout:
     * Layout 70: x_min=-1.48, x_max=6.80, y_min=-3.20, y_max=2.20 (anchor RIGHT).
     * Layout 20: x_min=-6.60, x_max=6.60, y_min=-3.40, y_max=2.10 (anchor CENTER).
     * Layout 100: Minimal lower-third bounds (duration <= 20.0s).
   - Step 5: Injects Simplilearn OSL design tokens (corner radius 0.074, border stroke #CBD5E1).
   - Step 6: Compiles catalog into {topic_id}_constructed_assets.json.
   - Step 7: Atomically updates 3_asset_construct_output_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * {topic_id}_constructed_assets.json:
       Location: output/<TOPIC_NAME>/{topic_id}_constructed_assets.json
       Content: Detailed multi-layer construction specifications for all visual assets.
     * constructed_assets.json:
       Location: output/<TOPIC_NAME>/constructed_assets.json
       Content: Mirrored copy of constructed assets catalog.
     * Output Tracker:
       Location: ppt_trackers/3_asset_construct_output_tracker.json
       Content: Atomic tracker confirming completion of asset construction.

6. DOWNSTREAM CONSUMERS:
   - Stage 6 (6_presentation_composer.py): Integrates constructed assets into spatial layouts.
   - Stage 10 (10_generate_code.py): Synthesizes executable Manim classes from construction specs.
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
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    SME_LAYOUT_100,
    SME_LAYOUT_70,
    SME_LAYOUT_20,
    COLORS,
    HIGHLIGHT_COLOR,
    HIGHLIGHT_THICKNESS,
    HIGHLIGHT_DRAW_TIME
)

try:
    from pipeline.semantic_matcher_asset import match_manim_snippets
except ImportError:
    try:
        from semantic_matcher_asset import match_manim_snippets
    except ImportError:
        def match_manim_snippets(text: str, top_k: int = 2):
            return []

CONSTRUCTION_SYSTEM_PROMPT = """
        ### ROLE

        You are an expert Manim Community Edition visual construction engineer.

        Design reusable, class-based visual assets built from primitives with strong internal structure, semantic decomposition, and high visual fidelity.

        You do NOT design animations.

        ---

        ### INPUTS

        You will receive:

        1. asset_suggestion
        2. visual description
        3. reference construction guidelines
        4. reference Manim asset implementations
        5. concrete instructional context (ZERO PLACEHOLDERS: All containers, labels, and elements must be fully realized with authentic technical labels)

        Produce ONE detailed construction paragraph describing how to build the asset.
        NEVER include placeholder containers, dummy avatars, or placeholder boxes.

        ---

        ### DESIGN GOAL

        The asset should resemble a believable simplified real-world object rather than an icon.

        Optimize for:

        • recognizability
        • structural realism
        • geometric richness
        • semantic decomposition
        • future reusability
        • clean Manim implementation

        The resulting asset should feel comparable in quality and sophistication to the best reference assets.

        ---

        ### REFERENCE UTILIZATION

        Treat both textual references and Manim code references as design knowledge.

        Extract and adapt:

        • decomposition strategies
        • silhouette construction
        • primitive composition patterns
        • layering techniques
        • realism-enhancing details
        • proportion relationships
        • reusable class architecture
        • grouping hierarchies
        • semantic component boundaries

        Do NOT copy specific layouts or coordinates.

        Instead reproduce the level of structural depth, visual richness, and engineering quality demonstrated by the references.

        If multiple references exist, synthesize their strongest ideas into a coherent construction strategy.

        ---

        ### CONSTRUCTION DEPTH

        Build every asset across multiple structural layers:

        1. Foundation layer

        * support structures
        * bases
        * frames
        * grounding geometry

        2. Primary structure

        * dominant functional forms
        * major recognizable volumes

        3. Secondary structure

        * connectors
        * supports
        * subdivisions
        * mechanical relationships

        4. Detail layer

        * rims
        * borders
        * thickness cues
        * internal markers
        * reinforcement features

        Avoid monolithic geometry. Do not stick to just the subcomponent cues present in the asset_suggestion. Think around how the existing suggestions can be redesigned into something more real.

        ---

        ### GEOMETRIC SOPHISTICATION

        Prefer primitives that best match the actual form.

        Combine primitives to approximate real geometry rather than symbolic representations.

        Reflect:

        • curvature
        • symmetry
        • thickness
        • layering
        • articulation
        • mechanical relationships

        Use geometric complexity comparable to the strongest reference assets whenever it improves recognizability.

        ---

        ### STRUCTURAL ARCHITECTURE

        Define:

        • semantic subcomponents
        • VGroup hierarchy
        • logical ownership structure

        Decompose objects according to how humans understand them physically:

        shells, supports, frames, connectors, indicators, hinges, handles, containers, surfaces, internal sections, controls, etc.

        Important regions should remain independent subcomponents.

        ---

        ### RELATIVE CONSTRUCTION

        Use only relative positioning relationships.

        Avoid absolute coordinates.

        Construction should remain stable under scaling and reuse.

        Maintain realistic proportions between components.

        ---

        ### PUBLIC CONTRACT

        Construction should naturally support:

        • public attributes for major components
        • getters for important regions
        • independent access to semantic parts
        • future transformations and interactions

        Do not describe animations.

        ---

        ### OUTPUT FORMAT

        One continuous paragraph.

        Flow:

        Asset overview → Foundation → Primary structure → Secondary structure → Detail layer → Group hierarchy → Public contract.

        ---

        ### SELF-CHECK

        Verify:

        • visually believable
        • not icon-like
        • matches sophistication of reference assets
        • contains layered structural depth
        • preserves semantic subcomponents
        • uses geometry appropriate to the real form
        • avoids monolithic construction
        • uses relative positioning only
        • supports future reuse and interaction
        • contains no animation sequencing

        """

CONSTRUCTION_USER_PROMPT = """
        For generating the detailed animation guidelines, refer to the following
        ------------------------
        The asset_suggestion:
        {asset_suggestion}
        ------------------------
        The original Visual description:
        {visual}
        ------------------------
        The reference scripts:
        {reference_scripts}

        """


class AssetConstruction:
    """
    Synthesizes coordinate-driven geometric construction specifications and retrieves
    procedural Manim code templates for classified visual components.
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
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    def retrieve_annotation_matches(self, visual_data: str, top_k: int = 2) -> str:
        """Fetch reference scripts via RAG on asset suggestions."""
        snippet_content = ""
        try:
            retrieved = match_manim_snippets(visual_data, top_k=top_k)
            for r in retrieved[:top_k]:
                p = Path(r["path"])
                if p.exists():
                    snippet_data = p.read_text(encoding="utf-8")
                    snippet_content += f"\n\n----------Construction Guidelines-------------\n{snippet_data}"
        except Exception as e:
            print(f"  [AssetConstruction] RAG notice: {e}")
        return snippet_content

    def build_local_spec(self, asset_desc: str, sid: int, aid: int, layout: str = "70") -> Dict[str, Any]:
        """Local deterministic fallback specification adhering to OSL 3.0."""
        bounds = {
            "x_min": -1.48 if layout == "70" else (-6.60 if layout == "20" else -5.0),
            "x_max": 6.80 if layout == "70" else (6.60 if layout == "20" else 5.0),
            "y_min": -3.20 if layout == "70" else (-3.40 if layout == "20" else -3.0),
            "y_max": 2.20 if layout == "70" else (2.10 if layout == "20" else -1.5),
            "anchor": "RIGHT" if layout == "70" else ("CENTER" if layout == "20" else "BOTTOM")
        }
        desc_lower = asset_desc.lower()
        if any(w in desc_lower for w in ["flywheel", "pra", "cycle", "revolving", "rotor"]):
            archetype = "VectorFlywheelMechanism"
            guide = "Foundation: Outer beveled gear rim with precision tick notches. Primary: 3 revolving stage pods (Perception #62B7E4, Reasoning #9B99C7, Action #8ECDB7). Secondary: Clockwise flow arcs with feedback loop. Detail: Center spindle hub with bearing rings, rotating spokes, and diagnostic iteration counter badge."
        elif any(w in desc_lower for w in ["infinity", "lemniscate", "figure-8", "interaction loop"]):
            archetype = "VectorInfinityLoopBridge"
            guide = "Foundation: Dual anchor domain disks (Agent left, Environment right). Primary: Continuous parametric figure-8 lemniscate path curve. Secondary: 4 waypoint callout pills (Observe, Decide, Execute, Re-evaluate). Detail: Continuous traveling data packet stream."
        elif any(w in desc_lower for w in ["funnel", "buffer", "ingestion", "intake"]):
            archetype = "VectorContextFunnel"
            guide = "Foundation: Top intake ports for multi-source signals. Primary: 3-stage tapered polygonal funnel body with filtration mesh tiers. Secondary: Bottom collection reservoir cylinder labeled Working Context Buffer. Detail: Trickling data particles."
        elif any(w in desc_lower for w in ["quad", "chamber", "architecture core", "central engine", "engine core"]):
            archetype = "VectorQuadChamberCore"
            guide = "Foundation: Central cognitive hub with glowing core and rotating spokes. Primary: 4 quadrant chambers (Perception, Memory, Reasoning, Action) with wide Layout 20 horizontal spread. Secondary: Connecting bus conduits and orbital synchronization ring. Detail: Clockwise traveling orbital pulse."
        elif any(w in desc_lower for w in ["telemetry", "gauge", "anomaly", "chart", "sensor"]):
            archetype = "VectorTelemetryChart"
            guide = "Foundation: 2D coordinate axes with grid lines. Primary: Smoothly animating continuous signal curve. Secondary: Dashed threshold baseline. Detail: Pulsing anomaly highlight marker."
        elif any(w in desc_lower for w in ["scale", "balance", "tradeoff"]):
            archetype = "PremiumBalanceScale"
            guide = "Foundation: Stepped plinth pedestal. Primary: Fluted column pillar with gimbal pivot and balance beam. Secondary: Twin suspended parabolic pans. Detail: Harmonic ambient sway."
        elif any(w in desc_lower for w in ["shield", "security", "policy", "verify"]):
            archetype = "VectorSecurityShield"
            guide = "Foundation: 2D vector shield body. Primary: Central cryptographic keyhole. Secondary: Verification badge pill. Detail: Pulsing authorization halo."
        elif any(w in desc_lower for w in ["matrix", "2x2", "quadrant", "swot", "prioritization"]):
            archetype = "Vector2x2Matrix"
            guide = "Foundation: 4-quadrant coordinate axes with labeled quadrant cards. Primary: Quadrant focus bounds. Detail: Plotted project dots."
        elif any(w in desc_lower for w in ["sprint", "agile", "scrum", "pdca"]):
            archetype = "VectorAgileSprintCycle"
            guide = "Foundation: Circular sprint feedback loop with 4 milestone pods. Primary: Directional flow arrows. Detail: Orbiting progress dot."
        elif any(w in desc_lower for w in ["kpi", "gauge", "dial", "speedometer", "metric card"]):
            archetype = "VectorKPIGaugeCard"
            guide = "Foundation: Executive metric card container with 10px rounded corners. Primary: Semicircular gauge track with active progress arc and indicator needle. Secondary: Prominent numerical readout counter with baseline subtext. Detail: Breathing needle oscillation updater."
        elif any(w in desc_lower for w in ["heatmap", "risk", "severity", "compliance grid"]):
            archetype = "VectorRiskHeatmap"
            guide = "Foundation: 3x3 Impact vs Likelihood severity grid with pastel-coded risk tiers. Primary: Coordinate axes labels. Secondary: Risk token badges mapped to cells. Detail: Pulsing perimeter focus border on critical risk cells."
        elif any(w in desc_lower for w in ["raci", "governance table", "responsibility matrix", "stakeholder matrix"]):
            archetype = "VectorRACIMatrix"
            guide = "Foundation: Dark slate header bar with stakeholder roles. Primary: Deliverable task rows with rounded cards. Secondary: Color-coded R/A/C/I pills (Mint, Amber, Sky, Lilac). Detail: Dynamic row highlight scanner."
        elif any(w in desc_lower for w in ["funnel", "conversion", "sales funnel", "pipeline funnel"]):
            archetype = "VectorMarketingFunnel"
            guide = "Foundation: Descending tiered conversion funnel. Primary: Proportional rounded width tiers with pastel fills. Secondary: Stage title labels. Detail: Trickling conversion particle flow updater."
        elif any(w in desc_lower for w in ["solar", "photovoltaic", "solar array", "solara grid", "panel"]):
            archetype = "VectorAdvancedSolarArray"
            guide = "Foundation: Dual-axis tracking gimbal mount and aluminum tripod trusses with ground shadow. Primary: Dual angled photovoltaic panel wings with 3x2 silicon wafer cells and silver busbars. Secondary: Glass glare reflection sweep polygon and inverter telemetry status badge. Detail: Continuous reflection sheen sweep and pulsing inverter LED."
        elif any(w in desc_lower for w in ["hammer", "static tool", "passive tool", "manual tool"]):
            archetype = "VectorMechanicalHammerTool"
            guide = "Foundation: Ground shadow and resting plinth pedestal with status badge pill. Primary: Angled ergonomic hammer handle with grip ribs and metallic collar. Secondary: Forged steel striking face and curved claw with central eye block. Detail: Dormant status indicator pulse."
        else:
            archetype = "SimplilearnDiagramBlock"
            guide = "Foundation layer: grounded base container. Primary structure: modular visual components with relative offsets. Secondary structure: directional connectors. Detail layer: 10px rounded borders (#DADCE0) with pastel accent fills."

        return {
            "asset_id": f"s{sid:02d}_asset_{aid:02d}",
            "description": asset_desc,
            "manim_class_archetype": archetype,
            "construction_guidelines": guide,
            "manim_geometry_bounds": bounds,
            "osl_compliance": {
                "corner_radius_px": 10,
                "manim_corner_radius": 0.074,
                "stroke_color": "#CBD5E1",
                "stroke_width": 2,
                "accent_color": "#2C81FE"
            }
        }

    def construct_all_assets(
        self,
        classified_catalog: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes all classified assets across scenes, running RAG retrieval
        and Gemini 3.8 Flash LLM construction synthesis.
        """
        scenes = classified_catalog.get("scenes", [])
        constructed_assets: Dict[str, Any] = {
            "topic": classified_catalog.get("topic", "Technical Lecture"),
            "constructed_catalog": {}
        }

        use_gemini = self.api_provider in ["auto", "gemini"] and self.api_key
        if use_gemini:
            print(f"[*] Synthesizing Manim visual asset construction blueprints via Gemini ({self.model_name})...")
            import google.generativeai as genai
            genai.configure(api_key=self.api_key, transport="rest")
            model = genai.GenerativeModel(self.model_name)

        asset_counter = 1
        for scene in scenes:
            sid = scene.get("scene_id", 1)
            layout = str(scene.get("sme_layout", "70"))
            steps = scene.get("steps", [])

            for step_idx, step in enumerate(steps, 1):
                asset_suggs = step.get("Asset_Suggestion") or []
                if not asset_suggs:
                    continue

                for sugg in asset_suggs:
                    asset_key = f"asset_{asset_counter}"
                    # RAG retrieval against Creative_Assets
                    rag_content = self.retrieve_annotation_matches(sugg, top_k=2)

                    visual_context = f"Scene {sid} Step {step_idx}: {scene.get('title', '')}"

                    construction_text = ""
                    if use_gemini:
                        try:
                            user_prompt = CONSTRUCTION_USER_PROMPT.replace(
                                "{asset_suggestion}", sugg
                            ).replace(
                                "{visual}", visual_context
                            ).replace(
                                "{reference_scripts}", rag_content or "No reference scripts available."
                            )
                            resp = model.generate_content(
                                f"{CONSTRUCTION_SYSTEM_PROMPT}\n\nUser Query: {user_prompt}",
                                generation_config=genai.GenerationConfig(
                                    temperature=0.7,
                                    max_output_tokens=3000
                                )
                            )
                            construction_text = resp.text.strip()
                        except Exception as e:
                            print(f"  [AssetConstruction] Asset {asset_key} LLM fallback: {e}")

                    if not construction_text:
                        local = self.build_local_spec(sugg, sid, asset_counter, layout=layout)
                        construction_text = local["construction_guidelines"]

                    # Determine Manim coordinates based on OSL 3.0 SME Layout
                    if layout == "70":
                        manim_bounds = {"x_min": -1.48, "x_max": 6.80, "y_min": -3.20, "y_max": 2.20, "anchor": "RIGHT"}
                        sme_note = "Strict clearance: x >= 760px (x >= -1.48 Manim). Right-side content canvas."
                    elif layout == "20":
                        manim_bounds = {"x_min": -6.60, "x_max": 6.60, "y_min": -3.40, "y_max": 2.10, "anchor": "CENTER"}
                        sme_note = "Wide canvas (1814px): Keep upper-right corner clear for 20% PIP window. Diagrams below y >= 270px."
                    else:
                        manim_bounds = {"x_min": -5.0, "x_max": 5.0, "y_min": -3.0, "y_max": -1.5, "anchor": "BOTTOM"}
                        sme_note = "Presenter 100% full frame. Minimal lower-third container only (<= 20.0s)."

                    constructed_assets["constructed_catalog"][asset_key] = {
                        "asset_name": asset_key,
                        "scene_id": sid,
                        "layout_context": layout,
                        "asset_suggestion": sugg,
                        "construction_paragraph": construction_text,
                        "manim_geometry_bounds": manim_bounds,
                        "sme_clearance_note": sme_note,
                        "osl_design_tokens": {
                            "corner_radius_px": 10,
                            "manim_corner_radius": 0.074,
                            "stroke_color": "#CBD5E1",
                            "stroke_width": 2,
                            "accent_color": COLORS["sky_blue"]
                        }
                    }
                    asset_counter += 1

        print(f"✓ Asset Construction Complete: Built {len(constructed_assets['constructed_catalog'])} visual asset specifications")
        return constructed_assets

    def run(self, assets_path: str, output_path: str, blueprint_path: Optional[str] = None) -> str:
        with open(assets_path, "r", encoding="utf-8") as f:
            classified_catalog = json.load(f)

        blueprint = None
        if blueprint_path and Path(blueprint_path).exists():
            with open(blueprint_path, "r", encoding="utf-8") as f:
                blueprint = json.load(f)

        specs = self.construct_all_assets(classified_catalog, blueprint=blueprint)

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(specs, f, indent=2, ensure_ascii=False)

        print(f"  Constructed blueprints saved -> {output_path}")
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
                print(f"Skipping {topic_id}: Already processed in asset construction tracker.")
                continue

            topic_dir = os.path.join(self.input_folder, topic_id)
            if not os.path.exists(topic_dir):
                continue

            print(f"Processing Asset Construction for {topic_id}...")
            meta_dir = os.path.join(topic_dir, "metadata_blueprints")
            os.makedirs(meta_dir, exist_ok=True)
            assets_file = os.path.join(meta_dir, f"{topic_id}_classified_assets.json")
            if not os.path.exists(assets_file):
                assets_file = os.path.join(topic_dir, f"{topic_id}_classified_assets.json")
            if not os.path.exists(assets_file):
                assets_file = os.path.join(topic_dir, "classified_assets.json")
            if not os.path.exists(assets_file):
                print(f"Skipping {topic_id}: Missing classified assets.")
                continue

            blueprint_file = os.path.join(meta_dir, f"{topic_id}_storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(topic_dir, f"{topic_id}_storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(meta_dir, "storyboard_blueprint.json")
            if not os.path.exists(blueprint_file):
                blueprint_file = os.path.join(topic_dir, "storyboard_blueprint.json")

            out_constructed = os.path.join(meta_dir, f"{topic_id}_constructed_assets.json")
            try:
                self.run(assets_file, out_constructed, blueprint_path=blueprint_file if os.path.exists(blueprint_file) else None)
                # Also save constructed_assets copy inside meta_dir
                try:
                    shutil.copy2(out_constructed, os.path.join(meta_dir, "constructed_assets.json"))
                    m_slug = getattr(self, "model_name", "model").replace(":", "-").replace("/", "-")
                    shutil.copy2(out_constructed, os.path.join(meta_dir, f"construction_output_{m_slug}.json"))
                except Exception:
                    pass

                if self.output_tracker_path:
                    self._save_tracker(self.output_tracker_path, {
                        topic_id: {
                            "output_path": out_constructed,
                            "processed": True,
                            "topic_name": topic_id,
                            "topic_id": topic_id,
                            "failure_reason": None
                        }
                    })
                print(f"Successfully constructed assets for {topic_id}.")
            except Exception as e:
                print(f"Error constructing assets for {topic_id}: {e}")
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
    parser = argparse.ArgumentParser(description="Asset Construction (Simplilearn OSL 3.0 Architecture)")
    parser.add_argument("-a", "--assets", required=True, help="Input classified assets JSON")
    parser.add_argument("-b", "--blueprint", default=None, help="Optional storyboard blueprint JSON")
    parser.add_argument("-o", "--output", required=True, help="Output constructed assets JSON")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM API provider")
    parser.add_argument("-m", "--model", default="gemini-3.8-flash", help="Model name")
    args = parser.parse_args()

    builder = AssetConstruction(
        api_provider=args.provider,
        model_name=args.model
    )
    builder.run(args.assets, args.output, blueprint_path=args.blueprint)
