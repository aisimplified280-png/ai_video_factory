"""Structured composition errors and blocker codes. No silent fallbacks."""
from __future__ import annotations

from dataclasses import dataclass

UNKNOWN_RUNTIME = "UNKNOWN_RUNTIME"
RUNTIME_LOCK_MISMATCH = "RUNTIME_LOCK_MISMATCH"
BLOCKED_RUNTIME_UNAVAILABLE = "BLOCKED_RUNTIME_UNAVAILABLE"
EDIT_NOT_APPROVED = "EDIT_NOT_APPROVED"
EDIT_STALE = "EDIT_STALE"
EDIT_NOT_FOUND = "EDIT_NOT_FOUND"
PLATFORM_MISMATCH = "PLATFORM_MISMATCH"
COMPOSITION_MODE_UNSUPPORTED = "COMPOSITION_MODE_UNSUPPORTED"
RENDERER_FAMILY_UNSUPPORTED = "RENDERER_FAMILY_UNSUPPORTED"
REMOTE_POLICY_UNSUPPORTED = "REMOTE_POLICY_UNSUPPORTED"


@dataclass(frozen=True)
class CompositionBlocker:
    """A single structured reason a composition job cannot proceed."""
    code: str
    message: str
    severity: str = "critical"
    correction: str = ""


class CompositionError(Exception):
    """Base class for composition routing failures."""


class UnknownRuntimeError(CompositionError):
    """Raised when the locked runtime is not registered."""


class RuntimeUnavailableError(CompositionError):
    """Raised when the locked runtime cannot execute right now. Never falls back."""


class RuntimeLockMismatchError(CompositionError):
    """Raised when proposal and edit runtime locks disagree. Never auto-corrects."""


class StaleEditError(CompositionError):
    """Raised when the referenced edit artifact is not the active version."""
