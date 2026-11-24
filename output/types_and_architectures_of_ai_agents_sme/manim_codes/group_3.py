C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_WHITE = "#FFFFFF"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040"
C_HIGHLIGHT = "#F78908"
C_MINT = "#8ECDB7"
C_BORDER = "#CBD5E1"
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
import os
import math

# Try importing InstrumentedScene, fallback gracefully if not defined in local environment
try:
    InstrumentedScene
except NameError:
    class InstrumentedScene(object):
        pass

# ---------------------------------------------------------
# CONSTANTS & PALETTE (SIMPLILEARN OSL 3.0 SPECIFICATION)
# ---------------------------------------------------------
CANVAS_BG = "#F0F4F8"          # Modern Soft Slate Canvas
C_PRIMARY_TEXT = "#404040"     # Primary Dark Charcoal
C_TITLE_SLATE = "#0F172A"      # Slate Title
C_SUB_SLATE = "#334155"        # Subtitle Slate
C_HIGHLIGHT_ORANGE = "#F78908" # Focus Attention Highlight

# 10-Color Approved Infographic Pastel Palette
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_LAVENDER = "#9B99C7"
C_MINT_SEAFOAM = "#8ECDB7"
C_WARM_AMBER = "#E6A157"
C_MUSTARD_GOLD = "#DDB945"
C_CORAL = "#E58F6D"
C_WARM_TAN = "#B88968"
C_DUSTY_ROSE = "#D98CA1"
C_SOFT_LILAC = "#C1A5C6"

# Card / Background Container Fills
C_CARD_WHITE = "#FFFFFF"
C_CARD_SOFT = "#F8FAFC"
C_BORDER_LIGHT = "#CBD5E1"

# Asset Paths from Scene Context
IMAGE_PATHS = {
    "act_call_api": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_act_call_api.png",
    "act_query_db": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_act_query_db.png",
    "act_send_alert": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_act_send_alert.png",
    "act_write_file": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_act_write_file.png",
    "action_hub_asset": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_action_hub_asset.png",
    "icon_action": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_icon_action.png",
    "icon_memory": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_icon_memory.png",
    "icon_perception": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_icon_perception.png",
    "icon_reasoning": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_icon_reasoning.png",
    "llm_brain": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_llm_brain.jpg",
    "solar_sensor": "/Users/saniyaacharya/Simplilearn/output/types_and_architectures_of_ai_agents_sme/images/scene_3_solar_sensor.jpg"
}

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------




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
def load_hero_image(key, target_height=1.5, fallback_func=None):
    """Safely wraps ImageMobject inside Group or constructs vector fallback."""
    path = IMAGE_PATHS.get(key, "")
    if path and os.path.exists(path):
        img = ImageMobject(path)
        img.scale_to_fit_height(target_height)
        return Group(img)
    elif fallback_func is not None:
        return Group(fallback_func())
    else:
        dummy = RoundedRectangle(corner_radius=0.1, width=target_height, height=target_height,
                                 fill_color=C_CARD_WHITE, fill_opacity=0.9, stroke_color=C_SKY_BLUE, stroke_width=1.5)
        return Group(dummy)


# ---------------------------------------------------------
# MAIN SCENE IMPLEMENTATION
# ---------------------------------------------------------

class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        # 1. Canvas Background Setup
        self.camera.background_color = CANVAS_BG
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















        # System Architecture Center & Radius
        SYS_CENTER = np.array([0.0, -0.6, 0.0])
        ORBIT_RADIUS = 2.4

        # Cardinal Node Positions (West: Perception, South: Memory, North: Reasoning, East: Action)
        POS_W = SYS_CENTER + np.array([-ORBIT_RADIUS, 0, 0])
        POS_S = SYS_CENTER + np.array([0, -ORBIT_RADIUS * 0.85, 0])
        POS_N = SYS_CENTER + np.array([0, ORBIT_RADIUS * 0.85, 0])
        POS_E = SYS_CENTER + np.array([ORBIT_RADIUS, 0, 0])

        # =====================================================
        # ## Presentation Step 1: One Core, Four Pillars
        # =====================================================
        title_group = create_title("One Core, Four Pillars", "Four Pillars of AI Agent Architecture")
        self.play(FadeIn(title_group, shift=DOWN * 0.15), run_time=0.8)

        # Agent Core Orb
        core_outer = Circle(radius=0.85, color=C_STEEL_BLUE, stroke_width=2.5, fill_color=C_CARD_WHITE, fill_opacity=0.95)
        core_inner = Circle(radius=0.65, color=C_SKY_BLUE, stroke_width=1.5, fill_color="#E0F2FE", fill_opacity=0.6)
        core_pulse = Circle(radius=0.95, color=C_SKY_BLUE, stroke_width=1.5, stroke_opacity=0.4)
        core_txt = CrispText("Agent Core", size=15, weight=BOLD, color=C_TITLE_SLATE)
        agent_core = VGroup(core_pulse, core_outer, core_inner, core_txt).move_to(SYS_CENTER)

        # Blueprint Orbital Guide Ring
        orbital_ring = DashedVMobject(Circle(radius=ORBIT_RADIUS, color=C_BORDER_LIGHT, stroke_width=1.5), num_dashes=36)
        orbital_ring.move_to(SYS_CENTER)

        # Four Dormant Quadrant Sockets
        socket_labels = ["Perception", "Memory", "Reasoning", "Action"]
        socket_positions = [POS_W, POS_S, POS_N, POS_E]
        socket_colors = [C_SKY_BLUE, C_LAVENDER, C_WARM_AMBER, C_CORAL]
        dormant_sockets = VGroup()

        for pos, label, col in zip(socket_positions, socket_labels, socket_colors):
            base_circ = Circle(radius=0.55, color=C_BORDER_LIGHT, stroke_width=1.5, fill_color=C_CARD_WHITE, fill_opacity=0.9)
            lbl = CrispText(label, size=12, weight=BOLD, color="#94A3B8")
            lbl.next_to(base_circ, DOWN if pos[1] <= SYS_CENTER[1] else UP, buff=0.15)
            dormant_sockets.add(VGroup(base_circ, lbl).move_to(pos))

        self.play(
            GrowFromCenter(agent_core),
            Create(orbital_ring),
            LaggedStart(*[FadeIn(s, scale=0.8) for s in dormant_sockets], lag_ratio=0.2),
            run_time=2.2
        )

        # West Socket (Perception) brightens with cyan sweep
        west_highlight = Circle(radius=0.62, color=C_SKY_BLUE, stroke_width=3.5).move_to(POS_W)
        west_active_lbl = CrispText("Perception", size=13, weight=BOLD, color=C_SKY_BLUE).move_to(dormant_sockets[0][1].get_center())
        
        self.play(
            Create(west_highlight),
            Transform(dormant_sockets[0][1], west_active_lbl),
            dormant_sockets[0][0].animate.set_stroke(color=C_SKY_BLUE, width=2.5),
            run_time=1.2
        )
        self.wait(1.5)

        # =====================================================
        # ## Presentation Step 2: Perception: Sensing the World
        # =====================================================
        new_title = create_title("Perception: Sensing the World", "Receiving Continuous Environmental Feeds")
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Radar Sweep Dish at West Position
        dish_center = POS_W + LEFT * 0.4
        dish_arc = Arc(radius=0.9, start_angle=-PI/2.5, angle=2*PI/2.5, color=C_SKY_BLUE, stroke_width=3).move_to(dish_center)
        dish_concentric = Arc(radius=0.6, start_angle=-PI/2.5, angle=2*PI/2.5, color=C_STEEL_BLUE, stroke_width=1.8).move_to(dish_center)
        dish_emitter = Dot(point=dish_arc.get_arc_center(), radius=0.08, color=C_SKY_BLUE)
        dish_group = VGroup(dish_arc, dish_concentric, dish_emitter)

        # Telemetry Sensor Card (Solar Installation Data)
        sensor_card_bg = RoundedRectangle(corner_radius=0.1, width=2.4, height=1.1, fill_color=C_CARD_WHITE, fill_opacity=0.95, stroke_color=C_SKY_BLUE, stroke_width=1.5)
        sensor_tag = CrispText("Solar Telemetry", size=13, weight=BOLD, color=C_TITLE_SLATE)
        sensor_metric = CrispText("Feed: 4.8 kW ∿ Live", size=11, weight=NORMAL, color="#0284C7")
        sensor_group_text = VGroup(sensor_tag, sensor_metric).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        fit_into_box(sensor_group_text, sensor_card_bg, pad_x=0.2, pad_y=0.08)
        sensor_card = VGroup(sensor_card_bg, sensor_group_text).arrange(ORIGIN).move_to([-5.2, -0.6, 0])

        # Particle Data Stream from Sensor Card to West Socket
        beam_line = Line(start=sensor_card.get_right(), end=dish_group.get_left(), color=C_SKY_BLUE, stroke_width=2.5)
        pulse_to_core = Arrow(start=POS_W, end=agent_core.get_left(), buff=0.2, color=C_SKY_BLUE, stroke_width=2.5, max_tip_length_to_length_ratio=0.2)

        self.play(
            FadeOut(dormant_sockets[0][0]),
            FadeIn(dish_group, shift=RIGHT * 0.2),
            FadeIn(sensor_card, shift=RIGHT * 0.3),
            Create(beam_line),
            Create(pulse_to_core),
            run_time=1.4
        )

        # Traveling Data Particle
        dot_particle = Dot(color=C_HIGHLIGHT_ORANGE, radius=0.09).move_to(beam_line.get_start())
        self.play(
            dot_particle.animate.move_to(dish_group.get_center()),
            rate_func=linear,
            run_time=0.9
        )
        self.play(
            dot_particle.animate.move_to(agent_core.get_center()),
            agent_core[0].animate.scale(1.1).set_stroke(opacity=0.8),
            run_time=0.8
        )
        self.play(FadeOut(dot_particle), agent_core[0].animate.scale(1/1.1).set_stroke(opacity=0.4), run_time=0.4)
        self.wait(1.0)

        # =====================================================
        # ## Presentation Step 3: Three Input Channels
        # =====================================================
        new_title = create_title("Three Input Channels", "Sensory Convergence: Telemetry, Queries, Triggers")
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Stacked 3 Input Source Channels on Far Left
        ch1 = RoundedRectangle(corner_radius=0.08, width=2.3, height=0.65, fill_color=C_CARD_WHITE, fill_opacity=0.95, stroke_color=C_SKY_BLUE, stroke_width=1.5)
        ch1_txt = CrispText("Solar Ingestion", size=11, weight=BOLD, color=C_TITLE_SLATE).move_to(ch1)
        chan_telemetry = VGroup(ch1, ch1_txt)

        ch2 = RoundedRectangle(corner_radius=0.08, width=2.3, height=0.65, fill_color=C_CARD_WHITE, fill_opacity=0.95, stroke_color=C_STEEL_BLUE, stroke_width=1.5)
        ch2_txt = CrispText("User Query API", size=11, weight=BOLD, color=C_TITLE_SLATE).move_to(ch2)
        chan_query = VGroup(ch2, ch2_txt)

        ch3 = RoundedRectangle(corner_radius=0.08, width=2.3, height=0.65, fill_color=C_CARD_WHITE, fill_opacity=0.95, stroke_color=C_WARM_AMBER, stroke_width=1.5)
        ch3_txt = CrispText("Monitor Trigger", size=11, weight=BOLD, color=C_TITLE_SLATE).move_to(ch3)
        chan_trigger = VGroup(ch3, ch3_txt)

        channels_grp = VGroup(chan_telemetry, chan_query, chan_trigger).arrange(DOWN, buff=0.25).move_to([-5.2, -0.6, 0])

        # Converging Lines into Perception Dish
        line_ch1 = Line(chan_telemetry.get_right(), dish_group.get_left(), color=C_SKY_BLUE, stroke_width=1.8)
        line_ch2 = Line(chan_query.get_right(), dish_group.get_left(), color=C_STEEL_BLUE, stroke_width=1.8)
        line_ch3 = Line(chan_trigger.get_right(), dish_group.get_left(), color=C_WARM_AMBER, stroke_width=1.8)
        converge_lines = VGroup(line_ch1, line_ch2, line_ch3)

        self.play(
            ReplacementTransform(sensor_card, chan_telemetry),
            FadeIn(chan_query, shift=UP * 0.1),
            FadeIn(chan_trigger, shift=DOWN * 0.1),
            ReplacementTransform(beam_line, line_ch1),
            Create(line_ch2),
            Create(line_ch3),
            run_time=1.5
        )

        # Highlight sequence for 3 channels
        for chan in [chan_telemetry, chan_query, chan_trigger]:
            h_pulse = chan[0].copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
            self.play(Create(h_pulse), run_time=0.35)
            self.play(FadeOut(h_pulse), run_time=0.25)

        # Dock Perception cluster cleanly to West and cue Memory layer
        perception_dock = VGroup(dish_group, channels_grp, converge_lines, dormant_sockets[0][1], west_highlight, pulse_to_core)
        
        # South Socket (Memory) lights violet to cue next beat
        south_highlight = Circle(radius=0.62, color=C_LAVENDER, stroke_width=3.5).move_to(POS_S)
        south_active_lbl = CrispText("Memory Layer", size=13, weight=BOLD, color=C_LAVENDER).move_to(dormant_sockets[1][1].get_center())

        self.play(
            perception_dock.animate.scale(0.65).move_to(POS_W + LEFT * 0.2),
            Create(south_highlight),
            Transform(dormant_sockets[1][1], south_active_lbl),
            dormant_sockets[1][0].animate.set_stroke(color=C_LAVENDER, width=2.5),
            run_time=1.4
        )
        self.wait(1.0)

        # =====================================================
        # ## Presentation Step 4: Memory: Two Tiers
        # =====================================================
        new_title = create_title("Memory: Two Tiers", "Short-Term Working Context & Long-Term Vector Store")
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Tier 1: Ephemeral Context Buffer Register (Short-Term)
        tier1_box = RoundedRectangle(corner_radius=0.08, width=3.4, height=1.0, fill_color=C_CARD_WHITE, fill_opacity=0.95, stroke_color=C_LAVENDER, stroke_width=2.0)
        tier1_pill = RoundedRectangle(corner_radius=0.06, width=1.4, height=0.3, fill_color="#EDE9FE", fill_opacity=1.0, stroke_width=0)
        tier1_tag = CrispText("Short-Term", size=11, weight=BOLD, color=C_LAVENDER).move_to(tier1_pill)
        pill1 = VGroup(tier1_pill, tier1_tag).next_to(tier1_box.get_top(), DOWN, buff=0.08)
        
        # Buffer slots
        slots = VGroup(*[RoundedRectangle(corner_radius=0.04, width=0.55, height=0.35, fill_color="#F1F5F9", stroke_color="#CBD5E1", stroke_width=1.0) for _ in range(4)]).arrange(RIGHT, buff=0.15)
        slots.next_to(pill1, DOWN, buff=0.1)
        tier1_group = VGroup(tier1_box, pill1, slots).move_to([0.0, 0.4, 0])

        # Tier 2: Persistent Vector Database Cylinder (Long-Term)
        tier2_box = RoundedRectangle(corner_radius=0.08, width=3.4, height=1.1, fill_color=C_CARD_WHITE, fill_opacity=0.95, stroke_color=C_STEEL_BLUE, stroke_width=2.0)
        tier2_pill = RoundedRectangle(corner_radius=0.06, width=1.4, height=0.3, fill_color="#E0E7FF", fill_opacity=1.0, stroke_width=0)
        tier2_tag = CrispText("Long-Term", size=11, weight=BOLD, color=C_STEEL_BLUE).move_to(tier2_pill)
        pill2 = VGroup(tier2_pill, tier2_tag).next_to(tier2_box.get_top(), DOWN, buff=0.08)
        
        db_rings = VGroup(*[Line(LEFT * 1.3, RIGHT * 1.3, color=C_STEEL_BLUE, stroke_width=1.5) for _ in range(2)]).arrange(DOWN, buff=0.16)
        db_rings.next_to(pill2, DOWN, buff=0.12)
        tier2_group = VGroup(tier2_box, pill2, db_rings).move_to([0.0, -1.3, 0])

        # Bidirectional retrieval arrow between tiers
        bidi_arrow = DoubleArrow(tier1_group.get_bottom(), tier2_group.get_top(), buff=0.12, color=C_HIGHLIGHT_ORANGE, stroke_width=2.5, tip_length=0.18)

        # Context capacity badge
        cap_badge = RoundedRectangle(corner_radius=0.06, width=1.6, height=0.35, fill_color=C_CARD_WHITE, fill_opacity=1.0, stroke_color=C_BORDER_LIGHT, stroke_width=1.2)
        cap_text = CrispText("Capacity: 8k", size=11, weight=BOLD, color=C_TITLE_SLATE).move_to(cap_badge)
        metric_chip = VGroup(cap_badge, cap_text).next_to(tier1_group, RIGHT, buff=0.25)

        self.play(
            agent_core.animate.set_opacity(0.60),
            FadeIn(tier1_group, shift=DOWN * 0.2),
            FadeIn(tier2_group, shift=UP * 0.2),
            Create(bidi_arrow),
            FadeIn(metric_chip, shift=LEFT * 0.2),
            run_time=1.6
        )
        self.wait(1.2)

        # =====================================================
        # ## Presentation Step 5: Memory Keeps Track
        # =====================================================
        new_title = create_title("Memory Keeps Track", "Breadcrumb Trail: Multi-Step Task Tracking")
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Step Breadcrumb Trail Waypoints (Step 1, Step 2, Step 3)
        wp1 = Dot(point=[-1.0, 0.4, 0], radius=0.12, color=C_LAVENDER)
        lbl1 = CrispText("Step 1", size=10, weight=BOLD, color=C_SUB_SLATE).next_to(wp1, UP, buff=0.08)
        wp2 = Dot(point=[0.0, 0.4, 0], radius=0.12, color=C_LAVENDER)
        lbl2 = CrispText("Step 2", size=10, weight=BOLD, color=C_SUB_SLATE).next_to(wp2, UP, buff=0.08)
        wp3 = Dot(point=[1.0, 0.4, 0], radius=0.12, color=C_LAVENDER)
        lbl3 = CrispText("Step 3", size=10, weight=BOLD, color=C_SUB_SLATE).next_to(wp3, UP, buff=0.08)
        
        trail_line = DashedLine(wp1.get_center(), wp3.get_center(), color=C_LAVENDER, stroke_width=2.0)
        breadcrumbs = VGroup(trail_line, wp1, lbl1, wp2, lbl2, wp3, lbl3)

        # "You Are Here" Marker with Pulse
        active_marker = Circle(radius=0.18, color=C_HIGHLIGHT_ORANGE, stroke_width=3.0).move_to(wp2.get_center())
        yah_badge = RoundedRectangle(corner_radius=0.04, width=1.1, height=0.28, fill_color=C_CARD_WHITE, stroke_color=C_HIGHLIGHT_ORANGE, stroke_width=1.0)
        yah_lbl = CrispText("Active", size=10, weight=BOLD, color=C_HIGHLIGHT_ORANGE).move_to(yah_badge)
        active_indicator = VGroup(active_marker, VGroup(yah_badge, yah_lbl).next_to(active_marker, DOWN, buff=0.08))

        self.play(
            FadeIn(breadcrumbs),
            Create(active_indicator),
            run_time=1.2
        )

        # Pulse database cylinder to show state read
        db_pulse = tier2_box.copy().set_fill(opacity=0).set_stroke(color=C_STEEL_BLUE, width=3.5)
        self.play(
            active_marker.animate.move_to(wp3.get_center()),
            active_indicator[1].animate.next_to(wp3, DOWN, buff=0.08),
            Create(db_pulse),
            run_time=1.2
        )
        self.play(FadeOut(db_pulse), run_time=0.4)

        # Consolidate and Dock Memory to South position
        memory_cluster = VGroup(tier1_group, tier2_group, bidi_arrow, metric_chip, breadcrumbs, active_indicator)
        
        # North Socket (Reasoning) lights amber to cue next beat
        north_highlight = Circle(radius=0.62, color=C_WARM_AMBER, stroke_width=3.5).move_to(POS_N)
        north_active_lbl = CrispText("Reasoning Engine", size=13, weight=BOLD, color=C_WARM_AMBER).move_to(dormant_sockets[2][1].get_center())

        self.play(
            memory_cluster.animate.scale(0.4).move_to(POS_S),
            agent_core.animate.set_opacity(0.95),
            Create(north_highlight),
            Transform(dormant_sockets[2][1], north_active_lbl),
            dormant_sockets[2][0].animate.set_stroke(color=C_WARM_AMBER, width=2.5),
            run_time=1.5
        )
        self.wait(1.0)

        # =====================================================
        # ## Presentation Step 6: Reasoning: The LLM Engine
        # =====================================================
        new_title = create_title("Reasoning: The LLM Engine", "Cognitive Deliberation: Interpret, Decide, Select Tool")
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Central LLM Processor Lattice Die
        die_bg = RoundedRectangle(corner_radius=0.12, width=4.8, height=2.0, fill_color=C_CARD_WHITE, fill_opacity=0.98, stroke_color=C_WARM_AMBER, stroke_width=2.5).move_to(SYS_CENTER + UP * 0.1)
        die_header = CrispText("LLM Cognition Core", size=14, weight=BOLD, color=C_TITLE_SLATE).next_to(die_bg.get_top(), DOWN, buff=0.12)
        
        # 3-Stage Pipeline: Interpret -> Decide -> Select Tool
        stg1 = RoundedRectangle(corner_radius=0.06, width=1.2, height=0.75, fill_color="#FEF3C7", stroke_color=C_WARM_AMBER, stroke_width=1.2)
        t_stg1 = CrispText("1. Interpret", size=11, weight=BOLD, color=C_TITLE_SLATE).move_to(stg1)
        p1 = VGroup(stg1, t_stg1)

        stg2 = RoundedRectangle(corner_radius=0.06, width=1.2, height=0.75, fill_color="#FEF3C7", stroke_color=C_WARM_AMBER, stroke_width=1.2)
        t_stg2 = CrispText("2. Decide", size=11, weight=BOLD, color=C_TITLE_SLATE).move_to(stg2)
        p2 = VGroup(stg2, t_stg2)

        stg3 = RoundedRectangle(corner_radius=0.06, width=1.3, height=0.75, fill_color="#FEF3C7", stroke_color=C_WARM_AMBER, stroke_width=1.2)
        t_stg3 = CrispText("3. Select Tool", size=11, weight=BOLD, color=C_TITLE_SLATE).move_to(stg3)
        p3 = VGroup(stg3, t_stg3)

        pipeline_grp = VGroup(p1, p2, p3).arrange(RIGHT, buff=0.25).move_to(SYS_CENTER + DOWN * 0.1)

        # Confidence Badge
        conf_pill = RoundedRectangle(corner_radius=0.05, width=1.8, height=0.3, fill_color=C_CARD_WHITE, stroke_color=C_BORDER_LIGHT, stroke_width=1.0)
        conf_txt = CrispText("Confidence: 0.94", size=11, weight=BOLD, color="#B45309").move_to(conf_pill)
        conf_badge = VGroup(conf_pill, conf_txt).next_to(die_bg, UP, buff=0.12)

        # Three Tool Icons on Right Edge
        t_icon1 = RoundedRectangle(corner_radius=0.05, width=0.8, height=0.45, fill_color=C_CARD_WHITE, stroke_color=C_BORDER_LIGHT, stroke_width=1.2)
        l_ic1 = CrispText("Query", size=10, weight=BOLD, color=C_TITLE_SLATE).move_to(t_icon1)
        tool1 = VGroup(t_icon1, l_ic1)

        t_icon2 = RoundedRectangle(corner_radius=0.05, width=0.8, height=0.45, fill_color=C_CARD_WHITE, stroke_color=C_HIGHLIGHT_ORANGE, stroke_width=1.8)
        l_ic2 = CrispText("API", size=10, weight=BOLD, color=C_HIGHLIGHT_ORANGE).move_to(t_icon2)
        tool2 = VGroup(t_icon2, l_ic2)

        t_icon3 = RoundedRectangle(corner_radius=0.05, width=0.8, height=0.45, fill_color=C_CARD_WHITE, stroke_color=C_BORDER_LIGHT, stroke_width=1.2)
        l_ic3 = CrispText("File", size=10, weight=BOLD, color=C_TITLE_SLATE).move_to(t_icon3)
        tool3 = VGroup(t_icon3, l_ic3)

        tool_fan = VGroup(tool1, tool2, tool3).arrange(DOWN, buff=0.15).next_to(die_bg, RIGHT, buff=0.25)

        self.play(
            agent_core.animate.set_opacity(0.60),
            FadeIn(die_bg),
            FadeIn(die_header),
            FadeIn(pipeline_grp, shift=RIGHT * 0.1),
            FadeIn(conf_badge),
            FadeIn(tool_fan, shift=LEFT * 0.1),
            run_time=1.6
        )

        # Stage Progression Highlight
        for stage in [p1, p2, p3]:
            h = stage[0].copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.0)
            self.play(Create(h), run_time=0.35)
            self.play(FadeOut(h), run_time=0.25)

        # Highlight Selected Tool ("API")
        tool_hl = tool2.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT_ORANGE, width=3.5)
        self.play(Create(tool_hl), run_time=0.5)
        self.wait(1.0)

        # =====================================================
        # ## Presentation Step 7: Action: Doing Something
        # =====================================================
        new_title = create_title("Action: Doing Something", "Actuator Layer: Executing Tool Operations")
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Contract Reasoning Die and dock to North position
        reasoning_cluster = VGroup(die_bg, die_header, pipeline_grp, conf_badge, tool_fan, tool_hl)
        
        # East Socket (Action Layer) expands into Mechanical API Dispatch Hub
        act_hub_bg = RoundedRectangle(corner_radius=0.12, width=3.6, height=2.2, fill_color=C_CARD_WHITE, fill_opacity=0.98, stroke_color=C_CORAL, stroke_width=2.5).move_to(POS_E + LEFT * 0.2)
        act_title = CrispText("Action Dispatch Hub", size=13, weight=BOLD, color=C_TITLE_SLATE).next_to(act_hub_bg.get_top(), DOWN, buff=0.12)
        
        # Central Dial Indicator
        act_dial_rim = Circle(radius=0.45, color=C_CORAL, stroke_width=2.0)
        act_dial_needle = Line(ORIGIN, UP * 0.35, color=C_HIGHLIGHT_ORANGE, stroke_width=3.0)
        dial_grp = VGroup(act_dial_rim, act_dial_needle).move_to(act_hub_bg.get_center() + LEFT * 0.7)

        # Status Pill: [Active]
        status_pill = RoundedRectangle(corner_radius=0.06, width=1.2, height=0.35, fill_color="#FEE2E2", stroke_color=C_CORAL, stroke_width=1.2)
        status_lbl = CrispText("Active", size=11, weight=BOLD, color="#B91C1C").move_to(status_pill)
        status_grp = VGroup(status_pill, status_lbl).next_to(act_hub_bg.get_center() + RIGHT * 0.6, UP, buff=0.05)

        # Levers / Ports
        lever1 = Line(LEFT * 0.3, RIGHT * 0.3, color=C_CORAL, stroke_width=2.5)
        lever2 = Line(LEFT * 0.3, RIGHT * 0.3, color=C_CORAL, stroke_width=2.5)
        levers_grp = VGroup(lever1, lever2).arrange(DOWN, buff=0.2).next_to(status_grp, DOWN, buff=0.15)

        act_hub_full = VGroup(act_hub_bg, act_title, dial_grp, status_grp, levers_grp)

        # Command Packet traveling from LLM Die to Action Hub
        cmd_packet = RoundedRectangle(corner_radius=0.04, width=0.9, height=0.3, fill_color=C_HIGHLIGHT_ORANGE, fill_opacity=1.0, stroke_width=0)
        cmd_txt = CrispText("Execute", size=9, weight=BOLD, color=C_CARD_WHITE).move_to(cmd_packet)
        cmd_obj = VGroup(cmd_packet, cmd_txt).move_to(SYS_CENTER)

        self.play(
            reasoning_cluster.animate.scale(0.35).move_to(POS_N),
            FadeIn(act_hub_full, shift=LEFT * 0.2),
            Create(cmd_obj),
            dormant_sockets[3].animate.set_opacity(0.60),
            agent_core.animate.set_opacity(0.85),
            run_time=1.6
        )

        # Command arrives into Action Hub, dial turns
        self.play(
            cmd_obj.animate.move_to(act_hub_bg.get_center()),
            act_dial_needle.animate.rotate(-PI / 3, about_point=act_dial_rim.get_center()),
            run_time=0.9
        )
        self.play(FadeOut(cmd_obj), run_time=0.3)
        self.wait(1.0)

        # =====================================================
        # ## Presentation Step 8: The Continuous Loop
        # =====================================================
        new_title = create_title("The Continuous Loop", "Autonomous Circuit: Perceive → Remember → Reason → Act")
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Shrink Action Hub to standard East Pillar Node
        self.play(
            act_hub_full.animate.scale(0.38).move_to(POS_E),
            run_time=1.0
        )

        # Re-establish 4 Balanced Pillar Stations with High-Craft Vector Cards
        p_card = RoundedRectangle(corner_radius=0.08, width=1.8, height=0.8, fill_color=C_CARD_WHITE, fill_opacity=0.98, stroke_color=C_SKY_BLUE, stroke_width=2.0).move_to(POS_W)
        p_t1 = CrispText("1. Perceive", size=12, weight=BOLD, color=C_SKY_BLUE).next_to(p_card.get_top(), DOWN, buff=0.1)
        p_t2 = CrispText("Sense Inputs", size=10, weight=NORMAL, color=C_SUB_SLATE).next_to(p_t1, DOWN, buff=0.05)
        pillar_perceive = VGroup(p_card, p_t1, p_t2)

        m_card = RoundedRectangle(corner_radius=0.08, width=1.8, height=0.8, fill_color=C_CARD_WHITE, fill_opacity=0.98, stroke_color=C_LAVENDER, stroke_width=2.0).move_to(POS_S)
        m_t1 = CrispText("2. Remember", size=12, weight=BOLD, color=C_LAVENDER).next_to(m_card.get_top(), DOWN, buff=0.1)
        m_t2 = CrispText("State & Vectors", size=10, weight=NORMAL, color=C_SUB_SLATE).next_to(m_t1, DOWN, buff=0.05)
        pillar_remember = VGroup(m_card, m_t1, m_t2)

        r_card = RoundedRectangle(corner_radius=0.08, width=1.8, height=0.8, fill_color=C_CARD_WHITE, fill_opacity=0.98, stroke_color=C_WARM_AMBER, stroke_width=2.0).move_to(POS_N)
        r_t1 = CrispText("3. Reason", size=12, weight=BOLD, color=C_WARM_AMBER).next_to(r_card.get_top(), DOWN, buff=0.1)
        r_t2 = CrispText("LLM Cognition", size=10, weight=NORMAL, color=C_SUB_SLATE).next_to(r_t1, DOWN, buff=0.05)
        pillar_reason = VGroup(r_card, r_t1, r_t2)

        a_card = RoundedRectangle(corner_radius=0.08, width=1.8, height=0.8, fill_color=C_CARD_WHITE, fill_opacity=0.98, stroke_color=C_CORAL, stroke_width=2.0).move_to(POS_E)
        a_t1 = CrispText("4. Act", size=12, weight=BOLD, color=C_CORAL).next_to(a_card.get_top(), DOWN, buff=0.1)
        a_t2 = CrispText("Tools & APIs", size=10, weight=NORMAL, color=C_SUB_SLATE).next_to(a_t1, DOWN, buff=0.05)
        pillar_act = VGroup(a_card, a_t1, a_t2)

        pillars_balanced = VGroup(pillar_perceive, pillar_remember, pillar_reason, pillar_act)

        # Continuous Orbital Closed-Loop Ribbon (Curved Arrows connecting 4 pillars in circular flow)
        arc_w_to_n = CurvedArrow(POS_W + UP * 0.45, POS_N + LEFT * 0.9, radius=2.3, color=C_SKY_BLUE, stroke_width=2.5)
        arc_n_to_e = CurvedArrow(POS_N + RIGHT * 0.9, POS_E + UP * 0.45, radius=2.3, color=C_WARM_AMBER, stroke_width=2.5)
        arc_e_to_s = CurvedArrow(POS_E + DOWN * 0.45, POS_S + RIGHT * 0.9, radius=2.3, color=C_CORAL, stroke_width=2.5)
        arc_s_to_w = CurvedArrow(POS_S + LEFT * 0.9, POS_W + DOWN * 0.45, radius=2.3, color=C_LAVENDER, stroke_width=2.5)
        loop_ribbon = VGroup(arc_w_to_n, arc_n_to_e, arc_e_to_s, arc_s_to_w)

        # Loop Cycle Counter Badge
        cycle_badge = RoundedRectangle(corner_radius=0.06, width=2.4, height=0.45, fill_color=C_CARD_WHITE, fill_opacity=1.0, stroke_color=C_SKY_BLUE, stroke_width=1.5)
        cycle_txt = CrispText("Loop State: Active Cycle", size=12, weight=BOLD, color=C_TITLE_SLATE).move_to(cycle_badge)
        cycle_chip = VGroup(cycle_badge, cycle_txt).move_to(SYS_CENTER + DOWN * 1.5)

        self.play(
            FadeOut(perception_dock),
            FadeOut(memory_cluster),
            FadeOut(reasoning_cluster),
            FadeOut(act_hub_full),
            FadeOut(dormant_sockets),
            FadeIn(pillars_balanced),
            agent_core.animate.set_opacity(1.0),
            Create(loop_ribbon),
            FadeIn(cycle_chip, shift=UP * 0.1),
            run_time=2.0
        )

        # Dynamic Pulse Indicator traveling around the continuous loop
        loop_dot = Dot(color=C_HIGHLIGHT_ORANGE, radius=0.1)
        self.play(MoveAlongPath(loop_dot, arc_w_to_n, rate_func=linear), run_time=0.8)
        self.play(MoveAlongPath(loop_dot, arc_n_to_e, rate_func=linear), run_time=0.8)
        self.play(MoveAlongPath(loop_dot, arc_e_to_s, rate_func=linear), run_time=0.8)
        self.play(MoveAlongPath(loop_dot, arc_s_to_w, rate_func=linear), run_time=0.8)
        self.play(FadeOut(loop_dot), run_time=0.3)

        # Subtle Core Breathing Pulse
        self.play(
            agent_core[0].animate.scale(1.15).set_stroke(color=C_HIGHLIGHT_ORANGE, width=2.5),
            run_time=0.7
        )
        self.play(
            agent_core[0].animate.scale(1/1.15).set_stroke(color=C_SKY_BLUE, width=1.5),
            run_time=0.7
        )
        self.wait(2.5)