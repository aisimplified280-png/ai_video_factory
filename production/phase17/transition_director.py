"""Phase 17 Transition Director.

Requirement 2 was revised: explanatory videos need SIMPLE, continuity-based
transitions — not a cycle of flashy effects.

Design rules (see the visual-priority reset):
- A cut or a gentle dissolve is the correct default. It never competes with the
  explanation for attention.
- Transitions are chosen for continuity of place/subject, never to rotate through
  an effects array for "variety".
- Fancy transitions (wipe, morph, object handoff) are opt-in: only when the scene
  metadata explicitly asks for them.
- Anything the renderer cannot resolve is forbidden.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Default boundary treatment: a gentle cross-dissolve. Explanatory videos ask for
# smooth continuity between scenes — a hard cut to an empty frame reads as a glitch.
DEFAULT_TRANSITION = "cross_dissolve"

# Simple continuity-based transitions. These are correct, not "lazy".
# slide_transition: sliding-physics push used when both sides of the boundary
# are the same workspace (the reference video's state-machine feel).
CONTINUITY_TRANSITIONS = ["hard_cut", "cross_dissolve", "fade", "match_cut", "slide_transition"]

# Everything the renderer can resolve. Opt-in only.
OPTIONAL_TRANSITIONS = [
    "directional_wipe",
    "object_transition",
    "motion_blur",
    "shape_morph",
    "zoom_transition",
    "light_flash",
]

ALLOWED_TRANSITIONS = [DEFAULT_TRANSITION, *CONTINUITY_TRANSITIONS, *OPTIONAL_TRANSITIONS]

# Only intents the renderer cannot resolve are rejected.
FORBIDDEN_TRANSITIONS = {"", "none", "null", "none/intentional"}


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


def _intent_for_scene(scene: dict[str, Any] | None) -> str:
    """Continuity-first intent: explicit request wins, otherwise a simple cut.

    §16: never cycle a transition array for visual variety.
    """
    if not scene:
        return DEFAULT_TRANSITION
    explicit = scene.get("transition_intent") or scene.get("transition_in")
    if isinstance(explicit, str) and explicit and explicit.lower() in {t.lower() for t in ALLOWED_TRANSITIONS}:
        return explicit.lower()
    return DEFAULT_TRANSITION


def continuity_boundary_intent(outgoing_environment: Any, incoming_environment: Any) -> str:
    """Boundary intent from place continuity: slide-push vs gentle dissolve.

    Same environment on both sides = one continuous workspace, so content
    slides into place (state-machine feel). A changed place — including the
    drop into the branded CTA studio — gets the gentle cross-dissolve so the
    move never implies spatial continuity that isn't there.
    """

    def key(value: Any) -> str:
        return " ".join(str(value or "").lower().split())

    out_key = key(outgoing_environment)
    in_key = key(incoming_environment)
    if out_key and in_key and out_key == in_key:
        return "slide_transition"
    return DEFAULT_TRANSITION


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

    No phantom final transition. Intent defaults to a simple cut unless the scene
    metadata explicitly requests an alternative.
    """
    if isinstance(scenes, int):
        scene_ids = [f"scene_{i+1:02d}" for i in range(max(0, scenes))]
        scene_dicts: list[dict[str, Any] | None] = [None] * len(scene_ids)
    elif isinstance(scenes, list):
        scene_ids = []
        scene_dicts = []
        for idx, item in enumerate(scenes):
            if isinstance(item, dict):
                sc_id = item.get("scene_id") or item.get("id") or f"scene_{idx+1:02d}"
                scene_ids.append(str(sc_id))
                scene_dicts.append(item)
            else:
                scene_ids.append(str(item))
                scene_dicts.append(None)
    else:
        scene_ids = []
        scene_dicts = []

    if len(scene_ids) <= 1:
        return []

    boundary_count = len(scene_ids) - 1
    transitions: list[SceneBoundaryTransition] = []
    for i in range(boundary_count):
        # Continuity is read from the incoming scene: how we arrive, not how we leave.
        intent = _intent_for_scene(scene_dicts[i + 1] if i + 1 < len(scene_dicts) else None)
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
    """Returns exactly (N - 1) transition intent strings for N scenes.

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
    """Validates that every intent resolves to a renderer module.

    Simple cuts and dissolves are explicitly valid: an explanatory scene must never
    be penalised for using the quietest possible transition.
    """
    errors = []
    known = {t.lower() for t in ALLOWED_TRANSITIONS}
    for idx, tr_item in enumerate(transitions):
        tr = tr_item.transition_intent if isinstance(tr_item, SceneBoundaryTransition) else str(tr_item)
        if tr.lower() in FORBIDDEN_TRANSITIONS:
            errors.append(f"Boundary {idx+1} transition '{tr}' is missing or unresolvable.")
        elif tr.lower() not in known:
            errors.append(f"Boundary {idx+1} transition '{tr}' is not supported by the renderer.")
    return len(errors) == 0, errors
