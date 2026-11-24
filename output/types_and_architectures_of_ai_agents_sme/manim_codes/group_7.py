C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_WHITE = "#FFFFFF"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
import os
import re
import numpy as np
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

# Safe fallback for instrumentation harness
try:
    from manim_instrumentation import InstrumentedScene
except ImportError:
    class InstrumentedScene:
        pass

# Fallback for CrispText if not injected into global scope
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
class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        # 1. Canvas Background Setup (Modern Soft Light Slate Canvas)
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
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)















        # Safe boundaries & coordinates
        # 20% SME PiP is reserved in top-right: x >= +3.5, y >= +1.8
        # Main presentation content area sits strictly below y <= 1.80

        # Colors from the approved 10-pastel infographic palette
        C_SKY_BLUE = "#62B7E4"
        C_STEEL_BLUE = "#7EA2C8"
        C_LAVENDER = "#9B99C7"
        C_MINT = "#8ECDB7"
        C_AMBER = "#E6A157"
        C_MUSTARD = "#DDB945"
        C_CORAL = "#E58F6D"
        C_ROSE = "#D98CA1"
        C_LILAC = "#C1A5C6"
        C_HIGHLIGHT = "#F78908"
        C_ALERT = "#E55353"
        C_TITLE = "#0F172A"
        C_TEXT = "#404040"
        C_MUTED = "#64748B"
        C_CARD_BG = "#FFFFFF"
        C_CARD_STROKE = "#CBD5E1"


        # =========================================================================
        # PRESENTATION STEP 1: Introduction of Three Agent Types
        # =========================================================================
        ## Presentation Step 1

        title_group = create_title(
            "Types of Agents: Reactive & Goal-Based",
            "Foundational architectures tailored for specific operational complexities"
        )
        self.play(FadeIn(title_group, shift=DOWN * 0.15), run_time=1.0)

        # Build 3 Architectural Pillar Slots horizontally
        # Total available width: x in [-6.2, +6.2], below y <= 1.8
        slot_w = 3.95
        slot_h = 4.85
        slot_y = -0.95
        slot_centers = [-4.15, 0.0, 4.15]

        # Slot 1: Reactive
        slot1_rect = RoundedRectangle(
            width=slot_w, height=slot_h, corner_radius=0.18,
            fill_color=C_CARD_BG, fill_opacity=0.95, stroke_color=C_CARD_STROKE, stroke_width=1.5
        ).move_to([slot_centers[0], slot_y, 0])
        slot1_pill = RoundedRectangle(
            width=2.8, height=0.48, corner_radius=0.24,
            fill_color=C_SKY_BLUE, fill_opacity=0.18, stroke_color=C_SKY_BLUE, stroke_width=1.8
        ).move_to([slot_centers[0], slot_y + slot_h/2 - 0.42, 0])
        slot1_title = CrispText("Reactive Agent", size=16, weight=BOLD, color=C_TITLE).move_to(slot1_pill)
        slot1_sub = CrispText("Rule-Driven Reflex", size=12, weight=NORMAL, color=C_MUTED).next_to(slot1_pill, DOWN, buff=0.14)
        slot1_group = VGroup(slot1_rect, slot1_pill, slot1_title, slot1_sub)

        # Slot 2: Goal-Based
        slot2_rect = RoundedRectangle(
            width=slot_w, height=slot_h, corner_radius=0.18,
            fill_color=C_CARD_BG, fill_opacity=0.95, stroke_color=C_CARD_STROKE, stroke_width=1.5
        ).move_to([slot_centers[1], slot_y, 0])
        slot2_pill = RoundedRectangle(
            width=2.8, height=0.48, corner_radius=0.24,
            fill_color=C_AMBER, fill_opacity=0.18, stroke_color=C_AMBER, stroke_width=1.8
        ).move_to([slot_centers[1], slot_y + slot_h/2 - 0.42, 0])
        slot2_title = CrispText("Goal-Based Agent", size=16, weight=BOLD, color=C_TITLE).move_to(slot2_pill)
        slot2_sub = CrispText("Planned Outcomes", size=12, weight=NORMAL, color=C_MUTED).next_to(slot2_pill, DOWN, buff=0.14)
        slot2_group = VGroup(slot2_rect, slot2_pill, slot2_title, slot2_sub)

        # Slot 3: Utility-Based (Preview/Subdued)
        slot3_rect = RoundedRectangle(
            width=slot_w, height=slot_h, corner_radius=0.18,
            fill_color=C_CARD_BG, fill_opacity=0.75, stroke_color=C_CARD_STROKE, stroke_width=1.5
        ).move_to([slot_centers[2], slot_y, 0])
        slot3_pill = RoundedRectangle(
            width=2.8, height=0.48, corner_radius=0.24,
            fill_color=C_LILAC, fill_opacity=0.18, stroke_color=C_LILAC, stroke_width=1.8
        ).move_to([slot_centers[2], slot_y + slot_h/2 - 0.42, 0])
        slot3_title = CrispText("Utility-Based Agent", size=16, weight=BOLD, color=C_TITLE).move_to(slot3_pill)
        slot3_sub = CrispText("Optimized Trade-Offs", size=12, weight=NORMAL, color=C_MUTED).next_to(slot3_pill, DOWN, buff=0.14)
        slot3_preview = CrispText("Deliberates on Best Path", size=13, weight=NORMAL, color=C_MUTED).move_to([slot_centers[2], slot_y - 0.2, 0])
        slot3_tag = RoundedRectangle(
            width=1.9, height=0.36, corner_radius=0.18,
            fill_color="#F1F5F9", fill_opacity=1.0, stroke_color=C_CARD_STROKE, stroke_width=1.2
        ).next_to(slot3_preview, DOWN, buff=0.25)
        slot3_tag_txt = CrispText("Upcoming Topic", size=11, weight=BOLD, color=C_MUTED).move_to(slot3_tag)
        slot3_group = VGroup(slot3_rect, slot3_pill, slot3_title, slot3_sub, slot3_preview, slot3_tag, slot3_tag_txt)

        # Sequential reveal of the three architectural options
        self.play(FadeIn(slot1_group, shift=UP * 0.2), run_time=0.9)
        self.play(FadeIn(slot2_group, shift=UP * 0.2), run_time=0.9)
        self.play(FadeIn(slot3_group, shift=UP * 0.2), run_time=0.9)

        # Highlight Slot 1 (Reactive) to transition into Step 2
        slot1_highlight = slot1_rect.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(Create(slot1_highlight), run_time=0.8)
        self.wait(1.5)

        # Ambient breath on highlight
        self.play(slot1_highlight.animate.set_stroke(opacity=0.6, width=2.5), run_time=1.2)
        self.play(slot1_highlight.animate.set_stroke(opacity=1.0, width=3.5), run_time=1.2)
        self.wait(1.0)

        # =========================================================================
        # PRESENTATION STEP 2: Reactive Agent: Rule-Driven Reflex
        # =========================================================================
        ## Presentation Step 2

        new_title = create_title(
            "Reactive Agent: Rule-Driven",
            "Immediate condition-action switch without state or deliberation"
        )
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Build Reactive Mechanism Inside Slot 1
        # Center x = -4.15, y in [-3.0, +1.0]
        # Top limitation badges: "No Memory" & "No Plan"
        badge_no_mem = VGroup(
            RoundedRectangle(width=1.55, height=0.36, corner_radius=0.18, fill_color="#FEE2E2", fill_opacity=0.9, stroke_color="#FCA5A5", stroke_width=1.2),
            CrispText("No Memory", size=11, weight=BOLD, color=C_ALERT)
        )
        badge_no_mem[1].move_to(badge_no_mem[0])
        badge_no_mem.move_to([slot_centers[0] - 0.95, slot_y + 0.95, 0])

        badge_no_plan = VGroup(
            RoundedRectangle(width=1.55, height=0.36, corner_radius=0.18, fill_color="#FEE2E2", fill_opacity=0.9, stroke_color="#FCA5A5", stroke_width=1.2),
            CrispText("No Plan", size=11, weight=BOLD, color=C_ALERT)
        )
        badge_no_plan[1].move_to(badge_no_plan[0])
        badge_no_plan.move_to([slot_centers[0] + 0.95, slot_y + 0.95, 0])

        self.play(
            FadeIn(badge_no_mem, shift=DOWN * 0.1),
            FadeIn(badge_no_plan, shift=DOWN * 0.1),
            run_time=0.8
        )

        # Mechanism Stage 1: Sensor & Condition
        sensor_box = RoundedRectangle(
            width=3.2, height=0.68, corner_radius=0.14,
            fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_SKY_BLUE, stroke_width=1.5
        ).move_to([slot_centers[0], slot_y + 0.35, 0])
        sensor_lbl = CrispText("Input Condition", size=11, weight=NORMAL, color=C_MUTED).move_to(sensor_box.get_top() + DOWN * 0.14)
        sensor_val = CrispText("Output < 8% Threshold", size=13, weight=BOLD, color=C_TITLE).move_to(sensor_box.get_bottom() + UP * 0.17)
        sensor_grp = VGroup(sensor_box, sensor_lbl, sensor_val)

        # Mechanism Stage 2: Rule Engine
        rule_box = RoundedRectangle(
            width=3.2, height=0.68, corner_radius=0.14,
            fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_STEEL_BLUE, stroke_width=1.5
        ).move_to([slot_centers[0], slot_y - 0.65, 0])
        rule_lbl = CrispText("Rule Engine", size=11, weight=NORMAL, color=C_MUTED).move_to(rule_box.get_top() + DOWN * 0.14)
        rule_val = CrispText("If Drop > 8% -> Trigger Alert", size=12, weight=BOLD, color=C_TITLE).move_to(rule_box.get_bottom() + UP * 0.17)
        rule_grp = VGroup(rule_box, rule_lbl, rule_val)

        # Mechanism Stage 3: Instant Action
        action_box = RoundedRectangle(
            width=3.2, height=0.68, corner_radius=0.14,
            fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_CORAL, stroke_width=1.5
        ).move_to([slot_centers[0], slot_y - 1.65, 0])
        action_lbl = CrispText("Instant Action", size=11, weight=NORMAL, color=C_MUTED).move_to(action_box.get_top() + DOWN * 0.14)
        action_val = CrispText("Send Notification: Site 12", size=12, weight=BOLD, color=C_ALERT).move_to(action_box.get_bottom() + UP * 0.17)
        action_grp = VGroup(action_box, action_lbl, action_val)

        # Directed signal arrows connecting them
        arr1 = Arrow(sensor_box.get_bottom(), rule_box.get_top(), buff=0.08, stroke_width=2.5, max_tip_length_to_length_ratio=0.25, color=C_SKY_BLUE)
        arr2 = Arrow(rule_box.get_bottom(), action_box.get_top(), buff=0.08, stroke_width=2.5, max_tip_length_to_length_ratio=0.25, color=C_CORAL)

        self.play(FadeIn(sensor_grp, shift=DOWN * 0.1), run_time=0.7)
        self.play(Create(arr1), FadeIn(rule_grp, shift=DOWN * 0.1), run_time=0.7)
        self.play(Create(arr2), FadeIn(action_grp, shift=DOWN * 0.1), run_time=0.7)

        # Kinetic signal pulse passing down the chain
        pulse_dot = Dot(radius=0.1, color=C_HIGHLIGHT).move_to(sensor_box.get_bottom())
        self.play(
            MoveAlongPath(pulse_dot, arr1, rate_func=linear, run_time=0.4)
        )
        self.play(
            rule_box.animate.set_stroke(color=C_HIGHLIGHT, width=2.8),
            run_time=0.2
        )
        self.play(
            MoveAlongPath(pulse_dot, arr2, rate_func=linear, run_time=0.4)
        )
        self.play(
            action_box.animate.set_stroke(color=C_ALERT, width=2.8),
            FadeOut(pulse_dot),
            run_time=0.3
        )
        self.play(
            rule_box.animate.set_stroke(color=C_STEEL_BLUE, width=1.5),
            action_box.animate.set_stroke(color=C_CORAL, width=1.5),
            run_time=0.4
        )

        # Pros and Cons evaluation tags: Fast & Predictable vs Limited
        pro_pill = RoundedRectangle(
            width=2.8, height=0.36, corner_radius=0.18,
            fill_color="#E6F4EA", fill_opacity=0.9, stroke_color=C_MINT, stroke_width=1.5
        ).move_to([slot_centers[0], slot_y - 2.22, 0])
        pro_txt = CrispText("Fast & Predictable Execution", size=11, weight=BOLD, color="#2D6A4F").move_to(pro_pill)
        pro_grp = VGroup(pro_pill, pro_txt)

        self.play(FadeIn(pro_grp, shift=UP * 0.1), run_time=0.7)
        self.wait(1.5)

        # Flash Limited / Trade-off callout
        con_pill = RoundedRectangle(
            width=2.8, height=0.36, corner_radius=0.18,
            fill_color="#FEE2E2", fill_opacity=0.95, stroke_color=C_ALERT, stroke_width=1.5
        ).move_to([slot_centers[0], slot_y - 2.22, 0])
        con_txt = CrispText("Limited: No Cause Investigation", size=11, weight=BOLD, color=C_ALERT).move_to(con_pill)
        con_grp = VGroup(con_pill, con_txt)

        self.play(ReplacementTransform(pro_grp, con_grp), run_time=0.8)
        self.wait(2.0)

        # =========================================================================
        # PRESENTATION STEP 3: Goal-Based Agent: Planned Outcomes
        # =========================================================================
        ## Presentation Step 3

        new_title_3 = create_title(
            "Goal-Based Agent: Planned Outcomes",
            "Deliberate path search and evidence evaluation to achieve a target outcome"
        )
        self.remove(new_title)
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title_3, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title_3

        # Transition highlight smoothly from Slot 1 to Slot 2
        slot2_highlight = slot2_rect.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(
            FadeOut(slot1_highlight),
            Create(slot2_highlight),
            run_time=0.8
        )

        # Build Goal-Based Mechanism Inside Slot 2 (center x = 0.0)
        # Agent node on left, Goal Target node on right
        agent_node = VGroup(
            Circle(radius=0.38, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=2.2),
            CrispText("AI Core", size=10, weight=BOLD, color=C_TITLE)
        ).move_to([slot_centers[1] - 1.25, slot_y - 0.35, 0])
        agent_node[1].move_to(agent_node[0])

        goal_node = VGroup(
            Circle(radius=0.45, fill_color="#FEF3C7", fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=2.4),
            Circle(radius=0.26, fill_color="#FDE68A", fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=1.5),
            Dot(radius=0.1, color=C_HIGHLIGHT),
            CrispText("Target Goal", size=10, weight=BOLD, color=C_TITLE)
        )
        goal_node[0:3].move_to([slot_centers[1] + 1.25, slot_y - 0.35, 0])
        goal_node[3].next_to(goal_node[0], DOWN, buff=0.1)

        # Branching paths from Agent to Goal
        # Path A (Top branch): Inverter Check (Evaluated and abandoned)
        # Path B (Middle branch): Irradiance Pull (Chosen path)
        # Path C (Bottom branch): Grid Drop Confirmed
        start_pt = agent_node[0].get_right()
        end_pt = goal_node[0].get_left()

        pA_mid = np.array([slot_centers[1], slot_y + 0.45, 0])
        pB_mid = np.array([slot_centers[1], slot_y - 0.35, 0])
        pC_mid = np.array([slot_centers[1], slot_y - 1.15, 0])

        pathA = CubicBezier(start_pt, start_pt + RIGHT * 0.4 + UP * 0.4, pA_mid + LEFT * 0.4, pA_mid, color=C_CARD_STROKE, stroke_width=2.0)
        pathB = Line(start_pt, end_pt, color=C_AMBER, stroke_width=3.0)
        pathC = CubicBezier(start_pt, start_pt + RIGHT * 0.4 + DOWN * 0.4, pC_mid + LEFT * 0.4, pC_mid, color=C_CARD_STROKE, stroke_width=2.0)

        # Path exploration nodes
        nodeA = VGroup(
            RoundedRectangle(width=1.5, height=0.34, corner_radius=0.17, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_CARD_STROKE, stroke_width=1.2),
            CrispText("Inverter Logs", size=10, weight=NORMAL, color=C_MUTED)
        ).move_to(pA_mid)
        nodeA[1].move_to(nodeA[0])

        nodeB = VGroup(
            RoundedRectangle(width=1.75, height=0.38, corner_radius=0.19, fill_color="#FEF3C7", fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=1.8),
            CrispText("Pull Solar Data", size=11, weight=BOLD, color=C_TITLE)
        ).move_to(pB_mid)
        nodeB[1].move_to(nodeB[0])

        nodeC = VGroup(
            RoundedRectangle(width=1.5, height=0.34, corner_radius=0.17, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_CARD_STROKE, stroke_width=1.2),
            CrispText("Check Weather", size=10, weight=NORMAL, color=C_MUTED)
        ).move_to(pC_mid)
        nodeC[1].move_to(nodeC[0])

        self.play(
            FadeIn(agent_node, shift=RIGHT * 0.1),
            FadeIn(goal_node, shift=LEFT * 0.1),
            run_time=0.8
        )
        self.play(
            Create(pathA), Create(pathB), Create(pathC),
            FadeIn(nodeA), FadeIn(nodeB), FadeIn(nodeC),
            run_time=1.0
        )

        # Evaluation indicator: Question mark on candidate paths
        q_markA = CrispText("?", size=14, weight=BOLD, color=C_MUTED).next_to(nodeA, UP, buff=0.08)
        q_markB = CrispText("★", size=14, weight=BOLD, color=C_HIGHLIGHT).next_to(nodeB, UP, buff=0.08)
        self.play(FadeIn(q_markA), FadeIn(q_markB), run_time=0.5)

        # Animate dynamic agent token moving along the chosen path B to the goal
        moving_evaluator = Dot(radius=0.12, color=C_HIGHLIGHT).move_to(start_pt)
        self.play(FadeIn(moving_evaluator), run_time=0.3)
        self.play(
            moving_evaluator.animate.move_to(nodeB.get_left()),
            run_time=0.8
        )
        self.play(
            nodeB.animate.set_stroke(color=C_HIGHLIGHT, width=2.5),
            run_time=0.3
        )
        self.play(
            moving_evaluator.animate.move_to(end_pt),
            run_time=0.9
        )
        self.play(
            goal_node[0].animate.set_stroke(color=C_HIGHLIGHT, width=3.5),
            FadeOut(moving_evaluator),
            run_time=0.4
        )

        # Path Score / Progress Bar
        score_bar_bg = RoundedRectangle(
            width=3.2, height=0.28, corner_radius=0.14, fill_color="#E2E8F0", fill_opacity=1.0, stroke_width=0
        ).move_to([slot_centers[1], slot_y - 1.75, 0])
        score_fill = RoundedRectangle(
            width=2.85, height=0.24, corner_radius=0.12, fill_color=C_MINT, fill_opacity=1.0, stroke_width=0
        ).align_to(score_bar_bg, LEFT).shift(RIGHT * 0.02)
        score_lbl = CrispText("Goal Probability: 94%", size=11, weight=BOLD, color="#2D6A4F").next_to(score_bar_bg, UP, buff=0.1)

        self.play(
            FadeIn(score_bar_bg),
            GrowFromEdge(score_fill, LEFT),
            FadeIn(score_lbl),
            run_time=0.9
        )

        # Comparison Badge: No Fixed Script (Struck out) vs Dynamic Adaptation
        fixed_script_tag = VGroup(
            RoundedRectangle(width=1.5, height=0.34, corner_radius=0.17, fill_color="#F1F5F9", fill_opacity=1.0, stroke_color=C_CARD_STROKE, stroke_width=1.2),
            CrispText("Fixed Script", size=10, weight=NORMAL, color=C_MUTED)
        ).move_to([slot_centers[1] - 0.85, slot_y - 2.25, 0])
        fixed_script_tag[1].move_to(fixed_script_tag[0])

        cross_line = Line(
            fixed_script_tag.get_left() + LEFT * 0.05, fixed_script_tag.get_right() + RIGHT * 0.05,
            color=C_ALERT, stroke_width=2.5
        )

        adaptive_tag = VGroup(
            RoundedRectangle(width=1.65, height=0.34, corner_radius=0.17, fill_color="#E6F4EA", fill_opacity=1.0, stroke_color=C_MINT, stroke_width=1.5),
            CrispText("Dynamic Plan", size=10, weight=BOLD, color="#2D6A4F")
        ).move_to([slot_centers[1] + 0.85, slot_y - 2.25, 0])
        adaptive_tag[1].move_to(adaptive_tag[0])

        self.play(FadeIn(fixed_script_tag), run_time=0.5)
        self.play(Create(cross_line), run_time=0.4)
        self.play(FadeIn(adaptive_tag, shift=UP * 0.1), run_time=0.6)

        # Final persistent breath across the active mechanism
        self.play(
            slot2_highlight.animate.set_stroke(opacity=0.7, width=2.8),
            run_time=1.0
        )
        self.play(
            slot2_highlight.animate.set_stroke(opacity=1.0, width=3.5),
            run_time=1.0
        )
        self.wait(1.5)