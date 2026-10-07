"""Phase 17 Transition Director.

Enforces Requirement 2: Every scene transition must transform.
Strictly forbids:
- fade
- crossfade / cross_dissolve
- hard_cut / cut

Requires transformative transitions:
- zoom_transition (camera push / zoom through)
- directional_wipe (tracking handoff / mask reveal)
- object_transition (object transformation)
- motion_blur (high-velocity camera whip / motion blur)
- shape_morph (scale & shape morph)
"""
from __future__ import annotations

FORBIDDEN_TRANSITIONS = {"fade", "cross_dissolve", "hard_cut", "cut", "none"}

ALLOWED_TRANSITIONS = [
    "zoom_transition",
    "directional_wipe",
    "object_transition",
    "motion_blur",
    "shape_morph",
]


def assign_transformative_transitions(scene_count: int) -> list[str]:
    """Assigns purposeful, transformative transition intents for each scene boundary."""
    # Sequence of meaningful transformations:
    # Scene 1: Zoom in (extreme camera push into macro embodiment)
    # Scene 2: Zoom through (push through gripper into articulated arm wrist)
    # Scene 3: Directional wipe / tracking handoff (tracking camera follows arm onto mobile chassis)
    # Scene 4: Zoom through (accelerates past barrier into expansive logistics floor)
    # Scene 5: Motion blur / object transition (raceway rovers converge into brand monogram)
    patterns = [
        "zoom_transition",
        "zoom_transition",
        "directional_wipe",
        "zoom_transition",
        "motion_blur",
    ]
    return [patterns[i % len(patterns)] for i in range(scene_count)]


def validate_transition_integrity(transitions: list[str]) -> tuple[bool, list[str]]:
    """Validates that no forbidden transitions exist and all are transformative."""
    errors = []
    for idx, tr in enumerate(transitions):
        if tr.lower() in FORBIDDEN_TRANSITIONS:
            errors.append(f"Scene {idx+1} transition '{tr}' is forbidden (static cuts and fades are banned).")
        elif tr not in ALLOWED_TRANSITIONS:
            errors.append(f"Scene {idx+1} transition '{tr}' is not in approved transformative transitions.")
    return len(errors) == 0, errors
