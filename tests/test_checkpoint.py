"""Tests for production/checkpoint.py."""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from production.checkpoint import CheckpointStore, Checkpoint
from production.state import StateStore
from schemas.models.common import ProductionStatus


@pytest.fixture
def temp_project_dir():
    with TemporaryDirectory() as td:
        yield Path(td)


def test_checkpoint_creation_and_ordering(temp_project_dir):
    pid = "proj_chk_test"
    pdir = temp_project_dir / pid
    store = CheckpointStore(pdir, pid)

    state_store = StateStore(projects_root=temp_project_dir)
    state = state_store.create(
        project_id=pid,
        pipeline="youtube-short",
        pipeline_version="2.0",
        target_duration=45.0,
    )

    chk1 = store.create_checkpoint(state, "production_created", stage="research", message="Init")
    assert chk1.sequence == 1
    assert chk1.event_type == "production_created"
    assert chk1.stage == "research"
    assert chk1.checkpoint_id.startswith("chk_0001_")
    assert chk1.state_hash.startswith("sha256:")

    state.status = ProductionStatus.RUNNING
    state.set_active_version("research_brief", 1)
    chk2 = store.create_checkpoint(state, "stage_completed", stage="research", message="Done research")
    assert chk2.sequence == 2
    assert chk2.artifact_versions == {"research_brief": 1}

    all_chks = store.list_checkpoints()
    assert len(all_chks) == 2
    assert all_chks[0].sequence == 1
    assert all_chks[1].sequence == 2

    latest = store.get_latest_checkpoint()
    assert latest is not None
    assert latest.sequence == 2
    assert latest.event_type == "stage_completed"


def test_checkpoint_serialization_roundtrip():
    chk = Checkpoint(
        checkpoint_id="chk_0001_test",
        production_id="proj_123",
        sequence=1,
        event_type="test_event",
        stage="test_stage",
        production_status="running",
        current_stage="test_stage",
        state_hash="sha256:" + "0" * 64,
        artifact_versions={"art1": 1},
        message="test msg",
    )
    json_str = chk.to_json()
    reloaded = Checkpoint.from_json(json_str)
    assert reloaded.checkpoint_id == chk.checkpoint_id
    assert reloaded.sequence == 1
    assert reloaded.state_hash == chk.state_hash
    assert reloaded.artifact_versions == {"art1": 1}
