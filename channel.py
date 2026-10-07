"""Channel configuration for AI SIMPLIFIED LAB.

All branding assets, paths, and channel-specific settings.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "AI SIMPLIFIED LAB"

# ── Channel Identity ─────────────────────────────────────────────────────
CHANNEL_NAME = "AI SIMPLIFIED LAB"
CHANNEL_TAGLINE = "Simplifying Complex Tech"

# ── Asset Paths ──────────────────────────────────────────────────────────
LOGO = ASSETS / "channel logo" / "Generated Image October 24, 2025 - 3_22PM.png"
STICKMAN = {
    "neutral": ASSETS / "Stickman" / "neutral.png",
    "left": ASSETS / "Stickman" / "left.png",
    "right": ASSETS / "Stickman" / "right.png",
}
INTROS = sorted((ASSETS / "intro").glob("intro*.mp4"))
OUTROS = sorted((ASSETS / "outro").glob("*.mp4"))
SUBSCRIBE = ASSETS / "Subsribe" / "profounder_com_0b9ab3efcc9133494f051cbd3cb62eb2-4e8c4d06073ea8c3c40a-webm_transparent.webm"
MUSIC_DIR = ASSETS / "music"
MUSIC_TRACKS = sorted(MUSIC_DIR.glob("*.mp3"))

# ── Brand Colours ────────────────────────────────────────────────────────
BRAND_BLUE = "#1A5CFF"
BRAND_DARK = "#0A0A0A"
BRAND_WHITE = "#FFFFFF"
BRAND_ACCENT = "#EE6C4D"
