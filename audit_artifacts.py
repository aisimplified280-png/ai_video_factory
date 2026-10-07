"""Audit Phase 8B immutable artifacts and verify cleanup safety."""
import json
import hashlib
from pathlib import Path

edit_dir = Path('projects/proj_3e27bd7a/edit')

# Read actual files
v001_path = edit_dir / 'edit_decisions.v001.json'
latest_path = edit_dir / 'edit_decisions.latest.json'

v001_text = v001_path.read_text()
latest_text = latest_path.read_text()

v001_data = json.loads(v001_text)
latest_data = json.loads(latest_text)

print('=== edit_decisions.v001.json ===')
print(f'version: {v001_data.get("version")}')
at = v001_data['data']['audio_tracks']
print(f'narration count: {len(at["narration"])}')
for t in at['narration'][:2]:
    eid = t['event_id']
    aaid = t.get('audio_asset_id', 'N/A')
    print(f'  {eid}: audio_asset_id={aaid}')

print()
print('=== edit_decisions.latest.json ===')
print(f'version: {latest_data.get("version")}')
print(f'file: {latest_data.get("file")}')
print(f'content_hash: {latest_data.get("content_hash")}')

# Compute canonical hash the way ArtifactStore does
canonical = json.dumps(v001_data, sort_keys=True, separators=(',', ':')).encode()
canonical_h = hashlib.sha256(canonical).hexdigest()
print(f'\nCanonical hash of v001 (sort_keys=True, separators=(",", ":")): {canonical_h}')

# Compare with latest.json content_hash
latest_h = latest_data.get('content_hash', '')
print(f'content_hash in .latest.json: {latest_h}')
print(f'Match: {canonical_h == latest_h}')

# Check the cleanup risk
json_files = sorted(edit_dir.glob('*.json'), key=lambda f: f.stat().st_mtime)
print(f'\n=== Cleanup Risk Analysis ===')
print(f'JSON files in edit/: {[f.name for f in json_files]}')
print(f'Number of .json files: {len(json_files)}')

# Simulate the cleanup: sort by mtime descending (newest first), delete files[1:]
json_files_sorted = sorted(json_files, key=lambda f: f.stat().st_mtime, reverse=True)
print(f'Sorted by mtime descending (newest first): {[f.name for f in json_files_sorted]}')
print(f'files[1..$files.Count-1] would delete: {[f.name for f in json_files_sorted[1:]]}')

if len(json_files_sorted) > 1:
    print(f'⚠️  DANGER: files[1] = {json_files_sorted[1].name} would be deleted!')
    print(f'   This is the IMMUTABLE Phase 8B baseline if it is older.')

# Also check edit_summary.md
md_files = list(edit_dir.glob('*.md'))
print(f'\nMD files: {[f.name for f in md_files]}')

print('\n=== Artifact Integrity Summary ===')
print(f'v001 hash: {hashlib.sha256(v001_path.read_bytes()).hexdigest()[:16]}...')
print(f'latest hash: {hashlib.sha256(latest_path.read_bytes()).hexdigest()[:16]}...')
print(f'canonical hash matches latest.content_hash: {canonical_h == latest_h}')