"""Generate TTS audio for Phase 8B production render.

Uses edge-tts (already installed) to produce narration from the project script.
Audio files are placed where props_builder.py expects them.
"""

import json
import os
import asyncio
from pathlib import Path

import edge_tts  # confirmed working on Windows

# Configuration
FACTORY_ROOT = Path(".")
PROJECT_ROOT = FACTORY_ROOT / "projects" / "proj_3e27bd7a"
AUDIO_DIR = PROJECT_ROOT / "audio"

os.makedirs(AUDIO_DIR, exist_ok=True)

# Load script and edit_decisions
script = json.load(open(PROJECT_ROOT / "script" / "script.v001.json"))
edit = json.load(open(PROJECT_ROOT / "edit" / "edit_decisions.v001.json"))

sections = script["data"]["sections"]
narration_tracks = edit["data"]["audio_tracks"]["narration"]

# Voice - JennyNeural is confirmed working on Windows with edge-tts
VOICE = "en-US-JennyNeural"

print(f"Generating TTS audio for {len(narration_tracks)} narration clips...")
print("=" * 60)

for i, track in enumerate(narration_tracks):
    req = track["audio_requirement"]
    spoken_text = req["spoken_text"]
    event_id = track["event_id"]

    # Use edge-tts to generate and save MP3
    communicate = edge_tts.Communicate(spoken_text, VOICE)

    # save() is a coroutine; run via asyncio
    asyncio.run(communicate.save(str(AUDIO_DIR / f"{event_id}.mp3")))

    # Verify file exists and has content
    output_path = AUDIO_DIR / f"{event_id}.mp3"
    if output_path.exists():
        size = output_path.stat().st_size
        print(f"  {event_id}: OK ({size} bytes)")
        print(f"    Text: {spoken_text[:60]}...")
    else:
        print(f"  {event_id}: FAILED - file not created")

print("=" * 60)
print("TTS audio generation complete.")
print(f"Audio files located at: {AUDIO_DIR}")

# List generated files
for f in sorted(AUDIO_DIR.glob("*.mp3")):
    print(f"  - {f.name} ({f.stat().st_size} bytes)")