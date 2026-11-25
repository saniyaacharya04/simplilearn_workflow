"""
vector_primitives.py — Simplilearn OSL 3.0 Architectural Vector Primitives
===========================================================================
Pure Manim geometric primitives designed to replace raster PNG images with
living, high-editorial vector assemblies for educational animations.

Classes:
  - PremiumBalanceScale: Articulated balance scale with stepped plinth, fluted column,
                         gimbal pivot, 3D weight blocks, and harmonic ambient sway.
  - PrecisionChronometerGauge: Calibrated gauge dial with graduated zones, tick marks,
                               knurled bezel, and live telemetry needle jitter.
  - NeuralReasoningCore: Multi-tiered neural core with glowing synapses, cognitive rings,
                         and continuous orbiting data particles.
  - ActionDispatchHub: Precision rotary cog hub with actuator core and continuous smooth gear drive.
  - VectorGoalTarget: Multi-tiered concentric bullseye target with crosshairs and breathing halo.
  - VectorOperatorStation: High-tech human operator console with live oscilloscope wave and alert beacon.
"""

from __future__ import annotations
import numpy as np
from manim import *


# -------------------------------------------------------------------------
# Safe CrispText Helper
# -------------------------------------------------------------------------
def CrispText(text: str, size: int = 14, font: str = "sans-serif", **kwargs) -> Mobject:
    """Renders crisp text using standard Manim Text with scale compensation."""
    kwargs.pop("font_size", None)
    kwargs.pop("autowrap", None)
    kwargs.pop("size", None)
    weight_val = kwargs.pop("weight", NORMAL)
    slant_val = kwargs.pop("slant", NORMAL)
    color_val = kwargs.pop("color", "#404040")

    if isinstance(weight_val, str):
        w = weight_val.upper().replace("-", "").replace("_", "").replace(" ", "")
        if w in ("BOLD", "HEAVY"):
            weight_val = BOLD
        elif w in ("SEMIBOLD", "MEDIUM"):
            weight_val = SEMIBOLD
        elif w == "LIGHT":
            weight_val = LIGHT
        else:
            weight_val = NORMAL

    txt = Text(
        str(text),
        font=font,
        font_size=int(size * 4),
        weight=weight_val,
        slant=slant_val,
        color=color_val,
        **kwargs
    ).scale(0.25)
    return txt


# -------------------------------------------------------------------------
# 1. PremiumBalanceScale (Living Analytical Trade-off Scale)
# -------------------------------------------------------------------------
class PremiumBalanceScale(VGroup):
    """
    Articulated Institutional Balance Scale with Living Mechanical Kinematics.
    - Stepped pedestal base with dark-indigo / slate two-tone shading and ground shadow.
    - Fluted central column pillar with polished brass hardware and gimbal pivot.
    - Sculpted double-flanged balance beam with brass terminal eyelets.
    - Twin suspended parabolic weighing pans with 3D-styled weight blocks.
    - Continuous harmonic ambient micro-swaying updater: never freezes or looks static!
    """

    def __init__(
        self,
        center=ORIGIN,
        tilt_angle: float = 0.0,
        beam_length: float = 3.6,
        hang_depth: float = 1.35,
        left_label: str = "Cost",
        right_label: str = "Speed",
        left_color: str = "#E58F6D",
        right_color: str = "#2C81FE",
        accent_color: str = "#F0C265",
        base_color: str = "#0F172A",
        enable_ambient_sway: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.beam_len = float(beam_length)
        self.hang_depth = float(hang_depth)
        self.left_label = left_label
        self.right_label = right_label
        self.left_color = left_color
        self.right_color = right_color
        self.accent_color = accent_color
        self.base_color = base_color
        self.enable_sway = enable_ambient_sway

        self.tilt_tracker = ValueTracker(tilt_angle)
        self.time_tracker = ValueTracker(0)

        self._build_static_structure()
        self._build_dynamic_rigging()
        self.add_updater(lambda mob, dt: mob._step_kinematics(dt))

    def _build_static_structure(self):
        c = self.center_pt

        # Base Drop Shadow
        self.shadow = Ellipse(
            width=self.beam_len * 1.15, height=0.30,
            fill_color="#CBD5E1", fill_opacity=0.45,
            stroke_width=0
        ).move_to(c + DOWN * 2.25)

        # Tiered Stepped Plinth (3 tiers with brass inlay)
        self.base_step1 = RoundedRectangle(
            width=3.4, height=0.36, corner_radius=0.08,
            fill_color=self.base_color, fill_opacity=0.06,
            stroke_color=self.base_color, stroke_width=2.2
        ).next_to(self.shadow, UP, buff=-0.14)

        self.base_brass = RoundedRectangle(
            width=2.5, height=0.12, corner_radius=0.04,
            fill_color=self.accent_color, fill_opacity=1.0,
            stroke_color=self.base_color, stroke_width=1.5
        ).next_to(self.base_step1, UP, buff=-0.02)

        self.base_step2 = RoundedRectangle(
            width=1.6, height=0.18, corner_radius=0.06,
            fill_color=self.base_color, fill_opacity=1.0, stroke_width=0
        ).next_to(self.base_brass, UP, buff=-0.02)

        # Precision Leveling Feet
        foot_l = Dot(self.base_step1.get_corner(DL) + RIGHT * 0.35 + DOWN * 0.04, radius=0.07, color=self.accent_color)
        foot_r = Dot(self.base_step1.get_corner(DR) + LEFT * 0.35 + DOWN * 0.04, radius=0.07, color=self.accent_color)

        # Two-Tone Fluted Central Column
        col_w = 0.38
        c_top = c + UP * 0.50
        c_bot = self.base_step2.get_top()

        col_left = Polygon(
            c_bot + LEFT * (col_w / 2.0), c_bot,
            c_top, c_top + LEFT * (col_w * 0.40),
            fill_color=self.base_color, fill_opacity=0.06,
            stroke_color=self.base_color, stroke_width=1.8
        )
        col_right = Polygon(
            c_bot, c_bot + RIGHT * (col_w / 2.0),
            c_top + RIGHT * (col_w * 0.40), c_top,
            fill_color=self.base_color, fill_opacity=1.0,
            stroke_color=self.base_color, stroke_width=1.8
        )

        col_collar_mid = RoundedRectangle(
            width=col_w + 0.16, height=0.10, corner_radius=0.03,
            fill_color=self.accent_color, fill_opacity=1.0, stroke_width=0
        ).move_to((c_top + c_bot) / 2.0)

        # Gimbal Pivot Assembly
        pivot_ring = Circle(
            radius=0.25, fill_color=self.accent_color, fill_opacity=1.0,
            stroke_color=self.base_color, stroke_width=2.5
        ).move_to(c_top)

        pivot_inner = Circle(
            radius=0.14, fill_color=self.base_color, fill_opacity=1.0, stroke_width=0
        ).move_to(c_top)

        pivot_jewel = Dot(c_top, radius=0.06, color=self.right_color)

        self.pedestal = VGroup(
            self.shadow, foot_l, foot_r,
            self.base_step1, self.base_brass, self.base_step2,
            col_left, col_right, col_collar_mid,
            pivot_ring, pivot_inner, pivot_jewel
        )
        self.add(self.pedestal)

    def _build_dynamic_rigging(self):
        c_top = self.center_pt + UP * 0.50

        # Sculpted Balance Beam (Double line with center reinforcement)
        self.beam = Line(
            LEFT * (self.beam_len / 2.0), RIGHT * (self.beam_len / 2.0),
            stroke_color=self.base_color, stroke_width=3.8
        ).move_to(c_top)

        self.beam_groove = Line(
            LEFT * (self.beam_len / 2.0 * 0.88), RIGHT * (self.beam_len / 2.0 * 0.88),
            stroke_color=self.accent_color, stroke_width=1.2
        ).move_to(c_top)

        # Terminal Eyelets
        self.eyelet_l = Circle(radius=0.10, fill_color=self.accent_color, fill_opacity=1.0, stroke_color=self.base_color, stroke_width=2.0)
        self.eyelet_r = Circle(radius=0.10, fill_color=self.accent_color, fill_opacity=1.0, stroke_color=self.base_color, stroke_width=2.0)

        self.rigging_group = VGroup()
        self.add(self.beam, self.beam_groove, self.eyelet_l, self.eyelet_r, self.rigging_group)
        self._update_rigging(0.0)

    def _step_kinematics(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        base_tilt = self.tilt_tracker.get_value()
        sway = 0.022 * np.sin(t * 2.2) if self.enable_sway else 0.0
        self._update_rigging(base_tilt + sway)

    def _update_rigging(self, ang: float):
        pivot = self.center_pt + UP * 0.50
        hw = self.beam_len / 2.0

        p_l = pivot + np.array([-np.cos(ang) * hw, -np.sin(ang) * hw, 0])
        p_r = pivot + np.array([ np.cos(ang) * hw,  np.sin(ang) * hw, 0])

        self.beam.put_start_and_end_on(p_l, p_r)
        self.beam_groove.put_start_and_end_on(
            pivot + np.array([-np.cos(ang) * (hw * 0.85), -np.sin(ang) * (hw * 0.85), 0]),
            pivot + np.array([ np.cos(ang) * (hw * 0.85),  np.sin(ang) * (hw * 0.85), 0])
        )
        self.eyelet_l.move_to(p_l)
        self.eyelet_r.move_to(p_r)

        self.rigging_group.submobjects.clear()

        # Render plumb suspension cords and pans
        for pt, label, col, is_left in [(p_l, self.left_label, self.left_color, True), (p_r, self.right_label, self.right_color, False)]:
            pan_center = pt + DOWN * self.hang_depth
            cord_l = Line(pt, pan_center + LEFT * 0.40 + UP * 0.16, stroke_color=self.base_color, stroke_width=1.4)
            cord_r = Line(pt, pan_center + RIGHT * 0.40 + UP * 0.16, stroke_color=self.base_color, stroke_width=1.4)

            # Curved Parabolic Pan with 2.5D Rim
            pan_arc = Arc(
                radius=0.50, start_angle=PI, angle=PI,
                color=self.base_color, stroke_width=2.5
            ).move_to(pan_center + DOWN * 0.14)

            pan_fill = Polygon(
                pan_center + LEFT * 0.50 + DOWN * 0.14,
                pan_center + RIGHT * 0.50 + DOWN * 0.14,
                pan_center + DOWN * 0.50,
                fill_color=col, fill_opacity=0.06, stroke_width=0
            )

            pan_rim = Line(
                pan_center + LEFT * 0.50 + DOWN * 0.14,
                pan_center + RIGHT * 0.50 + DOWN * 0.14,
                stroke_color=col, stroke_width=2.2
            )

            # 3D-styled weight block inside the pan
            w_box = RoundedRectangle(width=0.62, height=0.34, corner_radius=0.05, fill_color=col, fill_opacity=0.88, stroke_color=self.base_color, stroke_width=1.2).move_to(pan_center + DOWN * 0.05)
            w_txt = CrispText(label, size=9, weight=BOLD, color="#FFFFFF").move_to(w_box)
            weight_block = VGroup(w_box, w_txt)

            tag = CrispText(label, size=11, weight=BOLD, color=col).move_to(pan_center + UP * 0.22)
            self.rigging_group.add(cord_l, cord_r, pan_fill, pan_arc, pan_rim, weight_block, tag)


# -------------------------------------------------------------------------
# 2. PrecisionChronometerGauge (Live Calibrated Dial with Telemetry Jitter)
# -------------------------------------------------------------------------
class PrecisionChronometerGauge(VGroup):
    """
    Precision Calibrated Chronometer / Utility Gauge.
    - Knurled outer bezel rim with metallic accent disc.
    - Calibrated color zones (Optimal, Moderate, Alert/Threshold).
    - Graduated radial tick marks.
    - Live telemetry needle jitter: subtle continuous needle breathing.
    - Center ruby jewel pivot and digital metric display pill.
    """

    def __init__(
        self,
        center=ORIGIN,
        radius: float = 1.15,
        value: float = 0.5,
        min_angle: float = -PI * 0.75,
        max_angle: float =  PI * 0.75,
        title: str = "Perception Stream",
        unit_label: str = "Optimal Flow",
        enable_jitter: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.rad = float(radius)
        self.min_ang = float(min_angle)
        self.max_ang = float(max_angle)
        self.title_text = title
        self.unit_text = unit_label
        self.enable_jitter = enable_jitter

        self.val_tracker = ValueTracker(value)
        self.time_tracker = ValueTracker(0)

        self._build_gauge_housing()
        self._build_needle()
        self.add_updater(lambda mob, dt: mob._step_gauge(dt))

    def _build_gauge_housing(self):
        c = self.center_pt
        r = self.rad

        # Outer Shadow & Knurled Bezel
        shadow = Ellipse(width=r * 2.3, height=0.22, fill_color="#CBD5E1", fill_opacity=0.35, stroke_width=0).move_to(c + DOWN * (r + 0.35))
        bezel_outer = Circle(radius=r + 0.12, stroke_color="#0F172A", stroke_width=2.5, fill_color="#62B7E4", fill_opacity=0.04).move_to(c)
        bezel_rim = Circle(radius=r + 0.04, stroke_color="#F0C265", stroke_width=1.5, fill_opacity=0).move_to(c)
        dial_face = Circle(radius=r, fill_opacity=0, stroke_color="#CBD5E1", stroke_width=1.0).move_to(c)

        # Calibrated Arc Zones
        arc_alert = AnnularSector(
            inner_radius=r * 0.78, outer_radius=r * 0.90,
            angle=PI * 0.50, start_angle=PI * 0.25,
            fill_color="#E58F6D", fill_opacity=0.85, stroke_width=0
        ).move_to(c)

        arc_mod = AnnularSector(
            inner_radius=r * 0.78, outer_radius=r * 0.90,
            angle=PI * 0.50, start_angle=-PI * 0.25,
            fill_color="#DDB945", fill_opacity=0.85, stroke_width=0
        ).move_to(c)

        arc_opt = AnnularSector(
            inner_radius=r * 0.78, outer_radius=r * 0.90,
            angle=PI * 0.50, start_angle=-PI * 0.75,
            fill_color="#2C81FE", fill_opacity=0.85, stroke_width=0
        ).move_to(c)

        # Graduated Radial Ticks
        ticks = VGroup()
        for i in range(13):
            frac = i / 12.0
            ang = self.max_ang - frac * (self.max_ang - self.min_ang) + PI / 2.0
            t_len = 0.12 if i % 3 == 0 else 0.07
            t_start = c + np.array([np.cos(ang) * (r * 0.92), np.sin(ang) * (r * 0.92), 0])
            t_end = c + np.array([np.cos(ang) * (r * 0.92 - t_len), np.sin(ang) * (r * 0.92 - t_len), 0])
            sw = 2.0 if i % 3 == 0 else 1.0
            ticks.add(Line(t_start, t_end, stroke_color="#475569", stroke_width=sw))

        lbl_title = CrispText(self.title_text, size=11, weight=BOLD, color="#0F172A").move_to(c + UP * (r * 0.38))
        self.lbl_unit = CrispText(self.unit_text, size=10, weight=SEMIBOLD, color="#2C81FE").move_to(c + DOWN * (r * 0.42))

        self.housing = VGroup(
            shadow, bezel_outer, bezel_rim, dial_face,
            arc_alert, arc_mod, arc_opt, ticks,
            lbl_title, self.lbl_unit
        )
        self.add(self.housing)

    def _build_needle(self):
        c = self.center_pt
        self.needle_poly = Polygon(c, c, c, c, fill_color="#E58F6D", fill_opacity=1.0, stroke_color="#0F172A", stroke_width=1.2)
        self.hub_outer = Circle(radius=0.18, fill_color="#0F172A", fill_opacity=1.0, stroke_color="#F0C265", stroke_width=1.5).move_to(c)
        self.hub_jewel = Dot(c, radius=0.06, color="#FFFFFF")

        self.add(self.needle_poly, self.hub_outer, self.hub_jewel)
        self._update_needle(self.val_tracker.get_value())

    def _step_gauge(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        base_val = self.val_tracker.get_value()
        jitter = 0.015 * np.sin(t * 3.8) + 0.008 * np.cos(t * 6.2) if self.enable_jitter else 0.0
        self._update_needle(base_val + jitter)

    def _update_needle(self, current_val: float):
        c = self.center_pt
        r = self.rad
        val = np.clip(current_val, 0.0, 1.0)
        ang = (self.min_ang + val * (self.max_ang - self.min_ang)) + PI / 2.0

        p_tip = c + np.array([np.cos(ang) * (r * 0.78), np.sin(ang) * (r * 0.78), 0])
        p_left = c + np.array([np.cos(ang + PI/2) * 0.06, np.sin(ang + PI/2) * 0.06, 0])
        p_right = c + np.array([np.cos(ang - PI/2) * 0.06, np.sin(ang - PI/2) * 0.06, 0])
        p_back = c - np.array([np.cos(ang) * 0.16, np.sin(ang) * 0.16, 0])

        new_poly = Polygon(p_tip, p_left, p_back, p_right, fill_color="#E58F6D", fill_opacity=1.0, stroke_color="#0F172A", stroke_width=1.2)
        self.needle_poly.become(new_poly)


# -------------------------------------------------------------------------
# 3. NeuralReasoningCore (Multi-Tiered Neural Core with Orbiting Particles)
# -------------------------------------------------------------------------
class NeuralReasoningCore(VGroup):
    """
    Multi-Tiered Vector Neural Reasoning Engine.
    - Layered cognitive ring boundaries with 2.5D optical facets.
    - Central hexagonal cognitive nucleus with sapphire core.
    - Orbiting data particles circling the nucleus continuously!
    - Radial synaptic interlinks with pulsing respiration.
    """

    def __init__(self, center=ORIGIN, radius: float = 1.25, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.rad = float(radius)
        self.time_tracker = ValueTracker(0)

        self._build_core()
        self.add_updater(lambda mob, dt: mob._step_core(dt))

    def _build_core(self):
        c = self.center_pt
        r = self.rad

        # Ambient Glow Halos
        self.outer_glow = Circle(radius=r * 1.25, stroke_color="#9B99C7", stroke_width=1.5, fill_color="#9B99C7", fill_opacity=0.10).move_to(c)
        self.mid_ring = Circle(radius=r, stroke_color="#2C81FE", stroke_width=2.0, fill_color="#2C81FE", fill_opacity=0.04).move_to(c)

        # Central Hexagonal Cognitive Nucleus
        self.nucleus = RegularPolygon(n=6, radius=r * 0.55, stroke_color="#0F172A", stroke_width=2.5, fill_color="#0F172A", fill_opacity=1.0).move_to(c)
        self.inner_jewel = RegularPolygon(n=6, radius=r * 0.35, stroke_color="#F0C265", stroke_width=1.5, fill_color="#2C81FE", fill_opacity=0.85).move_to(c)

        # Radial Synaptic Lines and Nodes
        self.synapses = VGroup()
        self.nodes = VGroup()
        for i in range(6):
            ang = i * (PI / 3.0)
            p_node = c + np.array([np.cos(ang) * (r * 0.88), np.sin(ang) * (r * 0.88), 0])
            line = Line(c, p_node, stroke_color="#62B7E4", stroke_width=1.5, stroke_opacity=0.6)
            node_dot = Dot(p_node, radius=0.08, color="#2C81FE")
            node_halo = Circle(radius=0.14, stroke_color="#E58F6D", stroke_width=1.5, fill_opacity=0).move_to(p_node)
            self.synapses.add(line)
            self.nodes.add(node_dot, node_halo)

        # 3 Orbiting Data Particles
        self.orbit_particles = VGroup(
            Dot(color="#F0C265", radius=0.07),
            Dot(color="#E58F6D", radius=0.07),
            Dot(color="#2C81FE", radius=0.07)
        )

        label_bg = RoundedRectangle(width=2.2, height=0.40, corner_radius=0.1, fill_color="#2C81FE", fill_opacity=0.06, stroke_color="#2C81FE", stroke_width=1.5).next_to(self.mid_ring, DOWN, buff=0.20)
        label_txt = CrispText("LLM Reasoning Core", size=11, weight=BOLD, color="#0F172A").move_to(label_bg)
        self.label_grp = VGroup(label_bg, label_txt)

        self.add(self.outer_glow, self.mid_ring, self.synapses, self.nucleus, self.inner_jewel, self.nodes, self.orbit_particles, self.label_grp)

    def _step_core(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        c = self.center_pt
        r = self.rad

        # Respiration pulse
        s = 1.0 + 0.05 * np.sin(t * 3.0)
        self.outer_glow.set_stroke(opacity=max(0.1, 0.4 + 0.3 * np.sin(t * 3.0)))
        self.inner_jewel.scale_to_fit_width(r * 0.70 * s)

        # Update orbiting particles around cognitive core
        for i, dot in enumerate(self.orbit_particles):
            ang = t * 2.0 + i * (2 * PI / 3.0)
            dot.move_to(c + np.array([np.cos(ang) * (r * 0.65), np.sin(ang) * (r * 0.65), 0]))


# -------------------------------------------------------------------------
# 4. ActionDispatchHub (Precision Rotary Gear Drive)
# -------------------------------------------------------------------------
class ActionDispatchHub(VGroup):
    """
    Articulated Rotary Action Dispatch Hub.
    - Precision machine cogs radially anchored around central actuator.
    - High-contrast two-tone central drive disc with sapphire core.
    - Continuous smooth gear rotation updater.
    """

    def __init__(self, center=ORIGIN, radius: float = 1.25, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.rad = float(radius)
        self.time_tracker = ValueTracker(0)

        self._build_hub()
        self.add_updater(lambda mob, dt: mob._step_hub(dt))

    def _build_hub(self):
        c = self.center_pt
        r = self.rad

        shadow = Ellipse(width=r * 2.3, height=0.25, fill_color="#CBD5E1", fill_opacity=0.35, stroke_width=0).move_to(c + DOWN * (r + 0.25))
        hub_ring = Circle(radius=r, stroke_color="#0F172A", stroke_width=2.5, fill_color="#E58F6D", fill_opacity=0.04).move_to(c)
        hub_inner = Circle(radius=r * 0.75, stroke_color="#E58F6D", stroke_width=2.0, fill_opacity=0).move_to(c)

        # 6 Peripheral Cogs
        self.cogs = VGroup()
        for i in range(6):
            ang = i * (PI / 3.0)
            cog = RoundedRectangle(
                width=0.22, height=0.36, corner_radius=0.04,
                fill_color="#E58F6D", fill_opacity=0.85,
                stroke_color="#0F172A", stroke_width=1.2
            ).move_to(c + np.array([np.cos(ang) * (r * 0.95), np.sin(ang) * (r * 0.95), 0])).rotate(ang)
            self.cogs.add(cog)

        actuator_outer = Circle(radius=r * 0.40, fill_color="#0F172A", fill_opacity=1.0, stroke_color="#F0C265", stroke_width=2.0).move_to(c)
        actuator_inner = Circle(radius=r * 0.22, fill_color="#2C81FE", fill_opacity=1.0, stroke_width=0).move_to(c)
        actuator_center = Dot(c, radius=0.06, color="#FFFFFF")

        label_bg = RoundedRectangle(width=2.2, height=0.40, corner_radius=0.1, fill_color="#E58F6D", fill_opacity=0.06, stroke_color="#E58F6D", stroke_width=1.5).next_to(hub_ring, DOWN, buff=0.20)
        label_txt = CrispText("Action Dispatch Hub", size=11, weight=BOLD, color="#0F172A").move_to(label_bg)
        self.label_grp = VGroup(label_bg, label_txt)

        self.add(shadow, hub_ring, self.cogs, hub_inner, actuator_outer, actuator_inner, actuator_center, self.label_grp)

    def _step_hub(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        c = self.center_pt
        r = self.rad
        val = t * 0.75  # smooth continuous rotation

        for i, cog in enumerate(self.cogs):
            ang = (i * (PI / 3.0)) + val
            new_cog = RoundedRectangle(
                width=0.22, height=0.36, corner_radius=0.04,
                fill_color="#E58F6D", fill_opacity=0.85,
                stroke_color="#0F172A", stroke_width=1.2
            ).move_to(c + np.array([np.cos(ang) * (r * 0.95), np.sin(ang) * (r * 0.95), 0])).rotate(ang)
            cog.become(new_cog)


# -------------------------------------------------------------------------
# 5. VectorGoalTarget (Concentric Bullseye with Crosshairs & Pulsing Halo)
# -------------------------------------------------------------------------
class VectorGoalTarget(VGroup):
    """
    Pure Vector Target & Goal Objective Apparatus.
    Replaces static raster images with living vector target geometry:
    - Tiered concentric rings (#0F172A, #FFFFFF, #2C81FE, #F0C265).
    - Precision crosshair reticle needles with status ticks.
    - Pulsing glowing bullseye with continuous breathing halo.
    """

    def __init__(self, center=ORIGIN, radius: float = 0.90, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.rad = float(radius)
        self.time_tracker = ValueTracker(0)

        self._build_target()
        self.add_updater(lambda mob, dt: mob._step_target(dt))

    def _build_target(self):
        c = self.center_pt
        r = self.rad

        shadow = Ellipse(width=r * 2.4, height=0.20, fill_color="#CBD5E1", fill_opacity=0.40, stroke_width=0).move_to(c + DOWN * (r + 0.18))

        # Concentric Target Rings
        ring_outer = Circle(radius=r, fill_color="#62B7E4", fill_opacity=0.04, stroke_color="#0F172A", stroke_width=2.5).move_to(c)
        ring_brass = Circle(radius=r * 0.82, fill_color="#F0C265", fill_opacity=0.25, stroke_color="#F0C265", stroke_width=1.5).move_to(c)
        ring_mid = Circle(radius=r * 0.60, fill_color="#2C81FE", fill_opacity=0.85, stroke_color="#0F172A", stroke_width=2.0).move_to(c)
        ring_white = Circle(radius=r * 0.38, fill_color="#2C81FE", fill_opacity=0.06, stroke_color="#0F172A", stroke_width=1.5).move_to(c)
        ring_bullseye = Dot(c, radius=r * 0.20, color="#E58F6D")

        # Crosshair Reticle
        ch_h = Line(c + LEFT * (r * 1.15), c + RIGHT * (r * 1.15), stroke_color="#0F172A", stroke_width=1.5)
        ch_v = Line(c + DOWN * (r * 1.15), c + UP * (r * 1.15), stroke_color="#0F172A", stroke_width=1.5)
        reticle = VGroup(ch_h, ch_v)

        # Pulsing Glow Halo
        self.pulse_halo = Circle(radius=r * 0.28, stroke_color="#F0C265", stroke_width=2.0, fill_opacity=0).move_to(c)

        self.add(shadow, ring_outer, ring_brass, ring_mid, ring_white, ring_bullseye, reticle, self.pulse_halo)

    def _step_target(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        # Pulse bullseye halo
        scale_fac = 1.0 + 0.40 * (t % 1.2) / 1.2
        opacity = max(0.0, 1.0 - (t % 1.2) / 1.2)
        self.pulse_halo.become(
            Circle(radius=self.rad * 0.22 * scale_fac, stroke_color="#F0C265", stroke_width=2.0, fill_opacity=0)
            .set_stroke(opacity=opacity)
            .move_to(self.center_pt)
        )


# -------------------------------------------------------------------------
# 6. VectorOperatorStation (Human Escalation Station with Oscilloscope)
# -------------------------------------------------------------------------
class VectorOperatorStation(VGroup):
    """
    Pure Vector Human-in-the-Loop Operator Console.
    Replaces static raster operator PNG with high-editorial vector apparatus:
    - Stepped operator console workstation with brass trim.
    - Terminal monitor screen with live animated telemetry oscilloscope wave.
    - Flashing alert beacon indicating responsible escalation.
    """

    def __init__(self, center=ORIGIN, width: float = 2.2, height: float = 1.6, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.w = float(width)
        self.h = float(height)
        self.time_tracker = ValueTracker(0)

        self._build_station()
        self.add_updater(lambda mob, dt: mob._step_station(dt))

    def _build_station(self):
        c = self.center_pt
        w = self.w
        h = self.h

        # Ground Shadow
        shadow = Ellipse(width=w * 1.3, height=0.22, fill_color="#CBD5E1", fill_opacity=0.45, stroke_width=0).move_to(c + DOWN * (h/2 + 0.15))

        # Console Base Plinth
        plinth = RoundedRectangle(width=w * 1.1, height=0.28, corner_radius=0.06, fill_color="#0F172A", fill_opacity=1.0, stroke_width=0).move_to(c + DOWN * (h/2 - 0.05))
        plinth_trim = RoundedRectangle(width=w * 0.9, height=0.08, corner_radius=0.03, fill_color="#F0C265", fill_opacity=1.0, stroke_width=0).next_to(plinth, UP, buff=-0.02)

        # Terminal Screen Outer Frame
        screen_frame = RoundedRectangle(width=w, height=h * 0.85, corner_radius=0.12, fill_color="#0F172A", fill_opacity=0.04, stroke_color="#0F172A", stroke_width=2.2).move_to(c + UP * 0.15)
        screen_bezel = RoundedRectangle(width=w * 0.88, height=h * 0.68, corner_radius=0.08, fill_color="#0F172A", fill_opacity=1.0, stroke_width=0).move_to(screen_frame)

        # Flashing Alert Beacon on Top
        self.beacon_housing = RoundedRectangle(width=0.35, height=0.18, corner_radius=0.04, fill_color="#F0C265", fill_opacity=1.0, stroke_color="#0F172A", stroke_width=1.5).next_to(screen_frame, UP, buff=-0.04)
        self.beacon_light = Dot(self.beacon_housing.get_top() + UP * 0.08, radius=0.09, color="#E58F6D")
        self.beacon_halo = Circle(radius=0.20, stroke_color="#E58F6D", stroke_width=2.0, fill_opacity=0).move_to(self.beacon_light)

        # Live Oscilloscope Waveform on Screen
        self.wave_line = VMobject(stroke_color="#62B7E4", stroke_width=2.0)
        self.screen_center = screen_bezel.get_center()

        self.add(shadow, plinth, plinth_trim, screen_frame, screen_bezel, self.beacon_housing, self.beacon_light, self.beacon_halo, self.wave_line)
        self._update_wave(0.0)

    def _step_station(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)

        # Beacon flash
        beacon_opacity = 0.3 + 0.7 * abs(np.sin(t * 4.0))
        self.beacon_light.set_opacity(beacon_opacity)
        self.beacon_halo.set_stroke(opacity=max(0.0, beacon_opacity - 0.2))

        # Oscilloscope wave animation
        self._update_wave(t)

    def _update_wave(self, t: float):
        sc = self.screen_center
        pts = []
        for x in np.linspace(-0.75, 0.75, 25):
            y = 0.12 * np.sin(x * 8.0 + t * 5.0)
            pts.append(sc + np.array([x, y, 0]))
        self.wave_line.set_points_smoothly(pts)


class VectorSolarArray(VGroup):
    """
    Pure Manim vector representation of a modern industrial photovoltaic solar array.
    Features angled solar panel modules with grid segmentation, metallic support struts,
    and an active energy absorption shimmer updater.
    """
    def __init__(self, center: np.ndarray = ORIGIN, scale: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.time_tracker = ValueTracker(0.0)
        self._build_array()
        self.add_updater(lambda mob, dt: mob._step_solar(dt))

    def _build_array(self):
        c = self.center_pt
        s = self.scale_factor

        # Base shadow
        shadow = Ellipse(width=3.2 * s, height=0.40 * s, fill_color="#CBD5E1", fill_opacity=0.45, stroke_width=0).move_to(c + DOWN * 0.95 * s)

        # Diagonal structural mounting struts
        strut_l = Line(c + LEFT * 1.1 * s + DOWN * 0.9 * s, c + LEFT * 0.7 * s + UP * 0.1 * s, color="#5F6368", stroke_width=3.0 * s)
        strut_r = Line(c + RIGHT * 1.1 * s + DOWN * 0.9 * s, c + RIGHT * 0.7 * s + UP * 0.1 * s, color="#5F6368", stroke_width=3.0 * s)
        strut_cross = Line(c + LEFT * 0.9 * s + DOWN * 0.4 * s, c + RIGHT * 0.9 * s + DOWN * 0.4 * s, color="#7EA2C8", stroke_width=2.0 * s)

        # 4-Quadrant Solar Panel Plane
        self.panel_group = VGroup()
        quad_w, quad_h = 1.1 * s, 0.65 * s
        positions = [
            (-quad_w * 0.52, quad_h * 0.52),
            (quad_w * 0.52, quad_h * 0.52),
            (-quad_w * 0.52, -quad_h * 0.52),
            (quad_w * 0.52, -quad_h * 0.52)
        ]

        self.cells = []
        for dx, dy in positions:
            quad_center = c + np.array([dx, dy, 0])
            quad_box = RoundedRectangle(
                width=quad_w, height=quad_h, corner_radius=0.06 * s,
                fill_color="#1E293B", fill_opacity=0.95,
                stroke_color="#2C81FE", stroke_width=1.8 * s
            ).move_to(quad_center)

            grid_lines = VGroup(
                Line(quad_center + LEFT * quad_w * 0.45, quad_center + RIGHT * quad_w * 0.45, color="#62B7E4", stroke_width=1.0 * s),
                Line(quad_center + UP * quad_h * 0.45, quad_center + DOWN * quad_h * 0.45, color="#62B7E4", stroke_width=1.0 * s)
            )
            self.cells.append(quad_box)
            self.panel_group.add(quad_box, grid_lines)

        # Telemetry beacon on top frame
        self.telemetry_node = Dot(c + UP * 0.92 * s, radius=0.08 * s, color="#F0C265")
        self.telemetry_ring = Circle(radius=0.18 * s, stroke_color="#F0C265", stroke_width=1.5 * s, fill_opacity=0).move_to(self.telemetry_node)

        self.add(shadow, strut_l, strut_r, strut_cross, self.panel_group, self.telemetry_node, self.telemetry_ring)

    def _step_solar(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        pulse = 0.4 + 0.6 * abs(np.sin(t * 3.5))
        self.telemetry_node.set_opacity(pulse)
        self.telemetry_ring.set_stroke(opacity=max(0.0, pulse - 0.2))


class VectorDualStoreMemory(VGroup):
    """
    Pure Manim vector representation of an AI agent's dual-store memory.
    Left side: Short-Term Operational Context Cache (Illuminated stack registers)
    Right side: Long-Term Episodic Vector Database (3D Cylinder with circulating embeddings)
    """
    def __init__(self, center: np.ndarray = ORIGIN, scale: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.time_tracker = ValueTracker(0.0)
        self._build_memory()
        self.add_updater(lambda mob, dt: mob._step_memory(dt))

    def _build_memory(self):
        c = self.center_pt
        s = self.scale_factor

        # Left: Short-Term Cache Stack
        cache_c = c + LEFT * 1.35 * s
        cache_bg = RoundedRectangle(
            width=1.5 * s, height=1.8 * s, corner_radius=0.10 * s,
            fill_color="#7EA2C8", fill_opacity=0.06, stroke_color="#7EA2C8", stroke_width=1.8 * s
        ).move_to(cache_c)
        cache_header = Text("SHORT-TERM CACHE", font="Helvetica", weight=BOLD, color="#5F6368").scale(0.18 * s)
        cache_header.next_to(cache_bg.get_top(), DOWN, buff=0.12 * s)

        self.registers = []
        reg_colors = ["#2C81FE", "#62B7E4", "#9B99C7", "#8ECDB7"]
        for i, rcol in enumerate(reg_colors):
            ry = cache_c[1] + 0.35 * s - i * 0.30 * s
            r_bar = RoundedRectangle(
                width=1.2 * s, height=0.20 * s, corner_radius=0.04 * s,
                fill_color=rcol, fill_opacity=0.85, stroke_width=0
            ).move_to(np.array([cache_c[0], ry, 0]))
            self.registers.append(r_bar)

        self.cache_grp = VGroup(cache_bg, cache_header, *self.registers)

        # Right: Long-Term Vector DB (Layered 3D Cylinder)
        db_c = c + RIGHT * 1.35 * s
        top_ellipse = Ellipse(width=1.3 * s, height=0.45 * s, fill_color="#2C81FE", fill_opacity=0.9, stroke_color="#62B7E4", stroke_width=1.8 * s).move_to(db_c + UP * 0.65 * s)
        mid_rect = Rectangle(width=1.3 * s, height=1.1 * s, fill_color="#1E293B", fill_opacity=0.95, stroke_color="#62B7E4", stroke_width=1.8 * s).move_to(db_c + UP * 0.10 * s)
        bot_ellipse = Ellipse(width=1.3 * s, height=0.45 * s, fill_color="#1E293B", fill_opacity=0.95, stroke_color="#62B7E4", stroke_width=1.8 * s).move_to(db_c + DOWN * 0.45 * s)
        db_label = Text("VECTOR DB", font="Helvetica", weight=BOLD, color="#FFFFFF").scale(0.20 * s)
        db_label.move_to(db_c + UP * 0.10 * s)

        self.db_dots = []
        for d_angle in [0.3, 1.8, 3.5, 4.9]:
            d_pos = db_c + np.array([np.cos(d_angle) * 0.48 * s, np.sin(d_angle) * 0.15 * s + 0.1 * s, 0])
            v_dot = Dot(d_pos, radius=0.06 * s, color="#F0C265")
            self.db_dots.append((v_dot, d_angle))

        self.db_grp = VGroup(bot_ellipse, mid_rect, top_ellipse, db_label, *[d[0] for d in self.db_dots])

        # Interconnecting Bridge / Bus
        self.bus_line = DashedVMobject(Line(cache_c + RIGHT * 0.75 * s, db_c + LEFT * 0.65 * s, color="#F0C265", stroke_width=2.5 * s), num_dashes=8)
        self.packet = Dot(cache_c + RIGHT * 0.75 * s, radius=0.07 * s, color="#F0C265")

        self.add(self.cache_grp, self.db_grp, self.bus_line, self.packet)

    def _step_memory(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        s = self.scale_factor
        db_c = self.center_pt + RIGHT * 1.35 * s
        for dot, base_ang in self.db_dots:
            cur_ang = base_ang + t * 1.2
            dot.move_to(db_c + np.array([np.cos(cur_ang) * 0.48 * s, np.sin(cur_ang) * 0.15 * s + 0.1 * s, 0]))

        p_frac = (t * 0.8) % 1.0
        start = self.center_pt + LEFT * 0.60 * s
        end = self.center_pt + RIGHT * 0.70 * s
        self.packet.move_to(start + (end - start) * p_frac)


class VectorReflexSwitch(VGroup):
    """
    Pure Manim vector representation of a Reactive Agent's Condition-Action Reflex Switch.
    Shows high-speed direct routing: Condition Sensor -> Precision Switch Arm -> Effector Trigger.
    """
    def __init__(self, center: np.ndarray = ORIGIN, scale: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.time_tracker = ValueTracker(0.0)
        self._build_switch()
        self.add_updater(lambda mob, dt: mob._step_switch(dt))

    def _build_switch(self):
        c = self.center_pt
        s = self.scale_factor

        chassis = RoundedRectangle(
            width=3.2 * s, height=1.4 * s, corner_radius=0.12 * s,
            fill_color="#2C81FE", fill_opacity=0.06, stroke_color="#2C81FE", stroke_width=2.0 * s
        ).move_to(c)
        tag = Text("IF CONDITION -> THEN ACTION", font="Helvetica", weight=BOLD, color="#2C81FE").scale(0.18 * s)
        tag.next_to(chassis.get_top(), DOWN, buff=0.12 * s)

        self.term_in = Dot(c + LEFT * 1.1 * s + DOWN * 0.15 * s, radius=0.11 * s, color="#0F172A")
        self.term_out = Dot(c + RIGHT * 1.1 * s + DOWN * 0.15 * s, radius=0.11 * s, color="#0F172A")

        self.arm_pivot = self.term_in.get_center()
        self.arm_target = self.term_out.get_center()
        self.switch_arm = Line(
            self.arm_pivot,
            self.arm_pivot + (self.arm_target - self.arm_pivot) * 0.85 + UP * 0.25 * s,
            color="#E58F6D", stroke_width=4.0 * s
        )

        self.spark = Circle(radius=0.16 * s, stroke_color="#F0C265", stroke_width=2.5 * s, fill_opacity=0).move_to(self.term_out.get_center())

        self.add(chassis, tag, self.term_in, self.term_out, self.switch_arm, self.spark)

    def _step_switch(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        cycle = (t * 1.5) % 2.0
        s = self.scale_factor
        if cycle < 1.0:
            self.switch_arm.put_start_and_end_on(self.arm_pivot, self.arm_target + UP * 0.02 * s)
            self.switch_arm.set_color("#2C81FE")
            self.spark.set_stroke(opacity=0.4 + 0.6 * np.sin(t * 8.0))
        else:
            self.switch_arm.put_start_and_end_on(self.arm_pivot, self.arm_pivot + (self.arm_target - self.arm_pivot) * 0.85 + UP * 0.25 * s)
            self.switch_arm.set_color("#E58F6D")
            self.spark.set_stroke(opacity=0.0)


class VectorAutonomousHeroCore(VGroup):
    """
    Pure Manim vector hero artifact representing an Autonomous AI Agent.
    Combines central reasoning nucleus, orbiting perception scanner, and rotary action cog.
    """
    def __init__(self, center: np.ndarray = ORIGIN, scale: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.time_tracker = ValueTracker(0.0)
        self._build_hero()
        self.add_updater(lambda mob, dt: mob._step_hero(dt))

    def _build_hero(self):
        c = self.center_pt
        s = self.scale_factor

        self.outer_ring = Circle(radius=1.35 * s, stroke_color="#62B7E4", stroke_width=2.0 * s, fill_opacity=0).move_to(c)
        self.cog_ring = DashedVMobject(Circle(radius=1.15 * s, stroke_color="#2C81FE", stroke_width=3.5 * s, fill_opacity=0), num_dashes=16).move_to(c)
        self.core_disc = Circle(radius=0.75 * s, fill_color="#1E293B", fill_opacity=0.95, stroke_color="#F0C265", stroke_width=2.5 * s).move_to(c)
        self.core_symbol = Text("ACT", font="Helvetica", weight=BOLD, color="#FFFFFF").scale(0.32 * s)
        self.core_symbol.move_to(c)

        self.sat1 = Dot(c + RIGHT * 1.35 * s, radius=0.09 * s, color="#F0C265")
        self.sat2 = Dot(c + LEFT * 1.35 * s, radius=0.09 * s, color="#8ECDB7")

        self.add(self.outer_ring, self.cog_ring, self.core_disc, self.core_symbol, self.sat1, self.sat2)

    def _step_hero(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        s = self.scale_factor
        c = self.center_pt
        self.outer_ring.set_stroke(width=(1.5 + 1.0 * np.sin(t * 2.0)) * s, opacity=0.5 + 0.5 * np.cos(t * 2.0))
        ang1 = t * 1.4
        ang2 = t * 1.4 + np.pi
        self.sat1.move_to(c + np.array([np.cos(ang1) * 1.35 * s, np.sin(ang1) * 1.35 * s, 0]))
        self.sat2.move_to(c + np.array([np.cos(ang2) * 1.35 * s, np.sin(ang2) * 1.35 * s, 0]))
