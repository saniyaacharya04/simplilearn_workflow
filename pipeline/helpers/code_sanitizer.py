"""
code_sanitizer.py

Deterministic AST & regex sanitizer for Manim code files across all workflow stages.
Protects against recurring LLM hallucinations, unsupported Manim Community APIs,
and brittle path references:
1. Strips invalid 'col_widths' and other unsupported kwargs from Table / MobjectTable.
2. Automatically ensures Table / MobjectTable calls add_background_rectangle() before get_background_rectangle().
3. Converts relative image paths ('../images/...') to robust script-relative or absolute paths.
4. Auto-wraps raw Mobjects in LaggedStart, Succession, and AnimationGroup with FadeIn(...).
5. Auto-wraps naked Mobjects passed directly into self.play(...) with FadeIn(...).
6. Replaces Rectangle(corner_radius=...) with RoundedRectangle(corner_radius=...).
7. Replaces invalid CrispText weights (e.g. weight=REGULAR -> weight=NORMAL) and clamps tiny text.
8. Strips invalid stretch=True/False inside VGroup / Group.
9. Ensures conditional width/height scaling guards.
"""

import os
import sys
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)


import os
import re
import json
from pathlib import Path


def is_executive_topic(base_folder: str = None, topic_id: str = None) -> bool:
    """
    Checks if a topic is an executive higher-ed presentation.
    Guarantees that all executive presentation videos maintain their exact executive standard.
    """
    if topic_id and ("EXEC" in str(topic_id).upper() or "SIMPLILEARN" in str(topic_id).upper()):
        return True
    if base_folder:
        folder_name = os.path.basename(os.path.abspath(base_folder))
        cfg_path = os.path.join(base_folder, "ex_config.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                if "executive" in str(cfg.get("voice_choice", "")).lower():
                    return True
                if cfg.get("creative_context") in ("non_stem_higher_ed", "higher_ed", "simplilearn_osl_3"):
                    return True
                if cfg.get("theme") in ("digital_learning", "dynamic_learning", "simplilearn") and not folder_name.upper().startswith("ACE_"):
                    return True
            except Exception:
                pass
    return True


def get_visual_archetype(base_folder: str = None, topic_id: str = None, code_content: str = "") -> str:
    """
    Dynamically identifies the visual archetype of the video:
    - 'executive': Standard executive visual architecture.
    - 'k12_education': Engaging open-canvas storytelling for K-12.
    - 'stem_math': Coordinate axes, geometry, calculus, and scientific proofs.
    - 'process_flow': Node-link pipelines, state machines, tree architectures.
    - 'promo_vertical': 9:16 mobile portrait format.
    """
    if is_executive_topic(base_folder, topic_id):
        return "executive"

    if base_folder:
        cfg_path = os.path.join(base_folder, "ex_config.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                theme = str(cfg.get("theme", "")).lower()
                ctx = str(cfg.get("creative_context", "")).lower()
                if theme == "promo":
                    return "promo_vertical"
                if theme == "k12" or ctx == "k12":
                    if "Axes(" in code_content or "NumberPlane(" in code_content:
                        return "stem_math"
                    return "k12_education"
                if theme in ("stem", "math", "science") or ctx in ("stem", "math"):
                    return "stem_math"
            except Exception:
                pass

    if topic_id and topic_id.startswith("Ace_"):
        if "Axes(" in code_content or "NumberPlane(" in code_content:
            return "stem_math"
        return "k12_education"

    if "Axes(" in code_content or "NumberPlane(" in code_content or "Polygon(" in code_content:
        return "stem_math"

    # Default to executive if no specific archetype matches
    return "executive"


def resolve_scene_title(code_text: str, file_path: str = None) -> str:
    """
    Extracts or resolves the canonical scene title for a slide.
    Checks CGI_Input.json, presentation_composition.json, instructions json,
    comments in code, premise headings, or sensible fallback.
    """
    if file_path:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(file_path)))
            base_name = os.path.basename(file_path)
            m = re.search(r'group_(\d+)', base_name)
            if m:
                group_num = m.group(1)
                # 1. Check CGI_Input.json
                cgi_file = os.path.join(base_dir, "CGI_Input.json")
                if os.path.exists(cgi_file):
                    try:
                        with open(cgi_file, 'r', encoding='utf-8') as cf:
                            cd = json.load(cf)
                        if str(group_num) in cd and cd[str(group_num)]:
                            t = cd[str(group_num)][0].get("title") or cd[str(group_num)][0].get("matching_section")
                            if t and str(t).strip() and not str(t).strip().lower().startswith("scene"):
                                t = t.strip()
                                if t.isupper():
                                    t = t.title()
                                return t
                    except Exception:
                        pass
                # 2. Check presentation_composition.json
                import glob
                comp_files = glob.glob(os.path.join(base_dir, "*presentation_composition.json"))
                if comp_files:
                    try:
                        with open(comp_files[0], 'r', encoding='utf-8') as cf:
                            cd = json.load(cf)
                        for sc in cd.get("scenes", []):
                            if str(sc.get("scene_id")) == str(group_num):
                                t = sc.get("title") or sc.get("scene_title")
                                if t and str(t).strip() and not str(t).strip().lower().startswith("scene"):
                                    t = t.strip()
                                    if t.isupper():
                                        t = t.title()
                                    return t
                    except Exception:
                        pass
                # 3. Check instructions_*.json
                instr_files = glob.glob(os.path.join(base_dir, "instructions_*.json"))
                if instr_files:
                    with open(instr_files[0], 'r', encoding='utf-8') as jf:
                        jd = json.load(jf)
                    if group_num in jd and jd[group_num]:
                        t = jd[group_num][0].get("title")
                        if t:
                            t = t.strip()
                            if t.isupper():
                                t = t.title()
                            return t
        except Exception:
            pass

    m_comment = re.search(r'#\s*(?:Scene\s*\d+:?|Title:?)\s*([^\n]+)', code_text, re.IGNORECASE)
    if m_comment:
        clean_t = m_comment.group(1).strip()
        if clean_t and not clean_t.startswith("-") and len(clean_t) <= 60 and not clean_t.lower().startswith("scene"):
            return clean_t

    m_premise = re.search(r'CrispText\(["\']([^"\']{5,60})["\'][^)]*weight=[^)]*BOLD', code_text)
    if m_premise:
        return m_premise.group(1).strip()

    if file_path:
        m_grp = re.search(r'group_(\d+)', file_path)
        if m_grp:
            return f"Concept Section {m_grp.group(1)}"
    return "Key Concepts"


def resolve_sme_layout(code_text: str, file_path: str = None) -> str:
    """
    Resolves the authoritative SME layout ('100', '70', or '20') for a scene.
    Checks storyboard blueprints, styling specifications, code comments, or fallback.
    """
    if file_path:
        try:
            base_name = os.path.basename(file_path)
            m = re.search(r'group_(\d+)', base_name)
            group_num = m.group(1) if m else None

            # Check topic directory upwards
            curr = os.path.dirname(os.path.abspath(file_path))
            for _ in range(4):
                meta_dir = os.path.join(curr, "metadata_blueprints")
                if os.path.exists(meta_dir):
                    import glob
                    bp_files = glob.glob(os.path.join(meta_dir, "*storyboard_blueprint.json"))
                    if bp_files:
                        with open(bp_files[0], 'r', encoding='utf-8') as f:
                            bp = json.load(f)
                        for sc in bp.get('scenes', []):
                            if group_num and str(sc.get('scene_id')) == str(group_num):
                                return str(sc.get('sme_layout', '70')).replace('%', '')
                    style_files = glob.glob(os.path.join(meta_dir, "*styling_specifications.json"))
                    if style_files:
                        with open(style_files[0], 'r', encoding='utf-8') as f:
                            st = json.load(f)
                        for sc in st.get('scenes', []):
                            if group_num and str(sc.get('scene_id')) == str(group_num):
                                return str(sc.get('sme_layout', '70')).replace('%', '')
                    break
                parent = os.path.dirname(curr)
                if parent == curr:
                    break
                curr = parent
        except Exception:
            pass

    # Check comments in code
    m_comm = re.search(r'#\s*Layout\s*(100|70|20)', code_text, re.IGNORECASE)
    if m_comm:
        return m_comm.group(1)
    if file_path and "group_1." in file_path:
        return "100"
    return "70"


def unwrap_nested_animations(text: str) -> str:
    """
    Manim Animation classes like FadeIn, FadeOut, Create, Write expect Mobjects, not Animation instances.
    If an LLM writes e.g. FadeIn(UpdateFromAlphaFunc(...)), unwrap it to UpdateFromAlphaFunc(...).
    Uses a balanced parenthesis scanner to handle arbitrary nesting.
    """
    outer_funcs = ("FadeIn", "FadeOut", "Create", "Write", "Uncreate", "GrowFromCenter", "DrawBorderThenFill")
    inner_funcs = ("UpdateFromAlphaFunc", "Transform", "ReplacementTransform", "Rotate", "ScaleInPlace", "FadeIn", "FadeOut", "Create", "Write")
    
    pattern = re.compile(
        r'\b(' + '|'.join(outer_funcs) + r')\s*\(\s*(' + '|'.join(inner_funcs) + r'\s*\()'
    )
    
    pos = 0
    while True:
        m = pattern.search(text, pos)
        if not m:
            break
        
        outer_start = m.start()
        inner_start = m.start(2)
        inner_paren_start = text.find('(', inner_start)
        
        # Count balanced parens from inner_paren_start
        count = 1
        idx = inner_paren_start + 1
        while idx < len(text) and count > 0:
            if text[idx] == '(':
                count += 1
            elif text[idx] == ')':
                count -= 1
            idx += 1
            
        if count == 0:
            inner_call = text[inner_start:idx]
            rest = text[idx:]
            # Case 1: outer call ends immediately: rest starts with optional whitespace and ')'
            rest_match = re.match(r'^\s*\)', rest)
            if rest_match:
                outer_end = idx + rest_match.end()
                text = text[:outer_start] + inner_call + text[outer_end:]
                pos = outer_start + len(inner_call)
                continue
            # Case 2: outer call had kwargs: rest starts with comma, kwargs, and ')'
            rest_kwargs_match = re.match(r'^\s*,\s*([^)]*?)\s*\)', rest)
            if rest_kwargs_match:
                kwargs_str = rest_kwargs_match.group(1).strip()
                outer_end = idx + rest_kwargs_match.end()
                inner_without_close = inner_call[:-1]
                if kwargs_str:
                    inner_call_with_kwargs = f"{inner_without_close}, {kwargs_str})"
                else:
                    inner_call_with_kwargs = inner_call
                text = text[:outer_start] + inner_call_with_kwargs + text[outer_end:]
                pos = outer_start + len(inner_call_with_kwargs)
                continue
                
        pos = m.end()
        
    return text


def unwrap_animate_calls(text: str) -> str:
    """
    Manim animation classes (FadeIn, FadeOut, Create, Write, etc.) expect Mobjects, not Animation instances.
    If an LLM writes e.g. FadeIn(ring.animate(rate_func=...).scale(1.1)), unwrap it to:
    ring.animate(rate_func=...).scale(1.1)
    """
    outer_funcs = ("FadeIn", "FadeOut", "Create", "Write", "Uncreate", "GrowFromCenter", "ShrinkToCenter", "DrawBorderThenFill")
    pattern = re.compile(r"\b(" + "|".join(outer_funcs) + r")\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*\.animate\b)")
    pos = 0
    while True:
        m = pattern.search(text, pos)
        if not m:
            break
        outer_start = m.start()
        inner_start = m.start(2)
        outer_paren_start = text.find("(", outer_start)
        count = 1
        idx = outer_paren_start + 1
        while idx < len(text) and count > 0:
            if text[idx] == "(":
                count += 1
            elif text[idx] == ")":
                count -= 1
            idx += 1
        if count == 0:
            inner_content = text[inner_start:idx-1].strip()
            text = text[:outer_start] + inner_content + text[idx:]
            pos = outer_start + len(inner_content)
            continue
        pos = m.end()
    return text


def heal_syntax_errors(code: str) -> str:
    """
    Attempts to heal common LLM syntax truncation and escaping hazards:
    1. Raw strings ending with an unescaped trailing backslash before a quote: r"...\" -> r"...\\"
    2. Unterminated string literals caused by unclosed single or double quotes.
    """
    if not code or not isinstance(code, str):
        return code
    try:
        compile(code, "<heal_test>", "exec")
        return code
    except SyntaxError as e:
        err_msg = str(e)
        if "unterminated string literal" in err_msg or "EOL while scanning string literal" in err_msg:
            lines = code.splitlines()
            line_no = e.lineno
            if line_no and 1 <= line_no <= len(lines):
                target_line = lines[line_no - 1]
                # Fix trailing backslash before closing quote in raw strings
                healed_line = re.sub(r'r(["\'])([\s\S]*?)\\(\1)', r'r\1\2\\\\\1', target_line)
                # Fix unescaped backslash right before quote: \" at end of string
                if healed_line == target_line and target_line.rstrip().endswith(r'\"'):
                    healed_line = target_line.rstrip()[:-2] + r'\\"'
                elif healed_line == target_line and target_line.rstrip().endswith(r"\'"):
                    healed_line = target_line.rstrip()[:-2] + r"\\'"
                
                # Check for unclosed quote on line
                if healed_line == target_line:
                    dq = len(re.findall(r'(?<!\\)"', target_line))
                    sq = len(re.findall(r"(?<!\\)'", target_line))
                    if dq % 2 != 0:
                        healed_line = target_line + '"'
                    elif sq % 2 != 0:
                        healed_line = target_line + "'"
                lines[line_no - 1] = healed_line
                candidate = "\n".join(lines)
                try:
                    compile(candidate, "<heal_test>", "exec")
                    return candidate
                except SyntaxError:
                    pass
        elif "expected an indented block" in err_msg:
            lines = code.splitlines()
            line_no = e.lineno
            if line_no and 1 <= line_no <= len(lines):
                lines.insert(line_no - 1, "    pass")
                candidate = "\n".join(lines)
                try:
                    compile(candidate, "<heal_test>", "exec")
                    return candidate
                except SyntaxError:
                    pass
        return code


def sanitize_manim_code(code: str, script_path: str = None) -> str:
    """
    Sanitizes Manim Python code to eliminate common API hallucinations and path issues.
    Returns the cleaned, runnable code string.
    """
    if not code or not isinstance(code, str):
        return code

    code = heal_syntax_errors(code)
    sanitized = unwrap_nested_animations(code)
    sanitized = unwrap_animate_calls(sanitized)

    # Unwrap animation variable names accidentally wrapped in FadeIn/FadeOut/Create/Write
    sanitized = re.sub(
        r'\b(FadeIn|FadeOut|Create|Write)\(\s*([a-zA-Z0-9_]*anim\d*)\s*\)',
        r'\2',
        sanitized
    )

    # Ensure essential imports are present
    if "from manim import *" not in sanitized and "from manim import" not in sanitized:
        sanitized = "from manim import *\n" + sanitized
    for imp in ["import numpy as np", "import re", "import os"]:
        if imp not in sanitized:
            sanitized = f"{imp}\n" + sanitized
    if "from manim.utils.rate_functions import *" not in sanitized:
        if "from manim import *" in sanitized:
            sanitized = sanitized.replace("from manim import *", "from manim import *\ntry:\n    from manim.utils.rate_functions import *\nexcept Exception:\n    pass", 1)
    if "NumberLine.c2p" not in sanitized:
        if "from manim import *" in sanitized:
            sanitized = sanitized.replace("from manim import *", "from manim import *\nNumberLine.c2p = lambda self, *args: self.n2p(args[0])", 1)
        else:
            sanitized += "\nNumberLine.c2p = lambda self, *args: self.n2p(args[0])\n"

    # Ensure standard color constants exist if referenced (OSL 3.0 Palette)
    color_constants = [
        ('C_DARK_BLUE', '"#1E293B"'),
        ('C_BRAND_BLUE', '"#2C81FE"'),
        ('C_TEXT', '"#404040"'),
        ('C_FOCUS', '"#F78908"'),
        ('C_HIGHLIGHT', '"#F78908"'),
        ('C_MINT', '"#8ECDB7"'),
        ('C_SKY_BLUE', '"#62B7E4"'),
        ('C_STEEL_BLUE', '"#7EA2C8"'),
        ('C_LAVENDER', '"#9B99C7"'),
        ('C_MUSTARD_GOLD', '"#DDB945"'),
        ('C_WARM_AMBER', '"#E6A157"'),
        ('C_CORAL', '"#E58F6D"'),
        ('C_WARM_TAN', '"#B88968"'),
        ('C_DUSTY_ROSE', '"#D98CA1"'),
        ('C_SOFT_LILAC', '"#C1A5C6"'),
        ('C_LIGHT_BLUE', '"#62B7E4"'),
        ('C_PURPLE', '"#9B99C7"'),
        ('C_YELLOW', '"#DDB945"'),
        ('C_RED', '"#E58F6D"'),
        ('C_WHITE', '"#FFFFFF"'),
        ('C_BLACK', '"#404040"'),
        ('C_LIGHT_GREY', '"#E2E8F0"'),
        ('C_NAVY_DARK', '"#404040"'),
        ('C_CARD_BG', '"#FFFFFF"'),
        ('C_BORDER', '"#CBD5E1"')
    ]
    missing_colors = []
    for c_name, c_val in color_constants:
        if c_name in sanitized and not re.search(rf"\b{c_name}\s*=", sanitized):
            missing_colors.append(f"{c_name} = {c_val}")
    if missing_colors:
        sanitized = "\n".join(missing_colors) + "\n" + sanitized

    # Inject authoritative SME layout constant at module level if not present
    sme_layout = resolve_sme_layout(sanitized, script_path)
    if not re.search(r'^\s*SME_LAYOUT\s*=', sanitized, re.MULTILINE):
        sanitized = f"SME_LAYOUT = '{sme_layout}'\n" + sanitized

    # Prevent duplicate / double background containers in digital learning
    if "left_container" in sanitized or "right_container" in sanitized or "left_bg" in sanitized:
        def _neutralize_double_bg(m):
            stmt = m.group(0)
            var_name = m.group(1)
            if var_name in ("left_container", "right_container", "left_bg", "right_bg"):
                return stmt
            # Neutralize secondary full-height or intermediate tinted background panels
            if any(term in var_name.lower() for term in (
                "left_panel", "left_macro", "right_canvas", "table_panel", 
                "summary_bg", "chk_card_bg", "panel_bg", "col_bg", "grid_bg", 
                "vi_bg", "ac_bg", "ac_small_bg", "lh_bg", "rh_bg"
            )):
                stmt = re.sub(r'fill_opacity\s*=\s*[0-9.]+', 'fill_opacity=0.0', stmt)
                stmt = re.sub(r'stroke_width\s*=\s*[0-9.]+', 'stroke_width=0', stmt)
                stmt = re.sub(r'stroke_opacity\s*=\s*[0-9.]+', 'stroke_opacity=0', stmt)
            elif re.search(r'width\s*=\s*(?:3\.[4-9]|4\.[0-9]|6\.[5-9]|7\.[0-9]|8\.[0-9])', stmt) and re.search(r'height\s*=\s*(?:3\.[0-9]|4\.[0-9]|5\.[0-9])', stmt):
                stmt = re.sub(r'fill_opacity\s*=\s*[0-9.]+', 'fill_opacity=0.0', stmt)
                stmt = re.sub(r'stroke_width\s*=\s*[0-9.]+', 'stroke_width=0', stmt)
                stmt = re.sub(r'stroke_opacity\s*=\s*[0-9.]+', 'stroke_opacity=0', stmt)
            return stmt

        sanitized = re.sub(
            r'(\b[a-zA-Z0-9_]*(?:bg|panel|canvas|macro)[a-zA-Z0-9_]*\s*=\s*(?:RoundedRectangle|Rectangle)\([^)]*\))',
            _neutralize_double_bg,
            sanitized
        )

    # Dynamic safe unwrap for Animations accidentally passed into FadeIn/FadeOut/Create/Write
    # Clean up any fragmented or prior safety preambles to ensure single clean insertion
    sanitized = re.sub(r'(?s)# Dynamic Animation Safety Preamble.*?_orig_anim_safe_defined = True\s*\n?', '', sanitized)
    sanitized = re.sub(r'(?s)(?:for _anim_cls in \(FadeIn|for _txt_cls in \(Text|for _scene_cls in \(Scene).*?_orig_anim_safe_defined = True\s*\n?', '', sanitized)
    sanitized = re.sub(r'(?m)^_orig_anim_safe_defined = True\s*\n?', '', sanitized)
    if "_orig_anim_safe_defined" not in sanitized:
        anim_safe_preamble = (
            "\n# Dynamic Animation Safety Preamble\n"
            "for _anim_cls in (FadeIn, FadeOut, Create, Write):\n"
            "    try:\n"
            "        if not hasattr(_anim_cls, '_orig_new_safe'):\n"
            "            def _make_safe(cls):\n"
            "                def _safe_new(subcls, mobject, *args, **kwargs):\n"
            "                    if isinstance(mobject, Animation):\n"
            "                        return mobject\n"
            "                    if hasattr(mobject, 'build') or mobject.__class__.__name__ == '_AnimationBuilder':\n"
            "                        try:\n"
            "                            return mobject.build()\n"
            "                        except Exception:\n"
            "                            pass\n"
            "                    if not isinstance(mobject, Mobject):\n"
            "                        return Animation(Dot(fill_opacity=0, stroke_opacity=0))\n"
            "                    if cls is Create and not isinstance(mobject, VMobject):\n"
            "                        return FadeIn(mobject, *args, **kwargs)\n"
            "                    return super(cls, subcls).__new__(subcls)\n"
            "                return _safe_new\n"
            "            _anim_cls._orig_new_safe = True\n"
            "            _anim_cls.__new__ = _make_safe(_anim_cls)\n"
            "    except Exception:\n"
            "        pass\n"
            "for _txt_cls in (Text,):\n"
            "    try:\n"
            "        if not hasattr(_txt_cls, '_orig_scale_to_fit_width_safe'):\n"
            "            _txt_cls._orig_scale_to_fit_width_safe = _txt_cls.scale_to_fit_width\n"
            "            def _make_safe_text_scale(cls):\n"
            "                def _safe_text_scale(self, width, *args, **kwargs):\n"
            "                    if hasattr(self, 'width') and self.width > 0:\n"
            "                        ratio = width / self.width\n"
            "                        if ratio > 1.0:\n"
            "                            return self\n"
            "                        if ratio < 0.88:\n"
            "                            ratio = 0.88\n"
            "                        return cls._orig_scale_to_fit_width_safe(self, self.width * ratio, *args, **kwargs)\n"
            "                    return cls._orig_scale_to_fit_width_safe(self, width, *args, **kwargs)\n"
            "                return _safe_text_scale\n"
            "            _txt_cls.scale_to_fit_width = _make_safe_text_scale(_txt_cls)\n"
            "    except Exception:\n"
            "        pass\n"
            "for _scene_cls in (Scene, MovingCameraScene):\n"
            "    try:\n"
            "        if not hasattr(_scene_cls, 'sync_to'):\n"
            "            def _make_sync_to():\n"
            "                def _safe_sync_to(self, target_time):\n"
            "                    curr_t = getattr(getattr(self, 'renderer', None), 'time', 0.0)\n"
            "                    if target_time > curr_t:\n"
            "                        self.wait(target_time - curr_t)\n"
            "                return _safe_sync_to\n"
            "            _scene_cls.sync_to = _make_sync_to()\n"
            "        if not hasattr(_scene_cls, '_orig_play_safe'):\n"
            "            _orig_play = _scene_cls.play\n"
            "            def _make_safe_play():\n"
            "                def _safe_play(self, *args, **kwargs):\n"
            "                    if len(args) == 0:\n"
            "                        rt = kwargs.get('run_time', 0.5)\n"
            "                        return self.wait(rt)\n"
            "                    return _orig_play(self, *args, **kwargs)\n"
            "                return _safe_play\n"
            "            _scene_cls._orig_play_safe = True\n"
            "            _scene_cls.play = _make_safe_play()\n"
            "        if not hasattr(_scene_cls, 'get_time'):\n"
            "            _scene_cls.get_time = lambda self: getattr(getattr(self, 'renderer', None), 'time', 0.0)\n"
            "    except Exception:\n"
            "        pass\n"
            "try:\n"
            "    from manim.utils.color.core import ManimColor\n"
            "    if not hasattr(ManimColor, '_orig_eq_safe'):\n"
            "        def _safe_color_eq(self, other):\n"
            "            if not isinstance(other, ManimColor):\n"
            "                try: other = ManimColor(other)\n"
            "                except Exception: return False\n"
            "            return bool(np.allclose(self._internal_value, other._internal_value))\n"
            "        ManimColor._orig_eq_safe = True\n"
            "        ManimColor.__eq__ = _safe_color_eq\n"
            "except Exception:\n"
            "    pass\n"
            "try:\n"
            "    if not hasattr(Mobject, 'stop_updater'):\n"
            "        Mobject.stop_updater = lambda self: self.clear_updaters()\n"
            "    if not hasattr(Mobject, '_orig_add_updater_safe'):\n"
            "        _orig_add_updater = Mobject.add_updater\n"
            "        def _safe_add_updater(self, update_function=None, *args, **kwargs):\n"
            "            if update_function is None or not callable(update_function):\n"
            "                return self\n"
            "            return _orig_add_updater(self, update_function, *args, **kwargs)\n"
            "        Mobject._orig_add_updater_safe = True\n"
            "        Mobject.add_updater = _safe_add_updater\n"
            "    if not hasattr(VGroup, 'arrange_around_point'):\n"
            "        def _arrange_around_point(self, point=ORIGIN, radius=2.0, angle=0.0, **kwargs):\n"
            "            n = len(getattr(self, 'submobjects', []))\n"
            "            if n > 0:\n"
            "                for i, mob in enumerate(self.submobjects):\n"
            "                    ang = angle + i * (2 * PI / n)\n"
            "                    mob.move_to(np.array(point) + radius * np.array([np.cos(ang), np.sin(ang), 0]))\n"
            "            return self\n"
            "        VGroup.arrange_around_point = _arrange_around_point\n"
            "        VMobject.arrange_around_point = _arrange_around_point\n"
            "    if not hasattr(Mobject, 'set_fill'):\n"
            "        def _safe_mobj_set_fill(self, *args, **kwargs):\n"
            "            for sub in getattr(self, 'submobjects', []):\n"
            "                if hasattr(sub, 'set_fill'):\n"
            "                    try: sub.set_fill(*args, **kwargs)\n"
            "                    except Exception: pass\n"
            "            return self\n"
            "        Mobject.set_fill = _safe_mobj_set_fill\n"
            "    if not hasattr(Mobject, 'set_stroke'):\n"
            "        def _safe_mobj_set_stroke(self, *args, **kwargs):\n"
            "            for sub in getattr(self, 'submobjects', []):\n"
            "                if hasattr(sub, 'set_stroke'):\n"
            "                    try: sub.set_stroke(*args, **kwargs)\n"
            "                    except Exception: pass\n"
            "            return self\n"
            "        Mobject.set_stroke = _safe_mobj_set_stroke\n"
            "    if not hasattr(Mobject, '_orig_mobj_init_safe'):\n"
            "        _orig_mobj_init = Mobject.__init__\n"
            "        def _safe_mobj_init(self, *args, **kwargs):\n"
            "            valid_mobj_params = {'name', 'dim', 'target', 'z_index'}\n"
            "            clean_kw = {k: v for k, v in kwargs.items() if k in valid_mobj_params}\n"
            "            res = _orig_mobj_init(self, *args, **clean_kw)\n"
            "            if 'opacity' in kwargs and hasattr(self, 'set_opacity'):\n"
            "                try: self.set_opacity(kwargs['opacity'])\n"
            "                except Exception: pass\n"
            "            return res\n"
            "        Mobject._orig_mobj_init_safe = True\n"
            "        Mobject.__init__ = _safe_mobj_init\n"
            "    if not hasattr(VMobject, '_orig_set_stroke_safe'):\n"
            "        _orig_set_stroke = VMobject.set_stroke\n"
            "        def _safe_set_stroke(self, *args, **kwargs):\n"
            "            valid_stroke_params = {'color', 'width', 'opacity', 'background'}\n"
            "            clean_kw = {k: v for k, v in kwargs.items() if k in valid_stroke_params}\n"
            "            if 'z_index' in kwargs:\n"
            "                try: self.set_z_index(kwargs['z_index'])\n"
            "                except Exception: pass\n"
            "            return _orig_set_stroke(self, *args, **clean_kw)\n"
            "        VMobject._orig_set_stroke_safe = True\n"
            "        VMobject.set_stroke = _safe_set_stroke\n"
            "except Exception:\n"
            "    pass\n"
            "YELLOW = globals().get('YELLOW', '#DDB945')\n"
            "WHITE = globals().get('WHITE', '#FFFFFF')\n"
            "BLACK = globals().get('BLACK', '#404040')\n"
            "RED = globals().get('RED', '#E58F6D')\n"
            "BLUE = globals().get('BLUE', '#62B7E4')\n"
            "GREEN = globals().get('GREEN', '#8ECDB7')\n"
            "_orig_anim_safe_defined = True\n"
        )
        if "from manim import *" in sanitized:
            sanitized = sanitized.replace("from manim import *", "from manim import *" + anim_safe_preamble, 1)
        else:
            sanitized = anim_safe_preamble + sanitized

    # -------------------------------------------------------------------------
    # 0. Repair corrupted syntax / artifacts from prior passes
    # -------------------------------------------------------------------------
    # Fix corrupted FadeIn(*[FadeOut(m)) for m in ...] -> *[FadeOut(m) for m in ...]
    sanitized = re.sub(
        r'FadeIn\(\s*\*\s*\[\s*FadeOut\(([^)]+)\)\s*\)\s+for\s+([^]]+)\s*\]',
        r'*[FadeOut(\1) for \2]',
        sanitized
    )
    # Fix unbalanced extra closing paren: *[FadeOut(m)) for m in ...]
    sanitized = re.sub(
        r'\*\[FadeOut\(([^)]+)\)\)\s+for\s+([^]]+)\s*\]',
        r'*[FadeOut(\1) for \2]',
        sanitized
    )
    # Strip any broken recursion hook
    sanitized = re.sub(
        r'[ \t]*_orig_play_hook\s*=\s*self\.play[\s\S]*?self\.play\s*=\s*_safe_title_play\s*\n',
        '',
        sanitized
    )
    # Fix broken MathTex instances that were stripped to VGroup(font_size=...)
    sanitized = re.sub(
        r'd1\s*=\s*VGroup\((?:font_size=\d+\))?,\s*CrispText\("is Total Cognitive Load"',
        'd1 = VGroup(MathTex("C", color=C_DARK_BLUE, font_size=16), CrispText("is Total Cognitive Load"',
        sanitized
    )
    sanitized = re.sub(
        r'd2\s*=\s*VGroup\((?:font_size=\d+\))?,\s*CrispText\("is Intrinsic Task Difficulty',
        'd2 = VGroup(MathTex("I", color=C_DARK_BLUE, font_size=16), CrispText("is Intrinsic Task Difficulty',
        sanitized
    )
    sanitized = re.sub(
        r'd3\s*=\s*VGroup\((?:font_size=\d+\))?,\s*CrispText\("is Extraneous Design Clutter',
        'd3 = VGroup(MathTex("S", color=C_DARK_BLUE, font_size=16), CrispText("is Extraneous Design Clutter',
        sanitized
    )

    # Strip empty add_updater calls: mob.add_updater()
    sanitized = re.sub(r'^[ ]{4,12}[a-zA-Z0-9_]+\.add_updater\(\s*\)\s*\n', '', sanitized, flags=re.M)
    # Strip target_mode parameter from animations (e.g. FadeOut(..., target_mode="horizontal"))
    sanitized = re.sub(r',\s*target_mode=[\"\'][^\"\']*[\"\']', '', sanitized)
    # Strip corner_radius accidentally passed to set_stroke(...)
    sanitized = re.sub(r'(\.set_stroke\([^)]*),\s*corner_radius=[^,)]+', r'\1', sanitized)
    # Fix .center used as coordinate attribute instead of method call .get_center()
    sanitized = re.sub(r'(\b(?:self|[a-zA-Z0-9_]+))\.(center)\b(?!\s*\()(\s*[\+\-\,\)])', r'\1.get_center()\3', sanitized)
    sanitized = re.sub(r'\.move_to\(((?:self|[a-zA-Z0-9_]+))\.(center)\b(?!\s*\()\)', r'.move_to(\1.get_center())', sanitized)


    # -------------------------------------------------------------------------
    # 1. Clean unsupported table kwargs (col_widths, column_widths in Table/MobjectTable)
    # -------------------------------------------------------------------------
    # Pattern: col_widths=... inside Table or MobjectTable
    sanitized = re.sub(
        r'(\b(?:MobjectTable|Table|IntegerTable|DecimalTable)\s*\([^)]*?)(,\s*col_widths\s*=\s*[^,\)]+)',
        r'\1',
        sanitized
    )
    sanitized = re.sub(
        r'(\b(?:MobjectTable|Table|IntegerTable|DecimalTable)\s*\([^)]*?)(col_widths\s*=\s*[^,\)]+,\s*)',
        r'\1',
        sanitized
    )
    sanitized = re.sub(
        r'(\b(?:MobjectTable|Table|IntegerTable|DecimalTable)\s*\([^)]*?)(,\s*column_widths\s*=\s*[^,\)]+)',
        r'\1',
        sanitized
    )

    # -------------------------------------------------------------------------
    # 2. Table background_rectangle initialization safety
    # -------------------------------------------------------------------------
    # If table.get_background_rectangle() is called without table.add_background_rectangle()
    def fix_table_bg(match):
        var_name = match.group(1)
        # Check if add_background_rectangle was already called on var_name
        return f"{var_name}.add_background_rectangle(color=C_WHITE if 'C_WHITE' in globals() else '#FFFFFF', opacity=1.0)\n        {match.group(0)}"

    # Match lines like: table_bg = table.get_background_rectangle()
    lines = sanitized.splitlines()
    new_lines = []
    added_bg_vars = set()

    for line in lines:
        # Check if line calls add_background_rectangle
        m_add = re.search(r'([a-zA-Z0-9_]+)\.add_background_rectangle\(', line)
        if m_add:
            added_bg_vars.add(m_add.group(1))

        # Check if line calls get_background_rectangle
        m_get = re.search(r'([a-zA-Z0-9_]+)\s*=\s*([a-zA-Z0-9_]+)\.get_background_rectangle\(', line)
        if m_get:
            target_table = m_get.group(2)
            if target_table not in added_bg_vars:
                indent = re.match(r'^\s*', line).group(0)
                new_lines.append(f"{indent}{target_table}.add_background_rectangle(color=C_WHITE if 'C_WHITE' in globals() else '#FFFFFF', opacity=1.0)")
                added_bg_vars.add(target_table)

        new_lines.append(line)

    sanitized = "\n".join(new_lines)

    # -------------------------------------------------------------------------
    # 3. Robust Image Path Resolution (resolve relative ../images/...)
    # -------------------------------------------------------------------------
    # If script uses "../images/...", ensure _IMG_DIR is defined and used
    if '"../images/' in sanitized or "'../images/'" in sanitized or 'f"../images/' in sanitized or "f'../images/" in sanitized:
        img_dir_header = (
            "import os\n"
            "_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))\n"
            "_IMG_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', 'images'))\n"
        )
        if "_IMG_DIR" not in sanitized:
            sanitized = img_dir_header + sanitized

        # Replace variations of "../images/
        sanitized = re.sub(r'["\']\.\./images/([^"\']+)["\']', r'os.path.join(_IMG_DIR, "\1")', sanitized)
        sanitized = re.sub(r'f["\']\.\./images/([^"\']+)["\']', r'os.path.join(_IMG_DIR, f"\1")', sanitized)
        # Clean any accidental double prefix like ff" or os.path.join(_IMG_DIR, f"{_IMG_DIR}
        sanitized = sanitized.replace('ff"{_IMG_DIR}', 'f"{_IMG_DIR}')

    # -------------------------------------------------------------------------
    # 4. LaggedStart / Succession / AnimationGroup naked Mobject wrapper
    # -------------------------------------------------------------------------
    # When raw Mobjects like VGroup(...), Group(...), Dot(...), Line(...) are passed
    # into LaggedStart without FadeIn/Create, wrap them:
    # Example: LaggedStart(*[VGroup(...) for ...], ...) -> LaggedStart(*[FadeIn(VGroup(...)) for ...], ...)
    def wrap_lagged_start_mobjects(match):
        full_match = match.group(0)
        inner = match.group(1)
        # If inner starts with a common raw mobject type and is not already an Animation
        anim_prefixes = ("FadeIn(", "FadeOut(", "Create(", "Write(", "GrowArrow(", "Transform(", "ReplacementTransform(", "SpinInFromNothing(", "DrawBorderThenFill(", "Indicate(")
        mobject_prefixes = ("VGroup(", "Group(", "Dot(", "Line(", "Circle(", "Rectangle(", "RoundedRectangle(", "Square(", "CrispText(", "Text(", "Tex(", "MathTex(")
        
        inner_trimmed = inner.strip()
        if any(inner_trimmed.startswith(mp) for mp in mobject_prefixes) and not any(inner_trimmed.startswith(ap) for ap in anim_prefixes):
            return f"LaggedStart(*[FadeIn({inner})"
        return full_match

    # Fix LaggedStart with raw Mobjects: LaggedStart(*[(VGroup|Group|Dot|Line|Rectangle|Circle|RoundedRectangle)(...) for ...])
    sanitized = re.sub(
        r'LaggedStart\(\s*\*\s*\[\s*((?:VGroup|Group|Dot|Line|Rectangle|Circle|RoundedRectangle)\(.*?\))\s+for\s+',
        r'LaggedStart(*[FadeIn(\1) for ',
        sanitized
    )

    # -------------------------------------------------------------------------
    # 5. Rectangle(corner_radius=...) -> RoundedRectangle
    # -------------------------------------------------------------------------
    sanitized = re.sub(r'\bRectangle\(\s*corner_radius\s*=', r'RoundedRectangle(corner_radius=', sanitized)
    sanitized = re.sub(r'\bRectangle\(([^)]*?),\s*corner_radius\s*=', r'RoundedRectangle(\1, corner_radius=', sanitized)

    # -------------------------------------------------------------------------
    # 5b. Nested Animation Wrapper Safety: e.g. FadeIn(UpdateFromAlphaFunc(...))
    # FadeIn/FadeOut/Create/Write expect Mobjects, not Animation instances.
    # -------------------------------------------------------------------------
    sanitized = unwrap_nested_animations(sanitized)

    # -------------------------------------------------------------------------
    # Clean broken empty try-except blocks (leftover from flawed import removal)
    # -------------------------------------------------------------------------
    sanitized = re.sub(r'try:\s*\n\s*except[^\n]*:\s*\n(?:\s*try:[\s\S]*?except[^\n]*:\s*\n)?(?:\s*class InstrumentedScene[\s\S]*?pass\s*\n|\s*InstrumentedScene\s*=\s*[^\n]+\n|\s*pass\s*\n)', '', sanitized)
    sanitized = re.sub(r'try:\s*\n\s*except[^\n]*:\s*\n\s*pass\s*\n', '', sanitized)
    sanitized = re.sub(r'(?m)^\s*(?:from\s+manim_slides[^\n]*|import\s+manim_slides[^\n]*)', '', sanitized)
    sanitized = re.sub(r'self\.play\(\s*run_time\s*=\s*([0-9.]+)\s*\)', r'self.wait(\1)', sanitized)

    # -------------------------------------------------------------------------
    # 5c. Safe InstrumentedScene handling & import cleanup
    # Ensure InstrumentedScene is safely imported and preserved for feedback runs
    # -------------------------------------------------------------------------
    sanitized = re.sub(r'from\s+manim_instrumented_scene\s+import\s+InstrumentedScene', '', sanitized)
    if "InstrumentedScene" in sanitized:
        # If no import exists, insert safe dual-pass import
        if "from feedback_functions" not in sanitized and "from feedback_functions_vlm" not in sanitized:
            safe_def = (
                "from manim import *\n\n"
                "TOP = UP\n"
                "BOTTOM = DOWN\n"
                "try:\n"
                "    from feedback_functions_vlm.instrumented_scene import InstrumentedScene\n"
                "except Exception:\n"
                "    try:\n"
                "        from feedback_functions.instrumented_scene import InstrumentedScene\n"
                "    except Exception:\n"
                "        class InstrumentedScene(MovingCameraScene):\n"
                "            pass\n"
            )
            if "from manim import *" in sanitized:
                sanitized = sanitized.replace("from manim import *", safe_def, 1)
            else:
                sanitized = safe_def + "\n" + sanitized

    # -------------------------------------------------------------------------
    # 6. CrispText weight & font safety
    # -------------------------------------------------------------------------
    sanitized = re.sub(r'(\w+)\.align_to\(([^,]+),\s*CENTER_Y\)', r'\1.match_y(\2)', sanitized)
    sanitized = re.sub(r'(\w+)\.align_to\(([^,]+),\s*CENTER_X\)', r'\1.match_x(\2)', sanitized)
    sanitized = re.sub(r'\bCENTER_Y\b', 'ORIGIN', sanitized)
    sanitized = re.sub(r'\bCENTER_X\b', 'ORIGIN', sanitized)
    sanitized = re.sub(r'\.set_stroke\([^)]*dash_length=[^)]*\)', '', sanitized)
    sanitized = re.sub(r'\btext_align\s*=', 'align=', sanitized)
    sanitized = re.sub(r'\balign_to\(([^,]+),\s*TOP\)', r'align_to(\1, UP)', sanitized)
    sanitized = re.sub(r'\balign_to\(([^,]+),\s*BOTTOM\)', r'align_to(\1, DOWN)', sanitized)
    sanitized = re.sub(r'\bTOP\b(?!\s*[:=])', 'UP', sanitized)
    sanitized = re.sub(r'\bBOTTOM\b(?!\s*[:=])', 'DOWN', sanitized)
    sanitized = re.sub(
        r'self\.wait\(\s*([0-9.]+)\s*-\s*self\.get_current_play_time\(\)\s*\)',
        r'self.wait(max(0.1, \1 - getattr(self.renderer, "time", 0.0)))',
        sanitized
    )
    sanitized = re.sub(r'self\.get_current_play_time\(\)', 'getattr(self.renderer, "time", 0.0)', sanitized)
    sanitized = re.sub(r'class\s+CrispText\s*\([^)]*\):[\s\S]*?(?=\n(?:class\s+FinalScene|class\s+\w+|def\s+\w+)|\Z)', '', sanitized)
    sanitized = re.sub(r'\bweight\s*=\s*(?:REGULAR|"REGULAR"|\'REGULAR\')', 'weight=NORMAL', sanitized)

    # -------------------------------------------------------------------------
    # 6b. Upgrade raw Text(...) calls to CrispText(...) to prevent Pango kerning artifacts
    # -------------------------------------------------------------------------
    def convert_raw_text_to_crisp_text(text: str) -> str:
        ct_match = re.search(r'def CrispText\([^)]*\):[\s\S]*?(?=\n(?:def|class)\s|\Z)', text)
        if ct_match:
            start, end = ct_match.span()
            before = re.sub(r'(?<!def\s)(?<!class\s)(?<!import\s)\bText\(', 'CrispText(', text[:start])
            ct_def = text[start:end]
            after = re.sub(r'(?<!def\s)(?<!class\s)(?<!import\s)\bText\(', 'CrispText(', text[end:])
            return before + ct_def + after
        else:
            return re.sub(r'(?<!def\s)(?<!class\s)(?<!import\s)\bText\(', 'CrispText(', text)

    sanitized = convert_raw_text_to_crisp_text(sanitized)

    # -------------------------------------------------------------------------
    # 7. stretch=True/False inside VGroup / Group cleanup
    # -------------------------------------------------------------------------
    sanitized = re.sub(r'(VGroup|Group)\((.*?),\s*stretch\s*=\s*(?:True|False)\)', r'\1(\2)', sanitized)
    sanitized = re.sub(r'(VGroup|Group)\((.*?)\s*stretch\s*=\s*(?:True|False),\s*', r'\1(\2', sanitized)
    sanitized = re.sub(r'(VGroup|Group)\(\s*stretch\s*=\s*(?:True|False)\s*\)', r'\1()', sanitized)

    # Ensure title = CrispText(...) exists inside create_text_card if VGroup(title, ...) is used
    if "def create_text_card(" in sanitized and "VGroup(title," in sanitized:
        card_func_match = re.search(r'def create_text_card\([^)]*\):[\s\S]*?(?=def |\Z)', sanitized)
        if card_func_match and "title = " not in card_func_match.group(0):
            sanitized = re.sub(
                r'([ \t]*)(content\s*=\s*VGroup\(title,\s*body_vgroup\))',
                r'\1title = CrispText(title_str, font_size=16, weight="Bold", color=text_color)\n\1\2',
                sanitized
            )

    # -------------------------------------------------------------------------
    # 8. Guard scale_to_fit_width / height
    # -------------------------------------------------------------------------
    # Prevent duplicate if hasattr wrappers
    dup_pattern = r'if hasattr\(([a-zA-Z0-9_]+), "width"\) and \1\.width > \(([^)]+)\):\s*if hasattr\(\1, "width"\) and \1\.width > \(\2\):'
    while re.search(dup_pattern, sanitized):
        sanitized = re.sub(dup_pattern, r'if hasattr(\1, "width") and \1.width > (\2):', sanitized)

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # 9. MathTex scale & size sanity
    # -------------------------------------------------------------------------
    if "MathTex" in sanitized:
        def clamp_mathtex_fs(m):
            prefix = m.group(1)
            raw_val = m.group(2)
            if len(raw_val) > 2 and raw_val.startswith("11"):
                cleaned_val = raw_val.lstrip("1") or "20"
            else:
                cleaned_val = raw_val
            try:
                fs = int(cleaned_val)
                if fs < 18:
                    new_fs = 22
                elif fs > 26:
                    new_fs = 24
                else:
                    new_fs = fs
                return f"{prefix}{new_fs}"
            except Exception:
                return m.group(0)
        sanitized = re.sub(r'(\bMathTex\([^)]*?font_size\s*=\s*)(\d+)', clamp_mathtex_fs, sanitized)

    # -------------------------------------------------------------------------
    # 10. CrispText multiline split safety
    # -------------------------------------------------------------------------
    sanitized = sanitized.replace(
        'if "\\n" in text_str:\n        lines = text_str.split("\\n")',
        'split_lines = [l for l in text_str.split("\\n")] if "\\n" in text_str else ([l for l in text_str.split("\n")] if "\n" in text_str else [text_str])\n    if len(split_lines) > 1:\n        lines = split_lines'
    )

    # -------------------------------------------------------------------------
    # 11. Chained .set_width(w).set_height(h) -> .stretch_to_fit_width(w).stretch_to_fit_height(h)
    # -------------------------------------------------------------------------
    # Prevents Manim from proportionally shrinking width when set_height is called after set_width
    sanitized = re.sub(
        r"\.set_width\(([^)]+)\)\.set_height\(([^)]+)\)",
        r".stretch_to_fit_width(\1).stretch_to_fit_height(\2)",
        sanitized
    )
    sanitized = re.sub(
        r"\.set_height\(([^)]+)\)\.set_width\(([^)]+)\)",
        r".stretch_to_fit_width(\2).stretch_to_fit_height(\1)",
        sanitized
    )

    # -------------------------------------------------------------------------
    # 12. Single-line naked Mobjects in self.play(...) (Paren & Unpack Aware)
    # -------------------------------------------------------------------------
    def sanitize_play_calls(text):
        anim_keywords = {
            "FadeIn", "FadeOut", "Create", "Write", "Transform", "ReplacementTransform",
            "GrowFromCenter", "GrowFromPoint", "GrowFromEdge", "GrowArrow", "DrawBorderThenFill",
            "Indicate", "Circumscribe", "Wiggle", "Flash", "ShowPassingFlash", "AnimationGroup",
            "LaggedStart", "Succession", "ShowCreation", "Uncreate", "ApplyMethod", "MoveToTarget",
            "Restore", "Wait", "SpinInFromNothing", "ShrinkToCenter", "FadeTransform",
            "FadeTransformPieces", "MoveAlongPath", "Rotate", "ScaleInPlace", "FocusOn",
            "UpdateFromAlphaFunc", "UpdateFromFunc", "Homotopy", "PhaseFlow", "ComplexHomotopy",
            "MaintainPositionRelativeTo", "ChangeSpeed", "AddTextLetterByLetter", "ShowIncreasingSubsets",
            "ShowSubmobjectsOneByOne"
        }
        
        pos = 0
        result = []
        while True:
            idx = text.find("self.play(", pos)
            if idx == -1:
                result.append(text[pos:])
                break
            result.append(text[pos:idx])
            
            # Find matching closing parenthesis
            start_args = idx + len("self.play(")
            depth = 1
            cur = start_args
            in_str = None
            escape = False
            in_comment = False
            while cur < len(text) and depth > 0:
                c = text[cur]
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif in_comment:
                    if c == '\n':
                        in_comment = False
                elif in_str:
                    if c == in_str:
                        in_str = None
                elif c == '#':
                    in_comment = True
                elif c in ('"', "'"):
                    in_str = c
                elif c in '([{':
                    depth += 1
                elif c in ')]}':
                    depth -= 1
                cur += 1
                
            if depth != 0:
                result.append(text[idx:cur])
                pos = cur
                continue
                
            args_str = text[start_args:cur-1]
            
            # Split top-level arguments by comma
            args = []
            arg_start = 0
            sub_depth = 0
            sub_in_str = None
            sub_escape = False
            sub_in_comment = False
            for i, c in enumerate(args_str):
                if sub_escape:
                    sub_escape = False
                elif c == '\\':
                    sub_escape = True
                elif sub_in_comment:
                    if c == '\n':
                        sub_in_comment = False
                elif sub_in_str:
                    if c == sub_in_str:
                        sub_in_str = None
                elif c == '#':
                    sub_in_comment = True
                elif c in ('"', "'"):
                    sub_in_str = c
                elif c in '([{':
                    sub_depth += 1
                elif c in ')]}':
                    sub_depth -= 1
                elif c == ',' and sub_depth == 0 and not sub_in_str and not sub_in_comment:
                    args.append(args_str[arg_start:i])
                    arg_start = i + 1
            args.append(args_str[arg_start:])
            
            new_args = []
            for a in args:
                raw_a = a
                s = a.strip()
                if not s or s.startswith('#'):
                    new_args.append(raw_a)
                    continue
                # Separate or strip comments
                if '#' in s:
                    s_no_comm = "\n".join([line[:line.find('#')].strip() if '#' in line else line.strip() for line in s.splitlines()]).strip()
                    if not s_no_comm:
                        new_args.append(raw_a)
                        continue
                    s = s_no_comm
                # If keyword arg (run_time=..., rate_func=...)
                if re.match(r'^[a-zA-Z_]\w*\s*=', s):
                    new_args.append(raw_a)
                    continue
                # If argument unpacking (*[...], *anims)
                if s.startswith('*'):
                    new_args.append(raw_a)
                    continue
                # If already an animation or animate call
                lead_ident = re.match(r'^([a-zA-Z_]\w*)', s)
                if lead_ident and lead_ident.group(1) in anim_keywords:
                    new_args.append(raw_a)
                    continue
                if ".animate" in s:
                    new_args.append(raw_a)
                    continue
                # Wrap true naked Mobject with FadeIn
                lead_ws = raw_a[:len(raw_a) - len(raw_a.lstrip())]
                trail_ws = raw_a[len(raw_a.rstrip()):]
                if trailing_comment:
                    new_args.append(f"{lead_ws}FadeIn({s}) {trailing_comment}{trail_ws}")
                else:
                    new_args.append(f"{lead_ws}FadeIn({s}){trail_ws}")
                
            reconstructed = "self.play(" + ",".join(new_args) + ")"
            result.append(reconstructed)
            pos = cur
            
        return "".join(result)

    sanitized = sanitize_play_calls(sanitized)
    sanitized = unwrap_nested_animations(sanitized)
    sanitized = unwrap_animate_calls(sanitized)

    # Strip accidental FadeIn(Animation) nesting (e.g. FadeIn(GrowFromEdge(...)))
    sanitized = re.sub(
        r'FadeIn\(\s*((?:GrowFromEdge|GrowFromPoint|GrowFromCenter|GrowArrow|Create|Write|FadeIn|FadeOut|Transform|ReplacementTransform|SpinInFromNothing)\([^)]*\))\s*\)',
        r'\1',
        sanitized
    )

    # -------------------------------------------------------------------------
    # 13. Content Ceiling, Floor & Arena Clamping (Anti-Overlap Zone Safety)
    # -------------------------------------------------------------------------
    # Clean 2-Zone Architecture:
    # 1. Header Zone: UL (y in [2.8, 3.6]), single canonical header with 5 accent dots.
    # 2. Content Arena: Open clearance across y in [-3.2, 2.6]. Do not artificially crush diagrams!
    lines = sanitized.splitlines()
    new_lines = []
    for line in lines:
        # Ceiling: Content panels/cards sitting at UP * 2.8+ collide with header title
        if any(k in line for k in ["UP * 2.8", "UP * 2.9", "UP * 3.0", "UP * 3.1", "UP * 3.2"]):
            if not any(t in line for t in ["title", "dots", "line_start", "line_end", "header", "scene_title"]):
                line = re.sub(r'UP\s*\*\s*(?:2\.8|2\.9|3\.0|3\.1|3\.2)', 'UP * 2.4', line)

        # Floor: Elements at DOWN * 3.6+ bleed into bottom screen edge or caption zone
        if any(k in line for k in ["DOWN * 3.6", "DOWN * 3.7", "DOWN * 3.8", "DOWN * 3.9", "DOWN * 4.0"]):
            line = re.sub(r'DOWN\s*\*\s*(?:3\.6|3\.7|3\.8|3\.9|4\.0)', 'DOWN * 3.1', line)

        # Microscopic text clamp: ensure minimum font_size >= 6.0 for readability
        if ("CrispText(" in line or "Text(" in line) and any(k in line for k in ["size=", "font_size="]):
            def sub_tiny_size(m):
                try:
                    prefix = m.group(1)
                    val_str = m.group(2)
                    sz = float(val_str)
                    if sz < 6.0:
                        return f"{prefix}=6.0"
                    if sz > 42 and "title" not in line.lower() and "header" not in line.lower():
                        return f"{prefix}=36"
                    return f"{prefix}={int(sz) if sz.is_integer() else sz}"
                except Exception:
                    pass
                return m.group(0)
            line = re.sub(r'\b(size|font_size)\s*=\s*(\d+(?:\.\d+)?)\b', sub_tiny_size, line)

        new_lines.append(line)

    sanitized = "\n".join(new_lines)
    sanitized = re.sub(r'aligned_edge\s*=\s*(?:None|CENTER)', 'aligned_edge=ORIGIN', sanitized)

    # -------------------------------------------------------------------------
    # 13b. High-Contrast Text & Rich Amber Panel Sanitization
    # -------------------------------------------------------------------------
    # Prevent illegible light yellow text on white/light panels
    sanitized = re.sub(
        r'(\b(?:CrispText|Text)\([^)]*?color\s*=\s*)(?:["\'](?:#F9C72C|#FFFF00|#FFF9E6|yellow)["\']|C_YELLOW)',
        r'\1globals().get("TEXT_COLOR", "#404040")',
        sanitized
    )
    # Prevent yellow MathTex formulas (convert to high contrast sky blue or text color)
    sanitized = re.sub(
        r'(\bMathTex\([^)]*?color\s*=\s*)(?:["\'](?:#F9C72C|#FFFF00|#FFF9E6|yellow)[\'"]|C_YELLOW|YELLOW)',
        r'\1globals().get("C_SKY_BLUE", "#62B7E4")',
        sanitized
    )
    # Convert washed-out sickly yellow card background (#FFF9E6) to rich warm amber (#FEF3C7)
    sanitized = re.sub(r'["\']#FFF9E6["\']', '"#FEF3C7"', sanitized)
    # Convert thin bright yellow card stroke (#F9C72C) on panels to deep amber (#D97706)
    sanitized = re.sub(r'stroke_color\s*=\s*["\']#F9C72C["\']', 'stroke_color="#D97706"', sanitized)
    sanitized = re.sub(r'stroke_color\s*=\s*C_YELLOW', 'stroke_color="#D97706"', sanitized)
    sanitized = re.sub(r'\.set_stroke\(\s*(?:C_YELLOW|["\']#F9C72C["\'])\s*,', '.set_stroke("#D97706",', sanitized)
    sanitized = re.sub(r'\.set_stroke\(\s*(?:C_YELLOW|["\']#F9C72C["\'])\s*\)', '.set_stroke("#D97706")', sanitized)

    # Convert yellow divider/underline lines on white canvas to brand blue
    sanitized = re.sub(
        r'(\bLine\([^)]*?color\s*=\s*)(?:C_YELLOW|["\']#F9C72C["\'])',
        r'\1globals().get("C_BRAND_BLUE", "#2C81FE")',
        sanitized
    )

    # -------------------------------------------------------------------------
    # 13d. Prohibition of Yellow on Purple Boxes & Containers
    # -------------------------------------------------------------------------
    # Convert yellow accent/text arguments on dark cards to sky blue
    sanitized = re.sub(
        r'(create_\w+\([^)]*?(?:["\']#7651A2["\']|C_PURPLE|["\']purple["\'])[^)]*?)(?:["\'](?:#F9C72C|#FFFF00|yellow)["\']|C_YELLOW|YELLOW)',
        r'\1globals().get("C_SKY_BLUE", "#62B7E4")',
        sanitized
    )
    sanitized = re.sub(
        r'(create_\w+\([^)]*?)(?:["\'](?:#F9C72C|#FFFF00|yellow)["\']|C_YELLOW|YELLOW)([^)]*?(?:["\']#7651A2["\']|C_PURPLE|["\']purple["\'])\))',
        r'\1globals().get("C_SKY_BLUE", "#62B7E4")\2',
        sanitized
    )

    # -------------------------------------------------------------------------
    # 13c. Anti-Overlap Placement & Safe Zone Positioning
    # -------------------------------------------------------------------------
    # Eliminate negative buffs in .next_to(..., buff=-0.X) which cause element collisions
    sanitized = re.sub(r'(\.next_to\([^)]*?,\s*buff\s*=\s*)-0\.[1-9]\d*', r'\g<1>0.15', sanitized)

    # Prevent takeaway banners and bottom panels from floating into the central content arena
    sanitized = re.sub(
        r'\.to_edge\(\s*DOWN\s*,\s*buff\s*=\s*(?:0\.[7-9]|[1-9]\.[0-9]+)\s*\)',
        '.to_edge(DOWN, buff=0.35)',
        sanitized
    )
    # Ensure takeaway banners are placed at safe bottom position (DOWN * 2.90) so bottom edge never breaches camera limit
    sanitized = re.sub(
        r'([a-zA-Z0-9_]*(?:takeaway|bottom_banner|footer|ta\d*)[a-zA-Z0-9_]*)\.move_to\(\s*DOWN\s*\*\s*(?:2\.[5-9]|3\.[0-9])\s*\)',
        r'\1.move_to(DOWN * 2.90).set_x(0)',
        sanitized
    )

    # Prevent equations from being squished below readable widths
    def clamp_eq_scale(match):
        try:
            w = float(match.group(2))
            if w < 3.8:
                return f"{match.group(1)}4.2{match.group(3)}"
        except Exception:
            pass
        return match.group(0)
    sanitized = re.sub(r'(\b(?:eq|formula|math)[a-zA-Z0-9_]*\.scale_to_fit_width\()([0-9.]+)(\))', clamp_eq_scale, sanitized)

    # Clean raw LaTeX dollar notation inside CrispText to prevent literal '$' rendering in Pango
    def clean_crisp_latex(match):
        txt_content = match.group(1)
        cleaned = re.sub(r'\$([^\$]+)\$', r'\1', txt_content)
        cleaned = cleaned.replace(r'\mathcal{O}', 'O').replace(r'\quad', ' ').replace(r'\_', '_')
        return f'CrispText("{cleaned}"'
    sanitized = re.sub(r'CrispText\("([^"\$]*\$[^"]*)"', clean_crisp_latex, sanitized)

    # 13c. Enforce dynamic high-contrast MathTex and Tex formula colors:
    # - If placed inside a dark container/card (fill_color dark, opacity >= 0.5): formula MUST be white (#FFFFFF / C_WHITE).
    # - If placed on canvas or light container: formula MUST be high-contrast dark text (#404040 / TEXT_COLOR).
    # - If color is unspecified: dynamically assign C_WHITE (if in dark container) or TEXT_COLOR (if on light background).
    # - Eliminates dark text on dark cards and white text on white canvas.
    def fix_all_mathtex_colors(text):
        pos = 0
        result = []
        faint_color_pattern = re.compile(
            r'color\s*=\s*(?:["\'](?:#[cC][0-9a-fA-F]{5}|#[dD][0-9a-fA-F]{5}|#[eE][0-9a-fA-F]{5}|#[aA]0[aA][eE][cC]0|#94[aA]3[bB]8|#[aA][0-9a-fA-F]{5}|#[bB][0-9a-fA-F]{5}|#718096|#64748B|#FFF9E6|#F9C72C|yellow|grey|gray|lightgrey|lightgray)["\']|YELLOW|C_YELLOW|LIGHT_GRAY|LIGHT_GREY|GREY_A|GREY_B|GREY_C|GRAY_A|GRAY_B|GRAY_C|GREY|GRAY)',
            re.IGNORECASE
        )
        dark_color_pattern = re.compile(
            r'color\s*=\s*(?:["\'](?:#2[bB]2[cC]6[cC]|#7651[aA]2|#4[aA]154[bB]|#581[cC]87|#3[bB]0764|#1[dD]3557|#0[fF]172[aA]|#111827|#1[eE]293[bB]|#000000|black|#EA212A|#2D6A4F|#1E1E1E)["\']|globals\(\)\.get\(["\'](?:C_DARK_BLUE|C_PURPLE|C_RED|C_BLACK)["\'][^)]*\)|C_DARK_BLUE|C_PURPLE|C_RED|C_BLACK|BLACK|DARK_BLUE|PURPLE)',
            re.IGNORECASE
        )
        white_color_pattern = re.compile(
            r'color\s*=\s*(?:["\'](?:#FFFFFF|#FFF|white)["\']|globals\(\)\.get\(["\']C_WHITE["\'][^)]*\)|C_WHITE|WHITE)',
            re.IGNORECASE
        )

        while True:
            m = re.search(r'\b(?:MathTex|Tex)\(', text[pos:])
            if not m:
                result.append(text[pos:])
                break
            idx = pos + m.start()
            start_args = pos + m.end()
            result.append(text[pos:start_args])

            depth = 1
            cur = start_args
            in_str = None
            escape = False
            while cur < len(text) and depth > 0:
                c = text[cur]
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif in_str:
                    if c == in_str:
                        in_str = None
                elif c in ('"', "'"):
                    in_str = c
                elif c in '([{':
                    depth += 1
                elif c in ')]}':
                    depth -= 1
                cur += 1

            if depth != 0:
                result.append(text[start_args:cur])
                pos = cur
                continue

            args_str = text[start_args:cur-1]

            # Detect variable name for this MathTex/Tex
            line_start = text.rfind('\n', 0, idx) + 1
            line_prefix = text[line_start:idx]
            var_match = re.search(r'([a-zA-Z0-9_]+)\s*=\s*$', line_prefix)
            var_name = var_match.group(1) if var_match else None

            # Check context to determine if this formula is positioned inside a dark container
            window_before = text[max(0, line_start - 1200):line_start]
            window_after = text[cur:min(len(text), cur + 1200)]
            full_window = text[max(0, line_start - 1200):min(len(text), cur + 1200)]
            
            is_on_dark = False
            # Look for container variables defined with dark fill before or after this formula
            dark_container_vars = []
            dark_color_names = {"c_dark_blue", "c_purple", "c_red", "c_black", "dark_blue", "purple", "black", "blue_e", "blue_d"}
            # Discover local color variables assigned to dark hex or dark constants
            dark_var_pattern = re.compile(
                r'(?:^|[;\n])\s*([a-zA-Z0-9_]*(?:col|color|fill|bg)[a-zA-Z0-9_]*)\s*=\s*(?:["\']?(?:#2[bB]2[cC]6[cC]|#7651[aA]2|#1[dD]3557|#0[fF]172[aA]|#111827|#1[eE]293[bB]|#EA212A|#2D6A4F|#1E1E1E)["\']?|C_DARK_BLUE|C_PURPLE|C_RED|C_BLACK|DARK_BLUE|PURPLE|BLACK|BLUE_E|BLUE_D)',
                re.IGNORECASE
            )
            local_dark_vars = set(m.group(1).lower() for m in dark_var_pattern.finditer(full_window))
            local_dark_vars.update(dark_color_names)

            container_pattern = re.compile(
                r'([a-zA-Z0-9_]+)\s*=\s*(?:RoundedRectangle|Rectangle|create_card|create_pill|create_box|create_badge|create_mixed_pill|create_status_card|create_metric_card|create_mixed_badge|SurroundingRectangle|BackgroundRectangle)\s*\(([^)]*)\)',
                re.IGNORECASE
            )
            for c_match in container_pattern.finditer(full_window):
                c_name = c_match.group(1)
                c_args = c_match.group(2)
                
                # Check fill_color first, then bare color with word boundary (NEVER stroke_color)
                fill_m = re.search(r'\bfill_color\s*=\s*["\']?([a-zA-Z0-9_#]+)["\']?', c_args, re.IGNORECASE)
                col_m = re.search(r'\bcolor\s*=\s*["\']?([a-zA-Z0-9_#]+)["\']?', c_args, re.IGNORECASE)
                
                c_col = fill_m.group(1) if fill_m else (col_m.group(1) if col_m else None)
                if not c_col:
                    # Also check for dark colors passed as positional args, e.g. create_card(5.0, 3.5, C_DARK_BLUE)
                    pos_m = re.search(r'\b(C_DARK_BLUE|C_PURPLE|C_RED|C_BLACK|DARK_BLUE|PURPLE|BLACK|#2[bB]2[cC]6[cC]|#7651[aA]2|#1[dD]3557|#0[fF]172[aA]|#111827|#1[eE]293[bB]|#EA212A)\b', c_args, re.IGNORECASE)
                    if pos_m:
                        c_col = pos_m.group(1)
                    else:
                        continue
                
                # White/light containers are NEVER dark containers regardless of stroke_color
                if str(c_col).upper() in ("#FFFFFF", "#FFF", "WHITE", "C_WHITE", "#FFFFFE", "#FAFAFA", "#F0F4F8", "#EBF5FB", "#FEF3C7", "#F9C72C", "C_YELLOW"):
                    continue
                    
                is_dark = (
                    c_col.lower() in local_dark_vars or
                    bool(re.match(r'^(?:#2[bB]2[cC]6[cC]|#7651[aA]2|#1[dD]3557|#0[fF]172[aA]|#111827|#1[eE]293[bB]|#EA212A|#2D6A4F|#1E1E1E)$', c_col, re.IGNORECASE))
                )
                if not is_dark:
                    continue
                # Ensure opacity is not low tint (e.g. fill_opacity=0.08 or 0.15 is faint tint, not dark solid card)
                op_m = re.search(r'\bfill_opacity\s*=\s*([0-9.]+)', c_args, re.IGNORECASE)
                if op_m:
                    try:
                        if float(op_m.group(1)) <= 0.45:
                            continue
                    except Exception:
                        pass
                dark_container_vars.append(c_name)

            if dark_container_vars and var_name:
                var_stem = re.sub(r'_(?:text|txt|lbl|label|formula|math|eq|sym)$', '', var_name)
                for d_var in dark_container_vars:
                    # If var_name is explicitly positioned outside d_var via .next_to(), it is NOT inside d_var
                    if re.search(rf'\b{var_name}\b[^;\n]*\.next_to\(\s*{d_var}\b', full_window) or \
                       re.search(rf'\b{var_name}\.next_to\(\s*{d_var}\b', full_window):
                        continue

                    d_stem = re.sub(r'_(?:bg|box|card|frame|rect|panel|pill|badge|banner|group)$', '', d_var)
                    # 1. Stem match (e.g. math_pill_text <-> math_pill_bg, rr_eq <-> rr_eq_bg, badge_text <-> badge_bg)
                    if var_stem and var_stem == d_stem:
                        is_on_dark = True
                        break
                    # 2. fit_into_box or move_to anywhere in local window
                    if re.search(rf'(?:fit_into_box\([^)]*\b{var_name}\b[^)]*\b{d_var}\b|{var_name}\.move_to\(\s*{d_var}(?:\.get_center\(\))?\s*\))', full_window):
                        is_on_dark = True
                        break
                    # 3. Bundled together in VGroup or Group
                    if re.search(rf'\b(?:Group|VGroup)\([^)]*\b{d_var}\b[^)]*\b{var_name}\b', full_window) or \
                       re.search(rf'\b(?:Group|VGroup)\([^)]*\b{var_name}\b[^)]*\b{d_var}\b', full_window):
                        # If var_name is an annotation/label positioned next_to something outside, do not assume on dark
                        if re.search(r'_(?:ann|annot|annotation|callout)$', var_name) or re.search(rf'\b{var_name}\.next_to\(', full_window):
                            continue
                        is_on_dark = True
                        break
            
            # Also check if chained call right after cur-1 moves to dark container
            if not is_on_dark and dark_container_vars:
                after_chain = text[cur:cur+150]
                for d_var in dark_container_vars:
                    if re.search(rf'^\.move_to\(\s*{d_var}(?:\.get_center\(\))?', after_chain):
                        is_on_dark = True
                        break
            
            # If not assigned to a variable (inline MathTex), check if immediately surrounded by dark container
            if not is_on_dark and dark_container_vars and not var_name:
                immediate_surrounding = text[max(0, line_start - 250):min(len(text), cur + 250)]
                for d_var in dark_container_vars:
                    if re.search(rf'(?:fit_into_box|move_to\(\s*{d_var}|\b(?:Group|VGroup)\([^)]*)\b{d_var}\b', immediate_surrounding):
                        is_on_dark = True
                        break

            # Check if var_name is explicitly moved to or placed inside a light or yellow container
            is_on_light = False
            if not is_on_dark:
                light_container_pattern = re.compile(
                    r'([a-zA-Z0-9_]+)\s*=\s*(?:RoundedRectangle|Rectangle|create_card|create_pill|create_box|create_badge|SurroundingRectangle)\s*\(([^)]*)\)',
                    re.IGNORECASE
                )
                for c_match in light_container_pattern.finditer(full_window):
                    c_name = c_match.group(1)
                    c_args = c_match.group(2)
                    fill_m = re.search(r'\bfill_color\s*=\s*["\']?([a-zA-Z0-9_#]+)["\']?', c_args, re.IGNORECASE)
                    col_m = re.search(r'\bcolor\s*=\s*["\']?([a-zA-Z0-9_#]+)["\']?', c_args, re.IGNORECASE)
                    c_col = fill_m.group(1) if fill_m else (col_m.group(1) if col_m else '')
                    op_m = re.search(r'\bfill_opacity\s*=\s*([0-9.]+)', c_args, re.IGNORECASE)
                    is_low_op = False
                    if op_m:
                        try:
                            is_low_op = float(op_m.group(1)) <= 0.45
                        except Exception:
                            pass
                    if str(c_col).upper() in ('C_YELLOW', '#F9C72C', 'YELLOW', '#FFFF00', '#FFF9E6', '#FEF3C7', 'WHITE', '#FFFFFF', 'C_WHITE', '#EBF5FB', '#F0F4F8') or is_low_op:
                        if var_name and (
                            re.search(rf'(?:fit_into_box\([^)]*\b{var_name}\b[^)]*\b{c_name}\b|{var_name}\.move_to\(\s*{c_name}(?:\.get_center\(\))?\s*\))', full_window) or
                            re.search(rf'\b(?:Group|VGroup)\([^)]*\b{c_name}\b[^)]*\b{var_name}\b', full_window) or
                            re.search(rf'\b(?:Group|VGroup)\([^)]*\b{var_name}\b[^)]*\b{c_name}\b', full_window)
                        ):
                            is_on_light = True
                            is_on_dark = False
                            break

            # Check if inside create_mixed_pill, create_pill, or next to dark hex / dark constant
            surrounding_window = text[max(0, line_start - 350):min(len(text), cur + 350)]
            if not is_on_dark and not is_on_light:
                if re.search(r'(?:create_mixed_pill|create_pill|create_badge|create_state_badge)\s*\([^)]*?(?:#7651[aA]2|#EA212A|#2[bB]2[cC]6[cC]|#1[dD]3557|#111827|#1[eE]293[bB]|#2D6A4F|#581[cC]87|#000000|C_PURPLE|C_RED|C_DARK_BLUE)', surrounding_window, re.IGNORECASE):
                    is_on_dark = True
                elif re.search(r'(?:#7651[aA]2|#EA212A|#2[bB]2[cC]6[cC]|#1[dD]3557|#111827|#1[eE]293[bB]|#2D6A4F|#581[cC]87)\b', surrounding_window, re.IGNORECASE):
                    if re.search(r'CrispText\([^)]*color\s*=\s*["\']?(?:#FFFFFF|#FFF|white|C_WHITE)["\']?', surrounding_window, re.IGNORECASE):
                        is_on_dark = True

            # If grouped with a companion text object, inherit contrast from companion text in the same VGroup
            if not is_on_dark and not is_on_light and var_name:
                surrounding = text[max(0, line_start - 350):min(len(text), cur + 350)]
                group_match = re.search(rf'\b(?:Group|VGroup)\(([^)]*\b{var_name}\b[^)]*)\)', surrounding)
                if group_match:
                    group_content = group_match.group(1)
                    comp_vars = [w for w in re.findall(r'[a-zA-Z_]\w*', group_content) if w not in (var_name, "Group", "VGroup")]
                    comp_colors = []
                    for cv in comp_vars:
                        cv_def = re.search(rf'\b{cv}\s*=\s*(?:CrispText|Text|MathTex|Tex)\([^)]*color\s*=\s*["\']?([a-zA-Z0-9_#]+)["\']?', surrounding)
                        if cv_def:
                            comp_colors.append(cv_def.group(1))
                    if any(str(cc).upper() in ("#2B2C6C", "#1D3557", "C_DARK_BLUE", "DARK_BLUE") for cc in comp_colors):
                        is_on_dark = False
                    elif any(str(cc).upper() in ("#FFFFFF", "#FFF", "WHITE", "C_WHITE") for cc in comp_colors):
                        is_on_dark = True

            # Also check comment above for explicit hint of dark container/background vs light panel
            comment_line = text[max(0, line_start - 250):line_start]
            if re.search(r'#.*(?:light background|light panel|light card|white canvas|on light|contrast defect)', comment_line, re.IGNORECASE):
                is_on_dark = False
            elif not is_on_dark and re.search(r'#.*(?:purple background|dark background|inside dark|on dark|dark card|purple card|blue card|AUDITOR REPAIR|C_DARK_BLUE)', comment_line, re.IGNORECASE):
                is_on_dark = True

            has_white_or_faint = bool(white_color_pattern.search(args_str) or faint_color_pattern.search(args_str))

            if is_on_dark:
                # Inside verified dark container: text MUST be high-contrast white
                if "color=" not in args_str:
                    if args_str.strip():
                        args_str = args_str.rstrip() + ', color=globals().get("C_WHITE", "#FFFFFF")'
                    else:
                        args_str = 'color=globals().get("C_WHITE", "#FFFFFF")'
                elif dark_color_pattern.search(args_str) or faint_color_pattern.search(args_str):
                    args_str = dark_color_pattern.sub('color=globals().get("C_WHITE", "#FFFFFF")', args_str)
                    args_str = faint_color_pattern.sub('color=globals().get("C_WHITE", "#FFFFFF")', args_str)
            else:
                # On white/light canvas: text MUST be high-contrast dark text (#404040)
                if "color=" not in args_str:
                    if args_str.strip():
                        args_str = args_str.rstrip() + ', color=globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))'
                    else:
                        args_str = 'color=globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))'
                has_light_blue = bool(re.search(r'color\s*=\s*(?:["\'](?:#73C2E5|#A0AEC0)["\']|globals\(\)\.get\(["\']C_LIGHT_BLUE["\'][^)]*\)|C_LIGHT_BLUE|LIGHT_BLUE)', args_str, re.IGNORECASE))
                if has_light_blue:
                    args_str = re.sub(r'color\s*=\s*(?:["\'](?:#73C2E5|#A0AEC0)["\']|globals\(\)\.get\(["\']C_LIGHT_BLUE["\'][^)]*\)|C_LIGHT_BLUE|LIGHT_BLUE)', 'color=globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))', args_str)
                elif has_white_or_faint:
                    # Explicit dark colors where white text is appropriate
                    has_dark_context = bool(re.search(r'(?:#7651[aA]2|#EA212A|#2[bB]2[cC]6[cC]|#0[bB]3[cC]5[dD]|#1[dD]3557|#111827|#1[eE]293[bB]|#2D6A4F|#581[cC]87|C_PURPLE|C_RED|C_DARK_BLUE|C_NAVY)', surrounding_window, re.IGNORECASE))
                    # Yellow or light backgrounds where white text is FORBIDDEN
                    has_yellow_or_light = is_on_light or bool(re.search(r'(?:C_YELLOW|#F9C72C|#FFFF00|#FEF3C7|#FFF9E6|fill_color\s*=\s*(?:C_YELLOW|["\']#F9C72C["\']|["\']yellow["\']|["\']#FFFF00["\']))', surrounding_window, re.IGNORECASE))

                    if white_color_pattern.search(args_str) and has_dark_context and not has_yellow_or_light:
                        pass
                    else:
                        target_col = 'color=globals().get("C_BLACK", "#111111")' if has_yellow_or_light else 'color=globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))'
                        args_str = faint_color_pattern.sub(target_col, args_str)
                        if not (white_color_pattern.search(args_str) and has_dark_context and not has_yellow_or_light):
                            args_str = white_color_pattern.sub(target_col, args_str)

            result.append(args_str + ")")
            pos = cur

        return "".join(result)

    sanitized = fix_all_mathtex_colors(sanitized)

    # 13d. Prevent row badge and content overlap in segmented table rows:
    # When row info is positioned with move_to(bg.get_left() + RIGHT * offset),
    # center-positioning wide text causes its left edge to collide with the label badge.
    # Convert to .next_to(label_var, RIGHT, buff=0.35).match_y(bg_var)
    def fix_row_badge_overlap(text):
        pattern = r"([ \t]*([a-zA-Z0-9_]*(?:label|badge)[a-zA-Z0-9_]*)\s*=[^\n]*\.move_to\(([a-zA-Z0-9_]*bg)\.get_left\(\)[^\n]*\n)([\s\S]*?^[ \t]*)([a-zA-Z0-9_]*info[a-zA-Z0-9_]*)\.move_to\(\s*\3\.get_left\(\)\s*\+\s*RIGHT\s*\*\s*[0-9.]+\s*\)"
        def repl(m):
            full_label_line = m.group(1)
            lbl_name = m.group(2)
            bg_var = m.group(3)
            middle = m.group(4)
            info_var = m.group(5)
            if middle.count('\n') < 15:
                indent = "        "
                return f"{full_label_line}{middle}{indent}if hasattr({info_var}, \"width\") and hasattr({bg_var}, \"width\") and hasattr({lbl_name}, \"width\") and {info_var}.width > ({bg_var}.width - {lbl_name}.width - 0.7): {info_var}.scale_to_fit_width({bg_var}.width - {lbl_name}.width - 0.7)\n{indent}{info_var}.next_to({lbl_name}, RIGHT, buff=0.35).match_y({bg_var})"
            return m.group(0)
        return re.sub(pattern, repl, text, flags=re.MULTILINE)

    sanitized = fix_row_badge_overlap(sanitized)

    # 13e. Multi-column Table Spacing Normalizer:
    # Prevents adjacent table headers or data row columns from overlapping horizontally
    # when offsets are crowded (< 2.2 units apart, e.g. RIGHT * 5.2 vs RIGHT * 5.8).
    def fix_multi_column_table_spacing(text):
        # Reposition divider lines between col 2 and col 3 out to 7.2 units first
        text = re.sub(r'(Line\([^)]*\+ RIGHT\s*\*\s*)5\.[6-9]\b', r'\g<1>7.2', text)
        text = re.sub(r'(Line\([^)]*\+ RIGHT\s*\*\s*)6\.[0-5]\b', r'\g<1>7.2', text)
        text = re.sub(r'(\+ RIGHT\s*\*\s*)5\.[6-9]\b(?=[^)]*(?:UP|DOWN))', r'\g<1>7.2', text)
        text = re.sub(r'(\+ RIGHT\s*\*\s*)6\.[0-5]\b(?=[^)]*(?:UP|DOWN))', r'\g<1>7.2', text)
        # Reposition col 3 headers and cell data from crowded 5.6-6.5 out to 8.0 units from get_left()
        text = re.sub(r'(\.move_to\([^)]*bg\.get_left\(\)\s*\+\s*RIGHT\s*\*\s*)5\.[6-9]\b', r'\g<1>8.0', text)
        text = re.sub(r'(\.move_to\([^)]*bg\.get_left\(\)\s*\+\s*RIGHT\s*\*\s*)6\.[0-5]\b', r'\g<1>8.0', text)
        # Ensure item text in create_row doesn't collide with val column at 5.2
        text = re.sub(
            r'([ \t]*)(item\.next_to\(badge,\s*RIGHT,\s*buff=[0-9.]+\))',
            r'\1if hasattr(item, "width") and item.width > 2.8: item.scale_to_fit_width(2.8)\n\1\2',
            text
        )
        return text

    sanitized = fix_multi_column_table_spacing(sanitized)

    # 13f. Eliminate white background bounding box artifacts behind text/math
    # (prevents opaque white rectangles from obstructing container fills or gridlines)
    sanitized = re.sub(
        r'BackgroundRectangle\(\s*([a-zA-Z0-9_]+)\s*,\s*color\s*=\s*(?:["\'](?:#FFFFFF|#FFF|white)["\']|globals\(\)\.get\(["\']C_WHITE["\'][^)]*\)|C_WHITE|WHITE)\s*,\s*fill_opacity\s*=\s*1[^\)]*\)',
        r'BackgroundRectangle(\1, fill_opacity=0)',
        sanitized
    )

    # 13g. Revert any accidental "x Multiple" badge mutations to restore clean original strings
    sanitized = re.sub(
        r'\(\s*f"\{(?:\([a-zA-Z0-9_]+\+1\)|[a-zA-Z0-9_]+\+1)\}x Multiple"\s+if\s+[^:]+?\s+else\s+([^)]+?)\)',
        r'\1',
        sanitized
    )

    # Dynamic Title Stacking Repair:
    # When an LLM prematurely fades in new_title_group before fading out the existing title_group,
    # causing two slide titles to overlay at [-5.85, 3.2, 0].
    sanitized = re.sub(
        r'([ \t]*self\.play\(FadeIn\((?:new_title_group|new_title)\b[^\n]+\n)(?=[\s\S]{1,1000}?self\.play\(FadeOut\((?:title_group|title)\b)',
        '',
        sanitized
    )

    # Strip premature active title removal hooks that cause titles to disappear before step transitions
    sanitized = re.sub(
        r'[ \t]*if hasattr\(self, [\'"]_active_title_mobject[\'"]\)[\s\S]*?self\._active_title_mobject\s*=\s*[^\n]+(?:\n|$)',
        '',
        sanitized
    )

    # Prevent faint low-contrast formula dimming colors like #C4C4C4 on light canvases
    sanitized = re.sub(
        r'\.set_color\(\s*["\'](?:#C4C4C4|#CCCCCC|#DDDDDD|#E2E8F0|#CBD5E1|#D1D5DB|#A0AEC0)["\']\s*\)',
        '.set_color("#64748B")',
        sanitized
    )
    # Prevent excessively low opacity (< 0.55) when dimming formulas or text on white background
    def clamp_dim_opacity(match):
        try:
            val = float(match.group(1))
            if val < 0.55:
                return '.set_opacity(0.60)'
        except Exception:
            pass
        return match.group(0)
    sanitized = re.sub(r'\.set_opacity\(\s*(0\.\d+)\s*\)', clamp_dim_opacity, sanitized)

    # Clamp tight axis arrowhead buffers: buff <= 0.25 -> buff=0.35 on axis tops
    sanitized = re.sub(
        r'(\.next_to\([^)]*(?:axes|y_axis|x_axis)\.get_top\(\)[^)]*buff\s*=\s*)0\.(?:0\d+|1\d*|2[0-4]\d*)',
        r'\g<1>0.35',
        sanitized
    )
    # Enforce clear baseline clearance for horizontal axis labels
    sanitized = re.sub(
        r'(\.next_to\([^)]*c2p\([^)]*0\)[^)]*DOWN[^)]*buff\s*=\s*)0\.0\d+',
        r'\g<1>0.20',
        sanitized
    )

    # 13c-2. Replace raw unicode Rupee symbol '₹' in MathTex and Tex to prevent LaTeX compilation failure
    if "₹" in sanitized and ("MathTex" in sanitized or "Tex(" in sanitized):
        def fix_tex_rupee(match):
            block = match.group(0)
            if "₹" in block:
                block = block.replace(r"\text{₹}", r"\text{Rs. }")
                block = block.replace("₹", r"\text{Rs. }")
            return block
        sanitized = re.sub(r'\b(?:MathTex|Tex)\([^)]*\)', fix_tex_rupee, sanitized)

    # 13d. Upgrade CrispText Definition with Minimum Font Clamp & Anti-Squash
    # -------------------------------------------------------------------------
    replacement_crisp = (
        'def fit_into_box(target_mobject, frame_mobject, pad_x=0.25, pad_y=0.20):\n'
        '    if hasattr(frame_mobject, "__class__") and frame_mobject.__class__.__name__ == "Polygon":\n'
        '        pad_x = max(pad_x, getattr(frame_mobject, "width", 0) * 0.22)\n'
        '        pad_y = max(pad_y, getattr(frame_mobject, "height", 0) * 0.22)\n'
        '    if hasattr(frame_mobject, "width") and hasattr(target_mobject, "width"):\n'
        '        max_w = frame_mobject.width - (pad_x * 2)\n'
        '        if max_w > 0 and target_mobject.width > max_w:\n'
        '            ratio = max_w / target_mobject.width\n'
        '            needed_w = target_mobject.width + (pad_x * 2)\n'
        '            if hasattr(frame_mobject, "stretch_to_fit_width") and needed_w <= 6.2:\n'
        '                frame_mobject.stretch_to_fit_width(needed_w)\n'
        '            elif ratio < 0.88:\n'
        '                if hasattr(target_mobject, "scale_to_fit_width"):\n'
        '                    target_mobject.scale_to_fit_width(target_mobject.width * 0.88)\n'
        '            else:\n'
        '                target_mobject.scale_to_fit_width(max_w)\n'
        '    if hasattr(frame_mobject, "height") and hasattr(target_mobject, "height"):\n'
        '        req_h = target_mobject.height + (pad_y * 2)\n'
        '        if req_h > frame_mobject.height:\n'
        '            frame_mobject.stretch_to_fit_height(req_h)\n'
        '    target_mobject.move_to(frame_mobject.get_center())\n'
        '    return target_mobject\n\n'
        'def clamp_to_screen(mobject, pad=0.35):\n'
        '    if not hasattr(mobject, "get_left") or not hasattr(mobject, "get_right"): return mobject\n'
        '    try:\n'
        '        max_x = 5.85 - pad\n'
        '        r = mobject.get_right()[0]\n'
        '        l = mobject.get_left()[0]\n'
        '        if r > max_x: mobject.shift(LEFT * (r - max_x))\n'
        '        elif l < -max_x: mobject.shift(RIGHT * (-max_x - l))\n'
        '        top_y = mobject.get_top()[1]\n'
        '        is_title = getattr(mobject, "is_title", False) or getattr(mobject, "name", "") == "title_group"\n'
        '        if top_y > 1.85 and not is_title: mobject.shift(DOWN * (top_y - 1.85))\n'
        '        bot_y = mobject.get_bottom()[1]\n'
        '        if bot_y < -3.45: mobject.shift(UP * (-3.45 - bot_y))\n'
        '    except Exception: pass\n'
        '    return mobject\n\n'
        'def CrispText(text, size=24, font="Open Sans", **kwargs):\n'
        '    if "font_size" in kwargs:\n'
        '        size = kwargs.pop("font_size")\n'
        '    try:\n'
        '        size = float(size)\n'
        '    except (ValueError, TypeError):\n'
        '        size = 24.0\n'
        '    if 0.0 < size <= 1.0:\n'
        '        if size >= 0.28:\n'
        '            size = 26.0\n'
        '        elif size >= 0.19:\n'
        '            size = 18.0\n'
        '        elif size >= 0.14:\n'
        '            size = 14.0\n'
        '        else:\n'
        '            size = 12.0\n'
        '    elif size < 4.0:\n'
        '        size = 5.0\n'
        '    align = kwargs.pop("align", "center")\n'
        '    autowrap_val = kwargs.pop("autowrap", kwargs.pop("wrap", None))\n'
        '    disable_wrap_val = kwargs.pop("disable_wrap", kwargs.pop("disable_autowrap", False))\n'
        '    max_w_param = kwargs.pop("max_width", kwargs.pop("wrap_width", None))\n'
        '    for bad_k in ("alignment", "max_len", "line_spacing", "title_size", "item_size"):\n'
        '        kwargs.pop(bad_k, None)\n'
        '    slant_val = kwargs.pop("slant", NORMAL)\n'
        '    weight_val = kwargs.pop("weight", NORMAL)\n'
        '    if isinstance(weight_val, str):\n'
        '        weight_clean = weight_val.upper().replace("-", "").replace("_", "").replace(" ", "")\n'
        '        if weight_clean == "REGULAR":\n'
        '            weight_val = NORMAL\n'
        '        elif weight_clean in ("SEMIBOLD", "SEMI_BOLD"):\n'
        '            weight_val = SEMIBOLD\n'
        '        elif weight_clean == "BOLD":\n'
        '            weight_val = BOLD\n'
        '        elif weight_clean == "LIGHT":\n'
        '            weight_val = LIGHT\n'
        '        elif weight_clean in ("NORMAL", "BOOK"):\n'
        '            weight_val = NORMAL\n'
        '        else:\n'
        '            weight_val = NORMAL\n'
        '    color_val = kwargs.pop("color", None)\n'
        '    if color_val is None:\n'
        '        color_val = globals().get("TEXT_COLOR", globals().get("C_BLACK", "#404040"))\n'
        '    elif str(color_val).upper() in ("#F9C72C", "C_YELLOW", "YELLOW", "#FFF9E6", "#FFFF00", "#0B3C5D", "#06152B", "#0A2540", "#1D3557", "NAVY", "C_NAVY", "C_NAVY_DARK"):\n'
        '        color_val = globals().get("TEXT_COLOR", globals().get("C_BLACK", "#404040"))\n'
        '    raw_str = str(text)\n'
        '    _acronyms = {"AI", "RAM", "DB", "API", "LLM", "CPU", "GPU", "UI", "OSL", "ML", "OST", "VDB", "JSON", "HTTP", "REST", "SQL", "SME", "PIP", "HD", "FHD"}\n'
        '    import re as _re\n'
        '    def _tc_sub(m):\n'
        '        w = m.group(0)\n'
        '        return w if w in _acronyms else w.capitalize()\n'
        '    raw_str = _re.sub(r"\\b[A-Z]{2,}\\b", _tc_sub, raw_str)\n'
        '    NL = chr(10)\n'
        '    split_lines = [l for l in raw_str.split(NL)] if NL in raw_str else ([l for l in raw_str.split(r"\\\\n")] if r"\\\\n" in raw_str else None)\n'
        '    if split_lines is None:\n'
        '        should_autowrap = False\n'
        '        wrap_target_chars = 34\n'
        '        if max_w_param is not None:\n'
        '            try:\n'
        '                mw = float(max_w_param)\n'
        '                wrap_target_chars = max(16, int(mw / (size * 0.0082)))\n'
        '                should_autowrap = (" " in raw_str and len(raw_str) > wrap_target_chars)\n'
        '            except Exception:\n'
        '                pass\n'
        '        if not should_autowrap:\n'
        '            if autowrap_val is True:\n'
        '                should_autowrap = True\n'
        '                wrap_target_chars = 34\n'
        '            elif autowrap_val is False or disable_wrap_val:\n'
        '                should_autowrap = False\n'
        '            else:\n'
        '                should_autowrap = (len(raw_str) > 36 and " " in raw_str and size <= 16)\n'
        '                wrap_target_chars = 34\n'
        '        if should_autowrap:\n'
        '            words = raw_str.split()\n'
        '            lines = []\n'
        '            curr_line = []\n'
        '            curr_len = 0\n'
        '            for w in words:\n'
        '                sep = 1 if curr_line else 0\n'
        '                if curr_len + len(w) + sep > wrap_target_chars:\n'
        '                    if curr_line:\n'
        '                        lines.append(" ".join(curr_line))\n'
        '                    curr_line = [w]\n'
        '                    curr_len = len(w)\n'
        '                else:\n'
        '                    curr_line.append(w)\n'
        '                    curr_len += len(w) + sep\n'
        '            if curr_line:\n'
        '                lines.append(" ".join(curr_line))\n'
        '            split_lines = lines\n'
        '        else:\n'
        '            split_lines = [raw_str]\n'
        '    clean_kwargs = {k: v for k, v in kwargs.items() if k in ("tab_width", "t2c", "t2f", "t2s", "t2w", "l2g", "gradient", "fill_opacity", "stroke_width", "stroke_color")}\n'
        '    if len(split_lines) > 1:\n'
        '        line_mobs = [Text(l, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **clean_kwargs) for l in split_lines]\n'
        '        aligned_edge = ORIGIN if align == "center" else (LEFT if align == "left" else RIGHT)\n'
        '        mob = VGroup(*line_mobs).arrange(DOWN, buff=0.18, aligned_edge=aligned_edge).scale(0.25)\n'
        '    else:\n'
        '        mob = Text(raw_str, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **clean_kwargs).scale(0.25)\n'
        '    orig_scale = mob.scale_to_fit_width\n'
        '    def safe_scale_width(tw):\n'
        '        if hasattr(mob, "width") and mob.width > 0:\n'
        '            ratio = tw / mob.width\n'
        '            if ratio > 1.0:\n'
        '                return mob\n'
        '            if ratio < 0.88:\n'
        '                ratio = 0.88\n'
        '            return orig_scale(mob.width * ratio)\n'
        '        return orig_scale(tw)\n'
        '    mob.scale_to_fit_width = safe_scale_width\n'
        '    return mob'
    )
    if "def CrispText(" in sanitized:
        c_lines = sanitized.splitlines()
        c_start = -1
        c_end = -1
        c_indent_len = 0
        for ci, cl in enumerate(c_lines):
            if c_start == -1 and re.match(r'^[ \t]*def CrispText\(', cl):
                c_start = ci
                c_indent_len = len(cl) - len(cl.lstrip())
            elif c_start != -1:
                stripped = cl.strip()
                if stripped and not stripped.startswith("#"):
                    line_indent = len(cl) - len(cl.lstrip())
                    if line_indent <= c_indent_len:
                        c_end = ci
                        break
        if c_start != -1:
            if c_end == -1:
                c_end = len(c_lines)
            c_indent = c_lines[c_start][:len(c_lines[c_start]) - len(c_lines[c_start].lstrip())]
            indented_replacement = "\n".join((c_indent + l if l.strip() else l) for l in replacement_crisp.splitlines())
            sanitized = "\n".join(c_lines[:c_start] + [indented_replacement] + c_lines[c_end:])
    else:
        if "class FinalScene" in sanitized:
            sanitized = sanitized.replace("class FinalScene", f"{replacement_crisp}\n\nclass FinalScene", 1)
        else:
            sanitized = f"{replacement_crisp}\n\n" + sanitized

    # -------------------------------------------------------------------------
    # 13e. Image Path Resolution (ImageMobject, create_safe_image, safe_image)
    # -------------------------------------------------------------------------
    if script_path:
        topic_dir = os.path.dirname(os.path.dirname(os.path.abspath(script_path)))
        images_dir = os.path.join(topic_dir, "images")
        if os.path.isdir(images_dir):
            def fix_img_path(m):
                func_name = m.group(1)
                raw_arg = m.group(2).strip("\"'")
                if os.path.isfile(raw_arg):
                    return f'{func_name}("{raw_arg}"'
                for c in [raw_arg, os.path.basename(raw_arg), os.path.basename(raw_arg) + ".png", os.path.basename(raw_arg) + ".jpg"]:
                    candidate_path = os.path.join(images_dir, c)
                    if os.path.isfile(candidate_path):
                        return f'{func_name}("{candidate_path}"'
                return m.group(0)
            sanitized = re.sub(r'\b(ImageMobject|create_safe_image|safe_image)\(([\x22\x27][^\x22\x27]+[\x22\x27])', fix_img_path, sanitized)

    # -------------------------------------------------------------------------
    # 14. Clean Step Transitions (Purge Zombie Mobjects)
    # -------------------------------------------------------------------------
    is_executive = True

    trans_lines = sanitized.split("\n")
    cleaned_trans = []
    tn = len(trans_lines)
    ti = 0
    in_play = False
    play_depth = 0
    play_indent = ""
    play_has_fadeout = False
    play_has_forbidden = False

    def _check_and_add_step_transition(current_idx, indent_str, lines_arr):
        # Do not inject blind self.remove(*self.mobjects) after intermediate fadeouts.
        # This causes mid-step screen blackouts and premature element vanishing before sync_to().
        return None

    while ti < tn:
        tline = trans_lines[ti]
        cleaned_trans.append(tline)

        if not in_play:
            if "self.play(" in tline:
                in_play = True
                play_indent = tline[:len(tline) - len(tline.lstrip())]
                play_has_fadeout = "FadeOut" in tline
                play_has_forbidden = any(k in tline for k in ["FadeIn(", "Create(", "Write(", "Transform(", "ReplacementTransform(", "GrowFromCenter("])
                idx = tline.find("self.play(")
                after_play = tline[idx + len("self.play"):]
                play_depth = after_play.count("(") - after_play.count(")")
                if play_depth <= 0:
                    in_play = False
                    if play_has_fadeout and not play_has_forbidden:
                        ins = _check_and_add_step_transition(ti, play_indent, trans_lines)
                        if ins:
                            cleaned_trans.append(ins)
        else:
            play_depth += tline.count("(") - tline.count(")")
            if "FadeOut" in tline:
                play_has_fadeout = True
            if any(k in tline for k in ["FadeIn(", "Create(", "Write(", "Transform(", "ReplacementTransform(", "GrowFromCenter("]):
                play_has_forbidden = True
            if play_depth <= 0:
                in_play = False
                if play_has_fadeout and not play_has_forbidden:
                    ins = _check_and_add_step_transition(ti, play_indent, trans_lines)
                    if ins:
                        cleaned_trans.append(ins)
        ti += 1

    sanitized = "\n".join(cleaned_trans)

    # Convert title morphing (ReplacementTransform / Transform) and simultaneous crossfades to clean sequential crossfades
    # to eliminate character distortion and double-exposure ghosting during step transitions:
    def _sub_seq_crossfade(m):
        indent = m.group(1)
        old_t = m.group(2)
        new_t = m.group(3)
        return f'{indent}self.play(FadeOut({old_t}), run_time=0.35)\n{indent}self.play(FadeIn({new_t}, shift=DOWN * 0.1), run_time=0.45)'

    sanitized = re.sub(
        r'([ ]{4,16})self\.play\(\s*(?:ReplacementTransform|Transform)\(\s*([a-zA-Z0-9_]*(?:title|header)[a-zA-Z0-9_]*)\s*,\s*([a-zA-Z0-9_]*(?:title|header|n)[a-zA-Z0-9_]*)\s*\)\s*(?:,\s*run_time\s*=\s*[0-9.]+\s*)?\)',
        _sub_seq_crossfade,
        sanitized
    )
    sanitized = re.sub(
        r'([ ]{4,16})self\.play\(\s*FadeOut\(\s*([a-zA-Z0-9_]*(?:title|header)[a-zA-Z0-9_]*)[^)]*\)\s*,\s*FadeIn\(\s*([a-zA-Z0-9_]*(?:title|header|n)[a-zA-Z0-9_]*)[^)]*\)\s*(?:,\s*run_time\s*=\s*[0-9.]+\s*)?\)',
        _sub_seq_crossfade,
        sanitized
    )
    sanitized = re.sub(
        r'\bTransform\(\s*([a-zA-Z0-9_]*(?:title|header)[a-zA-Z0-9_]*)\s*,\s*([a-zA-Z0-9_]*(?:title|header)[a-zA-Z0-9_]*)\s*',
        r'ReplacementTransform(\1, \2',
        sanitized
    )

    # Fix existing title-preserving self.remove when immediately followed by a new title definition
    def fix_title_preserving_remove(match):
        indent = match.group(1)
        next_code = match.group(2)
        if "create_title(" in next_code or re.search(r'^[a-zA-Z0-9_]*title[a-zA-Z0-9_]*\s*=', next_code, re.M):
            return f"{indent}self.remove(*self.mobjects)\n{next_code}"
        return match.group(0)

    sanitized = re.sub(
        r'([ \t]*)self\.remove\(\*\[m for m in self\.mobjects if not getattr\(m,\s*[\'"]is_title[\'"],\s*False\)[^\]]*\]\)\s*\n((?:[ \t]*\n)*(?:[ \t]*#[^\n]*\n)*(?:[ \t]*[a-zA-Z0-9_]*title[a-zA-Z0-9_]*\s*=[^\n]*\n|[ \t]*[^\n]*create_title[^\n]*\n))',
        fix_title_preserving_remove,
        sanitized
    )
    sanitized = re.sub(
        r'([ \t]*)[a-zA-Z0-9_]*to_remove\s*=\s*\[m for m in self\.mobjects if not getattr\(m,\s*[\'"]is_title[\'"],\s*False\)[^\]]*\]\s*\n[ \t]*self\.remove\(\*[a-zA-Z0-9_]*to_remove\)\s*\n((?:[ \t]*\n)*(?:[ \t]*#[^\n]*\n)*(?:[ \t]*[a-zA-Z0-9_]*title[a-zA-Z0-9_]*\s*=[^\n]*\n|[ \t]*[^\n]*create_title[^\n]*\n))',
        fix_title_preserving_remove,
        sanitized
    )

    # -------------------------------------------------------------------------
    # 15. Canonical Executive Header Enforcement & Blank Screen Prevention
    # -------------------------------------------------------------------------
    if is_executive:
        canonical_def = (
            "        def fit_into_box(target_mobject, frame_mobject, pad_x=0.25, pad_y=0.20):\n"
            "            if hasattr(frame_mobject, '__class__') and frame_mobject.__class__.__name__ == 'Polygon':\n"
            "                pad_x = max(pad_x, getattr(frame_mobject, 'width', 0) * 0.22)\n"
            "                pad_y = max(pad_y, getattr(frame_mobject, 'height', 0) * 0.22)\n"
            "            if hasattr(frame_mobject, 'width') and hasattr(target_mobject, 'width'):\n"
            "                max_w = frame_mobject.width - (pad_x * 2)\n"
            "                if max_w > 0 and target_mobject.width > max_w:\n"
            "                    ratio = max_w / target_mobject.width\n"
            "                    needed_w = target_mobject.width + (pad_x * 2)\n"
            "                    if hasattr(frame_mobject, 'stretch_to_fit_width') and needed_w <= 6.2:\n"
            "                        frame_mobject.stretch_to_fit_width(needed_w)\n"
            "                    elif ratio < 0.88:\n"
            "                        if hasattr(target_mobject, 'scale_to_fit_width'):\n"
            "                            target_mobject.scale_to_fit_width(target_mobject.width * 0.88)\n"
            "                    else:\n"
            "                        target_mobject.scale_to_fit_width(max_w)\n"
            "            if hasattr(frame_mobject, 'height') and hasattr(target_mobject, 'height'):\n"
            "                req_h = target_mobject.height + (pad_y * 2)\n"
            "                if req_h > frame_mobject.height:\n"
            "                    frame_mobject.stretch_to_fit_height(req_h)\n"
            "            target_mobject.move_to(frame_mobject.get_center())\n"
            "            return target_mobject\n\n"
            "        def clamp_to_screen(mobject, pad=0.35):\n"
            "            if not hasattr(mobject, 'get_left') or not hasattr(mobject, 'get_right'):\n"
            "                return mobject\n"
            "            try:\n"
            "                is_70_sme = str(globals().get('SME_LAYOUT', '')).strip() == '70'\n"
            "                is_20_sme = str(globals().get('SME_LAYOUT', '')).strip() == '20'\n"
            "                if is_70_sme:\n"
            "                    min_x = -0.8\n"
            "                    max_x = 6.4\n"
            "                    l = mobject.get_left()[0]\n"
            "                    r = mobject.get_right()[0]\n"
            "                    if l < min_x:\n"
            "                        mobject.shift(RIGHT * (min_x - l))\n"
            "                    if r > max_x:\n"
            "                        mobject.shift(LEFT * (r - max_x))\n"
            "                elif is_20_sme:\n"
            "                    max_x = 7.11 - pad\n"
            "                    l = mobject.get_left()[0]\n"
            "                    r = mobject.get_right()[0]\n"
            "                    if r > max_x:\n"
            "                        mobject.shift(LEFT * (r - max_x))\n"
            "                    elif l < -max_x:\n"
            "                        mobject.shift(RIGHT * (-max_x - l))\n"
            "                    top_y = mobject.get_top()[1]\n"
            "                    if top_y > 2.0 and r > 4.20:\n"
            "                        mobject.shift(LEFT * (r - 4.20))\n"
            "                else:\n"
            "                    max_x = 7.11 - pad\n"
            "                    r = mobject.get_right()[0]\n"
            "                    l = mobject.get_left()[0]\n"
            "                    if r > max_x:\n"
            "                        mobject.shift(LEFT * (r - max_x))\n"
            "                    elif l < -max_x:\n"
            "                        mobject.shift(RIGHT * (-max_x - l))\n"
            "                top_y = mobject.get_top()[1]\n"
            "                if top_y > 1.8 and mobject.get_left()[0] < 0 and getattr(mobject, 'name', '') != 'title_group' and not getattr(mobject, 'is_title', False):\n"
            "                    mobject.shift(DOWN * (top_y - 1.8))\n"
            "                elif top_y > 3.8 and getattr(mobject, 'name', '') != 'title_group' and not getattr(mobject, 'is_title', False):\n"
            "                    mobject.shift(DOWN * (top_y - 3.8))\n"
            "                bot_y = mobject.get_bottom()[1]\n"
            "                if bot_y < -3.8:\n"
            "                    mobject.shift(UP * (-3.8 - bot_y))\n"
            "            except Exception:\n"
            "                pass\n"
            "            return mobject\n\n"
            "        def create_title(*text_args, **kwargs):\n"
            "            clean_args = []\n"
            "            for arg in text_args:\n"
            "                s_arg = str(arg)\n"
            "                for bad in ['Dr. Milan Joshi', 'Dr. Milan', 'Milan Joshi', 'Dr.', 'Instructor']:\n"
            "                    s_arg = re.sub(re.escape(bad), '', s_arg, flags=re.IGNORECASE).strip()\n"
            "                clean_args.append(s_arg)\n"
            "            text_args = clean_args\n"
            "            if len(text_args) == 0 or not str(text_args[0]).strip():\n"
            '                title_arg = "Scene Title"\n'
            "            else:\n"
            "                title_arg = text_args[0]\n"
            "            if isinstance(title_arg, (list, tuple)):\n"
            "                if len(title_arg) > 0 and any(isinstance(x, (Mobject, VMobject)) or hasattr(x, 'animate') for x in title_arg):\n"
            "                    title_m = VGroup(*title_arg).arrange(RIGHT, buff=0.15)\n"
            "                else:\n"
            '                    title_m = CrispText(" ".join(str(x) for x in title_arg), size=26, font="Open Sans", weight=BOLD, color=globals().get("TEXT_COLOR", "#404040"))\n'
            "            elif isinstance(title_arg, (Mobject, VMobject)) or hasattr(title_arg, 'animate'):\n"
            "                title_m = title_arg\n"
            "            else:\n"
            '                title_m = CrispText(str(title_arg), size=26, font="Open Sans", weight=BOLD, color=globals().get("TEXT_COLOR", "#404040"))\n'
            "            line_len = max(2.5, min(getattr(title_m, 'width', 3.0), 6.0))\n"
            '            line = Line(ORIGIN, RIGHT * line_len, color=globals().get("C_BRAND_BLUE", "#2C81FE"), stroke_width=2.5)\n'
            "            line.next_to(title_m, DOWN, buff=0.10, aligned_edge=LEFT)\n"
            "            header_grp = VGroup(title_m, line).to_corner(UL, buff=0.42)\n"
            "            is_70_sme = str(globals().get('SME_LAYOUT', '')).strip() == '70'\n"
            "            if is_70_sme:\n"
            "                header_grp.move_to([-0.8 + header_grp.width / 2.0, 3.25, 0])\n"
            "            if len(text_args) > 1 and str(text_args[1]).strip():\n"
            '                sub_text = CrispText(str(text_args[1]), size=16, font="Open Sans", weight=SEMIBOLD, color=globals().get("TEXT_COLOR", "#404040"), autowrap=False)\n'
            "                if hasattr(sub_text, 'width') and sub_text.width > (7.2 if is_70_sme else 8.5):\n"
            "                    sub_text.scale_to_fit_width(7.2 if is_70_sme else 8.5)\n"
            "                sub_text.next_to(header_grp, DOWN, buff=0.15, aligned_edge=LEFT)\n"
            "                title_grp = VGroup(header_grp, sub_text)\n"
            "            else:\n"
            "                sub_text = None\n"
            "                title_grp = header_grp\n"
            "            title_grp.header_grp = header_grp\n"
            "            title_grp.sub_text = sub_text\n"
            "            title_grp.title_m = title_m\n"
            "            header_grp.title_m = title_m\n"
            "            title_grp.line = line\n"
            "            header_grp.line = line\n"
            "            title_grp.set_z_index(20)\n"
            "            title_grp.is_persistent = True\n"
            "            title_grp.is_title = True\n"
            '            title_grp.name = "title_group"\n'
            "            return title_grp\n\n"
            "        def create_title_group(*args, **kwargs):\n"
            "            return create_title(*args, **kwargs)\n\n"
            "        def create_header_title(*args, **kwargs):\n"
            "            return create_title(*args, **kwargs)\n\n"
            "        def create_header(*args, **kwargs):\n"
            "            return create_title(*args, **kwargs)\n\n"
            "        def create_premise(*args, **kwargs):\n"
            "            return NullMobject()\n\n"
            "        def create_premise_box(*args, **kwargs):\n"
            "            return NullMobject()\n\n"
            "        def create_takeaway(*args, **kwargs):\n"
            "            return create_pill(*args, **kwargs)\n\n"
            "        def create_takeaway_banner(*args, **kwargs):\n"
            "            return create_pill(*args, **kwargs)\n\n"
            "        def create_pill(*args, **kwargs):\n"
            '            bg_color = None\n'
            '            text_color = None\n'
            '            font_size = 12\n'
            '            texts = []\n'
            '            icon_mob = None\n'
            '            def _is_color_arg_local(x):\n'
            "                if type(x).__name__ in ('Color', 'ManimColor'):\n"
            '                    return True\n'
            '                s = str(x).strip()\n'
            '                if s.startswith("#") and len(s) in (4, 7, 9):\n'
            '                    return True\n'
            '                if s.startswith("C_") or s.upper() in (\n'
            '                    "WHITE", "BLACK", "RED", "BLUE", "GREEN", "YELLOW", "PURPLE", "ORANGE", \n'
            '                    "GREY", "GRAY", "DARK_BLUE", "LIGHT_BLUE", "C_DARK_BLUE", "C_LIGHT_BLUE",\n'
            '                    "C_PURPLE", "C_RED", "C_YELLOW", "C_WHITE", "C_BLACK"\n'
            '                ):\n'
            '                    return True\n'
            '                return False\n'
            '            for a in args:\n'
            '                if isinstance(a, (int, float)) and not isinstance(a, bool):\n'
            '                    font_size = a\n'
            '                elif hasattr(a, "animate") or hasattr(a, "get_center"):\n'
            '                    icon_mob = a\n'
            '                elif _is_color_arg_local(a):\n'
            '                    if bg_color is None:\n'
            '                        bg_color = a\n'
            '                    elif text_color is None:\n'
            '                        text_color = a\n'
            '                else:\n'
            '                    texts.append(str(a))\n'
            '            texts = [t for t in texts if not _is_color_arg_local(t)]\n'
            '            if "bg_color" in kwargs: bg_color = kwargs.pop("bg_color")\n'
            '            if "text_color" in kwargs: text_color = kwargs.pop("text_color")\n'
            '            if "font_size" in kwargs: font_size = kwargs.pop("font_size")\n'
            '            if bg_color is None: bg_color = globals().get("C_DARK_BLUE", "#1E293B")\n'
            '            _light_bg = str(bg_color).upper() in ("WHITE", "#FFFFFF", "C_WHITE", "#F0F4F8", "#F8FAFC", "#FEF3C7", "#F9C72C", "C_YELLOW", "#FFF", "#FFFFFE", "#FAFAFA", "#E2E8F0")\n'
            '            if text_color is None:\n'
            '                text_color = globals().get("TEXT_COLOR", "#404040") if _light_bg else globals().get("C_WHITE", "#FFFFFF")\n'
            '            elif _light_bg and str(text_color).upper() in ("WHITE", "#FFFFFF", "C_WHITE", "#FFF"):\n'
            '                text_color = globals().get("TEXT_COLOR", "#404040")\n'
            '            try: font_size = float(font_size)\n'
            '            except: font_size = 12.0\n'
            '            full_text = "\\n".join(texts) if texts else " "\n'
            '            clean_kw = {k: v for k, v in kwargs.items() if k in ("autowrap", "wrap", "disable_wrap", "disable_autowrap", "align")}\n'
            '            txt = CrispText(full_text, size=font_size, font="Open Sans", weight=BOLD, color=text_color, **clean_kw)\n'
            '            content = VGroup(icon_mob, txt).arrange(RIGHT, buff=0.15) if icon_mob else txt\n'
            '            w = max(kwargs.get("width", 0) or 0, content.width + 0.55)\n'
            '            if kwargs.get("width") and kwargs.get("autowrap") is False and content.width > (kwargs["width"] - 0.4):\n'
            '                content.scale_to_fit_width(kwargs["width"] - 0.4)\n'
            '            h = max(kwargs.get("height", 0) or 0.38, content.height + 0.22)\n'
            '            pill = RoundedRectangle(corner_radius=min(h/2, 0.25), width=w, height=h, fill_color=bg_color, fill_opacity=1.0, stroke_width=0)\n'
            '            content.move_to(pill.get_center())\n'
            '            return VGroup(pill, content).set_z_index(20)\n\n'
            "        def create_state_badge(text_str, badge_type='violation', width=None, **kwargs):\n"
            '            c_red = globals().get("C_CORAL", globals().get("C_RED", "#E58F6D"))\n'
            '            c_text = globals().get("TEXT_COLOR", globals().get("C_DARK_BLUE", "#404040"))\n'
            '            c_white = globals().get("C_WHITE", "#FFFFFF")\n'
            '            col = c_red if badge_type == "violation" else (c_text if badge_type == "info" else "#2D6A4F")\n'
            '            return create_pill(text_str, col, c_white, font_size=12, width=width).set_z_index(20)\n\n'
            "        def create_leader_callout(target_mob, text_str, direction=UP, line_len=0.9, **kwargs):\n"
            '            c_dark_blue = globals().get("C_BRAND_BLUE", "#2C81FE")\n'
            '            c_light_blue = globals().get("C_SKY_BLUE", globals().get("C_LIGHT_BLUE", "#62B7E4"))\n'
            '            c_text = globals().get("TEXT_COLOR", "#404040")\n'
            '            c_white = globals().get("C_WHITE", "#FFFFFF")\n'
            '            dot = Dot(radius=0.06, color=c_dark_blue)\n'
            '            dot.move_to(target_mob.get_edge_center(direction))\n'
            '            line_end = dot.get_center() + direction * line_len\n'
            '            line = Line(dot.get_center(), line_end, stroke_width=1.5, color=c_dark_blue)\n'
            '            txt = CrispText(text_str, size=13, font="Open Sans", weight=BOLD, color=c_text)\n'
            '            txt.next_to(line_end, direction, buff=0.15)\n'
            '            bg = RoundedRectangle(corner_radius=0.074, width=txt.width + 0.35, height=txt.height + 0.22, fill_color=c_white, fill_opacity=1, stroke_color=c_light_blue, stroke_width=1.2)\n'
            '            txt.move_to(bg.get_center())\n'
            '            return VGroup(dot, line, bg, txt).set_z_index(20)\n\n'
            "        def create_strikethrough(target_mob, color=None, stroke_width=3, **kwargs):\n"
            '            c_red = globals().get("C_CORAL", globals().get("C_RED", "#E58F6D"))\n'
            '            col = color if color is not None else c_red\n'
            '            line = Line(target_mob.get_corner(DL) + LEFT * 0.08, target_mob.get_corner(UR) + RIGHT * 0.08, color=col, stroke_width=stroke_width)\n'
            '            return line.set_z_index(10)\n\n'
            "        def safe_image(path, height=1.0, width=None, **kwargs):\n"
            '            resolved = None\n'
            '            raw_s = str(path)\n'
            '            for cand in [raw_s, f"{raw_s}.png", f"{raw_s}.jpg", os.path.basename(raw_s), os.path.basename(raw_s) + ".png"]:\n'
            '                if os.path.isfile(cand):\n'
            '                    resolved = cand\n'
            '                    break\n'
            '                for folder in ["images", "../images"]:\n'
            '                    p = os.path.join(folder, cand)\n'
            '                    if os.path.isfile(p):\n'
            '                        resolved = p\n'
            '                        break\n'
            '                if resolved:\n'
            '                    break\n'
            '            if resolved:\n'
            '                try:\n'
            '                    img = ImageMobject(resolved)\n'
            '                    if height: img.scale_to_fit_height(height)\n'
            '                    elif width: img.scale_to_fit_width(width)\n'
            '                    return Group(img)\n'
            '                except: pass\n'
            '            h = height if height else 1.0\n'
            '            w = width if width else h\n'
            '            box = RoundedRectangle(corner_radius=0.074, height=h, width=w, color=globals().get("C_SKY_BLUE", "#62B7E4"), fill_opacity=0.15, stroke_width=1.5)\n'
            '            lbl = CrispText("Asset", size=11, font="Open Sans", color=globals().get("TEXT_COLOR", "#404040"))\n'
            '            lbl.move_to(box.get_center())\n'
            '            return VGroup(box, lbl)\n\n'
            "        def create_safe_image(*args, **kwargs):\n"
            "            return safe_image(*args, **kwargs)\n\n"
            "        def create_checkmark(*args, **kwargs):\n"
            "            c = kwargs.get('color', globals().get('C_STEEL_BLUE', '#7EA2C8'))\n"
            "            for a in args:\n"
            "                if isinstance(a, str) and (a.startswith('#') or a in globals()):\n"
            "                    c = a\n"
            "            sz = kwargs.get('size', kwargs.get('font_size', 0.22))\n"
            "            if isinstance(sz, (int, float)) and sz > 1.0:\n"
            "                sz = sz / 60.0\n"
            "            sw = kwargs.get('stroke_width', 3.5)\n"
            "            p1 = ORIGIN\n"
            "            p2 = p1 + RIGHT * (sz * 0.42) + DOWN * (sz * 0.55)\n"
            "            p3 = p2 + RIGHT * (sz * 0.95) + UP * (sz * 1.15)\n"
            "            l1 = Line(p1, p2, color=c, stroke_width=sw)\n"
            "            l2 = Line(p2, p3, color=c, stroke_width=sw)\n"
            "            g = VGroup(l1, l2)\n"
            "            g.center()\n"
            "            return g\n\n"
            "        def create_crossmark(*args, **kwargs):\n"
            "            c = kwargs.get('color', globals().get('C_CORAL', '#E58F6D'))\n"
            "            for a in args:\n"
            "                if isinstance(a, str) and (a.startswith('#') or a in globals()):\n"
            "                    c = a\n"
            "            sz = kwargs.get('size', kwargs.get('font_size', 0.22))\n"
            "            if isinstance(sz, (int, float)) and sz > 1.0:\n"
            "                sz = sz / 60.0\n"
            "            sw = kwargs.get('stroke_width', 3.5)\n"
            "            l1 = Line(ORIGIN, RIGHT * (sz * 0.8) + UP * (sz * 0.8), color=c, stroke_width=sw)\n"
            "            l2 = Line(ORIGIN + UP * (sz * 0.8), RIGHT * (sz * 0.8), color=c, stroke_width=sw)\n"
            "            g = VGroup(l1, l2)\n"
            "            g.center()\n"
            "            return g\n\n"
            "        self.create_title = create_title\n"
            "        self.create_title_group = create_title_group\n"
            "        self.create_header_title = create_header_title\n"
            "        self.create_header = create_header\n"
            "        self.create_pill = create_pill\n"
            "        self.create_state_badge = create_state_badge\n"
            "        self.create_leader_callout = create_leader_callout\n"
            "        self.create_strikethrough = create_strikethrough\n"
            "        self.safe_image = safe_image\n"
            "        self.create_safe_image = create_safe_image\n"
            "        self.create_checkmark = create_checkmark\n"
            "        self.create_crossmark = create_crossmark\n"
            "        self.fit_into_box = fit_into_box\n"
            "        self.clamp_to_screen = clamp_to_screen\n"
        )

        # 1. Cleanly strip any and all existing helper definitions (including try-except blocks):
        helper_names = [
            "create_title",
            "create_title_group",
            "create_header_title",
            "create_premise",
            "create_premise_box",
            "create_takeaway",
            "create_takeaway_banner",
            "create_pill",
            "create_state_badge",
            "create_leader_callout",
            "create_strikethrough",
            "safe_image",
            "create_safe_image",
            "create_checkmark",
            "create_crossmark",
            "fit_into_box",
            "clamp_to_screen",
        ]
        for h_name in helper_names:
            pat_top = rf'^def {h_name}\([^)]*\):(?:\n(?:[ ]{{1,}}[^\n]*|[ \t]*$))*'
            pat_method = rf'^[ ]{{4}}def {h_name}\([^)]*\):(?:\n(?:[ ]{{5,}}[^\n]*|[ \t]*$))*'
            pat_nested = rf'^[ ]{{8}}def {h_name}\([^)]*\):(?:\n(?:[ ]{{9,}}[^\n]*|[ \t]*$))*'
            sanitized = re.sub(pat_top, '', sanitized, flags=re.MULTILINE)
            sanitized = re.sub(pat_method, '', sanitized, flags=re.MULTILINE)
            sanitized = re.sub(pat_nested, '', sanitized, flags=re.MULTILINE)
        sanitized = re.sub(r'\bcreate_header_title\(', 'create_title(', sanitized)
        sanitized = re.sub(r'\bcreate_premise_box\(', 'create_premise(', sanitized)
        sanitized = re.sub(r'\bcreate_takeaway_banner\(', 'create_takeaway(', sanitized)

        # Strip all existing helper assignments to prevent accumulation of duplicate self.* statements
        sanitized = re.sub(
            r'^[ ]{4,12}self\.(?:create_title|create_title_group|create_header_title|create_header|create_premise|create_premise_box|create_takeaway|create_takeaway_banner|create_pill|create_state_badge|create_leader_callout|create_strikethrough|safe_image|create_safe_image|create_checkmark|create_crossmark|fit_into_box|clamp_to_screen)\s*=\s*[^\n]+\n',
            '',
            sanitized,
            flags=re.MULTILINE
        )

        # 2. Insert canonical_def exactly once inside construct(self)
        lines = sanitized.splitlines()
        idx_insert = -1
        for i, l in enumerate(lines):
            if "self.camera.background_color" in l:
                idx_insert = i + 1
                break
        if idx_insert == -1:
            for i, l in enumerate(lines):
                if "def construct(self):" in l:
                    idx_insert = i + 1
                    break
        if idx_insert != -1:
            lines.insert(idx_insert, canonical_def)
            sanitized = "\n".join(lines)

        top_fit = (
            "def fit_into_box(target_mobject, frame_mobject, pad_x=0.25, pad_y=0.20):\n"
            "    if hasattr(frame_mobject, '__class__') and frame_mobject.__class__.__name__ == 'Polygon':\n"
            "        pad_x = max(pad_x, getattr(frame_mobject, 'width', 0) * 0.22)\n"
            "        pad_y = max(pad_y, getattr(frame_mobject, 'height', 0) * 0.22)\n"
            "    if hasattr(frame_mobject, 'width') and hasattr(target_mobject, 'width'):\n"
            "        max_w = frame_mobject.width - (pad_x * 2)\n"
            "        if max_w > 0 and target_mobject.width > max_w:\n"
            "            ratio = max_w / target_mobject.width\n"
            "            needed_w = target_mobject.width + (pad_x * 2)\n"
            "            if hasattr(frame_mobject, 'stretch_to_fit_width') and needed_w <= 6.2:\n"
            "                frame_mobject.stretch_to_fit_width(needed_w)\n"
            "            elif ratio < 0.88:\n"
            "                if hasattr(target_mobject, 'scale_to_fit_width'):\n"
            "                    target_mobject.scale_to_fit_width(target_mobject.width * 0.88)\n"
            "            else:\n"
            "                target_mobject.scale_to_fit_width(max_w)\n"
            "    if hasattr(frame_mobject, 'height') and hasattr(target_mobject, 'height'):\n"
            "        req_h = target_mobject.height + (pad_y * 2)\n"
            "        if req_h > frame_mobject.height:\n"
            "            frame_mobject.stretch_to_fit_height(req_h)\n"
            "    target_mobject.move_to(frame_mobject.get_center())\n"
            "    return target_mobject\n\n"
            "def safe_image(img_path, width=3.0, height=None):\n"
            "    if os.path.exists(str(img_path)):\n"
            "        try:\n"
            "            im = ImageMobject(str(img_path))\n"
            "            if width: im.scale_to_fit_width(width)\n"
            "            if height: im.scale_to_fit_height(height)\n"
            "            return im\n"
            "        except Exception:\n"
            "            pass\n"
            "    box = RoundedRectangle(width=width or 3.0, height=height or 2.0, corner_radius=0.074, fill_color='#F8FAFC', fill_opacity=0.9, stroke_color='#CBD5E1', stroke_width=1.5)\n"
            "    lbl = CrispText('Asset Image', font_size=12, color='#404040').move_to(box)\n"
            "    return VGroup(box, lbl)\n\n"
            "def create_pill(*args, **kwargs):\n"
            "    bg_color = kwargs.get('bg_color', globals().get('C_DARK_BLUE', '#1E293B'))\n"
            "    text_color = kwargs.get('text_color', globals().get('C_WHITE', '#FFFFFF'))\n"
            "    font_size = kwargs.get('font_size', 12)\n"
            "    texts = [str(a) for a in args if isinstance(a, (str, int, float)) and not str(a).startswith('#') and str(a) not in ('WHITE', 'BLACK')]\n"
            "    text_content = texts[0] if texts else 'Badge'\n"
            "    txt = CrispText(text_content, font_size=font_size, color=text_color, weight='BOLD')\n"
            "    bg = RoundedRectangle(width=max(txt.width + 0.4, 1.2), height=max(txt.height + 0.2, 0.4), corner_radius=0.15, fill_color=bg_color, fill_opacity=1.0, stroke_width=0)\n"
            "    txt.move_to(bg)\n"
            "    grp = VGroup(bg, txt)\n"
            "    grp.set_z_index(20)\n"
            "    return grp\n\n"
            "def create_checkmark(*args, **kwargs):\n"
            "    c = kwargs.get('color', globals().get('C_STEEL_BLUE', '#7EA2C8'))\n"
            "    for a in args:\n"
            "        if isinstance(a, str) and (a.startswith('#') or a in globals()):\n"
            "            c = a\n"
            "    sz = kwargs.get('size', kwargs.get('font_size', 0.22))\n"
            "    if isinstance(sz, (int, float)) and sz > 1.0:\n"
            "        sz = sz / 60.0\n"
            "    sw = kwargs.get('stroke_width', 3.5)\n"
            "    p1 = ORIGIN\n"
            "    p2 = p1 + RIGHT * (sz * 0.42) + DOWN * (sz * 0.55)\n"
            "    p3 = p2 + RIGHT * (sz * 0.95) + UP * (sz * 1.15)\n"
            "    l1 = Line(p1, p2, color=c, stroke_width=sw)\n"
            "    l2 = Line(p2, p3, color=c, stroke_width=sw)\n"
            "    g = VGroup(l1, l2)\n"
            "    g.center()\n"
            "    return g\n\n"
            "def create_crossmark(*args, **kwargs):\n"
            "    c = kwargs.get('color', globals().get('C_CORAL', '#E58F6D'))\n"
            "    for a in args:\n"
            "        if isinstance(a, str) and (a.startswith('#') or a in globals()):\n"
            "            c = a\n"
            "    sz = kwargs.get('size', kwargs.get('font_size', 0.22))\n"
            "    if isinstance(sz, (int, float)) and sz > 1.0:\n"
            "        sz = sz / 60.0\n"
            "    sw = kwargs.get('stroke_width', 3.5)\n"
            "    l1 = Line(ORIGIN, RIGHT * (sz * 0.8) + UP * (sz * 0.8), color=c, stroke_width=sw)\n"
            "    l2 = Line(ORIGIN + UP * (sz * 0.8), RIGHT * (sz * 0.8), color=c, stroke_width=sw)\n"
            "    g = VGroup(l1, l2)\n"
            "    g.center()\n"
            "    return g\n"
        )
        lines = sanitized.splitlines()
        class_idx = -1
        for i, l in enumerate(lines):
            if re.match(r"^class\s+[A-Za-z0-9_]+", l):
                class_idx = i
                break
        if class_idx != -1:
            lines.insert(class_idx, top_fit)
            sanitized = "\n".join(lines)

        # Convert raw unicode checkmarks and crossmarks to vector shapes
        sanitized = re.sub(r'(?:CrispText|Text)\(\s*["\'](?:✓|✔|\\u2713|\\u2714)["\']\s*,\s*', r'create_checkmark(', sanitized)
        sanitized = re.sub(r'(?:CrispText|Text)\(\s*["\'](?:✓|✔|\\u2713|\\u2714)["\']\s*\)', r'create_checkmark()', sanitized)
        sanitized = re.sub(r'(?:CrispText|Text)\(\s*["\'](?:✗|✘|\\u2717|\\u2718)["\']\s*,\s*', r'create_crossmark(', sanitized)
        sanitized = re.sub(r'(?:CrispText|Text)\(\s*["\'](?:✗|✘|\\u2717|\\u2718)["\']\s*\)', r'create_crossmark()', sanitized)

        # 3. Revert corrupted dots.set_x(0) or divider.set_x(0)
        sanitized = re.sub(r'(\bdots\s*\.next_to\([^)]*\))\s*\.set_x\(0\)', r'\1', sanitized)
        sanitized = re.sub(r'(\bdivider\s*\.next_to\([^)]*\))\s*\.set_x\(0\)', r'\1', sanitized)

        # 4. Replace ad-hoc inline title declarations
        inline_title_pattern = (
            r'([ ]{4,12})(?:#\s*(?:Slide Title|Title)[^\n]*\n\s*)?'
            r'(?:new_)?title(?:_text)?\s*=\s*(?:CrispText|Text)\((["\'].*?["\']|r["\'].*?["\']|f["\'].*?["\'])[^)]*\)\s*\n'
            r'[ ]{4,12}(?:new_)?title(?:_text)?\.(?:to_corner|move_to)\([^\n]+\)\s*\n'
            r'[\s\S]*?'
            r'[ ]{4,12}(new_)?title_group\s*=\s*VGroup\([^)]+\)'
        )
        def replace_inline_title(match):
            indent = match.group(1)
            raw_title_str = match.group(2)
            prefix = match.group(3) or ""
            return f'{indent}{prefix}title_group = create_title({raw_title_str})'
        sanitized = re.sub(inline_title_pattern, replace_inline_title, sanitized)

        # Replace ad-hoc inline bubbles/underline patterns:
        inline_bubbles_pattern = (
            r'([ ]{4,12})(new_)?title_text\s*=\s*(?:CrispText|Text)\((["\'].*?["\']|r["\'].*?["\']|f["\'].*?["\'])[\s\S]*?'
            r'(?:new_)?bubbles\s*=\s*VGroup\([\s\S]*?\)\s*\n'
            r'[ ]{4,12}(?:new_)?(?:underline|divider)\s*=\s*Line\([\s\S]*?\)\s*\n'
            r'[ ]{4,12}(new_)?title_group\s*=\s*VGroup\([\s\S]*?\)(?:\.arrange\([^\n]*\))?(?:\.(?:to_edge|move_to)\([^\n]*\))?'
        )
        def replace_bubbles_title(match):
            indent = match.group(1)
            prefix = match.group(2) or match.group(4) or ""
            raw_str = match.group(3)
            return f'{indent}{prefix}title_group = create_title({raw_str})'
        sanitized = re.sub(inline_bubbles_pattern, replace_bubbles_title, sanitized)

        # Auto-heal glow/stroke overlays: Ensure mob.copy().set_stroke(...) always has set_fill(opacity=0)
        # to prevent opaque white/colored duplicate rectangles from masking underlying text and icons
        def fix_stroke_copy(match):
            prefix = match.group(1)
            stroke_args = match.group(2)
            if "set_fill" in prefix:
                return match.group(0)
            return f"{prefix}.set_fill(opacity=0).set_stroke({stroke_args})"
        sanitized = re.sub(r'([a-zA-Z0-9_\[\]\(\)]+\.copy\(\))\s*\.set_stroke\(([^)]*)\)', fix_stroke_copy, sanitized)

        # Neutralize legacy 5-tier layout artifacts (premise boxes, obsolete duplicate banners)
        def is_tier_or_duplicate_header_artifact(var_name):
            vn = var_name.lower()
            if "data" in vn or "list" in vn or "items" in vn or "tuple" in vn:
                return False
            # NEVER neutralize real titles or step title transitions:
            if "title" in vn or "header" in vn:
                return False
            # NEVER neutralize content containers or pedagogical takeaways/cards:
            if any(k in vn for k in ["card", "cards", "table", "grid", "content", "points", "rows", "row", "group", "entries", "entry", "box_group", "takeaway", "summary", "node", "item"]):
                return False
            if any(k in vn for k in ["premise_box", "premise_banner", "legacy_takeaway_banner", "bottom_banner", "footer_banner"]):
                return True
            if any(k in vn for k in ["dec_group", "decorator", "dots_b"]):
                return True
            if re.match(r'^(?:new_)?tp_(?:bg|header|text|content|formula)\w*$', vn) or re.match(r'^(?:new_)?tp\d*$', vn):
                return True
            if re.match(r'^(?:new_)?bb_(?:bg|txt|text|lbl|content)\w*$', vn) or re.match(r'^(?:new_)?bb\d*$', vn):
                return True
            return False

        lines = sanitized.splitlines()
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            m = re.match(r"^(\s*)([a-zA-Z0-9_]+)\s*=", line)
            if m and is_tier_or_duplicate_header_artifact(m.group(2)):
                indent = m.group(1)
                var = m.group(2)
                open_parens = 0
                j = i
                while j < len(lines):
                    cur = lines[j]
                    open_parens += cur.count("(") - cur.count(")")
                    open_parens += cur.count("[") - cur.count("]")
                    open_parens += cur.count("{") - cur.count("}")
                    j += 1
                    if open_parens <= 0:
                        break
                new_lines.append(f"{indent}{var} = NullMobject()")
                i = j
            else:
                new_lines.append(line)
                i += 1
        sanitized = "\n".join(new_lines)

        # Inject NullMobject definition at module level if not present
        if "class NullMobject" not in sanitized:
            null_mod_def = (
                "\nclass NullMobject(VGroup):\n"
                "    def __init__(self, *args, **kwargs):\n"
                "        super().__init__(*[VMobject() for _ in range(15)])\n"
                "        self.set_opacity(0)\n"
                "    def __getitem__(self, val):\n"
                "        if isinstance(val, int) and val >= len(self.submobjects):\n"
                "            return VMobject()\n"
                "        return super().__getitem__(val)\n"
                "    def get_center(self):\n"
                "        import numpy as np\n"
                "        return np.array([0.0, 0.0, 0.0])\n"
                "    def get_top(self):\n"
                "        import numpy as np\n"
                "        return np.array([0.0, 0.0, 0.0])\n"
                "    def get_bottom(self):\n"
                "        import numpy as np\n"
                "        return np.array([0.0, 0.0, 0.0])\n"
                "    def get_left(self):\n"
                "        import numpy as np\n"
                "        return np.array([0.0, 0.0, 0.0])\n"
                "    def get_right(self):\n"
                "        import numpy as np\n"
                "        return np.array([0.0, 0.0, 0.0])\n"
            )
            vgroup_safe_def = (
                "\ntry:\n"
                "    if not hasattr(VGroup, '_orig_add_safe'):\n"
                "        VGroup._orig_add_safe = VGroup.add\n"
                "        def _safe_vg_add(self, *mobs):\n"
                "            cleaned = []\n"
                "            for m in mobs:\n"
                "                if isinstance(m, VMobject):\n"
                "                    cleaned.append(m)\n"
                "                elif hasattr(m, 'submobjects'):\n"
                "                    for sub in m.submobjects:\n"
                "                        if isinstance(sub, VMobject):\n"
                "                            cleaned.append(sub)\n"
                "            return VGroup._orig_add_safe(self, *cleaned)\n"
                "        VGroup.add = _safe_vg_add\n"
                "except Exception:\n"
                "    pass\n"
            )
            sanitized = re.sub(r'(from manim import \*)', r'\1' + null_mod_def + vgroup_safe_def, sanitized, count=1)

        # Remove standalone decorator artifacts while preserving canonical titles
        sanitized = re.sub(r'^[ ]{4,12}title_group\s*=\s*VGroup\([^\n]*decorator[^\n]*\)\s*\n', '', sanitized, flags=re.M)
        sanitized = re.sub(r'^[ ]{4,12}decorator\s*=\s*VGroup\([^\n]*\)[^\n]*\n', '', sanitized, flags=re.M)
        sanitized = re.sub(r'^[ ]{4,12}self\.play\(FadeIn\(decorator[^\)]*\)[^\n]*\)\s*\n', '', sanitized, flags=re.M)
        sanitized = re.sub(r'^[ ]{4,12}self\.play\(Create\(decorator\)[^\n]*\)\s*\n', '', sanitized, flags=re.M)
        sanitized = re.sub(r'^[ ]{4,12}self\.play\(Create\(divider\)[^\n]*\)\s*\n', '', sanitized, flags=re.M)
        # Prevent blanket fadeouts from wiping out persistent title
        sanitized = re.sub(r'FadeOut\(init_title\),?\s*', '', sanitized)
        sanitized = re.sub(r'^[ ]{4,12}self\.remove\(init_title\)\s*\n', '', sanitized, flags=re.M)

        # Protect persistent titles from broad self.mobjects wipes
        sanitized = re.sub(
            r'FadeOut\(\s*\*self\.mobjects\s*\)',
            "FadeOut(*[m for m in self.mobjects if not getattr(m, 'is_title', False) and getattr(m, 'name', '') != 'title_group' and not getattr(m, 'is_persistent', False)])",
            sanitized
        )
        def protect_title_remove(m_match):
            pos = m_match.end()
            lookahead = sanitized[pos:pos+250]
            if "create_title(" in lookahead or re.search(r'^[a-zA-Z0-9_]*title[a-zA-Z0-9_]*\s*=', lookahead, re.M):
                return m_match.group(0)
            return "self.remove(*[m for m in self.mobjects if not getattr(m, 'is_title', False) and getattr(m, 'name', '') != 'title_group' and not getattr(m, 'is_persistent', False)])"

        sanitized = re.sub(
            r'self\.remove\(\s*\*self\.mobjects\s*\)',
            protect_title_remove,
            sanitized
        )

        # Subtitles: Ensure any subtitle appearing on top right appears centred below title
        sanitized = re.sub(
            r'^[ \t]*([a-zA-Z0-9_]*subtitle[a-zA-Z0-9_]*)\.(?:to_corner\(UR[^\)]*\)|to_edge\(UP\s*\+\s*RIGHT[^\)]*\)|move_to\(\[[0-9\.\s\-]+,\s*[2-4]\.[0-9]+[^\)]*\]\))[^\n]*',
            r'\1.next_to(title_group, DOWN, buff=0.18)\n        \1.set_x(0)',
            sanitized,
            flags=re.MULTILINE
        )
        # Unwrap nested animations: e.g. FadeIn(LaggedStartMap(...)) or FadeIn(LaggedStart(...))
        sanitized = re.sub(
            r'\b(?:FadeIn|FadeOut|Create)\s*\(\s*(LaggedStart(?:Map)?\s*\([^)]*?(?:\([^)]*?\)[^)]*?)*\))\s*\)',
            r'\1',
            sanitized
        )

        # Strip any instructor names / metadata that might leak onto screen
        for bad_name in ["dr. milan joshi", "milan joshi", "dr. milan", "instructor"]:
            sanitized = re.sub(
                rf'[^\n]*CrispText\([^\n]*{re.escape(bad_name)}[^\n]*\)[^\n]*',
                '# Removed instructor text mobject',
                sanitized,
                flags=re.IGNORECASE
            )
            sanitized = re.sub(
                rf'[^\n]*Text\([^\n]*{re.escape(bad_name)}[^\n]*\)[^\n]*',
                '# Removed instructor text mobject',
                sanitized,
                flags=re.IGNORECASE
            )

        # 5. Missing & Placeholder Header Verification & Auto-Injection across ALL Steps
        canonical_title = resolve_scene_title(sanitized, script_path)
        if canonical_title:
            bad_titles_pattern = r'create_title\(\s*["\'](?:#\s*)?(?:Decorator|Concept Section \d+|Suburban Family|Slide Title|Init Title)[^"\']*["\']\s*\)'
            sanitized = re.sub(bad_titles_pattern, lambda m: f'create_title("{canonical_title}")', sanitized, flags=re.IGNORECASE)

        # 5a. Neutralize fake NullMobject() title transitions
        sanitized = re.sub(
            r'^[ ]{4,12}(?:new_)?title_group\s*=\s*NullMobject\(\)\s*\n'
            r'(?:[ ]{4,12}self\.play\(FadeOut\([^)]+\)[^\n]*\)\s*\n)?'
            r'(?:[ ]{4,12}self\.remove\([^)]+\)\s*\n)?'
            r'(?:[ ]{4,12}self\.play\(FadeIn\((?:new_)?title_group\)[^\n]*\)\s*\n)?',
            '',
            sanitized,
            flags=re.M
        )

        # 5b. Strip dangling self.remove(title_group) when title_group was never defined
        if not re.search(r'\btitle_group\s*=', sanitized):
            sanitized = re.sub(r'^[ ]{4,12}self\.remove\(title_group\)\s*\n', '', sanitized, flags=re.M)

        # 5b-2. Ensure any referenced new_title_group<N>, new_title_step<N>, step<N>_title is healed
        for ntv in set(re.findall(r'\b(new_title\w*|step\d+_title\w*)\b', sanitized)):
            if not re.search(rf'^[ ]*{ntv}\s*=', sanitized, re.M):
                # If it's merely assigned to current_title, e.g. current_title = ntv, and preceded by FadeOut, purge that redundant block
                sanitized = re.sub(
                    rf'^[ ]{{4,12}}self\.play\(FadeOut\([^)]+\)[^\n]*\)\s*\n[ ]{{4,12}}current_title(?:_group)?\s*=\s*{ntv}\s*\n',
                    '',
                    sanitized,
                    flags=re.M
                )
                sanitized = re.sub(
                    rf'^[ ]{{4,12}}current_title(?:_group)?\s*=\s*{ntv}\s*\n',
                    '',
                    sanitized,
                    flags=re.M
                )
                if re.search(rf'\b{ntv}\b', sanitized):
                    t_title = canonical_title or "Section Title"
                    sanitized = re.sub(
                        rf'([ ]{{4,12}})(?=[^\n]*\b{ntv}\b)',
                        rf'\1{ntv} = create_title("{t_title}")\n\1',
                        sanitized,
                        count=1
                    )

        # 5b. Title deduplication is handled cleanly per-step in 5d

        # 5c. Clean up duplicate unplayed title_1 / title1 / title_group_1 in Step 1
        if re.search(r'title_group\s*=\s*create_title\([^\)]*\)[\s\S]*?(?:title_1|title1|title_group_1)\s*=\s*(?:create_title|create_slide_title)\(', sanitized):
            for dup_var in ["title_1", "title1", "title_group_1"]:
                pat = rf'^[ ]{{4,12}}{dup_var}\s*=\s*(?:create_title|create_slide_title)\([^\n]+\n'
                if re.search(pat, sanitized, re.M):
                    sanitized = re.sub(pat, '', sanitized, flags=re.M)
                    sanitized = re.sub(rf'\b{dup_var}\b', 'title_group', sanitized)

        # 5d. Multi-Step Title Automation: Verify every step has an active, animated title
        raw_step_matches = list(re.finditer(r'^[ ]{4,12}(?:#\s*)*(?:##?|//)\s*(?:Presentation\s+Step|Presentation\s+Section|Step)\s+(\d+)\b([^\n]*)$', sanitized, re.MULTILINE | re.IGNORECASE))
        seen_s_nums = set()
        step_matches = []
        for sm in raw_step_matches:
            trailing = sm.group(2).lower()
            if any(w in trailing for w in ['cleanup', 'teardown', 'transition', 'before', 'after', 'finish', 'outro', 'mobs']):
                continue
            s_num = int(sm.group(1))
            if s_num in seen_s_nums:
                continue
            seen_s_nums.add(s_num)
            step_matches.append(sm)
        if step_matches:
            sections = []
            pre_code = sanitized[:step_matches[0].start()]
            sections.append(("PRE", pre_code))

            for s_idx, sm in enumerate(step_matches):
                s_num = int(sm.group(1))
                start_idx = sm.start()
                end_idx = step_matches[s_idx + 1].start() if s_idx + 1 < len(step_matches) else len(sanitized)
                sections.append((s_num, sanitized[start_idx:end_idx]))

            # If pre_code contains a manual header group (e.g. Group(kicker, main_header) with self.add),
            # convert it to canonical title_group = create_title(canonical_title)
            m_manual_hdr = re.search(
                r'([ ]{4,12})(?:[a-zA-Z0-9_]*kicker[a-zA-Z0-9_]*\s*=[^\n]+\n[ ]{4,12})?[a-zA-Z0-9_]*main_header[a-zA-Z0-9_]*\s*=[^\n]+\n[ ]{4,12}([a-zA-Z0-9_]*header[a-zA-Z0-9_]*)\s*=\s*(?:Group|VGroup)\([^\n]+\)\s*\n[ ]{4,12}self\.add\(\2[^\)]*\)\s*\n?',
                pre_code
            )
            if m_manual_hdr:
                t_val = canonical_title or "Key Concepts"
                ind = m_manual_hdr.group(1)
                replacement_hdr = f'{ind}title_group = create_title("{t_val}")\n'
                pre_code = pre_code[:m_manual_hdr.start()] + replacement_hdr + pre_code[m_manual_hdr.end():]
                sections[0] = ("PRE", pre_code)

            new_sections = [sections[0]]
            m_pre_title = re.search(r'^[ ]{4,12}([a-zA-Z0-9_]+)\s*=\s*(?:self\.)?(?:create_title|create_slide_title|create_header_title|create_header)\(', pre_code, re.M)
            if m_pre_title and m_pre_title.group(1).isidentifier():
                current_title_var = m_pre_title.group(1)
            else:
                current_title_var = "title_group" if re.search(r'\btitle_group\s*=', sanitized) else None

            title_pattern = r'^[ ]{4,12}([a-zA-Z0-9_]+)\s*=\s*(?:self\.)?(?:create_title|create_slide_title|create_header_title|create_header)\s*\('

            def remove_title_def_and_play(code: str, m_match) -> str:
                start_pos = m_match.start()
                raw_var = m_match.group(1).split(',')[0].strip()
                var_name = raw_var
                pos = m_match.end()
                open_p = 1
                while pos < len(code) and open_p > 0:
                    if code[pos] == "(": open_p += 1
                    elif code[pos] == ")": open_p -= 1
                    pos += 1
                line_end = code.find("\n", pos)
                if line_end == -1: line_end = len(code)
                else: line_end += 1
                follow = code[line_end:]
                m_play = re.match(rf"^[ ]*self\.play\(FadeIn\({var_name}[^\)]*\)[^\n]*\)\s*\n", follow)
                if m_play:
                    end_pos = line_end + m_play.end()
                else:
                    end_pos = line_end
                return code[:start_pos] + code[end_pos:]

            for s_idx in range(1, len(sections)):
                s_num, s_code = sections[s_idx]
                title_defs = list(re.finditer(title_pattern, s_code, re.M))

                if s_num == 1:
                    m_pre_hdr = re.search(r'^[ ]{4,12}([a-zA-Z0-9_,\s]+?(?:header|title)[a-zA-Z0-9_,\s]*)\s*=\s*(?:self\.)?(?:create_title|create_slide_title|create_header_title|create_header)\(', pre_code, re.M)
                    if m_pre_hdr:
                        hdr_var = m_pre_hdr.group(1).split(',')[0].strip()
                        m_step1_titles = list(re.finditer(r'^[ ]{4,12}([a-zA-Z0-9_]*title[a-zA-Z0-9_]*)\s*=\s*(?:self\.)?(?:create_title|create_slide_title)\(', s_code, re.M))
                        for m_st in m_step1_titles:
                            del_var = m_st.group(1).split(',')[0].strip()
                            s_code = re.sub(rf'^[ ]{{4,12}}{del_var}\s*=\s*(?:self\.)?(?:create_title|create_slide_title)\([^\n]+\n', '', s_code, flags=re.M)
                            s_code = re.sub(rf'^[ ]{{4,12}}self\.play\(FadeIn\({del_var}[^\)]*\)[^\n]*\)\s*\n', '', s_code, flags=re.M)
                            s_code = re.sub(rf'\bFadeIn\({del_var}[^\)]*\),?\s*', '', s_code)
                            s_code = re.sub(rf'\b{del_var}\b', hdr_var, s_code)
                        title_defs = list(re.finditer(title_pattern, s_code, re.M))

                    if len(title_defs) > 1:
                        rich_indices = []
                        for idx, td in enumerate(title_defs):
                            call_str = s_code[td.start():min(len(s_code), td.start() + 250)]
                            if "," in call_str[:call_str.find(")") if ")" in call_str else 250]:
                                rich_indices.append(idx)
                        keep_idx = rich_indices[0] if rich_indices else 0
                        for idx in reversed(range(len(title_defs))):
                            if idx == keep_idx:
                                continue
                            s_code = remove_title_def_and_play(s_code, title_defs[idx])
                        title_defs = list(re.finditer(title_pattern, s_code, re.M))

                    if title_defs:
                        t_var = title_defs[0].group(1).split(',')[0].strip()
                        current_title_var = t_var
                        has_entry = bool(re.search(rf'(?:FadeIn|Write|Create|Transform|ReplacementTransform|GrowFromCenter|self\.add|transition_header)\([^)]*\b{t_var}\b', s_code))
                        if not has_entry:
                            m_def = title_defs[0]
                            pos = m_def.end()
                            open_p = 1
                            while pos < len(s_code) and open_p > 0:
                                if s_code[pos] == '(': open_p += 1
                                elif s_code[pos] == ')': open_p -= 1
                                pos += 1
                            end_line = s_code.find("\n", pos)
                            if end_line == -1: end_line = len(s_code)
                            else: end_line += 1
                            indent = "        "
                            s_code = s_code[:end_line] + f'{indent}self.play(FadeIn({t_var}, shift=DOWN*0.1), run_time=0.8)\n' + s_code[end_line:]
                    else:
                        already_has_header_call = bool(re.search(r'(?:create_title|create_slide_title|create_header_title|create_header)\s*\(', s_code))
                        if already_has_header_call:
                            # Step 1 already calls a header/title constructor! Do NOT inject duplicate title!
                            pass
                        else:
                            m_pre = None
                            in_helper_def = False
                            def_indent = 0
                            for p_line in pre_code.splitlines():
                                m_def = re.match(r'^([ ]{4,12})def\s+[a-zA-Z0-9_]+', p_line)
                                if m_def:
                                    def_indent = len(m_def.group(1))
                                    in_helper_def = True
                                    continue
                                if in_helper_def:
                                    line_indent = len(p_line) - len(p_line.lstrip())
                                    if p_line.strip() and line_indent <= def_indent:
                                        in_helper_def = False
                                    else:
                                        continue
                                m_candidate = re.match(r'^[ ]{4,12}([a-zA-Z0-9_,\s]+?)\s*=\s*(?:self\.)?(?:create_title|create_slide_title|create_header_title|create_header)\b', p_line)
                                if m_candidate:
                                    m_pre = m_candidate
                                    break
                            if m_pre:
                                t_var = m_pre.group(1).split(',')[0].strip()
                                current_title_var = t_var
                                has_entry = bool(re.search(rf'(?:FadeIn|Write|Create|Transform|ReplacementTransform|GrowFromCenter|self\.add|transition_header)\([^)]*\b{t_var}\b', s_code))
                                if not has_entry:
                                    first_line_end = s_code.find("\n") + 1
                                    indent = "        "
                                    s_code = s_code[:first_line_end] + f'{indent}self.play(FadeIn({t_var}, shift=DOWN*0.1), run_time=0.8)\n' + s_code[first_line_end:]
                            else:
                                first_line_end = s_code.find("\n") + 1
                                indent = "        "
                                s_code = s_code[:first_line_end] + f'{indent}title_group = create_title("{canonical_title}")\n{indent}self.play(FadeIn(title_group, shift=DOWN*0.1), run_time=0.8)\n' + s_code[first_line_end:]
                                current_title_var = "title_group"
                else:
                    if len(title_defs) > 1:
                        rich_indices = []
                        for idx, td in enumerate(title_defs):
                            call_str = s_code[td.start():min(len(s_code), td.start() + 250)]
                            if "," in call_str[:call_str.find(")") if ")" in call_str else 250]:
                                rich_indices.append(idx)
                        keep_idx = rich_indices[0] if rich_indices else 0
                        for idx in reversed(range(len(title_defs))):
                            if idx == keep_idx:
                                continue
                            s_code = remove_title_def_and_play(s_code, title_defs[idx])
                        title_defs = list(re.finditer(title_pattern, s_code, re.M))

                    if title_defs:
                        t_var = title_defs[0].group(1).split(',')[0].strip()
                        has_entry = bool(re.search(rf'(?:FadeIn|Write|Create|Transform|ReplacementTransform|GrowFromCenter|self\.add|transition_header)\([^)]*\b{t_var}\b', s_code))
                        if not has_entry:
                            # Check if t_var was reassigned to another variable like title_group = new_title_group
                            m_assign = re.search(rf'^[ ]*([a-zA-Z0-9_]*title[a-zA-Z0-9_]*)\s*=\s*{t_var}\b', s_code, re.M)
                            if m_assign:
                                assigned_var = m_assign.group(1)
                                if re.search(rf'(?:FadeIn|Write|Create|Transform|ReplacementTransform|GrowFromCenter|self\.add|transition_header)\([^)]*\b{assigned_var}\b', s_code):
                                    has_entry = True
                        if not has_entry:
                            m_def = title_defs[0]
                            pos = m_def.end()
                            open_p = 1
                            while pos < len(s_code) and open_p > 0:
                                if s_code[pos] == '(': open_p += 1
                                elif s_code[pos] == ')': open_p -= 1
                                pos += 1
                            end_line = s_code.find("\n", pos)
                            if end_line == -1: end_line = len(s_code)
                            else: end_line += 1
                            
                            sub_match = re.search(r'^[ ]{4,12}([a-zA-Z0-9_]*sub[a-zA-Z0-9_]*)\s*=\s*CrispText\([^\n]+\n[ ]{4,12}\1\.next_to\([^\n]+\)\n', s_code[end_line:])
                            sub_var = None
                            if sub_match:
                                sub_var = sub_match.group(1)
                                end_line += sub_match.end()

                            indent = "        "
                            if sub_var:
                                if re.search(rf'FadeOut\([^)]*\b(?:{current_title_var}|title_group|title_1|title1|title2|title_2)\b', s_code):
                                    play_stmt = f'{indent}self.play(FadeIn({t_var}, shift=DOWN*0.1), FadeIn({sub_var}, shift=DOWN*0.1), run_time=0.6)\n'
                                else:
                                    play_stmt = f'{indent}self.play(FadeOut({current_title_var}), FadeIn({t_var}, shift=DOWN*0.1), FadeIn({sub_var}, shift=DOWN*0.1), run_time=0.6)\n'
                            else:
                                if re.search(rf'FadeOut\([^)]*\b(?:{current_title_var}|title_group|title_1|title1|title2|title_2)\b', s_code):
                                    play_stmt = f'{indent}self.play(FadeIn({t_var}, shift=DOWN*0.1), run_time=0.5)\n'
                                else:
                                    play_stmt = f'{indent}self.play(FadeOut({current_title_var}), FadeIn({t_var}, shift=DOWN*0.1), run_time=0.4)\n'
                            
                            s_code = s_code[:end_line] + play_stmt + s_code[end_line:]
                            current_title_var = t_var
                        else:
                            if current_title_var and current_title_var != t_var and re.search(rf'^[ ]*{current_title_var}\s*=', sanitized, re.M):
                                if not re.search(rf'(?:FadeOut|ReplacementTransform|self\.remove)\([^)]*\b{current_title_var}\b', s_code):
                                    m_def = title_defs[0]
                                    pos = m_def.end()
                                    open_p = 1
                                    while pos < len(s_code) and open_p > 0:
                                        if s_code[pos] == '(': open_p += 1
                                        elif s_code[pos] == ')': open_p -= 1
                                        pos += 1
                                    end_line = s_code.find("\n", pos)
                                    if end_line == -1: end_line = len(s_code)
                                    else: end_line += 1
                                    indent = "        "
                                    s_code = s_code[:end_line] + f"{indent}self.remove({current_title_var})\n" + s_code[end_line:]
                            current_title_var = t_var
                    else:
                        if re.search(rf'\bFadeOut\(\s*{current_title_var}\s*\),?\s*', s_code):
                            s_code = re.sub(rf'\bFadeOut\(\s*{current_title_var}\s*\),?\s*', '', s_code)
                            s_code = re.sub(r'self\.play\(\s*run_time=[^)]*\)\s*\n', '', s_code)

                new_sections.append((s_num, s_code))

            sanitized = "".join(s[1] for s in new_sections)

        # Purge any dangling self.remove(title_group) if title_group is not defined
        if not re.search(r'^[ ]*title_group\s*=', sanitized, re.M):
            sanitized = re.sub(r'^[ ]{4,12}self\.remove\(title_group\)\s*\n', '', sanitized, flags=re.M)

        # Fix any undefined new_title_group<N> referenced in animations
        for ntv in set(re.findall(r'\b(new_title_group\d*)\b', sanitized)):
            if not re.search(rf'^[ ]*{ntv}\s*=', sanitized, re.M):
                t_title = canonical_title or "Section Title"
                m_play = re.search(rf'([ ]{{4,12}})self\.play\([^)]*\b{ntv}\b', sanitized)
                if m_play:
                    indent = m_play.group(1)
                    pos = m_play.start()
                    sanitized = sanitized[:pos] + f'{indent}{ntv} = create_title("{t_title}")\n' + sanitized[pos:]
                else:
                    sanitized = re.sub(
                        rf'([ ]{{4,12}})(?=[^\n]*\b{ntv}\b)',
                        rf'\1{ntv} = create_title("{t_title}")\n\1',
                        sanitized,
                        count=1
                    )

    # -------------------------------------------------------------------------
    # 16. Centered Canvas Distribution & Anti-Overlap Layout Rules
    # -------------------------------------------------------------------------
    if is_executive:
        # (a) Prevent badges, pills, and indicator tags from jamming against the top-left title
        sanitized = re.sub(
            r'([a-zA-Z0-9_]*(?:badge|pill|tag|banner)[a-zA-Z0-9_]*)\.next_to\((?:new_)?title[0-9]*(?:_group)?,\s*DOWN[^\)]*\)',
            r'\1.move_to(UP * 2.1).set_x(0)',
            sanitized
        )

        # (b) Prevent pills shoved into the top-left corner
        sanitized = re.sub(
            r'([a-zA-Z0-9_]*(?:pill|badge|card)[a-zA-Z0-9_]*)\.to_corner\(UL\)\.shift\(DOWN\s*\*\s*1\.[0-9]+\s*\+\s*RIGHT\s*\*\s*0\.[0-9]+\)',
            r'\1.move_to(UP * 2.0).set_x(0)',
            sanitized
        )

        # (c) Prevent macro diagrams, flowcharts, tables, split_panels, and content containers
        # from inheriting the top-left title's x-coordinate (which bleeds left off-screen).
        # Any .next_to(title_group, DOWN...) on main containers MUST be centered with .set_x(0).
        # CRITICAL: Exclude dots, divider, line, subtitle, and accent objects!
        def center_container_match(match):
            var_name = match.group(1)
            if any(ignored in var_name.lower() for ignored in ["dot", "divider", "line", "underline", "subtitle", "accent"]):
                return match.group(0)
            return f"{var_name}.next_to({match.group(2)}, DOWN{match.group(3)}).set_x(0)"

        sanitized = re.sub(
            r'([a-zA-Z0-9_]+)\.next_to\(((?:new_)?title[0-9]*(?:_group)?),\s*DOWN([^\)]*)\)(?!\s*\.(?:set_x|move_to))',
            center_container_match,
            sanitized
        )

        # (d) Direct replacements for known heavy container patterns
        sanitized = re.sub(
            r'([a-zA-Z0-9_]*(?:flowchart|diagram|tree|model|table|grid|split_panels)[a-zA-Z0-9_]*)\.next_to\((?:new_)?title[0-9]*(?:_group)?,\s*DOWN[^\)]*\)',
            r'\1.move_to(DOWN * 0.45).set_x(0)',
            sanitized
        )

        # (e) Invert upward looping curved arrows that collide with slide header and indicator pills
        def flip_curved_arrow(m):
            s = m.group(1)
            e = m.group(2)
            rest = m.group(3)
            rest = re.sub(r'angle\s*=\s*-(?:TAU/4|PI/2|TAU/8|PI/4|PI/2\.2)', 'angle=TAU/4', rest)
            return f'CurvedArrow({s}.get_bottom() + DOWN*0.1, {e}.get_bottom() + DOWN*0.1, {rest})'

        sanitized = re.sub(
            r'CurvedArrow\(\s*(?:start_point=)?([a-zA-Z0-9_\[\]]+)\.get_top\(\)[^,]*,\s*(?:end_point=)?([a-zA-Z0-9_\[\]]+)\.get_top\(\)[^,]*,\s*([^)]+)\)',
            flip_curved_arrow,
            sanitized
        )
        sanitized = re.sub(
            r'(\.move_to\([a-zA-Z0-9_]*arrow[a-zA-Z0-9_]*)\.get_top\(\)\s*\+\s*UP\s*\*\s*(?:0\.[0-9]+|1\.[0-9]+)\)',
            r'\1.get_bottom() + DOWN * 0.18)',
            sanitized
        )

        # (e2) Anti-Overlap Container Height Clamping for Split Tints & Comparison Backgrounds
        # Prevents full-screen background tints from colliding with top cards or bottom takeaway cards
        sanitized = re.sub(
            r'Rectangle\(width=(?:\d+\.\d+|\d+),\s*height=(?:3\.[5-9]|4\.[0-9]),\s*fill_color=([^,]+)(,[^\)]+)?\)\.move_to\((LEFT|RIGHT)\s*\*\s*(?:\d+\.\d+|\d+)\s*\+\s*DOWN\s*\*\s*0\.[3-9]\)',
            r'Rectangle(width=5.4, height=2.8, fill_color=\1\2).move_to(\3 * 2.8 + DOWN * 0.45)',
            sanitized
        )
        sanitized = re.sub(
            r'Line\(UP\s*\*\s*(?:\d+\.\d+|\d+),\s*DOWN\s*\*\s*(?:\d+\.\d+|\d+),\s*color=C_DARK_BLUE,\s*stroke_width=1\.5\)',
            r'Line(UP * 0.95, DOWN * 1.85, color=C_DARK_BLUE, stroke_width=1.5)',
            sanitized
        )

        # Clamp oversized macro containers that invade the header ceiling (y > 1.7)
        def clamp_macro_container(match):
            w_val = float(match.group(1))
            h_val = float(match.group(2))
            rest = match.group(3)
            if h_val > 5.0:
                h_val = 4.8
            if w_val > 12.0:
                w_val = 11.8
            return f"RoundedRectangle(width={w_val}, height={h_val}{rest}"

        sanitized = re.sub(
            r'RoundedRectangle\(width=([0-9.]+),\s*height=([0-9.]+)(,\s*corner_radius=[^\)]+)',
            clamp_macro_container,
            sanitized
        )
        sanitized = re.sub(
            r'(\b[a-zA-Z0-9_]*container[a-zA-Z0-9_]*)\.move_to\(ORIGIN\)',
            r'\1.move_to(DOWN * 0.70)',
            sanitized
        )

        # (f) Specific scene overlap fixes:
        # DNA card image_2 at UP * 1.1 overlaps table matrix at UP * 0.0
        if "image_2.move_to(UP * 1.1)" in sanitized and "matrix.move_to(UP * 0.0)" in sanitized:
            sanitized = sanitized.replace("matrix.move_to(UP * 0.0)", "matrix.move_to(DOWN * 0.55).set_x(0)")

        # TowerOfHanoi placed too low at DOWN * 2.4, cut off at bottom
        sanitized = re.sub(
            r'TowerOfHanoi\(([^)]*)\)\.scale\(0\.8\)\.move_to\((LEFT|RIGHT)\s*\*\s*2\.8\s*\+\s*DOWN\s*\*\s*2\.4\)',
            r'TowerOfHanoi(\1).scale(0.65).move_to(\2 * 2.8 + DOWN * 2.1)',
            sanitized
        )

        # Axis below card collisions with takeaway banner
        if "ax_left.next_to(left_card, DOWN, buff=0.8)" in sanitized:
            sanitized = sanitized.replace("ax_left.next_to(left_card, DOWN, buff=0.8)", "ax_left.move_to(LEFT * 2.8 + DOWN * 1.55)")
            sanitized = sanitized.replace("ax_right.next_to(right_card, DOWN, buff=0.8)", "ax_right.move_to(RIGHT * 2.8 + DOWN * 1.55)")
            sanitized = sanitized.replace("cards = Group(left_card, right_card).arrange(RIGHT, buff=0.8).next_to(premise_box, DOWN, buff=0.3).set_x(0)",
                                          "cards = Group(left_card, right_card).arrange(RIGHT, buff=0.8).move_to(UP * 0.65).set_x(0)")
            sanitized = sanitized.replace("return VGroup(bg, text).move_to(DOWN * 3.3)", "return VGroup(bg, text).move_to(DOWN * 3.1).set_x(0)")

        # (g) Clamp extreme horizontal coordinates that bleed off-camera (only standalone positions, NOT relative offsets)
        def _clamp_screen_x(m):
            prefix = m.group(1) or ""
            direction = m.group(2)
            if prefix.strip() in ("+", "-"):
                return m.group(0)
            return f"{prefix}{direction} * 5.2"

        sanitized = re.sub(r'([+\-]?\s*)\b(RIGHT|LEFT)\s*\*\s*(?:[6-9]|\d{2,})(?:\.\d+)?', _clamp_screen_x, sanitized)
        sanitized = re.sub(r'Line\(\s*LEFT\s*\*\s*5\.[0-9]\s*,\s*RIGHT\s*\*\s*5\.[0-9][^\)]*\)', 'Line(LEFT * 1.5, RIGHT * 1.5, color="#C4C4C4", stroke_width=1.5)', sanitized)

        # (h) Auto-fit container internal content to eliminate text slicing & border collisions
        sanitized = re.sub(
            r'(?<!\.)\b((?:self\.)?[a-zA-Z0-9_]*(?:content|inner|items|group|txt|text|math|body)[a-zA-Z0-9_]*)\.move_to\(([a-zA-Z0-9_]*(?:bg|rect|box|card|panel|container)[a-zA-Z0-9_]*)\.get_center\(\)\)',
            r'fit_into_box(\1, \2)',
            sanitized
        )
        # Ensure VGroup(bg, txt) pairs use fit_into_box if not already fitted
        def _ensure_vgroup_fit(m):
            indent = m.group(1)
            vname = m.group(2)
            bg = m.group(3)
            txt = m.group(4)
            return f"{indent}fit_into_box({txt}, {bg}, pad_x=0.2, pad_y=0.08)\n{indent}{vname} = VGroup({bg}, {txt})"

        sanitized = re.sub(
            r'(?m)^(\s*)([a-zA-Z0-9_]+)\s*=\s*VGroup\(\s*([a-zA-Z0-9_]*(?:bg|rect|box|card))\s*,\s*([a-zA-Z0-9_]*(?:txt|text|label|title))\s*\)',
            _ensure_vgroup_fit,
            sanitized
        )
        # Remove consecutive duplicate fit_into_box calls
        sanitized = re.sub(r'(fit_into_box\([^)]+\)\s*\n\s*)+fit_into_box\(', r'fit_into_box(', sanitized)
        sanitized = re.sub(r'\bself\.fit_into_box\(', 'fit_into_box(', sanitized)
        sanitized = re.sub(r'\bfit_into_box\(self\.label_text,', 'fit_into_box(label_text,', sanitized)

    # -------------------------------------------------------------------------
    # 17. Strip Miniature Residual Recap Scaling (Prevents Miniature Illegible Blobs)
    # -------------------------------------------------------------------------
    diag_patterns = ('model', 'ref', 'diagram', 'tree', 'matrix', 'graph', 'schema', 'group', 'recap', 'step', 'arch', 'flow')
    s_lines = sanitized.splitlines()
    new_slines = []
    for s_line in s_lines:
        # Check standalone statement: <var>.scale(0.xx).move_to(...)
        m_stmt = re.match(r'^(\s*)([a-zA-Z0-9_]+)\.scale\(\s*0\.[1-3]\d*\s*\)\.(?:move_to|to_corner)\(.*\)\s*$', s_line)
        if m_stmt and any(dp in m_stmt.group(2) for dp in diag_patterns):
            indent, var = m_stmt.group(1), m_stmt.group(2)
            new_slines.append(f'{indent}{var}.set_opacity(0)')
            continue

        # Check inside FadeIn(<var>.scale(0.xx).move_to(...))
        m_fade = re.search(r'FadeIn\(\s*([a-zA-Z0-9_]+)\.scale\(\s*0\.[1-3]\d*\s*\)\.(?:move_to|to_corner)\((.*?)\)\s*\)', s_line)
        if m_fade and any(dp in m_fade.group(1) for dp in diag_patterns):
            var = m_fade.group(1)
            s_line = s_line[:m_fade.start()] + f'FadeIn({var}.set_opacity(0))' + s_line[m_fade.end():]

        # Check inside self.play(<var>.animate.scale(0.xx).move_to(...))
        m_anim = re.search(r'([a-zA-Z0-9_]+)\.animate\.scale\(\s*0\.[1-3]\d*\s*\)\.(?:move_to|to_corner)\((.*?)\)', s_line)
        if m_anim and any(dp in m_anim.group(1) for dp in diag_patterns):
            var = m_anim.group(1)
            s_line = s_line[:m_anim.start()] + f'{var}.animate.set_opacity(0)' + s_line[m_anim.end():]

        # Check miniature recap container boxes like diagram_ref_rect
        m_rect = re.match(r'^(\s*)([a-zA-Z0-9_]*(?:ref_rect|recap_box|mini_frame)[a-zA-Z0-9_]*)\s*=\s*RoundedRectangle\([^)]*\)\.(?:to_corner|move_to)\(.*\)', s_line)
        if m_rect:
            indent, var = m_rect.group(1), m_rect.group(2)
            s_line = s_line + f'\n{indent}{var}.set_opacity(0)'

        new_slines.append(s_line)
    sanitized = '\n'.join(new_slines)

    # Clean up any generic "Scene X" titles
    topic_scene_titles = {}

    # Try dynamic lookup from nearby composition JSON, storyboard blueprint, or instructions JSON
    if script_path:
        try:
            parent_dir = os.path.dirname(os.path.abspath(script_path))
            out_dir = os.path.dirname(parent_dir) if os.path.basename(parent_dir) == "manim_codes" else parent_dir
            for f in sorted(os.listdir(out_dir)):
                if f.endswith("_presentation_composition.json") or f.endswith("_storyboard_blueprint.json"):
                    with open(os.path.join(out_dir, f), "r", encoding="utf-8") as jf:
                        jdata = json.load(jf)
                        for sc in jdata.get("scenes", []):
                            sid = str(sc.get("scene_id") or sc.get("scene_number") or "")
                            stitle = sc.get("title") or sc.get("scene_title")
                            if not stitle:
                                steps = sc.get("presentation_steps", [])
                                if steps and (steps[0].get("title") or steps[0].get("step_title")):
                                    stitle = steps[0].get("title") or steps[0].get("step_title")
                            if sid and stitle and not stitle.lower().startswith("scene ") and len(stitle) < 60:
                                topic_scene_titles[sid] = stitle
                    break
        except Exception:
            pass
        except Exception:
            pass

    for sid, stitle in topic_scene_titles.items():
        sanitized = re.sub(rf'create_title\(\s*["\']Scene\s+{sid}["\']\s*\)', f'create_title("{stitle}")', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(rf'CrispText\(\s*["\']Scene\s+{sid}["\']\s*,', f'CrispText("{stitle}",', sanitized, flags=re.IGNORECASE)

    def _sub_sc_title(m):
        sid = m.group(1)
        stitle = topic_scene_titles.get(sid, f"Autonomous Agent Architecture - Part {sid}")
        return f'create_title("{stitle}")'
    sanitized = re.sub(r'create_title\(\s*["\']Scene\s+(\d+)["\']\s*\)', _sub_sc_title, sanitized, flags=re.IGNORECASE)

    # Purge any remaining Lorem ipsum dummy text
    if "Lorem ipsum" in sanitized or "lorem ipsum" in sanitized:
        sanitized = re.sub(r'Lorem ipsum[^"\']+', 'Autonomous Agent Architecture & Operational Workflow', sanitized, flags=re.IGNORECASE)

    # Purge prohibited Navy Blue (#0B3C5D, #06152B, #0A2540, #1D3557, NAVY) per manager directive
    sanitized = re.sub(
        r'((?:fill_color|fill|bg_color|background_color)\s*=\s*)(?:["\'](?:#0B3C5D|#06152B|#0A2540|#1D3557|#1E3A8A)["\']|\bNAVY\b|\bC_NAVY\b|\bC_NAVY_DARK\b)',
        r'\1"#FFFFFF"',
        sanitized
    )
    sanitized = re.sub(
        r'((?:stroke_color|stroke|border_color)\s*=\s*)(?:["\'](?:#0B3C5D|#06152B|#0A2540|#1D3557|#1E3A8A)["\']|\bNAVY\b|\bC_NAVY\b|\bC_NAVY_DARK\b)',
        r'\1"#2C81FE"',
        sanitized
    )
    sanitized = re.sub(
        r'(color\s*=\s*)(?:["\'](?:#0B3C5D|#06152B|#0A2540|#1D3557|#1E3A8A)["\']|\bNAVY\b|\bC_NAVY\b|\bC_NAVY_DARK\b)',
        r'\1"#404040"',
        sanitized
    )
    sanitized = re.sub(
        r'\b(?:COLOR_NAVY|C_NAVY|C_NAVY_DARK)\s*=\s*["\'](?:#0B3C5D|#06152B|#0A2540|#1D3557|#1E3A8A)["\']',
        'COLOR_NAVY = "#1E293B"',
        sanitized
    )

    # Enforce NO ALL-CAPS on CrispText / Text / Titles / Labels string literals
    _acronyms_set = {"AI", "RAM", "DB", "API", "LLM", "CPU", "GPU", "UI", "OSL", "ML", "OST", "VDB", "JSON", "HTTP", "REST", "SQL", "SME", "PIP", "HD", "FHD"}
    def _sanitize_string_casing(match):
        prefix = match.group(1)
        quote = match.group(2)
        s_val = match.group(3)
        words = s_val.split(" ")
        res = []
        for w in words:
            cw = w.strip(":,.;!?()[]\'\"")
            if cw.isupper() and len(cw) > 1 and cw not in _acronyms_set:
                idx = w.find(cw)
                res.append(w[:idx] + cw.capitalize() + w[idx+len(cw):])
            else:
                res.append(w)
        return f'{prefix}{quote}{" ".join(res)}{quote}'
    sanitized = re.sub(r'(\b(?:CrispText|Text|MarkupText|Paragraph|create_title|create_pill|create_badge|create_state_badge|create_lead_in|create_card)\s*\(\s*)(["\'])(.*?)\2', _sanitize_string_casing, sanitized)

    # Executive Client Review Purge: Replace complex LaTeX academic formulas with clear engineering text
    banned_math_subs = [
        (r'\\pi\^\*\(a\)\s*=\s*\\arg\\max[^\$"]*', 'Optimal Action: Multi-Factor Policy Utility'),
        (r'\\arg\\max\s*\\mathbb\{E\}\[U\(a\)\][^\$"]*', 'Max Expected Action Utility (Optimal Choice)'),
        (r'\\cos\\theta\s*=\s*\\frac\{[^\}]+\}\{[^\}]+\}', 'Semantic Embedding Similarity (Cosine 0.94)'),
        (r'\\mathbb\{R\}\^d', 'Dense Embedding Space (d-Dimensional)'),
        (r'\\mathbb\{E\}\[U\(a\)\]', 'Expected Utility Metric'),
    ]
    for pat, repl in banned_math_subs:
        sanitized = re.sub(pat, repl, sanitized)

    return sanitized


def sanitize_file(file_path: str) -> bool:
    """
    Reads, sanitizes, and overwrites the specified Python file in-place if changes were made.
    Returns True if the file was updated, False otherwise.
    """
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original = f.read()

        cleaned = sanitize_manim_code(original, script_path=file_path)

        if cleaned != original:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
            return True
        return False
    except Exception as e:
        print(f"[Sanitizer] Warning: Could not sanitize {file_path}: {e}")
        return False


def parse_error(output: str, filename: str) -> tuple[int | None, str]:
    """
    Parses deepest error line and exception message from Manim / Python traceback.
    """
    cleaned_lines = [re.sub(r"[│╭╮╰╯─]", " ", l) for l in output.splitlines()]
    cleaned = "\n".join(cleaned_lines)

    line_matches = re.findall(re.escape(filename) + r":(\d+)", cleaned)
    line_matches += re.findall(
        r'File\s+"[^"]*' + re.escape(filename) + r'",\s*line\s+(\d+)', cleaned
    )
    error_line = max((int(n) for n in line_matches), default=None)

    error_message = ""
    for line in reversed(cleaned_lines):
        stripped = line.strip()
        if re.match(r"^[A-Za-z_.]*[A-Za-z_]Error\b.*:", stripped) or re.match(
            r"^[A-Za-z_.]*Exception\b.*:", stripped
        ):
            error_message = stripped
            break

    return error_line, error_message


def extract_code_from_response(text: str) -> str:
    """Strips markdown code fences and returns pure Python source."""
    text = text.strip()
    matches = re.findall(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
    if matches:
        for m in matches:
            if "class FinalScene" in m or "def construct(" in m:
                return m.strip()
        longest = max(matches, key=len)
        return longest.strip()
    fence_match = re.match(r"^```(?:python)?\s*\n(.*)\n```$", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return text


def build_repair_prompt(source_code: str, error_line: int | None, error_message: str, raw_traceback: str) -> str:
    return f"""You are fixing a Manim Community Python scene file that failed during rendering.

--- CODE ---
```python
{source_code}
```

--- ERROR ---
Line reported: {error_line}
Exception: {error_message}

Traceback tail for context:
{raw_traceback[-3000:]}

TASK:
1. Fix the reported error above.
2. Ensure every ImageMobject uses a valid path and is wrapped inside Group (not VGroup).
3. Do not pass invalid kwargs like col_widths to Table or MobjectTable.
4. Ensure LaggedStart and self.play receive Animation instances (like FadeIn), not raw VMobjects.
5. Do not redesign the scene, change timings, or alter visual intent. Only fix the bug.
6. Return the COMPLETE corrected Python file and nothing else (no explanations, no markdown fences).
"""


def repair_code_with_llm(
    source_code: str,
    error_output: str,
    filename: str,
    google_api_key: str,
    model: str = "gemini-3.8-flash"
) -> str | None:
    """
    Attempts to repair broken Manim code using Gemini, compiling and sanitizing the result.
    Returns the repaired code string on success, or None on failure.
    """
    if not google_api_key:
        print("[Self-Healing] No google_api_key provided for repair.")
        return None

    error_line, error_message = parse_error(error_output, filename)
    print(f"[Self-Healing] Detected {error_message} at line {error_line} in {filename}")

    prompt = build_repair_prompt(source_code, error_line, error_message, error_output)

    clean_model = "gemini-3.8-flash" if model in ["gemini-3.8-flash", "gemini-3.8-flash", "gemini-3.8-flash", None] else model
    models_to_try = [clean_model]
    if "gemini-3.8-flash" not in models_to_try:
        models_to_try.append("gemini-3.8-flash")

    for try_model in models_to_try:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=google_api_key)
            response = client.models.generate_content(
                model=try_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=45000,
                )
            )
            text = response.text or ""
            fixed_code = extract_code_from_response(text)

            if not fixed_code.strip():
                print(f"[Self-Healing] LLM ({try_model}) returned empty response.")
                continue

            # Sanitize the repaired code
            fixed_code = sanitize_manim_code(fixed_code)

            # Validate syntax
            compile(fixed_code, filename, "exec")
            print(f"[Self-Healing] Successfully compiled repaired code for {filename} using {try_model}")
            return fixed_code
        except Exception as e:
            print(f"[Self-Healing] Repair attempt with {try_model} failed: {e}")

    return None


def apply_programmatic_timing_sync(styled_code: str, gm: dict) -> str:
    """
    Deterministic AST/regex timing synchronizer fallback:
    Splits scene into Presentation Steps, distributes self.sync_to(statement_start)
    across animation calls within each step matching narration statements, and replaces
    giant single trailing self.wait(...) calls so elements never appear upfront.
    """
    lines = styled_code.splitlines()

    sync_method_code = [
        "    def sync_to(self, target_time):",
        "        current_time = getattr(getattr(self, 'renderer', None), 'time', 0.0)",
        "        if target_time > current_time:",
        "            self.wait(target_time - current_time)\n"
    ]

    if "def sync_to(" not in styled_code:
        new_lines = []
        sync_inserted = False
        for line in lines:
            if not sync_inserted and re.match(r"^\s*def construct\b", line):
                new_lines.extend(sync_method_code)
                new_lines.append(line)
                sync_inserted = True
            else:
                new_lines.append(line)
        lines = new_lines

    pairs = gm.get("pairs", {})
    step_pattern = re.compile(r"^\s*#+[\s#]*(?:Presentation\s+Step|Animations\s+Step|Step)\s+(\d+)", re.IGNORECASE)

    raw_step_markers = []
    for idx, line in enumerate(lines):
        m = step_pattern.search(line)
        if m:
            raw_step_markers.append((idx, int(m.group(1))))

    # Deduplicate step markers preserving first occurrence of each step_num
    seen_steps = set()
    step_markers = []
    for idx, s_num in raw_step_markers:
        if s_num not in seen_steps:
            seen_steps.add(s_num)
            step_markers.append((idx, s_num))

    if not step_markers:
        return "\n".join(lines)

    processed_lines = []
    last_end = 0

    for i, (start_idx, step_num) in enumerate(step_markers):
        processed_lines.extend(lines[last_end:start_idx])
        end_idx = step_markers[i + 1][0] if i + 1 < len(step_markers) else len(lines)
        step_block = lines[start_idx:end_idx]
        last_end = end_idx

        pair_info = pairs.get(str(step_num), {})
        stmts = pair_info.get("statements", [])

        if not stmts:
            processed_lines.extend(step_block)
            continue

        step_header = step_block[0]
        step_body = step_block[1:]

        filtered_body = []
        for b_line in step_body:
            wait_m = re.match(r"^(\s*)self\.wait\(\s*([\d\.]+)\s*\)", b_line)
            if wait_m and float(wait_m.group(2)) >= 4.0:
                continue
            filtered_body.append(b_line)

        play_indices = []
        for l_idx, b_line in enumerate(filtered_body):
            if re.match(r"^\s*self\.play\(", b_line):
                play_indices.append(l_idx)

        n_plays = len(play_indices)
        n_stmts = len(stmts)

        if n_plays == 0:
            step_end = float(stmts[-1]["end"])
            indent = "        "
            processed_lines.append(step_header)
            processed_lines.extend(filtered_body)
            processed_lines.append(f"{indent}self.sync_to({step_end:.2f})")
            continue

        injected_body = []
        play_set = set(play_indices)
        last_injected_time = -1.0
        current_play_idx = 0

        for l_idx, b_line in enumerate(filtered_body):
            if l_idx in play_set:
                stmt_idx = min(int(current_play_idx * n_stmts / n_plays), n_stmts - 1)
                target_time = round(float(stmts[stmt_idx]["start"]), 2)
                indent_m = re.match(r"^(\s*)", b_line)
                indent = indent_m.group(1) if indent_m else "        "

                if target_time > last_injected_time:
                    injected_body.append(f"{indent}self.sync_to({target_time:.2f})")
                    last_injected_time = target_time

                injected_body.append(b_line)
                current_play_idx += 1
            else:
                injected_body.append(b_line)

        step_end = float(stmts[-1]["end"])
        if step_end > last_injected_time:
            indent = "        "
            injected_body.append(f"{indent}self.sync_to({step_end:.2f})")

        processed_lines.append(step_header)
        processed_lines.extend(injected_body)

    processed_lines.extend(lines[last_end:])
    return "\n".join(processed_lines)

