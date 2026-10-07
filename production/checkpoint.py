"""Checkpoint management for crash recovery and state history.

Every significant production state transition persists an immutable checkpoint record in
projects/<production_id>/checkpoints/chk_{seq:04d}_{event_type}.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field

from schemas.models.production import ProductionState


_CHK_PATTERN = re.compile(r"^chk_(\d{4})_(.+)\.json$")
_TMP_SUFFIX = ".tmp"


class Checkpoint(BaseModel):
    """An immutable snapshot summary of a production state boundary."""
    checkpoint_id: str
    production_id: str
    sequence: int = Field(ge=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    stage: str | None = None
    production_status: str
    current_stage: str | None = None
    state_hash: str
    artifact_versions: dict[str, int] = Field(default_factory=dict)
    message: str = ""

    model_config = {"extra": "forbid"}

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "Checkpoint":
        return cls.model_validate_json(json_str)


class CheckpointStore:
    """Manages reading and writing checkpoints for a production."""

    def __init__(self, project_dir: Path, production_id: str) -> None:
        self.project_dir = Path(project_dir)
        self.production_id = production_id
        self.checkpoints_dir = self.project_dir / "checkpoints"

    def _ensure_dir(self) -> None:
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _compute_state_hash(state: ProductionState) -> str:
        canonical = json.dumps(json.loads(state.to_json()), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    def get_next_sequence(self) -> int:
        """Inspect existing checkpoints to determine next sequence number."""
        if not self.checkpoints_dir.exists():
            return 1
        seqs: list[int] = []
        for p in self.checkpoints_dir.glob("chk_*.json"):
            m = _CHK_PATTERN.match(p.name)
            if m:
                seqs.append(int(m.group(1)))
        return max(seqs, default=0) + 1

    def create_checkpoint(
        self,
        state: ProductionState,
        event_type: str,
        stage: str | None = None,
        message: str = "",
    ) -> Checkpoint:
        """Create and atomically persist a new checkpoint."""
        self._ensure_dir()
        seq = self.get_next_sequence()
        clean_event = re.sub(r"[^a-zA-Z0-9_]+", "_", event_type).strip("_").lower()
        chk_id = f"chk_{seq:04d}_{clean_event}"
        state_hash = self._compute_state_hash(state)

        checkpoint = Checkpoint(
            checkpoint_id=chk_id,
            production_id=self.production_id,
            sequence=seq,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            stage=stage,
            production_status=state.status.value,
            current_stage=state.current_stage,
            state_hash=state_hash,
            artifact_versions=dict(state.active_artifact_versions),
            message=message,
        )

        filename = f"{chk_id}.json"
        target_path = self.checkpoints_dir / filename
        tmp_path = target_path.with_suffix(_TMP_SUFFIX)

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(checkpoint.to_json())
                f.flush()
                os.fsync(f.fileno())
            tmp_path.replace(target_path)
        except Exception:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

        return checkpoint

    def list_checkpoints(self) -> list[Checkpoint]:
        """Return all checkpoints ordered by sequence."""
        if not self.checkpoints_dir.exists():
            return []
        checkpoints: list[Checkpoint] = []
        for p in sorted(self.checkpoints_dir.glob("chk_*.json")):
            m = _CHK_PATTERN.match(p.name)
            if m:
                try:
                    chk = Checkpoint.from_json(p.read_text(encoding="utf-8"))
                    checkpoints.append(chk)
                except Exception:
                    continue
        return sorted(checkpoints, key=lambda c: c.sequence)

    def get_latest_checkpoint(self) -> Checkpoint | None:
        """Return the most recent checkpoint, or None."""
        checkpoints = self.list_checkpoints()
        return checkpoints[-1] if checkpoints else None
