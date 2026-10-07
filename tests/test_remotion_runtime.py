"""Adapter tests: remotion jobs execute, everything else is refused, never rerouted."""
from types import SimpleNamespace

from composition.remotion.runtime import RemotionRuntime, declared_remotion_version


def _job(runtime_id="remotion"):
    return SimpleNamespace(
        runtime_id=runtime_id, production_id="proj_rt", edit_artifact_version=1,
        edit_artifact_hash="sha256:" + "a" * 64, renderer_family="explainer",
        composition_mode="atelier", platform_profile="profiles/youtube_short.json",
        output_format="mp4", remote_policy="auto",
    )


def test_declared_version_matches_pinned_package():
    assert declared_remotion_version() == "4.0.0"


def test_adapter_refuses_other_runtimes_jobs():
    adapter = RemotionRuntime()
    blockers = adapter.validate_job(_job("hyperframes"))
    assert [b["code"] for b in blockers] == ["RUNTIME_LOCK_MISMATCH"]
    assert "will not execute another runtime's job" in blockers[0]["message"]


def test_adapter_accepts_remotion_job_shape():
    assert RemotionRuntime().validate_job(_job("remotion")) == []


def test_render_blocks_when_toolchain_unavailable(tmp_path, monkeypatch):
    import composition.remotion.runtime as runtime_module

    monkeypatch.setattr(runtime_module, "COMPOSER_DIR", tmp_path / "composer")
    adapter = RemotionRuntime(composer_dir=tmp_path / "composer")
    monkeypatch.setattr(adapter, "is_available", lambda: False)
    result = adapter.render(tmp_path / "props.json", tmp_path / "out.mp4")
    assert result["status"] == "blocked"
    assert result["code"] == "BLOCKED_RUNTIME_UNAVAILABLE"
    assert result["output_path"] is None
    assert not (tmp_path / "out.mp4").exists()


def test_render_never_calls_legacy_or_alternate_runtimes(tmp_path, monkeypatch):
    import composition.remotion.runtime as runtime_module

    calls = []

    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError("render path must not execute any subprocess")

    monkeypatch.setattr(runtime_module.subprocess, "run", forbidden)
    adapter = RemotionRuntime(composer_dir=tmp_path / "composer")
    monkeypatch.setattr(adapter, "is_available", lambda: False)
    result = adapter.render(tmp_path / "props.json", tmp_path / "out.mp4")
    assert result["status"] == "blocked"
    assert calls == []


def test_availability_reflects_diagnostics():
    adapter = RemotionRuntime()
    assert isinstance(adapter.is_available(), bool)
    diagnostics = adapter.get_diagnostics()
    assert diagnostics["runtime_id"] == "remotion"
    assert {c["name"] for c in diagnostics["checks"]} >= {"node_available", "npm_available", "remotion_project"}
