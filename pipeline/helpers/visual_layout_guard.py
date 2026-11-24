"""
Visual Layout Guard & Geometry Collision Checker for Simplilearn OSL 3.0
========================================================================
Enforces strict screen boundaries, Layout 20 PiP clearance, non-overlapping
text spacing, and zero-equation mandates across all generated Manim code.
"""

import re
import ast
from typing import List, Dict, Tuple, Optional

# Strict camera viewport and safety margins (Manim 1920x1080 canvas: [-7.11, +7.11] x [-4.0, +4.0])
SAFE_X_MIN = -6.50
SAFE_X_MAX = 6.50
SAFE_Y_MIN = -3.55
SAFE_Y_MAX = 3.55

# Simplilearn Layout 20 Top-Right PiP Danger Zone: (1496, 40) px -> x >= 3.80 and y >= 1.50
PIP_X_MIN = 3.80
PIP_Y_MIN = 1.50

# Banned complex academic LaTeX patterns per client executive directive
BANNED_MATH_PATTERNS = [
    r'\\arg\\max',
    r'\\mathbb\{E\}',
    r'\\cos\\theta',
    r'\\mathbb\{R\}\^',
    r'\\sum_\{',
    r'\\prod_\{',
    r'\\int_\{',
    r'E\[U\(',
    r'\\pi\^\*\(a\)',
]


def check_banned_equations(code: str) -> List[str]:
    """Detects any complex LaTeX equations that violate executive review directives."""
    violations = []
    for pat in BANNED_MATH_PATTERNS:
        matches = re.findall(pat, code)
        if matches:
            violations.append(f"Banned equation pattern detected: '{matches[0]}'")
    return violations


def check_layout_20_clearance(code: str) -> List[str]:
    """Checks coordinate constants in Manim code to guarantee PiP clearance and bounds."""
    warnings = []
    
    # Check top chrome width / termination
    top_pos_matches = re.findall(r'move_to\(\s*(?:LEFT\s*\*\s*[\d\.]+\s*\+\s*)?UP\s*\*\s*([\d\.]+)', code)
    for y_val in top_pos_matches:
        y = float(y_val)
        if y > 3.65:
            warnings.append(f"Top chrome element at y={y:.2f} crowds upper screen edge (max recommended: 3.60).")

    # Check for direct coordinates that encroach PiP zone
    np_coords = re.findall(r'np\.array\(\[\s*([-+]?[\d\.]+)\s*,\s*([-+]?[\d\.]+)\s*,\s*([-+]?[\d\.]+)\s*\]\)', code)
    for xs, ys, _ in np_coords:
        x, y = float(xs), float(ys)
        if x >= PIP_X_MIN and y >= PIP_Y_MIN:
            warnings.append(f"Coordinate ({x:.2f}, {y:.2f}) encroaches Layout 20 PiP zone (x >= {PIP_X_MIN}, y >= {PIP_Y_MIN})!")
        if x < SAFE_X_MIN or x > SAFE_X_MAX:
            warnings.append(f"Coordinate x={x:.2f} overflows horizontal screen safety limit [{SAFE_X_MIN}, {SAFE_X_MAX}].")
        if y < SAFE_Y_MIN or y > SAFE_Y_MAX:
            warnings.append(f"Coordinate y={y:.2f} overflows vertical screen safety limit [{SAFE_Y_MIN}, {SAFE_Y_MAX}].")

    return warnings


def check_coordinate_collisions(code: str) -> List[str]:
    """Detects identical or dangerously close coordinates between different mobjects."""
    warnings = []
    coord_usage = {}
    lines = code.splitlines()
    for idx, line in enumerate(lines, 1):
        match = re.search(r'move_to\(np\.array\(\[\s*([-+]?[\d\.]+)\s*,\s*([-+]?[\d\.]+)', line)
        if match:
            x, y = round(float(match.group(1)), 2), round(float(match.group(2)), 2)
            key = (x, y)
            if key in coord_usage:
                prev_line, prev_code = coord_usage[key]
                # If they are different mobjects placed at exact same spot in the same step
                if line.strip() != prev_code.strip():
                    warnings.append(f"Direct collision risk: Lines {prev_line} and {idx} place different mobjects at exact same coordinate ({x}, {y})!")
            coord_usage[key] = (idx, line)
    return warnings


def validate_manim_layout_and_styling(code: str) -> Dict[str, any]:
    """Comprehensive validation suite for Manim presentation scripts."""
    eq_violations = check_banned_equations(code)
    pip_warnings = check_layout_20_clearance(code)
    collision_warnings = check_coordinate_collisions(code)

    is_valid = len(eq_violations) == 0 and len(pip_warnings) == 0
    return {
        "valid": is_valid,
        "equation_violations": eq_violations,
        "pip_and_bound_warnings": pip_warnings,
        "collision_warnings": collision_warnings,
        "summary": "PASS" if is_valid else f"FAIL ({len(eq_violations)} equations, {len(pip_warnings)} bounds/PiP)"
    }
