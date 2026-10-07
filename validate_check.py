"""Validate Phase 9 spec against Phase 8B codebase."""
import json, hashlib
from pathlib import Path

# Read the actual edit_decisions v001
with open('projects/proj_3e27bd7a/edit/edit_decisions.v001.json', 'r', encoding='utf-8') as f:
    edit = json.load(f)

at = edit['data']['audio_tracks']
print('Current Audio Tracks:')
for t in at['narration']:
    eid = t['event_id']
    aaid = t.get('audio_asset_id', 'N/A')
    print('  ' + eid + ': audio_asset_id=' + aaid)
print('Music: ' + str(at['music']))
print('SFX count: ' + str(len(at['sfx'])))

# Check the canonical hash
with open('projects/proj_3e27bd7a/edit/edit_decisions.v001.json', 'rb') as f:
    raw_h = hashlib.sha256(f.read()).hexdigest()
print('Raw file hash: ' + raw_h)

# Check the .latest.json
latest_path = Path('projects/proj_3e27bd7a/edit/edit_decisions.latest.json')
with open(latest_path, 'r', encoding='utf-8') as f:
    latest = json.load(f)
print('Latest pointer:')
print('  version: ' + str(latest['version']))
print('  file: ' + latest['file'])
print('  content_hash: ' + latest['content_hash'])