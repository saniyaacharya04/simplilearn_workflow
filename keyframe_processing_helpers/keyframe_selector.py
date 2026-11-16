"""
keyframe_selector.py  (Phase 2 selection -- v2, Phase 0.1 rewrite)

Decides which snapshot frames get sent to the VLM.

v1 regex-parsed the report's English issue strings back into signatures and
matched timestamps to frames within a tolerance. v2 consumes the STRUCTURED
report from structured_report.py, where every issue already carries the
frame number of its worst occurrence and signature dedup has already been
applied -- so selection reduces to:

  1. Error frames: group each section's issues by their `frame` field
     (one VLM image covers all issues that peak on that frame).
  2. Aesthetic frame: the last snapshot frame of each section
     (`frame_range[1]`) -- the settled composition right before the next
     section begins. If it coincides with an error frame, that frame is
     just tagged "error+aesthetic".

Manifest shape is unchanged from v1 (extract_vlm_keyframes.py compatible),
except `issues` entries are structured dicts (with .description) instead of
plain strings.
"""

import json


def build_manifest(full_report_path, aesthetic_backoff_frames=4, transition_ignore_frames=6, entrance_ignore_frames=4):
    """
    aesthetic_backoff_frames: Steps back from the end to find a completely settled composition.
    transition_ignore_frames: Drops any 'errors' reported during the final N frames as things exit.
    entrance_ignore_frames:   Drops any 'errors' reported during the initial N frames as things enter.
    """
    with open(full_report_path,"r", encoding="utf-8") as f:
        report = json.load(f)

    manifest = {}
    for key, sec in report.items():
        frame_range = sec.get("frame_range")
        start_frame = frame_range[0] if frame_range else 0
        end_frame = frame_range[1] if frame_range else 999999
        
        clusters = {}  # frame_number -> {"timestamp":, "issues": [...]}
        for issue in sec.get("issues", []):
            fn = issue.get("frame")
            
            # --- FILTER TRANSITION & ENTRANCE ERRORS ---
            # If the error happens right at the beginning or end of the section,
            # it is in-flight animation (FadeIn, Transform, FadeOut) rather than static layout.
            if fn is not None and fn >= (end_frame - transition_ignore_frames):
                print(f"  [Info] Ignoring {issue.get('type')} issue at frame {fn} (exit transition phase)")
                continue
            if fn is not None and fn <= (start_frame + entrance_ignore_frames):
                print(f"  [Info] Ignoring {issue.get('type')} issue at frame {fn} (entrance transition phase)")
                continue
            # ----------------------------------------------
            
            c = clusters.setdefault(fn, {"timestamp": issue.get("timestamp", 0.0),
                                         "issues": []})
            c["issues"].append(issue)

        frames = [
            {"frame_number": fn, "timestamp": c["timestamp"],
             "issues": c["issues"], "reason": "error"}
            for fn, c in sorted(clusters.items(),
                                key=lambda kv: (kv[0] is None, kv[0]))
        ]

        if frame_range:
            # Back off from the very last frame for the aesthetic shot
            aesthetic_frame = max(frame_range[0], frame_range[1] - aesthetic_backoff_frames)
            
            hit = next((f for f in frames if f["frame_number"] == aesthetic_frame), None)
            if hit:
                hit["reason"] = "error+aesthetic"
            else:
                window = sec.get("window") or [0.0, 0.0]
                fps_assumption = 15.0  # based on your prompt
                safe_timestamp = max(window[0], window[1] - (aesthetic_backoff_frames / fps_assumption))
                
                frames.append({"frame_number": aesthetic_frame,
                               "timestamp": safe_timestamp,
                               "issues": [], "reason": "aesthetic"})

        manifest[key] = {
            "scene": sec.get("scene"),
            "section": sec.get("section"),
            "window": sec.get("window"),
            "frames": frames,
        }

    return manifest

if __name__ == "__main__":
    import sys
    print(json.dumps(build_manifest(sys.argv[1]), indent=2, ensure_ascii=False))