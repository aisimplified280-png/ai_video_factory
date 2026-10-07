"""List edit_decisions versions."""
from pathlib import Path
from production.artifact_store import ArtifactStore

store = ArtifactStore(projects_root=Path("projects"))
versions = store.list_versions("edit_decisions", "proj_3e27bd7a")
print("Versions:", versions)