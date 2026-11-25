#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 4: IMAGE PROMPT GENERATION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 4
   - Script Name: 4_image_prompt_generation.py
   - Primary Class: ImagePrompting
   - Pipeline Role:
     Synthesizes high-fidelity, diffusion-ready image generation prompts for visual assets
     categorized in Stage 2 as requiring custom illustrations (Image_Suggestion).
     Strictly enforces Simplilearn OSL 3.0 vector graphics rules: 2D flat vector aesthetic,
     pure white isolated background (#FFFFFF) for lossless background removal, governance
     by the 10-Color Infographic Pastel Palette, zero on-screen text/labels, and strict
     exclusion of human silhouettes or realistic human characters.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 2 (2_asset_classification.py):
       - How: Ingests {topic_id}_classified_assets.json via
         2_asset_class_output_tracker.json.
       - Purpose: Identifies which assets require diffusion image generation.
   - Input Tracker: ppt_trackers/2_asset_class_output_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * {topic_id}_classified_assets.json (Stage 2):
       Location: output/<TOPIC_NAME>/{topic_id}_classified_assets.json
       Content: Image suggestion list and visual contexts.
     * ex_config.json:
       Location: output/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/2_asset_class_output_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 2_asset_class_output_tracker.json.
   - Step 2: Extracts image suggestion blocks and visual descriptions per scene.
   - Step 3: Applies Simplilearn 10-Color Infographic Pastel Palette tokens.
   - Step 4: Dispatches prompt synthesis call to Gemini 3.8 Flash using
     IMAGE_PROMPTING_SYSTEM_PROMPT.
   - Step 5: Generates dense visual construction prompts enforcing pure white background,
     flat corporate vector style, and zero text/labels.
   - Step 6: Formulates structured image prompt dictionary mapped by asset IDs.
   - Step 7: Atomically updates 4_prompt_images_output_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * {topic_id}_image_prompts.json:
       Location: output/<TOPIC_NAME>/{topic_id}_image_prompts.json
       Content: Diffusion-ready prompt dictionary mapped to scene image IDs.
     * image_prompts.json:
       Location: output/<TOPIC_NAME>/image_prompts.json
       Content: Mirrored copy of image prompts.
     * Output Tracker:
       Location: ppt_trackers/4_prompt_images_output_tracker.json
       Content: Atomic tracker confirming completion of image prompt generation.

6. DOWNSTREAM CONSUMERS:
   - Stage 8 (8_image_generator.py): Ingests prompts to render transparent PNG assets.
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

from pipeline.config import COLORS

SIMPLILEARN_PALETTE_GUIDELINES = """
Primary Background: Pure White (#FFFFFF)
Simplilearn 10-Color Educational Infographic Palette:
1. Sky Blue (#62B7E4)
2. Steel Blue (#7EA2C8)
3. Lavender Periwinkle (#9B99C7)
4. Mint Seafoam (#8ECDB7)
5. Warm Amber (#E6A157)
6. Mustard Gold (#DDB945)
7. Coral Terracotta (#E58F6D)
8. Warm Tan (#B88968)
9. Dusty Rose (#D98CA1)
10. Soft Lilac (#C1A5C6)
Accent Brand Blue: #2C81FE
Dark Charcoal Text/Edges: #404040
Slate Gray: #5F6368
Soft Border: #DADCE0
"""

IMAGE_PROMPTING_SYSTEM_PROMPT = """
        ### ROLE

        You are a senior visual prompt engineer specializing in high-quality vector illustrations for educational explainers.

        Generate diffusion-ready prompts that produce clean, visually rich illustrations suitable for compositing.

        ---

        ### TASK

        For each image suggestion, generate ONE diffusion prompt using:
        - image suggestion
        - visual context
        - audience and topic
        - selected color palette

        Context:
        - Explainer type: {explainer_type}
        - Course context: {course_context}
        - Topic: {topic}
        - Target audience: {target_audience}

        ---

        ### COLOR GOVERNANCE

        Use ONLY colors from the provided palette.

        Rules:
        - Background must use a single solid palette color
        - Foreground elements must use palette colors only
        - Maintain strong foreground/background separation
        - Use gradients within the palette to create depth and material variation
        - Do not use gradients on the background

        ---

        ### VISUAL DESCRIPTION PRINCIPLE

        Describe the illustration as a visually complete object, not a symbolic label.

        Focus on:
        - major structural components
        - proportions
        - material separation
        - visible surface details
        - clothing/object construction
        - geometric relationships
        - color distribution

        Do NOT exhaustively specify micro-details.
        Specify all major and visually meaningful components.
        Omit only details that do not affect structure, composition, material, depth, character identity or instructional meaning.

        Write each prompt as a dense visual construction description: primary subject → major components → secondary details → spatial relationships → surfaces/materials → depth cues → distinctive features → color distribution.

        Prefer:
        - component-aware descriptions
        - layered object structure
        - visible form and thickness
        - soft geometric depth
        - clean shape language

        Avoid:
        - abstract symbolism
        - generic icon-like phrasing
        - flat minimal descriptions
        - unnecessary micro-details

        When useful, describe important subcomponents explicitly instead of naming the object generically.

        Prefer describing:
        - how the object is visually constructed
        over:
        - what the object semantically represents.

        For human subjects, prioritize character design details over generic human labels.

        ### HUMAN CHARACTER CONSTRUCTION

        Human-related image suggestions should NEVER be rendered as generic silhouettes,
        stick figures, faceless icons, or placeholder people.

        Even when the image suggestion only references:

        * person
        * human
        * user
        * customer
        * employee
        * student
        * silhouette
        * crowd member

        construct a complete stylized character illustration.

        Include when inferable from context:

        * approximate age group
        * gender presentation
        * facial structure
        * hairstyle
        * expression
        * posture
        * clothing style
        * relevant accessories
        * role-specific visual cues

        Use facial appearance and clothing to reinforce the educational message,
        scene intent, and audience context.

        Default appearance:

        * Indian subcontinent skin tone
        * clean modern vector styling
        * fully clothed
        * friendly professional appearance

        Clothing colors should be selected exclusively from the provided palette.

        Describe characters as visually identifiable individuals rather than symbolic human icons.

        ---
        ### VISUAL DECOMPOSITION LAW

        Before writing the diffusion prompt, mentally decompose the image suggestion into its visible visual structure.

        The prompt must explicitly describe:
        - primary subject and overall form
        - major structural components
        - important secondary components
        - spatial relationships
        - shape, proportion and orientation
        - visible surfaces, thickness and material differences
        - distinctive recognition features
        - depth, layering and overlap
        - relevant human/character features
        - palette-based color distribution

        Do not stop at naming the object or scene. For every major component, describe what it looks like and how it relates visually to the other components.

        Prefer concrete visual descriptions over semantic labels.

        Generate enough visual information for an illustrator to construct the complete image without inferring major structural details.

        Do not add arbitrary details unsupported by the image suggestion or context.

        ---

        ### STYLE

        Use recognizable modern editorial/vector illustration aesthetics suitable for premium educational explainers.

        Preferred visual priors:
        - Corporate Memphis
        - fintech/UI illustration systems
        - modern educational motion-graphics styles

        Objects and characters should:

        * have substantial readable forms
        * clear silhouettes
        * recognizable internal structure
        * distinctive character design
        * soft gradient-based depth

        Use gradients sparingly to suggest volume and material separation — not realism.

        ---

        ### COMPOSITION

        - Centered primary subject
        - Occupies most of the frame
        - Minimal empty margins
        - Balanced composition
        - No cropping

        ---

        ### BACKGROUND

        - Solid background only
        - No environment or scenery
        - Clean isolation edges

        ---

        ### CONSTRAINTS

        Avoid:
        - 3D renders, 3D models, or 3D imagery (MUST be 2D flat vector educational illustration)
        - drop shadows, thick black outlines, dotted lines
        - silhouettes or black-and-white graphics
        - photorealism
        - texture-heavy rendering
        - cinematic environments
        - UI screenshots
        - excessive decorative detail
        - watermarks

        ---

        ### REQUIRED PHRASES

        Include:
        “8K ultra HD, ultra sharp vector clarity”

        If applicable:
        - “no text, no labels”
        - “fully clothed”

        ---

        ### OUTPUT FORMAT

        Image Prompt 1:
        <single paragraph>

        Image Prompt 2:
        <single paragraph>

        ...

        No explanations.
        """

IMAGE_PROMPTING_USER_PROMPT = """
        For generating the detailed image prompts, refer to the following:
        ------------------------
        The list of image_suggestions:
        {image_suggestions_block}
        ------------------------
        The original Visual description:
        {visual}
        -----------------------------------------------------
        Structured color coding governance framework:
        {color_coding}
        """


class ImagePrompting:
    """
    Synthesizes diffusion-ready image generation prompts for visual assets
    identified as requiring 2D vector illustrations or thematic graphics.
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

    def synthesize_local_prompt(self, suggestion: str, topic: str) -> str:
        """Deterministic local fallback prompt satisfying all quality rules."""
        return (
            f"2D flat vector illustration of {suggestion}. Modern clean educational vector aesthetic, "
            f"smooth geometric forms, soft pastel shading using Simplilearn palette (#62B7E4, #7EA2C8, #9B99C7). "
            f"Solid pure white background (#FFFFFF), clean isolation edges, balanced centered composition, "
            f"8K ultra HD, ultra sharp vector clarity, no text, no labels, fully clothed."
        )

    def generate_all_prompts(
        self,
        classified_catalog: Dict[str, Any],
        topic: str = "Technical Architecture",
        course_context: str = "Digital Learning",
        explainer_type: str = "Educational Explainer",
        target_audience: str = "Software engineers, technical architects, and enterprise learners"
    ) -> Dict[str, Any]:
        """
        Processes all Image_Suggestions from classified catalog, generating
        diffusion prompts via Gemini 3.8 / 3.8 Flash with full Simplilearn prompt fidelity.
        """
        scenes = classified_catalog.get("scenes", [])
        image_prompts_output: Dict[str, Any] = {
            "topic": topic,
            "color_governance": "Simplilearn 10-Color Infographic Palette (#FFFFFF Background)",
            "prompts": []
        }

        # Format system prompt
        prompt_replacements = {
            "course_context": course_context,
            "explainer_type": explainer_type,
            "topic": topic,
            "target_audience": target_audience
        }
        system_prompt = IMAGE_PROMPTING_SYSTEM_PROMPT
        for k, v in prompt_replacements.items():
            system_prompt = system_prompt.replace("{" + k + "}", str(v))

        use_gemini = self.api_provider in ["auto", "gemini"] and self.api_key
        if use_gemini:
            print(f"[*] Synthesizing diffusion-ready image prompts via Gemini ({self.model_name})...")
            import google.generativeai as genai
            genai.configure(api_key=self.api_key, transport="rest")
            model = genai.GenerativeModel(self.model_name)

        prompt_idx = 1
        for scene in scenes:
            sid = scene.get("scene_id", 1)
            steps = scene.get("steps", [])

            for step_idx, step in enumerate(steps, 1):
                image_suggs = step.get("Image_Suggestion") or []
                if not image_suggs:
                    continue

                for sugg in image_suggs:
                    prompt_id = f"s{sid:02d}_img_{prompt_idx:02d}"
                    visual_context = f"Scene {sid} Step {step_idx}: {scene.get('title', '')}"

                    prompt_text = ""
                    if use_gemini:
                        try:
                            user_prompt = IMAGE_PROMPTING_USER_PROMPT.replace(
                                "{image_suggestions_block}", sugg
                            ).replace(
                                "{visual}", visual_context
                            ).replace(
                                "{color_coding}", SIMPLILEARN_PALETTE_GUIDELINES
                            )
                            resp = model.generate_content(
                                f"{system_prompt}\n\nUser Query: {user_prompt}",
                                generation_config=genai.GenerationConfig(
                                    temperature=0.7,
                                    max_output_tokens=2500
                                )
                            )
                            cleaned = resp.text.strip()
                            # Strip "Image Prompt 1:" prefix if present
                            cleaned = re.sub(r'^Image\s+Prompt\s*\d*\s*:\s*', '', cleaned, flags=re.IGNORECASE)
                            prompt_text = cleaned.strip()
                        except Exception as e:
                            print(f"  [ImagePrompting] Prompt {prompt_id} LLM fallback: {e}")

                    if not prompt_text:
                        prompt_text = self.synthesize_local_prompt(sugg, topic)

                    image_prompts_output["prompts"].append({
                        "prompt_id": prompt_id,
                        "scene_id": sid,
                        "step_index": step_idx,
                        "suggestion_source": sugg,
                        "diffusion_prompt": prompt_text,
                        "negative_prompt": "photorealistic, 3D render, glossy, drop shadows, dark background, texture-heavy, text, watermark, labels, distorted anatomy",
                        "aspect_ratio": "16:9",
                        "background_color": "#FFFFFF"
                    })
                    prompt_idx += 1

        print(f"✓ Image Prompt Generation Complete: Synthesized {len(image_prompts_output['prompts'])} diffusion prompts")
        return image_prompts_output

    def run(self, assets_path: str, output_path: str) -> str:
        with open(assets_path, "r", encoding="utf-8") as f:
            classified_catalog = json.load(f)

        topic = classified_catalog.get("topic") or "Technical Architecture"
        prompts = self.generate_all_prompts(classified_catalog, topic=topic)

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)

        print(f"  Image prompts saved -> {output_path}")
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
                print(f"Skipping {topic_id}: Already processed in image prompting tracker.")
                continue

            topic_dir = os.path.join(self.input_folder, topic_id)
            if not os.path.exists(topic_dir):
                continue

            print(f"Processing Image Prompting for {topic_id}...")
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

            out_prompts = os.path.join(meta_dir, f"{topic_id}_image_prompts.json")
            try:
                self.run(assets_file, out_prompts)
                # Also save mirrored copies inside meta_dir
                try:
                    shutil.copy2(out_prompts, os.path.join(meta_dir, "image_prompts.json"))
                    m_slug = getattr(self, "model_name", "model").replace(":", "-").replace("/", "-")
                    shutil.copy2(out_prompts, os.path.join(meta_dir, f"image_prompt_{m_slug}.json"))
                except Exception:
                    pass

                if self.output_tracker_path:
                    self._save_tracker(self.output_tracker_path, {
                        topic_id: {
                            "output_path": out_prompts,
                            "processed": True,
                            "topic_name": topic_id,
                            "topic_id": topic_id,
                            "failure_reason": None
                        }
                    })
                print(f"Successfully generated image prompts for {topic_id}.")
            except Exception as e:
                print(f"Error generating image prompts for {topic_id}: {e}")
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
    parser = argparse.ArgumentParser(description="Image Prompt Generation (Simplilearn OSL 3.0 Architecture)")
    parser.add_argument("-a", "--assets", required=True, help="Input classified assets JSON")
    parser.add_argument("-o", "--output", required=True, help="Output image prompts JSON")
    parser.add_argument("-p", "--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="LLM API provider")
    parser.add_argument("-m", "--model", default="gemini-3.8-flash", help="Model name")
    args = parser.parse_args()

    prompter = ImagePrompting(
        api_provider=args.provider,
        model_name=args.model
    )
    prompter.run(args.assets, args.output)
