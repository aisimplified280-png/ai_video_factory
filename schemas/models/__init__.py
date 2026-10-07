"""Pydantic V2 models for the AI Simplified Lab Production System V2.

These are the typed contracts between every stage in the pipeline.
Import from here rather than individual modules when possible.
"""
from .common import (
    ArtifactStatus,
    ProducerKind,
    ProductionStatus,
    Severity,
    ApprovalMode,
    RunMode,
)
from .artifact import (
    ProducerInfo,
    ArtifactReference,
    ArtifactEnvelope,
    ArtifactState,
)
from .production import (
    BudgetState,
    Decision,
    Warning,
    ProductionError,
    ProductionState,
)
from .pipeline import (
    QualityGate,
    QualityGateType,
    ApprovalPolicy,
    StageDefinition,
    BudgetPolicy,
    RenderRuntimePolicy,
    PipelineDefinition,
)

__all__ = [
    # common
    "ArtifactStatus", "ProducerKind", "ProductionStatus",
    "Severity", "ApprovalMode", "RunMode",
    # artifact
    "ProducerInfo", "ArtifactReference", "ArtifactEnvelope", "ArtifactState",
    # production
    "BudgetState", "Decision", "Warning", "ProductionError", "ProductionState",
    # pipeline
    "QualityGate", "QualityGateType", "ApprovalPolicy", "StageDefinition",
    "BudgetPolicy", "RenderRuntimePolicy", "PipelineDefinition",
]
