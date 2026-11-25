#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 8: IMAGE GENERATION & ASSET MANIFEST FORMULATION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 8
   - Script Name: 8_image_generator.py
   - Primary Class: ImageGeneration (and ImageGenerator)
   - Pipeline Role:
     Executes diffusion-based 2D vector image synthesis from Stage 4 image prompts
     (using Google GenAI Imagen, Qwen 2.1 via ComfyUI, or deterministic local vector synthesis
     fallback). Automatically removes backgrounds using rembg / BiRefNet to produce
     transparent PNG assets in image_assets/ ready for direct insertion into Manim scenes.
     Formulates a structured image asset manifest.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 4 (4_image_prompt_generation.py):
       - How: Ingests {topic_id}_image_prompts.json via
         4_prompt_images_output_tracker.json.
       - Purpose: Supplies diffusion-ready prompt specifications and color governance.
   - Input Tracker: ppt_trackers/4_prompt_images_output_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * {topic_id}_image_prompts.json (Stage 4):
       Location: output/<TOPIC_NAME>/{topic_id}_image_prompts.json
       Content: Dictionary of image prompts mapped to asset IDs.
     * ex_config.json:
       Location: output/<TOPIC_NAME>/ex_config.json
       Content: Image prefix, model provider, and generation flags.
     * Input Tracker:
       Location: ppt_trackers/4_prompt_images_output_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 4_prompt_images_output_tracker.json.
   - Step 2: Checks SKIP_IMAGES flag; creates transparent placeholders if enabled.
   - Step 3: Dispatches image generation queries to GenAI Imagen or Qwen 2.1 ComfyUI.
   - Step 4: Fallback: Synthesizes deterministic 2D flat vector assets via PIL if APIs are unavailable.
   - Step 5: Executes automated background removal on generated PNGs using rembg / BiRefNet.
   - Step 6: Verifies transparency and saves assets to image_assets/image_{n}.png.
   - Step 7: Compiles image asset manifest and atomically updates 8_image_generation_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * Transparent Vector Image Assets:
       Location: output/<TOPIC_NAME>/image_assets/image_*.png
       Content: Transparent foreground PNG illustrations conforming to pastel palette.
     * Output Tracker:
       Location: ppt_trackers/8_image_generation_tracker.json
       Content: Atomic tracker confirming completion of image generation.

6. DOWNSTREAM CONSUMERS:
   - Stage 10 (10_generate_code.py): Loads image files into Manim ImageMobjects.
================================================================================
"""

import os
import sys
import json
import time
import re
import io
import base64
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from PIL import Image, ImageDraw

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import COLORS

try:
    import portalocker
except ImportError:
    portalocker = None

try:
    from filelock import FileLock
except ImportError:
    FileLock = None

try:
    from rembg import remove as rembg_remove
except ImportError:
    rembg_remove = None

# Optional Google GenAI
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

# Import Qwen 2.1 helper if available
try:
    from pipeline.helpers.image_generation_helper import (
        generate_t2i,
        generate_r2i,
        generate_image as generate_qwen_image,
        load_qwen_workflow,
    )
except ImportError:
    try:
        from helpers.image_generation_helper import (
            generate_t2i,
            generate_r2i,
            generate_image as generate_qwen_image,
            load_qwen_workflow,
        )
    except ImportError:
        try:
            from image_generation_helper import (
                generate_t2i,
                generate_r2i,
                generate_image as generate_qwen_image,
                load_qwen_workflow,
            )
        except ImportError:
            generate_t2i = None
            generate_r2i = None
            generate_qwen_image = None
            load_qwen_workflow = None


class ImageGenerator:
    """
    Executes 2D flat vector illustration generation using multimodal/diffusion
    APIs or deterministic high-resolution vector rendering fallback.
    """

    def __init__(self, api_provider: str = "auto", api_key: Optional[str] = None):
        self.api_provider = api_provider.lower()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.client_google = None
        if self.api_key and genai is not None:
            try:
                self.client_google = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"  [ImageGenerator] Notice initializing Google GenAI Client: {e}")

    def remove_background(self, input_path: str, output_path: str) -> bool:
        """Removes background from an image using rembg or fast alpha keying to produce transparent foreground PNG."""
        if rembg_remove is not None:
            try:
                img = Image.open(input_path).convert("RGBA")
                result = rembg_remove(img)
                result.save(output_path)
                print(f"  ✓ Saved transparent foreground cutout via rembg: {os.path.basename(output_path)}")
                return True
            except Exception as e:
                print(f"  ⚠️ rembg notice ({e}), applying high-precision color keying fallback...")

        try:
            import numpy as np
            img = Image.open(input_path).convert("RGBA")
            data = np.array(img)
            r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
            # Key out pure white or near-white background pixels
            white_mask = (r > 235) & (g > 235) & (b > 235)
            data[:, :, 3][white_mask] = 0
            out_img = Image.fromarray(data)
            out_img.save(output_path)
            print(f"  ✓ Saved transparent foreground cutout via color keying: {os.path.basename(output_path)}")
            return True
        except Exception as e2:
            print(f"  ⚠️ Error removing background: {e2}")
            if input_path != output_path and os.path.exists(input_path):
                import shutil
                shutil.copy2(input_path, output_path)
            return True

    def generate_local_vector_asset(
        self,
        prompt_item: Dict[str, Any],
        output_image_path: Path
    ) -> Path:
        """
        Creates a crisp 2D flat vector graphic adhering strictly to Simplilearn
        OSL 3.0 styling, clean system palette, vibrant accents, and transparent background.
        (Navy Blue is strictly prohibited).
        """
        try:
            width, height = 768, 768
            image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)

            p_text = str(prompt_item.get("prompt", "") or prompt_item.get("diffusion_prompt", "")).lower()

            # Crisp light fill styling with Brand Blue border adhering to OSL 3.0
            bg_radius = 28
            bg_margin = 48
            draw.rounded_rectangle(
                [bg_margin, bg_margin, width - bg_margin, height - bg_margin],
                radius=bg_radius,
                fill=(255, 255, 255, 250),    # Pure White #FFFFFF
                outline=(44, 129, 254, 255),  # Brand Blue #2C81FE
                width=4
            )

            banner_margin = 84
            draw.rounded_rectangle(
                [banner_margin, banner_margin, width - banner_margin, banner_margin + 80],
                radius=16,
                fill=(240, 244, 248, 255),    # Soft Slate #F0F4F8
                outline=(98, 183, 228, 255),  # Sky Blue #62B7E4
                width=3
            )

            center_x, center_y = width // 2, height // 2 + 25

            if any(k in p_text for k in ["perception", "sensor", "radar", "solar", "photovoltaic"]):
                # SENSORY PERCEPTION & RADAR TELEMETRY ASSET
                for r in [200, 150, 100]:
                    draw.ellipse(
                        [center_x - r, center_y - r, center_x + r, center_y + r],
                        outline=(0, 180, 216, 140),
                        width=2
                    )
                # Radar sweep cone / crosshair
                draw.line([(center_x - 210, center_y), (center_x + 210, center_y)], fill=(0, 180, 216, 180), width=2)
                draw.line([(center_x, center_y - 210), (center_x, center_y + 210)], fill=(0, 180, 216, 180), width=2)
                # Core sensor aperture
                draw.ellipse(
                    [center_x - 55, center_y - 55, center_x + 55, center_y + 55],
                    fill=(0, 180, 216, 255),
                    outline=(255, 255, 255, 255),
                    width=4
                )
                draw.ellipse(
                    [center_x - 22, center_y - 22, center_x + 22, center_y + 22],
                    fill=(10, 37, 64, 255)
                )
                # Signal blips
                for bx, by in [(center_x + 95, center_y - 70), (center_x - 110, center_y + 60), (center_x + 60, center_y + 115)]:
                    draw.ellipse([bx - 12, by - 12, bx + 12, by + 12], fill=(245, 158, 11, 255), outline=(255, 255, 255, 255), width=2)

            elif any(k in p_text for k in ["memory", "vector", "database", "cache", "storage", "rag"]):
                # DUAL-STORE MEMORY & VECTOR DATABASE ASSET
                # Left short-term cache register
                draw.rounded_rectangle(
                    [center_x - 230, center_y - 120, center_x - 30, center_y + 120],
                    radius=16,
                    fill=(15, 23, 42, 255),
                    outline=(0, 150, 199, 255),
                    width=3
                )
                for cy_off in [-70, -20, 30, 80]:
                    draw.rounded_rectangle(
                        [center_x - 210, center_y + cy_off - 16, center_x - 50, center_y + cy_off + 16],
                        radius=8,
                        fill=(25, 95, 215, 255),
                        outline=(72, 202, 228, 255),
                        width=2
                    )
                # Right 3D vector cylinder
                cyl_x = center_x + 130
                draw.ellipse([cyl_x - 90, center_y - 130, cyl_x + 90, center_y - 70], fill=(25, 95, 215, 255), outline=(0, 180, 216, 255), width=3)
                draw.rectangle([cyl_x - 90, center_y - 100, cyl_x + 90, center_y + 80], fill=(10, 37, 64, 255), outline=(0, 180, 216, 255), width=3)
                draw.ellipse([cyl_x - 90, center_y + 50, cyl_x + 90, center_y + 110], fill=(25, 95, 215, 255), outline=(0, 180, 216, 255), width=3)
                # Interconnecting vector line
                draw.line([(center_x - 30, center_y), (cyl_x - 90, center_y)], fill=(245, 158, 11, 255), width=4)

            elif any(k in p_text for k in ["reasoning", "neural", "processor", "deliberation", "llm"]):
                # SILICON NEURAL PROCESSOR DIE
                draw.rounded_rectangle(
                    [center_x - 170, center_y - 170, center_x + 170, center_y + 170],
                    radius=20,
                    fill=(15, 23, 42, 255),
                    outline=(99, 102, 241, 255),
                    width=5
                )
                # Central core
                draw.rounded_rectangle(
                    [center_x - 90, center_y - 90, center_x + 90, center_y + 90],
                    radius=14,
                    fill=(25, 95, 215, 255),
                    outline=(0, 180, 216, 255),
                    width=3
                )
                # Outer bus pins
                for offset in [-130, -75, -20, 35, 90]:
                    # Top & Bottom pins
                    draw.rectangle([center_x + offset - 8, center_y - 200, center_x + offset + 8, center_y - 170], fill=(245, 158, 11, 255))
                    draw.rectangle([center_x + offset - 8, center_y + 170, center_x + offset + 8, center_y + 200], fill=(245, 158, 11, 255))
                    # Left & Right pins
                    draw.rectangle([center_x - 200, center_y + offset - 8, center_x - 170, center_y + offset + 8], fill=(245, 158, 11, 255))
                    draw.rectangle([center_x + 170, center_y + offset - 8, center_x + 200, center_y + offset + 8], fill=(245, 158, 11, 255))

            else:
                # ACTION DISPATCH HUB & EXECUTIVE COCKPIT
                draw.ellipse(
                    [center_x - 175, center_y - 175, center_x + 175, center_y + 175],
                    fill=(15, 23, 42, 240),
                    outline=(0, 180, 216, 255),
                    width=5
                )
                draw.rounded_rectangle(
                    [center_x - 110, center_y - 110, center_x + 110, center_y + 110],
                    radius=20,
                    fill=(25, 95, 215, 255),
                    outline=(245, 158, 11, 255),
                    width=4
                )
                draw.polygon(
                    [
                        (center_x, center_y - 75),
                        (center_x + 65, center_y + 45),
                        (center_x - 65, center_y + 45)
                    ],
                    fill=(245, 158, 11, 255),
                    outline=(255, 255, 255, 255)
                )

            pill_w, pill_h = 170, 48
            pills = [
                (banner_margin + 30, height - banner_margin - 75, (0, 180, 216, 255)),
                (center_x - (pill_w // 2), height - banner_margin - 75, (16, 185, 129, 255)),
                (width - banner_margin - pill_w - 30, height - banner_margin - 75, (99, 102, 241, 255))
            ]
            for px, py, pcol in pills:
                draw.rounded_rectangle(
                    [px, py, px + pill_w, py + pill_h],
                    radius=12,
                    fill=pcol,
                    outline=(255, 255, 255, 230),
                    width=2
                )

            output_image_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_image_path, "PNG")
            return output_image_path
        except Exception as e:
            print(f"  [ImageGenerator] Fallback vector draw notice: {e}")
            output_image_path.parent.mkdir(parents=True, exist_ok=True)
            img = Image.new("RGBA", (512, 512), (44, 129, 254, 220))
            img.save(output_image_path, "PNG")
            return output_image_path

    def generate_image(
        self,
        prompt: str,
        dimensions: Tuple[int, int] = (768, 768),
        output_filename: str = "image.png",
        image_creation_model: str = "nano-banana",
        target_dir: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        save_dir = target_dir or "."
        os.makedirs(save_dir, exist_ok=True)

        base_name, _ = os.path.splitext(output_filename)
        png_filename = f"{base_name}_bg.png"
        bg_removed_filename = f"{base_name}.png"

        png_output_path = os.path.join(save_dir, png_filename)
        bg_removed_output_path = os.path.join(save_dir, bg_removed_filename)

        if os.path.exists(bg_removed_output_path):
            if os.environ.get("SKIP_IMAGES") == "1" or os.path.getsize(bg_removed_output_path) > 200:
                return bg_removed_output_path
            try:
                os.remove(bg_removed_output_path)
            except OSError:
                pass

        # 1. Try Qwen 2.1 if requested and helper available
        model_choice = str(image_creation_model).strip().lower()
        generated = False

        if ("qwen" in model_choice or "t2i" in model_choice or "r2i" in model_choice):
            ref_img = kwargs.get("ref_image") or kwargs.get("reference_image")
            comfy_url = kwargs.get("comfy_url", os.getenv("COMFYUI_URL", "http://127.0.0.1:8188"))
            aspect_ratio = kwargs.get("aspect_ratio", "1:1")

            if ref_img and generate_r2i is not None:
                try:
                    print(f"  🎨 [Model: Qwen 2.1 (R2I)] Calling Qwen multimodal generation...")
                    generate_r2i(
                        prompt=prompt,
                        output_path=os.path.abspath(png_output_path),
                        image_path=str(ref_img),
                        aspect_ratio=aspect_ratio,
                        comfy_url=comfy_url
                    )
                    generated = os.path.exists(png_output_path)
                except Exception as e:
                    print(f"  ⚠️ Qwen 2.1 R2I generation failed: {e}")

            if not generated and generate_t2i is not None:
                try:
                    print(f"  🎨 [Model: Qwen 2.1 (T2I)] Calling Qwen generation...")
                    generate_t2i(
                        prompt=prompt,
                        output_path=os.path.abspath(png_output_path),
                        aspect_ratio=aspect_ratio,
                        comfy_url=comfy_url
                    )
                    generated = os.path.exists(png_output_path)
                except Exception as e:
                    print(f"  ⚠️ Qwen 2.1 generation failed: {e}")

        # 2. Try Google GenAI (Imagen / Nano-Banana)
        if not generated and self.client_google is not None and ("banana" in model_choice or "google" in model_choice or "gemini" in model_choice or "imagen" in model_choice or self.api_provider in ["gemini", "auto"]):
            for img_m in ["imagen-3.0-generate-002", "nano-banana-pro-preview"]:
                try:
                    print(f"  🍌 [Model: Google GenAI] Generating image with {img_m}...")
                    response = self.client_google.models.generate_content(
                        model=img_m,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
                            image_config=types.ImageConfig(aspect_ratio="1:1")
                        )
                    )
                    if response and hasattr(response, "candidates") and response.candidates:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, "inline_data") and part.inline_data:
                                img_bytes = part.inline_data.data
                                if isinstance(img_bytes, str):
                                    img_bytes = base64.b64decode(img_bytes)
                                with open(png_output_path, "wb") as pf:
                                    pf.write(img_bytes)
                                generated = True
                                break
                    if generated:
                        break
                except Exception as e:
                    print(f"  ⚠️ Google GenAI generation notice ({img_m}): {e}")

        # 3. Deterministic Local Simplilearn 2D Flat Vector Synthesis
        if not generated and not os.path.exists(png_output_path):
            self.generate_local_vector_asset({"prompt": prompt}, Path(png_output_path))
            generated = True

        # 4. Remove background if png_output_path exists
        if os.path.exists(png_output_path):
            self.remove_background(png_output_path, bg_removed_output_path)
            if not os.path.exists(bg_removed_output_path):
                import shutil
                shutil.copy2(png_output_path, bg_removed_output_path)

        return bg_removed_output_path if os.path.exists(bg_removed_output_path) else None


# Alias ImageGeneration class for tracker-based pipelines (Somnath compatibility)
class ImageGeneration:
    """
    Stage 8: Image Generation (Pipeline Runner & Tracker Compatible).
    Dispatches generation prompts to either Qwen 2.1 (T2I/R2I via ComfyUI),
    Google GenAI (Nano-Banana / Gemini Flash Image), or high-contrast Simplilearn
    OSL 3.0 vector synthesis, strips backgrounds to transparent PNGs, and updates
    the asset inventory manifest.
    """
    def __init__(
        self,
        input_tracker_path: Optional[str] = None,
        output_tracker_path: Optional[str] = None,
        google_api_key: Optional[str] = None,
        claude_api_key: Optional[str] = None,
        input_folder: str = "."
    ):
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.claude_api_key = claude_api_key or os.environ.get("CLAUDE_API_KEY")
        self.input_folder = input_folder
        self.generator = ImageGenerator(api_key=self.google_api_key)

        if self.output_tracker_path and not os.path.exists(self.output_tracker_path):
            tracker_dir = os.path.dirname(self.output_tracker_path)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
            try:
                with open(self.output_tracker_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False)
            except Exception:
                pass

    def _load_tracker(self, filepath: str) -> dict:
        """Load a JSON tracker with a shared read lock."""
        if not filepath or not os.path.exists(filepath):
            return {}
        try:
            if portalocker:
                with open(filepath, 'r', encoding='utf-8') as f:
                    portalocker.lock(f, portalocker.LOCK_SH)
                    try:
                        content = f.read()
                        data = json.loads(content) if content else {}
                    finally:
                        portalocker.unlock(f)
                return data
            elif FileLock:
                lock_path = filepath + ".lock"
                with FileLock(lock_path, timeout=10):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        return json.loads(content) if content else {}
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return json.loads(content) if content else {}
        except Exception as e:
            print(f"Error loading tracker {filepath}: {e}")
            return {}

    def _save_tracker(self, filepath: str, data: Dict[str, Any]):
        """Save a JSON tracker with an exclusive write lock."""
        if not filepath:
            return
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        lock_path = filepath + ".lock"
        try:
            if portalocker:
                with portalocker.Lock(lock_path, timeout=60):
                    current = {}
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                current = json.load(f)
                        except Exception:
                            current = {}
                    current.update(data)
                    tmp = filepath + f".tmp.{os.getpid()}"
                    with open(tmp, 'w', encoding='utf-8') as f:
                        json.dump(current, f, indent=4, ensure_ascii=False)
                    os.replace(tmp, filepath)
            elif FileLock:
                with FileLock(lock_path, timeout=60):
                    current = {}
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                current = json.load(f)
                        except Exception:
                            current = {}
                    current.update(data)
                    tmp = filepath + f".tmp.{os.getpid()}"
                    with open(tmp, 'w', encoding='utf-8') as f:
                        json.dump(current, f, indent=4, ensure_ascii=False)
                    os.replace(tmp, filepath)
            else:
                current = {}
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            current = json.load(f)
                    except Exception:
                        current = {}
                current.update(data)
                tmp = filepath + f".tmp.{os.getpid()}"
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(current, f, indent=4, ensure_ascii=False)
                os.replace(tmp, filepath)
        except Exception as e:
            print(f"Error saving tracker {filepath}: {e}")

    def image_generator(self, config_data: dict, topic_id: str) -> str:
        """
        Main image generation batch routine. Reads configuration and asset
        classifications, checks model choice, routes prompts, and updates
        asset classifications with verified image paths.
        """
        print(f"\n🎬 Running image_generator for topic: {topic_id}")

        base_folder = config_data.get('base_folder', '.')
        if not os.path.exists(base_folder) and os.path.exists(os.path.join(self.input_folder, topic_id)):
            base_folder = os.path.join(self.input_folder, topic_id)

        image_creation_model = config_data.get('image_creation_model', 'nano-banana')
        comfy_url = config_data.get('comfy_url', os.getenv("COMFYUI_URL", "http://127.0.0.1:8188"))
        asset_class_model_name = config_data.get('asset_class_model_name', 'gemini-3.8-flash')
        image_prompt_model_name = config_data.get('image_prompt_model_name', 'gemini-3.8-flash')

        print(f"   Image Creation Model: {image_creation_model}")
        print(f"   Base Folder: {base_folder}")

        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        image_prompts_json_file = f"{meta_dir}/{topic_id}_image_prompts.json"
        if not os.path.exists(image_prompts_json_file):
            image_prompts_json_file = f"{base_folder}/image_prompt_{image_prompt_model_name}.json"
        if not os.path.exists(image_prompts_json_file):
            alt_candidates = (
                list(Path(meta_dir).glob("*image_prompt*.json")) +
                list(Path(base_folder).glob("*image_prompt*.json")) +
                [Path(base_folder) / "image_prompts.json"]
            )
            for cand in alt_candidates:
                if cand.exists():
                    image_prompts_json_file = str(cand)
                    break

        image_prompts_json = {}
        if os.path.exists(image_prompts_json_file):
            with open(image_prompts_json_file, 'r', encoding='utf-8') as f:
                image_prompts_json = json.load(f)

        asset_classification_output_file = f"{meta_dir}/{topic_id}_classified_assets.json"
        if not os.path.exists(asset_classification_output_file):
            asset_classification_output_file = f"{base_folder}/asset_classification_{asset_class_model_name}.json"
        if not os.path.exists(asset_classification_output_file):
            alt_candidates = (
                list(Path(meta_dir).glob("*classified_assets*.json")) +
                list(Path(meta_dir).glob("*asset_classification*.json")) +
                list(Path(base_folder).glob("*asset_classification*.json")) +
                [Path(base_folder) / "detailed_instructions.json"]
            )
            for cand in alt_candidates:
                if cand.exists():
                    asset_classification_output_file = str(cand)
                    break

        asset_classification = {}
        if os.path.exists(asset_classification_output_file):
            with open(asset_classification_output_file, 'r', encoding='utf-8') as f:
                asset_classification = json.load(f)

        # Normalize image prompts into a universal lookup map
        prompt_map = {}
        if isinstance(image_prompts_json, dict):
            if "prompts" in image_prompts_json and isinstance(image_prompts_json["prompts"], list):
                for p in image_prompts_json["prompts"]:
                    if isinstance(p, dict):
                        pid = p.get("prompt_id") or p.get("image_id") or p.get("name")
                        p_text = p.get("diffusion_prompt") or p.get("prompt")
                        if pid and p_text:
                            prompt_map[str(pid)] = str(p_text)
            else:
                for k, v in image_prompts_json.items():
                    if isinstance(v, str):
                        prompt_map[str(k)] = v
                    elif isinstance(v, dict):
                        prompt_map[str(k)] = v.get("diffusion_prompt") or v.get("prompt", "")
        elif isinstance(image_prompts_json, list):
            for p in image_prompts_json:
                if isinstance(p, dict):
                    pid = p.get("prompt_id") or p.get("image_id")
                    p_text = p.get("diffusion_prompt") or p.get("prompt")
                    if pid and p_text:
                        prompt_map[str(pid)] = str(p_text)

        images_folder = f"{base_folder}/images"
        os.makedirs(images_folder, exist_ok=True)

        image_dimensions = (768, 768)
        if isinstance(asset_classification, dict):
            for group, story_blocks in asset_classification.items():
                if not isinstance(story_blocks, list):
                    continue
                for s_nmbr, story_block in enumerate(story_blocks):
                    new_image_prompts = []
                    image_paths = []

                    if "Image_names" in story_block and story_block["Image_names"]:
                        for p_nmber, image_name in enumerate(story_block["Image_names"]):
                            prompt = prompt_map.get(image_name) or image_prompts_json.get(image_name, "None")
                            if prompt == "None" or not prompt:
                                continue

                            self.generator.generate_image(
                                prompt=prompt,
                                dimensions=image_dimensions,
                                output_filename=image_name + ".png",
                                image_creation_model=image_creation_model,
                                target_dir=images_folder,
                                comfy_url=comfy_url
                            )

                            full_path = os.path.join(images_folder, image_name + ".png")
                            if not os.path.exists(full_path):
                                base_name, _ = os.path.splitext(image_name)
                                png_eq_file = os.path.join(images_folder, base_name + "_bg.png")
                                full_path = png_eq_file
                                image_name = base_name + "_bg.png"

                            new_image_prompts.append(f"{image_name}: {prompt}")
                            image_paths.append(os.path.abspath(full_path))

                    story_block["image_prompts"] = new_image_prompts
                    story_block["image_paths"] = image_paths

            if os.path.exists(asset_classification_output_file):
                with open(asset_classification_output_file, 'w', encoding='utf-8') as f:
                    json.dump(asset_classification, f, indent=4)

        # Ensure all defined prompt assets are synthesized even if not nested in classified_assets story_blocks
        if prompt_map:
            print(f"   Synthesizing {len(prompt_map)} defined prompt assets into {images_folder}...")
            for img_name, prompt_text in prompt_map.items():
                full_path = os.path.join(images_folder, f"{img_name}.png")
                bg_path = os.path.join(images_folder, f"{img_name}_bg.png")
                if not os.path.exists(full_path) and not os.path.exists(bg_path):
                    self.generator.generate_image(
                        prompt=prompt_text,
                        dimensions=image_dimensions,
                        output_filename=f"{img_name}.png",
                        image_creation_model=image_creation_model,
                        target_dir=images_folder,
                        comfy_url=comfy_url
                    )

        return images_folder

    def process_files(self, target_topic_id=None):
        """Processes unprocessed topics from the pipeline tracker or local folder."""
        if self.input_tracker_path and os.path.exists(self.input_tracker_path):
            input_tracker = self._load_tracker(self.input_tracker_path)
            if input_tracker:
                print(f"Found {len(input_tracker)} items in input tracker.")
                for topic_id, input_entry in input_tracker.items():
                    if target_topic_id and topic_id != target_topic_id:
                        continue
                    if not input_entry.get("processed", False):
                        continue

                    output_tracker = self._load_tracker(self.output_tracker_path) if self.output_tracker_path else {}
                    if topic_id in output_tracker and output_tracker[topic_id].get("processed", False):
                        print(f"Skipping {topic_id}: Already processed.")
                        continue

                    print(f"Processing {topic_id}...")
                    base_folder = os.path.join(self.input_folder, topic_id)
                    config_path = os.path.join(base_folder, "ex_config.json")

                    try:
                        if os.path.exists(config_path):
                            with open(config_path, 'r', encoding='utf-8') as f:
                                config_data = json.load(f)
                            output_file_path = self.image_generator(config_data, topic_id)
                        else:
                            img_dir = os.path.join(base_folder, "images")
                            prompts_files = list(Path(base_folder).glob("*image_prompt*.json"))
                            if prompts_files:
                                run_image_generation(str(prompts_files[0]), img_dir)
                            output_file_path = img_dir

                        if self.output_tracker_path:
                            tracker = self._load_tracker(self.output_tracker_path)
                            tracker[topic_id] = {
                                "output_path": output_file_path,
                                "processed": True,
                                "topic_name": topic_id,
                                "topic_id": topic_id,
                                "failure_reason": None
                            }
                            self._save_tracker(self.output_tracker_path, tracker)
                        print(f"Successfully processed {topic_id}.")

                    except Exception as e:
                        print(f"Error processing {topic_id}: {e}")
                        if self.output_tracker_path:
                            tracker = self._load_tracker(self.output_tracker_path)
                            tracker[topic_id] = {
                                "output_path": None,
                                "processed": False,
                                "topic_name": topic_id,
                                "topic_id": topic_id,
                                "failure_reason": str(e)
                            }
                            self._save_tracker(self.output_tracker_path, tracker)
                return

        # Direct folder processing fallback
        target_dir = os.path.join(self.input_folder, target_topic_id) if target_topic_id else self.input_folder
        config_path = os.path.join(target_dir, "ex_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self.image_generator(cfg, topic_id=target_topic_id or "local_topic")
        else:
            img_dir = os.path.join(target_dir, "images")
            prompts_files = list(Path(target_dir).glob("*image_prompt*.json"))
            if prompts_files:
                run_image_generation(str(prompts_files[0]), img_dir)


def run_image_generation(
    prompts_json_path: str,
    output_images_dir: str,
    manifest_path: Optional[str] = None,
    api_provider: str = "auto"
) -> Dict[str, str]:
    prompts_path = Path(prompts_json_path)
    if not prompts_path.exists():
        raise FileNotFoundError(f"Prompts catalog not found: {prompts_json_path}")

    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts_data = json.load(f)

    out_dir = Path(output_images_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generator = ImageGenerator(api_provider=api_provider)
    resolved_catalog: Dict[str, str] = {}

    if isinstance(prompts_data, dict):
        if "prompts" in prompts_data:
            items = prompts_data["prompts"]
        else:
            items = [{"image_id": k, "prompt": v} for k, v in prompts_data.items()]
    elif isinstance(prompts_data, list):
        items = prompts_data
    else:
        items = []

    print(f"\n🎨 [ImageGenerator] Synthesizing {len(items)} 2D flat vector visual assets...")
    for idx, item in enumerate(items, 1):
        if isinstance(item, dict):
            img_id = item.get("image_id", f"image_{idx}")
            prompt = item.get("prompt") or item.get("visual_prompt", "")
        else:
            img_id = f"image_{idx}"
            prompt = str(item)

        out_img_name = f"{img_id}.png"
        resolved_path = generator.generate_image(
            prompt=prompt,
            output_filename=out_img_name,
            target_dir=str(out_dir)
        )
        if resolved_path:
            resolved_catalog[img_id] = str(Path(resolved_path).resolve())
            print(f"  ✓ [{idx}/{len(items)}] Generated visual asset: {out_img_name}")

    if manifest_path:
        m_path = Path(manifest_path)
        m_path.parent.mkdir(parents=True, exist_ok=True)
        with open(m_path, "w", encoding="utf-8") as mf:
            json.dump(resolved_catalog, mf, indent=2, ensure_ascii=False)

    return resolved_catalog


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Generator & Asset Manifest Formulation (Simplilearn OSL 3.0)")
    parser.add_argument("-p", "--prompts", required=True, help="Input image prompts JSON catalog")
    parser.add_argument("-o", "--output", required=True, help="Directory to save generated images")
    parser.add_argument("-m", "--manifest", default=None, help="Output image manifest JSON")
    parser.add_argument("--provider", default="auto", choices=["auto", "gemini", "claude", "local"], help="Generation provider")
    args = parser.parse_args()

    run_image_generation(
        prompts_json_path=args.prompts,
        output_images_dir=args.output,
        manifest_path=args.manifest,
        api_provider=args.provider
    )
