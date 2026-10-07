"""Check artifact store attributes."""
from pathlib import Path
from production.artifact_store import ArtifactStore

store = ArtifactStore(projects_root=Path("projects"))
attrs = [a for a in dir(store) if not a.startswith("__")]
print("Attributes:", attrs)