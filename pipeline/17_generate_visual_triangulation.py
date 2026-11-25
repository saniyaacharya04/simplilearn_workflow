#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 17: VISUAL TRIANGULATION (GRID & SET-OF-MARKS OVERLAYS)
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 17
   - Script Name: 17_generate_visual_triangulation.py
   - Primary Class: GridVisualTriangulation
   - Pipeline Role:
     Bridges visual screenshots and Manim coordinate space for Multimodal VLMs.
     Deduplicates keyframes, overlays a standardized coordinate grid matrix (e.g. 12x12)
     and Set-of-Marks (SoM) bounding labels onto screenshots, and generates a two-way
     coordinate mapping (cell -> Manim x,y coordinates). Features direct FFmpeg video
     keyframe extraction fallback if snapshot images are missing.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 16 (16_generate_vlm_feedback_report.py):
       - How: Triggered via input tracker 16_generate_vlm_feedback_tracker.json.
       - Purpose: Ingests geometric report.json to attach flagged issues to keyframes.
     * Stage 15 (15_run_manim_vlm_feedback.py):
       - How: Reads snapshot PNGs and JSONs in correction_insights_vlm/scene_{group}/.
       - Purpose: Keyframe images to annotate with grids and marks.
     * Stage 14/15 Videos (manim_extracted_videos/):
       - How: Direct FFmpeg extraction fallback if PNG snapshots are missing or corrupted.
     * Stage 5 (5_populate_audio_runtime.py):
       - How: Ingests CGI_Input.json for timestamp correlation.
   - Input Tracker: ppt_trackers/16_generate_vlm_feedback_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * correction_insights_vlm/scene_{group}/ (Stage 15 & 16):
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights_vlm/scene_*/
       Content: Keyframe PNG images, bounding box JSONs, and report.json.
     * manim_extracted_videos/ (Stage 15 fallback):
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_extracted_videos/*.mp4
       Content: Rendered videos for automated FFmpeg frame extraction.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Narration manifest with section timestamps.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/16_generate_vlm_feedback_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 16_generate_vlm_feedback_tracker.json.
   - Step 2: Builds deduplicated keyframe manifest (keyframe_selector.build_manifest) to
     select representative frames per section (peak action frame + settled composition frame).
   - Step 3: Materializes selected frames into vlm_inputs/scene_{group}/:
     * Draws coordinate grid overlay on image (add_grid_overlay).
     * Annotates object bounding boxes with numeric SoM labels (add_som_annotations).
     * Attaches deduplicated issue list from report.json.
   - Step 4: Generates cell-to-coordinate mapping (cellmap) linking visual cells to Manim (x, y) space.
   - Step 5: Atomically updates 17_generate_triangulation_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * vlm_inputs/scene_{group}/ directory:
       Location: data_ppt_advanced/<TOPIC_NAME>/vlm_inputs/scene_{group}/
       Content:
         - manifest.json: Scene triangulation manifest mapping each grid to its code block and visuals.
         - sec_{s}_frame_{f}_triangulated.png: Grid-overlaid, SoM-labeled keyframe PNG.
         - sec_{s}_frame_{f}_triangulated.json: Snapshot metadata with attached issue list.
         - sec_{s}_frame_{f}_cellmap.json: Cell-to-Manim coordinate lookup table.
     * vlm_inputs/manifest.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/vlm_inputs/manifest.json
       Content: Master triangulation manifest consolidating all scenes, grids, code blocks, and visuals.
     * Output Tracker:
       Location: ppt_trackers/17_generate_triangulation_tracker.json
       Content: Atomic tracker confirming completion of visual triangulation.

6. DOWNSTREAM CONSUMERS:
   - Stage 18 (18_vlm_fix_suggestor.py): Ingests manifest.json alongside triangulated frames to feed
     the VLM exact presentation step code snippets (start_line..end_line) and Set-of-Marks object
     identities, preventing variable name hallucination.
   - Stage 19 (19_vlm_fixing_stage.py): Ingests manifest.json to perform surgical section-level code
     directive synthesis restricted strictly to the mapped line boundaries.
================================================================================
"""

import os
import sys
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_HELPERS_DIR = os.path.join(_CURRENT_DIR, "helpers")
_ROOT_DIR = os.path.dirname(_CURRENT_DIR)
for _p in [_HELPERS_DIR, _CURRENT_DIR, _ROOT_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


import json
import os
import portalocker
import math
import argparse
import re
from glob import glob
from collections import defaultdict
from pathlib import Path
import shutil
import subprocess
from datetime import datetime
from keyframe_processing_helpers.grid_overlay import add_grid_overlay, add_som_annotations
from keyframe_processing_helpers.frame_context import (
    describe_objects_on_grid,
    grid_geometry_summary,
    _cell_coverage,
    _span,
)
from keyframe_processing_helpers.keyframe_selector import build_manifest

class GridVisualTriangulation:
    """
    Stage 17: Visual Triangulation.
    Overlays coordinate grids and Set-of-Marks annotations onto keyframes, mapping
    visual pixels to Manim world coordinates for multimodal LLM inspection.
    """
    def __init__(
        self,
        input_tracker_path,
        output_tracker_path,
        input_folder
    ):
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.input_folder = input_folder
        
        
        # Initialize output tracker file if it doesn't exist
        if not os.path.exists(self.output_tracker_path):
            tracker_dir = os.path.dirname(self.output_tracker_path)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
            with open(self.output_tracker_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

    # ---------------------------------------------------------
    # UTILITIES & FILE I/O
    # ---------------------------------------------------------

    def _load_tracker(self, filepath):
        """
        Load a JSON tracker with a shared lock (read lock).
        """
        if not os.path.exists(filepath):
            return {}
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                portalocker.lock(f, portalocker.LOCK_SH)
                try:
                    content = f.read()
                    if not content:
                        return {}
                    data = json.loads(content)
                except json.JSONDecodeError:
                    data = {}
                finally:
                    portalocker.unlock(f)
            return data
        except Exception as e:
            print(f"Error loading tracker {filepath}: {e}")
            return {}

    def _save_tracker(self, filepath, data):
        """
        Save a JSON tracker with an exclusive lock (write lock).
        """
        lock_path = filepath + ".lock"
        try:
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
        except Exception as e:
            print(f"Error saving tracker {filepath}: {e}")


    def load_json(self, path):
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)

    def determine_section(self, timestamp, scene_sections):
        running = 0.0
        for idx, section in enumerate(scene_sections, start=1):
            running += section.get("run_time", 0)
            if timestamp <= running:
                return idx
        return len(scene_sections)
    
    # ---------------------------------------------------------
    # CODE SLICING & VISUAL OBJECT EXTRACTION HELPERS
    # ---------------------------------------------------------

    def _find_scene_code(self, base, scene_number, code_path=None):
        """Locates the Manim source code for the requested scene."""
        candidates = [Path(code_path)] if code_path else [
            base / f"group_{scene_number}.py",
            base / "manim_extracted_codes" / f"group_{scene_number}.py",
            base / "manim_codes" / f"group_{scene_number}.py",
            base / "presentation_code_corrections" / f"scene_{scene_number}.py",
        ]
        return next((p for p in candidates if p and p.is_file()), None)

    def _extract_code_block_for_section(self, code_path, section_id):
        """
        Extracts line numbers, line count, and source code snippet corresponding
        to a section / presentation step from the scene's Python file.
        """
        if not code_path or not Path(code_path).is_file():
            return {
                "file": str(code_path) if code_path else None,
                "start_line": None,
                "end_line": None,
                "line_count": 0,
                "code_snippet": ""
            }

        try:
            with open(code_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

            sec_regex = re.compile(r"^\s*##\s*(?:Presentation Step|Section|Step)\s+(\d+)\b", re.IGNORECASE)
            marks = [(idx, int(m.group(1))) for idx, line in enumerate(lines) for m in [sec_regex.match(line)] if m]

            sid_target = int(section_id) if str(section_id).isdigit() else section_id
            target_idx = next((k for k, m in enumerate(marks) if m[1] == sid_target), None)

            if target_idx is None:
                return {
                    "file": str(code_path),
                    "start_line": None,
                    "end_line": None,
                    "line_count": 0,
                    "code_snippet": ""
                }

            start_line_0 = marks[target_idx][0]
            if target_idx + 1 < len(marks):
                end_line_0 = marks[target_idx + 1][0] - 1
            else:
                end_line_0 = len(lines) - 1

            while end_line_0 > start_line_0 and not lines[end_line_0].strip():
                end_line_0 -= 1

            snippet = "\n".join(lines[start_line_0:end_line_0 + 1])
            return {
                "file": str(code_path),
                "start_line": start_line_0 + 1,
                "end_line": end_line_0 + 1,
                "line_count": (end_line_0 - start_line_0 + 1),
                "code_snippet": snippet
            }
        except Exception as e:
            print(f"  [WARN] Failed to slice code for section {section_id}: {e}")
            return {
                "file": str(code_path),
                "start_line": None,
                "end_line": None,
                "line_count": 0,
                "code_snippet": ""
            }

    def _extract_visual_objects_for_manifest(self, snap_json, cell_map, target_names, legend):
        """
        Builds a structured list of visible visual elements with bounding boxes,
        grid cell spans, coverage distributions, SoM badges, and layout flags.
        """
        visual_objects = []
        for obj in snap_json.get("objects", []):
            if not obj.get("visible") or obj.get("degenerate") or not obj.get("name"):
                continue
            if obj.get("is_generic") and obj.get("name") not in target_names:
                continue

            bbox = obj.get("bbox") or [[0.0, 0.0], [0.0, 0.0]]
            (ox0, oy0, *_), (ox1, oy1, *_) = bbox

            cov = _cell_coverage(bbox, cell_map) if cell_map else []
            span_str = _span(cov) if cov else "?"
            top_cells = [{"cell": c, "percent": round(p, 1)} for c, p in cov[:6]]

            badge_id = None
            if legend:
                for b_str, b_name in legend.items():
                    if b_name == obj.get("name"):
                        badge_id = int(b_str) if str(b_str).isdigit() else b_str
                        break

            flags = []
            if ox1 > 6.4:
                flags.append(f"RIGHT OVERFLOW (right={ox1:.2f} > 6.4)")
            if ox0 < -6.4:
                flags.append(f"LEFT OVERFLOW (left={ox0:.2f} < -6.4)")
            if oy1 > 3.4:
                flags.append(f"TOP SAFE-ZONE BREACH (top={oy1:.2f} > 3.4)")
            if oy0 < -3.5:
                flags.append(f"BOTTOM SAFE-ZONE BREACH (bottom={oy0:.2f} < -3.5)")

            visual_objects.append({
                "name": obj.get("name"),
                "type": obj.get("type", "Unknown"),
                "width": round(obj.get("width", 0.0), 3),
                "height": round(obj.get("height", 0.0), 3),
                "center": [round(c, 3) for c in (obj.get("center") or [0.0, 0.0])[:2]],
                "manim_bbox": [
                    [round(ox0, 3), round(oy0, 3)],
                    [round(ox1, 3), round(oy1, 3)]
                ],
                "grid_span": span_str,
                "grid_cells": top_cells,
                "som_badge": badge_id,
                "is_issue_target": obj.get("name") in target_names,
                "fill_color": obj.get("fill_color"),
                "stroke_color": obj.get("stroke_color"),
                "flags": flags
            })

        return visual_objects

    def generate_triangulated_result(self, scene_number, base_dir=".", report_dir="llm_error_reports_vlm", theme="non_promo", grid_mode="edges"):
        """
        Processes keyframes for a scene, overlays grids and SoM badges,
        and generates a comprehensive manifest.json mapping grids to code blocks and visuals.
        """
        base = Path(base_dir)
        scene_dir = base / "correction_insights_vlm" / f"scene_{scene_number}"
        report_path = base / report_dir / f"scene_{scene_number}_full_report.json"
        output_dir = base / "vlm_inputs" / f"scene_{scene_number}"

        output_dir.mkdir(parents=True, exist_ok=True)

        if not scene_dir.is_dir() or not report_path.is_file():
            print(f"[NOTICE] Snapshots/report not found for scene {scene_number} -- using direct video keyframe fallback.")
            return self._fallback_video_extraction(base, scene_number, output_dir, grid_mode)

        print(f"Building selection manifest from {report_path} ...")
        manifest = build_manifest(str(report_path))

        code_file = self._find_scene_code(base, scene_number)
        code_file_rel = str(code_file.relative_to(base)) if code_file and code_file.is_relative_to(base) else (str(code_file) if code_file else None)

        scene_manifest_data = {
            "scene_number": int(scene_number) if str(scene_number).isdigit() else scene_number,
            "scene_code_file": code_file_rel,
            "generated_at": datetime.now().isoformat(),
            "extraction_mode": "snapshots",
            "total_frames_processed": 0,
            "sections": {}
        }

        total_processed = 0
        unresolved_count = 0
        missing_file_count = 0

        for section_id, data in manifest.items():
            code_block_info = self._extract_code_block_for_section(code_file, section_id)
            if code_block_info.get("file") and code_file and code_file.is_relative_to(base):
                code_block_info["file"] = str(code_file.relative_to(base))

            section_keyframes = []

            for frame_data in data["frames"]:
                frame_num = frame_data["frame_number"]

                if frame_num is None:
                    unresolved_count += len(frame_data["issues"])
                    print(f"  [WARN] section {section_id}: {len(frame_data['issues'])} issue(s) "
                        f"at t={frame_data['timestamp']:.3f} could not be matched to any "
                        f"snapshot frame (outside frame_tol) -- NOT sent to VLM.")
                    continue

                original_json = scene_dir / f"snapshot_{frame_num:04d}.json"
                original_png = scene_dir / f"snapshot_{frame_num:04d}.png"

                if not (original_png.exists() and original_json.exists()):
                    missing_file_count += 1
                    print(f"  [WARN] section {section_id}: frame {frame_num:04d} resolved "
                        f"but snapshot_{frame_num:04d}.json/.png missing on disk -- skipped.")
                    continue

                prefix = f"sec_{section_id}_frame_{frame_num:04d}_{frame_data['reason']}"
                dest_json = output_dir / f"{prefix}.json"
                dest_png = output_dir / f"{prefix}_grid.png"
                dest_cellmap = output_dir / f"{prefix}_cellmap.json"

                with open(original_json, "r", encoding='utf-8') as f:
                    snap_json = json.load(f)
                snap_json["filtered_issues_for_vlm"] = frame_data["issues"]

                fw_units, fh_units = 14.222, 8.0  # Safe fallback 16:9 defaults
                cam_center = (0.0, 0.0)

                for obj in snap_json.get("objects", []):
                    # MovingCameraScene stores its frame as a ScreenRectangle
                    if obj.get("type") == "ScreenRectangle":
                        fw_units = obj["width"]
                        fh_units = obj["height"]
                        cam_center = (obj["center"][0], obj["center"][1])
                        break
                
                # Use dynamic columns so cells stay square
                t_cols = 7 if (fh_units > fw_units) else 12
                    
                _, cell_map = add_grid_overlay(
                    image_path=str(original_png),
                    output_path=str(dest_png),
                    mode=grid_mode,
                    frame_height_units=fh_units,
                    frame_width_units=fw_units,
                    camera_center=cam_center,
                    target_cols=t_cols
                )

                # Persist raw cellmap lookup table for precision coordinate references
                with open(dest_cellmap, "w", encoding='utf-8') as f:
                    json.dump(cell_map, f, indent=2, ensure_ascii=False)

                # Set-of-Mark: outline + number the issue-involved objects directly on the grid image
                rank = {}
                for iss in frame_data["issues"]:
                    if not isinstance(iss, dict):
                        continue
                    r = iss.get("extent") or 0.0
                    for n in iss.get("objects", []):
                        rank[n] = max(rank.get(n, 0.0), r)
                target_names = sorted(rank, key=rank.get, reverse=True)
                legend = {}
                if target_names:
                    legend = add_som_annotations(
                        str(dest_png), str(dest_png),
                        snap_json.get("objects", []), target_names,
                        frame_height_units=fh_units,
                        frame_width_units=fw_units,
                        camera_center=cam_center
                    )
                    snap_json["som_markers"] = legend
                grid_lines = grid_geometry_summary(cell_map)
                obj_lines = describe_objects_on_grid(
                    snap_json.get("objects", []), cell_map,
                    priority_names=target_names)
                snap_json["grid_context_text"] = "\n".join(
                    grid_lines + [""]
                    + ["Objects in frame:"]
                    + obj_lines)             

                with open(dest_json, "w", encoding='utf-8') as f:
                    json.dump(snap_json, f, indent=2, ensure_ascii=False)

                # Extract rich visual objects for manifest
                visual_objects = self._extract_visual_objects_for_manifest(
                    snap_json, cell_map, target_names, legend
                )

                # Assemble keyframe entry mapping grid to visual
                keyframe_entry = {
                    "frame_number": frame_num,
                    "timestamp": round(snap_json.get("timestamp", frame_data.get("timestamp", 0.0)), 3),
                    "reason": frame_data.get("reason", "unknown"),
                    "grid": {
                        "image_file": dest_png.name,
                        "metadata_json": dest_json.name,
                        "cellmap_json": dest_cellmap.name,
                        "grid_columns": t_cols,
                        "grid_rows": len(set(k[1:] for k in cell_map.keys())) if cell_map else 7,
                        "cell_width_units": round(fw_units / t_cols, 3) if t_cols else None,
                        "cell_height_units": round(fh_units / (len(cell_map) / t_cols), 3) if cell_map and t_cols else None,
                        "camera_center": [round(c, 3) for c in cam_center]
                    },
                    "visuals": {
                        "total_objects": len(visual_objects),
                        "som_markers": legend,
                        "issues": snap_json.get("filtered_issues_for_vlm", []),
                        "objects": visual_objects,
                        "grid_context_text": snap_json.get("grid_context_text", "")
                    }
                }
                section_keyframes.append(keyframe_entry)

                print(f"  Processed: {prefix} ({len(frame_data['issues'])} issues)")
                total_processed += 1

            scene_manifest_data["sections"][str(section_id)] = {
                "section_id": int(section_id) if str(section_id).isdigit() else section_id,
                "presentation_step": int(section_id) if str(section_id).isdigit() else section_id,
                "code_block": code_block_info,
                "keyframes": section_keyframes
            }

        scene_manifest_data["total_frames_processed"] = total_processed

        print(f"\nPhase 2 complete: {total_processed} frames prepped in {output_dir}")
        if unresolved_count or missing_file_count:
            print(f"  -> {unresolved_count} issue(s) unresolved (no matching frame within tolerance), "
                f"{missing_file_count} frame(s) missing on disk. Check frame_tol / file paths above.")

        if total_processed == 0:
            print(f"[NOTICE] 0 frames processed from snapshots for scene {scene_number} -- running direct video keyframe extraction.")
            return self._fallback_video_extraction(base, scene_number, output_dir, grid_mode)

        # Save per-scene manifest.json
        scene_manifest_path = output_dir / "manifest.json"
        with open(scene_manifest_path, "w", encoding="utf-8") as f:
            json.dump(scene_manifest_data, f, indent=2, ensure_ascii=False)
        print(f"  [Manifest] Saved scene triangulation manifest -> {scene_manifest_path}")

        return scene_manifest_data

    def _fallback_video_extraction(self, base, scene_number, output_dir, grid_mode="edges"):
        """Direct video keyframe extraction fallback to guarantee VLM visual inputs are never missing."""
        video_file = base / "manim_extracted_videos" / f"group_{scene_number}.mp4"
        if not video_file.exists():
            video_file = base / "manim_time_synced_videos" / f"group_{scene_number}.mp4"
        if not video_file.exists():
            print(f"[WARN] No extracted video found for fallback extraction: {video_file}")
            return {}

        print(f"🎬 [Fallback] Extracting keyframes directly from {video_file.name} for VLM review...")
        meta_dir = base / "metadata_blueprints"
        cgi_file = meta_dir / "CGI_Input.json" if (meta_dir / "CGI_Input.json").exists() else (base / "CGI_Input.json")
        sections_list = []
        if cgi_file.exists():
            try:
                with open(cgi_file, "r", encoding="utf-8") as f:
                    cgi_data = json.load(f)
                sections_list = cgi_data.get(str(scene_number), [])
            except Exception:
                pass

        if not sections_list:
            sections_list = [{"run_time": 10.0}]

        code_file = self._find_scene_code(base, scene_number)
        code_file_rel = str(code_file.relative_to(base)) if code_file and code_file.is_relative_to(base) else (str(code_file) if code_file else None)

        fallback_scene_manifest = {
            "scene_number": int(scene_number) if str(scene_number).isdigit() else scene_number,
            "scene_code_file": code_file_rel,
            "generated_at": datetime.now().isoformat(),
            "extraction_mode": "video_ffmpeg_fallback",
            "total_frames_processed": 0,
            "sections": {}
        }

        total_fallback_frames = 0
        running_t = 0.0
        for s_idx, s_info in enumerate(sections_list, start=1):
            s_dur = float(s_info.get("run_time", 8.0))
            t_mid = running_t + 0.45 * s_dur
            t_end = max(t_mid + 1.0, running_t + 0.95 * s_dur)
            running_t += s_dur

            code_block_info = self._extract_code_block_for_section(code_file, s_idx)
            if code_block_info.get("file") and code_file and code_file.is_relative_to(base):
                code_block_info["file"] = str(code_file.relative_to(base))

            s_id_str = str(s_idx)
            section_keyframes = []

            for t_sample, r_label in [(t_mid, "error"), (t_end, "aesthetic")]:
                f_num = int(t_sample * 15)
                prefix = f"sec_{s_idx}_frame_{f_num:04d}_{r_label}"
                raw_png = output_dir / f"{prefix}_raw.png"
                grid_png = output_dir / f"{prefix}_grid.png"
                dest_json = output_dir / f"{prefix}.json"
                cellmap_path = output_dir / f"{prefix}_cellmap.json"

                cmd = ["ffmpeg", "-y", "-ss", str(max(0.0, t_sample)), "-i", str(video_file), "-frames:v", "1", str(raw_png)]
                subprocess.run(cmd, capture_output=True, check=False)

                cell_map = {}
                if raw_png.exists():
                    try:
                        _, cell_map = add_grid_overlay(str(raw_png), output_path=str(grid_png), mode=grid_mode)
                    except Exception:
                        shutil.copy(str(raw_png), str(grid_png))
                    raw_png.unlink(missing_ok=True)

                    frame_meta = {
                        "timestamp": round(t_sample, 3),
                        "frame": f_num,
                        "section": s_idx,
                        "filtered_issues_for_vlm": [f"Visual review for Presentation Step {s_idx}"],
                        "grid_context_text": f"Presentation Step {s_idx} keyframe at t={t_sample:.1f}s",
                        "som_markers": {}
                    }
                    with open(dest_json, "w", encoding="utf-8") as f:
                        json.dump(frame_meta, f, indent=2)

                    cellmap_data = cell_map if cell_map else {"grid_mode": grid_mode, "timestamp": t_sample}
                    with open(cellmap_path, "w", encoding="utf-8") as f:
                        json.dump(cellmap_data, f, indent=2)

                    section_keyframes.append({
                        "frame_number": f_num,
                        "timestamp": round(t_sample, 3),
                        "reason": r_label,
                        "grid": {
                            "image_file": grid_png.name,
                            "metadata_json": dest_json.name,
                            "cellmap_json": cellmap_path.name,
                            "grid_columns": 12,
                            "grid_rows": 7,
                            "camera_center": [0.0, 0.0]
                        },
                        "visuals": {
                            "total_objects": 0,
                            "som_markers": {},
                            "issues": frame_meta["filtered_issues_for_vlm"],
                            "objects": [],
                            "grid_context_text": frame_meta["grid_context_text"]
                        }
                    })
                    total_fallback_frames += 1

            fallback_scene_manifest["sections"][s_id_str] = {
                "section_id": s_idx,
                "presentation_step": s_idx,
                "code_block": code_block_info,
                "keyframes": section_keyframes
            }

        fallback_scene_manifest["total_frames_processed"] = total_fallback_frames

        # Save per-scene manifest.json
        scene_manifest_path = output_dir / "manifest.json"
        with open(scene_manifest_path, "w", encoding="utf-8") as f:
            json.dump(fallback_scene_manifest, f, indent=2, ensure_ascii=False)
        print(f"  [Manifest] Saved fallback scene triangulation manifest -> {scene_manifest_path}")

        return fallback_scene_manifest
        
    # ---------------------------------------------------------
    # BATCH RUNNERS
    # ---------------------------------------------------------

    def generate_report_with_grid_overlay(self, config_data, topic_id):
        print(f"[Simulated] Running generate_feedback_report for {topic_id}")
        base_folder = config_data['base_folder']
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        cgi_input_file = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_input_file):
            cgi_input_file = f"{base_folder}/CGI_Input.json"
        
        cgi_input = self.load_json(cgi_input_file)

        topic_manifest = {
            "topic_id": topic_id,
            "stage": 17,
            "stage_name": "Visual Triangulation & Set-of-Marks",
            "generated_at": datetime.now().isoformat(),
            "scenes": {}
        }

        for group in cgi_input.keys():
            scene_manifest = self.generate_triangulated_result(
                scene_number = group,
                base_dir = base_folder,
                report_dir="llm_error_reports_vlm",
                theme = config_data.get("theme", "non_promo")
            )
            print(f"The manifest generated for Scene {group}:{scene_manifest}")
            topic_manifest["scenes"][str(group)] = scene_manifest

        # Save topic-level combined manifest
        topic_manifest_path = Path(base_folder) / "vlm_inputs" / "manifest.json"
        with open(topic_manifest_path, "w", encoding="utf-8") as f:
            json.dump(topic_manifest, f, indent=2, ensure_ascii=False)
        print(f"📦 [Stage 17] Saved master triangulation manifest -> {topic_manifest_path}")

        return f"{base_folder}/vlm_inputs"

    def process_files(self, target_topic_id=None):
        input_tracker = self._load_tracker(self.input_tracker_path)
        if not input_tracker: return

        for topic_id, input_entry in input_tracker.items():
            if target_topic_id and topic_id != target_topic_id:
                continue
            if not input_entry.get("processed", False): continue

            output_tracker = self._load_tracker(self.output_tracker_path)
            if topic_id in output_tracker and output_tracker[topic_id].get("processed", False): continue

            print(f"Processing {topic_id}...")
            base_folder = os.path.join(self.input_folder, topic_id)
            config_path = os.path.join(base_folder, "ex_config.json")
            
            if not os.path.exists(config_path): continue
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                output_file_path = self.generate_report_with_grid_overlay(config_data, topic_id)
                
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": output_file_path, "processed": True,
                    "topic_name": topic_id, "topic_id": topic_id, "failure_reason": None
                }
                self._save_tracker(self.output_tracker_path, tracker)
                print(f"Successfully processed {topic_id}.")

            except Exception as e:
                print(f"Error processing {topic_id}: {e}")
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": None, "processed": False,
                    "topic_name": topic_id, "topic_id": topic_id, "failure_reason": str(e)
                }
                self._save_tracker(self.output_tracker_path, tracker)

if __name__=="__main__":
    workflow_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(workflow_dir)
    trackers_dir = os.path.join(parent_dir, "ppt_trackers") if os.path.exists(os.path.join(parent_dir, "ppt_trackers")) else os.path.join(parent_dir, "trackers")
    data_dir = os.path.join(parent_dir, "output") if os.path.exists(os.path.join(parent_dir, "output")) else (os.path.join(parent_dir, "data_ppt_advanced") if os.path.exists(os.path.join(parent_dir, "data_ppt_advanced")) else os.path.abspath("."))

    generate_vlm_feedback_tracker = os.path.join(trackers_dir, "16_generate_vlm_feedback_tracker.json")
    if not os.path.exists(generate_vlm_feedback_tracker):
        generate_vlm_feedback_tracker = os.path.join(trackers_dir, "generate_vlm_feedback_tracker.json")
    generate_triangulation_tracker = os.path.join(trackers_dir, "17_generate_triangulation_tracker.json")
    if not os.path.exists(generate_triangulation_tracker):
        generate_triangulation_tracker = os.path.join(trackers_dir, "generate_triangulation_tracker.json")

    stage = GridVisualTriangulation(
        input_tracker_path=generate_vlm_feedback_tracker,
        output_tracker_path=generate_triangulation_tracker, 
        input_folder=data_dir
    )
    stage.process_files()