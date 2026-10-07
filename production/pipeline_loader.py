"""PipelineLoader — loads and caches pipeline definitions from YAML.

There is ONE canonical place to parse pipeline YAML: here.
No stage or controller should parse YAML independently.

Usage:
    loader = PipelineLoader()
    pipeline = loader.load("youtube-short")
    stage = loader.get_stage("youtube-short", "research")
    loader.validate("youtube-short")   # raises if invalid
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml

from schemas.models.pipeline import (
    PipelineDefinition,
    StageDefinition,
    ApprovalPolicy,
    QualityGate,
    BudgetPolicy,
    RenderRuntimePolicy,
)
from schemas.models.common import ApprovalMode, QualityGateType, RunMode


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class PipelineLoaderError(Exception):
    """Base error for pipeline loading."""


class PipelineNotFoundError(PipelineLoaderError):
    """Named pipeline YAML does not exist."""


class PipelineParseError(PipelineLoaderError):
    """YAML is malformed or cannot be parsed."""


class PipelineValidationError(PipelineLoaderError):
    """Pipeline definition is structurally invalid."""


# ---------------------------------------------------------------------------
# PipelineLoader
# ---------------------------------------------------------------------------

_DEFAULT_PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline_defs"


class PipelineLoader:
    """Loads pipeline definitions from YAML files in `pipeline_dir`.

    Parsed definitions are cached in memory. The cache is keyed by pipeline name.
    A missing or structurally invalid pipeline always raises — never silently invents one.
    """

    def __init__(self, pipeline_dir: Path | None = None) -> None:
        self.pipeline_dir = Path(pipeline_dir) if pipeline_dir else _DEFAULT_PIPELINE_DIR
        self._cache: dict[str, PipelineDefinition] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, name: str) -> PipelineDefinition:
        """Load and return a PipelineDefinition by name.

        Raises:
            PipelineNotFoundError: pipeline YAML does not exist.
            PipelineParseError: YAML is malformed.
            PipelineValidationError: definition is structurally invalid.
        """
        if name in self._cache:
            return self._cache[name]

        path = self._find_pipeline_file(name)
        raw = self._read_yaml(path)
        defn = self._parse_definition(name, raw)
        self._cache[name] = defn
        return defn

    def list_pipelines(self) -> list[str]:
        """Return names of all available pipeline definitions."""
        if not self.pipeline_dir.exists():
            return []
        return sorted(
            p.stem for p in self.pipeline_dir.glob("*.yaml")
        )

    def validate(self, name: str) -> PipelineDefinition:
        """Load and fully validate a pipeline. Returns the definition if valid.

        Validation is performed by PipelineValidator. Raises PipelineValidationError
        if any structural issue is found.
        """
        from production.pipeline_validator import PipelineValidator
        defn = self.load(name)
        validator = PipelineValidator()
        errors = validator.validate(defn)
        if errors:
            msg = "\n".join(f"  - {e}" for e in errors)
            raise PipelineValidationError(
                f"Pipeline {name!r} failed validation:\n{msg}"
            )
        return defn

    def get_stage(self, pipeline_name: str, stage_name: str) -> StageDefinition:
        """Return a specific stage definition from a pipeline.

        Raises KeyError if stage does not exist in the pipeline.
        """
        defn = self.load(pipeline_name)
        stage = defn.get_stage(stage_name)
        if stage is None:
            raise KeyError(
                f"Stage {stage_name!r} not found in pipeline {pipeline_name!r}. "
                f"Available: {list(defn.stages.keys())}"
            )
        return stage

    def clear_cache(self) -> None:
        """Invalidate the in-memory pipeline cache (useful for tests)."""
        self._cache.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_pipeline_file(self, name: str) -> Path:
        path = self.pipeline_dir / f"{name}.yaml"
        if not path.exists():
            available = self.list_pipelines()
            raise PipelineNotFoundError(
                f"Pipeline {name!r} not found at {path}. "
                f"Available pipelines: {available}"
            )
        return path

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PipelineParseError(f"Cannot read pipeline file {path}: {exc}") from exc
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise PipelineParseError(f"YAML parse error in {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise PipelineParseError(f"Pipeline YAML must be a mapping, got {type(data).__name__}")
        return data

    def _parse_definition(self, name: str, raw: dict[str, Any]) -> PipelineDefinition:
        """Convert raw YAML dict into a validated PipelineDefinition."""
        try:
            # Parse stages
            stages_raw = raw.get("stages", {})
            if not isinstance(stages_raw, dict):
                raise PipelineParseError(f"'stages' must be a mapping in pipeline {name!r}")

            stages: dict[str, StageDefinition] = {}
            for stage_name, stage_raw in stages_raw.items():
                if not isinstance(stage_raw, dict):
                    raise PipelineParseError(
                        f"Stage {stage_name!r} must be a mapping in pipeline {name!r}"
                    )
                approval_raw = stage_raw.get("approval", {})
                if isinstance(approval_raw, str):
                    approval_raw = {"mode": approval_raw}
                approval = ApprovalPolicy(
                    mode=ApprovalMode(approval_raw.get("mode", "auto"))
                )
                quality_gates = [
                    self._parse_quality_gate(g)
                    for g in stage_raw.get("quality_gates", [])
                ]
                stages[stage_name] = StageDefinition(
                    name=stage_name,
                    required=bool(stage_raw.get("required", True)),
                    produces=list(stage_raw.get("produces", [])),
                    consumes=list(stage_raw.get("consumes", [])),
                    approval=approval,
                    max_revisions=int(stage_raw.get("max_revisions", 3)),
                    quality_gates=quality_gates,
                    description=str(stage_raw.get("description", "")),
                )

            # Parse pipeline-level quality gates
            pipeline_gates = [
                self._parse_quality_gate(g)
                for g in raw.get("quality_gates", [])
            ]

            # Parse per-stage approval policy overrides
            approval_policy: dict[str, ApprovalPolicy] = {}
            for sname, araw in raw.get("approval_policy", {}).items():
                if isinstance(araw, str):
                    araw = {"mode": araw}
                approval_policy[sname] = ApprovalPolicy(
                    mode=ApprovalMode(araw.get("mode", "auto"))
                )

            # Parse budget policy
            bp_raw = raw.get("budget_policy", {})
            budget_policy = BudgetPolicy(
                budget_cap=float(bp_raw.get("budget_cap", 10.0)),
                max_image_gen_calls=int(bp_raw.get("max_image_gen_calls", 20)),
                max_video_gen_calls=int(bp_raw.get("max_video_gen_calls", 5)),
                max_tts_chars=int(bp_raw.get("max_tts_chars", 5000)),
                max_llm_tokens=int(bp_raw.get("max_llm_tokens", 100_000)),
            )

            # Parse render runtime policy
            rr_raw = raw.get("render_runtime_policy", {})
            render_runtime_policy = RenderRuntimePolicy(
                primary=str(rr_raw.get("primary", "remotion")),
                fallback=rr_raw.get("fallback"),
                strict=bool(rr_raw.get("strict", True)),
            )

            return PipelineDefinition(
                name=str(raw.get("name", name)),
                version=str(raw.get("version", "2.0")),
                description=str(raw.get("description", "")),
                target_duration=float(raw.get("target_duration", 45)),
                platform=str(raw.get("platform", "youtube_shorts")),
                run_mode_default=RunMode(raw.get("run_mode_default", "auto")),
                required_stages=list(raw.get("required_stages", [])),
                optional_stages=list(raw.get("optional_stages", [])),
                required_artifacts=list(raw.get("required_artifacts", [])),
                stages=stages,
                quality_gates=pipeline_gates,
                approval_policy=approval_policy,
                budget_policy=budget_policy,
                render_runtime_policy=render_runtime_policy,
            )

        except PipelineParseError:
            raise
        except Exception as exc:
            raise PipelineParseError(
                f"Failed to parse pipeline {name!r}: {exc}"
            ) from exc

    @staticmethod
    def _parse_quality_gate(raw: dict[str, Any]) -> QualityGate:
        return QualityGate(
            name=str(raw.get("name", "")),
            type=QualityGateType(raw.get("type", "presence")),
            field=str(raw.get("field", "")),
            threshold=float(raw["threshold"]) if "threshold" in raw else None,
            pattern=raw.get("pattern"),
            required=bool(raw.get("required", True)),
            message=str(raw.get("message", "")),
        )
