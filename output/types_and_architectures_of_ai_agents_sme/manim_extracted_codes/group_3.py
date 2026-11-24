SME_LAYOUT = '20'
from feedback_functions_vlm.instrumented_scene import InstrumentedScene
import os
import re
import numpy as np
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

class PulsingShockwaves(VGroup):
    def __init__(self, center, color="#E6A157", max_radius=1.1, num_rings=3, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.color = color
        self.max_radius = max_radius
        self.num_rings = num_rings
        self.rings = [Circle(radius=0.2 + i * 0.3, color=color, stroke_width=2.0).move_to(self.center_pt) for i in range(num_rings)]
        self.add(*self.rings)
        self.t = 0.0
        def update_waves(mob, dt):
            mob.t += dt
            for i, ring in enumerate(mob.rings):
                phase = (mob.t * 0.9 + i / float(mob.num_rings)) % 1.0
                r = 0.25 + phase * (mob.max_radius - 0.25)
                ring.become(Circle(radius=r, color=mob.color, stroke_width=2.5 * (1.0 - phase)).move_to(mob.center_pt))
                ring.set_stroke(opacity=max(0.0, 1.0 - phase))
        self.add_updater(update_waves)

class DynamicRadarSweep(VGroup):
    def __init__(self, center, radius=0.9, color="#62B7E4", speed=3.0, **kwargs):
        super().__init__(**kwargs)
        self.center_pt = np.array(center)
        self.radius = radius
        self.speed = speed
        self.dish = Circle(radius=radius, fill_color="#E0F2FE", fill_opacity=0.85, stroke_width=0).move_to(self.center_pt)
        self.bezel = Circle(radius=radius, color=color, stroke_width=2.2).move_to(self.center_pt)
        self.r1 = Circle(radius=radius*0.45, color=color, stroke_width=1.0, stroke_opacity=0.5).move_to(self.center_pt)
        self.cross_h = Line(self.center_pt - np.array([radius, 0, 0]), self.center_pt + np.array([radius, 0, 0]), color="#BACAD8", stroke_width=0.8, stroke_opacity=0.6)
        self.cross_v = Line(self.center_pt - np.array([0, radius, 0]), self.center_pt + np.array([0, radius, 0]), color="#BACAD8", stroke_width=0.8, stroke_opacity=0.6)
        self.sweep_line = Line(self.center_pt, self.center_pt + np.array([radius, 0, 0]), color="#F78908", stroke_width=2.4)
        self.blip = Dot(self.center_pt + np.array([0.45*radius, 0.4*radius, 0]), radius=0.05, color="#F78908")
        self.add(self.dish, self.bezel, self.r1, self.cross_h, self.cross_v, self.blip, self.sweep_line)
        self.angle = 0.0
        def update_sweep(mob, dt):
            mob.angle = (mob.angle + mob.speed * dt) % (2 * PI)
            end_pt = mob.center_pt + mob.radius * np.array([np.cos(mob.angle), np.sin(mob.angle), 0])
            mob.sweep_line.set_points_by_ends(mob.center_pt, end_pt)
            d = (mob.angle - 0.7) % (2 * PI)
            mob.blip.set_opacity(max(0.2, 1.0 - d * 0.5))
        self.add_updater(update_sweep)

class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        # 1. Canvas Background Setup (Pure White per directive)
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


        # Color Palette Definitions (10-Color Palette & Accents)
        C_CHARCOAL = "#404040"
        C_SLATE_TITLE = "#0F172A"
        C_SLATE_BODY = "#334155"
        C_CYAN_SKY = "#62B7E4"
        C_STEEL_BLUE = "#7EA2C8"
        C_LAVENDER = "#9B99C7"
        C_AMBER = "#E6A157"
        C_CORAL = "#E58F6D"
        C_ORANGE_PULSE = "#F78908"
        C_CARD_BG = "#FFFFFF"
        C_CARD_BORDER = "#D9E2EC"


        def make_socket(pos, label, accent_col):
            dot = Dot(radius=0.10, color=accent_col)
            txt = CrispText(label, size=12, weight=BOLD, color=C_CHARCOAL)
            content = VGroup(dot, txt).arrange(RIGHT, buff=0.12)
            w = max(content.width + 0.55, 2.2)
            h = max(content.height + 0.25, 0.70)
            bg = RoundedRectangle(width=w, height=h, corner_radius=0.15, color=C_CARD_BORDER, stroke_width=1.5, fill_color=C_CARD_BG, fill_opacity=0.95)
            fit_into_box(content, bg)
            card = VGroup(bg, content).move_to(pos)
            card.set_z_index(10)
            return card

        # -------------------------------------------------------------
        ## Presentation Step 1: One Core, Four Pillars (run_time: 65.22)
        # -------------------------------------------------------------
        t_start = self.renderer.time
        title_group = create_title(
            "Types And Architectures Of Ai Agents",
            "One Core, Four Pillars"
        )
        self.play(FadeIn(title_group, shift=DOWN * 0.1), run_time=0.8)

        center_pos = np.array([0.0, -0.5, 0.0])
        orbit_radius = 3.2

        orbit_circle = DashedVMobject(
            Circle(radius=orbit_radius, color="#CBD5E1", stroke_width=2.0),
            num_dashes=48
        ).move_to(center_pos)

        core_outer = Circle(radius=0.85, color=C_STEEL_BLUE, stroke_width=2.5, fill_color="#F0F4F8", fill_opacity=0.6).move_to(center_pos)
        core_inner = Circle(radius=0.65, color=C_CYAN_SKY, stroke_width=2, fill_color="#FFFFFF", fill_opacity=0.95).move_to(center_pos)
        core_lbl = CrispText("Agent Core", size=14, weight=BOLD, color=C_CHARCOAL).move_to(center_pos)
        agent_core = VGroup(core_outer, core_inner, core_lbl).set_z_index(12)

        # Quadrant Sockets (West: Perception, North: Reasoning, East: Action, South-East: Memory)
        pos_west = center_pos + np.array([-orbit_radius, 0, 0])
        pos_north = center_pos + np.array([0, orbit_radius * 0.85, 0])
        pos_east = center_pos + np.array([orbit_radius, 0, 0])
        pos_se = center_pos + np.array([orbit_radius * 0.707, -orbit_radius * 0.707, 0])

        sock_w = make_socket(pos_west, "Perception", C_CYAN_SKY)
        sock_se = make_socket(pos_se, "Memory Layer", C_LAVENDER)
        sock_n = make_socket(pos_north, "Reasoning Engine", C_AMBER)
        sock_e = make_socket(pos_east, "Action Layer", C_CORAL)

        self.play(
            Create(orbit_circle),
            FadeIn(agent_core, scale=0.85),
            run_time=1.2
        )
        self.play(
            LaggedStart(
                FadeIn(sock_w, shift=RIGHT * 0.2),
                FadeIn(sock_se, shift=UP * 0.2),
                FadeIn(sock_n, shift=DOWN * 0.2),
                FadeIn(sock_e, shift=LEFT * 0.2),
                lag_ratio=0.25
            ),
            run_time=1.4
        )

        west_highlight = sock_w.copy().set_fill(opacity=0).set_stroke(color=C_CYAN_SKY, width=3.5)
        self.play(Create(west_highlight), run_time=0.8)
        self.play(FadeOut(west_highlight), run_time=0.5)

        # Sync wait time for Step 1 target 65.22s
        elapsed = self.renderer.time - t_start
        if elapsed < 65.22:
            self.wait(65.22 - elapsed)

        # -------------------------------------------------------------
        ## Presentation Step 2: Perception: Sensing the World (run_time: 11.5)
        # -------------------------------------------------------------
        t_start = self.renderer.time
        new_title = create_title(
            "Perception: Sensing The World",
            "Radar Sensing And Incoming Solar Feeds"
        )
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Dynamic Radar Sweep dish
        radar_sweep = DynamicRadarSweep(center=pos_west, radius=0.9, color=C_CYAN_SKY).set_z_index(15)

        # Solar Telemetry Source Anchor (Floating open space layout)
        solar_lbl = CrispText("Solar Ingestion", size=12, weight=BOLD, color=C_CHARCOAL)
        solar_sub = CrispText("Telemetry: 482 kW", size=10, weight=NORMAL, color=C_SLATE_BODY)
        solar_content = VGroup(solar_lbl, solar_sub).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        solar_panel_grp = solar_content.move_to(pos_west + LEFT * 2.1 + UP * 0.3)

        conduit_west = Arrow(solar_panel_grp.get_right(), pos_west + LEFT * 0.9, buff=0.1, color=C_CYAN_SKY, stroke_width=2.5, max_tip_length_to_length_ratio=0.12)

        self.play(
            sock_w.animate.scale(0.85).shift(UP * 1.0),
            FadeIn(radar_sweep, scale=0.8),
            FadeIn(solar_panel_grp, shift=DOWN * 0.2),
            Create(conduit_west),
            run_time=1.4
        )

        pulse_p1 = Dot(solar_panel_grp.get_right(), color=C_ORANGE_PULSE, radius=0.09)
        self.play(MoveAlongPath(pulse_p1, conduit_west), run_time=1.2)
        self.remove(pulse_p1)

        core_shock = PulsingShockwaves(center_pos, color=C_CYAN_SKY, max_radius=1.2, num_rings=2)
        self.add(core_shock)
        self.wait(1.0)
        self.remove(core_shock)

        elapsed = self.renderer.time - t_start
        if elapsed < 11.5:
            self.wait(11.5 - elapsed)

        # -------------------------------------------------------------
        ## Presentation Step 3: Three Input Channels (run_time: 10.5)
        # -------------------------------------------------------------
        t_start = self.renderer.time
        new_title = create_title(
            "Three Input Channels",
            "Telemetry, User Queries, And System Triggers"
        )
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Floating input channel labels
        query_lbl = CrispText("User Query", size=12, weight=BOLD, color=C_STEEL_BLUE).move_to(pos_west + LEFT * 2.1 + DOWN * 0.4)
        trigger_lbl = CrispText("System Trigger", size=12, weight=BOLD, color=C_AMBER).move_to(pos_west + LEFT * 2.1 + DOWN * 1.2)

        conduit_q = CurvedArrow(query_lbl.get_right(), pos_west + DOWN * 0.6, angle=-PI/4, color=C_STEEL_BLUE, stroke_width=2)
        conduit_t = CurvedArrow(trigger_lbl.get_right(), pos_west + DOWN * 0.8, angle=-PI/3, color=C_AMBER, stroke_width=2)

        self.play(FadeIn(query_lbl, shift=UP * 0.15), Create(conduit_q), run_time=0.8)
        self.play(FadeIn(trigger_lbl, shift=UP * 0.15), Create(conduit_t), run_time=0.8)

        perception_cluster = VGroup(sock_w, radar_sweep, solar_panel_grp, query_lbl, trigger_lbl, conduit_west, conduit_q, conduit_t)
        
        docked_p_bg = RoundedRectangle(width=2.1, height=0.72, corner_radius=0.15, color=C_CYAN_SKY, stroke_width=2, fill_color=C_CARD_BG, fill_opacity=0.95)
        docked_p_txt = CrispText("Perception Dock", size=12, weight=BOLD, color=C_CHARCOAL)
        fit_into_box(docked_p_txt, docked_p_bg, pad_x=0.2, pad_y=0.08)
        docked_perception = VGroup(docked_p_bg, docked_p_txt).arrange(ORIGIN).move_to(pos_west).set_z_index(15)

        # Fix: Replaced ReplacementTransform with FadeOut and FadeIn due to differing VGroup structures
        self.play(
            FadeOut(perception_cluster),
            FadeIn(docked_perception),
            run_time=1.4
        )

        mem_pulse = sock_se.copy().set_fill(opacity=0).set_stroke(color=C_LAVENDER, width=3.5)
        self.play(Create(mem_pulse), run_time=0.7)
        self.play(FadeOut(mem_pulse), run_time=0.4)

        elapsed = self.renderer.time - t_start
        if elapsed < 10.5:
            self.wait(10.5 - elapsed)

        # -------------------------------------------------------------
        ## Presentation Step 4: Memory: Two Tiers (run_time: 10.5)
        # -------------------------------------------------------------
        t_start = self.renderer.time
        new_title = create_title(
            "Memory: Two Tiers",
            "Short-Term Context Buffer And Long-Term Vector Store"
        )
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        # Fade out core and orbit circle so memory takes center stage without overlaps
        self.play(
            FadeOut(agent_core),
            FadeOut(orbit_circle),
            run_time=0.6
        )

        mem_center = np.array([0.0, -0.4, 0.0])

        # Short-Term Buffer Box
        cbuf_box = RoundedRectangle(width=4.0, height=1.0, corner_radius=0.15, color=C_STEEL_BLUE, stroke_width=1.5, fill_color=C_CARD_BG, fill_opacity=0.95)
        cbuf_title = CrispText("Short-Term Buffer", size=13, weight=BOLD, color=C_CHARCOAL)
        slots = VGroup(*[
            RoundedRectangle(width=0.55, height=0.32, corner_radius=0.08, color="#CBD5E1", stroke_width=1, fill_color="#F1F5F9", fill_opacity=0.9)
            for _ in range(4)
        ]).arrange(RIGHT, buff=0.1)
        ctx_tag = CrispText("Context: 8k", size=11, weight=BOLD, color=C_ORANGE_PULSE)
        cbuf_content = VGroup(cbuf_title, VGroup(slots, ctx_tag).arrange(RIGHT, buff=0.2)).arrange(DOWN, buff=0.12)
        cbuf_grp = VGroup(cbuf_box, cbuf_content).arrange(ORIGIN).move_to(mem_center + UP * 0.9)

        # Long-Term Substrate Box
        vdb_box = RoundedRectangle(width=4.0, height=1.1, corner_radius=0.15, color=C_LAVENDER, stroke_width=1.5, fill_color=C_CARD_BG, fill_opacity=0.95)
        vdb_title = CrispText("Long-Term Substrate", size=13, weight=BOLD, color=C_CHARCOAL)
        vdb_sub = CrispText("External Disk  |  Persistent Embeddings", size=11, weight=NORMAL, color=C_SLATE_BODY)
        vdb_content = VGroup(vdb_title, vdb_sub).arrange(DOWN, buff=0.12)
        vdb_grp = VGroup(vdb_box, vdb_content).arrange(ORIGIN).move_to(mem_center + DOWN * 0.8)

        sync_arrow = DoubleArrow(cbuf_box.get_bottom(), vdb_box.get_top(), buff=0.18, color=C_ORANGE_PULSE, stroke_width=2.5, max_tip_length_to_length_ratio=0.18)
        sync_lbl = CrispText("Retrieval & Write", size=11, weight=BOLD, color=C_ORANGE_PULSE).next_to(sync_arrow, RIGHT, buff=0.15)

        self.play(
            FadeIn(cbuf_grp, shift=DOWN * 0.2),
            FadeIn(vdb_grp, shift=UP * 0.2),
            Create(sync_arrow),
            FadeIn(sync_lbl),
            run_time=1.4
        )

        elapsed = self.renderer.time - t_start
        if elapsed < 10.5:
            self.wait(10.5 - elapsed)

        # -------------------------------------------------------------
        ## Presentation Step 5: Memory Keeps Track (run_time: 10.0)
        # -------------------------------------------------------------
        t_start = self.renderer.time
        new_title = create_title(
            "Memory Keeps Track",
            "Multi-Step Trajectory Without Context Loss"
        )
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        wp1 = Dot(mem_center + UP * 0.9 + LEFT * 1.2, radius=0.12, color=C_CYAN_SKY)
        wp2 = Dot(mem_center + UP * 0.9, radius=0.12, color=C_STEEL_BLUE)
        wp3 = Dot(mem_center + UP * 0.9 + RIGHT * 1.2, radius=0.12, color=C_AMBER)
        t1 = CrispText("Step 1", size=9, weight=BOLD, color=C_CHARCOAL).next_to(wp1, UP, buff=0.08)
        t2 = CrispText("Step 2", size=9, weight=BOLD, color=C_CHARCOAL).next_to(wp2, UP, buff=0.08)
        t3 = CrispText("Step 3", size=9, weight=BOLD, color=C_CHARCOAL).next_to(wp3, UP, buff=0.08)
        trail_line = DashedLine(wp1.get_center(), wp3.get_center(), color=C_STEEL_BLUE, stroke_width=2)
        breadcrumb_grp = VGroup(trail_line, wp1, wp2, wp3, t1, t2, t3)

        current_marker_ring = Circle(radius=0.18, color=C_ORANGE_PULSE, stroke_width=2.5).move_to(wp1.get_center())
        current_marker_lbl = CrispText("Current State", size=9, weight=BOLD, color=C_ORANGE_PULSE).next_to(current_marker_ring, DOWN, buff=0.08)
        current_marker = VGroup(current_marker_ring, current_marker_lbl)

        vdb_pulse = PulsingShockwaves(vdb_box.get_center(), color=C_LAVENDER, max_radius=1.5, num_rings=2)

        # FIX: self.add(vdb_pulse) cannot be passed directly as an argument to self.play().
        # It should be called before play if the mobject is to appear instantly, or wrapped in an animation like Create/FadeIn.
        self.add(vdb_pulse) 
        self.play(
            FadeIn(breadcrumb_grp),
            FadeIn(current_marker),
            run_time=1.2
        )
        self.play(
            current_marker.animate.move_to(wp2.get_center()),
            run_time=1.0
        )
        self.remove(vdb_pulse)

        docked_mem_bg = RoundedRectangle(width=2.1, height=0.72, corner_radius=0.15, color=C_LAVENDER, stroke_width=2, fill_color=C_CARD_BG, fill_opacity=0.95)
        docked_mem_txt = CrispText("Memory Dock", size=12, weight=BOLD, color=C_CHARCOAL)
        fit_into_box(docked_mem_txt, docked_mem_bg, pad_x=0.2, pad_y=0.08)
        docked_mem = VGroup(docked_mem_bg, docked_mem_txt).arrange(ORIGIN).move_to(pos_se).set_z_index(15)

        full_mem_cluster = VGroup(cbuf_grp, vdb_grp, sync_arrow, sync_lbl, breadcrumb_grp, current_marker)

        # Fix: Replaced ReplacementTransform with FadeOut and FadeIn due to differing VGroup structures
        self.play(
            FadeOut(full_mem_cluster),
            FadeIn(docked_mem),
            FadeIn(agent_core),
            FadeIn(orbit_circle),
            run_time=1.4
        )

        reason_pulse = sock_n.copy().set_fill(opacity=0).set_stroke(color=C_AMBER, width=3.5)
        self.play(Create(reason_pulse), run_time=0.6)
        self.play(FadeOut(reason_pulse), run_time=0.4)

        elapsed = self.renderer.time - t_start
        if elapsed < 10.0:
            self.wait(10.0 - elapsed)

        # -------------------------------------------------------------
        ## Presentation Step 6: Reasoning: The LLM Engine (run_time: 13.0)
        # -------------------------------------------------------------
        t_start = self.renderer.time
        new_title = create_title(
            "Reasoning: The LLM Engine",
            "Deliberation: Interpret, Decide, And Tool Selection"
        )
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        self.play(
            FadeOut(agent_core),
            FadeOut(orbit_circle),
            run_time=0.5
        )

        die_box = RoundedRectangle(width=4.8, height=2.2, corner_radius=0.2, color=C_AMBER, stroke_width=2, fill_color=C_CARD_BG, fill_opacity=0.95).move_to(center_pos)
        die_title = CrispText("LLM Reasoning Engine", size=14, weight=BOLD, color=C_CHARCOAL).next_to(die_box.get_top(), DOWN, buff=0.18)

        s1 = VGroup(RoundedRectangle(width=1.25, height=0.55, corner_radius=0.1, color=C_CYAN_SKY, stroke_width=1.5, fill_color="#F8FAFC", fill_opacity=0.9), CrispText("1. Interpret", size=10, weight=BOLD, color=C_CHARCOAL)).arrange(ORIGIN)
        s2 = VGroup(RoundedRectangle(width=1.25, height=0.55, corner_radius=0.1, color=C_STEEL_BLUE, stroke_width=1.5, fill_color="#F8FAFC", fill_opacity=0.9), CrispText("2. Decide", size=10, weight=BOLD, color=C_CHARCOAL)).arrange(ORIGIN)
        s3 = VGroup(RoundedRectangle(width=1.35, height=0.55, corner_radius=0.1, color=C_AMBER, stroke_width=1.5, fill_color="#F8FAFC", fill_opacity=0.9), CrispText("3. Select Tool", size=10, weight=BOLD, color=C_CHARCOAL)).arrange(ORIGIN)
        pipeline_grp = VGroup(s1, s2, s3).arrange(RIGHT, buff=0.15).next_to(die_title, DOWN, buff=0.22)

        grp_tq = CrispText("DB Query", size=11, weight=SEMIBOLD, color=C_CHARCOAL).move_to(die_box.get_right() + RIGHT * 1.0 + UP * 0.5)
        grp_tapi = CrispText("API Call", size=11, weight=BOLD, color=C_ORANGE_PULSE).move_to(die_box.get_right() + RIGHT * 1.0)
        grp_tfile = CrispText("File Io", size=11, weight=SEMIBOLD, color=C_CHARCOAL).move_to(die_box.get_right() + RIGHT * 1.0 + DOWN * 0.5)
        conf_lbl = CrispText("Confidence: 0.94", size=10, weight=BOLD, color=C_ORANGE_PULSE).next_to(grp_tapi, RIGHT, buff=0.15)
        tools_fanout = VGroup(grp_tq, grp_tapi, grp_tfile, conf_lbl)

        # Ingress vector arrows from perception and memory docks into neural die
        arr_p = Arrow(docked_perception.get_right(), die_box.get_left() + UP * 0.3, buff=0.1, color=C_CYAN_SKY, stroke_width=2)
        arr_m = Arrow(docked_mem.get_left(), die_box.get_bottom() + RIGHT * 0.5, buff=0.1, color=C_LAVENDER, stroke_width=2)

        self.play(
            FadeIn(die_box),
            FadeIn(die_title),
            Create(arr_p),
            Create(arr_m),
            run_time=1.0
        )
        self.play(
            LaggedStart(
                FadeIn(s1, shift=RIGHT * 0.15),
                FadeIn(s2, shift=RIGHT * 0.15),
                FadeIn(s3, shift=RIGHT * 0.15),
                lag_ratio=0.3
            ),
            run_time=1.4
        )
        self.play(FadeIn(tools_fanout, shift=LEFT * 0.2), run_time=0.9)

        docked_reason_bg = RoundedRectangle(width=2.1, height=0.72, corner_radius=0.15, color=C_AMBER, stroke_width=2, fill_color=C_CARD_BG, fill_opacity=0.95)
        docked_reason_txt = CrispText("Reasoning Dock", size=12, weight=BOLD, color=C_CHARCOAL)
        fit_into_box(docked_reason_txt, docked_reason_bg, pad_x=0.2, pad_y=0.08)
        docked_reason = VGroup(docked_reason_bg, docked_reason_txt).arrange(ORIGIN).move_to(pos_north).set_z_index(15)

        die_full_grp = VGroup(die_box, die_title, pipeline_grp, tools_fanout, arr_p, arr_m)
        # Fix: Replaced ReplacementTransform with FadeOut and FadeIn due to differing VGroup structures
        self.play(
            FadeOut(die_full_grp),
            FadeIn(docked_reason),
            FadeIn(agent_core),
            FadeIn(orbit_circle),
            run_time=1.4
        )

        elapsed = self.renderer.time - t_start
        if elapsed < 13.0:
            self.wait(13.0 - elapsed)

        # -------------------------------------------------------------
        ## Presentation Step 7: Action: Doing Something (run_time: 8.0)
        # -------------------------------------------------------------
        t_start = self.renderer.time
        new_title = create_title(
            "Action: Doing Something",
            "API Dispatch Hub And System Actuation"
        )
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        dispatch_box = RoundedRectangle(width=2.8, height=1.6, corner_radius=0.18, color=C_CORAL, stroke_width=2, fill_color=C_CARD_BG, fill_opacity=0.95).move_to(pos_east + RIGHT * 0.4)
        hub_lbl = CrispText("Dispatch Hub", size=13, weight=BOLD, color=C_CHARCOAL)

        status_pill_bg = RoundedRectangle(width=1.3, height=0.36, corner_radius=0.08, color="#94A3B8", stroke_width=1.2, fill_color="#F1F5F9", fill_opacity=0.9)
        status_pill_txt = CrispText("State: Idle", size=10, weight=BOLD, color=C_CHARCOAL)
        fit_into_box(status_pill_txt, status_pill_bg, pad_x=0.2, pad_y=0.08)
        status_pill = VGroup(status_pill_bg, status_pill_txt).arrange(ORIGIN)

        actuator_dial = Circle(radius=0.3, color=C_CORAL, stroke_width=2, fill_color="#FFF5F5", fill_opacity=0.8)
        dial_needle = Line(actuator_dial.get_center(), actuator_dial.get_center() + np.array([0.2, 0.0, 0]), color=C_ORANGE_PULSE, stroke_width=2.5)
        dial_grp = VGroup(actuator_dial, dial_needle)

        dispatch_content = VGroup(hub_lbl, status_pill, dial_grp).arrange(DOWN, buff=0.12).move_to(dispatch_box.get_center())
        action_hub = VGroup(dispatch_box, dispatch_content)

        cmd_path = CurvedArrow(docked_reason.get_right(), dispatch_box.get_top(), angle=-PI/3, color=C_ORANGE_PULSE, stroke_width=2.5)
        cmd_packet = Dot(color=C_ORANGE_PULSE, radius=0.1)

        self.play(
            FadeOut(sock_e),
            FadeIn(action_hub, shift=LEFT * 0.2),
            Create(cmd_path),
            run_time=1.1
        )
        self.play(MoveAlongPath(cmd_packet, cmd_path), run_time=0.9)
        self.remove(cmd_packet)

        # Rotate needle and shift status pill to Active
        active_pill_bg = RoundedRectangle(width=1.3, height=0.36, corner_radius=0.08, color="#06C170", stroke_width=1.2, fill_color="#ECFDF5", fill_opacity=0.9)
        active_pill_txt = CrispText("State: Active", size=10, weight=BOLD, color="#047857")
        fit_into_box(active_pill_txt, active_pill_bg, pad_x=0.2, pad_y=0.08)
        active_pill = VGroup(active_pill_bg, active_pill_txt).move_to(status_pill.get_center())

        self.play(
            Rotate(dial_needle, angle=PI/4, about_point=actuator_dial.get_center()),
            ReplacementTransform(status_pill, active_pill),
            run_time=1.2
        )

        elapsed = self.renderer.time - t_start
        if elapsed < 8.0:
            self.wait(8.0 - elapsed)

        # -------------------------------------------------------------
        ## Presentation Step 8: The Continuous Loop (run_time: 12.5)
        # -------------------------------------------------------------
        t_start = self.renderer.time
        new_title = create_title(
            "The Continuous Loop",
            "Perceive -> Remember -> Reason -> Act Circuit"
        )
        self.play(FadeOut(title_group), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45)
        title_group = new_title

        docked_act_bg = RoundedRectangle(width=2.1, height=0.72, corner_radius=0.15, color=C_CORAL, stroke_width=2, fill_color=C_CARD_BG, fill_opacity=0.95)
        docked_act_txt = CrispText("Action Dock", size=12, weight=BOLD, color=C_CHARCOAL)
        fit_into_box(docked_act_txt, docked_act_bg, pad_x=0.2, pad_y=0.08)
        docked_act = VGroup(docked_act_bg, docked_act_txt).arrange(ORIGIN).move_to(pos_east).set_z_index(15)

        self.play(
            FadeOut(VGroup(action_hub, cmd_path)),
            FadeIn(docked_act, scale=0.9),
            run_time=1.0
        )

        # Closed Loop Ribbon Connectors
        arc_ws = CurvedArrow(docked_perception.get_bottom(), docked_mem.get_left(), angle=PI/4, color=C_CYAN_SKY, stroke_width=2.5)
        arc_se = CurvedArrow(docked_mem.get_right(), docked_act.get_bottom(), angle=PI/4, color=C_LAVENDER, stroke_width=2.5)
        arc_en = CurvedArrow(docked_act.get_top(), docked_reason.get_right(), angle=PI/4, color=C_CORAL, stroke_width=2.5)
        arc_nw = CurvedArrow(docked_reason.get_left(), docked_perception.get_top(), angle=PI/4, color=C_AMBER, stroke_width=2.5)
        loop_ribbon = VGroup(arc_ws, arc_se, arc_en, arc_nw)

        self.play(Create(loop_ribbon), run_time=1.5)

        # Telemetry counter pill
        loop_counter_bg = RoundedRectangle(width=1.8, height=0.45, corner_radius=0.1, color=C_STEEL_BLUE, stroke_width=1.5, fill_color=C_CARD_BG, fill_opacity=0.95).move_to(center_pos + DOWN * 1.5)
        loop_counter_txt = CrispText("Loop 1", size=12, weight=BOLD, color=C_CHARCOAL).move_to(loop_counter_bg.get_center())
        fit_into_box(loop_counter_txt, loop_counter_bg, pad_x=0.2, pad_y=0.08)
        loop_counter = VGroup(loop_counter_bg, loop_counter_txt).set_z_index(20)

        self.play(FadeIn(loop_counter, shift=UP * 0.1), run_time=0.6)

        loop_pulse = Dot(docked_perception.get_bottom(), color=C_ORANGE_PULSE, radius=0.12).set_z_index(25)
        
        # Traverse Loop 1 -> Loop 2 -> Loop 3 with radial core pulse
        self.play(MoveAlongPath(loop_pulse, arc_ws), run_time=0.6)
        self.play(MoveAlongPath(loop_pulse, arc_se), run_time=0.6)
        
        txt_loop2 = CrispText("Loop 2", size=12, weight=BOLD, color=C_CHARCOAL).move_to(loop_counter_bg.get_center())
        self.play(
            MoveAlongPath(loop_pulse, arc_en),
            Transform(loop_counter_txt, txt_loop2),
            run_time=0.6
        )
        self.play(MoveAlongPath(loop_pulse, arc_nw), run_time=0.6)

        core_full_pulse = PulsingShockwaves(center_pos, color=C_ORANGE_PULSE, max_radius=1.6, num_rings=3)
        self.add(core_full_pulse)

        txt_loop3 = CrispText("Loop 3", size=12, weight=BOLD, color=C_CHARCOAL).move_to(loop_counter_bg.get_center())
        self.play(
            MoveAlongPath(loop_pulse, arc_ws),
            Transform(loop_counter_txt, txt_loop3),
            run_time=0.7
        )
        self.remove(loop_pulse, core_full_pulse)

        elapsed = self.renderer.time - t_start
        if elapsed < 12.5:
            self.wait(12.5 - elapsed)