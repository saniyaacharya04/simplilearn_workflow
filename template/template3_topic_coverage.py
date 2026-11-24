"""
template3_topic_coverage.py — Simplilearn OSL 3.0 Topic Coverage / Next Topic Template
=====================================================================================
Reusable Manim programmatic template for Topic Breakdown, Concept Coverage,
and "Next Topic" Transitions.
Adheres strictly to Simplilearn Learning Design & OSL 3.0 Video Guidelines:
- Layout: 40% Left SME Presenter region / 60% Right Elevated Card
- Header Consistency: Formatted per guidelines ("In the next topic, you will learn about: ...")
- Typography: Open Sans (Header: Bold/SemiBold #202428; Body: Regular #404040, 34px)
- Badges: Circular checkmarks (#0D6EFD with white tick) or numbered badges
- Concept Highlighting: Optional Rule 5 focus stroke (#F78908, 3px, 1.0s draw time)
- Video Ending: Optional 0.5s dissolve to White (#FFFFFF) per guideline 2.4

Usage:
------
from template3_topic_coverage import play_topic_coverage, create_topic_coverage_mobject

class MyScene(Scene):
    def construct(self):
        play_topic_coverage(
            self,
            bullets=[
                "Exploring advanced prompting techniques such as zero-shot and few-shot, and chain-of-thought prompting",
                "Improving agent reasoning and control over complex analytical tasks",
            ],
            header_text="In the next topic, you will learn about:",
            bullet_durations=[3.5, 3.5],
            hold_duration=3.0,
            dissolve_to_white=True,
        )

Command-line test render:
-------------------------
py -3.10 -m manim -pql template3_topic_coverage.py TopicCoverageScene
"""

from __future__ import annotations
import os
from typing import Optional, Union
import textwrap
from manim import *
import manimpango


def get_simplilearn_font(preferred: str = "Open Sans") -> str:
    """Returns preferred font if available, else clean system sans fallback."""
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


def create_checkmark_badge(radius: float = 0.22, color: str = "#0D6EFD") -> VGroup:
    """
    Standard OSL 3.0 circular checkmark badge:
    blue circle (#0D6EFD) with crisp white tick mark.
    """
    circle = Circle(
        radius=radius,
        fill_color=color,
        fill_opacity=1.0,
        stroke_width=0,
    )
    s = radius / 0.22
    check = VMobject(color=WHITE, stroke_width=2.8 * s)
    p1 = LEFT * 0.085 * s + DOWN * 0.010 * s
    p2 = DOWN * 0.080 * s
    p3 = RIGHT * 0.095 * s + UP * 0.085 * s
    check.set_points_as_corners([p1, p2, p3])
    return VGroup(circle, check)


def create_numbered_badge(
    number: int,
    radius: float = 0.22,
    color: str = "#0D6EFD",
    font_family: str = "Open Sans",
) -> VGroup:
    """
    Numbered circular badge used for concept sequencing and stepwise breakdowns.
    """
    font = get_simplilearn_font(font_family)
    circle = Circle(
        radius=radius,
        fill_color=color,
        fill_opacity=1.0,
        stroke_width=0,
    )
    num_text = CrispText(
        str(number),
        size=18,
        font=font,
        weight=BOLD,
        color=WHITE,
    ).move_to(circle.get_center())
    return VGroup(circle, num_text)


def create_sme_placeholder(
    x_min: float = -7.111,
    x_max: float = -1.800,
    bg_color: str = "#0F172A",
    font_family: str = "Open Sans",
) -> VGroup:
    """Mockup placeholder for the trainer camera layer."""
    font = get_simplilearn_font(font_family)
    w = x_max - x_min
    h = 8.0
    cx = (x_min + x_max) / 2.0

    sme_bg = Rectangle(
        width=w,
        height=h,
        fill_color=bg_color,
        fill_opacity=1.0,
        stroke_width=0,
    ).move_to([cx, 0, 0])

    divider = Line(
        [x_max, 4.0, 0],
        [x_max, -4.0, 0],
        stroke_color="#E2E8F0",
        stroke_width=1.5,
    )

    cam_body = RoundedRectangle(
        width=0.6,
        height=0.4,
        corner_radius=0.08,
        stroke_color="#94A3B8",
        stroke_width=2.0,
        fill_opacity=0.0,
    )
    cam_lens = Circle(radius=0.12, stroke_color="#94A3B8", stroke_width=2.0)
    cam_lens_dot = Dot(radius=0.04, color="#94A3B8")
    cam_lens_wedge = Polygon(
        RIGHT * 0.3 + UP * 0.14,
        RIGHT * 0.52 + UP * 0.22,
        RIGHT * 0.52 + DOWN * 0.22,
        RIGHT * 0.3 + DOWN * 0.14,
        stroke_color="#94A3B8",
        stroke_width=2.0,
        fill_opacity=0.0,
    )
    cam_icon = VGroup(cam_body, cam_lens, cam_lens_dot, cam_lens_wedge).scale(0.85)

    label = CrispText("Trainer Video Layer", size=18, font=font, color="#94A3B8")
    cam_group = VGroup(cam_icon, label).arrange(DOWN, buff=0.2).move_to([cx, 0, 0])

    return VGroup(sme_bg, divider, cam_group)


def create_topic_coverage_mobject(
    bullets: list[str],
    header_text: str = "In the next topic, you will learn about:",
    card_width: float = 8.42,
    card_center_x: float = 2.05,
    card_center_y: Optional[float] = None,
    badge_type: str = "checkmark",  # "checkmark" or "numbered"
    primary_badge_color: str = "#0D6EFD",
    font_family: str = "Open Sans",
    wrap_width: int = 60,
    show_sme_placeholder: bool = True,
    trainer_image: Optional[str] = None,
) -> tuple[Optional[Mobject], VGroup, VGroup, VGroup, list[VGroup]]:
    """
    Builds the Topic Coverage / Next Topic visual hierarchy:
    - Left Trainer/SME layer (40% width, earlier fallback mockup)
    - Right Canvas (60% width, clean pure white background)
    - Header text directly above card
    - Elevated Card (white with subtle drop shadow overlapping trainer edge)
    - List of Bullet Items (crisp blue checkmark or numbered badges + wrapped text)

    Returns:
    --------
    tuple:
        (sme_group, full_canvas_group, header, card_group, bullet_items)
    """
    font = get_simplilearn_font(font_family)

    # 1. Left SME layer (earlier fallback placeholder graphic)
    sme_group = (
        create_sme_placeholder(x_min=-7.111, x_max=-1.800, font_family=font_family).set_z_index(-1)
        if show_sme_placeholder
        else None
    )

    # 2. Right background canvas
    canvas_x_min = -1.800
    canvas_w = 7.1111 - canvas_x_min
    canvas_cx = (canvas_x_min + 7.1111) / 2.0
    right_canvas = Rectangle(
        width=canvas_w,
        height=8.0,
        fill_color="#FFFFFF",
        fill_opacity=1.0,
        stroke_width=0,
    ).move_to([canvas_cx, 0, 0]).set_z_index(0)

    # 3. Dynamic card geometry overlapping with left photo SME (as in img-2)
    if card_center_y is None:
        card_center_y = 1.25 if len(bullets) <= 2 else 0.69

    card_h = 2.30 if len(bullets) <= 2 else 3.30

    card_shadow = RoundedRectangle(
        width=card_width,
        height=card_h,
        corner_radius=0.18,
        fill_color="#CBD5E1",
        fill_opacity=0.35,
        stroke_width=0,
    ).move_to([card_center_x + 0.04, card_center_y - 0.05, 0]).set_z_index(1)

    card_body = RoundedRectangle(
        width=card_width,
        height=card_h,
        corner_radius=0.18,
        fill_color=WHITE,
        fill_opacity=1.0,
        stroke_color="#F1F5F9",
        stroke_width=1.0,
    ).move_to([card_center_x, card_center_y, 0]).set_z_index(2)

    card_group = VGroup(card_shadow, card_body)

    # 4. Header text directly above card per guidelines
    header = CrispText(
        header_text,
        size=24,
        font=font,
        weight=BOLD,
        color="#202428",
        align="left",
    ).set_z_index(2)
    header.move_to([card_center_x, card_body.get_top()[1] + 0.45, 0])

    # 5. Construct bullet items (badge + wrapped lines)
    bullet_items: list[VGroup] = []
    badge_radius = 0.17
    badge_x = card_center_x - card_width / 2.0 + 0.48

    top_y = card_body.get_top()[1] - 0.65
    spacing = 0.90 if len(bullets) <= 3 else (card_h - 1.0) / max(1, len(bullets) - 1)

    for idx, text_str in enumerate(bullets):
        by = top_y - (idx * spacing)
        if badge_type == "numbered":
            badge = create_numbered_badge(
                number=idx + 1,
                radius=badge_radius,
                color=primary_badge_color,
                font_family=font_family,
            ).set_z_index(3)
        else:
            badge = create_checkmark_badge(
                radius=badge_radius,
                color=primary_badge_color,
            ).set_z_index(3)
        badge.move_to([badge_x, by, 0])

        wrapped_lines = textwrap.wrap(text_str, width=wrap_width)
        text_block = CrispText(
            "\n".join(wrapped_lines),
            size=17,
            font=font,
            weight=NORMAL,
            color="#404040",
            align="left",
        ).set_z_index(3)

        first_line = text_block[0] if isinstance(text_block, VGroup) else text_block
        text_block.next_to(badge, RIGHT, buff=0.36)
        text_block.shift(UP * (by - first_line.get_center()[1]))

        item = VGroup(badge, text_block)
        bullet_items.append(item)

    full_canvas_group = VGroup(right_canvas)

    return sme_group, full_canvas_group, header, card_group, bullet_items


def play_topic_coverage(
    scene: Scene,
    bullets: list[str],
    header_text: str = "In the next topic, you will learn about:",
    bullet_durations: Union[list[float], float] = 3.5,
    hold_duration: float = 3.0,
    card_width: float = 8.42,
    badge_type: str = "checkmark",
    active_highlight_index: Optional[int] = None,
    show_sme_placeholder: bool = True,
    trainer_image: Optional[str] = None,
    dissolve_to_white: bool = True,
    font_family: str = "Open Sans",
    animate_in_time: float = 0.6,
    animate_out_time: float = 0.5,
) -> VGroup:
    """
    Renders and animates the Topic Coverage or Next Topic section on the given scene.
    Ensures complete, clean fade-out and removal of card and tick marks.
    """
    if isinstance(bullet_durations, (int, float)):
        durations = [float(bullet_durations)] * len(bullets)
    else:
        durations = list(bullet_durations)
        if len(durations) < len(bullets):
            durations.extend([3.5] * (len(bullets) - len(durations)))

    sme_group, canvas_group, header, card_group, bullet_items = create_topic_coverage_mobject(
        bullets=bullets,
        header_text=header_text,
        card_width=card_width,
        badge_type=badge_type,
        show_sme_placeholder=show_sme_placeholder,
        trainer_image=trainer_image,
        font_family=font_family,
    )

    # 1. Base canvas & SME setup
    scene.add(canvas_group)
    if sme_group:
        scene.add(sme_group)

    # 2. Entrance animation: Header and white card fade/slide in
    scene.play(
        FadeIn(card_group, shift=UP * 0.25, run_time=animate_in_time),
        FadeIn(header, shift=DOWN * 0.15, run_time=animate_in_time * 0.8),
    )

    # 3. Reveal bullet points sequentially
    for idx, (item, dur) in enumerate(zip(bullet_items, durations)):
        badge = item[0]
        text = item[1]

        scene.play(
            GrowFromCenter(badge, run_time=0.35),
            FadeIn(text, shift=RIGHT * 0.20, run_time=0.45),
        )

        # Optional Rule 5 Highlight on active concept
        if active_highlight_index is not None and idx == active_highlight_index:
            highlight_box = RoundedRectangle(
                width=item.width + 0.35,
                height=item.height + 0.25,
                corner_radius=0.10,
                stroke_color="#F78908",
                stroke_width=3.0,
                fill_opacity=0.0,
            ).move_to(item.get_center()).set_z_index(4)

            scene.play(Create(highlight_box, run_time=1.0))
            bullet_hold = max(0.2, dur - 1.45)
            scene.wait(bullet_hold)
        else:
            bullet_hold = max(0.2, dur - 0.45)
            scene.wait(bullet_hold)

    # 4. Hold completed card
    scene.wait(hold_duration)

    # 5. Exit: Standard 0.5-second dissolve to White (#FFFFFF) or clean fade out
    if dissolve_to_white:
        white_dissolve = FullScreenRectangle(
            fill_color="#FFFFFF",
            fill_opacity=1.0,
            stroke_width=0,
        ).set_z_index(100)
        scene.play(FadeIn(white_dissolve, run_time=0.5))
        scene.wait(0.5)
    else:
        fade_mobs = [header, card_group]
        for item in bullet_items:
            fade_mobs.extend([item[0], item[1]])
        scene.play(
            *[FadeOut(m, run_time=animate_out_time) for m in fade_mobs],
        )
        for m in fade_mobs:
            scene.remove(m)
            if hasattr(m, "submobjects"):
                scene.remove(*m.submobjects)

    return card_group

    return all_content


# =============================================================================
# Standalone Demo Scene
# =============================================================================
class TopicCoverageScene(Scene):
    """
    Runnable standalone test scene reproducing Img-3 & 2.02_Basic_Prompting_Techniques.mp4 at ~436s.
    Run with:
        py -3.10 -m manim -pql template3_topic_coverage.py TopicCoverageScene
    """
    def construct(self):
        play_topic_coverage(
            self,
            bullets=[
                "Exploring advanced prompting techniques such as zero-shot and few-shot, and chain-of-thought prompting",
                "Improving agent reasoning and control over complex analytical tasks",
            ],
            header_text="In the next topic, you will learn about:",
            bullet_durations=[3.0, 3.0],
            hold_duration=2.5,
            dissolve_to_white=True,
        )


class ConceptBreakdownScene(Scene):
    """
    Example demonstrating Template 3 used as a numbered Concept Breakdown
    with attention-guiding focus stroke on a specific topic (Rule 5).
    """
    def construct(self):
        play_topic_coverage(
            self,
            bullets=[
                "Zero-shot prompting: Querying the model without prior examples",
                "Few-shot prompting: Providing input-output demonstration exemplars",
                "Chain-of-thought prompting: Guiding step-by-step intermediate reasoning",
            ],
            header_text="Basic Prompting Techniques:",
            badge_type="numbered",
            bullet_durations=[2.5, 2.5, 2.5],
            active_highlight_index=0,  # Highlight Zero-shot prompting
            hold_duration=2.0,
            dissolve_to_white=False,
        )


if __name__ == "__main__":
    import subprocess
    subprocess.run([
        "py", "-3.10", "-m", "manim",
        "-pql", __file__, "TopicCoverageScene"
    ])

