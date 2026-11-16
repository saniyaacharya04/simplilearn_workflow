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

    def setup(self):

        super().setup()
        
        # Get the file path of the concrete scene class that inherits from InstrumentedScene
        scene_file_path = inspect.getfile(self.__class__)
        
        # Extract the filename (e.g., "group_1.py")
        scene_filename = os.path.basename(scene_file_path)
        
        # Use regex to find the group number
        match = re.match(r"group_(\d+)\.py", scene_filename)
        group_number = match.group(1) if match else "unknown"
        
        base_output_dir = (
            Path.cwd().parent
            / "correction_insights"
        )
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

        self.snapshot_manager.capture(
            self
        )

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

        self.snapshot_manager.capture(
            self
        )

        return result