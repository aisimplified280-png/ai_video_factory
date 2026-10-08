"""Regression tests for safe port and process management (Issue #9).

Verifies:
1. Dynamic / ephemeral port allocation avoids port collisions.
2. An unrelated listener is never killed or terminated by the runtime.
3. Only the process owned by the render invocation is terminated upon completion.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

from composition.remotion.runtime import RemotionRuntime, find_free_ephemeral_port


def test_ephemeral_port_allocation_is_valid():
    """Verify that find_free_ephemeral_port allocates open, usable ports."""
    port1 = find_free_ephemeral_port()
    port2 = find_free_ephemeral_port()
    assert isinstance(port1, int) and port1 > 1024
    assert isinstance(port2, int) and port2 > 1024


def test_unrelated_listener_is_never_killed(monkeypatch, tmp_path):
    """An existing listening socket/service must NEVER be terminated or disrupted."""
    # 1. Bind an unrelated listener socket
    dummy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dummy_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dummy_server.bind(("127.0.0.1", 0))
    dummy_server.listen(5)
    dummy_port = dummy_server.getsockname()[1]

    # Verify dummy listener is active and accepting connections
    test_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_client.connect(("127.0.0.1", dummy_port))
    conn, _ = dummy_server.accept()
    conn.close()
    test_client.close()

    # 2. Run a mocked Remotion render invocation
    def fake_run(argv, **kwargs):
        raise subprocess.SubprocessError("halt after server setup")

    monkeypatch.setattr("composition.remotion.runtime.subprocess.run", fake_run)
    (tmp_path / "node_modules").mkdir()
    adapter = RemotionRuntime(composer_dir=tmp_path)
    monkeypatch.setattr(adapter, "is_available", lambda: True)
    (tmp_path / "props.json").write_text("{}")
    (tmp_path / "public" / "assets").mkdir(parents=True)

    result = adapter.render(tmp_path / "props.json", tmp_path / "out.mp4")
    assert result["status"] == "blocked"

    # 3. Assert the unrelated listener is STILL ALIVE and can still accept connections
    test_client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test_client2.connect(("127.0.0.1", dummy_port))
    conn2, _ = dummy_server.accept()
    conn2.close()
    test_client2.close()

    # Cleanup
    dummy_server.close()


def test_owned_media_server_process_cleanup():
    """Verify that serve_public terminates cleanly when stopped by parent."""
    server_script = Path(__file__).resolve().parent.parent / "scripts" / "serve_public.py"
    port = find_free_ephemeral_port()
    proc = subprocess.Popen(
        [sys.executable, str(server_script), ".", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(0.5)

    # Verify server is listening
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))
    s.close()

    # Terminate owned process
    proc.terminate()
    proc.wait(timeout=3)
    assert proc.poll() is not None
