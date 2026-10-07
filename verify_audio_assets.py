"""Verify the audio_asset_id updates in edit_decisions."""
import json
from pathlib import Path

edit_path = Path("projects/proj_3e27bd7a/edit/edit_decisions.v001.json")
with open(edit_path, "r", encoding="utf-8") as f:
    edit = json.load(f)

at = edit["data"]["audio_tracks"]

print("Narration audio_asset_ids:")
for t in at["narration"]:
    print(f"  {t['event_id']}: {t['audio_asset_id']}")

print(f"\nMusic: {at['music'][0]['audio_asset_id']}")
print(f"SFX count: {len(at['sfx'])}")

# Verify file existence
print("\nFile existence check:")
audio_dir = Path("projects/proj_3e27bd7a/audio")
for t in at["narration"]:
    asset_id = t["audio_asset_id"]
    if asset_id:
        # Resolve: "projects/proj_3e27bd7a/audio/narration_scene_01.mp3"
        # → factory_root/projects/proj_3e27bd7a/audio/narration_scene_01.mp3
        candidate = Path(asset_id.replace("\\", "/"))
        if candidate.parts[:1] == ("projects",):
            source = Path(".").resolve().parent / candidate
        else:
            source = Path(".").resolve().parent / "projects" / "proj_3e27bd7a" / candidate
        exists = source.is_file()
        print(f"  {t['event_id']}: asset_id={asset_id}")
        print(f"    source={source} exists={exists}")