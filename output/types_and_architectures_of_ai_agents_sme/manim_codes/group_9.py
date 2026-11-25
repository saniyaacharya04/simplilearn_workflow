C_DARK_BLUE = "#1E293B"
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
from manim_slides.instrumented_scene import InstrumentedScene

# --- Global Constants and Helper Functions (as if from template_utils or global scope) ---
# Canvas Theme & Colors
C_BACKGROUND = "#F0F4F8"  # Modern Soft Light Slate Canvas
C_HEADER = "#1E293B"      # Dark Slate for titles/headers
C_SUBTITLE = "#475569"    # Muted Slate for subtitles
C_TEXT = "#404040"        # Primary Dark Charcoal for body text

# 10-Color Infographic Pastel Palette
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_LAVENDER = "#9B99C7"
C_MINT = "#8ECDB7"
C_AMBER = "#E6A157"
C_MUSTARD = "#DDB945"
C_CORAL = "#E58F6D"
C_TAN = "#B88968"
C_ROSE = "#D98CA1"
C_LILAC = "#C1A5C6"

HIGHLIGHT_COLOR = "#F78908" # Warm Orange for focus highlights

# Custom Text Class for consistent typography


# --- Custom Vector Assets (simplified for this example, mimicking kinetic standards) ---
class DynamicRadarSweep(VGroup):
    def __init__(self, radius=1.0, color=C_SKY_BLUE, **kwargs):
        super().__init__(**kwargs)
        self.radius = radius
        self.color = color
        
        # Base circle and radiating rings
        self.circle = Circle(radius=self.radius, stroke_color=self.color, stroke_width=2).set_fill(self.color, opacity=0.1)
        self.scan_line = Line(ORIGIN, self.radius * RIGHT, stroke_color=self.color, stroke_width=3)
        self.scan_line.rotate(PI/4, about_point=ORIGIN) # Initial angle
        
        self.add(self.circle, self.scan_line)

    def _update_sweep(self, mob, dt):
        mob.submobjects[1].rotate(0.5 * dt) # Rotate the scan line

    def add_updater(self, *args, **kwargs):
        super().add_updater(self._update_sweep)

    def stop_updater(self):
        self.remove_updater(self._update_sweep)

class DatabaseStack(VGroup):
    def __init__(self, num_disks=3, disk_radius=1.0, disk_height=0.2, color=C_MINT, **kwargs):
        super().__init__(**kwargs)
        self.num_disks = num_disks
        self.disk_radius = disk_radius
        self.disk_height = disk_height
        self.color = color

        disks = VGroup()
        self.original_heights = []
        self.original_widths = []
        for i in range(self.num_disks):
            cylinder = Cylinder(radius=self.disk_radius, height=self.disk_height, color=self.color, fill_opacity=0.3, stroke_color=self.color, stroke_width=2)
            cylinder.set_z_index(-i) # Stack order
            disks.add(cylinder)
            self.original_heights.append(cylinder.get_height())
            self.original_widths.append(cylinder.get_width())

        disks.arrange(DOWN, buff=self.disk_height * 0.8) # Stack them closely
        self.add(disks)
        self.pulse_tracker = ValueTracker(0)

    def _update_pulse(self, mob, dt):
        t = self.pulse_tracker.increment_value(dt * 0.5).get_value()
        scale_factor = 1 + 0.02 * np.sin(t * 2 * PI) # Subtle breathing effect
        for i, disk in enumerate(mob.submobjects[0]):
            disk.set_height(self.original_heights[i] * scale_factor)
            disk.set_width(self.original_widths[i] * scale_factor)
            disk.set_stroke(width=2 * scale_factor)

    def add_updater(self, *args, **kwargs):
        super().add_updater(self._update_pulse)

    def stop_updater(self):
        self.remove_updater(self._update_pulse)


class NeuralHaloPulses(VGroup):
    def __init__(self, core_radius=0.3, num_rings=3, max_radius=1.5, pulse_speed=1.0, color=C_LAVENDER, **kwargs):
        super().__init__(**kwargs)
        self.core_radius = core_radius
        self.num_rings = num_rings
        self.max_radius = max_radius
        self.pulse_speed = pulse_speed
        self.color = color

        self.core = Circle(radius=self.core_radius, color=self.color, fill_opacity=0.6, stroke_width=0)
        self.add(self.core)

        self.rings = VGroup()
        self.ring_trackers = []
        for i in range(self.num_rings):
            ring = Circle(radius=self.core_radius, stroke_color=self.color, stroke_width=2, fill_opacity=0)
            self.rings.add(ring)
            self.ring_trackers.append(ValueTracker(i * (self.max_radius / self.num_rings) / self.num_rings)) # Staggered start

        self.add(self.rings)

    def _update_pulses(self, mob, dt):
        for i, tracker in enumerate(self.ring_trackers):
            current_radius = tracker.get_value()
            current_radius += self.pulse_speed * dt

            if current_radius > self.max_radius:
                current_radius = self.core_radius # Reset to core radius

            tracker.set_value(current_radius)
            
            ring = self.rings[i]
            ring.set_width(current_radius * 2) # Set width to diameter
            
            # Fade out as it expands
            opacity = 1 - (current_radius - self.core_radius) / (self.max_radius - self.core_radius)
            ring.set_stroke(opacity=max(0, opacity), color=self.color)

    def add_updater(self, *args, **kwargs):
        super().add_updater(self._update_pulses)

    def stop_updater(self):
        self.remove_updater(self._update_pulses)

class ActionDispatchHub(VGroup):
    def __init__(self, gear_radius=1.0, color=C_AMBER, **kwargs):
        super().__init__(**kwargs)
        self.gear_radius = gear_radius
        self.color = color

        # Simple gear: A circle with a few rectangles as teeth
        gear_body = Circle(radius=self.gear_radius, stroke_color=self.color, stroke_width=2, fill_color=self.color, fill_opacity=0.3)
        
        teeth = VGroup()
        num_teeth = 8
        tooth_width = 0.2
        tooth_height = 0.3
        for i in range(num_teeth):
            tooth = Rectangle(width=tooth_width, height=tooth_height, fill_color=self.color, stroke_color=self.color, stroke_width=1, fill_opacity=0.6)
            tooth.next_to(gear_body, RIGHT, buff=0).shift(RIGHT * self.gear_radius)
            tooth.rotate(i * 2 * PI / num_teeth, about_point=ORIGIN)
            teeth.add(tooth)
        
        self.gear = VGroup(gear_body, teeth)
        self.add(self.gear)

    def _update_rotation(self, mob, dt):
        mob.rotate(0.5 * dt) # Rotate continuously

    def add_updater(self, *args, **kwargs):
        super().add_updater(self._update_rotation)

    def stop_updater(self):
        self.remove_updater(self._update_rotation)


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


        # SME Layout 70% constraint: Content area x ∈ [-0.80, +6.40]
        content_safe_x_min = -0.80
        content_safe_x_max = 6.40
        content_center_x = (content_safe_x_min + content_safe_x_max) / 2 # = 2.8

        # --- Presentation Step 1: Architectural Synthesis ---
        ## Presentation Step 1
        scene_title_text = "Architectural Synthesis & Hands-On Demo Launch"
        title_group = create_title(scene_title_text)
        self.play(FadeIn(title_group, shift=UP * 0.1), run_time=0.8)
        self.sync_to(0.0) # Start of narration for Step 1

        # Pillar dimensions and positioning
        pillar_height = 2.8
        pillar_width = 1.6
        pillar_buff = 0.6 
        
        # Calculate total width for 4 pillars and buffs
        total_pillars_width = 4 * pillar_width + 3 * pillar_buff
        
        # Position the first pillar to ensure the group is centered in the safe zone
        first_pillar_x = content_center_x - total_pillars_width / 2 + pillar_width / 2
        
        # Pillar 1: Perception
        perception_label = CrispText("Perception", target_height=0.21, weight=BOLD, color=C_HEADER) # Approx 18-20pt
        perception_base = RoundedRectangle(width=pillar_width, height=pillar_height, corner_radius=0.1, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=C_SKY_BLUE, stroke_width=2)
        perception_radar = DynamicRadarSweep(radius=pillar_width * 0.4, color=C_SKY_BLUE)
        
        perception_label.next_to(perception_base.get_bottom(), UP, buff=0.2)
        perception_radar.move_to(perception_base.get_center() + UP * 0.3)
        
        perception_pillar = VGroup(perception_base, perception_radar, perception_label)
        perception_pillar.move_to(RIGHT * first_pillar_x + DOWN * 0.3) # Adjust y position slightly lower

        # Pillar 2: Memory
        memory_label = CrispText("Memory", target_height=0.21, weight=BOLD, color=C_HEADER)
        memory_base = RoundedRectangle(width=pillar_width, height=pillar_height, corner_radius=0.1, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=C_MINT, stroke_width=2)
        memory_db = DatabaseStack(disk_radius=pillar_width * 0.4, disk_height=0.15, num_disks=4, color=C_MINT)
        
        memory_label.next_to(memory_base.get_bottom(), UP, buff=0.2)
        memory_db.move_to(memory_base.get_center() + UP * 0.3)
        
        memory_pillar = VGroup(memory_base, memory_db, memory_label)
        memory_pillar.next_to(perception_pillar, RIGHT, buff=pillar_buff)

        # Pillar 3: Reasoning
        reasoning_label = CrispText("Reasoning", target_height=0.21, weight=BOLD, color=C_HEADER)
        reasoning_base = RoundedRectangle(width=pillar_width, height=pillar_height, corner_radius=0.1, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=C_LAVENDER, stroke_width=2)
        reasoning_halo = NeuralHaloPulses(core_radius=pillar_width * 0.15, max_radius=pillar_width * 0.4, color=C_LAVENDER)
        
        reasoning_label.next_to(reasoning_base.get_bottom(), UP, buff=0.2)
        reasoning_halo.move_to(reasoning_base.get_center() + UP * 0.3)
        
        reasoning_pillar = VGroup(reasoning_base, reasoning_halo, reasoning_label)
        reasoning_pillar.next_to(memory_pillar, RIGHT, buff=pillar_buff)

        # Pillar 4: Action
        action_label = CrispText("Action", target_height=0.21, weight=BOLD, color=C_HEADER)
        action_base = RoundedRectangle(width=pillar_width, height=pillar_height, corner_radius=0.1, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=2)
        action_hub = ActionDispatchHub(gear_radius=pillar_width * 0.4, color=C_AMBER)
        
        action_label.next_to(action_base.get_bottom(), UP, buff=0.2)
        action_hub.move_to(action_base.get_center() + UP * 0.3)
        
        action_pillar = VGroup(action_base, action_hub, action_label)
        action_pillar.next_to(reasoning_pillar, RIGHT, buff=pillar_buff)

        pillars_group = VGroup(perception_pillar, memory_pillar, reasoning_pillar, action_pillar)
        
        # Ensure pillars are within safe bounds after initial positioning
        # Adjust if necessary to fit within content_safe_x_min/max
        if pillars_group.get_left()[0] < content_safe_x_min:
            pillars_group.shift(RIGHT * (content_safe_x_min - pillars_group.get_left()[0]))
        if pillars_group.get_right()[0] > content_safe_x_max:
            pillars_group.shift(LEFT * (pillars_group.get_right()[0] - content_safe_x_max))
        
        self.play(
            LaggedStart(
                FadeIn(perception_pillar, shift=DOWN * 0.2),
                FadeIn(memory_pillar, shift=DOWN * 0.2),
                FadeIn(reasoning_pillar, shift=DOWN * 0.2),
                FadeIn(action_pillar, shift=DOWN * 0.2),
                lag_ratio=0.2,
                run_time=3.0
            )
        )
        self.wait(1.0) # Allow initial animation to settle
        
        # Animate the internal kinetic elements
        self.play(
            Create(perception_radar),
            Create(memory_db),
            Create(reasoning_halo),
            Create(action_hub),
            run_time=2.0
        )

        # Add updaters for continuous ambient motion
        perception_radar.add_updater()
        memory_db.add_updater()
        reasoning_halo.add_updater()
        action_hub.add_updater()

        self.sync_to(56.42) # End of narration for Step 1
        self.wait(0.5) # Small pause before next step

        # --- Presentation Step 2: Progression of Sophistication ---
        ## Presentation Step 2
        # Narration: Reactive (rule-driven) -> Goal-based (planning) -> Utility-based (optimizing)
        
        # Highlight Reasoning pillar
        reasoning_highlight = reasoning_base.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5, corner_radius=0.1)
        self.play(Create(reasoning_highlight), run_time=0.6)

        # Labels for progression
        reactive_text = CrispText("Reactive (Rule-Driven)", target_height=0.18, color=C_TEXT) # Approx 14-16pt
        goal_based_text = CrispText("Goal-Based (Planning)", target_height=0.18, color=C_TEXT)
        utility_based_text = CrispText("Utility-Based (Optimizing)", target_height=0.18, color=C_TEXT)
        
        # Position labels to the right of the Reasoning pillar
        labels_group = VGroup(reactive_text, goal_based_text, utility_based_text).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        labels_group.next_to(reasoning_pillar, RIGHT, buff=0.8)
        
        # Animate progression text sequentially
        self.play(FadeIn(reactive_text, shift=RIGHT * 0.1), run_time=1.0)
        self.wait(2.0)
        self.play(FadeIn(goal_based_text, shift=RIGHT * 0.1), run_time=1.0)
        self.wait(2.0)
        self.play(FadeIn(utility_based_text, shift=RIGHT * 0.1), run_time=1.0)
        
        self.wait(5.0) # Hold for narration on progression
        
        self.play(FadeOut(reasoning_highlight), FadeOut(labels_group), run_time=0.8)
        self.wait(0.5) # Small pause

        # --- Presentation Step 3: What Is Next: Hands-On Demo Launch ---
        ## Presentation Step 3
        # Narration: Visualizing live decision loops and execution patterns in real time

        # Morph title to the specific step title
        new_title_text = "What Is Next: Hands-On Demo Launch"
        new_title_group = create_title(new_title_text)
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title_group, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title_group

        # Stop updaters on pillars before fading out
        perception_radar.stop_updater()
        memory_db.stop_updater()
        reasoning_halo.stop_updater()
        action_hub.stop_updater()

        self.play(FadeOut(pillars_group, shift=DOWN * 0.2), run_time=1.5)

        # Create a "Demo Launch" visual (console, terminal, button)
        launch_console = RoundedRectangle(width=5.0, height=3.0, corner_radius=0.2, fill_color="#1A202C", fill_opacity=0.9, stroke_color=C_SUBTITLE, stroke_width=2)
        
        # Launch button
        launch_button = Circle(radius=0.4, fill_color=C_CORAL, fill_opacity=1.0, stroke_color=C_ROSE, stroke_width=2)
        button_label = CrispText("Launch", target_height=0.15, weight=BOLD, color="#FFFFFF").move_to(launch_button.get_center())
        launch_button_grp = VGroup(launch_button, button_label).shift(DOWN * 0.6 + RIGHT * 1.5)

        # Terminal screen for output
        terminal_screen = Rectangle(width=3.5, height=1.8, fill_color="#0F172A", fill_opacity=1.0, stroke_color=C_SUBTITLE, stroke_width=1)
        terminal_screen.next_to(launch_console.get_top(), DOWN, buff=0.3)
        terminal_screen.align_to(launch_console, LEFT).shift(RIGHT * 0.3)

        console_label = CrispText("Demo Simulator", target_height=0.18, weight=BOLD, color=C_STEEL_BLUE).next_to(launch_console.get_top(), DOWN, buff=0.15)
        
        launch_visual = VGroup(launch_console, launch_button_grp, terminal_screen, console_label)
        launch_visual.center().shift(RIGHT * content_center_x).shift(LEFT * launch_visual.get_center()[0]) # Center in content area
        launch_visual.shift(DOWN * 0.3) # Adjust vertical position

        self.play(FadeIn(launch_visual, shift=UP * 0.2), run_time=1.5)

        # Animate "Launching..." text on terminal screen
        terminal_text_color = C_STEEL_BLUE # Using Steel Blue to avoid green
        
        launch_text1 = CrispText("Initializing...", target_height=0.16, color=terminal_text_color).to_corner(UL, buff=0.2)
        launch_text1.move_to(terminal_screen.get_top() + LEFT * 0.2 + DOWN * 0.2)
        launch_text1.align_to(terminal_screen, LEFT).shift(RIGHT * 0.1)

        launch_text2 = CrispText("Loading Modules...", target_height=0.16, color=terminal_text_color).next_to(launch_text1, DOWN, buff=0.1, aligned_edge=LEFT)
        launch_text3 = CrispText("Simulating Decision Loops...", target_height=0.16, color=terminal_text_color).next_to(launch_text2, DOWN, buff=0.1, aligned_edge=LEFT)
        launch_text4 = CrispText("Executing Actions...", target_height=0.16, color=terminal_text_color).next_to(launch_text3, DOWN, buff=0.1, aligned_edge=LEFT)
        
        launch_texts = VGroup(launch_text1, launch_text2, launch_text3, launch_text4)
        for text_mob in launch_texts:
            text_mob.set_x(terminal_screen.get_left()[0] + 0.2) # Ensure alignment within terminal

        self.play(Write(launch_text1), run_time=1.0)
        self.wait(0.5)
        self.play(Write(launch_text2), run_time=1.0)
        self.wait(0.5)
        self.play(Write(launch_text3), run_time=1.0)
        self.wait(0.5)
        self.play(Write(launch_text4), run_time=1.0)

        # Add a pulsing dot to simulate live execution
        live_dot = Dot(color=HIGHLIGHT_COLOR, radius=0.08).next_to(launch_text4, RIGHT, buff=0.1)
        live_dot.add_updater(lambda m, dt: m.set_opacity(0.5 + 0.5 * np.sin(self.get_time() * 5))) # Pulsing effect
        self.play(FadeIn(live_dot), run_time=0.5)

        self.wait(5.0) # Hold for narration
        
        # Fade out all elements for scene end
        self.play(
            FadeOut(launch_visual),
            FadeOut(launch_texts),
            FadeOut(live_dot),
            FadeOut(title_group),
            run_time=1.5
        )
        self.wait(1.0) # Final wait before scene ends