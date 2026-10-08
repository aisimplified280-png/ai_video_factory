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
    "match_cut",
]


def assign_transformative_transitions(scene_count: int, as_boundaries: bool = False) -> list[str]:
    """Assigns purposeful, transformative transition intents for each scene boundary.
    
    If as_boundaries is True, returns (scene_count - 1) transitions representing the
    exact boundaries between scenes, resolving boundary-count ambiguity (Issue #8).
    """
    patterns = [
        "zoom_transition",
        "directional_wipe",
        "object_transition",
        "shape_morph",
        "motion_blur",
    ]
    target_count = max(0, scene_count - 1) if as_boundaries else scene_count
    return [patterns[i % len(patterns)] for i in range(target_count)]


def assign_boundary_transitions(scene_count: int) -> list[str]:
    """Returns exactly (scene_count - 1) transitions between adjacent scenes."""
    return assign_transformative_transitions(scene_count, as_boundaries=True)


def validate_transition_integrity(transitions: list[str]) -> tuple[bool, list[str]]:
    """Validates that no forbidden transitions exist and all are transformative."""
    errors = []
    for idx, tr in enumerate(transitions):
        if tr.lower() in FORBIDDEN_TRANSITIONS:
            errors.append(f"Scene {idx+1} transition '{tr}' is forbidden (static cuts and fades are banned).")
        elif tr not in ALLOWED_TRANSITIONS:
            errors.append(f"Scene {idx+1} transition '{tr}' is not in approved transformative transitions.")
    return len(errors) == 0, errors
