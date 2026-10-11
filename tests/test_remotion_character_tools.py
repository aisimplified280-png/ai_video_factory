"""Mascot tool independence (P1 targeting bug).

The held tool must render independently of the arm pose: a target anchor
selects the pointing arm but must never hide the scene-specific tool
(inspect-with-scanner points AND shows the scanner). CharacterLayer uses
Remotion hooks so it cannot render in node; these tests pin the structure
that guarantees it — one helper, called in both arm branches — at the same
level as the existing CharacterLayer wiring tests.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAR = ROOT / "remotion-composer" / "src" / "primitives" / "CharacterLayer.tsx"

TOOLS = (
    "vector_token",
    "quantum_stylus",
    "optical_scanner",
    "telemetry_hud_panel",
    "briefing_tablet",
)

# Exact pre-existing resting-hand anchors — the refactor must not move tools.
RESTING_ANCHORS = {
    "vector_token": "[186, 140]",
    "quantum_stylus": "[184, 130]",
    "optical_scanner": "[180, 132]",
    "telemetry_hud_panel": "[178, 125]",
    "briefing_tablet": "[182, 135]",
}


def test_tool_renders_through_one_helper_called_in_both_branches():
    text = CHAR.read_text(encoding="utf-8")
    assert text.count("const renderHeldTool") == 1, "single tool helper"
    # Each tool id is drawn in exactly one place: inside the helper
    # (condition + resting-anchor map entry).
    for tool in TOOLS:
        assert text.count(tool) == 2, tool
    # Both arm branches render the helper: pointing keeps its tool.
    assert text.count("{renderHeldTool(") == 2, "pointing + resting branches"
    # The pointing arm is still target-selected (behavior unchanged).
    assert "spec.target_anchor || spec.pose?.includes('point')" in text


def test_resting_tool_anchors_unchanged():
    text = CHAR.read_text(encoding="utf-8")
    for tool, coords in RESTING_ANCHORS.items():
        assert f"{tool}: {coords}" in text, f"{tool} anchor moved"
