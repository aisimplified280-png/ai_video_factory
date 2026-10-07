"""Runtime router: validates the locked runtime and prepares a job. Never renders."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .composition_job import (
    COMPOSITION_MODES,
    OUTPUT_FORMATS,
    RENDERER_FAMILIES,
    CompositionJob,
    JobResult,
    build_output_path,
    load_platform_profile,
    platform_aspect_ratio,
    resolve_execution_target,
)
from .diagnostics import diagnose_runtime
from .runtime import RuntimeStatus
from .runtime_errors import (
    BLOCKED_RUNTIME_UNAVAILABLE,
    COMPOSITION_MODE_UNSUPPORTED,
    EDIT_NOT_APPROVED,
    EDIT_NOT_FOUND,
    EDIT_STALE,
    PLATFORM_MISMATCH,
    REMOTE_POLICY_UNSUPPORTED,
    RENDERER_FAMILY_UNSUPPORTED,
    RUNTIME_LOCK_MISMATCH,
    UNKNOWN_RUNTIME,
    CompositionBlocker,
)
from .runtime_registry import RuntimeRegistry, create_default_registry

LOCK_FIELDS = ("renderer_family", "render_runtime", "composition_mode")


def lock_triple(source: dict[str, Any]) -> dict[str, str]:
    """Extract the three locked routing fields. Renderer family, runtime, and
    composition mode have different meanings and are never collapsed."""
    return {field: source.get(field) for field in LOCK_FIELDS}


def validate_runtime_lock(proposal_data: dict[str, Any], edit_data: dict[str, Any]) -> list[CompositionBlocker]:
    """Verify proposal and edit locks agree on all three fields. Mismatch blocks."""
    selected_id = proposal_data.get("selected_concept_id")
    selected = next((c for c in proposal_data.get("concepts", []) if c.get("concept_id") == selected_id), None)
    if selected is None:
        return [CompositionBlocker(
            code=RUNTIME_LOCK_MISMATCH,
            message="Proposal has no selected concept, so there is no authoritative runtime lock.",
            correction="Select and approve a proposal concept before routing.",
        )]
    proposal_lock = lock_triple(selected)
    edit_lock = lock_triple(edit_data)
    if proposal_lock != edit_lock:
        differing = sorted(k for k in LOCK_FIELDS if proposal_lock.get(k) != edit_lock.get(k))
        return [CompositionBlocker(
            code=RUNTIME_LOCK_MISMATCH,
            message=f"Runtime lock mismatch on {differing}: proposal={proposal_lock} edit={edit_lock}.",
            correction="Regenerate edit_decisions from the approved proposal; never auto-correct the lock.",
        )]
    return []


class RuntimeRouter:
    """Binds an approved edit artifact to its locked runtime. Boring by design."""

    def __init__(self, registry: RuntimeRegistry | None = None, projects_root: Path | str | None = None) -> None:
        self.registry = registry if registry is not None else create_default_registry()
        self.projects_root = Path(projects_root) if projects_root is not None else Path("projects")

    def prepare_job(
        self,
        production_id: str,
        edit_envelope: Any,
        proposal_envelope: Any,
        state: Any = None,
        store: Any = None,
        remote_policy: str = "auto",
        output_format: str = "mp4",
    ) -> JobResult:
        """Validate everything and return a CompositionJob, or structured blockers."""
        blockers: list[CompositionBlocker] = []
        edit, proposal = edit_envelope.data, proposal_envelope.data

        # 1. Edit must exist and be approved.
        if edit_envelope.status.value != "approved":
            blockers.append(CompositionBlocker(
                code=EDIT_NOT_APPROVED,
                message=f"edit_decisions v{edit_envelope.artifact_version} has status {edit_envelope.status.value}; only approved edits are routable.",
                correction="Approve the edit artifact before preparing a composition job.",
            ))
        # 2. Edit must be the active, hash-matching version (no stale routing).
        if state is not None and store is not None:
            active = state.get_active_version("edit_decisions")
            if active != edit_envelope.artifact_version:
                blockers.append(CompositionBlocker(
                    code=EDIT_STALE,
                    message=f"edit_decisions v{edit_envelope.artifact_version} is not the active version (active=v{active}).",
                    correction="Route the active edit version, or approve the intended revision first.",
                ))
            else:
                try:
                    latest = store.latest("edit_decisions", production_id)
                    if latest.content_hash != edit_envelope.content_hash:
                        blockers.append(CompositionBlocker(
                            code=EDIT_STALE,
                            message="Active edit hash does not match the referenced edit artifact.",
                            correction="Reload the active edit artifact and prepare a new job.",
                        ))
                except Exception as exc:
                    blockers.append(CompositionBlocker(
                        code=EDIT_NOT_FOUND,
                        message=f"Could not reload the active edit artifact: {exc}",
                        correction="Ensure edit_decisions is persisted before routing.",
                    ))
        # 3. Proposal/edit locks must agree exactly, and the edit's recorded
        # provenance must match the proposal envelope actually presented.
        blockers.extend(validate_runtime_lock(proposal, edit))
        source = edit.get("runtime_lock_source") or {}
        if source and (
            source.get("version") != proposal_envelope.artifact_version
            or source.get("content_hash") != proposal_envelope.content_hash
        ):
            blockers.append(CompositionBlocker(
                code=RUNTIME_LOCK_MISMATCH,
                message="Edit runtime provenance does not match the presented proposal artifact version/hash.",
                correction="Route against the proposal version recorded in runtime_lock_source, or regenerate the edit.",
            ))
        if blockers:
            return JobResult(status="blocked", job=None, blockers=tuple(blockers))

        runtime_id = edit["render_runtime"]
        # 4. Runtime must be registered. Unknown is never available.
        if not self.registry.has(runtime_id):
            return JobResult(status="blocked", job=None, blockers=(CompositionBlocker(
                code=UNKNOWN_RUNTIME,
                message=f"Locked runtime {runtime_id!r} is not registered.",
                correction="Register the runtime or revise the approved proposal to a registered runtime.",
            ),))
        record = self.registry.get(runtime_id)
        # 5. Renderer family and composition mode stay separate, both validated.
        if edit["renderer_family"] not in RENDERER_FAMILIES:
            return JobResult(status="blocked", job=None, blockers=(CompositionBlocker(
                code=RENDERER_FAMILY_UNSUPPORTED,
                message=f"Renderer family {edit['renderer_family']!r} is not supported.",
                correction="Use one of: " + ", ".join(sorted(RENDERER_FAMILIES)),
            ),))
        if edit["composition_mode"] not in COMPOSITION_MODES:
            return JobResult(status="blocked", job=None, blockers=(CompositionBlocker(
                code=COMPOSITION_MODE_UNSUPPORTED,
                message=f"Composition mode {edit['composition_mode']!r} is not supported.",
                correction="Use one of: " + ", ".join(sorted(COMPOSITION_MODES)),
            ),))
        # 6. Platform profile must exist and describe a sane target.
        try:
            profile = load_platform_profile(edit["platform_profile"])
            platform_aspect_ratio(profile)
            if int(profile.get("fps", 0)) <= 0:
                raise ValueError(f"Invalid fps in {edit['platform_profile']}")
            if output_format not in OUTPUT_FORMATS:
                raise ValueError(f"Unsupported output format: {output_format!r}")
        except (FileNotFoundError, ValueError, KeyError) as exc:
            return JobResult(status="blocked", job=None, blockers=(CompositionBlocker(
                code=PLATFORM_MISMATCH,
                message=f"Platform validation failed: {exc}",
                correction="Reference profiles/youtube_short.json and request mp4 output.",
            ),))
        # 7. Runtime must actually be available. No silent fallback, ever.
        diagnostics = diagnose_runtime(record)
        local_available = diagnostics["status"] == RuntimeStatus.AVAILABLE.value
        remote_available = bool(diagnostics.get("remote_available", False))
        target = resolve_execution_target(
            remote_policy, record.supports_local, record.supports_remote,
            local_available, remote_available,
        )
        if target is None:
            detail = "; ".join(f"{c['name']}: {c['message']}" for c in diagnostics["checks"])
            reason = (
                f"Locked runtime {runtime_id!r} is {diagnostics['status']} "
                f"(policy={remote_policy}). Checks: {detail}."
                if remote_policy != "remote" or record.supports_remote else
                f"Locked runtime {runtime_id!r} requires remote execution, which is unprobed in Phase 7."
            )
            return JobResult(status="blocked", job=None, blockers=(CompositionBlocker(
                code=BLOCKED_RUNTIME_UNAVAILABLE,
                message=reason,
                correction="Make the locked runtime available; substitution with another runtime is forbidden.",
            ),))
        if remote_policy not in {"local", "remote", "auto"}:
            return JobResult(status="blocked", job=None, blockers=(CompositionBlocker(
                code=REMOTE_POLICY_UNSUPPORTED,
                message=f"Remote policy {remote_policy!r} is not supported.",
                correction="Use local, remote, or auto.",
            ),))
        job = CompositionJob(
            production_id=production_id,
            edit_artifact_version=edit_envelope.artifact_version,
            edit_artifact_hash=edit_envelope.content_hash,
            runtime_id=runtime_id,
            runtime_version=diagnostics["version"],
            renderer_family=edit["renderer_family"],
            composition_mode=edit["composition_mode"],
            platform_profile=edit["platform_profile"],
            output_format=output_format,
            output_path=build_output_path(self.projects_root, production_id, runtime_id, edit_envelope.artifact_version),
            remote_policy=remote_policy,
            execution_target=target,
            runtime_lock_source=dict(edit.get("runtime_lock_source", {})),
            parent_artifacts=[{"artifact_type": p.artifact_type, "version": p.version, "content_hash": p.content_hash}
                              for p in (edit_envelope.parent_artifacts or [])],
        )
        return JobResult(status="ready", job=job, blockers=())
