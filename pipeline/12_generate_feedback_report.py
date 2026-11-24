"""
================================================================================
PIPELINE STAGE 12: FEEDBACK REPORT GENERATION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 12
   - Script Name: 12_generate_feedback_report.py
   - Primary Class: GenerateFeedbackReport
   - Pipeline Role:
     Performs deterministic algorithmic geometric analysis on the snapshot JSONs
     dumped during Stage 11. Calculates object bounding box intersections, canvas
     boundary overshoots, text-to-container clipping, and proximity violations.
     Compiles structured feedback reports per scene and section that highlight
     exact spatial collisions without requiring LLM calls.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 11 (11_run_manim_for_feedback.py):
       - How: Analyzes snapshot JSONs in correction_insights/scene_{group}/ via
         11_run_manim_feedback_tracker.json.
       - Purpose: Reads coordinates, widths, heights, and center points of all rendered mobjects.
     * Stage 5 (5_generate_audio.py):
       - How: Ingests CGI_Input.json.
       - Purpose: Maps timestamped snapshots back to presentation section indices.
   - Input Tracker: ppt_trackers/11_run_manim_feedback_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * correction_insights/scene_{group}/ directory (Stage 11):
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights/scene_*/
       Content: Bounding box snapshot JSON files for each keyframe.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Master time-coded storyboard manifest with section runtimes.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/11_run_manim_feedback_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 11_run_manim_feedback_tracker.json.
   - Step 2: Iterates through each scene group in correction_insights/.
   - Step 3: Filters out background plates and evaluates active foreground elements.
   - Step 4: Performs geometric calculations:
     * Overlap Detection: Flags any pair of mobjects whose bounding box overlap area exceeds min_overlap_to_report (5%).
     * Screen Boundary Clipping: Flags objects with centers/edges extending outside screen limits (|x| > 6.8, |y| > 3.8).
     * Proximity Violations: Flags objects closer than proximity_threshold (1.0 unit) causing visual crowding.
   - Step 5: Maps issues to specific presentation sections using section timestamps.
   - Step 6: Writes aggregated section report to correction_insights/scene_{group}/report.json.
   - Step 7: Atomically updates 12_generate_feedback_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * correction_insights/scene_{group}/report.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/correction_insights/scene_{group}/report.json
       Content: Structured issue diagnostic report per section, listing overlapping
                elements, collision coordinates, and boundary violations.
     * Output Tracker:
       Location: ppt_trackers/12_generate_feedback_tracker.json
       Content: Atomic tracker confirming completion of geometric analysis.

6. DOWNSTREAM CONSUMERS:
   - Stage 13 (13_generate_corrections.py): Uses report.json to generate LLM code fix suggestions.
================================================================================
"""

import os
import sys
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)


import json
import os
import glob
import portalocker
import time
import re
from collections import defaultdict
import math

class GenerateFeedbackReport:
    """
    Stage 12: Feedback Report Generation.
    Performs deterministic geometric audits on Stage 11 snapshots to detect
    collisions, clipping, and crowding without requiring LLM calls.
    """

    def __init__(
        self,
        input_tracker_path,
        output_tracker_path,
        input_folder
    ):
        # Store required class variables (placeholders allowed)
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.input_folder = input_folder
        self.proximity_threshold = 1.0
        self.min_overlap_to_report = 0.05

        self.ignore_object_keywords = {
            "bg",
            "background"
        }
        
        # Initialize output tracker file if it doesn't exist
        if not os.path.exists(self.output_tracker_path):
            # Ensure the directory exists
            tracker_dir = os.path.dirname(self.output_tracker_path)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
                
            with open(self.output_tracker_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

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


    def load_json(self,path):
        with open(path, "r",encoding='utf-8') as f:
            return json.load(f)


    def determine_section(self,timestamp, scene_sections):

        running = 0.0

        for idx, section in enumerate(scene_sections, start=1):

            running += section.get("run_time", 0)

            if timestamp <= running:
                return idx

        return len(scene_sections)


    def euclidean_distance(self,a, b):

        dx = a["center"][0] - b["center"][0]
        dy = a["center"][1] - b["center"][1]

        return math.sqrt(dx * dx + dy * dy)


    def object_name(self,obj):

        return obj.get(
            "name",
            obj.get("id", "unknown")
        )


    def should_ignore_object(self,name):

        lower = name.lower()

        return any(
            keyword in lower
            for keyword in self.ignore_object_keywords
        )


    # ---------------------------------------------------------
    # RELATIONSHIP LOOKUP
    # ---------------------------------------------------------


    def compute_edge_distance(self, a, b):
        """Helper to calculate edge distance between two bounding boxes on-the-fly."""
        import math
        ax, ay = a["center"][:2]
        bx, by = b["center"][:2]
        dx = bx - ax
        dy = by - ay
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1e-6:
            ux, uy = dx / dist, dy / dist
            r_a = 0.5 * (a["width"] * abs(ux) + a["height"] * abs(uy))
            r_b = 0.5 * (b["width"] * abs(ux) + b["height"] * abs(uy))
            return float(max(0.0, dist - (r_a + r_b)))
        return 0.0

    def is_contained(self, inner, outer, strict=False):
        """Helper to verify geometric containment without needing a relationships array."""
        def _is_text_or_title(obj):
            if obj.get("type") in ["Text", "MathTex"]:
                return True
            n = obj.get("name", "").lower()
            return any(k in n for k in ["title", "header", "kicker", "label", "caption", "tag"])

        if _is_text_or_title(inner) and _is_text_or_title(outer):
            return False
        i_bbox = inner["bbox"]
        o_bbox = outer["bbox"]

        strict_contained = (
            i_bbox[0][0] >= o_bbox[0][0] and i_bbox[0][1] >= o_bbox[0][1] and
            i_bbox[1][0] <= o_bbox[1][0] and i_bbox[1][1] <= o_bbox[1][1]
        )
        if strict or strict_contained:
            return strict_contained

        if inner["type"] in ["Text", "MathTex"]:
            inter_min_x = max(i_bbox[0][0], o_bbox[0][0])
            inter_min_y = max(i_bbox[0][1], o_bbox[0][1])
            inter_max_x = min(i_bbox[1][0], o_bbox[1][0])
            inter_max_y = min(i_bbox[1][1], o_bbox[1][1])
            inter_w = max(0, inter_max_x - inter_min_x)
            inter_h = max(0, inter_max_y - inter_min_y)
            inter_area = inter_w * inter_h
            inner_area = inner["width"] * inner["height"]
            if inner_area > 0 and (inter_area / inner_area) >= 0.95:
                return True
        return False

    # ---------------------------------------------------------
    # PART DETAILS
    # ---------------------------------------------------------
    

    def generate_part_details(self, snapshot):
        objects = snapshot["objects"]
        object_lookup = {obj["id"]: obj for obj in objects}

        # Identify topmost definite objects (evaluation candidates)
        eval_ids = set()
        for obj in objects:
            if not obj.get("visible") or obj.get("is_generic"):
                continue
            has_definite_anc = False
            curr_pid = obj.get("parent_id")
            while curr_pid:
                parent = object_lookup.get(curr_pid)
                if parent and not parent.get("is_generic"):
                    has_definite_anc = True
                    break
                curr_pid = parent.get("parent_id") if parent else None
            if not has_definite_anc:
                eval_ids.add(obj["id"])

        part_details = {}

        # ---------------------------------------
        # Parent-child relationships (Constructed On-the-Fly)
        # ---------------------------------------
        parent_groups = defaultdict(list)
        
        for obj in objects:
            # 1. Add structural parents explicitly assigned by Stage 1
            pid = obj.get("parent_id")
            if pid:
                parent_groups[pid].append(obj["id"])
                
            # 2. Add spatial parents strictly for top-level targets to replace old relationship lookup
            if obj["id"] in eval_ids:
                for outer in objects:
                    if obj["id"] == outer["id"]: 
                        continue
                    if self.is_contained(obj, outer):
                        if obj["id"] not in parent_groups[outer["id"]]:
                            parent_groups[outer["id"]].append(obj["id"])

        # ---------------------------------------
        # Only compare siblings
        # ---------------------------------------
        for parent_id, children in parent_groups.items():
            for child_id in children:
                if child_id not in eval_ids:
                    continue

                child = object_lookup.get(child_id)
                if not child:
                    continue

                child_name = self.object_name(child)

                if child_name not in part_details:
                    part_details[child_name] = {
                        "dimensions": f"{child['width']:.2f} units wide by {child['height']:.2f} units tall",
                        "current_position": [round(child["center"][0], 2), round(child["center"][1], 2)],
                        "constraints": []
                    }

                for sibling_id in children:
                    if sibling_id == child_id:
                        continue
                    if sibling_id not in eval_ids:
                        continue

                    sibling = object_lookup.get(sibling_id)
                    if not sibling:
                        continue

                    # Calculate edge distance dynamically
                    distance = self.compute_edge_distance(child, sibling)
                    if distance > self.proximity_threshold:
                        continue

                    dx = sibling["center"][0] - child["center"][0]
                    dy = sibling["center"][1] - child["center"][1]

                    if abs(dx) > abs(dy):
                        orientation = "left of" if dx > 0 else "right of"
                    else:
                        orientation = "below" if dy > 0 else "above"

                    part_details[child_name]["constraints"].append(
                        f"{orientation} {self.object_name(sibling)} "
                        f"with edge distance {distance:.2f} units"
                    )

                parent_obj = object_lookup.get(parent_id)
                if parent_obj and not parent_obj.get("is_generic"):
                    part_details[child_name]["constraints"].append(
                        f"contained within {self.object_name(parent_obj)}"
                    )

        return part_details

    # ---------------------------------------------------------
    # ISSUE SUMMARIZATION
    # ---------------------------------------------------------

    def generate_issue_descriptions(self,snapshot):

        objects = snapshot["objects"]

        object_lookup = {
            obj["name"]: obj
            for obj in objects
            if "name" in obj
        }

        descriptions = []

        for issue in snapshot.get("issues", []):

            issue_type = issue.get("type")

            if issue_type == "overlap":

                objs = issue.get("objects", [])

                if len(objs) != 2:
                    continue

                a_name, b_name = objs

                if (
                    self.should_ignore_object(a_name)
                    or self.should_ignore_object(b_name)
                ):
                    continue

                a = object_lookup.get(a_name)
                b = object_lookup.get(b_name)

                # Use pre-calculated overlap details from the snapshot metadata
                details = issue.get("details", {})
                overlap_extent = details.get("overlap_extent", 0.0)

                if not a or not b or overlap_extent < self.min_overlap_to_report:
                    continue

                a_orient = details.get("a_orientation", "center").replace("_", " ")
                b_orient = details.get("b_orientation", "center").replace("_", " ")

                child_overlaps_info = ""
                child_overlaps = details.get("child_overlaps")
                if child_overlaps:
                    child_details = []
                    for co in child_overlaps:
                        child_details.append(
                            f"'{co['child_a_name']}' and '{co['child_b_name']}' (extent: {co['overlap_extent']:.2f})"
                        )
                    child_overlaps_info = " Additionally, the following named child objects overlap: " + "; ".join(child_details) + "."

                descriptions.append(
                    f"{a_name} overlaps with {b_name}. "
                    f"{a_name}'s {a_orient} is touching {b_name}'s {b_orient}. "
                    f"Estimated overlap extent "
                    f"{overlap_extent:.2f} units.{child_overlaps_info}"
                )
            
            elif issue_type == "potential_alignment":
                objs = issue.get("objects", [])
                if len(objs) != 2:
                    continue
                a_name, b_name = objs
                details = issue.get("details", {})
                overlap_area = details.get("overlap_area", 0.0)
                overlap_percent_a = details.get("overlap_percent_a", 0.0) * 100
                overlap_percent_b = details.get("overlap_percent_b", 0.0) * 100
                max_overlap_percent = details.get("max_overlap_percent", 0.0) * 100

                descriptions.append(
                    f"Potential alignment issue: '{a_name}' and '{b_name}' overlap significantly. "
                    f"Overlap area is {overlap_area:.2f} units. "
                    f"'{a_name}' is covered by {overlap_percent_a:.2f}%, "
                    f"and '{b_name}' is covered by {overlap_percent_b:.2f}%. Max overlap: {max_overlap_percent:.2f}%."
                )

            elif issue_type == "off_screen":
                details = issue.get("details", [])
                edge_info = ", ".join([f"{d['edge']} by {d['extent']:.2f}" for d in details])
                descriptions.append(
                    f"{issue.get('object')} "
                    f"is off screen on: {edge_info} units."
                )

            elif issue_type == "hidden_behind":

                descriptions.append(
                    f"{issue.get('object')} "
                    f"is hidden behind "
                    f"{issue.get('behind')}."
                )

            elif issue_type == "text_overflow":
                details = issue.get("details", [])
                overflow_info = []
                for d in details:
                    coord = d.get('parent_relative_coord', [0.0, 0.0])
                    overflow_info.append(
                        f"{d['edge']} edge (at {coord[0]:.2f}, {coord[1]:.2f}) by {d['extent']:.2f}"
                    )

                descriptions.append(
                    f"{issue.get('text')} "
                    f"overflows parent {issue.get('parent')} at: {'; '.join(overflow_info)} units."
                )

        # Check objects against SME Teacher Layout zones and unspoken MathTex
        scene_layout = getattr(self, "current_scene_layout", "20")
        for obj in objects:
            obj_name = obj.get("name", "")
            if self.should_ignore_object(obj_name):
                continue
            bbox = obj.get("bbox", [])
            if bbox and len(bbox) >= 2:
                try:
                    x_min, y_min = bbox[0][0], bbox[0][1]
                    x_max, y_max = bbox[1][0], bbox[1][1]
                except Exception:
                    continue
                if scene_layout == "70":
                    if x_min < -1.0:
                        descriptions.append(
                            f"CRITICAL TEACHER OVERLAP: '{obj_name}' encroaches into left Teacher Presenter area (Layout 70%). "
                            f"Object left edge is at x = {x_min:.2f} (must be >= -1.0). Reposition rightwards to safe workspace."
                        )
                elif scene_layout == "20":
                    if x_max > 4.20 and y_max > 2.0:
                        descriptions.append(
                            f"CRITICAL TEACHER OVERLAP: '{obj_name}' encroaches into top-right Teacher PiP Window (Layout 20%). "
                            f"Object top-right is at [{x_max:.2f}, {y_max:.2f}] (collides with x > 4.20, y > 2.0). Reposition leftwards or downwards."
                        )
            if obj.get("type") == "MathTex":
                descriptions.append(
                    f"UNSPOKEN MATHEMATICAL NOTATION: '{obj_name}' uses MathTex formula '{obj.get('tex', '')}'. "
                    f"Equations not spoken in narration must be removed and replaced with clean conceptual text/cards."
                )

        return descriptions


    # ---------------------------------------------------------
    # REPAIR HINTS
    # ---------------------------------------------------------

    def generate_repair_hints(self,issue_descriptions):

        hints = []

        for issue in issue_descriptions:
            if "overlaps with" in issue:
                # Format: "{a_name} overlaps with {b_name}. {a_name}'s {a_orient} is touching {b_name}'s {b_orient}. Estimated overlap extent {overlap_extent:.2f} units."
                match = re.search(r"(.+?) overlaps with (.+?)\. .+?'s (.+?) is touching .+?'s (.+?)\. Estimated overlap extent ([\d\.]+) units\.", issue)
                if match:
                    a, b, a_or, b_or, ext = match.groups()
                    hints.append(f"Reposition '{a}' or '{b}' by at least {ext} units to fix the {a_or}/{b_or} overlap.")
                else:
                    hints.append("Increase spacing between overlapping objects.")

            elif "is off screen on:" in issue:
                # Format: "{issue.get('object')} is off screen on: {edge_info} units."
                match = re.search(r"(.+?) is off screen on: (.+?) units\.", issue)
                if match:
                    obj, edges = match.groups()
                    hints.append(f"Move '{obj}' to fix boundaries: {edges}.")
                else:
                    hints.append("Move off-screen objects toward the center.")

            elif "is hidden behind" in issue:
                # Format: "{issue.get('object')} is hidden behind {issue.get('behind')}."
                match = re.search(r"(.+?) is hidden behind (.+?)\.", issue)
                if match:
                    obj, blocker = match.groups()
                    hints.append(f"Set z_index of '{obj}' higher than '{blocker}' to reveal it.")
                else:
                    hints.append("Adjust render order (z-index) for obscured objects.")

            elif "overflows parent" in issue:
                # Format: "{issue.get('text')} overflows parent {issue.get('parent')} at: {'; '.join(overflow_info)} units."
                match = re.search(r"(.+?) overflows parent (.+?) at: (.+?) units\.", issue)
                if match:
                    txt, parent, detail = match.groups()
                    hints.append(f"Reduce font size of '{txt}' or expand '{parent}' to fix overflow: {detail}.")
                else:
                    hints.append("Fix text overflow by scaling down text or widening the container.")
            
            elif "Potential alignment issue:" in issue:
                match = re.search(r"Potential alignment issue: '(.+?)' and '(.+?)' overlap significantly\. Overlap area is ([\d\.]+) units\. '(.+?)' is covered by ([\d\.]+)%, and '(.+?)' is covered by ([\d\.]+)%\. Max overlap: ([\d\.]+)%\.", issue)
                if match:
                    a_name, b_name, overlap_area, _, overlap_percent_a, _, overlap_percent_b, max_overlap_percent = match.groups()
                    hints.append(f"Adjust the position or size of '{a_name}' and '{b_name}' to reduce overlap below {max_overlap_percent} percent or ensure one fully contains the other.")
                else:
                    hints.append("Adjust position or size of overlapping rectangles to reduce overlap or ensure full containment.")

            elif "CRITICAL TEACHER OVERLAP:" in issue:
                match = re.search(r"CRITICAL TEACHER OVERLAP: '(.+?)'", issue)
                obj = match.group(1) if match else "object"
                if "Layout 70%" in issue:
                    hints.append(f"Move '{obj}' to the right so its left edge is at or right of x = -1.0 (Layout 70 safe area is x >= -1.0).")
                else:
                    hints.append(f"Move '{obj}' leftwards (x <= 4.20) or downwards (y <= 2.0) to avoid overlapping the 20% Teacher PiP.")

            elif "UNSPOKEN MATHEMATICAL NOTATION:" in issue:
                match = re.search(r"UNSPOKEN MATHEMATICAL NOTATION: '(.+?)'", issue)
                obj = match.group(1) if match else "equation"
                hints.append(f"Replace MathTex '{obj}' with a clean CrispText label or visual diagram card as equations were not spoken in narration.")


        return sorted(set(hints))


    # ---------------------------------------------------------
    # MAIN ANALYSIS
    # ---------------------------------------------------------


    def analyze_snapshot(
        self,
        snapshot_path,
        cgi_input_path,
        scene_id="2"
    ):

        snapshot = self.load_json(snapshot_path)
        cgi_input = self.load_json(cgi_input_path)

        timestamp = snapshot.get(
            "timestamp",
            snapshot.get("time", 0)
        )

        scene_sections = cgi_input[scene_id]

        section = self.determine_section(
            timestamp,
            scene_sections
        )

        issue_descriptions = (
            self.generate_issue_descriptions(
                snapshot
            )
        )

        output = {
            "scene": scene_id,
            "section": section,
            "timestamp": timestamp,
            "issues": issue_descriptions,
            # Assign the current timestamp to every issue found in this snapshot
            "issue_timestamps": [timestamp] * len(issue_descriptions),
            "part_details": self.generate_part_details(
                snapshot
            )
        }

        return output


    # ---------------------------------------------------------
    # DIRECTORY PROCESSOR
    # ---------------------------------------------------------


    def analyze_directory(
        self,
        snapshot_dir,
        cgi_input_path,
        output_dir,
        scene_id="2"
    ):
        """Aggregates all snapshots into a single report dictionary keyed by section number."""
        os.makedirs(output_dir, exist_ok=True)
        self.current_scene_layout = "70" if str(scene_id) in ("1", "2", "9", "10") else "20"

        cgi_input = self.load_json(cgi_input_path)
        scene_sections = cgi_input.get(scene_id, [])

        # Aggregator: section_id -> { issues: dict(issue -> timestamp), part_details: {name: dict} }
        # Changed "issues" from a set() to a dict() to track the earliest timestamp
        aggregated = defaultdict(lambda: {
            "issues": {}, 
            "part_details": defaultdict(lambda: {
                "dimensions": set(),
                "current_position": set(),
                "constraints": set()
            }),
        })
        
        if not os.path.exists(snapshot_dir):
            print(f"Directory {snapshot_dir} does not exist.")
            return
        
        # Save the entire dictionary into one file
        output_path = os.path.join(output_dir, f"scene_{scene_id}_full_report.json")
        if os.path.exists(output_path):
            print(f"Report for scene {scene_id} exists, so skipping it")
            return

        filenames = sorted([f for f in os.listdir(snapshot_dir) if f.endswith(".json")])

        for filename in filenames:
            snapshot_path = os.path.join(snapshot_dir, filename)
            snapshot = self.load_json(snapshot_path)

            timestamp = snapshot.get("timestamp", snapshot.get("time", 0))
            section_idx = self.determine_section(timestamp, scene_sections)

            # Generate raw data for this snapshot
            issues = self.generate_issue_descriptions(snapshot)
            parts = self.generate_part_details(snapshot)

            # Merge into the section aggregate
            target = aggregated[section_idx]
            
            # Map issue description to its first seen timestamp
            for issue in issues:
                if issue not in target["issues"]:
                    target["issues"][issue] = timestamp
                else:
                    # Keep the earliest timestamp if issue occurs multiple times
                    target["issues"][issue] = min(target["issues"][issue], timestamp)

            for obj_name, info in parts.items():
                obj_agg = target["part_details"][obj_name]
                obj_agg["dimensions"].add(info["dimensions"])
                obj_agg["current_position"].add(tuple(info["current_position"]))
                obj_agg["constraints"].update(info["constraints"])

        # Consolidated dictionary for all sections
        full_report = {}
        seen_issues_globally = set()
        seen_details_globally = set()

        for section_idx, data in sorted(aggregated.items()):
            # Only retain issues that haven't appeared in any previous section
            unique_issues = []
            unique_issue_timestamps = []
            
            for issue in sorted(list(data["issues"].keys())):
                if issue not in seen_issues_globally:
                    unique_issues.append(issue)
                    unique_issue_timestamps.append(data["issues"][issue])
                    seen_issues_globally.add(issue)

            # Only include part_details for objects mentioned in new issues
            objects_with_new_issues = set()
            for issue in unique_issues:
                for name in data["part_details"].keys():
                    if name in issue:
                        objects_with_new_issues.add(name)

            final_part_details = {}
            for obj_name in sorted(list(objects_with_new_issues)):
                obj_agg = data["part_details"].get(obj_name)
                if not obj_agg:
                    continue

                res = {}
                for field in ["dimensions", "current_position", "constraints"]:
                    field_data = sorted(list(obj_agg[field]))
                    unique_for_field = []
                    for item in field_data:
                        # Composite key to track field-specific data globally
                        key = (obj_name, field, item)
                        if key not in seen_details_globally:
                            # Convert coordinates back to list for JSON compatibility
                            val = list(item) if field == "current_position" else item
                            unique_for_field.append(val)
                            seen_details_globally.add(key)
                    
                    if unique_for_field:
                        res[field] = unique_for_field

                if res:
                    final_part_details[obj_name] = res
            
            # Generate hints based on the unique issues found across the whole section
            #final_hints = generate_repair_hints(unique_issues)

            report = {
                "scene": scene_id,
                "section": section_idx,
                "issues": unique_issues,
                "issue_timestamps": unique_issue_timestamps,
                "part_details": final_part_details
                #"repair_hints": final_hints
            }

            full_report[section_idx] = report

        
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        return full_report

    def generate_feedback_report(self, config_data, topic_id):
        """
        Function for the generate_feedback_report logic.
        This would typically call the LLM APIs using the API keys and prompts.
        """
        print(f"  [Simulated] Running generate_feedback_report for {topic_id}")
        
        base_folder = config_data['base_folder']
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        cgi_input_file = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_input_file):
            cgi_input_file = f"{base_folder}/CGI_Input.json"
        all_snapshots_dir = f"{base_folder}/correction_insights"

        cgi_input = self.load_json(cgi_input_file)

        for group,group_data in cgi_input.items():
            skip_scenes_env = os.environ.get("SKIP_SCENES")
            if skip_scenes_env and str(group) in [s.strip() for s in skip_scenes_env.split(",")]:
                print(f"Skipping Scene {group} per SKIP_SCENES")
                continue
            snapshot_dir = os.path.join(all_snapshots_dir, f"scene_{group}")

            self.analyze_directory(
                snapshot_dir=snapshot_dir,
                cgi_input_path=cgi_input_file,
                output_dir=f"{base_folder}/llm_error_reports",
                scene_id=group
            )
        
        
        return f"{base_folder}/llm_error_reports"

    def process_files(self, target_topic_id=None):
        """
        Main logic to process unprocessed files.
        """
        input_tracker = self._load_tracker(self.input_tracker_path)
        if not input_tracker:
            print(f"Input tracker is empty or missing: {self.input_tracker_path}")
            return

        print(f"Found {len(input_tracker)} items in input tracker.")

        for topic_id, input_entry in input_tracker.items():
            if target_topic_id and topic_id != target_topic_id:
                continue
            # 1. Skip if input processed is False
            # We cannot process a narration if the previous stage (storyboard) failed or isn't done.
            if not input_entry.get("processed", False):
                print(f"Skipping {topic_id}: Input not marked as processed.")
                continue

            # 2. Check output tracker (Reload to define current state)
            output_tracker = self._load_tracker(self.output_tracker_path)

            if os.environ.get("FORCE_RUN") != "1" and topic_id in output_tracker and output_tracker[topic_id].get("processed", False):
                print(f"Skipping {topic_id}: Already processed in output tracker.")
                continue

            print(f"Processing {topic_id}...")
            
            base_folder = os.path.join(self.input_folder, topic_id)
            
            # Define expected file paths
            config_path = os.path.join(base_folder, "ex_config.json")
            
            if not os.path.exists(config_path):
                print(f"Skipping {topic_id}: Missing context.txt or ex_config.json.")
                continue
            
            try:
                # Read input files
                
                with open(config_path, 'r',encoding='utf-8') as f:
                    config_data = json.load(f)

                # 3. Call fit_scene
                output_file_path = self.generate_feedback_report(config_data, topic_id)
                
                # 4. Update tracker (Success)
                # Re-load tracker to minimize race conditions
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": output_file_path,
                    "processed": True,
                    "topic_name": topic_id,
                    "topic_id": topic_id,
                    "failure_reason": None
                }
                self._save_tracker(self.output_tracker_path,tracker)
                print(f"Successfully processed {topic_id}.")

            except Exception as e:
                print(f"Error processing {topic_id}: {e}")
                # 5. Update tracker (Failure)
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": None,
                    "processed": False,
                    "topic_name": topic_id,
                    "topic_id": topic_id,
                    "failure_reason": str(e)
                }
                self._save_tracker(self.output_tracker_path,tracker)

if __name__=="__main__":
    workflow_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(workflow_dir)
    trackers_dir = os.path.join(parent_dir, "ppt_trackers") if os.path.exists(os.path.join(parent_dir, "ppt_trackers")) else os.path.join(parent_dir, "trackers")
    data_dir = os.path.join(parent_dir, "output") if os.path.exists(os.path.join(parent_dir, "output")) else (os.path.join(parent_dir, "data_ppt_advanced") if os.path.exists(os.path.join(parent_dir, "data_ppt_advanced")) else os.path.abspath("."))

    feedback_manim_tracker = os.path.join(trackers_dir, "11_run_manim_feedback_tracker.json")
    if not os.path.exists(feedback_manim_tracker):
        feedback_manim_tracker = os.path.join(trackers_dir, "run_manim_feedback_tracker.json")
    generate_feedback_report = os.path.join(trackers_dir, "12_generate_feedback_tracker.json")
    if not os.path.exists(generate_feedback_report):
        generate_feedback_report = os.path.join(trackers_dir, "generate_feedback_tracker.json")

    stage = GenerateFeedbackReport(
        input_tracker_path=feedback_manim_tracker,
        output_tracker_path=generate_feedback_report, 
        input_folder=data_dir
    )
    stage.process_files()