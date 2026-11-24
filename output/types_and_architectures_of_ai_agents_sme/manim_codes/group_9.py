import re
import numpy as np
SME_LAYOUT = '70'
from feedback_functions.instrumented_scene import InstrumentedScene
import os
import math
from manim import *
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

NumberLine.c2p = lambda self, *args: self.n2p(args[0])
try:
    from manim.utils.rate_functions import *
except Exception:
    pass

# Fallback base class if InstrumentedScene is not provided in global scope
try:
    InstrumentedScene
except NameError:
    class InstrumentedScene(Scene):
        def sync_to(self, target_time):
            current_time = self.renderer.time
            wait_time = target_time - current_time
            if wait_time > 0.001:
                self.wait(wait_time)

# High-fidelity text wrapper with Open Sans default


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

class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        # 1. Base Setup: Modern Soft Light Slate Canvas
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

        
        # Color Palette (Approved 10-Pastel & OSL 3.0 Tokens)
        C_TITLE = "#0F172A"       # Dark Slate for Titles
        C_BODY = "#334155"        # Slate for Body Text
        C_CHARCOAL = "#404040"    # Primary Charcoal
        C_MUTED = "#64748B"       # Muted Slate
        C_HIGHLIGHT = "#F78908"   # Warm Orange Accent / Spotlight
        C_BLUE = "#2C81FE"        # Brand Blue Accent
        C_SKY = "#62B7E4"         # Pastel Sky Blue
        C_STEEL = "#7EA2C8"       # Pastel Steel Blue
        C_MINT = "#8ECDB7"        # Pastel Mint Seafoam
        C_AMBER = "#E6A157"       # Pastel Warm Amber
        C_CORAL = "#E58F6D"       # Pastel Coral Peach
        C_PURPLE = "#9B99C7"      # Pastel Lavender Periwinkle
        C_CARD_BG = "#FFFFFF"     # Crisp White Container Fill
        C_CARD_BORDER = "#E2E8F0" # Soft Container Border

        # Safe Workspace Center for Layout 70 (x ∈ [-0.80, 6.40])
        # Center x ≈ 2.80
        CX = 2.80

        # Helper: Create Left-Anchored Header for Layout 70
        def create_header(title_str, subtitle_str=""):
            title_mob = CrispText(title_str, size=26, weight=BOLD, color=C_TITLE)
            grp = VGroup(title_mob)
            if subtitle_str:
                sub_mob = CrispText(subtitle_str, size=16, weight=SEMIBOLD, color=C_BLUE)
                sub_mob.next_to(title_mob, DOWN, buff=0.14, aligned_edge=LEFT)
                grp.add(sub_mob)
            grp.move_to(np.array([-0.80 + grp.width / 2.0, 3.0, 0]))
            return grp

        # =========================================================================
        ## Presentation Step 1: Key Takeaways
        # Narration Duration: ~82.845s
        # =========================================================================
        header_step1 = create_header("Summary & What's Next", "Key Takeaways")
        self.play(FadeIn(header_step1, shift=DOWN * 0.1), run_time=0.8)

        # -------------------------------------------------------------------------
        # Section 1: Components Mini-Loop (Perception, Memory, Reasoning, Action)
        # -------------------------------------------------------------------------
        sec1_header = CrispText("1. Core Agent Components", size=15, weight=BOLD, color=C_TITLE)
        sec1_header.move_to(np.array([CX, 2.05, 0]))
        self.play(FadeIn(sec1_header, shift=UP * 0.1), run_time=0.6)

        # Build 4 interactive nodes arranged in a balanced quad
        quad_cx, quad_cy = CX, 0.95
        dx, dy = 1.9, 0.65
        
        comp_data = [
            ("Perception", C_SKY, [-dx, dy, 0]),
            ("Memory", C_PURPLE, [dx, dy, 0]),
            ("Reasoning", C_AMBER, [dx, -dy, 0]),
            ("Action", C_CORAL, [-dx, -dy, 0]),
        ]
        
        comp_nodes = VGroup()
        for name, color, offset in comp_data:
            node_bg = RoundedRectangle(
                width=1.65, height=0.55, corner_radius=0.12,
                fill_color=C_CARD_BG, fill_opacity=1.0,
                stroke_color=color, stroke_width=2.0
            )
            node_txt = CrispText(name, size=13, weight=BOLD, color=C_CHARCOAL)
            fit_into_box(node_txt, node_bg, pad_x=0.2, pad_y=0.08)
            node_grp = VGroup(node_bg, node_txt).move_to(np.array([quad_cx + offset[0], quad_cy + offset[1], 0]))
            comp_nodes.add(node_grp)

        # Directed loop arrows connecting the 4 nodes
        arr_config = {"stroke_color": C_MUTED, "stroke_width": 2, "buff": 0.08, "max_tip_length_to_length_ratio": 0.25}
        a1 = Arrow(comp_nodes[0].get_right(), comp_nodes[1].get_left(), **arr_config)
        a2 = Arrow(comp_nodes[1].get_bottom(), comp_nodes[2].get_top(), **arr_config)
        a3 = Arrow(comp_nodes[2].get_left(), comp_nodes[3].get_right(), **arr_config)
        a4 = Arrow(comp_nodes[3].get_top(), comp_nodes[0].get_bottom(), **arr_config)
        comp_arrows = VGroup(a1, a2, a3, a4)

        # Mini rotating radar accent at the center of the components loop
        core_hub = Dot(point=[quad_cx, quad_cy, 0], radius=0.14, color=C_BLUE, fill_opacity=0.3)
        core_ring = Circle(radius=0.32, stroke_color=C_BLUE, stroke_width=1.5, stroke_opacity=0.6).move_to(core_hub)
        core_pulse = Circle(radius=0.48, stroke_color=C_SKY, stroke_width=1.0, stroke_opacity=0.3).move_to(core_hub)
        loop_hub_grp = VGroup(core_hub, core_ring, core_pulse)

        self.play(
            LaggedStart(
                FadeIn(comp_arrows),
                FadeIn(loop_hub_grp),
                *[FadeIn(node, shift=UP * 0.05) for node in comp_nodes],
                lag_ratio=0.15
            ),
            run_time=2.2
        )

        # Pulse highlight on Component Nodes in sync with narration
        pulse_box = RoundedRectangle(
            width=1.75, height=0.65, corner_radius=0.14,
            fill_opacity=0, stroke_color=C_HIGHLIGHT, stroke_width=3.5
        )
        for node in comp_nodes:
            pulse_box.move_to(node)
            self.play(Create(pulse_box), run_time=0.4)
            self.play(FadeOut(pulse_box), run_time=0.3)

        # -------------------------------------------------------------------------
        # Section 2: Agent-Environment Interaction Cycle (Observe -> Decide -> Act)
        # -------------------------------------------------------------------------
        sec2_header = CrispText("2. Continuous Interaction Loop", size=15, weight=BOLD, color=C_TITLE)
        sec2_header.move_to(np.array([CX, -0.05, 0]))
        self.play(FadeIn(sec2_header, shift=UP * 0.1), run_time=0.6)

        cycle_y = -0.75
        stages_data = [
            ("Observe", C_SKY),
            ("Decide", C_AMBER),
            ("Act", C_CORAL),
            ("Observe Again", C_STEEL)
        ]
        
        cycle_pills = VGroup()
        for idx, (txt, pcolor) in enumerate(stages_data):
            p_bg = RoundedRectangle(
                width=1.55, height=0.48, corner_radius=0.24,
                fill_color=C_CARD_BG, fill_opacity=1.0,
                stroke_color=pcolor, stroke_width=2.0
            )
            p_txt = CrispText(txt, size=12, weight=BOLD, color=C_CHARCOAL)
            cycle_pills.add(VGroup(p_bg, p_txt))
        
        cycle_pills.arrange(RIGHT, buff=0.38).move_to(np.array([CX, cycle_y, 0]))

        # Dynamic conduits connecting the loop
        cycle_conduits = VGroup()
        for i in range(len(cycle_pills) - 1):
            arr = Arrow(
                cycle_pills[i].get_right(), cycle_pills[i+1].get_left(),
                stroke_color=C_MUTED, stroke_width=2, buff=0.06, max_tip_length_to_length_ratio=0.25
            )
            cycle_conduits.add(arr)

        # Feedback curved loop back to start
        return_curve = CurvedArrow(
            cycle_pills[-1].get_bottom() + DOWN * 0.05,
            cycle_pills[0].get_bottom() + DOWN * 0.05,
            angle=-0.45, stroke_color=C_BLUE, stroke_width=2, stroke_opacity=0.8
        )
        return_label = CrispText("Feedback Stream", size=11, weight=SEMIBOLD, color=C_BLUE)
        return_label.next_to(return_curve, DOWN, buff=0.08)

        self.play(
            LaggedStart(
                *[FadeIn(p, shift=RIGHT * 0.1) for p in cycle_pills],
                FadeIn(cycle_conduits),
                Create(return_curve),
                FadeIn(return_label),
                lag_ratio=0.15
            ),
            run_time=2.5
        )

        # Flowing active particle across the loop
        flow_dot = Dot(color=C_HIGHLIGHT, radius=0.09).set_z_index(30)
        flow_path = VMobject()
        flow_path.set_points_as_corners([
            cycle_pills[0].get_center(),
            cycle_pills[1].get_center(),
            cycle_pills[2].get_center(),
            cycle_pills[3].get_center(),
        ])
        self.play(MoveAlongPath(flow_dot, flow_path), run_time=1.8, rate_func=linear)
        self.play(MoveAlongPath(flow_dot, return_curve), run_time=1.2, rate_func=smooth)
        self.remove(flow_dot)

        # -------------------------------------------------------------------------
        # Section 3: Agent Archetypes Spectrum (Reactive, Goal-Based, Utility-Based)
        # -------------------------------------------------------------------------
        sec3_header = CrispText("3. Agent Sophistication Spectrum", size=15, weight=BOLD, color=C_TITLE)
        sec3_header.move_to(np.array([CX, -1.65, 0]))
        self.play(FadeIn(sec3_header, shift=UP * 0.1), run_time=0.6)

        archetypes_data = [
            ("Reactive", "Rule-Driven", C_STEEL, "Fast heuristics"),
            ("Goal-Based", "Outcome-Focused", C_MINT, "Proactive plans"),
            ("Utility-Based", "Optimized", C_AMBER, "Trade-off solver")
        ]

        cards_y = -2.55
        arch_cards = VGroup()
        for title, tag, accent_col, desc in archetypes_data:
            c_bg = RoundedRectangle(
                width=2.1, height=1.1, corner_radius=0.12,
                fill_color=C_CARD_BG, fill_opacity=1.0,
                stroke_color=accent_col, stroke_width=2.0
            )
            c_title = CrispText(title, size=13, weight=BOLD, color=C_TITLE)
            c_tag_bg = RoundedRectangle(
                width=1.8, height=0.3, corner_radius=0.15,
                fill_color=accent_col, fill_opacity=0.2, stroke_width=0
            )
            c_tag_txt = CrispText(f"[{tag}]", size=11, weight=BOLD, color=C_CHARCOAL)
            fit_into_box(c_tag_txt, c_tag_bg, pad_x=0.2, pad_y=0.08)
            c_tag = VGroup(c_tag_bg, c_tag_txt)
            c_desc = CrispText(desc, size=11, weight=NORMAL, color=C_BODY)
            
            content = VGroup(c_title, c_tag, c_desc).arrange(DOWN, buff=0.08)
            fit_into_box(content, c_bg)
            arch_cards.add(VGroup(c_bg, content))

        arch_cards.arrange(RIGHT, buff=0.3).move_to(np.array([CX, cards_y, 0]))

        # Progression gradient line underneath indicating sophistication growth
        prog_arrow = Arrow(
            arch_cards[0].get_corner(DL) + DOWN * 0.18,
            arch_cards[2].get_corner(DR) + DOWN * 0.18,
            stroke_color=C_BLUE, stroke_width=2.5, buff=0, max_tip_length_to_length_ratio=0.15
        )
        prog_label = CrispText("Increasing Cognitive Complexity", size=11, weight=SEMIBOLD, color=C_BLUE)
        prog_label.next_to(prog_arrow, DOWN, buff=0.08)

        self.play(
            LaggedStart(
                *[FadeIn(card, shift=UP * 0.15) for card in arch_cards],
                GrowArrow(prog_arrow),
                FadeIn(prog_label),
                lag_ratio=0.2
            ),
            run_time=2.8
        )

        # Highlight each archetype as described in narration
        highlight_rect = RoundedRectangle(
            width=2.2, height=1.2, corner_radius=0.14,
            fill_opacity=0, stroke_color=C_HIGHLIGHT, stroke_width=3.5
        )
        for card in arch_cards:
            highlight_rect.move_to(card)
            self.play(Create(highlight_rect), run_time=0.6)
            self.play(FadeOut(highlight_rect), run_time=0.4)

        # Group all Step 1 content for clean morph
        step1_content = VGroup(
            sec1_header, comp_nodes, comp_arrows, loop_hub_grp,
            sec2_header, cycle_pills, cycle_conduits, return_curve, return_label,
            sec3_header, arch_cards, prog_arrow, prog_label
        )

        # Narration alignment for Step 1 (~82.8s)
        self.wait(1.5)

        # =========================================================================
        ## Presentation Step 2: What's Next: Hands-On Demo
        # Narration Duration: ~23.315s
        # =========================================================================
        header_step2 = create_header("Summary & What's Next", "Hands-On Demo: AI Agent Architectures in Action")
        
        self.play(
            FadeOut(step1_content, shift=LEFT * 0.3),
            ReplacementTransform(header_step1, header_step2),
            run_time=1.0
        )

        # Hero Banner for the Hands-On Demo
        banner_w = 6.9
        banner_h = 4.7
        banner_center = np.array([CX, -0.65, 0])

        banner_bg = RoundedRectangle(
            width=banner_w, height=banner_h, corner_radius=0.18,
            fill_color=C_CARD_BG, fill_opacity=1.0,
            stroke_color=C_BLUE, stroke_width=2.0
        ).move_to(banner_center)

        # Header bar inside banner
        banner_title_bar = RoundedRectangle(
            width=banner_w - 0.2, height=0.55, corner_radius=0.10,
            fill_color="#F8FAFC", fill_opacity=1.0,
            stroke_color=C_CARD_BORDER, stroke_width=1.0
        ).move_to(banner_bg.get_top() + DOWN * 0.38)

        # Live Demo Badge
        live_badge_bg = RoundedRectangle(
            width=1.45, height=0.36, corner_radius=0.18,
            fill_color=C_HIGHLIGHT, fill_opacity=0.18,
            stroke_color=C_HIGHLIGHT, stroke_width=1.5
        )
        live_dot = Dot(radius=0.06, color=C_HIGHLIGHT)
        live_txt = CrispText("Live Demo", size=12, weight=BOLD, color=C_HIGHLIGHT)
        live_badge = VGroup(live_badge_bg, live_dot, live_txt)
        live_dot.move_to(live_badge_bg.get_left() + RIGHT * 0.22)
        live_txt.move_to(live_badge_bg.get_center() + RIGHT * 0.12)
        live_badge.move_to(banner_title_bar.get_left() + RIGHT * 0.95)

        banner_label = CrispText("Interactive Simulation Lab", size=13, weight=BOLD, color=C_TITLE)
        banner_label.move_to(banner_title_bar.get_center() + RIGHT * 0.6)

        # Load transparent hero illustration asset if present
        img_path = "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_9_demo_lab.png"
        hero_illustration = None
        if os.path.exists(img_path):
            img_mob = ImageMobject(img_path)
            img_mob.scale_to_fit_height(2.3)
            if img_mob.width > banner_w - 0.8:
                img_mob.scale_to_fit_width(banner_w - 0.8)
            img_mob.move_to(banner_center + DOWN * 0.1)
            hero_illustration = Group(img_mob)
        else:
            # Procedural fallback simulation terminal window
            term_bg = RoundedRectangle(
                width=banner_w - 0.8, height=2.3, corner_radius=0.12,
                fill_color="#0F172A", fill_opacity=0.95,
                stroke_color="#334155", stroke_width=1.5
            ).move_to(banner_center + DOWN * 0.1)
            
            line1 = CrispText("> Initializing Agent Execution Runtime...", size=11, font="Courier", weight=NORMAL, color="#38BDF8")
            line2 = CrispText("> Instantiating Perception Sensor Pipelines [Active]", size=11, font="Courier", weight=NORMAL, color="#8ECDB7")
            line3 = CrispText("> Dynamic Utility Optimization Loop: Converged (0.98)", size=11, font="Courier", weight=NORMAL, color="#F78908")
            line4 = CrispText("> Executing Next Autonomous Action Cycle...", size=11, font="Courier", weight=NORMAL, color="#E2E8F0")
            
            term_lines = VGroup(line1, line2, line3, line4).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
            term_lines.move_to(term_bg.get_center())
            hero_illustration = Group(term_bg, term_lines)

        # Bottom Call-To-Action Pill with animated Play Glyph
        cta_bg = RoundedRectangle(
            width=3.6, height=0.55, corner_radius=0.28,
            fill_color=C_BLUE, fill_opacity=1.0,
            stroke_color="#1D4ED8", stroke_width=1.5
        )
        play_poly = RegularPolygon(n=3, radius=0.14, color="#FFFFFF", fill_opacity=1.0).rotate(-PI / 2)
        cta_txt = CrispText("Launch Real-Time Lab", size=13, weight=BOLD, color="#FFFFFF")
        cta_grp = VGroup(cta_bg, play_poly, cta_txt)
        play_poly.move_to(cta_bg.get_left() + RIGHT * 0.35)
        cta_txt.move_to(cta_bg.get_center() + RIGHT * 0.18)
        cta_grp.move_to(banner_bg.get_bottom() + UP * 0.52)

        # Assemble Banner Container
        self.play(
            FadeIn(banner_bg, shift=UP * 0.2),
            FadeIn(banner_title_bar),
            FadeIn(live_badge),
            FadeIn(banner_label),
            run_time=1.2
        )
        
        self.play(FadeIn(hero_illustration, shift=UP * 0.1), run_time=1.0)
        self.play(GrowFromCenter(cta_grp), run_time=0.8)

        # Ambient gentle pulse on the hero banner CTA
        pulse_cta = cta_bg.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(Create(pulse_cta), run_time=0.6)
        self.play(FadeOut(pulse_cta), run_time=0.5)

        # Final hold to naturally conclude step narration (~23.3s total)
        self.wait(2.0)