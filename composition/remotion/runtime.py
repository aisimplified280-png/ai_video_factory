"""Remotion runtime adapter. Executes remotion jobs only; refuses everything else."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from composition.diagnostics import diagnose_runtime, resolve_tool_argv
from composition.runtime import RuntimeStatus
from composition.runtime_capabilities import declared_capabilities
from composition.runtime_registry import create_default_registry

FACTORY_ROOT = Path(__file__).resolve().parent.parent.parent
COMPOSER_DIR = FACTORY_ROOT / "remotion-composer"
_RENDER_TIMEOUT = 3600


def find_free_ephemeral_port() -> int:
    """Allocate a free ephemeral port safely from the operating system."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        return int(s.getsockname()[1])


def declared_remotion_version() -> str | None:
    """Pinned Remotion version from package.json. No Node required to read it."""
    try:
        package = json.loads((COMPOSER_DIR / "package.json").read_text(encoding="utf-8"))
        return package.get("dependencies", {}).get("remotion")
    except (OSError, ValueError):
        return None


class RenderResult(dict):
    """Outcome of a render attempt: ready with paths, or blocked with a code."""

    def __init__(self, status: str, output_path: str | None = None,
                 manifest: dict | None = None, code: str | None = None,
                 message: str = "") -> None:
        super().__init__(status=status, output_path=output_path, manifest=manifest, code=code, message=message)


class ComposerRenderLock:
    """Cross-process exclusive lock for one composer render.

    Renders stage media into the composer's shared ``public/`` root under flat,
    identically-named files (``ast_scene_03_mid.png``) and build inside the
    same bundle workspace. Two concurrent renders therefore overwrite each
    other's staged assets — proven to produce topic-crossed frames (a GPS video
    showed the RAG production's diagram). One render at a time per composer;
    a crashed holder's lock breaks after ``stale_s``.
    """

    def __init__(self, path: Path | str, timeout_s: float = 4 * 3600.0,
                 stale_s: float = 2 * 3600.0) -> None:
        self._path = Path(path)
        self._timeout_s = timeout_s
        self._stale_s = stale_s
        self._held = False

    def acquire(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self._timeout_s
        while True:
            try:
                fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if self._break_if_stale():
                    continue
                if time.monotonic() > deadline:
                    raise BlockingIOError(
                        f"render busy: {self._path} is held by another render "
                        f"(waited {self._timeout_s:.0f}s)"
                    )
                time.sleep(2.0)
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(f"pid={os.getpid()} started={time.time():.3f}")
            self._held = True
            return

    def _break_if_stale(self) -> bool:
        try:
            age = time.time() - os.path.getmtime(self._path)
        except OSError:
            return True  # vanished between attempts
        if age > self._stale_s:
            try:
                os.unlink(self._path)
                return True
            except OSError:
                return False
        return False

    def release(self) -> None:
        if self._held:
            try:
                os.unlink(self._path)
            except OSError:
                pass
            self._held = False

    def __enter__(self) -> "ComposerRenderLock":
        self.acquire()
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.release()


class RemotionRuntime:
    """Concrete remotion runtime. Availability is probed, never assumed."""

    runtime_id = "remotion"

    def __init__(self, composer_dir: Path | str | None = None) -> None:
        self.composer_dir = Path(composer_dir) if composer_dir is not None else COMPOSER_DIR
        record = create_default_registry().get("remotion")
        self._capabilities = record.capabilities
        self.supports_local = record.supports_local
        self.supports_remote = record.supports_remote

    @property
    def version(self) -> str | None:
        return declared_remotion_version()

    @property
    def capabilities(self) -> frozenset[str]:
        return self._capabilities if self._capabilities else declared_capabilities("remotion")

    def is_available(self) -> bool:
        return diagnose_runtime(create_default_registry().get("remotion"))["status"] == RuntimeStatus.AVAILABLE.value

    def validate_environment(self) -> dict:
        return dict(diagnose_runtime(create_default_registry().get("remotion")))

    def validate_job(self, job: Any) -> list[dict]:
        """Refuse any job not locked to remotion. Never reroute it elsewhere."""
        runtime_id = job.get("runtime_id") if isinstance(job, dict) else getattr(job, "runtime_id", None)
        if runtime_id != "remotion":
            return [{"code": "RUNTIME_LOCK_MISMATCH",
                     "message": f"Remotion adapter refused a job locked to {runtime_id!r}; it will not execute another runtime's job.",
                     "severity": "critical",
                     "correction": "Route the job to its locked runtime."}]
        return []

    def render(self, props_path: Path | str, output_path: Path | str,
               manifest_path: Path | str | None = None,
               concurrency: int | None = None) -> RenderResult:
        """Render props to MP4. Unavailable locally means blocked, never a fallback.

        Concurrency defaults to the RENDER_CONCURRENCY environment variable,
        falling back to 2. Kept conservative to protect interactive machines.

        Serialized per composer by ComposerRenderLock: staging, bundling and
        encoding all share the composer's public/ root and bundle workspace.
        Queues behind an in-flight render (up to RENDER_LOCK_TIMEOUT_S, 90 min)
        instead of interleaving.
        """
        lock = ComposerRenderLock(
            self.composer_dir / ".render.lock",
            timeout_s=float(os.getenv("RENDER_LOCK_TIMEOUT_S", str(90 * 60))),
        )
        try:
            lock.acquire()
        except BlockingIOError as exc:
            return RenderResult(status="blocked", code="RENDER_BUSY", message=str(exc))
        try:
            return self._render_locked(props_path, output_path, manifest_path, concurrency)
        finally:
            lock.release()

    def _render_locked(self, props_path: Path | str, output_path: Path | str,
                       manifest_path: Path | str | None = None,
                       concurrency: int | None = None) -> RenderResult:
        if not self.is_available():
            return RenderResult(
                status="blocked",
                code="BLOCKED_RUNTIME_UNAVAILABLE",
                message="Remotion toolchain unavailable locally; refusing to substitute another renderer. Use a remote worker.",
            )
        node_modules = self.composer_dir / "node_modules"
        npm = resolve_tool_argv("npm")
        node = resolve_tool_argv("node")
        if npm is None or node is None:
            return RenderResult(status="blocked", code="BLOCKED_RUNTIME_UNAVAILABLE",
                                message="npm/node executables could not be resolved on PATH or the default install directory.")
        lockfile = self.composer_dir / "package-lock.json"
        if not node_modules.is_dir():
            install = subprocess.run(
                [*npm, "ci" if lockfile.is_file() else "install", "--no-audit", "--no-fund"],
                cwd=self.composer_dir, capture_output=True, text=True, timeout=_RENDER_TIMEOUT,
            )
            if install.returncode != 0:
                return RenderResult(status="blocked", code="BLOCKED_RUNTIME_UNAVAILABLE",
                                    message=f"npm install failed:\n{(install.stderr or '').strip()[-800:]}")
        public_dir = Path(props_path).parent / "public"
        # Sync bundled media into the composer's own public/ root. staticFile()
        # URL-encodes its whole argument, so nested subdirectories are
        # unreachable: media must sit flat at the public root, which is also
        # why no --public-dir override is passed (the composer default wins).
        try:
            staged = sorted((public_dir / "assets").glob("*")) if (public_dir / "assets").is_dir() else []
            composer_public = self.composer_dir / "public"
            composer_public.mkdir(parents=True, exist_ok=True)
            for asset_file in staged:
                if asset_file.is_file():
                    shutil.copyfile(asset_file, composer_public / asset_file.name)
        except OSError as exc:
            return RenderResult(status="blocked", code="RENDER_FAILED",
                                message=f"Could not stage media into the composer public dir: {exc}")
        import os
        workers = concurrency or int(os.getenv("RENDER_CONCURRENCY", "2"))
        
        server_process = None
        media_port = None
        try:
            import os
            import sys
            import time
            workspace_root = FACTORY_ROOT
            server_script = workspace_root / "scripts" / "serve_public.py"
            assets_dir = public_dir / "assets"
            if server_script.is_file() and assets_dir.is_dir():
                media_port = find_free_ephemeral_port()
                server_process = subprocess.Popen(
                    [sys.executable, str(server_script), str(assets_dir), str(media_port)],
                    cwd=str(workspace_root),
                )
                time.sleep(0.5)

            render_env = dict(os.environ)
            if media_port is not None:
                render_env["MEDIA_SERVER_PORT"] = str(media_port)
                render_env["REMOTION_MEDIA_PORT"] = str(media_port)
                p_file = Path(props_path)
                if p_file.is_file():
                    content = p_file.read_text(encoding="utf-8")
                    updated = re.sub(r"http://127\.0\.0\.1:\d+/", f"http://127.0.0.1:{media_port}/", content)
                    p_file.write_text(updated, encoding="utf-8")

            subprocess.run(
                [*node, "scripts/render.mjs", "--props", str(props_path), "--output", str(output_path), "--public-dir", "public"]
                + (["--manifest", str(manifest_path)] if manifest_path else [])
                + ["--concurrency", str(workers)],
                cwd=self.composer_dir, check=True, capture_output=True, encoding="utf-8", timeout=_RENDER_TIMEOUT,
                env=render_env,
            )
        except subprocess.CalledProcessError as exc:
            err_msg = (exc.stderr or exc.stdout or str(exc))[-1500:]
            return RenderResult(status="blocked", code="RENDER_FAILED", message=f"Remotion render failed (code {exc.returncode}):\n{err_msg}")
        except (OSError, subprocess.SubprocessError) as exc:
            return RenderResult(status="blocked", code="RENDER_FAILED", message=f"Remotion render failed: {exc}")
        finally:
            if server_process is not None:
                try:
                    server_process.terminate()
                    server_process.wait(timeout=2)
                except Exception:
                    try:
                        server_process.kill()
                        server_process.wait(timeout=1)
                    except Exception:
                        pass
        manifest = None
        if manifest_path and Path(manifest_path).is_file():
            manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        return RenderResult(status="ready", output_path=str(output_path), manifest=manifest)

    def get_diagnostics(self) -> dict:
        return self.validate_environment()

    @staticmethod
    def node_modules_present(composer_dir: Path | str | None = None) -> bool:
        root = Path(composer_dir) if composer_dir is not None else COMPOSER_DIR
        return (root / "node_modules").is_dir() and resolve_tool_argv("node") is not None
