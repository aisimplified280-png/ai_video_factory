"""Registry of known composition runtimes. Routing metadata only, no rendering."""
from __future__ import annotations

from dataclasses import dataclass, field

from .runtime_capabilities import declared_capabilities


@dataclass(frozen=True)
class RuntimeRecord:
    """Static routing record for one composition runtime."""
    runtime_id: str
    version: str | None = None
    enabled: bool = True
    capabilities: frozenset[str] = field(default_factory=frozenset)
    supports_local: bool = True
    supports_remote: bool = False
    description: str = ""


class UnknownRuntimeError(KeyError):
    """Raised when a runtime id is not registered."""


class RuntimeRegistry:
    """Maps runtime ids to their routing records."""

    def __init__(self) -> None:
        self._records: dict[str, RuntimeRecord] = {}

    def register(self, record: RuntimeRecord) -> None:
        self._records[record.runtime_id] = record

    def unregister(self, runtime_id: str) -> None:
        self._records.pop(runtime_id, None)

    def get(self, runtime_id: str) -> RuntimeRecord:
        try:
            return self._records[runtime_id]
        except KeyError:
            raise UnknownRuntimeError(f"Unknown composition runtime: {runtime_id!r}") from None

    def has(self, runtime_id: str) -> bool:
        return runtime_id in self._records

    def list_registered(self) -> list[str]:
        return sorted(self._records)


def create_default_registry() -> RuntimeRegistry:
    """Production registry: remotion, hyperframes, ffmpeg_pil. Nothing else."""
    registry = RuntimeRegistry()
    registry.register(RuntimeRecord(
        runtime_id="remotion",
        enabled=True,
        capabilities=declared_capabilities("remotion"),
        supports_local=True,
        supports_remote=True,
        description="React/TypeScript timeline composition; local when Node toolchain is present, otherwise remote.",
    ))
    registry.register(RuntimeRecord(
        runtime_id="hyperframes",
        enabled=True,
        capabilities=declared_capabilities("hyperframes"),
        supports_local=False,
        supports_remote=True,
        description="HTML/CSS motion-graphics composition; remote-only in this factory.",
    ))
    registry.register(RuntimeRecord(
        runtime_id="ffmpeg_pil",
        enabled=True,
        capabilities=declared_capabilities("ffmpeg_pil"),
        supports_local=True,
        supports_remote=False,
        description="Legacy local FFmpeg/PIL pipeline. Only for explicitly locked workflows; never an automatic fallback.",
    ))
    return registry


default_runtime_registry = create_default_registry()
