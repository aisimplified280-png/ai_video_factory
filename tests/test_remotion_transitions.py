"""Transition tests: canonical intents resolve, nothing is inserted secretly."""
from pathlib import Path

COMPOSER = Path(__file__).resolve().parent.parent / "remotion-composer" / "src"

MODULE_FOR_INTENT = {
    "hard_cut": "hardCut",
    "fade": "fade",
    "cross_dissolve": "fade",
    "directional_wipe": "wipe",
    "object_transition": "objectTransition",
    "zoom_transition": "zoom",
    "shape_morph": "shapeMorph",
    "light_flash": "lightFlash",
    "motion_blur": "motionBlur",
    "match_cut": "matchCut",
    "slide_transition": "slide",
}


def test_all_canonical_transitions_resolve():
    scene_source = (COMPOSER / "compositions" / "SceneComposition.tsx").read_text(encoding="utf-8")
    for intent, module in MODULE_FOR_INTENT.items():
        assert f"'{intent}'" in scene_source, intent
        assert module in scene_source, module


def test_transition_modules_expose_overlap_contract():
    transformative_modules = {"fade", "wipe", "zoom", "lightFlash", "motionBlur", "objectTransition", "shapeMorph", "matchCut", "slide"}
    instant = {"hardCut"}
    for module in transformative_modules:
        text = (COMPOSER / "transitions" / f"{module}.ts").read_text(encoding="utf-8")
        assert "export function overlapFrames" in text, module
        assert "return 0" not in text, f"Transformative transition {module} must not execute as a hard cut"
    for module in instant:
        text = (COMPOSER / "transitions" / f"{module}.ts").read_text(encoding="utf-8")
        assert "return 0" in text, module


def test_transition_modules_have_entrance_and_exit_styles():
    """Verify each transformative transition exports entrance and exit behaviors."""
    bidi_modules = {"motionBlur", "zoom", "objectTransition", "shapeMorph", "matchCut"}
    for module in bidi_modules:
        text = (COMPOSER / "transitions" / f"{module}.ts").read_text(encoding="utf-8")
        assert "incomingStyle" in text, f"{module} must define incomingStyle entrance behavior"
        assert "outgoingStyle" in text, f"{module} must define outgoingStyle exit behavior"


def test_no_secret_transition_insertion():
    production = (COMPOSER / "compositions" / "ProductionComposition.tsx").read_text(encoding="utf-8")
    assert "transition_in" in production
    # Entrance styles always derive from the event's own transition_in.
    assert production.count("transition_in") >= 3
