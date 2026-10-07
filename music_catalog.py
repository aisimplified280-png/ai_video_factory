"""Music Catalog & Mood Indexer for AI SIMPLIFIED LAB.

Indexes local music tracks into mood/genre categories, enabling:
- Direct user selection in Web UI (by Category or Track)
- Smart AI mood matching based on topic/style
- Resource saving (skips music mixing entirely when 'none' is chosen)
"""
from pathlib import Path
import random
from channel import MUSIC_DIR

CATEGORIES = {
    "chill_lofi": {
        "label": "Chill / Lofi",
        "tracks": [
            "lofi-study-112191.mp3",
            "chill-abstract_intention-12099.mp3",
            "Come Vibe With Me - Patrick Patrikios.mp3",
        ]
    },
    "tech_ambient": {
        "label": "Tech / Ambient",
        "tracks": [
            "Robots and Aliens - Joel Cummins.mp3",
            "Pulsar - The Grey Room _ Density & Time.mp3",
            "Cloud Patterns - Silent Partner.mp3",
        ]
    },
    "energetic_upbeat": {
        "label": "Energetic / Upbeat",
        "tracks": [
            "energetic-rock-trailer-140906.mp3",
            "Loose Slip - Stayloose.mp3",
            "No Sugar - Stayloose.mp3",
        ]
    },
    "cinematic": {
        "label": "Cinematic / Dramatic",
        "tracks": [
            "cinematic-mood-141761.mp3",
            "A Tale of Vengeance - Aakash Gandhi.mp3",
            "The Empty Moons of Jupiter - DivKid.mp3",
        ]
    },
    "upbeat_light": {
        "label": "Upbeat / Light",
        "tracks": [
            "Blue Skies - Silent Partner.mp3",
            "Switched on Carcassi - Brian Bolger.mp3",
        ]
    }
}


def list_music_options():
    """Return category labels and track files for UI selectors (auto-discovers any new .mp3 files)."""
    opts = [{"id": "auto", "label": "✨ Auto (Smart Mood Matching)"},
            {"id": "none", "label": "🚫 No Music (Voiceover Only)"}]
    for cat_id, cat_info in CATEGORIES.items():
        opts.append({"id": f"cat:{cat_id}", "label": f"📁 Category: {cat_info['label']}"})
    
    # Recursive dynamic scan of all .mp3 files in MUSIC_DIR
    for path in sorted(MUSIC_DIR.glob("**/*.mp3")):
        # Calculate relative path to support subfolders
        rel_path = path.relative_to(MUSIC_DIR).as_posix()
        opts.append({"id": f"track:{rel_path}", "label": f"🎵 Track: {path.stem[:40]}"})
    return opts


def get_music_track(selected_opt: str = "auto", topic: str = "", style_name: str = "explainer") -> Path | None:
    """Select background music track based on user selection or smart mood matching."""
    if not selected_opt or selected_opt == "none":
        return None

    if selected_opt.startswith("track:"):
        track_name = selected_opt.split("track:", 1)[1]
        path = MUSIC_DIR / track_name
        if path.exists():
            return path

    if selected_opt.startswith("cat:"):
        cat_id = selected_opt.split("cat:", 1)[1]
        if cat_id in CATEGORIES:
            valid_tracks = [MUSIC_DIR / t for t in CATEGORIES[cat_id]["tracks"] if (MUSIC_DIR / t).exists()]
            if valid_tracks:
                return random.choice(valid_tracks)

    # Smart Auto Matching based on style/topic
    style = style_name.lower()
    top = topic.lower()

    if "comparison" in style or "versus" in top or " vs " in top:
        target_cat = "energetic_upbeat"
    elif "interview" in style or "chat" in top:
        target_cat = "chill_lofi"
    elif "list" in style or "top 5" in top:
        target_cat = "upbeat_light"
    elif "cinematic" in top or "story" in top:
        target_cat = "cinematic"
    else:
        target_cat = "tech_ambient"

    valid_tracks = [MUSIC_DIR / t for t in CATEGORIES[target_cat]["tracks"] if (MUSIC_DIR / t).exists()]
    if valid_tracks:
        return random.choice(valid_tracks)

    # Fallback to any available track
    all_tracks = sorted(MUSIC_DIR.glob("*.mp3"))
    return random.choice(all_tracks) if all_tracks else None


if __name__ == "__main__":
    t = get_music_track("auto", "How does a VPN work?", "explainer")
    print(f"Auto-selected track: {t.name if t else 'None'}")
