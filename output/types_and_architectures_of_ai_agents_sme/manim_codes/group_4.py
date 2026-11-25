C_BRAND_BLUE = "#2C81FE"
C_TEXT = "#404040"
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_WARM_AMBER = "#E6A157"
C_CORAL = "#E58F6D"
C_SOFT_LILAC = "#C1A5C6"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_RED = "#E58F6D"
C_WHITE = "#FFFFFF"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
C_DARK_BLUE = "#1E293B"
C_HIGHLIGHT = "#F78908"
C_MINT = "#8ECDB7"
C_LAVENDER = "#9B99C7"
C_YELLOW = "#DDB945"

# --- Define missing color and font constants ---
C_BACKGROUND = C_WHITE
C_HEADER_DARK = C_TEXT
C_MINT_SEAFOAM = C_MINT
C_LAVENDER_PERIWINKLE = C_LAVENDER
C_HIGHLIGHT_ORANGE = C_HIGHLIGHT
C_BODY_DARK = C_TEXT

FONT_SIZE_COMPONENT_HEADER_MANIM = 24.0
FONT_SIZE_BADGE_MANIM = 14.0
FONT_SIZE_BODY_MANIM = 16.0

import os
import re
SME_LAYOUT = '20'
from manim import *
# Dynamic Animation Safety Preamble
for _anim_cls in (FadeIn, FadeOut, Create, Write):
    try:
        if not hasattr(_anim_cls, '_orig_new_safe'):
            def _make_safe(cls):
                def _safe_new(subcls, mobject, *args, **kwargs):
                    if isinstance(mobject, Animation):
                        return mobject
                    if hasattr(mobject, 'build') or mobject.__class__.__name__ == '_AnimationBuilder':
                        try:
                            return mobject.build()
                        except Exception:
                            pass
                    if not isinstance(mobject, Mobject):
                        return Animation(Dot(fill_opacity=0, stroke_opacity=0))
                    if cls is Create and not isinstance(mobject, VMobject):
                        return FadeIn(mobject, *args, **kwargs)
                    return super(cls, subcls).__new__(subcls)
                return _safe_new
            _anim_cls._orig_new_safe = True
            _anim_cls.__new__ = _make_safe(_anim_cls)
    except Exception:
        pass
for _txt_cls in (Text,):
    try:
        if not hasattr(_txt_cls, '_orig_scale_to_fit_width_safe'):
            _txt_cls._orig_scale_to_fit_width_safe = _txt_cls.scale_to_fit_width
            def _make_safe_text_scale(cls):
                def _safe_text_scale(self, width, *args, **kwargs):
                    if hasattr(self, 'width') and self.width > 0:
                        ratio = width / self.width
                        if ratio > 1.0:
                            return self
                        if ratio < 0.88:
                            ratio = 0.88
                        return cls._orig_scale_to_fit_width_safe(self, self.width * ratio, *args, **kwargs)
                    return cls._orig_scale_to_fit_width_safe(self, width, *args, **kwargs)
                return _safe_text_scale
            _txt_cls.scale_to_fit_width = _make_safe_text_scale(_txt_cls)
    except Exception:
        pass
for _scene_cls in (Scene, MovingCameraScene):
    try:
        if not hasattr(_scene_cls, 'sync_to'):
            def _make_sync_to():
                def _safe_sync_to(self, target_time):
                    curr_t = getattr(getattr(self, 'renderer', None), 'time', 0.0)
                    if target_time > curr_t:
                        self.wait(target_time - curr_t)
                return _safe_sync_to
            _scene_cls.sync_to = _make_sync_to()
    except Exception:
        pass
_orig_anim_safe_defined = True

try:
    from manim.utils.rate_functions import *
except Exception:
    pass
import numpy as np
import manim.utils.rate_functions as _rf
for _k in dir(_rf):
    if not _k.startswith("_"):
        globals()[_k] = getattr(_rf, _k)


# Replaced the simpler global safe_image with the more complex version previously in construct


# Replaced the simpler global create_pill with the more complex version previously in construct



def fit_into_box(target_mobject, frame_mobject, pad_x=0.25, pad_y=0.20):
    if hasattr(frame_mobject, '__class__') and frame_mobject.__class__.__name__ == 'Polygon':
        pad_x = max(pad_x, getattr(frame_mobject, 'width', 0) * 0.22)
        pad_y = max(pad_y, getattr(frame_mobject, 'height', 0) * 0.22)
    if hasattr(frame_mobject, 'width') and hasattr(target_mobject, 'width'):
        max_w = frame_mobject.width - (pad_x * 2)
        if max_w > 0 and target_mobject.width > max_w:
            ratio = max_w / target_mobject.width
            needed_w = target_mobject.width + (pad_x * 2)
            if hasattr(frame_mobject, 'stretch_to_fit_width') and needed_w <= 6.2:
                frame_mobject.stretch_to_fit_width(needed_w)
            elif ratio < 0.88:
                if hasattr(target_mobject, 'scale_to_fit_width'):
                    target_mobject.scale_to_fit_width(target_mobject.width * 0.88)
            else:
                target_mobject.scale_to_fit_width(max_w)
    if hasattr(frame_mobject, 'height') and hasattr(target_mobject, 'height'):
        req_h = target_mobject.height + (pad_y * 2)
        if req_h > frame_mobject.height:
            frame_mobject.stretch_to_fit_height(req_h)
    target_mobject.move_to(frame_mobject.get_center())
    return target_mobject

def safe_image(img_path, width=3.0, height=None):
    if os.path.exists(str(img_path)):
        try:
            im = ImageMobject(str(img_path))
            if width: im.scale_to_fit_width(width)
            if height: im.scale_to_fit_height(height)
            return im
        except Exception:
            pass
    box = RoundedRectangle(width=width or 3.0, height=height or 2.0, corner_radius=0.074, fill_color='#F8FAFC', fill_opacity=0.9, stroke_color='#CBD5E1', stroke_width=1.5)
    lbl = CrispText('Asset Image', font_size=12, color='#404040').move_to(box)
    return VGroup(box, lbl)

def create_pill(*args, **kwargs):
    bg_color = kwargs.get('bg_color', globals().get('C_DARK_BLUE', '#1E293B'))
    text_color = kwargs.get('text_color', globals().get('C_WHITE', '#FFFFFF'))
    font_size = kwargs.get('font_size', 12)
    texts = [str(a) for a in args if isinstance(a, (str, int, float)) and not str(a).startswith('#') and str(a) not in ('WHITE', 'BLACK')]
    text_content = texts[0] if texts else 'Badge'
    txt = CrispText(text_content, font_size=font_size, color=text_color, weight='BOLD')
    bg = RoundedRectangle(width=max(txt.width + 0.4, 1.2), height=max(txt.height + 0.2, 0.4), corner_radius=0.15, fill_color=bg_color, fill_opacity=1.0, stroke_width=0)
    txt.move_to(bg)
    fit_into_box(txt, bg, pad_x=0.2, pad_y=0.08)
    grp = VGroup(bg, txt)
    grp.set_z_index(20)
    return grp

def create_checkmark(*args, **kwargs):
    c = kwargs.get('color', globals().get('C_STEEL_BLUE', '#7EA2C8'))
    for a in args:
        if isinstance(a, str) and (a.startswith('#') or a in globals()):
            c = a
    sz = kwargs.get('size', kwargs.get('font_size', 0.22))
    if isinstance(sz, (int, float)) and sz > 1.0:
        sz = sz / 60.0
    sw = kwargs.get('stroke_width', 3.5)
    p1 = ORIGIN
    p2 = p1 + RIGHT * (sz * 0.42) + DOWN * (sz * 0.55)
    p3 = p2 + RIGHT * (sz * 0.95) + UP * (sz * 1.15)
    l1 = Line(p1, p2, color=c, stroke_width=sw)
    l2 = Line(p2, p3, color=c, stroke_width=sw)
    g = VGroup(l1, l2)
    g.center()
    return g

def create_crossmark(*args, **kwargs):
    c = kwargs.get('color', globals().get('C_CORAL', '#E58F6D'))
    for a in args:
        if isinstance(a, str) and (a.startswith('#') or a in globals()):
            c = a
    sz = kwargs.get('size', kwargs.get('font_size', 0.22))
    if isinstance(sz, (int, float)) and sz > 1.0:
        sz = sz / 60.0
    sw = kwargs.get('stroke_width', 3.5)
    l1 = Line(ORIGIN, RIGHT * (sz * 0.8) + UP * (sz * 0.8), color=c, stroke_width=sw)
    l2 = Line(ORIGIN + UP * (sz * 0.8), RIGHT * (sz * 0.8), color=c, stroke_width=sw)
    g = VGroup(l1, l2)
    g.center()
    return g

class NullMobject(VGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*[VMobject() for _ in range(15)])
        self.set_opacity(0)
    def __getitem__(self, val):
        if isinstance(val, int) and val >= len(self.submobjects):
            return VMobject()
        return super().__getitem__(val)
    def get_center(self):
        return np.array([0.0, 0.0, 0.0])
    def get_top(self):
        return np.array([0.0, 0.0, 0.0])
    def get_bottom(self):
        return np.array([0.0, 0.0, 0.0])
    def get_left(self):
        return np.array([0.0, 0.0, 0.0])
    def get_right(self):
        return np.array([0.0, 0.0, 0.0])

try:
    if not hasattr(VGroup, '_orig_add_safe'):
        VGroup._orig_add_safe = VGroup.add
        def _safe_vg_add(self, *mobs):
            cleaned = []
            for m in mobs:
                if isinstance(m, VMobject):
                    cleaned.append(m)
                elif hasattr(m, 'submobjects'):
                    for sub in m.submobjects:
                        if isinstance(sub, VMobject):
                            cleaned.append(sub)
            return VGroup._orig_add_safe(self, *cleaned)
        VGroup.add = _safe_vg_add
except Exception:
    pass

NumberLine.c2p = lambda self, *args: self.n2p(args[0])



def CrispText(text, size=24, font="Open Sans", **kwargs):
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
    elif size < 4.0:
        size = 5.0
    align = kwargs.pop("align", "center")
    autowrap_val = kwargs.pop("autowrap", kwargs.pop("wrap", None))
    disable_wrap_val = kwargs.pop("disable_wrap", kwargs.pop("disable_autowrap", False))
    max_w_param = kwargs.pop("max_width", kwargs.pop("wrap_width", None))
    for bad_k in ("alignment", "max_len", "line_spacing", "title_size", "item_size"):
        kwargs.pop(bad_k, None)
    slant_val = kwargs.pop("slant", NORMAL)
    weight_val = kwargs.pop("weight", NORMAL)
    if isinstance(weight_val, str):
        weight_clean = weight_val.upper().replace("-", "").replace("_", "").replace(" ", "")
        if weight_clean == "REGULAR":
            weight_val = NORMAL
        elif weight_clean in ("SEMIBOLD", "SEMI_BOLD"):
            weight_val = SEMIBOLD
        elif weight_clean == "BOLD":
            weight_val = BOLD
        elif weight_clean == "LIGHT":
            weight_val = LIGHT
        elif weight_clean in ("NORMAL", "BOOK"):
            weight_val = NORMAL
        else:
            weight_val = NORMAL
    color_val = kwargs.pop("color", None)
    if color_val is None:
        color_val = globals().get("TEXT_COLOR", globals().get("C_BLACK", "#404040"))
    elif str(color_val).upper() in ("#F9C72C", "C_YELLOW", "YELLOW", "#FFF9E6", "#FFFF00", "#0B3C5D", "#06152B", "#0A2540", "#1D3557", "NAVY", "C_NAVY", "C_NAVY_DARK"):
        color_val = globals().get("TEXT_COLOR", globals().get("C_BLACK", "#404040"))
    raw_str = str(text)
    _acronyms = {"AI", "RAM", "DB", "API", "LLM", "CPU", "GPU", "UI", "OSL", "ML", "OST", "VDB", "JSON", "HTTP", "REST", "SQL", "SME", "PIP", "HD", "FHD"}
    import re as _re
    def _tc_sub(m):
        w = m.group(0)
        return w if w in _acronyms else w.capitalize()
    raw_str = _re.sub(r"\b[A-Z]{2,}\b", _tc_sub, raw_str)
    NL = chr(10)
    split_lines = [l for l in raw_str.split(NL)] if NL in raw_str else ([l for l in raw_str.split(r"\\n")] if r"\\n" in raw_str else None)
    if split_lines is None:
        should_autowrap = False
        wrap_target_chars = 34
        if max_w_param is not None:
            try:
                mw = float(max_w_param)
                wrap_target_chars = max(16, int(mw / (size * 0.0082)))
                should_autowrap = (" " in raw_str and len(raw_str) > wrap_target_chars)
            except Exception:
                pass
        if not should_autowrap:
            if autowrap_val is True:
                should_autowrap = True
                wrap_target_chars = 34
            elif autowrap_val is False or disable_wrap_val:
                should_autowrap = False
            else:
                should_autowrap = (len(raw_str) > 36 and " " in raw_str and size <= 16)
                wrap_target_chars = 34
        if should_autowrap:
            words = raw_str.split()
            lines = []
            curr_line = []
            curr_len = 0
            for w in words:
                sep = 1 if curr_line else 0
                if curr_len + len(w) + sep > wrap_target_chars:
                    if curr_line:
                        lines.append(" ".join(curr_line))
                    curr_line = [w]
                    curr_len = len(w)
                else:
                    curr_line.append(w)
                    curr_len += len(w) + sep
            if curr_line:
                lines.append(" ".join(curr_line))
            split_lines = lines
        else:
            split_lines = [raw_str]
    clean_kwargs = {k: v for k, v in kwargs.items() if k in ("tab_width", "t2c", "t2f", "t2s", "t2w", "l2g", "gradient", "fill_opacity", "stroke_width", "stroke_color")}
    if len(split_lines) > 1:
        line_mobs = [Text(l, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **clean_kwargs) for l in split_lines]
        aligned_edge = ORIGIN if align == "center" else (LEFT if align == "left" else RIGHT)
        mob = VGroup(*line_mobs).arrange(DOWN, buff=0.18, aligned_edge=aligned_edge).scale(0.25)
    else:
        mob = Text(raw_str, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **clean_kwargs).scale(0.25)
    orig_scale = mob.scale_to_fit_width
    def safe_scale_width(tw):
        if hasattr(mob, "width") and mob.width > 0:
            ratio = tw / mob.width
            if ratio > 1.0:
                return mob
            if ratio < 0.88:
                ratio = 0.88
            return orig_scale(mob.width * ratio)
        return orig_scale(tw)
    mob.scale_to_fit_width = safe_scale_width
    return mob
class PulsingShockwaves(VGroup):
    def __init__(self, center, color="#E6A157", max_radius=1.1, num_rings=3, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.color = color
        self.max_radius = max_radius
        self.num_rings = num_rings
        self.rings = [Circle(radius=0.2 + i * 0.3, color=color, stroke_width=2.0).move_to(self.center_pt) for i in range(num_rings)]
        self.add(*self.rings)
        self.t = 0.0
        def update_waves(mob, dt):
            mob.t += dt
            for i, ring in enumerate(mob.rings):
                phase = (mob.t * 0.9 + i / float(mob.num_rings)) % 1.0
                r = 0.25 + phase * (mob.max_radius - 0.25)
                ring.become(Circle(radius=r, color=mob.color, stroke_width=2.5 * (1.0 - phase)).move_to(mob.center_pt))
                ring.set_stroke(opacity=max(0.0, 1.0 - phase))
        self.add_updater(update_waves)

class TelemetryWaves(VGroup):
    def __init__(self, center, color="#8ECDB7", **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.arcs = [
            Arc(radius=0.45 + i * 0.22, start_angle=-PI/3, angle=2*PI/3, color=color, stroke_width=2.2).move_to(self.center_pt + RIGHT * 0.50)
            for i in range(3)
        ]
        self.add(*self.arcs)
        self.t = 0.0
        def update_telemetry(mob, dt):
            mob.t += dt
            for i, arc in enumerate(mob.arcs):
                phase = (mob.t * 1.3 + i / 3.0) % 1.0
                arc.set_stroke(opacity=max(0.1, 1.0 - phase), width=2.6 * (1.0 - phase * 0.4))
        self.add_updater(update_telemetry)

class NeuralHaloPulses(VGroup):
    def __init__(self, center, color="#9B99C7", **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.h1 = Circle(radius=0.85, color=color, stroke_width=1.6).move_to(self.center_pt)
        self.nodes = [
            Dot(self.center_pt + np.array([np.cos(a)*0.65, np.sin(a)*0.65, 0]), radius=0.045, color=color)
            for a in np.linspace(0, 2*PI, 6, endpoint=False)
        ]
        self.lines = [Line(self.center_pt, n.get_center(), color=color, stroke_width=1.0, stroke_opacity=0.6) for n in self.nodes]
        self.add(self.h1, *self.lines, *self.nodes)
        self.t = 0.0
        def update_halo(mob, dt):
            mob.t += dt
            s = 1.0 + 0.07 * np.sin(mob.t * 3.0)
            mob.h1.become(Circle(radius=0.85 * s, color=color, stroke_width=1.6).move_to(mob.center_pt))
            mob.h1.set_stroke(opacity=0.4 + 0.4 * np.sin(mob.t * 3.0))
        self.add_updater(update_halo)

class DynamicRadarSweep(VGroup):
    def __init__(self, center, radius=1.0, color="#62B7E4", speed=3.0, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.radius = radius
        self.speed = speed
        self.dish = Circle(radius=radius, fill_color="#DCEEF9", fill_opacity=0.85, stroke_width=0).move_to(self.center_pt)
        self.bezel = Circle(radius=radius, color=color, stroke_width=2.2).move_to(self.center_pt)
        self.r1 = Circle(radius=radius*0.45, color=color, stroke_width=1.0, stroke_opacity=0.5).move_to(self.center_pt)
        self.cross_h = Line(self.center_pt - np.array([radius, 0, 0]), self.center_pt + np.array([radius, 0, 0]), color="#BACAD8", stroke_width=0.8, stroke_opacity=0.6)
        self.cross_v = Line(self.center_pt - np.array([0, radius, 0]), self.center_pt + np.array([0, radius, 0]), color="#BACAD8", stroke_width=0.8, stroke_opacity=0.6)
        self.sweep_line = Line(self.center_pt, self.center_pt + np.array([radius, 0, 0]), color="#F78908", stroke_width=2.4)
        self.blip = Dot(self.center_pt + np.array([0.45*radius, 0.4*radius, 0]), radius=0.05, color="#F78908")
        self.add(self.dish, self.bezel, self.r1, self.cross_h, self.cross_v, self.blip, self.sweep_line)
        self.angle = 0.0
        def update_sweep(mob, dt):
            mob.angle = (mob.angle + mob.speed * dt) % (2 * PI)
            end_pt = mob.center_pt + mob.radius * np.array([np.cos(mob.angle), np.sin(mob.angle), 0])
            mob.sweep_line.set_points_by_ends(mob.center_pt, end_pt)
            d = (mob.angle - 0.7) % (2 * PI)
            mob.blip.set_opacity(max(0.2, 1.0 - d * 0.5))
        self.add_updater(update_sweep)

class FlowingStream(VGroup):
    def __init__(self, start_pt, end_pt, color="#62B7E4", num_dots=4, speed=1.2, **kwargs):
        super().__init__(**kwargs)
        self.p0 = np.array(start_pt)
        self.p1 = np.array(end_pt)
        self.color = color
        self.num_dots = num_dots
        self.speed = speed
        self.rail = Line(self.p0, self.p1, color=color, stroke_width=1.5, stroke_opacity=0.4)
        self.dots = [Dot(radius=0.055, color=color) for _ in range(num_dots)]
        self.add(self.rail, *self.dots)
        self.t = 0.0
        def update_stream(mob, dt):
            mob.t += dt
            for i, dot in enumerate(mob.dots):
                alpha = (mob.t * mob.speed + i / float(mob.num_dots)) % 1.0
                dot.move_to(mob.p0 + alpha * (mob.p1 - mob.p0))
                dot.set_opacity(np.sin(alpha * PI))
        self.add_updater(update_stream)

class PulsingNode(VGroup):
    def __init__(self, center, radius=0.45, color="#2C81FE", label="", **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.radius = radius
        self.color = color
        self.core = Circle(radius=radius, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=color, stroke_width=2.5).move_to(self.center_pt)
        self.halo = Circle(radius=radius * 1.3, color=color, stroke_width=1.5).move_to(self.center_pt)
        self.add(self.core, self.halo)
        if label:
            self.lbl = CrispText(label, size=11, weight=BOLD, color="#404040").move_to(self.center_pt)
            self.add(self.lbl)
        self.t = 0.0
        def update_node(mob, dt):
            mob.t += dt
            s = 1.0 + 0.12 * np.sin(mob.t * 3.0)
            mob.halo.become(Circle(radius=mob.radius * 1.3 * s, color=mob.color, stroke_width=1.5).move_to(mob.center_pt))
            mob.halo.set_stroke(opacity=max(0.1, 0.6 + 0.4 * np.sin(mob.t * 3.0)))
        self.add_updater(update_node)

class BalanceScale(VGroup):
    def __init__(self, center, tilt_angle=0.12, beam_len=3.2, color="#404040", **kwargs):
        super().__init__(**kwargs)
        c = np.array(center)
        self.fulcrum = Polygon(c, c + np.array([-0.3, -0.5, 0]), c + np.array([0.3, -0.5, 0]), color=color, fill_color="#E5EDF4", fill_opacity=1.0, stroke_width=2.0)
        p_left = c + np.array([-np.cos(tilt_angle)*beam_len/2, -np.sin(tilt_angle)*beam_len/2, 0])
        p_right = c + np.array([np.cos(tilt_angle)*beam_len/2, np.sin(tilt_angle)*beam_len/2, 0])
        self.beam = Line(p_left, p_right, color=color, stroke_width=3.0)
        self.pivot = Dot(c, radius=0.07, color="#F78908")
        self.string_l = Line(p_left, p_left + DOWN * 0.5, color=color, stroke_width=1.2)
        self.tray_l = Arc(radius=0.45, start_angle=PI, angle=PI, color=color, stroke_width=2.0).move_to(p_left + DOWN * 0.72)
        self.string_r = Line(p_right, p_right + DOWN * 0.5, color=color, stroke_width=1.2)
        self.tray_r = Arc(radius=0.45, start_angle=PI, angle=PI, color=color, stroke_width=2.0).move_to(p_right + DOWN * 0.72)
        self.add(self.fulcrum, self.beam, self.pivot, self.string_l, self.tray_l, self.string_r, self.tray_r)

# --- Custom Base Classes and Helpers ---

# Removed `from feedback_functions.instrumented_scene import InstrumentedScene`
# as the class is defined here.
class InstrumentedScene(Scene):
    """
    A base class for Simplilearn presentations, providing simplified synchronization capabilities.
    In a real Simplilearn setup, this would include more robust timing and scene management
    integrated with audio markers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_play_time = 0.0

    def play(self, *args, **kwargs):
        """Overrides Manim's play to track current time."""
        run_time = kwargs.get('run_time', 1.0) # Default run_time if not specified
        super().play(*args, **kwargs)
        self._current_play_time += run_time

    def wait(self, duration=1.0):
        """Overrides Manim's wait to track current time."""
        super().wait(duration)
        self._current_play_time += duration

    def sync_to(self, target_time):
        """
        Pauses the scene until the current play time reaches the target_time.
        This is a simplified implementation.
        """
        time_to_wait = target_time - self._current_play_time
        if time_to_wait > 0:
            self.wait(time_to_wait)
        # If time_to_wait is negative, we've already passed the sync point, so no wait.

    def get_current_play_time(self):
        """Returns the current accumulated play time."""
        return self._current_play_time


def create_header(*args, **kwargs):
    return create_title(*args, **kwargs)








# --- Main Scene Class ---
class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        self.camera.background_color = C_BACKGROUND
        def fit_into_box(target_mobject, frame_mobject, pad_x=0.25, pad_y=0.20):
            if hasattr(frame_mobject, '__class__') and frame_mobject.__class__.__name__ == 'Polygon':
                pad_x = max(pad_x, getattr(frame_mobject, 'width', 0) * 0.22)
                pad_y = max(pad_y, getattr(frame_mobject, 'height', 0) * 0.22)
            if hasattr(frame_mobject, 'width') and hasattr(target_mobject, 'width'):
                max_w = frame_mobject.width - (pad_x * 2)
                if max_w > 0 and target_mobject.width > max_w:
                    ratio = max_w / target_mobject.width
                    needed_w = target_mobject.width + (pad_x * 2)
                    if hasattr(frame_mobject, 'stretch_to_fit_width') and needed_w <= 6.2:
                        frame_mobject.stretch_to_fit_width(needed_w)
                    elif ratio < 0.88:
                        if hasattr(target_mobject, 'scale_to_fit_width'):
                            target_mobject.scale_to_fit_width(target_mobject.width * 0.88)
                    else:
                        target_mobject.scale_to_fit_width(max_w)
            if hasattr(frame_mobject, 'height') and hasattr(target_mobject, 'height'):
                req_h = target_mobject.height + (pad_y * 2)
                if req_h > frame_mobject.height:
                    frame_mobject.stretch_to_fit_height(req_h)
            target_mobject.move_to(frame_mobject.get_center())
            return target_mobject

        def clamp_to_screen(mobject, pad=0.35):
            if not hasattr(mobject, 'get_left') or not hasattr(mobject, 'get_right'):
                return mobject
            try:
                is_70_sme = str(globals().get('SME_LAYOUT', '')).strip() == '70'
                is_20_sme = str(globals().get('SME_LAYOUT', '')).strip() == '20'
                if is_70_sme:
                    min_x = -0.8
                    max_x = 6.4
                    l = mobject.get_left()[0]
                    r = mobject.get_right()[0]
                    if l < min_x:
                        mobject.shift(RIGHT * (min_x - l))
                    if r > max_x:
                        mobject.shift(LEFT * (r - max_x))
                elif is_20_sme:
                    max_x = 7.11 - pad
                    l = mobject.get_left()[0]
                    r = mobject.get_right()[0]
                    if r > max_x:
                        mobject.shift(LEFT * (r - max_x))
                    elif l < -max_x:
                        mobject.shift(RIGHT * (-max_x - l))
                    top_y = mobject.get_top()[1]
                    if top_y > 2.0 and r > 4.20:
                        mobject.shift(LEFT * (r - 4.20))
                else:
                    max_x = 7.11 - pad
                    r = mobject.get_right()[0]
                    l = mobject.get_left()[0]
                    if r > max_x:
                        mobject.shift(LEFT * (r - max_x))
                    elif l < -max_x:
                        mobject.shift(RIGHT * (-max_x - l))
                top_y = mobject.get_top()[1]
                if top_y > 1.8 and mobject.get_left()[0] < 0 and getattr(mobject, 'name', '') != 'title_group' and not getattr(mobject, 'is_title', False):
                    mobject.shift(DOWN * (top_y - 1.8))
                elif top_y > 3.8 and getattr(mobject, 'name', '') != 'title_group' and not getattr(mobject, 'is_title', False):
                    mobject.shift(DOWN * (top_y - 3.8))
                bot_y = mobject.get_bottom()[1]
                if bot_y < -3.8:
                    mobject.shift(UP * (-3.8 - bot_y))
            except Exception:
                pass
            return mobject

        def create_title(*text_args, **kwargs):
            clean_args = []
            for arg in text_args:
                s_arg = str(arg)
                for bad in ['Dr. Milan Joshi', 'Dr. Milan', 'Milan Joshi', 'Dr.', 'Instructor']:
                    s_arg = re.sub(re.escape(bad), '', s_arg, flags=re.IGNORECASE).strip()
                clean_args.append(s_arg)
            text_args = clean_args
            if len(text_args) == 0 or not str(text_args[0]).strip():
                title_arg = "Scene Title"
            else:
                title_arg = text_args[0]
            if isinstance(title_arg, (list, tuple)):
                if len(title_arg) > 0 and any(isinstance(x, (Mobject, VMobject)) or hasattr(x, 'animate') for x in title_arg):
                    title_m = VGroup(*title_arg).arrange(RIGHT, buff=0.15)
                else:
                    title_m = CrispText(" ".join(str(x) for x in title_arg), size=26, font="Open Sans", weight=BOLD, color=globals().get("TEXT_COLOR", "#404040"))
            elif isinstance(title_arg, (Mobject, VMobject)) or hasattr(title_arg, 'animate'):
                title_m = title_arg
            else:
                title_m = CrispText(str(title_arg), size=26, font="Open Sans", weight=BOLD, color=globals().get("TEXT_COLOR", "#404040"))
            line_len = max(2.5, min(getattr(title_m, 'width', 3.0), 6.0))
            line = Line(ORIGIN, RIGHT * line_len, color=globals().get("C_BRAND_BLUE", "#2C81FE"), stroke_width=2.5)
            line.next_to(title_m, DOWN, buff=0.10, aligned_edge=LEFT)
            header_grp = VGroup(title_m, line).to_corner(UL, buff=0.42)
            is_70_sme = str(globals().get('SME_LAYOUT', '')).strip() == '70'
            if is_70_sme:
                header_grp.move_to([-0.8 + header_grp.width / 2.0, 3.25, 0])
            if len(text_args) > 1 and str(text_args[1]).strip():
                sub_text = CrispText(str(text_args[1]), size=16, font="Open Sans", weight=SEMIBOLD, color=globals().get("TEXT_COLOR", "#404040"), autowrap=False)
                if hasattr(sub_text, 'width') and sub_text.width > (7.2 if is_70_sme else 8.5):
                    sub_text.scale_to_fit_width(7.2 if is_70_sme else 8.5)
                sub_text.next_to(header_grp, DOWN, buff=0.15, aligned_edge=LEFT)
                title_grp = VGroup(header_grp, sub_text)
            else:
                sub_text = None
                title_grp = header_grp
            title_grp.header_grp = header_grp
            title_grp.sub_text = sub_text
            title_grp.title_m = title_m
            header_grp.title_m = title_m
            title_grp.line = line
            header_grp.line = line
            title_grp.set_z_index(20)
            title_grp.is_persistent = True
            title_grp.is_title = True
            title_grp.name = "title_group"
            return title_grp

        def create_title_group(*args, **kwargs):
            return create_title(*args, **kwargs)

        def create_header_title(*args, **kwargs):
            return create_title(*args, **kwargs)

        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)

        def create_premise(*args, **kwargs):
            return NullMobject()

        def create_premise_box(*args, **kwargs):
            return NullMobject()

        def create_takeaway(*args, **kwargs):
            return create_pill(*args, **kwargs)

        def create_takeaway_banner(*args, **kwargs):
            return create_pill(*args, **kwargs)

        def create_pill(*args, **kwargs):
            bg_color = None
            text_color = None
            font_size = 12
            texts = []
            icon_mob = None
            def _is_color_arg_local(x):
                if type(x).__name__ in ('Color', 'ManimColor'):
                    return True
                s = str(x).strip()
                if s.startswith("#") and len(s) in (4, 7, 9):
                    return True
                if s.startswith("C_") or s.upper() in (
                    "WHITE", "BLACK", "RED", "BLUE", "GREEN", "YELLOW", "PURPLE", "ORANGE", 
                    "GREY", "GRAY", "DARK_BLUE", "LIGHT_BLUE", "C_DARK_BLUE", "C_LIGHT_BLUE",
                    "C_PURPLE", "C_RED", "C_YELLOW", "C_WHITE", "C_BLACK"
                ):
                    return True
                return False
            for a in args:
                if isinstance(a, (int, float)) and not isinstance(a, bool):
                    font_size = a
                elif hasattr(a, "animate") or hasattr(a, "get_center"):
                    icon_mob = a
                elif _is_color_arg_local(a):
                    if bg_color is None:
                        bg_color = a
                    elif text_color is None:
                        text_color = a
                else:
                    texts.append(str(a))
            texts = [t for t in texts if not _is_color_arg_local(t)]
            if "bg_color" in kwargs: bg_color = kwargs.pop("bg_color")
            if "text_color" in kwargs: text_color = kwargs.pop("text_color")
            if "font_size" in kwargs: font_size = kwargs.pop("font_size")
            if bg_color is None: bg_color = globals().get("C_DARK_BLUE", "#1E293B")
            _light_bg = str(bg_color).upper() in ("WHITE", "#FFFFFF", "C_WHITE", "#F0F4F8", "#F8FAFC", "#FEF3C7", "#F9C72C", "C_YELLOW", "#FFF", "#FFFFFE", "#FAFAFA", "#E2E8F0")
            if text_color is None:
                text_color = globals().get("TEXT_COLOR", "#404040") if _light_bg else globals().get("C_WHITE", "#FFFFFF")
            elif _light_bg and str(text_color).upper() in ("WHITE", "#FFFFFF", "C_WHITE", "#FFF"):
                text_color = globals().get("TEXT_COLOR", "#404040")
            try: font_size = float(font_size)
            except: font_size = 12.0
            full_text = "\n".join(texts) if texts else " "
            clean_kw = {k: v for k, v in kwargs.items() if k in ("autowrap", "wrap", "disable_wrap", "disable_autowrap", "align")}
            txt = CrispText(full_text, size=font_size, font="Open Sans", weight=BOLD, color=text_color, **clean_kw)
            content = VGroup(icon_mob, txt).arrange(RIGHT, buff=0.15) if icon_mob else txt
            w = max(kwargs.get("width", 0) or 0, content.width + 0.55)
            if kwargs.get("width") and kwargs.get("autowrap") is False and content.width > (kwargs["width"] - 0.4):
                content.scale_to_fit_width(kwargs["width"] - 0.4)
            h = max(kwargs.get("height", 0) or 0.38, content.height + 0.22)
            pill = RoundedRectangle(corner_radius=min(h/2, 0.25), width=w, height=h, fill_color=bg_color, fill_opacity=1.0, stroke_width=0)
            content.move_to(pill.get_center())
            return VGroup(pill, content).set_z_index(20)

        def create_state_badge(text_str, badge_type='violation', width=None, **kwargs):
            c_red = globals().get("C_CORAL", globals().get("C_RED", "#E58F6D"))
            c_text = globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))
            c_white = globals().get("C_WHITE", "#FFFFFF")
            col = c_red if badge_type == "violation" else (c_text if badge_type == "info" else "#2D6A4F")
            return create_pill(text_str, col, c_white, font_size=12, width=width).set_z_index(20)

        def create_leader_callout(target_mob, text_str, direction=UP, line_len=0.9, **kwargs):
            c_dark_blue = globals().get("C_BRAND_BLUE", "#2C81FE")
            c_light_blue = globals().get("C_SKY_BLUE", globals().get("C_LIGHT_BLUE", "#62B7E4"))
            c_text = globals().get("TEXT_COLOR", "#404040")
            c_white = globals().get("C_WHITE", "#FFFFFF")
            dot = Dot(radius=0.06, color=c_dark_blue)
            dot.move_to(target_mob.get_edge_center(direction))
            line_end = dot.get_center() + direction * line_len
            line = Line(dot.get_center(), line_end, stroke_width=1.5, color=c_dark_blue)
            txt = CrispText(text_str, size=13, font="Open Sans", weight=BOLD, color=c_text)
            txt.next_to(line_end, direction, buff=0.15)
            bg = RoundedRectangle(corner_radius=0.074, width=txt.width + 0.35, height=txt.height + 0.22, fill_color=c_white, fill_opacity=1, stroke_color=c_light_blue, stroke_width=1.2)
            fit_into_box(txt, bg)
            return VGroup(dot, line, bg, txt).set_z_index(20)

        def create_strikethrough(target_mob, color=None, stroke_width=3, **kwargs):
            c_red = globals().get("C_CORAL", globals().get("C_RED", "#E58F6D"))
            col = color if color is not None else c_red
            line = Line(target_mob.get_corner(DL) + LEFT * 0.08, target_mob.get_corner(UR) + RIGHT * 0.08, color=col, stroke_width=stroke_width)
            return line.set_z_index(10)

        def safe_image(path, height=1.0, width=None, **kwargs):
            resolved = None
            raw_s = str(path)
            for cand in [raw_s, f"{raw_s}.png", f"{raw_s}.jpg", os.path.basename(raw_s), os.path.basename(raw_s) + ".png"]:
                if os.path.isfile(cand):
                    resolved = cand
                    break
                for folder in ["images", "../images"]:
                    p = os.path.join(folder, cand)
                    if os.path.isfile(p):
                        resolved = p
                        break
                if resolved:
                    break
            if resolved:
                try:
                    img = ImageMobject(resolved)
                    if height: img.scale_to_fit_height(height)
                    elif width: img.scale_to_fit_width(width)
                    return Group(img)
                except: pass
            h = height if height else 1.0
            w = width if width else h
            box = RoundedRectangle(corner_radius=0.074, height=h, width=w, color=globals().get("C_SKY_BLUE", "#62B7E4"), fill_opacity=0.15, stroke_width=1.5)
            lbl = CrispText("Asset", size=11, font="Open Sans", color=globals().get("TEXT_COLOR", "#404040"))
            lbl.move_to(box.get_center())
            return VGroup(box, lbl)

        def create_safe_image(*args, **kwargs):
            return safe_image(*args, **kwargs)

        def create_checkmark(*args, **kwargs):
            c = kwargs.get('color', globals().get('C_STEEL_BLUE', '#7EA2C8'))
            for a in args:
                if isinstance(a, str) and (a.startswith('#') or a in globals()):
                    c = a
            sz = kwargs.get('size', kwargs.get('font_size', 0.22))
            if isinstance(sz, (int, float)) and sz > 1.0:
                sz = sz / 60.0
            sw = kwargs.get('stroke_width', 3.5)
            p1 = ORIGIN
            p2 = p1 + RIGHT * (sz * 0.42) + DOWN * (sz * 0.55)
            p3 = p2 + RIGHT * (sz * 0.95) + UP * (sz * 1.15)
            l1 = Line(p1, p2, color=c, stroke_width=sw)
            l2 = Line(p2, p3, color=c, stroke_width=sw)
            g = VGroup(l1, l2)
            g.center()
            return g

        def create_crossmark(*args, **kwargs):
            c = kwargs.get('color', globals().get('C_CORAL', '#E58F6D'))
            for a in args:
                if isinstance(a, str) and (a.startswith('#') or a in globals()):
                    c = a
            sz = kwargs.get('size', kwargs.get('font_size', 0.22))
            if isinstance(sz, (int, float)) and sz > 1.0:
                sz = sz / 60.0
            sw = kwargs.get('stroke_width', 3.5)
            l1 = Line(ORIGIN, RIGHT * (sz * 0.8) + UP * (sz * 0.8), color=c, stroke_width=sw)
            l2 = Line(ORIGIN + UP * (sz * 0.8), RIGHT * (sz * 0.8), color=c, stroke_width=sw)
            g = VGroup(l1, l2)
            g.center()
            return g

        self.create_title = create_title
        self.create_title_group = create_title_group
        self.create_header_title = create_header_title
        self.create_header = create_header
        self.create_pill = create_pill
        self.create_state_badge = create_state_badge
        self.create_leader_callout = create_leader_callout
        self.create_strikethrough = create_strikethrough
        self.safe_image = safe_image
        self.create_safe_image = create_safe_image
        self.create_checkmark = create_checkmark
        self.create_crossmark = create_crossmark
        self.fit_into_box = fit_into_box
        self.clamp_to_screen = clamp_to_screen


        # Assign global helper functions to self for use within the scene


        ## Presentation Step 1: Unified Chassis Overview
        # Narration: Four fundamental components inside every AI agent
        # Step Title: Four Pillars of AI Agent Architecture

        current_scene_title = "Four Pillars of AI Agent Architecture"
        title_group = create_title(current_scene_title)
        self.play(FadeIn(title_group, shift=DOWN * 0.1), run_time=0.8)
        self.sync_to(0.0) # Sync point for the start of narration (0.0s for total 69.06s)

        # Define common styling for pillar components
        pillar_box_width = 2.8
        pillar_box_height = 1.6
        pillar_corner_radius = 0.15
        pillar_fill_color = "#FFFFFF"
        pillar_stroke_color = C_STEEL_BLUE
        pillar_stroke_width = 2

        # Define positions for the four pillars around a central core
        # Diagram centered at (0, -0.7) to respect content ceiling (y <= 1.8) and floor (y >= -3.5)
        center_y = -0.7
        center_x = 0

        # Central AI Agent Core
        ai_core_radius = 0.8
        ai_core = Circle(
            radius=ai_core_radius,
            fill_color=C_WARM_AMBER,
            fill_opacity=0.8,
            stroke_color=C_WARM_AMBER,
            stroke_width=3,
        ).move_to([center_x, center_y, 0])
        ai_core_label = CrispText(
            "AI Agent",
            size=FONT_SIZE_COMPONENT_HEADER_MANIM,
            weight=BOLD,
            color="#FFFFFF"
        ).move_to(ai_core.get_center())
        
        # Ambient pulse for AI Core
        pulse_tracker = ValueTracker(0)
        ai_core_pulse = always_redraw(
            lambda: Circle(
                radius=ai_core_radius * (1 + 0.05 * np.sin(pulse_tracker.get_value() * PI)),
                stroke_color=C_WARM_AMBER,
                stroke_width=3,
                fill_opacity=0
            ).move_to(ai_core.get_center())
        )
        ai_core_pulse.add_updater(lambda m, dt: pulse_tracker.increment_value(2 * dt))

        ai_core_group = VGroup(ai_core, ai_core_label)

        # Pillar positions relative to the core
        pillar_spacing_x = 3.5
        pillar_spacing_y = 2.0

        # 1. Perception Pillar (Top)
        perception_pos = [center_x, center_y + pillar_spacing_y, 0]
        perception_box = RoundedRectangle(
            width=pillar_box_width, height=pillar_box_height, corner_radius=pillar_corner_radius,
            fill_color=pillar_fill_color, fill_opacity=1.0,
            stroke_color=pillar_stroke_color, stroke_width=pillar_stroke_width
        ).move_to(perception_pos)
        perception_label = CrispText(
            "Perception", size=FONT_SIZE_COMPONENT_HEADER_MANIM, weight=BOLD, color=C_HEADER_DARK
        ).move_to(perception_box.get_center() + UP * 0.3)
        # Icon for Perception (radar dish with sweeping line)
        radar_dish = Arc(radius=0.3, start_angle=PI/4, angle=PI/2, arc_center=perception_box.get_center() + DOWN * 0.15, stroke_width=3, color=C_MINT_SEAFOAM)
        radar_line_tracker = ValueTracker(0)
        radar_sweep = always_redraw(
            lambda: Line(
                radar_dish.get_arc_center(),
                radar_dish.get_arc_center() + rotate_vector(UP * 0.3, radar_line_tracker.get_value()),
                stroke_width=3,
                color=C_MINT_SEAFOAM
            )
        )
        radar_sweep.add_updater(lambda m, dt: radar_line_tracker.increment_value(PI * dt / 2)) # Rotates 180 deg every 2 seconds
        perception_icon_group = VGroup(radar_dish, radar_sweep)
        perception_group = VGroup(perception_box, perception_label, perception_icon_group)

        # 2. Memory Pillar (Right)
        memory_pos = [center_x + pillar_spacing_x, center_y, 0]
        memory_box = RoundedRectangle(
            width=pillar_box_width, height=pillar_box_height, corner_radius=pillar_corner_radius,
            fill_color=pillar_fill_color, fill_opacity=1.0,
            stroke_color=pillar_stroke_color, stroke_width=pillar_stroke_width
        ).move_to(memory_pos)
        memory_label = CrispText(
            "Memory", size=FONT_SIZE_COMPONENT_HEADER_MANIM, weight=BOLD, color=C_HEADER_DARK
        ).move_to(memory_box.get_center() + UP * 0.3)
        # Icon for Memory (stacked disks)
        disk1 = Ellipse(width=0.8, height=0.2, fill_color=C_SOFT_LILAC, fill_opacity=0.8, stroke_color=C_SOFT_LILAC, stroke_width=1).move_to(memory_box.get_center() + DOWN * 0.1)
        disk2 = disk1.copy().shift(DOWN * 0.15)
        disk3 = disk2.copy().shift(DOWN * 0.15)
        memory_icon = VGroup(disk1, disk2, disk3).move_to(memory_box.get_center() + DOWN * 0.2)
        memory_group = VGroup(memory_box, memory_label, memory_icon)

        # 3. Reasoning Pillar (Bottom)
        reasoning_pos = [center_x, center_y - pillar_spacing_y, 0]
        reasoning_box = RoundedRectangle(
            width=pillar_box_width, height=pillar_box_height, corner_radius=pillar_corner_radius,
            fill_color=pillar_fill_color, fill_opacity=1.0,
            stroke_color=pillar_stroke_color, stroke_width=pillar_stroke_width
        ).move_to(reasoning_pos)
        reasoning_label = CrispText(
            "Reasoning", size=FONT_SIZE_COMPONENT_HEADER_MANIM, weight=BOLD, color=C_HEADER_DARK
        ).move_to(reasoning_box.get_center() + UP * 0.3)
        # Icon for Reasoning (stylized neural network nodes)
        brain_center = reasoning_box.get_center() + DOWN * 0.2
        brain_curve1 = Arc(radius=0.4, start_angle=PI/2, angle=PI, arc_center=brain_center + LEFT * 0.1, color=C_LAVENDER_PERIWINKLE, stroke_width=3)
        brain_curve2 = Arc(radius=0.4, start_angle=PI/2, angle=-PI, arc_center=brain_center + RIGHT * 0.1, color=C_LAVENDER_PERIWINKLE, stroke_width=3)
        neural_node1 = Dot(point=brain_center + LEFT * 0.2 + UP * 0.1, radius=0.08, color=C_LAVENDER_PERIWINKLE)
        neural_node2 = Dot(point=brain_center + RIGHT * 0.2 + DOWN * 0.1, radius=0.08, color=C_LAVENDER_PERIWINKLE)
        reasoning_icon = VGroup(brain_curve1, brain_curve2, neural_node1, neural_node2)
        reasoning_group = VGroup(reasoning_box, reasoning_label, reasoning_icon)

        # 4. Action Pillar (Left)
        action_pos = [center_x - pillar_spacing_x, center_y, 0]
        action_box = RoundedRectangle(
            width=pillar_box_width, height=pillar_box_height, corner_radius=pillar_corner_radius,
            fill_color=pillar_fill_color, fill_opacity=1.0,
            stroke_color=pillar_stroke_color, stroke_width=pillar_stroke_width
        ).move_to(action_pos)
        action_label = CrispText(
            "Action", size=FONT_SIZE_COMPONENT_HEADER_MANIM, weight=BOLD, color=C_HEADER_DARK
        ).move_to(action_box.get_center() + UP * 0.3)
        # Icon for Action (rotating gear)
        gear_outer = Circle(radius=0.4, stroke_width=3, color=C_WARM_AMBER)
        gear_inner = Circle(radius=0.2, fill_color=C_WARM_AMBER, fill_opacity=1, stroke_opacity=0)
        tooth_rect = Rectangle(width=0.15, height=0.15, color=C_WARM_AMBER, fill_opacity=1)
        gear_teeth = VGroup(
            tooth_rect.copy().move_to(gear_outer.point_at_angle(PI/4)).rotate(PI/4),
            tooth_rect.copy().move_to(gear_outer.point_at_angle(3*PI/4)).rotate(3*PI/4),
            tooth_rect.copy().move_to(gear_outer.point_at_angle(5*PI/4)).rotate(5*PI/4),
            tooth_rect.copy().move_to(gear_outer.point_at_angle(7*PI/4)).rotate(7*PI/4)
        )
        gear_icon = VGroup(gear_outer, gear_inner, gear_teeth).move_to(action_box.get_center() + DOWN * 0.2)
        gear_icon.add_updater(lambda m, dt: m.rotate(0.5 * dt)) # Rotates slowly
        action_group = VGroup(action_box, action_label, gear_icon)

        # Connectors (Arrows to/from AI Core)
        arrow_config = {"buff": 0.1, "stroke_width": 2.5, "max_tip_length_to_length_ratio": 0.15, "color": C_BODY_DARK}

        arrow_p_core = Arrow(perception_box.get_bottom(), ai_core.get_top(), **arrow_config, color=C_SKY_BLUE)
        arrow_m_core = Arrow(memory_box.get_left(), ai_core.get_right(), **arrow_config, color=C_SOFT_LILAC)
        arrow_r_core = Arrow(reasoning_box.get_top(), ai_core.get_bottom(), **arrow_config, color=C_LAVENDER_PERIWINKLE)
        arrow_core_a = Arrow(ai_core.get_left(), action_box.get_right(), **arrow_config, color=C_WARM_AMBER)

        # Group all elements for initial display and persistence
        all_pillars = VGroup(perception_group, memory_group, reasoning_group, action_group)
        all_arrows = VGroup(arrow_p_core, arrow_m_core, arrow_r_core, arrow_core_a)

        # Initial animation: Introduce AI Core and then all pillars as a unified chassis
        self.play(FadeIn(ai_core_group, scale=0.8), run_time=1.0)
        self.add(ai_core_pulse) # Add pulse updater for AI Core
        self.add(perception_icon_group[1]) # Add radar sweep updater
        self.add(action_group[2]) # Add gear rotation updater

        self.play(
            LaggedStart(
                FadeIn(perception_group, shift=DOWN*0.5),
                FadeIn(memory_group, shift=LEFT*0.5),
                FadeIn(reasoning_group, shift=UP*0.5),
                FadeIn(action_group, shift=RIGHT*0.5),
                lag_ratio=0.3,
                run_time=3.0
            )
        )
        self.play(
            LaggedStart(
                Create(arrow_p_core),
                Create(arrow_m_core),
                Create(arrow_r_core),
                Create(arrow_core_a),
                lag_ratio=0.2,
                run_time=2.0
            )
        )
        
        # Hold for the remainder of Step 1 narration (total 69.06s)
        self.wait(max(0.1, 69.06 - getattr(self.renderer, "time", 0.0)))


        ## Presentation Step 2: Perception Layer
        # Narration: Sensory ingress: telemetry, API payloads, document streams
        self.sync_to(69.06 + 1.0) # Arbitrary sync point after previous narration ends

        # Highlight Perception pillar
        perception_highlight = perception_group.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5, corner_radius=pillar_corner_radius)
        self.play(Create(perception_highlight), run_time=0.6)

        # Add details about Perception
        input_details_label = CrispText("Data Streams:", size=FONT_SIZE_BADGE_MANIM, color=C_TEXT, weight=BOLD)
        telemetry_text = CrispText("Telemetry", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        api_payloads_text = CrispText("API Payloads", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        document_streams_text = CrispText("Document Streams", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        
        input_details_content = VGroup(telemetry_text, api_payloads_text, document_streams_text).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        input_details_group = VGroup(input_details_label, input_details_content).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        input_details_group.next_to(perception_group, UP, buff=0.3).align_to(perception_group, LEFT).shift(LEFT * 0.5)

        # Animate data flowing into perception box
        dot_color = C_SKY_BLUE
        dot_radius = 0.05
        path_offset_y = 0.8
        path_start_left = perception_group.get_top() + UP * path_offset_y + LEFT * 0.7
        path_start_center = perception_group.get_top() + UP * path_offset_y
        path_start_right = perception_group.get_top() + UP * path_offset_y + RIGHT * 0.7
        path_end_target = perception_box.get_top() + UP * 0.1
        
        stream_path1 = Line(path_start_left, path_end_target + LEFT * 0.5, stroke_opacity=0)
        stream_path2 = Line(path_start_center, path_end_target, stroke_opacity=0)
        stream_path3 = Line(path_start_right, path_end_target + RIGHT * 0.5, stroke_opacity=0)
        
        data_dot1 = Dot(color=dot_color, radius=dot_radius).move_to(stream_path1.get_start())
        data_dot2 = Dot(color=dot_color, radius=dot_radius).move_to(stream_path2.get_start())
        data_dot3 = Dot(color=dot_color, radius=dot_radius).move_to(stream_path3.get_start())

        self.play(
            FadeIn(input_details_group),
            run_time=1.0
        )
        self.play(
            MoveAlongPath(data_dot1, stream_path1, rate_func=ease_out_cubic, run_time=1.5), # Fixed rate_func
            MoveAlongPath(data_dot2, stream_path2, rate_func=ease_out_cubic, run_time=1.5), # Fixed rate_func
            MoveAlongPath(data_dot3, stream_path3, rate_func=ease_out_cubic, run_time=1.5), # Fixed rate_func
            FadeIn(data_dot1, data_dot2, data_dot3),
            run_time=1.5
        )
        self.remove(data_dot1, data_dot2, data_dot3)
        
        self.wait(2.0) # Hold for narration
        self.play(FadeOut(input_details_group), run_time=0.5)
        self.play(FadeOut(perception_highlight), run_time=0.4)
        self.wait(1.0)


        ## Presentation Step 3: Memory Component
        # Narration: Short-term operational context and long-term state storage
        self.sync_to(69.06 + 1.0 + 8.0) # Arbitrary sync point

        # Highlight Memory pillar
        memory_highlight = memory_group.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5, corner_radius=pillar_corner_radius)
        self.play(Create(memory_highlight), run_time=0.6)

        # Add details for Memory
        memory_types_label = CrispText("Memory Types:", size=FONT_SIZE_BADGE_MANIM, color=C_TEXT, weight=BOLD)
        short_term_text = CrispText("Short-term Context", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        long_term_text = CrispText("Long-term Storage", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        
        memory_details_content = VGroup(short_term_text, long_term_text).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        memory_details_group = VGroup(memory_types_label, memory_details_content).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        memory_details_group.next_to(memory_group, UP, buff=0.3).align_to(memory_group, LEFT) # Positioned above and left-aligned

        self.play(
            FadeIn(memory_details_group),
            run_time=1.0
        )
        # Animate data flowing into memory from core
        data_flow_dot = Dot(color=C_SOFT_LILAC, radius=dot_radius).move_to(ai_core.get_right())
        path_core_to_memory = Line(ai_core.get_right(), memory_box.get_left())
        self.play(MoveAlongPath(data_flow_dot, path_core_to_memory, rate_func=ease_out_cubic, run_time=1.0)) # Fixed rate_func
        self.remove(data_flow_dot)

        self.wait(2.0)
        self.play(FadeOut(memory_details_group), run_time=0.5)
        self.play(FadeOut(memory_highlight), run_time=0.4)
        self.wait(1.0)


        ## Presentation Step 4: Reasoning Engine
        # Narration: Deliberation, LLM cognitive planning, and decision-making logic
        self.sync_to(69.06 + 1.0 + 8.0 + 8.0) # Arbitrary sync point

        # Highlight Reasoning pillar
        reasoning_highlight = reasoning_group.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5, corner_radius=pillar_corner_radius)
        self.play(Create(reasoning_highlight), run_time=0.6)

        # Add details for Reasoning
        reasoning_logic_label = CrispText("Logic:", size=FONT_SIZE_BADGE_MANIM, color=C_TEXT, weight=BOLD)
        deliberation_text = CrispText("Deliberation", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        llm_planning_text = CrispText("LLM Planning", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        decision_logic_text = CrispText("Decision-Making", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        
        reasoning_details_content = VGroup(deliberation_text, llm_planning_text, decision_logic_text).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        reasoning_details_group = VGroup(reasoning_logic_label, reasoning_details_content).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        reasoning_details_group.next_to(reasoning_group, DOWN, buff=0.3).align_to(reasoning_group, LEFT)

        self.play(
            FadeIn(reasoning_details_group),
            run_time=1.0
        )
        # Animate neural activity in the icon
        neural_pulse_dot = Dot(color=C_LAVENDER_PERIWINKLE, radius=dot_radius).move_to(neural_node1.get_center())
        path_nodes = [neural_node1.get_center(), brain_center, neural_node2.get_center()]
        neural_path = VMobject().set_points_as_corners(path_nodes)
        self.play(MoveAlongPath(neural_pulse_dot, neural_path, rate_func=ease_out_cubic, run_time=1.0)) # Fixed rate_func
        self.remove(neural_pulse_dot)

        self.wait(2.0)
        self.play(FadeOut(reasoning_details_group), run_time=0.5)
        self.play(FadeOut(reasoning_highlight), run_time=0.4)
        self.wait(1.0)


        ## Presentation Step 5: Action Layer
        # Narration: Effectors: tool execution, database updates, actuator dispatch
        self.sync_to(69.06 + 1.0 + 8.0 + 8.0 + 8.0) # Arbitrary sync point

        # Highlight Action pillar
        action_highlight = action_group.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5, corner_radius=pillar_corner_radius)
        self.play(Create(action_highlight), run_time=0.6)

        # Add details for Action
        effectors_label = CrispText("Effectors:", size=FONT_SIZE_BADGE_MANIM, color=C_TEXT, weight=BOLD)
        tool_exec_text = CrispText("Tool Execution", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        db_updates_text = CrispText("Database Updates", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        actuator_dispatch_text = CrispText("Actuator Dispatch", size=FONT_SIZE_BODY_MANIM, color=C_BODY_DARK)
        
        action_details_content = VGroup(tool_exec_text, db_updates_text, actuator_dispatch_text).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        action_details_group = VGroup(effectors_label, action_details_content).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
        action_details_group.next_to(action_group, RIGHT, buff=0.3).align_to(action_group, UP) # Positioned right and top-aligned

        self.play(
            FadeIn(action_details_group),
            run_time=1.0
        )
        # Animate action dispatch from core to action box
        action_dot = Dot(color=C_WARM_AMBER, radius=dot_radius).move_to(ai_core.get_left())
        path_core_to_action = Line(ai_core.get_left(), action_box.get_right())
        self.play(MoveAlongPath(action_dot, path_core_to_action, rate_func=ease_out_cubic, run_time=1.0)) # Fixed rate_func
        self.remove(action_dot)

        self.wait(2.0)
        self.play(FadeOut(action_details_group), run_time=0.5)
        self.play(FadeOut(action_highlight), run_time=0.4)
        self.wait(1.0)


        ## Presentation Step 6: Cohesive Integration
        # Narration: Inter-pillar synergy enabling autonomous operations
        self.sync_to(69.06 + 1.0 + 8.0 + 8.0 + 8.0 + 8.0) # Arbitrary sync point

        # Highlight the entire system (all pillars and core)
        system_highlight_perimeter = VGroup(
            perception_box, memory_box, reasoning_box, action_box, ai_core
        ).copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5, corner_radius=pillar_corner_radius)
        
        self.play(Create(system_highlight_perimeter), run_time=1.0)

        integration_text = CrispText(
            "Cohesive Integration: Inter-pillar Synergy",
            size=FONT_SIZE_COMPONENT_HEADER_MANIM,
            weight=BOLD,
            color=C_HEADER_DARK
        ).move_to([0, -3.0, 0]) # Position at the bottom of the safe area

        self.play(FadeIn(integration_text, shift=UP*0.5), run_time=1.0)
        
        # Add a feedback loop arrow from Action back to Perception
        feedback_arrow = CurvedArrow(
            action_group.get_bottom() + LEFT * 0.5,
            perception_group.get_top() + LEFT * 0.5,
            tip_length=0.15,
            stroke_width=2.5,
            color=C_MINT_SEAFOAM,
            angle=-PI/2 # Curve upwards and left
        )
        feedback_label = CrispText("Feedback Loop", size=FONT_SIZE_BADGE_MANIM, color=C_MINT_SEAFOAM).next_to(feedback_arrow, LEFT, buff=0.1)

        self.play(Create(feedback_arrow), FadeIn(feedback_label), run_time=1.5)
        
        # Define a path for a dot to flow through the main cycle, emphasizing continuous operation.
        loop_path_mobject = VMobject()
        loop_path_mobject.set_points_as_corners([
            perception_box.get_top() + UP * 0.3, # Start point for continuous flow
            perception_box.get_bottom(),
            ai_core.get_top(),
            ai_core.get_right(), # Added path points to cover memory
            memory_box.get_left(),
            memory_box.get_bottom(), # Added path points to cover reasoning
            ai_core.get_bottom(),
            reasoning_box.get_top(),
            reasoning_box.get_bottom(),
            ai_core.get_left(),
            action_box.get_right(),
            action_box.get_bottom(),
            feedback_arrow.get_start(),
            feedback_arrow.get_end(),
            perception_box.get_top() + UP * 0.3 # Loop back to start
        ])
        loop_path_mobject.set_stroke(opacity=0) # Make path invisible

        cycle_dot = Dot(color=C_HIGHLIGHT_ORANGE, radius=0.08)
        
        # Add updater for continuous movement along the path
        path_tracker = ValueTracker(0) # 0 to 1, representing proportion along the path
        cycle_dot.add_updater(
            lambda m, dt: m.move_to(loop_path_mobject.point_from_proportion(path_tracker.get_value()))
        )
        path_tracker.add_updater(
            lambda m, dt: m.set_value((m.get_value() + dt / 10.0) % 1) # Full loop every 10 seconds
        )

        self.add(cycle_dot)
        
        self.wait(10.0) # Let the dot flow for a while

        # Clean up for next scene / end of presentation
        self.play(
            FadeOut(system_highlight_perimeter),
            FadeOut(integration_text),
            FadeOut(feedback_arrow),
            FadeOut(feedback_label),
            run_time=1.0
        )
        
        # Clear all updaters and remove their associated mobjects to ensure a clean state
        ai_core_pulse.clear_updaters()
        perception_icon_group[1].clear_updaters()
        action_group[2].clear_updaters()
        cycle_dot.clear_updaters()
        path_tracker.clear_updaters()
        
        self.remove(ai_core_pulse, perception_icon_group[1], action_group[2], cycle_dot)
        
        # Per "Persistence" rule, the core diagram elements (title, AI agent core, pillars, arrows)
        # remain on screen as they are the main instructional content of the scene.
        self.wait(1.0) # Final wait for scene end