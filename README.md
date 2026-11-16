# Simplilearn OSL 3.0 Presentation Pipeline

Specialized educational presentation and asset pipeline developed for **Simplilearn Online Self-Learning (OSL 3.0)** standards.

This repository implements the stages assigned to **Saniya** as tracked in [`Simplilearn Workflow tracker.xlsx`](file:///Users/saniyaacharya/Simplilearn/Simplilearn%20Workflow%20tracker.xlsx):
- **Specific Guideline Creation**:
  * [`instructional_storyboarding_guidelines.txt`](file:///Users/saniyaacharya/Simplilearn/pipeline/instructional_storyboarding_guidelines.txt): Instructional Storyboard Guidelines (accounting for SME positioning: 100%, 70%, 20%).
  * [`color_guidelines.txt`](file:///Users/saniyaacharya/Simplilearn/pipeline/color_guidelines.txt): Color guidelines file (official Simplilearn 10-color system, #F78908 highlight, minimize green).
- **Stage Integration**:
  * [`1_instructional_design.py`](file:///Users/saniyaacharya/Simplilearn/pipeline/1_instructional_design.py): Automated 5-scene pedagogical chunking from lecture transcripts.
  * [`2_asset_classification.py`](file:///Users/saniyaacharya/Simplilearn/pipeline/2_asset_classification.py): Decomposing scenes into classified UI cards, code blocks, and diagrams.
  * [`3_image_prompt_generation.py`](file:///Users/saniyaacharya/Simplilearn/pipeline/3_image_prompt_generation.py): Formulating diffusion-ready prompts for visual assets.
  * **Downstream Hand-off**: Feeds Somnath's tasks (`Add image generation` and `Templates Creation`).

---

## 📂 Pipeline Structure & Assigned Deliverables

```
/Users/saniyaacharya/Simplilearn/
├── pipeline/
│   ├── instructional_storyboarding_guidelines.txt # SME positioning & 5-scene pedagogical rules
│   ├── color_guidelines.txt                       # 10-color palette & contrast guidelines
│   ├── 1_instructional_design.py                  # Stage 1: Storyboard Blueprint Generator
│   ├── 2_asset_classification.py                  # Stage 2: Visual Asset Classifier
│   ├── 3_image_prompt_generation.py               # Stage 3: Diffusion Image Prompt Generator
│   ├── config.py                                  # Shared constants, layout coordinates & palettes
│   └── run_pipeline.py                            # Master runner for assigned stages
├── guidelines.md                                  # Consolidated post-production guidelines reference
├── Simplilearn Workflow tracker.xlsx              # Team task tracker
├── Simplilearn Guide/                             # Official client reference PDFs & videos
└── requirements.txt                               # Dependencies
```

---

## 🎨 Simplilearn Design Standards & Specifications

| Element | Specification | Guideline Reference |
| :--- | :--- | :--- |
| **Stage Resolution** | `1920x1080` (Full HD, 16:9), 30 fps | OSL 3.0 Page 7–8 |
| **Corner Radius** | `10 px` for 70% layout rounded rectangle | OSL 3.0 Page 6 |
| **SME Layout 100%** | Full screen `1920x1080` for Intro / Hook | OSL 3.0 Page 6 |
| **SME Layout 70%** | Left rounded rect `640x920` (r=10) with `#1A73E8` blue bar | OSL 3.0 Page 6 & 16 |
| **SME Layout 20%** | Top-right corner PIP `384x216` (clearance x >= 1480, y <= 270) | OSL 3.0 Page 16 & 27 |
| **Primary Typography** | **Open Sans** (Bold 44/45px titles, Regular 28-32px body) | OSL 3.0 Page 13–14 |
| **Highlighting** | `#F78908` (Orange), `3 px` thickness, draw time `1.0s` | OSL 3.0 Page 25 |
| **Color Palette** | `#62B7E4`, `#7EA2C8`, `#C1A5C6`, `#9B99C7`, `#B88968`, `#DDB945`, `#E6A157`, `#E58F6D`, `#D98CA1`, `#8ECDB7` | OSL 3.0 Page 21 |
| **Next Topic Syntax** | `"In the next topic, you will learn about: <Action in -ing>"` | CE Checklist Page 1 |
| **Numbers Rule** | Numbers 0–9 spelled out in words (*zero* through *nine*) | CE Checklist Page 2 |

---

## 💻 Quick Start & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Saniya's Assigned Pipeline (Stages 1 -> 2 -> 3)
```bash
python3 pipeline/run_pipeline.py \
  --input-transcript "path/to/clean_transcript.json" \
  --output-dir "output/assigned_stages" \
  --lesson-title "Prompt Engineering Basics"
```

### 3. Running Individual Pipeline Stages

#### Stage 1: Instructional Storyboard Design
```bash
python3 pipeline/1_instructional_design.py \
  -t transcript.json \
  -o output/storyboard_blueprint.json \
  -l "Topic Title"
```

#### Stage 2: Asset Classification
```bash
python3 pipeline/2_asset_classification.py \
  -b output/storyboard_blueprint.json \
  -o output/classified_assets.json
```

#### Stage 3: Image Prompt Generation
```bash
python3 pipeline/3_image_prompt_generation.py \
  -a output/classified_assets.json \
  -o output/image_prompts.json
```
