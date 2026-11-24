"""
Simplilearn Pipeline Helper Modules, Templates & Utilities
"""
import os
import sys

_helpers_dir = os.path.dirname(os.path.abspath(__file__))
_pipeline_dir = os.path.dirname(_helpers_dir)
_root_dir = os.path.dirname(_pipeline_dir)

for _p in [_helpers_dir, _pipeline_dir, _root_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from .config import *
except Exception:
    pass
