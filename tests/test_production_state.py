"""Tests for production/state.py and schemas/models/production.py."""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from production.state import (
    StateStore,
    ProductionNotFoundError,
    ProductionStateCorruptedError,
    ProductionStateError,
)
from schemas.models.common import ProductionStatus, Severity, RunMode
from schemas.models.production import ProductionState, BudgetState


@pytest.fixture
def temp_state_store():
    with TemporaryDirectory() as td:
        store = StateStore(projects_root=Path(td))
        yield store, Path(td)


def test_create_and_load_production_state(temp_state_store):
    store, _ = temp_state_store
    pid = "proj_test_roundtrip"

    state = store.create(
        project_id=pid,
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=45.0,
        aspect_ratio="9:16",
        platform="youtube_shorts",
        budget_cap=12.0,
        metadata={"topic": "Vector DBs"}
    )
    assert state.project_id == pid
    assert state.status == ProductionStatus.CREATED
    assert state.budget.budget_cap == 12.0
    assert state.budget.remaining_budget == 12.0

    loaded = store.load(pid)
    assert loaded.project_id == pid
    assert loaded.pipeline == "youtube-short"
    assert loaded.target_duration == 45.0
    assert loaded.aspect_ratio == "9:16"
    assert loaded.metadata["topic"] == "Vector DBs"


def test_active_artifact_versions_persist(temp_state_store):
    store, _ = temp_state_store
    pid = "proj_test_active_versions"

    state = store.create(
        project_id=pid,
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=45.0
    )
    state.set_active_version("research_brief", 2)
    state.set_active_version("proposal_packet", 1)
    state.set_active_version("script", 3)
    store.save(state)

    reloaded = store.load(pid)
    assert reloaded.get_active_version("research_brief") == 2
    assert reloaded.get_active_version("proposal_packet") == 1
    assert reloaded.get_active_version("script") == 3
    assert reloaded.get_active_version("nonexistent") is None


def test_revision_counter_tracks_and_persists(temp_state_store):
    store, _ = temp_state_store
    pid = "proj_test_revisions"

    state = store.create(
        project_id=pid,
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=45.0
    )
    assert state.get_revision_count("scene_plan") == 0
    assert state.increment_revision("scene_plan") == 1
    assert state.increment_revision("scene_plan") == 2
    store.save(state)

    reloaded = store.load(pid)
    assert reloaded.get_revision_count("scene_plan") == 2


def test_decisions_warnings_errors_persist(temp_state_store):
    store, _ = temp_state_store
    pid = "proj_test_audit"

    state = store.create(
        project_id=pid,
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=45.0
    )
    state.add_decision(
        stage="proposal",
        decision="Selected concept 1",
        reason="Strongest hook angle",
        actor="director"
    )
    state.add_warning(
        code="LONG_WORD_COUNT",
        stage="script",
        message="Script is slightly fast-paced",
        severity=Severity.WARNING
    )
    state.add_error(
        code="RENDER_TIMEOUT",
        stage="compose",
        message="Render process exceeded 60s timeout",
        severity=Severity.ERROR,
        recoverable=True
    )
    store.save(state)

    reloaded = store.load(pid)
    assert len(reloaded.decisions) == 1
    assert reloaded.decisions[0].decision == "Selected concept 1"
    assert len(reloaded.warnings) == 1
    assert reloaded.warnings[0].code == "LONG_WORD_COUNT"
    assert len(reloaded.errors) == 1
    assert reloaded.errors[0].code == "RENDER_TIMEOUT"
    assert reloaded.errors[0].recoverable is True


def test_duplicate_production_id_raises(temp_state_store):
    store, _ = temp_state_store
    pid = "proj_test_dup"
    store.create(
        project_id=pid,
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=45.0
    )
    with pytest.raises(ProductionStateError):
        store.create(
            project_id=pid,
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=45.0
        )


def test_load_nonexistent_production_raises(temp_state_store):
    store, _ = temp_state_store
    with pytest.raises(ProductionNotFoundError):
        store.load("proj_does_not_exist")


def test_corrupted_state_file_raises(temp_state_store):
    store, root = temp_state_store
    pid = "proj_test_corrupt"
    store.create(
        project_id=pid,
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=45.0
    )
    state_file = root / pid / "production_state.json"
    state_file.write_text("invalid json content {{{", encoding="utf-8")

    with pytest.raises(ProductionStateCorruptedError):
        store.load(pid)


def test_budget_state_calculations():
    b = BudgetState(budget_cap=10.0, actual_cost=3.5)
    assert b.remaining_budget == 6.5
    assert not b.is_over_budget
    assert b.can_spend(5.0)
    assert not b.can_spend(7.0)

    b_over = BudgetState(budget_cap=10.0, actual_cost=11.2)
    assert b_over.remaining_budget == 0.0
    assert b_over.is_over_budget
