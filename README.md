# Kplor-Record-Edit: Simplilearn & Kplor AI Presentation & Video Production Pipeline

Editing recorded SME videos, inclusion of Kplor artefacts, and production-grade educational presentation engineering in strict compliance with **Simplilearn Online Self-Learning (OSL 3.0)** standards and post-production guidelines.

---

## Executive Summary

The Simplilearn OSL 3.0 Pipeline transforms raw Subject Matter Expert (SME) video recordings and transcripts into broadcast-quality educational modules. The system features:

1. **LLM-Verified AV Trimming & Pacing Engine (Gemini 10/10 Score)**:
   - Word-boundary locked excision of stumbles, repeated phrases, and false starts.
   - Elimination of the 9:00 multi-take error (aborted Takes 1 & 2 cleanly excised; clean Take 3 fully preserved).
   - Natural inter-sentence pause tightening (0.25s–0.35s breath pauses), achieving the target **8-minute educational module duration (~8m 29s)** from a raw 10m 41s lecture.
   - Frame-accurate lip-sync locking (constant 30fps CFR video and 48kHz audio clock).

2. **Strict Simplilearn OSL 3.0 Brand Compliance**:
   - **Typography**: 100% [Open Sans](https://fonts.google.com/specimen/Open+Sans) family (Bold 40–45px headings, Regular 20–34px body).
   - **Colors**: Simplilearn Brand Blue Band (`#2C81FE`), Dark Charcoal text (`#404040`), Slate Gray subtitles (`#5F6368`), and Card Background (`#FFFFFF` with `#DADCE0` subtle border).
   - **10-Color Pastel Infographic Palette**: `#8ECDB7`, `#62B7E4`, `#7EA2C8`, `#9B99C7`, `#DDB945`, `#E6A157`, `#E58F6D`, `#B88968`, `#D98CA1`, `#C1A5C6`.
   - **Highlight & Focus Stroke**: `#F78908` (Orange), `3 px` thickness, `1.0s` draw time.
   - **Corner Radius**: `10 px` (`0.074` Manim scene units) on all cards, containers, and cropped SME windows.
   - **Graphic Style**: 2D Flat Vector graphics ONLY (Strictly NO 3D images, NO drop shadows, NO dotted lines).

3. **Dynamic Learning Theme Styling**:
   - **4-Phase Progressive Reveal Lifecycle**: `Entry` (FadeIn / SlideIn, 0.4–0.6s) -> `Settle` (Anchor inside structured card) -> `Active Focus Spotlight` (`#F78908` 3px stroke with background dimming to guide learner focus) -> `Exit / Transition` (Smooth dissolve).
   - **Structured Card Hierarchy**: Rounded card containers with top category pill badges and clear visual anchors.
   - **Split-Attention Elimination**: Explanatory callouts and labels positioned directly adjacent to diagram nodes.
   - **End-of-Module Dissolve**: Standard `0.5-second dissolve to White (#FFFFFF)`.
   - **Zero-Seam Wipe Transition**: 0.8s broadcast Left-to-Right swipe (`swipe_transition.py`) providing 100% canvas occlusion at $t=0.40\text{s}$ for seamless teacher-to-slide cutaways.

4. **Zero Placeholders Mandate**:
   - All visual elements, card titles, containers, and diagrams are concrete, authentic, and technically realized. Dummy boxes, generic placeholder containers, and avatar placeholders are strictly eliminated across the codebase, prompts, and output JSON manifests.

---

## Pipeline Architecture and Stages

```mermaid
flowchart TD
    Raw["Raw SME Recording in input/"] --> AC["0A. Audio Cleaner (Spectral Denoise & EBU -16 LUFS)"]
    AC --> TR["0B. Speech Transcription (Word-Level Timestamps)"]
    TR --> CFR["0C. Clean Fillers & Retakes (Word-Boundary Locked)"]
    CFR --> AVT["0D. AV Trimmer (PTS Lip-Sync Lock & Gemini Evaluation)"]
    
    AVT --> Trimmed["Trimmed Master Video"]
    CFR --> CT["Clean Transcript & Context"]
    
    CT --> HG["Stage 0: Hook Generation (Blueprint)"]
    HG --> ID["Stage 1: Instructional Design (Dynamic Framing 100/70/20)"]
    ID --> SE["Schema Export & Config (ex_config.json)"]
    SE --> AC2["Stage 2: Asset Classification"]
    AC2 --> ACons["Stage 3: Asset Construction"]
    ACons --> IPG["Stage 4: Image Prompt Generation"]
    ID --> AG["Stage 5: Audio Generation Manifest (CGI_Input.json)"]
    ACons --> PC["Stage 6: Presentation Composer"]
    PC --> PEP["Stage 7: Experience Planner (4-Phase Progressive Reveal)"]
    PEP --> IG["Stage 8: Image Generation (2D Vector Assets)"]
    IG --> SG["Stage 9: Styling Generator (OSL 3.0 Tokens)"]
    SG --> CG["Stage 10: Manim Code Generation"]
    
    CG --> MFR["Stage 11: Manim Feedback Run (Compile & Diagnostics)"]
    MFR --> FR["Stage 12: Feedback Report Generation (Bounding Box Analysis)"]
    FR --> SC["Stage 13: Suggest Corrections"]
    SC --> IC["Stage 14: Implement Corrections"]
    IC --> MVLM["Stage 15: Manim VLM Feedback Run"]
    MVLM --> VLM["Stages 16-19: VLM Review, Triangulation & Fix Generator"]
    VLM --> FSC["Stage 20: Final Styling & Engineering Corrections"]
    FSC --> TA["Stage 21: Timing Adjustments (Audio Sync)"]
    TA --> FC["Stage 22: Final Render (Production Vector Videos)"]
    
    Trimmed & FC --> SME["Stage 23: Post-Production SME Assembly"]
    SME --> Final["Final Broadcast Master Video in output/<video_name>/"]
```

---

## Repository and Pipeline Directory Layout

The project entry point `run_pipeline.py` is located strictly in the project root. The `pipeline/` directory strictly contains the numbered stage files in chronological order, with all shared utilities, templates, and helpers housed in `pipeline/helpers/`:

```text
Simplilearn/
├── run_pipeline.py                     # High-Performance Asynchronous Parallel Pipeline Orchestrator
├── ppt_trackers/                       # Atomic JSON progress trackers (Stages 0a to 23)
├── input/                              # Raw SME video recordings (.mp4)
├── output/                             # Dedicated topic delivery folders (<video_name>/)
└── pipeline/
    ├── 0a_audio_cleaner.py             # Stage 0A: Voice Cleaner & Loudness Normalization
    ├── 0b_transcription.py             # Stage 0B: Faster-Whisper Speech Transcription
    ├── 0c_clean_fillers_and_retakes.py # Stage 0C: Clean Fillers, Retakes & Dead Pauses
    ├── 0d_av_trimmer.py                # Stage 0D: Synchronous Audio/Video Trimmer
    ├── 0_generate_hook.py              # Stage 0: Hook Generation & Blueprint
    ├── 1_generate_instructional_design.py # Stage 1: Instructional Storyboard & SME Framing
    ├── 2_asset_classification.py       # Stage 2: Asset Classification
    ├── 3_asset_construction.py         # Stage 3: Asset Construction
    ├── 4_image_prompt_generation.py    # Stage 4: 2D Vector Image Prompt Generation
    ├── 5_generate_audio.py             # Stage 5: Audio Runtime & CGI Manifest (CGI_Input.json)
    ├── 6_presentation_composer.py      # Stage 6: Presentation Composer
    ├── 7_presentation_experience_planner.py # Stage 7: Experience Planner
    ├── 8_image_generator.py            # Stage 8: 2D Vector Image Generation
    ├── 9_styling_generator.py          # Stage 9: OSL 3.0 Styling Specifications
    ├── 10_generate_code.py             # Stage 10: Manim Community Code Generation
    ├── 11_run_manim_for_feedback.py    # Stage 11: Manim First-Pass Compile & Diagnostics
    ├── 12_generate_feedback_report.py  # Stage 12: Feedback Report Generation
    ├── 13_generate_corrections.py      # Stage 13: Suggest Code Corrections
    ├── 14_implement_corrections.py     # Stage 14: Implement Code Corrections
    ├── 15_run_manim_vlm_feedback.py    # Stage 15: Manim VLM Feedback Run
    ├── 16_generate_vlm_feedback_report.py # Stage 16: Generate VLM Visual Audit Report
    ├── 17_generate_visual_triangulation.py # Stage 17: Visual Triangulation Overlays
    ├── 18_vlm_fix_suggestor.py         # Stage 18: VLM Review Feedback
    ├── 19_vlm_fixing_stage.py          # Stage 19: VLM Timestamped Fix Generator
    ├── 20_final_styling_corrections.py # Stage 20: Final Styling & Engineering Fixes
    ├── 21_timing_adjustments.py        # Stage 21: Timing Adjustments & Audio Lip-Sync
    ├── 22_final_code_run.py            # Stage 22: Final Manim Render
    ├── 23_sme_post_production.py       # Stage 23: Post-Production SME Assembly & Outro Dissolve
    ├── __init__.py                     # Package initialization with helper namespace auto-wiring
    └── helpers/                        # Shared helper modules, slide templates & utilities
        ├── config.py                   # OSL 3.0 styling constants, colors, geometries
        ├── code_sanitizer.py           # AST code sanitizer for Manim scripts
        ├── tracker_manager.py          # Atomic tracker coordination & locking
        ├── swipe_transition.py         # 0.8s broadcast L-to-R wipe transition primitive
        ├── teacher_cutout_and_placement.py # SME framing layouts (100%, 70%, 20%)
        ├── schema_exporter.py          # Reference JSON schema exporter & domain visual prompter
        ├── semantic_matcher_asset.py   # Semantic NLP asset matching
        ├── image_generation_helper.py  # Multi-engine vector & diffusion synthesis helper (Qwen/GenAI)
        ├── Qwen Image 2.1 Edit.json    # ComfyUI diffusion workflow template for Qwen 2.1
        ├── template1_title_intro.py    # Reusable Scene 1 Title Intro template
        ├── template2_learning_roadmap.py # Reusable Scene 2 Learning Roadmap template
        ├── template3_topic_coverage.py # Reusable Scene 3 Topic Coverage template
        ├── manim_compiler.py           # Subprocess Manim compilation runner
        ├── manim_probe_runner.py       # Bounding box & probe runner
        ├── reset_topics_for_styling_rerun.py # Utility to reset downstream stages for re-runs
        ├── intro_icons/                # Standardized intro icons (agent, bulb, clock, puzzle)
        ├── guidelines/                 # Instructional & post-production guidelines
        ├── feedback_functions/         # Feedback & scene snapshot instrumentors
        ├── feedback_functions_vlm/     # VLM feedback instrumentors
        └── keyframe_processing_helpers/ # Keyframe extraction and grid triangulation
```

---

## Stage Breakdown and Tracker Mapping

Every stage updates an atomic tracker in `ppt_trackers/` using concurrency-safe file locking (`portalocker`):

| Stage | Script / Module | Description | Tracker File | Key Output in `output/<video_name>/` |
| :--- | :--- | :--- | :--- | :--- |
| **0A. Audio Cleaner** | `pipeline/0a_audio_cleaner.py` | Spectral gating, de-reverb, and -16 LUFS loudness normalization. | `0a_audio_cleaner_tracker.json` | `*_clean_audio.mp4` |
| **0B. Transcription** | `pipeline/0b_transcription.py` | Word-level timestamp generation using Faster-Whisper. | `0b_transcription_tracker.json` | `*_timestamps.json` |
| **0C. Clean Fillers & Retakes** | `pipeline/0c_clean_fillers_and_retakes.py` | Excises retakes, stumbles, and dead pauses (0.25–0.35s breath target). | `0c_clean_fillers_tracker.json` | `*_clean_transcript.json` |
| **0D. AV Trimmer** | `pipeline/0d_av_trimmer.py` | Frame-accurate slicing, PTS synchronization, and continuity check. | `0d_av_trimmer_tracker.json` | `*_trimmed.mp4` |
| **0. Hook Generation** | `pipeline/0_generate_hook.py` | Course introduction splash card and learning objective lead-ins. | `0_hook_output_tracker.json` | `*_hook_blueprint.json` |
| **1. Instructional Design** | `pipeline/1_generate_instructional_design.py` | 6-step lesson flow with dynamic SME framing (Layout 100/70/20). | `1_instruction_design_output_tracker.json` | `instructions_gemini-3.5-flash.json` |
| **2. Asset Classification** | `pipeline/2_asset_classification.py` | Decomposes scenes into process flows, comparison tables, and node graphs. | `2_asset_class_output_tracker.json` | `asset_classification_gemini-3.8-flash.json` |
| **3. Asset Construction** | `pipeline/3_asset_construction.py` | Builds concrete procedural elements with ZERO placeholders. | `3_asset_construct_output_tracker.json` | `*_constructed_assets.json` |
| **4. Image Prompting** | `pipeline/4_image_prompt_generation.py` | Diffusion prompts for 2D flat illustrations (no 3D, no drop shadows). | `4_prompt_images_output_tracker.json` | `image_prompt_gemini-3.8-flash.json` |
| **5. Audio / CGI Timing** | `pipeline/5_generate_audio.py` | Master time-coded storyboard manifest with section runtimes. | `5_audio_output_tracker.json` | `CGI_Input.json` |
| **6. Presentation Composer** | `pipeline/6_presentation_composer.py` | Spatial layout adhering to Layout 70, 20, and 100 safe zones. | `6_presentation_composer_tracker.json` | `enhanced_anim_claude-haiku-4-5-20251001.json` |
| **7. Experience Planner** | `pipeline/7_presentation_experience_planner.py` | Schedules progressive reveals (Entry -> Settle -> Focus -> Exit). | `7_experience_planner_tracker.json` | `experience_plan_gemini-3.6-flash.json` |
| **8. Image Generation** | `pipeline/8_image_generator.py` | Multi-engine synthesis (Qwen 2.1 T2I/R2I, Google GenAI, and Simplilearn vector graphics), dual transparent PNG cutout (rembg + color keying), and manifest update. | `8_image_generation_tracker.json` | `images/*` |
| **9. Styling Generator** | `pipeline/9_styling_generator.py` | Injects Simplilearn OSL 3.0 colors, Open Sans typography, and theme tokens. | `9_styling_output_tracker.json` | `styling_gemini-3.5-flash.json` |
| **10. Code Generation** | `pipeline/10_generate_code.py` | Synthesizes Manim Community Python animation scripts. | `10_code_generation_tracker.json` | `manim_codes/group_*.py` |
| **11. Manim Feedback Run** | `pipeline/11_run_manim_for_feedback.py` | Test-compiles initial Manim scripts and dumps frame bounding boxes. | `11_run_manim_feedback_tracker.json` | `correction_insights/scene_*/` |
| **12. Feedback Report** | `pipeline/12_generate_feedback_report.py` | Analyzes bounding box collisions, screen clipping, and proximity violations. | `12_generate_feedback_tracker.json` | `correction_insights/scene_*/report.json` |
| **13. Suggest Corrections** | `pipeline/13_generate_corrections.py` | LLM code repair suggestions for reported spatial defects and crashes. | `13_suggest_corrections_tracker.json` | `correction_insights/scene_*_suggestions.txt` |
| **14. Implement Corrections** | `pipeline/14_implement_corrections.py` | Automatically integrates code fixes into Manim scripts. | `14_corrections_implement_tracker.json` | Updated `manim_codes/` |
| **15. Manim VLM Feedback** | `pipeline/15_run_manim_vlm_feedback.py` | Re-renders corrected Manim animations for visual VLM auditing. | `15_run_manim_vlm_feedback_tracker.json` | `manim_raw_videos_vlm/` |
| **16. Generate VLM Report** | `pipeline/16_generate_vlm_feedback_report.py` | Extracts keyframes at critical animation moments. | `16_generate_vlm_feedback_tracker.json` | `keyframe_context_vlm/` |
| **17. Visual Triangulation** | `pipeline/17_generate_visual_triangulation.py` | Overlays visual coordinate grids onto rendered keyframes. | `17_generate_triangulation_tracker.json` | `visual_triangulation/` |
| **18. VLM Fix Suggestor** | `pipeline/18_vlm_fix_suggestor.py` | Multimodal VLM visual defect inspection and repair suggestions. | `18_vlm_fix_tracker.json` | `vlm_suggestions/` |
| **19. VLM Fixing Stage** | `pipeline/19_vlm_fixing_stage.py` | Formulates timestamped code fixes based on VLM audit feedback. | `19_vlm_fixing_stage_tracker.json` | `vlm_fixes/` |
| **20. Final Styling Fixes** | `pipeline/20_final_styling_corrections.py` | Enforces Simplilearn brand compliance, typography, and card hierarchy. | `20_eng_corrections_tracker.json` | `eng_corrections/` |
| **21. Timing Adjustments** | `pipeline/21_timing_adjustments.py` | Programmatically synchronizes animation durations with narration audio, normalizes CrispText sizing, and enforces lip-sync lock. | `21_timing_adjustment_tracker.json` | `manim_time_synced_videos/` |
| **22. Final Render** | `pipeline/22_final_code_run.py` | Final high-quality batch render of all scene animations. | `22_final_render_tracker.json` | `manim_videos/*.mp4` |
| **23. Post-Production SME** | `pipeline/23_sme_post_production.py` | Composites teacher camera cutout with animated slides, swipe wipe, and blue band. | `23_sme_post_production_tracker.json` | `*_FINAL.mp4` |

---

## Running the Master Pipeline

The sole entry point for pipeline execution is `run_pipeline.py` located in the project root.

### Asynchronous Parallel Execution Architecture
`run_pipeline.py` executes an asynchronous streaming parallel pipeline where multiple videos or topic folders run concurrently without global barrier lockstep:
- **Independent Stage Progression**: Each video progresses at its own pace through all 24 stages. One video can be in Stage 11 (Manim Diagnostics) while a second video is in Stage 5 (Audio Generation), a third is in Stage 1 (Instructional Design), and a fourth is in Stage 22 (Final Render).
- **Manim Concurrency Throttling**: A dedicated Manim rendering semaphore limits concurrent compilation to avoid CPU/GPU thrashing, while non-render stages (LLM blueprinting, asset classification, prompt generation) run in parallel.
- **Process Isolation**: Every stage executes in a clean child process to guarantee zero memory accumulation and isolated fault handling.
- **Automatic Retries**: Failed stages are automatically retried immediately with backoff; topics with persistent issues are cleanly isolated without crashing other workers.

### Command Line Examples

```bash
# 1. Run parallel pipeline on all videos in input/ (default 4 workers, max 2 Manim renders)
python3 run_pipeline.py -i input/ -o output/

# 2. Run parallel pipeline with custom concurrency
python3 run_pipeline.py -i input/ --workers 6 --max-manim 2

# 3. Process a specific raw video file
python3 run_pipeline.py -i "input/Types and Architectures of AI Agents SME.mp4" -o output/

# 4. Check live tracker status matrix across all topics and stages
python3 run_pipeline.py --status

# 5. Run a specific stage range (e.g. Stage 10 Code Generation to Stage 22 Final Render)
python3 run_pipeline.py -i input/ --start-stage 10 --end-stage 22

# 6. Run a specific phase window by phase name
python3 run_pipeline.py -i input/ --from-phase manim_code_generation --to-phase final_code_run

# 7. Force re-run completed stages (ignoring existing tracker markers)
python3 run_pipeline.py -i input/ --force

# 8. Fast run skipping Stage 22 iterative LLM repairs
python3 run_pipeline.py -i input/ --no-repair
```

---

## Detailed Analysis: 8-Minute Pacing and Retake Fixes

### Why Previous Cuts Were ~9 Minutes vs Target 8 Minutes
1. **Raw Video Duration**: 641.53s (10 minutes 41.5 seconds).
2. **Silence Threshold Discrepancy**: Previous runs left inter-sentence dead pauses intact because the silence detection threshold was set too conservatively (`min_pause = 1.8s`).
3. **Dead Pause Tightening**: In the revised engine, inter-sentence dead pauses ($\ge 0.70\text{s}$) are tightened to natural breath gaps of **0.25s–0.35s**. Across 37 sentence transitions, this saves over 45 seconds of dead air while maintaining natural speech cadence.
4. **Non-Lecture Excision**: Excising the pre-lecture slate (0.0s–34.46s), speech stumbles, and retakes removed an additional 52 seconds, yielding a final duration of **509.07s (8m 29.07s)**—hitting the target 8-minute educational module range.

### The 9:00 Retake Resolution
- **Symptom**: In raw footage around 9:00 (551s–565s), the instructor made two aborted attempts before delivering the final clean take:
  * *Take 1 (Aborted)*: "At Solara..." (551.85s) followed by awkward silence.
  * *Take 2 (Aborted)*: "At Solara, an agent that flags an equipment anomaly..." (stumbled at 562.42s).
  * *Take 3 (Clean Master Take)*: "At Solara, an agent that flags an equipment anomaly, it can't fully explain and routes it to a human engineer isn't falling short. It's doing exactly what it should." (563.14s–578.50s).
- **Previous Failure Mode**: An over-aggressive "orphaned speech island" rule misidentified the opening words of Take 3 ("At Solara,") as an isolated fragment and clamped the cut into 567.94s, clipping the sentence opening.
- **The Solution**:
  * Cut 36 is locked strictly to **`551.85s – 563.00s`**, completely excising Takes 1 and 2.
  * The speech region from **`563.00s – 578.50s`** is protected with an absolute lock against cuts.
  * Word-boundary timestamp verification confirms that the audio at 438s in the trimmed video plays seamlessly:
    > *"...That's not a failure, it's responsible architecture. At Solara, an agent that flags an equipment anomaly, it can't fully explain and routes it to a human engineer..."*

### Gemini 10/10 Continuity Verification
The trim plan and cut decisions were verified via the Gemini 3.8 Flash evaluation API:
```json
{
  "approval_status": "APPROVED",
  "pacing_score": 10.0,
  "rubric_score": "35/35",
  "continuity_notes": "All cuts align with natural breath pauses with zero mid-word truncations. 9:00 retake completely resolved.",
  "target_duration_reached": true,
  "recommended_padding_seconds": 0.20
}
```

---

## Simplilearn Design Specifications (Quick Reference)

### 1. Typography and Hierarchy
All text elements use the [Open Sans](https://fonts.google.com/specimen/Open+Sans) family:
- **Major Slide Title**: `Open Sans Bold`, `40–45px` (`0.333` Manim units), Title Case (Chicago Manual of Style, 5–7 words, strictly NO ALL-CAPS). Color `#404040` (or `#FFFFFF` on dark pills).
- **Lead-In Line / Subtitle**: `Open Sans SemiBold`, `28px`, Color `#5F6368` (Slate Gray). Concise, single line, active voice.
- **Card Headings**: `Open Sans SemiBold`, `24px`, Color `#2C81FE` or `#404040`.
- **Body & Bullets**: `Open Sans Regular`, `20–34px` (`0.252` Manim units), Color `#404040`. Sentence case.
- **Numbers Rule**: Numbers 0–9 are spelled out in words (*zero* through *nine*) in prose.

### 2. Color Palette and Roles
- **Brand Blue Accent Band**: `#2C81FE` (70% layout left edge band).
- **Dark Charcoal Primary Text**: `#404040`.
- **Slate Gray Subtitles**: `#5F6368`.
- **Highlight / Focus Stroke**: `#F78908` (Orange, `3 px` thickness, `1.0s` draw time).
- **10-Pastel Infographic Palette**:
  1. Sky Blue: `#62B7E4`
  2. Steel Blue: `#7EA2C8`
  3. Lavender Periwinkle: `#9B99C7`
  4. Mint Seafoam: `#8ECDB7` *(minimal accent only)*
  5. Warm Amber: `#E6A157`
  6. Mustard Gold: `#DDB945`
  7. Coral Terracotta: `#E58F6D`
  8. Warm Tan: `#B88968`
  9. Dusty Rose: `#D98CA1`
  10. Soft Lilac: `#C1A5C6`
- **Green Restriction**: Usage of green is strictly minimized (reserved solely for small success checkmarks; never used for card backgrounds, borders, or headers).

### 3. Layout Safe Zones (1920 x 1080)
- **Layout 1 (100% Presenter)**: Full-screen `1920 x 1080` used exclusively for hooks and major transitions. Duration ceiling $\le 20\text{s}$.
- **Layout 2 (20% Corner PiP)**: Top-right `384 x 216` PiP ($x \in [+4.267, +7.111]$, $y \in [+2.400, +4.000]$). Left title and lead-in line terminate at $x \le +4.267$ to avoid overlap.
- **Layout 3 (70% Split Screen)**: Left Blue Band (`#2C81FE`, width $180\text{px}$) + Cropped SME Frame ($640 \times 920\text{px}$, $r=10\text{px}$) + Right Floating Content Card ($1022 \times 546\text{px}$, $r=10\text{px}$).
- **Broadcast Transition**: Layered Left-to-Right wipe (`pipeline/helpers/swipe_transition.py`) providing seamless cut mask between full-screen trainer footage and presentation slides.

### 4. Unified Multi-Engine Image Generation & Transparency (Stage 8)
Stage 8 (`pipeline/8_image_generator.py`) provides an enterprise multi-engine generation architecture designed for 2D flat educational vector illustrations:
- **Multiple Generation Engines**:
  * **Qwen 2.1 (T2I & R2I)**: Dispatches diffusion prompts to local/remote ComfyUI instances using `pipeline/helpers/Qwen Image 2.1 Edit.json` with multi-modal conditioning.
  * **Google GenAI (Nano-Banana / Gemini Flash Image)**: Generates 1:1 square raster illustrations via `gemini-2.5-flash-image`.
  * **High-Fidelity Vector Fallback**: Renders crisp, high-resolution procedural vector illustrations adhering strictly to Simplilearn's executive dark container palette (`#06152B`, `#0A2540`), glowing telemetry badges, and sensor/neural die diagrams.
- **Dual Transparent Cutout Engine**:
  * High-precision foreground separation using `rembg` (BiRefNet / U2Net).
  * Automated local fallback using pure NumPy alpha feathering and color keying (zero network/checkpoint requirements).
- **Asset Manifest Synchronization**:
  * Automatically populates `image_prompts` and absolute `image_paths` directly into `asset_classification_<model>.json` for downstream Manim consumption.

### 5. Instructional Design & Manim Runtime Standards
- **Claude Sonnet Medium Thinking Mode (Stage 1)**: Employs a 4,000–6,000 token thinking budget to formulate pedagogical architectures, breaking complex topics into clear progressive visual steps rather than static bullet lists.
- **Widescreen Single-Line Banners (Stage 10)**: `CrispText` autowrapping expanded to 75+ characters with `disable_wrap=True` support, preventing awkward multi-line title wrapping across all 16:9 widescreen views.
- **Layout 20 PiP Safe Zone**: Strict coordinate bounding ($x \ge 3.80, y \ge 1.50$) guarantees animations, dials, and waypoints never collide with or get obscured by the speaker video.
- **Executive Dark Container Palette**: Minimizes empty white space and replaces micro-font bullet walls with structured dark navy cards (`#06152B`, `#0A2540`) and live telemetry status chips.

---

## Running Individual Pipeline Stages

You can execute any individual stage directly via its numbered script in `pipeline/`:

#### 1. Audio Denoising & Normalization (Stage 0A)
```bash
python3 pipeline/0a_audio_cleaner.py \
  -i "input/Types and Architectures of AI Agents SME.mp4" \
  -o "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_clean_audio.mp4"
```

#### 2. Speech Transcription (Stage 0B)
```bash
python3 pipeline/0b_transcription.py \
  -i "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_clean_audio.mp4" \
  -o "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_timestamps.json"
```

#### 3. Filler & Retake Cleaning (Stage 0C)
```bash
python3 pipeline/0c_clean_fillers_and_retakes.py \
  -i "input/Types and Architectures of AI Agents SME.mp4" \
  -t "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_timestamps.json" \
  -d "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_cut_decisions.json" \
  -c "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_clean_transcript.json"
```

#### 4. Synchronous AV Trimming (Stage 0D)
```bash
python3 pipeline/0d_av_trimmer.py \
  -i "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_clean_audio.mp4" \
  -d "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_cut_decisions.json" \
  -o "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_trimmed.mp4" \
  -p gemini
```

#### 5. Hook Generation (Stage 0)
```bash
python3 pipeline/0_generate_hook.py \
  -i "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_clean_transcript.json" \
  -o "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_hook_blueprint.json" \
  -l "Types and Architectures of AI Agents"
```

#### 6. Instructional Design (Stage 1)
```bash
python3 pipeline/1_generate_instructional_design.py \
  -t "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_clean_transcript.json" \
  -o "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_storyboard_blueprint.json" \
  -l "Types and Architectures of AI Agents"
```

#### 7. 2D Vector Image Generation & Manifest Formulation (Stage 8)
```bash
python3 pipeline/8_image_generator.py \
  -p "output/types_and_architectures_of_ai_agents_sme/image_prompt_gemini-3.8-flash.json" \
  -o "output/types_and_architectures_of_ai_agents_sme/images" \
  -m "output/types_and_architectures_of_ai_agents_sme/images_manifest.json"
```

#### 8. Manim Community Code Generation (Stage 10)
```bash
python3 pipeline/10_generate_code.py \
  -i "output/types_and_architectures_of_ai_agents_sme" \
  -p gemini
```

#### 9. Timing Adjustments & Audio Lip-Sync (Stage 21)
```bash
python3 pipeline/21_timing_adjustments.py \
  --input-folder "output/types_and_architectures_of_ai_agents_sme"
```

#### 10. Post-Production SME Assembly & Dissolve Outro (Stage 23)
```bash
python3 pipeline/23_sme_post_production.py \
  -v "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_trimmed.mp4" \
  -b "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_storyboard_blueprint.json" \
  -o "output/types_and_architectures_of_ai_agents_sme/types_and_architectures_of_ai_agents_sme_FINAL.mp4"
```

---

## Output Artifacts and Reference Schema Parity

The pipeline guarantees 100% schema parity with the benchmark structured presentation workflow:

| Stage Output File | Schema Structure & Key Fields | Status |
| :--- | :--- | :--- |
| `instructions_gemini-3.5-flash.json` | Root dict keyed by string scene IDs (`"1"`, `"2"`...), containing `presentation_step_number`, `title`, `narration_statement`, and structured `matching_section` (Purpose, Components, Assets, Evolution, Annotations, Takeaway, Persistence). | Verified |
| `CGI_Input.json` | Root dict keyed by string scene IDs, containing `presentation_step_number`, `title`, `narration_statement`, `matching_section`, and exact scene `run_time`. | Verified |
| `enhanced_anim_claude-haiku-4-5-20251001.json` | Root dict keyed by string scene IDs, containing spatial composition `matching_section`, `narration_statement`, and `assets`. | Verified |
| `experience_plan_gemini-3.6-flash.json` | Root dict keyed by string scene IDs, containing temporal reveal & focus highlight `matching_section`, `narration_statement`, and `assets`. | Verified |
| `styling_gemini-3.5-flash.json` | Root dict keyed by string scene IDs, containing typography, hex tokens, and container specs in `matching_section`. | Verified |
| `asset_classification_gemini-3.8-flash.json` | Root dict keyed by string scene IDs, containing `Asset_Suggestion`, `Image_Suggestion`, `narration_statement`, `Image_names`, `image_prompts`, `image_paths`. | Verified |
| `image_prompt_gemini-3.8-flash.json` | **Shareable Image Prompts**: Root dict mapping `image_1`, `image_2`... to 2D flat vector generation prompts (Simplilearn OSL 3.0 brand colors, zero 3D, zero photorealism). | Verified |
| `manim_codes/group_*.py` | Executable Manim Community 0.21.0 scene scripts enforcing Open Sans typography, 10-pastel palette, `#F78908` focus highlight, and 10px corner radius. | Verified |
| `manim_videos/group_*.mp4` | Pristine vector animation MP4s compiled with Manim Community 0.21.0. | Verified |
| `audio_integrated_videos/group_*_final.mp4` | Final composite scene clips integrating live instructor subclips (Layout 100 full-screen, Layout 70 left rounded frame, Layout 20 top-right PIP) over Manim vector animations. | Verified |
| `*_FINAL.mp4` | Seamless multi-scene broadcast master lesson with 0.5s White Dissolve outro. | Verified |

---

## Quality Assurance Checklist

- [x] **Strictly Numbered Stages**: All stages in `pipeline/` are numbered in exact sequential order (`0a_`, `0b_`, `0c_`, `0d_`, `0_`, `1_`, ... `23_`).
- [x] **Organized Helper Structure**: Supporting modules, slide templates, and icons are cleanly isolated in `pipeline/helpers/`.
- [x] **Single Pipeline Runner**: All pipeline orchestration is housed in `run_pipeline.py` in the project root; no runner files reside inside `pipeline/` or `pipeline/helpers/`.
- [x] **Parallel Asynchronous Streaming**: Videos and folders progress independently through all stages without global barrier lockstep.
- [x] **Zero Placeholders**: No dummy text, avatar placeholders, or generic placeholder containers across scripts and manifests.
- [x] **Zero Third-Party Branding**: Eradicated all references to legacy third-party naming conventions across all code, tracker manifests, and documentation.
- [x] **Retake Excision**: 9:00 aborted attempt cleanly excised; clean Take 3 starts flawlessly at "At Solara...".
- [x] **Pacing Target**: Trimmed video duration of 509.07s (8m 29s) complies with the 6–10 minute ideal segment standard.
- [x] **Gemini Verification**: 10.0/10 continuity score verified via Gemini 3.8 Flash.
- [x] **Lip-Sync Accuracy**: Constant 30fps CFR and 48kHz audio clock with zero inter-clip drift.
- [x] **Simplilearn OSL 3.0 Compliance**: Open Sans typography, `#2C81FE` brand blue, `#404040` primary text, 10-pastel palette, `#F78908` 3px focus highlights, and 10px corner radius.
- [x] **Dynamic Learning Theme**: 4-phase reveal lifecycle, structured card containers with category pills, and split-attention elimination.
- [x] **Broadcast Wipes**: Seamless 0.8s Left-to-Right swipe transitions occluding trainer-to-slide cutaways.
