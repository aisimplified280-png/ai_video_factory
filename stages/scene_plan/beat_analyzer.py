"""Beat analyzer and shot rhythm planner.

Deconstructs scene durations into rhythmic shot beats with chronological
continuity, camera transitions, and strict gap/overlap prevention.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ShotBeat(BaseModel):
    """Semantic shot beat within a scene."""
    shot_id: str
    start: float = Field(ge=0.0)  # Relative offset within scene in seconds
    end: float = Field(ge=0.0)    # Relative offset within scene in seconds
    purpose: str
    focus_subject: str
    visual_change: str
    camera_intent: str
    motion_intent: str
    transition: str = "cut"

    model_config = {"extra": "forbid"}


def generate_scene_shots(
    scene_id: str,
    duration: float,
    subject: str,
    visual_purpose: str,
    camera_intent: str = "approach_subject",
    motion_intent: str = "assemble",
    visual_technique: str = "diagram_reveal",
) -> list[dict[str, Any]]:
    """Generate shot beats that cover the entire scene duration with zero gaps or overlaps.

    Rules:
    - Duration <= 2.5s: 1 beat (punchy)
    - 2.5s < Duration <= 5.5s: 2 beats (setup -> reveal/shift)
    - Duration > 5.5s: 3 beats (establish -> develop -> climax/detail)
    """
    duration = max(1.0, round(duration, 2))
    shots: list[dict[str, Any]] = []

    if duration <= 2.5:
        # Single shot beat
        shots.append({
            "shot_id": f"{scene_id}_shot_01",
            "start": 0.0,
            "end": duration,
            "purpose": visual_purpose or "Direct focal impact",
            "focus_subject": subject,
            "visual_change": f"Immediate visual presentation of {subject}",
            "camera_intent": camera_intent,
            "motion_intent": motion_intent,
            "transition": "cut",
        })
    elif duration <= 5.5:
        # Two shot beats: setup -> focal shift
        split_time = round(duration * 0.5, 2)
        shots.append({
            "shot_id": f"{scene_id}_shot_01",
            "start": 0.0,
            "end": split_time,
            "purpose": "Establish primary subject",
            "focus_subject": subject,
            "visual_change": f"Initial emergence of {subject}",
            "camera_intent": camera_intent,
            "motion_intent": motion_intent,
            "transition": "cut",
        })
        shots.append({
            "shot_id": f"{scene_id}_shot_02",
            "start": split_time,
            "end": duration,
            "purpose": visual_purpose or "Drive narrative understanding",
            "focus_subject": f"{subject} action",
            "visual_change": f"Transformation and dynamic action of {subject}",
            "camera_intent": "shift_focus" if camera_intent != "shift_focus" else "reveal_space",
            "motion_intent": "transform" if motion_intent != "transform" else "expand",
            "transition": "cut",
        })
    else:
        # Three shot beats: establish -> detail -> consequence
        t1 = round(duration * 0.35, 2)
        t2 = round(duration * 0.70, 2)
        shots.append({
            "shot_id": f"{scene_id}_shot_01",
            "start": 0.0,
            "end": t1,
            "purpose": "Establish environmental scale and subject",
            "focus_subject": subject,
            "visual_change": f"Initial spatial framing of {subject}",
            "camera_intent": "reveal_space",
            "motion_intent": "emerge",
            "transition": "cut",
        })
        shots.append({
            "shot_id": f"{scene_id}_shot_02",
            "start": t1,
            "end": t2,
            "purpose": "Inspect structural mechanism",
            "focus_subject": f"{subject} interior mechanism",
            "visual_change": f"Assembly and active processing of {subject}",
            "camera_intent": camera_intent,
            "motion_intent": motion_intent,
            "transition": "cut",
        })
        shots.append({
            "shot_id": f"{scene_id}_shot_03",
            "start": t2,
            "end": duration,
            "purpose": visual_purpose or "Resolve consequence and transition anchor",
            "focus_subject": f"{subject} outcome",
            "visual_change": f"Resolution and state transformation of {subject}",
            "camera_intent": "expand_scale",
            "motion_intent": "flow",
            "transition": "cut",
        })

    return shots


def validate_shots_coverage(shots: list[dict[str, Any]], expected_duration: float) -> list[str]:
    """Validate that shots start at 0, end at expected duration, and have no gaps or overlaps."""
    errors: list[str] = []
    if not shots:
        return ["Scene contains no shot beats."]

    first_start = shots[0].get("start", -1.0)
    if abs(first_start - 0.0) > 0.05:
        errors.append(f"First shot start time must be 0.0s, got {first_start}s.")

    last_end = shots[-1].get("end", -1.0)
    if abs(last_end - expected_duration) > 0.1:
        errors.append(
            f"Last shot end time {last_end}s does not match scene duration {expected_duration}s."
        )

    for i in range(len(shots) - 1):
        cur_end = shots[i].get("end", 0.0)
        nxt_start = shots[i + 1].get("start", 0.0)
        if abs(cur_end - nxt_start) > 0.05:
            if nxt_start < cur_end:
                errors.append(f"Shot beat overlap between shot {i} (end={cur_end}s) and shot {i+1} (start={nxt_start}s).")
            else:
                errors.append(f"Shot beat timing gap between shot {i} (end={cur_end}s) and shot {i+1} (start={nxt_start}s).")

    return errors
