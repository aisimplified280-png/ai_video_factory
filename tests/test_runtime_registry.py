"""Tests for the composition runtime registry (routing metadata only)."""
import pytest

from composition.runtime_registry import RuntimeRecord, RuntimeRegistry, UnknownRuntimeError, create_default_registry
from composition.runtime_capabilities import declared_capabilities


def test_default_registry_contains_exactly_three_runtimes():
    registry = create_default_registry()
    assert registry.list_registered() == ["ffmpeg_pil", "hyperframes", "remotion"]


def test_unknown_runtime_rejected():
    registry = create_default_registry()
    assert not registry.has("after_effects")
    with pytest.raises(UnknownRuntimeError):
        registry.get("after_effects")


def test_legacy_runtime_is_local_only_and_never_a_fallback():
    record = create_default_registry().get("ffmpeg_pil")
    assert record.supports_local is True
    assert record.supports_remote is False
    assert "react" not in record.capabilities


def test_hyperframes_is_remote_only():
    record = create_default_registry().get("hyperframes")
    assert record.supports_local is False
    assert record.supports_remote is True


def test_isolated_registry_register_and_unregister():
    registry = RuntimeRegistry()
    registry.register(RuntimeRecord(runtime_id="fake", capabilities=declared_capabilities("ffmpeg_pil")))
    assert registry.has("fake")
    registry.unregister("fake")
    assert not registry.has("fake")
    # Production default is untouched by isolated registries.
    assert not create_default_registry().has("fake")


def test_capability_sets_are_nonempty_and_typed():
    for runtime_id in create_default_registry().list_registered():
        capabilities = declared_capabilities(runtime_id)
        assert capabilities
        assert all(isinstance(capability, str) for capability in capabilities)
    assert declared_capabilities("no_such_runtime") == frozenset()
