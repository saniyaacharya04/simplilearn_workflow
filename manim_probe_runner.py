# manim_probe_runner.py

import argparse
import json
import traceback
import os
from pathlib import Path

import sys

import argparse
import ast
import importlib.util
import inspect
import json
import os
import sys
from pathlib import Path
import numpy as np

MAX_SNIPPET_CHARS = 220

class SourceIndex:
    """Maps a line number to the enclosing statement and its text."""

    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").splitlines()
        self.stmts: list[tuple[int, int]] = []
        try:
            tree = ast.parse("\n".join(self.lines), filename=str(path))
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.stmt) and getattr(node, "end_lineno", None):
                self.stmts.append((node.lineno, node.end_lineno))

    def span(self, line: int) -> tuple[int, int]:
        best = None
        for lo, hi in self.stmts:
            if lo <= line <= hi:
                if best is None or (hi - lo) < (best[1] - best[0]):
                    best = (lo, hi)
        return best or (line, line)

    def snippet(self, line: int) -> tuple[int, int, str]:
        lo, hi = self.span(line)
        text = " ".join(l.strip() for l in self.lines[lo - 1:hi])
        text = " ".join(text.split())
        if len(text) > MAX_SNIPPET_CHARS:
            text = text[: MAX_SNIPPET_CHARS - 1] + "…"
        return lo, hi, text

class Probe:
    def __init__(self, scene_file: Path, fps: float = 60.0):
        self.scene_file = str(scene_file.resolve())
        self.index = SourceIndex(scene_file)
        self.events: list[dict] = []
        self.fps = fps
        self.render_clock = 0.0   # what renderer.time will read in a real render
        self.in_hold = False

    def frames_for(self, duration: float, frozen: bool) -> int:
        """Manim quantises each play to whole frames, and does it two ways.

        An animated play renders ``len(np.arange(0, t, 1/fps))`` frames, which
        rounds up. A static wait goes through ``freeze_current_frame``, which
        uses ``int(duration / dt)`` and rounds down. Modelling both keeps the
        probe's clock identical to the renderer's, instead of drifting by up
        to one frame per play.
        """
        dt = 1.0 / self.fps
        if frozen:
            return int(duration / dt)
        return int(len(np.arange(0, duration, dt)))

    def advance(self, duration: float, frozen: bool) -> tuple[float, float]:
        start = self.render_clock
        self.render_clock += self.frames_for(duration, frozen) / self.fps
        return start, self.render_clock

    def caller_line(self) -> int | None:
        """Innermost frame that lives in the scene file."""
        frame = inspect.currentframe()
        while frame is not None:
            if os.path.abspath(frame.f_code.co_filename) == self.scene_file:
                return frame.f_lineno
            frame = frame.f_back
        return None

    def record(self, kind: str, line: int | None, start: float, end: float, **extra):
        lo, hi, src = self.index.snippet(line) if line else (None, None, "")
        ev = {
            "i": len(self.events),
            "kind": kind,
            "line": lo,
            "end_line": hi,
            "start": round(start, 4),
            "end": round(end, 4),
            "duration": round(end - start, 4),
            "src": src,
        }
        ev.update(extra)
        self.events.append(ev)

def load_scene_class(scene_file: Path, scene_class: str | None):
    """Import the scene module by path and return the requested class."""
    scene_file = scene_file.resolve()
    sys.path.insert(0, str(scene_file.parent))
    spec = importlib.util.spec_from_file_location(scene_file.stem, scene_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {scene_file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    from manim import Scene

    candidates = [
        obj
        for name, obj in vars(module).items()
        if isinstance(obj, type)
        and issubclass(obj, Scene)
        and obj.__module__ == spec.name
    ]
    if scene_class:
        for c in candidates:
            if c.__name__ == scene_class:
                return module, c
        raise NameError(
            f"{scene_class} not found in {scene_file}. "
            f"Scenes present: {[c.__name__ for c in candidates]}"
        )
    if len(candidates) == 1:
        return module, candidates[0]
    raise NameError(
        f"{scene_file} defines {len(candidates)} scenes "
        f"({[c.__name__ for c in candidates]}); pass --scene-class"
    )

def probe_scene(
    scene_file: Path,
    scene_class: str | None = None,
    manifest: str | None = None,
    quiet: bool = True,
    fps: float | None = None,
    ignore_overrides: bool = False,
):
    # ============================================================
    # YOUR ORIGINAL probe_scene() CODE GOES HERE
    # ============================================================

    os.environ["NARRATION_PROBE"] = "1"
    os.environ["NARRATION_IGNORE_OVERRIDES"] = (
        "1" if ignore_overrides else "0"
    )

    if manifest:
        os.environ["NARRATION_MANIFEST"] = str(
            Path(manifest).resolve()
        )

    from manim import config, logger
    import logging

    if fps:
        config.frame_rate = fps

    config.dry_run = True
    config.disable_caching = True
    config.verbosity = "ERROR" if quiet else "INFO"

    if quiet:
        config.progress_bar = "none"
        logger.setLevel(logging.ERROR)

    from manim.renderer.cairo_renderer import CairoRenderer
    from manim.scene.scene import Scene
    
    module, cls = load_scene_class(scene_file, scene_class)
    probe = Probe(scene_file, fps=float(config.frame_rate))

    # --- stub out rasterisation ------------------------------------------
    orig_render = CairoRenderer.render
    orig_update_frame = CairoRenderer.update_frame
    orig_static = CairoRenderer.save_static_frame_data
    CairoRenderer.render = lambda self, scene, time, moving_mobjects: None
    CairoRenderer.update_frame = lambda self, *a, **k: None
    CairoRenderer.save_static_frame_data = lambda self, scene, static_mobjects: None

    # --- instrument the clock --------------------------------------------
    orig_play = Scene.play

    def probed_play(self, *args, **kwargs):
        t0 = self.renderer.time
        line = probe.caller_line()
        orig_play(self, *args, **kwargs)
        # Read scene.duration rather than differencing the clock: manim passes
        # exactly this float to np.arange, and an accumulated clock difference
        # carries enough float error (0.8 -> 0.8000000000000007) to add a
        # phantom frame.
        exact = getattr(self, "duration", None)
        if exact is None:
            exact = self.renderer.time - t0

        frozen = False
        try:
            frozen = self.is_current_animation_frozen_frame()
        except Exception:
            pass
        start, end = probe.advance(exact, frozen)
        # Hand the quantised clock back to the scene, so sync_to() makes the
        # same decisions here that it will make during a real render.
        self.renderer.time = end

        if probe.in_hold:
            # This is sync_to's own wait; the sync event already spans it.
            return

        src = probe.index.snippet(line)[2] if line else ""
        kind = "wait" if src.startswith("self.wait") else "play"
        probe.record(kind, line, start, end,
                    exact_duration=round(exact, 6),
                    frozen=frozen,
                    n_play=self.renderer.num_plays)

    Scene.play = probed_play

    # --- instrument sync calls, if the scene has any ----------------------
    sync_owner = None
    for base in cls.__mro__:
        if "sync_to" in vars(base):
            sync_owner = base
            break

    if sync_owner is not None:
        orig_sync = sync_owner.sync_to

        def probed_sync(self, target_time, label="", **kw):
            start = probe.render_clock
            line = probe.caller_line()
            probe.in_hold = True
            try:
                orig_sync(self, target_time, label=label, **kw)
            finally:
                probe.in_hold = False
            probe.record(
                "sync", line, start, probe.render_clock,
                sync_target=round(target_time, 4),
                sync_label=label,
                drift=round(start - target_time, 4),
            )

        sync_owner.sync_to = probed_sync

    # --- run --------------------------------------------------------------
    # Scenes reference assets relatively ("../images/x.png"), which manim
    # resolves against the working directory. Render from the scene's own
    # directory so the probe sees exactly what a normal `manim` run sees.
    prev_cwd = os.getcwd()
    try:
        os.chdir(scene_file.resolve().parent)
        scene = cls(skip_animations=True)
        scene.render()
        total = scene.renderer.time
        error = None
    except Exception as exc:  # surface it, but keep whatever we measured
        total = None
        error = f"{type(exc).__name__}: {exc}"
        import traceback

        traceback.print_exc()
    finally:
        os.chdir(prev_cwd)
        Scene.play = orig_play
        CairoRenderer.render = orig_render
        CairoRenderer.update_frame = orig_update_frame
        CairoRenderer.save_static_frame_data = orig_static
        if sync_owner is not None:
            sync_owner.sync_to = orig_sync

    import manim

    return {
        "scene_file": str(scene_file.resolve()),
        "scene_class": cls.__name__,
        "group_id": str(getattr(cls, "GROUP_ID", "")) or None,
        "manim_version": manim.__version__,
        "fps": float(config.frame_rate),
        "ignored_overrides": bool(ignore_overrides),
        "total_duration": round(total, 3)
        if total is not None
        else None,
        "n_events": len(probe.events),
        "error": error,
        "events": probe.events,
    }


# ================================================================
# THIS IS JUST THE ENTRYPOINT
# ================================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--scene", required=True)
    parser.add_argument("--scene-class", default=None)
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument(
        "--ignore-overrides",
        action="store_true",
    )

    args = parser.parse_args()

    try:

        result = probe_scene(
            scene_file=Path(args.scene),
            scene_class=args.scene_class,
            manifest=args.manifest,
            fps=args.fps,
            ignore_overrides=args.ignore_overrides,
        )

        # IMPORTANT:
        # stdout contains ONLY this JSON.
        print(json.dumps(result))

    except Exception:

        # Diagnostics go to stderr.
        traceback.print_exc()

        raise