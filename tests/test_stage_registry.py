"""Tests for production/stage_registry.py."""
import pytest
from production.stage_registry import (
    StageRegistry,
    StageResultStatus,
    StageHandlerResult,
    StageHandler,
    global_stage_registry,
)
from schemas.models.artifact import ProducerInfo
from schemas.models.common import ProducerKind
from schemas.models.production import ProductionState


class DummyHandler:
    def run(self, stage_name, state, inputs, **kwargs):
        return StageHandlerResult(
            status=StageResultStatus.READY,
            data={"dummy": "ok"},
            producer=ProducerInfo(kind=ProducerKind.SYSTEM),
        )


def test_default_registry_has_no_production_handlers():
    """Verify Phase 2 rule: default registry has NO fake production handlers."""
    assert len(global_stage_registry.list_registered()) == 0
    assert not global_stage_registry.has("research")
    assert not global_stage_registry.has("proposal")
    assert not global_stage_registry.has("script")
    assert global_stage_registry.get("research") is None


def test_custom_stage_registry_register_and_get():
    reg = StageRegistry()
    handler = DummyHandler()
    assert not reg.has("custom_stage")

    reg.register("custom_stage", handler)
    assert reg.has("custom_stage")
    assert reg.get("custom_stage") is handler
    assert reg.list_registered() == ["custom_stage"]

    reg.unregister("custom_stage")
    assert not reg.has("custom_stage")
    assert reg.get("custom_stage") is None


def test_custom_stage_registry_clear():
    reg = StageRegistry()
    reg.register("s1", DummyHandler())
    reg.register("s2", DummyHandler())
    assert len(reg.list_registered()) == 2

    reg.clear()
    assert len(reg.list_registered()) == 0
