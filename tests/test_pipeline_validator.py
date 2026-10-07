"""Tests for production/pipeline_validator.py."""
import pytest
from production.pipeline_validator import PipelineValidator
from production.pipeline_loader import PipelineLoader
from schemas.models.pipeline import (
    PipelineDefinition,
    StageDefinition,
    ApprovalPolicy,
    QualityGate,
    BudgetPolicy,
    RenderRuntimePolicy,
)
from schemas.models.common import ApprovalMode, QualityGateType, RunMode


@pytest.fixture
def validator():
    return PipelineValidator()


def test_validate_all_real_pipelines(validator):
    loader = PipelineLoader()
    for name in loader.list_pipelines():
        defn = loader.load(name)
        errors = validator.validate(defn)
        assert errors == [], f"Pipeline {name} had validation errors: {errors}"


def test_validator_detects_duplicate_stage_names(validator):
    loader = PipelineLoader()
    defn = loader.load("youtube-short").model_copy(deep=True)
    defn.required_stages.append("research")  # duplicate

    errors = validator.validate(defn)
    assert any("Duplicate stage name" in e for e in errors)


def test_validator_detects_undefined_stage(validator):
    loader = PipelineLoader()
    defn = loader.load("youtube-short").model_copy(deep=True)
    defn.required_stages.append("ghost_stage")

    errors = validator.validate(defn)
    assert any("ghost_stage" in e for e in errors)


def test_validator_detects_missing_upstream_artifact(validator):
    loader = PipelineLoader()
    defn = loader.load("youtube-short").model_copy(deep=True)
    # Stage consumes an artifact that nobody produces
    defn.stages["research"] = defn.stages["research"].model_copy(
        update={"consumes": ["nonexistent_artifact_xyz"]}
    )

    errors = validator.validate(defn)
    assert any("nonexistent_artifact_xyz" in e for e in errors)


def test_validator_detects_cyclic_dependency(validator):
    """Stage A consumes B's output, Stage B consumes A's output -> impossible cycle."""
    stage_a = StageDefinition(
        name="stage_a",
        required=True,
        produces=["artifact_a"],
        consumes=["artifact_b"],
        approval=ApprovalPolicy(),
        max_revisions=3,
        quality_gates=[],
    )
    stage_b = StageDefinition(
        name="stage_b",
        required=True,
        produces=["artifact_b"],
        consumes=["artifact_a"],
        approval=ApprovalPolicy(),
        max_revisions=3,
        quality_gates=[],
    )

    defn = PipelineDefinition(
        name="cyclic-test",
        version="2.0",
        description="test cyclic",
        target_duration=30.0,
        platform="youtube_shorts",
        run_mode_default=RunMode.AUTO,
        required_stages=["stage_a", "stage_b"],
        required_artifacts=["artifact_a", "artifact_b"],
        stages={"stage_a": stage_a, "stage_b": stage_b},
        quality_gates=[],
        approval_policy={},
        budget_policy=BudgetPolicy(),
        render_runtime_policy=RenderRuntimePolicy(primary="remotion"),
    )

    errors = validator.validate(defn)
    assert any("Dependency cycle detected" in e for e in errors)


def test_validator_detects_missing_quality_gate_threshold(validator):
    loader = PipelineLoader()
    defn = loader.load("youtube-short").model_copy(deep=True)
    # MIN gate without threshold
    broken_gate = QualityGate.model_construct(
        name="broken_min",
        type=QualityGateType.MIN,
        field="some_field",
        threshold=None,
        required=True,
        message="broken"
    )
    defn.stages["research"].quality_gates.append(broken_gate)

    errors = validator.validate(defn)
    assert any("no threshold is set" in e for e in errors)
