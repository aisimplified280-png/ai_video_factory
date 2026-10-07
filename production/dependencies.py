"""Artifact dependency locking, resolution, and downstream invalidation.

Ensures that:
1. Every stage execution locks the exact artifact versions and hashes it consumed.
2. A later update to an upstream artifact (e.g. research_brief v3) does NOT silently
   change the meaning of an existing downstream artifact (e.g. proposal v1).
3. Downstream artifacts whose locked dependencies no longer match active versions are
   identified as STALE, and can be invalidated cleanly without destroying audit history.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemas.models.artifact import ArtifactEnvelope, ArtifactReference
from schemas.models.common import ArtifactStatus
from schemas.models.pipeline import PipelineDefinition
from schemas.models.production import ProductionState
from production.artifact_store import ArtifactStore, ArtifactStoreError


def resolve_dependencies(
    stage_name: str,
    pipeline_def: PipelineDefinition,
    state: ProductionState,
    artifact_store: ArtifactStore,
) -> tuple[list[ArtifactReference], list[str]]:
    """Resolve and lock all input dependencies for a stage.

    Returns:
        (locked_references, blockers)
        If blockers is non-empty, the stage cannot run.
    """
    stage_def = pipeline_def.get_stage(stage_name)
    if stage_def is None:
        return [], [f"Stage '{stage_name}' does not exist in pipeline '{pipeline_def.name}'"]

    locked: list[ArtifactReference] = []
    blockers: list[str] = []

    for consumed_type in stage_def.consumes:
        # Special case: 'brief' is the initial seed input
        if consumed_type == "brief":
            brief_ref = _resolve_brief_dependency(state, artifact_store)
            if brief_ref is None:
                blockers.append("Initial 'brief' artifact not found in production")
            else:
                locked.append(brief_ref)
            continue

        active_version = state.get_active_version(consumed_type)
        if active_version is None:
            blockers.append(
                f"Required input artifact '{consumed_type}' has no active version in production state"
            )
            continue

        try:
            artifact = artifact_store.load(consumed_type, state.project_id, version=active_version)
        except ArtifactStoreError as exc:
            blockers.append(f"Failed to load active input artifact '{consumed_type}' v{active_version}: {exc}")
            continue

        # Check status: must be approved or ready
        if artifact.status not in (ArtifactStatus.READY, ArtifactStatus.APPROVED):
            blockers.append(
                f"Input artifact '{consumed_type}' v{active_version} has status '{artifact.status.value}' "
                f"(must be 'ready' or 'approved')"
            )
            continue

        locked.append(
            ArtifactReference(
                artifact_type=artifact.artifact_type,
                version=artifact.artifact_version,
                content_hash=artifact.content_hash,
            )
        )

    return locked, blockers


def _resolve_brief_dependency(
    state: ProductionState,
    artifact_store: ArtifactStore,
) -> ArtifactReference | None:
    """Resolve the seed 'brief' dependency from the project directory."""
    # Check if 'brief' exists as an artifact in ArtifactStore
    if artifact_store.exists("brief", state.project_id):
        try:
            art = artifact_store.latest("brief", state.project_id)
            return ArtifactReference(
                artifact_type="brief",
                version=art.artifact_version,
                content_hash=art.content_hash,
            )
        except Exception:
            pass

    # Check brief/brief.json directly
    brief_file = artifact_store.projects_root / state.project_id / "brief" / "brief.json"
    if brief_file.exists():
        try:
            content = json.loads(brief_file.read_text(encoding="utf-8"))
            h = artifact_store.compute_hash(content)
            return ArtifactReference(
                artifact_type="brief",
                version=1,
                content_hash=h,
            )
        except Exception:
            return None

    return None


def is_artifact_stale(
    artifact: ArtifactEnvelope,
    state: ProductionState,
    artifact_store: ArtifactStore,
) -> tuple[bool, str]:
    """Check if an artifact's locked dependencies are no longer active.

    Returns:
        (is_stale, reason)
    """
    for parent in artifact.parent_artifacts:
        if parent.artifact_type == "brief":
            current_brief = _resolve_brief_dependency(state, artifact_store)
            if current_brief is None or current_brief.content_hash != parent.content_hash:
                return True, f"Seed 'brief' content has changed since artifact was generated"
            continue

        active_version = state.get_active_version(parent.artifact_type)
        if active_version is None:
            return True, f"Parent artifact '{parent.artifact_type}' no longer has an active version"

        if active_version != parent.version:
            return True, (
                f"Parent artifact '{parent.artifact_type}' version changed: "
                f"locked v{parent.version} != active v{active_version}"
            )

        try:
            active_artifact = artifact_store.load(
                parent.artifact_type, state.project_id, version=active_version
            )
            if active_artifact.content_hash != parent.content_hash:
                return True, (
                    f"Parent artifact '{parent.artifact_type}' v{parent.version} hash mismatch: "
                    f"locked {parent.content_hash} != current {active_artifact.content_hash}"
                )
        except Exception as exc:
            return True, f"Failed to verify parent '{parent.artifact_type}': {exc}"

    return False, ""


def find_stale_artifacts(
    state: ProductionState,
    artifact_store: ArtifactStore,
) -> dict[str, str]:
    """Find all active artifacts whose dependencies have become stale.

    Returns:
        dict mapping artifact_type -> staleness_reason
    """
    stale: dict[str, str] = {}
    for art_type, version in list(state.active_artifact_versions.items()):
        try:
            artifact = artifact_store.load(art_type, state.project_id, version=version)
            is_st, reason = is_artifact_stale(artifact, state, artifact_store)
            if is_st:
                stale[art_type] = reason
        except Exception as exc:
            stale[art_type] = f"Error loading artifact: {exc}"
    return stale


def invalidate_downstream(
    changed_artifact_type: str,
    pipeline_def: PipelineDefinition,
    state: ProductionState,
    artifact_store: ArtifactStore,
) -> list[str]:
    """Invalidate all downstream active artifacts that depend on `changed_artifact_type`.

    Removes them from active_artifact_versions in ProductionState.
    Historical artifact files on disk are preserved for auditing.

    Returns:
        List of invalidated artifact_types.
    """
    invalidated: list[str] = []

    # Iterate until no more downstream artifacts are found stale
    stale_map = find_stale_artifacts(state, artifact_store)
    for art_type in list(stale_map.keys()):
        if art_type in state.active_artifact_versions:
            del state.active_artifact_versions[art_type]
            invalidated.append(art_type)

    return invalidated
