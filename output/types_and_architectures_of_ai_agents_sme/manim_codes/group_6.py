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
import os

# Safe fallback for execution environments where InstrumentedScene may or may not be pre-defined
if "InstrumentedScene" not in globals():
    class InstrumentedScene(Scene):
        def sync_to(self, time_point):
            current = self.renderer.time
            if time_point > current:
                self.wait(time_point - current)





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














        start_time = self.renderer.time

        # Image Paths
        brain_path = "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_6_llm_brain.png"
        action_hub_path = "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_6_action_hub_asset.png"
        gauge_path = "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_6_utility_gauge.png"

        # Safe Header Builder (Terminates left of x = 3.5 to respect Layout 20 SME PiP)

        # =========================================================================
        # PRESENTATION STEP 1: Perception: Input Intake
        # =========================================================================
        ## Presentation Step 1
        t_step1_end = start_time + 43.731
        
        # Header instantiation
        title_group = create_title("Perception-Reasoning-Action Cycle Deep Dive", "Perception: Continuous Ingest & Contextual Intake")
        self.play(FadeIn(title_group, shift=DOWN * 0.1), run_time=0.8)

        # Perception Visual Mechanism (Sensory Radar & Receptor Hub)
        p_center = np.array([-1.5, -0.4, 0])

        # Sensory Beacon Core
        sensory_base = Circle(radius=1.2, stroke_color="#62B7E4", stroke_width=3, fill_color="#FFFFFF", fill_opacity=0.95)
        sensory_inner = Circle(radius=0.85, stroke_color="#7EA2C8", stroke_width=1.5, stroke_opacity=0.6, fill_color="#F8FAFC", fill_opacity=0.9)
        sensory_core_dot = Dot(point=p_center, radius=0.22, color="#2C81FE")
        
        # Radar rings for ambient pulse
        radar_ring1 = Circle(radius=1.5, stroke_color="#62B7E4", stroke_width=1.5, stroke_opacity=0.4).move_to(p_center)
        radar_ring2 = Circle(radius=1.8, stroke_color="#7EA2C8", stroke_width=1.0, stroke_opacity=0.25).move_to(p_center)
        
        # Perception Badge
        p_badge_rect = RoundedRectangle(corner_radius=0.08, width=2.4, height=0.46, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#62B7E4", stroke_width=2.0)
        p_badge_txt = CrispText("Perception Module", size=13, weight=BOLD, color="#0F172A")
        fit_into_box(p_badge_txt, p_badge_rect, pad_x=0.2, pad_y=0.08)
        p_badge = VGroup(p_badge_rect, p_badge_txt).move_to(p_center + UP * 1.55)

        perception_unit = VGroup(sensory_base, sensory_inner, sensory_core_dot, radar_ring1, radar_ring2, p_badge).move_to(p_center)
        
        # Ambient Radar Sweep Line
        sweep_line = Line(p_center, p_center + RIGHT * 1.2, color="#2C81FE", stroke_width=2.5)
        def rotate_sweep(mob, dt):
            mob.rotate(1.8 * dt, about_point=p_center)
        sweep_line.add_updater(rotate_sweep)

        self.play(
            FadeIn(sensory_base),
            FadeIn(sensory_inner),
            FadeIn(sensory_core_dot),
            Create(radar_ring1),
            Create(radar_ring2),
            FadeIn(p_badge, shift=UP * 0.1),
            Create(sweep_line),
            run_time=1.4
        )

        # Working Context Panel on the Right
        wc_pos = np.array([3.6, -0.4, 0])
        wc_frame = RoundedRectangle(corner_radius=0.1, width=3.4, height=4.2, fill_color="#FFFFFF", fill_opacity=0.95, stroke_color="#CBD5E1", stroke_width=2.0).move_to(wc_pos)
        wc_title_rect = RoundedRectangle(corner_radius=0.06, width=3.0, height=0.42, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#7EA2C8", stroke_width=1.5).move_to(wc_pos + UP * 1.65)
        wc_title_txt = CrispText("Working Context Stack", size=13, weight=BOLD, color="#0F172A").move_to(wc_title_rect)
        wc_panel = VGroup(wc_frame, wc_title_rect, wc_title_txt)

        self.play(FadeIn(wc_panel, shift=LEFT * 0.2), run_time=1.0)

        # Data Stream Sources (Entering from Left & Converging on Perception)
        input_data = [
            ("Data Reading", "#62B7E4", np.array([-5.6, 1.2, 0])),
            ("User Request", "#E6A157", np.array([-5.8, 0.2, 0])),
            ("Tool Result", "#8ECDB7", np.array([-5.8, -0.8, 0])),
            ("Error Message", "#E58F6D", np.array([-5.6, -1.8, 0]))
        ]

        stream_nodes = []
        stream_arrows = []
        stack_slots = [wc_pos + UP * (1.05 - 0.72 * i) for i in range(4)]
        context_cards = []

        for i, (label_txt, color_code, start_pos) in enumerate(input_data):
            # Input Pill
            pill_rect = RoundedRectangle(corner_radius=0.07, width=2.1, height=0.48, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=color_code, stroke_width=2.0)
            pill_txt = CrispText(label_txt, size=12, weight=BOLD, color="#404040")
            fit_into_box(pill_txt, pill_rect, pad_x=0.2, pad_y=0.08)
            pill = VGroup(pill_rect, pill_txt).move_to(start_pos)
            stream_nodes.append(pill)

            # Arrow into Perception Core
            stream_arr = Arrow(start=start_pos + RIGHT * 1.1, end=p_center + LEFT * 1.15 + UP * (0.5 - 0.35 * i), buff=0.1, color=color_code, stroke_width=2.5, max_tip_length_to_length_ratio=0.25)
            stream_arrows.append(stream_arr)

            # Context Card inside Working Context Stack
            card_rect = RoundedRectangle(corner_radius=0.06, width=2.9, height=0.55, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=color_code, stroke_width=1.5)
            card_dot = Dot(radius=0.08, color=color_code).move_to(card_rect.get_left() + RIGHT * 0.25)
            card_lbl = CrispText(f"+ {label_txt}", size=11, weight=BOLD, color="#334155").next_to(card_dot, RIGHT, buff=0.15)
            card_group = VGroup(card_rect, card_dot, card_lbl).move_to(stack_slots[i])
            context_cards.append(card_group)

        # Ingest streams sequentially with kinetic particle transfers
        for i in range(4):
            pill = stream_nodes[i]
            arr = stream_arrows[i]
            card = context_cards[i]
            
            # Animate stream entry
            self.play(FadeIn(pill, shift=RIGHT * 0.2), GrowArrow(arr), run_time=1.0)
            
            # Packet pulse traveling into Perception
            pkt = Dot(arr.get_start(), radius=0.12, color=input_data[i][1])
            self.play(
                MoveAlongPath(pkt, arr, rate_func=smooth),
                sensory_base.animate.set_stroke(color="#F78908", width=4.5),
                run_time=1.1
            )
            self.remove(pkt)
            
            # Channel from Perception to Working Context
            transfer_arr = Arrow(start=p_center + RIGHT * 1.25, end=card.get_left(), buff=0.15, color=input_data[i][1], stroke_width=2.0)
            self.play(
                sensory_base.animate.set_stroke(color="#62B7E4", width=3.0),
                GrowArrow(transfer_arr),
                run_time=0.7
            )
            self.play(
                FadeIn(card, shift=DOWN * 0.1),
                FadeOut(transfer_arr),
                run_time=0.8
            )
            self.wait(1.5)

        # Pulse highlight on context stack to reinforce aggregation
        stack_highlight = wc_frame.copy().set_fill(opacity=0).set_stroke(color="#F78908", width=3.5)
        self.play(Create(stack_highlight), run_time=0.8)
        self.play(FadeOut(stack_highlight), run_time=0.6)

        # Natural sync wait to complete Step 1
        current_time = self.renderer.time
        if current_time < t_step1_end:
            self.wait(t_step1_end - current_time)

        # =========================================================================
        # PRESENTATION STEP 2: Reasoning: Interpretation & Plan
        # =========================================================================
        ## Presentation Step 2
        t_step2_end = t_step1_end + 18.001

        # Seamless Title Transition
        new_title = create_title("Perception-Reasoning-Action Cycle Deep Dive", "Reasoning: LLM Cognition, Goal Alignment & Planning")
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Stop updater on sweep line before transitioning
        sweep_line.clear_updaters()

        # Condense Step 1 visuals to the far left
        step1_inputs = VGroup(*stream_nodes, *stream_arrows)
        self.play(FadeOut(step1_inputs), run_time=0.7)

        # Scale down Perception Module and move to left dock (x = -5.4, y = -0.4)
        p_scaled_group = VGroup(sensory_base, sensory_inner, sensory_core_dot, radar_ring1, radar_ring2, p_badge, sweep_line)
        self.play(
            p_scaled_group.animate.scale(0.55).move_to([-5.3, -0.4, 0]),
            wc_panel.animate.scale(0.65).move_to([-3.1, -0.4, 0]),
            VGroup(*context_cards).animate.scale(0.65).move_to([-3.1, -0.4, 0]),
            run_time=1.2
        )

        # Central Reasoning Engine (Brain Hero Illustration or Neural Node)
        reason_center = np.array([0.6, -0.4, 0])

        if os.path.exists(brain_path):
            brain_img = ImageMobject(brain_path).scale_to_fit_height(2.3).move_to(reason_center)
            reason_hero = Group(brain_img)
        else:
            # Procedural Neural Hub Fallback
            b_bg = Circle(radius=1.1, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#9B99C7", stroke_width=2.5).move_to(reason_center)
            b_dot = Dot(reason_center, radius=0.25, color="#9B99C7")
            b_ring = Circle(radius=1.35, stroke_color="#62B7E4", stroke_width=1.5, stroke_opacity=0.6).move_to(reason_center)
            reason_hero = Group(VGroup(b_bg, b_dot, b_ring))

        reason_badge_rect = RoundedRectangle(corner_radius=0.08, width=2.4, height=0.46, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#9B99C7", stroke_width=2.0)
        reason_badge_txt = CrispText("Reasoning Engine", size=13, weight=BOLD, color="#0F172A")
        fit_into_box(reason_badge_txt, reason_badge_rect, pad_x=0.2, pad_y=0.08)
        reason_badge = VGroup(reason_badge_rect, reason_badge_txt).move_to(reason_center + UP * 1.55)

        # Connect Context to Reasoning Engine
        context_to_reason = Arrow(start=[-2.0, -0.4, 0], end=[reason_center[0] - 1.25, -0.4, 0], buff=0.1, color="#7EA2C8", stroke_width=3.0)

        # Internal Cognitive Factors [Goal Badge & Past Actions Badge]
        goal_rect = RoundedRectangle(corner_radius=0.06, width=1.9, height=0.42, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#E6A157", stroke_width=1.5)
        goal_txt = CrispText("Goal: Uptime 99%", size=11, weight=BOLD, color="#E6A157")
        fit_into_box(goal_txt, goal_rect, pad_x=0.2, pad_y=0.08)
        goal_badge = VGroup(goal_rect, goal_txt).move_to(reason_center + UP * 0.75 + RIGHT * 1.6)

        hist_rect = RoundedRectangle(corner_radius=0.06, width=1.9, height=0.42, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#B88968", stroke_width=1.5)
        hist_txt = CrispText("History: 3 Checks", size=11, weight=BOLD, color="#B88968")
        fit_into_box(hist_txt, hist_rect, pad_x=0.2, pad_y=0.08)
        hist_badge = VGroup(hist_rect, hist_txt).move_to(reason_center + DOWN * 0.75 + RIGHT * 1.6)

        # Formulated Plan Output Artifact (Flowchart Pill)
        plan_rect = RoundedRectangle(corner_radius=0.08, width=2.2, height=0.72, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#8ECDB7", stroke_width=2.5)
        plan_hdr = CrispText("Formulated Plan", size=12, weight=BOLD, color="#0F172A")
        plan_sub = CrispText("Step-by-step Policy", size=10, weight=NORMAL, color="#475569")
        plan_txt = VGroup(plan_hdr, plan_sub).arrange(DOWN, buff=0.05).move_to(plan_rect)
        fit_into_box(plan_txt, plan_rect, pad_x=0.2, pad_y=0.08)
        plan_badge = VGroup(plan_rect, plan_txt).move_to(np.array([4.4, -0.4, 0]))

        reason_to_plan = Arrow(start=reason_center + RIGHT * 1.25, end=plan_badge.get_left(), buff=0.15, color="#8ECDB7", stroke_width=3.0)

        self.play(
            FadeIn(reason_hero),
            FadeIn(reason_badge, shift=UP * 0.1),
            GrowArrow(context_to_reason),
            run_time=1.2
        )

        self.play(
            FadeIn(goal_badge, shift=LEFT * 0.2),
            FadeIn(hist_badge, shift=LEFT * 0.2),
            run_time=1.0
        )

        # Cognition pulse (intelligence active)
        reason_pulse = Circle(radius=1.35, stroke_color="#F78908", stroke_width=3.5).move_to(reason_center)
        self.play(Create(reason_pulse), run_time=0.7)
        self.play(
            FadeOut(reason_pulse),
            GrowArrow(reason_to_plan),
            FadeIn(plan_badge, shift=RIGHT * 0.2),
            run_time=1.2
        )

        # Step 2 sync wait
        current_time = self.renderer.time
        if current_time < t_step2_end:
            self.wait(t_step2_end - current_time)

        # =========================================================================
        # PRESENTATION STEP 3: Action: Execution & Cycle Restart
        # =========================================================================
        ## Presentation Step 3
        t_step3_end = t_step2_end + 43.415

        # Final Step Title Transition
        final_title = create_title("Perception-Reasoning-Action Cycle Deep Dive", "Action: Tool Dispatch, Environmental Feedback & Cycle Recurrence")
        self.remove(new_title)
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(final_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = final_title

        # Fade out peripheral badges from Step 2 to make space for the full cycle
        self.play(
            FadeOut(goal_badge),
            FadeOut(hist_badge),
            FadeOut(context_to_reason),
            FadeOut(reason_to_plan),
            run_time=0.6
        )

        # Position 3 Pillars of PRA Architecture:
        # 1. Perception Hub (Left: x = -4.5)
        # 2. Reasoning Hub (Center: x = -0.5)
        # 3. Action Hub (Right: x = +3.5)
        p_anchor = np.array([-4.5, -0.4, 0])
        r_anchor = np.array([-0.5, -0.4, 0])
        a_anchor = np.array([3.5, -0.4, 0])

        self.play(
            p_scaled_group.animate.move_to(p_anchor),
            wc_panel.animate.move_to(p_anchor + DOWN * 1.5).scale(0.8),
            VGroup(*context_cards).animate.move_to(p_anchor + DOWN * 1.5).scale(0.8),
            reason_hero.animate.scale(0.75).move_to(r_anchor),
            reason_badge.animate.scale(0.85).move_to(r_anchor + UP * 1.3),
            run_time=1.2
        )

        # Action Hub Setup
        if os.path.exists(action_hub_path):
            action_img = ImageMobject(action_hub_path).scale_to_fit_height(1.8).move_to(a_anchor)
            action_hero = Group(action_img)
        else:
            # Procedural Action Gear Mechanism
            gear_outer = Circle(radius=0.9, stroke_color="#E6A157", stroke_width=3.0, fill_color="#FFFFFF", fill_opacity=1.0).move_to(a_anchor)
            gear_core = Dot(a_anchor, radius=0.25, color="#E6A157")
            action_hero = Group(VGroup(gear_outer, gear_core))

        action_badge_rect = RoundedRectangle(corner_radius=0.08, width=2.2, height=0.46, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#E6A157", stroke_width=2.0)
        action_badge_txt = CrispText("Action Layer", size=13, weight=BOLD, color="#0F172A")
        fit_into_box(action_badge_txt, action_badge_rect, pad_x=0.2, pad_y=0.08)
        action_badge = VGroup(action_badge_rect, action_badge_txt).move_to(a_anchor + UP * 1.3)

        # Plan moving from Reasoning into Action Layer
        self.play(
            FadeIn(action_hero),
            FadeIn(action_badge, shift=UP * 0.1),
            plan_badge.animate.scale(0.75).move_to((r_anchor + a_anchor) / 2 + UP * 0.2),
            run_time=1.0
        )

        pra_arr1 = Arrow(start=p_anchor + RIGHT * 0.8, end=r_anchor + LEFT * 0.8, buff=0.1, color="#62B7E4", stroke_width=3.0)
        pra_arr2 = Arrow(start=r_anchor + RIGHT * 0.8, end=a_anchor + LEFT * 0.8, buff=0.1, color="#9B99C7", stroke_width=3.0)

        self.play(GrowArrow(pra_arr1), GrowArrow(pra_arr2), run_time=0.8)

        # Outward Action Signals: [Call Tool], [Write Output], [Send Message], [Update Record]
        action_dispatches = [
            ("Call Tool", "#62B7E4", np.array([5.7, 0.9, 0])),
            ("Write Output", "#8ECDB7", np.array([5.7, 0.3, 0])),
            ("Send Message", "#E6A157", np.array([5.7, -0.3, 0])),
            ("Update Record", "#9B99C7", np.array([5.7, -0.9, 0]))
        ]

        dispatch_mobs = []
        dispatch_arrows = []
        for label, color_code, pos in action_dispatches:
            pill_bg = RoundedRectangle(corner_radius=0.06, width=1.9, height=0.4, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color=color_code, stroke_width=1.5)
            pill_l = CrispText(label, size=11, weight=BOLD, color="#334155")
            item = VGroup(pill_bg, pill_l).move_to(pos)
            arr = Arrow(start=a_anchor + RIGHT * 0.9 + UP * (pos[1] * 0.4), end=item.get_left(), buff=0.1, color=color_code, stroke_width=2.0)
            dispatch_mobs.append(item)
            dispatch_arrows.append(arr)

        for i in range(4):
            self.play(
                GrowArrow(dispatch_arrows[i]),
                FadeIn(dispatch_mobs[i], shift=RIGHT * 0.15),
                run_time=0.5
            )

        self.wait(1.0)

        # The Loop Closure: Environment Feedback Arrow back to Perception ("New Perception")
        # Bottom curved arrow linking Action back to Perception
        feedback_path = CurvedArrow(
            start_point=a_anchor + DOWN * 0.9,
            end_point=p_anchor + DOWN * 0.9,
            angle=0.45,
            color="#2C81FE",
            stroke_width=3.0
        )
        feedback_label_rect = RoundedRectangle(corner_radius=0.06, width=2.2, height=0.38, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#2C81FE", stroke_width=1.5)
        feedback_label_txt = CrispText("New Perception", size=11, weight=BOLD, color="#2C81FE")
        fit_into_box(feedback_label_txt, feedback_label_rect, pad_x=0.2, pad_y=0.08)
        feedback_tag = VGroup(feedback_label_rect, feedback_label_txt).move_to(feedback_path.point_from_proportion(0.5) + DOWN * 0.3)

        self.play(
            Create(feedback_path),
            FadeIn(feedback_tag, shift=UP * 0.1),
            run_time=1.2
        )

        # Solara Agent Iteration Sequence (Cycle Running "Dozens of Times")
        # Rapid kinetic pulses through the P-R-A Loop with evolving status pills
        cycle_status_rect = RoundedRectangle(corner_radius=0.08, width=3.8, height=0.5, fill_color="#0F172A", fill_opacity=1.0, stroke_color="#CBD5E1", stroke_width=1.5).move_to([0.0, 1.6, 0])
        status_texts = [
            "Cycle #01: Querying Diagnostic Sensors...",
            "Cycle #02: Evaluating Thermal Variance...",
            "Cycle #03: Deciding Next Bearing Inspection...",
            "Cycle #04: Generating Predictive Finding..."
        ]

        active_status = CrispText(status_texts[0], size=12, weight=BOLD, color="#FFFFFF").move_to(cycle_status_rect)
        self.play(FadeIn(cycle_status_rect), FadeIn(active_status), run_time=0.6)

        # Loop kinetic particle circulating along the cycle
        cycle_pts = [p_anchor, r_anchor, a_anchor, a_anchor + DOWN * 0.9, p_anchor + DOWN * 0.9, p_anchor]
        for idx in range(1, 4):
            # Pulse the hubs sequentially
            glow_p = Circle(radius=0.8, stroke_color="#F78908", stroke_width=3.5).move_to(p_anchor)
            glow_r = Circle(radius=0.8, stroke_color="#F78908", stroke_width=3.5).move_to(r_anchor)
            glow_a = Circle(radius=0.8, stroke_color="#F78908", stroke_width=3.5).move_to(a_anchor)

            next_status = CrispText(status_texts[idx], size=12, weight=BOLD, color="#FFFFFF").move_to(cycle_status_rect)
            
            self.play(
                Create(glow_p),
                Transform(active_status, next_status),
                run_time=0.6
            )
            self.play(
                ReplacementTransform(glow_p, glow_r),
                run_time=0.6
            )
            self.play(
                ReplacementTransform(glow_r, glow_a),
                run_time=0.6
            )
            self.play(FadeOut(glow_a), run_time=0.4)
            self.wait(0.5)

        # Final Convergence: Emergence of the "Final Output" Artifact
        self.play(
            FadeOut(cycle_status_rect),
            FadeOut(active_status),
            VGroup(*dispatch_mobs).animate.fade(0.2),
            VGroup(*dispatch_arrows).animate.fade(0.2),
            run_time=0.8
        )

        final_doc_rect = RoundedRectangle(corner_radius=0.1, width=3.2, height=1.6, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#8ECDB7", stroke_width=3.0).move_to([5.0, -0.4, 0])
        final_doc_hdr = CrispText("Final Deliverable", size=13, weight=BOLD, color="#0F172A")
        final_doc_b1 = CrispText("• Equipment Health: 99.4%", size=10, weight=NORMAL, color="#334155")
        final_doc_b2 = CrispText("• Bearing Service Scheduled", size=10, weight=NORMAL, color="#334155")
        final_doc_tag = CrispText("Task Complete", size=9, weight=BOLD, color="#2C81FE")
        
        doc_content = VGroup(final_doc_hdr, final_doc_b1, final_doc_b2, final_doc_tag).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(final_doc_rect)
        final_doc = VGroup(final_doc_rect, doc_content)

        final_connector = Arrow(start=a_anchor + RIGHT * 0.9, end=final_doc.get_left(), buff=0.15, color="#8ECDB7", stroke_width=3.5)

        self.play(
            GrowArrow(final_connector),
            FadeIn(final_doc, shift=RIGHT * 0.25),
            run_time=1.2
        )

        # Golden focus highlight on final output
        final_pulse = final_doc_rect.copy().set_fill(opacity=0).set_stroke(color="#F78908", width=3.5)
        self.play(Create(final_pulse), run_time=0.8)
        self.play(FadeOut(final_pulse), run_time=0.5)

        # Sync to end of Step 3
        current_time = self.renderer.time
        if current_time < t_step3_end:
            self.wait(t_step3_end - current_time)