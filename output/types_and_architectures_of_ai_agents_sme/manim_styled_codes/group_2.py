from manim import *

TOP = UP
BOTTOM = DOWN
try:
    from feedback_functions_vlm.instrumented_scene import InstrumentedScene
except Exception:
    try:
        from feedback_functions.instrumented_scene import InstrumentedScene
    except Exception:
        class InstrumentedScene(MovingCameraScene):
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

try:
    from manim.utils.rate_functions import *
except Exception:
    pass
import os
import re
import numpy as np

# Standard Color Tokens
C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_WHITE = "#FFFFFF"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"


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

# SME Layout Configuration: 70 Split (Left area x < -0.80 reserved for SME presenter window)
SME_LAYOUT = '70'

if "InstrumentedScene" not in globals():
    class InstrumentedScene(Scene):
        pass



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
class FinalScene(MovingCameraScene):
    def construct(self):
        # 1. Pure White Canvas Configuration
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




        # Approved 10-Color Palette Tokens
        C_SKY = "#62B7E4"
        C_STEEL = "#7EA2C8"
        C_LAVENDER = "#9B99C7"
        C_MINT = "#8ECDB7"
        C_AMBER = "#E6A157"
        C_CORAL = "#E58F6D"
        C_TITLE = "#0F172A"       # Bold Dark Slate
        C_BODY = "#334155"        # Slate Text
        C_MUTED = "#64748B"       # Subtle Annotation Text
        C_HIGHLIGHT = "#F78908"   # Warm Focus Orange

        def create_badge(icon_mob, bg_color=C_SKY, radius=0.32):
            disc = Circle(radius=radius, fill_color=bg_color, fill_opacity=0.18, stroke_color=bg_color, stroke_width=2)
            icon_mob.move_to(disc.get_center())
            return VGroup(disc, icon_mob)

        # -------------------------------------------------------------------------
        ## Presentation Step 1: Solara Goal-Driven Operational Pipeline
        # Step Duration: 26.66s
        # -------------------------------------------------------------------------
        step1_title = create_title(
            "Diverse Architectures & Learning Objectives",
            "Solara Energy: Goal-Driven Autonomous Execution"
        )
        self.play(FadeIn(step1_title, shift=DOWN * 0.15), run_time=0.8)

        # 1.1 Solara Master Brand Emblem (Anchored at x = -0.1, y = 1.25)
        sun_core = Circle(radius=0.32, fill_color=C_AMBER, fill_opacity=0.9, stroke_color="#FFFFFF", stroke_width=2)
        sun_rays = VGroup(*[
            Line(
                start=sun_core.point_at_angle(a) + 0.05 * np.array([np.cos(a), np.sin(a), 0]),
                end=sun_core.point_at_angle(a) + 0.15 * np.array([np.cos(a), np.sin(a), 0]),
                stroke_color=C_AMBER, stroke_width=2.0
            )
            for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)
        ])
        brand_name = CrispText("Solara Energy", size=14, weight="BOLD", color=C_TITLE)
        brand_sub = CrispText("Operations Hub", size=10, weight="NORMAL", color=C_MUTED)
        brand_txt = VGroup(brand_name, brand_sub).arrange(DOWN, aligned_edge=LEFT, buff=0.04)
        brand_txt.next_to(sun_core, RIGHT, buff=0.16)
        solara_emblem = VGroup(sun_core, sun_rays, brand_txt).move_to([-0.1, 1.25, 0])

        self.play(
            GrowFromCenter(sun_core),
            Create(sun_rays),
            FadeIn(brand_txt, shift=RIGHT * 0.15),
            run_time=1.2
        )

        # 1.2 Five Standalone Vector Pipeline Stages (Positioned at cy = 0.25 to stay clear of top title)
        def make_bullseye():
            return VGroup(
                Circle(radius=0.20, stroke_color=C_SKY, stroke_width=2),
                Circle(radius=0.10, fill_color=C_SKY, fill_opacity=0.85, stroke_color=C_SKY, stroke_width=1),
                Dot(radius=0.035, color="#FFFFFF")
            )

        def make_query_icon():
            glass = Circle(radius=0.14, stroke_color=C_STEEL, stroke_width=2)
            handle = Line(glass.point_at_angle(-np.pi / 4), glass.point_at_angle(-np.pi / 4) + np.array([0.12, -0.12, 0]), stroke_color=C_STEEL, stroke_width=2.5)
            return VGroup(glass, handle)

        def make_compare_icon():
            beam = Line([-0.16, 0.05, 0], [0.16, -0.03, 0], stroke_color=C_LAVENDER, stroke_width=2.0)
            pivot = Triangle(fill_color=C_LAVENDER, fill_opacity=1, stroke_width=0).scale(0.09).next_to(beam, DOWN, buff=-0.03)
            return VGroup(beam, pivot)

        def make_flag_icon():
            pole = Line([0, -0.18, 0], [0, 0.18, 0], stroke_color=C_CORAL, stroke_width=2.0)
            cloth = Polygon([0, 0.18, 0], [0.20, 0.09, 0], [0, 0, 0], fill_color=C_CORAL, fill_opacity=0.9, stroke_width=0)
            return VGroup(pole, cloth)

        def make_report_icon():
            sheet = RoundedRectangle(width=0.25, height=0.34, corner_radius=0.04, fill_color="#FFFFFF", fill_opacity=1, stroke_color=C_MINT, stroke_width=1.8)
            l1 = Line([-0.07, 0.07, 0], [0.07, 0.07, 0], stroke_color=C_MINT, stroke_width=1.5)
            l2 = Line([-0.07, 0.0, 0], [0.07, 0.0, 0], stroke_color=C_MINT, stroke_width=1.5)
            l3 = Line([-0.07, -0.07, 0], [0.02, -0.07, 0], stroke_color=C_MINT, stroke_width=1.5)
            return VGroup(sheet, l1, l2, l3)

        pipeline_data = [
            ("Goal: Monitor", "Site Performance", make_bullseye(), C_SKY),
            ("Query Data", "Inverter Telemetry", make_query_icon(), C_STEEL),
            ("Compare", "Model Baselines", make_compare_icon(), C_LAVENDER),
            ("Flag Alerts", "Thermal Deviations", make_flag_icon(), C_CORAL),
            ("Reports", "Ops Dispatch Ready", make_report_icon(), C_MINT),
        ]

        flow_cards = VGroup()
        connecting_arrows = VGroup()

        # Place horizontal pipeline nodes across x ∈ [1.3, 6.1], y = 0.25
        x_positions = [1.3, 2.5, 3.7, 4.9, 6.1]

        for idx, (head_txt, sub_txt, icon_vg, accent_c) in enumerate(pipeline_data):
            cx = x_positions[idx]
            cy = 0.25

            badge = create_badge(icon_vg, bg_color=accent_c, radius=0.28).move_to([cx, cy + 0.25, 0])

            title_m = CrispText(head_txt, size=11, weight="BOLD", color=C_TITLE)
            title_m.move_to([cx, cy - 0.15, 0])

            sub_m = CrispText(sub_txt, size=9, weight="NORMAL", color=C_MUTED)
            sub_m.move_to([cx, cy - 0.38, 0])

            step_chip = RoundedRectangle(width=0.36, height=0.18, corner_radius=0.04, fill_color=accent_c, fill_opacity=0.15, stroke_width=0)
            step_num = CrispText(f"0{idx+1}", size=8, weight="BOLD", color=accent_c)
            step_num.move_to(step_chip)
            chip_grp = VGroup(step_chip, step_num).move_to([cx, cy + 0.65, 0])

            node_grp = VGroup(chip_grp, badge, title_m, sub_m)
            flow_cards.add(node_grp)

            if idx < 4:
                arrow = Arrow(
                    start=[cx + 0.38, cy + 0.25, 0],
                    end=[x_positions[idx + 1] - 0.38, cy + 0.25, 0],
                    buff=0, stroke_width=2.0, color=C_STEEL, max_tip_length_to_length_ratio=0.22
                )
                connecting_arrows.add(arrow)

        # Reveal 5 pipeline stages across ~20.5 seconds
        for i in range(len(flow_cards)):
            anims = [FadeIn(flow_cards[i], shift=UP * 0.15)]
            if i > 0:
                anims.append(GrowArrow(connecting_arrows[i - 1]))
            self.play(*anims, run_time=1.0)

            # Focal stroke highlight on active node badge
            badge_glow = flow_cards[i][1][0].copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
            self.play(Create(badge_glow), run_time=0.4)
            self.play(FadeOut(badge_glow), run_time=0.3)
            self.wait(2.4)

        # Kinetic packet flow stream along the conduits
        trail_dots = VGroup(*[Dot(radius=0.06, color=C_HIGHLIGHT) for _ in range(4)])
        self.play(
            LaggedStart(*[
                MoveAlongPath(dot, arr, rate_func=linear)
                for dot, arr in zip(trail_dots, connecting_arrows)
            ], lag_ratio=0.25),
            run_time=2.2
        )
        self.remove(trail_dots)
        
        self.wait(1.96)

        # -------------------------------------------------------------------------
        ## Presentation Step 2: Agent Diversity & Architectural Matching
        # Step Duration: 21.236s
        # -------------------------------------------------------------------------
        step2_title = create_title(
            "Agent Diversity & Architectures",
            "Matching Architecture to Task Complexity"
        )
        
        # Clean sequential title transition & dim step 1 baseline
        self.play(FadeOut(step1_title), run_time=0.3)
        self.play(
            FadeIn(step2_title, shift=DOWN * 0.10),
            solara_emblem.animate.set_opacity(0.60),
            flow_cards.animate.set_opacity(0.60),
            connecting_arrows.animate.set_opacity(0.60),
            run_time=0.5
        )

        # 2.1 Central Problem Sphere
        problem_center = np.array([2.8, -0.8, 0])
        problem_outer = Circle(radius=1.0, stroke_color=C_STEEL, stroke_width=1.8, stroke_opacity=0.6)
        problem_dashed = DashedVMobject(Circle(radius=0.85, stroke_color=C_AMBER, stroke_width=2.0), num_dashes=20)
        problem_core = Circle(radius=0.65, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=C_TITLE, stroke_width=1.8)

        prob_tag = CrispText("Task Space", size=13, weight="BOLD", color=C_TITLE).move_to(problem_center + UP * 0.10)
        prob_desc = CrispText("Solara Thermal Anomaly", size=9, weight="NORMAL", color=C_MUTED).next_to(prob_tag, DOWN, buff=0.06)
        problem_sphere = VGroup(problem_outer, problem_dashed, problem_core, prob_tag, prob_desc).move_to(problem_center)

        # 2.2 Three Distinct Open Vector Agent Nodes
        gear_outer = Circle(radius=0.25, stroke_color=C_SKY, stroke_width=2)
        gear_teeth = VGroup(*[
            Line(
                gear_outer.point_at_angle(a),
                gear_outer.point_at_angle(a) + 0.07 * np.array([np.cos(a), np.sin(a), 0]),
                stroke_color=C_SKY, stroke_width=2.5
            )
            for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)
        ])
        gear_icon = VGroup(gear_outer, gear_teeth)

        compass_ring = Circle(radius=0.25, stroke_color=C_AMBER, stroke_width=2)
        compass_needle = Polygon([0, 0.20, 0], [0.05, 0, 0], [0, -0.20, 0], [-0.05, 0, 0], fill_color=C_AMBER, fill_opacity=0.85, stroke_width=0)
        compass_icon = VGroup(compass_ring, compass_needle)

        prism_body = Polygon([0, 0.25, 0], [0.22, -0.14, 0], [-0.22, -0.14, 0], stroke_color=C_LAVENDER, stroke_width=2, fill_color=C_LAVENDER, fill_opacity=0.3)
        prism_line = Line([0, 0.25, 0], [0, -0.14, 0], stroke_color=C_LAVENDER, stroke_width=1.5)
        prism_icon = VGroup(prism_body, prism_line)

        agent_configs = [
            ("Reactive Agent", "Fixed Condition-Action Rules", gear_icon, C_SKY, [-0.2, -0.8, 0]),
            ("Deliberative Agent", "Internal World Model & Planning", compass_icon, C_AMBER, [2.8, 0.8, 0]),
            ("Utility Optimizer", "Multi-Objective Trade-off Engine", prism_icon, C_LAVENDER, [5.8, -0.8, 0]),
        ]

        agent_nodes = VGroup()
        connecting_conduits = VGroup()

        for name, sub, icon_m, col, pos in agent_configs:
            badge = create_badge(icon_m, bg_color=col, radius=0.32).move_to(pos)

            a_title = CrispText(name, size=12, weight="BOLD", color=C_TITLE).next_to(badge, DOWN, buff=0.10)
            a_sub = CrispText(sub, size=9, weight="NORMAL", color=C_BODY).next_to(a_title, DOWN, buff=0.05)

            agent_m = VGroup(badge, a_title, a_sub)
            agent_nodes.add(agent_m)

            conduit = CurvedArrow(
                start_point=np.array(pos) + (problem_center - np.array(pos)) * 0.28,
                end_point=problem_center + (np.array(pos) - problem_center) * 0.38,
                angle=0.16 if pos[0] >= 2.8 else -0.16,
                color=col, stroke_width=2.2
            )
            connecting_conduits.add(conduit)

        # Reveal Step 2 elements
        self.play(GrowFromCenter(problem_sphere), run_time=1.2)

        for i in range(3):
            self.play(
                FadeIn(agent_nodes[i], shift=UP * 0.12),
                Create(connecting_conduits[i]),
                run_time=0.9
            )

        shift_ring = Circle(radius=0.75, stroke_color=C_HIGHLIGHT, stroke_width=2.5).move_to(problem_center)
        self.play(
            problem_dashed.animate.rotate(np.pi / 2),
            Create(shift_ring),
            run_time=1.2
        )
        self.play(FadeOut(shift_ring), run_time=0.4)

        # Highlight optimal match on Utility Optimizer (Agent 3)
        matched_conduit = connecting_conduits[2]
        match_pulse = matched_conduit.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=4.5)

        match_badge = RoundedRectangle(width=1.35, height=0.28, corner_radius=0.06, fill_color=C_HIGHLIGHT, fill_opacity=1.0, stroke_width=0)
        match_txt = CrispText("Optimal Match", size=9, weight="BOLD", color="#FFFFFF").move_to(match_badge)
        match_flag = VGroup(match_badge, match_txt).next_to(agent_nodes[2], UP, buff=0.10)

        packets = VGroup(*[Dot(radius=0.06, color=C_HIGHLIGHT) for _ in range(3)])
        self.play(
            Create(match_pulse),
            FadeIn(match_flag, shift=DOWN * 0.08),
            run_time=1.1
        )
        self.play(
            LaggedStart(*[
                MoveAlongPath(p, matched_conduit) for p in packets
            ], lag_ratio=0.3),
            run_time=2.2
        )
        self.remove(packets)

        step2_all = VGroup(problem_sphere, agent_nodes, connecting_conduits, match_pulse, match_flag)

        self.wait(11.636)

        # -------------------------------------------------------------------------
        ## Presentation Step 3: Core Learning Outcomes & Synthesis
        # Step Duration: 39.206s
        # -------------------------------------------------------------------------
        step3_title = create_title(
            "Learning Outcomes",
            "Core Architectural Competencies & Real-World Objectives"
        )
        
        # Clean title transition & explicit lifecycle purge of previous step visual clutter
        self.play(FadeOut(step2_title), run_time=0.3)
        self.play(
            FadeIn(step3_title, shift=DOWN * 0.10),
            FadeOut(solara_emblem),
            FadeOut(flow_cards),
            FadeOut(connecting_arrows),
            FadeOut(step2_all),
            run_time=0.7
        )
        self.remove(solara_emblem, flow_cards, connecting_arrows, step2_all)

        # 3.1 Five Vector Learning Outcome Rows
        def make_triad_blocks():
            b1 = Square(side_length=0.11, fill_color=C_SKY, fill_opacity=0.9, stroke_width=0).move_to([-0.06, -0.05, 0])
            b2 = Square(side_length=0.11, fill_color=C_SKY, fill_opacity=0.9, stroke_width=0).move_to([0.06, -0.05, 0])
            b3 = Square(side_length=0.11, fill_color=C_SKY, fill_opacity=0.9, stroke_width=0).move_to([0, 0.07, 0])
            return VGroup(b1, b2, b3)

        def make_loop_icon():
            arc1 = Arc(radius=0.13, start_angle=0, angle=1.6 * np.pi, stroke_color=C_STEEL, stroke_width=2)
            tip = ArrowTriangleTip(color=C_STEEL).scale(0.11).move_to(arc1.get_end())
            return VGroup(arc1, tip)

        def make_matrix_icon():
            d1 = Dot(radius=0.035, color=C_LAVENDER).move_to([-0.09, 0.07, 0])
            d2 = Dot(radius=0.035, color=C_LAVENDER).move_to([0.09, 0.07, 0])
            d3 = Dot(radius=0.035, color=C_LAVENDER).move_to([0, -0.07, 0])
            l1 = Line(d1.get_center(), d2.get_center(), stroke_color=C_LAVENDER, stroke_width=1.2)
            l2 = Line(d1.get_center(), d3.get_center(), stroke_color=C_LAVENDER, stroke_width=1.2)
            l3 = Line(d2.get_center(), d3.get_center(), stroke_color=C_LAVENDER, stroke_width=1.2)
            return VGroup(l1, l2, l3, d1, d2, d3)

        def make_shapes_triad():
            c = Circle(radius=0.065, stroke_color=C_AMBER, stroke_width=1.5).move_to([-0.11, 0, 0])
            t = Triangle(stroke_color=C_AMBER, stroke_width=1.5).scale(0.075).move_to([0, 0, 0])
            s = Square(side_length=0.11, stroke_color=C_AMBER, stroke_width=1.5).move_to([0.11, 0, 0])
            return VGroup(c, t, s)

        def make_streamline_icon():
            line = Line([-0.15, 0, 0], [0.15, 0, 0], stroke_color=C_MINT, stroke_width=2)
            p1 = Dot(radius=0.03, color=C_MINT).move_to([-0.09, 0, 0])
            p2 = Dot(radius=0.03, color=C_MINT).move_to([0, 0, 0])
            p3 = Dot(radius=0.03, color=C_MINT).move_to([0.09, 0, 0])
            return VGroup(line, p1, p2, p3)

        outcomes_data = [
            ("Core Agent Components", "Sensors, internal state memory & cognitive actuators", make_triad_blocks(), C_SKY),
            ("Closed Feedback Loop", "Continuous perception, action & environment dynamics", make_loop_icon(), C_STEEL),
            ("Perception-Action Cycle", "Sequential runtime deliberation & decision gating", make_matrix_icon(), C_LAVENDER),
            ("Three Agent Archetypes", "Reactive, deliberative & utility-driven models", make_shapes_triad(), C_AMBER),
            ("Operational Workflows", "End-to-end execution from stimulus to verified outcome", make_streamline_icon(), C_MINT),
        ]

        outcome_cards = VGroup()
        y_positions = [0.8, 0.0, -0.8, -1.6, -2.4]

        for idx, (head_t, body_t, icon_mob, theme_c) in enumerate(outcomes_data):
            row_y = y_positions[idx]

            num_lbl = CrispText(f"0{idx+1}", size=11, weight="BOLD", color=theme_c).move_to([1.8, row_y + 0.12, 0])
            icon_b = create_badge(icon_mob, bg_color=theme_c, radius=0.20).move_to([1.8, row_y - 0.14, 0])
            icon_grp = VGroup(num_lbl, icon_b)

            head_lbl = CrispText(head_t, size=13, weight="BOLD", color=C_TITLE)
            head_lbl.move_to([2.4 + head_lbl.width / 2.0, row_y + 0.12, 0])

            body_lbl = CrispText(body_t, size=10, weight="NORMAL", color=C_BODY, max_width=3.4)
            body_lbl.move_to([2.4 + body_lbl.width / 2.0, row_y - 0.14, 0])

            # Pure vector checkmark shape
            chk_stem = Line([-0.05, 0.0, 0], [-0.01, -0.04, 0], stroke_color=theme_c, stroke_width=2.0)
            chk_tail = Line([-0.01, -0.04, 0], [0.06, 0.04, 0], stroke_color=theme_c, stroke_width=2.0)
            chk_disc = Circle(radius=0.15, fill_color=theme_c, fill_opacity=0.15, stroke_color=theme_c, stroke_width=1.2)
            check_icon = VGroup(chk_disc, chk_stem, chk_tail).move_to([6.1, row_y, 0])

            baseline = Line([1.6, row_y - 0.36, 0], [6.3, row_y - 0.36, 0], stroke_color="#E2E8F0", stroke_width=1)

            full_row = VGroup(icon_grp, head_lbl, body_lbl, check_icon, baseline)
            outcome_cards.add(full_row)

        # 3.2 Progressive Reveal Loop
        for i, card in enumerate(outcome_cards):
            self.play(FadeIn(card, shift=RIGHT * 0.18), run_time=0.85)

            pulse_line = Line([1.6, y_positions[i] - 0.36, 0], [6.3, y_positions[i] - 0.36, 0], stroke_color=C_HIGHLIGHT, stroke_width=2.8)
            self.play(Create(pulse_line), run_time=0.55)
            self.play(FadeOut(pulse_line), run_time=0.45)

            self.wait(5.5)

        self.wait(1.456)