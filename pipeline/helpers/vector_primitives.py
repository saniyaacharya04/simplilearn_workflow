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
def CrispText(text: str, size: int = 14, font: str = "Open Sans", **kwargs) -> Mobject:
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
        cache_header = Text("SHORT-TERM CACHE", font="Open Sans", weight=BOLD, color="#5F6368").scale(0.18 * s)
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
        db_label = Text("VECTOR DB", font="Open Sans", weight=BOLD, color="#FFFFFF").scale(0.20 * s)
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
        tag = Text("IF CONDITION -> THEN ACTION", font="Open Sans", weight=BOLD, color="#2C81FE").scale(0.18 * s)
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
        self.core_symbol = Text("ACT", font="Open Sans", weight=BOLD, color="#FFFFFF").scale(0.32 * s)
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


# -------------------------------------------------------------------------
# 11. VectorTelemetryChart (Dynamic Performance & Metric Chart)
# -------------------------------------------------------------------------
class VectorTelemetryChart(VGroup):
    """
    Dynamic 2D coordinate telemetry graph.
    Visualizes live metric trends, dynamic threshold markers, and spoken status callouts.
    Free from hardcoded arbitrary numbers — labels, metrics, and colors derive dynamically from narration.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        x_label: str = "Time",
        y_label: str = "Performance",
        status_label: str = "Optimal",
        line_color: str = "#2C81FE",
        badge_color: str = "#8ECDB7",
        highlight_color: str = "#F78908",
        axis_color: str = "#1E293B",
        bg_color: str = "#F8FAFC",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.x_label = x_label
        self.y_label = y_label
        self.status_label = status_label
        self.line_color = line_color
        self.badge_color = badge_color
        self.highlight_color = highlight_color
        self.axis_color = axis_color
        self.bg_color = bg_color
        self.time_tracker = ValueTracker(0.0)
        self._build_chart()
        self.add_updater(lambda mob, dt: mob._step_chart(dt))

    def _build_chart(self):
        c = self.center_pt
        s = self.scale_factor

        self.bg_card = RoundedRectangle(
            width=4.4 * s, height=3.0 * s, corner_radius=0.10 * s,
            fill_color=self.bg_color, fill_opacity=0.95,
            stroke_color="#CBD5E1", stroke_width=1.5 * s
        ).move_to(c)

        origin_pt = c + LEFT * 1.7 * s + DOWN * 1.0 * s
        x_end = origin_pt + RIGHT * 3.4 * s
        y_end = origin_pt + UP * 2.0 * s

        self.x_axis = Line(origin_pt, x_end, stroke_color=self.axis_color, stroke_width=2.0 * s)
        self.y_axis = Line(origin_pt, y_end, stroke_color=self.axis_color, stroke_width=2.0 * s)

        self.x_lbl = CrispText(self.x_label, size=9, weight=SEMIBOLD, color="#64748B").next_to(self.x_axis.get_end(), DOWN, buff=0.08 * s)
        self.y_lbl = CrispText(self.y_label, size=9, weight=SEMIBOLD, color="#64748B").next_to(self.y_axis.get_end(), LEFT, buff=0.08 * s)

        points = [
            origin_pt + RIGHT * 0.2 * s + UP * 0.4 * s,
            origin_pt + RIGHT * 1.0 * s + UP * 0.8 * s,
            origin_pt + RIGHT * 1.8 * s + UP * 0.5 * s,
            origin_pt + RIGHT * 2.6 * s + UP * 1.5 * s,
            origin_pt + RIGHT * 3.2 * s + UP * 1.7 * s
        ]
        self.curve = VMobject(stroke_color=self.line_color, stroke_width=3.0 * s)
        self.curve.set_points_smoothly(points)

        badge_box = RoundedRectangle(
            width=1.5 * s, height=0.34 * s, corner_radius=0.08 * s,
            fill_color=self.badge_color, fill_opacity=0.9,
            stroke_color=self.line_color, stroke_width=1.0 * s
        ).move_to(c + UP * 1.15 * s + RIGHT * 1.1 * s)
        badge_txt = CrispText(self.status_label, size=9, weight=BOLD, color="#FFFFFF").move_to(badge_box)
        self.status_badge = VGroup(badge_box, badge_txt)

        self.cursor_dot = Dot(points[-1], radius=0.07 * s, color=self.highlight_color)
        self.pulse_ring = Circle(radius=0.14 * s, stroke_color=self.highlight_color, stroke_width=1.5 * s, fill_opacity=0).move_to(points[-1])

        self.add(self.bg_card, self.x_axis, self.y_axis, self.x_lbl, self.y_lbl, self.curve, self.status_badge, self.cursor_dot, self.pulse_ring)

    def _step_chart(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        s = self.scale_factor
        self.pulse_ring.set_stroke(opacity=0.3 + 0.7 * np.sin(t * 3.0), width=(1.5 + 0.8 * np.sin(t * 3.0)) * s)


# -------------------------------------------------------------------------
# 12. VectorAPIGateway (Cloud & Service Distribution Gateway)
# -------------------------------------------------------------------------
class VectorAPIGateway(VGroup):
    """
    Cloud API Gateway and Service Distributor.
    Connects incoming request streams to backend services or tools.
    Colors, channels, and labels adapt dynamically based on narration context.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        title: str = "API Gateway",
        services: Optional[List[str]] = None,
        gateway_color: str = "#1E293B",
        accent_color: str = "#2C81FE",
        service_colors: Optional[List[str]] = None,
        packet_color: str = "#F78908",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.title_str = title
        self.services_list = services or ["Service A", "Service B", "Service C"]
        self.gateway_color = gateway_color
        self.accent_color = accent_color
        self.service_colors = service_colors or ["#7EA2C8", "#62B7E4", "#8ECDB7"]
        self.packet_color = packet_color
        self.time_tracker = ValueTracker(0.0)
        self._build_gateway()
        self.add_updater(lambda mob, dt: mob._step_gateway(dt))

    def _build_gateway(self):
        c = self.center_pt
        s = self.scale_factor

        in_box = RoundedRectangle(width=1.4 * s, height=0.55 * s, corner_radius=0.10 * s, fill_color="#EFF6FF", fill_opacity=1.0, stroke_color=self.accent_color, stroke_width=1.5 * s).move_to(c + LEFT * 2.2 * s)
        in_txt = CrispText("Request", size=10, weight=BOLD, color=self.accent_color).move_to(in_box)
        self.ingress_m = VGroup(in_box, in_txt)

        gw_box = RoundedRectangle(width=1.8 * s, height=1.6 * s, corner_radius=0.12 * s, fill_color=self.gateway_color, fill_opacity=0.95, stroke_color=self.accent_color, stroke_width=2.5 * s).move_to(c)
        gw_txt = CrispText(self.title_str, size=11, weight=BOLD, color="#FFFFFF").move_to(gw_box.get_top() + DOWN * 0.3 * s)
        gw_icon = Circle(radius=0.25 * s, fill_color=self.accent_color, fill_opacity=0.8, stroke_color="#8ECDB7", stroke_width=1.5 * s).move_to(gw_box.get_center() + DOWN * 0.2 * s)
        self.gateway_m = VGroup(gw_box, gw_txt, gw_icon)

        self.in_line = Line(in_box.get_right(), gw_box.get_left(), stroke_color=self.accent_color, stroke_width=2.0 * s)

        self.dest_groups = []
        self.out_lines = []
        self.out_dots = []
        n_services = len(self.services_list)
        y_span = 1.8 * s
        y_start = (y_span / 2) if n_services > 1 else 0

        for i, s_name in enumerate(self.services_list):
            y_offset = (y_start - i * (y_span / max(1, n_services - 1))) if n_services > 1 else 0
            svc_c = c + RIGHT * 2.2 * s + UP * y_offset
            s_col = self.service_colors[i % len(self.service_colors)]
            svc_box = RoundedRectangle(width=1.5 * s, height=0.45 * s, corner_radius=0.08 * s, fill_color="#F0F4F8", fill_opacity=0.95, stroke_color=s_col, stroke_width=1.5 * s).move_to(svc_c)
            svc_txt = CrispText(s_name, size=9.5, weight=BOLD, color="#1E293B").move_to(svc_box)
            svc_grp = VGroup(svc_box, svc_txt)
            self.dest_groups.append(svc_grp)

            line = Line(gw_box.get_right(), svc_box.get_left(), stroke_color="#CBD5E1", stroke_width=1.5 * s)
            self.out_lines.append(line)

            dot = Dot(line.get_start(), radius=0.05 * s, color=self.packet_color)
            self.out_dots.append(dot)

        self.in_dot = Dot(self.in_line.get_start(), radius=0.05 * s, color=self.accent_color)

        self.add(self.ingress_m, self.gateway_m, self.in_line, self.in_dot, *self.dest_groups, *self.out_lines, *self.out_dots)

    def _step_gateway(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        p1 = (t * 0.8) % 1.0
        self.in_dot.move_to(self.in_line.point_from_proportion(p1))
        for i, dot in enumerate(self.out_dots):
            p2 = ((t * 0.8) + i * 0.3) % 1.0
            dot.move_to(self.out_lines[i].point_from_proportion(p2))


# -------------------------------------------------------------------------
# 13. Vector2x2Matrix (Executive Prioritization & Decision Matrix)
# -------------------------------------------------------------------------
class Vector2x2Matrix(VGroup):
    """
    Executive 2x2 Decision & Prioritization Matrix (e.g. Impact vs. Effort, SWOT).
    Organized into four rounded quadrants with dynamic pastel tones from Simplilearn palette.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        x_label: str = "Effort",
        y_label: str = "Impact",
        quadrant_titles: Optional[Dict[str, str]] = None,
        quadrant_colors: Optional[Dict[str, str]] = None,
        axis_color: str = "#1E293B",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.x_label = x_label
        self.y_label = y_label
        self.axis_color = axis_color
        defaults = {
            "top_right": "Strategic",
            "top_left": "Quick Wins",
            "bottom_left": "Low Priority",
            "bottom_right": "Re-evaluate"
        }
        self.q_titles = {**defaults, **(quadrant_titles or {})}
        default_colors = {
            "top_left": "#62B7E4",     # Sky Blue
            "top_right": "#8ECDB7",    # Mint
            "bottom_left": "#C1A5C6",  # Soft Lilac
            "bottom_right": "#DDB945"  # Mustard Gold
        }
        self.q_colors = {**default_colors, **(quadrant_colors or {})}
        self._build_matrix()

    def _build_matrix(self):
        c = self.center_pt
        s = self.scale_factor
        qw = 2.0 * s
        qh = 1.3 * s
        r = 0.08 * s

        q_cfg = [
            (-qw/2 - 0.08*s,  qh/2 + 0.08*s, self.q_colors["top_left"], "top_left"),
            ( qw/2 + 0.08*s,  qh/2 + 0.08*s, self.q_colors["top_right"], "top_right"),
            (-qw/2 - 0.08*s, -qh/2 - 0.08*s, self.q_colors["bottom_left"], "bottom_left"),
            ( qw/2 + 0.08*s, -qh/2 - 0.08*s, self.q_colors["bottom_right"], "bottom_right")
        ]

        self.quadrants = []
        for dx, dy, col, key in q_cfg:
            box = RoundedRectangle(
                width=qw, height=qh, corner_radius=r,
                fill_color=col, fill_opacity=0.25,
                stroke_color=col, stroke_width=1.8 * s
            ).move_to(c + np.array([dx, dy, 0]))
            label = CrispText(self.q_titles.get(key, ""), size=9.5, weight=BOLD, color="#1E293B").move_to(box)
            self.quadrants.append(VGroup(box, label))

        self.h_axis = Line(c + LEFT * (qw + 0.2 * s), c + RIGHT * (qw + 0.2 * s), stroke_color=self.axis_color, stroke_width=2.0 * s)
        self.v_axis = Line(c + DOWN * (qh + 0.2 * s), c + UP * (qh + 0.2 * s), stroke_color=self.axis_color, stroke_width=2.0 * s)

        self.x_txt = CrispText(self.x_label, size=10, weight=BOLD, color=self.axis_color).next_to(self.h_axis.get_end(), RIGHT, buff=0.1 * s)
        self.y_txt = CrispText(self.y_label, size=10, weight=BOLD, color=self.axis_color).next_to(self.v_axis.get_end(), UP, buff=0.1 * s)

        self.add(*self.quadrants, self.h_axis, self.v_axis, self.x_txt, self.y_txt)


# -------------------------------------------------------------------------
# 14. VectorMarketingFunnel (Multi-Stage Conversion & Process Funnel)
# -------------------------------------------------------------------------
class VectorMarketingFunnel(VGroup):
    """
    Tiered conversion funnel or progressive workflow pipeline.
    Renders descending rounded tiers with dynamic colors matching narration intent.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        stages: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.stages_list = stages or ["Awareness", "Consideration", "Conversion", "Retention"]
        self.colors_list = colors or ["#62B7E4", "#7EA2C8", "#E6A157", "#8ECDB7", "#9B99C7"]
        self._build_funnel()

    def _build_funnel(self):
        c = self.center_pt
        s = self.scale_factor
        n = len(self.stages_list)

        tier_h = 0.55 * s
        tier_gap = 0.10 * s
        total_h = n * tier_h + (n - 1) * tier_gap
        top_y = c[1] + (total_h / 2) - (tier_h / 2)

        max_w = 4.2 * s
        min_w = 1.8 * s

        self.tiers = []
        for i, s_title in enumerate(self.stages_list):
            w = max_w - i * ((max_w - min_w) / max(1, n - 1)) if n > 1 else max_w
            y = top_y - i * (tier_h + tier_gap)
            col = self.colors_list[i % len(self.colors_list)]

            box = RoundedRectangle(
                width=w, height=tier_h, corner_radius=0.08 * s,
                fill_color=col, fill_opacity=0.85,
                stroke_color="#FFFFFF", stroke_width=1.5 * s
            ).move_to(np.array([c[0], y, 0]))

            txt = CrispText(s_title, size=10.5, weight=BOLD, color="#FFFFFF").move_to(box)
            self.tiers.append(VGroup(box, txt))

        self.add(*self.tiers)
        self.time_tracker = ValueTracker(0.0)
        self.flow_dots = VGroup()
        for i in range(4):
            d = Dot(radius=0.06 * s, color="#FFFFFF")
            self.flow_dots.add(d)
        self.add(self.flow_dots)
        self.add_updater(lambda mob, dt: mob._step_funnel(dt))

    def _step_funnel(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        c = self.center_pt
        s = self.scale_factor
        n = len(self.stages_list)
        tier_h = 0.55 * s
        tier_gap = 0.10 * s
        total_h = n * tier_h + (n - 1) * tier_gap
        top_y = c[1] + (total_h / 2)
        for i, dot in enumerate(self.flow_dots):
            p = ((t * 0.65) + i * 0.25) % 1.0
            y = top_y - p * total_h
            jx = np.sin(t * 3.0 + i) * 0.15 * (1.0 - p) * s
            dot.move_to(np.array([c[0] + jx, y, 0]))
            dot.set_opacity(0.9 * (1.0 - p * 0.4))


# -------------------------------------------------------------------------
# 15. VectorAgileSprintCycle (Continuous Loop & Sprint Governance)
# -------------------------------------------------------------------------
class VectorAgileSprintCycle(VGroup):
    """
    Circular feedback loop for Agile sprint cycles and continuous governance.
    Features smooth circular loop, milestone discs, and orbiting progress indicator.
    Colors dynamically map to phase semantics from the narration.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        phases: Optional[List[str]] = None,
        track_color: str = "#2C81FE",
        center_color: str = "#1E293B",
        node_colors: Optional[List[str]] = None,
        orbit_color: str = "#F78908",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.phases_list = phases or ["Plan", "Build", "Review", "Retrospective"]
        self.track_color = track_color
        self.center_color = center_color
        self.node_colors = node_colors or ["#62B7E4", "#8ECDB7", "#DDB945", "#E58F6D"]
        self.orbit_color = orbit_color
        self.time_tracker = ValueTracker(0.0)
        self._build_sprint()
        self.add_updater(lambda mob, dt: mob._step_sprint(dt))

    def _build_sprint(self):
        c = self.center_pt
        s = self.scale_factor
        rad = 1.35 * s

        self.track = Circle(radius=rad, stroke_color=self.track_color, stroke_width=3.0 * s, fill_opacity=0).move_to(c)

        center_box = Circle(radius=0.55 * s, fill_color=self.center_color, fill_opacity=0.95, stroke_color="#62B7E4", stroke_width=2.0 * s).move_to(c)
        center_txt = CrispText("Sprint", size=10, weight=BOLD, color="#FFFFFF").move_to(center_box)
        self.center_badge = VGroup(center_box, center_txt)

        self.nodes = []
        n = len(self.phases_list)

        for i, p_title in enumerate(self.phases_list):
            ang = np.pi / 2 - i * (2 * np.pi / n)
            pos = c + np.array([np.cos(ang) * rad, np.sin(ang) * rad, 0])
            col = self.node_colors[i % len(self.node_colors)]
            node_circle = Circle(radius=0.28 * s, fill_color=col, fill_opacity=1.0, stroke_color="#FFFFFF", stroke_width=1.5 * s).move_to(pos)
            node_num = CrispText(f"0{i+1}", size=9, weight=BOLD, color="#FFFFFF").move_to(node_circle)

            label_pos = c + np.array([np.cos(ang) * (rad + 0.45 * s), np.sin(ang) * (rad + 0.45 * s), 0])
            lbl = CrispText(p_title, size=9.5, weight=BOLD, color="#1E293B").move_to(label_pos)

            self.nodes.append(VGroup(node_circle, node_num, lbl))

        self.orbit_dot = Dot(c + UP * rad, radius=0.08 * s, color=self.orbit_color)

        self.add(self.track, self.center_badge, *self.nodes, self.orbit_dot)

    def _step_sprint(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        s = self.scale_factor
        c = self.center_pt
        rad = 1.35 * s
        ang = np.pi / 2 - t * 0.8
        self.orbit_dot.move_to(c + np.array([np.cos(ang) * rad, np.sin(ang) * rad, 0]))


# -------------------------------------------------------------------------
# 16. VectorSecurityShield (Verification & Security Policy Shield)
# -------------------------------------------------------------------------
class VectorSecurityShield(VGroup):
    """
    Clean 2D vector security & verification shield with central keyhole
    and dynamic verification status badge.
    Colors dynamically reflect security state and policy verification.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        label: str = "Verified",
        shield_color: str = "#1E293B",
        stroke_color: str = "#2C81FE",
        badge_color: str = "#8ECDB7",
        glow_color: str = "#8ECDB7",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.status_label = label
        self.shield_color = shield_color
        self.stroke_color = stroke_color
        self.badge_color = badge_color
        self.glow_color = glow_color
        self.time_tracker = ValueTracker(0.0)
        self._build_shield()
        self.add_updater(lambda mob, dt: mob._step_shield(dt))

    def _build_shield(self):
        c = self.center_pt
        s = self.scale_factor

        pts = [
            c + UP * 1.0 * s + LEFT * 0.9 * s,
            c + UP * 1.0 * s + RIGHT * 0.9 * s,
            c + DOWN * 0.2 * s + RIGHT * 0.85 * s,
            c + DOWN * 1.0 * s,
            c + DOWN * 0.2 * s + LEFT * 0.85 * s,
        ]
        self.shield_body = Polygon(
            *pts,
            fill_color=self.shield_color, fill_opacity=0.95,
            stroke_color=self.stroke_color, stroke_width=2.5 * s
        )

        top_circle = Circle(radius=0.18 * s, fill_color="#62B7E4", fill_opacity=1.0, stroke_width=0).move_to(c + UP * 0.2 * s)
        slot = Rectangle(width=0.12 * s, height=0.25 * s, fill_color="#62B7E4", fill_opacity=1.0, stroke_width=0).move_to(c + DOWN * 0.05 * s)
        self.keyhole = VGroup(top_circle, slot)

        badge_box = RoundedRectangle(
            width=1.4 * s, height=0.35 * s, corner_radius=0.08 * s,
            fill_color=self.badge_color, fill_opacity=0.95,
            stroke_color=self.stroke_color, stroke_width=1.0 * s
        ).move_to(c + DOWN * 1.25 * s)
        badge_txt = CrispText(self.status_label, size=9.5, weight=BOLD, color="#FFFFFF").move_to(badge_box)
        self.badge_m = VGroup(badge_box, badge_txt)

        self.glow_ring = Circle(radius=0.45 * s, stroke_color=self.glow_color, stroke_width=1.5 * s, fill_opacity=0).move_to(self.keyhole.get_center())

        self.add(self.shield_body, self.keyhole, self.badge_m, self.glow_ring)

    def _step_shield(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        s = self.scale_factor
        self.glow_ring.set_stroke(opacity=0.3 + 0.5 * np.sin(t * 2.5), width=(1.2 + 0.6 * np.sin(t * 2.5)) * s)



# -------------------------------------------------------------------------
# 17. VectorFlywheelMechanism (Revolving Multi-Stage Progression Flywheel)
# -------------------------------------------------------------------------
class VectorFlywheelMechanism(VGroup):
    """
    Revolving 3-stage / multi-stage triangular progression flywheel with
    beveled gear rim, stage pods, feedback flow arcs, and continuous rotation.
    Represents the Perception-Reasoning-Action (PRA) perpetual cycle.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        radius: float = 1.9,
        stages: list = None,
        cycle_label: str = "Diagnostic Cycle: 24 Iterations",
        enable_rotation: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.radius = float(radius)
        self.stages = stages or [
            ("Perception", "#62B7E4", "Data / Input"),
            ("Reasoning", "#9B99C7", "LLM / Planning"),
            ("Action", "#8ECDB7", "Tool / Output")
        ]
        self.cycle_label = cycle_label
        self.enable_rotation = enable_rotation
        self.time_tracker = ValueTracker(0.0)
        self._build_flywheel()
        if self.enable_rotation:
            self.add_updater(lambda mob, dt: mob._step_flywheel(dt))

    def _build_flywheel(self):
        c = self.center_pt
        r = self.radius

        # Foundation: Outer Gear Rim & Track
        self.outer_rim = Circle(radius=r, stroke_color="#CBD5E1", stroke_width=2.5, fill_opacity=0.0).move_to(c)
        self.inner_track = Circle(radius=r * 0.72, stroke_color="#E2E8F0", stroke_width=1.5, stroke_opacity=0.6).move_to(c)

        # Gear teeth ticks around outer rim
        ticks = VGroup()
        for i in range(24):
            ang = i * (2 * np.pi / 24)
            p1 = c + np.array([np.cos(ang) * (r - 0.08), np.sin(ang) * (r - 0.08), 0])
            p2 = c + np.array([np.cos(ang) * (r + 0.08), np.sin(ang) * (r + 0.08), 0])
            ticks.add(Line(p1, p2, stroke_color="#94A3B8", stroke_width=1.8))
        self.gear_ticks = ticks

        # Rotor assembly that rotates
        self.rotor = VGroup()
        n_stages = len(self.stages)
        self.stage_mobs = []

        for i, (name, color, sub) in enumerate(self.stages):
            ang = np.pi / 2 - i * (2 * np.pi / n_stages)
            pod_pos = c + np.array([np.cos(ang) * (r * 0.72), np.sin(ang) * (r * 0.72), 0])

            # Stage Pod Container
            pod_card = RoundedRectangle(
                width=1.45, height=0.65, corner_radius=0.08,
                fill_color="#FFFFFF", fill_opacity=0.98,
                stroke_color=color, stroke_width=2.2
            ).move_to(pod_pos)
            pod_txt = CrispText(name, size=9.5, weight=BOLD, color=color).move_to(pod_card.get_center() + UP * 0.10)
            pod_sub = CrispText(sub, size=7.0, weight=NORMAL, color="#64748B").move_to(pod_card.get_center() + DOWN * 0.12)
            pod_group = VGroup(pod_card, pod_txt, pod_sub)
            self.stage_mobs.append(pod_group)
            self.rotor.add(pod_group)

            # Spokes from center to stage pod
            spoke = Line(c, pod_pos, stroke_color=color, stroke_width=1.5, stroke_opacity=0.5)
            self.rotor.add(spoke)

        # Feedback Flow Arcs linking stages in a clockwise loop
        self.flow_arcs = VGroup()
        for i in range(n_stages):
            start_ang = np.pi / 2 - i * (2 * np.pi / n_stages) - 0.35
            arc = Arc(
                radius=r * 0.72,
                start_angle=start_ang,
                angle=-(2 * np.pi / n_stages - 0.70),
                stroke_color=self.stages[i][1],
                stroke_width=2.5
            ).move_to(c)
            self.flow_arcs.add(arc)

        # Traveling pulse particle along flow track
        self.flow_dot = Dot(radius=0.09, color="#F78908").move_to(c + UP * (r * 0.72))

        # Center Spindle Hub & Counter Badge
        hub_base = Circle(radius=0.55, fill_color="#1E293B", fill_opacity=0.98, stroke_color="#F78908", stroke_width=2.0).move_to(c)
        hub_core = Circle(radius=0.35, fill_color="#0F172A", fill_opacity=1.0, stroke_color="#62B7E4", stroke_width=1.5).move_to(c)
        counter_lbl = CrispText("ITERATIVE\nPRA CORE", size=7.0, weight=BOLD, color="#FFFFFF").move_to(c)
        self.center_hub = VGroup(hub_base, hub_core, counter_lbl)

        # Banner badge below
        badge_box = RoundedRectangle(
            width=2.5, height=0.38, corner_radius=0.08,
            fill_color="#F8FAFC", fill_opacity=0.95,
            stroke_color="#CBD5E1", stroke_width=1.2
        ).move_to(c + DOWN * (r + 0.35))
        badge_txt = CrispText(self.cycle_label, size=8.5, weight=BOLD, color="#1E293B").move_to(badge_box)
        self.badge = VGroup(badge_box, badge_txt)

        self.add(self.outer_rim, self.inner_track, self.gear_ticks, self.flow_arcs, self.rotor, self.flow_dot, self.center_hub, self.badge)

    def _step_flywheel(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        c = self.center_pt
        r = self.radius * 0.72
        ang = np.pi / 2 - t * 0.75
        self.flow_dot.move_to(c + np.array([np.cos(ang) * r, np.sin(ang) * r, 0]))
        # Gentle tick rotation
        self.gear_ticks.rotate(0.08 * dt, about_point=c)


# -------------------------------------------------------------------------
# 18. VectorInfinityLoopBridge (Figure-8 Interaction Bridge)
# -------------------------------------------------------------------------
class VectorInfinityLoopBridge(VGroup):
    """
    Parametric figure-8 lemniscate loop bridging Agent and Environment domains,
    with designated waypoint milestones (Observe, Decide, Execute, Re-evaluate)
    and continuous traveling packet stream.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        width: float = 6.2,
        height: float = 2.4,
        left_title: str = "Agent Core",
        right_title: str = "Environment Grid",
        waypoints: list = None,
        enable_flow: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.w = float(width)
        self.h = float(height)
        self.left_title = left_title
        self.right_title = right_title
        self.waypoints = waypoints or [
            "1. Observe",
            "2. Decide",
            "3. Execute",
            "4. Re-evaluate"
        ]
        self.enable_flow = enable_flow
        self.time_tracker = ValueTracker(0.0)
        self._build_infinity_loop()
        if self.enable_flow:
            self.add_updater(lambda mob, dt: mob._step_infinity(dt))

    def _curve_point(self, t: float) -> np.ndarray:
        # Bernoulli Lemniscate parametric curve
        c = self.center_pt
        a = self.w * 0.44
        b = self.h * 0.48
        denom = 1.0 + np.sin(t) ** 2
        x = a * np.cos(t) / denom
        y = b * np.sin(t) * np.cos(t) / denom
        return c + np.array([x, y, 0])

    def _build_infinity_loop(self):
        c = self.center_pt

        # Domain Anchor Disks
        d_rad = 1.15
        left_c = c + LEFT * (self.w * 0.32)
        right_c = c + RIGHT * (self.w * 0.32)

        self.left_disk = Circle(
            radius=d_rad, fill_color="#F0F9FF", fill_opacity=0.85,
            stroke_color="#2C81FE", stroke_width=2.0
        ).move_to(left_c)
        self.right_disk = Circle(
            radius=d_rad, fill_color="#FFF7ED", fill_opacity=0.85,
            stroke_color="#E58F6D", stroke_width=2.0
        ).move_to(right_c)

        left_lbl = CrispText(self.left_title, size=11, weight=BOLD, color="#2C81FE").move_to(left_c + UP * 0.65)
        right_lbl = CrispText(self.right_title, size=11, weight=BOLD, color="#E58F6D").move_to(right_c + UP * 0.65)

        # Lemniscate Path Curve
        curve_pts = [self._curve_point(t) for t in np.linspace(0, 2 * np.pi, 120)]
        self.path_glow = VMobject(stroke_color="#62B7E4", stroke_width=4.0, stroke_opacity=0.4)
        self.path_glow.set_points_as_corners(curve_pts)

        self.path_core = VMobject(stroke_color="#2C81FE", stroke_width=2.2, stroke_opacity=0.95)
        self.path_core.set_points_as_corners(curve_pts)

        # 4 Waypoint Callout Pills along the curve
        t_vals = [0.25 * np.pi, 0.75 * np.pi, 1.25 * np.pi, 1.75 * np.pi]
        colors = ["#62B7E4", "#9B99C7", "#E58F6D", "#8ECDB7"]
        self.waypoint_mobs = VGroup()

        for idx, (lbl, t_val, col) in enumerate(zip(self.waypoints, t_vals, colors)):
            pt = self._curve_point(t_val)
            offset = UP * 0.42 if (idx % 2 == 0) else DOWN * 0.42
            box = RoundedRectangle(
                width=1.45, height=0.34, corner_radius=0.08,
                fill_color="#FFFFFF", fill_opacity=0.98,
                stroke_color=col, stroke_width=1.6
            ).move_to(pt + offset)
            txt = CrispText(lbl, size=8.5, weight=BOLD, color=col).move_to(box)
            dot = Dot(radius=0.08, color=col).move_to(pt)
            line = Line(pt, box.get_center(), stroke_color=col, stroke_width=1.2, stroke_opacity=0.6)
            self.waypoint_mobs.add(VGroup(dot, line, box, txt))

        # Traveling Data Packet Dots (3 dots in sequence)
        self.packets = VGroup(*[
            Dot(radius=0.09, color="#F78908") for _ in range(3)
        ])

        self.add(
            self.left_disk, self.right_disk, left_lbl, right_lbl,
            self.path_glow, self.path_core,
            self.waypoint_mobs, self.packets
        )

    def _step_infinity(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        for i, dot in enumerate(self.packets):
            param = (t * 0.85 + i * (2 * np.pi / 3)) % (2 * np.pi)
            dot.move_to(self._curve_point(param))


# -------------------------------------------------------------------------
# 19. VectorContextFunnel (Multi-Stage Ingestion Context Funnel)
# -------------------------------------------------------------------------
class VectorContextFunnel(VGroup):
    """
    3-Stage Tapered Ingestion Funnel aggregating multi-modal inputs
    (Telemetry, Prompts, Tools, Alerts) into a unified Working Context Buffer.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        input_items: list = None,
        buffer_label: str = "Working Context Buffer",
        accent_color: str = "#62B7E4",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = float(scale)
        self.input_items = input_items or [
            ("Telemetry", "#62B7E4"),
            ("User Query", "#9B99C7"),
            ("Tool Result", "#8ECDB7"),
            ("Alert Signal", "#E58F6D")
        ]
        self.buffer_label = buffer_label
        self.accent_color = accent_color
        self.time_tracker = ValueTracker(0.0)
        self._build_funnel()
        self.add_updater(lambda mob, dt: mob._step_funnel(dt))

    def _build_funnel(self):
        c = self.center_pt
        s = self.scale_factor

        # 1. Top Input Ports (4 intake slots)
        n_in = len(self.input_items)
        self.intake_nodes = VGroup()
        slot_w = 3.6 * s
        for i, (name, col) in enumerate(self.input_items):
            x_off = -slot_w / 2 + (i + 0.5) * (slot_w / n_in)
            pos = c + np.array([x_off, 1.4 * s, 0])
            pill = RoundedRectangle(
                width=0.82 * s, height=0.32 * s, corner_radius=0.06 * s,
                fill_color="#FFFFFF", fill_opacity=0.95,
                stroke_color=col, stroke_width=1.5 * s
            ).move_to(pos)
            txt = CrispText(name, size=7.5, weight=BOLD, color=col).move_to(pill)
            arrow = Arrow(pos + DOWN * 0.16 * s, pos + DOWN * 0.42 * s, buff=0, stroke_width=1.5 * s, max_tip_length_to_length_ratio=0.25, color=col)
            self.intake_nodes.add(VGroup(pill, txt, arrow))

        # 2. Funnel Body (Polygonal Tapered Shell)
        top_w = 4.0 * s
        bot_w = 1.4 * s
        top_y = 0.95 * s
        bot_y = -0.45 * s
        poly_pts = [
            c + np.array([-top_w / 2, top_y, 0]),
            c + np.array([top_w / 2, top_y, 0]),
            c + np.array([bot_w / 2, bot_y, 0]),
            c + np.array([-bot_w / 2, bot_y, 0])
        ]
        self.funnel_body = Polygon(
            *poly_pts,
            fill_color="#F8FAFC", fill_opacity=0.92,
            stroke_color=self.accent_color, stroke_width=2.2 * s
        )

        # Internal Filter Mesh lines
        self.filter_tiers = VGroup(
            Line(c + np.array([-1.5 * s, 0.5 * s, 0]), c + np.array([1.5 * s, 0.5 * s, 0]), stroke_color="#CBD5E1", stroke_width=1.4 * s, stroke_opacity=0.7),
            Line(c + np.array([-1.0 * s, 0.0 * s, 0]), c + np.array([1.0 * s, 0.0 * s, 0]), stroke_color="#CBD5E1", stroke_width=1.4 * s, stroke_opacity=0.7)
        )

        # Funnel Tier Labels
        lbl_ingest = CrispText("STAGE 1: INGESTION", size=6.5, weight=BOLD, color="#94A3B8").move_to(c + np.array([0, 0.72 * s, 0]))
        lbl_filter = CrispText("STAGE 2: FILTER & NORMALIZE", size=6.5, weight=BOLD, color="#94A3B8").move_to(c + np.array([0, 0.25 * s, 0]))

        # 3. Collection Reservoir Chamber (Bottom Buffer)
        res_box = RoundedRectangle(
            width=2.4 * s, height=0.55 * s, corner_radius=0.08 * s,
            fill_color="#FFFFFF", fill_opacity=0.98,
            stroke_color="#2C81FE", stroke_width=2.2 * s
        ).move_to(c + np.array([0, -0.85 * s, 0]))
        res_title = CrispText(self.buffer_label, size=9.0, weight=BOLD, color="#1E293B").move_to(res_box.get_center() + UP * 0.08 * s)
        res_sub = CrispText("Aggregated Token Context Window", size=6.8, weight=NORMAL, color="#64748B").move_to(res_box.get_center() + DOWN * 0.12 * s)
        self.reservoir = VGroup(res_box, res_title, res_sub)

        # Traveling particles trickling into reservoir
        self.trickle_dots = VGroup(*[
            Dot(radius=0.06 * s, color=self.accent_color) for _ in range(4)
        ])

        self.add(
            self.intake_nodes, self.funnel_body, self.filter_tiers,
            lbl_ingest, lbl_filter, self.reservoir, self.trickle_dots
        )

    def _step_funnel(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        c = self.center_pt
        s = self.scale_factor
        for i, dot in enumerate(self.trickle_dots):
            progress = (t * 0.9 + i * 0.25) % 1.0
            y = (0.8 - progress * 1.4) * s
            x_spread = (1.0 - progress) * (np.sin(t * 3.0 + i) * 0.6 * s)
            dot.move_to(c + np.array([x_spread, y, 0]))


# -------------------------------------------------------------------------
# 20. VectorQuadChamberCore (Unified Quad-Chamber Architecture Engine Core)
# -------------------------------------------------------------------------
class VectorQuadChamberCore(VGroup):
    """
    Expansive 4-Chamber AI Agent Architecture Engine Core designed for
    full-canvas screen utilization (Layout 20).
    Chambers:
      - Top-Left: Perception Layer (#62B7E4)
      - Bottom-Left: Memory Layer (#E58F6D / Amber #DDB945)
      - Top-Right: Reasoning Core (#9B99C7)
      - Bottom-Right: Action Layer (#8ECDB7)
    Surrounds a central cognitive nexus hub with continuous orbital ring.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        width: float = 9.8,
        height: float = 4.6,
        enable_pulse: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.w = float(width)
        self.h = float(height)
        self.enable_pulse = enable_pulse
        self.time_tracker = ValueTracker(0.0)
        self._build_quad_core()
        if self.enable_pulse:
            self.add_updater(lambda mob, dt: mob._step_quad(dt))

    def _build_quad_core(self):
        c = self.center_pt
        dx = self.w * 0.28
        dy = self.h * 0.28

        # Center Cognitive Hub
        hub_outer = Circle(radius=0.90, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#2C81FE", stroke_width=2.5).move_to(c)
        hub_inner = Circle(radius=0.72, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#CBD5E1", stroke_width=1.5).move_to(c)
        hub_title = CrispText("AGENT CORE", size=10.5, weight=BOLD, color="#1E293B").move_to(c + UP * 0.12)
        hub_sub = CrispText("Cognitive Loop", size=7.5, weight=NORMAL, color="#64748B").move_to(c + DOWN * 0.14)
        self.hub = VGroup(hub_outer, hub_inner, hub_title, hub_sub)

        # 4 Quadrants
        card_w = 3.6
        card_h = 1.6
        q_configs = [
            ("Perception Layer", "#62B7E4", c + np.array([-dx, dy, 0]), "Telemetry, Queries & Signals"),
            ("Memory Layer", "#E58F6D", c + np.array([-dx, -dy, 0]), "Short-Term RAM + Vector Store"),
            ("Reasoning Engine", "#9B99C7", c + np.array([dx, dy, 0]), "LLM Decision & Tool Planner"),
            ("Action Layer", "#8ECDB7", c + np.array([dx, -dy, 0]), "API, SQL, Alerts & Files")
        ]

        self.quadrant_cards = VGroup()
        for title, col, pos, sub in q_configs:
            box = RoundedRectangle(
                width=card_w, height=card_h, corner_radius=0.10,
                fill_color="#FFFFFF", fill_opacity=0.98,
                stroke_color=col, stroke_width=2.2
            ).move_to(pos)
            badge = RoundedRectangle(
                width=card_w * 0.75, height=0.34, corner_radius=0.06,
                fill_color=col, fill_opacity=0.15,
                stroke_color=col, stroke_width=1.2
            ).move_to(pos + UP * 0.48)
            b_txt = CrispText(title, size=9.5, weight=BOLD, color=col).move_to(badge)
            s_txt = CrispText(sub, size=8.0, weight=NORMAL, color="#475569").move_to(pos + DOWN * 0.20)
            self.quadrant_cards.add(VGroup(box, badge, b_txt, s_txt))

        # Connecting Bus Conduits from Hub to Quadrants
        self.conduits = VGroup()
        for _, col, pos, _ in q_configs:
            line = Line(c, pos, stroke_color=col, stroke_width=2.0, stroke_opacity=0.5)
            self.conduits.add(line)

        # Orbital Clockwise Synchronization Ring
        self.orbital_ring = Circle(radius=np.sqrt(dx**2 + dy**2) * 0.95, stroke_color="#F78908", stroke_width=2.2, stroke_opacity=0.85).move_to(c)

        # Orbital traveling pulse dot
        self.orbital_pulse = Dot(radius=0.11, color="#F78908").move_to(c + UP * (dy * 1.3))

        self.add(self.conduits, self.orbital_ring, self.quadrant_cards, self.hub, self.orbital_pulse)

    def _step_quad(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        c = self.center_pt
        dx = self.w * 0.28
        dy = self.h * 0.28
        rad = np.sqrt(dx**2 + dy**2) * 0.95
        ang = np.pi / 2 - t * 0.9
        self.orbital_pulse.move_to(c + np.array([np.cos(ang) * rad, np.sin(ang) * rad, 0]))




# -------------------------------------------------------------------------
# 19. VectorKPIGaugeCard (Executive KPI & Metric Dial Card)
# -------------------------------------------------------------------------
class VectorKPIGaugeCard(VGroup):
    """
    Executive performance metric card featuring a precision semi-circular gauge dial,
    dynamic needle indicator, prominent KPI readout, and target benchmark pill.
    Zero navy blue, zero green card containers - strictly adheres to OSL 3.0.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        title: str = "Portfolio ROI",
        metric_value: str = "+24.8%",
        subtext: str = "vs. Q3 Projected Baseline",
        target_pct: float = 0.78,  # 0.0 to 1.0 on semicircular dial
        accent_color: str = "#2C81FE",
        card_bg: str = "#F8FAFC",
        border_color: str = "#E2E8F0",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.title_str = title
        self.metric_str = metric_value
        self.subtext_str = subtext
        self.target_pct = np.clip(target_pct, 0.0, 1.0)
        self.accent_color = accent_color
        self.card_bg = card_bg
        self.border_color = border_color
        self.time_tracker = ValueTracker(0.0)
        self._build_kpi_card()
        self.add_updater(lambda mob, dt: mob._step_gauge(dt))

    def _build_kpi_card(self):
        c = self.center_pt
        s = self.scale_factor

        cw, ch = 3.6 * s, 3.8 * s
        # Background card with 10px rounded corners
        self.card = RoundedRectangle(
            width=cw, height=ch, corner_radius=0.12 * s,
            fill_color=self.card_bg, fill_opacity=0.95,
            stroke_color=self.border_color, stroke_width=1.5 * s
        ).move_to(c)

        # Title badge pill
        self.title_pill = RoundedRectangle(
            width=2.4 * s, height=0.36 * s, corner_radius=0.08 * s,
            fill_color=self.accent_color, fill_opacity=0.15,
            stroke_color=self.accent_color, stroke_width=1.2 * s
        ).move_to(c + UP * (ch/2 - 0.35 * s))
        self.title_txt = CrispText(self.title_str, size=9.5, weight=BOLD, color="#1E293B").move_to(self.title_pill)

        # Semicircular Gauge Track
        dial_center = c + UP * 0.25 * s
        dial_r = 1.0 * s
        self.dial_center = dial_center
        self.dial_r = dial_r

        # Background track arc (180 degrees from PI to 0)
        self.track_arc = Arc(
            radius=dial_r, start_angle=PI, angle=-PI,
            stroke_color="#E2E8F0", stroke_width=5.0 * s, arc_center=dial_center
        )

        # Active progress arc
        prog_angle = -PI * self.target_pct
        self.active_arc = Arc(
            radius=dial_r, start_angle=PI, angle=prog_angle,
            stroke_color=self.accent_color, stroke_width=5.5 * s, arc_center=dial_center
        )

        # Needle indicator line
        needle_ang = PI + prog_angle
        needle_end = dial_center + np.array([np.cos(needle_ang) * (dial_r * 0.85), np.sin(needle_ang) * (dial_r * 0.85), 0])
        self.needle = Line(dial_center, needle_end, stroke_color="#F78908", stroke_width=2.5 * s)
        self.needle_hub = Dot(dial_center, radius=0.08 * s, color="#1E293B")

        # Metric numerical readout
        self.metric_label = CrispText(self.metric_str, size=20, weight=BOLD, color="#0F172A").move_to(dial_center + DOWN * 0.6 * s)

        # Subtext / comparison benchmark
        self.subtext_label = CrispText(self.subtext_str, size=8.5, weight="NORMAL", color="#64748B").move_to(c + DOWN * (ch/2 - 0.35 * s))

        # Focus highlight pulse border (idle by default)
        self.highlight_box = self.card.copy().set_fill(opacity=0).set_stroke(color="#F78908", width=3.5 * s, opacity=0)

        self.add(
            self.card, self.title_pill, self.title_txt,
            self.track_arc, self.active_arc, self.needle, self.needle_hub,
            self.metric_label, self.subtext_label, self.highlight_box
        )

    def _step_gauge(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        # Subtle breathing needle oscillation (+- 0.02 rad)
        osc = np.sin(t * 2.2) * 0.025
        base_ang = PI * (1.0 - self.target_pct)
        cur_ang = base_ang + osc
        r = self.dial_r * 0.85
        n_end = self.dial_center + np.array([-np.cos(cur_ang) * r, np.sin(cur_ang) * r, 0])
        self.needle.put_start_and_end_on(self.dial_center, n_end)


# -------------------------------------------------------------------------
# 20. VectorRiskHeatmap (Enterprise Risk Severity & Compliance Grid)
# -------------------------------------------------------------------------
class VectorRiskHeatmap(VGroup):
    """
    3x3 enterprise risk severity matrix (Impact vs. Likelihood).
    Features pastel color-coded risk bands (Low/Medium/High/Critical),
    coordinate grid axes, and animated risk token callouts.
    Strictly complies with OSL 3.0: zero navy blue, pure white/slate backgrounds.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        x_label: str = "Likelihood",
        y_label: str = "Impact",
        risk_tokens: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.x_label = x_label
        self.y_label = y_label
        self.risk_tokens_data = risk_tokens or [
            {"row": 2, "col": 2, "label": "R1: Model Drift", "color": "#E58F6D"},
            {"row": 1, "col": 0, "label": "R2: Latency Spike", "color": "#DDB945"},
            {"row": 0, "col": 1, "label": "R3: Data Gap", "color": "#8ECDB7"}
        ]
        self.time_tracker = ValueTracker(0.0)
        self._build_heatmap()
        self.add_updater(lambda mob, dt: mob._step_heatmap(dt))

    def _build_heatmap(self):
        c = self.center_pt
        s = self.scale_factor
        cell_w, cell_h = 1.35 * s, 0.95 * s
        r = 0.06 * s

        # 3x3 Heatmap colors: row 0=Low, 1=Med, 2=High; col 0=Low, 1=Med, 2=High
        # Low=Mint (#8ECDB7, 0.25), Med=Amber (#E6A157, 0.25), High=Coral (#E58F6D, 0.35)
        color_matrix = [
            ["#8ECDB7", "#8ECDB7", "#DDB945"],  # Impact Low
            ["#8ECDB7", "#DDB945", "#E6A157"],  # Impact Med
            ["#DDB945", "#E6A157", "#E58F6D"]   # Impact High
        ]

        self.cells = []
        self.cell_centers = {}

        grid_orig_x = c[0] - (1.5 * cell_w)
        grid_orig_y = c[1] - (1.5 * cell_h)

        for row in range(3):
            for col in range(3):
                x = grid_orig_x + (col + 0.5) * cell_w
                y = grid_orig_y + (row + 0.5) * cell_h
                col_hex = color_matrix[row][col]
                cell = RoundedRectangle(
                    width=cell_w - 0.05*s, height=cell_h - 0.05*s, corner_radius=r,
                    fill_color=col_hex, fill_opacity=0.30,
                    stroke_color=col_hex, stroke_width=1.2 * s
                ).move_to([x, y, 0])
                self.cells.append(cell)
                self.cell_centers[(row, col)] = np.array([x, y, 0])

        # Axes labels
        self.x_axis_txt = CrispText(f"{self.x_label} (Low -> High)", size=9, weight=BOLD, color="#404040").move_to(c + DOWN * (1.65 * cell_h))
        self.y_axis_txt = CrispText(f"{self.y_label} (Low -> High)", size=9, weight=BOLD, color="#404040").move_to(c + LEFT * (1.8 * cell_w)).rotate(PI / 2)

        # Risk item tokens
        self.tokens_group = VGroup()
        self.token_dots = []
        for item in self.risk_tokens_data:
            r_idx, c_idx = item.get("row", 0), item.get("col", 0)
            target_pt = self.cell_centers.get((r_idx, c_idx), c)
            lbl_str = item.get("label", "Risk")
            col_tok = item.get("color", "#F78908")

            badge = RoundedRectangle(
                width=1.05 * s, height=0.28 * s, corner_radius=0.06 * s,
                fill_color=col_tok, fill_opacity=0.95,
                stroke_color="#FFFFFF", stroke_width=1.0 * s
            ).move_to(target_pt)
            txt = CrispText(lbl_str, size=7.5, weight=BOLD, color="#FFFFFF").move_to(badge)
            dot = Dot(target_pt + LEFT * 0.45 * s, radius=0.04 * s, color="#FFFFFF")
            self.token_dots.append(badge)
            self.tokens_group.add(VGroup(badge, txt, dot))

        # Critical attention pulse ring around top-right high risk cell
        crit_center = self.cell_centers[(2, 2)]
        self.crit_pulse = RoundedRectangle(
            width=cell_w + 0.04*s, height=cell_h + 0.04*s, corner_radius=r,
            fill_color="#E58F6D", fill_opacity=0,
            stroke_color="#F78908", stroke_width=2.5 * s
        ).move_to(crit_center)

        self.add(*self.cells, self.x_axis_txt, self.y_axis_txt, self.tokens_group, self.crit_pulse)

    def _step_heatmap(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        # Pulsing opacity on the critical risk cell
        pulse_op = 0.35 + 0.35 * np.sin(t * 3.0)
        self.crit_pulse.set_stroke(opacity=pulse_op)


# -------------------------------------------------------------------------
# 21. VectorRACIMatrix (Project Governance & Role Responsibility Table)
# -------------------------------------------------------------------------
class VectorRACIMatrix(VGroup):
    """
    RACI (Responsible, Accountable, Consulted, Informed) governance matrix table.
    Renders clean rounded horizontal rows, functional role headers, and
    color-coded RACI badges adhering strictly to Open Sans and the OSL 3.0 palette.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        roles: Optional[List[str]] = None,
        tasks: Optional[List[Dict[str, Any]]] = None,
        card_bg: str = "#F8FAFC",
        border_color: str = "#E2E8F0",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.roles_list = roles or ["Product", "Eng", "Data", "Security"]
        self.tasks_data = tasks or [
            {"task": "Model Architecture", "raci": ["C", "A", "R", "I"]},
            {"task": "Data Pipeline Sync", "raci": ["I", "C", "R", "C"]},
            {"task": "Production Release", "raci": ["A", "R", "C", "A"]}
        ]
        self.card_bg = card_bg
        self.border_color = border_color
        self.time_tracker = ValueTracker(0.0)
        self._build_raci()
        self.add_updater(lambda mob, dt: mob._step_raci(dt))

    def _build_raci(self):
        c = self.center_pt
        s = self.scale_factor

        num_roles = len(self.roles_list)
        num_tasks = len(self.tasks_data)

        table_w = 6.4 * s
        task_col_w = 2.4 * s
        role_col_w = (table_w - task_col_w) / max(1, num_roles)
        row_h = 0.52 * s
        gap_y = 0.08 * s

        total_h = (num_tasks + 1) * (row_h + gap_y)
        top_y = c[1] + (total_h / 2) - (row_h / 2)

        # RACI badge colors: R=Mint (#8ECDB7), A=Amber (#E6A157), C=Sky (#62B7E4), I=Lilac (#C1A5C6)
        raci_colors = {
            "R": "#8ECDB7",  # Responsible
            "A": "#E6A157",  # Accountable
            "C": "#62B7E4",  # Consulted
            "I": "#C1A5C6"   # Informed
        }

        # Header Row
        header_bar = RoundedRectangle(
            width=table_w, height=row_h, corner_radius=0.08 * s,
            fill_color="#1E293B", fill_opacity=0.95,
            stroke_color="#1E293B", stroke_width=1.0 * s
        ).move_to([c[0], top_y, 0])

        task_hdr = CrispText("Deliverable / Task", size=9.5, weight=BOLD, color="#FFFFFF").move_to(
            [c[0] - (table_w/2) + (task_col_w/2), top_y, 0]
        )

        role_hdrs = []
        for i, r_name in enumerate(self.roles_list):
            rx = c[0] - (table_w/2) + task_col_w + (i + 0.5) * role_col_w
            rtxt = CrispText(r_name, size=9.5, weight=BOLD, color="#FFFFFF").move_to([rx, top_y, 0])
            role_hdrs.append(rtxt)

        self.rows = []
        for row_idx, t_item in enumerate(self.tasks_data):
            ry = top_y - (row_idx + 1) * (row_h + gap_y)
            row_bg = RoundedRectangle(
                width=table_w, height=row_h, corner_radius=0.06 * s,
                fill_color=self.card_bg, fill_opacity=0.90,
                stroke_color=self.border_color, stroke_width=1.0 * s
            ).move_to([c[0], ry, 0])

            t_name = t_item.get("task", f"Task {row_idx+1}")
            t_txt = CrispText(t_name, size=9, weight=BOLD, color="#1E293B").move_to(
                [c[0] - (table_w/2) + (task_col_w/2), ry, 0]
            )

            badges = []
            raci_vals = t_item.get("raci", [])
            for col_idx in range(num_roles):
                val = raci_vals[col_idx] if col_idx < len(raci_vals) else "-"
                rx = c[0] - (table_w/2) + task_col_w + (col_idx + 0.5) * role_col_w
                b_color = raci_colors.get(val, "#94A3B8")

                pill = RoundedRectangle(
                    width=0.42 * s, height=0.32 * s, corner_radius=0.06 * s,
                    fill_color=b_color, fill_opacity=0.90,
                    stroke_color="#FFFFFF", stroke_width=1.0 * s
                ).move_to([rx, ry, 0])
                p_txt = CrispText(val, size=9, weight=BOLD, color="#FFFFFF").move_to(pill)
                badges.append(VGroup(pill, p_txt))

            self.rows.append(VGroup(row_bg, t_txt, *badges))

        # Active row highlight ring
        self.active_row_highlight = RoundedRectangle(
            width=table_w + 0.04*s, height=row_h + 0.04*s, corner_radius=0.08 * s,
            fill_color="#F78908", fill_opacity=0,
            stroke_color="#F78908", stroke_width=2.5 * s
        ).move_to(self.rows[0][0].get_center())

        self.add(header_bar, task_hdr, *role_hdrs, *self.rows, self.active_row_highlight)

    def _step_raci(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        # Scan through rows every 2 seconds
        num_tasks = len(self.tasks_data)
        if num_tasks > 0:
            active_idx = int((t / 2.0) % num_tasks)
            target_center = self.rows[active_idx][0].get_center()
            self.active_row_highlight.move_to(target_center)



# -------------------------------------------------------------------------
# 22. VectorMechanicalHammerTool (Passive Static Tool Asset)
# -------------------------------------------------------------------------
class VectorMechanicalHammerTool(VGroup):
    """
    Editorial 2D vector mechanical hammer / static tool card apparatus.
    Contrasts a passive inanimate tool against an autonomous agent.
    Features:
    - Dedicated clean card container matching Manim node architectures.
    - Top header: Bold high-contrast title.
    - Precision hammer illustration: Teak/honey wood shaft, rubber grip ribs,
      metallic ferrule collar, forged steel eye, beveled face, and curved claw.
    - Status badge pill: 'Idle / Waiting' with active amber indicator LED.
    - OSL 3.0 brand compliance: Pure white card, dark slate text, amber accents.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        label: str = "Static Tool",
        subtext: str = "Idle / Waiting",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.label_str = label
        self.subtext_str = subtext
        self.time_tracker = ValueTracker(0.0)
        self._build_tool()
        self.add_updater(lambda mob, dt: mob._step_tool(dt))

    def _build_tool(self):
        c = self.center_pt
        s = self.scale_factor

        # 1. Main Card Container (Matches standard node proportions)
        card_w = 2.40 * s
        card_h = 2.30 * s
        self.card = RoundedRectangle(
            width=card_w, height=card_h, corner_radius=0.12 * s,
            fill_color="#FFFFFF", fill_opacity=0.98,
            stroke_color="#CBD5E1", stroke_width=1.8 * s
        ).move_to(c)

        # 2. Card Header Title
        fs_title = max(8.0, 12.0 * s)
        self.title_txt = Text(
            self.label_str, font="Open Sans", font_size=fs_title, weight="BOLD", color="#1E293B"
        ).move_to(c + UP * (0.80 * s))

        # 3. Precision Hammer Vector Assembly (Resting at -25 degrees)
        hammer_grp = VGroup()
        hammer_center = c + DOWN * (0.05 * s)
        ang = -25 * DEGREES

        # Wood handle shaft (Warm teak finish)
        handle_len = 1.25 * s
        handle_w = 0.16 * s
        handle = RoundedRectangle(
            width=handle_len, height=handle_w, corner_radius=0.04 * s,
            fill_color="#C27827", fill_opacity=1.0,
            stroke_color="#783D08", stroke_width=1.0 * s
        ).move_to(hammer_center + np.array([-0.10 * s, -0.15 * s, 0])).rotate(ang)

        # Grip grooves (Dark rubber ribs)
        grip_ribs = VGroup()
        for i in range(4):
            dx = -0.40 * s + i * 0.12 * s
            rib = RoundedRectangle(
                width=0.045 * s, height=handle_w + 0.03 * s, corner_radius=0.015 * s,
                fill_color="#783D08", fill_opacity=0.85, stroke_width=0
            ).move_to(hammer_center + np.array([-0.10 * s + dx * np.cos(ang), -0.15 * s + dx * np.sin(ang), 0])).rotate(ang)
            grip_ribs.add(rib)

        # Metallic collar / ferrule
        collar = RoundedRectangle(
            width=0.14 * s, height=handle_w + 0.06 * s, corner_radius=0.02 * s,
            fill_color="#94A3B8", fill_opacity=1.0,
            stroke_color="#64748B", stroke_width=0.8 * s
        ).move_to(hammer_center + np.array([0.38 * s * np.cos(ang), 0.38 * s * np.sin(ang), 0])).rotate(ang)

        # Hammer head (Forged steel block)
        head_pos = hammer_center + np.array([0.62 * s * np.cos(ang), 0.62 * s * np.sin(ang), 0])
        head_eye = RoundedRectangle(
            width=0.36 * s, height=0.38 * s, corner_radius=0.04 * s,
            fill_color="#334155", fill_opacity=1.0,
            stroke_color="#1E293B", stroke_width=1.0 * s
        ).move_to(head_pos).rotate(ang)

        # Beveled striking face
        striking_face = Polygon(
            head_pos + np.array([0.14 * s, 0.15 * s, 0]),
            head_pos + np.array([0.36 * s, 0.11 * s, 0]),
            head_pos + np.array([0.36 * s, -0.11 * s, 0]),
            head_pos + np.array([0.14 * s, -0.15 * s, 0]),
            fill_color="#E2E8F0", fill_opacity=1.0,
            stroke_color="#64748B", stroke_width=1.0 * s
        ).rotate(ang, about_point=head_pos)

        # Curved claw
        claw = Polygon(
            head_pos + np.array([-0.14 * s, 0.14 * s, 0]),
            head_pos + np.array([-0.36 * s, 0.22 * s, 0]),
            head_pos + np.array([-0.32 * s, 0.04 * s, 0]),
            head_pos + np.array([-0.14 * s, -0.08 * s, 0]),
            fill_color="#475569", fill_opacity=1.0,
            stroke_color="#1E293B", stroke_width=1.0 * s
        ).rotate(ang, about_point=head_pos)

        # Brass wedge pin
        wedge = Dot(head_pos, radius=0.035 * s, color="#F59E0B")

        hammer_grp.add(handle, grip_ribs, collar, claw, striking_face, head_eye, wedge)

        # 4. Bottom Status Badge Pill
        pill_w = 1.85 * s
        pill_h = 0.36 * s
        self.status_pill = RoundedRectangle(
            width=pill_w, height=pill_h, corner_radius=0.08 * s,
            fill_color="#F1F5F9", fill_opacity=0.95,
            stroke_color="#E2E8F0", stroke_width=1.0 * s
        ).move_to(c + DOWN * (0.80 * s))

        self.dormant_dot = Dot(self.status_pill.get_left() + RIGHT * (0.22 * s), radius=0.05 * s, color="#F59E0B")
        fs_sub = max(7.0, 9.5 * s)
        self.status_txt = Text(
            self.subtext_str, font="Open Sans", font_size=fs_sub, weight="BOLD", color="#64748B"
        ).next_to(self.dormant_dot, RIGHT, buff=0.10 * s)

        self.add(self.card, self.title_txt, hammer_grp, self.status_pill, self.dormant_dot, self.status_txt)

    def _step_tool(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        # Gentle breathing pulse on amber LED
        p = 0.50 + 0.45 * np.sin(t * 2.5)
        self.dormant_dot.set_opacity(p)

print('VectorMechanicalHammerTool defined successfully!')


# -------------------------------------------------------------------------
# 23. VectorAdvancedSolarArray (High-Fidelity Photovoltaic Array)
# -------------------------------------------------------------------------
class VectorAdvancedSolarArray(VGroup):
    """
    Broadcast-Quality 2.5D Photovoltaic Solar Array & Grid Inverter Hub.
    Features:
    - Dual axonometric photovoltaic wings angled at 25 degrees.
    - 3x2 silicon wafer segmentation with silver micro-busbars per panel.
    - Continuous diagonal glass glare shimmer reflection sweep across panels.
    - Industrial aluminum truss frame and dual-axis solar tracking gimbal.
    - Power generation status pill with live green/mint telemetry pulse.
    - Clean OSL 3.0 color compliance: Deep Slate, Sky Blue, Steel Blue, Mint.
    """
    def __init__(
        self,
        center: np.ndarray = ORIGIN,
        scale: float = 1.0,
        output_kw: str = "450 kW",
        efficiency: str = "98.4%",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.center_pt = np.array(center, dtype=float)
        self.scale_factor = scale
        self.output_str = output_kw
        self.eff_str = efficiency
        self.time_tracker = ValueTracker(0.0)
        self._build_solar_hub()
        self.add_updater(lambda mob, dt: mob._step_solar(dt))

    def _build_solar_hub(self):
        c = self.center_pt
        s = self.scale_factor

        # Ground contact shadow
        shadow = Ellipse(
            width=3.6 * s, height=0.45 * s,
            fill_color="#CBD5E1", fill_opacity=0.45, stroke_width=0
        ).move_to(c + DOWN * 1.15 * s)

        # Dual-axis tracking gimbal mount & aluminum tripod trusses
        gimbal_post = Line(c + DOWN * 1.1 * s, c + DOWN * 0.1 * s, color="#475569", stroke_width=4.0 * s)
        truss_l = Line(c + DOWN * 1.1 * s + LEFT * 0.8 * s, c + DOWN * 0.25 * s, color="#64748B", stroke_width=2.5 * s)
        truss_r = Line(c + DOWN * 1.1 * s + RIGHT * 0.8 * s, c + DOWN * 0.25 * s, color="#64748B", stroke_width=2.5 * s)
        pivot_hub = Dot(c + DOWN * 0.1 * s, radius=0.12 * s, color="#1E293B")
        pivot_ring = Circle(radius=0.18 * s, stroke_color="#62B7E4", stroke_width=1.5 * s).move_to(pivot_hub)

        # Photovoltaic Panel Array (2 angled wings: Left and Right)
        self.panel_surfaces = []
        panels_grp = VGroup()

        pw, ph = 1.45 * s, 1.1 * s
        for side, dx in [("L", -0.85 * s), ("R", 0.85 * s)]:
            p_center = c + np.array([dx, 0.45 * s, 0])
            # Outer aluminum frame
            frame = RoundedRectangle(
                width=pw, height=ph, corner_radius=0.06 * s,
                fill_color="#0F172A", fill_opacity=0.98,
                stroke_color="#2C81FE", stroke_width=1.8 * s
            ).move_to(p_center)
            self.panel_surfaces.append(frame)

            # 3x2 silicon wafer cells
            cells = VGroup()
            cw, ch = (pw - 0.12 * s) / 2, (ph - 0.14 * s) / 3
            for col in range(2):
                for row in range(3):
                    cx_val = p_center[0] - (pw/2) + 0.06*s + (col + 0.5) * cw
                    cy_val = p_center[1] - (ph/2) + 0.07*s + (row + 0.5) * ch
                    cell_rect = RoundedRectangle(
                        width=cw - 0.03*s, height=ch - 0.03*s, corner_radius=0.02*s,
                        fill_color="#1E293B", fill_opacity=0.90,
                        stroke_color="#62B7E4", stroke_width=0.8 * s
                    ).move_to([cx_val, cy_val, 0])
                    # Silver busbar lines
                    busbar = Line(
                        [cx_val, cy_val - ch*0.4, 0], [cx_val, cy_val + ch*0.4, 0],
                        color="#7EA2C8", stroke_width=0.8 * s
                    )
                    cells.add(cell_rect, busbar)

            panels_grp.add(frame, cells)

        # Glass glare reflection sweep polygon
        self.glare_polygon = Polygon(
            c + np.array([-1.5 * s, 0.9 * s, 0]),
            c + np.array([-1.1 * s, 0.9 * s, 0]),
            c + np.array([-1.7 * s, 0.0, 0]),
            c + np.array([-2.1 * s, 0.0, 0]),
            fill_color="#FFFFFF", fill_opacity=0.22, stroke_width=0
        )

        # Inverter Telemetry Status Badge
        self.inverter_badge = RoundedRectangle(
            width=2.8 * s, height=0.38 * s, corner_radius=0.08 * s,
            fill_color="#F8FAFC", fill_opacity=0.95,
            stroke_color="#E2E8F0", stroke_width=1.2 * s
        ).move_to(c + DOWN * 0.75 * s)

        self.telemetry_led = Dot(self.inverter_badge.get_left() + RIGHT * 0.22 * s, radius=0.06 * s, color="#8ECDB7")
        self.inverter_txt = Text(
            f"PV Solar Inverter: {self.output_str}  •  {self.eff_str}",
            font="Open Sans", font_size=8.5 * s, weight="SEMIBOLD", color="#1E293B"
        ).next_to(self.telemetry_led, RIGHT, buff=0.12 * s)

        # Energy absorption halo dot on top
        self.solar_core_beacon = Dot(c + UP * 1.15 * s, radius=0.08 * s, color="#F0C265")

        self.add(
            shadow, gimbal_post, truss_l, truss_r, pivot_hub, pivot_ring,
            panels_grp, self.glare_polygon,
            self.inverter_badge, self.telemetry_led, self.inverter_txt,
            self.solar_core_beacon
        )

    def _step_solar(self, dt: float):
        t = self.time_tracker.get_value() + dt
        self.time_tracker.set_value(t)
        s = self.scale_factor
        c = self.center_pt

        # Glare sweep across panels every 3.5 seconds
        cycle_t = (t % 3.5) / 3.5
        glare_x = c[0] - 1.8 * s + cycle_t * 3.6 * s
        self.glare_polygon.move_to([glare_x, c[1] + 0.45 * s, 0])
        self.glare_polygon.set_opacity(0.18 * np.sin(cycle_t * PI))

        # Inverter LED pulse
        pulse = 0.4 + 0.6 * abs(np.sin(t * 3.0))
        self.telemetry_led.set_opacity(pulse)

print('VectorAdvancedSolarArray defined successfully!')
