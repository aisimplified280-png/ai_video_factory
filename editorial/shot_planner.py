from __future__ import annotations


def choose_layout_family(intents: list[str], role: str = "process") -> str:
    intents = [i.lower() for i in (intents or [])]
    if "comparison" in intents or "before_after" in intents:
        return "split_screen"
    if "network" in intents or "connection" in intents:
        return "network"
    if "timeline" in intents or "list" in intents:
        return "timeline"
    if "statistics" in intents or "ranking" in intents:
        return "detail_zoom"
    if "architecture" in intents or "system" in intents:
        return "diagram"
    if "process" in intents or "workflow" in intents:
        return "horizontal_process" if role in {"process", "proof"} else "vertical_process"
    if "alert" in intents:
        return "detail_zoom"
    if "announcement" in intents:
        return "centered_hero"
    return "editorial"


def plan_shot_sequence(text: str, intents: list[str], role: str = "process") -> list[dict]:
    narrative = (text or "").strip()
    if not narrative:
        return [{"start": 0.0, "end": 1.0, "focus": "hero reveal"}]

    density = len(intents)
    if density <= 2:
        shots = [{"start": 0.0, "end": 1.0, "focus": "hero reveal", "visual_story": "single concept introduced clearly"}]
    elif density <= 4:
        shots = [
            {"start": 0.0, "end": 0.4, "focus": "hook", "visual_story": "open on the key object or system"},
            {"start": 0.4, "end": 1.0, "focus": "detail", "visual_story": "show the mechanism or relationship"},
        ]
    else:
        shots = [
            {"start": 0.0, "end": 0.32, "focus": "hook", "visual_story": "set the semantic frame"},
            {"start": 0.32, "end": 0.6, "focus": "mechanism", "visual_story": "show the key transformation"},
            {"start": 0.6, "end": 1.0, "focus": "proof", "visual_story": "resolve the story with a clear outcome"},
        ]

    if role == "cta":
        shots = [{"start": 0.0, "end": 1.0, "focus": "cta", "visual_story": "brand lockup and call to action"}]
    return shots
