# Simplilearn OSL & Blended Learning Post-Production Guidelines

Consolidated reference compiled from all five guideline documents in [`Documents/`]:

| Document | Scope | Primary Audience |
| --- | --- | --- |
| [`Learning_Design_Guidelines.pdf`] | Post-production LD standards, lesson flow, segmentation, cognitive load, narration & checklist | Learning Design & Post-Production Teams |
| [`LD - Training doc.pdf`] | AI/ML Video Post-Production LD Playbook (Rules 1–8, examples, self-check & review rubric) | Video Production Vendors |
| [`OSL SL Guidelines.pdf`]| OSL Content Editor (CE) rules for titles, lead-in lines, bullets, bottom lines, transcripts & VO | Content Editors & Script/VO Teams |
| [`OSL_CE Checklist for Blended Learning .pdf`]| 16-point Blended Learning OSL Content Editor QA checklist | Content Editors & Reviewers |
| [`OSL_3.0_Post_Production_Guidelines_2026.pdf`]| OSL 3.0 technical specs, Camtasia/AE settings, layouts, typography, colors, naming & packaging | Post-Production Editors & Motion Designers |

---

## Table of Contents

1. [Core Learning Design Philosophy](#1-core-learning-design-philosophy)
2. [Content Flow, Segmentation & Pacing](#2-content-flow-segmentation--pacing)
3. [Cognitive Load & Split-Attention Management](#3-cognitive-load--split-attention-management)
4. [On-Screen Text (OST) & Editorial Standards](#4-on-screen-text-ost--editorial-standards)
5. [Audio, Transcript & Voiceover (VO) Guidelines](#5-audio-transcript--voiceover-vo-guidelines)
6. [Visual Design, Typography & Color Palette](#6-visual-design-typography--color-palette)
7. [Technical Stage Settings, Naming & Packaging](#7-technical-stage-settings-naming--packaging)
8. [Manim Numerical Layout & Geometry Guidelines](#8-manim-numerical-layout--geometry-guidelines)
9. [Checklists & Acceptance Review Rubric](#9-checklists--acceptance-review-rubric)

---

## 1. Core Learning Design Philosophy

Every post-production enhancement exists to enforce **learning clarity** and transform raw Subject Matter Expert (SME) recordings into structured, high-retention videos.

### 1.1 Overarching Goals
Post-produced content must:
- Be **outcome-driven** and **learner-focused**.
- Apply sound **learning design pedagogy**.
- Promote **active learning** via smart interactivity.
- Manage **cognitive load** through chunking and clean visual design.
- Deliver a **consistent, professional** learner experience.

> **Final Guiding Rule:** *Consistency, clarity, and intent matter more than creativity. If forced to choose, always choose **learning effectiveness** over visual flair.*

### 1.2 Three Core Pillars
1. **Outcome-Driven Design:** Every on-screen element must serve a clear learning outcome. Before adding anything, ask: *"What should the learner be able to do after watching this?"*
2. **Active Learning:** Prompt learners to think, predict, and apply—not passively watch—using pause prompts, interactive questions, and reflection cues.
3. **Application-Focused:** Emphasize real-world relevance. Connect concepts to practical, professional scenarios through examples and visuals.

### 1.3 Treating SME Audio as the Source of Truth
- **Audio Is Primary, Visuals Must Support It (Rule 1):** Listen to the SME audio **without visuals first** to detect:
  - Concept boundaries
  - Repeating explanation patterns
  - Natural instructional structure
- **Surface, Do Not Invent Structure:** Post-production surfaces and reinforces the structure already present in the SME audio without altering SME intent.
- **Extract Only What Belongs on Screen:** Identify **keywords**, **steps**, and **comparisons** from the audio and visualize only those elements.

---

## 2. Content Flow, Segmentation & Pacing

### 2.1 Recommended 6-Step Lesson Flow
Even if the raw SME recording is unstructured, the final output must feel guided and follow the core arc: **`context → teaching → engagement → recap`**.

| Step | Purpose | Post-Production Action |
| --- | --- | --- |
| **1. Hook / Introduction** | Grabs attention, sets context | Add a short title card or on-screen prompt |
| **2. Learning Objective** | Tells the learner what to expect | Display objective as on-screen text (using the LO template) |
| **3. Concept Explanation** | Delivers the core teaching | Add supporting visuals, annotations, highlights |
| **4. Example or Demonstration** | Shows the concept in action | Annotate key steps; zoom into details |
| **5. Learner Activity / Pause Prompt** | Engages the learner to think or try | Insert pause screen or interactive question |
| **6. Summary** | Reinforces key takeaways | Display summary bullets on-screen |

*(Shorter clips may combine steps, but `context → teaching → engagement → recap` must always remain intact.)*

### 2.2 Segmentation & Chunking
- **One Concept Per Segment:** Focus each segment on a single key concept or skill, aligned to the approved Table of Contents (TOC) without gaps or overlaps.
- **Ideal Segment Length:** **6–10 minutes** (e.g., three focused 7-minute videos outperform a single 21-minute lecture).
- **Split, Never Compress:** Break complex or multi-topic recordings into smaller parts rather than rushing or cramming.
- **Complete Narrative Arc:** Every segment must have a clear beginning, middle, and end.

### 2.3 Structural Consistency Across Related Concepts (Rule 8B)
When multiple concepts belong to the same category, enforce the **exact same instructional sequence** across all of them (e.g., `Example → Definition → Visual → Applications`, or `Problem → Solution → Benefit`):
- **Good:**
  - GANs: `Example → Definition → Visual → Applications`
  - VAEs: `Example → Definition → Visual → Applications`
  - Transformers: `Example → Definition → Visual → Applications`
- **Bad:** Mixing `Definition → Math → Example` for GANs, `Example → Architecture → Applications` for VAEs, and `Architecture only` for Transformers.

### 2.4 Pacing, Editing & Transitions
- **Invisible Edits:** Do not cut mid-explanation; preserve natural pauses when the SME shifts concepts.
- **Clean Unnecessary Content:** Remove retakes, unwanted blank spaces, recording chatter, long pauses, errors, and off-topic content.
- **Transitions:** Ensure smooth transitions; avoid flashy transitions and unnecessary jump cuts.
- **Demo Zoom-In / Zoom-Out Technique:**
  1. **Zoom In Smoothly:** Gradually zoom into detailed diagrams, code snippets, form fields, or software UIs so learners stay oriented.
  2. **Hold Steady During Explanation:** Keep the frame steady while the zoomed-in element is centered and fully visible.
  3. **Zoom Out Slowly:** Gradually return to the full-screen view once the explanation finishes.
- **Standard Video End Animation:** Use a **0.5-second dissolve to White (`#FFFFFF`)** at the end of every edited video segment.

---

## 3. Cognitive Load & Split-Attention Management

### 3.1 Six Strategies for Reducing Cognitive Load
1. **Chunk Content:** Keep segments to **6–10 minutes**, one core idea per segment.
2. **Remove Redundancy:** Never display text that duplicates the speaker's spoken sentences.
3. **Signal Key Information:** Use visual cues (highlights, arrows, color) to direct attention.
4. **Simplify Visuals (Rule 3):** Complexity must come from the concept, not the visual. Strip extraneous diagram detail.
5. **Pace Information:** Allow breathing room after complex explanations; do not rush between concepts.
6. **Progressive Disclosure:** Break large diagrams into stages and reveal steps **only when discussed** (e.g., reveal a 4-step ML pipeline one step at a time rather than dumping 8–10 components on screen at once).

### 3.2 Preventing the Split-Attention Effect
- Learners must never split attention between reading dense text and listening to audio, or between a diagram on one side and a separate explanation box on the other.
- **Solution:** Integrate short labels and annotations **directly onto or next to** the visual elements they describe.

### 3.3 Attention-Guiding Highlights (Rule 5 & OSL 3.0 Spec)
- **One Highlight at a Time:** Highlight **only** when the SME emphasizes a specific point; mute/dim all other elements. (Never highlight two competing models/sections simultaneously when contrasting a single difference.)
- **Technical Highlight Specification (OSL 3.0):**
  - **Color:** `#F78908` (Orange)
  - **Thickness:** `3 px` (`~0.022` Manim units, or `stroke_width=3`)
  - **Draw Time:** `1.0 second`

---

## 4. On-Screen Text (OST) & Editorial Standards

### 4.1 When to Add vs. Avoid On-Screen Text
| Add OST When… | Do NOT Add OST When… |
| --- | --- |
| Displaying learning objectives at the start of a segment | The speaker is already saying the exact same words (duplication) |
| Highlighting key terms, definitions, formulas, or jargon definitions | Multiple text elements are already visible (clutter) |
| Labeling parts of a diagram or process | Turning slides into paragraphs/slide decks (text is for **anchoring, not teaching**) |
| Showing step-by-step instructions during a demo | The SME never refers to the text or visual on screen (**Rule 4**) |
| Summarizing key takeaways at the end of a segment | — |
| Providing a brief recap screen if the speaker moves too fast | — |

- **Convert Sentences to Anchors:** Distill spoken sentences into **keywords** or **short phrases**; remove adjectives and filler words.
  - *Example:* Spoken: *"Overfitting happens when a model performs well on training data but poorly on unseen data."* → OST: `Overfitting` / `Training Data → High Accuracy` / `New Data → Poor Performance`.

### 4.2 Slide Titles & Headings
- **Casing & Style:** Follow **title casing** per the *Chicago Manual of Style*.
- **Word Count:** Maximum **5–7 words** (e.g., *GenAI Tools for Predicting Customer Behavior*). **Avoid one-word titles.**
- **Punctuation:** Use a **colon (`:`)** to separate a title from its subtitle; add **`?`** for question titles.
- **Phrasing Rules:**
  - Use short, incomplete statements (e.g., *Enhanced SWOT Analysis Using GenAI*).
  - For demos, activities, or tool-usage slides, start with an **`-ing` verb** (e.g., *Analyzing Feedback and Performance Data Using GenAI Tools*).
  - Question titles are allowed sparingly, but **avoid starting with "Why"** (e.g., *Why Is Sales Forecasting Necessary?* → *Need for Sales Forecasting*).
- Always include titles/headings to set context for the topic being discussed.

### 4.3 Lead-In Lines, Bullets, Key Phrases & Bottom Lines
| Rule Area | Standard |
| --- | --- |
| **Language & Grammar** | **US English**, grammatically correct, factually accurate, **active voice**, **simple present / present indefinite tense**. |
| **No Title Redundancy** | Do not start the lead-in line with the slide title (e.g., Title: *"What is Microsoft Copilot?"* → Start with *"It is an…"* instead of *"Microsoft Copilot is an…"*). |
| **No Bottom-Line Redundancy** | Bottom line must not repeat content already in the lead-in line or infographic. |
| **Tone** | Lead-in and bottom lines must **not** have a conversational tone (e.g., avoid *"Now, let's see an example of IKEA Place."*). |
| **Pronouns** | **Avoid** first-person pronouns (`I`, `me`, `we`). Second-person (`you`) is permitted. |
| **Prohibited Forms** | Avoid **abbreviations and contractions** (`e.g.`, `i.e.`, `&`, `etc.`, `don't`), **idioms, slang, colloquialisms**, and **generic phrases**. |
| **Periods & Casing** | Complete sentences **must end with a period (`.`)**; incomplete sentences, fragments, and key phrases **must NOT** have periods (Chicago Manual of Style). Use **sentence casing** for bulleted points and key phrases. |
| **Parallelism** | All bulleted points in a list must follow parallel grammatical structure. |
| **Highlighting Text** | **Do not** use single quotes (`'...'`) or double quotes (`"..."`) to emphasize text on screen—use **bold** or *italics* instead. |
| **Numbers** | Spell out numbers **0–9** in narrative text (`two numeric variables`, not `2 numeric variables`; `four missing values`, not `4`) to separate prose from data representation. |
| **Dates** | Always use US English date format **`MM/DD/YYYY`** consistently. |

### 4.4 Conceptual Clarity, Breaks & Video Closings (Blended Learning CE Checklist)
- **Self-Contained Short Phrases:** Even if a learner watches muted, on-screen phrases must be conceptually complete and include key context/keywords.
  - *Bad:* `Points scattered`, `No day extraction`, `No date difference` (ambiguous without verbs/context).
- **Logical Line/Box Breaks:** Never break a sentence at random places just to shorten it or split it across two separate boxes.
- **Logical Link:** If two points appear on one screen, there must be a clear logical connection between them.
- **Preserve Meaning:** Shortening or rephrasing OST must never change the original meaning.
- **Consistent End-of-Video "Next Topic" Statement:** Use one consistent grammatical template across the entire course:
  - *Consistent:* `"In the next topic, you will learn about: Computing…"` / `"In the next topic, you will learn about: Converting, extracting, and performing…"`
  - *Consistent:* `"In the next topic, you will learn how to: Compute…"` / `"In the next topic, you will learn how to: Convert, extract…"`
  - *Incorrect:* Mixing noun/gerund and infinitive forms or using `"In the next topic, you will learn: Computing…"`.
- **Conversational Non-Interactive Closing:** Avoid misleading live-session phrases like *"I'll see you there."* Use clear, pre-recorded transitions such as:
  - *"Let's move to the next topic."*
  - *"Continue to the next lesson to learn more."*
  - *"In the next section, we will explore…"*

---

## 5. Audio, Transcript & Voiceover (VO) Guidelines

### 5.1 Script & Voiceover Standards
- **Language & Pronunciation:** US English; VO pronunciation must follow **Merriam-Webster**.
- **Grammar & Tense:** Grammatically correct, **active voice**, **simple present / present indefinite tense**.
- **Conversational Delivery:** Unlike lead-in OST, both the audio script and VO **should be conversational**.
- **Zero Repetition & Verbatim Alignment:** No repetition in script or VO; conceptually align OST with VO/transcript and avoid verbatim mismatches.
- **Topic Transitions:** Always include a clear transition sentence/phrase/word before shifting topics (e.g., *"Now, let's look at the various uses of Generative AI."*).

### 5.2 Audio Quality Requirements
- Consistent loudness levels throughout the video (enable **Auto-normalize loudness** in Camtasia).
- Free from background noise, echo, stammering, fumbling, glitches, static noise, and long pauses.
- **Pause Limit:** **Maximum 2-second pause** after every sentence.
- **Fallback Captions:** If audio quality drops in any section, add on-screen captions as support.

---

## 6. Visual Design, Typography & Color Palette

### 6.1 Visual Types & Purpose
Every visual must serve a learning purpose (never mere decoration). Validate every asset against: **"Where does the SME talk about this?"**—if there is no answer, remove it (Rule 4).

| Visual Type | Best Used For | Example |
| --- | --- | --- |
| **Concept Diagram** | Explaining how parts relate to a whole | Machine learning pipeline overview |
| **Process Flow** | Showing step-by-step procedures | Data cleaning workflow |
| **Comparison Chart** | Highlighting differences/similarities | Supervised vs. unsupervised learning |
| **Infographic** | Summarizing data or statistics | Key industry trends |
| **Annotated Screenshot** | Walking through a tool or interface | IDE or dashboard walkthrough |
| **Graph or Chart** | Displaying data patterns | Model accuracy over epochs |

### 6.2 Visual Rules, Labeling & Citations
- **One Idea Per Screen:** Do not overload a single frame.
- **Visual Hierarchy:** `Heading → Subheading → Body`, with balanced whitespace.
- **Label Everything (Rule 6):** Learners must never guess what a visual represents (e.g., label `Encoder`, `Decoder`, `Attention Mechanism` on a Transformer diagram and ensure the SME references those labels).
- **Cite Sources (Rule 7):** Place readable, unobtrusive source citations in the **bottom corner** whenever external material or third-party images are used (e.g., `Source: Vaswani et al., Attention Is All You Need` or source URL).
- **Do's and Don'ts (OSL 3.0):**
  - Use **light colors** for shapes/boxes with **`#404040`** text inside.
  - Use **rounded edges only** on shapes and images (`10 px` corner radius in the 70% layout).
  - Use the **updated Simplilearn logo** wherever discussed.
  - **DO NOT** use 3D images, dotted lines, silhouette or black-and-white images, thick outlines, or drop shadows.
  - **DO NOT** squeeze or stretch shapes/images; always maintain aspect ratio and scale proportionally.
  - **DO NOT** use irrelevant stock art (e.g., stock robots when explaining linear regression).
  - Match bullet size and bullet-to-text spacing to the `"logo reference"` library asset.

### 6.3 Typography Specifications
Install the full **Open Sans** font family (`Regular`, `Italic`, `Light`, `Light Italic`, `Semibold`, `Semibold Italic`, `Bold`, `Bold Italic`, `Extrabold`, `Extrabold Italic`) before editing.

| Context | Font Family | Weight / Style | Camtasia Size | After Effects Size | Color |
| --- | --- | --- | --- | --- | --- |
| **Splash Screen — Course Intro Header / Topic Title** | Open Sans | Bold | `45 px` | `44 px` | `#FFFFFF` |
| **Splash Screen — Course Intro Subtitle** | Open Sans | Regular | `45 px` | `44 px` | `#FFFFFF` |
| **Standard Content Screen Body / Bullets** | Open Sans | Regular | `34 px` | `33 px` | `#404040` |

### 6.4 Approved Infographic Color Palette (OSL 3.0)
Use these 10 approved light/pastel tones for diagrams, nodes, category pills, and infographics:

| Swatch | Hex Code | Suggested Role |
| --- | --- | --- |
| Mint / Seafoam | `#8ECDB7` | Category / node accent |
| Sky Blue | `#62B7E4` | Category / node accent |
| Steel Blue | `#7EA2C8` | Category / node accent |
| Lavender / Periwinkle | `#9B99C7` | Category / node accent |
| Mustard Gold | `#DDB945` | Category / node accent |
| Warm Amber | `#E6A157` | Category / node accent |
| Coral / Terracotta | `#E58F6D` | Category / node accent |
| Warm Tan | `#B88968` | Category / node accent |
| Dusty Rose | `#D98CA1` | Category / node accent |
| Soft Lilac | `#C1A5C6` | Category / node accent |

**System UI & Accent Colors:**
- **Highlight / Focus Stroke:** `#F78908` (`3 px` stroke, `1.0 s` draw time)
- **Primary Content Text:** `#404040`
- **Splash Text / End-Dissolve Background:** `#FFFFFF`
- **70% Layout Left Accent Band:** `#2C81FE` *(library gradient/blue band asset)*

---

## 7. Technical Stage Settings, Naming & Packaging

### 7.1 Project & Composition Settings
| Parameter | Camtasia Project Settings | After Effects Composition Settings |
| --- | --- | --- |
| **Dimensions / Resolution** | FHD `1920 × 1080` | `1920 × 1080` (`Full`, `8 bpc`), Square Pixels, `16:9 (1.78)` |
| **Frame Rate** | `30 fps` | `29.97 fps` (`Drop Frame`) |
| **Background Color** | White (`#FFFFFF`) | Pale Blue |
| **Audio** | Auto-normalize loudness: **Enabled** | — |

### 7.2 Raw Trainer Recording Formats
- **Camtasia (`.trec`):** Shared as a zipped `.trec` containing **two layers**: (1) Trainer camera layer, (2) Content background layer.
- **Tella / Other Screen Capture (`.mp4`):** Shared as **two separate MP4 files**: (1) Full-screen SME video, (2) Content/PPT background video.

### 7.3 Folder Structure & Naming Standards
Organize deliverables under the course root folder with numbered lesson subfolders:

```text
Course Name/
├── Lesson_01_Name/
│   ├── Output: 1.01_Course_Introduction.mp4
│   ├── Output: 1.02_What_Will_You_Learn.mp4
│   ├── Source: 1.01_Course_Introduction.zip
│   └── Source: 1.02_What_Will_You_Learn.zip
├── Lesson_02_Name/
│   ├── 2.01_File_Name.mp4  /  2.01_File_Name.zip
│   ├── 2.02_File_Name.mp4  /  2.02_File_Name.zip
│   └── 2.03_File_Name.mp4  /  2.03_File_Name.zip
├── Lesson_03_Name/
│   └── 3.01_File_Name.mp4  /  3.01_File_Name.zip
└── Lesson_04_Name/
    └── 4.01_File_Name.mp4  /  4.01_File_Name.zip
```

- **Output Videos:** `<Lesson>.<TwoDigitTopic>_<Topic_Title>.mp4`
- **Archived Source Projects:** `<Lesson>.<TwoDigitTopic>_<Topic_Title>.zip`

### 7.4 Collecting & Archiving Source Files
Before archiving, **remove all unused/unwanted assets** from the media bin/project:
- **Camtasia:** `File → Export → Zipped Project`
- **After Effects:** `File → Dependencies → Collect Files`

*(Use the official `Camtasia Blended_learning` library assets shared post-POC approval: `Blended Learning workflow`, `Learning objective and What…`, `left_sme`, `S+Right corner+Content 20%`, and `logo reference`.)*

---

## 8. Manim Numerical Layout & Geometry Guidelines

The Camtasia layout diagrams in `OSL_3.0_Post_Production_Guidelines_2026.pdf` (Slides 6, 9, 13, 16, 17, 19, 27, 30) are converted below into exact **Manim 16:9 scene units** (`1920 × 1080`) so animations match the OSL 3.0 templates without manual guesswork.

### 8.1 Manim Coordinate System & Unit Conversions
Standard Manim 16:9 camera (`config.pixel_width = 1920`, `config.pixel_height = 1080`):
- **Frame Width:** $W = \frac{128}{9} \approx 14.222$ units ($x \in [-7.111,\ +7.111]$)
- **Frame Height:** $H = 8.000$ units ($y \in [-4.000,\ +4.000]$)
- **Origin:** $(0,\ 0)$ at screen center ($+X$ right, $+Y$ up)
- **Scale Factor:** $1\text{ Manim unit} = 135\text{ px}$ ($1\text{ px} = \frac{1}{135} \approx 0.007407\text{ units}$)

Conversion from top-left pixel coordinates $(x_{\text{px}}, y_{\text{px}})$ on a $1920 \times 1080$ canvas:

$$x_{\text{manim}} = \left(\frac{x_{\text{px}}}{1920} - 0.5\right) \cdot \frac{128}{9}, \qquad y_{\text{manim}} = \left(0.5 - \frac{y_{\text{px}}}{1080}\right) \cdot 8.0$$

- **Corner Radius (`10 px`):** $10 / 135 \approx \mathbf{0.074}$ Manim units.
- **Highlight Stroke (`3 px`):** $3 / 135 \approx \mathbf{0.022}$ scene units (in Manim's screen-point `stroke_width`, use `stroke_width=3` with `color="#F78908"`, `run_time=1.0`).
- **Typography Scale:**
  - `45 px` (Splash title) $= 45 / 135 = 0.333$ units line-box height (`4.17%` of frame height).
  - `34 px` (Content text) $= 34 / 135 = 0.252$ units line-box height (`3.15%` of frame height; in Manim `Text(..., font="Open Sans")`, scale or calibrate `font_size` so capital/line height matches `~0.25` units).

---

### 8.2 Layout 0: Global Safe Work Area (Slide 9)
All non-edge-bleed content (text, diagrams, cards, labels) must stay inside the green safe area:

| Edge | Margin (% of Canvas) | 1080p Pixels | Manim Units | Safe Boundary |
| --- | --- | --- | --- | --- |
| **Left** | `2.7%` | `52 px` | `0.384 u` | `x_min = -6.727` |
| **Right** | `2.8%` | `53 px` | `0.394 u` | `x_max = +6.717` |
| **Bottom** | `4.2%` | `45 px` | `0.336 u` | `y_min = -3.664` |
| **Top** *(includes title-pill clearance)* | `7.7%` | `84 px` | `0.619 u` | `y_max = +3.381` |

- **Safe Content Box:** `width = 13.44 u` (`1814 px`), `height = 7.04 u` (`950 px`), `center = (-0.005, -0.142)`.
- *(When no top-left title pill is present, a uniform `~0.38–0.40 u` margin on all four sides yields `x ∈ [-6.72, +6.72]`, `y ∈ [-3.60, +3.60]`.)*

---

### 8.3 Layout 1: SME Placement 100% — Full-Screen Presenter (Slide 16)
Used when the SME speaks directly to camera with no slide content overlay:
- **Center:** `(0.000, 0.000)`
- **Dimensions:** `width = 14.222 u`, `height = 8.000 u` (`1920 × 1080 px`, `100% × 100%`)
- **Bounds:** `x ∈ [-7.111, +7.111]`, `y ∈ [-4.000, +4.000]`
- **Corner Radius:** `0`

---

### 8.4 Layout 2: SME Placement 20% — Top-Right PiP + Content / Lead-In (Slides 16, 27, 30)
*(Percentages are calculated assuming a Full HD `1920 × 1080` raw SME recording.)*

| Element | Center `(x, y)` (Manim) | Size `w × h` (Manim) | Bounds `x`, `y` (Manim) | 1080p Equivalent |
| --- | --- | --- | --- | --- |
| **20% SME PiP Box** | `(+5.689, +3.200)` | `2.844 × 1.600 u` (`20% × 20%`) | `x ∈ [+4.267, +7.111]`, `y ∈ [+2.400, +4.000]` | `x=1536, y=0, 384×216 px` |
| **Top-Left Title Pill** *(Slide 30)* | `(-6.087, +3.519)` *(width scales to text)* | `~2.048 × 0.550 u` | `x ∈ [-7.111, -5.063]`, `y ∈ [+3.244, +3.794]` | `x=0, y=28, 277×74 px` |
| **Lead-In Box** *(Slide 27)* | `(+0.210, +2.557)` | `8.135 × 1.037 u` | `x ∈ [-3.857, +4.267]`, `y ∈ [+2.039, +3.075]` | `x=439, y=125, 1098×140 px` |
| **Main Diagram Zone** | `(-0.005, -0.830)` | `13.440 × 5.660 u` | `x ∈ [-6.727, +6.717]`, `y ∈ [-3.664, +2.000]` | `x=52, y=270, 1814×764 px` |

- **Collision Rule (Slide 27):** The lead-in line's right edge must terminate at or left of `x = +4.267` (`80%` of canvas width) so it never overlaps the 20% SME window.
- **Blue Band Transition Rule (Slide 6):** When transitioning from Layout 3 (70%) to Layout 2 (20%), animate the left blue band sliding **off-screen to the left** (`x → -7.111 - band_width/2`).

---

### 8.5 Layout 3: SME Placement 70% — Split Left SME + Right Content Area (Slides 6, 16, 19)
Used for standard concept slides combining a cropped SME feed on the left with a structured visual/bullet panel on the right:

| Element | Center `(x, y)` (Manim) | Size `w × h` (Manim) | Bounds `x`, `y` (Manim) | 1080p Equivalent |
| --- | --- | --- | --- | --- |
| **Left Blue Band** | `(-6.216, 0.000)` *(diag.)* / `(-6.329, 0.000)` *(prod.)* | `(1.565–1.789) × 8.000 u` | `x ∈ [-7.111, -5.546..-5.322]`, `y ∈ [-4.000, +4.000]` | `x=0, y=0, (211–242)×1080 px` |
| **Cropped SME Frame** *(Slide 16 diagram)* | `(-4.334, -0.238)` | `4.626 × 5.435 u` | `x ∈ [-6.647, -2.021]`, `y ∈ [-2.955, +2.479]` | `x=63, y=205, 625×734 px` |
| **Cropped SME Frame** *(Slide 19 prod.)* | `(-3.687, -0.023)` | `4.937 × 5.349 u` | `x ∈ [-6.155, -1.218]`, `y ∈ [-2.698, +2.651]` | `x=129, y=182, 667×722 px` |
| **Safe Content Area** *(Slide 16 outer)* | `(+2.459, -0.046)` | `8.987 × 7.590 u` | `x ∈ [-2.035, +6.952]`, `y ∈ [-3.841, +3.749]` | `x=685, y=34, 1213×1025 px` |
| **Content Card** *(Slide 19 example)* | `(+2.548, +0.319)` | `7.570 × 4.047 u` | `x ∈ [-1.237, +6.333]`, `y ∈ [-1.705, +2.342]` | `x=793, y=224, 1022×546 px` |
| **Content Card Tab** *(Slide 19 example)* | `(+0.464, +2.482)` | `3.401 × 0.375 u` | `x ∈ [-1.237, +2.164]`, `y ∈ [+2.295, +2.670]` | `x=793, y=180, 459×51 px` |

- **Mandatory Corner Radius (Slide 6):** The 70% cropped SME frame must use **`corner_radius = 10 px` (`0.074` Manim units)**.
- **Layering Order:** Background (`#FFFFFF`) → Left Blue Band → Cropped SME RoundedRect (overlaps right edge of blue band) → Right Safe Content Panel.

---

### 8.6 Layout 4: Learning Objective & "What's Next" Template (Slide 17)
- **Left SME Placeholder Zone:** Full-height vertical region on the left (`x ∈ [-7.111, -2.431]` visible; extends behind the overlapping right card).
- **Right Floating White Card:**
  - **Center:** `(+2.037, -0.425)`
  - **Dimensions:** `width = 8.936 u`, `height = 5.674 u` (`1206 × 766 px`, `62.8% × 70.9%`)
  - **Bounds:** `x ∈ [-2.431, +6.505]`, `y ∈ [-3.262, +2.412]`
  - **Margins around Card:** Right `0.606 u` (`82 px`), Bottom `0.738 u` (`100 px`), Top `1.588 u` (`214 px`).

---

### 8.7 Layout 5: Splash Screen — Course Intro & Topic Screen (Slides 13–14)
- **Centered Gradient Pill Banner:**
  - **Center:** `(0.000, -0.022)` *(centered at `(0, 0)`)*
  - **Dimensions:** `width = 11.510 u`, `height = 1.384 u` (`1554 × 187 px`, `80.9% × 17.3%`)
  - **Horizontal Margins:** `1.356 u` (`183 px`, `9.5%`) on both left and right edges
  - **Corner Radius:** `0.692 u` (`93.5 px`, full capsule pill)
  - **Text Spec:** Left-aligned inside pill to the right of the circular icon badge; `Open Sans`, `45 px` (`0.333 u`), `#FFFFFF` (Bold for Topic Title / Course Intro header; Regular for Course Subtitle).

---

### 8.8 Ready-to-Use Manim Layout Constants (Python Reference)

```python
# manim_osl_constants.py — OSL 3.0 Geometry & Style Constants (1920x1080, 16:9)
from dataclasses import dataclass

FRAME_W = 128.0 / 9.0   # 14.2222...
FRAME_H = 8.0
PX_TO_MANIM = 1.0 / 135.0  # 1080 / 8.0 = 135 px per Manim unit

def px(pixels: float) -> float:
    return pixels * PX_TO_MANIM

def px_to_manim(x_px: float, y_px: float) -> tuple[float, float]:
    return ((x_px / 1920.0 - 0.5) * FRAME_W, (0.5 - y_px / 1080.0) * FRAME_H)

# Typography & Visual Accents
FONT_FAMILY = "Open Sans"
SPLASH_FONT_PX = 45          # 0.333 Manim units
CONTENT_FONT_PX = 34         # 0.252 Manim units
CORNER_RADIUS_70 = px(10)    # 0.074 Manim units
HIGHLIGHT_COLOR = "#F78908"
HIGHLIGHT_STROKE_PX = 3
HIGHLIGHT_DRAW_TIME = 1.0
END_DISSOLVE_TIME = 0.5
END_DISSOLVE_COLOR = "#FFFFFF"
TEXT_COLOR = "#404040"

INFOGRAPHIC_PALETTE = [
    "#8ECDB7", "#62B7E4", "#7EA2C8", "#9B99C7", "#DDB945",
    "#E6A157", "#E58F6D", "#B88968", "#D98CA1", "#C1A5C6",
]

@dataclass(frozen=True)
class BoxSpec:
    cx: float
    cy: float
    w: float
    h: float
    corner_radius: float = 0.0

    @property
    def center(self) -> tuple[float, float, float]:
        return (self.cx, self.cy, 0.0)

# Layout 0: Global Safe Work Area
SAFE_WORK_AREA = BoxSpec(cx=-0.005, cy=-0.142, w=13.444, h=7.045)

# Layout 1: 100% SME
SME_100 = BoxSpec(cx=0.0, cy=0.0, w=FRAME_W, h=FRAME_H)

# Layout 2: 20% SME + Lead-In + Content
SME_20 = BoxSpec(cx=5.689, cy=3.200, w=2.844, h=1.600)
TITLE_PILL_20 = BoxSpec(cx=-6.087, cy=3.519, w=2.048, h=0.550, corner_radius=0.275)
LEAD_IN_20 = BoxSpec(cx=0.210, cy=2.557, w=8.135, h=1.037)
CONTENT_20 = BoxSpec(cx=-0.005, cy=-0.832, w=13.444, h=5.664)

# Layout 3: 70% Split SME + Right Safe Content
BLUE_BAND_70 = BoxSpec(cx=-6.216, cy=0.000, w=1.789, h=FRAME_H)
SME_70_DIAGRAM = BoxSpec(cx=-4.334, cy=-0.238, w=4.626, h=5.435, corner_radius=CORNER_RADIUS_70)
SME_70_PROD = BoxSpec(cx=-3.687, cy=-0.023, w=4.937, h=5.349, corner_radius=CORNER_RADIUS_70)
SAFE_CONTENT_70 = BoxSpec(cx=2.459, cy=-0.046, w=8.987, h=7.590)
CONTENT_CARD_70 = BoxSpec(cx=2.548, cy=0.319, w=7.570, h=4.047)
CONTENT_TAB_70 = BoxSpec(cx=0.464, cy=2.482, w=3.401, h=0.375)

# Layout 4: Learning Objective / What's Next Card
LO_CARD = BoxSpec(cx=2.037, cy=-0.425, w=8.936, h=5.674)

# Layout 5: Splash Screen Pill
SPLASH_PILL = BoxSpec(cx=0.000, cy=-0.022, w=11.510, h=1.384, corner_radius=0.692)
```

---

## 9. Checklists & Acceptance Review Rubric

### 9.1 Pre-Production SME Recording Verification (OSL 3.0)
Before starting post-production, verify:
- [ ] SME video is clear, confident, and free from background noise.
- [ ] Explanations are accurate, understandable, and aligned with the approved TOC.
- [ ] Trainer energy level remains consistent throughout the recording.
- [ ] Complete video duration maps cleanly to all TOC topics with no gaps or overlaps.
- [ ] No mispronunciations, incorrect explanations, or unclear delivery (reject and request re-recording if found).
- [ ] Teaching quality meets learner comprehension and engagement standards.
- [ ] All trainer materials have been shared.
- [ ] Camtasia source is a zipped `.trec`, OR Tella/screen-capture provides two separate rendered files (background + SME video).

### 9.2 Learning Design Quick Reference Checklist
- [ ] Learning objective is displayed on screen.
- [ ] Content follows a logical flow (`hook → teach → engage → recap`).
- [ ] Segment is **6–10 minutes** or shorter.
- [ ] On-screen text is readable, well-timed, and non-overlapping.
- [ ] Visuals clarify concepts (never decorative).
- [ ] No split-attention issues (labels integrated into visuals).
- [ ] Cognitive load feels manageable (watch back as a first-time learner).
- [ ] Audio levels are consistent.
- [ ] Visual style is consistent with other videos in the program.

### 9.3 Vendor "Before You Submit" Self-Check (Zero "No" Policy)
*If any answer below is **No**, the video is not ready for submission.*

- **Learning & Structure:** Logically chunked into clear concepts? Consistent instructional flow across similar concepts (`Example → Definition → Visual → Application`)? Preserves SME audio intent?
- **Audio–Visual Alignment:** Every visual directly supports what the SME is saying at that moment? OST limited to keywords/short phrases? No full sentences duplicating narration?
- **Visual Quality:** Diagrams simple, legible, progressively revealed? All images/charts/diagrams clearly labeled? Highlights used sparingly (one at a time)?
- **Relevance & Clarity:** All decorative/irrelevant visuals removed? Nothing on screen that the SME never refers to?
- **Consistency:** Fonts, text sizes, highlights, and layouts consistent across the video? Instructional structure consistent across related concepts?
- **Credibility:** Sources cited wherever external material is referenced?

### 9.4 Common Non-Negotiable Mistakes to Avoid
- Turning videos into slide decks
- Overloading visuals
- Inconsistent teaching structure across related concepts
- Editing for aesthetics instead of learning

### 9.5 Learning Design Acceptance Review Rubric (35 Points Total)

| Criterion | Score Range | Key Evaluation Indicators |
| --- | --- | --- |
| **1. Learning Clarity** | `0–5` | Concepts clearly explained; visuals reduce confusion |
| **2. Structural Consistency** | `0–5` | Consistent instructional flow across related concepts; clear chunking and sequencing |
| **3. Audio–Visual Alignment** | `0–5` | Visuals appear exactly when needed; no redundant or mismatched content |
| **4. Cognitive Load Management** | `0–5` | No text-heavy screens; no unnecessary visuals |
| **5. Visual & Design Consistency** | `0–5` | Fonts, layouts, highlights used consistently |
| **6. Instructional Value of Visuals** | `0–5` | Every visual contributes to understanding |
| **7. Credibility & Accuracy** | `0–5` | Sources cited where required; diagrams accurately represent concepts |

**Scoring Thresholds:**
- **30–35:** Acceptable
- **25–29:** Rework required
- **< 25:** Rejected

