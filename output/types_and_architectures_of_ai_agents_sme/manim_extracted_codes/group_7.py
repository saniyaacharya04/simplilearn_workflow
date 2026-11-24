C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_CORAL = "#E58F6D"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_WHITE = "#FFFFFF"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
SME_LAYOUT = '20'
from feedback_functions_vlm.instrumented_scene import InstrumentedScene
import os
import re
import numpy as np
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

# DEGREES is available directly from manim, no need for manim.constants
# from manim.constants import DEGTORAD # Removed explicit import for DEGTORAD



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

if "CrispText" not in globals():


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
def create_clean_title(text_str):
    title = CrispText(text_str, size=22, weight=BOLD, color="#0F172A")
    line = Line(ORIGIN, RIGHT * title.width, color="#2C81FE", stroke_width=2.5)
    line.next_to(title, DOWN, buff=0.1, aligned_edge=LEFT)
    grp = VGroup(title, line)
    grp.move_to([-1.0, 3.2, 0])
    grp.set_z_index(20)
    return grp

def create_datum_bay(center_x, width=3.6, top_y=1.6, bot_y=-2.8):
    top_line = Line([center_x - width/2, top_y, 0], [center_x + width/2, top_y, 0], color="#CBD5E1", stroke_width=1.5)
    bot_line = Line([center_x - width/2, bot_y, 0], [center_x + width/2, bot_y, 0], color="#CBD5E1", stroke_width=1.5)
    ticks = VGroup()
    for lx in [center_x - width/2, center_x, center_x + width/2]:
        ticks.add(Line([lx, top_y - 0.08, 0], [lx, top_y + 0.08, 0], color="#94A3B8", stroke_width=1.5))
        ticks.add(Line([lx, bot_y - 0.08, 0], [lx, bot_y + 0.08, 0], color="#94A3B8", stroke_width=1.5))
    return VGroup(top_line, bot_line, ticks)



class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        # 1. Canvas Background Setup
        self.camera.background_color = "#FFFFFF"
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

        # The following functions are defined globally and then redefined locally.
        # Keeping the local definitions if they differ or are unique to the scene,
        # otherwise removing identical local redefinitions.



        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)











        # Removed redundant local definition, using global create_checkmark
        # def create_checkmark(*args, **kwargs):
        #     c = kwargs.get('color', globals().get('C_STEEL_BLUE', '#7EA2C8'))
        #     for a in args:
        #         if isinstance(a, str) and (a.startswith('#') or a in globals()):
        #             c = a
        #     sz = kwargs.get('size', kwargs.get('font_size', 0.22))
        #     if isinstance(sz, (int, float)) and sz > 1.0:
        #         sz = sz / 60.0
        #     sw = kwargs.get('stroke_width', 3.5)
        #     p1 = ORIGIN
        #     p2 = p1 + RIGHT * (sz * 0.42) + DOWN * (sz * 0.55)
        #     p3 = p2 + RIGHT * (sz * 0.95) + UP * (sz * 1.15)
        #     l1 = Line(p1, p2, color=c, stroke_width=sw)
        #     l2 = Line(p2, p3, color=c, stroke_width=sw)
        #     g = VGroup(l1, l2)
        #     g.center()
        #     return g

        # Removed redundant local definition, using global create_crossmark
        # def create_crossmark(*args, **kwargs):
        #     c = kwargs.get('color', globals().get('C_CORAL', '#E58F6D'))
        #     for a in args:
        #         if isinstance(a, str) and (a.startswith('#') or a in globals()):
        #             c = a
        #     sz = kwargs.get('size', kwargs.get('font_size', 0.22))
        #     if isinstance(sz, (int, float)) and sz > 1.0:
        #         sz = sz / 60.0
        #     sw = kwargs.get('stroke_width', 3.5)
        #     l1 = Line(ORIGIN, RIGHT * (sz * 0.8) + UP * (sz * 0.8), color=c, stroke_width=sw)
        #     l2 = Line(ORIGIN + UP * (sz * 0.8), RIGHT * (sz * 0.8), color=c, stroke_width=sw)
        #     g = VGroup(l1, l2)
        #     g.center()
        #     return g



        # Removed redundant definitions of create_header
        # def create_header(*args, **kwargs):
        #     return create_title(*args, **kwargs)
        # def create_header(*args, **kwargs):
        #     return create_title(*args, **kwargs)
        # def create_header(*args, **kwargs):
        #     return create_title(*args, **kwargs)


        # =========================================================================
        # PRESENTATION STEP 1: Introduction of Three Agent Types
        title_group = create_title("Autonomous Decision Models")
        self.play(FadeIn(title_group, shift=DOWN*0.1), run_time=0.8)
        # =========================================================================
        ## Presentation Step 1

        title_step1 = create_clean_title("Types of Autonomous Agents")
        self.play(FadeIn(title_step1, shift=DOWN * 0.1), run_time=1.0)

        # Central Distribution Node
        dist_bg = RoundedRectangle(
            width=3.2, height=0.52, corner_radius=0.14,
            fill_color="#F1F5F9", fill_opacity=1.0, stroke_color="#7EA2C8", stroke_width=1.8
        ).move_to([0.0, 2.2, 0])
        dist_txt = CrispText("Autonomous Decision Models", size=13, weight=BOLD, color="#0F172A").move_to(dist_bg)
        fit_into_box(dist_txt, dist_bg, pad_x=0.2, pad_y=0.08)
        dist_node = VGroup(dist_bg, dist_txt).set_z_index(10)

        self.play(FadeIn(dist_node, shift=DOWN * 0.15), run_time=1.0)

        # Three Datum Bays (Open structural staging areas framed by datum lines)
        bay1_datum = create_datum_bay(-4.2)
        bay2_datum = create_datum_bay(0.0)
        bay3_datum = create_datum_bay(4.2)

        # Conduits branching from central node to bay tops
        cond1 = CubicBezier([0, 1.94, 0], [-1.5, 1.94, 0], [-3.0, 1.6, 0], [-4.2, 1.6, 0], color="#7EA2C8", stroke_width=2.0)
        cond2 = Line([0, 1.94, 0], [0, 1.6, 0], color="#7EA2C8", stroke_width=2.0)
        cond3 = CubicBezier([0, 1.94, 0], [1.5, 1.94, 0], [3.0, 1.6, 0], [4.2, 1.6, 0], color="#7EA2C8", stroke_width=2.0)

        conduits = VGroup(cond1, cond2, cond3)

        self.play(Create(conduits), run_time=2.0)
        self.play(Create(bay1_datum), Create(bay2_datum), Create(bay3_datum), run_time=2.0)

        # Bay Title Badges
        badge1 = create_pill("Reactive Model", bg_color="#62B7E4", font_size=12).move_to([-4.2, 1.2, 0])
        badge2 = create_pill("Goal-Based Architecture", bg_color="#7EA2C8", font_size=12).move_to([0.0, 1.2, 0])
        badge3 = create_pill("Utility-Based Optimization", bg_color="#9B99C7", font_size=12).move_to([4.2, 1.2, 0])

        bay_badges = VGroup(badge1, badge2, badge3)
        self.play(FadeIn(bay_badges, shift=DOWN * 0.1), run_time=1.5)

        # Ambient focus indicator on Reactive Bay
        reactive_focus = RoundedRectangle(
            width=3.6, height=4.3, corner_radius=0.2,
            fill_color="#62B7E4", fill_opacity=0.04, stroke_color="#F78908", stroke_width=2.2
        ).move_to([-4.2, -0.6, 0])
        self.play(Create(reactive_focus), run_time=1.5)

        # Kinetic Bus Signal Pulses
        pulse1 = Dot(color="#2C81FE", radius=0.08).move_to(dist_bg.get_bottom())
        pulse2 = Dot(color="#2C81FE", radius=0.08).move_to(dist_bg.get_bottom())
        pulse3 = Dot(color="#2C81FE", radius=0.08).move_to(dist_bg.get_bottom())

        self.play(
            MoveAlongPath(pulse1, cond1, rate_func=linear),
            MoveAlongPath(pulse2, cond2, rate_func=linear),
            MoveAlongPath(pulse3, cond3, rate_func=linear),
            run_time=3.0
        )
        self.play(FadeOut(pulse1), FadeOut(pulse2), FadeOut(pulse3), run_time=0.5)

        # Fill Step 1 duration (44.14s exact total)
        self.wait(31.64)

        # =========================================================================
        # PRESENTATION STEP 2: Reactive Agent: Rule-Driven Reflex
        # =========================================================================
        ## Presentation Step 2

        title_step2 = create_clean_title("Reactive Agent: Rule-Driven")
        self.play(FadeOut(title_step1), run_time=0.35)
        self.play(FadeIn(title_step2, shift=DOWN * 0.1), run_time=0.45)
        self.play(FadeOut(reactive_focus), run_time=0.5)

        # Subdue Center & Right Bays
        self.play(
            bay2_datum.animate.set_opacity(0.60),
            bay3_datum.animate.set_opacity(0.60),
            badge2.animate.set_opacity(0.60),
            badge3.animate.set_opacity(0.60),
            run_time=1.0
        )

        # Floating Struck-Through Constraint Tags above switch conduit
        tag1_bg = RoundedRectangle(width=1.5, height=0.32, corner_radius=0.16, fill_color="#FEE2E2", fill_opacity=0.9, stroke_color="#FCA5A5", stroke_width=1.2)
        tag1_txt = CrispText("Zero State Storage", size=9, weight=BOLD, color="#E55353").move_to(tag1_bg)
        tag1_strike = Line(tag1_bg.get_left() + LEFT*0.04, tag1_bg.get_right() + RIGHT*0.04, color="#E55353", stroke_width=2.0)
        tag1 = VGroup(tag1_bg, tag1_txt, tag1_strike).move_to([-5.1, 0.45, 0])

        tag2_bg = RoundedRectangle(width=1.5, height=0.32, corner_radius=0.16, fill_color="#FEE2E2", fill_opacity=0.9, stroke_color="#FCA5A5", stroke_width=1.2)
        tag2_txt = CrispText("Zero Plan Horizon", size=9, weight=BOLD, color="#E55353").move_to(tag2_bg)
        tag2_strike = Line(tag2_bg.get_left() + LEFT*0.04, tag2_bg.get_right() + RIGHT*0.04, color="#E55353", stroke_width=2.0)
        tag2 = VGroup(tag2_bg, tag2_txt, tag2_strike).move_to([-3.3, 0.45, 0])

        constraint_tags = VGroup(tag1, tag2)
        self.play(FadeIn(constraint_tags, shift=DOWN * 0.1), run_time=1.0)

        # 1. Telemetry Sensor Icon & Condition Badge
        sensor_box = Circle(radius=0.42, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#62B7E4", stroke_width=2.0).move_to([-5.5, -0.4, 0])
        wave = ParametricFunction(lambda t: np.array([t, 0.12 * np.sin(5 * np.pi * t), 0]), t_range=[-0.25, 0.25], color="#62B7E4", stroke_width=2.0).move_to(sensor_box.get_center())
        sensor_icon = VGroup(sensor_box, wave)
        cond_badge = create_pill("Output Below 8%", bg_color="#E58F6D", font_size=9).next_to(sensor_box, DOWN, buff=0.15)
        sensor_grp = VGroup(sensor_icon, cond_badge)

        # 2. Rule Engine Icon
        rule_box = Circle(radius=0.42, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#7EA2C8", stroke_width=2.0).move_to([-4.2, -0.4, 0])
        gear_center = rule_box.get_center()
        gear_teeth = VGroup(*[
            Square(side_length=0.11, fill_color="#7EA2C8", fill_opacity=1.0, stroke_width=0).move_to(gear_center + 0.38 * np.array([np.cos(a), np.sin(a), 0]))
            for a in np.linspace(0, 2*np.pi, 8, endpoint=False)
        ])
        gear_inner = Circle(radius=0.22, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#7EA2C8", stroke_width=1.5).move_to(gear_center)
        switch_lever = Line(gear_center + LEFT*0.12 + DOWN*0.08, gear_center + RIGHT*0.12 + UP*0.08, color="#F78908", stroke_width=2.5)
        rule_icon = VGroup(gear_teeth, rule_box, gear_inner, switch_lever)
        rule_lbl = CrispText("Rule Engine", size=10, weight=BOLD, color="#404040").next_to(rule_box, DOWN, buff=0.15)
        rule_grp = VGroup(rule_icon, rule_lbl)

        # 3. Actuator Dispatch Icon
        dispatch_box = Circle(radius=0.42, fill_color="#FEF3C7", fill_opacity=1.0, stroke_color="#E6A157", stroke_width=2.0).move_to([-2.9, -0.4, 0])
        beacon = Triangle(color="#E55353", fill_color="#E55353", fill_opacity=0.85).scale(0.18).move_to(dispatch_box.get_center())
        dispatch_icon = VGroup(dispatch_box, beacon)
        action_lbl = create_pill("Send Dispatch Alert", bg_color="#E55353", font_size=9).next_to(dispatch_box, DOWN, buff=0.15)
        dispatch_grp = VGroup(dispatch_icon, action_lbl)

        # Lateral Transmission Conduits
        arr_rx1 = Arrow(sensor_box.get_right(), rule_box.get_left(), buff=0.08, stroke_width=2.5, max_tip_length_to_length_ratio=0.25, color="#62B7E4")
        arr_rx2 = Arrow(rule_box.get_right(), dispatch_box.get_left(), buff=0.08, stroke_width=2.5, max_tip_length_to_length_ratio=0.25, color="#E6A157")

        rx_chain = VGroup(sensor_grp, arr_rx1, rule_grp, arr_rx2, dispatch_grp)
        self.play(FadeIn(rx_chain, shift=DOWN * 0.1), run_time=1.5)

        # Operational Performance & Scope Descriptors
        perf_lbl = CrispText("Sub-Millisecond Execution", size=10, weight=BOLD, color="#2D6A4F").move_to([-4.2, -1.75, 0])
        scope_pill = create_pill("Fixed Static Response", bg_color="#F1F5F9", text_color="#64748B", font_size=10).next_to(perf_lbl, DOWN, buff=0.12)
        bottom_descriptors = VGroup(perf_lbl, scope_pill)
        self.play(FadeIn(bottom_descriptors, shift=UP * 0.1), run_time=1.0)

        # Pulse animation through Reactive Engine
        rx_pulse = Dot(color="#F78908", radius=0.09).move_to(sensor_box.get_center())
        self.play(FadeIn(rx_pulse), run_time=0.3)
        self.play(MoveAlongPath(rx_pulse, arr_rx1, rate_func=linear), run_time=0.8)
        self.play(rule_box.animate.set_stroke(color="#F78908", width=3.0), run_time=0.3)
        self.play(MoveAlongPath(rx_pulse, arr_rx2, rate_func=linear), run_time=0.8)
        self.play(
            dispatch_box.animate.set_stroke(color="#E55353", width=3.5),
            FadeOut(rx_pulse),
            run_time=0.4
        )
        self.play(
            rule_box.animate.set_stroke(color="#7EA2C8", width=2.0),
            dispatch_box.animate.set_stroke(color="#E6A157", width=2.0),
            run_time=0.5
        )

        # Group reactive bay content for subduing in Step 3
        reactive_bay_content = VGroup(constraint_tags, rx_chain, bottom_descriptors)

        # Fill Step 2 duration (44.148s exact total)
        self.wait(35.048)

        # =========================================================================
        # PRESENTATION STEP 3: Goal-Based Agent: Planned Outcomes
        # =========================================================================
        ## Presentation Step 3

        title_step3 = create_clean_title("Goal-Based Agent: Planned Outcomes")
        self.play(FadeOut(title_step2), run_time=0.35)
        self.play(FadeIn(title_step3, shift=DOWN * 0.1), run_time=0.45)

        # Subdue Reactive Bay (Left), Activate Goal-Based Bay (Center)
        self.play(
            bay1_datum.animate.set_opacity(0.60),
            badge1.animate.set_opacity(0.60),
            reactive_bay_content.animate.set_opacity(0.60),
            bay2_datum.animate.set_opacity(1.0),
            badge2.animate.set_opacity(1.0),
            run_time=1.0
        )

        # Build Goal-Based Trajectory Network in Center Bay (x = 0.0)
        # 1. Reasoning Core (Agent Core) at x = -1.45, y = -0.4
        agent_core_bg = Circle(radius=0.42, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#7EA2C8", stroke_width=2.0).move_to([-1.45, -0.4, 0])
        lattice_dots = VGroup(
            Dot([-1.55, -0.3, 0], radius=0.04, color="#2C81FE"),
            Dot([-1.35, -0.3, 0], radius=0.04, color="#2C81FE"),
            Dot([-1.45, -0.5, 0], radius=0.04, color="#2C81FE")
        )
        lattice_lines = VGroup(
            Line([-1.55, -0.3, 0], [-1.35, -0.3, 0], color="#7EA2C8", stroke_width=1.0),
            Line([-1.55, -0.3, 0], [-1.45, -0.5, 0], color="#7EA2C8", stroke_width=1.0),
            Line([-1.35, -0.3, 0], [-1.45, -0.5, 0], color="#7EA2C8", stroke_width=1.0)
        )
        agent_core_icon = VGroup(agent_core_bg, lattice_lines, lattice_dots)
        agent_core_lbl = CrispText("Agent Core", size=10, weight=BOLD, color="#404040").next_to(agent_core_bg, DOWN, buff=0.12)
        agent_core_grp = VGroup(agent_core_icon, agent_core_lbl)

        # 2. Target Objective (Root Cause Identified) at x = 1.45, y = -0.4
        reticle_outer = Circle(radius=0.42, fill_color="#FEF3C7", fill_opacity=1.0, stroke_color="#E6A157", stroke_width=2.0).move_to([1.45, -0.4, 0])
        reticle_inner = Circle(radius=0.24, fill_color="#FFFFFF", fill_opacity=0.0, stroke_color="#E6A157", stroke_width=1.5).move_to([1.45, -0.4, 0])
        reticle_ch1 = Line([1.23, -0.4, 0], [1.67, -0.4, 0], color="#E6A157", stroke_width=1.5)
        reticle_ch2 = Line([1.45, -0.62, 0], [1.45, -0.18, 0], color="#E6A157", stroke_width=1.5)
        target_icon = VGroup(reticle_outer, reticle_inner, reticle_ch1, reticle_ch2)
        target_lbl = CrispText("Root Cause Identified", size=9, weight=BOLD, color="#E6A157").next_to(reticle_outer, DOWN, buff=0.12)
        target_grp = VGroup(target_icon, target_lbl)

        # 3. Option Evaluation Junction Node at x = -0.75, y = -0.4
        junc_bg = Square(side_length=0.28, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#94A3B8", stroke_width=1.5).rotate(45 * DEGREES).move_to([-0.75, -0.4, 0])
        junc_glyph = CrispText("◇", size=10, color="#64748B").move_to(junc_bg)
        junc_node = VGroup(junc_bg, junc_glyph)

        conn_core_junc = Line(agent_core_bg.get_right(), junc_bg.get_left(), color="#7EA2C8", stroke_width=2.0)

        # 4. Three Diverging Pathways
        # Upper exploratory path (ends in open terminal node)
        p_upper = CubicBezier([-0.61, -0.4, 0], [-0.35, 0.35, 0], [-0.05, 0.45, 0], [0.25, 0.45, 0], color="#62B7E4", stroke_width=1.5)