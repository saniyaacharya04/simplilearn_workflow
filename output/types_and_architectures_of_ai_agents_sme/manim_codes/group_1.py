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
import numpy as np
SME_LAYOUT = '100'
from feedback_functions.instrumented_scene import InstrumentedScene
import os
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

# Pre-defined helpers and base class stubs for compatibility

class InstrumentedScene(Scene):
    def current_time(self):
        return getattr(self, "_current_time", 0.0)

    def sync_to(self, target_time):
        dt = target_time - self.renderer.time
        if dt > 0:
            self.wait(dt)





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
        # 1. Canvas Background Setup (OSL 3.0 Standard)
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















        ## Presentation Step 1
        # Step Title: Agent: Beyond Response
        # Duration: 48.68s
        # Concept: AI Agent is an active system that perceives and acts upon the environment continuously.

        # --- Header Creation ---
        title_group = create_title("AI Agent: The Active System", "Agent: Beyond Response")
        self.play(FadeIn(title_group, shift=DOWN * 0.15), run_time=0.8)

        # --- Ambient Kinetic Environment Grid ---
        grid_lines = VGroup()
        for x in range(-6, 7, 2):
            line = DashedLine(
                start=[x, -3.2, 0],
                end=[x, 2.2, 0],
                dash_length=0.1,
                dashed_ratio=0.5,
                stroke_color="#7EA2C8",
                stroke_opacity=0.18,
                stroke_width=1.2,
            )
            grid_lines.add(line)
        for y in range(-3, 3, 1):
            line = DashedLine(
                start=[-6.2, y, 0],
                end=[6.2, y, 0],
                dash_length=0.1,
                dashed_ratio=0.5,
                stroke_color="#7EA2C8",
                stroke_opacity=0.18,
                stroke_width=1.2,
            )
            grid_lines.add(line)

        # Environment Boundary Rings (Concentric Sensing Zones)
        env_rings = VGroup()
        for r in [2.0, 2.8, 3.6]:
            env_ring = Circle(radius=r, stroke_color="#8ECDB7", stroke_opacity=0.22, stroke_width=1.5)
            env_rings.add(env_ring)

        env_label_top = CrispText("Environment Sensing Sphere", size=13, weight=BOLD, color="#7EA2C8")
        env_label_top.move_to([0, 2.15, 0])

        self.play(
            FadeIn(grid_lines, run_time=1.0),
            FadeIn(env_rings, run_time=1.2),
            FadeIn(env_label_top, run_time=0.8),
        )

        # --- Multi-Faceted Living AI Agent Core ---
        # Outer pulsating aura
        core_aura = Circle(radius=1.35, stroke_color="#62B7E4", stroke_width=2.5, stroke_opacity=0.45)
        core_aura.set_fill("#62B7E4", opacity=0.06)

        # Middle rotating gear/dendrite ring
        core_ring_outer = DashedVMobject(
            Circle(radius=1.05, stroke_color="#2C81FE", stroke_width=2.5),
            num_dashes=18,
            dashed_ratio=0.6,
        )

        # Inner faceted polygon
        core_hex = RegularPolygon(n=8, radius=0.75, stroke_color="#62B7E4", stroke_width=2.5)
        core_hex.set_fill("#FFFFFF", opacity=0.92)

        # Inner Glowing Processor Core
        core_inner_glow = Circle(radius=0.45, stroke_color="#E6A157", stroke_width=2.0)
        core_inner_glow.set_fill("#E6A157", opacity=0.25)

        # Central Chip Symbol / Node
        chip_box = Square(side_length=0.38, stroke_color="#0F172A", stroke_width=2.0, fill_color="#F8FAFC", fill_opacity=1.0)
        chip_cross_h = Line([-0.12, 0, 0], [0.12, 0, 0], stroke_color="#62B7E4", stroke_width=2)
        chip_cross_v = Line([0, -0.12, 0], [0, 0.12, 0], stroke_color="#62B7E4", stroke_width=2)
        chip_glyph = VGroup(chip_box, chip_cross_h, chip_cross_v)

        core_group = VGroup(core_aura, core_ring_outer, core_hex, core_inner_glow, chip_glyph)
        core_group.move_to([0, -0.3, 0])

        # Core Label Pill
        core_tag_bg = RoundedRectangle(corner_radius=0.1, width=1.9, height=0.42, stroke_color="#62B7E4", stroke_width=1.5, fill_color="#FFFFFF", fill_opacity=0.95)
        core_tag_text = CrispText("AI Agent Core", size=14, weight=BOLD, color="#0F172A")
        fit_into_box(core_tag_text, core_tag_bg, pad_x=0.2, pad_y=0.08)
        core_tag = VGroup(core_tag_bg, core_tag_text).move_to([0, -1.35, 0])

        # Status Badge: Autonomous Action Engine
        sub_badge_bg = RoundedRectangle(corner_radius=0.08, width=2.4, height=0.34, stroke_color="#8ECDB7", stroke_width=1.2, fill_color="#F8FAFC", fill_opacity=0.9)
        sub_badge_txt = CrispText("Active Decision Loop", size=12, weight=SEMIBOLD, color="#404040")
        fit_into_box(sub_badge_txt, sub_badge_bg, pad_x=0.2, pad_y=0.08)
        sub_badge = VGroup(sub_badge_bg, sub_badge_txt).next_to(core_tag, DOWN, buff=0.14)

        # Optional Hero illustration asset if provided
        img_path = "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_1_solara_plant.png"
        hero_asset = None
        if os.path.exists(img_path):
            try:
                raw_img = ImageMobject(img_path)
                raw_img.scale_to_fit_height(1.8)
                raw_img.move_to([4.2, -0.3, 0])
                hero_tag_bg = RoundedRectangle(corner_radius=0.08, width=2.2, height=0.38, stroke_color="#7EA2C8", stroke_width=1.2, fill_color="#FFFFFF", fill_opacity=0.9)
                hero_tag_txt = CrispText("Real-World Context", size=12, weight=BOLD, color="#0F172A")
                fit_into_box(hero_tag_txt, hero_tag_bg, pad_x=0.2, pad_y=0.08)
                hero_tag = VGroup(hero_tag_bg, hero_tag_txt).next_to(raw_img, DOWN, buff=0.15)
                hero_asset = Group(raw_img, hero_tag)
            except Exception:
                hero_asset = None

        # Build entry animation for AI core
        self.play(
            GrowFromCenter(core_aura),
            GrowFromCenter(core_hex),
            FadeIn(core_ring_outer),
            FadeIn(core_inner_glow),
            FadeIn(chip_glyph),
            run_time=1.4,
        )
        self.play(
            FadeIn(core_tag, shift=UP * 0.1),
            FadeIn(sub_badge, shift=UP * 0.1),
            run_time=0.8,
        )
        if hero_asset:
            self.play(FadeIn(hero_asset, shift=LEFT * 0.2), run_time=1.0)

        # --- Dynamic Telemetry Conduits & Dual Flow Vectors ---
        # Left Inflow Conduit: Perception & Sensor Ingestion (Continuous data flowing INTO core)
        inflow_path_1 = CurvedArrow(start_point=[-4.8, 0.9, 0], end_point=[-1.2, 0.2, 0], angle=-0.35, color="#62B7E4")
        inflow_path_2 = CurvedArrow(start_point=[-4.8, -1.5, 0], end_point=[-1.2, -0.6, 0], angle=0.35, color="#7EA2C8")

        inflow_badge_bg = RoundedRectangle(corner_radius=0.08, width=2.2, height=0.45, stroke_color="#62B7E4", stroke_width=1.5, fill_color="#FFFFFF", fill_opacity=0.95)
        inflow_badge_txt = CrispText("1. Continuous Sensing", size=13, weight=BOLD, color="#0F172A")
        fit_into_box(inflow_badge_txt, inflow_badge_bg, pad_x=0.2, pad_y=0.08)
        inflow_badge = VGroup(inflow_badge_bg, inflow_badge_txt).move_to([-4.4, 1.45, 0])

        # Right Outflow Conduit: Autonomous Action Execution (Action signals flowing OUT of core)
        outflow_path_1 = CurvedArrow(start_point=[1.2, 0.2, 0], end_point=[4.8, 0.9, 0], angle=0.35, color="#E6A157")
        outflow_path_2 = CurvedArrow(start_point=[1.2, -0.6, 0], end_point=[4.8, -1.5, 0], angle=-0.35, color="#E58F6D")

        outflow_badge_bg = RoundedRectangle(corner_radius=0.08, width=2.2, height=0.45, stroke_color="#E6A157", stroke_width=1.5, fill_color="#FFFFFF", fill_opacity=0.95)
        outflow_badge_txt = CrispText("2. Proactive Action", size=13, weight=BOLD, color="#0F172A")
        fit_into_box(outflow_badge_txt, outflow_badge_bg, pad_x=0.2, pad_y=0.08)
        outflow_badge = VGroup(outflow_badge_bg, outflow_badge_txt).move_to([4.4 if not hero_asset else 3.8, 1.45, 0])

        self.play(
            Create(inflow_path_1),
            Create(inflow_path_2),
            FadeIn(inflow_badge, shift=RIGHT * 0.15),
            run_time=1.2,
        )
        self.play(
            Create(outflow_path_1),
            Create(outflow_path_2),
            FadeIn(outflow_badge, shift=LEFT * 0.15),
            run_time=1.2,
        )

        # --- Continuous Updaters for Living Kinetic Motion ---
        # 1. Continuous rotation of core rings
        core_ring_outer.add_updater(lambda m, dt: m.rotate(0.35 * dt))
        core_hex.add_updater(lambda m, dt: m.rotate(-0.15 * dt))

        # 2. Pulsing aura breathing updater
        pulse_tracker = ValueTracker(1.0)
        def aura_updater(m):
            scale_val = 1.0 + 0.08 * np.sin(pulse_tracker.get_value() * 3.0)
            m.set_stroke(opacity=0.35 + 0.15 * np.cos(pulse_tracker.get_value() * 3.0))
        core_aura.add_updater(aura_updater)

        # Update tracker continuously during animations
        self.add(pulse_tracker)
        pulse_tracker.add_updater(lambda m, dt: m.increment_value(dt))

        # --- Flowing Data Packets & Action Pulses ---
        # Data Packet Stream: Ingestion (Left to Center)
        p1 = Dot(point=[-4.8, 0.9, 0], radius=0.09, color="#62B7E4").set_z_index(30)
        p2 = Dot(point=[-4.8, -1.5, 0], radius=0.09, color="#7EA2C8").set_z_index(30)

        # Action Packet Stream: Execution (Center to Right)
        a1 = Dot(point=[1.2, 0.2, 0], radius=0.10, color="#F78908").set_z_index(30)
        a2 = Dot(point=[1.2, -0.6, 0], radius=0.10, color="#E6A157").set_z_index(30)

        # Focus Highlight on Active System Core
        core_highlight = core_hex.copy().set_fill(opacity=0).set_stroke(color="#F78908", width=3.5)
        self.play(Create(core_highlight), run_time=0.9)

        # Orchestrated Flow Cycles to match ~48s narration
        # Packet cycle 1
        self.play(
            MoveAlongPath(p1, inflow_path_1, rate_func=linear, run_time=1.8),
            MoveAlongPath(p2, inflow_path_2, rate_func=linear, run_time=1.8),
        )
        self.remove(p1, p2)

        # Core processes and responds proactively
        self.play(
            core_inner_glow.animate.set_fill("#F78908", opacity=0.5),
            run_time=0.8,
        )
        self.play(
            MoveAlongPath(a1, outflow_path_1, rate_func=smooth, run_time=1.8),
            MoveAlongPath(a2, outflow_path_2, rate_func=smooth, run_time=1.8),
            core_inner_glow.animate.set_fill("#E6A157", opacity=0.25),
        )
        self.remove(a1, a2)
        self.play(FadeOut(core_highlight), run_time=0.6)

        # Informative Cognitive Sub-Card: The Agent Paradigm
        card_bg = RoundedRectangle(corner_radius=0.1, width=6.2, height=0.85, stroke_color="#8ECDB7", stroke_width=1.5, fill_color="#FFFFFF", fill_opacity=0.96)
        card_title = CrispText("Dynamic Closed-Loop Behavior", size=14, weight=BOLD, color="#0F172A")
        card_desc = CrispText("Perceives environmental state, reasons internally, and triggers deliberate impact.", size=12, weight=NORMAL, color="#334155")
        card_group = VGroup(card_title, card_desc).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        full_card = VGroup(card_bg, card_group).move_to([0, -2.55, 0])
        fit_into_box(card_group, card_bg)

        self.play(FadeIn(full_card, shift=UP * 0.15), run_time=1.0)

        # Packet cycle 2 & 3: Sustained dynamic circulation across remaining narration duration
        for _ in range(3):
            p1_loop = Dot(point=[-4.8, 0.9, 0], radius=0.08, color="#62B7E4").set_z_index(30)
            p2_loop = Dot(point=[-4.8, -1.5, 0], radius=0.08, color="#7EA2C8").set_z_index(30)
            a1_loop = Dot(point=[1.2, 0.2, 0], radius=0.09, color="#F78908").set_z_index(30)
            a2_loop = Dot(point=[1.2, -0.6, 0], radius=0.09, color="#E58F6D").set_z_index(30)

            self.play(
                MoveAlongPath(p1_loop, inflow_path_1, rate_func=linear, run_time=2.2),
                MoveAlongPath(p2_loop, inflow_path_2, rate_func=linear, run_time=2.2),
            )
            self.remove(p1_loop, p2_loop)

            self.play(
                MoveAlongPath(a1_loop, outflow_path_1, rate_func=smooth, run_time=2.2),
                MoveAlongPath(a2_loop, outflow_path_2, rate_func=smooth, run_time=2.2),
            )
            self.remove(a1_loop, a2_loop)

        # Smooth synchronization to the allocated presentation step boundary
        self.sync_to(48.68)