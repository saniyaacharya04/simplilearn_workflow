C_LIGHT_BLUE = "#62B7E4"
C_RED = "#E58F6D"
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

try:
    from manim.utils.rate_functions import *
except Exception:
    pass








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

NumberLine.c2p = lambda self, *args: self.n2p(args[0])

# Colors
C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_CORAL = "#E58F6D"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_WHITE = "#FFFFFF"
C_BLACK = "#404040"
C_HIGHLIGHT = "#F78908"
SME_LAYOUT = '20'










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
def create_datum_bay(center_x, width=3.6, top_y=1.6, bot_y=-2.8):
    top_line = Line([center_x - width/2, top_y, 0], [center_x + width/2, top_y, 0], color="#CBD5E1", stroke_width=1.5)
    bot_line = Line([center_x - width/2, bot_y, 0], [center_x + width/2, bot_y, 0], color="#CBD5E1", stroke_width=1.5)
    ticks = VGroup()
    for lx in [center_x - width/2, center_x, center_x + width/2]:
        ticks.add(Line([lx, top_y - 0.08, 0], [lx, top_y + 0.08, 0], color="#94A3B8", stroke_width=1.5))
        ticks.add(Line([lx, bot_y - 0.08, 0], [lx, bot_y + 0.08, 0], color="#94A3B8", stroke_width=1.5))
    return VGroup(top_line, bot_line, ticks)


class FinalScene(MovingCameraScene):
    def sync_to(self, target_time):
        curr_t = getattr(getattr(self, 'renderer', None), 'time', 0.0)
        if target_time > curr_t:
            self.wait(target_time - curr_t)

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
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)














        # =========================================================================
        ## Presentation Step 1
        # =========================================================================

        # [0.00s -> 4.14s] Title & Central Architecture Concept
        self.sync_to(0.00)
        main_title = create_title("Autonomous Decision Models")
        step_title1 = CrispText("Overview: Types of Autonomous Agents", size=15, font="Open Sans", weight=SEMIBOLD, color="#64748B")
        step_title1.next_to(main_title, DOWN, buff=0.12, aligned_edge=LEFT)

        dist_bg = RoundedRectangle(
            width=3.6, height=0.56, corner_radius=0.14,
            fill_color="#F1F5F9", fill_opacity=1.0, stroke_color="#7EA2C8", stroke_width=1.8
        ).move_to([0.0, 2.10, 0])
        dist_txt = CrispText("Autonomous Decision Models", size=14, weight=BOLD, color="#0F172A").move_to(dist_bg)
        fit_into_box(dist_txt, dist_bg, pad_x=0.2, pad_y=0.08)
        dist_node = VGroup(dist_bg, dist_txt).set_z_index(10)

        self.play(
            FadeIn(main_title, shift=DOWN * 0.1),
            FadeIn(step_title1, shift=DOWN * 0.1),
            FadeIn(dist_node, shift=DOWN * 0.15),
            run_time=1.0
        )

        # [4.74s -> 7.84s] Branching conduits and Datum Bays
        self.sync_to(2.00)
        bay1_datum = create_datum_bay(-4.2)
        bay2_datum = create_datum_bay(0.0)
        bay3_datum = create_datum_bay(4.2)

        cond1 = CubicBezier([0, 1.84, 0], [-1.5, 1.84, 0], [-3.0, 1.6, 0], [-4.2, 1.6, 0], color="#7EA2C8", stroke_width=2.0)
        cond2 = Line([0, 1.84, 0], [0, 1.6, 0], color="#7EA2C8", stroke_width=2.0)
        cond3 = CubicBezier([0, 1.84, 0], [1.5, 1.84, 0], [3.0, 1.6, 0], [4.2, 1.6, 0], color="#7EA2C8", stroke_width=2.0)
        conduits = VGroup(cond1, cond2, cond3)

        self.play(
            Create(conduits),
            Create(bay1_datum),
            Create(bay2_datum),
            Create(bay3_datum),
            run_time=1.4
        )

        # [8.26s -> 17.72s] Reveal Three Core Agent Models with focus on Utility Optimization
        self.sync_to(3.50)
        badge1 = create_pill("Reactive Model", bg_color="#62B7E4", font_size=13).move_to([-4.2, 1.35, 0])
        badge2 = create_pill("Goal-Based Architecture", bg_color="#7EA2C8", font_size=13).move_to([0.0, 1.35, 0])
        badge3 = create_pill("Utility-Based Optimization", bg_color="#9B99C7", font_size=13).move_to([4.2, 1.35, 0])
        bay_badges = VGroup(badge1, badge2, badge3)
        self.play(FadeIn(bay_badges, shift=DOWN * 0.1), run_time=1.0)

        # In-place highlight when speaking "most efficiently... lowest cost"
        self.sync_to(4.20)
        self.play(
            badge3.animate.set_stroke(color=C_HIGHLIGHT, width=3.0),
            run_time=0.45
        )
        self.play(
            badge3.animate.set_stroke(color=C_STEEL_BLUE, width=0),
            run_time=0.45
        )

        # [18.60s -> 27.36s] Utility Agent managing trade-offs at Solara
        self.sync_to(4.40)
        pulse_intro = Dot(color="#2C81FE", radius=0.08).move_to(dist_bg.get_bottom())
        self.play(FadeIn(pulse_intro), run_time=0.2)
        self.play(MoveAlongPath(pulse_intro, cond3, rate_func=linear), run_time=1.6)
        self.play(FadeOut(pulse_intro), run_time=0.3)

        # [27.36s -> 34.30s] Trade-Off decisions: Diagnostic report vs summary
        self.sync_to(4.50)
        tradeoff_pill = create_pill("Trade-Off: Cost vs Precision", bg_color="#9B99C7", font_size=11).move_to([4.2, 0.40, 0])
        self.play(FadeIn(tradeoff_pill, shift=UP * 0.1), run_time=0.6)

        # [34.30s -> 39.76s] Evaluating options against utility function
        self.sync_to(4.58)
        utility_fn_pill = create_pill("Maximize Utility U(x)", bg_color="#2C81FE", font_size=11).move_to([4.2, -0.20, 0])
        self.play(FadeIn(utility_fn_pill, shift=UP * 0.1), run_time=0.6)

        # [39.76s -> 44.14s] Zoom out across all three models and frame Reactive Agent
        self.sync_to(4.65)
        p1 = Dot(color="#2C81FE", radius=0.08).move_to(dist_bg.get_bottom())
        p2 = Dot(color="#2C81FE", radius=0.08).move_to(dist_bg.get_bottom())
        p3 = Dot(color="#2C81FE", radius=0.08).move_to(dist_bg.get_bottom())
        self.play(
            MoveAlongPath(p1, cond1, rate_func=linear),
            MoveAlongPath(p2, cond2, rate_func=linear),
            MoveAlongPath(p3, cond3, rate_func=linear),
            FadeOut(tradeoff_pill),
            FadeOut(utility_fn_pill),
            run_time=1.5
        )
        self.play(FadeOut(p1), FadeOut(p2), FadeOut(p3), run_time=0.3)

        reactive_focus = RoundedRectangle(
            width=3.6, height=4.1, corner_radius=0.18,
            fill_color="#62B7E4", fill_opacity=0.05, stroke_color=C_HIGHLIGHT, stroke_width=2.4
        ).move_to([-4.2, -0.6, 0])
        self.play(Create(reactive_focus), run_time=0.7)

        # =========================================================================
        ## Presentation Step 2
        # =========================================================================

        # [2.1] 44.49s -> 48.04s The first type is the reactive agent
        self.sync_to(4.68)
        step_title2 = CrispText("Reactive Agent: Rule-Driven", size=15, font="Open Sans", weight=SEMIBOLD, color="#64748B")
        step_title2.next_to(main_title, DOWN, buff=0.12, aligned_edge=LEFT)

        self.play(
            FadeOut(step_title1),
            FadeIn(step_title2, shift=DOWN * 0.1),
            FadeOut(reactive_focus),
            bay2_datum.animate.set_opacity(0.60),
            bay3_datum.animate.set_opacity(0.60),
            badge2.animate.set_opacity(0.60),
            badge3.animate.set_opacity(0.60),
            bay1_datum.animate.set_opacity(1.0),
            badge1.animate.set_opacity(1.0),
            run_time=0.7
        )

        # [2.2] 48.19s -> 53.77s Responds to current input using predefined rules
        self.sync_to(10.68)
        sensor_box = Circle(radius=0.36, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#62B7E4", stroke_width=2.0).move_to([-5.30, -0.35, 0])
        wave = ParametricFunction(lambda t: np.array([t, 0.10 * np.sin(5 * np.pi * t), 0]), t_range=[-0.20, 0.20], color="#62B7E4", stroke_width=2.0).move_to(sensor_box.get_center())
        sensor_icon = VGroup(sensor_box, wave)

        rule_box = Circle(radius=0.36, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#7EA2C8", stroke_width=2.0).move_to([-4.20, -0.35, 0])
        gear_center = rule_box.get_center()
        gear_teeth = VGroup(*[
            Square(side_length=0.08, fill_color="#7EA2C8", fill_opacity=1.0, stroke_width=0).move_to(gear_center + 0.32 * np.array([np.cos(a), np.sin(a), 0]))
            for a in np.linspace(0, 2*np.pi, 8, endpoint=False)
        ])
        gear_inner = Circle(radius=0.18, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#7EA2C8", stroke_width=1.5).move_to(gear_center)
        switch_lever = Line(gear_center + LEFT*0.10 + DOWN*0.06, gear_center + RIGHT*0.10 + UP*0.06, color=C_HIGHLIGHT, stroke_width=2.5)
        rule_icon = VGroup(gear_teeth, rule_box, gear_inner, switch_lever)

        dispatch_box = Circle(radius=0.36, fill_color="#FEF3C7", fill_opacity=1.0, stroke_color="#E6A157", stroke_width=2.0).move_to([-3.10, -0.35, 0])
        beacon = Triangle(color="#E55353", fill_color="#E55353", fill_opacity=0.85).scale(0.16).move_to(dispatch_box.get_center())
        dispatch_icon = VGroup(dispatch_box, beacon)

        arr_rx1 = Arrow(sensor_box.get_right(), rule_box.get_left(), buff=0.04, stroke_width=2.5, max_tip_length_to_length_ratio=0.25, color="#62B7E4")
        arr_rx2 = Arrow(rule_box.get_right(), dispatch_box.get_left(), buff=0.04, stroke_width=2.5, max_tip_length_to_length_ratio=0.25, color="#E6A157")
        rx_chain_core = VGroup(sensor_icon, arr_rx1, rule_icon, arr_rx2, dispatch_icon)

        self.play(FadeIn(rx_chain_core, shift=DOWN * 0.1), run_time=1.0)

        # [2.3] 53.92s -> 57.98s It has no memory of what happened before
        self.sync_to(13.50)
        tag1_bg = RoundedRectangle(width=1.5, height=0.32, corner_radius=0.15, fill_color="#FEE2E2", fill_opacity=1.0, stroke_color="#FCA5A5", stroke_width=1.2)
        tag1_txt = CrispText("Zero State Memory", size=13, weight=BOLD, color="#E55353").move_to(tag1_bg)
        tag1_strike = Line(tag1_bg.get_left() + LEFT*0.04, tag1_bg.get_right() + RIGHT*0.04, color="#E55353", stroke_width=2.0)
        tag1 = VGroup(tag1_bg, tag1_txt, tag1_strike).move_to([-5.35, 0.60, 0]).set_z_index(20)

        self.play(FadeIn(tag1, shift=DOWN * 0.1), run_time=0.6)
        self.play(tag1_bg.animate.set_stroke(color="#DC2626", width=2.2), run_time=0.35)
        self.play(tag1_bg.animate.set_stroke(color="#FCA5A5", width=1.2), run_time=0.35)

        # [2.4] 58.13s -> 60.67s No ability to plan ahead
        self.sync_to(15.50)
        tag2_bg = RoundedRectangle(width=1.5, height=0.32, corner_radius=0.15, fill_color="#FEE2E2", fill_opacity=1.0, stroke_color="#FCA5A5", stroke_width=1.2)
        tag2_txt = CrispText("Zero Plan Horizon", size=13, weight=BOLD, color="#E55353").move_to(tag2_bg)
        tag2_strike = Line(tag2_bg.get_left() + LEFT*0.04, tag2_bg.get_right() + RIGHT*0.04, color="#E55353", stroke_width=2.0)
        tag2 = VGroup(tag2_bg, tag2_txt, tag2_strike).move_to([-3.05, 0.60, 0]).set_z_index(20)
        constraint_tags = VGroup(tag1, tag2)
        self.play(FadeIn(tag2, shift=DOWN * 0.1), run_time=0.6)

        # [2.5] 60.82s -> 64.37s Simply observes condition and responds
        self.sync_to(17.34)
        rule_lbl = CrispText("Rule Engine", size=14, weight=BOLD, color="#404040").move_to([-4.20, -0.95, 0])
        scope_pill = create_pill("Fixed Static Response", bg_color="#F1F5F9", text_color="#64748B", font_size=10).move_to([-4.20, -2.45, 0])
        self.play(FadeIn(rule_lbl), FadeIn(scope_pill, shift=UP * 0.1), run_time=0.6)

        rx_micro_pulse = Dot(color="#62B7E4", radius=0.08).move_to(sensor_box.get_center())
        self.play(MoveAlongPath(rx_micro_pulse, arr_rx1, rate_func=linear), run_time=0.7)
        self.play(FadeOut(rx_micro_pulse), run_time=0.2)

        # [2.6] 64.52s -> 68.58s Think of a simple alert agent as Solara
        self.sync_to(20.00)
        solara_alert_callout = create_pill("Solara Alert Node", bg_color="#62B7E4", font_size=9).move_to([-5.30, 0.15, 0])
        self.play(
            sensor_box.animate.set_stroke(color=C_HIGHLIGHT, width=3.0),
            FadeIn(solara_alert_callout, shift=UP * 0.1),
            run_time=0.6
        )
        self.play(sensor_box.animate.set_stroke(color="#62B7E4", width=2.0), run_time=0.4)

        # [2.7] 68.73s -> 75.84s Output drops below 8% -> send notification
        self.sync_to(22.20)
        cond_badge = create_pill("Output < 8%", bg_color="#E58F6D", font_size=9).move_to([-5.40, -1.25, 0])
        action_lbl = create_pill("Send Dispatch\nAlert", bg_color="#E55353", font_size=9).move_to([-3.00, -1.25, 0])
        self.play(FadeIn(cond_badge, shift=DOWN * 0.1), run_time=0.6)

        # Trigger execution pulse along conduit chain
        rx_pulse = Dot(color=C_HIGHLIGHT, radius=0.08).move_to(sensor_box.get_center())
        self.play(FadeIn(rx_pulse), run_time=0.2)
        self.play(MoveAlongPath(rx_pulse, arr_rx1, rate_func=linear), run_time=0.6)
        self.play(rule_box.animate.set_stroke(color=C_HIGHLIGHT, width=3.0), run_time=0.3)
        self.play(MoveAlongPath(rx_pulse, arr_rx2, rate_func=linear), run_time=0.6)
        self.play(
            FadeIn(action_lbl, shift=DOWN * 0.1),
            dispatch_box.animate.set_stroke(color="#E55353", width=3.5),
            FadeOut(rx_pulse),
            run_time=0.5
        )
        self.play(
            rule_box.animate.set_stroke(color="#7EA2C8", width=2.0),
            dispatch_box.animate.set_stroke(color="#E6A157", width=2.0),
            run_time=0.4
        )

        # [2.8] 75.99s -> 78.02s That's a reactive agent
        self.sync_to(28.48)
        self.play(
            badge1.animate.set_stroke(color=C_HIGHLIGHT, width=2.5),
            action_lbl.animate.scale(1.08),
            run_time=0.4
        )
        self.play(
            badge1.animate.set_stroke(width=0),
            action_lbl.animate.scale(1/1.08),
            run_time=0.4
        )

        # [2.9] 78.17s -> 81.72s Fast, predictable, easy to build, but limited
        self.sync_to(31.50)
        perf_lbl = CrispText("Sub-Millisecond Execution", size=14, weight=BOLD, color="#404040").move_to([-4.20, -1.90, 0])
        self.play(
            FadeIn(perf_lbl, shift=UP * 0.1),
            tag1_bg.animate.set_stroke(color="#E55353", width=2.0),
            tag2_bg.animate.set_stroke(color="#E55353", width=2.0),
            run_time=0.6
        )

        # [2.10] 81.87s -> 89.99s Can't investigate why drop happened
        self.sync_to(36.30)
        self.play(
            tag1.animate.scale(1.10),
            tag2.animate.scale(1.10),
            run_time=0.45
        )
        self.play(
            tag1.animate.scale(1/1.10),
            tag2.animate.scale(1/1.10),
            run_time=0.45
        )

        # Ambient telemetry kinetic action during the explanation of limitations
        self.sync_to(39.00)
        self.play(
            rule_box.animate.set_stroke(color="#62B7E4", width=2.6),
            sensor_box.animate.set_stroke(color=C_HIGHLIGHT, width=2.6),
            run_time=0.8
        )
        self.play(
            rule_box.animate.set_stroke(color="#7EA2C8", width=2.0),
            sensor_box.animate.set_stroke(color="#62B7E4", width=2.0),
            run_time=0.8
        )

        # =========================================================================
        ## Presentation Step 3
        # =========================================================================

        # [3.1] 90.34s -> 93.89s The second type is the goal-based agent
        self.sync_to(41.02)
        step_title3 = CrispText("Goal-Based Agent: Planned Outcomes", size=15, font="Open Sans", weight=SEMIBOLD, color="#64748B")
        step_title3.next_to(main_title, DOWN, buff=0.12, aligned_edge=LEFT)

        rx_full_group = VGroup(
            rx_chain_core, cond_badge, action_lbl, solara_alert_callout,
            rule_lbl, perf_lbl, scope_pill, constraint_tags
        )

        self.play(
            FadeOut(step_title2),
            FadeIn(step_title3, shift=DOWN * 0.1),
            FadeOut(rx_full_group),
            bay1_datum.animate.set_opacity(0.60),
            badge1.animate.set_opacity(0.60),
            bay2_datum.animate.set_opacity(1.0),
            badge2.animate.set_opacity(1.0),
            run_time=0.8
        )

        # [3.2] 94.04s -> 103.17s Reasons about actions in terms of moving closer to outcome
        self.sync_to(46.84)
        agent_core_bg = Circle(radius=0.36, fill_color="#F8FAFC", fill_opacity=1.0, stroke_color="#7EA2C8", stroke_width=2.0).move_to([-1.30, -0.40, 0])
        lattice_dots = VGroup(
            Dot([-1.38, -0.32, 0], radius=0.04, color="#2C81FE"),
            Dot([-1.22, -0.32, 0], radius=0.04, color="#2C81FE"),
            Dot([-1.30, -0.48, 0], radius=0.04, color="#2C81FE")
        )
        lattice_lines = VGroup(
            Line([-1.38, -0.32, 0], [-1.22, -0.32, 0], color="#7EA2C8", stroke_width=1.0),
            Line([-1.38, -0.32, 0], [-1.30, -0.48, 0], color="#7EA2C8", stroke_width=1.0),
            Line([-1.22, -0.32, 0], [-1.30, -0.48, 0], color="#7EA2C8", stroke_width=1.0)
        )
        agent_core_icon = VGroup(agent_core_bg, lattice_lines, lattice_dots)
        agent_core_lbl = CrispText("Agent Core", size=14, weight=BOLD, color="#404040").move_to([-1.30, -1.15, 0])
        agent_core_grp = VGroup(agent_core_icon, agent_core_lbl)

        target_outer = Circle(radius=0.36, fill_color="#FEF3C7", fill_opacity=1.0, stroke_color="#E6A157", stroke_width=2.0).move_to([1.30, -0.40, 0])
        target_inner = Circle(radius=0.20, fill_color="#FFFFFF", fill_opacity=0.0, stroke_color="#E6A157", stroke_width=1.5).move_to([1.30, -0.40, 0])
        reticle_ch1 = Line([1.10, -0.40, 0], [1.50, -0.40, 0], color="#E6A157", stroke_width=1.5)
        reticle_ch2 = Line([1.30, -0.60, 0], [1.30, -0.20, 0], color="#E6A157", stroke_width=1.5)
        target_icon = VGroup(target_outer, target_inner, reticle_ch1, reticle_ch2)
        target_lbl = create_pill("Target Goal", bg_color="#E6A157", font_size=9).move_to([1.40, -1.20, 0])
        target_grp = VGroup(target_icon, target_lbl)

        junc_bg = Square(side_length=0.24, fill_color="#FFFFFF", fill_opacity=1.0, stroke_color="#64748B", stroke_width=1.5).rotate(45 * DEGREES).move_to([-0.60, -0.40, 0])
        junc_glyph = CrispText("◇", size=14, color="#64748B").move_to(junc_bg)
        junc_node = VGroup(junc_bg, junc_glyph)
        conn_core_junc = Line(agent_core_bg.get_right(), junc_bg.get_left(), color="#7EA2C8", stroke_width=2.0)

        self.play(FadeIn(agent_core_grp), FadeIn(target_grp), run_time=1.0)

        self.sync_to(49.00)
        self.play(FadeIn(junc_node), Create(conn_core_junc), run_time=0.8)

        # [3.3] 103.32s -> 105.86s It plans and evaluates options
        self.sync_to(50.70)
        p_upper = CubicBezier([-0.48, -0.40, 0], [-0.10, 0.35, 0], [0.80, 0.35, 0], [1.30, -0.04, 0], color="#E58F6D", stroke_width=1.8)
        p_optimal = Line([-0.48, -0.40, 0], [0.94, -0.40, 0], color="#2C81FE", stroke_width=2.5)
        p_lower = CubicBezier([-0.48, -0.40, 0], [-0.10, -1.15, 0], [0.80, -1.15, 0], [1.30, -0.76, 0], color="#9B99C7", stroke_width=1.8)
        paths = VGroup(p_upper, p_optimal, p_lower)

        self.play(Create(paths), run_time=1.1)

        # [3.4] 106.01s -> 111.08s Chooses the path most likely to achieve goal
        self.sync_to(53.50)
        badge_upper = create_pill("High Latency", bg_color="#E58F6D", font_size=8).move_to([0.35, 0.35, 0])
        badge_opt = create_pill("Optimal Route", bg_color="#62B7E4", font_size=8).move_to([0.35, -0.40, 0])
        badge_lower = create_pill("Sub-Optimal", bg_color="#9B99C7", font_size=8).move_to([0.15, -1.00, 0])
        path_badges = VGroup(badge_upper, badge_opt, badge_lower)

        self.play(FadeIn(path_badges, shift=DOWN * 0.1), run_time=0.8)

        self.sync_to(55.50)
        opt_highlight = SurroundingRectangle(badge_opt, color=C_HIGHLIGHT, stroke_width=2.8, buff=0.06, corner_radius=0.12)
        self.play(Create(opt_highlight), run_time=0.6)

        # [3.5] 111.23s -> 115.30s Solara's Site Performance Investigation Agent
        self.sync_to(57.34)
        opt_pulse = Dot(color=C_HIGHLIGHT, radius=0.08).move_to(p_optimal.get_start())
        self.play(FadeIn(opt_pulse), run_time=0.2)
        self.play(MoveAlongPath(opt_pulse, p_optimal, rate_func=linear), run_time=1.2)
        self.play(
            target_outer.animate.set_stroke(color=C_HIGHLIGHT, width=3.5),
            FadeOut(opt_pulse),
            run_time=0.4
        )
        self.play(target_outer.animate.set_stroke(color="#E6A157", width=2.0), run_time=0.4)

        # [3.6] 115.44s -> 121.03s Goal: determine why Site 47 under-performed
        self.sync_to(62.24)
        site_goal_pill = create_pill("Goal: Site 47 Root Cause", bg_color="#E6A157", text_color="#FFFFFF", font_size=9).move_to([1.30, 0.35, 0])
        self.play(FadeIn(site_goal_pill, shift=DOWN * 0.1), run_time=0.6)
        self.play(target_icon.animate.scale(1.08), run_time=0.4)
        self.play(target_icon.animate.scale(1/1.08), run_time=0.4)

        # [3.7] 121.18s -> 124.22s It doesn't follow a fixed script
        self.sync_to(68.78)
        perf_lbl_g = CrispText("Proactive Goal Search", size=14, weight=BOLD, color="#404040").move_to([0.0, -1.85, 0])
        scope_pill_g = create_pill("Multi-Step Planning Horizon", bg_color="#7EA2C8", font_size=10).move_to([0.0, -2.35, 0])
        bottom_descriptors_g = VGroup(perf_lbl_g, scope_pill_g)

        self.play(
            FadeIn(bottom_descriptors_g, shift=UP * 0.1),
            junc_node.animate.scale(1.15).set_color(C_HIGHLIGHT),
            run_time=0.6
        )
        self.play(junc_node.animate.scale(1/1.15).set_color("#64748B"), run_time=0.4)

        # [3.8] 124.37s -> 133.51s Decides what data to pull, adjusting approach as results arrive
        self.sync_to(71.00)
        loop_pulse = Dot(color="#2C81FE", radius=0.08).move_to(p_optimal.get_start())
        self.play(FadeIn(loop_pulse), run_time=0.2)
        self.play(MoveAlongPath(loop_pulse, p_optimal, rate_func=linear), run_time=1.2)
        self.play(FadeOut(loop_pulse), run_time=0.2)

        # Ambient continuous focus maintenance until audio concludes
        self.sync_to(73.70)
        self.play(
            agent_core_bg.animate.set_stroke(color="#2C81FE", width=2.8),
            target_outer.animate.set_stroke(color=C_HIGHLIGHT, width=2.8),
            run_time=0.8
        )
        self.play(
            agent_core_bg.animate.set_stroke(color="#7EA2C8", width=2.0),
            target_outer.animate.set_stroke(color="#E6A157", width=2.0),
            run_time=0.8
        )

        # Final hold matching total audio duration
        self.sync_to(77.30)