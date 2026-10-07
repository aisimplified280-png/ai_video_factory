"""Common enums and primitives shared across all models."""
from __future__ import annotations

from enum import Enum


class ArtifactStatus(str, Enum):
    """Lifecycle status of a persisted artifact."""
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProducerKind(str, Enum):
    """Who or what produced this artifact."""
    SYSTEM = "system"
    HUMAN = "human"
    LLM = "llm"
    TOOL = "tool"
    PROVIDER = "provider"


class ProductionStatus(str, Enum):
    """Lifecycle status of an entire production."""
    CREATED = "created"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class Severity(str, Enum):
    """Severity level for decisions, warnings, and errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ApprovalMode(str, Enum):
    """How a stage artifact is approved.

    AUTO         — system auto-approves if quality gates pass (default, works in all run modes)
    HUMAN        — requires explicit human approval (used in GUIDED / MANUAL mode)
    ALWAYS_AUTO  — never requires human approval even in GUIDED mode (override)
    """
    AUTO = "auto"
    HUMAN = "human"
    ALWAYS_AUTO = "always_auto"


class RunMode(str, Enum):
    """How the production runs end-to-end.

    AUTO    — Topic → finished video (fully automated, no human checkpoints)
    GUIDED  — Topic → 2-3 concepts → user selects → finished video
    MANUAL  — Full override: user can replace any artifact at any stage
    """
    AUTO = "auto"
    GUIDED = "guided"
    MANUAL = "manual"


class QualityGateType(str, Enum):
    """Type of comparison performed by a quality gate."""
    MIN = "min"
    MAX = "max"
    BOOL = "bool"
    PRESENCE = "presence"
    REGEX = "regex"
