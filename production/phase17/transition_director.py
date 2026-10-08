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

from dataclasses import dataclass
from typing import Any

FORBIDDEN_TRANSITIONS = {"fade", "cross_dissolve", "hard_cut", "cut", "none"}

ALLOWED_TRANSITIONS = [
    "zoom_transition",
    "directional_wipe",
    "object_transition",
    "motion_blur",
    "shape_morph",
    "match_cut",
]

TRANSITION_CYCLE = [
    "zoom_transition",
    "directional_wipe",
    "object_transition",
    "shape_morph",
    "motion_blur",
    "match_cut",
]


@dataclass
class SceneBoundaryTransition:
    from_scene_id: str
    to_scene_id: str
    transition_intent: str
    boundary_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_scene_id": self.from_scene_id,
            "to_scene_id": self.to_scene_id,
            "transition_intent": self.transition_intent,
            "boundary_index": self.boundary_index,
        }


def assign_boundary_transitions(
    scenes: int | list[dict[str, Any]] | list[str],
) -> list[SceneBoundaryTransition]:
    """Define ONE authoritative contract for scene-boundary transitions.
    
    Rule: N scenes = exactly (N - 1) transitions between adjacent scenes.
    Every transition object explicitly identifies:
    - from_scene_id
    - to_scene_id
    - transition_intent
    - boundary_index
    
    No phantom final transition.
    """
    if isinstance(scenes, int):
        scene_ids = [f"scene_{i+1:02d}" for i in range(max(0, scenes))]
    elif isinstance(scenes, list):
        scene_ids = []
        for idx, item in enumerate(scenes):
            if isinstance(item, dict):
                sc_id = item.get("scene_id") or item.get("id") or f"scene_{idx+1:02d}"
                scene_ids.append(str(sc_id))
            else:
                scene_ids.append(str(item))
    else:
        scene_ids = []

    if len(scene_ids) <= 1:
        return []

    boundary_count = len(scene_ids) - 1
    transitions: list[SceneBoundaryTransition] = []
    for i in range(boundary_count):
        intent = TRANSITION_CYCLE[i % len(TRANSITION_CYCLE)]
        transitions.append(
            SceneBoundaryTransition(
                from_scene_id=scene_ids[i],
                to_scene_id=scene_ids[i + 1],
                transition_intent=intent,
                boundary_index=i,
            )
        )
    return transitions


def assign_transformative_transitions(
    scenes: int | list[dict[str, Any]] | list[str],
) -> list[str]:
    """Returns exactly (N - 1) transformative transition intent strings for N scenes.
    
    Unifies the API so there is no ambiguity:
    1 scene  -> 0 transitions
    2 scenes -> 1 transition
    5 scenes -> 4 transitions
    6 scenes -> 5 transitions
    """
    boundaries = assign_boundary_transitions(scenes)
    return [b.transition_intent for b in boundaries]


def validate_transition_integrity(
    transitions: list[str] | list[SceneBoundaryTransition],
) -> tuple[bool, list[str]]:
    """Validates that no forbidden transitions exist and all are transformative."""
    errors = []
    for idx, tr_item in enumerate(transitions):
        tr = tr_item.transition_intent if isinstance(tr_item, SceneBoundaryTransition) else str(tr_item)
        if tr.lower() in FORBIDDEN_TRANSITIONS:
            errors.append(f"Boundary {idx+1} transition '{tr}' is forbidden (static cuts and fades are banned).")
        elif tr not in ALLOWED_TRANSITIONS:
            errors.append(f"Boundary {idx+1} transition '{tr}' is not in approved transformative transitions.")
    return len(errors) == 0, errors

