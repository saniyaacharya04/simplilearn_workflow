"""
template1_title_intro.py — Simplilearn OSL 3.0 Title / Intro Section Template
=============================================================================
Reusable Manim programmatic template for the Course & Topic Title Splash Screen.
Adheres strictly to Simplilearn Learning Design & OSL 3.0 Video Guidelines:
- Canvas: Full HD 1920x1080 (16:9 widescreen)
- Typography: Open Sans Bold (#FFFFFF, 45px standard scale per guidelines)
- Color: Brand Blue (#0B63E5 / #0062FF to #2563EB gradient)
- Geometry: Centered pill/capsule banner with left circular icon disc
- Standards: Chicago Title Case, concise 5-7 words, no all-caps, US English

Usage:
------
from template1_title_intro import play_title_intro, create_title_intro_mobject

class MyScene(Scene):
    def construct(self):
        play_title_intro(
            self,
            topic_title="Basic Prompting Techniques",
            course_name="Generative AI Essentials",  # optional subtitle
            duration=3.0,
        )

Command-line test render:
-------------------------
py -3.10 -m manim -pql template1_title_intro.py TitleIntroScene
"""

from __future__ import annotations
import os
from typing import Optional, Union
from manim import *
import manimpango


def get_simplilearn_font(preferred: str = "Open Sans") -> str:
    """
    Returns preferred font if installed in OS font registry, else falls
    back gracefully to an available clean system sans (e.g. Segoe UI, Arial)
    to prevent Manim runtime warnings while strictly honoring design specs.
    """
    try:
        available = manimpango.list_fonts()
        if preferred in available:
            return preferred
        for fallback in ["Open Sans", "Segoe UI", "Arial", "Sans"]:
            if fallback in available:
                return fallback
    except Exception:
        pass
    return "Sans"


def CrispText(text, size=24, font="Open Sans", **kwargs):
    """
    High-fidelity typography renderer providing consistent letter spacing,
    crisp glyph outlines, and automatic word wrapping via 4x supersampling.
    """
    if "font_size" in kwargs:
        size = kwargs.pop("font_size")
    try:
        size = float(size)
    except (ValueError, TypeError):
        size = 24.0
    if 0.0 < size <= 1.0:
        if size >= 0.28:
            size = 26.0
        elif size >= 0.19:
            size = 18.0
        elif size >= 0.14:
            size = 14.0
        else:
            size = 12.0
    elif size < 10.0:
        size = 12.0
    align = kwargs.pop("align", "center")
    kwargs.pop("alignment", None)
    slant_val = kwargs.pop("slant", NORMAL)
    weight_val = kwargs.pop("weight", NORMAL)
    if isinstance(weight_val, str):
        weight_val = weight_val.upper()
        if weight_val == "REGULAR":
            weight_val = "NORMAL"
    color_val = kwargs.pop("color", None)
    if color_val is None:
        color_val = globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))
    elif str(color_val).upper() in ("#F9C72C", "C_YELLOW", "YELLOW", "#FFF9E6", "#FFFF00"):
        color_val = globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))
    raw_str = str(text)
    NL = chr(10)
    split_lines = [l for l in raw_str.split(NL)] if NL in raw_str else ([l for l in raw_str.split(r"\n")] if r"\n" in raw_str else None)
    if split_lines is None:
        if len(raw_str) > 36 and " " in raw_str and size <= 18:
            words = raw_str.split()
            lines = []
            curr_line = []
            curr_len = 0
            for w in words:
                if curr_len + len(w) + 1 > 32:
                    lines.append(" ".join(curr_line))
                    curr_line = [w]
                    curr_len = len(w)
                else:
                    curr_line.append(w)
                    curr_len += len(w) + 1
            if curr_line:
                lines.append(" ".join(curr_line))
            split_lines = lines
        else:
            split_lines = [raw_str]
    if len(split_lines) > 1:
        line_mobs = [Text(l, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **kwargs) for l in split_lines]
        aligned_edge = ORIGIN if align == "center" else (LEFT if align == "left" else RIGHT)
        mob = VGroup(*line_mobs).arrange(DOWN, buff=0.18, aligned_edge=aligned_edge).scale(0.25)
    else:
        mob = Text(raw_str, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **kwargs).scale(0.25)
    orig_scale = mob.scale_to_fit_width
    def safe_scale_width(tw):
        if hasattr(mob, "width") and mob.width > 0:
            ratio = tw / mob.width
            if ratio < 0.85: ratio = 0.85
            return mob.scale(ratio)
        return orig_scale(tw)
    mob.scale_to_fit_width = safe_scale_width
    return mob


def create_analytics_icon(scale: float = 0.85) -> VGroup:
    """
    Constructs a crisp vector desktop monitor icon with an embedded bar chart
    and metric circle, reproducing the visual badge in the reference video.
    """
    # Monitor frame
    monitor = RoundedRectangle(
        width=0.68,
        height=0.46,
        corner_radius=0.06,
        stroke_color=WHITE,
        stroke_width=2.5,
        fill_opacity=0.0,
    )

    # Monitor stand neck & base plate
    neck = Line(DOWN * 0.23, DOWN * 0.32, stroke_color=WHITE, stroke_width=2.5)
    base = Line(
        LEFT * 0.16 + DOWN * 0.32,
        RIGHT * 0.16 + DOWN * 0.32,
        stroke_color=WHITE,
        stroke_width=2.5,
    )

    # Screen divider / baseline
    baseline = Line(
        LEFT * 0.26 + DOWN * 0.12,
        RIGHT * 0.26 + DOWN * 0.12,
        stroke_color=WHITE,
        stroke_width=1.5,
        stroke_opacity=0.5,
    )

    # 3 ascending bar chart lines on the left half of the screen
    bar1 = Line(
        LEFT * 0.18 + DOWN * 0.12,
        LEFT * 0.18 + DOWN * 0.02,
        stroke_color=WHITE,
        stroke_width=2.8,
    )
    bar2 = Line(
        LEFT * 0.11 + DOWN * 0.12,
        LEFT * 0.11 + UP * 0.05,
        stroke_color=WHITE,
        stroke_width=2.8,
    )
    bar3 = Line(
        LEFT * 0.04 + DOWN * 0.12,
        LEFT * 0.04 + UP * 0.11,
        stroke_color=WHITE,
        stroke_width=2.8,
    )

    # Circular chart / metric gauge on the right half of the screen
    pie_center = RIGHT * 0.13 + UP * 0.01
    pie_outer = Circle(
        radius=0.10,
        stroke_color=WHITE,
        stroke_width=2.0,
        fill_opacity=0.0,
    ).move_to(pie_center)
    pie_line1 = Line(
        pie_center,
        pie_center + UP * 0.10,
        stroke_color=WHITE,
        stroke_width=1.8,
    )
    pie_line2 = Line(
        pie_center,
        pie_center + RIGHT * 0.10,
        stroke_color=WHITE,
        stroke_width=1.8,
    )

    icon = VGroup(
        monitor, neck, base, baseline,
        bar1, bar2, bar3,
        pie_outer, pie_line1, pie_line2,
    )
    icon.scale(scale)
    return icon


def create_ambient_bg_waves() -> VGroup:
    """
    Renders faint, elegant wave curves matching the light-textured background
    seen in OSL 3.0 splash screens.
    """
    waves = VGroup()
    curve_points = [
        [LEFT * 7.5 + DOWN * 3.5, LEFT * 3.0 + DOWN * 2.8, RIGHT * 2.0 + DOWN * 3.8, RIGHT * 7.5 + DOWN * 3.0],
        [LEFT * 7.5 + DOWN * 3.8, LEFT * 2.0 + DOWN * 3.2, RIGHT * 3.0 + DOWN * 4.0, RIGHT * 7.5 + DOWN * 3.4],
        [LEFT * 7.5 + DOWN * 3.2, LEFT * 4.0 + DOWN * 2.4, RIGHT * 1.0 + DOWN * 3.5, RIGHT * 7.5 + DOWN * 2.7],
    ]
    for pts in curve_points:
        curve = CubicBezier(*pts)
        curve.set_stroke(color="#CBD5E1", width=1.0, opacity=0.35)
        waves.add(curve)
    return waves


# =============================================================================
# The Three Signature Intro Prelude Icons (Img-1)
# =============================================================================
def create_gradient_disc(radius: float = 0.58, color_1: str = "#0B63E5", color_2: str = "#6366F1") -> Circle:
    """Circular gradient disc background matching the 3 intro icons in Img-1."""
    return Circle(
        radius=radius,
        fill_color=[color_1, color_2],
        fill_opacity=1.0,
        stroke_color=WHITE,
        stroke_width=1.0,
        stroke_opacity=0.3,
    )


def create_pie_chart_icon(scale: float = 1.12) -> VGroup:
    """
    Icon 1 (Left): Pie chart with cut slice & surrounding document bracket.
    """
    import numpy as np
    p_center = np.array([-0.03, -0.03, 0])
    r = 0.22
    arc_main = Arc(radius=r, start_angle=0.25 * np.pi, angle=1.5 * np.pi, stroke_color=WHITE, stroke_width=2.2, arc_center=p_center)
    line_r1 = Line(p_center, p_center + np.array([r * np.cos(0.25 * np.pi), r * np.sin(0.25 * np.pi), 0]), stroke_color=WHITE, stroke_width=2.2)
    line_r2 = Line(p_center, p_center + np.array([r * np.cos(1.75 * np.pi), r * np.sin(1.75 * np.pi), 0]), stroke_color=WHITE, stroke_width=2.2)

    slice_center = p_center + np.array([0.08, 0.08, 0])
    arc_slice = Arc(radius=r, start_angle=1.75 * np.pi, angle=0.5 * np.pi, stroke_color=WHITE, stroke_width=2.2, arc_center=slice_center)
    slice_line1 = Line(slice_center, slice_center + np.array([r * np.cos(1.75 * np.pi), r * np.sin(1.75 * np.pi), 0]), stroke_color=WHITE, stroke_width=2.2)
    slice_line2 = Line(slice_center, slice_center + np.array([r * np.cos(0.25 * np.pi), r * np.sin(0.25 * np.pi), 0]), stroke_color=WHITE, stroke_width=2.2)

    bracket = VMobject(stroke_color=WHITE, stroke_width=2.0)
    pts = [
        np.array([-0.12, 0.20, 0]),
        np.array([-0.24, 0.20, 0]),
        np.array([-0.24, -0.22, 0]),
        np.array([0.08, -0.22, 0]),
        np.array([0.08, -0.14, 0]),
    ]
    bracket.set_points_as_corners(pts)
    return VGroup(arc_main, line_r1, line_r2, arc_slice, slice_line1, slice_line2, bracket).scale(scale)


def create_analytics_board_icon(scale: float = 1.12) -> VGroup:
    """
    Icon 2 (Center): Dashboard board with line chart, nodes, bars & magnifying glass.
    """
    import numpy as np
    board = RoundedRectangle(
        width=0.50, height=0.42, corner_radius=0.06,
        stroke_color=WHITE, stroke_width=2.2, fill_opacity=0.0,
    ).move_to([-0.02, 0.02, 0])

    p1 = np.array([-0.16, -0.02, 0])
    p2 = np.array([-0.04, 0.10, 0])
    p3 = np.array([0.08, 0.06, 0])
    line_chart = VMobject(stroke_color=WHITE, stroke_width=1.8).set_points_as_corners([p1, p2, p3])
    d1 = Dot(p1, radius=0.03, color=WHITE)
    d2 = Dot(p2, radius=0.03, color=WHITE)
    d3 = Dot(p3, radius=0.03, color=WHITE)

    b1 = Line([-0.16, -0.14, 0], [-0.16, -0.06, 0], stroke_color=WHITE, stroke_width=2.2)
    b2 = Line([-0.10, -0.14, 0], [-0.10, -0.02, 0], stroke_color=WHITE, stroke_width=2.2)
    b3 = Line([-0.04, -0.14, 0], [-0.04, 0.02, 0], stroke_color=WHITE, stroke_width=2.2)

    glass_c = np.array([0.11, -0.06, 0])
    glass = Circle(radius=0.08, stroke_color=WHITE, stroke_width=2.0, fill_opacity=0.0).move_to(glass_c)
    handle = Line(glass_c + np.array([0.05, -0.05, 0]), glass_c + np.array([0.13, -0.13, 0]), stroke_color=WHITE, stroke_width=2.5)
    return VGroup(board, line_chart, d1, d2, d3, b1, b2, b3, glass, handle).scale(scale)


def create_gear_chart_icon(scale: float = 1.12) -> VGroup:
    """
    Icon 3 (Right): Cog / gear wheel with growth arrow curve and bar columns.
    """
    import numpy as np
    outer_r = 0.28
    inner_r = 0.21
    n_teeth = 8
    points = []
    for i in range(n_teeth):
        a1 = i * (2 * np.pi / n_teeth)
        a2 = a1 + (0.35 * np.pi / n_teeth)
        a3 = a1 + (0.65 * np.pi / n_teeth)
        a4 = a1 + (1.00 * np.pi / n_teeth)
        points.append(np.array([inner_r * np.cos(a1), inner_r * np.sin(a1), 0]))
        points.append(np.array([outer_r * np.cos(a2), outer_r * np.sin(a2), 0]))
        points.append(np.array([outer_r * np.cos(a3), outer_r * np.sin(a3), 0]))
        points.append(np.array([inner_r * np.cos(a4), inner_r * np.sin(a4), 0]))
    points.append(points[0])
    gear = VMobject(stroke_color=WHITE, stroke_width=2.0, fill_opacity=0.0)
    gear.set_points_as_corners(points)

    arrow_line = Line([-0.10, -0.06, 0], [0.08, 0.08, 0], stroke_color=WHITE, stroke_width=2.0)
    arrow_tip1 = Line([0.08, 0.08, 0], [0.01, 0.08, 0], stroke_color=WHITE, stroke_width=2.0)
    arrow_tip2 = Line([0.08, 0.08, 0], [0.08, 0.01, 0], stroke_color=WHITE, stroke_width=2.0)

    b1 = Line([-0.07, -0.10, 0], [-0.07, -0.04, 0], stroke_color=WHITE, stroke_width=2.0)
    b2 = Line([-0.01, -0.10, 0], [-0.01, 0.00, 0], stroke_color=WHITE, stroke_width=2.0)
    b3 = Line([0.05, -0.10, 0], [0.05, 0.04, 0], stroke_color=WHITE, stroke_width=2.0)
    return VGroup(gear, arrow_line, arrow_tip1, arrow_tip2, b1, b2, b3).scale(scale)


def create_three_intro_icons(radius: float = 0.618, spacing: float = 1.518) -> tuple[Mobject, Mobject, Mobject]:
    """
    Constructs the three signature intro discs (Img-1) centered at [-spacing, 0, 0], [0, 0, 0], [spacing, 0, 0].
    Uses high-resolution assets extracted directly from the reference video if available,
    otherwise gracefully falls back to clean vector procedural shapes.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon1_path = os.path.join(base_dir, "icons", "intro_icon_1.png")
    icon2_path = os.path.join(base_dir, "icons", "intro_icon_2.png")
    icon3_path = os.path.join(base_dir, "icons", "intro_icon_3.png")

    if os.path.exists(icon1_path) and os.path.exists(icon2_path) and os.path.exists(icon3_path):
        g1 = ImageMobject(icon1_path).scale_to_fit_height(radius * 2.0).move_to([-spacing, 0, 0]).set_z_index(2)
        g2 = ImageMobject(icon2_path).scale_to_fit_height(radius * 2.0).move_to([0, 0, 0]).set_z_index(2)
        g3 = ImageMobject(icon3_path).scale_to_fit_height(radius * 2.0).move_to([spacing, 0, 0]).set_z_index(2)
        return g1, g2, g3

    disc1 = create_gradient_disc(radius=radius).move_to([-spacing, 0, 0])
    icon1 = create_pie_chart_icon().move_to(disc1.get_center())
    g1 = VGroup(disc1, icon1).set_z_index(2)

    disc2 = create_gradient_disc(radius=radius).move_to([0, 0, 0])
    icon2 = create_analytics_board_icon().move_to(disc2.get_center())
    g2 = VGroup(disc2, icon2).set_z_index(2)

    disc3 = create_gradient_disc(radius=radius).move_to([spacing, 0, 0])
    icon3 = create_gear_chart_icon().move_to(disc3.get_center())
    g3 = VGroup(disc3, icon3).set_z_index(2)

    return g1, g2, g3


def create_title_intro_mobject(
    topic_title: str,
    course_name: Optional[str] = None,
    pill_width: Optional[float] = None,
    pill_height: float = 1.38,
    primary_color: str = "#0B63E5",
    gradient_color: str = "#2563EB",
    font_family: str = "Open Sans",
) -> tuple[VGroup, Group]:
    """
    Builds the complete Title / Intro visual hierarchy mobject.

    Parameters:
    -----------
    topic_title: str
        The topic or lesson name (e.g. "Basic Prompting Techniques").
        Guidelines require Chicago Title Case, max 5-7 words, no all-caps.
    course_name: Optional[str]
        Optional subtitle or course overarching name.
    pill_width: Optional[float]
        Explicit width in Manim scene units. If None, auto-calculated.
    pill_height: float
        Capsule height (standard OSL 3.0 is 1.38 units / ~187px).
    primary_color: str
        Left gradient start color.
    gradient_color: str
        Right gradient end color.
    font_family: str
        Standard font family (defaults to Open Sans).

    Returns:
    --------
    tuple[VGroup, Group]:
        (background_group, banner_group)
    """
    font = get_simplilearn_font(font_family)

    # 1. Background layer (clean off-white canvas with subtle waves)
    bg_rect = FullScreenRectangle(fill_color="#FAFAFD", fill_opacity=1.0, stroke_width=0)
    waves = create_ambient_bg_waves()
    bg_group = VGroup(bg_rect, waves)

    # 2. Text layout
    # Title per guidelines: Open Sans Bold, ~45px (rendered via CrispText for uniform kerning)
    title_text = CrispText(
        topic_title,
        size=36,
        font=font,
        weight=BOLD,
        color=WHITE,
    )

    if course_name:
        # Subtitle per guidelines: Open Sans Regular, #FFFFFF
        subtitle_text = CrispText(
            course_name,
            size=24,
            font=font,
            weight=NORMAL,
            color="#E0E7FF",
        )
        text_group = VGroup(title_text, subtitle_text).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
    else:
        text_group = VGroup(title_text)

    # 3. Dynamic width calculation (clamped inside safe work area width 13.4u)
    badge_radius = pill_height * 0.42
    left_margin = 0.50
    badge_to_text_gap = 0.85
    right_margin = 0.85
    min_pill_w = 8.5
    max_pill_w = 12.8

    max_allowed_text_w = max_pill_w - (left_margin + badge_radius * 2 + badge_to_text_gap + right_margin)
    if text_group.width > max_allowed_text_w:
        text_group.scale_to_fit_width(max_allowed_text_w)

    calculated_w = left_margin + (badge_radius * 2) + badge_to_text_gap + text_group.width + right_margin
    actual_width = pill_width if pill_width is not None else max(min_pill_w, min(calculated_w, max_pill_w))

    # 4. Pill Capsule Banner (centered strictly at ORIGIN)
    capsule = RoundedRectangle(
        width=actual_width,
        height=pill_height,
        corner_radius=pill_height / 2.0,
        fill_color=[primary_color, gradient_color],
        fill_opacity=1.0,
        stroke_width=0,
    ).move_to(ORIGIN)

    # 5. Icon Badge Disc
    disc_center_x = -actual_width / 2.0 + left_margin + badge_radius
    badge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "intro_monitor_badge.png")
    if os.path.exists(badge_path):
        badge_group = ImageMobject(badge_path).scale_to_fit_height(badge_radius * 2.0).move_to(np.array([disc_center_x, 0, 0])).set_z_index(3)
    else:
        icon_disc = Circle(
            radius=badge_radius,
            fill_color="#083E9C",
            fill_opacity=0.55,
            stroke_color=WHITE,
            stroke_width=1.0,
            stroke_opacity=0.3,
        ).move_to(np.array([disc_center_x, 0, 0]))
        icon_art = create_analytics_icon(scale=0.82).move_to(icon_disc.get_center())
        badge_group = VGroup(icon_disc, icon_art).set_z_index(3)

    # 6. Align text inside pill to the right of badge
    text_group.next_to(badge_group, RIGHT, buff=badge_to_text_gap)
    text_group.set_y(0).set_z_index(3)

    banner_group = Group(capsule, badge_group, text_group)

    return bg_group, banner_group


def play_title_intro(
    scene: Scene,
    topic_title: str,
    course_name: Optional[str] = None,
    duration: float = 4.4,
    pill_width: Optional[float] = None,
    font_family: str = "Open Sans",
    animate_three_icons: bool = True,
    animate_in_time: float = 0.8,
    animate_out_time: float = 0.6,
) -> Group:
    """
    Executes the standard Simplilearn Title / Intro animation on the given Scene.

    When animate_three_icons=True (default):
    1. Shows the 3 signature prelude icons (Pie chart, Analytics board, Gear chart)
       centered in the scene (Img-1).
    2. The blue pill banner emerges behind them.
    3. The 3 icons smoothly converge to the left as the capsule expands to its full width.
    4. Morphs into the final desktop analytics monitor badge (Img-2) while the dynamic
       topic title wipes/fades in with crisp typography.

    Parameters:
    -----------
    scene: Scene
        The active Manim scene.
    topic_title: str
        Title of the topic (e.g. "Basic Prompting Techniques").
    course_name: Optional[str]
        Optional subtitle / course intro label.
    duration: float
        Total duration of the intro section in seconds (default: 4.4s).
    pill_width: Optional[float]
        Optional fixed width for the pill capsule.
    font_family: str
        Font to use (default: Open Sans).
    animate_three_icons: bool
        Whether to play the 3-icon prelude emergence & convergence (Img-1 -> Img-2).
    animate_in_time: float
        Animation entrance duration (default: 0.8s).
    animate_out_time: float
        Animation exit duration (default: 0.6s).
    """
    bg_group, banner_group = create_title_intro_mobject(
        topic_title=topic_title,
        course_name=course_name,
        pill_width=pill_width,
        font_family=font_family,
    )
    bg_group.set_z_index(-10)
    scene.add(bg_group)

    capsule = banner_group[0].set_z_index(0)
    badge = banner_group[1].set_z_index(3)
    text = banner_group[2].set_z_index(3)

    if animate_three_icons:
        # Phase 1: 3 Initial Prelude Discs appear (Img-1)
        g1, g2, g3 = create_three_intro_icons(radius=0.618, spacing=1.518)
        scene.play(
            GrowFromCenter(g1),
            GrowFromCenter(g2),
            GrowFromCenter(g3),
            run_time=0.55,
        )
        scene.wait(0.35)

        # Phase 2: Pill emerges behind them and stretches
        initial_pill = RoundedRectangle(
            width=4.5,
            height=capsule.height,
            corner_radius=capsule.height / 2.0,
            fill_color=capsule.fill_color,
            fill_opacity=1.0,
            stroke_width=0,
        ).move_to(ORIGIN).set_z_index(0)

        target_disc_x = badge.get_center()[0]

        scene.play(
            FadeIn(initial_pill, scale=0.8, run_time=0.25),
        )
        scene.play(
            Transform(initial_pill, capsule),
            g1.animate.move_to([target_disc_x, 0, 0]),
            g2.animate.move_to([target_disc_x, 0, 0]).set_opacity(0.0),
            g3.animate.move_to([target_disc_x, 0, 0]).set_opacity(0.0),
            run_time=0.85,
            rate_func=smooth,
        )
        scene.remove(g2, g3)

        # Phase 3: Morph disc into final monitor badge and reveal title
        scene.play(
            FadeTransform(g1, badge),
            FadeIn(text, shift=RIGHT * 0.35),
            run_time=0.50,
        )

        assembled_banner = Group(initial_pill, badge, text)

        # Phase 4: Hold
        elapsed = 0.55 + 0.35 + 0.25 + 0.85 + 0.50 + animate_out_time
        hold_time = max(0.4, duration - elapsed)
        scene.wait(hold_time)

        # Phase 5: Exit
        scene.play(
            FadeOut(assembled_banner, run_time=animate_out_time),
            FadeOut(bg_group, run_time=animate_out_time),
        )
        scene.remove(assembled_banner, bg_group, initial_pill, capsule)
        return assembled_banner

    else:
        # Direct expansion mode
        scene.play(
            GrowFromCenter(capsule, run_time=animate_in_time * 0.9),
            FadeIn(badge, scale=0.85, run_time=animate_in_time),
            FadeIn(text, shift=RIGHT * 0.35, run_time=animate_in_time),
        )
        hold_time = max(0.5, duration - animate_in_time - animate_out_time)
        scene.wait(hold_time)
        scene.play(
            FadeOut(banner_group, run_time=animate_out_time),
            FadeOut(bg_group, run_time=animate_out_time),
        )
        scene.remove(banner_group, bg_group)
        return banner_group


# =============================================================================
# Standalone Demo Scene
# =============================================================================
class TitleIntroScene(Scene):
    """
    Runnable standalone test scene demonstrating Template 1.
    Run with:
        py -3.10 -m manim -pql template1_title_intro.py TitleIntroScene
    """
    def construct(self):
        play_title_intro(
            self,
            topic_title="Basic Prompting Techniques",
            course_name="Generative AI Essentials",
            duration=4.4,
            animate_three_icons=True,
        )


if __name__ == "__main__":
    import subprocess
    subprocess.run([
        "py", "-3.10", "-m", "manim",
        "-pql", __file__, "TitleIntroScene"
    ])

