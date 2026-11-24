C_BRAND_BLUE = "#2C81FE"
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_RED = "#E58F6D"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
C_DARK_BLUE = "#1E293B"
C_TEXT = "#404040"
C_YELLOW = "#DDB945"
import re
SME_LAYOUT = '70'
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
        import numpy as np
        return np.array([0.0, 0.0, 0.0])
    def get_top(self):
        import numpy as np
        return np.array([0.0, 0.0, 0.0])
    def get_bottom(self):
        import numpy as np
        return np.array([0.0, 0.0, 0.0])
    def get_left(self):
        import numpy as np
        return np.array([0.0, 0.0, 0.0])
    def get_right(self):
        import numpy as np
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
try:
    from manim.utils.rate_functions import *
except Exception:
    pass
import numpy as np
import manim.utils.rate_functions as _rf
for _k in dir(_rf):
    if not _k.startswith("_"):
        globals()[_k] = getattr(_rf, _k)




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


from feedback_functions.instrumented_scene import InstrumentedScene
from manim import *
import numpy as np
import os

# -------------------------------------------------------------------------
# Fallback helpers for execution environments where CrispText or InstrumentedScene
# might not be pre-injected into global scope.
# -------------------------------------------------------------------------
try:
    from template1_title_intro import CrispText
except ImportError:
    
    pass
class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        # 1. Canvas Setup (Modern Soft Light Slate Canvas)
        self.camera.background_color = "#F0F4F8"
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



        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)














        
        # Safe Workspace for Layout 70 (70% Left Split SME):
        # Left x <= -1.48 reserved for SME instructor video.
        # Active workspace: x in [-0.80, 6.40], y in [-3.50, 2.20], center x ~ +2.80.
        X_LEFT_SAFE = -0.80
        X_CENTER = 2.80
        Y_CEILING = 2.20
        
        # Color Palette Tokens (Approved 10-Color Infographic Pastel Palette)
        C_SKY = "#62B7E4"
        C_STEEL = "#7EA2C8"
        C_LAVENDER = "#9B99C7"
        C_MINT = "#8ECDB7"
        C_AMBER = "#E6A157"
        C_CORAL = "#E58F6D"
        C_ROSE = "#D98CA1"
        C_TEXT_MAIN = "#1E293B"
        C_TEXT_BODY = "#404040"
        C_WHITE = "#FFFFFF"
        C_ORANGE_ALERT = "#F78908"

        # -----------------------------------------------------------------
        # Header Construction Helper
        # -----------------------------------------------------------------

        # =================================================================
        ## Presentation Step 1: Monitoring Grid Performance
        # =================================================================
        # Narration: At Solara, an agent monitoring grid performance isn't
        # just waiting for someone to run a report. It's watching...
        
        title_group = create_title("Dynamic Interaction Example", "Monitoring Grid Performance")
        self.play(FadeIn(title_group, shift=DOWN * 0.15), run_time=0.8)

        # -----------------------------------------------------------------
        # Asset 1: Solara Site (Solar Panel Vector Mechanism)
        # -----------------------------------------------------------------
        site_center = np.array([0.70, 0.10, 0])
        
        # Stand and ground
        site_pole = Line(site_center + DOWN * 0.9, site_center + DOWN * 0.1, stroke_color=C_STEEL, stroke_width=4)
        site_base = Line(site_center + DOWN * 0.9 + LEFT * 0.6, site_center + DOWN * 0.9 + RIGHT * 0.6, stroke_color=C_STEEL, stroke_width=3)
        
        # Angled solar panel face
        panel_outline = Polygon(
            site_center + LEFT * 1.05 + UP * 0.55,
            site_center + RIGHT * 1.05 + UP * 0.55,
            site_center + RIGHT * 0.85 + DOWN * 0.35,
            site_center + LEFT * 0.85 + DOWN * 0.35,
            stroke_color=C_STEEL,
            fill_color=C_SKY,
            fill_opacity=0.35,
            stroke_width=2.5
        )
        # Solar cell grid lines
        panel_grid_v1 = Line(site_center + LEFT * 0.35 + UP * 0.55, site_center + LEFT * 0.28 + DOWN * 0.35, stroke_color=C_STEEL, stroke_width=1.5)
        panel_grid_v2 = Line(site_center + RIGHT * 0.35 + UP * 0.55, site_center + RIGHT * 0.28 + DOWN * 0.35, stroke_color=C_STEEL, stroke_width=1.5)
        panel_grid_h = Line(site_center + LEFT * 0.95 + UP * 0.10, site_center + RIGHT * 0.95 + UP * 0.10, stroke_color=C_STEEL, stroke_width=1.5)
        
        # Badge Label for Site
        site_pill_bg = RoundedRectangle(corner_radius=0.074, width=1.65, height=0.38, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_STEEL, stroke_width=1.5)
        site_pill_txt = CrispText("Solara Site Alpha", size=11, weight=BOLD, color=C_TEXT_MAIN)
        fit_into_box(site_pill_txt, site_pill_bg, pad_x=0.2, pad_y=0.08)
        site_pill = VGroup(site_pill_bg, site_pill_txt).next_to(site_base, DOWN, buff=0.15)
        solara_site_grp = VGroup(site_pole, site_base, panel_outline, panel_grid_v1, panel_grid_v2, panel_grid_h, site_pill)

        # -----------------------------------------------------------------
        # Asset 2: Performance Gauge (Dial with Dynamic Needle & Threshold)
        # -----------------------------------------------------------------
        gauge_center = site_center + UP * 1.45
        gauge_radius = 0.58
        
        # Arc Dial
        dial_bg = Arc(radius=gauge_radius, start_angle=0, angle=PI, arc_center=gauge_center, stroke_color="#CBD5E1", stroke_width=6)
        dial_normal = Arc(radius=gauge_radius, start_angle=PI * 0.35, angle=PI * 0.65, arc_center=gauge_center, stroke_color=C_MINT, stroke_width=6)
        dial_danger = Arc(radius=gauge_radius, start_angle=0, angle=PI * 0.35, arc_center=gauge_center, stroke_color=C_CORAL, stroke_width=6)
        
        # Threshold Indicator Marker
        thresh_angle = PI * 0.35
        thresh_pos = gauge_center + np.array([np.cos(thresh_angle), np.sin(thresh_angle), 0]) * (gauge_radius + 0.12)
        thresh_line = Line(
            gauge_center + np.array([np.cos(thresh_angle), np.sin(thresh_angle), 0]) * (gauge_radius - 0.15),
            thresh_pos,
            stroke_color=C_ROSE,
            stroke_width=2.5
        )
        thresh_label = CrispText("Threshold", size=9, weight=BOLD, color=C_ROSE).next_to(thresh_pos, UP + RIGHT, buff=0.05)
        
        # Needle (Pivot at gauge_center)
        needle_hub = Dot(gauge_center, radius=0.07, color=C_TEXT_MAIN)
        needle_angle_val = ValueTracker(PI * 0.85)  # Start healthy in green zone
        
        needle = always_redraw(lambda: Line(
            gauge_center,
            gauge_center + np.array([np.cos(needle_angle_val.get_value()), np.sin(needle_angle_val.get_value()), 0]) * (gauge_radius - 0.08),
            stroke_color=C_TEXT_MAIN,
            stroke_width=2.8
        ))
        
        gauge_badge = RoundedRectangle(corner_radius=0.06, width=1.45, height=0.32, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_STEEL, stroke_width=1.2)
        gauge_txt = CrispText("Grid Output", size=10, weight=BOLD, color=C_TEXT_MAIN)
        gauge_tag = VGroup(gauge_badge, gauge_txt).move_to(gauge_center + DOWN * 0.22)
        gauge_group = VGroup(dial_bg, dial_danger, dial_normal, thresh_line, thresh_label, needle_hub, needle, gauge_tag)

        # -----------------------------------------------------------------
        # Asset 3: Monitoring Agent AI Core Node
        # -----------------------------------------------------------------
        agent_center = np.array([3.40, 0.40, 0])
        
        # Rotating outer halo
        agent_halo = DashedVMobject(
            Circle(radius=0.78, arc_center=agent_center, stroke_color=C_SKY, stroke_width=1.8),
            num_dashes=14
        )
        agent_core_bg = Circle(radius=0.58, arc_center=agent_center, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_SKY, stroke_width=2.5)
        
        # Microchip icon inside agent core
        chip_box = Square(side_length=0.40, fill_color=C_SKY, fill_opacity=0.25, stroke_color=C_SKY, stroke_width=1.5).move_to(agent_center)
        chip_line1 = Line(agent_center + LEFT * 0.12, agent_center + RIGHT * 0.12, stroke_color=C_TEXT_MAIN, stroke_width=1.5)
        chip_line2 = Line(agent_center + UP * 0.12, agent_center + DOWN * 0.12, stroke_color=C_TEXT_MAIN, stroke_width=1.5)
        agent_icon = VGroup(chip_box, chip_line1, chip_line2)
        
        agent_label_bg = RoundedRectangle(corner_radius=0.074, width=1.70, height=0.38, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_SKY, stroke_width=1.5)
        agent_label_txt = CrispText("Monitoring Agent", size=11, weight=BOLD, color=C_TEXT_MAIN)
        fit_into_box(agent_label_txt, agent_label_bg, pad_x=0.2, pad_y=0.08)
        agent_pill = VGroup(agent_label_bg, agent_label_txt).next_to(agent_core_bg, DOWN, buff=0.15)
        agent_node = VGroup(agent_halo, agent_core_bg, agent_icon, agent_pill)

        # Telemetry arrow between gauge and agent
        telemetry_arrow = Arrow(gauge_center + RIGHT * 0.85, agent_center + LEFT * 0.75, buff=0.1, stroke_width=2.5, max_tip_length_to_length_ratio=0.2, color=C_STEEL)
        telemetry_label = CrispText("Perception Stream", size=10, weight=BOLD, color=C_STEEL).next_to(telemetry_arrow, UP, buff=0.08)

        # Introduce Solara Site, Gauge, and Agent
        self.play(
            GrowFromCenter(solara_site_grp),
            FadeIn(gauge_group, shift=DOWN * 0.2),
            run_time=1.4
        )
        self.wait(1.2)

        self.play(
            GrowFromCenter(agent_node),
            GrowArrow(telemetry_arrow),
            FadeIn(telemetry_label, shift=UP * 0.1),
            run_time=1.2
        )
        self.wait(1.5)

        # Needle drops below threshold (Simulation of sudden output drop)
        self.play(
            needle_angle_val.animate.set_value(PI * 0.18),
            run_time=2.2,
            rate_func=easeInOutCubic
        )
        
        # Red/Orange Alert Pulse on the Gauge
        alert_pulse = Circle(radius=0.62, arc_center=gauge_center, stroke_color=C_ORANGE_ALERT, stroke_width=3.5).set_fill(opacity=0)
        self.play(
            Create(alert_pulse),
            run_time=0.6
        )
        self.play(
            alert_pulse.animate.scale(1.35).set_stroke(opacity=0),
            run_time=0.8
        )
        self.remove(alert_pulse)

        # Perception signal particle moves to agent
        signal_particle = Dot(color=C_ORANGE_ALERT, radius=0.09).move_to(gauge_center + RIGHT * 0.85)
        self.play(
            MoveAlongPath(signal_particle, Line(gauge_center + RIGHT * 0.85, agent_center + LEFT * 0.75), rate_func=ease_out_cubic),
            run_time=1.0
        )
        self.remove(signal_particle)

        # Agent cognitive glow response
        agent_pulse = agent_core_bg.copy().set_fill(opacity=0).set_stroke(color=C_ORANGE_ALERT, width=3.5)
        self.play(
            Create(agent_pulse),
            agent_halo.animate.rotate(PI * 0.8),
            run_time=1.1
        )
        self.play(FadeOut(agent_pulse), run_time=0.5)
        self.wait(1.0)

        # -----------------------------------------------------------------
        # Asset 4: Decision Tree Sprouting to the Right
        # -----------------------------------------------------------------
        # Branches: Query Data, Cross-Ref Weather, Escalate Human
        tree_origin = agent_center + RIGHT * 0.75 + UP * 0.05
        
        target_branch1 = np.array([5.50, 1.40, 0])
        target_branch2 = np.array([5.50, 0.40, 0])
        target_branch3 = np.array([5.50, -0.60, 0])
        
        path1 = CubicBezier(tree_origin, tree_origin + RIGHT * 0.6 + UP * 0.4, target_branch1 + LEFT * 0.5, target_branch1, stroke_color=C_STEEL, stroke_width=2.0)
        path2 = Line(tree_origin, target_branch2, stroke_color=C_STEEL, stroke_width=2.0)
        path3 = CubicBezier(tree_origin, tree_origin + RIGHT * 0.6 + DOWN * 0.4, target_branch3 + LEFT * 0.5, target_branch3, stroke_color=C_STEEL, stroke_width=2.0)

        # Branch Option Cards / Badges
        card_w, card_h = 1.70, 0.45
        
        def create_branch_card(text, color):
            bg = RoundedRectangle(corner_radius=0.074, width=card_w, height=card_h, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=color, stroke_width=1.6)
            txt = CrispText(text, size=11, weight=BOLD, color=C_TEXT_MAIN)
            return VGroup(bg, txt)

        card_query = create_branch_card("Query Data", C_STEEL).move_to(target_branch1)
        card_weather = create_branch_card("Weather Data", C_LAVENDER).move_to(target_branch2)
        card_escalate = create_branch_card("Escalate Human", C_AMBER).move_to(target_branch3)

        self.play(
            Create(path1),
            Create(path2),
            Create(path3),
            FadeIn(card_query, shift=RIGHT * 0.2),
            FadeIn(card_weather, shift=RIGHT * 0.2),
            FadeIn(card_escalate, shift=RIGHT * 0.2),
            run_time=2.0
        )
        self.wait(1.5)

        # Highlight "Escalate Human" Branch as chosen Action
        highlight_box = card_escalate[0].copy().set_fill(opacity=0).set_stroke(color=C_ORANGE_ALERT, width=3.5)
        path3_glow = path3.copy().set_fill(opacity=0).set_stroke(color=C_ORANGE_ALERT, width=3.5)
        
        self.play(
            Create(path3_glow),
            Create(highlight_box),
            run_time=1.2
        )
        self.wait(1.0)

        # -----------------------------------------------------------------
        # Asset 5: Human Operator Vector Icon
        # -----------------------------------------------------------------
        human_pos = np.array([5.50, -1.75, 0])
        arrow_to_human = Arrow(target_branch3 + DOWN * 0.25, human_pos + UP * 0.40, buff=0.08, stroke_width=2.5, color=C_ORANGE_ALERT)
        
        # Human icon: head circle and shoulder arc
        human_head = Circle(radius=0.16, arc_center=human_pos + UP * 0.16, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_TEXT_MAIN, stroke_width=2.0)
        human_body = Arc(radius=0.30, start_angle=PI * 0.15, angle=PI * 0.70, arc_center=human_pos + DOWN * 0.15, stroke_color=C_TEXT_MAIN, stroke_width=2.2)
        human_pill = VGroup(
            RoundedRectangle(corner_radius=0.06, width=1.55, height=0.34, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_TEXT_MAIN, stroke_width=1.3),
            CrispText("Human Operator", size=10, weight=BOLD, color=C_TEXT_MAIN)
        ).next_to(human_body, DOWN, buff=0.12)
        human_operator_grp = VGroup(arrow_to_human, human_head, human_body, human_pill)

        self.play(
            GrowArrow(arrow_to_human),
            FadeIn(human_head, shift=DOWN * 0.1),
            Create(human_body),
            FadeIn(human_pill),
            run_time=1.5
        )

        # Action execution feedback packet
        action_packet = Dot(color=C_ORANGE_ALERT, radius=0.09).move_to(target_branch3)
        self.play(
            MoveAlongPath(action_packet, arrow_to_human),
            run_time=0.9
        )
        self.remove(action_packet)

        # Action Execution Status Pill
        action_pill = VGroup(
            RoundedRectangle(corner_radius=0.06, width=1.65, height=0.32, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_ORANGE_ALERT, stroke_width=1.5),
            CrispText("Action: Dispatched", size=10, weight=BOLD, color=C_ORANGE_ALERT)
        ).next_to(human_pill, DOWN, buff=0.10)
        
        self.play(FadeIn(action_pill, shift=UP * 0.1), run_time=0.8)

        # Ambient live rotation to avoid frozen canvas before step sync
        halo_updater = lambda m, dt: m.rotate(0.35 * dt)
        agent_halo.add_updater(halo_updater)
        
        # Sync with narration duration for Step 1 (~58.85s)
        self.sync_to(58.855)

        # =================================================================
        ## Presentation Step 2: Bi-Directional Relationship
        # =================================================================
        # Narration: The environment shapes the agent. The agent shapes the
        # environment. That bi-directional relationship is what makes agents...

        agent_halo.remove_updater(halo_updater)

        # Title transition
        new_title_group = create_title("Dynamic Interaction Example", "Bi-Directional Relationship")
        self.play(
            ReplacementTransform(title_group, new_title_group),
            FadeOut(card_query),
            FadeOut(card_weather),
            FadeOut(card_escalate),
            FadeOut(highlight_box),
            FadeOut(path1),
            FadeOut(path2),
            FadeOut(path3),
            FadeOut(path3_glow),
            FadeOut(human_operator_grp),
            FadeOut(action_pill),
            FadeOut(telemetry_arrow),
            FadeOut(telemetry_label),
            FadeOut(gauge_group),
            run_time=1.4
        )
        title_group = new_title_group

        # Reposition Solara Site (Environment) and Agent for symmetrical bi-directional loop
        env_pos = np.array([0.90, -0.10, 0])
        agent_target_pos = np.array([4.60, -0.10, 0])
        
        self.play(
            solara_site_grp.animate.move_to(env_pos),
            agent_node.animate.move_to(agent_target_pos),
            run_time=1.5
        )

        # -----------------------------------------------------------------
        # Bi-Directional Kinetic Arcs
        # Arc 1 (Top): Environment -> Agent ("Shapes Agent" / Perception)
        # Arc 2 (Bottom): Agent -> Environment ("Shapes Environment" / Action)
        # -----------------------------------------------------------------
        arc_start_top = env_pos + UP * 0.95 + RIGHT * 0.30
        arc_end_top = agent_target_pos + UP * 0.95 + LEFT * 0.30
        top_curve = CurvedArrow(arc_start_top, arc_end_top, angle=-0.55, stroke_width=3.2, color=C_SKY)
        
        arc_start_bottom = agent_target_pos + DOWN * 0.95 + LEFT * 0.30
        arc_end_bottom = env_pos + DOWN * 0.95 + RIGHT * 0.30
        bottom_curve = CurvedArrow(arc_start_bottom, arc_end_bottom, angle=-0.55, stroke_width=3.2, color=C_AMBER)

        # Labels for Bi-directional influences
        label_top_bg = RoundedRectangle(corner_radius=0.074, width=2.45, height=0.42, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_SKY, stroke_width=1.5)
        label_top_txt = CrispText("Shapes Agent (Perception)", size=11, weight=BOLD, color=C_TEXT_MAIN)
        fit_into_box(label_top_txt, label_top_bg, pad_x=0.2, pad_y=0.08)
        label_top = VGroup(label_top_bg, label_top_txt).next_to(top_curve, UP, buff=0.15)

        label_bottom_bg = RoundedRectangle(corner_radius=0.074, width=2.55, height=0.42, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=1.5)
        label_bottom_txt = CrispText("Shapes Environment (Action)", size=11, weight=BOLD, color=C_TEXT_MAIN)
        fit_into_box(label_bottom_txt, label_bottom_bg, pad_x=0.2, pad_y=0.08)
        label_bottom = VGroup(label_bottom_bg, label_bottom_txt).next_to(bottom_curve, DOWN, buff=0.15)

        # Central Cognitive Badge
        center_loop_pos = (env_pos + agent_target_pos) / 2.0
        badge_bg = RoundedRectangle(corner_radius=0.09, width=2.10, height=0.55, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=C_STEEL, stroke_width=2.0)
        badge_txt = CrispText("Bi-Directional", size=13, weight=BOLD, color=C_TEXT_MAIN)
        badge_sub = CrispText("Dynamic Closed Loop", size=9, weight=NORMAL, color="#64748B")
        badge_content = VGroup(badge_txt, badge_sub).arrange(DOWN, buff=0.04)
        center_badge = VGroup(badge_bg, badge_content).move_to(center_loop_pos)

        # Sub-nodes around agent: Perceive -> Reason -> Act
        pra_radius = 0.95
        p_pos = agent_target_pos + np.array([np.cos(PI * 0.75), np.sin(PI * 0.75), 0]) * pra_radius
        r_pos = agent_target_pos + np.array([0, 1.0, 0]) * pra_radius
        a_pos = agent_target_pos + np.array([np.cos(PI * 0.25), np.sin(PI * 0.25), 0]) * pra_radius

        def make_micro_pill(txt, color):
            bg = RoundedRectangle(corner_radius=0.05, width=0.85, height=0.30, fill_color=C_WHITE, fill_opacity=1.0, stroke_color=color, stroke_width=1.2)
            t = CrispText(txt, size=9, weight=BOLD, color=color)
            return VGroup(bg, t)

        pill_p = make_micro_pill("Perceive", C_SKY).move_to(p_pos)
        pill_r = make_micro_pill("Reason", C_LAVENDER).move_to(r_pos + UP * 0.15)
        pill_a = make_micro_pill("Act", C_AMBER).move_to(a_pos)
        pra_group = VGroup(pill_p, pill_r, pill_a)

        # Reveal Bi-directional arrows and badges
        self.play(
            Create(top_curve),
            FadeIn(label_top, shift=DOWN * 0.1),
            run_time=1.4
        )
        self.play(
            Create(bottom_curve),
            FadeIn(label_bottom, shift=UP * 0.1),
            run_time=1.4
        )
        self.play(
            GrowFromCenter(center_badge),
            FadeIn(pra_group, shift=UP * 0.15),
            run_time=1.2
        )

        # -----------------------------------------------------------------
        # Continuous Living Particle Loop (Environment <-> Agent)
        # -----------------------------------------------------------------
        particle_forward = Dot(color=C_SKY, radius=0.08)
        particle_return = Dot(color=C_AMBER, radius=0.08)
        
        # Kinetic particle travel across loop
        self.play(
            MoveAlongPath(particle_forward, top_curve, rate_func=ease_out_cubic),
            MoveAlongPath(particle_return, bottom_curve, rate_func=ease_out_cubic),
            run_time=2.2
        )
        self.remove(particle_forward, particle_return)

        # Attach ambient continuous updaters so the screen remains kinetic
        # and alive throughout the remainder of the narration.
        agent_halo.add_updater(halo_updater)
        
        # Subtle pulsing focus highlight on the bi-directional center badge
        badge_pulse = badge_bg.copy().set_fill(opacity=0).set_stroke(color=C_ORANGE_ALERT, width=3.0)
        self.play(
            Create(badge_pulse),
            run_time=1.0
        )
        self.play(
            badge_pulse.animate.scale(1.15).set_stroke(opacity=0),
            run_time=1.2
        )
        self.remove(badge_pulse)

        # Particle stream continuous loop
        def stream_cycle():
            p1 = Dot(color=C_SKY, radius=0.08)
            p2 = Dot(color=C_AMBER, radius=0.08)
            self.play(
                MoveAlongPath(p1, top_curve, rate_func=ease_out_cubic),
                MoveAlongPath(p2, bottom_curve, rate_func=ease_out_cubic),
                run_time=2.0
            )
            self.remove(p1, p2)

        # Run stream cycles while narrator completes explanation
        for _ in range(3):
            stream_cycle()

        agent_halo.remove_updater(halo_updater)

        # Exact audio synchronization for Step 2 (~36.65s, cumulative ~95.50s)
        self.sync_to(58.855 + 36.645)