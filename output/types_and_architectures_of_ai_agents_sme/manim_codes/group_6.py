C_SKY_BLUE = "#62B7E4"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_RED = "#E58F6D"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
C_STEEL_BLUE = "#7EA2C8"
C_YELLOW = "#DDB945"
C_WHITE = "#FFFFFF"
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
C_BG = "#FFFFFF"          # Pure White Canvas
C_SLATE_TITLE = "#0F172A" # Dark Slate Title
C_SUBTITLE = "#475569"    # Medium Slate Subtitle
C_TEXT = "#404040"        # Primary Dark Charcoal Body Text
C_BRAND_BLUE = "#2C81FE"  # Brand Blue
C_DARK_BLUE = "#1E293B"   # Dark Slate
C_SKY = "#62B7E4"         # Sky Blue
C_STEEL = "#7EA2C8"       # Steel Blue
C_LAVENDER = "#9B99C7"    # Lavender Periwinkle
C_MINT = "#8ECDB7"        # Mint Seafoam
C_AMBER = "#E6A157"       # Warm Amber
C_MUSTARD = "#DDB945"     # Mustard Yellow
C_CORAL = "#E58F6D"       # Coral Peach
C_LILAC = "#C1A5C6"       # Soft Lilac
C_HIGHLIGHT = "#F78908"   # Warm Orange Focal Highlight
C_CARD_BG = "#FFFFFF"     # Pure White Sub-Card Fill
C_BORDER = "#CBD5E1"      # Subtle Slate Border
SME_LAYOUT = '70'


class FinalScene(MovingCameraScene):
    def sync_to(self, target_time):
        curr_t = getattr(getattr(self, 'renderer', None), 'time', 0.0)
        if target_time > curr_t:
            self.wait(target_time - curr_t)

    def construct(self):
        # 1. Canvas Theme Setting
        self.camera.background_color = C_BG
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

















        def create_header(step_subtitle):
            title = CrispText("The Perception-Reasoning-Action Cycle", size=26, weight=BOLD, color=C_SLATE_TITLE)
            if title.width > 5.2:
                title.scale_to_fit_width(5.2)
            sub = CrispText(step_subtitle, size=16, weight=SEMIBOLD, color=C_SUBTITLE)
            if sub.width > 5.2:
                sub.scale_to_fit_width(5.2)
            header = VGroup(title, sub).arrange(DOWN, buff=0.10, aligned_edge=LEFT)
            header.move_to([-0.80 + header.width / 2.0, 3.10, 0])
            header.set_z_index(20)
            return header

        # ---------------------------------------------------------
        ## Presentation Step 1: Perception: Input Intake
        # ---------------------------------------------------------
        # [1.1] 0.00s -> 35.16s: "Perception is input."
        self.sync_to(0.00)
        header_grp = create_header("Perception: Input Intake")
        self.play(FadeIn(header_grp, shift=DOWN * 0.15), run_time=0.64)

        # Shifted diagram layout to right workspace (x >= -0.8) to guarantee teacher clearance
        p_center = np.array([2.05, -0.15, 0])

        outer_ring = Arc(radius=1.20, start_angle=0, angle=TAU, color=C_SKY, stroke_width=2.5).move_to(p_center)
        dashed_ring = DashedVMobject(Circle(radius=1.38, color=C_STEEL, stroke_width=1.5), num_dashes=28).move_to(p_center)
        inner_core = Circle(radius=0.75, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_SKY, stroke_width=3).move_to(p_center)
        
        iris_outer = Ellipse(width=0.90, height=0.55, stroke_color=C_STEEL, stroke_width=2, fill_color=C_BG, fill_opacity=0.6)
        pupil = Dot(radius=0.18, color=C_SLATE_TITLE)
        pupil_glow = Dot(radius=0.06, color=C_SKY).shift(UR * 0.05)
        iris_grp = VGroup(iris_outer, pupil, pupil_glow).move_to(p_center)

        p_label_badge = RoundedRectangle(width=2.2, height=0.48, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_SKY, stroke_width=2)
        p_label_txt = CrispText("Perception Core", size=15, weight=BOLD, color=C_SLATE_TITLE)
        p_badge_grp = VGroup(p_label_badge, p_label_txt).move_to(p_center + DOWN * 1.55)

        perception_sensor_grp = VGroup(dashed_ring, outer_ring, inner_core, iris_grp)

        # Working Context Panel (Right side of Perception workspace)
        wc_center = np.array([4.85, -0.15, 0])
        wc_frame = RoundedRectangle(width=2.6, height=3.8, corner_radius=0.12, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_BORDER, stroke_width=1.5).move_to(wc_center)
        wc_header_bg = RoundedRectangle(width=2.6, height=0.75, corner_radius=0.12, fill_color=C_STEEL, fill_opacity=0.25, stroke_width=0).move_to(wc_frame.get_top() + DOWN * 0.37)
        wc_title = CrispText("Working Context", size=15, weight=BOLD, color=C_SLATE_TITLE).move_to(wc_header_bg.get_center())

        slot_data = [
            ("Telemetry Reading", C_AMBER),
            ("User Request", C_SKY),
            ("Tool Result", C_STEEL),
            ("Error Message", C_CORAL),
        ]
        slots = VGroup()
        slot_frames = VGroup()
        for i, (label, col) in enumerate(slot_data):
            pos = wc_center + UP * (0.85 - i * 0.72)
            f_rect = DashedVMobject(RoundedRectangle(width=2.3, height=0.62, corner_radius=0.074, fill_color=C_BG, fill_opacity=0.35, stroke_color=C_BORDER, stroke_width=1.0), num_dashes=16).move_to(pos)
            slot_frames.add(f_rect)
            
            s_rect = RoundedRectangle(width=2.3, height=0.62, corner_radius=0.074, fill_color=C_BG, fill_opacity=0.95, stroke_color=col, stroke_width=1.8)
            s_dot = Dot(radius=0.07, color=col).shift(LEFT * 0.88)
            s_txt = CrispText(label, size=13, weight=BOLD, color=C_TEXT).shift(RIGHT * 0.10)
            slot_unit = VGroup(s_rect, s_dot, s_txt).move_to(pos)
            slots.add(slot_unit)

        wc_group = VGroup(wc_frame, wc_header_bg, wc_title)

        # Spoken Word: "agent" / "actions" (1.00s) -> Reveal Perception Core
        self.sync_to(3.00)
        self.play(
            GrowFromCenter(perception_sensor_grp),
            FadeIn(p_badge_grp, shift=UP * 0.1),
            run_time=0.80
        )
        dashed_ring.add_updater(lambda m, dt: m.rotate(0.25 * dt))

        # Spoken Word: "It plans. It evaluates options." (6.80s) -> Introduce Working Context Panel
        self.sync_to(8.14)
        self.play(
            FadeIn(wc_group, shift=LEFT * 0.2),
            FadeIn(slot_frames),
            run_time=0.80
        )

        # Spoken Word: "Solara's site performance investigation agent..." (13.70s) -> Telemetry radar sweep
        self.sync_to(10.00)
        scan_arc = Arc(radius=1.1, start_angle=-PI/3, angle=2*PI/3, color=C_SKY, stroke_width=3).move_to(p_center)
        self.play(Create(scan_arc), p_badge_grp.animate.set_stroke(color=C_SKY, width=2.5), run_time=0.56)
        self.play(FadeOut(scan_arc), p_badge_grp.animate.set_stroke(color=C_SKY, width=1.5), run_time=0.40)

        # Spoken Word: "Its goal is to determine why site 47 underperformed..." (17.84s) -> Iris sensory focus
        self.sync_to(12.46)
        focus_ring = Circle(radius=0.75, stroke_color=C_AMBER, stroke_width=3).move_to(p_center)
        self.play(
            iris_outer.animate.scale(1.15),
            pupil.animate.set_color(C_HIGHLIGHT),
            Create(focus_ring),
            run_time=0.48
        )
        self.play(
            iris_outer.animate.scale(1/1.15),
            pupil.animate.set_color(C_SLATE_TITLE),
            focus_ring.animate.scale(1.3).set_stroke(opacity=0),
            run_time=0.48
        )
        self.remove(focus_ring)

        # Spoken Word: "It decides what data to pull based on what it finds..." (25.58s) -> Aperture telemetry calibration
        self.sync_to(13.50)
        self.play(
            wc_frame.animate.set_stroke(color=C_BRAND_BLUE, width=2.5),
            inner_core.animate.set_stroke(color=C_BRAND_BLUE, width=3.5),
            run_time=0.48
        )
        self.play(
            wc_frame.animate.set_stroke(color=C_BORDER, width=1.5),
            inner_core.animate.set_stroke(color=C_SKY, width=3),
            run_time=0.48
        )

        # Spoken Word: "The third type is..." (32.72s) -> Perception aperture intake focus ping
        self.sync_to(14.58)
        focus_pulse = inner_core.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(Create(focus_pulse), run_time=0.40)
        self.play(FadeOut(focus_pulse), run_time=0.40)

        # [1.2] 35.31s -> 43.78s: Input cards constrained strictly to x >= -0.80 (right workspace)
        input_configs = [
            ("Data Reading", C_AMBER, np.array([-0.15, 1.35, 0]), 0),
            ("User Request", C_SKY, np.array([-0.15, 0.45, 0]), 1),
            ("Tool Result", C_STEEL, np.array([-0.15, -0.45, 0]), 2),
            ("Error Message", C_CORAL, np.array([-0.15, -1.35, 0]), 3),
        ]

        active_inputs_grp = VGroup()

        # 1. "a data reading" (35.31s)
        self.sync_to(15.50)
        src_label, color, start_pt, s_idx = input_configs[0]
        src_badge_0 = RoundedRectangle(width=1.6, height=0.46, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=color, stroke_width=1.8).move_to(start_pt)
        src_txt_0 = CrispText(src_label, size=13, weight=BOLD, color=C_TEXT).move_to(src_badge_0)
        src_grp_0 = VGroup(src_badge_0, src_txt_0).set_z_index(20)
        stream_path_0 = CurvedArrow(start_pt + RIGHT * 0.8, p_center + LEFT * 0.75, radius=2.5, color=color, stroke_width=2.5, tip_length=0.15)
        particle_0 = Dot(radius=0.10, color=color).move_to(stream_path_0.get_start())
        self.play(FadeIn(src_grp_0, shift=RIGHT * 0.15), Create(stream_path_0), run_time=0.32)
        self.play(MoveAlongPath(particle_0, stream_path_0), run_time=0.40, rate_func=smooth)
        pulse_ring_0 = Circle(radius=0.75, stroke_color=color, stroke_width=3.5, fill_opacity=0).move_to(p_center)
        self.play(ReplacementTransform(particle_0, pulse_ring_0), pulse_ring_0.animate.scale(1.35).set_stroke(opacity=0), run_time=0.24)
        self.remove(pulse_ring_0)
        xfer_arr_0 = Arrow(p_center + RIGHT * 0.75, slots[0].get_left(), buff=0.10, stroke_width=2.5, color=color, tip_length=0.15)
        xfer_dot_0 = Dot(radius=0.09, color=color).move_to(xfer_arr_0.get_start())
        self.play(Create(xfer_arr_0), MoveAlongPath(xfer_dot_0, xfer_arr_0), run_time=0.32)
        self.remove(xfer_dot_0)
        self.play(FadeIn(slots[0], shift=LEFT * 0.12), FadeOut(xfer_arr_0), run_time=0.24)
        active_inputs_grp.add(src_grp_0, stream_path_0)

        # 2. "a user request" (37.40s)
        self.sync_to(17.20)
        src_label, color, start_pt, s_idx = input_configs[1]
        src_badge_1 = RoundedRectangle(width=1.6, height=0.46, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=color, stroke_width=1.8).move_to(start_pt)
        src_txt_1 = CrispText(src_label, size=13, weight=BOLD, color=C_TEXT).move_to(src_badge_1)
        src_grp_1 = VGroup(src_badge_1, src_txt_1).set_z_index(20)
        stream_path_1 = CurvedArrow(start_pt + RIGHT * 0.8, p_center + LEFT * 0.75, radius=2.5, color=color, stroke_width=2.5, tip_length=0.15)
        particle_1 = Dot(radius=0.10, color=color).move_to(stream_path_1.get_start())
        self.play(FadeIn(src_grp_1, shift=RIGHT * 0.15), Create(stream_path_1), run_time=0.32)
        self.play(MoveAlongPath(particle_1, stream_path_1), run_time=0.40, rate_func=smooth)
        pulse_ring_1 = Circle(radius=0.75, stroke_color=color, stroke_width=3.5, fill_opacity=0).move_to(p_center)
        self.play(ReplacementTransform(particle_1, pulse_ring_1), pulse_ring_1.animate.scale(1.35).set_stroke(opacity=0), run_time=0.24)
        self.remove(pulse_ring_1)
        xfer_arr_1 = Arrow(p_center + RIGHT * 0.75, slots[1].get_left(), buff=0.10, stroke_width=2.5, color=color, tip_length=0.15)
        xfer_dot_1 = Dot(radius=0.09, color=color).move_to(xfer_arr_1.get_start())
        self.play(Create(xfer_arr_1), MoveAlongPath(xfer_dot_1, xfer_arr_1), run_time=0.32)
        self.remove(xfer_dot_1)
        self.play(FadeIn(slots[1], shift=LEFT * 0.12), FadeOut(xfer_arr_1), run_time=0.24)
        active_inputs_grp.add(src_grp_1, stream_path_1)

        # 3. "a tool result" (39.50s)
        self.sync_to(18.90)
        src_label, color, start_pt, s_idx = input_configs[2]
        src_badge_2 = RoundedRectangle(width=1.6, height=0.46, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=color, stroke_width=1.8).move_to(start_pt)
        src_txt_2 = CrispText(src_label, size=13, weight=BOLD, color=C_TEXT).move_to(src_badge_2)
        src_grp_2 = VGroup(src_badge_2, src_txt_2).set_z_index(20)
        stream_path_2 = CurvedArrow(start_pt + RIGHT * 0.8, p_center + LEFT * 0.75, radius=2.5, color=color, stroke_width=2.5, tip_length=0.15)
        particle_2 = Dot(radius=0.10, color=color).move_to(stream_path_2.get_start())
        self.play(FadeIn(src_grp_2, shift=RIGHT * 0.15), Create(stream_path_2), run_time=0.32)
        self.play(MoveAlongPath(particle_2, stream_path_2), run_time=0.40, rate_func=smooth)
        pulse_ring_2 = Circle(radius=0.75, stroke_color=color, stroke_width=3.5, fill_opacity=0).move_to(p_center)
        self.play(ReplacementTransform(particle_2, pulse_ring_2), pulse_ring_2.animate.scale(1.35).set_stroke(opacity=0), run_time=0.24)
        self.remove(pulse_ring_2)
        xfer_arr_2 = Arrow(p_center + RIGHT * 0.75, slots[2].get_left(), buff=0.10, stroke_width=2.5, color=color, tip_length=0.15)
        xfer_dot_2 = Dot(radius=0.09, color=color).move_to(xfer_arr_2.get_start())
        self.play(Create(xfer_arr_2), MoveAlongPath(xfer_dot_2, xfer_arr_2), run_time=0.32)
        self.remove(xfer_dot_2)
        self.play(FadeIn(slots[2], shift=LEFT * 0.12), FadeOut(xfer_arr_2), run_time=0.24)
        active_inputs_grp.add(src_grp_2, stream_path_2)

        # 4. "and error message" (41.60s)
        self.sync_to(20.50)
        src_label, color, start_pt, s_idx = input_configs[3]
        src_badge_3 = RoundedRectangle(width=1.6, height=0.46, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=color, stroke_width=1.8).move_to(start_pt)
        src_txt_3 = CrispText(src_label, size=13, weight=BOLD, color=C_TEXT).move_to(src_badge_3)
        src_grp_3 = VGroup(src_badge_3, src_txt_3).set_z_index(20)
        stream_path_3 = CurvedArrow(start_pt + RIGHT * 0.8, p_center + LEFT * 0.75, radius=2.5, color=color, stroke_width=2.5, tip_length=0.15)
        particle_3 = Dot(radius=0.10, color=color).move_to(stream_path_3.get_start())
        self.play(FadeIn(src_grp_3, shift=RIGHT * 0.15), Create(stream_path_3), run_time=0.32)
        self.play(MoveAlongPath(particle_3, stream_path_3), run_time=0.40, rate_func=smooth)
        pulse_ring_3 = Circle(radius=0.75, stroke_color=color, stroke_width=3.5, fill_opacity=0).move_to(p_center)
        self.play(ReplacementTransform(particle_3, pulse_ring_3), pulse_ring_3.animate.scale(1.35).set_stroke(opacity=0), run_time=0.24)
        self.remove(pulse_ring_3)
        xfer_arr_3 = Arrow(p_center + RIGHT * 0.75, slots[3].get_left(), buff=0.10, stroke_width=2.5, color=color, tip_length=0.15)
        xfer_dot_3 = Dot(radius=0.09, color=color).move_to(xfer_arr_3.get_start())
        self.play(Create(xfer_arr_3), MoveAlongPath(xfer_dot_3, xfer_arr_3), run_time=0.32)
        self.remove(xfer_dot_3)
        self.play(FadeIn(slots[3], shift=LEFT * 0.12), FadeOut(xfer_arr_3), run_time=0.24)
        active_inputs_grp.add(src_grp_3, stream_path_3)

        # [1.3] 43.93s -> 44.03s: "It takes that in and adds it to its working context."
        self.sync_to(22.00)
        self.play(
            wc_frame.animate.set_stroke(color=C_BRAND_BLUE, width=3.0),
            wc_header_bg.animate.set_fill(color=C_BRAND_BLUE, opacity=0.35),
            run_time=0.16
        )
        self.play(
            wc_frame.animate.set_stroke(color=C_BORDER, width=1.5),
            wc_header_bg.animate.set_fill(color=C_STEEL, opacity=0.25),
            run_time=0.16
        )

        # ---------------------------------------------------------
        ## Presentation Step 2: Reasoning: Interpretation & Plan
        # ---------------------------------------------------------
        # [2.1] 44.38s -> 47.03s: "Reasoning is interpretation and planning."
        self.sync_to(26.50)
        new_header_grp = create_header("Reasoning: Interpretation & Plan")
        self.play(FadeOut(header_grp), run_time=0.28)
        self.play(FadeIn(new_header_grp, shift=DOWN * 0.1), run_time=0.36)
        header_grp = new_header_grp

        dashed_ring.clear_updaters()
        self.play(FadeOut(active_inputs_grp), FadeOut(slot_frames), run_time=0.32)

        p_full_module = VGroup(perception_sensor_grp, p_badge_grp)
        compact_perception_group = VGroup(p_full_module, wc_group, slots)

        self.play(
            compact_perception_group.animate.scale(0.68).move_to([0.65, -0.10, 0]),
            run_time=0.64
        )

        r_center = np.array([3.72, -0.05, 0])

        r_halo = Circle(radius=1.35, stroke_color=C_LAVENDER, stroke_width=2.5, stroke_opacity=0.8).move_to(r_center)
        r_dashed = DashedVMobject(Circle(radius=1.52, color=C_STEEL, stroke_width=1.5), num_dashes=32).move_to(r_center)
        r_core_bg = Circle(radius=1.05, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_LAVENDER, stroke_width=3).move_to(r_center)

        node_c = Dot(radius=0.12, color=C_SLATE_TITLE).move_to(r_center)
        node_nw = Dot(radius=0.08, color=C_SKY).move_to(r_center + UL * 0.48)
        node_ne = Dot(radius=0.08, color=C_AMBER).move_to(r_center + UR * 0.48)
        node_sw = Dot(radius=0.08, color=C_MINT).move_to(r_center + DL * 0.48)
        node_se = Dot(radius=0.08, color=C_CORAL).move_to(r_center + DR * 0.48)

        synapses = VGroup(
            Line(node_c.get_center(), node_nw.get_center(), stroke_color=C_BORDER, stroke_width=1.5),
            Line(node_c.get_center(), node_ne.get_center(), stroke_color=C_BORDER, stroke_width=1.5),
            Line(node_c.get_center(), node_sw.get_center(), stroke_color=C_BORDER, stroke_width=1.5),
            Line(node_c.get_center(), node_se.get_center(), stroke_color=C_BORDER, stroke_width=1.5),
            Line(node_nw.get_center(), node_ne.get_center(), stroke_color=C_BORDER, stroke_width=1.5),
            Line(node_sw.get_center(), node_se.get_center(), stroke_color=C_BORDER, stroke_width=1.5),
        )
        neural_cluster = VGroup(synapses, node_c, node_nw, node_ne, node_sw, node_se)

        r_label_badge = RoundedRectangle(width=2.2, height=0.48, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_LAVENDER, stroke_width=2)
        r_label_txt = CrispText("Reasoning Core", size=15, weight=BOLD, color=C_SLATE_TITLE)
        r_badge_grp = VGroup(r_label_badge, r_label_txt).move_to(r_center + DOWN * 1.60)

        reasoning_engine_grp = VGroup(r_dashed, r_halo, r_core_bg, neural_cluster, r_badge_grp)

        self.play(GrowFromCenter(reasoning_engine_grp), run_time=0.72)
        r_dashed.add_updater(lambda m, dt: m.rotate(0.20 * dt))

        # [2.2] 47.18s -> 59.35s: "The agent's LLM process is what it's received..."
        self.sync_to(30.34)
        context_to_reason = Arrow(compact_perception_group.get_right() + UP * 0.1, r_core_bg.get_left(), buff=0.15, stroke_color=C_STEEL, stroke_width=3, tip_length=0.16)
        c_dot = Dot(radius=0.09, color=C_SKY).move_to(context_to_reason.get_start())
        self.play(Create(context_to_reason), MoveAlongPath(c_dot, context_to_reason), run_time=0.72)
        self.remove(c_dot)

        # Beat B: "considers its goal" (50.00s)
        self.sync_to(32.80)
        goal_badge = RoundedRectangle(width=1.8, height=0.46, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=1.8).move_to(r_center + UP * 1.85 + LEFT * 0.85)
        goal_txt = CrispText("Target Goal", size=14, weight=BOLD, color=C_TEXT).move_to(goal_badge)
        goal_grp = VGroup(goal_badge, goal_txt).set_z_index(20)
        goal_line = DashedLine(goal_badge.get_bottom(), r_core_bg.get_top() + LEFT * 0.25, stroke_color=C_AMBER, stroke_width=1.5)
        goal_path = Line(goal_badge.get_bottom(), r_core_bg.get_top() + LEFT * 0.25)

        g_pulse = Dot(radius=0.08, color=C_AMBER).move_to(goal_badge.get_bottom())
        self.play(FadeIn(goal_grp, shift=DOWN * 0.1), Create(goal_line), run_time=0.48)
        self.play(MoveAlongPath(g_pulse, goal_path), run_time=0.32)
        self.remove(g_pulse)

        # Beat C: "reviews what it's already done" (52.50s)
        self.sync_to(35.00)
        memory_badge = RoundedRectangle(width=1.8, height=0.46, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_MINT, stroke_width=1.8).move_to(r_center + UP * 1.85 + RIGHT * 0.85)
        memory_txt = CrispText("Past Actions", size=14, weight=BOLD, color=C_TEXT).move_to(memory_badge)
        memory_grp = VGroup(memory_badge, memory_txt).set_z_index(20)
        mem_line = DashedLine(memory_badge.get_bottom(), r_core_bg.get_top() + RIGHT * 0.25, stroke_color=C_MINT, stroke_width=1.5)
        mem_path = Line(memory_badge.get_bottom(), r_core_bg.get_top() + RIGHT * 0.25)

        m_pulse = Dot(radius=0.08, color=C_MINT).move_to(memory_badge.get_bottom())
        self.play(FadeIn(memory_grp, shift=DOWN * 0.1), Create(mem_line), run_time=0.48)
        self.play(MoveAlongPath(m_pulse, mem_path), run_time=0.32)
        self.remove(m_pulse)

        # Beat D: Neural Synapse Deliberation (54.50s)
        self.sync_to(36.20)
        self.play(
            node_nw.animate.set_color(C_HIGHLIGHT).scale(1.2),
            node_ne.animate.set_color(C_HIGHLIGHT).scale(1.2),
            node_se.animate.set_color(C_HIGHLIGHT).scale(1.2),
            node_sw.animate.set_color(C_HIGHLIGHT).scale(1.2),
            run_time=0.32
        )
        self.play(
            node_nw.animate.set_color(C_SKY).scale(1/1.2),
            node_ne.animate.set_color(C_AMBER).scale(1/1.2),
            node_se.animate.set_color(C_CORAL).scale(1/1.2),
            node_sw.animate.set_color(C_MINT).scale(1/1.2),
            run_time=0.40
        )

        # Beat E: "and decides what action to take next" (56.50s)
        self.sync_to(37.52)
        plan_center = np.array([5.35, -0.05, 0])
        plan_arrow = Arrow(r_core_bg.get_right(), plan_center + LEFT * 0.85, buff=0.12, stroke_color=C_AMBER, stroke_width=3, tip_length=0.18)
        
        plan_card = RoundedRectangle(width=1.7, height=1.35, corner_radius=0.10, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=2.2).move_to(plan_center)
        plan_pill = RoundedRectangle(width=1.5, height=0.34, corner_radius=0.074, fill_color=C_AMBER, fill_opacity=0.25, stroke_width=0).move_to(plan_card.get_top() + DOWN * 0.25)
        plan_header = CrispText("Selected Plan", size=12, weight=BOLD, color=C_SLATE_TITLE).move_to(plan_pill)
        
        f_box1 = Rectangle(width=0.36, height=0.22, stroke_color=C_SLATE_TITLE, stroke_width=1.2, fill_color=C_BG, fill_opacity=1).move_to(plan_center + DOWN * 0.18 + LEFT * 0.28)
        f_box2 = Rectangle(width=0.36, height=0.22, stroke_color=C_SLATE_TITLE, stroke_width=1.2, fill_color=C_BG, fill_opacity=1).move_to(plan_center + DOWN * 0.18 + RIGHT * 0.28)
        f_conn = Arrow(f_box1.get_right(), f_box2.get_left(), buff=0.03, stroke_width=1.2, tip_length=0.07, color=C_STEEL)
        flow_glyph = VGroup(f_box1, f_box2, f_conn)
        
        plan_grp = VGroup(plan_card, plan_pill, plan_header, flow_glyph).set_z_index(20)

        p_dot = Dot(radius=0.09, color=C_AMBER).move_to(plan_arrow.get_start())
        self.play(Create(plan_arrow), MoveAlongPath(p_dot, plan_arrow), run_time=0.48)
        self.remove(p_dot)
        self.play(FadeIn(plan_grp, shift=LEFT * 0.2), run_time=0.56)

        # [2.3] 59.51s -> 62.68s: "This is where the intelligence lives."
        self.sync_to(41.38)
        r_pulse = r_core_bg.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=4.0)
        self.play(
            Create(r_pulse),
            r_badge_grp[0].animate.set_stroke(color=C_HIGHLIGHT, width=3.0),
            r_badge_grp[1].animate.set_color(C_HIGHLIGHT),
            run_time=0.48
        )
        self.play(
            FadeOut(r_pulse),
            r_badge_grp[0].animate.set_stroke(color=C_LAVENDER, width=2.0),
            r_badge_grp[1].animate.set_color(C_SLATE_TITLE),
            run_time=0.48
        )

        # ---------------------------------------------------------
        ## Presentation Step 3: Action: Execution & Cycle Restart
        # ---------------------------------------------------------
        # [3.1] 63.03s -> 64.62s: "Action is execution."
        self.sync_to(46.00)
        new_header_grp = create_header("Action: Execution & Cycle Restart")
        self.play(
            FadeOut(header_grp), FadeIn(new_header_grp, shift=DOWN * 0.1),
            FadeOut(goal_grp), FadeOut(memory_grp), FadeOut(goal_line), FadeOut(mem_line),
            FadeOut(context_to_reason), FadeOut(plan_arrow), FadeOut(plan_grp),
            run_time=0.32
        )
        header_grp = new_header_grp

        r_dashed.clear_updaters()

        # Workspace positions strictly within right canvas (x >= -0.8)
        target_p_pos = np.array([-0.10, 0.45, 0])
        target_r_pos = np.array([2.15, 0.45, 0])
        target_a_pos = np.array([4.40, 0.45, 0])

        r_full_module = VGroup(r_dashed, r_halo, r_core_bg, neural_cluster, r_badge_grp)

        # Action Execution Layer
        a_center = target_a_pos
        a_halo = Circle(radius=0.85, stroke_color=C_MINT, stroke_width=2.5).move_to(a_center)
        a_core_bg = Circle(radius=0.70, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_MINT, stroke_width=3).move_to(a_center)

        gear_center = Dot(radius=0.09, color=C_SLATE_TITLE).move_to(a_center)
        teeth = VGroup()
        for i in range(8):
            angle = i * (TAU / 8)
            tooth = RoundedRectangle(width=0.12, height=0.24, corner_radius=0.03, fill_color=C_STEEL, stroke_width=0).rotate(angle).move_to(a_center + np.array([np.cos(angle)*0.40, np.sin(angle)*0.40, 0]))
            teeth.add(tooth)
        gear_inner_ring = Circle(radius=0.30, stroke_color=C_STEEL, stroke_width=2.5, fill_color=C_CARD_BG, fill_opacity=1).move_to(a_center)
        gear_glyph = VGroup(teeth, gear_inner_ring, gear_center)

        a_label_badge = RoundedRectangle(width=2.0, height=0.45, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_MINT, stroke_width=2)
        a_label_txt = CrispText("Action Layer", size=15, weight=BOLD, color=C_SLATE_TITLE)
        a_badge_grp = VGroup(a_label_badge, a_label_txt).move_to(a_center + DOWN * 1.18)

        action_hub_grp = VGroup(a_halo, a_core_bg, gear_glyph, a_badge_grp)

        # Sequence Fix: Reposition core modules FIRST before instantiating connecting arrows to avoid line rendering artifacts
        self.play(
            compact_perception_group.animate.scale(0.85).move_to(target_p_pos),
            r_full_module.animate.scale(0.72).move_to(target_r_pos),
            GrowFromCenter(action_hub_grp),
            run_time=0.64
        )

        p_to_r_arrow = Arrow(compact_perception_group.get_right() + UP * 0.1, r_core_bg.get_left(), buff=0.12, stroke_color=C_SKY, stroke_width=2.5, tip_length=0.14)
        r_to_a_arrow = Arrow(r_core_bg.get_right(), a_core_bg.get_left(), buff=0.12, stroke_color=C_LAVENDER, stroke_width=2.5, tip_length=0.14)

        self.play(
            Create(p_to_r_arrow),
            Create(r_to_a_arrow),
            run_time=0.24
        )
        gear_glyph.add_updater(lambda m, dt: m.rotate(-0.4 * dt))

        # [3.2] 64.77s -> 72.71s: "The agent calls a tool, writes an output, sends a message..."
        action_outputs = [
            ("Call Tool", C_SKY, np.array([5.70, 1.35, 0])),
            ("Write Output", C_AMBER, np.array([5.70, 0.75, 0])),
            ("Send Message", C_CORAL, np.array([5.70, 0.15, 0])),
            ("Update Record", C_LILAC, np.array([5.70, -0.45, 0])),
        ]

        env_signals = VGroup()
        for label, color, pos in action_outputs:
            act_pill = RoundedRectangle(width=1.4, height=0.48, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=color, stroke_width=1.8).move_to(pos)
            act_txt = CrispText(label, size=12, weight=BOLD, color=C_TEXT).move_to(act_pill)
            sig_arrow = Arrow(a_core_bg.get_right(), act_pill.get_left(), buff=0.06, stroke_color=color, stroke_width=1.8, tip_length=0.10)
            env_signals.add(VGroup(sig_arrow, act_pill, act_txt).set_z_index(20))

        # Action 1: "calls a tool" (64.77s)
        self.sync_to(49.00)
        self.play(FadeIn(env_signals[0], shift=RIGHT * 0.10), run_time=0.48)

        # Action 2: "writes an output" (66.80s)
        self.sync_to(50.80)
        self.play(FadeIn(env_signals[1], shift=RIGHT * 0.10), run_time=0.48)

        # Action 3: "sends a message" (68.80s)
        self.sync_to(52.50)
        self.play(FadeIn(env_signals[2], shift=RIGHT * 0.10), run_time=0.48)

        # Action 4: "or updates a record" (70.80s)
        self.sync_to(54.20)
        self.play(FadeIn(env_signals[3], shift=RIGHT * 0.10), run_time=0.48)

        # [3.3] 72.86s -> 77.10s: "Something changes in the world as a result."
        self.sync_to(56.16)
        act_pulse = a_core_bg.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(
            Create(act_pulse),
            *[sig[1].animate.set_stroke(color=C_HIGHLIGHT, width=2.5) for sig in env_signals],
            run_time=0.48
        )
        self.play(
            FadeOut(act_pulse),
            *[sig[1].animate.set_stroke(color=col, width=1.8) for sig, (_, col, _) in zip(env_signals, action_outputs)],
            run_time=0.48
        )

        # [3.4] 77.25s -> 79.89s: "Then the cycle begins again."
        self.sync_to(64.60)
        loop_start = np.array([4.40, -0.75, 0])
        loop_mid = np.array([2.15, -2.00, 0])
        loop_end = np.array([-0.10, -0.75, 0])

        feedback_curve = CubicBezier(
            loop_start,
            loop_start + DOWN * 0.8,
            loop_end + DOWN * 0.8,
            loop_end,
            color=C_AMBER,
            stroke_width=3
        )
        feedback_arrow_tip = ArrowTriangleFilledTip(color=C_AMBER).rotate(PI / 2).move_to(loop_end)
        
        fb_pill = RoundedRectangle(width=2.1, height=0.45, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_AMBER, stroke_width=2).move_to(loop_mid + DOWN * 0.35)
        fb_txt = CrispText("New Perception", size=14, weight=BOLD, color=C_SLATE_TITLE).move_to(fb_pill)
        feedback_label_grp = VGroup(fb_pill, fb_txt).set_z_index(20)

        self.play(
            Create(feedback_curve),
            FadeIn(feedback_arrow_tip),
            run_time=0.72
        )

        # [3.5] 80.05s -> 84.28s: "The result of the action becomes new perception."
        self.sync_to(67.66)
        self.play(FadeIn(feedback_label_grp, shift=UP * 0.1), run_time=0.32)
        loop_packet = Dot(radius=0.10, color=C_AMBER).move_to(loop_start)
        self.play(
            MoveAlongPath(loop_packet, feedback_curve),
            rate_func=smooth,
            run_time=0.96
        )
        self.remove(loop_packet)
        p_receipt_pulse = Circle(radius=0.75, stroke_color=C_AMBER, stroke_width=3).move_to(compact_perception_group.get_center())
        self.play(Create(p_receipt_pulse), p_receipt_pulse.animate.scale(1.3).set_stroke(opacity=0), run_time=0.40)
        self.remove(p_receipt_pulse)

        # [3.6] 84.43s -> 88.67s: "The agent reasons about what that result means."
        self.sync_to(72.38)
        p2r_packet = Dot(radius=0.09, color=C_SKY).move_to(p_to_r_arrow.get_start())
        self.play(MoveAlongPath(p2r_packet, p_to_r_arrow), run_time=0.56)
        self.remove(p2r_packet)
        self.play(
            node_nw.animate.set_color(C_HIGHLIGHT).scale(1.2),
            node_ne.animate.set_color(C_HIGHLIGHT).scale(1.2),
            node_se.animate.set_color(C_HIGHLIGHT).scale(1.2),
            node_sw.animate.set_color(C_HIGHLIGHT).scale(1.2),
            r_badge_grp[0].animate.set_stroke(color=C_HIGHLIGHT, width=2.5),
            run_time=0.40
        )
        self.play(
            node_nw.animate.set_color(C_SKY).scale(1/1.2),
            node_ne.animate.set_color(C_AMBER).scale(1/1.2),
            node_se.animate.set_color(C_CORAL).scale(1/1.2),
            node_sw.animate.set_color(C_MINT).scale(1/1.2),
            r_badge_grp[0].animate.set_stroke(color=C_LAVENDER, width=2.0),
            run_time=0.40
        )

        # [3.7] 88.82s -> 97.82s: "For Solaira's Equipment Help Monitoring Agent..."
        self.sync_to(75.00)
        loop_badge = RoundedRectangle(width=3.8, height=0.48, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_BRAND_BLUE, stroke_width=2.0).move_to([2.15, -1.25, 0])
        loop_txt = CrispText("Equipment Monitoring: Autonomous Loop", size=13, weight=BOLD, color=C_BRAND_BLUE).move_to(loop_badge)
        loop_badge_grp = VGroup(loop_badge, loop_txt).set_z_index(20)
        self.play(FadeIn(loop_badge_grp, shift=UP * 0.1), run_time=0.48)

        # Rapid Multi-Cycle Waves
        pkt1 = Dot(radius=0.09, color=C_SKY).move_to(p_to_r_arrow.get_start())
        pkt2 = Dot(radius=0.09, color=C_LAVENDER).move_to(r_to_a_arrow.get_start())
        pkt3 = Dot(radius=0.09, color=C_AMBER).move_to(loop_start)
        self.play(
            MoveAlongPath(pkt1, p_to_r_arrow),
            MoveAlongPath(pkt2, r_to_a_arrow),
            MoveAlongPath(pkt3, feedback_curve),
            run_time=1.04,
            rate_func=linear
        )
        self.remove(pkt1, pkt2, pkt3)

        pkt4 = Dot(radius=0.09, color=C_SKY).move_to(p_to_r_arrow.get_start())
        pkt5 = Dot(radius=0.09, color=C_LAVENDER).move_to(r_to_a_arrow.get_start())
        pkt6 = Dot(radius=0.09, color=C_AMBER).move_to(loop_start)
        self.play(
            MoveAlongPath(pkt4, p_to_r_arrow),
            MoveAlongPath(pkt5, r_to_a_arrow),
            MoveAlongPath(pkt6, feedback_curve),
            loop_badge.animate.set_stroke(color=C_HIGHLIGHT, width=2.5),
            run_time=1.04,
            rate_func=linear
        )
        self.remove(pkt4, pkt5, pkt6)
        self.play(FadeOut(loop_badge_grp), run_time=0.40)

        # [3.8] 97.97s -> 107.50s: "Quarrying data, evaluating results..."
        cycle_status_badge = RoundedRectangle(width=2.8, height=0.48, corner_radius=0.08, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_HIGHLIGHT, stroke_width=2.2).move_to([2.15, -1.25, 0]).set_z_index(20)
        
        # 1. "Quarrying data" (97.97s)
        self.sync_to(77.82)
        st_txt1 = CrispText("Querying Data...", size=14, weight=BOLD, color=C_AMBER).move_to(cycle_status_badge)
        st_grp1 = VGroup(cycle_status_badge, st_txt1).set_z_index(20)
        pkt_st1 = Dot(radius=0.09, color=C_AMBER).move_to(p_to_r_arrow.get_start())
        self.play(FadeIn(st_grp1), MoveAlongPath(pkt_st1, p_to_r_arrow), run_time=0.64, rate_func=linear)
        self.remove(pkt_st1)

        # 2. "evaluating results" (99.80s)
        self.sync_to(79.00)
        st_txt2 = CrispText("Evaluating Results...", size=14, weight=BOLD, color=C_LAVENDER).move_to(cycle_status_badge)
        pkt_st2 = Dot(radius=0.09, color=C_LAVENDER).move_to(r_to_a_arrow.get_start())
        self.play(Transform(st_txt1, st_txt2), MoveAlongPath(pkt_st2, r_to_a_arrow), run_time=0.64, rate_func=linear)
        self.remove(pkt_st2)

        # 3. "deciding what to check next" (101.50s)
        self.sync_to(80.50)
        st_txt3 = CrispText("Deciding Next Action...", size=14, weight=BOLD, color=C_MINT).move_to(cycle_status_badge)
        pkt_st3 = Dot(radius=0.09, color=C_MINT).move_to(feedback_curve.get_start())
        self.play(Transform(st_txt1, st_txt3), MoveAlongPath(pkt_st3, feedback_curve), run_time=0.64, rate_func=linear)
        self.remove(pkt_st3)

        # 4. "generating a finding" (103.20s)
        self.sync_to(81.80)
        st_txt4 = CrispText("Generating Finding...", size=14, weight=BOLD, color=C_SKY).move_to(cycle_status_badge)
        self.play(
            Transform(st_txt1, st_txt4),
            a_core_bg.animate.set_stroke(color=C_HIGHLIGHT, width=3.5),
            run_time=0.64
        )
        self.play(a_core_bg.animate.set_stroke(color=C_MINT, width=3.0), FadeOut(st_grp1), run_time=0.32)

        # 5. "before it produces a final output" (104.80s)
        self.sync_to(83.00)
        out_center = np.array([4.40, -2.45, 0])
        doc_card = RoundedRectangle(width=2.4, height=1.35, corner_radius=0.10, fill_color=C_CARD_BG, fill_opacity=1.0, stroke_color=C_HIGHLIGHT, stroke_width=2.5).move_to(out_center)
        doc_header_bar = RoundedRectangle(width=2.0, height=0.32, corner_radius=0.06, fill_color=C_HIGHLIGHT, fill_opacity=0.25, stroke_width=0).move_to(doc_card.get_top() + DOWN * 0.22)
        doc_title = CrispText("Final Output", size=13, weight=BOLD, color=C_SLATE_TITLE).move_to(doc_header_bar)

        line1 = Line(LEFT * 0.8, RIGHT * 0.8, stroke_color=C_STEEL, stroke_width=2).move_to(out_center + DOWN * 0.10)
        line2 = Line(LEFT * 0.8, RIGHT * 0.4, stroke_color=C_BORDER, stroke_width=2).move_to(out_center + DOWN * 0.28)
        check_icon = Dot(radius=0.09, color=C_HIGHLIGHT).move_to(out_center + DOWN * 0.44 + RIGHT * 0.65)
        
        final_doc_grp = VGroup(doc_card, doc_header_bar, doc_title, line1, line2, check_icon).set_z_index(20)
        doc_flow_arrow = Arrow(a_badge_grp.get_bottom(), doc_card.get_top(), buff=0.08, stroke_color=C_HIGHLIGHT, stroke_width=2.5, tip_length=0.14)

        self.play(
            Create(doc_flow_arrow),
            FadeIn(final_doc_grp, shift=UP * 0.15),
            run_time=0.64
        )

        doc_pulse = doc_card.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        self.play(Create(doc_pulse), run_time=0.40)
        self.play(FadeOut(doc_pulse), run_time=0.40)

        gear_glyph.clear_updaters()

        # Hold scene through completion of the voiceover
        self.sync_to(84.50)