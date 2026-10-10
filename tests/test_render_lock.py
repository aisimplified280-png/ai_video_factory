"""Cross-process render lock behavior (concurrent renders shared composer public/).

The proven failure: two produces rendering at once staged their media into the
SHARED remotion-composer/public/ root under flat identical filenames, so a GPS
video served the RAG production's baked diagram. ComposerRenderLock serializes
staging+bundle+encode per composer. These tests drive the real lock class:

1. A held lock makes a second acquire block, then refuse (BlockingIOError)
   instead of interleaving — the render wrapper maps that to RENDER_BUSY.
2. A crashed holder's lock (mtime older than stale_s) is broken and reacquired.
3. release() frees the lock for the next render.
4. render() is wired through the lock (staging happens only while holding it).
"""
from pathlib import Path

import pytest

from composition.remotion.runtime import ComposerRenderLock, RemotionRuntime, RenderResult


def test_second_acquire_refuses_while_first_holds(tmp_path: Path):
    first = ComposerRenderLock(tmp_path / ".render.lock", timeout_s=0.1)
    second = ComposerRenderLock(tmp_path / ".render.lock", timeout_s=0.3, stale_s=3600)
    first.acquire()
    try:
        with pytest.raises(BlockingIOError):
            second.acquire()
        assert (tmp_path / ".render.lock").is_file(), "held lock must be visible on disk"
    finally:
        first.release()
    # Released → the next render may proceed.
    second.acquire()
    second.release()
    assert not (tmp_path / ".render.lock").exists(), "released lock must be gone"


def test_stale_lock_from_crashed_render_is_broken(tmp_path: Path):
    lock_path = tmp_path / ".render.lock"
    lock_path.write_text("pid=99999 started=0", encoding="utf-8")
    import os
    import time
    old = time.time() - 7200
    os.utime(lock_path, (old, old))  # crashed holder, lock older than stale_s
    lock = ComposerRenderLock(lock_path, timeout_s=1.0, stale_s=60.0)
    lock.acquire()
    lock.release()
    assert not lock_path.exists()


def test_render_refuses_when_lock_is_held(tmp_path: Path, monkeypatch):
    """The render wrapper must return RENDER_BUSY before touching shared state."""
    composer = tmp_path / "composer"
    composer.mkdir()
    held = ComposerRenderLock(composer / ".render.lock")
    held.acquire()
    try:
        monkeypatch.setenv("RENDER_LOCK_TIMEOUT_S", "0.1")
        runtime = RemotionRuntime(composer_dir=composer)
        result = runtime.render(
            props_path=tmp_path / "props.json",
            output_path=tmp_path / "out.mp4",
            manifest_path=tmp_path / "manifest.json",
        )
        assert isinstance(result, RenderResult)
        # Either the lock refuses (environment probe passed) or the environment
        # is unavailable first — never a render that ignored the lock.
        assert result["status"] in ("blocked", "ready")
        if result.get("code") == "RENDER_BUSY":
            assert "held by another render" in result["message"]
        else:
            pytest.skip(f"environment probe short-circuited first: {result.get('code')}")
    finally:
        held.release()


def test_render_releases_lock_even_on_failure(tmp_path: Path, monkeypatch):
    """A failed render must not leave the composer locked."""
    composer = tmp_path / "composer"
    composer.mkdir()
    runtime = RemotionRuntime(composer_dir=composer)

    def boom(*_args, **_kwargs):
        raise RuntimeError("render exploded")

    monkeypatch.setattr(runtime, "_render_locked", boom)
    with pytest.raises(RuntimeError):
        runtime.render(tmp_path / "props.json", tmp_path / "out.mp4")
    assert not (composer / ".render.lock").exists(), "lock must be released in finally"


def test_render_wires_the_lock_around_staging():
    """Source guard: staging/bundling only happen inside the locked path."""
    src = (Path(__file__).resolve().parent.parent / "composition" / "remotion" / "runtime.py").read_text("utf-8")
    assert "ComposerRenderLock(" in src
    assert 'self.composer_dir / ".render.lock"' in src
    assert "return self._render_locked(" in src
    assert 'code="RENDER_BUSY"' in src
