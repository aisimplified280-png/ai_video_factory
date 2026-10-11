"""Validator tests: Python-side props checks plus TS parity for every intent."""
from pathlib import Path

import pytest

from composition.remotion.props_builder import PropsError, build_production_props
from test_remotion_props import PROFILE, _artifacts, _write_asset

COMPOSER = Path(__file__).resolve().parent.parent / "remotion-composer" / "src"

CAMERA_INTENTS = {"reveal_space", "approach_subject", "expand_scale", "follow_subject",
                  "shift_focus", "observe_static", "cross_system"}
MOTION_INTENTS = {"emerge", "assemble", "connect", "expand", "collapse", "trace", "flow",
                  "pulse", "transform", "travel", "reveal", "compare", "count", "focus", "reorder"}
TRANSITION_INTENTS = {"hard_cut", "cross_dissolve", "motion_blur", "match_cut", "directional_wipe",
                      "zoom_transition", "object_transition", "shape_morph", "light_flash", "fade"}


def _resolver_source() -> str:
    return (COMPOSER / "runtime" / "styleResolvers.ts").read_text(encoding="utf-8")


def test_every_camera_intent_has_an_implementation():
    # Bindings live in the tested resolvers module that SceneComposition
    # renders through (extracted from the composition, not removed).
    scene_source = (COMPOSER / "compositions" / "SceneComposition.tsx").read_text(encoding="utf-8")
    assert "from '../runtime/styleResolvers'" in scene_source
    resolvers = _resolver_source()
    for intent in CAMERA_INTENTS:
        assert f"'{intent}'" in resolvers, intent
    for module in ("static", "pushIn", "pullOut", "pan", "tracking", "parallax", "zoom", "focusShift"):
        assert (COMPOSER / "camera" / f"{module}.ts").is_file()


def test_every_motion_intent_has_an_implementation():
    resolvers = _resolver_source()
    for intent in MOTION_INTENTS:
        assert f"'{intent}'" in resolvers, intent
    for module in ("appear", "reveal", "grow", "move", "connect", "pulse", "transform",
                   "trace", "count", "compare", "focus"):
        path = COMPOSER / "motion" / f"{module}.ts"
        assert path.is_file()
        assert "export function" in path.read_text(encoding="utf-8")


def test_every_transition_intent_resolves_to_a_module():
    resolvers = _resolver_source()
    for intent in TRANSITION_INTENTS:
        assert f"'{intent}'" in resolvers, intent
    for module in ("hardCut", "fade", "wipe", "zoom", "lightFlash", "motionBlur", "matchCut"):
        assert (COMPOSER / "transitions" / f"{module}.ts").is_file()


def test_no_card_templates_in_composer():
    banned = ("HeroCard", "StatCard", "InfoCard", "AIExplainerCard")
    for path in COMPOSER.rglob("*.tsx"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{path.name} contains {token}"


def test_metric_layer_wraps_instead_of_overflowing():
    text = (COMPOSER / "primitives" / "MetricLayer.tsx").read_text(encoding="utf-8")
    assert "overflowWrap" in text
    assert "maxWidth" in text


def test_diagram_labels_wrap_inside_node_boxes():
    text = (COMPOSER / "primitives" / "DiagramLayer.tsx").read_text(encoding="utf-8")
    assert "wrapLabel" in text
    assert ".slice(0, 28)" not in text


def test_scene_type_never_selects_a_template():
    for name in ("SceneComposition.tsx", "ProductionComposition.tsx"):
        text = (COMPOSER / "compositions" / name).read_text(encoding="utf-8")
        assert "scene.type" not in text, name


def test_props_reject_zero_duration_event(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    edit["timeline"][0]["duration"] = 0
    with pytest.raises(PropsError):
        build_production_props(
            edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
            art_direction_data=art, script_data=script, platform_profile=PROFILE,
            projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
