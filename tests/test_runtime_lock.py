"""Tests that the proposal runtime lock is authoritative end to end."""
from types import SimpleNamespace

from composition.runtime_router import RuntimeRouter, validate_runtime_lock
from composition.runtime_registry import RuntimeRecord, RuntimeRegistry
from composition.runtime import RuntimeStatus


def _proposal(triple=("explainer", "remotion", "atelier")):
    family, runtime, mode = triple
    return {
        "concepts": [{
            "concept_id": "c1",
            "hook": "A deterministic hook",
            "audience_promise": "A deterministic promise.",
            "narrative_structure": "Hook then CTA",
            "visual_direction": "Deterministic direction",
            "tone": "Direct",
            "target_duration": 12.0,
            "renderer_family": family,
            "render_runtime": runtime,
            "composition_mode": mode,
        }],
        "selected_concept_id": "c1",
    }


def _edit(triple=("explainer", "remotion", "atelier")):
    family, runtime, mode = triple
    return {
        "renderer_family": family,
        "render_runtime": runtime,
        "composition_mode": mode,
        "platform_profile": "profiles/youtube_short.json",
        "runtime_lock_source": {
            "artifact_type": "proposal_packet",
            "version": 1,
            "content_hash": "sha256:" + "b" * 64,
            "locked_at": "2026-10-05T00:00:00+00:00",
            "locked_concept_id": "c1",
        },
    }


def _envelope(data, version=1):
    return SimpleNamespace(
        data=data,
        status=SimpleNamespace(value="approved"),
        artifact_version=version,
        content_hash="sha256:" + "b" * 64,
        parent_artifacts=[],
    )


def test_agreeing_triple_passes_lock_validation():
    assert validate_runtime_lock(_proposal(), _edit()) == []


def test_each_divergent_field_blocks():
    for triple in (("cinematic", "remotion", "atelier"), ("explainer", "hyperframes", "atelier"), ("explainer", "remotion", "templated")):
        blockers = validate_runtime_lock(_proposal(), _edit(triple))
        assert [b.code for b in blockers] == ["RUNTIME_LOCK_MISMATCH"]


def test_router_preserves_provenance_in_job(monkeypatch):
    from composition import runtime_router

    def fake_diagnose(record):
        return {"runtime_id": record.runtime_id, "status": RuntimeStatus.AVAILABLE.value, "version": "1.0", "checks": []}

    monkeypatch.setattr(runtime_router, "diagnose_runtime", fake_diagnose)
    registry = RuntimeRegistry()
    registry.register(RuntimeRecord(runtime_id="remotion", capabilities=frozenset(), supports_local=True, supports_remote=True))
    router = RuntimeRouter(registry=registry, projects_root="/tmp/projects")
    state = SimpleNamespace(get_active_version=lambda _type: 1)
    store = SimpleNamespace(latest=lambda _type, _pid, version=None: _envelope(_edit()))
    result = router.prepare_job("proj_lock", _envelope(_edit()), _envelope(_proposal()), state=state, store=store)
    assert result.status == "ready"
    assert result.job.runtime_lock_source["locked_concept_id"] == "c1"
    assert result.job.runtime_lock_source["version"] == 1


def test_router_rejects_provenance_pointing_at_another_proposal(monkeypatch):
    from composition import runtime_router

    def fake_diagnose(record):
        return {"runtime_id": record.runtime_id, "status": RuntimeStatus.AVAILABLE.value, "version": "1.0", "checks": []}

    monkeypatch.setattr(runtime_router, "diagnose_runtime", fake_diagnose)
    registry = RuntimeRegistry()
    registry.register(RuntimeRecord(runtime_id="remotion", capabilities=frozenset(), supports_local=True, supports_remote=True))
    router = RuntimeRouter(registry=registry, projects_root="/tmp/projects")
    edit = _edit()
    edit["runtime_lock_source"] = dict(edit["runtime_lock_source"], content_hash="sha256:" + "c" * 64)
    state = SimpleNamespace(get_active_version=lambda _type: 1)
    store = SimpleNamespace(latest=lambda _type, _pid, version=None: _envelope(edit))
    result = router.prepare_job("proj_lock", _envelope(edit), _envelope(_proposal()), state=state, store=store)
    assert result.status == "blocked"
    assert any(b.code == "RUNTIME_LOCK_MISMATCH" for b in result.blockers)
