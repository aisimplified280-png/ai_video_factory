"""Local runtime tests: adapter behavior on this machine without rendering."""
import subprocess

from composition.remotion.runtime import RemotionRuntime


def test_local_runtime_reports_availability():
    adapter = RemotionRuntime()
    assert isinstance(adapter.is_available(), bool)
    assert adapter.get_diagnostics()["runtime_id"] == "remotion"


def test_render_passes_concurrency_flag(monkeypatch, tmp_path):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        raise subprocess.SubprocessError("stop here")

    monkeypatch.setattr("composition.remotion.runtime.subprocess.run", fake_run)
    (tmp_path / "node_modules").mkdir()
    adapter = RemotionRuntime(composer_dir=tmp_path)
    monkeypatch.setattr(adapter, "is_available", lambda: True)
    (tmp_path / "props.json").write_text("{}")
    (tmp_path / "public" / "assets").mkdir(parents=True)
    result = adapter.render(tmp_path / "props.json", tmp_path / "out.mp4", concurrency=3)
    assert result["status"] == "blocked"
    assert "--concurrency" in calls[0] and "3" in calls[0]


def test_render_defaults_to_conservative_concurrency(monkeypatch, tmp_path):

    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        raise subprocess.SubprocessError("stop here")

    monkeypatch.setattr("composition.remotion.runtime.subprocess.run", fake_run)
    monkeypatch.delenv("RENDER_CONCURRENCY", raising=False)
    (tmp_path / "node_modules").mkdir()
    adapter = RemotionRuntime(composer_dir=tmp_path)
    monkeypatch.setattr(adapter, "is_available", lambda: True)
    (tmp_path / "props.json").write_text("{}")
    (tmp_path / "public" / "assets").mkdir(parents=True)
    adapter.render(tmp_path / "props.json", tmp_path / "out.mp4")
    index = calls[0].index("--concurrency")
    assert int(calls[0][index + 1]) <= 2


def test_browser_check_present_in_diagnostics():
    diagnostics = RemotionRuntime().get_diagnostics()
    assert "browser_runtime" in {check["name"] for check in diagnostics["checks"]}
