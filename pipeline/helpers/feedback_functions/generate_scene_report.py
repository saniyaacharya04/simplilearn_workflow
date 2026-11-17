import json
import os
import math
import re
from collections import defaultdict


# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

PROXIMITY_THRESHOLD = 1.0
MIN_OVERLAP_TO_REPORT = 0.05

IGNORE_OBJECT_KEYWORDS = {
    "bg",
    "background"
}


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def determine_section(timestamp, scene_sections):

    running = 0.0

    for idx, section in enumerate(scene_sections, start=1):

        running += section.get("run_time", 0)

        if timestamp <= running:
            return idx

    return len(scene_sections)


def euclidean_distance(a, b):

    dx = a["center"][0] - b["center"][0]
    dy = a["center"][1] - b["center"][1]

    return math.sqrt(dx * dx + dy * dy)


def object_name(obj):

    return obj.get(
        "name",
        obj.get("id", "unknown")
    )


def should_ignore_object(name):

    lower = name.lower()

    return any(
        keyword in lower
        for keyword in IGNORE_OBJECT_KEYWORDS
    )


# ---------------------------------------------------------
# RELATIONSHIP LOOKUP
# ---------------------------------------------------------

def build_relationship_index(snapshot):

    rels_by_source = defaultdict(list)
    rels_by_target = defaultdict(list)

    for rel in snapshot.get("relationships", []):

        rels_by_source[rel["source"]].append(rel)
        rels_by_target[rel["target"]].append(rel)

    return rels_by_source, rels_by_target


# ---------------------------------------------------------
# PART DETAILS
# ---------------------------------------------------------

def generate_part_details(snapshot):

    objects = snapshot["objects"]

    object_lookup = {
        obj["id"]: obj
        for obj in objects
    }

    # Identify topmost definite objects (evaluation candidates)
    # These are visible, non-generic objects with no non-generic ancestors.
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

    # Build a lookup for edge distances from pre-calculated relationships
    # Map (id_a, id_b) -> edge_distance
    edge_dist_lookup = {}
    for rel in snapshot.get("relationships", []):
        pair = tuple(sorted([rel["source"], rel["target"]]))
        edge_dist_lookup[pair] = rel.get("edge_distance", 0.0)

    # ---------------------------------------
    # Parent-child relationships
    # ---------------------------------------

    parent_groups = defaultdict(list)

    for rel in snapshot.get("relationships", []):

        if rel["relation"] == "contains":

            parent_id = rel["source"]
            child_id = rel["target"]

            parent_groups[parent_id].append(child_id)

    # ---------------------------------------
    # Only compare siblings
    # ---------------------------------------

    for parent_id, children in parent_groups.items():

        for child_id in children:
            # Only report details for topmost definite objects to reduce noise
            if child_id not in eval_ids:
                continue

            child = object_lookup.get(child_id)

            if not child:
                continue

            child_name = object_name(child)

            if child_name not in part_details:
                part_details[child_name] = {
                    "dimensions": f"{child['width']:.2f} units wide by {child['height']:.2f} units tall",
                    "current_position": [round(child["center"][0], 2), round(child["center"][1], 2)],
                    "constraints": []
                }

            for sibling_id in children:

                if sibling_id == child_id:
                    continue

                # Only compare against other topmost definite objects
                if sibling_id not in eval_ids:
                    continue

                pair = tuple(sorted([child_id, sibling_id]))
                if pair not in edge_dist_lookup:
                    continue
                
                distance = edge_dist_lookup[pair]

                if distance > PROXIMITY_THRESHOLD:
                    continue

                sibling = object_lookup.get(sibling_id)
                if not sibling:
                    continue

                dx = (
                    sibling["center"][0]
                    - child["center"][0]
                )

                dy = (
                    sibling["center"][1]
                    - child["center"][1]
                )

                if abs(dx) > abs(dy):

                    orientation = (
                        "left of"
                        if dx > 0
                        else "right of"
                    )

                else:

                    orientation = (
                        "below"
                        if dy > 0
                        else "above"
                    )

                part_details[child_name]["constraints"].append(
                    f"{orientation} {object_name(sibling)} "
                    f"with edge distance "
                    f"{distance:.2f} units"
                )

            parent_obj = object_lookup.get(parent_id)

            if parent_obj:

                if not parent_obj.get("is_generic"):
                    part_details[child_name]["constraints"].append(
                        f"contained within "
                        f"{object_name(parent_obj)}"
                    )

    return part_details


# ---------------------------------------------------------
# ISSUE SUMMARIZATION
# ---------------------------------------------------------

def generate_issue_descriptions(snapshot):

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
                should_ignore_object(a_name)
                or should_ignore_object(b_name)
            ):
                continue

            a = object_lookup.get(a_name)
            b = object_lookup.get(b_name)

            # Use pre-calculated overlap details from the snapshot metadata
            details = issue.get("details", {})
            overlap_extent = details.get("overlap_extent", 0.0)

            if not a or not b or overlap_extent < MIN_OVERLAP_TO_REPORT:
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

    return descriptions


# ---------------------------------------------------------
# REPAIR HINTS
# ---------------------------------------------------------

def generate_repair_hints(issue_descriptions):

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


    return sorted(set(hints))


# ---------------------------------------------------------
# MAIN ANALYSIS
# ---------------------------------------------------------

def analyze_snapshot(
    snapshot_path,
    cgi_input_path,
    scene_id="2"
):

    snapshot = load_json(snapshot_path)

    cgi_input = load_json(cgi_input_path)

    timestamp = snapshot.get(
        "timestamp",
        snapshot.get("time", 0)
    )

    scene_sections = cgi_input[scene_id]

    section = determine_section(
        timestamp,
        scene_sections
    )

    issue_descriptions = (
        generate_issue_descriptions(
            snapshot
        )
    )

    output = {
        "scene": scene_id,
        "section": section,
        "timestamp": timestamp,
        "issues": issue_descriptions,
        "part_details": generate_part_details(
            snapshot
        ),
        "repair_hints": generate_repair_hints(
            issue_descriptions
        )
    }

    return output


# ---------------------------------------------------------
# DIRECTORY PROCESSOR
# ---------------------------------------------------------

def analyze_directory(
    snapshot_dir,
    cgi_input_path,
    output_dir,
    scene_id="2"
):
    """Aggregates all snapshots into a single report dictionary keyed by section number."""
    os.makedirs(output_dir, exist_ok=True)

    cgi_input = load_json(cgi_input_path)
    scene_sections = cgi_input.get(scene_id, [])

    # Aggregator: section_id -> { issues: set, part_details: {name: set}, hints: set }
    aggregated = defaultdict(lambda: {
        "issues": set(),
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
        snapshot = load_json(snapshot_path)

        timestamp = snapshot.get("timestamp", snapshot.get("time", 0))
        section_idx = determine_section(timestamp, scene_sections)

        # Generate raw data for this snapshot
        issues = generate_issue_descriptions(snapshot)
        parts = generate_part_details(snapshot)

        # Merge into the section aggregate
        target = aggregated[section_idx]
        target["issues"].update(issues)
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
        for issue in sorted(list(data["issues"])):
            if issue not in seen_issues_globally:
                unique_issues.append(issue)
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
        final_hints = generate_repair_hints(unique_issues)

        report = {
            "scene": scene_id,
            "section": section_idx,
            "issues": unique_issues,
            "part_details": final_part_details,
            "repair_hints": final_hints
        }

        full_report[section_idx] = report

    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------
# EXAMPLE
# ---------------------------------------------------------

if __name__ == "__main__":

    cgi_input_file = "../../CGI_Input.json"
    all_snapshots_dir = "../../correction_insights"

    cgi_input = load_json(cgi_input_file)
    
    for group,group_data in cgi_input.items():
        snapshot_dir = os.path.join(all_snapshots_dir, f"scene_{group}")

        analyze_directory(
            snapshot_dir=snapshot_dir,
            cgi_input_path=cgi_input_file,
            output_dir="../../llm_error_reports",
            scene_id=group
        )