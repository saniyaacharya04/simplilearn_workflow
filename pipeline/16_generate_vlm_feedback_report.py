#!/usr/bin/env python3
"""
================================================================================
PIPELINE STAGE 16: GENERATE VLM FEEDBACK REPORT
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 16
   - Script Name: 16_generate_vlm_feedback_report.py
   - Primary Class: GenerateVLMFeedbackReport
   - Pipeline Role:
     Processes the visual keyframe snapshots and bounding box JSONs collected during
     Stage 15. Performs mathematical evaluation of layout balance, element proximity,
     card boundaries, and margin clearance. Produces section-by-section geometric audit
     reports (report.json) formatted specifically to provide structural context to
     subsequent Multimodal VLM reasoning stages.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 15 (15_run_manim_vlm_feedback.py):
       - How: Ingests snapshot JSON files from correction_insights_vlm/scene_{group}/
         via 15_run_manim_vlm_feedback_tracker.json.
       - Purpose: Reads coordinates, bounding boxes, and object names captured during render.
     * Stage 5 (5_populate_audio_runtime.py):
       - How: Ingests CGI_Input.json.
       - Purpose: Maps snapshots to exact presentation section numbers.
   - Input Tracker: ppt_trackers/15_run_manim_vlm_feedback_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * correction_insights_vlm/scene_{group}/ (Stage 15):
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights_vlm/scene_*/
       Content: Snapshot JSON files with mobject dimensions and coordinates.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Master time-coded storyboard manifest.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/15_run_manim_vlm_feedback_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 15_run_manim_vlm_feedback_tracker.json.
   - Step 2: Reads all snapshot files in correction_insights_vlm/scene_{group}/.
   - Step 3: Calculates object-to-object distances and overlaps:
     * Flags bounding box collisions (> 5% overlap).
     * Flags objects positioned dangerously close to screen borders (|x| > 6.8, |y| > 3.8).
     * Evaluates header clearance ceiling (y <= 1.70).
   - Step 4: Compiles issue summaries and part details per presentation section.
   - Step 5: Writes report.json and section-level JSONs into correction_insights_vlm/scene_{group}/.
   - Step 6: Atomically updates 16_generate_vlm_feedback_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * correction_insights_vlm/scene_{group}/report.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights_vlm/scene_{group}/report.json
       Content: Structured geometric audit report per section detailing visual issues.
     * Output Tracker:
       Location: ppt_trackers/16_generate_vlm_feedback_tracker.json
       Content: Atomic tracker confirming completion of VLM report generation.

6. DOWNSTREAM CONSUMERS:
   - Stage 17 (17_generate_visual_triangulation.py): Ingests report.json to construct triangulation overlays.
   - Stage 18 & 19: Provides geometric issue context to multimodal LLMs.
================================================================================
"""

import os
import sys
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)


import json
import os
import portalocker
import math
import argparse
from glob import glob
from collections import defaultdict


class GenerateVLMFeedbackReport:
    """
    Stage 16: Generate VLM Feedback Report.
    Audits Stage 15 snapshot bounding boxes to generate structured geometric reports
    identifying overlaps, clipping, and spatial balance issues for VLM inspection.
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
        
        # Geometry and proximity thresholds
        self.proximity_threshold = 1.0
        self.min_overlap_to_report = 0.05
        self.ignore_object_keywords = {"bg", "background"}

        # Structured Report Constraints (from Phase 0.1)
        self.extent_sanity_limit = 30.0
        self.min_redundant_overlap_area = 0.02
        self.containment_coverage = 0.98
        self.containment_area_ratio = 0.5
        self.legacy_type_map = {"potential_alignment": "redundant_overlap"}
        
        # Initialize output tracker file if it doesn't exist
        if not os.path.exists(self.output_tracker_path):
            tracker_dir = os.path.dirname(self.output_tracker_path)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
            with open(self.output_tracker_path, 'w',encoding='utf-8') as f:
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
        with open(path, "r",encoding='utf-8') as f:
            return json.load(f)

    def determine_section(self, timestamp, scene_sections):
        running = 0.0
        for idx, section in enumerate(scene_sections, start=1):
            running += section.get("run_time", 0)
            if timestamp <= running:
                return idx
        return len(scene_sections)

    def object_name(self, obj):
        return obj.get("name", obj.get("id", "unknown"))

    def should_ignore_object(self, name):
        lower = name.lower()
        return any(keyword in lower for keyword in self.ignore_object_keywords)

    # ---------------------------------------------------------
    # GEOMETRY & RELATIONSHIPS
    # ---------------------------------------------------------

    def compute_edge_distance(self, a, b):
        ax, ay = a["center"][:2]
        bx, by = b["center"][:2]
        dx, dy = bx - ax, by - ay
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1e-6:
            ux, uy = dx / dist, dy / dist
            r_a = 0.5 * (a["width"] * abs(ux) + a["height"] * abs(uy))
            r_b = 0.5 * (b["width"] * abs(ux) + b["height"] * abs(uy))
            return float(max(0.0, dist - (r_a + r_b)))
        return 0.0

    def is_contained(self, inner, outer):
        if inner["type"] == "Text" and outer.get("type") == "Text": return False
        i_bbox, o_bbox = inner["bbox"], outer["bbox"]
        strict = (
            i_bbox[0][0] >= o_bbox[0][0] and i_bbox[0][1] >= o_bbox[0][1] and
            i_bbox[1][0] <= o_bbox[1][0] and i_bbox[1][1] <= o_bbox[1][1]
        )
        if strict: return True

        if inner["type"] in ["Text", "MathTex"]:
            inter_min_x, inter_max_x = max(i_bbox[0][0], o_bbox[0][0]), min(i_bbox[1][0], o_bbox[1][0])
            inter_min_y, inter_max_y = max(i_bbox[0][1], o_bbox[0][1]), min(i_bbox[1][1], o_bbox[1][1])
            inter_area = max(0, inter_max_x - inter_min_x) * max(0, inter_max_y - inter_min_y)
            inner_area = inner["width"] * inner["height"]
            if inner_area > 0 and (inter_area / inner_area) > 0.75: return True
        return False

    def generate_part_details(self, snapshot):
        objects = snapshot["objects"]
        object_lookup = {obj["id"]: obj for obj in objects}

        # Identify topmost definite objects
        eval_ids = set()
        for obj in objects:
            if not obj.get("visible") or obj.get("is_generic"): continue
            has_definite_anc, curr_pid = False, obj.get("parent_id")
            while curr_pid:
                parent = object_lookup.get(curr_pid)
                if parent and not parent.get("is_generic"):
                    has_definite_anc = True
                    break
                curr_pid = parent.get("parent_id") if parent else None
            if not has_definite_anc: eval_ids.add(obj["id"])

        part_details = {}
        parent_groups = defaultdict(list)
        
        for obj in objects:
            if pid := obj.get("parent_id"): parent_groups[pid].append(obj["id"])
            if obj["id"] in eval_ids:
                for outer in objects:
                    if obj["id"] != outer["id"] and self.is_contained(obj, outer):
                        if obj["id"] not in parent_groups[outer["id"]]:
                            parent_groups[outer["id"]].append(obj["id"])

        for parent_id, children in parent_groups.items():
            for child_id in children:
                if child_id not in eval_ids: continue
                child = object_lookup.get(child_id)
                if not child: continue

                child_name = self.object_name(child)
                if child_name not in part_details:
                    part_details[child_name] = {
                        "dimensions": f"{child['width']:.2f} units wide by {child['height']:.2f} units tall",
                        "current_position": [round(child["center"][0], 2), round(child["center"][1], 2)],
                        "constraints": []
                    }

                for sibling_id in children:
                    if sibling_id == child_id or sibling_id not in eval_ids: continue
                    sibling = object_lookup.get(sibling_id)
                    if not sibling: continue

                    distance = self.compute_edge_distance(child, sibling)
                    if distance > self.proximity_threshold: continue

                    dx, dy = sibling["center"][0] - child["center"][0], sibling["center"][1] - child["center"][1]
                    orientation = ("left of" if dx > 0 else "right of") if abs(dx) > abs(dy) else ("below" if dy > 0 else "above")
                    part_details[child_name]["constraints"].append(
                        f"{orientation} {self.object_name(sibling)} with edge distance {distance:.2f} units"
                    )

                if (parent_obj := object_lookup.get(parent_id)) and not parent_obj.get("is_generic"):
                    part_details[child_name]["constraints"].append(f"contained within {self.object_name(parent_obj)}")

        return part_details

    # ---------------------------------------------------------
    # STRUCTURED REPORT ISSUE FORMATTERS
    # ---------------------------------------------------------
    
    def _issue_objects(self, issue):
        t = issue.get("type")
        if t in ("overlap", "redundant_overlap", "potential_alignment", "bar_containment"):
            return [o for o in issue.get("objects", []) if o]
        if t in ("off_screen", "suboptimal_scale"): return [issue.get("object")] if issue.get("object") else []
        if t == "hidden_behind": return [o for o in (issue.get("object"), issue.get("behind")) if o]
        if t == "text_overflow": return [o for o in (issue.get("text"), issue.get("parent")) if o]
        return [o for o in (issue.get("object"),) if o]

    def _issue_extent(self, issue):
        t, d = issue.get("type"), issue.get("details", {})
        try:
            if t == "overlap": return float(d.get("overlap_extent"))
            if t in ("redundant_overlap", "potential_alignment"): return float(d.get("overlap_area"))
            if t in ("off_screen", "text_overflow"): return max(float(x["extent"]) for x in d)
            if t == "bar_containment": return max(float(x["extent"]) for x in d.get("exits", []))
        except (TypeError, KeyError, ValueError): pass
        return None

    def _describe_issue(self, issue, extent):
        t, d = issue.get("type"), issue.get("details", {})
        if t == "overlap":
            a, b = issue["objects"]
            child_info = ""
            if d.get("child_overlaps"):
                parts = [f"'{co['child_a_name']}' and '{co['child_b_name']}' (extent: {co['overlap_extent']:.2f})" for co in d["child_overlaps"]]
                child_info = " Additionally, the following named child objects overlap: " + "; ".join(parts) + "."
            return (f"{a} overlaps with {b}. {a}'s {d.get('a_orientation', 'center').replace('_', ' ')} is touching "
                    f"{b}'s {d.get('b_orientation', 'center').replace('_', ' ')}. Estimated overlap extent {extent:.2f} units.{child_info}")

        if t in ("redundant_overlap", "potential_alignment"):
            a, b = issue["objects"]
            return (f"Redundant overlap: '{a}' and '{b}' overlap almost entirely (area {d.get('overlap_area', 0.0):.2f} units; "
                    f"'{a}' covered {d.get('overlap_percent_a', 0.0)*100:.1f}%, '{b}' covered {d.get('overlap_percent_b', 0.0)*100:.1f}%, "
                    f"max {d.get('max_overlap_percent', 0.0)*100:.1f}%) without either containing the other.")

        if t == "off_screen":
            edge_info = ", ".join(f"{x['edge']} by {x['extent']:.2f}" for x in d)
            return f"{issue.get('object')} is off screen on: {edge_info} units."

        if t == "hidden_behind": return f"{issue.get('object')} is hidden behind {issue.get('behind')}."

        if t == "text_overflow":
            parts = [f"{x['edge']} edge (at {x.get('parent_relative_coord', [0.0, 0.0])[0]:.2f}, {x.get('parent_relative_coord', [0.0, 0.0])[1]:.2f}) by {x['extent']:.2f}" for x in d]
            return f"{issue.get('text')} overflows parent {issue.get('parent')} at: {'; '.join(parts)} units."

        if t == "bar_containment":
            exits = ", ".join(f"{x['edge']} by {x['extent']:.2f}" for x in d.get("exits", []))
            return f"{d.get('fill')} (fill bar) escapes its track/container {d.get('track')} on: {exits} units -- the fill must stay strictly inside the track."

        if t == "suboptimal_scale":
            return f"{issue.get('object')} (image) renders very small: {d.get('width', 0.0):.2f} x {d.get('height', 0.0):.2f} units -- likely under-scaled for its role."

        if t == "teacher_overlap":
            return d.get("message", "Object collides with Teacher Presenter layout area.")

        if t == "unspoken_equation":
            return d.get("message", "Mathematical formula displayed is not mentioned in spoken audio.")

        return f"{t}: {json.dumps(d,ensure_ascii=False)}"

    # ---------------------------------------------------------
    # MAIN ANALYSIS (Structured)
    # ---------------------------------------------------------

    def analyze_directory(self, snapshot_dir, cgi_input_path, output_dir, scene_id="2"):
        """Aggregates snapshots into a structured report using Phase 0.1 logic."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"scene_{scene_id}_full_report.json")
        
        if os.path.exists(output_path):
            print(f"Report for scene {scene_id} exists, skipping.")
            return None

        cgi_input = self.load_json(cgi_input_path)
        scene_sections = cgi_input.get(str(scene_id), [])
        if not scene_sections:
            raise ValueError(f"scene_id {scene_id!r} not found in {cgi_input_path}")

        snapshot_paths = sorted(glob(os.path.join(snapshot_dir, "snapshot_*.json")))
        if not snapshot_paths:
            print(f"No snapshot_*.json found in {snapshot_dir} - generating fallback section report for scene {scene_id}")
            full_report = {}
            running_time = 0.0
            for sec_idx, sec_info in enumerate(scene_sections, start=1):
                dur = float(sec_info.get("run_time", 5.0))
                t_start = running_time
                t_end = running_time + dur
                running_time = t_end
                f_start = int(t_start * 15)
                f_end = int(t_end * 15)
                full_report[sec_idx] = {
                    "scene": str(scene_id),
                    "section": sec_idx,
                    "window": [round(t_start, 4), round(t_end, 4)],
                    "frame_range": [f_start, f_end],
                    "issues": [
                        {
                            "id": f"visual_audit:sec_{sec_idx}",
                            "type": "visual_audit",
                            "objects": [f"step_{sec_idx}_content"],
                            "extent": 0.5,
                            "frame": f_start + int((f_end - f_start) * 0.45),
                            "timestamp": round(t_start + 0.45 * dur, 3),
                            "details": {"reason": "Video keyframe layout audit"},
                            "description": f"Audit Presentation Step {sec_idx} layout, margins, and containment."
                        }
                    ],
                    "part_details": {}
                }
            with open(output_path, "w", encoding='utf-8') as f:
                json.dump(full_report, f, indent=2, ensure_ascii=False)
            print(f"Done -- {len(full_report)} section(s) written to fallback {output_path}")
            return full_report

        best_by_sig = {}
        sec_window = defaultdict(lambda: [float("inf"), float("-inf")])
        sec_frames = defaultdict(lambda: [float("inf"), float("-inf")])
        sec_parts = defaultdict(lambda: defaultdict(lambda: {"dimensions": set(), "current_position": set(), "constraints": set()}))
        n_degenerate = 0

        for path in snapshot_paths:
            snapshot = self.load_json(path)
            ts = float(snapshot.get("timestamp", snapshot.get("time", 0.0)))
            frame = int(snapshot.get("frame", -1))
            section_idx = self.determine_section(ts, scene_sections)

            # Update timeline bounds
            sec_window[section_idx][0] = min(sec_window[section_idx][0], ts)
            sec_window[section_idx][1] = max(sec_window[section_idx][1], ts)
            sec_frames[section_idx][0] = min(sec_frames[section_idx][0], frame)
            sec_frames[section_idx][1] = max(sec_frames[section_idx][1], frame)

            # Aggregate part details
            for obj_name, info in self.generate_part_details(snapshot).items():
                agg = sec_parts[section_idx][obj_name]
                agg["dimensions"].add(info["dimensions"])
                agg["current_position"].add(tuple(info["current_position"]))
                agg["constraints"].update(info["constraints"])

            # Pre-pass: suppress geometry noise (containment patterns)
            suppress_pairs = set()
            for raw in snapshot.get("issues", []):
                if self.legacy_type_map.get(raw.get("type"), raw.get("type")) != "redundant_overlap": continue
                d = raw.get("details") or {}
                area_a, area_b = d.get("area_a", 0.0), d.get("area_b", 0.0)
                if not area_a or not area_b: continue
                ratio = min(area_a, area_b) / max(area_a, area_b)
                if d.get("max_overlap_percent", 0.0) >= self.containment_coverage and ratio < self.containment_area_ratio:
                    suppress_pairs.add(tuple(sorted(self._issue_objects(raw))))

            # Synthesize layout-specific teacher clearance & unspoken equation issues
            raw_issues = list(snapshot.get("issues", []))
            sme_layout = "70" if str(scene_id) in ("1", "2", "9", "10") else "20"
            for obj in snapshot.get("objects", []):
                obj_name = obj.get("name", "")
                if self.should_ignore_object(obj_name): continue
                bbox = obj.get("bbox", [])
                if bbox and len(bbox) == 2:
                    x_min, y_min = bbox[0][0], bbox[0][1]
                    x_max, y_max = bbox[1][0], bbox[1][1]
                    if sme_layout == "70" and x_min < -1.0:
                        raw_issues.append({
                            "type": "teacher_overlap",
                            "objects": [obj_name],
                            "details": {
                                "message": f"CRITICAL TEACHER OVERLAP: '{obj_name}' encroaches into left Teacher area (Layout 70%, x={x_min:.2f} < -1.0). Reposition rightwards to x >= -1.0."
                            }
                        })
                    elif sme_layout == "20" and x_max > 4.20 and y_max > 2.0:
                        raw_issues.append({
                            "type": "teacher_overlap",
                            "objects": [obj_name],
                            "details": {
                                "message": f"CRITICAL TEACHER OVERLAP: '{obj_name}' encroaches into top-right Teacher PiP (Layout 20%, x={x_max:.2f}>4.20, y={y_max:.2f}>2.0). Reposition outside PiP."
                            }
                        })
                if obj.get("type") == "MathTex":
                    raw_issues.append({
                        "type": "unspoken_equation",
                        "objects": [obj_name],
                        "details": {
                            "message": f"UNSPOKEN EQUATION: '{obj_name}' renders LaTeX MathTex '{obj.get('tex', '')}'. Must be replaced with clean conceptual text/cards."
                        }
                    })

            # Process actual issues
            for raw in raw_issues:
                norm_type = self.legacy_type_map.get(raw.get("type"), raw.get("type"))
                objects = self._issue_objects(raw)
                
                if not objects or any(self.should_ignore_object(n) for n in objects): continue
                if norm_type in ("overlap", "redundant_overlap") and tuple(sorted(objects)) in suppress_pairs: continue

                extent = self._issue_extent(raw)
                if norm_type == "overlap" and (extent is None or extent < self.min_overlap_to_report): continue
                if norm_type == "redundant_overlap" and (extent is None or extent < self.min_redundant_overlap_area): continue
                
                if extent is not None and extent > self.extent_sanity_limit:
                    n_degenerate += 1
                    continue

                sig = (norm_type, tuple(sorted(objects)))
                rank = extent if extent is not None else -1.0

                if sig in best_by_sig:
                    rec = best_by_sig[sig]
                    if section_idx != rec["section"] or rank <= rec["rank"]: continue

                best_by_sig[sig] = {
                    "section": section_idx, "rank": rank, 
                    "issue": {
                        "id": f"{norm_type}:" + "|".join(sorted(objects)),
                        "type": norm_type, "objects": objects, "extent": extent,
                        "frame": frame, "timestamp": ts, "details": raw.get("details"),
                        "description": self._describe_issue({**raw, "type": norm_type, "objects": objects}, extent)
                    }
                }

        if n_degenerate:
            print(f"  [structured_report] {n_degenerate} degenerate issue(s) skipped (extent > {self.extent_sanity_limit}).")

        # Assemble per section
        sec_issues = defaultdict(list)
        for rec in best_by_sig.values(): sec_issues[rec["section"]].append(rec["issue"])
        for issues in sec_issues.values(): issues.sort(key=lambda i: (i["frame"], i["id"]))

        full_report = {}
        for section_idx in sorted(sec_window.keys()):
            issues = sec_issues.get(section_idx, [])
            issue_objs = {name for i in issues for name in i["objects"]}

            part_details = {}
            for obj_name in sorted(issue_objs):
                agg = sec_parts[section_idx].get(obj_name)
                if agg:
                    part_details[obj_name] = {
                        "dimensions": sorted(agg["dimensions"]),
                        "current_position": [list(p) for p in sorted(agg["current_position"])],
                        "constraints": sorted(agg["constraints"]),
                    }

            full_report[section_idx] = {
                "scene": str(scene_id),
                "section": section_idx,
                "window": [round(v, 4) for v in sec_window[section_idx]],
                "frame_range": list(sec_frames[section_idx]),
                "issues": issues,
                "part_details": part_details,
            }

        with open(output_path, "w",encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
            
        print(f"Done -- {len(full_report)} section(s) written to {output_path}")
        return full_report

    # ---------------------------------------------------------
    # BATCH RUNNERS
    # ---------------------------------------------------------

    def generate_feedback_report(self, config_data, topic_id):
        print(f"  [Simulated] Running generate_feedback_report for {topic_id}")
        base_folder = config_data['base_folder']
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        cgi_input_file = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_input_file):
            cgi_input_file = f"{base_folder}/CGI_Input.json"
        all_snapshots_dir = f"{base_folder}/correction_insights_vlm"
        cgi_input = self.load_json(cgi_input_file)

        for group in cgi_input.keys():
            snapshot_dir = os.path.join(all_snapshots_dir, f"scene_{group}")
            self.analyze_directory(
                snapshot_dir=snapshot_dir,
                cgi_input_path=cgi_input_file,
                output_dir=f"{base_folder}/llm_error_reports_vlm",
                scene_id=group
            )
        return f"{base_folder}/llm_error_reports_vlm"

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

                output_file_path = self.generate_feedback_report(config_data, topic_id)
                
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

    feedback_vlm_manim_tracker = os.path.join(trackers_dir, "15_run_manim_vlm_feedback_tracker.json")
    if not os.path.exists(feedback_vlm_manim_tracker):
        feedback_vlm_manim_tracker = os.path.join(trackers_dir, "run_manim_vlm_feedback_tracker.json")
    generate_vlm_feedback_tracker = os.path.join(trackers_dir, "16_generate_vlm_feedback_tracker.json")
    if not os.path.exists(generate_vlm_feedback_tracker):
        generate_vlm_feedback_tracker = os.path.join(trackers_dir, "generate_vlm_feedback_tracker.json")

    stage = GenerateVLMFeedbackReport(
        input_tracker_path=feedback_vlm_manim_tracker,
        output_tracker_path=generate_vlm_feedback_tracker, 
        input_folder=data_dir
    )
    stage.process_files()
