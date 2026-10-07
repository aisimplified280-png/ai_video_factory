"""Check audio setup."""
import json
from pathlib import Path

# Check props
with open('projects/proj_3e27bd7a/composition/remotion_work/props.json') as f:
    props = json.load(f)

audio_tracks = props.get('audio', [])
print('Audio tracks in props:', len(audio_tracks))
for a in audio_tracks:
    eid = a['event_id']
    pp = a.get('publicPath', 'None')
    print('  ' + eid + ': publicPath=' + str(pp))

# Check if audio files exist
AUDIO_DIR = Path('projects/proj_3e27bd7a/audio')
print()
for a in audio_tracks:
    eid = a['event_id']
    pp = a.get('publicPath')
    if pp:
        # The publicPath is like 'assets/narration_scene_01.mp3'
        # props_builder copies to composer_public/assets/
        expected = Path('remotion-composer/public') / pp
        print('  ' + eid + ': file=' + str(expected.exists()) + ' at ' + str(expected))

# Check original MP4
mp4_path = Path('projects/proj_3e27bd7a/composition/remotion_edit-v001.mp4')
print('Original MP4 exists:', mp4_path.exists())

# Check original render manifest
manifest_path = Path('projects/proj_3e27bd7a/composition/remotion_work/render_manifest.json')
if manifest_path.exists():
    with open(manifest_path) as f:
        m = json.load(f)
    at_m = m.get('audio_tracks', [])
    print('Original render audio_tracks:')
    for a in at_m:
        eid = a.get('event_id', '?')
        file_val = a.get('file', '?')
        print('  ' + eid + ': file=' + str(file_val))