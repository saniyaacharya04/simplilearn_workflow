import os, sys
_cur_dir = os.path.dirname(os.path.abspath(__file__))
if _cur_dir not in sys.path:
    sys.path.insert(0, _cur_dir)
from manim import *
from template1_title_intro import play_title_intro

class FinalScene(Scene):
    def construct(self):
        play_title_intro(
            self,
            topic_title="Topic Introduction:\nTypes and Architectures of AI Agents",
            course_name="Artificial Intelligence and Agentic Workflows",
            duration=7.86,
        )
