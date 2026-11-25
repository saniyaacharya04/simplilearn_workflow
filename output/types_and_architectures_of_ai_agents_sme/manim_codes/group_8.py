C_DARK_BLUE = "#1E293B"
C_MINT = "#8ECDB7"
C_LAVENDER = "#9B99C7"
C_CORAL = "#E58F6D"
C_YELLOW = "#DDB945"
import os
import re
SME_LAYOUT = '70'
from manim import *
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
from manim_slides import Slide
from manim_slides.slides import InstrumentedScene
import numpy as np

# Custom Text for better control, ensuring Open Sans and default color


# Helper for a styled node (e.g., process step in a workflow)
class StyledNode(RoundedRectangle):
    def __init__(self, text_content, width=2.5, height=1.0, fill_color=WHITE, stroke_color=C_STEEL_BLUE, text_color=C_TEXT, corner_radius=0.074, text_size=0.2, **kwargs):
        super().__init__(
            width=width,
            height=height,
            corner_radius=corner_radius,
            fill_color=fill_color,
            fill_opacity=1.0,
            stroke_color=stroke_color,
            stroke_width=1.5,
            **kwargs
        )
        self.text_mob = CrispText(text_content, size=text_size, color=text_color, weight=SEMIBOLD)
        self.text_mob.move_to(self.center)
        self.add(self.text_mob)

    def get_text_mobject(self):
        return self.text_mob

# Helper for a styled pill/badge (e.g., criteria, labels)
class StyledPill(RoundedRectangle):
    def __init__(self, text_content, width=1.8, height=0.5, fill_color=WHITE, stroke_color=C_SKY_BLUE, text_color=C_TEXT, corner_radius=0.074, text_size=0.14, **kwargs):
        super().__init__(
            width=width,
            height=height,
            corner_radius=corner_radius,
            fill_color=fill_color,
            fill_opacity=1.0,
            stroke_color=stroke_color,
            stroke_width=1.5,
            **kwargs
        )
        self.text_mob = CrispText(text_content, size=text_size, color=text_color, weight=SEMIBOLD)
        self.text_mob.move_to(self.center)
        self.add(self.text_mob)
    
    def get_text_mobject(self):
        return self.text_mob

# Custom Agent Core visualization with internal animation
class AgentCore(VGroup):
    def __init__(self, text_content="Reasoning Engine", color=C_LAVENDER_PERIWINKLE, **kwargs):
        super().__init__(**kwargs)
        
        self.outer_shape = RoundedRectangle(width=2.8, height=1.8, corner_radius=0.3, fill_color=color, fill_opacity=0.8, stroke_color=color, stroke_width=2.5)
        
        self.inner_light = Circle(radius=0.5, fill_color=WHITE, fill_opacity=0.3, stroke_width=0)
        self.inner_gear = RegularPolygon(n=6, radius=0.6, stroke_color=WHITE, stroke_width=1.5, fill_opacity=0)
        
        self.text_mob = CrispText(text_content, size=6.0, color=WHITE, weight=BOLD)
        
        self.add(self.outer_shape, self.inner_light, self.inner_gear, self.text_mob)
        self.text_mob.move_to(self.outer_shape.center)
        self.inner_light.move_to(self.outer_shape.center)
        self.inner_gear.move_to(self.outer_shape.center)
        
        # Add continuous ambient animation to inner elements
        self.gear_updater = lambda m, dt: m.inner_gear.rotate(0.1 * dt)
        self.light_updater = lambda m, dt: m.inner_light.set_opacity(0.3 + 0.1 * np.sin(self.get_time() * 2)) 
        
        self.add_updater(self.gear_updater)
        self.add_updater(self.light_updater)

    def get_text_mobject(self):
        return self.text_mob

    def remove_updaters(self):
        self.remove_updater(self.gear_updater)
        self.remove_updater(self.light_updater)


class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        self.camera.background_color = C_BG
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


        # --- Initial Setup: Scene Title ---
        current_title_group = create_title("Architecture Type 3: Utility-Based Agents & Workflow")
        self.play(FadeIn(current_title_group, shift=UP * 0.1), run_time=0.8)
        
        # Define core diagram components (initially hidden or in minimal state)
        agent_core = AgentCore(text_content="Reasoning Engine").move_to(RIGHT * 2.8 + DOWN * 0.5)
        
        # Nodes for the lifecycle (will be positioned and revealed later)
        goal_ingestion_node = StyledNode("Goal Ingestion", stroke_color=C_SKY_BLUE, text_size=0.18)
        perception_node = StyledNode("Perception", stroke_color=C_MINT_SEAFOAM, text_size=0.18)
        action_execution_node = StyledNode("Action Execution", stroke_color=C_CORAL_PEACH, text_size=0.18)

        ## Presentation Step 1
        self.play(FadeIn(current_title_group, shift=DOWN*0.1), run_time=0.8)
        # Step Title: Architecture Type 3: Utility-Based Agent
        # Narration: Goes beyond binary goal completion: which action achieves it best?
        
        self.play(GrowFromCenter(agent_core), run_time=1.5)
        self.wait(2.0) 

        # Candidate actions concept
        candidate_action_text = CrispText("Candidate Actions", size=6.0, color=C_TEXT, weight=SEMIBOLD)
        candidate_action_arrow = Arrow(start=LEFT, end=RIGHT, stroke_color=C_SKY_BLUE, stroke_width=2).scale(0.8)
        candidate_actions_group = VGroup(candidate_action_text, candidate_action_arrow).arrange(RIGHT, buff=0.1)
        candidate_actions_group.next_to(agent_core, UP + LEFT, buff=0.8)
        
        optimal_action_text = CrispText("Optimal Action", size=6.0, color=C_TEXT, weight=SEMIBOLD)
        optimal_action_arrow = Arrow(start=LEFT, end=RIGHT, stroke_color=C_CORAL_PEACH, stroke_width=2).scale(0.8)
        optimal_action_group = VGroup(optimal_action_arrow, optimal_action_text).arrange(RIGHT, buff=0.1)
        optimal_action_group.next_to(agent_core, RIGHT * 1.5, buff=0.8)

        self.play(
            FadeIn(candidate_actions_group, shift=LEFT*0.5),
            Create(Arrow(candidate_actions_group.get_right(), agent_core.outer_shape.get_top() + LEFT * 0.5, buff=0.1, stroke_color=C_SKY_BLUE)),
            run_time=1.5
        )
        self.wait(1.0) # Sync with narration "which action achieves it best?"
        
        agent_core_highlight = agent_core.outer_shape.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5)
        self.play(
            FadeIn(optimal_action_group, shift=RIGHT*0.5),
            Create(Arrow(agent_core.outer_shape.get_right(), optimal_action_group.get_left(), buff=0.1, stroke_color=C_CORAL_PEACH)),
            Create(agent_core_highlight),
            run_time=2.0
        )
        self.wait(1.0)
        self.play(
            FadeOut(agent_core_highlight), 
            FadeOut(candidate_actions_group), 
            FadeOut(optimal_action_group),
            *[FadeOut(m) for m in self.mobjects if isinstance(m, Arrow) and m.stroke_color != C_STEEL_BLUE], # Only fade out new arrows
            run_time=0.8
        )
        self.wait(0.5) 

        ## Presentation Step 2
        # Step Title: Multi-Objective Utility Criteria
        # Narration: Balancing execution speed, compute cost, and decision confidence
        new_title_group_2 = create_title("Multi-Objective Utility Criteria")
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(new_title_group_2, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = new_title_group_2

        # Utility criteria pills
        speed_pill = StyledPill("Execution Speed", stroke_color=C_MUSTARD_YELLOW).next_to(agent_core, UP * 2.5 + LEFT * 0.5, buff=0.5)
        cost_pill = StyledPill("Compute Cost", stroke_color=C_DUSTY_ROSE).next_to(agent_core, UP * 2.5 + RIGHT * 0.5, buff=0.5)
        confidence_pill = StyledPill("Decision Confidence", stroke_color=C_MINT_SEAFOAM).next_to(agent_core, UP * 1.5, buff=0.5)
        
        # Arrows from pills to agent core
        arrow_speed = CurvedArrow(speed_pill.get_bottom(), agent_core.outer_shape.get_top() + LEFT * 0.5, color=C_MUSTARD_YELLOW, angle=-TAU/4, tip_length=0.2)
        arrow_cost = CurvedArrow(cost_pill.get_bottom(), agent_core.outer_shape.get_top() + RIGHT * 0.5, color=C_DUSTY_ROSE, angle=TAU/4, tip_length=0.2)
        arrow_confidence = Arrow(confidence_pill.get_bottom(), agent_core.outer_shape.get_top(), color=C_MINT_SEAFOAM, tip_length=0.2)

        self.play(FadeIn(speed_pill, shift=UP*0.5), Create(arrow_speed), run_time=1.0)
        self.wait(0.5)
        self.play(FadeIn(cost_pill, shift=UP*0.5), Create(arrow_cost), run_time=1.0)
        self.wait(0.5)
        self.play(FadeIn(confidence_pill, shift=UP*0.5), Create(arrow_confidence), run_time=1.0)
        self.wait(1.5) 

        criteria_highlight_group = VGroup(
            speed_pill.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5),
            cost_pill.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5),
            confidence_pill.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5)
        )
        self.play(Create(criteria_highlight_group), run_time=1.0)
        self.wait(0.5)
        self.play(FadeOut(criteria_highlight_group), run_time=0.5)
        self.wait(0.5)

        ## Presentation Step 3
        # Step Title: Solara Trade-off: Report Scope
        # Narration: Full diagnostic report vs. executive summary allocation
        new_title_group_3 = create_title("Solara Trade-off: Report Scope")
        self.remove(new_title_group_2)
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(new_title_group_3, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = new_title_group_3

        # Trade-off representation (branching paths from agent core)
        tradeoff_label = CrispText("Report Scope", size=6.0, color=C_TEXT, weight=SEMIBOLD).next_to(agent_core, DOWN, buff=0.8)
        
        full_report_option = StyledPill("Full Diagnostic Report", width=3.0, stroke_color=C_STEEL_BLUE).next_to(tradeoff_label, LEFT, buff=0.8)
        summary_option = StyledPill("Executive Summary", width=3.0, stroke_color=C_WARM_AMBER).next_to(tradeoff_label, RIGHT, buff=0.8)

        arrow_to_full = Arrow(tradeoff_label.get_bottom() + LEFT * 0.2, full_report_option.get_top(), buff=0.1, color=C_STEEL_BLUE, tip_length=0.2)
        arrow_to_summary = Arrow(tradeoff_label.get_bottom() + RIGHT * 0.2, summary_option.get_top(), buff=0.1, color=C_WARM_AMBER, tip_length=0.2)
        
        self.play(FadeIn(tradeoff_label, shift=UP*0.2), run_time=0.8)
        self.wait(0.5)
        self.play(FadeIn(full_report_option, shift=LEFT*0.2), Create(arrow_to_full), run_time=1.2)
        self.wait(0.5)
        self.play(FadeIn(summary_option, shift=RIGHT*0.2), Create(arrow_to_summary), run_time=1.2)
        self.wait(1.5) 

        tradeoff_highlight_group = VGroup(
            full_report_option.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5),
            summary_option.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5)
        )
        self.play(Create(tradeoff_highlight_group), run_time=1.0)
        self.wait(0.5)
        self.play(FadeOut(tradeoff_highlight_group), run_time=0.5)
        self.wait(0.5)

        ## Presentation Step 4
        # Step Title: Solara Trade-off: Anomaly Action
        # Narration: Immediate engineer escalation vs. automated telemetry logging
        new_title_group_4 = create_title("Solara Trade-off: Anomaly Action")
        self.remove(new_title_group_3)
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(new_title_group_4, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = new_title_group_4

        self.play(
            FadeOut(tradeoff_label),
            FadeOut(full_report_option),
            FadeOut(summary_option),
            FadeOut(arrow_to_full),
            FadeOut(arrow_to_summary),
            run_time=0.8
        )
        
        # New trade-off: Anomaly Action
        anomaly_label = CrispText("Anomaly Action", size=6.0, color=C_TEXT, weight=SEMIBOLD).next_to(agent_core, DOWN, buff=0.8)
        
        escalation_option = StyledPill("Engineer Escalation", width=3.0, stroke_color=C_CORAL_PEACH).next_to(anomaly_label, LEFT, buff=0.8)
        logging_option = StyledPill("Automated Logging", width=3.0, stroke_color=C_MINT_SEAFOAM).next_to(anomaly_label, RIGHT, buff=0.8)

        arrow_to_escalation = Arrow(anomaly_label.get_bottom() + LEFT * 0.2, escalation_option.get_top(), buff=0.1, color=C_CORAL_PEACH, tip_length=0.2)
        arrow_to_logging = Arrow(anomaly_label.get_bottom() + RIGHT * 0.2, logging_option.get_top(), buff=0.1, color=C_MINT_SEAFOAM, tip_length=0.2)

        self.play(FadeIn(anomaly_label, shift=UP*0.2), run_time=0.8)
        self.wait(0.5)
        self.play(FadeIn(escalation_option, shift=LEFT*0.2), Create(arrow_to_escalation), run_time=1.2)
        self.wait(0.5)
        self.play(FadeIn(logging_option, shift=RIGHT*0.2), Create(arrow_to_logging), run_time=1.2)
        self.wait(1.5) 

        anomaly_highlight_group = VGroup(
            escalation_option.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5),
            logging_option.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5)
        )
        self.play(Create(anomaly_highlight_group), run_time=1.0)
        self.wait(0.5)
        self.play(FadeOut(anomaly_highlight_group), run_time=0.5)
        self.wait(0.5)

        ## Presentation Step 5
        # Step Title: Complete Closed-Loop Lifecycle
        # Narration: Goal Ingestion -> Perception -> Reasoning Engine -> Action Execution
        new_title_group_5 = create_title("Complete Closed-Loop Lifecycle")
        self.remove(new_title_group_4)
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(new_title_group_5, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = new_title_group_5

        self.play(
            FadeOut(anomaly_label),
            FadeOut(escalation_option),
            FadeOut(logging_option),
            FadeOut(arrow_to_escalation),
            FadeOut(arrow_to_logging),
            FadeOut(speed_pill),
            FadeOut(cost_pill),
            FadeOut(confidence_pill),
            FadeOut(arrow_speed),
            FadeOut(arrow_cost),
            FadeOut(arrow_confidence),
            run_time=1.0
        )
        
        # Position the main lifecycle nodes relative to the agent_core
        goal_ingestion_node.move_to(RIGHT * 0.5 + UP * 0.5)
        perception_node.move_to(RIGHT * 0.5 + DOWN * 1.5)
        action_execution_node.move_to(RIGHT * 5.0 + UP * 0.5)

        # Arrows for the cycle
        arrow_goal_to_perception = Arrow(goal_ingestion_node.get_bottom(), perception_node.get_top(), buff=0.1, color=C_SKY_BLUE, tip_length=0.2)
        arrow_perception_to_agent = Arrow(perception_node.get_right(), agent_core.get_left(), buff=0.1, color=C_MINT_SEAFOAM, tip_length=0.2)
        arrow_agent_to_action = Arrow(agent_core.get_right(), action_execution_node.get_left(), buff=0.1, color=C_CORAL_PEACH, tip_length=0.2)
        
        # Feedback loop path (will be drawn and animated later)
        feedback_arc = ArcBetweenPoints(
            action_execution_node.get_bottom() + DOWN * 0.2,
            goal_ingestion_node.get_bottom() + DOWN * 0.2,
            angle=-TAU/2, 
            stroke_color=C_STEEL_BLUE,
            stroke_width=2
        )
        # Manually create arrow tip for the arc
        feedback_arrow_tip = Arrow(feedback_arc.get_end() + RIGHT * 0.1, feedback_arc.get_end(), color=C_STEEL_BLUE, tip_length=0.25)


        self.play(GrowFromCenter(goal_ingestion_node), run_time=1.0)
        self.wait(0.5)
        self.play(GrowFromCenter(perception_node), Create(arrow_goal_to_perception), run_time=1.0)
        self.wait(0.5)
        self.play(Create(arrow_perception_to_agent), run_time=1.0)
        self.wait(0.5)
        self.play(GrowFromCenter(action_execution_node), Create(arrow_agent_to_action), run_time=1.0)
        self.wait(1.5) 
        
        # Animate particle flow through the loop
        dot_color = HIGHLIGHT_COLOR
        dot_radius = 0.08
        
        path1_dot = Dot(color=dot_color, radius=dot_radius).move_to(arrow_goal_to_perception.get_start())
        path2_dot = Dot(color=dot_color, radius=dot_radius).move_to(arrow_perception_to_agent.get_start())
        path3_dot = Dot(color=dot_color, radius=dot_radius).move_to(arrow_agent_to_action.get_start())

        self.play(MoveAlongPath(path1_dot, arrow_goal_to_perception, rate_func=linear, run_time=1.0), FadeOut(path1_dot), run_time=1.0)
        self.play(MoveAlongPath(path2_dot, arrow_perception_to_agent, rate_func=linear, run_time=1.0), FadeOut(path2_dot), run_time=1.0)
        self.play(MoveAlongPath(path3_dot, arrow_agent_to_action, rate_func=linear, run_time=1.0), FadeOut(path3_dot), run_time=1.0)
        self.wait(0.5)

        ## Presentation Step 6
        # Step Title: Feedback Loop & Exit Conditions
        # Narration: Three termination states: Goal Achieved, Error, or Human Escalation
        new_title_group_6 = create_title("Feedback Loop & Exit Conditions")
        self.remove(new_title_group_5)
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(new_title_group_6, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = new_title_group_6

        # Show the feedback loop path
        self.play(Create(feedback_arc), run_time=1.0)
        self.play(Create(feedback_arrow_tip), run_time=0.5)
        self.wait(0.5)

        # Termination states as branching paths from action_execution_node
        goal_achieved_pill = StyledPill("Goal Achieved", stroke_color=C_MINT_SEAFOAM).next_to(action_execution_node, RIGHT * 2, buff=0.8).shift(UP * 0.5)
        error_pill = StyledPill("Error", stroke_color=C_DUSTY_ROSE).next_to(action_execution_node, RIGHT * 2, buff=0.8) 
        human_escalation_pill = StyledPill("Human Escalation", stroke_color=C_CORAL_PEACH).next_to(action_execution_node, RIGHT * 2, buff=0.8).shift(DOWN * 0.5)
        
        # Arrange them vertically for clear presentation
        exit_conditions_group = VGroup(goal_achieved_pill, error_pill, human_escalation_pill).arrange(DOWN, buff=0.3)
        exit_conditions_group.next_to(action_execution_node, RIGHT * 2, buff=0.8)

        arrow_to_achieved = Arrow(action_execution_node.get_right(), goal_achieved_pill.get_left(), buff=0.1, color=C_MINT_SEAFOAM, tip_length=0.2)
        arrow_to_error = Arrow(action_execution_node.get_right(), error_pill.get_left(), buff=0.1, color=C_DUSTY_ROSE, tip_length=0.2)
        arrow_to_escalation_exit = Arrow(action_execution_node.get_right(), human_escalation_pill.get_left(), buff=0.1, color=C_CORAL_PEACH, tip_length=0.2)

        self.play(FadeIn(goal_achieved_pill, shift=RIGHT*0.2), Create(arrow_to_achieved), run_time=1.0)
        self.wait(0.5)
        self.play(FadeIn(error_pill, shift=RIGHT*0.2), Create(arrow_to_error), run_time=1.0)
        self.wait(0.5)
        self.play(FadeIn(human_escalation_pill, shift=RIGHT*0.2), Create(arrow_to_escalation_exit), run_time=1.0)
        self.wait(1.5)

        exit_highlight_group = VGroup(
            goal_achieved_pill.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5),
            error_pill.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5),
            human_escalation_pill.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5)
        )
        self.play(Create(exit_highlight_group), run_time=1.0)
        self.wait(0.5)
        self.play(FadeOut(exit_highlight_group), run_time=0.5)
        self.wait(0.5)

        ## Presentation Step 7
        # Step Title: Responsible Architecture & Escalation
        # Narration: Recognizing confidence limits and routing to human engineers
        new_title_group_7 = create_title("Responsible Architecture & Escalation")
        self.remove(new_title_group_6)
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(new_title_group_7, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = new_title_group_7

        self.play(
            FadeOut(goal_achieved_pill), FadeOut(arrow_to_achieved),
            FadeOut(error_pill), FadeOut(arrow_to_error),
            run_time=0.8
        )
        
        # Introduce a "Confidence Monitor" within the agent core
        confidence_monitor = StyledPill("Confidence Monitor", width=2.0, height=0.6, fill_color=C_SOFT_LILAC, stroke_color=C_LAVENDER_PERIWINKLE, text_color=WHITE, text_size=0.18, weight=BOLD)
        confidence_monitor.move_to(agent_core.center + UP * 0.6)
        
        confidence_value = DecimalNumber(85, num_decimal_places=0, unit="%", color=WHITE, font_size=0.25).next_to(confidence_monitor.get_text_mobject(), DOWN, buff=0.1)
        confidence_value.set_z_index(confidence_monitor.get_z_index() + 1)
        
        confidence_group = VGroup(confidence_monitor, confidence_value)

        self.play(FadeIn(confidence_group, shift=UP*0.2), run_time=1.0)
        self.wait(0.5)
        
        # Simulate confidence dropping and triggering escalation
        self.play(
            confidence_value.animate.set_value(30),
            run_time=2.0,
            rate_func=linear
        )
        self.wait(0.5)

        escalation_path_highlight = VGroup(
            human_escalation_pill.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5),
            arrow_to_escalation_exit.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5)
        )
        self.play(Create(escalation_path_highlight), run_time=1.0)
        self.wait(1.5) 
        
        # --- Final Cleanup ---
        self.play(
            FadeOut(escalation_path_highlight),
            FadeOut(confidence_group),
            FadeOut(human_escalation_pill), FadeOut(arrow_to_escalation_exit),
            FadeOut(goal_ingestion_node), FadeOut(perception_node), FadeOut(action_execution_node),
            FadeOut(arrow_goal_to_perception), FadeOut(arrow_perception_to_agent), FadeOut(arrow_agent_to_action),
            FadeOut(feedback_arc), FadeOut(feedback_arrow_tip),
            FadeOut(agent_core),
            FadeOut(current_title_group),
            run_time=2.0
        )
        
        # Ensure all updaters are removed for clean exit
        agent_core.remove_updaters()

        self.wait(1.0)