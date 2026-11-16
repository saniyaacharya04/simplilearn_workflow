"""
frame_context.py

Deterministic text transformations that replace raw-JSON payloads in the VLM
prompt (Phase 2 refinement): instead of shipping the object dicts and the
per-cell cellmap and letting the model do the geometry, we precompute:

  1. describe_objects_on_grid(): one plain-text line per object stating which
     grid cells its bounding box overlaps and by how much, e.g.
       - note_bl [Text] 1.20x0.45u at (-3.10, 1.42): spans B2:C3;
         area distribution B2 38%, C2 30%, B3 18%, C3 14%
  2. grid_geometry_summary(): three lines describing the grid instead of the
     full 70+ entry cellmap.
  3. load_scene_code(): line-numbered Manim source for code-aware analysis.
"""

import re


_CELL_RE = re.compile(r"^([A-Z]+)(\d+)$")


def _col_index(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _parse_cell(cell_id):
    m = _CELL_RE.match(cell_id)
    if not m:
        return None
    return _col_index(m.group(1)), int(m.group(2)) - 1  # (col, row), 0-based


def grid_geometry_summary(cell_map):
    """3-line textual replacement for shipping the whole cellmap."""
    if not cell_map:
        return ["(no grid available)"]
    cols, rows = set(), set()
    for cell_id in cell_map:
        parsed = _parse_cell(cell_id)
        if parsed:
            cols.add(parsed[0])
            rows.add(parsed[1])
    n_cols, n_rows = max(cols) + 1, max(rows) + 1
    a1 = cell_map.get("A1")
    x0, y_bot, x1, y_top = a1["manim_bbox"]
    cell_w, cell_h = x1 - x0, y_top - y_bot
    last_col_letter = [k for k in cell_map if _parse_cell(k) == (n_cols - 1, n_rows - 1)]
    return [
        f"Grid: {n_cols} columns (A..) x {n_rows} rows (1..), "
        f"cell size {cell_w:.2f} x {cell_h:.2f} Manim units.",
        f"Cell A1's top-left corner is at Manim ({x0:.2f}, {y_top:.2f}); columns "
        f"advance rightward (+x), rows advance downward (-y).",
        "Cell centers: center(COL i, ROW j) = A1 top-left + ((i+0.5)*cell_w, -(j+0.5)*cell_h).",
    ]


def _cell_coverage(bbox, cell_map, min_pct=2.0):
    """[(cell_id, pct_of_object_area)] sorted desc, cells under min_pct dropped."""
    (ox0, oy0, *_), (ox1, oy1, *_) = bbox
    # zero-dimension objects (Lines) still deserve a location: inflate slightly
    if ox1 - ox0 < 0.02:
        ox0, ox1 = ox0 - 0.01, ox1 + 0.01
    if oy1 - oy0 < 0.02:
        oy0, oy1 = oy0 - 0.01, oy1 + 0.01
    area = (ox1 - ox0) * (oy1 - oy0)
    if area <= 0:
        return []
    out = []
    for cell_id, info in cell_map.items():
        cx0, cy0, cx1, cy1 = info["manim_bbox"]
        iw = min(ox1, cx1) - max(ox0, cx0)
        ih = min(oy1, cy1) - max(oy0, cy0)
        if iw <= 0 or ih <= 0:
            continue
        pct = 100.0 * (iw * ih) / area
        if pct >= min_pct:
            out.append((cell_id, pct))
    out.sort(key=lambda t: -t[1])
    return out


def _span(cells):
    """'B2:D3' style span over the covered cells."""
    parsed = [p for p in (_parse_cell(c) for c, _ in cells) if p]
    if not parsed:
        return "?"
    cmin, cmax = min(p[0] for p in parsed), max(p[0] for p in parsed)
    rmin, rmax = min(p[1] for p in parsed), max(p[1] for p in parsed)

    def col_letter(n):
        label = ""
        n += 1
        while n > 0:
            n, rem = divmod(n - 1, 26)
            label = chr(65 + rem) + label
        return label

    tl = f"{col_letter(cmin)}{rmin + 1}"
    br = f"{col_letter(cmax)}{rmax + 1}"
    return tl if tl == br else f"{tl}:{br}"


def describe_objects_on_grid(objects, cell_map, priority_names=(),
                             max_objects=40, max_cells_listed=6):
    """
    One plain-text line per visible, non-degenerate object, priority names
    first (issue-involved objects), remainder by area descending.
    """
    priority = {n: i for i, n in enumerate(priority_names)}
    visible = []
    for o in objects:
        if not o.get("visible") or o.get("degenerate") or not o.get("name"):
            continue
        if o.get("is_generic") and o.get("name") not in priority:
            continue
        visible.append(o)

    def sort_key(o):
        name = o["name"]
        if name in priority:
            return (0, priority[name], 0.0)
        return (1, 0, -(o.get("width", 0.0) * o.get("height", 0.0)))

    visible.sort(key=sort_key)
    seen = set()
    lines = []
    for o in visible:
        name = o["name"]
        if name in seen:
            continue
        seen.add(name)
        if len(lines) >= max_objects:
            lines.append(f"  (... {len(visible) - max_objects} more objects omitted)")
            break

        cov = _cell_coverage(o["bbox"], cell_map)
        cx = (o["bbox"][0][0] + o["bbox"][1][0]) / 2
        cy = (o["bbox"][0][1] + o["bbox"][1][1]) / 2
        left_e = o["bbox"][0][0]
        right_e = o["bbox"][1][0]
        bottom_e = o["bbox"][0][1]
        top_e = o["bbox"][1][1]

        edge_flags = []
        if right_e > 6.4:
            overflow = right_e - 6.1
            edge_flags.append(f"⚠️ RIGHT OVERFLOW (right={right_e:.2f} > 6.4, shift left >= {overflow:.2f}u or clamp width)")
        elif right_e > 6.0:
            edge_flags.append(f"ℹ️ near right boundary ({right_e:.2f})")

        if left_e < -6.4:
            overflow = -6.1 - left_e
            edge_flags.append(f"⚠️ LEFT OVERFLOW (left={left_e:.2f} < -6.4, shift right >= {overflow:.2f}u)")
        elif left_e < -6.0:
            edge_flags.append(f"ℹ️ near left boundary ({left_e:.2f})")

        if top_e > 3.4:
            edge_flags.append(f"⚠️ TOP SAFE-ZONE BREACH (top={top_e:.2f} > 3.4)")
        if bottom_e < -3.5:
            edge_flags.append(f"⚠️ BOTTOM SAFE-ZONE BREACH (bottom={bottom_e:.2f} < -3.5)")

        edge_str = f" | {'; '.join(edge_flags)}" if edge_flags else ""

        listed = cov[:max_cells_listed]
        dist = ", ".join(f"{c} {p:.0f}%" for c, p in listed)
        if len(cov) > max_cells_listed:
            dist += ", ..."
        colors = []
        if o.get("fill_color"):
            colors.append(f"fill {o['fill_color']}")
        if o.get("stroke_color"):
            colors.append(f"stroke {o['stroke_color']}")
        color_txt = f"; {', '.join(colors)}" if colors else ""
        flag = " [ISSUE]" if name in priority else ""
        lines.append(
            f"  - {name} [{o.get('type', '?')}] {o.get('width', 0):.2f}x"
            f"{o.get('height', 0):.2f}u at ({cx:.2f}, {cy:.2f}) [x:[{left_e:.2f},{right_e:.2f}], y:[{bottom_e:.2f},{top_e:.2f}]]: "
            f"spans {_span(cov)}; area distribution {dist or 'sub-cell'}{color_txt}{flag}{edge_str}"
        )
    return lines


def load_scene_code(path):
    """Line-numbered scene source for the CODE-AWARE ANALYSIS prompt block."""
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    return "\n".join(f"{i + 1:4d} | {line}"
                     for i, line in enumerate(src.splitlines()))


_SECTION_MARK_RE = re.compile(r"^\s*##\s*Section\s+(\d+)\b", re.IGNORECASE)


def _is_fence(line):
    s = line.strip()
    return bool(s) and set(s) <= set("#=-")


def slice_scene_code_for_section(path, section_id=None):
    """
    Line-numbered slice of a generated scene file for the CODE-AWARE prompt
    block: the full preamble (imports, helper functions, asset classes --
    everything before the first '## Section N' marker, where shared root
    causes live) plus ONLY the requested section's block. Original line
    numbers are preserved so the VLM can cite them.

    section_id None -> preamble only (for the consolidation pass).
    No markers found, or section missing -> full numbered file (safe fallback).
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    def num(segment, start_idx):
        return "\n".join(f"{start_idx + j + 1:4d} | {l}"
                         for j, l in enumerate(segment))

    marks = [(i, m.group(1)) for i, l in enumerate(lines)
             for m in [_SECTION_MARK_RE.match(l)] if m]
    if not marks:
        return num(lines, 0)

    first = marks[0][0]
    pre_end = first - 1 if first > 0 and _is_fence(lines[first - 1]) else first
    preamble = num(lines[:pre_end], 0)
    if section_id is None:
        return preamble

    sid = str(section_id)
    for k, (i, s) in enumerate(marks):
        if s != sid:
            continue
        start = i - 1 if i > 0 and _is_fence(lines[i - 1]) else i
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        if end > start and _is_fence(lines[end - 1]):
            end -= 1  # leave the next section's opening fence out
        block = num(lines[start:end], start)
        return (preamble
                + "\n     | ... (other sections omitted) ...\n"
                + block)

    return num(lines, 0)