"""Phase 7 composition runtime routing; it selects and validates runtimes, never renders."""
from .composition_job import CompositionJob, JobResult
from .diagnostics import diagnose_all, diagnose_runtime
from .runtime import CompositionRuntime, DiagnosticCheck, RuntimeDiagnostics, RuntimeStatus
from .runtime_capabilities import CAPABILITY_DESCRIPTIONS, Capability
from .runtime_errors import (
    BLOCKED_RUNTIME_UNAVAILABLE,
    COMPOSITION_MODE_UNSUPPORTED,
    EDIT_NOT_APPROVED,
    EDIT_STALE,
    PLATFORM_MISMATCH,
    RENDERER_FAMILY_UNSUPPORTED,
    RUNTIME_LOCK_MISMATCH,
    UNKNOWN_RUNTIME,
    CompositionBlocker,
    CompositionError,
    RuntimeLockMismatchError,
    RuntimeUnavailableError,
    StaleEditError,
    UnknownRuntimeError,
)
from .runtime_registry import RuntimeRecord, RuntimeRegistry, create_default_registry
from .runtime_router import RuntimeRouter

__all__ = [
    "BLOCKED_RUNTIME_UNAVAILABLE",
    "CAPABILITY_DESCRIPTIONS",
    "COMPOSITION_MODE_UNSUPPORTED",
    "EDIT_NOT_APPROVED",
    "EDIT_STALE",
    "PLATFORM_MISMATCH",
    "RENDERER_FAMILY_UNSUPPORTED",
    "RUNTIME_LOCK_MISMATCH",
    "UNKNOWN_RUNTIME",
    "Capability",
    "CompositionBlocker",
    "CompositionError",
    "CompositionJob",
    "CompositionRuntime",
    "DiagnosticCheck",
    "JobResult",
    "RuntimeDiagnostics",
    "RuntimeLockMismatchError",
    "RuntimeRecord",
    "RuntimeRegistry",
    "RuntimeRouter",
    "RuntimeStatus",
    "RuntimeUnavailableError",
    "StaleEditError",
    "UnknownRuntimeError",
    "create_default_registry",
    "diagnose_all",
    "diagnose_runtime",
]
