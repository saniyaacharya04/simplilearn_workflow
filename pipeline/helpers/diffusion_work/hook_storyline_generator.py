import json
import os
import glob
import fcntl
import time
import re
import google.generativeai as genai
from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv()

class HookStorylineCreator:
    """
    Class definition. Identify all unprocessed inputs and pass them through the fit_scene() method.
    """

    def __init__(self, google_api_key, claude_api_key):
        self.google_api_key = google_api_key
        self.claude_api_key = claude_api_key
    

    def create_hook_storyline(self, case_study_plan, reference_storyboard, color_palette, hook_index):
        """
        Placeholder for the ideate_hook logic.
        This would typically call the LLM APIs using the API keys and prompts.
        """
        
        #model_vendor = "google"
        #hook_model_name = "gemini-3.8-flash"
        model_vendor = "claude"
        hook_model_name = "claude-haiku-4-5-20251001"

        if model_vendor=="google":
            genai.configure(api_key=self.google_api_key)
        elif model_vendor == "claude":
            client = Anthropic(api_key=self.claude_api_key,timeout=800)

        def remove_code_fences(text: str) -> str:
            """
            Removes ```json ... ``` or ``` ... ``` wrappers
            from the beginning and end of a string.
            """
            return re.sub(
                r"^\s*```(?:json)?\s*\n?(.*?)\n?```\s*$",
                r"\1",
                text,
                flags=re.DOTALL
            )

        
        case_plot_creation_prompt = """
        # ROLE
        You are a Cinematic Art Director and Lead Storyboarder. Your job is to take a high-level video hook concept and expand it into a detailed, meticulously timed 3-act beat sheet for a 3D-animated diffusion clip (Pixar-style). 

        # OBJECTIVE
        Expand the provided `Hook Segment` into exactly THREE acts (each lasting 13–14.5 seconds). 
        Because the core plot is already provided, your primary focus is on pacing, cinematic framing, continuity, and perfectly synchronizing the visual actions with the voiceover. Act 3 must end by leading seamlessly into the provided `Core Video Storyboard`.

        ---
        # INPUTS
        You will be provided with:
        1. **Hook Segment:** The core dilemma, visual action, and base voiceover to adapt.
        2. **Core Video Storyboard:** The theoretical video that plays immediately after this hook. (Use this to contextualize the Act 3 transition).
        3. **Color Palette:** The lighting and color mood for the scene.

        ---
        # STRICT CONTINUITY & PACING RULES

        1. AUDIO-VISUAL SYNC & DYNAMIC SCOPE:
        - Break each Act down into 2 to 3 "Beats". 
        - The visual scope MUST dynamically match the narrative scope of the voiceover. If the audio references multiple locations, large-scale systems, or external elements, the camera must reveal them (e.g., via cutaways, wide environmental shots, or integrated tech/screens). Do not trap characters in a static framing if the audio implies a wider world.
        - LITERAL CHOREOGRAPHY: The visual action must strictly and chronologically map to the spoken words. If the audio lists three specific things (e.g., "from X, to Y, to Z"), the camera and character actions MUST physically handle or reveal X, then Y, then Z, perfectly timed to those exact verbal cues.
        - You may slightly edit the provided base voiceover to ensure it flows naturally, but you MUST keep its original intent and end with the exact `transition_to_theory` line.
        - Please do not repeat any audio across beats. If there is no room to accommodate 2 or more beats, you dont need to force fit.

        2. CONSTANT MOTION (ACTION DENSITY):
        - Every 3–5 seconds (every beat) must contain a new visual change, physical interaction, or camera cut. No static talking heads. The characters must be actively handling the physical objects described in the hook.
        - Make sure you have 10-15 words representing the physical action for every 5 seconds of voiceover - helps align the duration with the pace of speaking

        3. CONTINUITY LOCKS (NO MAGIC):
        - Object Permanence: Objects do not appear or disappear. If a character needs an object in Act 2, they must have brought it in Act 1, or visibly pick it up on-screen.
        - Character Origin: Characters cannot materialize from inside containers or thin air. They must walk in or already be present.
        - Number/State Lock: If Act 1 establishes 3 boxes, Act 2 must have 3 boxes unless one is physically removed.
        - Hand-offs: If an object is passed, explicitly state who holds it, when it leaves their hand, and who catches it.

        4. CINEMATIC 3D STYLE:
        - Describe realistic Pixar-style 3D environments (depth of field, physical textures, foreground/background layers).
        - NO floating text, UI screens, or abstract math symbols unless explicitly stated as a physical prop (e.g., a printed sign).
        - Translate the provided `Color Palette` into natural lighting/environmental descriptions (e.g., "warm amber warehouse lighting" - NEVER use hex codes in the output).

        5. GRANULAR MICRO-ACTIONS (HIGH DETAIL):
        - Do not just say a character "does" something 
        - Describe the exact mechanics of the movement: the specific grip of the hand, the shift in posture or facial expression, where the eyes are tracking, and how the physical weight/texture of the object reacts to them. Downstream animators need exact micro-level blocking.

        6. PROFESSIONAL AUTHENTICITY:
        - Props and interactions must reflect authentic, industry-standard practices for the given scenario. 
        - Avoid cheap, DIY, or overly simplistic metaphors (e.g., do not use basic stickers, craft paper, or simple cardboard to represent high-stakes enterprise or logistical tasks). Equip characters with realistic, specialized tools, hardware, and physical systems appropriate for a professional setting.

        7. HYPER-DETAILED MATERIALITY:
        - Describe the precise 3D physical properties of every focal prop. 
        - Detail the textures (matte, glossy, brushed, woven), weight, and how the materials interact with the scene's lighting (reflections, LED glows, deep shadows). 
        - Describe how these physical properties react to character handling (e.g., physical resistance, the satisfying snap of a lock, the heavy thud of an item on a desk).

        ----
        # OUTPUT FORMAT (STRICT JSON)
        To ensure the output is easily parsed by code, you MUST format your entire response as a single, valid JSON object. Do not include any markdown formatting (like ```json), introductions, or concluding text outside of the JSON structure.

        {{
            "diffusion_clip": {{
                "act_1": {{
                "title": "The Setup",
                "timestamp_range": "0:00 - 0:14",
                "goal": "Establish the environment, the characters, and the physical items representing the data/math.",
                "beats": [
                    {{
                        "beat_number": 1,
                        "timestamp": "0:00 - 0:05",
                        "visual": "[Strict chronological choreography mapping exactly to the audio cues. Include: 1) Camera framing that tracks the spoken subject, 2) Step-by-step kinetic micro-actions, and 3) Authentic materiality (textures, weight, light reflections).]",
                        "audio": "[Exact spoken dialogue/VO]"
                    }},
                    {{
                        "beat_number": 2,
                        "timestamp": "0:05 - 0:10",
                        "visual": "[Describe the camera cut or next action]",
                        "audio": "[Exact spoken dialogue/VO]"
                    }},
                    {{
                        "beat_number": 3,
                        "timestamp": "0:10 - 0:14",
                        "visual": "[Action escalating the dilemma]",
                        "audio": "[Exact spoken dialogue/VO]"
                    }}
                ]
                }},
                "act_2": {{
                "title": "The Escalation",
                "timestamp_range": "0:14 - 0:28",
                "goal": "A camera cut initiates this act. Deepen the physical sorting/arranging problem.",
                "beats": [
                    {{
                        "beat_number": 1,
                        "timestamp": "0:14 - 0:20",
                        "visual": "[Strict chronological choreography mapping exactly to the audio cues. Include: 1) Camera framing that tracks the spoken subject, 2) Step-by-step kinetic micro-actions, and 3) Authentic materiality (textures, weight, light reflections).]",
                        "audio": "[Exact spoken dialogue/VO]"
                    }},
                    {{
                        "beat_number": 2,
                        "timestamp": "0:20 - 0:28",
                        "visual": "[Visual action]",
                        "audio": "[Exact spoken dialogue/VO]"
                    }},
                    ...
                ]
                }},
                "act_3": {{
                    "title": "The Transition",
                    "timestamp_range": "0:28 - 0:42",
                    "goal": "Bring the physical dilemma to its peak and deliver the final transition line. Characters MUST remain completely immersed in their task—no looking at the camera, no gesturing to the viewer, and no breaking the fourth wall.",
                    "beats": [
                        {{
                            "beat_number": 1,
                            "timestamp": "0:28 - 0:35",
                            "visual": "[Strict chronological choreography mapping exactly to the audio cues. Include: 1) Camera framing that tracks the spoken subject, 2) Step-by-step kinetic micro-actions, and 3) Authentic materiality (textures, weight, light reflections).]",
                            "audio": "[Exact spoken dialogue/VO]"
                        }},
                        {{
                            "beat_number": 2,
                            "timestamp": "0:35 - 0:42",
                            "visual": "[Final cinematic framing. Characters continue working in-world. Describe a purely cinematic camera transition (e.g., pushing in extreme close-up on the physical object, a match-cut, or passing through a physical element) to tee up the theoretical video without the characters signaling the audience.]",
                            "audio": "[Exact transition_to_theory line]"
                        }},
                        ...
                    ]
                }}
            }}
        }}

        ---
        # INPUT DATA
        **Hook Segment:**
        {hook_segment}

        **Core Video Storyboard:**
        {video_storyboard}

        **Color Palette:**
        {color_palette}

        **Overarching Goal:**
        {goal}

        **Anchor Characters:**
        {characters}

        **The Context:**
        {context}
        """

        hook_segment = case_study_plan["hooks"][hook_index]
        goal = case_study_plan["metadata"]["overarching_goal"]
        characters = case_study_plan["metadata"]["anchor_characters"]
        context = case_study_plan["metadata"]["core_visual_metaphor"]
        topic_name = case_study_plan["metadata"]["course_topic"]
        video_number = hook_segment["video_number"]

        formatted_hook_system_prompt = case_plot_creation_prompt.format(
            hook_segment=hook_segment,
            video_storyboard=reference_storyboard,
            color_palette=color_palette,
            goal=goal,
            characters=characters,
            context=context
        )
    

        raw_storyline_file = f"./Comb_case/storyline_{topic_name}_{video_number}_{hook_model_name}.txt"
        storyline_file = f"./Comb_case/storyline_{topic_name}_{video_number}_{hook_model_name}.json"
        
        full_prompt = f"{formatted_hook_system_prompt}"
        print(f"Full hook prompt:\n{full_prompt}")

        ch = input("Continue? (y/n)")
        if ch=="n":
            exit(1)

        if not os.path.exists(raw_storyline_file):
            if model_vendor == "google":
                print(f"Using google's model of {hook_model_name}")
                full_prompt = formatted_hook_system_prompt
                model_variant = f"models/{hook_model_name}"
                model = genai.GenerativeModel(model_variant)

                response = model.generate_content(
                    contents=[{"role": "user", "parts": [full_prompt]}],
                    generation_config=genai.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=30000
                    )
                )
                generated_result = response.text
            elif model_vendor == "claude":
                print(f"Using claude's model of {hook_model_name}")
                message = client.messages.create(
                    max_tokens=30000,
                    messages=[
                    {"role": "user", "content": formatted_hook_system_prompt},
                    ],
                    model=hook_model_name,
                    temperature=0.7
                )
                generated_result = message.content[0].text
            print(f"Generated result:{generated_result}")
            with open(raw_storyline_file,'w') as f:
                f.write(generated_result)
        else:
            with open(raw_storyline_file,'r') as f:
                generated_result = f.read()

        sanitized_result = remove_code_fences(generated_result)
        story_parameters = json.loads(sanitized_result)

        #print(f"Parsed story parameters: {story_parameters}")

        with open(storyline_file,'w') as f:
            json.dump(story_parameters,f,indent=4)
        
        return storyline_file

if __name__ == "__main__":
    topic_name = "Set Theory"
    hook_model_name = "gemini-3.8-flash"
    case_study_plan_file = f"./Comb_case/raw_parameters_{topic_name}_{hook_model_name}.json"
    with open(case_study_plan_file, 'r') as f:
        case_study_plan = json.load(f)

    reference_storyboard_file = f"./instructions_raw_{hook_model_name}.txt"
    if not os.path.exists(reference_storyboard_file):
        reference_storyboard_file = "./instructions_raw.txt"
    with open(reference_storyboard_file, 'r') as f:
        reference_storyboard = f.read()

    color_palette_file = "./image_color_palette_file.txt"
    with open(color_palette_file, 'r') as f:
        color_palette = f.read().strip()

    generator = HookStorylineCreator(google_api_key=os.environ.get("GOOGLE_API_KEY"), claude_api_key=os.environ.get("CLAUDE_API_KEY"))
    generator.create_hook_storyline(case_study_plan=case_study_plan["case_study_plan"], reference_storyboard=reference_storyboard, color_palette=color_palette, hook_index=2)