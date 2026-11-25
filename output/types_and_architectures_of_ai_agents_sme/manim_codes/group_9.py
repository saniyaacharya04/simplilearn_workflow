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
import os
import re
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
import numpy as np

# Safe fallback for CrispText and InstrumentedScene
try:
    CrispText
except NameError:






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
try:
    InstrumentedScene
except NameError:
    class InstrumentedScene(Scene):
        def sync_to(self, t):
            pass



class FinalScene(InstrumentedScene, MovingCameraScene):
    
    def sync_to(self, target_time):
        curr_t = getattr(self.renderer, 'time', 0)
        if target_time > curr_t:
            self.wait(target_time - curr_t)

    def construct(self):
        # 1. Canvas Theme & Background
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

















        # Color Palette constants (strictly compliant with 10-pastel palette & slate text)
        C_BG = "#F0F4F8"
        C_CARD_BG = "#FFFFFF"
        C_TITLE = "#0F172A"
        C_SUBTITLE = "#475569"
        C_TEXT = "#334155"
        C_DARK_CHARCOAL = "#404040"
        C_BORDER = "#CBD5E1"
        C_HIGHLIGHT = "#F78908"

        # 10-color infographic pastels
        C_SKY = "#62B7E4"
        C_STEEL = "#7EA2C8"
        C_LAVENDER = "#9B99C7"
        C_MINT = "#8ECDB7"
        C_AMBER = "#E6A157"
        C_CORAL = "#E58F6D"
        C_LILAC = "#C1A5C6"
        C_MUSTARD = "#DDB945"

        # Layout 70 parameters (Safe Content Workspace: x ∈ [-0.80, 6.40], Center x ≈ 2.80)
        X_CENTER_SME_LAYOUT_70 = 2.80 # Renamed from ORIGIN to avoid shadowing manim.ORIGIN
        TOP_CEILING = 2.15

        # =========================================================================
        ## Presentation Step 1: Key Takeaways
        # =========================================================================
        # Narration: "Let's bring it together. Every agent is built from four components...
        # ...working together in a continuous loop... observes, decides, acts...
        # ...three types of agents: reactive, goal-based, and utility-based..."
        step1_start = 0.0
        step1_duration = 82.845

        # Slide Title Header
        title_group = create_title("Handoff, Summary & What's Next", "Key Takeaways: Agent Architecture & Interaction")
        self.play(FadeIn(title_group, shift=DOWN * 0.15), run_time=1.0)

        # Main dynamic summary canvas container (Right 60% safe area)
        panel_w = 6.90
        panel_h = 5.25
        summary_panel = RoundedRectangle(
            corner_radius=0.15,
            width=panel_w,
            height=panel_h,
            fill_color=C_CARD_BG,
            fill_opacity=0.96,
            stroke_color=C_BORDER,
            stroke_width=1.5
        ).move_to(np.array([X_CENTER_SME_LAYOUT_70, -0.55, 0]))

        # Sub-header bar for Summary Panel
        panel_tag = RoundedRectangle(
            corner_radius=0.074,
            width=2.4,
            height=0.38,
            fill_color=C_SKY,
            fill_opacity=0.18,
            stroke_color=C_SKY,
            stroke_width=1.2
        ).move_to(np.array([X_CENTER_SME_LAYOUT_70 - 2.0, 2.05, 0]))
        panel_tag_lbl = CrispText("Architecture Summary", size=12, weight=BOLD, color=C_TITLE).move_to(panel_tag)

        self.play(
            FadeIn(summary_panel, shift=UP * 0.1),
            FadeIn(panel_tag),
            FadeIn(panel_tag_lbl),
            run_time=1.2
        )

        # -------------------------------------------------------------------------
        # Section 1: Components (Mini-loop of Perception, Memory, Reasoning, Action)
        # -------------------------------------------------------------------------
        sec1_header = CrispText("1. Core Components", size=14, weight=BOLD, color=C_TITLE)
        sec1_header.move_to(np.array([X_CENTER_SME_LAYOUT_70 - 1.80, 1.55, 0]))

        # 4 Nodes in a circular coordinate arrangement
        comp_center = np.array([X_CENTER_SME_LAYOUT_70 - 1.80, 0.50, 0])
        radius = 0.65
        node_configs = [
            ("Perception", C_SKY, UP * radius),
            ("Reasoning", C_AMBER, RIGHT * radius),
            ("Action", C_CORAL, DOWN * radius),
            ("Memory", C_LAVENDER, LEFT * radius),
        ]

        comp_nodes = VGroup()
        comp_labels = VGroup()
        for label, color, offset in node_configs:
            pos = comp_center + offset
            pill = RoundedRectangle(
                corner_radius=0.07, width=1.25, height=0.34,
                fill_color=C_BG, fill_opacity=1.0, stroke_color=color, stroke_width=1.8
            ).move_to(pos)
            txt = CrispText(label, size=10, weight=BOLD, color=C_DARK_CHARCOAL).move_to(pos)
            comp_nodes.add(pill)
            comp_labels.add(txt)

        # Curved directional arrows connecting the 4 nodes in a clockwise loop
        comp_arrows = VGroup()
        for i in range(4):
            p1 = comp_center + node_configs[i][2] * 0.65
            p2 = comp_center + node_configs[(i + 1) % 4][2] * 0.65
            arr = CurvedArrow(p1, p2, radius=-0.80, stroke_width=1.8, color=C_STEEL)
            comp_arrows.add(arr)

        # -------------------------------------------------------------------------
        # Section 2: Interaction Loop (Observe -> Decide -> Act)
        # -------------------------------------------------------------------------
        sec2_header = CrispText("2. Interaction Loop", size=14, weight=BOLD, color=C_TITLE)
        sec2_header.move_to(np.array([X_CENTER_SME_LAYOUT_70 + 1.80, 1.55, 0]))

        loop_center = np.array([X_CENTER_SME_LAYOUT_70 + 1.80, 0.50, 0])
        loop_radius = 0.65
        loop_circle = DashedVMobject(
            Circle(radius=loop_radius, color=C_STEEL, stroke_width=1.8),
            num_dashes=20
        ).move_to(loop_center)

        loop_stages = [
            ("Observe", C_SKY, UP * loop_radius * 0.95),
            ("Decide", C_AMBER, (RIGHT * 0.9 + DOWN * 0.4) * loop_radius),
            ("Act", C_CORAL, (LEFT * 0.9 + DOWN * 0.4) * loop_radius)
        ]

        loop_pills = VGroup()
        loop_texts = VGroup()
        for name, col, offset in loop_stages:
            pos = loop_center + offset
            pill = RoundedRectangle(
                corner_radius=0.07, width=1.05, height=0.32,
                fill_color=C_BG, fill_opacity=1.0, stroke_color=col, stroke_width=1.6
            ).move_to(pos)
            txt = CrispText(name, size=10, weight=BOLD, color=C_DARK_CHARCOAL).move_to(pos)
            loop_pills.add(pill)
            loop_texts.add(txt)
        loop_texts = VGroup()
        for name, col, offset in loop_stages:
            pos = loop_center + offset
            pill = RoundedRectangle(
                corner_radius=0.07, width=1.10, height=0.36,
                fill_color=C_BG, fill_opacity=1.0, stroke_color=col, stroke_width=1.8
            ).move_to(pos)
            txt = CrispText(name, size=11, weight=BOLD, color=C_DARK_CHARCOAL).move_to(pos)
            loop_pills.add(pill)
            loop_texts.add(txt)

        # Flowing particle tracker along the circular interaction path
        loop_dot = Dot(radius=0.08, color=C_HIGHLIGHT).move_to(loop_center + UP * loop_radius)
        loop_angle = ValueTracker(0)

        def update_loop_dot(mob):
            theta = loop_angle.get_value()
            mob.move_to(loop_center + np.array([np.cos(theta), np.sin(theta), 0]) * loop_radius)

        loop_dot.add_updater(update_loop_dot)

        # -------------------------------------------------------------------------
        # Section 3: Agent Types (Reactive, Goal-Based, Utility-Based)
        # -------------------------------------------------------------------------
        sec3_y = -1.90
        sec3_header = CrispText("3. Agent Sophistication Levels", size=15, weight=BOLD, color=C_TITLE)
        sec3_header.move_to(np.array([X_CENTER_SME_LAYOUT_70 - 1.25, sec3_y + 0.85, 0]))

        # 3 Structured horizontal cards
        types_data = [
            ("Reactive Agent", "Rule-Driven", C_SKY, "Fast local responses\nto triggers", -1.95),
            ("Goal-Based Agent", "Outcome-Focused", C_AMBER, "Plans action paths\ntoward goals", 0.0),
            ("Utility-Based Agent", "Optimized", C_LILAC, "Balances trade-offs\nacross utilities", +1.95)
        ]

        agent_cards = VGroup()
        agent_highlights = VGroup()

        for title, badge_text, accent, desc, x_offset in types_data:
            c_pos = np.array([X_CENTER_SME_LAYOUT_70 + x_offset, sec3_y - 0.20, 0])
            card_box = RoundedRectangle(
                corner_radius=0.10, width=2.10, height=1.65,
                fill_color=C_BG, fill_opacity=0.9, stroke_color=accent, stroke_width=1.8
            ).move_to(c_pos)

            # Icon vector representation
            if title == "Reactive Agent":
                # Micro gear representation
                center_circ = Circle(radius=0.16, stroke_color=accent, stroke_width=2.5, fill_color=C_CARD_BG, fill_opacity=1.0)
                spokes = VGroup(*[
                    Line(center_circ.get_center() + UP * 0.16, center_circ.get_center() + UP * 0.26, stroke_width=2.5, color=accent).rotate(a, about_point=center_circ.get_center())
                    for a in np.linspace(0, 2 * PI, 8, endpoint=False)
                ])
                icon = VGroup(center_circ, spokes).move_to(c_pos + UP * 0.48)
            elif title == "Goal-Based Agent":
                # Target rings
                r1 = Circle(radius=0.22, stroke_color=accent, stroke_width=1.8)
                r2 = Circle(radius=0.12, stroke_color=accent, stroke_width=1.8)
                r3 = Dot(radius=0.05, color=accent)
                icon = VGroup(r1, r2, r3).move_to(c_pos + UP * 0.48)
            else:
                # Balance scale icon
                beam = Line(LEFT * 0.24, RIGHT * 0.24, stroke_width=2.2, color=accent)
                pivot = Triangle().scale(0.12).set_stroke(color=accent, width=1.5).set_fill(accent, opacity=0.8)
                pan_l = Arc(radius=0.12, start_angle=PI, angle=PI, stroke_width=1.5, color=accent).move_to(beam.get_left() + DOWN * 0.10)
                pan_r = Arc(radius=0.12, start_angle=PI, angle=PI, stroke_width=1.5, color=accent).move_to(beam.get_right() + DOWN * 0.10)
                icon = VGroup(beam, pivot.next_to(beam, DOWN, buff=0), pan_l, pan_r).move_to(c_pos + UP * 0.48)

            type_lbl = CrispText(title, size=12, weight=BOLD, color=C_TITLE).move_to(c_pos + UP * 0.12)
            badge_pill = RoundedRectangle(
                corner_radius=0.06, width=1.70, height=0.30,
                fill_color=accent, fill_opacity=0.22, stroke_color=accent, stroke_width=1.2
            ).move_to(c_pos + DOWN * 0.22)
            badge_lbl = CrispText(badge_text, size=11, weight=BOLD, color=C_DARK_CHARCOAL).move_to(badge_pill)

            sub_desc = CrispText(desc, size=9, weight=NORMAL, color=C_TEXT, align="center").move_to(c_pos + DOWN * 0.58)

            single_card = VGroup(card_box, icon, type_lbl, badge_pill, badge_lbl, sub_desc)
            agent_cards.add(single_card)

        # Animate Section 1: Components mini-loop
        self.play(Write(sec1_header), run_time=0.8)
        self.play(
            LaggedStart(
                *[FadeIn(comp_nodes[i], shift=UP * 0.08) for i in range(4)],
                *[Write(comp_labels[i]) for i in range(4)],
                *[Create(comp_arrows[i]) for i in range(4)],
                lag_ratio=0.15
            ),
            run_time=1.4
        )

        # Animate Section 2: Interaction Loop
        self.play(Write(sec2_header), Create(loop_circle), run_time=1.2)
        self.play(
            LaggedStart(
                *[FadeIn(loop_pills[i], shift=DOWN * 0.05) for i in range(3)],
                *[Write(loop_texts[i]) for i in range(3)],
                lag_ratio=0.2
            ),
            FadeIn(loop_dot),
            run_time=1.8
        )

        # Rotate loop particle continuously
        self.play(loop_angle.animate.set_value(loop_angle.get_value() + 2 * PI), run_time=3.5, rate_func=linear)

        # Animate Section 3: Agent Types
        self.play(Write(sec3_header), run_time=1.0)
        for i in range(3):
            self.play(FadeIn(agent_cards[i], shift=UP * 0.15), run_time=1.2)

        # Sequential illumination & focus highlight per narration
        # Beat: Reactive agents
        pulse_reactive = agent_cards[0][0].copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(Create(pulse_reactive), run_time=0.8)
        self.play(loop_angle.animate.set_value(loop_angle.get_value() + 2 * PI), run_time=5.0, rate_func=linear)
        self.play(FadeOut(pulse_reactive), run_time=0.5)

        # Beat: Goal-based agents
        pulse_goal = agent_cards[1][0].copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(Create(pulse_goal), run_time=0.8)
        self.play(loop_angle.animate.set_value(loop_angle.get_value() + 2 * PI), run_time=5.0, rate_func=linear)
        self.play(FadeOut(pulse_goal), run_time=0.5)

        # Beat: Utility-based agents
        pulse_utility = agent_cards[2][0].copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(Create(pulse_utility), run_time=0.8)
        self.play(loop_angle.animate.set_value(loop_angle.get_value() + 2 * PI), run_time=6.0, rate_func=linear)
        self.play(FadeOut(pulse_utility), run_time=0.6)

        # Ambient circulation during concluding voiceover of Step 1
        self.play(loop_angle.animate.set_value(loop_angle.get_value() + 4 * PI), run_time=10.0, rate_func=linear)

        # Cleanly remove updater before transitioning
        loop_dot.clear_updaters()

        # =========================================================================
        ## Presentation Step 2: What's Next: Hands-On Demo
        # =========================================================================
        # Narration: "Coming up next, we're going hands-on. In the demo, we'll visualize
        # types and architectures of AI, agents, and action as good so you can see..."
        step2_duration = 23.315

        # Seamless header transition to Step 2
        new_title_group = create_title("Handoff, Summary & What's Next", "What's Next: Interactive Hands-On Demo")
        self.play(
            ReplacementTransform(title_group, new_title_group),
            FadeOut(summary_panel),
            FadeOut(panel_tag),
            FadeOut(panel_tag_lbl),
            FadeOut(sec1_header),
            FadeOut(comp_nodes),
            FadeOut(comp_labels),
            FadeOut(comp_arrows),
            FadeOut(sec2_header),
            FadeOut(loop_circle),
            FadeOut(loop_pills),
            FadeOut(loop_texts),
            FadeOut(loop_dot),
            FadeOut(sec3_header),
            FadeOut(agent_cards),
            run_time=1.4
        )

        # Prominent What's Next Banner & Interactive Preview in Safe Right Workspace
        banner_w = 6.90
        banner_h = 5.20
        banner_center = np.array([X_CENTER_SME_LAYOUT_70, -0.55, 0])

        banner_box = RoundedRectangle(
            corner_radius=0.18,
            width=banner_w,
            height=banner_h,
            fill_color=C_CARD_BG,
            fill_opacity=0.98,
            stroke_color=C_BORDER,
            stroke_width=1.8
        ).move_to(banner_center)

        # Category pill badge at top of card
        demo_badge = RoundedRectangle(
            corner_radius=0.08, width=2.40, height=0.44,
            fill_color=C_CORAL, fill_opacity=0.20, stroke_color=C_CORAL, stroke_width=1.5
        ).move_to(banner_box.get_top() + DOWN * 0.50)
        demo_badge_txt = CrispText("Hands-On Lab Preview", size=13, weight=BOLD, color=C_DARK_CHARCOAL).move_to(demo_badge)

        # Hero Vector Terminal / Code & Simulation Window
        sim_w = 6.10
        sim_h = 3.60
        sim_box = RoundedRectangle(
            corner_radius=0.12, width=sim_w, height=sim_h,
            fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_STEEL, stroke_width=1.5
        ).move_to(banner_center + DOWN * 0.25)

        # Window chrome top bar
        sim_top_bar = RoundedRectangle(
            corner_radius=0.12, width=sim_w, height=0.46,
            fill_color="#E2E8F0", fill_opacity=1.0, stroke_color=C_STEEL, stroke_width=1.5
        ).move_to(sim_box.get_top() + DOWN * 0.23)

        # 3 micro window control dots (non-green per guidelines)
        c_red = Dot(radius=0.065, color="#EF4444").move_to(sim_top_bar.get_left() + RIGHT * 0.35)
        c_yellow = Dot(radius=0.065, color=C_MUSTARD).move_to(sim_top_bar.get_left() + RIGHT * 0.60)
        c_blue = Dot(radius=0.065, color=C_SKY).move_to(sim_top_bar.get_left() + RIGHT * 0.85)
        bar_title = CrispText("environment_sim.py — Live Runtime", size=12, weight=BOLD, color=C_TEXT).move_to(sim_top_bar.get_center() + RIGHT * 0.4)

        sim_chrome = VGroup(sim_box, sim_top_bar, c_red, c_yellow, c_blue, bar_title)

        # Simulated live runtime vector visual: split into Decision Loop Graph & Telemetry Streams
        # Left side: Live execution graph nodes
        graph_center = sim_box.get_center() + LEFT * 1.45 + DOWN * 0.15
        state_node_1 = RoundedRectangle(corner_radius=0.07, width=1.5, height=0.42, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_SKY, stroke_width=2.0).move_to(graph_center + UP * 0.8)
        lbl_s1 = CrispText("State Ingest", size=11, weight=BOLD, color=C_DARK_CHARCOAL).move_to(state_node_1)

        state_node_2 = RoundedRectangle(corner_radius=0.07, width=1.5, height=0.42, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=2.0).move_to(graph_center)
        lbl_s2 = CrispText("Policy Engine", size=11, weight=BOLD, color=C_DARK_CHARCOAL).move_to(state_node_2)

        state_node_3 = RoundedRectangle(corner_radius=0.07, width=1.5, height=0.42, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_CORAL, stroke_width=2.0).move_to(graph_center + DOWN * 0.8)
        lbl_s3 = CrispText("Dispatch Tool", size=11, weight=BOLD, color=C_DARK_CHARCOAL).move_to(state_node_3)

        arrow_g1 = Arrow(state_node_1.get_bottom(), state_node_2.get_top(), buff=0.08, stroke_width=2.0, color=C_STEEL, max_tip_length_to_length_ratio=0.25)
        arrow_g2 = Arrow(state_node_2.get_bottom(), state_node_3.get_top(), buff=0.08, stroke_width=2.0, color=C_STEEL, max_tip_length_to_length_ratio=0.25)

        exec_graph = VGroup(state_node_1, lbl_s1, arrow_g1, state_node_2, lbl_s2, arrow_g2, state_node_3, lbl_s3)

        # Right side: Kinetic 'Play / Live Session' Vector Beacon
        beacon_center = sim_box.get_center() + RIGHT * 1.45 + DOWN * 0.15
        outer_ring = Circle(radius=0.85, stroke_color=C_SKY, stroke_width=1.8, stroke_opacity=0.6).move_to(beacon_center)
        mid_ring = Circle(radius=0.62, stroke_color=C_AMBER, stroke_width=2.0).move_to(beacon_center)

        # Vector Play Icon
        play_btn = Triangle().scale(0.32).rotate(-PI / 2).set_fill(C_HIGHLIGHT, opacity=1.0).set_stroke(color=C_HIGHLIGHT, width=1.5).move_to(beacon_center + RIGHT * 0.04)

        play_label = CrispText("Live Execution Demo", size=12, weight=BOLD, color=C_TITLE).next_to(outer_ring, DOWN, buff=0.22)
        live_tag = RoundedRectangle(corner_radius=0.06, width=1.2, height=0.30, fill_color=C_CORAL, fill_opacity=0.25, stroke_color=C_CORAL, stroke_width=1.2).next_to(play_label, DOWN, buff=0.12)
        live_tag_txt = CrispText("Real-Time", size=10, weight=BOLD, color=C_DARK_CHARCOAL).move_to(live_tag)

        beacon_grp = VGroup(outer_ring, mid_ring, play_btn, play_label, live_tag, live_tag_txt)

        # Banner Entry
        self.play(
            FadeIn(banner_box, shift=UP * 0.15),
            FadeIn(demo_badge),
            FadeIn(demo_badge_txt),
            FadeIn(sim_chrome),
            run_time=1.5
        )

        # Animate Graph & Beacon inside the demo terminal
        self.play(
            LaggedStart(
                FadeIn(exec_graph, shift=RIGHT * 0.1),
                FadeIn(beacon_grp, shift=LEFT * 0.1),
                lag_ratio=0.25
            ),
            run_time=1.8
        )

        # Gentle pulsing updater on the play beacon ring to represent active live preview
        pulse_scale = ValueTracker(1.0)

        def pulse_ring_updater(mob):
            s = pulse_scale.get_value()
            mob.become(Circle(radius=0.85 * s, stroke_color=C_SKY, stroke_width=2.2 / s, stroke_opacity=max(0.0, 1.2 - s)).move_to(beacon_center))

        outer_ring.add_updater(pulse_ring_updater)

        # Highlight stroke animation around What's Next banner
        banner_pulse = banner_box.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(Create(banner_pulse), run_time=0.9)
        self.play(FadeOut(banner_pulse), run_time=0.6)

        # Ambient kinetic execution loop: packet moving along nodes while beacon breathes
        pkt = Dot(radius=0.07, color=C_HIGHLIGHT).move_to(state_node_1.get_center())
        self.add(pkt)

        # Synchronized living execution cycle for remaining narration duration
        for _ in range(2):
            self.play(
                MoveAlongPath(pkt, arrow_g1, rate_func=ease_out_cubic), # Changed rate_func
                pulse_scale.animate.set_value(1.25),
                run_time=0.8
            )
            self.play(
                MoveAlongPath(pkt, arrow_g2, rate_func=ease_out_cubic), # Changed rate_func
                pulse_scale.animate.set_value(1.0),
                run_time=0.8
            )
            self.play(pkt.animate.move_to(state_node_1.get_center()), run_time=0.6)

        self.remove(pkt)
        outer_ring.clear_updaters()

        # Clean hold to conclude presentation
        self.sync_to(56.42)
        self.sync_to(56.42)
