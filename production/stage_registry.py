"""StageHandler protocol and StageRegistry.

In Phase 2, NO production stage handlers (research, proposal, script, etc.) are implemented.
Unimplemented stages explicitly return status NOT_IMPLEMENTED rather than creating fake artifacts.
Test suites can register deterministic test handlers into an isolated registry.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ProducerKind
from schemas.models.production import ProductionState


class StageResultStatus(str, Enum):
    """Execution status returned by a stage handler or StageRunner."""
    READY = "ready"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    FAILED = "failed"
    NOT_IMPLEMENTED = "not_implemented"


class StageHandlerResult(BaseModel):
    """The raw domain output returned by a StageHandler implementation."""
    status: StageResultStatus
    data: dict[str, Any] | None = None
    producer: ProducerInfo = Field(
        default_factory=lambda: ProducerInfo(kind=ProducerKind.SYSTEM)
    )
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    message: str = ""

    model_config = {"extra": "forbid"}


@runtime_checkable
class StageHandler(Protocol):
    """Contract for any stage execution worker (e.g. LLM agent, tool, script)."""

    def run(
        self,
        stage_name: str,
        state: ProductionState,
        inputs: dict[str, ArtifactEnvelope],
        **kwargs: Any,
    ) -> StageHandlerResult:
        """Execute stage domain work and return StageHandlerResult."""
        ...


class StageNotImplementedError(Exception):
    """Raised when an attempt is made to run a stage without a registered handler."""


class StageRegistry:
    """Registry mapping stage names to concrete StageHandler implementations."""

    def __init__(self) -> None:
        self._handlers: dict[str, StageHandler] = {}

    def register(self, stage_name: str, handler: StageHandler) -> None:
        """Register a handler for a stage name."""
        self._handlers[stage_name] = handler

    def unregister(self, stage_name: str) -> None:
        """Remove a registered handler."""
        self._handlers.pop(stage_name, None)

    def get(self, stage_name: str) -> StageHandler | None:
        """Retrieve the handler for a stage, or None if unimplemented."""
        return self._handlers.get(stage_name)

    def has(self, stage_name: str) -> bool:
        """Check if a handler is registered for this stage."""
        return stage_name in self._handlers

    def list_registered(self) -> list[str]:
        """List all stages with registered handlers."""
        return sorted(self._handlers.keys())

    def clear(self) -> None:
        """Clear all registered handlers (useful in testing)."""
        self._handlers.clear()


# Canonical shared bare registry instance
global_stage_registry = StageRegistry()


def register_phase3_handlers(registry: StageRegistry) -> StageRegistry:
    """Register real Phase 3 handlers into a target registry."""
    from stages.research.research_director import ResearchHandler
    from stages.proposal.proposal_director import ProposalHandler
    from stages.art_direction.art_direction_director import ArtDirectionHandler

    registry.register("research", ResearchHandler())
    registry.register("proposal", ProposalHandler())
    registry.register("art_direction", ArtDirectionHandler())
    return registry


def register_phase4_handlers(registry: StageRegistry) -> StageRegistry:
    """Register real Phase 4 handlers into a target registry."""
    from stages.script.script_director import ScriptHandler
    from stages.scene_plan.scene_planner import ScenePlanHandler

    registry.register("script", ScriptHandler())
    registry.register("scene_plan", ScenePlanHandler())
    return registry


def register_phase5_handlers(registry: StageRegistry) -> StageRegistry:
    """Register real Phase 5 handlers into a target registry."""
    from stages.assets.asset_director import AssetHandler

    registry.register("assets", AssetHandler())
    return registry


def register_phase6_handlers(registry: StageRegistry) -> StageRegistry:
    """Register the Phase 6 edit authority; no composition runtime is registered."""
    from stages.edit.edit_director import EditDirector
    registry.register("edit", EditDirector())
    return registry


def create_default_registry() -> StageRegistry:
    """Create a StageRegistry populated with real Phase 3 through Phase 6 production handlers.

    Unimplemented stages (compose, etc.) remain unregistered
    and return NOT_IMPLEMENTED.
    """
    reg = StageRegistry()
    register_phase3_handlers(reg)
    register_phase4_handlers(reg)
    register_phase5_handlers(reg)
    register_phase6_handlers(reg)
    return reg


_default_production_registry: StageRegistry | None = None


def get_default_stage_registry() -> StageRegistry:
    """Return the shared production registry with real Phase 3 handlers lazily initialized."""
    global _default_production_registry
    if _default_production_registry is None:
        _default_production_registry = create_default_registry()
    return _default_production_registry


class _LazyProductionRegistry(StageRegistry):
    def _target(self) -> StageRegistry:
        return get_default_stage_registry()

    def register(self, stage_name: str, handler: StageHandler) -> None:
        self._target().register(stage_name, handler)

    def unregister(self, stage_name: str) -> None:
        self._target().unregister(stage_name)

    def get(self, stage_name: str) -> StageHandler | None:
        return self._target().get(stage_name)

    def has(self, stage_name: str) -> bool:
        return self._target().has(stage_name)

    def list_registered(self) -> list[str]:
        return self._target().list_registered()

    def clear(self) -> None:
        self._target().clear()


# Canonical shared production registry with real Phase 3 handlers (lazily populated)
default_production_registry = _LazyProductionRegistry()

