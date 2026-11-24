"""
template4_process_flow.py — Simplilearn OSL 3.0 Process Showcase & Visual Flow Template
========================================================================================
Reusable Manim programmatic template for Multi-Stage Process Flows, Candidate Path
Evaluation, and State-Transition Workflows (Derived from Pilot Standard 0:40 - 1:20).

Adheres strictly to Simplilearn Learning Design & OSL 3.0 Video Guidelines:
- Layout: Compatible with Layout 70 (Right Canvas x >= -1.2) and Layout 20 (Full Canvas below y <= 1.8)
- Visual Style: Dynamic kinetic flow with Start -> Candidate Paths -> Selected Outcome
- Low Text Mandate: Concise 1-3 word node titles, status pills, and numeric metrics
- Animation Logic: Signal evaluation pulses, progressive step reveals, zero camera moves
- Word-Level Sync: Spoken emphasis hooks and dynamic path state transformations

Usage:
------
from template4_process_flow import play_process_flow, create_process_flow_mobject

class MyScene(Scene):
    def construct(self):
        play_process_flow(
            self,
            kicker="AI AGENT PIPELINE",
            title="Candidate Path Evaluation",
            origin_label="Data Ingress",
            paths=[
                {"name": "Path A: Standard Batch", "status": "Ruled Out", "reason": "High Latency", "optimal": False},
                {"name": "Path B: Streaming Edge", "status": "Optimal", "reason": "Sub-millisecond", "optimal": True},
            ],
            target_label="Action Output",
            step_durations=[2.5, 3.0, 3.5, 2.0],
        )

Command-line test render:
-------------------------
python -m manim -pql template4_process_flow.py ProcessFlowScene
"""

from __future__ import annotations
import os
import textwrap
from typing import Optional, Union, List, Dict, Any
import numpy as np
from manim import *
import manimpango

# =========================================================
# BRAND COLOR TOKENS
# =========================================================
COLOR_NAVY       = "#0A2540"
COLOR_DARK_NAVY  = "#0F172A"
COLOR_BLUE       = "#007ACC"
COLOR_COBALT     = "#1D4ED8"
COLOR_CYAN       = "#0284C7"
COLOR_TEAL       = "#10B981"
COLOR_WHITE      = "#FFFFFF"
COLOR_CARD_BG    = "#F8FAFC"
COLOR_BOX_BG     = "#F1F5F9"
COLOR_BORDER     = "#CBD5E1"
COLOR_GRAY       = "#64748B"
COLOR_DARK       = "#1E293B"


def get_simplilearn_font(preferred: str = "Open Sans") -> str:
    """Returns preferred font if installed in OS font registry, else clean system fallback."""
    try:
        available = manimpango.list_fonts()
        if preferred in available:
            return preferred
        for fallback in ["Segoe UI", "Arial", "Inter", "Calibri", "Sans"]:
            if fallback in available:
                return fallback
    except Exception:
        pass
    return "Sans"


def CrispText(text, size=24, font="Sans-Serif", **kwargs):
    """
    High-fidelity typography renderer providing consistent letter spacing,
    crisp glyph outlines, and automatic word wrapping via 4x supersampling.
    """
    if "font_size" in kwargs:
        size = kwargs.pop("font_size")
    if size < 12:
        size = 12
    align = kwargs.pop("align", "center")
    kwargs.pop("alignment", None)
    slant_val = kwargs.pop("slant", NORMAL)
    weight_val = kwargs.pop("weight", NORMAL)
    if isinstance(weight_val, str):
        weight_val = weight_val.upper()
        if weight_val == "REGULAR":
            weight_val = "NORMAL"
    color_val = kwargs.pop("color", COLOR_DARK)

    raw_str = str(text)
    split_lines = raw_str.split("\n") if "\n" in raw_str else [raw_str]
    if len(split_lines) > 1:
        line_mobs = [
            Text(l, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **kwargs)
            for l in split_lines
        ]
        aligned_edge = ORIGIN if align == "center" else (LEFT if align == "left" else RIGHT)
        mob = VGroup(*line_mobs).arrange(DOWN, buff=0.18, aligned_edge=aligned_edge).scale(0.25)
    else:
        mob = Text(raw_str, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **kwargs).scale(0.25)
    return mob


def create_process_flow_mobject(
    kicker: str = "EXECUTION PIPELINE • STEP 01",
    title: str = "Sensory Ingestion to Action Flow",
    origin_label: str = "Perception Ingress",
    paths: Optional[List[Dict[str, Any]]] = None,
    target_label: str = "Action Execution",
    center_pos: np.ndarray = np.array([0.0, -0.35, 0.0]),
    width_span: float = 9.6,
    font_family: str = "Open Sans",
) -> Dict[str, Any]:
    """
    Constructs the procedural visual process flow framework.
    """
    font = get_simplilearn_font(font_family)

    if paths is None:
        paths = [
            {"name": "Candidate Path A", "sub": "Batch inference loop", "status": "✕ Ruled out: Latency", "optimal": False, "color": COLOR_GRAY},
            {"name": "Candidate Path B", "sub": "Real-time streaming agent", "status": "★ Selected optimal", "optimal": True, "color": COLOR_COBALT},
        ]

    # 1. Header Group
    kicker_mob = CrispText(kicker.upper(), size=12.0, color=COLOR_GRAY, weight=BOLD, font=font, align="left")
    title_mob = CrispText(title, size=21.0, color=COLOR_NAVY, weight=BOLD, font=font, align="left").next_to(kicker_mob, DOWN, aligned_edge=LEFT, buff=0.10)
    header_grp = VGroup(kicker_mob, title_mob).move_to(np.array([-5.8, 3.5, 0]), aligned_edge=LEFT)

    # 2. Origin Node (Left)
    origin_x = center_pos[0] - width_span / 2.0 + 1.2
    origin_y = center_pos[1]
    origin_box = RoundedRectangle(
        corner_radius=0.14, width=2.40, height=0.90,
        fill_color=COLOR_WHITE, fill_opacity=1.0,
        stroke_color=COLOR_BLUE, stroke_width=2.0
    ).move_to(np.array([origin_x, origin_y, 0]))
    
    disc_origin = Circle(radius=0.22, fill_color=COLOR_BLUE, fill_opacity=1.0, stroke_color=COLOR_WHITE, stroke_width=1.5).move_to(origin_box.get_left() + RIGHT * 0.38)
    disc_icon = CrispText("01", size=11.0, color=COLOR_WHITE, weight=BOLD, font=font).move_to(disc_origin)
    origin_txt = CrispText(origin_label, size=13.0, color=COLOR_DARK, weight=BOLD, font=font, align="left").next_to(disc_origin, RIGHT, buff=0.20)
    origin_sub = CrispText("Raw Signal Ingress", size=9.5, color=COLOR_GRAY, weight=NORMAL, font=font, align="left").next_to(origin_txt, DOWN, aligned_edge=LEFT, buff=0.06)
    origin_node = VGroup(origin_box, disc_origin, disc_icon, origin_txt, origin_sub)

    # 3. Target Node (Right)
    target_x = center_pos[0] + width_span / 2.0 - 1.2
    target_box = RoundedRectangle(
        corner_radius=0.14, width=2.40, height=0.90,
        fill_color=COLOR_WHITE, fill_opacity=1.0,
        stroke_color=COLOR_TEAL, stroke_width=2.0
    ).move_to(np.array([target_x, origin_y, 0]))

    disc_target = Circle(radius=0.22, fill_color=COLOR_TEAL, fill_opacity=1.0, stroke_color=COLOR_WHITE, stroke_width=1.5).move_to(target_box.get_left() + RIGHT * 0.38)
    target_num = CrispText("03", size=11.0, color=COLOR_WHITE, weight=BOLD, font=font).move_to(disc_target)
    target_txt = CrispText(target_label, size=13.0, color=COLOR_DARK, weight=BOLD, font=font, align="left").next_to(disc_target, RIGHT, buff=0.20)
    target_sub = CrispText("Verified Actuation", size=9.5, color=COLOR_GRAY, weight=NORMAL, font=font, align="left").next_to(target_txt, DOWN, aligned_edge=LEFT, buff=0.06)
    target_node = VGroup(target_box, disc_target, target_num, target_txt, target_sub)

    # 4. Intermediate Candidate Path Nodes (Center)
    path_groups = []
    in_conduits = []
    out_conduits = []
    mid_x = center_pos[0]
    n_paths = len(paths)
    y_offsets = [0.85, -0.85] if n_paths == 2 else np.linspace(1.2, -1.2, n_paths)

    for i, p_info in enumerate(paths):
        py = origin_y + y_offsets[i]
        is_opt = p_info.get("optimal", False)
        stroke_col = COLOR_COBALT if is_opt else COLOR_BORDER
        fill_col = COLOR_WHITE if is_opt else COLOR_BOX_BG

        c_box = RoundedRectangle(
            corner_radius=0.12, width=3.20, height=0.95,
            fill_color=fill_col, fill_opacity=1.0,
            stroke_color=stroke_col, stroke_width=2.2 if is_opt else 1.4
        ).move_to(np.array([mid_x, py, 0]))

        p_name = CrispText(p_info.get("name", f"Option {i+1}"), size=12.0, color=COLOR_DARK, weight=BOLD, font=font, align="left")
        p_name.move_to(c_box.get_top() + DOWN * 0.28)

        status_str = p_info.get("status", "Evaluating...")
        status_col = COLOR_COBALT if is_opt else COLOR_GRAY
        p_status = CrispText(status_str, size=10.0, color=status_col, weight=BOLD, font=font).next_to(p_name, DOWN, buff=0.10)

        path_grp = VGroup(c_box, p_name, p_status)
        path_groups.append(path_grp)

        # Ingress conduit from origin to candidate
        in_line = Line(origin_box.get_right(), c_box.get_left(), color=COLOR_BLUE if is_opt else "#94A3B8", stroke_width=2.0)
        in_conduits.append(in_line)

        # Egress conduit from candidate to target
        if is_opt:
            out_line = Line(c_box.get_right(), target_box.get_left(), color=COLOR_COBALT, stroke_width=2.5)
        else:
            out_line = DashedLine(c_box.get_right(), target_box.get_left(), color="#CBD5E1", stroke_width=1.5, dash_length=0.08)
        out_conduits.append(out_line)

    return {
        "header_grp": header_grp,
        "origin_node": origin_node,
        "target_node": target_node,
        "path_groups": path_groups,
        "in_conduits": in_conduits,
        "out_conduits": out_conduits,
    }


def play_process_flow(
    scene: Scene,
    kicker: str = "EXECUTION PIPELINE • STEP 01",
    title: str = "Sensory Ingestion to Action Flow",
    origin_label: str = "Perception Ingress",
    paths: Optional[List[Dict[str, Any]]] = None,
    target_label: str = "Action Execution",
    center_pos: np.ndarray = np.array([0.0, -0.35, 0.0]),
    step_durations: Optional[List[float]] = None,
    font_family: str = "Open Sans",
):
    """
    Executes smooth, word-synchronized animations for the process flow framework.
    """
    mobs = create_process_flow_mobject(
        kicker=kicker,
        title=title,
        origin_label=origin_label,
        paths=paths,
        target_label=target_label,
        center_pos=center_pos,
        font_family=font_family,
    )

    header_grp = mobs["header_grp"]
    origin_node = mobs["origin_node"]
    target_node = mobs["target_node"]
    path_groups = mobs["path_groups"]
    in_conduits = mobs["in_conduits"]
    out_conduits = mobs["out_conduits"]

    durs = step_durations or [2.0, 3.0, 3.5, 2.5]

    # Step 1: Header and Ingress Node materialize
    scene.play(FadeIn(header_grp, shift=DOWN * 0.15), run_time=0.5)
    pulse_ring = Circle(radius=0.25, stroke_color=COLOR_BLUE, stroke_width=2.2).move_to(origin_node[1].get_center())
    scene.play(
        FadeIn(origin_node, shift=RIGHT * 0.2),
        pulse_ring.animate.scale(2.2).set_opacity(0),
        run_time=0.6
    )
    scene.remove(pulse_ring)
    scene.wait(max(0.2, durs[0] - 1.1))

    # Step 2: Conduits branch out and Candidate Paths appear
    scene.play(
        *[Create(c, run_time=0.6) for c in in_conduits],
        *[FadeIn(p, shift=RIGHT * 0.2, run_time=0.7) for p in path_groups],
    )

    # Step 3: Evaluation signal pulses travel along conduits
    pulse_dots = [
        Dot(c.get_start(), radius=0.08, color=COLOR_BLUE).set_z_index(10)
        for c in in_conduits
    ]
    scene.play(
        *[pulse_dots[i].animate.move_to(in_conduits[i].get_end()) for i in range(len(pulse_dots))],
        run_time=0.8,
        rate_func=linear
    )
    for dot in pulse_dots:
        scene.remove(dot)

    # Step 4: Decision activation & Target connection
    # Optimal path highlights, sub-optimal dims
    scene.play(
        *[Create(c, run_time=0.6) for c in out_conduits],
        FadeIn(target_node, shift=LEFT * 0.2, run_time=0.7),
        run_time=0.8
    )
    scene.wait(max(0.5, durs[-1] - 0.8))


class ProcessFlowScene(Scene):
    def construct(self):
        bg = Rectangle(width=16, height=10, fill_color=COLOR_WHITE, fill_opacity=1.0, stroke_width=0)
        self.add(bg)
        play_process_flow(self)


if __name__ == "__main__":
    import subprocess
    subprocess.run(["python", "-m", "manim", "-pql", __file__, "ProcessFlowScene"])
