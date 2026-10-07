"""Composition runtime interface. Routing decisions only; no rendering here."""
from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable


class RuntimeStatus(str, Enum):
    """Environment availability of a composition runtime."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MISCONFIGURED = "misconfigured"
    UNKNOWN = "unknown"


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


def _status_value(status) -> str:
    return status.value if isinstance(status, Enum) else str(status)


class DiagnosticCheck(dict):
    """A single environment check: {name, status, message, severity}."""

    def __init__(self, name: str, status: CheckStatus | str, message: str, severity: str = "info") -> None:
        super().__init__(name=name, status=_status_value(status), message=message, severity=severity)


class RuntimeDiagnostics(dict):
    """Structured diagnostics: {runtime_id, status, version, checks[], remote_available}.

    `status` describes local availability. `remote_available` is True only when
    a remote endpoint was actually probed successfully; Phase 7 never probes
    remote endpoints, so production diagnostics always report False here.
    """

    def __init__(self, runtime_id: str, status: RuntimeStatus | str, version: str | None, checks: list[dict], remote_available: bool = False) -> None:
        super().__init__(runtime_id=runtime_id, status=_status_value(status), version=version, checks=checks, remote_available=remote_available)


@runtime_checkable
class CompositionRuntime(Protocol):
    """Contract every composition runtime must satisfy for routing."""

    @property
    def runtime_id(self) -> str: ...
    @property
    def version(self) -> str | None: ...
    @property
    def capabilities(self) -> frozenset[str]: ...
    @property
    def supports_local(self) -> bool: ...
    @property
    def supports_remote(self) -> bool: ...

    def is_available(self) -> bool:
        """True only when the runtime can execute a job right now."""
        ...

    def validate_environment(self) -> RuntimeDiagnostics:
        """Probe the environment without rendering anything."""
        ...

    def validate_job(self, job: Any) -> list[dict]:
        """Return structured blockers for a job; empty means routable."""
        ...

    def prepare_job(self, job: Any) -> dict:
        """Return an execution plan for a valid job without executing it."""
        ...

    def get_diagnostics(self) -> RuntimeDiagnostics:
        """Return cached or freshly probed diagnostics."""
        ...
