import json
import inspect
import os
import uuid
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
from manim import *
import sys
CURRENT_DIR = Path(__file__).resolve().parent

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

class SceneSnapshotManager:

    def __init__(self, output_dir="scene_snapshots"):
        self.output_dir = output_dir
        self.frame_counter = 0

        config_env = os.environ.get("EX_CONFIG_PATH")
        if config_env and os.path.exists(config_env):
            self.config_file_path = Path(config_env)
        else:
            out_p = Path(output_dir).resolve()
            found_cfg = None
            curr = out_p
            while curr != curr.parent:
                if (curr / "ex_config.json").exists():
                    found_cfg = curr / "ex_config.json"
                    break
                curr = curr.parent

            if found_cfg:
                self.config_file_path = found_cfg
            elif (Path.cwd().parent / "ex_config.json").exists():
                self.config_file_path = Path.cwd().parent / "ex_config.json"
            elif (Path.cwd() / "ex_config.json").exists():
                self.config_file_path = Path.cwd() / "ex_config.json"
            else:
                self.config_file_path = Path.cwd() / "ex_config.json"
        if not os.path.exists(self.config_file_path):
            print("Did not find the config file")
            self.theme = "non_promo"
        else:
            print("Found the config file")
            with open(self.config_file_path,'r', encoding="utf-8") as f:
                config_data = json.load(f)
            self.theme = config_data.get("theme","non_promo")
            print(f"The current video theme is:{self.theme}")

        os.makedirs(output_dir, exist_ok=True)

    # --------------------------------------------------
    # PUBLIC ENTRY POINT
    # --------------------------------------------------

    def capture(self, scene):

        # Build a map of object IDs to variable names from the caller's scope
        self.var_name_map = {}
        try:
            # Search the stack for the 'construct' method to capture local variable names
# NEW
            curr_frame = inspect.currentframe()
            construct_locals = {}
            while curr_frame:
                if curr_frame.f_code.co_name == 'construct':
                    construct_locals = dict(curr_frame.f_locals)
                    break
                curr_frame = curr_frame.f_back

            # Pass 1: direct variable names (locals win over indexed names)
            for name, val in construct_locals.items():
                self.var_name_map[id(val)] = name
            for name, val in scene.__dict__.items():
                self.var_name_map[id(val)] = name

            # Pass 2 (0.4): indexed names for elements of lists/tuples and
            # VGroup/Group children, e.g. small_boxes[7] -- setdefault so a
            # direct local name always takes priority
            for name, val in construct_locals.items():
                items = None
                if isinstance(val, (list, tuple)):
                    items = val
                elif type(val).__name__ in ("VGroup", "Group"):
                    items = val.submobjects
                if items:
                    for i, item in enumerate(items):
                        if isinstance(item, Mobject):
                            self.var_name_map.setdefault(id(item), f"{name}[{i}]")
        except Exception:
            pass

        objects = []
        visited = set()
        object_lookup = {}
        counters = defaultdict(int)

        def walk(mobj, parent_id=None):
            if id(mobj) in visited:
                return
            visited.add(id(mobj))

            obj_data = self.extract_object(mobj, counters)
            obj_data["parent_id"] = parent_id
            object_lookup[id(mobj)] = obj_data

            objects.append(obj_data)
            for child in mobj.submobjects:
                walk(child, obj_data["id"])

        for root in scene.mobjects:
            walk(root)

        
        issues = self.detect_issues(objects)

        snapshot = {
            "frame": self.frame_counter,
            "timestamp": float(scene.renderer.time),
            "object_count": len(objects),
            "objects": objects,
            "issues": issues
        }

        filename = os.path.join(
            self.output_dir,
            f"snapshot_{self.frame_counter:04d}.json"
        )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)

        self.save_frame_image(scene)

        self.frame_counter += 1

    def save_frame_image(self, scene):
        """
        Saves the current rendered frame as a PNG using the exact same
        frame_counter as the JSON snapshot, so snapshot_0061.json and
        snapshot_0061.png always correspond to the identical moment in time.
        This is what gets handed to the VLM in Phase 3 -- no grid overlay,
        since the JSON already carries exact coordinates as text context.
        """
        try:
            # grid = NumberPlane(background_line_style={"stroke_opacity": 0.4})
            # scene.add(grid)
            image = scene.renderer.camera.get_image()
            # scene.remove(grid)
        except Exception as e:
            # Don't let image capture failures break the (already working)
            # JSON/issue-detection pipeline.
            print(f"[SceneSnapshotManager] Warning: failed to capture frame image: {e}")
            return

        image_path = os.path.join(
            self.output_dir,
            f"snapshot_{self.frame_counter:04d}.png"
        )

        try:
            image.save(image_path)
        except Exception as e:
            print(f"[SceneSnapshotManager] Warning: failed to save frame image: {e}")

    # --------------------------------------------------
    # OBJECT EXTRACTION
    # --------------------------------------------------

    def extract_object(self, obj, counters):

        class_name = obj.__class__.__name__

        counters[class_name] += 1

        obj_name = self.generate_name(
            obj,
            class_name,
            counters[class_name]
        )
        is_generic = obj_name == f"{class_name}_{counters[class_name]}"

        center = obj.get_center()

        bbox = np.array([obj.get_corner(DL), obj.get_corner(UR)])
        
        # Calculate aggregate opacity. Containers (Groups) often have 0 opacity themselves 
        # while containing visible objects. FadeOut(group) sets all family opacities to 0.
        opacity = 0.0
        family = obj.get_family()
        has_opacity_defined = False
        
        for member in family:
            if isinstance(member, VMobject):
                opacity = max(opacity, float(member.get_fill_opacity()), float(member.get_stroke_opacity()))
                has_opacity_defined = True
            elif hasattr(member, "opacity"):
                opacity = max(opacity, float(member.opacity))
                has_opacity_defined = True
        
        if not has_opacity_defined:
            opacity = 1.0

        # Color extraction (needed for the contrast check, and as extra
        # context for the VLM's aesthetic pass). Wrapped defensively since
        # not every mobject type exposes fill/stroke color the same way.
        fill_color = None
        stroke_color = None
        try:
            if isinstance(obj, VMobject):
                if float(obj.get_fill_opacity()) > 0:
                    fill_color = obj.get_fill_color().to_hex()
                if float(obj.get_stroke_opacity()) > 0:
                    stroke_color = obj.get_stroke_color().to_hex()
        except Exception:
            pass

        return {
            "id": str(uuid.uuid4())[:8],
            "name": obj_name,
            "type": class_name,
            "center": [
                float(center[0]),
                float(center[1]),
                float(center[2])
            ],
            "width": float(obj.width),
            "height": float(obj.height),
            "z_index": int(obj.z_index),
            "visible": opacity > 0,
            "is_generic": is_generic,
            "opacity": opacity,
            "bbox": bbox.tolist(),
            "fill_color": fill_color,
            "stroke_color": stroke_color
        }

    # --------------------------------------------------
    # GENERIC AUTO NAMING
    # --------------------------------------------------

    def generate_name(
        self,
        obj,
        class_name,
        count
    ):

        # Prioritize names found in the source code variable assignments
        if hasattr(self, "var_name_map") and id(obj) in self.var_name_map:
            return self.var_name_map[id(obj)]

        try:

            if isinstance(obj, Text):
                txt = obj.text.strip()

                if txt:
                    return f"Text[{txt[:40]}]"

        except:
            pass

        try:

            if isinstance(obj, MathTex):
                tex = "".join(obj.tex_strings)

                if tex:
                    return f"MathTex[{tex[:40]}]"

        except:
            pass

        return f"{class_name}_{count}"

    # --------------------------------------------------
    # SPATIAL RELATIONSHIPS
    # --------------------------------------------------

    def derive_spatial_relationships(
        self,
        objects
    ):

        relationships = []

        n = len(objects)

        for i in range(n):

            a = objects[i]

            for j in range(i + 1, n):

                b = objects[j]

                ax, ay = a["center"][:2]
                bx, by = b["center"][:2]

                dx = bx - ax
                dy = by - ay

                dist = np.sqrt(
                    dx * dx +
                    dy * dy
                )

                # Edge-to-edge distance along center-line
                if dist > 1e-6:
                    ux, uy = dx / dist, dy / dist
                    r_a = 0.5 * (a["width"] * abs(ux) + a["height"] * abs(uy))
                    r_b = 0.5 * (b["width"] * abs(ux) + b["height"] * abs(uy))
                    edge_dist = float(dist - (r_a + r_b))
                else:
                    edge_dist = 0.0

                # containment and hidden_behind
                if self.is_contained(a, b):
                    relationships.append({
                        "source": b["id"],
                        "target": a["id"],
                        "relation": "contains",
                        "edge_distance": edge_dist
                    })

                    # Check if 'a' is hidden behind 'b'
                    if a["z_index"] < b["z_index"] and b["opacity"] > 0.6:
                        relationships.append({
                            "source": a["id"],
                            "target": b["id"],
                            "relation": "hidden_behind",
                            "edge_distance": edge_dist
                        })
                    
                elif self.is_contained(b, a):
                    relationships.append({
                        "source": a["id"],
                        "target": b["id"],
                        "relation": "contains",
                        "edge_distance": edge_dist
                    })

                    # Check if 'b' is hidden behind 'a'
                    if b["z_index"] < a["z_index"] and a["opacity"] > 0.6:
                        relationships.append({
                            "source": b["id"],
                            "target": a["id"],
                            "relation": "hidden_behind",
                            "edge_distance": edge_dist
                        })

                # near

                if dist < 1.5:

                    relationships.append({
                        "source": a["id"],
                        "target": b["id"],
                        "relation": "near",
                        "edge_distance": edge_dist
                    })

                # diagonals
                if abs(dx) > 0.5 and abs(dy) > 0.5:
                    if dx > 0 and dy > 0: d_rel = "lower_left"
                    elif dx < 0 and dy > 0: d_rel = "lower_right"
                    elif dx > 0 and dy < 0: d_rel = "upper_left"
                    else: d_rel = "upper_right"
                    
                    relationships.append({
                        "source": a["id"],
                        "target": b["id"],
                        "relation": d_rel,
                        "edge_distance": edge_dist
                    })

                # left/right

                if abs(dx) > 0.5:

                    if dx > 0:

                        relationships.append({
                            "source": a["id"],
                            "target": b["id"],
                            "relation": "left_of",
                            "edge_distance": edge_dist
                        })

                    else:

                        relationships.append({
                            "source": a["id"],
                            "target": b["id"],
                            "relation": "right_of",
                            "edge_distance": edge_dist
                        })

                # above/below

                if abs(dy) > 0.5:

                    if dy > 0:

                        relationships.append({
                            "source": a["id"],
                            "target": b["id"],
                            "relation": "below",
                            "edge_distance": edge_dist
                        })

                    else:

                        relationships.append({
                            "source": a["id"],
                            "target": b["id"],
                            "relation": "above",
                            "edge_distance": edge_dist
                        })

        return relationships

    # --------------------------------------------------
    # ISSUE DETECTION
    # --------------------------------------------------
    def classify_bar_pair(self, a, b):
        """(fill, track) if a/b look like a fill bar (or nested box) paired with
        its containing track rectangle, else None. Pattern: both rectangles, the
        smaller has >=60% of its area inside the larger, and EITHER the larger
        is >=1.5x the smaller's area (partial fill) OR the intersection also
        covers >=50% of the larger (near-concentric pair, e.g. a ~full bar).
        Role tiebreak: if exactly one of the two has a fill_color, that one is
        the fill regardless of size (tracks are typically stroke-only)."""
        if a["type"] not in ("Rectangle", "RoundedRectangle"):
            return None
        if b["type"] not in ("Rectangle", "RoundedRectangle"):
            return None
        if not self.overlaps(a, b):
            return None
        area_a = a["width"] * a["height"]
        area_b = b["width"] * b["height"]
        if area_a <= 0 or area_b <= 0:
            return None
        small, big = (a, b) if area_a <= area_b else (b, a)
        small_area = min(area_a, area_b)
        big_area = max(area_a, area_b)
        inter = self.calculate_overlap_area(a, b)
        if inter / small_area < 0.6:
            return None
        if not (big_area >= 1.5 * small_area or inter / big_area >= 0.5):
            return None
        has_fill_small = bool(small.get("fill_color"))
        has_fill_big = bool(big.get("fill_color"))
        if has_fill_small != has_fill_big:
            return (small, big) if has_fill_small else (big, small)
        return small, big

    def bar_exit_details(self, fill, track, tol=0.02):
        """Per-edge extents by which `fill` escapes `track`'s bbox."""
        (fx0, fy0, *_), (fx1, fy1, *_) = fill["bbox"]
        (tx0, ty0, *_), (tx1, ty1, *_) = track["bbox"]
        exits = []
        if tx0 - fx0 > tol: exits.append({"edge": "left",   "extent": float(tx0 - fx0)})
        if fx1 - tx1 > tol: exits.append({"edge": "right",  "extent": float(fx1 - tx1)})
        if ty0 - fy0 > tol: exits.append({"edge": "bottom", "extent": float(ty0 - fy0)})
        if fy1 - ty1 > tol: exits.append({"edge": "top",    "extent": float(fy1 - ty1)})
        return exits

    def detect_issues(self, objects):

        issues = []
        obj_map = {o["id"]: o for o in objects}

        has_children = defaultdict(bool)
        for obj in objects:
            if obj.get("parent_id"):
                has_children[obj["parent_id"]] = True

        eval_objects = []
        for obj in objects:
# NEW
            is_text_mobject = obj["type"] in ["Text", "MathTex"]
            if not obj["visible"] or (obj["is_generic"] and not is_text_mobject):
                continue

            # 0.2: exclude degenerate bboxes (empty mobjects / mid-update
            # ValueTracker artifacts with coords like 25000) from all checks;
            # flag them in the saved JSON so downstream can skip them too
            bb = obj["bbox"]
            if (obj["width"] == 0 and obj["height"] == 0) or any(
                abs(c) > 30.0 for c in (bb[0][0], bb[0][1], bb[1][0], bb[1][1])
            ):
                obj["degenerate"] = True
                continue
            
            has_definite_anc = False
            curr_pid = obj.get("parent_id")
            while curr_pid:
                parent = obj_map.get(curr_pid)
                if parent and not parent["is_generic"]:
                    has_definite_anc = True
                    break
                curr_pid = parent.get("parent_id") if parent else None
            
            if not has_definite_anc or is_text_mobject:
                eval_objects.append(obj)

        eval_ids = {o["id"] for o in eval_objects}

        # NEW: Check for 'hidden_behind' directly here to avoid O(N^2) JSON bloat
        for a in eval_objects:
            for b in objects:
                if a["id"] == b["id"]:
                    continue
                if a["z_index"] < b["z_index"] and b.get("opacity", 1.0) > 0.6:
                    if self.is_contained(a, b):
                        issues.append({
                            "type": "hidden_behind",
                            "object": a["name"],
                            "behind": b["name"]
                        })

        is_promo = getattr(self, "theme", "") == "promo"
        limit_x = 3.9 if is_promo else 7.0
        limit_y = 7.0 if is_promo else 3.9
        
        n_eval = len(eval_objects)
        for i in range(n_eval):
            a = eval_objects[i]
            bbox = a["bbox"]
            min_ax, min_ay = bbox[0][0], bbox[0][1]
            max_ax, max_ay = bbox[1][0], bbox[1][1]

            # Detailed Off-screen Check
            off_screen_details = []
            if min_ax < -limit_x: 
                off_screen_details.append({"edge": "left", "extent": float(-limit_x - min_ax)})
            if max_ax > limit_x:  
                off_screen_details.append({"edge": "right", "extent": float(max_ax - limit_x)})
            if min_ay < -limit_y: 
                off_screen_details.append({"edge": "bottom", "extent": float(-limit_y - min_ay)})
            if max_ay > limit_y:  
                off_screen_details.append({"edge": "top", "extent": float(max_ay - limit_y)})

            if off_screen_details:
                issues.append({
                    "type": "off_screen",
                    "object": a["name"],
                    "details": off_screen_details
                })

            # Check for suboptimal scale
            if a["type"] == "ImageMobject" and (a["width"] < 0.5 or a["height"] < 0.5):
                issues.append({
                    "type": "suboptimal_scale",
                    "object": a["name"],
                    "details": {
                        "width": a["width"],
                        "height": a["height"]
                    }
                })


            for j in range(i + 1, n_eval):
                b = eval_objects[j]

                # Phase 1.4: fill-bar/track pairs get a dedicated containment
                # check and are exempt from the generic overlap and
                # redundant_overlap checks (their overlap is by design)
                bar_pair = self.classify_bar_pair(a, b)
                if bar_pair:
                    bar_fill_obj, bar_track_obj = bar_pair
                    exits = self.bar_exit_details(bar_fill_obj, bar_track_obj)
                    if exits:
                        issues.append({
                            "type": "bar_containment",
                            "objects": [bar_fill_obj["name"], bar_track_obj["name"]],
                            "details": {"fill": bar_fill_obj["name"],
                                        "track": bar_track_obj["name"],
                                        "exits": exits},
                        })
                    continue

                # Check for potential alignment issues
                if (a["type"] in ["Rectangle", "RoundedRectangle"] and
                    b["type"] in ["Rectangle", "RoundedRectangle"] and
                    self.overlaps(a, b) and
                    not self.is_contained(a, b) and
                    not self.is_contained(b, a) and
                    not has_children[a["id"]] and
                    not has_children[b["id"]]):

                    overlap_area = self.calculate_overlap_area(a, b)
                    area_a = a["width"] * a["height"]
                    area_b = b["width"] * b["height"]

                    overlap_percent_a = overlap_area / area_a if area_a > 0 else 0
                    overlap_percent_b = overlap_area / area_b if area_b > 0 else 0
                    
                    max_overlap_percent = max(overlap_percent_a, overlap_percent_b)

                    if max_overlap_percent > 0.85:
                        issues.append({
                            "type": "redundant_overlap",
                            "objects": [a["name"], b["name"]],
                            "details": {
                                "overlap_area": float(overlap_area),
                                "area_a": float(area_a),
                                "area_b": float(area_b),
                                "overlap_percent_a": float(overlap_percent_a),
                                "overlap_percent_b": float(overlap_percent_b),
                                "max_overlap_percent": float(max_overlap_percent)
                            }
                        })


                b = eval_objects[j]

                if self.overlaps(a, b):
                    # If one contains the other (including lenient Text check), skip overlap issue
                    if self.is_contained(a, b) or self.is_contained(b, a):
                        continue

                    # New logic: Capture overlaps between named children of a and b
                    named_children_of_a = self._get_named_visible_descendants(a["id"], objects, obj_map)
                    named_children_of_b = self._get_named_visible_descendants(b["id"], objects, obj_map)

                    child_overlaps_list = []
                    for child_a in named_children_of_a:
                        for child_b in named_children_of_b:
                            if self.overlaps(child_a, child_b):
                                # Calculate overlap extent for children
                                cax, cay = child_a["center"][:2]
                                cbx, cby = child_b["center"][:2]
                                cdx, cdy = cbx - cax, cby - cay
                                cdist = np.sqrt(cdx*cdx + cdy*cdy)

                                child_extent = 0.0
                                if cdist > 1e-6:
                                    cux, cuy = cdx / cdist, cdy / cdist
                                    cproj_a = 0.5 * (child_a["width"] * abs(cux) + child_a["height"] * abs(cuy))
                                    cproj_b = 0.5 * (child_b["width"] * abs(cux) + child_b["height"] * abs(cuy))
                                    child_extent = float(cproj_a + cproj_b - cdist)
                                else:
                                    child_extent = float(max(child_a["width"], child_a["height"]))

                                child_overlaps_list.append({
                                    "child_a_name": child_a["name"],
                                    "child_b_name": child_b["name"],
                                    "overlap_extent": child_extent
                                })

                    # If child overlaps are found, add them to the details of the main overlap issue
                    # Otherwise, the main overlap issue is reported without child details.
                    
                    # Existing code to calculate main overlap details

                    ax, ay = a["center"][:2]
                    bx, by = b["center"][:2]
                    dx, dy = bx - ax, by - ay
                    dist = np.sqrt(dx*dx + dy*dy)

                    # Determine orientation based on relative center positions
                    a_h = "right" if dx > 0 else "left"
                    a_v = "top" if dy > 0 else "bottom"
                    b_h = "left" if dx > 0 else "right"
                    b_v = "bottom" if dy > 0 else "top"

                    # Calculate overlap extent along the line connecting centers
                    if dist > 1e-6:
                        ux, uy = dx / dist, dy / dist
                        # Projected half-extents of the boxes onto the center-line
                        proj_a = 0.5 * (a["width"] * abs(ux) + a["height"] * abs(uy))
                        proj_b = 0.5 * (b["width"] * abs(ux) + b["height"] * abs(uy))
                        extent = float(proj_a + proj_b - dist)
                    else:
                        extent = float(max(a["width"], a["height"]))

                    issues.append({
                        "type": "overlap",
                        "objects": [a["name"], b["name"]],
                        "details": {
                            "a_orientation": f"{a_v}_{a_h}",
                            "b_orientation": f"{b_v}_{b_h}",
                            "overlap_extent": extent,
                            **({"child_overlaps": child_overlaps_list} if child_overlaps_list else {})
                        }
                    })

        # NEW TEXT OVERFLOW LOGIC: Check if a Text/MathTex object overflows a related shape object
        text_mobjects = [obj for obj in objects if obj["type"] in ["Text", "MathTex"] and obj["visible"]]
        shape_mobjects = [obj for obj in objects if obj["type"] in ["Rectangle", "RoundedRectangle"] and obj["visible"] and not obj["is_generic"]]

        for text_obj in text_mobjects:
            text_ancestor_chain = self._get_ancestor_chain(text_obj["id"], obj_map)
            
            for shape_obj in shape_mobjects:
                shape_ancestor_chain = self._get_ancestor_chain(shape_obj["id"], obj_map)

                # Check if they share a common ancestor (including direct parent-child relationships)
                # or if the text center lies inside the shape's bounding box (catches ungrouped text inside containers)
                text_center = text_obj["center"]
                center_inside_shape = (
                    shape_obj["bbox"][0][0] <= text_center[0] <= shape_obj["bbox"][1][0] and
                    shape_obj["bbox"][0][1] <= text_center[1] <= shape_obj["bbox"][1][1]
                )
                if (not set(text_ancestor_chain).isdisjoint(set(shape_ancestor_chain)) or 
                    text_obj["parent_id"] == shape_obj["id"] or 
                    center_inside_shape):

                    # If text_obj is not strictly contained within shape_obj, it's an overflow
                    if not self.is_contained(text_obj, shape_obj, strict=True):
                        overflow_details = self._get_overflow_details(text_obj, shape_obj)
                        if overflow_details: # Only add if there's actual overflow
                            issues.append({
                                "type": "text_overflow",
                                "parent": shape_obj["name"], # The shape is the 'container' for this overflow
                                "text": text_obj["name"],
                                "details": overflow_details
                            })

        return issues

    def calculate_overlap_area(self, a, b):
        """Calculates the area of overlap between two objects' bounding boxes."""
        # Get bounding box coordinates
        a_min_x, a_min_y = a["bbox"][0][0], a["bbox"][0][1]
        a_max_x, a_max_y = a["bbox"][1][0], a["bbox"][1][1]

        b_min_x, b_min_y = b["bbox"][0][0], b["bbox"][0][1]
        b_max_x, b_max_y = b["bbox"][1][0], b["bbox"][1][1]

        # Calculate intersection coordinates
        inter_min_x = max(a_min_x, b_min_x)
        inter_min_y = max(a_min_y, b_min_y)
        inter_max_x = min(a_max_x, b_max_x)
        inter_max_y = min(a_max_y, b_max_y)

        # Calculate intersection area
        inter_w = max(0, inter_max_x - inter_min_x)
        inter_h = max(0, inter_max_y - inter_min_y)
        
        return inter_w * inter_h

    def _get_ancestor_chain(self, obj_id, obj_map):
        """
        Returns a list of ancestor IDs for a given object, from immediate parent up to the root.
        """
        chain = []
        current_id = obj_id
        while True:
            obj = obj_map.get(current_id)
            if not obj:
                break
            parent_id = obj.get("parent_id")
            if parent_id:
                chain.append(parent_id)
                current_id = parent_id
            else:
                break
        return chain

    def _get_named_visible_descendants(self, root_obj_id, all_objects_list, obj_map_dict):
        """
        Recursively gets all non-generic, visible descendants of an object.
        Excludes the root object itself.
        """
        descendants = []
        queue = [root_obj_id]
        visited_desc = set()

        while queue:
            current_id = queue.pop(0)
            if current_id in visited_desc:
                continue
            visited_desc.add(current_id)

            current_obj = obj_map_dict.get(current_id)
            if not current_obj:
                continue

            if current_obj["id"] != root_obj_id and not current_obj["is_generic"] and current_obj["visible"]:
                descendants.append(current_obj)

            for obj_candidate in all_objects_list:
                if obj_candidate.get("parent_id") == current_id:
                    queue.append(obj_candidate["id"])
        return descendants

    def _get_overflow_details(self, text_obj, shape_obj):
        """
        Calculates and returns details about how text_obj overflows shape_obj.
        """
        min_ax, min_ay = text_obj["bbox"][0][0], text_obj["bbox"][0][1]
        max_ax, max_ay = text_obj["bbox"][1][0], text_obj["bbox"][1][1]

        p_bbox = shape_obj["bbox"]
        p_center = shape_obj["center"]
        overflow_details = []
        
        # Check each edge for overflow
        if min_ax < p_bbox[0][0]:
            overflow_details.append({
                "edge": "left",
                "parent_relative_coord": [float(p_bbox[0][0] - p_center[0]), 0.0],
                "extent": float(p_bbox[0][0] - min_ax)
            })
        if max_ax > p_bbox[1][0]:
            overflow_details.append({
                "edge": "right",
                "parent_relative_coord": [float(p_bbox[1][0] - p_center[0]), 0.0],
                "extent": float(max_ax - p_bbox[1][0])
            })
        if min_ay < p_bbox[0][1]:
            overflow_details.append({
                "edge": "bottom",
                "parent_relative_coord": [0.0, float(p_bbox[0][1] - p_center[1])],
                "extent": float(p_bbox[0][1] - min_ay)
            })
        if max_ay > p_bbox[1][1]:
            overflow_details.append({
                "edge": "top",
                "parent_relative_coord": [0.0, float(p_bbox[1][1] - p_center[1])],
                "extent": float(max_ay - p_bbox[1][1])
            })
        return overflow_details

    def is_off_screen(self, obj):
        """Checks if any part of the object's bounding box is outside the screen limits."""
        bbox = obj["bbox"]
        min_x, min_y = bbox[0][0], bbox[0][1]
        max_x, max_y = bbox[1][0], bbox[1][1]

        is_promo = getattr(self, "theme", "") == "promo"
        limit_x = 3.9 if is_promo else 7.0
        limit_y = 7.0 if is_promo else 3.9

        return min_x < -limit_x or max_x > limit_x or min_y < -limit_y or max_y > limit_y

    def is_contained(self, inner, outer, strict=False):
        """Returns True if inner is entirely within outer, or strictly within outer."""
        def _is_text_or_title(obj):
            if obj.get("type") in ["Text", "MathTex"]:
                return True
            n = obj.get("name", "").lower()
            return any(k in n for k in ["title", "header", "kicker", "label", "caption", "tag"])

        # If both inner and outer are text/title objects, they are colliding, not contained
        if _is_text_or_title(inner) and _is_text_or_title(outer):
            return False
        
        i_bbox = inner["bbox"]
        o_bbox = outer["bbox"]

        # Strict geometric containment
        is_strictly_inside = (
            i_bbox[0][0] >= o_bbox[0][0] and
            i_bbox[0][1] >= o_bbox[0][1] and
            i_bbox[1][0] <= o_bbox[1][0] and
            i_bbox[1][1] <= o_bbox[1][1]
        )
        if strict or is_strictly_inside:
            return is_strictly_inside

        # Lenient containment for Text/MathTex (for general background overlap suppression only)
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

    # --------------------------------------------------
    # OVERLAP CHECK
    # --------------------------------------------------

    def overlaps(
        self,
        a,
        b
    ):

        ax, ay = a["center"][:2]
        bx, by = b["center"][:2]

        return (
            abs(ax - bx)
            <
            (a["width"] + b["width"]) / 2
        ) and (
            abs(ay - by)
            <
            (a["height"] + b["height"]) / 2
        )