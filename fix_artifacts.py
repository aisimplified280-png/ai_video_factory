"""Fix artifact store hashes and reconcile state."""
import json, hashlib
from pathlib import Path
from production.artifact_store import ArtifactStore, ArtifactEnvelope
from production.artifact_store import ArtifactType as _ArtifactType
from production.artifact_store import ArtifactStatus as _ArtifactStatus
from production.state import ProducerKind as _ProducerKind, ProducerInfo as _ProducerInfo
from datetime import datetime, timezone

store = ArtifactStore(projects_root=Path('projects'))

# Read the current edit_decisions v001
edit_path = Path('projects/proj_3e27bd7a/edit/edit_decisions.v001.json')
with open(edit_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Compute canonical hash
canonical = store.compute_hash(data)
print('Canonical hash:', canonical)

# Create envelope
envelope = ArtifactEnvelope(
    artifact_type='edit_decisions',
    artifact_version=1,
    production_id='proj_3e27bd7a',
    status=_ArtifactStatus.APPROVED,
    content_hash=canonical,
    data=data,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
    producer=_ProducerInfo(kind=_ProducerKind.SYSTEM, provider='phase8_local_render')
)

# Save the envelope
try:
    result = store.save(envelope)
    print('Save succeeded!')
    print('Result:', result)
except Exception as e:
    print('Save failed:', e)
    import traceback
    traceback.print_exc()
"