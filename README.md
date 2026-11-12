# Simplilearn AI/ML Video Post-Production Automated Pipeline

A comprehensive, production-ready AI post-production pipeline engineered specifically for **Simplilearn's Online Self-Learning (OSL 3.0) standards**.

This pipeline automates the end-to-end processing of Subject Matter Expert (SME) video recordings (Camtasia `.trec` / Tella MP4 / webcam recordings) according to:
- **OSL 3.0 Post-Production Guidelines 2026**
- **Learning Design (LD) Guidelines & Playbook for Vendors**
- **Content Editor (CE) Guidelines & Blended Learning Checklist**

---

## 🚀 Key Capabilities & Pipeline Steps

### 1. Studio Voice Cleaner & Loudness Normalization (`pipeline/voice_cleaner.py`)
- **Noise Suppression**: Removes ambient hiss, HVAC rumble, and mic handling noise using highpass filtering (80 Hz cut) and adaptive FFT de-noising (`afftdn`).
- **Dynamic Compression**: Levels vocal dynamics to ensure clear, confident educator delivery.
- **Broadcast Loudness Normalization**: Enforces strict **EBU R128** standards (`-16.0 LUFS` integrated loudness, `-1.0 dBTP` True Peak limit, `11.0 LRA`) for consistent volume across all course modules.

### 2. Speech-to-Text Transcription & Timestamping (`pipeline/transcribe_and_timestamp.py`)
- **Word-Level & Segment Timestamps**: Generates high-accuracy word and segment start/end timings (`start`, `end`, `duration`).
- **Engines**: Built-in local `faster-whisper` (runs offline on CPU/GPU, zero cloud dependency) with optional cloud fallback to `Groq Whisper-large-v3`.
- **Hinglish & Multi-language Support**: Preserves technical jargon, domain terminology, and bilingual delivery.

### 3. Content, Filler Words & Repeated Sentences Cleaner (`pipeline/content_and_retake_cleaner.py`)
- **Filler Word Stripping**: Detects and eliminates English fillers (`uh`, `um`, `like`, `you know`, `basically`, `so yeah`) and Hindi/Hinglish fillers (`मतलब`, `हम्म`, `उम्`, `यार`).
- **Repeated Sentences & False Starts**: Analyzes consecutive transcript segments using fuzzy sequence matching and n-gram overlap. When an instructor stumbles and re-starts a sentence, the botched take is flagged for cutting while retaining the final clean take.
- **Verbal Retake Triggers**: Detects verbal retake cues (`sorry cut`, `let me start again`, `restart`, `wait`, `hold on`, `stop`).
- **Silence & Dead Air Pruning**: Integrates FFmpeg `silencedetect` (`-35 dB`, `> 1.0s`) to remove dead pauses.
- **Smart Padding**: Applies `0.20s` safety padding around cuts to prevent clipped speech and abrupt audio pop artifacts.

### 4. Synchronous Audio/Video Trimmer (`pipeline/av_trimmer.py`)
- **Frame-Accurate Cuts**: Trims audio and video streams simultaneously from computed keep segments.
- **Lip-Sync Preservation**: Re-encodes segment boundaries cleanly and stitches them via FFmpeg concat demuxer without audio drift.

### 5. Voiceover Sheet Generator in Word & PDF (`pipeline/voiceover_doc_generator.py`)
- **Formatted Tables**: Generates delivery-ready `.docx` and `.pdf` documents containing:
  - `S.NO.`
  - `Voiceover / Narration Script` (cleaned of verbal chatter)
  - `Time Stamp` (formatted as `mm:ss`)
- **Client Styling**: Simplilearn Dark Blue header (`#0B3C5D`), Open Sans typography, and clean borders.

### 6. LLM Instructional Design & Presentation Storyboard Blueprint (`pipeline/llm_instructional_designer.py`)
Adapted from **Kplor Structured Presentation Workflow** (`instructional_storyboard.txt` & `styling_generator.txt`):
- **Only Raw Video Input**: Because no slide decks or background videos are provided, an LLM (Gemini 2.5 Flash / Claude 3.5 Sonnet / OpenAI) analyzes the cleaned spoken transcript.
- **Pedagogical Progression**: Automatically chunks the monologue into discrete pedagogical scenes:
  1. `hook_intro` (SME Layout: 100% Full Screen)
  2. `learning_objectives` (SME Layout: 70% Left Rounded-Rectangle + Objectives cards)
  3. `concept_explanation` / `demo` (SME Layout: 20% Top-Right Corner PIP + Full Slide Visual Workspace)
  4. `summary_takeaways` (SME Layout: 70% Left Rounded-Rectangle + Key Takeaway cards)
  5. `whats_next` (SME Layout: 70% Left Rounded-Rectangle with *"In the next topic, you will learn about: <Action in -ing>"*)
- **CE & LD Rule Enforcement**:
  - Eliminates split attention: on-screen text never duplicates voiceover verbatim.
  - Generates 5–7 word Chicago-cased titles and concise lead-in lines.
  - Spells out numbers zero to nine (0–9).
  - Automatically draws light cards with approved palette accents (`#62B7E4`, `#7EA2C8`, `#C1A5C6`, `#E6A157`, etc.).
  - Guarantees strict clearance for the 20% top-right corner SME so no text overlaps.

### 7. Official SME (Trainer) Placement Layouts (`pipeline/teacher_cutout_and_placement.py`)
Per Simplilearn's official guidelines (*OSL 3.0 Page 6, 16 & 27* and *SimpliLearn.pdf*), **no green screen or AI silhouette matting is used**. Instead, the raw recording (webcam/office background intact) is cropped and framed into exactly **3 official layouts**:
- **1. Full Screen Layout (100%)**: Full `1920x1080` trainer video for hooks, topic introductions, and closing.
- **2. 70% Cropped Area Layout (Left-Aligned Rounded Rectangle)**:
  - Cropped to `640x920` inside an anti-aliased rounded rectangle (**Corner Radius = 10 px**).
  - Positioned on the left side with a **Blue vertical accent band** (`#1A73E8`).
  - Leaves the right workspace for slide titles, learning objectives, and content cards.
- **3. 20% Right Corner PIP Layout**:
  - Scaled to 20% FHD (`384x216`, corner radius 8) in the top-right corner (`x=1496, y=40`).
  - Ensures ample clearance for slide lead-in lines and demonstration interfaces without overlap.

### 8. End-to-End Multi-Scene Assembly & Outro (`pipeline/osl_post_production.py`)
- **Multi-Scene Staging**: Automatically slices the trimmed teacher video into each scene's time window, composites each scene with its generated slide graphic in the assigned layout (100%, 70%, 20%), and concatenates them seamlessly.
- **Standard Video End Animation**: Implements the mandatory **0.5-second dissolve to White (`#FFFFFF`)** at the end of each topic video *(OSL 3.0 Page 30)*.

---

## 🧩 Steps Incorporated from `Kplor_Structured_Presentation_Workflow`

When input is **ONLY the raw teacher video**, the following stages from Kplor's 23-stage workflow are incorporated to generate the complete broadcast video:

| Kplor Stage | Original Kplor Purpose | Implementation in Simplilearn Pipeline |
| :--- | :--- | :--- |
| **Stage 0: Hook Synthesis** (`0_generate_hook.py`) | Crafts opening narrative hooks from text curriculum | Analyzes first 30–60s of teacher transcript, establishes topic title (5–7 words) and hooks; maps to **100% Full-Screen SME**. |
| **Stage 1: Instructional Design** (`1_generate_instructional_design.py`) | 2-column storyboard generation | Pedagogical chunking of raw lecture into the 5 Simplilearn sections (Intro, Objectives, Core Demo, Summary, Next Topic). |
| **Stage 2–3: Asset Classification & Construction** (`2_asset_classification.py`, `3_asset_construction.py`) | Categorizes visual components (cards, formulas, diagrams) | Classifies slide layout type: 70% dual-column layout vs 20% full-screen diagram/code workspace. |
| **Stage 6: Presentation Composer** (`6_presentation_composer.py`) | 2D canvas layout composition | Assembles the slide visual layout: title, lead-in line, cards, icons, ensuring strict clearance for the 20% top-right corner SME. |
| **Stage 7: Presentation Experience Planner** (`7_presentation_experience_planner.py`) | Choreographs progressive reveals and motion | Plans timed animations: cards slide in, highlight boxes draw in over 1.0s (`#F78908`), bullet points reveal. |
| **Stage 9: Styling Generator** (`9_styling_generator.py`) | Color palette & typography injection | Applies Simplilearn design system: Open Sans, 10px rounded corners, approved 10-color palette, no green background/containers. |
| **Stage 10: Code Generation / Rendering** (`10_generate_code.py`) | Generates executable Manim code | Generates dynamic 1080p slide graphics and animations synced to teacher voice. |
| **Stages 15–19: VLM Quality Feedback Loop** (`16_generate_vlm_feedback_report.py`, `18_vlm_fix_suggestor.py`) | Multimodal LLM visual inspection | Vision LLM inspects rendered video frames: checks for text clipping, overlap with 20% SME corner, color contrast, and guideline compliance. |
| **Stage 21: Timing Adjustment Engine** (`21_timing_adjustments.py`) | Precision sync to TTS audio | Syncs visual elements and highlights to the teacher's exact Whisper word timestamps. |
| **Final Assembly & Outro** | Audio-video muxing | Synchronously stitches trimmed teacher video across the 3 layouts (100%, 70%, 20%) and appends **0.5s White Dissolve**. |

---

## 🎨 Simplilearn Design Standards & Specifications

| Element | Specification | Guideline Reference |
| :--- | :--- | :--- |
| **Stage Resolution** | `1920x1080` (Full HD, 16:9), 30 fps | OSL 3.0 Page 7–8 |
| **Outro Transition** | 0.5-second dissolve to White (`#FFFFFF`) | OSL 3.0 Page 30 |
| **Corner Radius** | `10 px` for 70% layout rounded rectangle | OSL 3.0 Page 6 |
| **Primary Typography** | **Open Sans** (Bold 44/45px titles, Regular 28-32px body) | OSL 3.0 Page 13–14 |
| **Text Color** | `#FFFFFF` (on dark/blue) or `#404040` (inside light cards) | OSL 3.0 Page 34 |
| **Highlighting** | `#F78908` (Orange), `3 px` thickness, draw time `1.0s` | OSL 3.0 Page 25 |
| **Color Palette** | `#62B7E4`, `#7EA2C8`, `#C1A5C6`, `#9B99C7`, `#B88968`, `#DDB945`, `#E6A157`, `#E58F6D`, `#D98CA1`, `#8ECDB7` | OSL 3.0 Page 21 |
| **Audio Loudness** | EBU R128: `-16 LUFS` (±1.0), True Peak `-1.0 dBTP` | OSL 3.0 Page 5 |
| **Next Topic Syntax** | `"In the next topic, you will learn about: <Action in -ing>"` | CE Checklist Page 1 |
| **Numbers Rule** | Numbers 0–9 spelled out in words (*zero* through *nine*) | CE Checklist Page 2 |

---

## 📂 Project Structure

```
/Users/saniyaacharya/Simplilearn/
├── pipeline/
│   ├── config.py                       # OSL 3.0 constants, colors, layouts & audio standards
│   ├── 0_clean_audio.py                # Step 0: Studio voice cleaner, FFT denoise & EBU R128 (-16 LUFS)
│   ├── 1_transcribe_and_timestamp.py   # Step 1: Speech transcription with word & segment timestamps
│   ├── 2_clean_fillers_and_retakes.py  # Step 2: Filler stripping, repeated sentence & retake removal
│   ├── 3_synchronous_av_trimmer.py     # Step 3: Frame-accurate lip-sync audio/video cutting & stitching
│   ├── 4_generate_voiceover_docs.py    # Step 4: Formatted Voiceover DOCX & PDF tables (mm:ss)
│   ├── 5_llm_instructional_design.py   # Step 5: LLM pedagogical blueprinting & scene structuring
│   ├── 6_generate_slide_graphics.py    # Step 6: 1920x1080 slide graphics generator (Open Sans, cards)
│   ├── 7_sme_placement_layouts.py      # Step 7: 100%, 70% (r=10 rounded rect) & 20% PIP layouts
│   ├── 8_multi_scene_assembler.py      # Step 8: Multi-scene subclip slicing & layout compositing
│   ├── 9_apply_white_dissolve_outro.py # Step 9: 0.5s fade to White (#FFFFFF) outro transition
│   └── run_pipeline.py                 # Master CLI orchestrator (runs steps 0-9 sequentially)
├── fonts/                              # Open Sans & Noto Sans TrueType fonts
├── Simplilearn Guide/                  # Client PDF guidelines & reference videos
├── output/                             # Generated videos, transcripts, slides, and sheets
└── requirements.txt                    # Python dependencies
```

---

## 💻 Quick Start & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Full End-to-End Pipeline
```bash
python3 pipeline/run_pipeline.py \
  --input "path/to/raw_trainer_video.mp4" \
  --output-dir "output/module_01"
```

To run a specific subset of stages (e.g. Stage 0 to 4):
```bash
python3 pipeline/run_pipeline.py -i raw_video.mp4 -o output/mod1 --start-stage 0 --end-stage 4
```

---

## 🛠️ Running Individual Step Scripts

Every step is an isolated, standalone executable script:

#### Step 0: Clean Studio Audio & EBU R128 Normalization
```bash
python3 pipeline/0_clean_audio.py -i input_raw.mp4 -o output_clean.mp4
```

#### Step 1: Transcribe & Extract Word Timestamps
```bash
python3 pipeline/1_transcribe_and_timestamp.py -i output_clean.mp4 -o timestamps.json -e local -m base
```

#### Step 2: Detect & Clean Fillers, Retakes, and Repeated Sentences
```bash
python3 pipeline/2_clean_fillers_and_retakes.py -i output_clean.mp4 -t timestamps.json -d cut_decisions.json -c clean_transcript.json
```

#### Step 3: Synchronous Audio/Video Trimming
```bash
python3 pipeline/3_synchronous_av_trimmer.py -i output_clean.mp4 -d cut_decisions.json -o trimmed_video.mp4
```

#### Step 4: Generate Voiceover Documentation (DOCX & PDF)
```bash
python3 pipeline/4_generate_voiceover_docs.py -i clean_transcript.json -o output_docs/ -t "Machine Learning Basics"
```

#### Step 5: LLM Instructional Design & Blueprinting
```bash
python3 pipeline/5_llm_instructional_design.py -t clean_transcript.json -o blueprint.json -l "Neural Networks"
```

#### Step 6: Presentation Slide Graphics Generation
```bash
python3 pipeline/6_generate_slide_graphics.py -b blueprint.json -o output_slides/
```

#### Step 7: SME Placement Layouts (No Green Screen)
```bash
# 70% Layout (Rounded rectangle radius 10, blue bar):
python3 pipeline/7_sme_placement_layouts.py -l 70 -i subclip.mp4 -b slide.png -o rendered_70.mp4

# 20% PIP Layout (Top-right corner):
python3 pipeline/7_sme_placement_layouts.py -l 20 -i subclip.mp4 -b slide.png -o rendered_20.mp4

# 100% Full Screen Layout:
python3 pipeline/7_sme_placement_layouts.py -l 100 -i subclip.mp4 -o rendered_100.mp4
```

#### Step 8: Multi-Scene Educational Lesson Assembly
```bash
python3 pipeline/8_multi_scene_assembler.py -i trimmed_video.mp4 -b blueprint_with_slides.json -o assembled.mp4
```

#### Step 9: Simplilearn 0.5s White Dissolve Outro
```bash
python3 pipeline/9_apply_white_dissolve_outro.py -i assembled.mp4 -o FINAL_DELIVERY.mp4
```

