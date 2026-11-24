"""
Enterprise Image Generator for Educational Animation Pipeline.

Supports Multiple Generation Engines:
  1. Q-Image (Fast 9-step ComfyUI Turbo UNET with Qwen 3.4B)
  2. Nano-Banana (Google GenAI nano-banana-pro-preview / gemini-2.5-flash-image)
  3. Qwen 2.1 Text-to-Image (T2I) via ComfyUI
  4. Qwen 2.1 Reference-to-Image (R2I) with multimodal conditioning
  5. Integrated Automatic Background Removal via BiRefNet ('image_bg_remover.py')
"""

import os
import sys
import json
import time
import copy
import glob
import random
import re
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Union, Tuple, Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# 1. CONFIGURATION & URLS
# ==============================================================================
COMFYUI_URL = "http://127.0.0.1:8188"

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent if (BASE_DIR.parent.parent / "Manim_Asset").exists() else BASE_DIR
MANIM_ASSET_DIR = PROJECT_ROOT / "Manim_Asset"
IMAGES_DIR = BASE_DIR / "images"
NO_BG_DIR = IMAGES_DIR / "images_wo_bg"
REF_DIR = MANIM_ASSET_DIR / "reference_illustrations"

# Aspect Ratio Mapping for Qwen 2.1 ResolutionSelector node
ASPECT_RATIO_MAP = {
    "1:1": "1:1 (Square)",
    "square": "1:1 (Square)",
    "16:9": "16:9 (Widescreen)",
    "landscape": "16:9 (Widescreen)",
    "9:16": "9:16 (Vertical)",
    "portrait": "9:16 (Vertical)",
    "4:3": "4:3",
    "3:4": "3:4",
    "21:9": "21:9 (Cinematic)"
}

# Embedded Q-Image (Qwen 3.4B + Turbo UNET) workflow template
Q_IMAGE_WORKFLOW = {
  "1": {
    "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"},
    "class_type": "UNETLoader"
  },
  "3": {
    "inputs": {"vae_name": "ae.safetensors"},
    "class_type": "VAELoader"
  },
  "4": {
    "inputs": {"text": "", "clip": ["10", 0]},
    "class_type": "CLIPTextEncode"
  },
  "6": {
    "inputs": {
      "seed": 184167860019721,
      "steps": 9,
      "cfg": 1,
      "sampler_name": "res_multistep",
      "scheduler": "simple",
      "denoise": 1,
      "model": ["1", 0],
      "positive": ["4", 0],
      "negative": ["12", 0],
      "latent_image": ["11", 0]
    },
    "class_type": "KSampler"
  },
  "8": {
    "inputs": {"samples": ["6", 0], "vae": ["3", 0]},
    "class_type": "VAEDecode"
  },
  "10": {
    "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"},
    "class_type": "CLIPLoader"
  },
  "11": {
    "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
    "class_type": "EmptySD3LatentImage"
  },
  "12": {
    "inputs": {"text": "tilted camera, Dutch angle, skewed axes, leaning vertical lines, crooked uprights, warped perspective, distorted coordinate grid, converging verticals, fisheye, curved axes, Minecraft, voxel, childish cartoon, clipart, sticker, thick black outlines, coloring book, naive doodle, burst lines, action lines, flat clip art, low-effort sticker, mascot, 3d render, 3d model, 3d cgi, octane render, blender render, volumetric lighting, raytracing, realistic 3d, glossy 3d plastic, photorealistic 3d shading, realistic shadows, ambient occlusion, studio lighting, depth of field blur, photorealistic, photo, low quality, distorted, bad anatomy, floor shadow, ground shadow, drop shadow, cast shadow, surface shadow, contact shadow, gray shadow oval, ambient shadow, shadow beneath object, floor reflection, ground plane, base shadow, contact darkness, ambient occlusion gradient, drop shadow ellipse, ground ellipse", "clip": ["10", 0]},
    "class_type": "CLIPTextEncode"
  },
  "18": {
    "inputs": {"filename_prefix": "ComfyUI_QImage", "images": ["8", 0]},
    "class_type": "SaveImage"
  }
}
Z_IMAGE_WORKFLOW = Q_IMAGE_WORKFLOW  # Backwards compatibility alias

# Embedded Qwen Image 2.1 Edit workflow template (dual-reference R2I & T2I via switch node)
QWEN_IMAGE_EDIT_WORKFLOW = {
  "461": {"inputs": {"filename_prefix": "Qwen_image_2.1", "format": "png", "format.bit_depth": "8-bit", "format.input_color_space": "sRGB", "images": ["459:457", 0]}, "class_type": "SaveImageAdvanced", "_meta": {"title": "Save Image (Advanced)"}},
  "470": {"inputs": {"image": "portrait_model_denim.png"}, "class_type": "LoadImage", "_meta": {"title": "Load Image"}},
  "472": {"inputs": {"compare_view": {"__value__": ["", ""]}, "image_a": ["470", 0], "image_b": ["461", 0]}, "class_type": "ImageCompare", "_meta": {"title": "Compare Images"}},
  "475": {"inputs": {"image": "clothing_light_blue_denim_shirt.png"}, "class_type": "LoadImage", "_meta": {"title": "Load Image"}},
  "459:451": {"inputs": {"unet_name": "qwen_image_2.1_bf16.safetensors", "weight_dtype": "default"}, "class_type": "UNETLoader", "_meta": {"title": "Load Diffusion Model"}},
  "459:453": {"inputs": {"clip_name": "qwen3vl_8b_int8_convrot.safetensors", "type": "qwen_image", "device": "default"}, "class_type": "CLIPLoader", "_meta": {"title": "Load CLIP"}},
  "459:454": {"inputs": {"vae_name": "qwen_image_2.1_vae_bf16.safetensors"}, "class_type": "VAELoader", "_meta": {"title": "Load VAE"}},
  "459:456": {"inputs": {"width": 1024, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage", "_meta": {"title": "Empty Latent Image"}},
  "459:457": {"inputs": {"samples": ["459:458", 0], "vae": ["459:454", 0]}, "class_type": "VAEDecode", "_meta": {"title": "VAE Decode"}},
  "459:458": {"inputs": {"seed": 1085356340921131, "steps": 25, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "denoise": 1, "model": ["459:469", 0], "positive": ["459:474", 0], "negative": ["459:474", 1], "latent_image": ["459:468", 0]}, "class_type": "KSampler", "_meta": {"title": "KSampler"}},
  "459:468": {"inputs": {"switch": False, "on_false": ["459:474", 2], "on_true": ["459:456", 0]}, "class_type": "ComfySwitchNode", "_meta": {"title": "If/Else Switch"}},
  "459:469": {"inputs": {"device": "auto", "dtype": "default", "model": ["459:451", 0]}, "class_type": "QwenImage21Cache", "_meta": {"title": "Qwen Image 2.1 Cache"}},
  "459:474": {"inputs": {"prompt": "", "negative_prompt": "", "resolution": 0, "clip": ["459:453", 0], "images.image_1": ["470", 0], "vae": ["459:454", 0], "images.image_2": ["475", 0]}, "class_type": "TextEncodeQwenImage21", "_meta": {"title": "Text Encode Qwen Image 2.1"}},
  "459:477": {"inputs": {"clip_name": "qwen3.5_9b_qwen_image_2.1_pe_t2i.int8_convrot.safetensors", "type": "qwen_image", "device": "default"}, "class_type": "CLIPLoader", "_meta": {"title": "Load CLIP"}},
  "459:479": {"inputs": {"value": "# Edit Prompt Enhancer — General (v2)"}, "class_type": "PrimitiveStringMultiline", "_meta": {"title": "Text (System Prompt)"}},
  "459:480": {"inputs": {"source": ["459:484", 0]}, "class_type": "PreviewAny", "_meta": {"title": "Preview as Text"}},
  "459:484": {"inputs": {"switch": False, "on_false": "", "on_true": ["459:500", 0]}, "class_type": "ComfySwitchNode", "_meta": {"title": "If/Else Switch"}},
  "459:485": {"inputs": {"images.image0": ["470", 0], "images.image1": ["475", 0]}, "class_type": "BatchImagesNode", "_meta": {"title": "Batch Images"}},
  "459:500": {"inputs": {"prompt": "", "max_length": 4096, "sampling_mode": "on", "sampling_mode.temperature": 1, "sampling_mode.top_k": 20, "sampling_mode.top_p": 0.95, "sampling_mode.min_p": 0, "sampling_mode.repetition_penalty": 1, "sampling_mode.seed": 1085356340921131, "sampling_mode.presence_penalty": 0, "thinking": False, "use_default_template": True, "mtp": "auto", "clip": ["459:477", 0], "image": ["459:485", 0], "system_prompt": ["459:479", 0]}, "class_type": "TextGenerate", "_meta": {"title": "Generate Text"}}
}


# ==============================================================================
# 2. PROMPT & PARAMETER UTILITIES
# ==============================================================================
def clean_prompt(prompt: str) -> Tuple[str, str]:
    """
    Separate positive and negative prompt segments, stripping Midjourney-style flags.
    """
    if not prompt:
        return "", ""

    match = re.search(r"\n\s*NEGATIVE PROMPT\s*:\s*", prompt, flags=re.IGNORECASE)
    if not match:
        positive = prompt.strip()
        negative = ""
    else:
        positive = prompt[:match.start()].strip()
        negative = prompt[match.end():].strip()

    positive = re.sub(r"--ar\s+\d+:\d+", "", positive)
    positive = re.sub(r"--style\s+\w+", "", positive)
    positive = re.sub(r"--v\s+\d+(\.\d+)?", "", positive)
    return positive.strip(), negative.strip()


DEFAULT_NEGATIVE_PROMPT = (
    "tilted camera, Dutch angle, skewed axes, leaning vertical lines, crooked uprights, "
    "warped perspective, distorted coordinate grid, converging verticals, fisheye, curved axes, "
    "Minecraft, voxel, isometric skew, tilted frame, "
    "childish cartoon, clipart, sticker, thick black outlines, coloring book, naive doodle, "
    "burst lines, action lines, flat clip art, low-effort sticker, mascot, naive drawing, "
    "3D render, 3D model, 3D CGI, octane render, blender render, unreal engine, "
    "volumetric lighting, raytracing, realistic 3D, glossy 3D plastic, photorealistic 3D shading, "
    "realistic shadows, ambient occlusion, studio lighting, depth of field blur, photographic noise, "
    "photorealistic skin, photorealistic grain, photo, photograph, DSLR, "
    "blurry, low quality, simplistic, 3D perspective distortion, vanishing point lens distortion, "
    "watermark, signature, text, cropped, low resolution, deformed geometry, "
    "floor shadow, ground shadow, drop shadow, cast shadow, surface shadow, contact shadow, "
    "gray shadow oval, ambient shadow, shadow beneath object, floor reflection, ground plane, "
    "oval shadow, shadow blob, base shadow, contact darkness, ambient occlusion gradient, "
    "drop shadow ellipse, ground ellipse, colored shadow bounce"
)


def enhance_vector_prompt(prompt: str) -> str:
    """
    Ensure the prompt has strong illustration craftsmanship, rich details,
    strict axis alignment, and appropriate style constraints for clean 2D/2.5D motion design assets.
    """
    lower = prompt.lower()
    enhancements = []

    has_axis_rule = any(kw in lower for kw in [
        "plumb", "vertical axis", "strictly vertical", "straight vertical", "orthographic", "isometric"
    ])
    if not has_axis_rule:
        enhancements.append("strictly plumb vertical upright axes, perfectly straight vertical lines, true isometric or clean frontal orthographic alignment")

    if "editorial" not in lower and "illustration" not in lower:
        enhancements.append("premium editorial vector illustration in the refined style of Stripe and Linear")
    if "hairline" not in lower and "contour" not in lower:
        enhancements.append("refined hairline contours, no thick black outlines")
    if "matte" not in lower and "shading" not in lower:
        enhancements.append("smooth matte tonal shading, clean geometric planes, zero 3D CGI rendering")
    if "no floor shadow" not in lower and "zero shadow" not in lower:
        enhancements.append("floating levitating in pure white void, strictly zero floor shadow, zero ground shadow, zero drop shadow beneath object")

    if enhancements:
        return f"{prompt.rstrip('. ')}; {', '.join(enhancements)}."
    return prompt


def normalize_aspect_ratio(ar_str: str) -> str:
    """Map shorthand aspect ratio (e.g. '1:1', '16:9') to ComfyUI node format."""
    cleaned = ar_str.strip().lower()
    return ASPECT_RATIO_MAP.get(cleaned, ASPECT_RATIO_MAP.get(cleaned.replace(" ", ""), "1:1 (Square)"))


def get_dimensions_from_aspect_ratio(aspect_ratio: str) -> Tuple[int, int]:
    """Map aspect ratio shorthand to width and height in pixels."""
    cleaned = str(aspect_ratio).strip().lower()
    if "16:9" in cleaned or "landscape" in cleaned or "widescreen" in cleaned:
        return 1280, 720
    elif "9:16" in cleaned or "portrait" in cleaned or "vertical" in cleaned:
        return 720, 1280
    elif "4:3" in cleaned:
        return 1024, 768
    elif "3:4" in cleaned:
        return 768, 1024
    elif "21:9" in cleaned:
        return 1344, 576
    else:
        return 1024, 1024


def find_workflow_json(filename: str) -> Optional[Path]:
    """Search for workflow JSON file in common project directories."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / filename,
        Path("Code_script") / filename,
        BASE_DIR / filename,
        BASE_DIR / "Manim_Asset" / filename,
        BASE_DIR.parent / filename,
        BASE_DIR.parent / "Manim_Asset" / filename,
        PROJECT_ROOT / "Manim_Asset" / filename,
        PROJECT_ROOT / filename,
        Path.cwd() / filename,
        Path.cwd() / "Manim_Asset" / filename,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def load_qwen_workflow(preferred_file: str = "Qwen Image 2.1 Edit.json") -> dict:
    """Loads Qwen workflow JSON from workspace, falling back to embedded definition."""
    candidates = [
        preferred_file,
        "Qwen Image 2.1 Edit.json",
        "Qwen 2.1 R2I api.json",
        "Qwen 2.1 T2I api.json"
    ]
    seen = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        wf_path = find_workflow_json(c)
        if wf_path and wf_path.exists():
            try:
                with open(wf_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"  ⚠ Failed to load workflow {wf_path}: {e}")
    return copy.deepcopy(QWEN_IMAGE_EDIT_WORKFLOW)


# ==============================================================================
# 3. GOOGLE GENAI / NANO-BANANA ENGINE
# ==============================================================================
def generate_nano_banana(
    prompt: str,
    output_path: Union[str, Path],
    negative_prompt: str = "",
    aspect_ratio: str = "1:1",
    model_name: str = "nano-banana-pro-preview",
    api_key: Optional[str] = None
) -> Path:
    """
    Generates an image directly using Google GenAI Nano-Banana model.
    Falls back gracefully across candidate image models.

    Args:
        prompt: Image description prompt.
        output_path: Destination path (.png or .jpg).
        negative_prompt: Optional negative constraints.
        aspect_ratio: '1:1', '16:9', '9:16', '4:3', '3:4'.
        model_name: Model identifier (defaults to 'nano-banana-pro-preview').
        api_key: Optional GOOGLE_API_KEY (defaults to env var).

    Returns:
        Path: Saved image path.
    """
    from google import genai
    from google.genai import types

    key = api_key or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    client = genai.Client(api_key=key)

    pos_prompt, neg_prompt = clean_prompt(prompt)
    full_neg = negative_prompt or neg_prompt
    final_prompt = pos_prompt
    if full_neg:
        final_prompt += f"\n\nNEGATIVE CONSTRAINTS:\nDo not depict: {full_neg}"

    target_path = Path(output_path).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    candidates = [model_name, "nano-banana-pro-preview", "gemini-2.5-flash-image", "gemini-3-pro-image"]
    seen = set()
    models_to_try = [m for m in candidates if not (m in seen or seen.add(m))]

    last_err = None
    for m in models_to_try:
        try:
            print(f"🍌 [Nano-Banana] Generating image with '{m}' (AR: {aspect_ratio})...")
            gen_config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            )
            if aspect_ratio in ["1:1", "16:9", "9:16", "4:3", "3:4"]:
                try:
                    gen_config.image_config = types.ImageConfig(aspect_ratio=aspect_ratio)
                except Exception:
                    pass

            response = client.models.generate_content(
                model=m,
                contents=final_prompt,
                config=gen_config
            )
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if getattr(part, "inline_data", None):
                        img = part.as_image()
                        img.save(str(target_path))
                        print(f"  ✓ [Nano-Banana] Saved: {target_path}")
                        return target_path
        except Exception as e:
            last_err = e
            print(f"  ⚠ [Nano-Banana] '{m}' attempt error: {e}. Trying fallback...")

    raise RuntimeError(f"Nano-Banana generation failed on all models: {last_err}")


# ==============================================================================
# 4. COMFYUI API INTERACTION
# ==============================================================================
def upload_input_image(file_path: Union[str, Path], comfy_url: str = COMFYUI_URL) -> str:
    """
    Upload a local image to the ComfyUI server's input directory.
    """
    path_obj = Path(file_path).resolve()
    if not path_obj.exists():
        raise FileNotFoundError(f"Reference image not found for upload: {path_obj}")

    url = f"{comfy_url}/upload/image"
    ext = path_obj.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"

    with open(path_obj, "rb") as f:
        files = {"image": (path_obj.name, f, mime)}
        data = {"overwrite": "true"}
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
        res_json = response.json()
        server_name = res_json.get("name", path_obj.name)
        print(f"  ✓ [ComfyUI Upload] Uploaded '{path_obj.name}' -> server name '{server_name}'")
        return server_name


def queue_prompt(prompt_workflow: dict, comfy_url: str = COMFYUI_URL) -> str:
    """Submit a workflow dictionary to ComfyUI /prompt endpoint."""
    url = f"{comfy_url}/prompt"
    payload = json.dumps({"prompt": prompt_workflow}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        res = json.loads(response.read().decode("utf-8"))
        if "error" in res:
            raise RuntimeError(f"ComfyUI prompt error: {res['error']}")
        return res["prompt_id"]


def get_history(prompt_id: str, comfy_url: str = COMFYUI_URL) -> dict:
    """Query ComfyUI execution history for given prompt_id."""
    url = f"{comfy_url}/history/{prompt_id}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_prompt_completion(
    prompt_id: str,
    comfy_url: str = COMFYUI_URL,
    poll_interval: float = 3.0,
    timeout: float = 600.0
) -> dict:
    """
    Poll ComfyUI history until the job finishes or fails.
    """
    print(f"  ⏳ [ComfyUI] Execution active for prompt ID {prompt_id} (polling every {poll_interval}s)...")
    start_time = time.time()
    last_print = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"ComfyUI task {prompt_id} timed out after {timeout} seconds.")

        try:
            history = get_history(prompt_id, comfy_url)
            if prompt_id in history:
                task_data = history[prompt_id]
                status = task_data.get("status", {})
                if status.get("completed", True):
                    print(f"  ✓ [ComfyUI] Execution completed in {elapsed:.1f}s.")
                    return task_data.get("outputs", {})
                elif status.get("status_str") == "error":
                    raise RuntimeError(f"ComfyUI execution failed: {status.get('messages')}")
        except Exception as e:
            if not isinstance(e, (RuntimeError, TimeoutError)):
                pass
            else:
                raise

        if elapsed - last_print >= 10:
            print(f"  ⏳ [ComfyUI] Still rendering... ({elapsed:.0f}s elapsed)")
            last_print = elapsed

        time.sleep(poll_interval)


def download_output_media(
    outputs: dict,
    target_save_path: Union[str, Path],
    comfy_url: str = COMFYUI_URL
) -> Path:
    """
    Download rendered media from ComfyUI view endpoint to local disk.
    """
    target = Path(target_save_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    for node_id, node_output in outputs.items():
        for media_key in ["images", "videos", "gifs"]:
            if media_key in node_output and node_output[media_key]:
                file_info = node_output[media_key][0]
                filename = file_info["filename"]
                subfolder = file_info.get("subfolder", "")
                file_type = file_info.get("type", "output")

                params = urllib.parse.urlencode({
                    "filename": filename,
                    "subfolder": subfolder,
                    "type": file_type
                })
                view_url = f"{comfy_url}/view?{params}"
                urllib.request.urlretrieve(view_url, str(target))
                print(f"  ✓ [ComfyUI Output] Successfully saved image to: {target}")
                return target

    raise RuntimeError("No output images or videos found in ComfyUI task execution history.")


# ==============================================================================
# 5. COMFYUI WORKFLOW GENERATION ENGINES
# ==============================================================================

def generate_r2i(
    prompt: str,
    reference_image_path: Union[str, Path],
    output_path: Union[str, Path],
    aspect_ratio: str = "1:1",
    seed: Optional[int] = None,
    negative_prompt: str = "",
    reference_image_2: Optional[Union[str, Path]] = None,
    comfy_url: str = COMFYUI_URL,
    **kwargs
) -> Path:
    """
    Generate / edit an image using Qwen Image 2.1 Edit workflow.
    Accommodates single-reference R2I and dual-reference editing.
    """
    wf = load_qwen_workflow("Qwen Image 2.1 Edit.json")

    # 1. Upload primary reference image
    server_img_name = upload_input_image(reference_image_path, comfy_url)
    if "470" in wf and "inputs" in wf["470"]:
        wf["470"]["inputs"]["image"] = server_img_name

    # 2. Upload secondary reference image if provided, or mirror primary to satisfy both inputs
    second_ref = reference_image_2 or kwargs.get("second_reference_image") or kwargs.get("reference_image_2")
    if second_ref:
        server_img_name_2 = upload_input_image(second_ref, comfy_url)
    else:
        server_img_name_2 = server_img_name

    if "475" in wf and "inputs" in wf["475"]:
        wf["475"]["inputs"]["image"] = server_img_name_2

    # 3. ComfySwitchNode (Node 459:468): False routes to on_false = ["459:474", 2] (reference image latents)
    if "459:468" in wf and "inputs" in wf["459:468"]:
        wf["459:468"]["inputs"]["switch"] = False

    # 4. Text Prompt & Negative Prompt
    final_prompt = enhance_vector_prompt(prompt)
    if "<image1>" not in final_prompt and "<image" not in final_prompt:
        final_prompt = f"Using reference <image1>, {final_prompt}"

    neg_prompt = negative_prompt.strip() if negative_prompt else DEFAULT_NEGATIVE_PROMPT

    if "459:474" in wf and "inputs" in wf["459:474"]:
        wf["459:474"]["inputs"]["prompt"] = final_prompt
        wf["459:474"]["inputs"]["negative_prompt"] = neg_prompt

    if "459:452" in wf and "inputs" in wf["459:452"]:
        wf["459:452"]["inputs"]["prompt"] = final_prompt
        wf["459:452"]["inputs"]["negative_prompt"] = neg_prompt

    actual_seed = seed if seed is not None else random.randint(1, 10**15)
    if "459:458" in wf and "inputs" in wf["459:458"]:
        wf["459:458"]["inputs"]["seed"] = actual_seed

    # Prompt enhancer nodes if present
    if "459:500" in wf and "inputs" in wf["459:500"]:
        wf["459:500"]["inputs"]["prompt"] = final_prompt
        if "sampling_mode.seed" in wf["459:500"]["inputs"]:
            wf["459:500"]["inputs"]["sampling_mode.seed"] = actual_seed
    if "459:484" in wf and "inputs" in wf["459:484"]:
        if "on_false" in wf["459:484"]["inputs"] and isinstance(wf["459:484"]["inputs"]["on_false"], str):
            wf["459:484"]["inputs"]["on_false"] = final_prompt

    # 5. Output Filename Prefix
    if "461" in wf and "inputs" in wf["461"]:
        wf["461"]["inputs"]["filename_prefix"] = f"ComfyUI_Qwen_R2I/{Path(output_path).stem}"

    # 6. Resolution / Aspect Ratio
    w, h = get_dimensions_from_aspect_ratio(aspect_ratio)
    if "459:456" in wf and "inputs" in wf["459:456"]:
        if isinstance(wf["459:456"]["inputs"].get("width"), (int, float)):
            wf["459:456"]["inputs"]["width"] = w
        if isinstance(wf["459:456"]["inputs"].get("height"), (int, float)):
            wf["459:456"]["inputs"]["height"] = h

    ar_val = normalize_aspect_ratio(aspect_ratio)
    if "13" in wf and "inputs" in wf["13"]:
        wf["13"]["inputs"]["aspect_ratio"] = ar_val

    print(f"🚀 [ComfyUI R2I/Edit] Dispatching Reference-to-Image job (Seed: {actual_seed}, AR: {ar_val}, {w}x{h})...")
    prompt_id = queue_prompt(wf, comfy_url)
    outputs = wait_for_prompt_completion(prompt_id, comfy_url)
    return download_output_media(outputs, output_path, comfy_url)


def generate_t2i(
    prompt: str,
    output_path: Union[str, Path],
    aspect_ratio: str = "1:1",
    seed: Optional[int] = None,
    negative_prompt: str = "",
    comfy_url: str = COMFYUI_URL
) -> Path:
    """
    Generate an image using Qwen 2.1 Text-to-Image (T2I) API workflow.
    Supports Qwen Image 2.1 Edit.json (via ComfySwitchNode switch=True) as well as standalone T2I workflow.
    """
    wf = load_qwen_workflow("Qwen Image 2.1 Edit.json")

    final_prompt = enhance_vector_prompt(prompt)
    neg_prompt = negative_prompt.strip() if negative_prompt else DEFAULT_NEGATIVE_PROMPT
    actual_seed = seed if seed is not None else random.randint(1, 10**15)

    w, h = get_dimensions_from_aspect_ratio(aspect_ratio)
    ar_val = normalize_aspect_ratio(aspect_ratio)

    # If using unified Edit workflow, switch to EmptyLatentImage and detach demo images
    if "459:468" in wf and "inputs" in wf["459:468"]:
        wf["459:468"]["inputs"]["switch"] = True
        # Detach reference image inputs from TextEncodeQwenImage21 for pure text-to-image
        if "459:474" in wf and "inputs" in wf["459:474"]:
            wf["459:474"]["inputs"].pop("images.image_1", None)
            wf["459:474"]["inputs"].pop("images.image_2", None)
        for unused_node in ["470", "475", "472", "459:485"]:
            wf.pop(unused_node, None)

    if "459:474" in wf and "inputs" in wf["459:474"]:
        wf["459:474"]["inputs"]["prompt"] = final_prompt
        wf["459:474"]["inputs"]["negative_prompt"] = neg_prompt

    if "459:452" in wf and "inputs" in wf["459:452"]:
        wf["459:452"]["inputs"]["prompt"] = final_prompt
        wf["459:452"]["inputs"]["negative_prompt"] = neg_prompt

    if "459:458" in wf and "inputs" in wf["459:458"]:
        wf["459:458"]["inputs"]["seed"] = actual_seed

    if "459:456" in wf and "inputs" in wf["459:456"]:
        if isinstance(wf["459:456"]["inputs"].get("width"), (int, float)):
            wf["459:456"]["inputs"]["width"] = w
        if isinstance(wf["459:456"]["inputs"].get("height"), (int, float)):
            wf["459:456"]["inputs"]["height"] = h

    if "13" in wf and "inputs" in wf["13"]:
        wf["13"]["inputs"]["aspect_ratio"] = ar_val

    if "461" in wf and "inputs" in wf["461"]:
        wf["461"]["inputs"]["filename_prefix"] = f"ComfyUI_Qwen_T2I/{Path(output_path).stem}"

    print(f"🚀 [ComfyUI T2I] Dispatching Text-to-Image job (Seed: {actual_seed}, AR: {ar_val}, {w}x{h})...")
    prompt_id = queue_prompt(wf, comfy_url)
    outputs = wait_for_prompt_completion(prompt_id, comfy_url)
    return download_output_media(outputs, output_path, comfy_url)


# Aliases for image editing
generate_image_edit = generate_r2i
qwen_image_edit = generate_r2i


def q_image(
    prompt: str,
    output_path: Union[str, Path],
    seed: Optional[int] = None,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str = "",
    comfy_url: str = COMFYUI_URL
) -> Path:
    """
    Q-Image fast 9-step generation using Qwen 3.4B text encoder and turbo UNET.
    """
    wf = copy.deepcopy(Q_IMAGE_WORKFLOW)
    actual_seed = seed if seed is not None else random.randint(1, 10**15)

    final_prompt = enhance_vector_prompt(prompt)
    neg_prompt = negative_prompt.strip() if negative_prompt else DEFAULT_NEGATIVE_PROMPT
    wf["4"]["inputs"]["text"] = final_prompt
    wf["6"]["inputs"]["seed"] = actual_seed
    wf["11"]["inputs"]["width"] = width
    wf["11"]["inputs"]["height"] = height
    if "12" in wf and "inputs" in wf["12"]:
        wf["12"]["inputs"]["text"] = neg_prompt

    print(f"🚀 [ComfyUI Q-Image] Dispatching 9-step Qwen Turbo job (Seed: {actual_seed}, {width}x{height})...")
    prompt_id = queue_prompt(wf, comfy_url)
    outputs = wait_for_prompt_completion(prompt_id, comfy_url)
    return download_output_media(outputs, output_path, comfy_url)


# Aliases for flexible import
generate_q_image = q_image
generate_z_image = q_image


# ==============================================================================
# 6. UNIFIED GENERATION API
# ==============================================================================

def generate_image(
    prompt: str,
    output_path: Union[str, Path],
    reference_image: Optional[Union[str, Path]] = None,
    reference_image_2: Optional[Union[str, Path]] = None,
    negative_prompt: str = "",
    aspect_ratio: str = "1:1",
    mode: str = "q_image",
    seed: Optional[int] = None,
    remove_bg: bool = False,
    crop_to_16_9: bool = False,
    comfy_url: str = COMFYUI_URL,
    **kwargs
) -> Path:
    """
    Universal entry point for image generation across all engines.

    Parameters:
      - prompt: Main visual description
      - output_path: Destination local file path (.png or .jpg)
      - reference_image: Optional path to primary reference image (triggers R2I / Edit)
      - reference_image_2: Optional path to secondary reference image (for dual-ref Qwen Edit)
      - negative_prompt: Negative constraint string
      - aspect_ratio: '1:1', '16:9', '9:16', '4:3'
      - mode: 'q_image', 'nano_banana', 't2i', 'r2i', 'edit', or 'auto'
      - seed: Optional deterministic integer seed
      - remove_bg: If True, automatically removes background via image_bg_remover
    """
    target_path = Path(output_path).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    pos_prompt, neg_prompt = clean_prompt(prompt)
    final_negative = negative_prompt or neg_prompt

    ar = aspect_ratio
    if crop_to_16_9 and ar == "1:1":
        ar = "16:9"

    # Determine execution engine
    resolved_ref = None
    if reference_image:
        p_ref = Path(reference_image)
        if p_ref.is_file():
            resolved_ref = p_ref.resolve()
        else:
            for cand_root in [BASE_DIR, BASE_DIR.parent, PROJECT_ROOT, MANIM_ASSET_DIR]:
                check_p = (cand_root / reference_image).resolve()
                if check_p.is_file():
                    resolved_ref = check_p
                    break
        if resolved_ref is None and p_ref.exists():
            resolved_ref = p_ref

    resolved_ref_2 = None
    ref_2_candidate = reference_image_2 or kwargs.get("second_reference_image") or kwargs.get("reference_image_2")
    if ref_2_candidate:
        p_ref2 = Path(ref_2_candidate)
        if p_ref2.is_file():
            resolved_ref_2 = p_ref2.resolve()
        else:
            for cand_root in [BASE_DIR, BASE_DIR.parent, PROJECT_ROOT, MANIM_ASSET_DIR]:
                check_p2 = (cand_root / ref_2_candidate).resolve()
                if check_p2.is_file():
                    resolved_ref_2 = check_p2
                    break
        if resolved_ref_2 is None and p_ref2.exists():
            resolved_ref_2 = p_ref2

    effective_mode = mode.lower()
    if (resolved_ref or resolved_ref_2) and effective_mode not in ["nano_banana", "nano-banana", "banana"]:
        effective_mode = "r2i"
    elif effective_mode in ["edit", "image_edit", "qwen_edit"]:
        effective_mode = "r2i"
    elif effective_mode == "auto":
        effective_mode = "r2i" if (resolved_ref or resolved_ref_2) else "q_image"

    print("\n" + "=" * 65)
    print(f"[Image Generator] Engine: {effective_mode.upper()} | Output: {target_path.name}")
    print("=" * 65)

    if effective_mode in ["nano_banana", "nano-banana", "banana"]:
        saved_path = generate_nano_banana(
            prompt=pos_prompt,
            output_path=target_path,
            negative_prompt=final_negative,
            aspect_ratio=ar
        )
    elif effective_mode in ["q_image", "z_image", "qimage"]:
        w, h = (1280, 720) if ar == "16:9" else (1024, 1024)
        saved_path = q_image(
            prompt=pos_prompt,
            output_path=target_path,
            seed=seed,
            width=w,
            height=h,
            negative_prompt=final_negative,
            comfy_url=comfy_url
        )
    elif effective_mode in ["r2i", "edit", "image_edit", "qwen_edit"]:
        if not resolved_ref and not resolved_ref_2:
            print("  ⚠ [Image Generator] R2I/Edit requested but no reference image found. Falling back to Qwen T2I.")
            saved_path = generate_t2i(
                prompt=pos_prompt,
                output_path=target_path,
                aspect_ratio=ar,
                seed=seed,
                negative_prompt=final_negative,
                comfy_url=comfy_url
            )
        else:
            saved_path = generate_r2i(
                prompt=pos_prompt,
                reference_image_path=resolved_ref or resolved_ref_2,
                output_path=target_path,
                aspect_ratio=ar,
                seed=seed,
                negative_prompt=final_negative,
                reference_image_2=resolved_ref_2,
                comfy_url=comfy_url,
                **kwargs
            )
    else:  # Default 't2i'
        saved_path = generate_t2i(
            prompt=pos_prompt,
            output_path=target_path,
            aspect_ratio=ar,
            seed=seed,
            negative_prompt=final_negative,
            comfy_url=comfy_url
        )

    # Automatic background removal via image_bg_remover
    if remove_bg:
        try:
            from image_bg_remover import remove_background
            no_bg_dir = target_path.parent / "images_wo_bg"
            no_bg_dir.mkdir(parents=True, exist_ok=True)
            no_bg_path = no_bg_dir / f"{target_path.stem}.png"
            print(f"  ✂ [BG Remover] Removing background -> {no_bg_path.name}...")
            remove_background(
                input_path=str(saved_path),
                output_path=str(no_bg_path)
                #model="birefnet-general",
                #defringe=True
            )
            print(f"  ✓ [BG Remover] Completed: {no_bg_path}")
        except Exception as e:
            print(f"  ⚠ [BG Remover] Background removal failed: {e}")

    return saved_path


# ==============================================================================
# 7. BATCH GENERATION FROM PROMPTS JSON
# ==============================================================================

def generate_images_from_prompts(
    prompt_file_or_data: Union[str, Path, dict],
    output_dir: Optional[Union[str, Path]] = None,
    comfy_url: Optional[str] = None,
    mode: str = "q_image",
    aspect_ratio: str = "1:1",
    remove_bg: bool = True,
    overwrite: bool = False
) -> Dict[str, Path]:
    """
    Iterates through a prompts JSON file or dictionary and generates images
    for each prompt, automatically removing backgrounds if requested.

    Args:
        prompt_file_or_data: Path to JSON file (e.g. image_prompt_gemini-3.8-flash.json)
                             or a dictionary of prompt definitions.
        output_dir: Directory where generated images are saved (defaults to 'images/').
        comfy_url: ComfyUI server URL (defaults to COMFYUI_URL).
        mode: Engine mode ('q_image', 'nano_banana', 't2i', 'r2i', 'auto').
        aspect_ratio: Aspect ratio ('1:1', '16:9', etc.).
        remove_bg: Whether to automatically remove background via image_bg_remover (default True).
        overwrite: If True, re-generates even if output image already exists.

    Returns:
        Dict[str, Path]: Mapping from image keys to saved output paths.
    """
    url = (comfy_url or COMFYUI_URL).rstrip("/")

    # Resolve prompts dictionary
    if isinstance(prompt_file_or_data, (str, Path)):
        p_path = Path(prompt_file_or_data).resolve()
        if not p_path.exists():
            raise FileNotFoundError(f"Prompts file not found: {p_path}")
        with open(p_path, "r", encoding="utf-8") as f:
            prompts_dict = json.load(f)
        print(f"📖 Loaded {len(prompts_dict)} prompts from: {p_path.name}")
    elif isinstance(prompt_file_or_data, dict):
        prompts_dict = prompt_file_or_data
    else:
        raise TypeError(f"Expected path or dict, got {type(prompt_file_or_data)}")

    # Resolve output directory
    if output_dir:
        out_dir = Path(output_dir).resolve()
    else:
        out_dir = BASE_DIR / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, Path] = {}
    total = len(prompts_dict)

    print("\n" + "=" * 65)
    print(f"🎨 [Batch Generator] Starting generation for {total} images -> {out_dir}")
    print(f"🎨 [Batch Generator] Engine: {mode.upper()} (Auto-remove BG: {remove_bg})")
    print("=" * 65)

    for idx, (img_key, entry) in enumerate(prompts_dict.items(), start=1):
        target_path = out_dir / f"{img_key}.png"

        # Check existing file
        if target_path.exists() and not overwrite:
            print(f"  ⤷ [{idx}/{total}] Skipping generation for {img_key} (already exists: {target_path.name})")
            saved_path = target_path
        else:
            # Extract prompt string and optional reference image(s)
            if isinstance(entry, dict):
                prompt_text = entry.get("image_prompt", "")
                ref_image = entry.get("reference_image", None)
                ref_image_2 = entry.get("reference_image_2", entry.get("second_reference_image", None))
            else:
                prompt_text = str(entry)
                ref_image = None
                ref_image_2 = None

            if not prompt_text.strip():
                print(f"  ⚠ [{idx}/{total}] Skipping {img_key}: prompt text is empty.")
                continue

            print(f"\n  ▶ [{idx}/{total}] Generating '{img_key}'...")
            try:
                saved_path = generate_image(
                    prompt=prompt_text,
                    output_path=target_path,
                    reference_image=ref_image,
                    reference_image_2=ref_image_2,
                    aspect_ratio=aspect_ratio,
                    mode=mode,
                    remove_bg=False,  # Handled below
                    comfy_url=url
                )
                print(f"  ✓ [{idx}/{total}] Generated {img_key} -> {saved_path}")
            except Exception as e:
                print(f"  ❌ [{idx}/{total}] Failed to generate {img_key}: {e}")
                continue

        results[img_key] = saved_path

        # Background removal
        if remove_bg:
            try:
                from image_bg_remover import remove_background
                no_bg_dir = out_dir / "images_wo_bg"
                no_bg_dir.mkdir(parents=True, exist_ok=True)
                no_bg_path = no_bg_dir / f"{img_key}.png"

                if no_bg_path.exists() and not overwrite:
                    print(f"  ⤷ [{idx}/{total}] Transparent PNG already exists: {no_bg_path.name}")
                else:
                    print(f"  ✂ [{idx}/{total}] Removing background -> {no_bg_path.name}...")
                    remove_background(
                        input_path=str(saved_path),
                        output_path=str(no_bg_path)
                        #model="birefnet-general",
                        #defringe=True
                    )
            except Exception as e:
                print(f"  ⚠ [{idx}/{total}] Background removal error: {e}")

    print("\n" + "=" * 65)
    print(f"✅ [Batch Generator] Finished. Processed {len(results)}/{total} images.")
    if remove_bg:
        print(f"📁 Transparent cutouts stored at: {out_dir / 'images_wo_bg'}")
    print("=" * 65 + "\n")

    return results


# ==============================================================================
# 8. COMMAND LINE INTERFACE
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Image Generator (Q-Image ComfyUI & Nano-Banana Google GenAI)"
    )
    parser.add_argument("--prompt", "-p", type=str, default=None, help="Image description prompt.")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output destination file path.")
    parser.add_argument("--reference-image", "--ref", "-r", type=str, default=None, help="Path to primary reference image (triggers R2I / Edit).")
    parser.add_argument("--reference-image-2", "--ref2", type=str, default=None, help="Path to optional secondary reference image (for dual-ref Qwen Edit).")
    parser.add_argument("--negative-prompt", "-n", type=str, default="", help="Negative prompt.")
    parser.add_argument("--aspect-ratio", "-ar", type=str, default="1:1", help="Aspect ratio (1:1, 16:9, 9:16, 4:3).")
    parser.add_argument("--mode", "-m", type=str, choices=["q_image", "nano_banana", "auto", "r2i", "t2i", "edit", "z_image"], default="q_image", help="Generation engine.")
    parser.add_argument("--seed", "-s", type=int, default=None, help="Random seed.")
    parser.add_argument("--remove-bg", action="store_true", default=True, help="Automatically remove background.")
    parser.add_argument("--no-remove-bg", action="store_false", dest="remove_bg", help="Do not remove background.")
    parser.add_argument("--comfy-url", type=str, default=COMFYUI_URL, help="ComfyUI server URL.")
    parser.add_argument("--prompts-json", "-pj", type=str, default=None, help="Batch generate images from an image_prompt JSON file.")
    parser.add_argument("--output-dir", "-od", type=str, default=None, help="Destination directory for batch generation.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing image files during batch generation.")

    args = parser.parse_args()

    # Batch mode
    if args.prompts_json:
        generate_images_from_prompts(
            prompt_file_or_data=args.prompts_json,
            output_dir=args.output_dir,
            comfy_url=args.comfy_url,
            mode=args.mode,
            aspect_ratio=args.aspect_ratio,
            remove_bg=args.remove_bg,
            overwrite=args.overwrite
        )
        return

    # Single image mode
    if not args.prompt:
        parser.error("Either --prompt (-p) or --prompts-json (-pj) must be provided.")

    default_output = IMAGES_DIR / "generated_output.png"
    out_path = Path(args.output) if args.output else default_output

    generate_image(
        prompt=args.prompt,
        output_path=out_path,
        reference_image=args.reference_image,
        reference_image_2=args.reference_image_2,
        negative_prompt=args.negative_prompt,
        aspect_ratio=args.aspect_ratio,
        mode=args.mode,
        seed=args.seed,
        remove_bg=args.remove_bg,
        comfy_url=args.comfy_url
    )


if __name__ == "__main__":
    main()
