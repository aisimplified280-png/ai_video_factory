"""Update edit_decisions.v001.json to reference generated TTS audio assets.

Sets audio_asset_id for each narration track to the generated MP3 files.
Leaves music_bed and SFX as null (no silent fallback — PropsError will fire
if a referenced file is missing, which is the correct behavior per design).
"""

import json
from pathlib import Path

FACTORY_ROOT = Path(".")
PROJECT_ROOT = FACTORY_ROOT / "projects" / "proj_3e27bd7a"

# Load current edit_decisions
edit_path = PROJECT_ROOT / "edit" / "edit_decisions.v001.json"
with open(edit_path, "r", encoding="utf-8") as f:
    edit = json.load(f)

# The audio_tracks are inside edit["data"]
audio_tracks = edit["data"]["audio_tracks"]

# Generate the audio_asset_id paths
# Resolution: audio_asset_id = "projects/proj_3e27bd7a/audio/{event_id}.mp3"
#   resolves to factory_root/projects/proj_3e27bd7a/audio/{event_id}.mp3
#   which is where generate_audio.py placed the files.
asset_base = "projects/proj_3e27bd7a/audio"

# Update narration tracks (indices 0-5)
narration_tracks = audio_tracks.get("narration", [])
for i, track in enumerate(narration_tracks):
    event_id = track["event_id"]
    # Set audio_asset_id to the generated file
    track["audio_asset_id"] = f"{asset_base}/{event_id}.mp3"
    print(f"Updated {event_id}: audio_asset_id = {track['audio_asset_id']}")

# Leave music track as null (no approved music asset; narration-only is acceptable)
music_track = audio_tracks.get("music", [])
if music_track:
    music_track[0]["audio_asset_id"] = None
    print(f"Updated {music_track[0]['event_id']}: audio_asset_id = None (narration-only)")

# Leave SFX tracks as null (no generated SFX; will PropsError if silently substituted)
sfx_tracks = audio_tracks.get("sfx", [])
for i, track in enumerate(sfx_tracks):
    track["audio_asset_id"] = None
    print(f"Updated {track['event_id']}: audio_asset_id = None (no SFX asset)")

# Write back
with open(edit_path, "w", encoding="utf-8") as f:
    json.dump(edit, f, indent=2)

print(f"\nUpdated {edit_path}")
print("Now re-running render will include actual narration audio.")