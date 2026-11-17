from __future__ import annotations

import argparse
import ast
import contextlib
import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

MAX_SNIPPET_CHARS = 220

# Splitting rule, byte-for-byte the same as the generation script.
_TAG_SPLIT = re.compile(r"(<[^>]+>)")
_SENTENCE_SPLIT = re.compile(r"(?<=[.;?:!])(?![.;?:!])")

_DUR_CACHE: dict[str, float] = {}

def split_statements(narration: str) -> list[str]:
    """Split a narration paragraph into TTS statements.

    Angle-bracket tags become standalone statements; everything else splits
    after sentence-final punctuation.
    """
    out: list[str] = []
    for part in _TAG_SPLIT.split(narration):
        if not part:
            continue
        if part.startswith("<") and part.endswith(">"):
            out.append(part.strip("<>").strip())
        else:
            for sub in _SENTENCE_SPLIT.split(part):
                if sub.strip():
                    out.append(sub.strip())
    return out


def audio_duration(path: Path) -> float:
    key = str(path)
    if key in _DUR_CACHE:
        return _DUR_CACHE[key]
    try:
        with contextlib.closing(wave.open(str(path), "rb")) as fh:
            dur = fh.getnframes() / float(fh.getframerate())
    except (wave.Error, EOFError):
        dur = _ffprobe_duration(path)
    _DUR_CACHE[key] = dur
    return dur


def _ffprobe_duration(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cannot read duration of {path}: {proc.stderr.strip()}")
    return float(proc.stdout.strip())


def load_narration(path: Path) -> dict:
    """Return ``{group_id: [pair_dict, ...]}`` from a CGI or storyboard file."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"{path} should be an object keyed by group id")
    for gid, pairs in doc.items():
        if not isinstance(pairs, list):
            raise ValueError(f"group {gid!r} should map to a list of pairs")
        for i, pair in enumerate(pairs, 1):
            if "narration_statement" not in pair:
                raise ValueError(f"group {gid} pair {i} has no narration_statement")
    return doc



def summarise(manifest: dict) -> str:
    lines = []
    for gid, g in manifest["groups"].items():
        lines.append(
            f"  group {gid}: {g['n_pairs']} pairs, {g['n_statements']} statements, "
            f"{g['duration']:.2f}s"
        )
        for pid in sorted(g["pairs"], key=int):
            p = g["pairs"][pid]
            cgi = p.get("cgi_run_time")
            delta = ""
            if cgi:
                delta = f"  (CGI predicted {cgi:.2f}s, off by {p['duration'] - cgi:+.2f}s)"
            lines.append(
                f"    pair {pid}: {p['start']:7.2f} -> {p['end']:7.2f}  "
                f"{len(p['statements'])} stmts{delta}"
            )
    return "\n".join(lines)

def render_text_timeline(result: dict, max_src: int = 150) -> str:
    """Compact human/LLM readable timeline."""
    out = [
        f"# timeline: {Path(result['scene_file']).name} :: {result['scene_class']}",
        f"# total animation duration: {result['total_duration']}s "
        f"over {result['n_events']} calls",
        "",
        f"{'idx':>4}  {'line':>5}  {'start':>8}  {'end':>8}  {'dur':>6}  source",
    ]
    for e in result["events"]:
        src = e["src"][:max_src]
        marker = ""
        if e["kind"] == "sync":
            marker = f"  <<< SYNC -> {e.get('sync_target')}s"
        out.append(
            f"{e['i']:>4}  {str(e['line'] or '-'):>5}  {e['start']:>8.2f}  "
            f"{e['end']:>8.2f}  {e['duration']:>6.2f}  {src}{marker}"
        )
    return "\n".join(out)

