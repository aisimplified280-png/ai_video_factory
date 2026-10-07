"""Test audio_asset_id path resolution as props_builder.py does."""
import json
from pathlib import Path

# Simulate how props_builder.py resolves audio_asset_id
PROJECT_ROOT = Path('projects/proj_3e27bd7a')
projects_root_parent = Path('projects')

def resolve_source(asset_file):
    candidate = Path(str(asset_file).replace("\\", "/"))
    if candidate.parts[:1] == ("projects",):
        source = projects_root_parent / candidate
    else:
        source = PROJECT_ROOT / candidate
    return source

# Test 1: audio_asset_id = 'projects/audio/narration_scene_01.mp3'
asset_id_1 = 'projects/audio/narration_scene_01.mp3'
source1 = resolve_source(asset_id_1)
print(f'Test 1 - audio_asset_id="{asset_id_1}"')
print(f'  source resolves to: {source1}')
print(f'  exists: {source1.is_file()}')
print()

# Test 2: audio_asset_id = 'projects/proj_3e27bd7a/audio/narration_scene_01.mp3'
asset_id_2 = 'projects/proj_3e27bd7a/audio/narration_scene_01.mp3'
source2 = resolve_source(asset_id_2)
print(f'Test 2 - audio_asset_id="{asset_id_2}"')
print(f'  source resolves to: {source2}')
print(f'  exists: {source2.is_file()}')
print()

# Test 3: Just the filename - won't work without full path
asset_id_3 = 'narration_scene_01.mp3'
source3 = resolve_source(asset_id_3)
print(f'Test 3 - audio_asset_id="{asset_id_3}"')
print(f'  source resolves to: {source3}')
print(f'  exists: {source3.is_file()}')
print()

# Test 4: Full path under projects root
asset_id_4 = 'projects/proj_3e27bd7a/audio/narration_scene_01.mp3'
source4 = resolve_source(asset_id_4)
print(f'Test 4 - audio_asset_id="{asset_id_4}"')
print(f'  source resolves to: {source4}')
print(f'  exists: {source4.is_file()}')