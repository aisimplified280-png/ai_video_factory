"""Check the edit_decisions audio tracks."""
import json
with open('projects/proj_3e27bd7a/edit/edit_decisions.v002.json') as f:
    edit = json.load(f)
at = edit['data']['audio_tracks']
print('Narration tracks:')
for t in at['narration']:
    eid = t['event_id']
    aaid = t.get('audio_asset_id', 'None')
    print(f'  {eid}: audio_asset_id={aaid}')
print('Music:', at['music'])
print('SFX count:', len(at['sfx']))
for s in at['sfx']:
    print(f'  {s[\"event_id\"]}: asset_id={s.get(\"audio_asset_id\", \"None\")}')