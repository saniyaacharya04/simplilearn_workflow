C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
C_HIGHLIGHT = "#F78908"
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
from manim_slides import Slide

# --- Global Constants and Helper Functions (Simplilearn Framework) ---

# Colors (10-color infographic pastel palette + core UI colors)
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

C_HIGHLIGHT_ORANGE = "#F78908" # Focus highlight color
C_DARK_SLATE_TITLE = "#1E293B" # For main titles and headers
C_SLATE_BODY = "#334155"       # For body text
C_DARK_CHARCOAL = "#404040"    # General dark text on light backgrounds
C_LIGHT_CANVAS = "#F0F4F8"     # Background color for light infographic canvas
C_WHITE = "#FFFFFF"            # Pure white for cards, text on dark

# Font settings
FONT_OPEN_SANS = "Open Sans"

# Helper for CrispText (maps descriptive sizes to Manim unit heights)




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

class FlowingParticle(Dot):
    def __init__(self, path_mobject, color=C_HIGHLIGHT_ORANGE, radius=0.08, speed=0.5, **kwargs):
        super().__init__(color=color, radius=radius, **kwargs)
        self.path_mobject = path_mobject
        self.speed = speed
        self.tracker = ValueTracker(0) # Proportion along the path

        # Use partial functions for updaters to bind self and path_mobject
        def update_particle_position(mob, dt):
            mob.tracker.increment_value(mob.speed * dt)
            if mob.tracker.get_value() >= 1:
                mob.tracker.set_value(0) # Reset to start for continuous loop
            mob.move_to(mob.path_mobject.point_from_proportion(mob.tracker.get_value()))
        
        self.add_updater(update_particle_position)
        
    def cease_flow(self):
        self.remove_updater(self.updaters[0]) # Remove the position updater


class FinalScene(Slide, MovingCameraScene): # Inherit from Slide for Manim-Slides
    def construct(self):
        # 1. Canvas Background: #F0F4F8 (Modern Soft Light Slate Canvas)
        self.camera.background_color = C_LIGHT_CANVAS
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















        # --- Scene Setup: Define common positions and dimensions for Layout 70% ---
        # Content workspace: x ∈ [-0.80, +6.40], y ∈ [-3.60, +2.20].
        # Title will be at x = -0.80, y = 3.2 (top-left of content area).

        # --- Mobject Definitions (will be animated progressively) ---

        # 1. Environment components (hero illustrations)
        # Assume images exist in 'images/' directory.
        solar_plant_img = ImageMobject("images/scene_5_solar_plant.png")
        power_grid_img = ImageMobject("images/scene_5_power_grid.png")
        database_img = ImageMobject("images/scene_5_database.png")
        
        # Scale to fit height and then arrange
        img_height = 1.2 # Standard height for these icons
        solar_plant_img.scale_to_fit_height(img_height)
        power_grid_img.scale_to_fit_height(img_height)
        database_img.scale_to_fit_height(img_height)

        # Arrange environment images horizontally
        environment_icons = VGroup(solar_plant_img, power_grid_img, database_img).arrange(RIGHT, buff=0.6)
        
        # Ensure the environment group is on the right side of the content area
        environment_group = Group(environment_icons)
        environment_group.move_to(RIGHT * 4.0 + DOWN * 0.5) # Center in the right content area
        environment_label = CrispText("Operational Environment", size="header", weight=BOLD, color=C_DARK_SLATE_TITLE)
        environment_label.next_to(environment_group, DOWN, buff=0.4)
        environment_vgroup = VGroup(environment_group, environment_label) # Group for easy animation

        # 2. Agent Core component (human operator icon)
        human_operator_img = ImageMobject("images/scene_5_human_operator.png")
        human_operator_img.scale_to_fit_height(1.8) # Slightly larger as a central figure
        
        # Position agent to the left of the environment, within the content area
        agent_core_group = Group(human_operator_img)
        agent_core_group.move_to(RIGHT * 0.8 + DOWN * 0.5)
        agent_core_label = CrispText("Agent Core", size="header", weight=BOLD, color=C_DARK_SLATE_TITLE)
        agent_core_label.next_to(agent_core_group, DOWN, buff=0.4)
        agent_core_vgroup = VGroup(agent_core_group, agent_core_label)

        # 3. Internal State component (smaller database icon for memory/state)
        internal_state_icon = ImageMobject("images/scene_5_database.png")
        internal_state_icon.scale_to_fit_height(0.8) # Smaller scale
        internal_state_icon.move_to(agent_core_group.get_center() + LEFT * 1.5 + UP * 0.8) # Position near agent
        internal_state_label = CrispText("Internal State", size="badge", weight=BOLD, color=C_DARK_SLATE_TITLE)
        internal_state_label.next_to(internal_state_icon, DOWN, buff=0.2)
        internal_state_vgroup = VGroup(internal_state_icon, internal_state_label)

        # 4. Action Tool (wrench icon)
        wrench_img = ImageMobject("images/scene_5_wrench.png")
        wrench_img.scale_to_fit_height(0.65) # Smaller icon
        wrench_img.move_to(environment_group.get_center() + UP * 1.0) # Position near environment, for action impact
        wrench_label = CrispText("Tool Execution", size="badge", weight=BOLD, color=C_DARK_SLATE_TITLE)
        wrench_label.next_to(wrench_img, DOWN, buff=0.2)
        wrench_vgroup = VGroup(wrench_img, wrench_label)


        # --- Paths and Particles ---
        # Perception path (Environment -> Agent)
        perception_arrow = Arrow(
            environment_group.get_left(),
            agent_core_group.get_right(),
            buff=0.3,
            stroke_width=3,
            color=C_MINT_SEAFOAM, # Mint Seafoam for perception
            tip_length=0.25
        ).shift(UP * 0.5) # Shift up slightly to differentiate from action
        perception_label = CrispText("Sensory Observation", size="badge", weight=SEMIBOLD, color=C_DARK_CHARCOAL)
        perception_label.next_to(perception_arrow, UP, buff=0.1)
        
        # Internal processing path (within Agent / to Internal State)
        internal_process_arrow_to = ArcBetweenPoints(
            agent_core_group.get_top() + LEFT * 0.5,
            internal_state_icon.get_top(),
            angle=-TAU/4, # Clockwise arc
            stroke_width=2,
            color=C_LAVENDER_PERIWINKLE,
            tip_length=0.2
        )
        internal_process_arrow_from = ArcBetweenPoints(
            internal_state_icon.get_bottom(),
            agent_core_group.get_bottom() + LEFT * 0.5,
            angle=-TAU/4, # Clockwise arc
            stroke_width=2,
            color=C_LAVENDER_PERIWINKLE,
            tip_length=0.2
        )
        internal_process_path = VGroup(internal_process_arrow_to, internal_process_arrow_from)
        internal_process_label = CrispText("Processing", size="badge", weight=SEMIBOLD, color=C_DARK_CHARCOAL)
        internal_process_label.next_to(internal_process_arrow_to, UP * 0.5 + LEFT * 0.5, buff=0.1)


        # Action path (Agent -> Environment)
        action_arrow = Arrow(
            agent_core_group.get_right(),
            environment_group.get_left(),
            buff=0.3,
            stroke_width=3,
            color=C_WARM_AMBER, # Warm Amber for action
            tip_length=0.25
        ).shift(DOWN * 0.5) # Shift down slightly
        action_label = CrispText("Action Impact", size="badge", weight=SEMIBOLD, color=C_DARK_CHARCOAL)
        action_label.next_to(action_arrow, DOWN, buff=0.1)

        # Particles for continuous flow
        perception_particle = FlowingParticle(perception_arrow, color=C_MINT_SEAFOAM, speed=0.8)
        internal_particle = FlowingParticle(internal_process_arrow_to, color=C_LAVENDER_PERIWINKLE, speed=0.6)
        action_particle = FlowingParticle(action_arrow, color=C_WARM_AMBER, speed=0.8)


        # --- Scene Title Initialization ---
        current_title_group = create_title("Continuous Agent-Environment Feedback Loop")
        self.play(FadeIn(current_title_group, shift=DOWN*0.1), run_time=0.8)
        self.wait(0.5)

        ## Presentation Step 1: The Operational Environment
        self.play(FadeIn(current_title_group, shift=DOWN*0.1), run_time=0.8)
        # Narration: Dynamic enterprise setting: solar arrays, grid fluctuations, databases
        self.sync_to(0.0) 
        self.play(FadeOut(current_title_group), run_time=0.35)
        current_title_group = step1_title

        # Animate environment components
        self.play(
            LaggedStart(
                FadeIn(environment_icons, shift=UP * 0.2),
                Write(environment_label),
                lag_ratio=0.2,
                run_time=2.0
            )
        )
        self.wait(2.0) # Hold for narration

        # Add ambient animation to environment (subtle pulse)
        env_pulse_rect = RoundedRectangle(
            width=environment_vgroup.width + 0.4,
            height=environment_vgroup.height + 0.4,
            corner_radius=0.1,
            stroke_color=C_MINT_SEAFOAM,
            stroke_width=1.5,
            fill_opacity=0
        ).move_to(environment_vgroup.get_center()).set_z_index(-1)

        def pulse_updater(m, dt):
            factor = np.sin(self.get_time() * 2) * 0.05 + 1.0 # Oscillate width between 0.95 and 1.05 of base
            m.set_stroke(width=1.5 * factor)
            m.set_opacity(np.sin(self.get_time() * 2) * 0.2 + 0.5) # Opacity oscillates
        
        env_pulse_rect.add_updater(pulse_updater)
        self.add(env_pulse_rect) # Add the pulsing outline to the scene

        self.wait_until_last_animation_finishes()
        self.wait(5.0) # Additional wait for narration
        self.next_slide()


        ## Presentation Step 2: Continuous Sensory Observation
        # Narration: Agent ingests real-time environmental telemetry
        self.sync_to(7.0) # Adjusted timestamp based on previous run_time
        step2_title = create_title("Continuous Sensory Observation")
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(step2_title, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = step2_title

        # Introduce Agent Core
        self.play(
            LaggedStart(
                FadeIn(agent_core_group, shift=UP * 0.2),
                Write(agent_core_label),
                lag_ratio=0.2,
                run_time=1.5
            )
        )
        self.wait(0.5)

        # Draw perception arrow and label
        self.play(Create(perception_arrow), Write(perception_label), run_time=1.0)
        self.wait(0.5)

        # Highlight environment and perception, start particle flow
        highlight_perception_env = environment_vgroup.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
        highlight_perception_arrow = perception_arrow.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
        
        self.play(
            Create(highlight_perception_env),
            Create(highlight_perception_arrow),
            FadeIn(perception_particle), # Add particle
            run_time=1.0
        )
        self.add(perception_particle) # Add particle to scene permanently for updater
        self.wait(2.0)
        self.play(
            FadeOut(highlight_perception_env),
            FadeOut(highlight_perception_arrow),
            run_time=0.8
        )
        
        self.wait(5.0) # Hold for narration
        self.next_slide()


        ## Presentation Step 3: Internal State Transformation
        # Narration: Updating beliefs and operational context based on observations
        self.sync_to(17.0) # Adjusted timestamp
        step3_title = create_title("Internal State Transformation")
        self.remove(step2_title)
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(step3_title, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = step3_title

        # Introduce Internal State
        self.play(
            LaggedStart(
                FadeIn(internal_state_icon, shift=UP * 0.2),
                Write(internal_state_label),
                lag_ratio=0.2,
                run_time=1.5
            )
        )
        self.wait(0.5)

        # Draw internal processing path and label
        self.play(
            Create(internal_process_path),
            Write(internal_process_label),
            run_time=1.5
        )
        self.wait(0.5)

        # Highlight agent and internal state, start internal particle flow
        highlight_agent_core = agent_core_vgroup.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
        highlight_internal_state = internal_state_vgroup.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
        highlight_internal_path = internal_process_path.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)

        self.play(
            Create(highlight_agent_core),
            Create(highlight_internal_state),
            Create(highlight_internal_path),
            FadeIn(internal_particle),
            run_time=1.0
        )
        self.add(internal_particle) # Add particle to scene permanently
        self.wait(2.0)
        self.play(
            FadeOut(highlight_agent_core),
            FadeOut(highlight_internal_state),
            FadeOut(highlight_internal_path),
            run_time=0.8
        )

        self.wait(5.0) # Hold for narration
        self.next_slide()


        ## Presentation Step 4: Action Impact & Environmental Shift
        # Narration: Agent actions alter the external state of the environment
        self.sync_to(27.0) # Adjusted timestamp
        step4_title = create_title("Action Impact & Environmental Shift")
        self.remove(step3_title)
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(step4_title, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = step4_title

        # Introduce action tool
        self.play(
            LaggedStart(
                FadeIn(wrench_img, shift=UP * 0.2),
                Write(wrench_label),
                lag_ratio=0.2,
                run_time=1.5
            )
        )
        self.wait(0.5)

        # Draw action arrow and label
        self.play(Create(action_arrow), Write(action_label), run_time=1.0)
        self.wait(0.5)

        # Highlight agent, action, environment, and wrench, start action particle flow
        highlight_action_agent = agent_core_vgroup.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
        highlight_action_arrow = action_arrow.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
        highlight_action_env = environment_vgroup.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
        highlight_wrench = wrench_vgroup.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)

        self.play(
            Create(highlight_action_agent),
            Create(highlight_action_arrow),
            Create(highlight_action_env),
            Create(highlight_wrench),
            FadeIn(action_particle),
            run_time=1.0
        )
        self.add(action_particle) # Add particle to scene permanently
        self.wait(2.0)
        self.play(
            FadeOut(highlight_action_agent),
            FadeOut(highlight_action_arrow),
            FadeOut(highlight_action_env),
            FadeOut(highlight_wrench),
            run_time=0.8
        )
        
        self.wait(5.0) # Hold for narration
        self.next_slide()


        ## Presentation Step 5: Closed-Loop Convergence
        # Narration: Perpetual feedback loop driving convergence toward mission goals
        self.sync_to(37.0) # Adjusted timestamp
        step5_title = create_title("Closed-Loop Convergence")
        self.remove(step4_title)
        self.play(FadeOut(current_title_group), run_time=0.35)
        self.play(FadeIn(step5_title, shift=DOWN * 0.1), run_time=0.45)
        current_title_group = step5_title

        # All elements are now on screen with particles flowing.
        # Highlight the entire loop to show convergence.
        # Group all dynamic elements for a collective highlight
        full_loop_elements = VGroup(
            environment_vgroup,
            agent_core_vgroup,
            internal_state_vgroup,
            wrench_vgroup,
            perception_arrow, perception_label,
            internal_process_path, internal_process_label,
            action_arrow, action_label
        )
        
        highlight_full_loop = full_loop_elements.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
        
        self.play(
            Create(highlight_full_loop),
            run_time=1.5
        )
        self.wait(3.0) # Longer hold to emphasize the complete loop

        # Fade out highlight
        self.play(FadeOut(highlight_full_loop), run_time=0.8)

        # Keep all elements on screen with updaters running for the remainder of the narration.
        self.wait(5.0) # Final hold

        # Clean up updaters before ending the scene
        perception_particle.cease_flow()
        internal_particle.cease_flow()
        action_particle.cease_flow()
        env_pulse_rect.remove_updater(pulse_updater)