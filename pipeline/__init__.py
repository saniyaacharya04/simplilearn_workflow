"""
Simplilearn Post-Production AI Pipeline Package
"""
import os
import sys
import importlib

_pipeline_dir = os.path.dirname(os.path.abspath(__file__))
_helpers_dir = os.path.join(_pipeline_dir, "helpers")
_root_dir = os.path.dirname(_pipeline_dir)

for _p in [_helpers_dir, _pipeline_dir, _root_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Expose helper modules so 'from pipeline.config import ...' continues to work seamlessly
_helper_modules = [
    "config", "code_sanitizer", "tracker_manager",
    "semantic_matcher_asset", "swipe_transition", "teacher_cutout_and_placement",
    "image_generation_helper", "template1_title_intro", "template2_learning_roadmap",
    "template3_topic_coverage", "manim_compiler", "manim_probe_runner",
    "copy_pipeline_outputs", "reset_topics_for_styling_rerun"
]

for _m in _helper_modules:
    try:
        _imported = importlib.import_module(f"pipeline.helpers.{_m}")
        sys.modules[f"pipeline.{_m}"] = _imported
    except Exception:
        pass

try:
    from pipeline.helpers.config import *
except Exception:
    pass

# Ensure CrispText is globally accessible in builtins without modifying template files
try:
    import builtins
    if not hasattr(builtins, "CrispText"):
        from pipeline.helpers.template1_title_intro import CrispText
        builtins.CrispText = CrispText
except Exception:
    pass

