"""Fix .latest.json content_hash to match the actual artifact."""
import json, hashlib
from pathlib import Path

PROJECT_ROOT = Path.cwd()
EDIT_DIR = PROJECT_ROOT / "projects" / "proj_3e27bd7a" / "edit"

V001_PATH = EDIT_DIR / "edit_decisions.v001.json"
LATEST_PATH = EDIT_DIR / "edit_decisions.latest.json"

v001_data = json.loads(V001_PATH.read_text())
latest_data = json.loads(LATEST_PATH.read_text())

# Compute canonical hash
canonical = json.dumps(v001_data, sort_keys=True, separators=(',', ':'))
actual_hash = hashlib.sha256(canonical.encode()).hexdigest()

print(f"Computed canonical hash: {actual_hash}")

# Update latest
latest_data['content_hash'] = f'sha256:{actual_hash}'
latest_data['file'] = 'edit_decisions.v001.json'
LATEST_PATH.write_text(json.dumps(latest_data, indent=2, sort_keys=False))

# Verify
verify = json.loads(LATEST_PATH.read_text())
print(f"Fixed .latest.json content_hash: {verify['content_hash']}")
print(f"Expected: sha256:{actual_hash}")
print(f"Match: {verify['content_hash'] == f'sha256:{actual_hash}'}")