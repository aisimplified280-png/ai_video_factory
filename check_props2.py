"""Check the edit_decisions audio tracks - simpler."""
import json
with open('projects/proj_3e27bd7a/edit/edit_decisions.v002.json') as f:
    edit = json.load(f)
at = edit['data']['audio_tracks']
print('Narration tracks:')
for t in at['narration']:
    eid = t['event_id']
    aaid = t.get('audio_asset_id', 'N/A')
    print('  ' + eid + ': ' + aaid)
print('Music: ' + str(at['music']))
print('SFX count: ' + str(len(at['sfx'])))
for s in at['sfx']:
    eid = s['event_id']
    aaid = s.get('audio_asset_id', 'N/A')
    print('  ' + eid + ': ' + aaid)