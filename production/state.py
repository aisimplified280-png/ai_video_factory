"""ProductionState persistence — load, save, and manage production state files.

The ProductionState itself is defined in schemas/models/production.py (pure Pydantic).
This module adds the file I/O layer, enforcing atomic writes and consistent paths.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from schemas.models.common import ProductionStatus, RunMode
from schemas.models.production import ProductionState, BudgetState
from schemas.models.pipeline import BudgetPolicy


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STATE_FILENAME = "production_state.json"
_STATE_TMP_SUFFIX = ".tmp"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ProductionStateError(Exception):
    """Base error for production state operations."""


class ProductionNotFoundError(ProductionStateError):
    """Production directory or state file does not exist."""


class ProductionStateCorruptedError(ProductionStateError):
    """State file cannot be parsed or fails validation."""


# ---------------------------------------------------------------------------
# StateStore
# ---------------------------------------------------------------------------

class StateStore:
    """Reads and writes ProductionState to disk.

    Every production has a single state file at:
        projects/<production_id>/production_state.json

    Writes are atomic (tmp → fsync → replace).
    """

    def __init__(self, projects_root: Path) -> None:
        self.projects_root = Path(projects_root)

    def _project_dir(self, production_id: str) -> Path:
        return self.projects_root / production_id

    def _state_path(self, production_id: str) -> Path:
        return self._project_dir(production_id) / _STATE_FILENAME

    @staticmethod
    def _write_atomic(path: Path, content: str) -> None:
        tmp = path.with_suffix(_STATE_TMP_SUFFIX)
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(content)
                fh.flush()
                os.fsync(fh.fileno())
            tmp.replace(path)
        except Exception:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def create(
        self,
        *,
        project_id: str | None = None,
        pipeline: str,
        pipeline_version: str,
        target_duration: float,
        aspect_ratio: str = "9:16",
        platform: str = "youtube_shorts",
        style: str = "auto",
        run_mode: RunMode = RunMode.AUTO,
        budget_cap: float = 10.0,
        metadata: dict | None = None,
    ) -> ProductionState:
        """Create a new ProductionState and persist it immediately.

        Args:
            project_id: If not provided, a short unique ID is generated.
        """
        if project_id is None:
            project_id = f"proj_{uuid.uuid4().hex[:8]}"

        # Validate project_id doesn't already exist
        if self.exists(project_id):
            raise ProductionStateError(
                f"Production {project_id!r} already exists. "
                f"Use load() to resume it."
            )

        now = datetime.now(timezone.utc)
        state = ProductionState(
            project_id=project_id,
            pipeline=pipeline,
            pipeline_version=pipeline_version,
            run_mode=run_mode,
            status=ProductionStatus.CREATED,
            target_duration=target_duration,
            aspect_ratio=aspect_ratio,
            platform=platform,
            style=style,
            budget=BudgetState(budget_cap=budget_cap),
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        self._project_dir(project_id).mkdir(parents=True, exist_ok=True)
        self._write_atomic(self._state_path(project_id), state.to_json())
        return state

    def save(self, state: ProductionState) -> Path:
        """Persist a ProductionState to disk atomically.

        Updates `updated_at` before writing.
        """
        state.updated_at = datetime.now(timezone.utc)
        path = self._state_path(state.project_id)
        self._project_dir(state.project_id).mkdir(parents=True, exist_ok=True)
        self._write_atomic(path, state.to_json())
        return path

    def load(self, production_id: str) -> ProductionState:
        """Load and validate a ProductionState from disk.

        Raises:
            ProductionNotFoundError: if the state file does not exist.
            ProductionStateCorruptedError: if the file is invalid.
        """
        path = self._state_path(production_id)
        if not path.exists():
            raise ProductionNotFoundError(
                f"Production state not found: {path}. "
                f"Has this production been created yet?"
            )
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ProductionStateCorruptedError(
                f"Cannot read production state at {path}: {exc}"
            ) from exc
        try:
            state = ProductionState.from_json(content)
        except Exception as exc:
            raise ProductionStateCorruptedError(
                f"Production state at {path} failed validation: {exc}"
            ) from exc
        return state

    def exists(self, production_id: str) -> bool:
        """Return True if a state file exists for this production_id."""
        return self._state_path(production_id).exists()

    def list_productions(self) -> list[str]:
        """Return all production_ids that have a state file."""
        if not self.projects_root.exists():
            return []
        result = []
        for d in self.projects_root.iterdir():
            if d.is_dir() and (d / _STATE_FILENAME).exists():
                result.append(d.name)
        return sorted(result)

    def update_status(
        self,
        production_id: str,
        status: ProductionStatus,
        current_stage: str | None = None,
    ) -> ProductionState:
        """Convenience: load, update status, save."""
        state = self.load(production_id)
        state.status = status
        if current_stage is not None:
            state.current_stage = current_stage
        self.save(state)
        return state
