"""Camera tests: semantic intents bind to real behaviors deterministically."""
from pathlib import Path

COMPOSER = Path(__file__).resolve().parent.parent / "remotion-composer" / "src"

INTENT_TO_MODULE = {
    "reveal_space": "pushIn",
    "approach_subject": "pushIn",
    "expand_scale": "zoom",
    "follow_subject": "tracking",
    "shift_focus": "focusShift",
    "observe_static": "static",
    "cross_system": "pan",
}


def test_every_camera_intent_binds_to_a_behavior():
    scene_source = (COMPOSER / "compositions" / "SceneComposition.tsx").read_text(encoding="utf-8")
    for intent, module in INTENT_TO_MODULE.items():
        assert f"'{intent}'" in scene_source, intent
        assert module in scene_source, module


def test_camera_modules_are_pure_frame_functions():
    for module in ("static", "pushIn", "pullOut", "pan", "tracking", "parallax", "zoom", "focusShift"):
        text = (COMPOSER / "camera" / f"{module}.ts").read_text(encoding="utf-8")
        assert "export function" in text, module
        assert "useCurrentFrame" not in text and "useState" not in text, module


def test_parallax_supports_depth_layers():
    text = (COMPOSER / "camera" / "parallax.ts").read_text(encoding="utf-8")
    assert "background" in text and "foreground" in text
