#!/usr/bin/env python3
"""
Pipeline Outputs Exporter / Deliverables Sync
Exports final videos, screenshots, storyboards, and presentation assets
into the designated deliverables directory.
"""

import os
import sys
import shutil
import argparse
from pathlib import Path


def copy_deliverables(source_dir: Path, dest_dir: Path, topic: str = None):
    source_dir = Path(source_dir).resolve()
    dest_dir = Path(dest_dir).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    topics = [topic] if topic else [p.name for p in source_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]

    for t in topics:
        src_topic_path = source_dir / t
        if not src_topic_path.exists():
            continue
        dst_topic_path = dest_dir / t
        dst_topic_path.mkdir(parents=True, exist_ok=True)
        print(f"📦 Syncing deliverables for: {t} -> {dst_topic_path}")

        # Copy final videos, images, schemas
        for pattern in ["*.mp4", "*.json", "*.txt", "*.png"]:
            for f in src_topic_path.glob(pattern):
                shutil.copy2(f, dst_topic_path / f.name)

        # Copy subdirectories if present
        for sub in ["manim_videos", "images", "audio_integrated_videos", "audio_elements"]:
            sub_src = src_topic_path / sub
            if sub_src.exists() and sub_src.is_dir():
                sub_dst = dst_topic_path / sub
                sub_dst.mkdir(parents=True, exist_ok=True)
                for item in sub_src.iterdir():
                    if item.is_file():
                        shutil.copy2(item, sub_dst / item.name)


def main():
    default_src = Path(__file__).resolve().parent.parent / "output"
    default_dst = Path(__file__).resolve().parent.parent / "simplilearn_output_standard"

    parser = argparse.ArgumentParser(
        description="Unified Presentation Workflow Deliverables Exporter."
    )
    parser.add_argument(
        "--src",
        type=str,
        default=str(default_src),
        help="Path to source output directory"
    )
    parser.add_argument(
        "--dest",
        type=str,
        default=str(default_dst),
        help="Path to output export destination"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Specific topic ID to export (optional)"
    )

    args = parser.parse_args()
    copy_deliverables(Path(args.src), Path(args.dest), topic=args.topic)


if __name__ == "__main__":
    main()
