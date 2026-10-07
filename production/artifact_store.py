"""ArtifactStore — the single persistence abstraction for all production artifacts.

ALL artifact I/O must go through this class. No stage should invent its own
JSON writing convention. Guarantees:

  - Atomic writes (write tmp → fsync → replace)
  - Deterministic content hashing (canonical JSON, key-sorted, no whitespace)
  - Immutable approved artifacts (cannot overwrite approved version with new data)
  - Versioned storage (artifact_type.v001.json, .v002.json, …)
  - Active-version pointer (.latest) always consistent
  - JSON schema validation at persistence boundary
  - Corrupted or hash-mismatched artifacts are detected at load time
  - Type-safety: saves reject mismatched artifact_type / stage / production_id
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from schemas.models.artifact import ArtifactEnvelope, ArtifactState, ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ArtifactStoreError(Exception):
    """Base class for all ArtifactStore errors."""


class ImmutableArtifactError(ArtifactStoreError):
    """Raised when attempting to overwrite an approved artifact with new data."""


class ArtifactNotFoundError(ArtifactStoreError):
    """Raised when a requested artifact does not exist."""


class ArtifactHashMismatchError(ArtifactStoreError):
    """Raised when the loaded artifact's content_hash does not match the data."""


class ArtifactCorruptedError(ArtifactStoreError):
    """Raised when the artifact file cannot be parsed."""


class ArtifactTypeMismatchError(ArtifactStoreError):
    """Raised when artifact_type, stage, or production_id don't match expectations."""


class ArtifactSchemaError(ArtifactStoreError):
    """Raised when an artifact fails JSON schema validation."""


class ArtifactVersionError(ArtifactStoreError):
    """Raised when version numbering is inconsistent."""


# ---------------------------------------------------------------------------
# Stage-to-directory mapping
# ---------------------------------------------------------------------------

STAGE_DIRS: dict[str, str] = {
    "research": "research",
    "proposal": "proposal",
    "script": "script",
    "art_direction": "direction",
    "scene_plan": "scenes",
    "assets": "assets",
    "edit": "edit",
    "compose": "composition",
    "audio": "audio",
    "review": "review",
    "qa": "qa",
    "publish": "publish",
    "brief": "brief",
}

# Artifact type → stage it belongs to (derived from pipeline definitions).
# This is the authoritative mapping used for type-safety checks.
ARTIFACT_STAGE_MAP: dict[str, str] = {
    "research_brief": "research",
    "proposal_packet": "proposal",
    "script": "script",
    "art_direction": "art_direction",
    "scene_plan": "scene_plan",
    "asset_manifest": "assets",
    "edit_decisions": "edit",
    "render_report": "compose",
    "review_report": "review",
    "qa_report": "qa",
    "publish_log": "publish",
}

# Filename patterns
_VERSION_PATTERN = re.compile(r"^(.+)\.v(\d{3})\.json$")
_LATEST_SUFFIX = ".latest.json"
_TMP_SUFFIX = ".tmp"


# ---------------------------------------------------------------------------
# ArtifactStore
# ---------------------------------------------------------------------------

class ArtifactStore:
    """Atomic, versioned, schema-validated artifact persistence.

    Args:
        projects_root: Root directory under which per-production project dirs live.
            Typically the ``output/`` directory of the workspace, or a custom path.
        schemas_root: Directory containing JSON schema files.
            Defaults to ``schemas/`` relative to this file.
    """

    def __init__(
        self,
        projects_root: Path,
        schemas_root: Path | None = None,
    ) -> None:
        self.projects_root = Path(projects_root)
        if schemas_root is None:
            schemas_root = Path(__file__).resolve().parent.parent / "schemas"
        self.schemas_root = Path(schemas_root)

        # Schema cache: {artifact_type: compiled jsonschema validator}
        self._schema_cache: dict[str, Any] = {}
        self._envelope_schema: dict | None = None

    # ------------------------------------------------------------------
    # Hash
    # ------------------------------------------------------------------

    @staticmethod
    def compute_hash(data: dict[str, Any]) -> str:
        """Deterministic SHA-256 of `data`, independent of key order and whitespace.

        Returns a string in the form ``sha256:<64-hex-chars>``.
        """
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    # ------------------------------------------------------------------
    # Schema loading
    # ------------------------------------------------------------------

    def _load_envelope_schema(self) -> dict:
        if self._envelope_schema is None:
            path = self.schemas_root / "artifact_envelope.schema.json"
            if not path.exists():
                raise ArtifactStoreError(f"Envelope schema not found: {path}")
            self._envelope_schema = json.loads(path.read_text(encoding="utf-8"))
        return self._envelope_schema

    def _load_artifact_schema(self, artifact_type: str) -> dict | None:
        """Load the artifact-specific schema if it exists; return None if not found."""
        if artifact_type in self._schema_cache:
            return self._schema_cache[artifact_type]
        path = self.schemas_root / "artifacts" / f"{artifact_type}.schema.json"
        if not path.exists():
            return None
        schema = json.loads(path.read_text(encoding="utf-8"))
        self._schema_cache[artifact_type] = schema
        return schema

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def _project_dir(self, production_id: str) -> Path:
        return self.projects_root / production_id

    def _stage_dir(self, production_id: str, stage: str) -> Path:
        dir_name = STAGE_DIRS.get(stage, stage)
        return self._project_dir(production_id) / dir_name

    @staticmethod
    def _versioned_filename(artifact_type: str, version: int) -> str:
        return f"{artifact_type}.v{version:03d}.json"

    @staticmethod
    def _latest_filename(artifact_type: str) -> str:
        return f"{artifact_type}{_LATEST_SUFFIX}"

    # ------------------------------------------------------------------
    # Atomic write
    # ------------------------------------------------------------------

    @staticmethod
    def _write_atomic(path: Path, content: str) -> None:
        """Write `content` to `path` atomically.

        Uses write-to-tmp → fsync → rename so a crash never leaves a
        half-written file as the active artifact.
        """
        tmp = path.with_suffix(_TMP_SUFFIX)
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(content)
                fh.flush()
                os.fsync(fh.fileno())
            # Windows-safe atomic replace with retry loop and fallback
            for attempt in range(5):
                try:
                    tmp.replace(path)
                    break
                except (PermissionError, OSError):
                    if attempt == 4:
                        import shutil
                        shutil.copyfile(tmp, path)
                        try:
                            tmp.unlink(missing_ok=True)
                        except OSError:
                            pass
                        break
                    import time
                    time.sleep(0.05 * (attempt + 1))
        except Exception:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    # ------------------------------------------------------------------
    # create()
    # ------------------------------------------------------------------

    def create(
        self,
        artifact_type: str,
        production_id: str,
        stage: str,
        data: dict[str, Any],
        producer: ProducerInfo,
        parent_artifacts: list | None = None,
        warnings: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactEnvelope:
        """Construct a new ArtifactEnvelope (does NOT persist — call save() after).

        Automatically determines the next version number by inspecting what
        already exists on disk.
        """
        existing = self.list_versions(artifact_type, production_id)
        next_version = max(existing, default=0) + 1
        now = datetime.now(timezone.utc)
        content_hash = self.compute_hash(data)

        return ArtifactEnvelope(
            artifact_type=artifact_type,
            schema_version="2.0",
            artifact_version=next_version,
            production_id=production_id,
            stage=stage,
            status=ArtifactStatus.PENDING,
            created_at=now,
            updated_at=now,
            producer=producer,
            content_hash=content_hash,
            data=data,
            parent_artifacts=parent_artifacts or [],
            warnings=warnings or [],
            metadata=metadata or {},
        )

    # ------------------------------------------------------------------
    # save()
    # ------------------------------------------------------------------

    def save(self, envelope: ArtifactEnvelope) -> Path:
        """Atomically persist an artifact envelope.

        Raises:
            ImmutableArtifactError: if this version already exists on disk as APPROVED.
            ArtifactTypeMismatchError: if type/stage/production_id are inconsistent.
            ArtifactSchemaError: if the envelope fails JSON schema validation.
            ArtifactHashMismatchError: if the provided hash doesn't match the data.
        """
        # 1. Type safety checks
        self._check_type_consistency(envelope)

        # 2. Verify hash integrity
        expected_hash = self.compute_hash(envelope.data)
        if envelope.content_hash != expected_hash:
            raise ArtifactHashMismatchError(
                f"content_hash mismatch for {envelope.artifact_type} v{envelope.artifact_version}: "
                f"stored={envelope.content_hash!r}, computed={expected_hash!r}"
            )

        # 3. Immutability: cannot overwrite an approved version with new data
        existing = self._load_raw_by_version(
            envelope.artifact_type, envelope.production_id, envelope.artifact_version
        )
        if existing is not None and existing.get("status") == ArtifactStatus.APPROVED.value:
            # Status-only changes go through _update_status(); data changes must be a new version
            if existing.get("content_hash") != envelope.content_hash:
                raise ImmutableArtifactError(
                    f"{envelope.artifact_type} v{envelope.artifact_version} is APPROVED "
                    f"and cannot be overwritten with different data. "
                    f"Create a new version instead."
                )

        # 4. Schema validation
        self.validate(envelope)

        # 5. Prepare directory
        stage_dir = self._stage_dir(envelope.production_id, envelope.stage)
        stage_dir.mkdir(parents=True, exist_ok=True)

        # 6. Atomic write of versioned file
        filename = self._versioned_filename(envelope.artifact_type, envelope.artifact_version)
        filepath = stage_dir / filename
        self._write_atomic(filepath, envelope.model_dump_json(indent=2))

        # 7. Update latest pointer atomically
        latest_path = stage_dir / self._latest_filename(envelope.artifact_type)
        self._write_atomic(latest_path, json.dumps({
            "version": envelope.artifact_version,
            "file": filename,
            "status": envelope.status.value,
            "content_hash": envelope.content_hash,
            "updated_at": envelope.updated_at.isoformat(),
        }, indent=2))

        return filepath

    # ------------------------------------------------------------------
    # load()
    # ------------------------------------------------------------------

    def load(
        self,
        artifact_type: str,
        production_id: str,
        version: int | None = None,
    ) -> ArtifactEnvelope:
        """Load an artifact by version, or the latest version if version is None.

        Raises:
            ArtifactNotFoundError: if the artifact does not exist.
            ArtifactCorruptedError: if the file cannot be parsed.
            ArtifactHashMismatchError: if the loaded hash does not match data.
        """
        if version is None:
            return self.latest(artifact_type, production_id)
        return self._load_by_version(artifact_type, production_id, version)

    def _load_by_version(
        self,
        artifact_type: str,
        production_id: str,
        version: int,
    ) -> ArtifactEnvelope:
        # Try all known stage directories for this production
        for stage_dir_name in STAGE_DIRS.values():
            path = self._project_dir(production_id) / stage_dir_name / \
                   self._versioned_filename(artifact_type, version)
            if path.exists():
                return self._load_and_verify(path, artifact_type, production_id)
        raise ArtifactNotFoundError(
            f"Artifact {artifact_type} v{version:03d} not found for production {production_id!r}"
        )

    def _load_raw_by_version(
        self,
        artifact_type: str,
        production_id: str,
        version: int,
    ) -> dict | None:
        """Load raw dict without full Pydantic validation (used for immutability checks)."""
        for stage_dir_name in STAGE_DIRS.values():
            path = self._project_dir(production_id) / stage_dir_name / \
                   self._versioned_filename(artifact_type, version)
            if path.exists():
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    return None
        return None

    def _load_and_verify(
        self,
        path: Path,
        expected_type: str,
        expected_production_id: str,
    ) -> ArtifactEnvelope:
        """Parse, Pydantic-validate, and hash-verify an artifact file."""
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ArtifactCorruptedError(f"Cannot parse artifact at {path}: {exc}") from exc

        try:
            envelope = ArtifactEnvelope.model_validate(raw)
        except Exception as exc:
            raise ArtifactCorruptedError(
                f"Artifact at {path} failed Pydantic validation: {exc}"
            ) from exc

        # Verify type and production_id match
        if envelope.artifact_type != expected_type:
            raise ArtifactTypeMismatchError(
                f"Expected artifact_type={expected_type!r} but got {envelope.artifact_type!r} "
                f"in {path}"
            )
        if envelope.production_id != expected_production_id:
            raise ArtifactTypeMismatchError(
                f"Expected production_id={expected_production_id!r} but got "
                f"{envelope.production_id!r} in {path}"
            )

        # Verify hash
        computed = self.compute_hash(envelope.data)
        if envelope.content_hash != computed:
            raise ArtifactHashMismatchError(
                f"Hash mismatch in {path}: "
                f"stored={envelope.content_hash!r}, computed={computed!r}"
            )

        return envelope

    # ------------------------------------------------------------------
    # exists()
    # ------------------------------------------------------------------

    def exists(
        self,
        artifact_type: str,
        production_id: str,
        version: int | None = None,
    ) -> bool:
        """Return True if the artifact (any or specific version) exists on disk."""
        if version is not None:
            return self._find_versioned_file(artifact_type, production_id, version) is not None
        return bool(self.list_versions(artifact_type, production_id))

    def _find_versioned_file(
        self, artifact_type: str, production_id: str, version: int
    ) -> Path | None:
        for stage_dir_name in STAGE_DIRS.values():
            path = self._project_dir(production_id) / stage_dir_name / \
                   self._versioned_filename(artifact_type, version)
            if path.exists():
                return path
        return None

    # ------------------------------------------------------------------
    # list_versions()
    # ------------------------------------------------------------------

    def list_versions(
        self,
        artifact_type: str,
        production_id: str,
    ) -> list[int]:
        """Return sorted list of persisted version numbers for an artifact type."""
        versions: list[int] = []
        proj_dir = self._project_dir(production_id)
        if not proj_dir.exists():
            return versions

        for stage_dir_name in STAGE_DIRS.values():
            stage_dir = proj_dir / stage_dir_name
            if not stage_dir.is_dir():
                continue
            for f in stage_dir.iterdir():
                m = _VERSION_PATTERN.match(f.name)
                if m and m.group(1) == artifact_type:
                    versions.append(int(m.group(2)))

        return sorted(set(versions))

    # ------------------------------------------------------------------
    # latest()
    # ------------------------------------------------------------------

    def latest(self, artifact_type: str, production_id: str) -> ArtifactEnvelope:
        """Load the highest-version artifact, verifying via the .latest pointer."""
        # First try the .latest pointer for O(1) lookup
        for stage_dir_name in STAGE_DIRS.values():
            latest_path = self._project_dir(production_id) / stage_dir_name / \
                          self._latest_filename(artifact_type)
            if latest_path.exists():
                try:
                    ptr = json.loads(latest_path.read_text(encoding="utf-8"))
                    version = int(ptr["version"])
                    return self._load_by_version(artifact_type, production_id, version)
                except (KeyError, ValueError, ArtifactNotFoundError):
                    pass  # Fall through to scan

        # Fallback: scan all versions
        versions = self.list_versions(artifact_type, production_id)
        if not versions:
            raise ArtifactNotFoundError(
                f"No versions of {artifact_type!r} found for production {production_id!r}"
            )
        return self._load_by_version(artifact_type, production_id, max(versions))

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    def _update_status(
        self,
        artifact_type: str,
        production_id: str,
        version: int,
        new_status: ArtifactStatus,
    ) -> ArtifactEnvelope:
        """Internal: change status of an existing artifact version atomically."""
        envelope = self._load_by_version(artifact_type, production_id, version)
        # Build updated envelope (Pydantic models are immutable — create new instance)
        updated = envelope.model_copy(update={
            "status": new_status,
            "updated_at": datetime.now(timezone.utc),
        })
        # For status updates, write directly without the immutability check
        # (immutability blocks new DATA writes, not status transitions)
        stage_dir = self._stage_dir(production_id, envelope.stage)
        filename = self._versioned_filename(artifact_type, version)
        filepath = stage_dir / filename
        self._write_atomic(filepath, updated.model_dump_json(indent=2))

        # Update latest pointer
        latest_path = stage_dir / self._latest_filename(artifact_type)
        # Only update latest pointer if this is the current latest version
        current_versions = self.list_versions(artifact_type, production_id)
        if current_versions and max(current_versions) == version:
            self._write_atomic(latest_path, json.dumps({
                "version": version,
                "file": filename,
                "status": new_status.value,
                "content_hash": updated.content_hash,
                "updated_at": updated.updated_at.isoformat(),
            }, indent=2))

        return updated

    def approve(
        self,
        artifact_type: str,
        production_id: str,
        version: int,
        actor: str = "",
    ) -> ArtifactEnvelope:
        """Approve an artifact version. Approved artifacts become immutable."""
        envelope = self._load_by_version(artifact_type, production_id, version)
        if envelope.status not in (ArtifactStatus.READY, ArtifactStatus.PENDING):
            raise ArtifactStoreError(
                f"Cannot approve {artifact_type} v{version}: status is {envelope.status.value}, "
                f"expected 'ready' or 'pending'"
            )
        return self._update_status(artifact_type, production_id, version, ArtifactStatus.APPROVED)

    def reject(
        self,
        artifact_type: str,
        production_id: str,
        version: int,
        reason: str = "",
    ) -> ArtifactEnvelope:
        """Reject an artifact version. A new version should be created next."""
        envelope = self._load_by_version(artifact_type, production_id, version)
        if envelope.status == ArtifactStatus.APPROVED:
            raise ImmutableArtifactError(
                f"Cannot reject {artifact_type} v{version}: already APPROVED"
            )
        updated = self._update_status(
            artifact_type, production_id, version, ArtifactStatus.REJECTED
        )
        return updated

    def mark_ready(
        self,
        artifact_type: str,
        production_id: str,
        version: int,
    ) -> ArtifactEnvelope:
        """Mark an artifact as ready (passed generation, ready for review)."""
        return self._update_status(
            artifact_type, production_id, version, ArtifactStatus.READY
        )

    def mark_failed(
        self,
        artifact_type: str,
        production_id: str,
        version: int,
    ) -> ArtifactEnvelope:
        """Mark an artifact as failed (generation error)."""
        return self._update_status(
            artifact_type, production_id, version, ArtifactStatus.FAILED
        )

    # ------------------------------------------------------------------
    # validate()
    # ------------------------------------------------------------------

    def validate(self, envelope: ArtifactEnvelope) -> None:
        """Validate an artifact envelope against its JSON schema.

        Validates in two passes:
        1. Envelope schema (structure, required fields, formats)
        2. Artifact-specific schema (data payload)

        Raises ArtifactSchemaError on any validation failure.
        """
        raw = json.loads(envelope.model_dump_json())

        # Pass 1: envelope schema
        env_schema = self._load_envelope_schema()
        try:
            jsonschema.validate(raw, env_schema, format_checker=jsonschema.FormatChecker())
        except jsonschema.ValidationError as exc:
            raise ArtifactSchemaError(
                f"Envelope schema validation failed for {envelope.artifact_type} "
                f"v{envelope.artifact_version}: {exc.message}"
            ) from exc

        # Pass 2: artifact-specific schema (if available)
        art_schema = self._load_artifact_schema(envelope.artifact_type)
        if art_schema is not None:
            try:
                # Resolve $ref in artifact schema pointing to envelope schema
                schema_file = self.schemas_root / "artifacts" / f"{envelope.artifact_type}.schema.json"
                env_file = self.schemas_root / "artifact_envelope.schema.json"
                store = {
                    "../artifact_envelope.schema.json": env_schema,
                    env_file.as_uri(): env_schema,
                    "artifact_envelope.schema.json": env_schema,
                    "artifact_envelope": env_schema,
                    (self.schemas_root / "artifact_envelope").as_uri(): env_schema,
                }
                resolver = jsonschema.RefResolver(
                    base_uri=schema_file.as_uri(),
                    referrer=art_schema,
                    store=store,
                )
                validator = jsonschema.Draft202012Validator(
                    art_schema,
                    resolver=resolver,
                    format_checker=jsonschema.FormatChecker(),
                )
                validator.validate(raw)
            except jsonschema.ValidationError as exc:
                raise ArtifactSchemaError(
                    f"Artifact schema validation failed for {envelope.artifact_type} "
                    f"v{envelope.artifact_version}: {exc.message}"
                ) from exc

    # ------------------------------------------------------------------
    # Type consistency checks
    # ------------------------------------------------------------------

    def _check_type_consistency(self, envelope: ArtifactEnvelope) -> None:
        """Ensure artifact_type, stage, and production_id are mutually consistent."""
        # Check that artifact_type is saved under its correct stage
        expected_stage = ARTIFACT_STAGE_MAP.get(envelope.artifact_type)
        if expected_stage is not None and envelope.stage != expected_stage:
            raise ArtifactTypeMismatchError(
                f"artifact_type={envelope.artifact_type!r} must be saved under "
                f"stage={expected_stage!r}, but envelope.stage={envelope.stage!r}"
            )

    # ------------------------------------------------------------------
    # to_artifact_state()
    # ------------------------------------------------------------------

    def to_artifact_state(self, envelope: ArtifactEnvelope) -> ArtifactState:
        """Convert a loaded envelope into an ArtifactState summary for ProductionState."""
        versions = self.list_versions(envelope.artifact_type, envelope.production_id)
        latest_version = max(versions) if versions else envelope.artifact_version
        return ArtifactState(
            artifact_type=envelope.artifact_type,
            latest_version=latest_version,
            active_version=envelope.artifact_version,
            status=envelope.status,
            content_hash=envelope.content_hash,
            stage=envelope.stage,
            updated_at=envelope.updated_at,
        )
