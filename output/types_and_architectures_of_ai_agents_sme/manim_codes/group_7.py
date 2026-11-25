C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
C_MINT = "#8ECDB7"
C_LAVENDER = "#9B99C7"
C_CORAL = "#E58F6D"
import os
import re
import numpy as np
SME_LAYOUT = '70'
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

# Global constants for styling (OSL 3.0 & Styling Generator Compliance)
C_BG = "#F0F4F8"  # Modern Soft Light Slate Canvas
C_TITLE = "#0F172A"  # Dark Slate for titles
C_HEADER = "#1E293B"  # Darker Slate for headers
C_BODY = "#334155"  # Slate for body text
C_TEXT = "#404040"  # Primary Dark Charcoal for general text
HIGHLIGHT_COLOR = "#F78908"  # Warm Orange for focus highlights
C_WHITE = "#FFFFFF"
C_SOFT_CARD = "#F8FAFC"  # Soft card background
C_STROKE_LIGHT = "#E2E8F0"  # Light gray for card borders

# Approved 10-color infographic pastel palette (subset used in this scene)
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_LAVENDER_PERIWINKLE = "#9B99C7"
C_MINT_SEAFOAM = "#8ECDB7"
C_WARM_AMBER = "#E6A157"
C_MUSTARD_YELLOW = "#DDB945"
C_CORAL_PEACH = "#E58F6D"
# C_WARM_TAN = "#B88968"
# C_DUSTY_ROSE = "#D98CA1"
# C_SOFT_LILAC = "#C1A5C6"


# Custom CrispText function for consistent typography










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
    """
    Placeholder for Simplilearn's InstrumentedScene. Defaults to Manim's Scene.
    """
    pass


class ProcessNode(VGroup):
    """
    A custom Mobject for a process node, consisting of a rounded rectangle and centered text.
    Dynamically adjusts size based on text content.
    """
    def __init__(self, text, fill_color=C_SOFT_CARD, stroke_color=C_STROKE_LIGHT, text_color=C_TEXT,
                 corner_radius=0.15, width=2.5, height=1.0, font_size=0.18, **kwargs):
        super().__init__(**kwargs)
        self.text_obj = CrispText(text, size=font_size, weight=SEMIBOLD, color=text_color)
        
        # Adjust width and height based on text content, ensuring minimums
        padding_x = 0.8  # Horizontal padding
        padding_y = 0.4  # Vertical padding
        actual_width = max(width, self.text_obj.width + padding_x)
        actual_height = max(height, self.text_obj.height + padding_y)

        self.box = RoundedRectangle(
            width=actual_width,
            height=actual_height,
            corner_radius=corner_radius,
            fill_color=fill_color,
            fill_opacity=1.0,
            stroke_color=stroke_color,
            stroke_width=2,
            z_index=1  # Ensure it's above lines/arrows
        )
        self.add(self.box, self.text_obj)


class FlowingStream(VGroup):
    """
    Creates a stream of dots flowing along a given path, simulating data flow.
    Uses updaters for continuous motion.
    """
    def __init__(self, path, num_dots=5, dot_radius=0.05, dot_color=HIGHLIGHT_COLOR, flow_speed=0.5, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.num_dots = num_dots
        self.flow_speed = flow_speed
        self.dots = VGroup()
        self.trackers = []

        for i in range(num_dots):
            # Start dots at different points along the path for a continuous stream effect
            tracker = ValueTracker(i / num_dots)
            dot = Dot(radius=dot_radius, color=dot_color, z_index=3)
            # Add updater to each dot to move it along the path
            dot.add_updater(lambda m, t=tracker: m.move_to(path.point_from_proportion(t.get_value())))
            self.dots.add(dot)
            self.trackers.append(tracker)
        
        self.add(self.dots)
        self.add_updater(self._update_flow)

    def _update_flow(self, mob, dt):
        """Updates the position of each dot along the path."""
        for tracker in mob.trackers:
            current_prop = tracker.get_value()
            new_prop = (current_prop + mob.flow_speed * dt) % 1.0  # Loop the flow
            tracker.set_value(new_prop)

    def stop_flow(self):
        """Removes updaters to stop the flow animation."""
        self.remove_updater(self._update_flow)
        for dot in self.dots:
            if dot.updaters: # Check if updaters exist before trying to remove
                dot.remove_updater(dot.updaters[0])







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



        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)















        # Assign global helper functions to self for convenience

        # SME Layout 70% requires content on the right side of the screen.
        # Safe content workspace: x ∈ [-0.80, +6.40], y ∈ [-3.60, +2.20].
        # Center x for content is approximately (-0.80 + 6.40) / 2 = 2.80
        content_center_x = 2.80
        content_width = 6.40 - (-0.80)  # Total width is 7.2 units

        # Initialize scene title
        current_title_group = create_title("Architecture Types 1 & 2: Reactive vs Goal-Based Agents", layout="70")
        self.play(FadeIn(current_title_group, shift=UP * 0.1), run_time=0.8)
        self.wait(0.5)

        ## Presentation Step 1: Architecture Type 1: Simple Reflex / Reactive
        self.play(FadeIn(current_title_group, shift=DOWN*0.1), run_time=0.8)
        # The previous title FadeIn also handles this, no need to repeat.
        # Narration Text: Direct Condition-Action rules (IF temperature > threshold THEN trip breaker)
        
        # Reactive Agent Components (ProcessNode instances)
        perception_node = ProcessNode("Perception", fill_color=C_SKY_BLUE, text_color=C_WHITE, font_size=0.18, width=2.0)
        condition_action_node = ProcessNode("Condition-Action Rules", fill_color=C_WARM_AMBER, text_color=C_WHITE, font_size=0.18, width=3.5)
        action_node = ProcessNode("Action", fill_color=C_MINT_SEAFOAM, text_color=C_WHITE, font_size=0.18, width=2.0)

        # Arrange nodes horizontally within the content safe area
        reactive_nodes_group = VGroup(perception_node, condition_action_node, action_node).arrange(RIGHT, buff=0.8)
        reactive_nodes_group.move_to(RIGHT * content_center_x + DOWN * 0.5)
        
        # Ensure the group fits within the allowed width
        if reactive_nodes_group.width > content_width:
            reactive_nodes_group.scale_to_fit_width(content_width - 0.2)
            reactive_nodes_group.move_to(RIGHT * content_center_x + DOWN * 0.5)

        # Arrows connecting the nodes
        arrow1 = Arrow(perception_node.box.get_right(), condition_action_node.box.get_left(), buff=0.2, stroke_color=C_TEXT, tip_length=0.2)
        arrow2 = Arrow(condition_action_node.box.get_right(), action_node.box.get_left(), buff=0.2, stroke_color=C_TEXT, tip_length=0.2)

        # Narration-aligned text for explanation
        narration_text1 = CrispText("Direct Condition-Action rules", size=6, weight=NORMAL, color=C_BODY, alignment="left")
        narration_text1.next_to(condition_action_node, UP, buff=0.3).align_to(condition_action_node, LEFT)

        if_then_example = CrispText("If temperature > threshold\nTHEN trip breaker", size=6, weight=NORMAL, color=C_TEXT, alignment="left")
        if_then_example.next_to(condition_action_node, DOWN, buff=0.3)
        
        # Animate the components
        self.play(
            GrowFromCenter(perception_node),
            run_time=1.5
        )
        self.wait(1.0) # Adjusted wait
        self.play(
            Create(arrow1),
            GrowFromCenter(condition_action_node),
            FadeIn(narration_text1, shift=UP * 0.1),
            run_time=2.0
        )
        self.wait(1.0) # Adjusted wait
        self.play(
            FadeIn(if_then_example, shift=UP * 0.1),
            run_time=2.0
        )
        self.wait(1.0) # Adjusted wait
        self.play(
            Create(arrow2),
            GrowFromCenter(action_node),
            run_time=1.5
        )
        self.wait(1.0) # Adjusted wait

        # Kinetic element: data flowing through the reactive agent (continuous updater)
        flow_path_reactive_combined = VMobject()
        flow_path_reactive_combined.set_points_as_corners([
            perception_node.box.get_right(),
            condition_action_node.box.get_left(),
            condition_action_node.box.get_right(),
            action_node.box.get_left()
        ])
        
        reactive_stream = FlowingStream(flow_path_reactive_combined, num_dots=4, dot_color=HIGHLIGHT_COLOR, flow_speed=0.7)
        self.add(reactive_stream)
        self.wait(10.0) # Extended wait for narration to cover the concept

        ## Presentation Step 2: Reactive Strengths & Limitations
        # Narration Text: Sub-millisecond latency but zero memory or future deliberation
        
        # Morph title for the new step
        new_title_group_step2 = create_title("Reactive Strengths & Limitations", layout="70")
        self.play(
            ReplacementTransform(current_title_group, new_title_group_step2),
            FadeOut(narration_text1, shift=DOWN * 0.1),
            FadeOut(if_then_example, shift=DOWN * 0.1),
            run_time=0.6
        )
        current_title_group = new_title_group_step2
        self.wait(0.5)

        # Highlight Condition-Action Rules for latency
        highlight_latency = condition_action_node.box.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5).set_z_index(5)
        latency_text = CrispText("Sub-millisecond Latency", size=6, weight=BOLD, color=HIGHLIGHT_COLOR)
        latency_text.next_to(condition_action_node, UP, buff=0.3)

        self.play(
            Create(highlight_latency),
            FadeIn(latency_text, shift=UP * 0.1),
            run_time=1.5
        )
        self.wait(3.0) # Adjusted wait

        # Text for memory/deliberation limitation
        limitation_text = CrispText("Zero Memory or Future Deliberation", size=6, weight=NORMAL, color=C_BODY)
        limitation_text.next_to(reactive_nodes_group, DOWN, buff=1.0) # Below the entire group

        self.play(
            FadeOut(highlight_latency),
            FadeOut(latency_text, shift=DOWN * 0.1),
            FadeIn(limitation_text, shift=UP * 0.1),
            run_time=1.5
        )
        self.wait(5.0) # Adjusted wait

        ## Presentation Step 3: Architecture Type 2: Goal-Based Agents
        # Narration Text: Incorporates explicit future goals into decision formulation
        
        # Stop reactive stream and remove it
        reactive_stream.stop_flow()
        self.remove(reactive_stream)

        # Morph title for the new step
        new_title_group_step3 = create_title("Architecture Type 2: Goal-Based Agents", layout="70")
        self.remove(new_title_group_step2)
        self.play(
            ReplacementTransform(current_title_group, new_title_group_step3),
            FadeOut(limitation_text, shift=DOWN * 0.1),
            run_time=0.6
        )
        current_title_group = new_title_group_step3
        self.wait(0.5)

        # Define new positions for existing nodes and new nodes for Goal-Based architecture
        perception_node_goal = perception_node.copy().move_to(RIGHT * (content_center_x - 3.0) + UP * 0.5)
        action_node_goal = action_node.copy().move_to(RIGHT * (content_center_x + 3.0) + UP * 0.5)

        model_of_world_node = ProcessNode("Model of World", fill_color=C_STEEL_BLUE, text_color=C_WHITE, font_size=0.18, width=2.5)
        goals_node = ProcessNode("Goals", fill_color=C_LAVENDER_PERIWINKLE, text_color=C_WHITE, font_size=0.18, width=1.5)
        search_planning_node = ProcessNode("Search & Planning", fill_color=C_MUSTARD_YELLOW, text_color=C_WHITE, font_size=0.18, width=3.0)

        # Arrange internal nodes for goal-based architecture
        model_of_world_node.move_to(RIGHT * (content_center_x - 0.5) + UP * 1.0)
        goals_node.next_to(model_of_world_node, DOWN, buff=0.8).shift(LEFT * 0.5) # Below Model, slightly left
        search_planning_node.next_to(goals_node, RIGHT, buff=0.8).align_to(model_of_world_node, DOWN) # Aligned with goals, to the right

        # Arrows for goal-based connections
        arrow_p_mw = Arrow(perception_node_goal.box.get_right(), model_of_world_node.box.get_left(), buff=0.2, stroke_color=C_TEXT, tip_length=0.2)
        arrow_mw_sp = Arrow(model_of_world_node.box.get_right(), search_planning_node.box.get_left(), buff=0.2, stroke_color=C_TEXT, tip_length=0.2)
        arrow_g_sp = CurvedArrow(goals_node.box.get_right(), search_planning_node.box.get_bottom(), angle=-PI/4, stroke_color=C_TEXT, tip_length=0.2) # Removed 'buff'
        arrow_sp_a = Arrow(search_planning_node.box.get_right(), action_node_goal.box.get_left(), buff=0.2, stroke_color=C_TEXT, tip_length=0.2)

        # Narration-aligned text for goal-based
        narration_text3 = CrispText("Incorporates explicit future goals into\ndecision formulation", size=6, weight=NORMAL, color=C_BODY, alignment="left")
        narration_text3.next_to(search_planning_node, UP, buff=0.5).align_to(search_planning_node, LEFT)

        # Animate transformation from reactive to goal-based
        self.play(
            Transform(perception_node, perception_node_goal),
            Transform(action_node, action_node_goal),
            FadeOut(condition_action_node, shift=RIGHT*0.2), # Condition-Action node is removed
            FadeOut(arrow1),
            FadeOut(arrow2),
            run_time=2.0
        )
        self.wait(1.0) # Adjusted wait
        self.play(
            GrowFromCenter(model_of_world_node),
            Create(arrow_p_mw),
            run_time=1.5
        )
        self.wait(1.0) # Adjusted wait
        self.play(
            GrowFromCenter(goals_node),
            GrowFromCenter(search_planning_node),
            Create(arrow_g_sp),
            Create(arrow_mw_sp),
            FadeIn(narration_text3, shift=UP * 0.1),
            run_time=2.5
        )
        self.wait(1.0) # Adjusted wait
        self.play(
            Create(arrow_sp_a),
            run_time=1.0
        )
        self.wait(5.0) # Extended wait for narration

        # Kinetic element: data flowing through the goal-based agent
        path_points_goal = [
            perception_node_goal.box.get_right(),
            arrow_p_mw.get_end(),
            model_of_world_node.box.get_right(),
            arrow_mw_sp.get_end(),
            search_planning_node.box.get_right(),
            arrow_sp_a.get_end()
        ]
        goal_based_stream_main = FlowingStream(VMobject().set_points_as_corners(path_points_goal), num_dots=4, dot_color=HIGHLIGHT_COLOR, flow_speed=0.5)

        path_points_goal_curved = [
            goals_node.box.get_right(),
            arrow_g_sp.get_end()
        ]
        goal_based_stream_goals = FlowingStream(VMobject().set_points_as_corners(path_points_goal_curved), num_dots=2, dot_color=C_LAVENDER_PERIWINKLE, flow_speed=0.4)
        
        self.add(goal_based_stream_main, goal_based_stream_goals)
        self.wait(5.0) # Extended wait

        ## Presentation Step 4: Search & Planning Mechanisms
        # Narration Text: Evaluating multi-step sequences: will this action lead toward the goal?
        
        # Stop goal-based streams and remove them
        goal_based_stream_main.stop_flow()
        goal_based_stream_goals.stop_flow()
        self.remove(goal_based_stream_main, goal_based_stream_goals)

        # Morph title for the new step
        new_title_group_step4 = create_title("Search & Planning Mechanisms", layout="70")
        self.remove(new_title_group_step3)
        self.play(
            ReplacementTransform(current_title_group, new_title_group_step4),
            FadeOut(narration_text3, shift=DOWN * 0.1),
            run_time=0.6
        )
        current_title_group = new_title_group_step4
        self.wait(0.5)

        # Highlight Search & Planning node
        highlight_sp = search_planning_node.box.copy().set_fill(opacity=0).set_stroke(color=HIGHLIGHT_COLOR, width=3.5, z_index=5)
        
        planning_text = CrispText("Evaluating Multi-step Sequences:\nWill this action lead toward the goal?", size=6, weight=NORMAL, color=C_BODY, alignment="left")
        planning_text.next_to(search_planning_node, DOWN, buff=0.8)

        self.play(
            Create(highlight_sp),
            FadeIn(planning_text, shift=UP * 0.1),
            run_time=2.0
        )
        self.wait(7.0) # Extended wait for narration
        self.play(
            FadeOut(highlight_sp),
            FadeOut(planning_text, shift=DOWN * 0.1),
            run_time=1.0
        )
        self.wait(0.5)

        ## Presentation Step 5: Architectural Trade-Off Comparison
        # Narration Text: Reflex speed vs. Deliberative foresight in enterprise operations
        
        # Morph title for the new step
        new_title_group_step5 = create_title("Architectural Trade-Off Comparison", layout="70")
        self.remove(new_title_group_step4)
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(new_title_group_step5, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = new_title_group_step5
        self.wait(0.5)

        # Fade out previous goal-based diagram elements to make way for comparison
        self.play(
            FadeOut(perception_node),
            FadeOut(model_of_world_node),
            FadeOut(goals_node),
            FadeOut(search_planning_node),
            FadeOut(action_node),
            FadeOut(arrow_p_mw),
            FadeOut(arrow_mw_sp),
            FadeOut(arrow_g_sp),
            FadeOut(arrow_sp_a),
            run_time=1.5
        )
        self.wait(0.5)
        
        # Reactive Agent for Comparison Column
        reactive_col_header = CrispText("Reactive Agent", size=6, weight=BOLD, color=C_SKY_BLUE)
        reactive_col_desc = CrispText("Reflex Speed", size=6, weight=SEMIBOLD, color=C_CORAL_PEACH)
        
        comp_perception_r = ProcessNode("Perception", fill_color=C_SKY_BLUE, text_color=C_WHITE, font_size=0.16, width=1.5, height=0.7)
        comp_ca_r = ProcessNode("Condition-Action", fill_color=C_WARM_AMBER, text_color=C_WHITE, font_size=0.16, width=2.5, height=0.7)
        comp_action_r = ProcessNode("Action", fill_color=C_MINT_SEAFOAM, text_color=C_WHITE, font_size=0.16, width=1.5, height=0.7)

        comp_reactive_group = VGroup(comp_perception_r, comp_ca_r, comp_action_r).arrange(RIGHT, buff=0.4)
        comp_arrow_r1 = Arrow(comp_perception_r.box.get_right(), comp_ca_r.box.get_left(), buff=0.15, stroke_color=C_TEXT, tip_length=0.18)
        comp_arrow_r2 = Arrow(comp_ca_r.box.get_right(), comp_action_r.box.get_left(), buff=0.15, stroke_color=C_TEXT, tip_length=0.18)
        
        reactive_diagram = VGroup(comp_reactive_group, comp_arrow_r1, comp_arrow_r2)
        reactive_col_content = VGroup(reactive_col_header, reactive_col_desc, reactive_diagram).arrange(DOWN, buff=0.5).align_to(reactive_col_header, LEFT)

        # Goal-Based Agent for Comparison Column
        goal_col_header = CrispText("Goal-Based Agent", size=6, weight=BOLD, color=C_STEEL_BLUE)
        goal_col_desc = CrispText("Deliberative Foresight", size=6, weight=SEMIBOLD, color=C_LAVENDER_PERIWINKLE)
        
        comp_perception_g = ProcessNode("Perception", fill_color=C_SKY_BLUE, text_color=C_WHITE, font_size=0.16, width=1.5, height=0.7)
        comp_model_g = ProcessNode("Model", fill_color=C_STEEL_BLUE, text_color=C_WHITE, font_size=0.16, width=1.5, height=0.7)
        comp_goals_g = ProcessNode("Goals", fill_color=C_LAVENDER_PERIWINKLE, text_color=C_WHITE, font_size=0.16, width=1.5, height=0.7)
        comp_sp_g = ProcessNode("Search & Planning", fill_color=C_MUSTARD_YELLOW, text_color=C_WHITE, font_size=0.16, width=2.5, height=0.7)
        comp_action_g = ProcessNode("Action", fill_color=C_MINT_SEAFOAM, text_color=C_WHITE, font_size=0.16, width=1.5, height=0.7)

        # Arrange goal-based components more compactly for comparison
        comp_perception_g.move_to(LEFT * 2.0 + UP * 0.5)
        comp_action_g.move_to(RIGHT * 2.0 + UP * 0.5)
        comp_model_g.next_to(comp_perception_g, RIGHT, buff=0.4).shift(UP * 0.5)
        comp_goals_g.next_to(comp_model_g, DOWN, buff=0.4).align_to(comp_perception_g, LEFT) # Aligned below model
        comp_sp_g.next_to(comp_goals_g, RIGHT, buff=0.4).align_to(comp_model_g, UP) # Align with model top
        comp_sp_g.move_to(VGroup(comp_model_g, comp_goals_g).get_center() + RIGHT * 1.5) # Re-center SP

        comp_arrow_pg = Arrow(comp_perception_g.box.get_right(), comp_model_g.box.get_left(), buff=0.15, stroke_color=C_TEXT, tip_length=0.18)
        comp_arrow_mg_sp = Arrow(comp_model_g.box.get_right(), comp_sp_g.box.get_left(), buff=0.15, stroke_color=C_TEXT, tip_length=0.18)
        comp_arrow_gg_sp = CurvedArrow(comp_goals_g.box.get_right(), comp_sp_g.box.get_bottom(), angle=-PI/4, stroke_color=C_TEXT, tip_length=0.18) # Removed 'buff'
        comp_arrow_spg_a = Arrow(comp_sp_g.box.get_right(), comp_action_g.box.get_left(), buff=0.15, stroke_color=C_TEXT, tip_length=0.18)

        goal_diagram = VGroup(comp_perception_g, comp_model_g, comp_goals_g, comp_sp_g, comp_action_g,
                              comp_arrow_pg, comp_arrow_mg_sp, comp_arrow_gg_sp, comp_arrow_spg_a)
        goal_col_content = VGroup(goal_col_header, goal_col_desc, goal_diagram).arrange(DOWN, buff=0.5).align_to(goal_col_header, LEFT)

        # Arrange both columns side-by-side in the content area
        comparison_group = VGroup(reactive_col_content, goal_col_content).arrange(RIGHT, buff=1.5)
        comparison_group.scale_to_fit_width(content_width - 0.4) # Ensure it fits with margins
        comparison_group.move_to(RIGHT * content_center_x + DOWN * 0.3)

        narration_text5 = CrispText("Reflex speed vs. Deliberative foresight\nin enterprise operations", size=6, weight=NORMAL, color=C_BODY, alignment="center")
        narration_text5.next_to(comparison_group, DOWN, buff=1.0)

        self.play(
            FadeIn(reactive_col_content, shift=LEFT * 0.5),
            FadeIn(goal_col_content, shift=RIGHT * 0.5),
            run_time=2.0
        )
        self.wait(0.5)
        self.play(
            FadeIn(narration_text5, shift=UP * 0.1),
            run_time=1.5
        )
        self.wait(5.0) # Extended wait for narration

        # Add continuous flow to the comparison diagrams
        comp_reactive_flow_path = VMobject()
        comp_reactive_flow_path.set_points_as_corners([
            comp_perception_r.box.get_right(), comp_ca_r.box.get_left(),
            comp_ca_r.box.get_right(), comp_action_r.box.get_left()
        ])
        comp_reactive_stream = FlowingStream(comp_reactive_flow_path, num_dots=3, dot_color=HIGHLIGHT_COLOR, flow_speed=0.6)
        self.add(comp_reactive_stream)

        comp_goal_main_flow_path = VMobject()
        comp_goal_main_flow_path.set_points_as_corners([
            comp_perception_g.box.get_right(), comp_model_g.box.get_left(),
            comp_model_g.box.get_right(), comp_sp_g.box.get_left(),
            comp_sp_g.box.get_right(), comp_action_g.box.get_left()
        ])
        comp_goal_main_stream = FlowingStream(comp_goal_main_flow_path, num_dots=4, dot_color=HIGHLIGHT_COLOR, flow_speed=0.5)

        comp_goal_goals_flow_path = VMobject()
        comp_goal_goals_flow_path.set_points_as_corners([
            comp_goals_g.box.get_right(), comp_arrow_gg_sp.get_end()
        ])
        comp_goal_goals_stream = FlowingStream(comp_goal_goals_flow_path, num_dots=2, dot_color=C_LAVENDER_PERIWINKLE, flow_speed=0.4)
        self.add(comp_goal_main_stream, comp_goal_goals_stream)

        self.wait(10.0) # Final wait to let the streams flow during narration

        # Clean up all mobjects at the end of the scene
        self.play(
            FadeOut(current_title_group),
            FadeOut(reactive_col_content),
            FadeOut(goal_col_content),
            FadeOut(narration_text5),
            run_time=1.0
        )
        comp_reactive_stream.stop_flow()
        comp_goal_main_stream.stop_flow()
        comp_goal_goals_stream.stop_flow()
        self.remove(comp_reactive_stream, comp_goal_main_stream, comp_goal_goals_stream)
        self.wait(1.0)