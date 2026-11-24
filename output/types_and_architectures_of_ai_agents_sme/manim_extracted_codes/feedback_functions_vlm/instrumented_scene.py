from manim import *
import inspect
import os
import re

from pathlib import Path
import sys

CURRENT_DIR = Path(__file__).resolve().parent

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from scene_snapshot import SceneSnapshotManager



class InstrumentedScene(Scene):

    def __init__(self, *args, **kwargs):
        self.snapshot_manager = None
        super().__init__(*args, **kwargs)

    def setup(self):

        super().setup()
        
        # Get the file path of the concrete scene class that inherits from InstrumentedScene
        scene_file_path = inspect.getfile(self.__class__)
        
        # Extract the filename (e.g., "group_1.py")
        scene_filename = os.path.basename(scene_file_path)
        
        # Use regex to find the group number
        match = re.match(r"group_(\d+)\.py", scene_filename)
        group_number = match.group(1) if match else "unknown"
        
        # 1. Environment variable override
        insights_env = os.environ.get("CORRECTION_INSIGHTS_VLM_DIR")
        if insights_env:
            base_output_dir = Path(insights_env)
        else:
            # 2. Walk up directory tree from the scene file to find ex_config.json
            scene_path = Path(scene_file_path).resolve()
            topic_dir = None
            curr = scene_path.parent
            while curr != curr.parent:
                if (curr / "ex_config.json").exists():
                    topic_dir = curr
                    break
                curr = curr.parent

            if topic_dir:
                base_output_dir = topic_dir / "correction_insights_vlm"
            elif (Path.cwd().parent / "ex_config.json").exists():
                base_output_dir = Path.cwd().parent / "correction_insights_vlm"
            elif (Path.cwd() / "ex_config.json").exists():
                base_output_dir = Path.cwd() / "correction_insights_vlm"
            elif Path.cwd().name in ["manim_codes", "codes", "manim_raw_videos", "manim_videos", "manim_extracted_codes", "manim_styled_codes"]:
                base_output_dir = Path.cwd().parent / "correction_insights_vlm"
            else:
                base_output_dir = Path.cwd() / "output" / "correction_insights_vlm"

        base_output_dir.mkdir(parents=True, exist_ok=True)

        dynamic_output_dir = (
            base_output_dir
            / f"scene_{group_number}"
        )

        self.snapshot_manager = SceneSnapshotManager(output_dir=dynamic_output_dir)

    def play(
        self,
        *args,
        **kwargs
    ):

        result = super().play(
            *args,
            **kwargs
        )

        if getattr(self, "snapshot_manager", None) is not None:
            try:
                self.snapshot_manager.capture(self)
            except Exception:
                pass

        return result

    def wait(
        self,
        *args,
        **kwargs
    ):

        result = super().wait(
            *args,
            **kwargs
        )

        if getattr(self, "snapshot_manager", None) is not None:
            try:
                self.snapshot_manager.capture(self)
            except Exception:
                pass

        return result