"""Check the artifact store stage directories."""
from pathlib import Path
from production.artifact_store import ArtifactStore

store = ArtifactStore(projects_root=Path("projects"))
print("stage_dirs():", store.stage_dirs())