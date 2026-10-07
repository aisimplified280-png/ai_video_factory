"""Tests for production/artifact_store.py."""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from production.artifact_store import (
    ArtifactStore,
    ArtifactStoreError,
    ImmutableArtifactError,
    ArtifactNotFoundError,
    ArtifactHashMismatchError,
    ArtifactCorruptedError,
    ArtifactTypeMismatchError,
    ArtifactSchemaError,
)
from schemas.models.artifact import ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind


@pytest.fixture
def temp_store():
    with TemporaryDirectory() as td:
        store = ArtifactStore(projects_root=Path(td))
        yield store, Path(td)


def make_sample_research_data():
    return {
        "topic": "Neural Radiance Fields",
        "audience": "Graphics engineers",
        "sources": [{"title": "NeRF Paper", "url": "https://arxiv.org/abs/2003.08934"}],
        "facts": ["NeRF synthesizes novel views of complex scenes using neural networks."],
        "angles_discovered": ["From 2D photogrammetry to continuous 5D neural volumetric representations."]
    }


def test_content_hash_deterministic():
    data1 = {"b": 2, "a": 1, "c": [1, 2, 3]}
    data2 = {"a": 1, "c": [1, 2, 3], "b": 2}
    h1 = ArtifactStore.compute_hash(data1)
    h2 = ArtifactStore.compute_hash(data2)
    assert h1 == h2
    assert h1.startswith("sha256:")
    assert len(h1) == 7 + 64


def test_content_hash_different_data():
    data1 = {"a": 1}
    data2 = {"a": 2}
    assert ArtifactStore.compute_hash(data1) != ArtifactStore.compute_hash(data2)


def test_artifact_version_increments(temp_store):
    store, _ = temp_store
    pid = "proj_test_versions"
    producer = ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash")
    data = make_sample_research_data()

    art1 = store.create("research_brief", pid, "research", data, producer)
    assert art1.artifact_version == 1
    store.save(art1)

    art2 = store.create("research_brief", pid, "research", data, producer)
    assert art2.artifact_version == 2
    store.save(art2)

    versions = store.list_versions("research_brief", pid)
    assert versions == [1, 2]


def test_approved_artifact_is_immutable(temp_store):
    store, _ = temp_store
    pid = "proj_test_immutability"
    producer = ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash")
    data = make_sample_research_data()

    art = store.create("research_brief", pid, "research", data, producer)
    store.save(art)
    store.approve("research_brief", pid, 1, actor="human_director")

    # Attempting to save new data under the same approved version must fail
    modified_data = dict(data)
    modified_data["topic"] = "Completely Different Topic"
    modified_hash = store.compute_hash(modified_data)

    tampered_art = art.model_copy(update={
        "data": modified_data,
        "content_hash": modified_hash
    })

    with pytest.raises(ImmutableArtifactError):
        store.save(tampered_art)


def test_cannot_reject_approved_artifact(temp_store):
    store, _ = temp_store
    pid = "proj_test_approve_reject"
    producer = ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash")
    data = make_sample_research_data()

    art = store.create("research_brief", pid, "research", data, producer)
    store.save(art)
    store.approve("research_brief", pid, 1)

    with pytest.raises(ImmutableArtifactError):
        store.reject("research_brief", pid, 1, reason="I changed my mind")


def test_failed_artifact_can_be_replaced_by_new_version(temp_store):
    store, _ = temp_store
    pid = "proj_test_fail_recovery"
    producer = ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash")
    data = make_sample_research_data()

    art1 = store.create("research_brief", pid, "research", data, producer)
    store.save(art1)
    store.mark_failed("research_brief", pid, 1)

    art2 = store.create("research_brief", pid, "research", data, producer)
    assert art2.artifact_version == 2
    store.save(art2)
    store.approve("research_brief", pid, 2)

    latest = store.latest("research_brief", pid)
    assert latest.artifact_version == 2
    assert latest.status == ArtifactStatus.APPROVED


def test_atomic_write_leaves_no_tmp_files(temp_store):
    store, root = temp_store
    pid = "proj_test_atomic"
    producer = ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash")
    data = make_sample_research_data()

    art = store.create("research_brief", pid, "research", data, producer)
    saved_path = store.save(art)

    assert saved_path.exists()
    stage_dir = root / pid / "research"
    tmp_files = list(stage_dir.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_loads_latest_version(temp_store):
    store, _ = temp_store
    pid = "proj_test_latest"
    producer = ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash")
    data = make_sample_research_data()

    art1 = store.create("research_brief", pid, "research", data, producer)
    store.save(art1)

    art2 = store.create("research_brief", pid, "research", data, producer)
    store.save(art2)

    latest = store.latest("research_brief", pid)
    assert latest.artifact_version == 2


def test_detects_corrupted_json(temp_store):
    store, root = temp_store
    pid = "proj_test_corrupt"
    producer = ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash")
    data = make_sample_research_data()

    art = store.create("research_brief", pid, "research", data, producer)
    filepath = store.save(art)

    # Corrupt the file content
    filepath.write_text("{ incomplete json...", encoding="utf-8")

    with pytest.raises(ArtifactCorruptedError):
        store.load("research_brief", pid, 1)


def test_detects_hash_mismatch(temp_store):
    store, root = temp_store
    pid = "proj_test_hash_mismatch"
    producer = ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash")
    data = make_sample_research_data()

    art = store.create("research_brief", pid, "research", data, producer)
    filepath = store.save(art)

    # Tamper with the data inside without updating content_hash
    content = json.loads(filepath.read_text(encoding="utf-8"))
    content["data"]["topic"] = "Tampered Topic"
    filepath.write_text(json.dumps(content), encoding="utf-8")

    with pytest.raises(ArtifactHashMismatchError):
        store.load("research_brief", pid, 1)


def test_type_mismatch_stage_rejected(temp_store):
    store, _ = temp_store
    pid = "proj_test_type_mismatch"
    producer = ProducerInfo(kind=ProducerKind.LLM, provider="gemini", model="gemini-2.0-flash")
    data = make_sample_research_data()

    # research_brief must be stage='research', attempting stage='proposal' must fail
    art = store.create("research_brief", pid, "proposal", data, producer)
    with pytest.raises(ArtifactTypeMismatchError):
        store.save(art)


def test_load_nonexistent_artifact_raises(temp_store):
    store, _ = temp_store
    with pytest.raises(ArtifactNotFoundError):
        store.load("research_brief", "nonexistent_pid", 1)
