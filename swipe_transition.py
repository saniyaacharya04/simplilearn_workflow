#!/usr/bin/env python3
"""
================================================================================
SIMPLILEARN BROADCAST SWIPE TRANSITION
================================================================================

Visual Design & Geometry:
  - Left-to-Right (L-to-R) horizontal broadcast swipe.
  - Layered multi-bar graphic wipe:
      1. Base Block: Deep Navy (#0B3C5D), width=36.0, height=12.0
      2. Trailing Accent: Simplilearn Light Sky Blue (#62B7E4), width=17.5, height=12.0
      3. Crisp Divider: Pure White (#FFFFFF), width=0.08, height=12.0
      4. Highlight Stripe: Orange Accent (#F78908) / Teal (#3F888F), width=0.25, height=12.0
  - Motion Dynamics:
      * Linear travel from LEFT * 26.0 to RIGHT * 26.0
      * Duration: Exactly 0.80 seconds
      * Full-Screen Occlusion: 100% canvas coverage at t = 0.40s, providing a seamless
        zero-seam cut mask between full-screen trainer footage and presentation slides.

Rendering Instructions:
  1. Render Standalone 0.8s Swipe Transition (MP4):
     manim -qh --fps 60 swipe_transition.py SwipeTransition

  2. Render Transparent Alpha Overlay (1080p ProRes / QuickTime RLE MOV):
     manim -qh --fps 24 -t swipe_transition.py TransitionsOverlay

  3. Standalone Script Execution:
     python3 swipe_transition.py
================================================================================
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Manim Community Imports (with graceful fallback)
try:
    from manim import (
        Scene,
        Rectangle,
        VGroup,
        LEFT,
        RIGHT,
        linear,
        config
    )
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False
    Scene = object

# ==============================================================================
# OFFICIAL SIMPLILEARN COLOR CONSTANTS
# ==============================================================================
COLOR_NAVY       = "#0B3C5D"   # Primary deep corporate navy
COLOR_LIGHT_BLUE = "#62B7E4"   # Simplilearn hero pastel sky blue
COLOR_WHITE      = "#FFFFFF"   # Clean boundary divider
COLOR_ORANGE     = "#F78908"   # Focus highlight accent stripe
COLOR_TEAL       = "#3F888F"   # Alternate broadcast secondary accent


# ==============================================================================
# CORE ANIMATION PRIMITIVE: play_ltor_swipe
# ==============================================================================
def play_ltor_swipe(scene, duration: float = 0.80, use_orange: bool = True):
    """
    Executes the exact Left-to-Right broadcast swipe transition used in
    'Types and Architectures of AI Agents SME.mp4'.

    Parameters:
        scene: An active Manim Scene instance.
        duration: Swipe duration in seconds (standard: 0.8s).
        use_orange: If True, uses #F78908 accent; otherwise uses #3F888F teal.
    """
    accent_color = COLOR_ORANGE if use_orange else COLOR_TEAL

    # 1. Construct layered geometry
    base = Rectangle(
        width=36.0,
        height=12.0,
        fill_color=COLOR_NAVY,
        fill_opacity=1.0,
        stroke_width=0
    )
    trailing = Rectangle(
        width=17.5,
        height=12.0,
        fill_color=COLOR_LIGHT_BLUE,
        fill_opacity=1.0,
        stroke_width=0
    ).align_to(base, LEFT)

    sep_white = Rectangle(
        width=0.08,
        height=12.0,
        fill_color=COLOR_WHITE,
        fill_opacity=1.0,
        stroke_width=0
    ).next_to(trailing, RIGHT, buff=0)

    sep_accent = Rectangle(
        width=0.25,
        height=12.0,
        fill_color=accent_color,
        fill_opacity=1.0,
        stroke_width=0
    ).next_to(sep_white, RIGHT, buff=0)

    # 2. Assemble swipe group off-screen to the left
    swipe_grp = VGroup(base, trailing, sep_white, sep_accent)
    swipe_grp.move_to(LEFT * 26.0)
    scene.add(swipe_grp)

    # 3. Animate linear swipe across the canvas
    scene.play(
        swipe_grp.animate.move_to(RIGHT * 26.0),
        run_time=duration,
        rate_func=linear
    )

    # 4. Cleanup off-screen geometry
    scene.remove(swipe_grp)


# ==============================================================================
# MANIM SCENE 1: Standalone Single Wipe (SwipeTransition)
# ==============================================================================
if MANIM_AVAILABLE:
    class SwipeTransition(Scene):
        """
        Renders a single isolated 0.80-second broadcast swipe clip.
        Output: media/videos/.../SwipeTransition.mp4
        """
        def construct(self):
            play_ltor_swipe(self, duration=0.80, use_orange=True)


    # ==============================================================================
    # MANIM SCENE 2: Master Transparent Overlay (TransitionsOverlay)
    # ==============================================================================
    class TransitionsOverlay(Scene):
        """
        Renders the transparent (-t) alpha MOV overlay used directly in
        'Types and Architectures of AI Agents SME.mp4' video compositing.

        Wipes are centered at cut timestamps so that the 50% occlusion point
        aligns precisely with each transition cut.
        """
        # Cut timestamps from 'Types and Architectures of AI Agents'
        # (Cut at 2.15s: Teacher hook -> Slide Presentation in Scene 5 & 6)
        cut_times = [
            2.15     # Wipes from 1.75s to 2.55s, centered at 2.15s
        ]
        total_duration = 4.58  # Matching rendered TransitionsOverlay.mov duration

        def construct(self):
            current_time = 0.0
            swipe_dur = 0.80
            half_dur = swipe_dur / 2.0

            for cut in self.cut_times:
                start_swipe = max(0.0, cut - half_dur)
                wait_before = start_swipe - current_time
                if wait_before > 0:
                    self.wait(wait_before)
                    current_time += wait_before

                # Execute swipe
                play_ltor_swipe(self, duration=swipe_dur, use_orange=True)
                current_time += swipe_dur

            # Hold until end of overlay duration
            remaining = self.total_duration - current_time
            if remaining > 0:
                self.wait(remaining)


    class FullLectureTransitionsOverlay(Scene):
        """
        Multi-cut master overlay covering all 11 scene transitions in the
        complete 9-minute 'Types and Architectures of AI Agents' lecture.
        """
        cut_times = [
            3.5,     # Cut 0: Intro Card -> Full Screen Teacher Hook
            48.5,    # Cut 1: Full Screen Teacher Hook -> Scene 1 Presentation
            84.0,    # Cut 2: Scene 1 Objectives -> Scene 2 Pillars
            151.0,   # Cut 3: Scene 2 Pillars -> Scene 3 Feedback Loop
            232.0,   # Cut 4: Scene 3 Feedback Loop -> Scene 4 Decision Cycle
            306.5,   # Cut 5: Scene 4 Decision Cycle -> Scene 5 Reactive Agent
            351.5,   # Cut 6: Scene 5 Reactive Agent -> Scene 6 Goal vs Utility
            434.5,   # Cut 7: Scene 6 Goal vs Utility -> Scene 7 Enterprise Pipeline
            519.0,   # Cut 8: Scene 7 Enterprise Pipeline -> Scene 8 Summary Recap
            557.5,   # Cut 9: Scene 8 Summary Recap -> Full Screen Teacher Outro
            581.3    # Cut 10: Full Screen Teacher Outro -> Ending Card
        ]
        total_duration = 586.5

        def construct(self):
            current_time = 0.0
            swipe_dur = 0.80
            half_dur = swipe_dur / 2.0

            for cut in self.cut_times:
                start_swipe = max(0.0, cut - half_dur)
                wait_before = start_swipe - current_time
                if wait_before > 0:
                    self.wait(wait_before)
                    current_time += wait_before

                play_ltor_swipe(self, duration=swipe_dur, use_orange=True)
                current_time += swipe_dur

            remaining = self.total_duration - current_time
            if remaining > 0:
                self.wait(remaining)


# ==============================================================================
# CLI EXECUTION HELPER
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Simplilearn Broadcast Swipe Transition Renderer"
    )
    parser.add_argument(
        "--scene",
        default="SwipeTransition",
        choices=["SwipeTransition", "TransitionsOverlay", "FullLectureTransitionsOverlay"],
        help="Scene class to render"
    )
    parser.add_argument(
        "--transparent", "-t",
        action="store_true",
        help="Render transparent alpha MOV (qtrle/png)"
    )
    parser.add_argument(
        "--quality", "-q",
        default="qh",
        choices=["ql", "qm", "qh", "qk"],
        help="Render quality (ql: 480p, qh: 1080p, qk: 4k)"
    )
    args = parser.parse_args()

    # Detect manim binary
    manim_cmd = "manim"
    cmd = [manim_cmd, f"-{args.quality}", "--fps", "24", str(Path(__file__).resolve()), args.scene]
    if args.transparent:
        cmd.append("-t")

    print("\n" + "=" * 70)
    print("SIMPLILEARN BROADCAST SWIPE TRANSITION")
    print(f"Executing: {' '.join(cmd)}")
    print("=" * 70 + "\n")

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("[!] 'manim' command not found in PATH.")
        print("    Run inside your Manim environment:")
        print(f"    manim -{args.quality} -t {Path(__file__).name} {args.scene}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Manim render failed with code {e.returncode}")


if __name__ == "__main__":
    main()
