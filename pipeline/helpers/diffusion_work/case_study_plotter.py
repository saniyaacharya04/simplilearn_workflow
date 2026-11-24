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

class CasePlotter:
    """
    Class definition. Identify all unprocessed inputs and pass them through the fit_scene() method.
    """

    def __init__(self, google_api_key, claude_api_key):
        self.google_api_key = google_api_key
        self.claude_api_key = claude_api_key
    

    def ideate_case(self, file_content, topic_name, target_audience):
        """
        Placeholder for the ideate_hook logic.
        This would typically call the LLM APIs using the API keys and prompts.
        """
        
        model_vendor = "google"
        hook_model_name = "gemini-3.5-flash"

        if model_vendor=="google":
            genai.configure(api_key=self.google_api_key)
        elif model_vendor == "claude":
            client = Anthropic(api_key=self.claude_api_key)

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
        Role: You are an elite Educational Creative Director and Lead Scriptwriter specializing in creating highly engaging, narrative-driven explainer videos.

        Objective: I will provide you with the raw text of an educational module. Your task is to design a continuous case study that will serve as the foundation for 30-40 second video hooks (upfront diffusion clips) for each video in the module. These hooks will seamlessly transition into the theoretical video content.

        ---
        ### INPUT DATA:
        - **Module Topic:** {Module_topic}
        - **Raw Module Content:** 
        {Document}

        ---
        ### CREATIVE & NARRATIVE CONSTRAINTS:

        1. Target Audience & Relatability (The Scenario):
        - The audience consists of {target_audience} 
        - However, the plot should NOT be overly technical. Instead, use relatable business, social, logistical, marketplace or healthcare scenarios. 
        - The goal is to translate abstract academic concepts into everyday, tangible problem-solving situations that this audience can easily grasp and appreciate.

        2. Visual Style (Tangible & Character-Driven):
        - The visual direction must focus on character-driven actions and physical environments. 
        - DO NOT rely on textual typography, floating UI screens, or purely abstract motion graphics. 
        - Abstract concepts must be represented by physical, tangible objects that characters can hold, move, or sort (e.g., using shipping containers, colored folders, physical conveyor belts, or groups of people).
        - Crucial: While abstract concepts must be physical objects (bins, clipboards, lanyards, conveyor belts), the actions must make realistic business sense.
        - Do NOT force characters into absurd or illogical actions just to map directly to a concept (e.g., do NOT hand a client an "empty box" to represent an empty set, and do NOT literally herd human guests into hula-hoops)

        3. Anchor Entities (The Protagonists):
        - Create 1-2 persistent anchor characters (e.g., a stressed logistics manager and an eager intern, or an event planner).
        - These characters must face an overarching, relatable project or dilemma that spans the entire module.

        4. Episodic Independence (CRUCIAL):
        - While the hooks share the same characters and overarching project, EACH hook must stand completely on its own.
        - DO NOT use phrases like "Welcome back," "Last time," or "As we saw before."
        - A viewer should be able to watch Video 4 without having seen Videos 1-3 and understand exactly what the immediate micro-problem is.

        5. Hook Mechanics & Pacing:
        - Each hook script should translate to exactly 30-40 seconds of screen time (approx. 55-75 words of Voiceover).
        - Structure of each hook:
        a) The Micro-Dilemma: A sudden, specific problem arises in the project.
        b) The Visual Action: Characters interact with their environment and tangible objects to visualize the problem. The interaction must be a highly practical, realistic logistical action (e.g., organizing badges, sorting inventory bins, reviewing color-coded shipping tags)
        c) The Transition: A concluding sentence that naturally pivots from the narrative dilemma to the actual course content.

        ---
        ### OUTPUT FORMAT (STRICT JSON):
        To ensure the output is easily parsed by code, you MUST format your entire response as a single, valid JSON object. Do not include any markdown formatting (like ```json), introduction, or conclusion text outside of the JSON structure.

        {{
        "case_study_plan": {{
            "metadata": {{
            "course_topic": "[Extract Topic Name]",
            "overarching_goal": "[1-2 sentences describing the relatable business/social project the characters are trying to complete across all videos]",
            "anchor_characters": [
                {{
                    "name": "[Name]",
                    "role": "[Job Title/Role]",
                    "description": "[1 sentence physical and personality description]"
                }}
            ],
            "core_visual_metaphor": "[Describe the physical environment and the tangible objects used to represent abstract concepts]"
            }},
            "hooks": [
            {{
                "video_number": 1,
                "video_topic": "[Extract the topic from the text]",
                "micro_dilemma": "[1 sentence describing the specific problem the character faces in this exact moment]",
                "visual_action": "[2-3 sentences describing the character-driven animation and physical interactions. MUST be a realistic, logical business action—no absurd metaphors. No typography.]",
                "voiceover": "[The exact spoken script, 55-75 words. Engaging, urgent, and accessible.]",
                "transition_to_theory": "[The final sentence of the VO that tees up the theoretical content of the video]"
            }}
            // Generate a hook object for EVERY video marker identified in the raw text.
            ]
            }}
        }}
        
        """
        

        formatted_hook_system_prompt = case_plot_creation_prompt.format(
            target_audience=target_audience,
            Module_topic=topic_name,
            Document=file_content
        )
    

        raw_story_parameters_file = f"./Comb_case/raw_parameters_{topic_name}_{hook_model_name}.txt"
        story_parameters_file = f"./Comb_case/raw_parameters_{topic_name}_{hook_model_name}.json"
        
        full_prompt = f"{formatted_hook_system_prompt}"
        #print(f"Full hook prompt:\n{full_prompt}")

        if not os.path.exists(raw_story_parameters_file):
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
                    max_tokens=20000,
                    messages=[
                    {"role": "user", "content": formatted_hook_system_prompt},
                    ],
                    model=hook_model_name,
                    temperature=0.7
                )
                generated_result = message.content[0].text
            print(f"Generated result:{generated_result}")
            with open(raw_story_parameters_file,'w') as f:
                f.write(generated_result)
        else:
            with open(raw_story_parameters_file,'r') as f:
                generated_result = f.read()

        sanitized_result = remove_code_fences(generated_result)
        story_parameters = json.loads(sanitized_result)

        #print(f"Parsed story parameters: {story_parameters}")

        with open(story_parameters_file,'w') as f:
            json.dump(story_parameters,f,indent=4)
        
        return story_parameters_file

if __name__ == "__main__":
    input_file_path = os.environ.get("CASE_STUDY_INPUT", "Week_1.md")
    if os.path.exists(input_file_path):
        with open(input_file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    else:
        file_content = "# Module Context\nMathematical principles and practical applications."
    topic_name = "Set Theory"

    generator = CasePlotter(google_api_key=os.environ.get("GOOGLE_API_KEY"), claude_api_key=os.environ.get("CLAUDE_API_KEY"))
    generator.ideate_case(file_content, topic_name, target_audience="BSc and MSc students in Data Science and AI, as well as working professionals")