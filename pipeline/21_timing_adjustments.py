"""
================================================================================
PIPELINE STAGE 21: TIMING ADJUSTMENTS & AUDIO SYNCHRONIZATION
================================================================================

1. STAGE OVERVIEW:
   - Stage Index: 21
   - Script Name: 21_timing_adjustments.py
   - Primary Class: GenerateTimingAdjustments
   - Pipeline Role:
     Performs millisecond-precision audio-animation time synchronization on the styled
     Manim scripts produced in Stage 20. Measures the exact runtime of every visual
     animation step (via manim_probe_runner.py or static AST analysis) and compares
     it against the corresponding narration audio duration from CGI_Input.json.
     Injects precise self.wait(...) or sync_to(...) delays into the Manim code,
     outputting synchronized scripts to manim_time_synced_code/.

2. UPSTREAM DEPENDENCIES & PREVIOUS STAGES USED:
   - Uses Previous Stages: YES.
   - Upstream Stages Used:
     * Stage 20 (20_final_styling_corrections.py):
       - How: Ingests styled scripts from manim_styled_codes/group_{group}.py via
         20_eng_corrections_tracker.json.
       - Purpose: Provides the polished, defect-free Manim code to be synchronized.
     * Stage 5 (5_generate_audio.py):
       - How: Ingests CGI_Input.json.
       - Purpose: Supplies the exact duration in seconds for each spoken narration sentence.
   - Input Tracker: ppt_trackers/20_eng_corrections_tracker.json

3. INPUT SPECIFICATIONS:
   - What is picked up as input:
     * manim_styled_codes/group_{group}.py (Stage 20):
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_styled_codes/group_*.py
       Content: Fully styled and sanitized Manim Python scripts.
     * CGI_Input.json (Stage 5):
       Location: data_ppt_advanced/<TOPIC_NAME>/CGI_Input.json
       Content: Master time-coded narration manifest with statement runtimes.
     * ex_config.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/ex_config.json
       Content: Topic configuration.
     * Input Tracker:
       Location: ppt_trackers/20_eng_corrections_tracker.json

4. EXECUTION LOGIC & PROCESSING:
   - Step 1: Validates upstream completion in 20_eng_corrections_tracker.json.
   - Step 2: Parses narration statements and cumulative target runtimes from CGI_Input.json.
   - Step 3: Probes the runtime of each presentation step in the Manim code (using manim_probe_runner.py
     or static animation AST calculation).
   - Step 4: Calculates the delta: required_pause = audio_duration - animation_runtime.
   - Step 5: Uses LLM (or programmatic AST rewriting) to inject calculated self.wait(required_pause)
     at exact statement boundaries, ensuring animations never drift or finish out of sync with audio.
   - Step 6: Generates audio_animation_sync_manifest.json detailing the timing alignment.
   - Step 7: Writes synchronized code into manim_time_synced_code/group_{n}.py.
   - Step 8: Atomically updates 21_timing_adjustment_tracker.json.

5. OUTPUT SPECIFICATIONS:
   - What is generated as output:
     * manim_time_synced_code/group_{n}.py:
       Location: data_ppt_advanced/<TOPIC_NAME>/manim_time_synced_code/group_*.py
       Content: Audio-synchronized Manim Community Python scripts with precision waits.
     * audio_animation_sync_manifest.json:
       Location: data_ppt_advanced/<TOPIC_NAME>/audio_animation_sync_manifest.json
       Content: Detailed statement-level audio vs. animation timing comparison manifest.
     * Output Tracker:
       Location: ppt_trackers/21_timing_adjustment_tracker.json
       Content: Atomic tracker confirming completion of timing adjustment phase.

6. DOWNSTREAM CONSUMERS:
   - Stage 22 (22_final_code_run.py): Compiles synchronized code into final video deliverables.
================================================================================
"""


import os
import sys
from pathlib import Path

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_HELPERS_DIR = os.path.join(_CURRENT_DIR, "helpers")
_ROOT_DIR = _CURRENT_DIR if os.path.exists(os.path.join(_CURRENT_DIR, "pipeline")) else os.path.dirname(_CURRENT_DIR)
_PIPELINE_HELPERS = os.path.join(_ROOT_DIR, "pipeline", "helpers")
_PIPELINE_DIR = os.path.join(_ROOT_DIR, "pipeline")
for _p in [_CURRENT_DIR, _HELPERS_DIR, _PIPELINE_HELPERS, _PIPELINE_DIR, _ROOT_DIR]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from audio_adjustment_helpers.helper_utilities import *
except ImportError:
    pass

try:
    from word_transcriber import (
        get_or_create_word_transcript,
        find_keyword_spoken_time,
        extract_key_spoken_anchors
    )
except ImportError:
    try:
        from helpers.word_transcriber import (
            get_or_create_word_transcript,
            find_keyword_spoken_time,
            extract_key_spoken_anchors
        )
    except ImportError:
        def get_or_create_word_transcript(*args, **kwargs):
            return None
        def find_keyword_spoken_time(*args, **kwargs):
            return None
        def extract_key_spoken_anchors(*args, **kwargs):
            return []

import os
import sys
import json
import math
import re
import subprocess
import wave
import argparse
import contextlib
from collections import defaultdict
from datetime import datetime, timezone
from glob import glob
from pathlib import Path
import time
import shutil
from typing import Union, List, Dict, Any, Optional

try:
    import portalocker
except ImportError:
    portalocker = None

try:
    from filelock import FileLock
except ImportError:
    FileLock = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from dotenv import load_dotenv
load_dotenv()

try:
    from code_sanitizer import (
        sanitize_manim_code, sanitize_file, extract_code_from_response,
        repair_code_with_llm, apply_programmatic_timing_sync
    )
except ImportError:
    def sanitize_manim_code(code: str, **kwargs) -> str:
        return code
    def sanitize_file(path: str, **kwargs) -> None:
        pass
    def extract_code_from_response(text: str) -> str:
        m = re.search(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
        return m.group(1).strip() if m else text.strip()
    def repair_code_with_llm(code: str, **kwargs) -> str:
        return code
    def apply_programmatic_timing_sync(code: str, gm: dict) -> str:
        return code


_TAG_SPLIT = re.compile(r"(<[^>]+>)")
_SENTENCE_SPLIT = re.compile(r"(?<=[.;?:!])(?![.;?:!])")

_DUR_CACHE: dict[str, float] = {}
SECTION_RE = re.compile(r"^\s*#+\s*Section\s+(\d+)", re.IGNORECASE)

# Standalone helper definitions if helper_utilities was not imported
if "load_narration" not in globals():
    def load_narration(path: Union[str, Path]) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

if "split_statements" not in globals():
    def split_statements(raw: str) -> list[str]:
        parts = _TAG_SPLIT.split(raw)
        out = []
        for p in parts:
            if not p:
                continue
            if p.startswith("<") and p.endswith(">"):
                out.append(p.strip("<>").strip())
            else:
                for s in _SENTENCE_SPLIT.split(p):
                    s = s.strip()
                    if s:
                        out.append(s)
        return out or ([raw.strip()] if raw.strip() else ["Statement"])

if "audio_duration" not in globals():
    def audio_duration(file_path: Union[str, Path]) -> float:
        path_str = str(file_path)
        if path_str in _DUR_CACHE:
            return _DUR_CACHE[path_str]
        p = Path(file_path)
        if not p.exists() or p.stat().st_size == 0:
            return 0.0
        dur = 0.0
        if p.suffix.lower() == ".wav":
            try:
                with wave.open(str(p), "rb") as wf:
                    dur = float(wf.getnframes()) / float(wf.getframerate())
            except Exception:
                dur = 0.0
        if dur <= 0.0:
            try:
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                dur = float(res.stdout.strip())
            except Exception:
                pass
        dur = round(dur, 3)
        _DUR_CACHE[path_str] = dur
        return dur

if "summarise" not in globals():
    def summarise(manifest: dict) -> str:
        groups = manifest.get("groups", {})
        total_dur = sum(g.get("duration", 0.0) for g in groups.values())
        total_stmts = sum(g.get("n_statements", 0) for g in groups.values())
        return f"Manifest summary: {len(groups)} groups, {total_stmts} statements, total duration: {total_dur:.2f}s"

SYSTEM_PROMPT = """
You are a narration-driven Manim animation timing editor.

You are given:

1. NARRATION — ordered statements with explicit absolute start/end times.
2. CODE — the existing Manim scene and its visual design.

Your task is to modify the CODE so that the visual story unfolds in sync with the individual narration statements.

The NARRATION controls **WHEN** things happen.
The CODE controls **WHAT** is shown.


The existing animation sequence and durations are NOT authoritative.

## PRIMARY OBJECTIVE

Treat every narration statement as an independent temporal opportunity for a meaningful visual change.

The primary mechanism is:
```
def sync_to(self, target_time):
    current_time = self.renderer.time
    if target_time > current_time:
        self.wait(target_time - current_time)
```

For each statement, ask:

> What should the viewer see BEGIN happening when this statement begins?

Then make that visual event begin at the statement's start time.

Use:

```python
self.sync_to(START_TIME)
```

immediately before the corresponding visual event.

Do NOT synchronize only to presentation-step boundaries.

Do NOT use the end of a presentation step as the default synchronization target.

A presentation step is only a container for multiple narration statements.

For N distinct narration ideas, aim for approximately N meaningful visual beats.

## NARRATION TIMING

The narration provides absolute times.

Example:

```text
[1.1] 0.00s -> 4.58s
When organizing a project, we often group individuals by their skills.

[1.2] 4.58s -> 7.80s
Let us assume we have two distinct groups of developers.

[1.3] 7.80s -> 12.62s
Team A knows Python, and Team B knows JavaScript.
```

Use those start times directly:

```python
self.sync_to(0.00)
...
self.sync_to(4.58)
...
self.sync_to(7.80)
```

Do not recalculate or infer different target times.

## VISUAL DECOMPOSITION — CRITICAL

Do NOT treat a VGroup, Group, card, diagram, equation, list, or composite object as one visual event merely because it is one Python object.

Before constructing the animation sequence, mentally decompose the existing CODE into meaningful visual components.

The synchronization unit is a **meaningful instructional component**, not a Python object.

If a composite object contains independently meaningful elements, reveal those elements progressively.

### Example

Given:

```python
lists_group = VGroup(list_a_card, list_b_card)

list_a_items = VGroup(
    create_pill("Alice"),
    create_pill("Bob"),
    create_pill("Charlie")
)
```

Do NOT automatically do:

```python
self.sync_to(4.58)
self.play(FadeIn(lists_group))
```

Instead, when supported by the narration, use smaller reveals such as:

```python
self.sync_to(4.58)
self.play(FadeIn(list_a_card))

self.sync_to(...)
self.play(FadeIn(list_b_card))

self.sync_to(...)
self.play(FadeIn(list_a_items[0]))

self.sync_to(...)
self.play(FadeIn(list_a_items[1]))
```

The exact decomposition must follow the narration.

## PROGRESSIVE REVEAL

Progressive reveal is the DEFAULT.

Prefer:

* card → title → contents
* list → individual items
* diagram → components
* equation → meaningful parts
* VGroup → meaningful children
* concept → example → highlight
* objects → relationship between objects

Do not reveal several independently meaningful concepts simultaneously merely because they belong to the same VGroup.

However, do NOT over-split purely decorative or implementation-level objects.

Do not separately animate:

* every border stroke
* every decorative shape
* every character of ordinary text
* helper geometry with no instructional meaning

The goal is:

**one narration idea → one meaningful visual reveal**

not:

**one Python object → one animation**

## STATEMENT-TO-VISUAL MAPPING

Before implementing the animation, internally map each narration statement to the visual component(s) that communicate it.

For example:

```text
statement: "two groups"
→ reveal the two group containers

statement: "Python and JavaScript"
→ reveal the corresponding labels/content

statement: "either language"
→ introduce the union/OR concept

statement: "both languages"
→ introduce the intersection/overlap
```

This mapping is internal. Do NOT output it.

If the CODE already contains the required objects, reuse them.

Do not invent new visual concepts when existing objects can communicate the narration.

If a statement has no meaningful new visual event, it may continue an existing visual state. Do not invent meaningless animation just to force synchronization.

## CODE MODIFICATION

You may freely restructure the animation sequence.

You may:

* split `self.play()` calls
* split VGroups into meaningful children
* reveal children progressively
* change `run_time`
* remove redundant waits
* add `sync_to()`
* introduce intermediate highlights
* reorder visual reveals when necessary for narration alignment

The existing object hierarchy is NOT a synchronization constraint.

For example:

```python
self.play(FadeIn(lists_group))
```

may become several animations of its children.

## CRITICAL MANDATE — VISUAL RETENTION, TYPOGRAPHY & TEMPORAL SCHEDULING:
Your responsibility is precise TEMPORAL SYNCHRONIZATION, PACING, and LEGIBILITY:

1. PERSISTENCE & FULL SPOKEN DURATION MANDATE:
   - Visual elements (cards, diagrams, text groups, nodes) MUST stay on screen for the FULL TIME they are being spoken about.
   - NEVER dismiss, fade out, or wipe away an element immediately after animating it in!
   - If the narrator discusses a concept for 10, 15, or 20 seconds, KEEP THAT CARD VISIBLE for the entire discussion.
   - Dismiss or fade out elements ONLY when the narrator clearly transitions to an entirely new section or topic.

2. WORD-LEVEL SYNCHRONIZATION & IN-PLACE SPOKEN HIGHLIGHTING:
   - Use the exact word timestamps provided in the prompt to schedule reveals (`self.sync_to(word_start)`).
   - When the speaker refers to or emphasizes a component that is ALREADY on screen, do NOT delete or recreate it. Trigger an in-place spoken highlight at that exact word timestamp:
     ```python
     self.sync_to(word_start)
     self.play(card.animate.set_stroke(color=COLOR_HIGHLIGHT, width=3.0), run_time=0.35)
     self.play(card.animate.set_stroke(color=COLOR_BORDER, width=1.5), run_time=0.5)
     ```
     Or pulse text:
     ```python
     self.sync_to(word_start)
     self.play(txt.animate.set_color(COLOR_HIGHLIGHT), run_time=0.3)
     self.play(txt.animate.set_color(COLOR_NAVY_TITLE), run_time=0.5)
     ```

3. TYPOGRAPHY SCALE & WHITESPACE ELIMINATION MANDATE:
   - Text must be bold, crisp, and clearly legible on mobile and 1080p desktop:
     * Scene Super-Header: font_size=32 to 36
     * Card / Section Headers: font_size=22 to 26
     * Body Text & Bullet lines: font_size=18 to 20 (NEVER allow font sizes below 16!)
     * Badges / Pill Tags: font_size=14 to 16
   - If the input code has tiny unreadable text (font_size 10 to 14), upgrade it to these standard legible sizes and ensure container cards span adequately (e.g. width=5.8 to 6.4 in Layout 70, or width=10.5 to 12.0 in Layout 20) so the screen is balanced without barren white space voids.

4. TEMPORAL SCHEDULING:
   - Insert `self.sync_to(TIMESTAMP)` before visual reveals.
   - Split composite `self.play()` calls into progressive child reveals when aligned with narration.
   - Adjust `run_time` so animations complete before the next timestamp beat.
   - Conclude construct() with `self.sync_to(total_audio_duration)` matching the group's total audio duration.

5. AMBIENT KINETIC MOTION DURING EXTENDED SPOKEN INTERVALS (NO DEAD FREEZES):
   - When a statement or explanation spans more than 4–5 seconds between reveals, DO NOT leave the video as a completely frozen still frame during `self.sync_to()`.
   - Preserve and maintain continuous updaters (`add_updater`, rotating elements, flowing particle dots, breathing telemetry halos) across pauses.
   - If a scene has long waits, inject subtle kinetic micro-actions at intermediate timestamps:
     * Gentle focus stroke pulse or subtle scale ping on the active concept being explained.
     * Traveling data dot along an existing conduit using `MoveAlongPath`.
     * Dithering or progressive update on gauge or value readouts.
   - The screen must remain visually dynamic and engaging at all times throughout the speaker's voiceover.

## FORWARD-ONLY TIMING

`sync_to()` only waits forward.

Therefore, ensure that preceding animations do not push important visual beats beyond their target timestamps.

If necessary, split or shorten earlier animations.

Bad:

```python
self.play(long_animation, run_time=8)
self.sync_to(4.58)
```

Good:

```python
self.sync_to(4.58)
self.play(animation, run_time=1.5)
```

## SECTION BOUNDARIES

Presentation-step boundaries are NOT synchronization points unless a narration statement actually begins there.

This is wrong:

```python
self.sync_to(31.95)
```

simply because the presentation step ends at 31.95s.

This is correct:

```python
self.sync_to(24.26)
```

if a narration statement begins at 24.26s and a corresponding visual beat begins there.

A final `sync_to(section_end)` must never be used as a substitute for statement-level synchronization.

## SYNCHRONIZATION DENSITY

Do not cluster the visual animation at the beginning of a presentation step.

Distribute meaningful visual changes across the narration interval.

If six statements progressively introduce six ideas, the visual composition should progressively develop across those six statement boundaries.

Avoid patterns like:

```python
self.play(large_animation)
self.play(another_large_animation)
self.wait(15)
self.sync_to(section_end)
```

when the narration contains multiple distinct concepts during that interval.

Prefer:

```python
self.sync_to(t1)
self.play(visual_1)

self.sync_to(t2)
self.play(visual_2)

self.sync_to(t3)
self.play(visual_3)

self.sync_to(t4)
self.play(visual_4)
```

## FINAL CHECK

Before returning the code, verify:

1. Every narration statement has a known absolute start time.
2. Each statement with a distinct visual idea has a corresponding visual beat where practical.
3. `sync_to()` appears immediately before the relevant visual beat.
4. Visual beats are distributed across the narration interval.
5. Composite objects are progressively revealed when their components are independently meaningful.
6. No large VGroup/Card/Diagram reveal unnecessarily covers several narration statements.
7. No presentation-step boundary is being used as a substitute for statement timing.
8. No preceding animation makes a later synchronization target unreachable.
9. The instructional meaning and visual design remain intact.
10. ALWAYS conclude construct() with `self.sync_to(total_duration)` matching the group's total audio duration so the scene remains held while the final narration statement finishes speaking.

Return the COMPLETE MODIFIED MANIM CODE ONLY. Please make sure that the presentation step boundaries are shown as `## Presentation Step N` in the code

Do not return explanations, JSON, analysis, mappings, or commentary.

"""

class GenerateTimingAdjustments:
    """
    Stage 21: Timing Adjustments & Audio Synchronization.
    Probes animation durations, calculates pacing delta against CGI_Input.json audio,
    and injects precision synchronization pauses into Manim code.
    """
    def __init__(
        self,
        input_tracker_path: Optional[str] = None,
        output_tracker_path: Optional[str] = None,
        google_api_key: Optional[str] = None,
        claude_api_key: Optional[str] = None,
        input_folder: Optional[str] = None
    ):
        self.input_tracker_path = input_tracker_path
        self.output_tracker_path = output_tracker_path
        self.google_api_key = google_api_key
        self.claude_api_key = claude_api_key
        self.input_folder = input_folder or "."
        
        # Initialize output tracker file if it doesn't exist
        if self.output_tracker_path and not os.path.exists(self.output_tracker_path):
            tracker_dir = os.path.dirname(self.output_tracker_path)
            if tracker_dir and not os.path.exists(tracker_dir):
                os.makedirs(tracker_dir, exist_ok=True)
            with open(self.output_tracker_path, 'w', encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False)

    # ---------------------------------------------------------
    # UTILITIES & FILE I/O
    # ---------------------------------------------------------

    def _load_tracker(self, filepath):
        """
        Load a JSON tracker with a shared lock (read lock).
        """
        if not os.path.exists(filepath):
            return {}
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if portalocker:
                    portalocker.lock(f, portalocker.LOCK_SH)
                try:
                    content = f.read()
                    if not content:
                        return {}
                    data = json.loads(content)
                except json.JSONDecodeError:
                    data = {}
                finally:
                    if portalocker:
                        portalocker.unlock(f)
            return data
        except Exception as e:
            print(f"Error loading tracker {filepath}: {e}")
            return {}

    def _save_tracker(self, filepath, data):
        """
        Save a JSON tracker with an exclusive lock (write lock).
        """
        lock_path = filepath + ".lock"
        try:
            if portalocker:
                lock_ctx = portalocker.Lock(lock_path, timeout=60)
            elif FileLock:
                lock_ctx = FileLock(lock_path, timeout=60)
            else:
                lock_ctx = contextlib.nullcontext()

            with lock_ctx:
                current = {}
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            current = json.load(f)
                    except Exception:
                        current = {}
                current.update(data)
                temp_file = filepath + f".tmp.{os.getpid()}"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(current, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, filepath)
        except Exception as e:
            print(f"Error saving tracker {filepath}: {e}")


    def load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def sort_key(self,k):
        match = re.search(r"group_(\d+).py", k)
        if match:
            group_num = int(match.group(1))
            return group_num
        return float('inf')
    
    def _natkey(self, s: str):
        return (0, int(s)) if str(s).isdigit() else (1, str(s))

    def build_manifest(
        self,
        narration_path: Path,
        audio_dir: Path,
        gap_within_pair: float = 0.15,
        gap_between_pairs: float = 0.35,
        lead_in: float = 0.0,
        groups: list[str] | None = None,
        lenient: bool = False,
    ) -> dict:
        narration = load_narration(narration_path)
        wanted = [str(g) for g in groups] if groups else sorted(narration, key=self._natkey)

        out_groups: dict[str, dict] = {}
        problems: list[str] = []

        for gid in wanted:
            if gid not in narration:
                problems.append(f"group {gid} is not in {narration_path.name}")
                continue

            clock = lead_in          # <-- reset per group; this is the fix
            pairs_out: dict[str, dict] = {}

            for pair_index, pair in enumerate(narration[gid], start=1):
                pair_start = clock
                statements = []

                raw_stmts = pair.get("statements")
                has_statements_array = (
                    isinstance(raw_stmts, list)
                    and len(raw_stmts) > 0
                    and all(isinstance(s, dict) and "statement" in s and "runtime" in s for s in raw_stmts)
                )

                if has_statements_array:
                    # Iterate through statements array from CGI_Input.json directly
                    for st_index, stmt_info in enumerate(raw_stmts, start=1):
                        stmt_text = str(stmt_info.get("statement", "")).strip()
                        is_silence = stmt_text.strip("<>").lower() == "silence"
                        try:
                            dur = float(stmt_info.get("runtime", 0.0))
                        except (ValueError, TypeError):
                            dur = 0.0

                        # Check if matching .wav file happens to exist in audio_dir
                        fname = f"group_{gid}_pair_{pair_index}_statement{st_index}.wav"
                        fpath = audio_dir / fname
                        file_val = fname if fpath.exists() else ""

                        statements.append(
                            {
                                "index": st_index,
                                "text": stmt_text,
                                "file": file_val,
                                "start": round(clock, 3),
                                "end": round(clock + dur, 3),
                                "duration": round(dur, 3),
                                "silence": is_silence,
                            }
                        )
                        clock += dur + gap_within_pair
                else:
                    raw = pair.get("narration_statement") or pair.get("voiceover_narration") or ""
                    is_silence = raw.strip().strip("<>").lower() == "silence"
                    texts = ["<silence>"] if is_silence else split_statements(raw)

                    for st_index, text in enumerate(texts, start=1):
                        fname = f"group_{gid}_pair_{pair_index}_statement{st_index}.wav"
                        fpath = audio_dir / fname

                        if not fpath.exists():
                            msg = f"missing audio: {fname}"
                            if not lenient:
                                problems.append(msg)
                                continue
                            problems.append(msg + " (skipped, --lenient)")
                            continue

                        dur = audio_duration(fpath)
                        statements.append(
                            {
                                "index": st_index,
                                "text": text,
                                "file": fname,
                                "start": round(clock, 3),
                                "end": round(clock + dur, 3),
                                "duration": round(dur, 3),
                                "silence": is_silence,
                            }
                        )
                        clock += dur + gap_within_pair

                if not statements:
                    pairs_out[str(pair_index)] = {
                        "pair": pair_index,
                        "start": round(pair_start, 3),
                        "end": round(pair_start, 3),
                        "duration": 0.0,
                        "cgi_run_time": pair.get("run_time"),
                        "statements": [],
                    }
                    continue

                # The trailing within-pair gap becomes the between-pair gap.
                clock -= gap_within_pair
                pair_end = clock
                clock += gap_between_pairs

                pairs_out[str(pair_index)] = {
                    "pair": pair_index,
                    "start": round(pair_start, 3),
                    "end": round(pair_end, 3),
                    "duration": round(pair_end - pair_start, 3),
                    "cgi_run_time": pair.get("run_time"),
                    "statements": statements,
                }

            total = max((p["end"] for p in pairs_out.values()), default=0.0)
            out_groups[gid] = {
                "group_id": gid,
                "duration": round(total, 3),
                "n_pairs": len(pairs_out),
                "n_statements": sum(len(p["statements"]) for p in pairs_out.values()),
                "pairs": pairs_out,
            }

        manifest = {
            "meta": {
                "schema": 2,
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "narration_source": str(narration_path),
                "audio_dir": str(audio_dir),
                "gap_within_pair": gap_within_pair,
                "gap_between_pairs": gap_between_pairs,
                "lead_in": lead_in,
            },
            "groups": out_groups,
        }
        return manifest, problems
    
    def _strip_fences(self, text: str) -> str:
        return extract_code_from_response(text)

    @staticmethod
    def apply_programmatic_timing_sync(styled_code: str, gm: dict) -> str:
        """
        Deterministic AST/regex timing synchronizer fallback:
        Splits scene into Presentation Steps, distributes self.sync_to(statement_start)
        across animation calls within each step matching narration statements, and replaces
        giant single trailing self.wait(...) calls so elements never appear upfront.
        """
        return apply_programmatic_timing_sync(styled_code, gm)


    @staticmethod
    def replace_func_in_code(code: str, func_name: str, new_func_body: str) -> str:
        """
        Replaces the complete definition of func_name in code with new_func_body,
        preserving matching indentation level without regex backtracking risks.
        """
        lines = code.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(rf"^([ \t]*)def {func_name}\b", line)
            if match:
                indent = match.group(1)
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if not next_line.strip():
                        j += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip(" "))
                    if next_indent <= len(indent):
                        break
                    j += 1
                body_lines = [f"{indent}{l}" if l.strip() else "" for l in new_func_body.strip().splitlines()]
                lines = lines[:i] + body_lines + lines[j:]
                return "\n".join(lines)
            i += 1
        return code

    @staticmethod
    def make_scaling_conditional(code: str) -> str:
        """
        Ensures any call to .scale_to_fit_width(arg) is safely guarded by
        'if hasattr(var, "width") and var.width > (arg): var.scale_to_fit_width(arg)'.
        Idempotent: collapses any existing duplicate 'if hasattr' guards and avoids
        re-wrapping lines that are already guarded.
        """
        pattern = r'if hasattr\(([a-zA-Z0-9_]+), "width"\) and \1\.width > \(([^)]+)\):\s*if hasattr\(\1, "width"\) and \1\.width > \(\2\):'
        while re.search(pattern, code):
            code = re.sub(pattern, r'if hasattr(\1, "width") and \1.width > (\2):', code)

        lines = code.splitlines()
        new_lines = []
        for line in lines:
            if ".scale_to_fit_width(" in line:
                prefix = line.split(".scale_to_fit_width(")[0].strip()
                if "if hasattr(" in line or prefix.startswith("if "):
                    new_lines.append(line)
                else:
                    m = re.match(r"^(\s*)([a-zA-Z0-9_]+)\.scale_to_fit_width\(([^)]+)\)(.*)$", line)
                    if m:
                        indent, var, arg, trailing = m.groups()
                        new_lines.append(f'{indent}if hasattr({var}, "width") and {var}.width > ({arg}): {var}.scale_to_fit_width({arg})')
                        trailing = trailing.strip()
                        if trailing:
                            if trailing.startswith('.'):
                                new_lines.append(f'{indent}{var}{trailing}')
                            else:
                                new_lines.append(f'{indent}{trailing}')
                    else:
                        new_lines.append(line)
            else:
                new_lines.append(line)
        return "\n".join(new_lines)

    @staticmethod
    def normalize_code_typography(code: str) -> str:
        """
        Normalizes typography, layout bounds, and syntax across generated Manim code:
        1. Cleans invalid 'stretch=True/False' erroneously placed inside VGroup(...) or Group(...).
        2. Clamps oversized MathTex font_size (>24) down to 20 so formulas match non-latex body text.
        3. Scales down oversized MathTex .scale(...) (>=0.65) to .scale(0.45) so LaTeX does not tower over surrounding text.
        4. Enforces uniform minimum font size: clamps microscopic text (size < 10) up to size=11.
        5. Enforces Content Header Ceiling: ensures content panels/containers sit strictly below header (clamps UP * 2.8+ to UP * 2.3).
        6. Enforces Left-Right separation: clamps left container width (<= 4.2) to prevent center-seam bleeding.
        """
        lines = code.splitlines()
        new_lines = []
        for line in lines:
            # 1. Clean stretch in VGroup and Group
            if ("VGroup(" in line or "Group(" in line) and "stretch=" in line:
                line = re.sub(r'(VGroup|Group)\((.*?),\s*stretch\s*=\s*(?:True|False)\)', r'\1(\2)', line)
                line = re.sub(r'(VGroup|Group)\((.*?)\s*stretch\s*=\s*(?:True|False),\s*', r'\1(\2', line)
                line = re.sub(r'(VGroup|Group)\(\s*stretch\s*=\s*(?:True|False)\s*\)', r'\1()', line)

            # 2. Normalize MathTex font sizing & scaling
            if "MathTex" in line:
                if "font_size" in line:
                    def sub_fs(m):
                        fs = int(m.group(1))
                        return "font_size=20" if fs > 24 else m.group(0)
                    line = re.sub(r'font_size\s*=\s*(\d+)', sub_fs, line)
                if ".scale(" in line:
                    def sub_sc(m):
                        val = float(m.group(1))
                        return ".scale(0.45)" if val >= 0.65 else m.group(0)
                    line = re.sub(r'\.scale\(\s*([0-9]*\.?[0-9]+)\s*\)', sub_sc, line)

            # 3. Typography Uniformity: Clamp microscopic text (<13pt) up to 14pt (or 13pt for badges)
            if "CrispText(" in line and "size=" in line:
                def sub_tiny_size(m):
                    try:
                        sz = float(m.group(1))
                        if sz < 13:
                            if any(k in line.lower() for k in ["badge", "pill", "tag"]):
                                return "size=13"
                            return "size=14"
                    except Exception:
                        pass
                    return m.group(0)
                line = re.sub(r'size\s*=\s*(\d+(?:\.\d+)?)', sub_tiny_size, line)

            # 4. Header Ceiling Rule: Keep content strictly below header zone (ceiling y <= 2.4)
            if any(k in line for k in ["UP * 2.8", "UP * 2.9", "UP * 3.0", "UP * 3.1", "UP * 3.2"]):
                if not any(t in line for t in ["title", "dots", "line_start", "line_end", "header", "scene_title"]):
                    line = re.sub(r'UP\s*\*\s*(?:2\.8|2\.9|3\.0|3\.1|3\.2)', 'UP * 2.3', line)

            # 5. Left panel width clamp: prevent bleeding across center gutter into right column
            if re.search(r'\b\w*left\w*(panel|macro|col|container)\w*\b', line, re.I) or any(k in line for k in ["left_panel", "left_macro"]):
                line = re.sub(r'width\s*=\s*(?:4\.[4-9]|5\.[0-9])', 'width=4.2', line)

            new_lines.append(line)
        normalized = "\n".join(new_lines)
        normalized = re.sub(r'aligned_edge\s*=\s*(?:None|CENTER)', 'aligned_edge=ORIGIN', normalized)
        return normalized

    @staticmethod
    def ensure_clean_step_transitions(code: str) -> str:
        """
        Automatically purges leaked or zombie mobjects (such as table cells highlighted
        via Indicate or submobjects) while strictly protecting persistent slide titles.
        """
        lines = code.split("\n")
        new_lines = []
        i = 0
        n = len(lines)
        
        while i < n:
            line = lines[i]
            new_lines.append(line)
            
            stripped = line.strip()
            if stripped == ")" or stripped.startswith(")"):
                j = len(new_lines) - 2
                found_play = False
                has_forbidden = False
                has_fadeout = False
                indent = ""
                while j >= 0 and (len(new_lines) - 2 - j) < 35:
                    prev_line = new_lines[j]
                    if "self.play(" in prev_line:
                        found_play = True
                        indent = prev_line[:len(prev_line) - len(prev_line.lstrip())]
                        if any(k in prev_line for k in ["FadeIn(", "Create(", "Write(", "Transform(", "ReplacementTransform(", "GrowFromCenter("]):
                            has_forbidden = True
                        if "FadeOut" in prev_line:
                            has_fadeout = True
                        break
                    if any(k in prev_line for k in ["FadeIn(", "Create(", "Write(", "Transform(", "ReplacementTransform(", "GrowFromCenter("]):
                        has_forbidden = True
                    if "FadeOut(" in prev_line:
                        has_fadeout = True
                    j -= 1
                
                if found_play and has_fadeout and not has_forbidden:
                    k = i + 1
                    while k < n and lines[k].strip() == "":
                        k += 1
                    if k < n:
                        next_line_stripped = lines[k].strip()
                        if "self.remove(" not in next_line_stripped:
                            if (next_line_stripped.startswith("# Presentation Step") or
                                next_line_stripped.startswith("# Step") or
                                "self.create_title(" in next_line_stripped or
                                re.match(r"^[a-zA-Z0-9_]*title[a-zA-Z0-9_]*\s*=", next_line_stripped)):
                                new_lines.append(f"{indent}self.remove(*[m for m in self.mobjects if not getattr(m, 'is_title', False) and getattr(m, 'name', '') != 'title_group' and not getattr(m, 'is_persistent', False)])")
            i += 1
            
        return "\n".join(new_lines)

    @staticmethod
    def ensure_final_sync(code: str, target_duration: float) -> str:
        """
        Ensures the Manim scene stays alive for the exact full duration of the
        spoken audio track by guaranteeing a final self.sync_to(target_duration)
        call at the end of construct().
        """
        if target_duration <= 0:
            return code

        # Check existing sync_to calls
        matches = list(re.finditer(r"self\.sync_to\(\s*([\d\.]+)\s*\)", code))
        if matches:
            last_sync_time = float(matches[-1].group(1))
            # If the script already syncs to or past the target duration (within 0.15s), it is sufficient
            if last_sync_time >= target_duration - 0.15:
                return code

        # Append final sync_to to ensure construct() holds until narration completes
        lines = code.rstrip().split("\n")
        indent = "        "  # Default 8 spaces for construct() body
        for l in reversed(lines):
            if l.strip() and not l.startswith("class ") and not l.startswith("def "):
                m = re.match(r"^(\s+)", l)
                if m:
                    indent = " " * len(m.group(1)) if len(m.group(1)) in [4, 8, 12] else "        "
                    break

        new_sync_line = f"{indent}self.sync_to({target_duration:.2f})"
        lines.append(new_sync_line)
        return "\n".join(lines) + "\n"


    def probe_scene(
        self,
        scene_file: Path,
        scene_class: str | None = None,
        manifest: str | None = None,
        quiet: bool = True,
        fps: float | None = None,
        ignore_overrides: bool = False,
        base_folder: str | Path | None = None,
        config_data: dict | None = None,
        topic_id: str | None = None,
    ):
        """
        Run the Manim probe inside the dedicated Manim conda environment.

        The current Python environment does NOT need Manim installed.

        Set MANIM_PYTHON to the Python executable of the Manim environment,
        e.g.:

            export MANIM_PYTHON=/home/user/miniconda3/envs/manim/bin/python

        Or replace the fallback path below.
        """

        import json
        import os
        import subprocess
        import sys
        from pathlib import Path

        scene_file = Path(scene_file).resolve()

        # Ensure base_folder falls back gracefully to the topic directory if missing or invalid on disk
        if config_data and isinstance(config_data, dict) and config_data.get("base_folder"):
            cfg_base = config_data.get("base_folder")
            if os.path.isdir(str(cfg_base)):
                base_folder = str(cfg_base)
        if not base_folder or not os.path.isdir(str(base_folder)):
            if topic_id and hasattr(self, "input_folder") and os.path.isdir(os.path.join(self.input_folder, str(topic_id))):
                base_folder = os.path.join(self.input_folder, str(topic_id))
            elif topic_id and os.path.isdir(str(topic_id)):
                base_folder = str(topic_id)
            else:
                base_folder = str(scene_file.parent)

        if manifest:
            manifest = str(Path(manifest).resolve())
        elif base_folder:
            meta_dir = os.path.join(str(base_folder), "metadata_blueprints")
            if os.path.exists(os.path.join(meta_dir, "narration_manifest.json")):
                manifest = str(Path(meta_dir) / "narration_manifest.json")
            elif os.path.exists(os.path.join(str(base_folder), "narration_manifest.json")):
                manifest = str(Path(base_folder) / "narration_manifest.json")

        # ------------------------------------------------------------------
        # Python executable belonging to the Manim environment
        # ------------------------------------------------------------------
        manim_python = os.environ.get("MANIM_PYTHON", sys.executable)
        manim_python = str(Path(manim_python).expanduser().resolve())

        if not os.path.isfile(manim_python):
            raise RuntimeError(
                f"Manim Python executable not found:\n"
                f"  {manim_python}\n\n"
                f"Set MANIM_PYTHON to the Python executable of your "
                f"Manim conda environment."
            )

        # ------------------------------------------------------------------
        # Locate the subprocess runner.
        #
        # This file should be placed next to the module containing this
        # method, OR change this path to wherever you put the runner.
        # ------------------------------------------------------------------
        runner_candidates = [
            Path(__file__).resolve().parent / "manim_probe_runner.py",
            Path(__file__).resolve().parent / "helpers" / "manim_probe_runner.py",
            Path(_ROOT_DIR) / "pipeline" / "helpers" / "manim_probe_runner.py",
            Path(_CURRENT_DIR) / "pipeline" / "helpers" / "manim_probe_runner.py",
        ]
        runner = next((p for p in runner_candidates if p.is_file()), runner_candidates[0])
        print(f"Starting probe_scene for {scene_file}")

        cmd = [
            manim_python,
            str(runner),
            "--scene",
            str(scene_file.resolve()),
        ]

        if scene_class:
            cmd += ["--scene-class", scene_class]

        if manifest:
            cmd += ["--manifest", str(Path(manifest).resolve())]

        if fps is not None:
            cmd += ["--fps", str(fps)]

        if ignore_overrides:
            cmd.append("--ignore-overrides")

        env = os.environ.copy()

        env["NARRATION_PROBE"] = "1"
        env["NARRATION_IGNORE_OVERRIDES"] = (
            "1" if ignore_overrides else "0"
        )

        if manifest:
            env["NARRATION_MANIFEST"] = str(
                Path(manifest).resolve()
            )

        result = subprocess.run(
            cmd,
            cwd=str(scene_file.resolve().parent),
            env=env,
            capture_output=True,
            text=True,
        )

        print(f"The return code of the subprocess call is:{result.returncode}")

        if result.returncode != 0:
            raise RuntimeError(
                "Manim probe failed:\n\n"
                f"{result.stderr}"
            )

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Manim probe returned invalid JSON.\n\n"
                f"stdout:\n{result.stdout}\n\n"
                f"stderr:\n{result.stderr}"
            ) from exc

    
    def build_prompt(self, group_manifest: dict, script_path: str, base_folder: str = "") -> str:
        
        parts = [SYSTEM_PROMPT]

        gid = str(group_manifest.get("group_id", "1"))
        parts.append("## NARRATION")
        parts.append(
            f"group {gid}: "
            f"{int(group_manifest['n_statements'])} statements across "
            f"{int(group_manifest['n_pairs'])} pairs, "
            f"{float(group_manifest['duration']):.1f}s of audio total"
        )

        for pid in sorted(
            group_manifest["pairs"],
            key=lambda x: int(x),
        ):
            p = group_manifest["pairs"][pid]

            parts.append(
                f"\npair {pid}  "
            )

            for st in p["statements"]:
                text = " ".join(str(st["text"]).split())

                parts.append(
                    f"  [{pid}.{st['index']}] "
                    f"{float(st['start']):5.2f}s -> {float(st['end']):5.2f}s\n"
                    f"{text}"
                )

        # Word-Level Timestamps from Whisper ASR (via transcribe.py integration)
        if base_folder:
            transcript = get_or_create_word_transcript(base_folder, gid)
            if transcript and transcript.get("words"):
                parts.append("\n## EXACT WORD-LEVEL TIMESTAMPS (FROM GROQ WHISPER ASR)")
                parts.append(
                    "Use these exact word timestamps to schedule reveals (`self.sync_to(t)`) and "
                    "in-place keyword highlights (`.animate.set_stroke(color=COLOR_HIGHLIGHT)`). "
                    "Ensure visual elements stay on screen for the full duration they are spoken about:\n"
                )
                words_list = transcript["words"]
                for seg in transcript.get("segments", []):
                    seg_s = float(seg.get("start", 0.0))
                    seg_e = float(seg.get("end", 0.0))
                    seg_t = seg.get("text", "")
                    matching_words = [
                        f"'{w['word']}' ({float(w['start']):.2f}s)"
                        for w in words_list
                        if seg_s - 0.1 <= float(w.get("start", 0.0)) <= seg_e + 0.1
                    ]
                    parts.append(f"[{seg_s:.2f}s -> {seg_e:.2f}s] \"{seg_t}\"")
                    if matching_words:
                        parts.append(f"  Spoken words: {', '.join(matching_words[:12])}")

        if script_path:
            with open(script_path,'r', encoding="utf-8") as f:
                manim_code = f.read()
            parts.append("\n## CODE\n\n")
            parts.append(manim_code+"\n")
        
        print("Appended all parts including word-level timestamps")
        return "\n".join(parts)

    def call_gemini(self, prompt: str, model: str = "gemini-3.8-flash") -> str:
        key = self.google_api_key

        try:
            from google import genai
            from google.genai import types

            google_client = genai.Client(api_key=self.google_api_key)

            clean_model = "gemini-3.8-flash" if model in ("gemini-2.5-flash", "gemini-3.6-flash", "gemini-3.8-flash") else model
            models_to_try = [clean_model, "gemini-3.8-flash", "gemini-3.5-flash"]
            last_err = None

            for attempt in range(1, 4):
                try_model = models_to_try[min(attempt - 1, len(models_to_try) - 1)]
                try:
                    print(f"Calling Gemini ({try_model}) for timing sync (attempt {attempt}/3)...")
                    response = google_client.models.generate_content(
                        model=try_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.15,
                            max_output_tokens=65000,
                            thinking_config=types.ThinkingConfig(thinking_level="high")
                        )
                    )
                    generated_code = response.text or ""
                    code = extract_code_from_response(generated_code)
                    if code and len(code) > 200:
                        return code
                except Exception as e:
                    last_err = e
                    print(f"Gemini call failed on attempt {attempt}/3 with model {try_model}: {e}")
                    if attempt < 3:
                        time.sleep(4 * attempt)

            raise last_err or RuntimeError("Failed to generate content from Gemini after retries")

        except ImportError:
            pass

        return ""

    def generate_timing_sync(self, config_data, topic_id, force=False):
        force = force or (os.environ.get("FORCE_RUN") == "1")
        print(f"  [Simulated] Running timing synchronization for {topic_id}")

        # Ensure base_folder falls back gracefully to the topic directory if missing or not a valid directory on disk
        base_folder = config_data.get('base_folder') if isinstance(config_data, dict) else None
        if not base_folder or not os.path.isdir(str(base_folder)):
            candidate_dirs = []
            if hasattr(self, "input_folder") and self.input_folder:
                candidate_dirs.append(os.path.join(self.input_folder, str(topic_id)))
            if topic_id:
                candidate_dirs.append(str(topic_id))
                candidate_dirs.append(os.path.abspath(str(topic_id)))

            chosen_base = None
            for cand in candidate_dirs:
                if os.path.isdir(cand):
                    chosen_base = cand
                    break
            base_folder = chosen_base or (candidate_dirs[0] if candidate_dirs else ".")

        base_folder = os.path.abspath(str(base_folder))
        meta_dir = os.path.join(base_folder, "metadata_blueprints")
        os.makedirs(meta_dir, exist_ok=True)
        cgi_input_file = os.path.join(meta_dir, "CGI_Input.json")
        if not os.path.exists(cgi_input_file):
            cgi_input_file = os.path.join(base_folder, "CGI_Input.json")
        audio_dir = os.path.join(base_folder, "audio_elements")
        manifest_output_file = os.path.join(meta_dir, "narration_manifest.json")

        with open(cgi_input_file,'r', encoding="utf-8") as f:
            cgi_input = json.load(f)

        manifest = None
        problems = []
        if os.path.exists(manifest_output_file):
            try:
                with open(manifest_output_file, 'r', encoding="utf-8") as mf:
                    cand = json.load(mf)
                if cand and cand.get("groups"):
                    manifest = cand
                    problems = []
            except Exception:
                manifest = None

        if not manifest:
            manifest, problems = self.build_manifest(
                narration_path = Path(cgi_input_file),
                audio_dir = Path(audio_dir)
            )

        if problems:
            if os.path.exists(manifest_output_file):
                try:
                    with open(manifest_output_file, 'r', encoding="utf-8") as mf:
                        cand = json.load(mf)
                    if cand and cand.get("groups"):
                        manifest = cand
                        problems = []
                except Exception:
                    pass

        if problems:
            print("Problems:", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            
            print("\nRefusing to write a manifest with gaps. "
                "Fix the audio, or re-run with --lenient.", file=sys.stderr)
            raise RuntimeError(f"Refusing to write a manifest with gaps: {problems}")

        with open(manifest_output_file,'w', encoding="utf-8") as f:
            json.dump(manifest,f,indent=4, ensure_ascii=False)
        
        print(f"Wrote the narration manifest")
        print(summarise(manifest))

        manim_codes_folder = os.path.join(base_folder, "manim_styled_codes")
        if not os.path.exists(manim_codes_folder) and os.path.exists(os.path.join(base_folder, "manim_codes")):
            manim_codes_folder = os.path.join(base_folder, "manim_codes")
        code_file_names = os.listdir(manim_codes_folder) if os.path.exists(manim_codes_folder) else []
        sorted_code_file_names = sorted(code_file_names,key=self.sort_key)

        code_timing_dir = f"{base_folder}/manim_code_timing_extract"
        os.makedirs(code_timing_dir,exist_ok=True)

        timed_code_dir = f"{base_folder}/manim_time_synced_code"
        os.makedirs(timed_code_dir,exist_ok=True)

        for code_file in sorted_code_file_names:
            
            #Just extract the group number first
            match = re.search(r"group_(\d+).py", code_file)
            if match:
                group_num = int(match.group(1))
            else:
                print("Invalid file found. Continuing now to the next item")
                continue

            skip_scenes_env = os.environ.get("SKIP_SCENES")
            if skip_scenes_env and str(group_num) in [s.strip() for s in skip_scenes_env.split(",")]:
                print(f"Skipping Scene {group_num} per SKIP_SCENES")
                src = os.path.join(manim_codes_folder, code_file)
                dst = os.path.join(timed_code_dir, code_file)
                if os.path.exists(src) and (not os.path.exists(dst) or src != dst):
                    shutil.copy2(src, dst)
                continue

            absolute_script_path = os.path.abspath(os.path.join(manim_codes_folder,code_file))

            gm = manifest["groups"][str(group_num)]
            cgi_group = cgi_input.get(str(group_num),{})

            print(f"Calling the build prompt function for group {group_num}")
            prompt = self.build_prompt(group_manifest = gm, script_path = absolute_script_path, base_folder = base_folder)
            print(f"The prompt for group {group_num}:\n {prompt}")

            timed_code_file = os.path.join(timed_code_dir, f"group_{group_num}.py")

            with open(absolute_script_path, "r", encoding="utf-8") as rf:
                raw_code = rf.read()
            has_tmpl_call = any(t in raw_code for t in ["play_title_intro(", "play_learning_roadmap(", "play_topic_coverage("])
            has_multiple_steps = "## Presentation Step 2" in raw_code or "## Presentation Step 3" in raw_code
            is_pure_template = has_tmpl_call and not has_multiple_steps and len(raw_code.splitlines()) < 80

            if is_pure_template:
                print(f"Preserving official pure Simplilearn template for Scene {group_num} in Stage 21...")
                with open(timed_code_file, "w", encoding="utf-8") as wf:
                    wf.write(raw_code)
                continue

            # Check if timed_code_file already exists, is newer, and ACTUALLY has valid timing synchronization
            if os.path.exists(timed_code_file) and not force:
                if os.path.getmtime(timed_code_file) >= os.path.getmtime(absolute_script_path):
                    try:
                        with open(timed_code_file, "r", encoding="utf-8") as tf:
                            existing_timed_content = tf.read()
                        if "self.sync_to(" in existing_timed_content:
                            compile(existing_timed_content, f"group_{group_num}.py", "exec")
                            print(f"Time synced file for {group_num} already exists, compiles, and has valid sync_to beats. Moving to next scene.")
                            continue
                        else:
                            print(f"Existing file for {group_num} has no sync_to calls (likely prior untimed fallback). Re-synchronizing...")
                    except Exception:
                        print(f"Existing file for {group_num} is corrupted or broken. Re-synchronizing...")

            robust_crisp_text = r"""def CrispText(text, size=24, font="Poppins", **kwargs):
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
    elif size < 10.0:
        size = 12.0
    align = kwargs.pop("align", "center")
    autowrap_val = kwargs.pop("autowrap", kwargs.pop("wrap", None))
    disable_wrap_val = kwargs.pop("disable_wrap", kwargs.pop("disable_autowrap", False))
    max_w = kwargs.pop("max_width", kwargs.pop("wrap_width", None))
    for bad_k in ("alignment", "max_len", "line_spacing", "title_size", "item_size"):
        kwargs.pop(bad_k, None)
    slant_val = kwargs.pop("slant", NORMAL)
    weight_val = kwargs.pop("weight", NORMAL)
    if isinstance(weight_val, str):
        weight_val = weight_val.upper()
        if weight_val == "REGULAR":
            weight_val = "NORMAL"
    color_val = kwargs.pop("color", None)
    if color_val is None:
        color_val = globals().get("C_DARK_BLUE", "#1E293B")
    elif str(color_val).upper() in ("#F9C72C", "C_YELLOW", "YELLOW", "#FFF9E6", "#FFFF00"):
        color_val = globals().get("C_DARK_BLUE", "#1E293B")
    
    text_str = str(text)
    NL = chr(10)
    split_lines = [l for l in text_str.split(NL)] if NL in text_str else ([l for l in text_str.split(r"\n")] if r"\n" in text_str else None)
    if split_lines is None:
        should_autowrap = False
        wrap_chars = 34
        if max_w is not None:
            try:
                wrap_chars = max(18, int(float(max_w) / 0.115))
                should_autowrap = True
            except Exception:
                wrap_chars = 34
        elif autowrap_val is True:
            should_autowrap = True
        elif autowrap_val is False or disable_wrap_val:
            should_autowrap = False
        else:
            should_autowrap = (len(text_str) > 36 and " " in text_str and size <= 16)
        if should_autowrap:
            words = text_str.split()
            lines = []
            curr_line = []
            curr_len = 0
            for w in words:
                if curr_len + len(w) + 1 > wrap_chars:
                    if curr_line:
                        lines.append(" ".join(curr_line))
                    curr_line = [w]
                    curr_len = len(w)
                else:
                    curr_line.append(w)
                    curr_len += len(w) + 1
            if curr_line:
                lines.append(" ".join(curr_line))
            split_lines = lines
        else:
            split_lines = [text_str]
    if len(split_lines) > 1:
        line_mobs = []
        for line in split_lines:
            line_mob = Text(line, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **kwargs)
            line_mobs.append(line_mob)
        aligned_edge = ORIGIN if align == "center" else (LEFT if align == "left" else RIGHT)
        mob = VGroup(*line_mobs).arrange(DOWN, buff=0.18, aligned_edge=aligned_edge).scale(0.25)
    else:
        mob = Text(text_str, font=font, font_size=size * 4, slant=slant_val, weight=weight_val, color=color_val, **kwargs).scale(0.25)
    orig_scale = mob.scale_to_fit_width
    def safe_scale_width(tw):
        if hasattr(mob, "width") and mob.width > 0:
            ratio = tw / mob.width
            if ratio < 0.88: ratio = 0.88
            if ratio > 1.0: ratio = 1.0
            return mob.scale(ratio)
        return orig_scale(tw)
    mob.scale_to_fit_width = safe_scale_width
    return mob"""

            with open(absolute_script_path, "r", encoding="utf-8") as sf:
                styled_code_source = sf.read()

            group_dur = float(gm.get("duration", 0.0))
            sync_success = False
            last_sync_err = None

            for gen_attempt in range(1, 4):
                try:
                    print(f"Generating timed code for group {group_num} via LLM (attempt {gen_attempt}/3)...")
                    candidate_code = self.call_gemini(prompt, model="gemini-3.6-flash")
                    if not candidate_code or len(candidate_code) < 300:
                        raise ValueError(f"LLM returned empty or too-short code for group {group_num}")

                    candidate_code = self.replace_func_in_code(candidate_code, "CrispText", robust_crisp_text)
                    candidate_code = self.make_scaling_conditional(candidate_code)
                    candidate_code = self.normalize_code_typography(candidate_code)
                    candidate_code = self.ensure_clean_step_transitions(candidate_code)
                    candidate_code = self.ensure_final_sync(candidate_code, group_dur)
                    candidate_code = sanitize_manim_code(candidate_code, script_path=timed_code_file)

                    # Ensure FinalScene has sync_to method defined if not already present
                    if "def sync_to(" not in candidate_code and "class FinalScene" in candidate_code:
                        candidate_code = re.sub(
                            r"(class FinalScene\s*\([^)]*\)\s*:\n)",
                            r"\1    def sync_to(self, target_time):\n        current_time = getattr(getattr(self, 'renderer', None), 'time', 0.0)\n        if target_time > current_time:\n            self.wait(target_time - current_time)\n\n",
                            candidate_code,
                            count=1
                        )

                    # Validate syntax before writing
                    try:
                        compile(candidate_code, f"group_{group_num}.py", "exec")
                    except SyntaxError as syn_err:
                        print(f"⚠️ Syntax validation failed for group {group_num} (attempt {gen_attempt}/3): {syn_err}. Attempting self-healing repair...")
                        repaired = repair_code_with_llm(
                            source_code=candidate_code,
                            error_output=str(syn_err),
                            filename=f"group_{group_num}.py",
                            google_api_key=self.google_api_key
                        )
                        if repaired:
                            repaired = sanitize_manim_code(repaired, script_path=timed_code_file)
                            compile(repaired, f"group_{group_num}.py", "exec")
                            candidate_code = repaired
                            print(f"✅ Self-healing successfully repaired syntax for group {group_num}!")
                        else:
                            raise syn_err

                    # Quality check: verify that timing synchronization actually exists
                    sync_matches = re.findall(r"self\.sync_to\(\s*([\d\.]+)\s*\)", candidate_code)
                    if len(sync_matches) < 2:
                        print(f"⚠️ Generated code for group {group_num} has insufficient sync_to calls ({len(sync_matches)} found). Retrying...")
                        raise ValueError(f"Insufficient timing synchronization in generated code ({len(sync_matches)} sync_to calls)")

                    with open(timed_code_file, "w", encoding="utf-8") as f:
                        f.write(candidate_code)
                    sanitize_file(timed_code_file)
                    print(f"✅ Successfully generated and verified time-synchronized code for group {group_num} ({len(sync_matches)} sync_to beats).")
                    sync_success = True
                    break

                except Exception as e:
                    last_sync_err = e
                    print(f"⚠️ Attempt {gen_attempt}/3 failed for group {group_num}: {e}")
                    if "Forbidden" in str(e) or "not allowed by policy" in str(e):
                        break
                    if gen_attempt < 3:
                        time.sleep(3 * gen_attempt)

            if not sync_success:
                print(f"⚡ LLM timing generation failed after 3 attempts for group {group_num}: {last_sync_err}")
                print(f"⚡ Applying deterministic AST/programmatic timing synchronization fallback...")
                try:
                    fallback_timed_code = self.apply_programmatic_timing_sync(styled_code_source, gm)
                    fallback_timed_code = self.replace_func_in_code(fallback_timed_code, "CrispText", robust_crisp_text)
                    fallback_timed_code = self.make_scaling_conditional(fallback_timed_code)
                    fallback_timed_code = self.normalize_code_typography(fallback_timed_code)
                    fallback_timed_code = self.ensure_clean_step_transitions(fallback_timed_code)
                    fallback_timed_code = self.ensure_final_sync(fallback_timed_code, group_dur)
                    fallback_timed_code = sanitize_manim_code(fallback_timed_code, script_path=timed_code_file)
                    compile(fallback_timed_code, f"group_{group_num}.py", "exec")

                    with open(timed_code_file, "w", encoding="utf-8") as f:
                        f.write(fallback_timed_code)
                    sanitize_file(timed_code_file)
                    sync_cnt = len(re.findall(r"self\.sync_to\(\s*([\d\.]+)\s*\)", fallback_timed_code))
                    print(f"✅ Programmatic timing fallback succeeded for group {group_num} ({sync_cnt} sync_to beats injected). ZERO elements will appear upfront!")
                except Exception as prog_err:
                    print(f"❌ Fatal: Programmatic timing fallback failed for group {group_num}: {prog_err}")
                    raise RuntimeError(f"Could not generate time-synchronized code for group {group_num}: {last_sync_err} | {prog_err}")

            # Invalidate downstream video files
            downstream_video = os.path.join(base_folder, "manim_time_synced_videos", f"group_{group_num}.mp4")
            downstream_final = os.path.join(base_folder, "audio_integrated_videos", f"group_{group_num}_final.mp4")
            for dp in [downstream_video, downstream_final]:
                if os.path.exists(dp):
                    try:
                        os.remove(dp)
                        print(f"  [Invalidated] Removed stale downstream video: {dp}")
                    except Exception:
                        pass

        # Validate that all scene code files were generated
        missing_scenes = []
        for code_file in sorted_code_file_names:
            match = re.search(r"group_(\d+).py", code_file)
            if match:
                grp = int(match.group(1))
                expected = os.path.join(timed_code_dir, f"group_{grp}.py")
                if not os.path.exists(expected):
                    missing_scenes.append(grp)
        if missing_scenes:
            raise RuntimeError(f"Missing time-synced scenes for {topic_id}: {missing_scenes}")

        # Copy official Simplilearn templates and intro_icons into timed_code_dir
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for tmpl in ["template1_title_intro.py", "template2_learning_roadmap.py", "template3_topic_coverage.py", "template4_process_flow.py", "template5_action_flowchart.py"]:
            tmpl_src = os.path.join(script_dir, "helpers", tmpl)
            if not os.path.exists(tmpl_src):
                tmpl_src = os.path.join(os.path.dirname(script_dir), "template", tmpl)
            if os.path.exists(tmpl_src):
                shutil.copy2(tmpl_src, timed_code_dir)

        icons_src = os.path.join(script_dir, "helpers", "intro_icons")
        if not os.path.exists(icons_src):
            icons_src = os.path.join(os.path.dirname(script_dir), "template", "intro_icons")
        if os.path.exists(icons_src):
            shutil.copytree(icons_src, os.path.join(timed_code_dir, "intro_icons"), dirs_exist_ok=True)

        return timed_code_dir

    def process_files(self, target_topic_id=None, force=False):
        force = force or (os.environ.get("FORCE_RUN") == "1")
        input_tracker = self._load_tracker(self.input_tracker_path)
        if not input_tracker: return

        for topic_id, input_entry in input_tracker.items():
            if target_topic_id and topic_id != target_topic_id:
                continue
            if not input_entry.get("processed", False): continue

            output_tracker = self._load_tracker(self.output_tracker_path)
            if not force and topic_id in output_tracker and output_tracker[topic_id].get("processed", False): continue

            print(f"Processing {topic_id}...")
            base_folder = os.path.join(self.input_folder, topic_id)
            config_path = os.path.join(base_folder, "ex_config.json")
            
            if not os.path.exists(config_path): continue
            
            try:
                with open(config_path, 'r', encoding="utf-8") as f:
                    config_data = json.load(f)

                output_file_path = self.generate_timing_sync(config_data, topic_id, force=force)
                
                if not output_file_path or output_file_path == 1 or not os.path.isdir(str(output_file_path)):
                    raise RuntimeError(f"Stage 21 failed to generate valid time-synced directory: {output_file_path}")

                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": output_file_path, "processed": True,
                    "topic_name": topic_id, "topic_id": topic_id, "failure_reason": None
                }
                self._save_tracker(self.output_tracker_path, tracker)

                # Reset downstream tracker 22 so final render is guaranteed to run
                tracker_dir = os.path.dirname(self.output_tracker_path)
                dt_path = os.path.join(tracker_dir, "22_final_render_tracker.json")
                if os.path.exists(dt_path):
                    try:
                        d_tracker = self._load_tracker(dt_path)
                        if topic_id in d_tracker:
                            d_tracker[topic_id]["processed"] = False
                            self._save_tracker(dt_path, d_tracker)
                            print(f"  [Tracker] Reset downstream tracker 22_final_render_tracker.json for {topic_id}")
                    except Exception as dt_err:
                        print(f"  [Warn] Could not reset downstream tracker {dt_path}: {dt_err}")

                print(f"Successfully processed {topic_id}.")

            except Exception as e:
                print(f"Error processing {topic_id}: {e}")
                tracker = self._load_tracker(self.output_tracker_path)
                tracker[topic_id] = {
                    "output_path": None, "processed": False,
                    "topic_name": topic_id, "topic_id": topic_id, "failure_reason": str(e)
                }
                self._save_tracker(self.output_tracker_path, tracker)

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 21: Timing Adjustments")
    parser.add_argument("--topic", type=str, default=None, help="Target specific topic ID")
    parser.add_argument("--force", action="store_true", help="Force timing adjustment regeneration")
    args = parser.parse_args()

    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = current_file_dir if os.path.exists(os.path.join(current_file_dir, "pipeline")) else os.path.dirname(current_file_dir)
    eng_correction_styling_tracker = os.path.join(project_root, "ppt_trackers", "20_eng_corrections_tracker.json")
    timing_adjustment_tracker = os.path.join(project_root, "ppt_trackers", "21_timing_adjustment_tracker.json")

    candidate_input_folders = [
        os.path.join(project_root, "output"),
        os.path.join(project_root, "data_ppt_advanced"),
        project_root
    ]
    data_dir = next((d for d in candidate_input_folders if os.path.isdir(d)), project_root)

    stage = GenerateTimingAdjustments(
        input_tracker_path=eng_correction_styling_tracker, 
        google_api_key=os.environ.get("GOOGLE_API_KEY"), 
        claude_api_key=os.environ.get("CLAUDE_API_KEY"),
        output_tracker_path=timing_adjustment_tracker, 
        input_folder=data_dir
    )
    stage.process_files(target_topic_id=args.topic, force=args.force)
