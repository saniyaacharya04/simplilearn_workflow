"""
grid_overlay.py

Post-processing step (Phase 3 prep): draws a spreadsheet-style reference grid
(columns A, B, C... / rows 1, 2, 3...) on top of an already-rendered
snapshot PNG, so every cell has a unique ID like "D3". This lets the VLM refer
to *where* in the frame an issue is ("the label overflows around C2") without
needing pixel coordinates, and without needing Manim to re-render anything.

Runs only on the small subset of frames Phase 2 selects for VLM review --
not on every snapshot -- since it's pure post-processing on the PNG.
"""

from PIL import Image, ImageDraw, ImageFont


def _col_label(n):
    """0 -> 'A', 25 -> 'Z', 26 -> 'AA', ... (spreadsheet-style column naming)."""
    label = ""
    n += 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        label = chr(65 + rem) + label
    return label


def _load_font(size):
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def add_grid_overlay(
    image_path,
    output_path=None,
    target_cols=12,
    mode="edges",
    line_rgba=(0, 0, 0, 70),
    label_rgba=(255, 60, 60, 220),
    label_bg_rgba=(255, 255, 255, 160),
    frame_height_units=8.0,
    frame_width_units=None,
    camera_center=(0.0, 0.0)  # <-- ADD THIS
):
    """
    Draws a labeled grid on `image_path` and saves it to `output_path`
    (defaults to `<name>_grid.png` next to the original).

    mode="edges" (default): column letters along the TOP and BOTTOM edges,
        row numbers along the LEFT and RIGHT edges. Interior stays clean.
        Any point is at most half a cell-width from a header in each axis,
        traceable along a visible gridline -- no counting required.
    mode="full": every cell gets its own "A1"-style label in the corner
        (original behavior). More direct, but clutters busy scenes.

    Cell size is computed from `target_cols` so cells stay square regardless
    of the image's aspect ratio -- a portrait-oriented (promo) render just
    ends up with more rows, a wide one with more columns, both using the
    same physical cell size.

    frame_width_units / frame_height_units: the Manim coordinate span the
    image represents (default 14.0 x 7.8, i.e. the standard non-promo frame,
    -7..7 by -3.9..3.9). Pass 7.8 x 14.0 for the promo/vertical theme. Used
    to build a cell -> approximate Manim-coordinate mapping.

    Returns (output_path, cell_map) where cell_map is a dict like:
        {"A1": {"px_bbox": [x0,y0,x1,y1], "manim_bbox": [x0,y0,x1,y1]}, ...}
    """
    img = Image.open(image_path).convert("RGBA")
    w, h = img.size

    if frame_width_units is None:
        frame_width_units = frame_height_units * (w / h)

    cell_px = w / target_cols
    n_cols = target_cols
    n_rows = max(1, round(h / cell_px))
    # recompute exact cell size so rows/cols tile the image evenly
    cell_w = w / n_cols
    cell_h = h / n_rows

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(10, int(min(cell_w, cell_h) * 0.22))
    font = _load_font(font_size)

    # grid lines
    for c in range(n_cols + 1):
        x = round(c * cell_w)
        draw.line([(x, 0), (x, h)], fill=line_rgba, width=1)
    for r in range(n_rows + 1):
        y = round(r * cell_h)
        draw.line([(0, y), (w, y)], fill=line_rgba, width=1)

    def _label(text, pos):
        bbox = draw.textbbox(pos, text, font=font)
        draw.rectangle(
            [bbox[0] - 1, bbox[1] - 1, bbox[2] + 1, bbox[3] + 1],
            fill=label_bg_rgba,
        )
        draw.text(pos, text, fill=label_rgba, font=font)

    if mode == "edges":
        for c in range(n_cols):
            col_txt = _col_label(c)
            x_center = c * cell_w + 2
            _label(col_txt, (x_center, 1))                      # top edge
            _label(col_txt, (x_center, h - font_size - 3))       # bottom edge
        for r in range(n_rows):
            row_txt = str(r + 1)
            y_center = r * cell_h + 1
            _label(row_txt, (2, y_center))                       # left edge
            _label(row_txt, (w - font_size * len(row_txt) - 3, y_center))  # right edge
    elif mode != "full":
        raise ValueError("mode must be 'edges' or 'full'")

    cell_map = {}
    for r in range(n_rows):
        for c in range(n_cols):
            x0, y0 = c * cell_w, r * cell_h
            x1, y1 = x0 + cell_w, y0 + cell_h
            cell_id = f"{_col_label(c)}{r + 1}"

            if mode == "full":
                _label(cell_id, (x0 + 2, y0 + 1))

            # pixel bbox -> Manim coordinate bbox
            # image (0,0) is top-left; Manim (0,0) is frame center, y-up
            '''
            mx0 = (x0 / w) * frame_width_units - frame_width_units / 2
            mx1 = (x1 / w) * frame_width_units - frame_width_units / 2
            my0 = frame_height_units / 2 - (y1 / h) * frame_height_units
            my1 = frame_height_units / 2 - (y0 / h) * frame_height_units
            '''
            cx, cy = camera_center[0], camera_center[1]
            mx0 = (x0 / w) * frame_width_units + (cx - frame_width_units / 2)
            mx1 = (x1 / w) * frame_width_units + (cx - frame_width_units / 2)
            my0 = (cy + frame_height_units / 2) - (y1 / h) * frame_height_units
            my1 = (cy + frame_height_units / 2) - (y0 / h) * frame_height_units

            cell_map[cell_id] = {
                "px_bbox": [x0, y0, x1, y1],
                "manim_bbox": [round(mx0, 3), round(my0, 3), round(mx1, 3), round(my1, 3)],
            }

    composited = Image.alpha_composite(img, overlay).convert("RGB")

    if output_path is None:
        stem = image_path.rsplit(".", 1)[0]
        output_path = f"{stem}_grid.png"

    composited.save(output_path)
    return output_path, cell_map


if __name__ == "__main__":
    import sys
    import json

    path = sys.argv[1]
    out_path, cell_map = add_grid_overlay(path)
    print(f"Saved: {out_path}")
    print(json.dumps(cell_map, indent=2,ensure_ascii=False)[:500], "...")

# --------------------------------------------------------------------------
# Phase 2.1: Set-of-Mark annotation
# --------------------------------------------------------------------------

SOM_COLORS = [
    (255, 70, 70), (60, 150, 255), (60, 190, 90), (255, 165, 30),
    (195, 100, 255), (0, 190, 190), (255, 100, 165), (150, 150, 40),
]


def add_som_annotations(image_path, output_path, objects, target_names,
                        frame_height_units=8.0, frame_width_units=None,
                        camera_center=(0.0, 0.0), max_markers=10):
    """
    Set-of-Mark v2: draws each target object's bbox outline plus a numbered
    badge so the VLM can identify issue-involved objects with certainty.
    """
    img = Image.open(image_path).convert("RGBA")
    w, h = img.size
    if frame_width_units is None:
        frame_width_units = frame_height_units * (w / h)

    lookup = {}
    for o in objects:
        if o.get("visible") and not o.get("degenerate") and o.get("name"):
            lookup.setdefault(o["name"], o)

    ordered = [n for n in dict.fromkeys(target_names) if n in lookup][:max_markers]

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _load_font(max(13, int(h * 0.030)))

    # Updated to support dynamic camera centers
    cx, cy = camera_center[0], camera_center[1]
    def to_px(mx, my):
        return (((mx - (cx - frame_width_units / 2)) / frame_width_units) * w,
                ((cy + frame_height_units / 2 - my) / frame_height_units) * h)

    def rects_overlap(a, b, pad=2):
        return not (a[2] + pad < b[0] or b[2] + pad < a[0]
                    or a[3] + pad < b[1] or b[3] + pad < a[1])

    placed_badges = []  # badge px rects, for collision avoidance
    legend = {}

    for idx, name in enumerate(ordered, start=1):
        o = lookup[name]
        (x0, y0, _), (x1, y1, _) = o["bbox"]
        px0, py1 = to_px(x0, y0)   # Manim y-up -> image y-down
        px1, py0 = to_px(x1, y1)
        color = SOM_COLORS[(idx - 1) % len(SOM_COLORS)]

        tiny = (px1 - px0 < 14) and (py1 - py0 < 14)
        ocx, ocy = (px0 + px1) / 2, (py0 + py1) / 2
        if tiny:
            r = 8
            # --- SURGICAL FIX: Cast coordinates to int ---
            draw.ellipse([int(ocx - r), int(ocy - r), int(ocx + r), int(ocy + r)],
                         outline=color + (255,), width=3)
            anchor = (int(ocx), int(ocy - r))
        else:
            if px1 - px0 < 4:
                px0, px1 = px0 - 2, px1 + 2
            if py1 - py0 < 4:
                py0, py1 = py0 - 2, py1 + 2
            # --- SURGICAL FIX: Cast coordinates to int ---
            draw.rectangle([int(px0), int(py0), int(px1), int(py1)], outline=color + (255,), width=3)
            anchor = (int(px0), int(py0))

        badge = str(idx)
        tb = draw.textbbox((0, 0), badge, font=font)
        bw, bh = tb[2] - tb[0] + 8, tb[3] - tb[1] + 8

        # candidate badge positions around the anchor, nearest first
        ax, ay = anchor
        cands = [(ax, ay - bh - 6), (ax - bw - 6, ay - bh - 6),
                 (ax + 8, ay - bh - 6), (ax - bw - 8, ay),
                 (px1 + 6 if not tiny else ocx + 12, ay),
                 (ax, py1 + 6 if not tiny else ocy + 12),
                 (ax - bw - 8, py1 + 6 if not tiny else ocy + 12)]
        chosen = None
        for bx, by in cands:
            bx = min(max(2, bx), w - bw - 2)
            by = min(max(2, by), h - bh - 2)
            # Ensure chosen boundaries are clean integers
            rect = (int(bx), int(by), int(bx + bw), int(by + bh))
            if not any(rects_overlap(rect, pb) for pb in placed_badges):
                chosen = rect
                break
        if chosen is None:  # everything crowded: slide down-right until free
            bx, by = min(max(2, ax), w - bw - 2), min(max(2, ay), h - bh - 2)
            rect = (int(bx), int(by), int(bx + bw), int(by + bh))
            while any(rects_overlap(rect, pb) for pb in placed_badges) and rect[3] < h - 2:
                rect = (rect[0], rect[1] + bh + 4, rect[2], rect[3] + bh + 4)
            chosen = rect
        placed_badges.append(chosen)

        # leader line if the badge ended up away from its object
        bcx, bcy = (chosen[0] + chosen[2]) / 2, (chosen[1] + chosen[3]) / 2
        if abs(bcx - ax) > bw or abs(bcy - ay) > bh:
            # --- SURGICAL FIX: Cast line draw arguments to INT ---
            draw.line([int(bcx), int(bcy), int(ax), int(ay)], fill=color + (255,), width=2)

        # --- SURGICAL FIX: Cast rectangle and text arguments to INT ---
        draw.rectangle([int(x) for x in chosen], fill=color + (235,))
        draw.text((int(chosen[0] + 4), int(chosen[1] + 3)), badge,
                  fill=(255, 255, 255, 255), font=font)
        legend[badge] = name

    Image.alpha_composite(img, overlay).convert("RGB").save(output_path)
    return legend