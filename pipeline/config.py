"""
Simplilearn OSL 3.0 Post-Production Configuration & Standards
Reference: OSL_3.0_Post_Production_Guidelines_2026.pdf, Learning_Design_Guidelines.pdf,
           OSL SL Guidelines.pdf, OSL_CE Checklist for Blended Learning.pdf
"""

from pathlib import Path

# ==============================================================================
# 1. VIDEO & CANVAS STANDARDS
# ==============================================================================
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
FRAME_RATE = 30
VIDEO_CODEC = "libx264"
VIDEO_PRESET = "fast"
VIDEO_CRF = 18
PIXEL_FORMAT = "yuv420p"

# Outro Animation (OSL 3.0 Page 30: 0.5-second dissolve to White #FFFFFF)
OUTRO_DISSOLVE_COLOR = "#FFFFFF"
OUTRO_DISSOLVE_DURATION = 0.5

# ==============================================================================
# 2. AUDIO & VOICE STANDARDS
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

# ==============================================================================
# 3. SME (TRAINER) PLACEMENT LAYOUTS (OSL 3.0 Page 6 & 16)
# ==============================================================================
# Layout 1: 100% Full-Screen
SME_LAYOUT_100 = {
    "name": "full_screen",
    "width": 1920,
    "height": 1080,
    "x": 0,
    "y": 0,
    "corner_radius": 0
}

# Layout 2: 70% Left-Aligned Rounded Rectangle (Corner Radius = 10 px)
# Used for Learning Objectives, Concept Intro, and What's Next
SME_LAYOUT_70 = {
    "name": "left_70",
    "width": 640,
    "height": 920,
    "x": 80,
    "y": 80,
    "corner_radius": 10,
    "blue_bar_width": 180,
    "blue_bar_color": "0x1A73E8"
}

# Layout 3: 20% Top-Right Corner Picture-In-Picture
# Used when full content/demo screen is active; ensures no overlap with lead-in lines
SME_LAYOUT_20 = {
    "name": "corner_20",
    "width": 384,
    "height": 216,
    "x": 1496,
    "y": 40,
    "corner_radius": 8
}

# ==============================================================================
# 4. TYPOGRAPHY & FONT STANDARDS (OSL 3.0 Page 13-14 & 18)
# ==============================================================================
FONT_FAMILY = "Open Sans"
TITLE_FONT_SIZE = 45        # 44px-45px Bold for Course/Lesson/Topic Title
TITLE_FONT_COLOR = "#FFFFFF"
BODY_FONT_SIZE = 28         # Regular 28px-32px
BODY_FONT_COLOR = "#404040" # Text color inside light cards

# Font file paths (local project fonts)
FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"
OPEN_SANS_REGULAR = FONTS_DIR / "OpenSans-Regular.ttf"
OPEN_SANS_BOLD = FONTS_DIR / "OpenSans-Bold.ttf"
NOTO_SANS_REGULAR = FONTS_DIR / "NotoSans-Regular.ttf"
NOTO_SANS_BOLD = FONTS_DIR / "NotoSans-Bold.ttf"

# ==============================================================================
# 5. APPROVED COLOR PALETTE (OSL 3.0 Page 21 & 25)
# ==============================================================================
COLORS = {
    "primary_blue": "#62B7E4",
    "steel_blue": "#7EA2C8",
    "lavender": "#C1A5C6",
    "soft_violet": "#9B99C7",
    "terracotta": "#B88968",
    "gold_yellow": "#DDB945",
    "warm_tangerine": "#E6A157",
    "soft_coral": "#E58F6D",
    "blush_rose": "#D98CA1",
    "sage_mint": "#8ECDB7",
    "highlight_orange": "#F78908",  # 3px thickness highlight
    "header_navy": "#0B3C5D",      # Voiceover sheet header table background
    "white": "#FFFFFF",
    "dark_gray": "#404040"
}

HIGHLIGHT_COLOR = COLORS["highlight_orange"]
HIGHLIGHT_THICKNESS = 3
DRAW_TIME = 1.0

# ==============================================================================
# 6. RETAKE & FILLER WORDS REMOVAL STANDARDS
# ==============================================================================
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

# Audio/Video Cut Safety Padding (Prevents clipped speech)
CUT_PADDING_SECONDS = 0.20
MERGE_GAP_THRESHOLD = 0.80

# ==============================================================================
# 7. CE (CONTENT EDITOR) & LD (LEARNING DESIGN) RULES
# ==============================================================================
NEXT_TOPIC_PREFIX = "In the next topic, you will learn about:"
MAX_TITLE_WORDS = 7
RECOMMENDED_SEGMENT_MINUTES = (6, 10)

