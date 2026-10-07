"""Tests for the runtime router. Fake runtimes stay in isolated registries."""
from types import SimpleNamespace

import pytest

from composition.runtime import RuntimeStatus
from composition.runtime_errors import (
    BLOCKED_RUNTIME_UNAVAILABLE,
    RUNTIME_LOCK_MISMATCH,
    UNKNOWN_RUNTIME,
)
from composition.runtime_registry import RuntimeRecord, RuntimeRegistry
from composition.runtime_router import RuntimeRouter, validate_runtime_lock


def _concept(runtime="hyperframes", family="cinematic", mode="templated"):
    return {
        "concept_id": "concept_02",
        "hook": "A deterministic hook for routing tests",
        "audience_promise": "A deterministic promise.",
        "narrative_structure": "Hook then CTA",
        "visual_direction": "Deterministic direction",
        "tone": "Direct",
        "target_duration": 36.0,
        "renderer_family": family,
        "render_runtime": runtime,
        "composition_mode": mode,
    }


def _proposal_data(runtime="hyperframes", family="cinematic", mode="templated"):
    return {"concepts": [_concept(runtime, family, mode)], "selected_concept_id": "concept_02"}


def _edit_data(runtime="hyperframes", family="cinematic", mode="templated"):
    return {
        "production_id": "proj_router",
        "total_duration": 36.88,
        "platform_profile": "profiles/youtube_short.json",
        "platform": {},
        "runtime_lock_source": {
            "artifact_type": "proposal_packet",
            "version": 1,
            "content_hash": "sha256:" + "a" * 64,
            "locked_at": "2026-10-05T00:00:00+00:00",
            "locked_concept_id": "concept_02",
        },
        "renderer_family": family,
        "render_runtime": runtime,
        "composition_mode": mode,
        "timeline": [],
        "video_tracks": {},
        "audio_tracks": {"narration": [], "music": [], "sfx": []},
        "caption_track": [],
        "validation": {},
        "cta": {},
        "tracks": {"video": []},
    }


def _envelope(data, version=1, status="approved"):
    return SimpleNamespace(
        data=data,
        status=SimpleNamespace(value=status),
        artifact_version=version,
        content_hash="sha256:" + "a" * 64,
        parent_artifacts=[],
    )


def _state(active_version=1):
    return SimpleNamespace(get_active_version=lambda _type: active_version)


def _store(active_version=1):
    return SimpleNamespace(latest=lambda _type, _pid, version=None: _envelope(_edit_data(), version=active_version))


def _available_diagnostics(monkeypatch, status=RuntimeStatus.AVAILABLE):
    from composition import runtime_router

    def fake_diagnose(record):
        return {"runtime_id": record.runtime_id, "status": status.value, "version": "9.9", "checks": [], "remote_available": False}

    monkeypatch.setattr(runtime_router, "diagnose_runtime", fake_diagnose)


def _router_with_fake(monkeypatch, runtime_id="hyperframes", status=RuntimeStatus.AVAILABLE):
    registry = RuntimeRegistry()
    registry.register(RuntimeRecord(
        runtime_id=runtime_id, capabilities=frozenset({"video_layers"}),
        supports_local=True, supports_remote=True,
    ))
    _available_diagnostics(monkeypatch, status)
    return RuntimeRouter(registry=registry, projects_root="/tmp/projects")


def test_unknown_runtime_is_blocked():
    router = RuntimeRouter(projects_root="/tmp/projects")
    proposal = _proposal_data()
    proposal["concepts"][0]["render_runtime"] = "vegas_pro"
    result = router.prepare_job(
        "proj_router", _envelope(_edit_data(runtime="vegas_pro")), _envelope(proposal),
        state=_state(), store=_store(),
    )
    assert result.status == "blocked"
    assert result.job is None
    assert [b.code for b in result.blockers] == [UNKNOWN_RUNTIME]


def test_unavailable_locked_runtime_blocks_without_fallback(monkeypatch):
    router = _router_with_fake(monkeypatch, status=RuntimeStatus.UNAVAILABLE)
    result = router.prepare_job(
        "proj_router", _envelope(_edit_data()), _envelope(_proposal_data()),
        state=_state(), store=_store(),
    )
    assert result.status == "blocked"
    assert result.job is None
    assert [b.code for b in result.blockers] == [BLOCKED_RUNTIME_UNAVAILABLE]
    assert "remotion" not in result.blockers[0].message
    assert "ffmpeg" not in result.blockers[0].message


def test_lock_mismatch_blocks_without_autocorrect(monkeypatch):
    router = _router_with_fake(monkeypatch)
    edit = _edit_data(runtime="remotion")
    result = router.prepare_job(
        "proj_router", _envelope(edit), _envelope(_proposal_data()),
        state=_state(), store=_store(),
    )
    assert result.status == "blocked"
    assert [b.code for b in result.blockers] == [RUNTIME_LOCK_MISMATCH]
    assert edit["render_runtime"] == "remotion"  # input untouched


def test_valid_lock_produces_job_preserving_all_three_fields(monkeypatch):
    router = _router_with_fake(monkeypatch)
    result = router.prepare_job(
        "proj_router", _envelope(_edit_data()), _envelope(_proposal_data()),
        state=_state(), store=_store(),
    )
    assert result.status == "ready"
    assert (result.job.renderer_family, result.job.runtime_id, result.job.composition_mode) == ("cinematic", "hyperframes", "templated")
    assert result.job.edit_artifact_hash == "sha256:" + "a" * 64
    assert result.job.edit_artifact_version == 1


def test_stale_edit_is_blocked(monkeypatch):
    router = _router_with_fake(monkeypatch)
    result = router.prepare_job(
        "proj_router", _envelope(_edit_data(), version=1), _envelope(_proposal_data()),
        state=_state(active_version=2), store=_store(active_version=2),
    )
    assert result.status == "blocked"
    assert any(b.code == "EDIT_STALE" for b in result.blockers)


def test_unapproved_edit_is_blocked(monkeypatch):
    router = _router_with_fake(monkeypatch)
    result = router.prepare_job(
        "proj_router", _envelope(_edit_data(), status="ready"), _envelope(_proposal_data()),
        state=_state(), store=_store(),
    )
    assert result.status == "blocked"
    assert any(b.code == "EDIT_NOT_APPROVED" for b in result.blockers)


def test_remote_policy_resolves_remote_target(monkeypatch):
    from composition import runtime_router

    def fake_remote_diagnose(record):
        return {"runtime_id": record.runtime_id, "status": RuntimeStatus.UNKNOWN.value,
                "version": None, "checks": [], "remote_available": True}

    monkeypatch.setattr(runtime_router, "diagnose_runtime", fake_remote_diagnose)
    registry = RuntimeRegistry()
    registry.register(RuntimeRecord(
        runtime_id="hyperframes", capabilities=frozenset({"video_layers"}),
        supports_local=False, supports_remote=True,
    ))
    router = RuntimeRouter(registry=registry, projects_root="/tmp/projects")
    result = router.prepare_job(
        "proj_router", _envelope(_edit_data()), _envelope(_proposal_data()),
        state=_state(), store=_store(), remote_policy="remote",
    )
    assert result.status == "ready"
    assert result.job.execution_target == "remote"


def test_local_policy_rejects_remote_only_runtime(monkeypatch):
    registry = RuntimeRegistry()
    registry.register(RuntimeRecord(
        runtime_id="hyperframes", capabilities=frozenset({"video_layers"}),
        supports_local=False, supports_remote=True,
    ))
    _available_diagnostics(monkeypatch)
    router = RuntimeRouter(registry=registry, projects_root="/tmp/projects")
    result = router.prepare_job(
        "proj_router", _envelope(_edit_data()), _envelope(_proposal_data()),
        state=_state(), store=_store(), remote_policy="local",
    )
    assert result.status == "blocked"
    assert any(b.code == BLOCKED_RUNTIME_UNAVAILABLE for b in result.blockers)


def test_validate_runtime_lock_detects_each_field():
    proposal = _proposal_data()
    for field, bad in (("renderer_family", "documentary"), ("render_runtime", "remotion"), ("composition_mode", "atelier")):
        edit = dict(_edit_data())
        edit[field] = bad
        blockers = validate_runtime_lock(proposal, edit)
        assert [b.code for b in blockers] == [RUNTIME_LOCK_MISMATCH]


def test_provenance_mismatch_blocks_even_when_triples_agree(monkeypatch):
    router = _router_with_fake(monkeypatch)
    edit = _edit_data()
    edit["runtime_lock_source"] = dict(edit["runtime_lock_source"], version=2)
    result = router.prepare_job(
        "proj_router", _envelope(edit), _envelope(_proposal_data()),
        state=_state(), store=_store(),
    )
    assert result.status == "blocked"
    assert any(b.code == RUNTIME_LOCK_MISMATCH for b in result.blockers)


def test_fakes_never_leak_into_production_registry(monkeypatch):
    from composition.runtime_registry import create_default_registry
    _router_with_fake(monkeypatch)
    assert create_default_registry().list_registered() == ["ffmpeg_pil", "hyperframes", "remotion"]


def test_router_never_renders(monkeypatch):
    import composition.runtime_router as router_module
    assert not hasattr(router_module, "render")
    assert "render(" not in open(router_module.__file__, encoding="utf-8").read().replace("render_runtime", "")
