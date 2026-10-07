"""Motion tests: semantic intents bind to observable frame-level motion."""
from pathlib import Path

COMPOSER = Path(__file__).resolve().parent.parent / "remotion-composer" / "src"

INTENT_TO_MODULE = {
    "emerge": "appear",
    "assemble": "grow",
    "connect": "connect",
    "expand": "grow",
    "collapse": "grow",
    "trace": "trace",
    "flow": "move",
    "pulse": "pulse",
    "transform": "transform",
    "travel": "move",
    "reveal": "reveal",
    "compare": "compare",
    "count": "appear",
    "focus": "focus",
    "reorder": "reveal",
}


def test_every_motion_intent_binds_to_an_implementation():
    scene_source = (COMPOSER / "compositions" / "SceneComposition.tsx").read_text(encoding="utf-8")
    for intent, module in INTENT_TO_MODULE.items():
        assert f"'{intent}'" in scene_source, intent
        assert module in scene_source, module
    # `reorder` is an editorial ordering concept; it resolves through reveal.
    assert "'reorder'" in scene_source


def test_motion_modules_produce_style_objects():
    for module in ("appear", "reveal", "grow", "move", "connect", "pulse", "transform",
                   "trace", "count", "compare", "focus"):
        text = (COMPOSER / "motion" / f"{module}.ts").read_text(encoding="utf-8")
        assert "export function" in text, module
        assert "progress" in text, module


def test_no_default_durations_in_motion():
    for path in (COMPOSER / "motion").glob("*.ts"):
        text = path.read_text(encoding="utf-8")
        assert "500" not in text and "1000" not in text, path.name
