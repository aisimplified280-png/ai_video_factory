"""Tests for the immutable CompositionJob contract."""
import pytest
from pydantic import ValidationError

from composition.composition_job import (
    CompositionJob,
    build_output_path,
    load_platform_profile,
    platform_aspect_ratio,
    resolve_execution_target,
)


def _job(**overrides):
    fields = {
        "production_id": "proj_job",
        "edit_artifact_version": 5,
        "edit_artifact_hash": "sha256:" + "d" * 64,
        "runtime_id": "hyperframes",
        "runtime_version": None,
        "renderer_family": "cinematic",
        "composition_mode": "templated",
        "platform_profile": "profiles/youtube_short.json",
        "output_path": "/tmp/projects/proj_job/composition/hyperframes_edit-v005.mp4",
        "remote_policy": "auto",
        "execution_target": "remote",
    }
    fields.update(overrides)
    return CompositionJob(**fields)


def test_job_references_exact_edit_hash():
    job = _job()
    assert job.edit_artifact_hash == "sha256:" + "d" * 64
    assert job.edit_artifact_version == 5


def test_job_rejects_malformed_hash():
    with pytest.raises(ValidationError):
        _job(edit_artifact_hash="not-a-hash")


def test_job_is_immutable():
    job = _job()
    with pytest.raises(ValidationError):
        job.runtime_id = "remotion"


def test_job_rejects_unknown_renderer_family_and_mode():
    with pytest.raises(ValidationError):
        _job(renderer_family="powerpoint")
    with pytest.raises(ValidationError):
        _job(composition_mode="slideshow")


def test_output_path_is_deterministic():
    assert build_output_path("/tmp/projects", "proj_job", "hyperframes", 5) == \
        "/tmp/projects/proj_job/composition/hyperframes_edit-v005.mp4"


def test_platform_profile_loads_without_scattered_constants():
    profile = load_platform_profile("profiles/youtube_short.json")
    assert (profile["resolution"]["width"], profile["resolution"]["height"], profile["fps"]) == (1080, 1920, 30)
    assert platform_aspect_ratio(profile) == "9:16"


def test_platform_profile_missing_is_an_error():
    with pytest.raises(FileNotFoundError):
        load_platform_profile("profiles/does_not_exist.json")


def test_remote_policy_matrix():
    assert resolve_execution_target("local", True, False, True, False) == "local"
    assert resolve_execution_target("local", False, True, False, True) is None
    assert resolve_execution_target("remote", False, True, False, True) == "remote"
    assert resolve_execution_target("remote", True, False, True, False) is None
    assert resolve_execution_target("auto", True, True, True, False) == "local"
    assert resolve_execution_target("auto", False, True, False, True) == "remote"
    assert resolve_execution_target("auto", False, False, False, False) is None


def test_legacy_job_only_when_explicitly_locked(monkeypatch):
    from types import SimpleNamespace
    from composition import runtime_router
    from composition.runtime_registry import RuntimeRecord, RuntimeRegistry
    from composition.runtime import RuntimeStatus
    from composition.runtime_router import RuntimeRouter

    def fake_diagnose(record):
        status = RuntimeStatus.AVAILABLE if record.runtime_id == "ffmpeg_pil" else RuntimeStatus.UNAVAILABLE
        return {"runtime_id": record.runtime_id, "status": status.value, "version": "9.0", "checks": []}

    monkeypatch.setattr(runtime_router, "diagnose_runtime", fake_diagnose)
    registry = RuntimeRegistry()
    for runtime_id in ("remotion", "hyperframes", "ffmpeg_pil"):
        registry.register(RuntimeRecord(runtime_id=runtime_id, capabilities=frozenset(), supports_local=True, supports_remote=False))
    router = RuntimeRouter(registry=registry, projects_root="/tmp/projects")
    edit = {
        "renderer_family": "explainer", "render_runtime": "ffmpeg_pil", "composition_mode": "atelier",
        "platform_profile": "profiles/youtube_short.json", "runtime_lock_source": {},
        "total_duration": 30.0,
    }
    proposal = {"concepts": [dict(concept_id="c1", hook="h", audience_promise="p", narrative_structure="n",
                                  visual_direction="v", tone="t", target_duration=30.0,
                                  renderer_family="explainer", render_runtime="ffmpeg_pil", composition_mode="atelier")],
                "selected_concept_id": "c1"}
    edit_env = SimpleNamespace(data=edit, status=SimpleNamespace(value="approved"),
                               artifact_version=1, content_hash="sha256:" + "e" * 64, parent_artifacts=[])
    prop_env = SimpleNamespace(data=proposal, status=SimpleNamespace(value="approved"),
                               artifact_version=1, content_hash="sha256:" + "f" * 64, parent_artifacts=[])
    state = SimpleNamespace(get_active_version=lambda _type: 1)
    store = SimpleNamespace(latest=lambda _type, _pid, version=None: edit_env)
    result = router.prepare_job("proj_legacy", edit_env, prop_env, state=state, store=store)
    assert result.status == "ready"
    assert result.job.runtime_id == "ffmpeg_pil"
