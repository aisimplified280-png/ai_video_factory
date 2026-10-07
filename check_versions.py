"""Check all edit_decisions versions and their hashes."""
import json, hashlib
from pathlib import Path

edit_dir = Path('projects/proj_3e27bd7a/edit')

for f in sorted(edit_dir.glob('*.json')):
    if 'edit_decisions' not in f.name:
        continue
    data = json.load(open(f, 'r', encoding='utf-8'))
    canonical_h = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    print(f.name + ':')
    print('  canon: sha256:' + canonical_h)
    name = f.name.replace('edit_decisions.', '').replace('.json', '')
    print('  version: ' + name)
    print()