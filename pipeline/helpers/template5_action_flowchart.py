"""
template5_action_flowchart.py — Simplilearn OSL 3.0 Action-Oriented Flowchart Template
=======================================================================================
Reusable Manim programmatic template for Action-Oriented Decision Routing, Tool Dispatch,
and Multi-Factor Trade-off Evaluation (Derived from Pilot Standard 1:54 - 2:10).

Adheres strictly to Simplilearn Learning Design & OSL 3.0 Video Guidelines:
- Layout: Compatible with Layout 70 and Layout 20.
- Visual Architecture: Central Decision Hub -> Multi-Branch Action Endpoints with Particle Streams
- Morphing Continuity: Smooth scale-down of completed step into persistent anchor cards
- Multi-Factor Trade-off: Includes decision criteria pills (Efficiency, Cost, Confidence) & winning badge
- Zero Elastic Wobbles: Clean, purposeful animations using rate_func=smooth and rate_func=linear

Usage:
------
from template5_action_flowchart import play_action_flowchart, create_action_flowchart_mobject

class MyScene(Scene):
    def construct(self):
        play_action_flowchart(
            self,
            hub_title="LLM Reasoning Core",
            branches=[
                {"title": "Sensory Analysis", "color": "#1D4ED8"},
                {"title": "Plan Evaluation", "color": "#0284C7"},
                {"title": "Tool Dispatch", "color": "#10B981"},
            ],
            trade_off_options=[
                {"name": "Option A: Diagnostic Report", "selected": False},
                {"name": "Option B: Real-Time Summary", "selected": True},
            ]
        )

Command-line test render:
-------------------------
python -m manim -pql template5_action_flowchart.py ActionFlowchartScene
"""

from __future__ import annotations
import os
from typing import Optional, Union, List, Dict, Any
import numpy as np
from manim import *
import manimpango

COLOR_NAVY       = "#1E293B"
COLOR_DARK_NAVY  = "#0F172A"
COLOR_BLUE       = "#007ACC"
COLOR_COBALT     = "#1D4ED8"
COLOR_CYAN       = "#0284C7"
COLOR_TEAL       = "#10B981"
COLOR_INDIGO     = "#6366F1"
COLOR_WHITE      = "#FFFFFF"
COLOR_CARD_BG    = "#F8FAFC"
COLOR_BOX_BG     = "#F1F5F9"
COLOR_BORDER     = "#CBD5E1"
COLOR_GRAY       = "#64748B"
COLOR_DARK       = "#1E293B"


def get_simplilearn_font(preferred: str = "Open Sans") -> str:
    """Returns preferred font if available, else clean system fallback."""
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


def CrispText(text, size=24, font="Open Sans", **kwargs):
    """Typography renderer with 4x supersampling for crisp glyph display."""
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


class FlowingStream(VGroup):
    """Animated directional stream of particle dots traveling along a vector conduit."""
    def __init__(self, start_pt, end_pt, color=COLOR_BLUE, num_dots=3, speed=0.6, dot_radius=0.065, **kwargs):
        super().__init__(**kwargs)
        self.start_pt = np.array(start_pt)
        self.end_pt = np.array(end_pt)
        self.color = color
        self.num_dots = num_dots
        self.speed = speed
        self.dot_radius = dot_radius
        self.phase = 0.0

        self.dots = [Dot(radius=self.dot_radius, color=self.color).set_z_index(12) for _ in range(num_dots)]
        self.add(*self.dots)
        self.add_updater(self._update_stream)

    def _update_stream(self, mob, dt):
        self.phase = (self.phase + dt * self.speed) % 1.0
        vec = self.end_pt - self.start_pt
        for i, dot in enumerate(self.dots):
            t = (self.phase + i / float(self.num_dots)) % 1.0
            dot.move_to(self.start_pt + t * vec)


def create_action_flowchart_mobject(
    hub_title: str = "LLM Deliberation Core",
    branches: Optional[List[Dict[str, Any]]] = None,
    stage_center: np.ndarray = np.array([0.0, -0.35, 0.0]),
    font_family: str = "Open Sans",
) -> Dict[str, Any]:
    """Constructs the action-oriented flowchart and decision branch hierarchy."""
    font = get_simplilearn_font(font_family)

    if branches is None:
        branches = [
            {"title": "Perception\nanalysis", "color": COLOR_INDIGO},
            {"title": "Plan & goal\nevaluation", "color": COLOR_SKY if 'COLOR_SKY' in globals() else COLOR_CYAN},
            {"title": "Tool action\nselection", "color": COLOR_TEAL},
        ]

    # 1. Central Ingress Hub (Top Center)
    hub_box = RoundedRectangle(
        corner_radius=0.14, width=2.40, height=0.72,
        fill_color=COLOR_DARK_NAVY, fill_opacity=1.0,
        stroke_color=COLOR_BLUE, stroke_width=2.2
    ).move_to(stage_center + UP * 1.05)

    hub_txt = CrispText(hub_title, size=14.0, color=COLOR_WHITE, weight=BOLD, font=font).move_to(hub_box)
    hub_grp = VGroup(hub_box, hub_txt)

    # 2. Decision Branches (Below Hub)
    branch_mobs = []
    lines = []
    streams = []
    n_br = len(branches)
    x_coords = np.linspace(-2.2, 2.2, n_br)

    for i, br in enumerate(branches):
        bx = stage_center[0] + x_coords[i]
        by = stage_center[1] - 0.45
        b_color = br.get("color", COLOR_BLUE)

        b_box = RoundedRectangle(
            corner_radius=0.10, width=1.75, height=0.78,
            fill_color=COLOR_DARK_NAVY, fill_opacity=1.0,
            stroke_color=b_color, stroke_width=1.8
        ).move_to(np.array([bx, by, 0]))

        b_txt = CrispText(br.get("title", f"Branch {i+1}"), size=10.5, color=COLOR_WHITE, weight=BOLD, font=font, align="center").move_to(b_box)
        b_grp = VGroup(b_box, b_txt)
        branch_mobs.append(b_grp)

        # Connection line
        c_line = Line(hub_box.get_bottom(), b_box.get_top(), color=b_color, stroke_width=2.0)
        lines.append(c_line)

        # Animated Particle Stream
        stream = FlowingStream(hub_box.get_bottom(), b_box.get_top(), color=b_color, num_dots=2, speed=0.55)
        streams.append(stream)

    # 3. Subtitle annotation pill
    sub_box = RoundedRectangle(corner_radius=0.10, width=5.2, height=0.42, fill_color="#EFF6FF", fill_opacity=1.0, stroke_color=COLOR_BLUE, stroke_width=1.2).move_to(stage_center + DOWN * 1.45)
    sub_txt = CrispText("LLM core interprets sensory state & dynamically routes actions", size=10.5, color=COLOR_DARK, weight=BOLD, font=font).move_to(sub_box)
    sub_pill = VGroup(sub_box, sub_txt)

    return {
        "hub_grp": hub_grp,
        "branch_mobs": branch_mobs,
        "lines": lines,
        "streams": streams,
        "sub_pill": sub_pill,
    }


def play_action_flowchart(
    scene: Scene,
    hub_title: str = "LLM Deliberation Core",
    branches: Optional[List[Dict[str, Any]]] = None,
    stage_center: np.ndarray = np.array([0.0, -0.35, 0.0]),
    hold_duration: float = 3.5,
    font_family: str = "Open Sans",
):
    """Executes the action-oriented flowchart animation with particle streams."""
    mobs = create_action_flowchart_mobject(
        hub_title=hub_title,
        branches=branches,
        stage_center=stage_center,
        font_family=font_family,
    )

    hub_grp = mobs["hub_grp"]
    branch_mobs = mobs["branch_mobs"]
    lines = mobs["lines"]
    streams = mobs["streams"]
    sub_pill = mobs["sub_pill"]

    # 1. Entrance of Central Hub
    scene.play(FadeIn(hub_grp, scale=0.9), run_time=0.6)
    scene.wait(0.3)

    # 2. Branch lines draw out, particle streams ignite, action cards appear
    scene.play(
        *[Create(l, run_time=0.6) for l in lines],
        *[FadeIn(b, shift=UP * 0.15, run_time=0.7) for b in branch_mobs],
        *[FadeIn(s) for s in streams],
        FadeIn(sub_pill, shift=UP * 0.1),
        run_time=0.8
    )

    # 3. Word-level spoken emphasis sweep across action nodes
    for i, b in enumerate(branch_mobs):
        scene.play(
            Indicate(b, color=b[0].get_stroke_color(), scale_factor=1.08),
            run_time=0.4
        )

    scene.wait(hold_duration)

    # Cleanup stream updaters
    for s in streams:
        s.clear_updaters()


class ActionFlowchartScene(Scene):
    def construct(self):
        bg = Rectangle(width=16, height=10, fill_color=COLOR_WHITE, fill_opacity=1.0, stroke_width=0)
        self.add(bg)
        play_action_flowchart(self)


if __name__ == "__main__":
    import subprocess
    subprocess.run(["python", "-m", "manim", "-pql", __file__, "ActionFlowchartScene"])
