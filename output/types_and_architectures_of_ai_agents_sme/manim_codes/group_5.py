C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_WHITE = "#FFFFFF"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
SME_LAYOUT = '70'
C_TEXT = "#404040"
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
try:
    from manim.utils.rate_functions import *
except Exception:
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
    def sync_to(self, target_time):
        current_time = getattr(getattr(self, 'renderer', None), 'time', 0.0)
        if target_time > current_time:
            self.wait(target_time - current_time)

    def construct(self):
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



        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        # Approved Color Palette
        C_SKY_BLUE = "#62B7E4"
        C_STEEL_BLUE = "#7EA2C8"
        C_SEAFOAM = "#8ECDB7"
        C_AMBER = "#E6A157"
        C_CORAL = "#E58F6D"
        C_TEXT_DARK = "#404040"
        C_TEXT_MUTED = "#555555"
        C_CARD_BG = "#FFFFFF"
        C_ORANGE_HIGHLIGHT = "#F78908"
        C_GRAY_PASSIVE = "#64748B"
        C_GRAY_LIGHT = "#E2E8F0"

        # Standard Header Factory (Centered at 0.0, 2.90, 0)
        def create_header(title_str, subtitle_str):
            title = CrispText(title_str, size=28, weight=BOLD, color=C_TEXT_DARK)
            subtitle = CrispText(subtitle_str, size=18, weight=SEMIBOLD, color=C_TEXT_MUTED)
            header_grp = VGroup(title, subtitle).arrange(DOWN, aligned_edge=ORIGIN, buff=0.12)
            header_grp.move_to(np.array([0.0, 2.90, 0]))
            return header_grp

        # =========================================================
        ## Presentation Step 1: Agent-Environment Interaction Loop (0.00s -> 5.68s)
        # =========================================================

        # [0.00s] "That loop is what we call agent environment interaction."
        self.sync_to(0.00)
        header_group = create_header("Agent-Environment Interaction", "Continuous Loop Architecture")
        
        center_1 = np.array([0.0, -0.55, 0])

        # 1. Environment Outer Boundary Ring
        env_ring_outer = DashedVMobject(
            Circle(radius=2.40, stroke_color=C_STEEL_BLUE, stroke_width=2.0),
            num_dashes=36,
            dashed_ratio=0.55
        ).move_to(center_1)

        env_ring_pulse = Circle(
            radius=2.46,
            stroke_color=C_SKY_BLUE,
            stroke_width=1.8,
            fill_opacity=0.04,
            fill_color=C_SKY_BLUE
        ).move_to(center_1)

        env_badge = VGroup(
            RoundedRectangle(width=1.9, height=0.44, corner_radius=0.10, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_STEEL_BLUE, stroke_width=1.6),
            CrispText("Environment", size=15, weight=BOLD, color=C_TEXT_MUTED)
        ).move_to(center_1 + UP * 1.95).set_z_index(15)

        # 2. Central Memory Core Node
        mem_card = RoundedRectangle(width=1.85, height=1.15, corner_radius=0.10, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_STEEL_BLUE, stroke_width=2.0).move_to(center_1)
        db_tier1 = Ellipse(width=0.52, height=0.14, fill_color=C_STEEL_BLUE, fill_opacity=0.35, stroke_color=C_STEEL_BLUE, stroke_width=1.5).move_to(center_1 + UP * 0.22)
        db_tier2 = Ellipse(width=0.52, height=0.14, fill_color=C_STEEL_BLUE, fill_opacity=0.55, stroke_color=C_STEEL_BLUE, stroke_width=1.5).move_to(center_1 + UP * 0.10)
        db_tier3 = Ellipse(width=0.52, height=0.14, fill_color=C_STEEL_BLUE, fill_opacity=0.85, stroke_color=C_STEEL_BLUE, stroke_width=1.5).move_to(center_1 - UP * 0.02)
        db_icon = VGroup(db_tier1, db_tier2, db_tier3)
        mem_label = CrispText("Memory", size=16, weight=BOLD, color=C_TEXT_DARK).move_to(center_1 + DOWN * 0.28)
        mem_group = VGroup(mem_card, db_icon, mem_label).set_z_index(10)

        # 3. Flow Nodes Definition
        pos_perceive = center_1 + UP * 1.25
        pos_reason = center_1 + RIGHT * 1.60 + DOWN * 0.25
        pos_act = center_1 + LEFT * 1.60 + DOWN * 0.25

        def create_flow_node(title_str, color_accent, position, icon_type="radar"):
            bg = RoundedRectangle(width=1.85, height=0.82, corner_radius=0.10, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=color_accent, stroke_width=2.2)
            if icon_type == "radar":
                ic1 = Arc(radius=0.18, angle=PI, stroke_color=color_accent, stroke_width=2.0)
                ic2 = Dot(radius=0.04, color=color_accent).move_to(ic1.get_bottom())
                icon = VGroup(ic1, ic2).scale(0.85)
            elif icon_type == "gear":
                c = Circle(radius=0.14, stroke_color=color_accent, stroke_width=2.0)
                teeth = VGroup(*[Line(UP * 0.14, UP * 0.20, stroke_color=color_accent, stroke_width=2.0).rotate(a, about_point=ORIGIN) for a in np.linspace(0, TAU, 6, endpoint=False)])
                icon = VGroup(c, teeth).scale(0.85)
            else:
                dot_c = Dot(radius=0.06, color=color_accent)
                ring = Circle(radius=0.15, stroke_color=color_accent, stroke_width=1.5)
                icon = VGroup(ring, dot_c).scale(0.85)

            title = CrispText(title_str, size=16, weight=BOLD, color=C_TEXT_DARK)
            content = VGroup(icon, title).arrange(RIGHT, buff=0.12)
            node = VGroup(bg, content).move_to(position).set_z_index(12)
            return node

        node_perceive = create_flow_node("Perception", C_SKY_BLUE, pos_perceive, "radar")
        node_reason = create_flow_node("Reasoning", C_AMBER, pos_reason, "brain")
        node_act = create_flow_node("Action", C_SEAFOAM, pos_act, "gear")

        start_mem = np.array([mem_card.get_right()[0], center_1[1] - 0.15, 0])
        end_reason = np.array([node_reason.get_left()[0], center_1[1] - 0.15, 0])
        mem_link = DoubleArrow(
            start_mem,
            end_reason,
            stroke_color=C_STEEL_BLUE,
            stroke_width=2.0,
            tip_length=0.12,
            buff=0.08
        ).set_z_index(8)
        link_label = CrispText("State & Knowledge", size=14, weight=SEMIBOLD, color=C_TEXT_MUTED)
        link_label.next_to(mem_link, UP, buff=0.06)
        link_label.set_y(center_1[1] + 0.02)

        arrow_p_to_r = CurvedArrow(
            node_perceive.get_right() + DOWN * 0.05,
            node_reason.get_top() + LEFT * 0.05,
            angle=-0.4,
            stroke_color=C_SKY_BLUE,
            stroke_width=2.8,
            tip_length=0.18
        )
        arrow_r_to_a = CurvedArrow(
            node_reason.get_bottom() + LEFT * 0.05,
            node_act.get_bottom() + RIGHT * 0.05,
            angle=-0.4,
            stroke_color=C_AMBER,
            stroke_width=2.8,
            tip_length=0.18
        )
        arrow_a_to_p = CurvedArrow(
            node_act.get_top() + RIGHT * 0.05,
            node_perceive.get_left() + DOWN * 0.05,
            angle=-0.4,
            stroke_color=C_SEAFOAM,
            stroke_width=2.8,
            tip_length=0.18
        )
        loop_badge = VGroup(
            RoundedRectangle(width=1.7, height=0.42, corner_radius=0.08, fill_color="#F8FAFC", fill_opacity=0.95, stroke_color=C_CORAL, stroke_width=1.8),
            CrispText("Agent Loop", size=15, weight=BOLD, color=C_CORAL)
        ).move_to(center_1 + DOWN * 1.35).set_z_index(14)

        particle_1 = Dot(radius=0.08, color=C_ORANGE_HIGHLIGHT).move_to(arrow_p_to_r.get_start())
        particle_2 = Dot(radius=0.08, color=C_SKY_BLUE).move_to(arrow_r_to_a.get_start())
        particle_3 = Dot(radius=0.08, color=C_SEAFOAM).move_to(arrow_a_to_p.get_start())

        self.play(
            FadeIn(header_group, shift=DOWN * 0.15),
            Create(env_ring_outer),
            FadeIn(env_ring_pulse),
            FadeIn(env_badge, shift=DOWN * 0.1),
            GrowFromCenter(mem_group),
            FadeIn(node_perceive, shift=DOWN * 0.15),
            FadeIn(node_reason, shift=LEFT * 0.15),
            FadeIn(node_act, shift=RIGHT * 0.15),
            Create(mem_link),
            FadeIn(link_label),
            Create(arrow_p_to_r),
            Create(arrow_r_to_a),
            Create(arrow_a_to_p),
            FadeIn(loop_badge, shift=UP * 0.1),
            run_time=2.2
        )

        self.play(
            FadeIn(particle_1),
            FadeIn(particle_2),
            FadeIn(particle_3),
            MoveAlongPath(particle_1, arrow_p_to_r, rate_func=linear),
            MoveAlongPath(particle_2, arrow_r_to_a, rate_func=linear),
            MoveAlongPath(particle_3, arrow_a_to_p, rate_func=linear),
            run_time=2.0
        )
        self.remove(particle_1, particle_2, particle_3)

        agent_loop_all = VGroup(
            env_ring_outer, env_ring_pulse, env_badge,
            mem_group, node_perceive, node_reason, node_act,
            arrow_p_to_r, arrow_r_to_a, arrow_a_to_p,
            mem_link, link_label, loop_badge
        )

        # =========================================================
        ## Presentation Step 2: Agent vs. Static Tool (5.68s -> 27.50s)
        # =========================================================

        # [5.68s] "And it's worth understanding because it's what separates an agent from a static tool."
        self.sync_to(13.10)
        new_header_group = create_header("Static Tool vs. AI Agent", "Passive Response vs. Autonomous Loop")
        target_agent_center = np.array([2.50, -0.40, 0])
        shift_vector = target_agent_center - center_1

        divider_line = DashedLine(
            np.array([0.0, 1.65, 0]),
            np.array([0.0, -2.75, 0]),
            stroke_color=C_GRAY_LIGHT,
            stroke_width=1.8,
            dash_length=0.14
        )

        agent_col_badge = VGroup(
            RoundedRectangle(width=2.7, height=0.52, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_SKY_BLUE, stroke_width=2.0),
            CrispText("AI Agent: Autonomous", size=16, weight=BOLD, color=C_TEXT_DARK)
        ).move_to(np.array([2.50, 1.50, 0]))

        agent_status_text = CrispText("Autonomous\nInteraction Loop", size=15, weight=SEMIBOLD, color=C_TEXT_DARK, align="center")
        agent_status_bg = RoundedRectangle(width=2.8, height=0.76, corner_radius=0.07, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_SEAFOAM, stroke_width=1.5)
        fit_into_box(agent_status_text, agent_status_bg, pad_x=0.2, pad_y=0.08)
        agent_status_tag = VGroup(agent_status_bg, agent_status_text).move_to(np.array([2.50, -2.40, 0]))

        tool_col_badge = VGroup(
            RoundedRectangle(width=2.7, height=0.52, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_GRAY_PASSIVE, stroke_width=2.0),
            CrispText("Static Tool: Passive", size=16, weight=BOLD, color=C_GRAY_PASSIVE)
        ).move_to(np.array([-2.50, 1.50, 0]))

        user_input_card = RoundedRectangle(width=1.4, height=0.75, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_GRAY_PASSIVE, stroke_width=1.8).move_to(np.array([-4.10, -0.40, 0]))
        user_text = CrispText("User\nInput", size=15, weight=BOLD, color=C_TEXT_DARK, align="center").move_to(user_input_card)
        fit_into_box(user_text, user_input_card, pad_x=0.2, pad_y=0.08)
        user_input_grp = VGroup(user_input_card, user_text)

        tool_body_rect = RoundedRectangle(
            width=1.65,
            height=1.05,
            corner_radius=0.09,
            fill_color="#F8FAFC",
            fill_opacity=1.0,
            stroke_color=C_GRAY_PASSIVE,
            stroke_width=2.0
        ).move_to(np.array([-2.35, -0.40, 0]))

        tool_icon_wrench = VGroup(
            Line(DL * 0.12, UR * 0.12, stroke_color=C_GRAY_PASSIVE, stroke_width=2.5),
            Circle(radius=0.08, stroke_color=C_GRAY_PASSIVE, stroke_width=1.8).move_to(UR * 0.12)
        ).scale(0.85).move_to(np.array([-2.35, -0.16, 0]))

        tool_name = CrispText("Static Tool", size=16, weight=BOLD, color=C_TEXT_DARK).next_to(tool_icon_wrench, DOWN, buff=0.06)
        cursor_txt = CrispText("Idle _", size=14, weight=SEMIBOLD, color=C_GRAY_PASSIVE).next_to(tool_name, DOWN, buff=0.04)
        tool_body_grp = VGroup(tool_body_rect, tool_icon_wrench, tool_name, cursor_txt)

        self.play(
            FadeOut(header_group),
            FadeIn(new_header_group, shift=DOWN * 0.1),
            agent_loop_all.animate.scale(0.62, about_point=center_1).shift(shift_vector),
            Create(divider_line),
            FadeIn(agent_col_badge, shift=DOWN * 0.1),
            FadeIn(agent_status_tag, shift=UP * 0.1),
            FadeIn(tool_col_badge, shift=DOWN * 0.1),
            FadeIn(user_input_grp, shift=RIGHT * 0.1),
            FadeIn(tool_body_grp, shift=RIGHT * 0.1),
            run_time=2.4
        )
        header_group = new_header_group

        # [12.56s] "A static tool waits to be asked. An agent operates within an environment."
        self.sync_to(20.86)
        arrow_tool_in = Arrow(
            np.array([-3.40, -0.40, 0]),
            np.array([-3.10, -0.40, 0]),
            buff=0.05,
            stroke_color=C_GRAY_PASSIVE,
            stroke_width=2.2,
            tip_length=0.14
        )
        tool_status_text = CrispText("Waits for\nDirect Command", size=15, weight=SEMIBOLD, color=C_GRAY_PASSIVE, align="center")
        tool_status_bg = RoundedRectangle(width=2.8, height=0.76, corner_radius=0.07, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_GRAY_PASSIVE, stroke_width=1.5)
        fit_into_box(tool_status_text, tool_status_bg, pad_x=0.2, pad_y=0.08)
        tool_status_tag = VGroup(tool_status_bg, tool_status_text).move_to(np.array([-2.50, -2.40, 0]))

        self.play(
            Create(arrow_tool_in),
            FadeIn(tool_status_tag, shift=UP * 0.1),
            tool_body_rect.animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=3.0),
            agent_col_badge[0].animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=3.5),
            env_ring_pulse.animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=2.5, opacity=0.9),
            run_time=1.8
        )
        self.play(
            tool_body_rect.animate.set_stroke(color=C_GRAY_PASSIVE, width=2.0),
            agent_col_badge[0].animate.set_stroke(color=C_SKY_BLUE, width=2.0),
            env_ring_pulse.animate.set_stroke(color=C_SKY_BLUE, width=1.8, opacity=0.3),
            run_time=1.2
        )

        # [18.30s] "It observes what's happening, decides what action is appropriate, and executes."
        self.sync_to(28.64)
        particle_agent = Dot(radius=0.07, color=C_ORANGE_HIGHLIGHT).move_to(arrow_p_to_r.get_start())
        self.add(particle_agent)
        
        # Perception highlight -> Observes
        self.play(
            node_perceive[0].animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=3.5),
            MoveAlongPath(particle_agent, arrow_p_to_r, rate_func=smooth),
            run_time=1.4
        )
        node_perceive[0].set_stroke(color=C_SKY_BLUE, width=2.2)

        # Reasoning highlight -> Decides
        self.play(
            node_reason[0].animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=3.5),
            MoveAlongPath(particle_agent, arrow_r_to_a, rate_func=smooth),
            run_time=1.4
        )
        node_reason[0].set_stroke(color=C_AMBER, width=2.2)

        # Action highlight -> Executes
        self.play(
            node_act[0].animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=3.5),
            run_time=0.9
        )
        node_act[0].set_stroke(color=C_SEAFOAM, width=2.2)

        # [23.74s] "Then it checks the result, and decides what comes next."
        self.sync_to(33.18)
        arrow_tool_out = Arrow(
            np.array([-1.55, -0.40, 0]),
            np.array([-1.25, -0.40, 0]),
            buff=0.0,
            stroke_color=C_GRAY_PASSIVE,
            stroke_width=2.2,
            tip_length=0.14
        )
        tool_result_rect = RoundedRectangle(width=1.45, height=0.75, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_GRAY_LIGHT, stroke_width=1.5).move_to(np.array([-0.55, -0.40, 0]))
        tool_result_text = CrispText("Result\n(Halts)", size=15, weight=SEMIBOLD, color=C_GRAY_PASSIVE, align="center").move_to(tool_result_rect)
        fit_into_box(tool_result_text, tool_result_rect, pad_x=0.2, pad_y=0.08)
        tool_result_grp = VGroup(tool_result_rect, tool_result_text)

        self.play(
            Create(arrow_tool_out),
            FadeIn(tool_result_grp, shift=RIGHT * 0.1),
            MoveAlongPath(particle_agent, arrow_a_to_p, rate_func=smooth),
            run_time=1.8
        )
        self.remove(particle_agent)

        # =========================================================
        ## Presentation Step 3: Real-World Case: Solara Grid Telemetry (28.70s -> 55.00s)
        # =========================================================

        # [28.70s] "At Solara, an agent monitoring grid performance isn't just waiting for someone to run a report."
        self.sync_to(39.72)
        solara_header = create_header("Solara Grid Telemetry", "Autonomous Performance Monitoring")
        
        solara_badge = VGroup(
            RoundedRectangle(width=2.8, height=0.52, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_SKY_BLUE, stroke_width=2.0),
            CrispText("Solara Grid Telemetry: Site 12", size=15, weight=BOLD, color=C_TEXT_DARK)
        ).move_to(np.array([0.0, 1.85, 0])).set_z_index(22)

        telemetry_card = RoundedRectangle(width=2.8, height=0.76, corner_radius=0.08, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_SKY_BLUE, stroke_width=1.8).move_to(np.array([-3.2, 0.20, 0]))
        telemetry_txt = CrispText("Site 12 Telemetry\nPower: 94.2 kW (Normal)", size=14, weight=SEMIBOLD, color=C_TEXT_DARK, align="center").move_to(telemetry_card)
        fit_into_box(telemetry_txt, telemetry_card, pad_x=0.2, pad_y=0.08)
        telemetry_grp = VGroup(telemetry_card, telemetry_txt).set_z_index(20)

        self.play(
            FadeOut(header_group),
            FadeIn(solara_header, shift=DOWN * 0.1),
            FadeOut(tool_col_badge),
            FadeOut(user_input_grp),
            FadeOut(tool_body_grp),
            FadeOut(arrow_tool_in),
            FadeOut(tool_status_tag),
            FadeOut(arrow_tool_out),
            FadeOut(tool_result_grp),
            FadeOut(divider_line),
            FadeOut(agent_col_badge),
            FadeOut(agent_status_tag),
            agent_loop_all.animate.scale(1.0 / 0.62, about_point=target_agent_center).move_to(np.array([1.20, -0.45, 0])),
            FadeIn(solara_badge, shift=DOWN * 0.1),
            FadeIn(telemetry_grp, shift=RIGHT * 0.1),
            run_time=2.4
        )
        header_group = solara_header

        # [35.88s] "It's watching. When output at a site drops below threshold, it observes the deviation,"
        self.sync_to(47.68)
        radar_ping = Circle(radius=0.35, stroke_color=C_SKY_BLUE, stroke_width=2.5).move_to(node_perceive.get_center())
        
        telemetry_alert_card = RoundedRectangle(width=2.8, height=0.76, corner_radius=0.08, fill_color="#FEF2F2", fill_opacity=1.0, stroke_color=C_CORAL, stroke_width=2.0).move_to(np.array([-3.2, 0.20, 0]))
        telemetry_alert_txt = CrispText("Site 12 Anomaly\nOutput: 78.4 kW (-16.8%)", size=14, weight=BOLD, color=C_CORAL, align="center").move_to(telemetry_alert_card)
        fit_into_box(telemetry_alert_txt, telemetry_alert_card, pad_x=0.2, pad_y=0.08)
        telemetry_alert_grp = VGroup(telemetry_alert_card, telemetry_alert_txt).set_z_index(21)

        self.play(
            radar_ping.animate.scale(2.2).set_stroke(opacity=0),
            node_perceive[0].animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=3.5),
            Transform(telemetry_grp, telemetry_alert_grp),
            run_time=2.0
        )
        self.remove(radar_ping)
        node_perceive[0].set_stroke(color=C_SKY_BLUE, width=2.2)

        # Word sync: Observes deviation and transfers into reasoning
        particle_solara = Dot(radius=0.08, color=C_ORANGE_HIGHLIGHT).move_to(arrow_p_to_r.get_start())
        self.add(particle_solara)
        self.play(
            MoveAlongPath(particle_solara, arrow_p_to_r, rate_func=smooth),
            node_reason[0].animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=3.5),
            run_time=1.8
        )
        node_reason[0].set_stroke(color=C_AMBER, width=2.2)

        # [44.08s] "decides the appropriate response, which might be querying historical data,"
        self.sync_to(55.06)
        hist_query_card = RoundedRectangle(width=2.8, height=0.68, corner_radius=0.08, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color=C_STEEL_BLUE, stroke_width=1.6).move_to(np.array([-3.2, -0.85, 0]))
        hist_query_txt = CrispText("Historical Query\nPast 30-Day Irradiance", size=13, weight=SEMIBOLD, color=C_TEXT_DARK, align="center").move_to(hist_query_card)
        fit_into_box(hist_query_txt, hist_query_card, pad_x=0.2, pad_y=0.08)
        hist_grp = VGroup(hist_query_card, hist_query_txt).set_z_index(20)

        self.play(
            mem_card.animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=3.5),
            mem_link.animate.set_color(C_ORANGE_HIGHLIGHT),
            FadeIn(hist_grp, shift=UP * 0.1),
            run_time=1.6
        )
        self.play(
            mem_card.animate.set_stroke(color=C_STEEL_BLUE, width=2.0),
            mem_link.animate.set_color(C_STEEL_BLUE),
            run_time=1.0
        )

        # [49.14s] "cross-referencing weather records, or escalating to a human operator, and takes that action."
        self.sync_to(62.16)
        action_card1 = RoundedRectangle(width=2.8, height=0.68, corner_radius=0.08, fill_color="#ECFDF5", fill_opacity=1.0, stroke_color=C_SEAFOAM, stroke_width=1.6).move_to(np.array([-3.2, -1.80, 0]))
        action_txt1 = CrispText("Weather Sync: Clear\nInverter Fault Flagged", size=13, weight=SEMIBOLD, color=C_TEXT_DARK, align="center").move_to(action_card1)
        fit_into_box(action_txt1, action_card1, pad_x=0.2, pad_y=0.08)
        action_grp1 = VGroup(action_card1, action_txt1).set_z_index(20)

        action_card2 = RoundedRectangle(width=2.8, height=0.68, corner_radius=0.08, fill_color="#FFFBEB", fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=1.8).move_to(np.array([-3.2, -2.65, 0]))
        action_txt2 = CrispText("Escalation Dispatched\nSite Engineer Notified", size=13, weight=BOLD, color=C_TEXT_DARK, align="center").move_to(action_card2)
        fit_into_box(action_txt2, action_card2, pad_x=0.2, pad_y=0.08)
        action_grp2 = VGroup(action_card2, action_txt2).set_z_index(20)

        self.play(
            MoveAlongPath(particle_solara, arrow_r_to_a, rate_func=smooth),
            node_act[0].animate.set_stroke(color=C_ORANGE_HIGHLIGHT, width=3.5),
            FadeIn(action_grp1, shift=LEFT * 0.1),
            FadeIn(action_grp2, shift=UP * 0.1),
            run_time=2.2
        )
        self.remove(particle_solara)
        node_act[0].set_stroke(color=C_SEAFOAM, width=2.2)

        # Hold visual scene for full spoken duration matching total audio duration
        
        # [69.30s] "The environment shapes the agent. The agent shapes the environment."
        self.sync_to(69.30)
        reciprocal_banner = VGroup(
            RoundedRectangle(width=8.2, height=0.62, corner_radius=0.12, fill_color="#0F172A", fill_opacity=0.95, stroke_color=C_ORANGE_HIGHLIGHT, stroke_width=2.0),
            CrispText("The environment shapes the agent. The agent shapes the environment.", size=14, weight=BOLD, color="#FFFFFF")
        ).move_to(np.array([0.0, -3.2, 0])).set_z_index(30)

        loop_glow = Circle(radius=1.8, stroke_color=C_ORANGE_HIGHLIGHT, stroke_width=4.0).move_to(np.array([1.20, -0.45, 0]))

        self.play(
            FadeIn(reciprocal_banner, shift=UP * 0.15),
            Create(loop_glow),
            run_time=1.8
        )
        self.play(FadeOut(loop_glow), run_time=1.0)

        # Hold visual scene for full spoken duration matching total audio duration
        self.sync_to(74.00)

