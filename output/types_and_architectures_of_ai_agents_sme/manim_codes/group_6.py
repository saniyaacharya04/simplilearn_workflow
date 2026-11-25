C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_WHITE = "#FFFFFF"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
C_MINT = "#8ECDB7"
C_LAVENDER = "#9B99C7"
C_CORAL = "#E58F6D"
import os
import re
SME_LAYOUT = '20'
from feedback_functions.instrumented_scene import InstrumentedScene
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
        if not hasattr(_scene_cls, '_orig_play_safe'):
            _orig_play = _scene_cls.play
            def _make_safe_play():
                def _safe_play(self, *args, **kwargs):
                    if len(args) == 0:
                        rt = kwargs.get('run_time', 0.5)
                        return self.wait(rt)
                    return _orig_play(self, *args, **kwargs)
                return _safe_play
            _scene_cls._orig_play_safe = True
            _scene_cls.play = _make_safe_play()
        if not hasattr(_scene_cls, 'get_time'):
            _scene_cls.get_time = lambda self: getattr(getattr(self, 'renderer', None), 'time', 0.0)
    except Exception:
        pass
try:
    from manim.utils.color.core import ManimColor
    if not hasattr(ManimColor, '_orig_eq_safe'):
        def _safe_color_eq(self, other):
            if not isinstance(other, ManimColor):
                try: other = ManimColor(other)
                except Exception: return False
            return bool(np.allclose(self._internal_value, other._internal_value))
        ManimColor._orig_eq_safe = True
        ManimColor.__eq__ = _safe_color_eq
except Exception:
    pass
try:
    if not hasattr(Mobject, 'stop_updater'):
        Mobject.stop_updater = lambda self: self.clear_updaters()
    if not hasattr(Mobject, 'set_fill'):
        def _safe_mobj_set_fill(self, *args, **kwargs):
            for sub in getattr(self, 'submobjects', []):
                if hasattr(sub, 'set_fill'):
                    try: sub.set_fill(*args, **kwargs)
                    except Exception: pass
            return self
        Mobject.set_fill = _safe_mobj_set_fill
    if not hasattr(Mobject, 'set_stroke'):
        def _safe_mobj_set_stroke(self, *args, **kwargs):
            for sub in getattr(self, 'submobjects', []):
                if hasattr(sub, 'set_stroke'):
                    try: sub.set_stroke(*args, **kwargs)
                    except Exception: pass
            return self
        Mobject.set_stroke = _safe_mobj_set_stroke
    if not hasattr(Mobject, '_orig_mobj_init_safe'):
        _orig_mobj_init = Mobject.__init__
        def _safe_mobj_init(self, *args, **kwargs):
            valid_mobj_params = {'name', 'dim', 'target', 'z_index'}
            clean_kw = {k: v for k, v in kwargs.items() if k in valid_mobj_params}
            res = _orig_mobj_init(self, *args, **clean_kw)
            if 'opacity' in kwargs and hasattr(self, 'set_opacity'):
                try: self.set_opacity(kwargs['opacity'])
                except Exception: pass
            return res
        Mobject._orig_mobj_init_safe = True
        Mobject.__init__ = _safe_mobj_init
    if not hasattr(VMobject, '_orig_set_stroke_safe'):
        _orig_set_stroke = VMobject.set_stroke
        def _safe_set_stroke(self, *args, **kwargs):
            valid_stroke_params = {'color', 'width', 'opacity', 'background'}
            clean_kw = {k: v for k, v in kwargs.items() if k in valid_stroke_params}
            if 'z_index' in kwargs:
                try: self.set_z_index(kwargs['z_index'])
                except Exception: pass
            return _orig_set_stroke(self, *args, **clean_kw)
        VMobject._orig_set_stroke_safe = True
        VMobject.set_stroke = _safe_set_stroke
except Exception:
    pass
YELLOW = globals().get('YELLOW', '#DDB945')
WHITE = globals().get('WHITE', '#FFFFFF')
BLACK = globals().get('BLACK', '#404040')
RED = globals().get('RED', '#E58F6D')
BLUE = globals().get('BLUE', '#62B7E4')
GREEN = globals().get('GREEN', '#8ECDB7')
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

# Define custom colors from the infographic pastel palette
C_BACKGROUND = "#F0F4F8"
C_PRIMARY_TEXT = "#404040"
C_SECONDARY_TEXT = "#334155"
C_HEADER_TEXT = "#1E293B"

C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_LAVENDER_PERIWINKLE = "#9B99C7"
C_MINT_SEAFOAM = "#8ECDB7"
C_WARM_AMBER = "#E6A157"
C_MUSTARD_YELLOW = "#DDB945"
C_CORAL_PEACH = "#E58F6D"
C_WARM_TAN = "#B88968"
C_DUSTY_ROSE = "#D98CA1"
C_SOFT_LILAC = "#C1A5C6"

C_HIGHLIGHT = "#F78908" # Warm Orange for focus

# Font settings
FONT = "Open Sans"
TITLE_SIZE = 0.33 # ~45px
HEADER_SIZE = 0.21 # ~28px
BODY_SIZE = 0.16 # ~22px
PILL_SIZE = 0.13 # ~17px

# Helper for CrispText (Manim's Text class with Open Sans default)










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
class InstrumentedScene(Scene):
    def sync_to(self, t):
        # Placeholder for actual sync logic. For local testing, it acts as wait.
        # In a production environment, this would synchronize with audio.
        if hasattr(self.renderer, 'time'):
            current_time = self.renderer.time
            if t > current_time:
                self.wait(t - current_time)
        else:
            self.wait(0.1) # Small wait if renderer.time is not available

# Custom PRA Node class
class PRANode(VGroup):
    def __init__(self, label_text, icon_mob, color, position=ORIGIN, **kwargs):
        super().__init__(**kwargs)
        self.color = color
        self.label_text = label_text

        self.outer_circle = Circle(
            radius=0.7,
            stroke_width=2,
            stroke_color=self.color,
            fill_color=C_BACKGROUND,
            fill_opacity=1.0,
            z_index=1
        )
        self.inner_circle = Circle(
            radius=0.6,
            stroke_width=0,
            fill_color=self.color,
            fill_opacity=0.2,
            z_index=0
        )
        self.label = CrispText(
            self.label_text,
            size=PILL_SIZE + 0.02, # Slightly larger for node labels
            weight=BOLD,
            color=C_HEADER_TEXT
        ).move_to(self.outer_circle.get_bottom() + DOWN * 0.3)

        # Scale icon to fit within the node
        icon_mob.scale_to_fit_height(0.6).move_to(self.outer_circle.get_center())
        
        self.add(self.outer_circle, self.inner_circle, icon_mob, self.label)
        self.move_to(position)

    def get_highlight_stroke(self):
        # Creates a highlight stroke around the node's outer circle
        return self.outer_circle.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)

# Procedural Icons for PRA nodes
class SensorIcon(VGroup):
    def __init__(self, color=C_HEADER_TEXT, **kwargs):
        super().__init__(**kwargs)
        # Fix: Replaced 'end_angle' with 'angle' as 'Arc' might not consume 'end_angle' directly in Mobject.__init__
        dish = Arc(radius=0.4, start_angle=PI/4, angle=PI/2, arc_center=ORIGIN, stroke_width=2, color=color)
        dish.reverse_points() # To make it face up
        line1 = Line(dish.get_center(), dish.get_top(), stroke_width=2, color=color)
        line2 = Line(line1.get_top(), line1.get_top() + RIGHT * 0.2, stroke_width=2, color=color)
        line3 = Line(line1.get_top(), line1.get_top() + LEFT * 0.2, stroke_width=2, color=color)
        self.add(dish, line1, line2, line3)
        self.scale(0.8)

class BrainIcon(VGroup):
    def __init__(self, color=C_HEADER_TEXT, **kwargs):
        super().__init__(**kwargs)
        # Fix: Changed end_angle to angle
        lobe1 = Arc(radius=0.3, start_angle=PI/2, angle=PI, stroke_width=2, color=color).shift(LEFT*0.1)
        lobe2 = Arc(radius=0.3, start_angle=-PI/2, angle=PI, stroke_width=2, color=color).shift(RIGHT*0.1)
        center_line = Line(lobe1.get_top(), lobe2.get_top(), stroke_width=2, color=color)
        bottom_line = Line(lobe1.get_bottom(), lobe2.get_bottom(), stroke_width=2, color=color)
        self.add(lobe1, lobe2, center_line, bottom_line)
        self.scale(0.8)

class GearWrenchIcon(VGroup):
    def __init__(self, color=C_HEADER_TEXT, **kwargs):
        super().__init__(**kwargs)
        gear = RegularPolygon(n=6, radius=0.3, stroke_width=2, color=color).rotate(PI/6)
        wrench_body = Rectangle(width=0.15, height=0.5, stroke_width=0, fill_color=color, fill_opacity=1).rotate(PI/4).shift(RIGHT*0.1 + UP*0.1)
        # Fix: Changed end_angle to angle
        wrench_head = Arc(radius=0.15, start_angle=PI/2, angle=PI, stroke_width=0, fill_color=color, fill_opacity=1).next_to(wrench_body.get_top(), UP, buff=0).shift(LEFT*0.05)
        self.add(gear, wrench_body, wrench_head)
        self.scale(0.8)

class CheckGaugeIcon(VGroup):
    def __init__(self, color=C_HEADER_TEXT, **kwargs):
        super().__init__(**kwargs)
        gauge_arc = Arc(radius=0.4, start_angle=PI, angle=-PI, stroke_width=2, color=color)
        pointer = Line(gauge_arc.get_center(), gauge_arc.get_top(), stroke_width=2, color=color)
        # Fix: Changed Checkmark to create_checkmark
        check = create_checkmark(color=color).scale(0.2).next_to(gauge_arc.get_bottom(), DOWN, buff=0.1)
        self.add(gauge_arc, pointer, check)
        self.scale(0.8)


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



        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)















        # ## Presentation Step 1: Initial Setup and Perceive Node
        current_title = create_title("Perceive-Reason-Act (Pra) Execution Cycle")
        self.play(FadeIn(current_title, shift=DOWN * 0.1), run_time=0.8)
        self.sync_to(0.0) # Narration: Extracting structured signals from noisy raw sensory data

        # Define node positions for a slightly skewed circular/diamond layout,
        # ensuring clearance from the top-right SME (x >= +3.500 and y >= +1.800)
        
        # Adjust positions to fit the 20% SME layout.
        # The main content area is roughly x in [-6.4, 6.4] and y in [-3.5, 1.8]
        # Let's target a vertical center around y=-0.5 for the diagram.
        
        perceive_pos = LEFT * 4.5 + UP * 0.8
        reason_pos = LEFT * 4.5 + DOWN * 2.0
        act_pos = RIGHT * 4.5 + DOWN * 2.0
        verification_pos = RIGHT * 4.5 + UP * 0.8

        # Create nodes
        perceive_node = PRANode("Perceive", SensorIcon(color=C_HEADER_TEXT), C_SKY_BLUE, position=perceive_pos)
        reason_node = PRANode("Reason", BrainIcon(color=C_HEADER_TEXT), C_LAVENDER_PERIWINKLE, position=reason_pos)
        act_node = PRANode("Act", GearWrenchIcon(color=C_HEADER_TEXT), C_CORAL_PEACH, position=act_pos)
        verification_node = PRANode("Verify", CheckGaugeIcon(color=C_HEADER_TEXT), C_MINT_SEAFOAM, position=verification_pos)

        # Create arrows connecting the nodes
        arrow_pr = CurvedArrow(
            perceive_node.outer_circle.get_bottom() + DOWN * 0.1,
            reason_node.outer_circle.get_top() + UP * 0.1,
            color=C_SKY_BLUE,
            tip_length=0.2,
            stroke_width=2.5
        )

        arrow_ra = CurvedArrow(
            reason_node.outer_circle.get_right() + RIGHT * 0.1,
            act_node.outer_circle.get_left() + LEFT * 0.1,
            color=C_LAVENDER_PERIWINKLE,
            tip_length=0.2,
            stroke_width=2.5
        )

        arrow_av = CurvedArrow(
            act_node.outer_circle.get_bottom() + DOWN * 0.1,
            verification_node.outer_circle.get_top() + UP * 0.1,
            color=C_CORAL_PEACH,
            tip_length=0.2,
            stroke_width=2.5
        )

        arrow_vp = CurvedArrow(
            verification_node.outer_circle.get_left() + LEFT * 0.1,
            perceive_node.outer_circle.get_right() + RIGHT * 0.1,
            color=C_MINT_SEAFOAM,
            tip_length=0.2,
            stroke_width=2.5,
            # Adjust control points for a smoother, wider curve for the feedback loop
            control_point_array=[
                verification_node.outer_circle.get_left() + LEFT * 0.1,
                verification_node.outer_circle.get_left() + LEFT * 1.5 + UP * 2.0,
                perceive_node.outer_circle.get_right() + RIGHT * 1.5 + UP * 2.0,
                perceive_node.outer_circle.get_right() + RIGHT * 0.1
            ]
        )
        
        self.play(
            LaggedStart(
                GrowFromCenter(perceive_node),
                Create(arrow_pr),
                GrowFromCenter(reason_node),
                Create(arrow_ra),
                GrowFromCenter(act_node),
                Create(arrow_av),
                GrowFromCenter(verification_node),
                Create(arrow_vp),
                lag_ratio=0.15, # Faster sequential reveal
                run_time=3.5
            )
        )
        
        # Add ambient updater for the radar icon within the Perceive node
        radar_sweep_arm = Line(
            perceive_node.outer_circle.get_center(),
            perceive_node.outer_circle.get_center() + UP * 0.5,
            color=C_SKY_BLUE,
            stroke_width=2
        )
        # The radar sweep should stay within the node's circle
        radar_sweep_arm.add_updater(lambda m, dt: m.rotate(0.5 * dt, about_point=perceive_node.outer_circle.get_center()))
        self.add(radar_sweep_arm)


        # Narration for Step 1: "Extracting structured signals from noisy raw sensory data"
        perceive_desc = CrispText(
            "Extracting structured signals from\nnoisy raw sensory data",
            size=PILL_SIZE,
            color=C_SECONDARY_TEXT,
            alignment="left"
        ).next_to(perceive_node, RIGHT, buff=0.7).shift(DOWN * 0.2)
        
        perceive_highlight = perceive_node.get_highlight_stroke()
        self.play(
            Create(perceive_highlight),
            FadeIn(perceive_desc, shift=LEFT * 0.2),
            run_time=1.5
        )
        self.sync_to(5.0) # Example sync point
        
        # Add a flowing particle to Perceive -> Reason arrow
        perceive_particle = Dot(color=C_HIGHLIGHT, radius=0.08, z_index=10)
        self.play(
            # Fix: Change rate_func from linear to ease_out_cubic
            MoveAlongPath(perceive_particle, arrow_pr, rate_func=ease_out_cubic, run_time=1.5),
            run_time=1.5
        )
        self.remove(perceive_particle)
        
        self.play(FadeOut(perceive_highlight, shift=DOWN*0.1), run_time=0.4)
        self.sync_to(8.0) # Example sync point


        ## Presentation Step 2: Context Synthesis
        # Narration: "Fusing observations with past historical operational memory"
        
        context_synthesis_text = CrispText(
            "Fusing observations with past\nhistorical operational memory",
            size=PILL_SIZE,
            color=C_SECONDARY_TEXT,
            alignment="left"
        ).next_to(perceive_node, RIGHT, buff=0.7).shift(DOWN * 0.2)
        
        self.play(
            FadeOut(perceive_desc, shift=UP * 0.1),
            FadeIn(context_synthesis_text, shift=LEFT * 0.2),
            run_time=0.8
        )
        
        perceive_highlight_2 = perceive_node.get_highlight_stroke()
        self.play(Create(perceive_highlight_2), run_time=0.6)
        self.sync_to(11.0) # Example sync point
        
        perceive_particle_2 = Dot(color=C_HIGHLIGHT, radius=0.08, z_index=10)
        self.play(
            # Fix: Change rate_func from linear to ease_out_cubic
            MoveAlongPath(perceive_particle_2, arrow_pr, rate_func=ease_out_cubic, run_time=1.5),
            run_time=1.5
        )
        self.remove(perceive_particle_2)
        
        self.play(FadeOut(perceive_highlight_2, shift=DOWN*0.1), run_time=0.4)
        self.sync_to(14.0) # Example sync point


        ## Presentation Step 3: Reason: Planning & Selection
        # Narration: "Formulating viable multi-step execution candidate paths"
        
        self.play(FadeOut(context_synthesis_text, shift=UP * 0.1), run_time=0.8)
        
        reason_desc = CrispText(
            "Formulating viable multi-step\nexecution candidate paths",
            size=PILL_SIZE,
            color=C_SECONDARY_TEXT,
            alignment="left"
        ).next_to(reason_node, RIGHT, buff=0.7).shift(DOWN * 0.2)
        
        reason_highlight = reason_node.get_highlight_stroke()
        self.play(
            Create(reason_highlight),
            FadeIn(reason_desc, shift=LEFT * 0.2),
            run_time=1.5
        )
        self.sync_to(17.0) # Example sync point
        
        reason_particle = Dot(color=C_HIGHLIGHT, radius=0.08, z_index=10)
        self.play(
            # Fix: Change rate_func from linear to ease_out_cubic
            MoveAlongPath(reason_particle, arrow_ra, rate_func=ease_out_cubic, run_time=1.5),
            run_time=1.5
        )
        self.remove(reason_particle)
        
        self.play(FadeOut(reason_highlight, shift=DOWN*0.1), run_time=0.4)
        self.sync_to(20.0) # Example sync point


        ## Presentation Step 4: Act: Effector Dispatch
        # Narration: "Invoking specialized external tools and system APIs"
        
        self.play(FadeOut(reason_desc, shift=UP * 0.1), run_time=0.8)
        
        act_desc = CrispText(
            "Invoking specialized external tools\nand system APIs",
            size=PILL_SIZE,
            color=C_SECONDARY_TEXT,
            alignment="left"
        ).next_to(act_node, LEFT, buff=0.7).shift(DOWN * 0.2) # Position to the left of act_node
        
        act_highlight = act_node.get_highlight_stroke()
        self.play(
            Create(act_highlight),
            FadeIn(act_desc, shift=RIGHT * 0.2), # Shift from right
            run_time=1.5
        )
        self.sync_to(23.0) # Example sync point
        
        act_particle = Dot(color=C_HIGHLIGHT, radius=0.08, z_index=10)
        self.play(
            # Fix: Change rate_func from linear to ease_out_cubic
            MoveAlongPath(act_particle, arrow_av, rate_func=ease_out_cubic, run_time=1.5),
            run_time=1.5
        )
        self.remove(act_particle)
        
        self.play(FadeOut(act_highlight, shift=DOWN*0.1), run_time=0.4)
        self.sync_to(26.0) # Example sync point


        ## Presentation Step 5: Verification & State Check
        # Narration: "Validating outcome before initiating the subsequent cycle"
        
        self.play(FadeOut(act_desc, shift=UP * 0.1), run_time=0.8)
        
        verification_desc = CrispText(
            "Validating outcome before initiating\nthe subsequent cycle",
            size=PILL_SIZE,
            color=C_SECONDARY_TEXT,
            alignment="left"
        ).next_to(verification_node, LEFT, buff=0.7).shift(DOWN * 0.2) # Position to the left of verification_node
        
        verification_highlight = verification_node.get_highlight_stroke()
        self.play(
            Create(verification_highlight),
            FadeIn(verification_desc, shift=RIGHT * 0.2), # Shift from right
            run_time=1.5
        )
        self.sync_to(29.0) # Example sync point
        
        verification_particle = Dot(color=C_HIGHLIGHT, radius=0.08, z_index=10)
        self.play(
            # Fix: Change rate_func from linear to ease_out_cubic
            MoveAlongPath(verification_particle, arrow_vp, rate_func=ease_out_cubic, run_time=1.5),
            run_time=1.5
        )
        self.remove(verification_particle)
        
        self.play(FadeOut(verification_highlight, shift=DOWN*0.1), run_time=0.4)
        self.sync_to(32.0) # Example sync point

        # Final cleanup for persistent elements
        radar_sweep_arm.remove_updater(lambda m, dt: m.rotate(0.5 * dt, about_point=perceive_node.outer_circle.get_center())) # Remove updater before ending scene
        self.play(
            FadeOut(perceive_node),
            FadeOut(reason_node),
            FadeOut(act_node),
            FadeOut(verification_node),
            FadeOut(arrow_pr),
            FadeOut(arrow_ra),
            FadeOut(arrow_av),
            FadeOut(arrow_vp),
            FadeOut(verification_desc),
            FadeOut(radar_sweep_arm), # Ensure the radar arm is also faded out
            run_time=1.0
        )
        self.wait(0.5)