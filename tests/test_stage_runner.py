"""Tests for production/stage_runner.py."""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from schemas.models.artifact import ProducerInfo
from schemas.models.common import ProducerKind
from schemas.models.production import BudgetState
from production.artifact_store import ArtifactStore
from production.pipeline_loader import PipelineLoader
from production.state import StateStore
from production.stage_registry import (
    StageRegistry,
    StageHandlerResult,
    StageResultStatus,
)
from production.stage_runner import StageRunner


class FakeSuccessResearchHandler:
    def run(self, stage_name, state, inputs, **kwargs):
        return StageHandlerResult(
            status=StageResultStatus.READY,
            data={
                "topic": "Neural Radiance Fields",
                "audience": "Developers",
                "sources": [
                    {"title": "NeRF Paper", "url": "https://arxiv.org/abs/2003.08934"},
                    {"title": "Instant-NGP", "url": "https://github.com/NVlabs/instant-ngp"},
                    {"title": "Mip-NeRF 360", "url": "https://jonbarron.info/mipnerf360/"}
                ],
                "facts": ["NeRF trains a continuous volumetric scene representation."],
                "angles_discovered": ["From 3D meshes to coordinate-based neural rendering."]
            },
            producer=ProducerInfo(kind=ProducerKind.TOOL, tool="test_runner"),
            warnings=[],
            errors=[]
        )


class FakeFailureHandler:
    def run(self, stage_name, state, inputs, **kwargs):
        return StageHandlerResult(
            status=StageResultStatus.FAILED,
            data=None,
            producer=ProducerInfo(kind=ProducerKind.TOOL),
            warnings=[],
            errors=["Simulated API timeout or rate limit exceeded"]
        )


class FakeCrashingHandler:
    def run(self, stage_name, state, inputs, **kwargs):
        raise RuntimeError("Unexpected internal crash inside handler")


@pytest.fixture
def runner_fixture():
    with TemporaryDirectory() as td:
        root = Path(td)
        store = ArtifactStore(projects_root=root)
        state_store = StateStore(projects_root=root)
        registry = StageRegistry()
        runner = StageRunner(artifact_store=store, registry=registry)
        loader = PipelineLoader()
        pipeline_def = loader.load("youtube-short")
        pid = "proj_runner_test"

        state = state_store.create(
            project_id=pid,
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=45.0,
        )

        # Seed brief
        brief_dir = root / pid / "brief"
        brief_dir.mkdir(parents=True, exist_ok=True)
        (brief_dir / "brief.json").write_text(json.dumps({"topic": "NeRF"}), encoding="utf-8")

        yield root, store, state_store, registry, runner, pipeline_def, state


def test_unimplemented_stage_returns_not_implemented(runner_fixture):
    _, _, _, registry, runner, pipeline_def, state = runner_fixture
    assert not registry.has("research")
    result = runner.run("research", pipeline_def, state)
    assert result.status == StageResultStatus.NOT_IMPLEMENTED
    assert "not yet implemented" in result.message


def test_blocked_by_missing_dependency(runner_fixture):
    _, _, _, registry, runner, pipeline_def, state = runner_fixture
    # proposal requires research_brief, which does not exist yet
    result = runner.run("proposal", pipeline_def, state)
    assert result.status == StageResultStatus.BLOCKED
    assert any("research_brief" in e for e in result.errors)


def test_fake_success_handler_produces_artifact(runner_fixture):
    _, store, _, registry, runner, pipeline_def, state = runner_fixture
    registry.register("research", FakeSuccessResearchHandler())

    result = runner.run("research", pipeline_def, state)
    assert result.status == StageResultStatus.READY
    assert result.stage == "research"
    assert result.artifact_type == "research_brief"
    assert result.artifact_version == 1
    assert result.content_hash is not None

    # Verify persisted in store
    loaded = store.load("research_brief", state.project_id, version=1)
    assert loaded.status.value in ("ready", "pending")
    assert state.get_active_version("research_brief") == 1


def test_fake_failure_handler_returns_failed_without_artifact(runner_fixture):
    _, store, _, registry, runner, pipeline_def, state = runner_fixture
    registry.register("research", FakeFailureHandler())

    result = runner.run("research", pipeline_def, state)
    assert result.status == StageResultStatus.FAILED
    assert "Simulated API timeout" in result.errors[0]
    assert not store.exists("research_brief", state.project_id)


def test_crashing_handler_caught_gracefully(runner_fixture):
    _, _, _, registry, runner, pipeline_def, state = runner_fixture
    registry.register("research", FakeCrashingHandler())

    result = runner.run("research", pipeline_def, state)
    assert result.status == StageResultStatus.FAILED
    assert "Unexpected internal crash" in result.message


def test_revision_limit_blocks_stage(runner_fixture):
    _, _, _, registry, runner, pipeline_def, state = runner_fixture
    registry.register("research", FakeSuccessResearchHandler())

    # Max revisions for research in youtube-short is 3
    state.revision_count["research"] = 3
    result = runner.run("research", pipeline_def, state)
    assert result.status == StageResultStatus.BLOCKED
    assert "maximum revisions" in result.message


def test_budget_exceeded_blocks_stage(runner_fixture):
    _, _, _, registry, runner, pipeline_def, state = runner_fixture
    registry.register("research", FakeSuccessResearchHandler())

    state.budget.actual_cost = 15.0  # Cap is 10.0
    result = runner.run("research", pipeline_def, state)
    assert result.status == StageResultStatus.BLOCKED
    assert "over budget cap" in result.message
