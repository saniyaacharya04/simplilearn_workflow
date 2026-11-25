C_DARK_BLUE = "#1E293B"
C_BRAND_BLUE = "#2C81FE"
C_LIGHT_BLUE = "#62B7E4"
C_PURPLE = "#9B99C7"
C_YELLOW = "#DDB945"
C_RED = "#E58F6D"
C_WHITE = "#FFFFFF"
C_BLACK = "#404040"
C_NAVY_DARK = "#404040" # This seems to be a duplicate of C_BLACK's value, but the name implies dark blue. Keeping as is.
C_MINT = "#8ECDB7"
C_LAVENDER = "#9B99C7" # Duplicate of C_PURPLE
C_CORAL = "#E58F6D" # Duplicate of C_RED
import os
import re
SME_LAYOUT = '70'
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
        if not hasattr(_scene_cls, '_orig_play_safe'):
            _orig_play = _scene_cls.play
            def _make_safe_play():
                def _safe_play(self, *args, **kwargs):
                    if len(args) == 0:
                        rt = kwargs.get('run_time', 0.5)
                        return self.wait(rt)
                    return _orig_play(self, *args, **kwargs)
                return _safe_play
            _scene_cls._orig_play_safe = True
            _scene_cls.play = _make_safe_play()
        if not hasattr(_scene_cls, 'get_time'):
            _scene_cls.get_time = lambda self: getattr(getattr(self, 'renderer', None), 'time', 0.0)
    except Exception:
        pass
try:
    from manim.utils.color.core import ManimColor
    if not hasattr(ManimColor, '_orig_eq_safe'):
        def _safe_color_eq(self, other):
            if not isinstance(other, ManimColor):
                try: other = ManimColor(other)
                except Exception: return False
            return bool(np.allclose(self._internal_value, other._internal_value))
        ManimColor._orig_eq_safe = True
        ManimColor.__eq__ = _safe_color_eq
except Exception:
    pass
try:
    if not hasattr(Mobject, 'stop_updater'):
        Mobject.stop_updater = lambda self: self.clear_updaters()
    if not hasattr(Mobject, 'set_fill'):
        def _safe_mobj_set_fill(self, *args, **kwargs):
            for sub in getattr(self, 'submobjects', []):
                if hasattr(sub, 'set_fill'):
                    try: sub.set_fill(*args, **kwargs)
                    except Exception: pass
            return self
        Mobject.set_fill = _safe_mobj_set_fill
    if not hasattr(Mobject, 'set_stroke'):
        def _safe_mobj_set_stroke(self, *args, **kwargs):
            for sub in getattr(self, 'submobjects', []):
                if hasattr(sub, 'set_stroke'):
                    try: sub.set_stroke(*args, **kwargs)
                    except Exception: pass
            return self
        Mobject.set_stroke = _safe_mobj_set_stroke
    if not hasattr(Mobject, '_orig_mobj_init_safe'):
        _orig_mobj_init = Mobject.__init__
        def _safe_mobj_init(self, *args, **kwargs):
            valid_mobj_params = {'name', 'dim', 'target', 'z_index'}
            clean_kw = {k: v for k, v in kwargs.items() if k in valid_mobj_params}
            res = _orig_mobj_init(self, *args, **clean_kw)
            if 'opacity' in kwargs and hasattr(self, 'set_opacity'):
                try: self.set_opacity(kwargs['opacity'])
                except Exception: pass
            return res
        Mobject._orig_mobj_init_safe = True
        Mobject.__init__ = _safe_mobj_init
    if not hasattr(VMobject, '_orig_set_stroke_safe'):
        _orig_set_stroke = VMobject.set_stroke
        def _safe_set_stroke(self, *args, **kwargs):
            valid_stroke_params = {'color', 'width', 'opacity', 'background'}
            clean_kw = {k: v for k, v in kwargs.items() if k in valid_stroke_params}
            if 'z_index' in kwargs:
                try: self.set_z_index(kwargs['z_index'])
                except Exception: pass
            return _orig_set_stroke(self, *args, **clean_kw)
        VMobject._orig_set_stroke_safe = True
        VMobject.set_stroke = _safe_set_stroke
except Exception:
    pass
YELLOW = globals().get('YELLOW', '#DDB945')
WHITE = globals().get('WHITE', '#FFFFFF')
BLACK = globals().get('BLACK', '#404040')
RED = globals().get('RED', '#E58F6D')
BLUE = globals().get('BLUE', '#62B7E4')
GREEN = globals().get('GREEN', '#8ECDB7')
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
# Removed: from manim_slides import Slide # This import is not used and causes ModuleNotFoundError
import numpy as np

# Global constants for styling
C_BACKGROUND = "#F0F4F8"
C_TITLE_DARK = "#1E293B"
C_HEADER_DARK = "#1E293B"
C_BODY_TEXT = "#334155"
C_TEXT = "#404040"
C_HIGHLIGHT = "#F78908" # Warm Orange

# Pastel Palette
C_SKY_BLUE = "#62B7E4"
C_STEEL_BLUE = "#7EA2C8"
C_LAVENDER_PERIWINKLE = "#9B99C7"
C_MINT_SEAFOAM = "#8ECDB7"
C_WARM_AMBER = "#E6A157"
C_MUSTARD_YELLOW = "#DDB945"
C_CORAL_PEACH = "#E58F6D"
C_WARM_TAN = "#B88968"
C_DUSTY_ROSE = "#D98CA1"
C_SOFT_LILAC = "#C1A5C6"

# Helper for CrispText














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
class PulsingNode(VGroup):
    def __init__(self, text, node_color=C_SKY_BLUE, text_color=C_TEXT, font_size=20, corner_radius=0.1, pulse_color=C_HIGHLIGHT, z_index=1, **kwargs):
        super().__init__(**kwargs)
        self.text_mob = CrispText(text, font_size=font_size, color=text_color, weight=BOLD)
        
        # Calculate box dimensions based on text, ensuring minimum size
        min_width = 2.0
        min_height = 0.8
        padding_x = 0.4
        padding_y = 0.3
        
        box_width = max(min_width, self.text_mob.width + padding_x)
        box_height = max(min_height, self.text_mob.height + padding_y)
        
        self.node_rect = RoundedRectangle(
            width=box_width,
            height=box_height,
            corner_radius=corner_radius,
            fill_color=node_color,
            fill_opacity=0.8,
            stroke_color=node_color,
            stroke_width=2,
            z_index=z_index
        )
        self.add(self.node_rect, self.text_mob)
        self.text_mob.move_to(self.node_rect.get_center())
        
        # Pulse effect, initially transparent
        self.pulse_rect = self.node_rect.copy().set_fill(opacity=0).set_stroke(color=pulse_color, width=3.5, opacity=0)
        self.add(self.pulse_rect)

    def pulse(self, scene, run_time=0.6):
        scene.play(
            self.pulse_rect.animate.set_stroke(opacity=1),
            run_time=run_time / 2
        )
        scene.play(
            self.pulse_rect.animate.set_stroke(opacity=0),
            run_time=run_time / 2
        )

# Custom Manim class for a flowing data stream with animated particles
class DataStream(VGroup):
    def __init__(self, start_mob, end_mob, stream_color=C_MINT_SEAFOAM, num_particles=10, particle_color=C_WARM_AMBER, particle_radius=0.05, **kwargs):
        super().__init__(**kwargs)
        self.start_mob = start_mob
        self.end_mob = end_mob
        self.stream_color = stream_color
        self.num_particles = num_particles
        self.particle_color = particle_color
        self.particle_radius = particle_radius

        self.arrow = Arrow(
            self.start_mob.get_right(),
            self.end_mob.get_left(),
            buff=0.2,
            stroke_width=2,
            max_tip_length_to_length_ratio=0.1,
            color=stream_color
        )
        self.add(self.arrow)

        self.particles = VGroup(*[
            Dot(radius=self.particle_radius, color=self.particle_color, z_index=2)
            for _ in range(self.num_particles)
        ])
        for particle in self.particles:
            # Distribute particles along the path initially
            alpha = np.random.rand()
            particle.move_to(self.arrow.point_from_proportion(alpha))
            particle.set_opacity(0) # Initially transparent for FadeIn animation
        self.add(self.particles)

        # Use individual ValueTrackers to allow staggered starts and continuous flow
        self.particle_trackers = [ValueTracker(np.random.rand()) for _ in range(self.num_particles)] # Random initial positions
        
        def updater(mobj, dt):
            for i, particle in enumerate(self.particles):
                tracker = self.particle_trackers[i]
                tracker.increment_value(dt * 0.5) # Speed of particles (can be adjusted)
                
                alpha = tracker.get_value() % 1.0 # Cycle from 0 to 1
                
                # Update particle position
                point = self.arrow.point_from_proportion(alpha)
                particle.move_to(point)

        self.add_updater(updater)

    def stop_animation(self):
        # Check if there are updaters before trying to remove
        if self.get_updaters():
            self.remove_updater(self.get_updaters()[0])
        self.particles.set_opacity(0) # Hide all particles

# Custom Manim class for a radar sweep animation
class RadarSweep(VGroup):
    def __init__(self, center_point=ORIGIN, radius=1.5, sweep_color=C_SKY_BLUE, ring_color=C_STEEL_BLUE, num_rings=3, **kwargs):
        super().__init__(**kwargs)
        self.center_point = center_point
        self.radius = radius
        self.sweep_color = sweep_color
        self.ring_color = ring_color
        self.num_rings = num_rings

        self.rings = VGroup(*[
            Circle(radius=self.radius * (i + 1) / num_rings, color=ring_color, stroke_width=1.0, opacity=0.5)
            for i in range(num_rings)
        ])
        self.base_circle = Circle(radius=self.radius, color=ring_color, stroke_width=1.5) # Outer ring is thicker
        
        self.radar_line = Line(start=self.center_point, end=self.center_point + self.radius * RIGHT, color=sweep_color, stroke_width=3)
        self.radar_line.set_stroke(opacity=0.7)

        self.add(self.rings, self.base_circle)
        self.add(self.radar_line)

        self.angle_tracker = ValueTracker(0)
        self.radar_line.add_updater(
            lambda m: m.become(Line(start=self.center_point, end=self.center_point + self.radius * RIGHT).rotate(self.angle_tracker.get_value(), about_point=self.center_point))
        )
        self.add_updater(lambda m, dt: self.angle_tracker.increment_value(dt * 0.5 * DEGREES * 360)) # Rotate slowly

    def stop_animation(self):
        if self.radar_line.get_updaters():
            self.radar_line.remove_updater(self.radar_line.get_updaters()[0])
        if self.get_updaters():
            self.remove_updater(self.get_updaters()[0])

# Custom Manim class for an Agent Core representation with ambient motion
class AgentCore(VGroup):
    def __init__(self, label_text, core_color=C_LAVENDER_PERIWINKLE, text_color=C_TEXT, font_size=18, **kwargs):
        super().__init__(**kwargs)
        self.label_text = CrispText(label_text, font_size=font_size, color=text_color, weight=BOLD)
        
        # A more complex shape for an agent core, e.g., a gear or a circuit board representation
        self.outer_circle = Circle(radius=0.6, color=core_color, fill_opacity=0.6, stroke_width=2)
        self.inner_circle = Circle(radius=0.4, color=ManimColor(core_color).lighter(0.2), fill_opacity=0.8, stroke_width=1)
        self.center_dot = Dot(radius=0.1, color=ManimColor(core_color).darker(0.2))

        self.add(self.outer_circle, self.inner_circle, self.center_dot, self.label_text)
        self.label_text.next_to(self.outer_circle, DOWN, buff=0.1)
        
        # Add a subtle internal rotation for the inner part
        self.inner_circle.add_updater(lambda m, dt: m.rotate(dt * 0.2, about_point=self.get_center()))
        self.center_dot.add_updater(lambda m, dt: m.rotate(-dt * 0.4, about_point=self.get_center()))

    def stop_animation(self):
        if self.inner_circle.get_updaters():
            self.inner_circle.remove_updater(self.inner_circle.get_updaters()[0])
        if self.center_dot.get_updaters():
            self.center_dot.remove_updater(self.center_dot.get_updaters()[0])


class FinalScene(InstrumentedScene, MovingCameraScene):
    def construct(self):
        self.camera.background_color = C_BACKGROUND
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
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)
















        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)














        # Removed redundant local definitions of helper functions.
        # The global definitions are used, and assigned to `self` for convenience.


        def create_header(*args, **kwargs):
            return create_title(*args, **kwargs)





        # The global create_pill is used




        # The global safe_image is used






        # SME 70% layout: Content right of x = -0.80
        content_x_start = -0.80
        content_width = 6.40 - content_x_start # Right safe boundary is +6.40
        content_center_x = content_x_start + content_width / 2
        content_y_max = 2.20
        content_y_min = -3.50
        content_center_y = (content_y_max + content_y_min) / 2

        # Scene Title
        scene_title_text = "Core Problem and Operational Context"
        current_title = self.create_title(scene_title_text)
        self.play(FadeIn(current_title, shift=DOWN * 0.1), run_time=0.8)
        
        ## Presentation Step 1
        self.play(FadeIn(current_title, shift=DOWN*0.1), run_time=0.8)
        # Purpose: Explain Solara Energy Introduction
        # Narration: Monitoring site performance and goal-driven action sequences
        step1_title_text = "Solara Energy Introduction"

        # Visuals for Step 1: Monitoring Hub, Site Performance, Action Dispatch
        monitoring_hub = RadarSweep(
            center_point=np.array([content_center_x - 1.5, content_center_y + 0.5, 0]),
            radius=1.2,
            sweep_color=C_SKY_BLUE,
            ring_color=C_STEEL_BLUE
        )
        monitoring_label = CrispText("Monitoring Hub", font_size=18, weight=BOLD, color=C_HEADER_DARK).next_to(monitoring_hub, DOWN, buff=0.2)
        
        site_performance_node = PulsingNode("Site Performance", node_color=C_MINT_SEAFOAM, font_size=16)
        site_performance_node.move_to(monitoring_hub.get_left() + LEFT * 1.5 + UP * 0.5) # Position left of hub

        action_dispatch_node = PulsingNode("Action Dispatch", node_color=C_WARM_AMBER, font_size=16)
        action_dispatch_node.move_to(monitoring_hub.get_right() + RIGHT * 1.5 + UP * 0.5) # Position right of hub
        
        # Group and position the initial elements to ensure they fit the content area
        initial_diagram_group = VGroup(site_performance_node, monitoring_hub, monitoring_label, action_dispatch_node)
        
        # Scale down if necessary to fit within content_width, with a small margin
        if initial_diagram_group.width > content_width * 0.9:
            initial_diagram_group.scale_to_fit_width(content_width * 0.9)
        initial_diagram_group.move_to(np.array([content_center_x, content_center_y, 0]))

        self.play(
            LaggedStart(
                GrowFromCenter(monitoring_hub),
                FadeIn(monitoring_label, shift=DOWN*0.1),
                lag_ratio=0.5,
                run_time=2.0
            )
        )
        self.play(
            FadeIn(site_performance_node, shift=LEFT*0.5),
            run_time=1.5
        )
        self.play(
            FadeIn(action_dispatch_node, shift=RIGHT*0.5),
            run_time=1.5
        )

        # Data flow from Site Performance to Monitoring Hub
        data_flow_to_hub = DataStream(site_performance_node, monitoring_hub, stream_color=C_MINT_SEAFOAM)
        # Add the DataStream to the scene AFTER its components are created
        # Particles are initially transparent in DataStream's __init__
        self.add(data_flow_to_hub) # Add updater immediately, but particles are transparent
        self.play(Create(data_flow_to_hub.arrow), FadeIn(data_flow_to_hub.particles), run_time=1.0) # Animate the arrow itself and fade in particles

        # Connection from Monitoring Hub to Action Dispatch
        monitor_to_action_arrow = Arrow(
            monitoring_hub.get_right(),
            action_dispatch_node.get_left(),
            buff=0.2,
            stroke_width=2,
            max_tip_length_to_length_ratio=0.1,
            color=C_SKY_BLUE
        )
        self.play(Create(monitor_to_action_arrow), run_time=1.0)
        
        # Add a particle for the action flow
        action_particle = Dot(radius=0.08, color=C_HIGHLIGHT, z_index=2)
        self.play(
            MoveAlongPath(action_particle, monitor_to_action_arrow, rate_func=ease_out_cubic, run_time=1.5), # Fixed rate_func
            run_time=1.5
        )
        self.remove(action_particle)

        # Highlight Monitoring Hub and Action Dispatch
        monitoring_hub_pulse = monitoring_hub.base_circle.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
        action_dispatch_pulse = action_dispatch_node.node_rect.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)

        self.play(Create(monitoring_hub_pulse), run_time=0.6)
        self.play(FadeOut(monitoring_hub_pulse), run_time=0.4)
        
        self.play(Create(action_dispatch_pulse), run_time=0.6)
        self.play(FadeOut(action_dispatch_pulse), run_time=0.4)

        # Total runtime for step 1 is 34.38.
        # Recalculate: 0.8 (initial title fadein) + 0.8 (title transition) + 2.0 (hub/label) + 1.5 (site node) + 1.5 (action node) + 1.0 (data_flow) + 1.0 (monitor_to_action_arrow) + 1.5 (action particle) + 0.6 (hub pulse) + 0.4 (hub pulse fade) + 0.6 (action pulse) + 0.4 (action pulse fade) = 14.1 seconds
        self.wait(34.38 - 14.1) # Adjust wait time based on animations

        ## Presentation Step 2
        # Purpose: Explain Real-World Action Sequence
        # Narration: Querying data, comparing outputs, flagging anomalies, generating reports
        step2_title_text = "Real-World Action Sequence"
        new_title = self.create_title(step2_title_text) # Create new title for step 2
        self.play(FadeOut(current_title), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45) # Combined fade out/in
        current_title = new_title

        # Stop updaters before removing
        data_flow_to_hub.stop_animation()
        monitoring_hub.stop_animation()
        
        # Fade out elements not directly relevant to action sequence for clarity
        self.play(
            FadeOut(site_performance_node),
            FadeOut(data_flow_to_hub),
            FadeOut(monitoring_hub),
            FadeOut(monitoring_label),
            FadeOut(monitor_to_action_arrow),
            run_time=1.0
        )

        # Reposition action_dispatch_node to a more central position for elaboration
        self.play(action_dispatch_node.animate.move_to(np.array([content_center_x, content_center_y + 1.0, 0])), run_time=1.0)

        # Sub-actions around Action Dispatch
        query_data_node = PulsingNode("Query Data", node_color=C_LAVENDER_PERIWINKLE, font_size=16)
        compare_outputs_node = PulsingNode("Compare Outputs", node_color=C_MUSTARD_YELLOW, font_size=16)
        flag_anomalies_node = PulsingNode("Flag Anomalies", node_color=C_CORAL_PEACH, font_size=16)
        generate_reports_node = PulsingNode("Generate Reports", node_color=C_SOFT_LILAC, font_size=16)

        # Arrange these nodes in a circular flow around action_dispatch_node
        center_pt = action_dispatch_node.get_center()
        radius = 2.5
        nodes = [query_data_node, compare_outputs_node, flag_anomalies_node, generate_reports_node]
        angles = [PI/2, 0, -PI/2, PI]
        for node, ang in zip(nodes, angles):
            node.move_to(center_pt + radius * np.array([np.cos(ang), np.sin(ang), 0]))
        action_nodes_group = VGroup(*nodes)

        self.play(
            LaggedStart(
                FadeIn(query_data_node, shift=UP*0.5),
                FadeIn(compare_outputs_node, shift=RIGHT*0.5),
                FadeIn(flag_anomalies_node, shift=DOWN*0.5),
                FadeIn(generate_reports_node, shift=LEFT*0.5),
                lag_ratio=0.3,
                run_time=3.0
            )
        )

        # Arrows connecting the flow
        arrow1 = CurvedArrow(action_dispatch_node.get_bottom(), query_data_node.get_top(), color=C_STEEL_BLUE, tip_length=0.2, buff=0.1)
        arrow2 = CurvedArrow(query_data_node.get_right(), compare_outputs_node.get_top(), color=C_STEEL_BLUE, tip_length=0.2, buff=0.1)
        arrow3 = CurvedArrow(compare_outputs_node.get_bottom(), flag_anomalies_node.get_right(), color=C_STEEL_BLUE, tip_length=0.2, buff=0.1)
        arrow4 = CurvedArrow(flag_anomalies_node.get_left(), generate_reports_node.get_bottom(), color=C_STEEL_BLUE, tip_length=0.2, buff=0.1)
        arrow5 = CurvedArrow(generate_reports_node.get_top(), action_dispatch_node.get_left(), color=C_STEEL_BLUE, tip_length=0.2, buff=0.1)

        flow_arrows = VGroup(arrow1, arrow2, arrow3, arrow4, arrow5)
        self.play(Create(flow_arrows), run_time=2.0)

        # Animate particles flowing through the sequence
        flow_particles = VGroup(*[Dot(radius=0.06, color=C_HIGHLIGHT, z_index=2) for _ in range(5)])
        flow_paths = [arrow1, arrow2, arrow3, arrow4, arrow5]

        particle_trackers = [ValueTracker(i * 0.2) for i in range(len(flow_particles))] # Staggered start
        
        def flow_updater(mobj, dt):
            for i, particle in enumerate(flow_particles):
                tracker = particle_trackers[i]
                tracker.increment_value(dt * 0.4) # Speed of particles
                alpha = tracker.get_value()
                
                # Determine current path index based on alpha value
                path_idx = int(alpha) % len(flow_paths)
                current_path = flow_paths[path_idx]
                
                # Proportion along the current path
                prop_on_path = alpha % 1.0
                
                # Hide particle briefly at path transitions for smoother loop
                if prop_on_path < 0.95:
                    point = current_path.point_from_proportion(prop_on_path)
                    particle.move_to(point).set_opacity(1)
                else:
                    particle.set_opacity(0)
        
        flow_particles.add_updater(flow_updater)
        self.add(flow_particles)

        # Let the flow animation run for a duration
        self.wait(10.0) 

        # Highlight each node as it's mentioned (implicitly by showing the flow)
        self.play(action_dispatch_node.pulse_rect.animate.set_stroke(opacity=1), run_time=0.4)
        self.play(FadeOut(action_dispatch_node.pulse_rect), run_time=0.3)
        self.play(query_data_node.pulse_rect.animate.set_stroke(opacity=1), run_time=0.4)
        self.play(FadeOut(query_data_node.pulse_rect), run_time=0.3)
        self.play(compare_outputs_node.pulse_rect.animate.set_stroke(opacity=1), run_time=0.4)
        self.play(FadeOut(compare_outputs_node.pulse_rect), run_time=0.3)
        self.play(flag_anomalies_node.pulse_rect.animate.set_stroke(opacity=1), run_time=0.4)
        self.play(FadeOut(flag_anomalies_node.pulse_rect), run_time=0.3)
        self.play(generate_reports_node.pulse_rect.animate.set_stroke(opacity=1), run_time=0.4)
        self.play(FadeOut(generate_reports_node.pulse_rect), run_time=0.3)

        # Stop particle animation before fading out
        flow_particles.remove_updater(flow_updater)
        self.remove(flow_particles)
        
        self.wait(0.5) # Small pause

        ## Presentation Step 3
        # Purpose: Explain Architectural Diversity
        # Narration: Different types built on different architectures for different problems
        step3_title_text = "Architectural Diversity"
        new_title = self.create_title(step3_title_text) # Create new title for step 3
        self.play(FadeOut(current_title), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45) # Combined fade out/in
        current_title = new_title

        # Fade out detailed action sequence to focus on architectures
        self.play(
            FadeOut(action_dispatch_node),
            FadeOut(action_nodes_group),
            FadeOut(flow_arrows),
            run_time=1.0
        )

        # Introduce diverse agent architectures
        arch_colors = [C_SKY_BLUE, C_MINT_SEAFOAM, C_LAVENDER_PERIWINKLE, C_WARM_AMBER]
        arch_labels = ["Reactive Agent", "Deliberative Agent", "Hybrid Agent", "Hierarchical Agent"]

        architectures = VGroup()
        for i, label in enumerate(arch_labels):
            arch = AgentCore(label, core_color=arch_colors[i], font_size=16)
            architectures.add(arch)

        # Arrange architectures horizontally within the content safe area
        architectures.arrange(RIGHT, buff=0.8)
        # Scale to fit width and center in the content area
        architectures.scale_to_fit_width(content_width * 0.9) 
        architectures.move_to(np.array([content_center_x, content_center_y, 0]))

        self.play(
            LaggedStart(*[GrowFromCenter(arch) for arch in architectures], lag_ratio=0.2, run_time=3.0)
        )

        # Highlight each architecture type briefly
        for i, arch in enumerate(architectures):
            pulse_rect = arch.outer_circle.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
            self.play(Create(pulse_rect), run_time=0.5)
            self.play(FadeOut(pulse_rect), run_time=0.3)
            self.wait(0.5)
        
        # Keep architectures on screen, let ambient updaters run
        self.wait(4.0)

        ## Presentation Step 4
        # Purpose: Explain Engineering Alignment
        # Narration: Matching the right agent architecture to the right operational job
        step4_title_text = "Engineering Alignment"
        new_title = self.create_title(step4_title_text) # Create new title for step 4
        self.play(FadeOut(current_title), run_time=0.35)
        self.play(FadeIn(new_title, shift=DOWN * 0.1), run_time=0.45) # Combined fade out/in
        current_title = new_title

        # Stop ambient updaters for architectures to prepare for transformations
        for arch in architectures:
            arch.stop_animation()

        # Shift architectures up slightly to make room for 'Operational Jobs'
        self.play(architectures.animate.shift(UP * 1.5), run_time=1.0)

        # Introduce "Operational Jobs" below the architectures
        job_labels = ["Rapid Response", "Complex Planning", "Adaptive Control", "Long-Term Goals"]
        operational_jobs = VGroup()
        for i, label in enumerate(job_labels):
            job_node = PulsingNode(label, node_color=C_DUSTY_ROSE, font_size=16, text_color=C_TEXT)
            operational_jobs.add(job_node)
        
        operational_jobs.arrange(RIGHT, buff=0.8)
        # Match overall width for alignment, then position
        operational_jobs.scale_to_fit_width(architectures.width) # Match width with architectures
        operational_jobs.next_to(architectures, DOWN, buff=1.0)
        operational_jobs.align_to(architectures, LEFT) # Align to left of architectures group

        self.play(
            LaggedStart(*[GrowFromCenter(job) for job in operational_jobs], lag_ratio=0.2, run_time=3.0)
        )

        # Draw matching lines one by one, with highlight
        match_arrows = VGroup()
        for i in range(len(architectures)):
            arrow = Arrow(
                architectures[i].get_bottom(),
                operational_jobs[i].get_top(),
                buff=0.2,
                stroke_width=3,
                max_tip_length_to_length_ratio=0.15,
                color=C_HIGHLIGHT # Use highlight color for matches
            )
            match_arrows.add(arrow)
            self.play(Create(arrow), run_time=0.8)
            
            # Highlight both connected nodes
            arch_pulse = architectures[i].outer_circle.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
            job_pulse = operational_jobs[i].node_rect.copy().set_fill(opacity=0).set_stroke(color=C_HIGHLIGHT, width=3.5)
            
            self.play(
                AnimationGroup(
                    Create(arch_pulse),
                    Create(job_pulse),
                    lag_ratio=0.2,
                    run_time=0.6
                )
            )
            self.play(FadeOut(arch_pulse, job_pulse), run_time=0.4)
            self.wait(0.2) # Short pause after highlight

        self.wait(5.0) # Let the final diagram persist

        # Clean up all elements at the end
        self.play(
            FadeOut(current_title),
            FadeOut(architectures),
            FadeOut(operational_jobs),
            FadeOut(match_arrows),
            run_time=1.0
        )
        self.wait(0.5) # Final short wait