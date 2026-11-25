import os, sys
_cur_dir = os.path.dirname(os.path.abspath(__file__))
if _cur_dir not in sys.path:
    sys.path.insert(0, _cur_dir)
from manim import *
from template2_learning_roadmap import play_learning_roadmap

class FinalScene(Scene):
    def construct(self):
        play_learning_roadmap(
            self,
            bullets=[
                "Describe Core Architectural Components (Perception, Memory, Reasoning, Action)",
                "Explain the Agent-Environment Continuous Feedback Loop",
                "Walk Through the Perceive-Reason-Act (PRA) Execution Cycle",
                "Identify the Three Main Agent Paradigms (Reactive, Goal, Utility)",
                "Visualize the End-to-End Operational Workflow & Human Escalation"
            ],
            header_text="By the end of this topic, you will be able to:",
            bullet_durations=[5.00, 6.10, 5.80, 5.00, 6.00],
            hold_duration=2.20,
        )
