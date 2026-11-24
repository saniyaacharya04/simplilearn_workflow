C_DARK_BLUE = "#1E293B"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
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
import manim.utils.rate_functions as rate_functions

# Global Color Palette - 10-Color Infographic Slate Compliance
C_SLATE_TITLE = "#0F172A"
C_SUBTITLE = "#475569"
C_CHARCOAL = "#404040"
C_CARD_BG = "#FFFFFF"
C_BORDER = "#CBD5E1"
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_LAVENDER = "#9B99C7"
C_AMBER = "#E6A157"
C_CORAL = "#E58F6D"
C_ALERT_RED = "#E05252"
C_FOCUS = "#F78908"
C_BRAND_BLUE = "#2C81FE"
C_WHITE = "#FFFFFF"

SME_LAYOUT = '20'

try:
    from feedback_functions_vlm.instrumented_scene import InstrumentedScene
except Exception:
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
class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        # 1. Canvas Background Setup (Pure White Canvas)
        self.camera.background_color = C_WHITE
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














        self.camera.frame.save_state()

        # =========================================================================
        # PRESENTATION STEP 1: Monitoring Grid Performance (Target: 58.855s)
        # =========================================================================
        ## Presentation Step 1

        title_group = create_title(
            "Agent-Environment Interaction Loop",
            "Real-Time Monitoring: Perception, Decision, and Actuation"
        )
        self.play(FadeIn(title_group, shift=DOWN * 0.1), run_time=1.0)

        # ---------------------------------------------------------
        # Procedural Graphic: Solara Site (Solar Photovoltaic Array)
        # ---------------------------------------------------------
        site_center = np.array([-4.6, -0.5, 0])
        site_base = RoundedRectangle(
            width=2.4, height=2.8, corner_radius=0.15,
            fill_color=C_CARD_BG, fill_opacity=0.95,
            stroke_color=C_STEEL_BLUE, stroke_width=2
        ).move_to(site_center)

        site_label = CrispText("Solara Site", size=14, weight=BOLD, color=C_SLATE_TITLE)
        site_label.next_to(site_base.get_top(), DOWN, buff=0.2)

        panels = VGroup()
        for row in range(2):
            for col in range(2):
                p = Polygon(
                    [-0.42, -0.24, 0], [0.42, -0.24, 0],
                    [0.32, 0.24, 0], [-0.32, 0.24, 0],
                    fill_color="#2B6CB0", fill_opacity=0.85,
                    stroke_color="#93C5FD", stroke_width=1.5
                ).shift(site_center + np.array([(col - 0.5) * 0.95, (0.5 - row) * 0.7 - 0.25, 0]))
                h_line = Line(p.get_left(), p.get_right(), stroke_color="#93C5FD", stroke_width=1)
                v_line = Line(p.get_bottom(), p.get_top(), stroke_color="#93C5FD", stroke_width=1)
                panels.add(p, h_line, v_line)

        site_group = VGroup(site_base, site_label, panels)

        self.play(
            FadeIn(site_base, shift=UP * 0.2),
            Write(site_label),
            LaggedStart(*[FadeIn(p, scale=0.8) for p in panels], lag_ratio=0.08),
            run_time=3.0
        )

        # ---------------------------------------------------------
        # Procedural Graphic: Performance Gauge (Shifted RIGHT by 1.0)
        # ---------------------------------------------------------
        gauge_center = np.array([-0.8, -0.5, 0])
        gauge_rim = Arc(
            radius=1.05, start_angle=-PI / 4, angle=1.5 * PI,
            stroke_color=C_BORDER, stroke_width=7
        ).move_to(gauge_center)

        gauge_safe = Arc(
            radius=1.05, start_angle=PI / 4, angle=PI,
            stroke_color=C_SKY_BLUE, stroke_width=7
        ).move_to(gauge_center)

        gauge_alert_band = Arc(
            radius=1.05, start_angle=-PI / 4, angle=PI / 2,
            stroke_color=C_ALERT_RED, stroke_width=7
        ).move_to(gauge_center)

        threshold_angle = PI / 4
        thresh_pos = gauge_center + 1.05 * np.array([np.cos(threshold_angle), np.sin(threshold_angle), 0])
        thresh_line = Line(
            thresh_pos - 0.16 * np.array([np.cos(threshold_angle), np.sin(threshold_angle), 0]),
            thresh_pos + 0.16 * np.array([np.cos(threshold_angle), np.sin(threshold_angle), 0]),
            stroke_color=C_FOCUS, stroke_width=3.5
        )
        thresh_tag = CrispText("Threshold", size=11, weight=BOLD, color=C_FOCUS)
        thresh_tag.next_to(thresh_pos, UR, buff=0.12).shift(UP * 0.1 + RIGHT * 0.1)

        needle_angle = ValueTracker(PI * 0.75)
        needle_pivot = Dot(gauge_center, radius=0.08, color=C_SLATE_TITLE)

        def get_needle():
            ang = needle_angle.get_value()
            tip = gauge_center + 0.85 * np.array([np.cos(ang), np.sin(ang), 0])
            return Line(gauge_center, tip, stroke_color=C_SLATE_TITLE, stroke_width=3.5)

        needle = always_redraw(get_needle)

        gauge_label = CrispText("Performance Gauge", size=13, weight=BOLD, color=C_SLATE_TITLE)
        gauge_label.next_to(gauge_rim, DOWN, buff=0.35)

        conduit_1 = Line(site_base.get_right(), gauge_center + LEFT * 1.15, stroke_color=C_STEEL_BLUE, stroke_width=2)

        self.play(
            Create(conduit_1),
            Create(gauge_rim),
            Create(gauge_safe),
            Create(gauge_alert_band),
            Create(thresh_line),
            FadeIn(thresh_tag),
            FadeIn(needle_pivot),
            FadeIn(needle),
            Write(gauge_label),
            run_time=3.0
        )
        self.wait(2.0)

        # Telemetry packet flow
        stream_dot = Dot(site_base.get_right(), radius=0.07, color=C_SKY_BLUE)
        self.play(MoveAlongPath(stream_dot, conduit_1, rate_func=rate_functions.ease_out_cubic), run_time=1.5)
        self.remove(stream_dot)

        # ---------------------------------------------------------
        # Needle Drops Below Threshold -> Alert Shockwave
        # ---------------------------------------------------------
        alert_pulse = Circle(radius=1.1, stroke_color=C_ALERT_RED, stroke_width=3.5, fill_opacity=0).move_to(gauge_center)
        alert_badge = RoundedRectangle(
            width=1.5, height=0.42, corner_radius=0.08,
            fill_color=C_ALERT_RED, fill_opacity=0.95,
            stroke_color=C_WHITE, stroke_width=1
        ).next_to(gauge_label, DOWN, buff=0.15)
        alert_text = CrispText("Output Drop", size=11, weight=BOLD, color=C_WHITE).move_to(alert_badge.get_center())

        self.play(
            needle_angle.animate.set_value(0.0),
            run_time=2.5,
            rate_func=rate_functions.ease_in_out_sine
        )
        self.play(
            Create(alert_pulse),
            alert_pulse.animate.scale(1.3).set_stroke(opacity=0),
            FadeIn(alert_badge),
            FadeIn(alert_text),
            run_time=1.8
        )
        self.remove(alert_pulse)

        # ---------------------------------------------------------
        # Monitoring Agent Core (AI Perception Hub)
        # ---------------------------------------------------------
        agent_center = np.array([1.4, -0.5, 0])
        agent_outer_ring = Circle(radius=0.9, stroke_color=C_SKY_BLUE, stroke_width=2.5, fill_color=C_CARD_BG, fill_opacity=0.95).move_to(agent_center)
        agent_inner_core = Circle(radius=0.55, stroke_color=C_AMBER, stroke_width=2, fill_color="#FEF3C7", fill_opacity=0.5).move_to(agent_center)

        halo_lines = VGroup(*[
            Line(
                agent_center + 0.6 * np.array([np.cos(a), np.sin(a), 0]),
                agent_center + 0.82 * np.array([np.cos(a), np.sin(a), 0]),
                stroke_color=C_SKY_BLUE, stroke_width=1.5
            ) for a in np.linspace(0, 2 * PI, 12, endpoint=False)
        ])
        halo_lines.add_updater(lambda m, dt: m.rotate(0.25 * dt, about_point=agent_center))

        agent_title = CrispText("Monitoring Agent", size=14, weight=BOLD, color=C_SLATE_TITLE).next_to(agent_outer_ring, UP, buff=0.18)
        agent_sub = CrispText("Autonomous AI Core", size=11, color=C_SUBTITLE).next_to(agent_title, DOWN, buff=0.08)

        # Perception Transmission Arrow & Pill (Shifted Right by 0.5, Z-indexed properly)
        perception_arrow = Arrow(
            gauge_center + RIGHT * 1.1,
            agent_outer_ring.get_left(),
            buff=0.1, stroke_width=3, color=C_FOCUS, max_tip_length_to_length_ratio=0.2
        ).set_z_index(12)

        perception_pill = RoundedRectangle(
            width=1.5, height=0.38, corner_radius=0.07,
            fill_color=C_CARD_BG, fill_opacity=1.0,
            stroke_color=C_FOCUS, stroke_width=1.5
        ).move_to(perception_arrow.get_center()).set_z_index(13)

        perception_text = CrispText("Perception", size=11, weight=BOLD, color=C_FOCUS).move_to(perception_pill).set_z_index(14)

        self.play(
            GrowFromCenter(agent_outer_ring),
            GrowFromCenter(agent_inner_core),
            FadeIn(halo_lines),
            Write(agent_title),
            FadeIn(agent_sub),
            GrowArrow(perception_arrow),
            FadeIn(perception_pill),
            Write(perception_text),
            run_time=3.5
        )
        self.wait(3.0)

        # ---------------------------------------------------------
        # Decision Tree Sprouting from Agent Core (Shifted RIGHT by 0.8)
        # ---------------------------------------------------------
        tree_origin = agent_center + RIGHT * 0.9
        branch_targets = [
            np.array([4.3, 0.9, 0]),
            np.array([4.3, -0.5, 0]),
            np.array([4.3, -1.9, 0])
        ]
        branch_labels_text = [
            "Query Data",
            "Cross-Ref Weather",
            "Escalate Human"
        ]

        branches = VGroup()
        branch_cards = VGroup()

        for idx, (target, label_text) in enumerate(zip(branch_targets, branch_labels_text)):
            branch_line = CubicBezier(
                tree_origin,
                tree_origin + RIGHT * 0.8,
                target + LEFT * 0.8,
                target,
                stroke_color=C_BORDER, stroke_width=2.5
            )
            branches.add(branch_line)

            pill = RoundedRectangle(
                width=2.4, height=0.55, corner_radius=0.1,
                fill_color=C_CARD_BG, fill_opacity=0.95,
                stroke_color=C_BORDER, stroke_width=1.5
            ).move_to(target)

            dot_marker = Dot(pill.get_left() + RIGHT * 0.25, radius=0.07, color=C_STEEL_BLUE)
            txt = CrispText(label_text, size=12, weight=SEMIBOLD, color=C_CHARCOAL)
            txt.next_to(dot_marker, RIGHT, buff=0.15)
            branch_cards.add(VGroup(pill, dot_marker, txt))

        self.play(
            LaggedStart(*[Create(b) for b in branches], lag_ratio=0.25),
            LaggedStart(*[FadeIn(c, shift=RIGHT * 0.2) for c in branch_cards], lag_ratio=0.25),
            run_time=4.0
        )
        self.wait(4.0)

        # ---------------------------------------------------------
        # Actuation Choice: Escalate Human Path Glows
        # ---------------------------------------------------------
        escalate_branch = branches[2]
        escalate_card = branch_cards[2]

        operator_pos = np.array([4.3, -2.9, 0])
        op_head = Circle(radius=0.16, fill_color=C_CORAL, fill_opacity=0.9, stroke_color=C_CHARCOAL, stroke_width=1.5).move_to(operator_pos + UP * 0.2)
        op_body = Arc(radius=0.28, start_angle=0, angle=PI, stroke_color=C_CHARCOAL, stroke_width=1.5, fill_color=C_CORAL, fill_opacity=0.9).move_to(operator_pos - UP * 0.08)
        op_console = RoundedRectangle(width=1.2, height=0.32, corner_radius=0.06, fill_color=C_CHARCOAL, fill_opacity=0.85, stroke_width=0).next_to(op_body, DOWN, buff=0.06)
        op_label = CrispText("Human Operator", size=10, weight=BOLD, color=C_WHITE).move_to(op_console.get_center())
        op_group = VGroup(op_head, op_body, op_console, op_label)

        action_arrow = Arrow(
            escalate_card.get_bottom(),
            op_group.get_top(),
            stroke_color=C_FOCUS, stroke_width=3, buff=0.08, max_tip_length_to_length_ratio=0.22
        )

        focus_highlight_box = escalate_card[0].copy().set_fill(opacity=0).set_stroke(color=C_FOCUS, width=3.5)

        self.play(
            escalate_branch.animate.set_stroke(color=C_FOCUS, width=4.0),
            Create(focus_highlight_box),
            escalate_card[1].animate.set_color(C_FOCUS),
            run_time=2.0
        )
        self.play(
            GrowArrow(action_arrow),
            FadeIn(op_group, shift=UP * 0.15),
            run_time=2.0
        )

        action_packet = Dot(escalate_card.get_bottom(), radius=0.08, color=C_FOCUS)
        self.play(
            MoveAlongPath(action_packet, action_arrow, rate_func=rate_functions.ease_out_cubic),
            run_time=1.5
        )
        self.remove(action_packet)

        dispatched_pill = RoundedRectangle(
            width=1.8, height=0.42, corner_radius=0.08,
            fill_color="#FEF3C7", fill_opacity=0.95,
            stroke_color=C_FOCUS, stroke_width=1.5
        ).next_to(agent_inner_core, DOWN, buff=0.45)
        dispatched_txt = CrispText("Action Executed", size=11, weight=BOLD, color=C_FOCUS).move_to(dispatched_pill)

        self.play(FadeIn(dispatched_pill), Write(dispatched_txt), run_time=1.5)
        
        # Exact step 1 time budget completion (Total step 1 = 58.855s)
        self.wait(22.555)

        # =========================================================================
        # PRESENTATION STEP 2: Bi-Directional Relationship (Target: 36.645s)
        # =========================================================================
        ## Presentation Step 2

        step2_title_group = create_title(
            "Agent-Environment Interaction Loop",
            "Bi-Directional Dynamics: Continuous Reciprocal Influence"
        )

        halo_lines.clear_updaters()

        self.play(
            ReplacementTransform(title_group, step2_title_group),
            FadeOut(conduit_1),
            FadeOut(gauge_rim),
            FadeOut(gauge_safe),
            FadeOut(gauge_alert_band),
            FadeOut(thresh_line),
            FadeOut(thresh_tag),
            FadeOut(needle_pivot),
            FadeOut(needle),
            FadeOut(gauge_label),
            FadeOut(alert_badge),
            FadeOut(alert_text),
            FadeOut(perception_arrow),
            FadeOut(perception_pill),
            FadeOut(perception_text),
            FadeOut(branches),
            FadeOut(branch_cards),
            FadeOut(focus_highlight_box),
            FadeOut(action_arrow),
            FadeOut(op_group),
            FadeOut(dispatched_pill),
            FadeOut(dispatched_txt),
            run_time=2.5
        )

        # Reposition Environment (Shift LEFT by 0.5) & Agent (Shift RIGHT by 0.5)
        env_target_pos = np.array([-4.1, -0.5, 0])
        agent_target_pos = np.array([2.9, -0.5, 0])

        self.play(
            site_group.animate.move_to(env_target_pos),
            agent_outer_ring.animate.move_to(agent_target_pos),
            agent_inner_core.animate.move_to(agent_target_pos),
            halo_lines.animate.move_to(agent_target_pos),
            agent_title.animate.next_to(agent_outer_ring.move_to(agent_target_pos), UP, buff=0.25),
            agent_sub.animate.next_to(agent_title, DOWN, buff=0.08),
            run_time=2.5
        )

        halo_lines.add_updater(lambda m, dt: m.rotate(0.3 * dt, about_point=agent_target_pos))

        env_badge = RoundedRectangle(
            width=3.2, height=0.65, corner_radius=0.1,
            fill_color=C_CARD_BG, fill_opacity=1.0,
            stroke_color=C_STEEL_BLUE, stroke_width=2
        ).next_to(site_base, DOWN, buff=0.45)
        env_text = CrispText("Environment (Grid System)", size=12, weight=BOLD, color=C_SLATE_TITLE).move_to(env_badge)

        agent_badge = RoundedRectangle(
            width=2.6, height=0.65, corner_radius=0.1,
            fill_color=C_CARD_BG, fill_opacity=1.0,
            stroke_color=C_SKY_BLUE, stroke_width=2
        ).next_to(agent_outer_ring, DOWN, buff=0.45)
        agent_badge_text = CrispText("Agent (Reasoning Core)", size=12, weight=BOLD, color=C_SLATE_TITLE).move_to(agent_badge)

        self.play(
            FadeIn(env_badge),
            Write(env_text),
            FadeIn(agent_badge),
            Write(agent_badge_text),
            run_time=2.0
        )

        # ---------------------------------------------------------
        # Bi-Directional Kinetic Conduits
        # ---------------------------------------------------------
        top_arc = CurvedArrow(
            env_target_pos + UP * 1.5 + RIGHT * 0.8,
            agent_target_pos + UP * 1.5 + LEFT * 0.8,
            angle=-0.42,
            color=C_SKY_BLUE,
            stroke_width=4.5
        )

        top_tag = RoundedRectangle(
            width=2.4, height=0.6, corner_radius=0.08,
            fill_color=C_CARD_BG, fill_opacity=1.0,
            stroke_color=C_SKY_BLUE, stroke_width=2
        ).move_to(top_arc.point_from_proportion(0.5) + UP * 0.35)
        top_txt = CrispText("Shapes Agent", size=13, weight=BOLD, color=C_SLATE_TITLE).move_to(top_tag)
        top_sub = CrispText("Telemetry, Constraints, Shifts", size=10, color=C_SUBTITLE).next_to(top_tag, UP, buff=0.06)

        bottom_arc = CurvedArrow(
            agent_target_pos + DOWN * 1.5 + LEFT * 0.8,
            env_target_pos + DOWN * 1.5 + RIGHT * 0.8,
            angle=-0.42,
            color=C_AMBER,
            stroke_width=4.5
        )

        bottom_tag = RoundedRectangle(
            width=2.6, height=0.6, corner_radius=0.08,
            fill_color=C_CARD_BG, fill_opacity=1.0,
            stroke_color=C_AMBER, stroke_width=2
        ).move_to(bottom_arc.point_from_proportion(0.5) + DOWN * 0.35)
        bottom_txt = CrispText("Shapes Environment", size=13, weight=BOLD, color=C_SLATE_TITLE).move_to(bottom_tag)
        bottom_sub = CrispText("Dispatches, Mitigations, State Changes", size=10, color=C_SUBTITLE).next_to(bottom_tag, DOWN, buff=0.06)

        # Central Cognitive Anchor: "Bi-Directional"
        center_focal_pos = np.array([-0.6, -0.5, 0])
        center_pill = RoundedRectangle(
            width=2.5, height=0.65, corner_radius=0.12,
            fill_color="#F8FAFC", fill_opacity=1.0,
            stroke_color=C_FOCUS, stroke_width=2.5
        ).move_to(center_focal_pos)
        center_title = CrispText("Bi-Directional", size=14, weight=BOLD, color=C_SLATE_TITLE).move_to(center_pill.get_center() + UP * 0.08)
        center_sub = CrispText("Dynamic Closed Loop", size=10, weight=SEMIBOLD, color=C_FOCUS).next_to(center_title, DOWN, buff=0.05)
        center_focal_grp = VGroup(center_pill, center_title, center_sub)

        self.play(
            Create(top_arc),
            FadeIn(top_tag),
            Write(top_txt),
            FadeIn(top_sub),
            run_time=2.5
        )
        self.play(
            Create(bottom_arc),
            FadeIn(bottom_tag),
            Write(bottom_txt),
            FadeIn(bottom_sub),
            run_time=2.5
        )
        self.play(
            GrowFromCenter(center_focal_grp),
            run_time=2.0
        )

        # ---------------------------------------------------------
        # Orbital Micro-Ring around Agent Core
        # ---------------------------------------------------------
        pra_radius = 1.35
        pra_colors = [C_SKY_BLUE, C_AMBER, C_CORAL]
        pra_labels = ["Perception", "Reasoning", "Action"]
        pra_angles = [PI / 2, 11 * PI / 6, 7 * PI / 6]

        pra_group = VGroup()
        for ang, col, lbl in zip(pra_angles, pra_colors, pra_labels):
            pos = agent_target_pos + pra_radius * np.array([np.cos(ang), np.sin(ang), 0])
            node = Dot(pos, radius=0.12, color=col)
            node_tag = CrispText(lbl, size=11, weight=BOLD, color=C_SLATE_TITLE).next_to(
                pos, np.array([np.cos(ang), np.sin(ang), 0]), buff=0.18
            )
            pra_group.add(node, node_tag)

        pra_orbit = Circle(radius=pra_radius, stroke_color=C_BORDER, stroke_width=1.5, stroke_opacity=0.6).move_to(agent_target_pos)

        self.play(
            Create(pra_orbit),
            LaggedStart(*[FadeIn(p) for p in pra_group], lag_ratio=0.2),
            run_time=2.5
        )

        # ---------------------------------------------------------
        # Synchronized Circulation Packets
        # ---------------------------------------------------------
        data_packet = Dot(radius=0.1, color=C_SKY_BLUE)
        act_packet = Dot(radius=0.1, color=C_AMBER)
        center_glow = center_pill.copy().set_fill(opacity=0).set_stroke(color=C_FOCUS, width=4)

        for _ in range(2):
            self.play(
                MoveAlongPath(data_packet, top_arc, rate_func=rate_functions.ease_out_cubic),
                MoveAlongPath(act_packet, bottom_arc, rate_func=rate_functions.ease_out_cubic),
                Create(center_glow),
                run_time=2.5
            )
            self.play(
                FadeOut(center_glow),
                run_time=0.8
            )

        self.remove(data_packet, act_packet)
        halo_lines.clear_updaters()

        # Exact step 2 time budget completion (Total step 2 = 36.645s)
        self.wait(11.545)