"""
Simplilearn OSL 3.0 Post-Production Configuration & Standards
Strictly derived from guidelines.md (compiled from all 5 official OSL documents):
- OSL_3.0_Post_Production_Guidelines_2026.pdf
- Learning_Design_Guidelines.pdf
- LD - Training doc.pdf
- OSL SL Guidelines.pdf
- OSL_CE Checklist for Blended Learning.pdf
"""

from pathlib import Path
import os
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
        if "GOOGLE_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
            os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
        elif "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
        if "CLAUDE_API_KEY" in os.environ and "ANTHROPIC_API_KEY" not in os.environ:
            os.environ["ANTHROPIC_API_KEY"] = os.environ["CLAUDE_API_KEY"]
        elif "ANTHROPIC_API_KEY" in os.environ and "CLAUDE_API_KEY" not in os.environ:
            os.environ["CLAUDE_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
except ImportError:
    pass

# ==============================================================================
# 1. VIDEO & CANVAS STANDARDS (guidelines.md Section 7.1)
# ==============================================================================
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
FRAME_RATE = 30
VIDEO_CODEC = "libx264"
VIDEO_PRESET = "fast"
VIDEO_CRF = 18
PIXEL_FORMAT = "yuv420p"

# Outro Animation (guidelines.md Section 2.4: 0.5-second dissolve to White #FFFFFF)
OUTRO_DISSOLVE_COLOR = "#FFFFFF"
OUTRO_DISSOLVE_DURATION = 0.5

# ==============================================================================
# AUDIO & VOICE STANDARDS (guidelines.md Section 7.2)
# ==============================================================================
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 2
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"

# Broadcast EBU R128 Loudness Normalization
TARGET_I_LUFS = -16.0       # Integrated loudness target
TARGET_TP_DB = -1.0         # True Peak limit
TARGET_LRA = 11.0           # Loudness Range

# Noise Filtering
HIGHPASS_FREQ = 80          # Cut low-frequency rumble below 80 Hz
NOISE_FLOOR_DB = -35.0      # Silence threshold
MIN_SILENCE_DURATION = 1.0  # Seconds of silence before flagging cut

# Filler & Retake Removal Standards
FILLER_WORDS_EN = [
    "uh", "um", "like", "you know", "basically", "so yeah",
    "actually", "sort of", "kind of", "i mean", "right"
]
FILLER_WORDS_HI = [
    "मतलब", "हम्म", "उम्", "तो", "यार"
]
RETAKE_KEYWORDS = [
    "sorry cut", "cut", "start again", "restart", "let me repeat",
    "एक second", "wait", "hold on", "stop", "take two", "sorry"
]
CUT_PADDING_SECONDS = 0.20
MERGE_GAP_THRESHOLD = 0.80

# ==============================================================================
# 2. SME (TRAINER) PLACEMENT LAYOUTS & GEOMETRY (guidelines.md Section 8)
# ==============================================================================
# Layout 1: 100% Full-Screen Presenter (guidelines.md Section 8.3)
SME_LAYOUT_100 = {
    "name": "full_screen",
    "width": 1920,
    "height": 1080,
    "x": 0,
    "y": 0,
    "corner_radius": 0
}

# Layout 3: 70% Left-Aligned Rounded Rectangle (guidelines.md Section 8.5)
# Used for Learning Objectives, Concept Intro, Summary, and What's Next
SME_LAYOUT_70 = {
    "name": "left_70",
    "width": 640,
    "height": 920,
    "x": 80,
    "y": 80,
    "corner_radius": 10,           # Mandatory 10px corner radius (0.074 Manim units)
    "blue_bar_width": 242,         # 211px to 242px width
    "blue_bar_color": "#2C81FE",   # Library blue accent band (guidelines.md line 254)
    "safe_content_x_min": 760,     # Right side content area clearance
    "safe_content_x_max": 1840
}

# Layout 2: 20% Top-Right Corner Picture-In-Picture (guidelines.md Section 8.4)
# Used for Core Concept Breakdown, Demos, Architecture Walkthroughs
SME_LAYOUT_20 = {
    "name": "corner_20",
    "width": 384,                  # 20% of FHD width
    "height": 216,                 # 20% of FHD height
    "x": 1536,                     # Upper right corner flush (or 1496 with margin)
    "y": 0,
    "corner_radius": 10,
    "lead_in_max_x": 1450,         # Collision rule: Lead-in right edge must not cross 1450px
    "diagram_y_min": 270           # Diagram zone stays below y=270px
}

# Global Safe Work Area (guidelines.md Section 8.2)
SAFE_WORK_AREA = {
    "left_margin_px": 52,
    "right_margin_px": 53,
    "top_margin_px": 84,
    "bottom_margin_px": 45,
    "width_px": 1814,
    "height_px": 950
}

# ==============================================================================
# 3. TYPOGRAPHY & FONT STANDARDS (guidelines.md Section 6.3)
# ==============================================================================
FONT_FAMILY = "Open Sans"
TITLE_FONT_SIZE = 45               # 45px Camtasia / 44px After Effects Bold
TITLE_FONT_COLOR = "#FFFFFF"       # White for splash & headers
CONTENT_FONT_SIZE = 34             # 34px Camtasia / 33px After Effects Regular
CONTENT_FONT_COLOR = "#404040"     # Primary content text inside light cards

# Font file paths (local project fonts)
FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
OPEN_SANS_REGULAR = FONTS_DIR / "OpenSans-Regular.ttf"
OPEN_SANS_BOLD = FONTS_DIR / "OpenSans-Bold.ttf"
NOTO_SANS_REGULAR = FONTS_DIR / "NotoSans-Regular.ttf"
NOTO_SANS_BOLD = FONTS_DIR / "NotoSans-Bold.ttf"

# ==============================================================================
# 4. APPROVED COLOR PALETTE (guidelines.md Section 6.4)
# ==============================================================================
# 10 Approved Infographic Pastel Tones
COLORS = {
    "mint_seafoam": "#8ECDB7",     # Mint / Seafoam
    "sky_blue": "#62B7E4",         # Sky Blue
    "steel_blue": "#7EA2C8",       # Steel Blue
    "lavender": "#9B99C7",         # Lavender / Periwinkle
    "mustard_gold": "#DDB945",     # Mustard Gold
    "warm_amber": "#E6A157",       # Warm Amber
    "coral_terracotta": "#E58F6D", # Coral / Terracotta
    "warm_tan": "#B88968",         # Warm Tan
    "dusty_rose": "#D98CA1",       # Dusty Rose
    "soft_lilac": "#C1A5C6",       # Soft Lilac
    # System UI Colors
    "highlight_orange": "#F78908", # Highlight focus: 3px stroke, 1.0s draw time
    "blue_accent_band": "#2C81FE", # 70% layout left band
    "header_navy": "#0B3C5D",      # Banner & table headers
    "white": "#FFFFFF",            # Containers & end-dissolve
    "dark_charcoal": "#404040",    # Primary text color
    "canvas_bg": "#F8FAFC"         # Soft off-white slide background
}

HIGHLIGHT_COLOR = COLORS["highlight_orange"]
HIGHLIGHT_THICKNESS = 3            # Exactly 3 px (0.022 Manim units)
HIGHLIGHT_DRAW_TIME = 1.0          # Exactly 1.0 second draw time

# ==============================================================================
# 5. EDITORIAL & LEARNING DESIGN RULES (guidelines.md Section 2 & 4)
# ==============================================================================
NEXT_TOPIC_PREFIX = "In the next topic, you will learn about:"
MAX_TITLE_WORDS = 7
MIN_TITLE_WORDS = 3
RECOMMENDED_SEGMENT_MINUTES = (6, 10)
MAX_PAUSE_SECONDS = 2.0            # Max 2-second pause after every sentence

# Numbers rule: 0-9 spelled out in prose (guidelines.md Section 4.3)
SPELLED_NUMBERS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
}
