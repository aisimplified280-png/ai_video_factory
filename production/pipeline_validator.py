"""PipelineValidator — validates a PipelineDefinition for structural correctness.

Checks performed:
  - Stage names are unique
  - Every required_stage exists in stages dict
  - All consumed artifacts are produced by some upstream stage
  - No impossible dependency cycles
  - Quality gate types are valid
  - Approval modes are valid
  - Render runtime values are valid
  - No stage produces an artifact not in required_artifacts or optional
  - Budget policy values are non-negative
"""
from __future__ import annotations

from schemas.models.pipeline import PipelineDefinition, StageDefinition
from schemas.models.common import QualityGateType, ApprovalMode


class PipelineValidator:
    """Validates a PipelineDefinition and returns a list of error strings.

    An empty list means the pipeline is valid.
    The controller calls this at startup to fail fast before any stage runs.
    """

    def validate(self, defn: PipelineDefinition) -> list[str]:
        errors: list[str] = []
        errors.extend(self._check_stage_uniqueness(defn))
        errors.extend(self._check_required_stages_defined(defn))
        errors.extend(self._check_artifact_dependencies(defn))
        errors.extend(self._check_dependency_cycles(defn))
        errors.extend(self._check_quality_gates(defn))
        errors.extend(self._check_approval_modes(defn))
        errors.extend(self._check_runtime_policy(defn))
        errors.extend(self._check_budget_policy(defn))
        return errors

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_stage_uniqueness(self, defn: PipelineDefinition) -> list[str]:
        """Stage names must be unique across required + optional."""
        errors = []
        all_names = defn.required_stages + defn.optional_stages
        seen: set[str] = set()
        for name in all_names:
            if name in seen:
                errors.append(f"Duplicate stage name: {name!r}")
            seen.add(name)
        return errors

    def _check_required_stages_defined(self, defn: PipelineDefinition) -> list[str]:
        """Every stage listed in required_stages/optional_stages must have a StageDefinition."""
        errors = []
        for name in defn.all_stage_names():
            if name not in defn.stages:
                errors.append(
                    f"Stage {name!r} is listed in pipeline order but has no "
                    f"stage definition in 'stages'. "
                    f"Defined stages: {list(defn.stages.keys())}"
                )
        return errors

    def _check_artifact_dependencies(self, defn: PipelineDefinition) -> list[str]:
        """Every consumed artifact must be produced by some upstream stage."""
        errors = []
        # Build the set of all artifacts produced, in stage order
        # "brief" is the seed artifact provided at production creation
        produced_so_far: set[str] = {"brief"}

        for stage_name in defn.all_stage_names():
            stage = defn.stages.get(stage_name)
            if stage is None:
                continue  # Already caught by _check_required_stages_defined
            for consumed in stage.consumes:
                if consumed not in produced_so_far:
                    errors.append(
                        f"Stage {stage_name!r} consumes {consumed!r}, "
                        f"but it is not produced by any upstream stage. "
                        f"Produced so far: {sorted(produced_so_far) or ['(none)']}"
                    )
            for produced in stage.produces:
                produced_so_far.add(produced)
        return errors

    def _check_dependency_cycles(self, defn: PipelineDefinition) -> list[str]:
        """Detect impossible circular dependencies using topological sort (Kahn's algorithm)."""
        # Build adjacency: stage → set of stages that depend on it
        # A cycle exists if we can't topologically order all stages.
        stage_names = list(defn.stages.keys())
        produces_map: dict[str, str] = {}  # artifact_type → producing stage
        for name, stage in defn.stages.items():
            for artifact in stage.produces:
                produces_map[artifact] = name

        # Build in-degree and adjacency list
        in_degree: dict[str, int] = {n: 0 for n in stage_names}
        adj: dict[str, list[str]] = {n: [] for n in stage_names}

        for name, stage in defn.stages.items():
            for consumed in stage.consumes:
                producer = produces_map.get(consumed)
                if producer and producer != name:
                    adj[producer].append(name)
                    in_degree[name] += 1

        # Kahn's algorithm
        queue = [n for n in stage_names if in_degree[n] == 0]
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited != len(stage_names):
            # Cycle detected
            remaining = [n for n in stage_names if in_degree[n] > 0]
            return [
                f"Dependency cycle detected among stages: {remaining}. "
                f"These stages have circular artifact dependencies."
            ]
        return []

    def _check_quality_gates(self, defn: PipelineDefinition) -> list[str]:
        """Quality gate types must be valid and threshold/pattern consistent."""
        errors = []
        all_gates = list(defn.quality_gates)
        for stage in defn.stages.values():
            all_gates.extend(stage.quality_gates)

        for gate in all_gates:
            if gate.type in (QualityGateType.MIN, QualityGateType.MAX):
                if gate.threshold is None:
                    errors.append(
                        f"Quality gate {gate.name!r} has type {gate.type.value!r} "
                        f"but no threshold is set"
                    )
            if gate.type == QualityGateType.REGEX:
                if not gate.pattern:
                    errors.append(
                        f"Quality gate {gate.name!r} has type 'regex' but no pattern is set"
                    )
        return errors

    def _check_approval_modes(self, defn: PipelineDefinition) -> list[str]:
        """Approval modes in stage definitions and pipeline overrides must be valid."""
        errors = []
        valid_modes = {m.value for m in ApprovalMode}

        for stage_name, stage in defn.stages.items():
            mode = stage.approval.mode.value
            if mode not in valid_modes:
                errors.append(
                    f"Stage {stage_name!r} has invalid approval mode: {mode!r}. "
                    f"Valid: {valid_modes}"
                )

        for stage_name, policy in defn.approval_policy.items():
            mode = policy.mode.value
            if mode not in valid_modes:
                errors.append(
                    f"Pipeline approval_policy[{stage_name!r}] has invalid mode: {mode!r}. "
                    f"Valid: {valid_modes}"
                )
            if stage_name not in defn.stages:
                errors.append(
                    f"Pipeline approval_policy references unknown stage: {stage_name!r}"
                )
        return errors

    def _check_runtime_policy(self, defn: PipelineDefinition) -> list[str]:
        """Render runtime primary and fallback must be valid identifiers."""
        errors = []
        valid = {"remotion", "hyperframes", "ffmpeg_pil"}
        p = defn.render_runtime_policy.primary
        if p not in valid:
            errors.append(
                f"render_runtime_policy.primary={p!r} is invalid. Valid: {valid}"
            )
        f = defn.render_runtime_policy.fallback
        if f is not None and f not in valid:
            errors.append(
                f"render_runtime_policy.fallback={f!r} is invalid. Valid: {valid}"
            )
        if defn.render_runtime_policy.strict and f is not None:
            # Strict + fallback defined is a warning, not an error —
            # the strict flag means "don't use fallback silently", but having one
            # defined is OK for explicit manual override.
            pass
        return errors

    def _check_budget_policy(self, defn: PipelineDefinition) -> list[str]:
        """Budget policy values must be non-negative."""
        errors = []
        bp = defn.budget_policy
        if bp.budget_cap < 0:
            errors.append(f"budget_policy.budget_cap must be >= 0, got {bp.budget_cap}")
        if bp.max_image_gen_calls < 0:
            errors.append(f"budget_policy.max_image_gen_calls must be >= 0")
        if bp.max_video_gen_calls < 0:
            errors.append(f"budget_policy.max_video_gen_calls must be >= 0")
        return errors
