"""Deterministic semantic transition selection, independent of a renderer."""
from __future__ import annotations

from .timeline import TransitionType

VALID_TRANSITIONS = set(TransitionType.__args__)
_STOPWORDS = frozenset({
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of",
    "on", "or", "the", "to", "with",
})


def _meaningful_tokens(value: object) -> set[str]:
    words = str(value or "").lower().replace("-", " ").replace("/", " ").split()
    return {word.strip(".,;:!?()[]\"'") for word in words} - _STOPWORDS - {""}


class TransitionPlanner:
    def plan(self, previous: dict | None, current: dict, index: int, previous_transition: str | None = None) -> TransitionType:
        if previous is None:
            return "fade"
        previous_subject = _meaningful_tokens(previous.get("subject"))
        subject = _meaningful_tokens(current.get("subject"))
        if previous_subject & subject:
            candidates = ("match_cut", "cross_dissolve", "hard_cut")
        elif current.get("narrative_role") == "cta":
            candidates = ("fade",)
        elif current.get("narrative_role") in {"hook", "reveal"} or previous.get("narrative_role") == "hook":
            candidates = ("light_flash", "cross_dissolve", "hard_cut")
        elif current.get("motion_intent") in {"travel", "flow", "connect"}:
            candidates = ("directional_wipe", "motion_blur", "hard_cut")
        else:
            ordered = ("hard_cut", "cross_dissolve", "zoom_transition", "motion_blur")
            candidates = (ordered[index % len(ordered)],) + tuple(t for t in ordered if t != ordered[index % len(ordered)])
        for candidate in candidates:
            if candidate != previous_transition:
                return candidate
        return candidates[0]

    def plan_sequence(self, scenes: list[dict]) -> dict[str, TransitionType]:
        """Plan every scene boundary while avoiding an immediate transition repeat."""
        plan: dict[str, TransitionType] = {}
        previous_transition: str | None = None
        for index, scene in enumerate(scenes):
            scene_id = scene.get("scene_id") or scene.get("id")
            transition = self.plan(scenes[index - 1] if index else None, scene, index, previous_transition)
            plan[scene_id] = transition
            previous_transition = transition
        return plan

    @staticmethod
    def validate(value: str | None) -> bool:
        return value is None or value in VALID_TRANSITIONS
