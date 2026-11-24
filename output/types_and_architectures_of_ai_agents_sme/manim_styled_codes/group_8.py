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

try:
    from manim.utils.rate_functions import *
except Exception:
    pass

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

SME_LAYOUT = '70'


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
    """
    Scene 8: Utility-Based Agents & Workflow
    Layout Archetype: Layout 70 (70% Left Split SME Presentation)
    Safe presentation workspace: x in [-0.80, +6.40], y in [-3.50, +2.20]
    """

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





        # =========================================================================
        # PRESENTATION STEP 1: Utility-Based Agent: Optimized Trade-offs
        # Target Run Time: 109.483s
        # =========================================================================
        ## Presentation Step 1

        title_step1 = create_title(
            "Utility-Based Agent: Optimized Trade-offs",
            "Evaluating available options against efficiency, cost, and confidence"
        )
        self.play(FadeIn(title_step1, shift=DOWN * 0.15), run_time=0.9)

        # Multi-Criteria Decision Matrix Setup across x in [-1.10, 3.80]
        col_widths = [1.30, 1.00, 0.90, 1.10, 1.00]
        col_x = [-0.60, 0.50, 1.40, 2.35, 3.30]

        headers = ["Action", "Efficiency", "Cost", "Confidence", "Utility"]
        header_group = VGroup()
        for idx, (hx, name) in enumerate(zip(col_x, headers)):
            bg = RoundedRectangle(
                width=col_widths[idx], height=0.42, corner_radius=0.074,
                fill_color="#7EA2C8" if name != "Utility" else "#E6A157",
                fill_opacity=0.95, stroke_color="#CBD5E1", stroke_width=1.2
            ).move_to(np.array([hx, 1.25, 0]))
            lbl = CrispText(name, size=12, weight=BOLD, color="#FFFFFF")
            fit_into_box(lbl, bg)
            header_group.add(VGroup(bg, lbl))

        row_data = [
            ("Full Report", "0.62", "High", "0.95", "0.78"),
            ("Summary", "0.94", "Low", "0.88", "0.85"),
            ("Escalate", "0.45", "Medium", "0.82", "0.92"),
            ("Log Review", "0.85", "Low", "0.70", "0.77"),
        ]

        row_groups = VGroup()
        matrix_rows = []
        y_cursor = 0.65

        for r_idx, (act, eff, cost, conf, score) in enumerate(row_data):
            row_items = [act, eff, cost, conf, score]
            r_vgroup = VGroup()
            for c_idx, (cx, val) in enumerate(zip(col_x, row_items)):
                cell_box = RoundedRectangle(
                    width=col_widths[c_idx], height=0.46, corner_radius=0.074,
                    fill_color="#FFFFFF", fill_opacity=0.95,
                    stroke_color="#E2E8F0", stroke_width=1.0
                ).move_to(np.array([cx, y_cursor, 0]))

                val_color = "#404040" if c_idx == 0 else ("#E6A157" if c_idx == 4 else "#404040")
                val_weight = BOLD if c_idx in (0, 4) else NORMAL
                val_text = CrispText(val, size=11, weight=val_weight, color=val_color)
                fit_into_box(val_text, cell_box)
                if val_text.width > cell_box.width - 0.15:
                    if hasattr(val_text, "width") and val_text.width > (cell_box.width - 0.15): val_text.scale_to_fit_width(cell_box.width - 0.15)
                r_vgroup.add(VGroup(cell_box, val_text))

            row_groups.add(r_vgroup)
            matrix_rows.append(r_vgroup)
            y_cursor -= 0.54

        matrix_assembly = VGroup(header_group, row_groups)

        # Procedural AI Core Node positioned above table at x = 1.35, y = 2.10
        ai_core_center = np.array([1.35, 2.10, 0])
        core_outer_ring = Arc(radius=0.42, angle=2 * np.pi, color="#62B7E4", stroke_width=2.5).move_to(ai_core_center)
        core_inner_ring = Arc(radius=0.28, angle=2 * np.pi, color="#9B99C7", stroke_width=2.0).move_to(ai_core_center)
        core_hub = Dot(point=ai_core_center, radius=0.17, color="#2C81FE")
        core_lbl = CrispText("Utility AI", size=10, weight=BOLD, color="#FFFFFF").move_to(ai_core_center)
        ai_core = VGroup(core_outer_ring, core_inner_ring, core_hub, core_lbl)

        # Analytical Utility Function Spline Curve at center x = 5.00, y = 0.55
        curve_axes = Axes(
            x_range=[0, 4, 1], y_range=[0, 1.2, 0.5],
            x_length=2.0, y_length=1.1,
            axis_config={"color": "#94A3B8", "stroke_width": 1.5, "include_tip": False}
        ).move_to(np.array([5.00, 0.55, 0]))

        def utility_func(x):
            return 1.05 * np.exp(-0.45 * (x - 2.2) ** 2)

        curve_graph = curve_axes.plot(utility_func, x_range=[0.3, 3.7], color="#E6A157", stroke_width=3.0)
        peak_dot = Dot(point=curve_axes.c2p(2.2, utility_func(2.2)), radius=0.08, color="#F78908")
        curve_tag = CrispText("Utility Spline U(a)", size=11, weight=BOLD, color="#404040")
        curve_tag.next_to(curve_axes, UP, buff=0.10, aligned_edge=LEFT)
        curve_group = VGroup(curve_axes, curve_graph, peak_dot, curve_tag)

        # Dynamic Trade-off Card at x = 5.00, y = -1.25
        tradeoff_box = RoundedRectangle(
            width=2.2, height=1.20, corner_radius=0.074,
            fill_color="#FFFFFF", fill_opacity=0.95, stroke_color="#62B7E4", stroke_width=1.5
        ).move_to(np.array([5.00, -1.25, 0]))
        to_title = CrispText("Dynamic Trade-Off", size=12, weight=BOLD, color="#404040").move_to(np.array([5.00, -0.80, 0]))
        to_line1 = CrispText("Depth vs Speed", size=11, weight=NORMAL, color="#404040").move_to(np.array([5.00, -1.15, 0]))
        to_line2 = CrispText("Max Score: 0.92", size=12, weight=BOLD, color="#E6A157").move_to(np.array([5.00, -1.50, 0]))
        tradeoff_group = VGroup(tradeoff_box, to_title, to_line1, to_line2)

        # Entrance Choreography for Step 1
        self.play(FadeIn(header_group, shift=DOWN * 0.15), run_time=1.0)
        for r in row_groups:
            self.play(FadeIn(r, shift=RIGHT * 0.12), run_time=0.45)

        self.play(GrowFromCenter(ai_core), run_time=1.0)
        self.play(FadeIn(curve_group, shift=UP * 0.15), FadeIn(tradeoff_group, shift=UP * 0.15), run_time=1.2)

        # Laser Sweep Animation originates from below header row to row right edges
        eval_start = np.array([1.35, 0.95, 0])
        eval_line = Line(eval_start, matrix_rows[0].get_right(), color="#9B99C7", stroke_width=2.5)
        self.play(Create(eval_line), run_time=0.6)

        for i in range(1, 4):
            new_line = Line(eval_start, matrix_rows[i].get_right(), color="#9B99C7", stroke_width=2.5)
            self.play(ReplacementTransform(eval_line, new_line), run_time=0.55)
            eval_line = new_line

        self.play(FadeOut(eval_line), run_time=0.4)

        # Highlight Row 2 ("Escalate" - Score 0.92) with opt_badge placed RIGHT of box
        optimal_row = matrix_rows[2]
        highlight_box = RoundedRectangle(
            width=optimal_row.width + 0.14, height=optimal_row.height + 0.10, corner_radius=0.074,
            stroke_color="#F78908", stroke_width=3.0, fill_opacity=0
        ).move_to(optimal_row)

        opt_badge = create_pill("Optimal Action: Escalate", bg_color="#E6A157", text_color="#FFFFFF", font_size=11, width=2.1)
        opt_badge.next_to(highlight_box, RIGHT, buff=0.18)

        self.play(Create(highlight_box), FadeIn(opt_badge, scale=1.1), run_time=1.1)

        # Ambient Core rotation
        def rotate_rings(m, dt):
            core_outer_ring.rotate(0.35 * dt)
            core_inner_ring.rotate(-0.45 * dt)

        core_outer_ring.add_updater(rotate_rings)

        # Calculated step 1 wait budget: 109.483 - 9.65 = 99.833s
        self.wait(99.833)
        core_outer_ring.remove_updater(rotate_rings)

        # =========================================================================
        # PRESENTATION STEP 2: Complete Agent Workflow
        # Target Run Time: 42.248s
        # =========================================================================
        ## Presentation Step 2

        title_step2 = create_title(
            "Complete Agent Workflow",
            "Perception-Reason-Act Lifecycle"
        )

        step1_mobs = VGroup(matrix_assembly, ai_core, curve_group, tradeoff_group, highlight_box, opt_badge)
        
        # Sequential title crossfade per Rule 9
        self.play(FadeOut(title_step1), FadeOut(step1_mobs, shift=DOWN * 0.2), run_time=0.5)
        self.play(FadeIn(title_step2, shift=DOWN * 0.15), run_time=0.5)

        # Node Creation Helper with subtitle bounds check
        def create_workflow_node(text_title, subtitle, color_border, pos):
            box = RoundedRectangle(
                width=1.70, height=0.95, corner_radius=0.074,
                fill_color="#FFFFFF", fill_opacity=0.98,
                stroke_color=color_border, stroke_width=2.2
            ).move_to(pos)
            top_pill = RoundedRectangle(
                width=1.50, height=0.30, corner_radius=0.074,
                fill_color=color_border, fill_opacity=0.18, stroke_width=0
            ).move_to(pos + UP * 0.24)
            t_title = CrispText(text_title, size=12, weight=BOLD, color="#404040").move_to(top_pill)
            t_sub = CrispText(subtitle, size=10, weight=NORMAL, color="#404040").move_to(pos + DOWN * 0.20)
            if t_sub.width > 1.50:
                if hasattr(t_sub, "width") and t_sub.width > (1.50): t_sub.scale_to_fit_width(1.50)
            return VGroup(box, top_pill, t_title, t_sub)

        # Re-balanced Workflow Node Positions
        node_goal = create_workflow_node("Goal Input", "Arrives to Agent", "#62B7E4", np.array([-0.40, 0.50, 0]))
        node_perceive = create_workflow_node("Perceive", "Context Update", "#7EA2C8", np.array([1.60, 1.10, 0]))
        node_reason = create_workflow_node("Reason", "Plan & Evaluate", "#9B99C7", np.array([4.20, 1.10, 0]))
        node_act = create_workflow_node("Act", "Execute Action", "#E6A157", np.array([2.90, -0.80, 0]))

        # Connecting Conduits
        arr_g_to_p = Arrow(node_goal.get_top(), node_perceive.get_left(), buff=0.10, color="#62B7E4", stroke_width=2.2)
        arr_p_to_r = Arrow(node_perceive.get_right(), node_reason.get_left(), buff=0.10, color="#7EA2C8", stroke_width=2.2)
        arr_r_to_a = Arrow(node_reason.get_bottom(), node_act.get_right(), buff=0.10, color="#9B99C7", stroke_width=2.2)
        arr_a_to_p = Arrow(node_act.get_left(), node_perceive.get_bottom(), buff=0.10, color="#E6A157", stroke_width=2.2)

        # Telemetry Goal Progress Gauge (Centered vertical alignment)
        p_frame = RoundedRectangle(
            width=2.4, height=0.36, corner_radius=0.074,
            fill_color="#FFFFFF", fill_opacity=0.95, stroke_color="#CBD5E1", stroke_width=1.2
        ).move_to(np.array([2.90, 2.15, 0]))
        p_fill = RoundedRectangle(
            width=1.80, height=0.24, corner_radius=0.074,
            fill_color="#62B7E4", fill_opacity=0.9, stroke_width=0
        )
        p_fill.move_to(p_frame.get_center()).align_to(p_frame, LEFT).shift(RIGHT * 0.06)
        p_lbl = CrispText("Goal Progress: 75%", size=11, weight=BOLD, color="#404040").move_to(p_frame.get_center())
        progress_bar = VGroup(p_frame, p_fill, p_lbl)

        # Repositioned Error & Success Nodes
        error_box = RoundedRectangle(
            width=1.70, height=0.82, corner_radius=0.074,
            fill_color="#FFFFFF", fill_opacity=0.98, stroke_color="#E58F6D", stroke_width=2.0
        ).move_to(np.array([5.20, -1.80, 0]))
        err_t1 = CrispText("Error Condition", size=12, weight=BOLD, color="#404040").move_to(np.array([5.20, -1.65, 0]))
        err_t2 = CrispText("Anomaly Detected", size=10, weight=NORMAL, color="#404040").move_to(np.array([5.20, -1.95, 0]))
        node_error = VGroup(error_box, err_t1, err_t2)

        arr_error = CurvedArrow(node_reason.get_bottom(), node_error.get_top(), angle=-0.4, color="#E58F6D", stroke_width=2.2)

        achieved_box = RoundedRectangle(
            width=1.60, height=0.82, corner_radius=0.074,
            fill_color="#FFFFFF", fill_opacity=0.98, stroke_color="#8ECDB7", stroke_width=2.0
        ).move_to(np.array([0.60, -1.80, 0]))
        ach_t1 = CrispText("Goal Achieved", size=12, weight=BOLD, color="#404040").move_to(np.array([0.60, -1.65, 0]))
        ach_t2 = CrispText("Action Verified", size=10, weight=NORMAL, color="#404040").move_to(np.array([0.60, -1.95, 0]))
        node_achieved = VGroup(achieved_box, ach_t1, ach_t2)

        arr_success = CurvedArrow(node_act.get_left(), achieved_box.get_top(), angle=0.4, color="#8ECDB7", stroke_width=2.2)

        # Step 2 Animations
        self.play(FadeIn(node_goal, shift=RIGHT * 0.15), FadeIn(progress_bar, shift=DOWN * 0.1), run_time=0.9)
        self.play(Create(arr_g_to_p), FadeIn(node_perceive, shift=DOWN * 0.15), run_time=0.85)
        self.play(Create(arr_p_to_r), FadeIn(node_reason, shift=LEFT * 0.15), run_time=0.85)
        self.play(Create(arr_r_to_a), FadeIn(node_act, shift=UP * 0.15), run_time=0.85)
        self.play(Create(arr_a_to_p), run_time=0.7)

        # Animated Traveling Data Packet
        packet = Dot(radius=0.11, color="#F78908")
        packet.move_to(arr_g_to_p.get_start())
        self.add(packet)
        self.play(MoveAlongPath(packet, arr_g_to_p), run_time=0.7)
        self.play(MoveAlongPath(packet, arr_p_to_r), run_time=0.7)
        self.play(MoveAlongPath(packet, arr_r_to_a), run_time=0.7)
        self.play(MoveAlongPath(packet, arr_a_to_p), run_time=0.7)

        # Progress update on second cycle
        new_fill = RoundedRectangle(
            width=2.25, height=0.24, corner_radius=0.074,
            fill_color="#62B7E4", fill_opacity=0.9, stroke_width=0
        )
        new_fill.move_to(p_frame.get_center()).align_to(p_frame, LEFT).shift(RIGHT * 0.06)
        new_lbl = CrispText("Goal Progress: 100%", size=11, weight=BOLD, color="#404040").move_to(p_frame.get_center())

        self.play(
            MoveAlongPath(packet, arr_p_to_r),
            Transform(p_fill, new_fill),
            Transform(p_lbl, new_lbl),
            run_time=0.8
        )
        self.play(MoveAlongPath(packet, arr_r_to_a), run_time=0.7)
        self.remove(packet)

        self.play(Create(arr_error), FadeIn(node_error, shift=UP * 0.15), run_time=0.9)
        self.play(Create(arr_success), FadeIn(node_achieved, shift=UP * 0.15), run_time=0.9)

        # Calculated step 2 wait budget: 42.248 - 11.30 = 30.948s
        self.wait(30.948)

        # =========================================================================
        # PRESENTATION STEP 3: Responsible Handoff
        # Target Run Time: 31.330s
        # =========================================================================
        ## Presentation Step 3

        title_step3 = create_title(
            "Responsible Handoff",
            "Escalation when confidence limits are reached"
        )

        # Sequential title crossfade per Rule 9
        self.play(FadeOut(title_step2), run_time=0.35)
        self.play(FadeIn(title_step3, shift=DOWN * 0.1), run_time=0.45)

        # Step Boundary Cleanup: FadeOut transient Step 2 components
        self.play(
            FadeOut(progress_bar), FadeOut(arr_a_to_p), FadeOut(arr_p_to_r),
            FadeOut(node_goal), FadeOut(arr_g_to_p),
            FadeOut(node_achieved), FadeOut(arr_success),
            FadeOut(node_error), FadeOut(arr_error),
            run_time=0.7
        )

        # Confidence Gauge relocated to x = 5.20, y = 0.60
        gauge_center = np.array([5.20, 0.60, 0])
        gauge_bg = RoundedRectangle(
            width=2.10, height=1.25, corner_radius=0.074,
            fill_color="#FFFFFF", fill_opacity=0.98,
            stroke_color="#E58F6D", stroke_width=1.8
        ).move_to(gauge_center)
        self.remove(*[m for m in self.mobjects if not getattr(m, 'is_title', False) and getattr(m, 'name', '') != 'title_group' and not getattr(m, 'is_persistent', False)])

        gauge_arc = Arc(radius=0.40, start_angle=0, angle=np.pi, color="#CBD5E1", stroke_width=3.5).move_to(gauge_center + UP * 0.08)
        needle = Line(gauge_center + UP * 0.08, gauge_center + UP * 0.26 + LEFT * 0.26, color="#E58F6D", stroke_width=2.8)
        gauge_title = CrispText("Confidence Gauge", size=11, weight=BOLD, color="#404040").move_to(gauge_center + UP * 0.42)
        gauge_val = CrispText("Confidence: Low", size=11, weight=BOLD, color="#E58F6D").move_to(gauge_center + DOWN * 0.38)
        confidence_gauge = VGroup(gauge_bg, gauge_arc, needle, gauge_title, gauge_val)

        # Vector Human Engineer Receiving Station at x = 4.80, y = -1.85 (width 2.60 plinth)
        eng_center = np.array([4.80, -1.85, 0])
        eng_plinth = RoundedRectangle(
            width=2.60, height=1.40, corner_radius=0.074,
            fill_color="#FFFFFF", fill_opacity=0.98,
            stroke_color="#8ECDB7", stroke_width=2.2
        ).move_to(eng_center)

        glyph_center = eng_center + LEFT * 0.70
        hard_hat = Arc(radius=0.20, angle=np.pi, color="#DDB945", stroke_width=3.0).move_to(glyph_center + UP * 0.10)
        hat_brim = Line(glyph_center + UP * 0.10 + LEFT * 0.22, glyph_center + UP * 0.10 + RIGHT * 0.22, color="#DDB945", stroke_width=2.2)
        face_circle = Circle(radius=0.13, color="#404040", stroke_width=1.6).move_to(glyph_center)
        shoulders = Arc(radius=0.26, angle=np.pi, color="#404040", stroke_width=1.8).move_to(glyph_center + DOWN * 0.20)
        engineer_glyph = VGroup(face_circle, hard_hat, hat_brim, shoulders)

        eng_lbl1 = CrispText("Human Engineer", size=11, weight=BOLD, color="#404040")
        eng_lbl2 = CrispText("Solara Operations", size=10, weight=NORMAL, color="#404040")
        eng_status = CrispText("Expert In The Loop", size=10, weight=BOLD, color="#8ECDB7")

        labels_grp = VGroup(eng_lbl1, eng_lbl2, eng_status).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        labels_grp.move_to(eng_center + RIGHT * 0.35)

        human_engineer_station = VGroup(eng_plinth, engineer_glyph, labels_grp)

        # Curved Handoff Conduit with angle=-0.35 sweeping cleanly around node_act
        handoff_path = CurvedArrow(
            node_reason.get_bottom(),
            human_engineer_station.get_top(),
            angle=-0.35, color="#8ECDB7", stroke_width=3.0
        )

        # Handoff Badge positioned at x = 4.10, y = -0.85
        handoff_pill = RoundedRectangle(
            width=1.80, height=0.34, corner_radius=0.074,
            fill_color="#8ECDB7", fill_opacity=0.95, stroke_width=0
        )
        handoff_tag = CrispText("Responsible Handoff", size=11, weight=BOLD, color="#FFFFFF").move_to(handoff_pill)
        handoff_badge = VGroup(handoff_pill, handoff_tag).move_to(np.array([4.10, -0.85, 0])).set_z_index(20)

        # Step 3 Entrance Sequence
        self.play(FadeIn(confidence_gauge, shift=RIGHT * 0.15), run_time=0.9)
        self.play(Create(handoff_path), FadeIn(handoff_badge, scale=1.1), run_time=1.1)
        self.play(FadeIn(human_engineer_station, shift=UP * 0.15), run_time=1.0)

        # Telemetry Packet Flow along Handoff Path
        anomaly_packet = Dot(radius=0.13, color="#F78908").move_to(node_reason.get_bottom())
        self.add(anomaly_packet)
        self.play(MoveAlongPath(anomaly_packet, handoff_path), run_time=1.2)
        self.remove(anomaly_packet)

        # Station Pulse Highlight
        pulse_highlight = eng_plinth.copy().set_fill(opacity=0).set_stroke(color="#F78908", width=3.0)
        self.play(Create(pulse_highlight), run_time=0.7)
        self.play(FadeOut(pulse_highlight), run_time=0.5)

        # Calculated step 3 wait budget: 31.330 - 6.90 = 24.430s
        self.wait(24.430)