"""Voice performance metadata and direction generator.

Defines pace, energy, pause intensity, and tone for spoken narration
sections to guide downstream TTS audio rendering.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class VoicePerformance(BaseModel):
    """Structured voice performance directive for a script section."""
    pace: str = Field(default="fast_clear")  # "fast_clear", "measured", "urgent", "deliberate", "steady"
    energy: int = Field(default=7, ge=1, le=10)
    pause_intensity: int = Field(default=4, ge=1, le=10)
    tone: str = Field(default="confident_explanatory")

    model_config = {"extra": "ignore"}


ROLE_PERFORMANCE_MAP: dict[str, dict[str, Any]] = {
    "hook": {
        "pace": "fast_clear",
        "energy": 8,
        "pause_intensity": 3,
        "tone": "curious_probing",
    },
    "context": {
        "pace": "fast_clear",
        "energy": 7,
        "pause_intensity": 4,
        "tone": "confident_explanatory",
    },
    "problem": {
        "pace": "measured",
        "energy": 7,
        "pause_intensity": 6,
        "tone": "intense_dramatic",
    },
    "tension": {
        "pace": "measured",
        "energy": 8,
        "pause_intensity": 6,
        "tone": "intense_dramatic",
    },
    "mechanism": {
        "pace": "fast_clear",
        "energy": 7,
        "pause_intensity": 4,
        "tone": "confident_explanatory",
    },
    "process": {
        "pace": "fast_clear",
        "energy": 7,
        "pause_intensity": 4,
        "tone": "confident_explanatory",
    },
    "evidence": {
        "pace": "measured",
        "energy": 7,
        "pause_intensity": 5,
        "tone": "thoughtful_revelatory",
    },
    "proof": {
        "pace": "measured",
        "energy": 7,
        "pause_intensity": 5,
        "tone": "thoughtful_revelatory",
    },
    "reveal": {
        "pace": "measured",
        "energy": 9,
        "pause_intensity": 5,
        "tone": "thoughtful_revelatory",
    },
    "payoff": {
        "pace": "measured",
        "energy": 8,
        "pause_intensity": 5,
        "tone": "confident_explanatory",
    },
    "implication": {
        "pace": "deliberate",
        "energy": 7,
        "pause_intensity": 6,
        "tone": "thoughtful_revelatory",
    },
    "cta": {
        "pace": "fast_clear",
        "energy": 8,
        "pause_intensity": 3,
        "tone": "welcoming_direct",
    },
    "transition": {
        "pace": "fast_clear",
        "energy": 6,
        "pause_intensity": 4,
        "tone": "confident_explanatory",
    },
}


def determine_voice_performance(
    narrative_role: str,
    override_dict: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Determine performance settings for a narrative beat."""
    base = ROLE_PERFORMANCE_MAP.get(narrative_role.lower(), {
        "pace": "fast_clear",
        "energy": 7,
        "pause_intensity": 4,
        "tone": "confident_explanatory",
    }).copy()

    if override_dict:
        if "pace" in override_dict:
            base["pace"] = str(override_dict["pace"])
        if "energy" in override_dict:
            try:
                base["energy"] = max(1, min(10, int(override_dict["energy"])))
            except (ValueError, TypeError):
                pass
        if "pause_intensity" in override_dict:
            try:
                base["pause_intensity"] = max(1, min(10, int(override_dict["pause_intensity"])))
            except (ValueError, TypeError):
                pass
        if "tone" in override_dict:
            base["tone"] = str(override_dict["tone"])

    return base


def format_speaker_direction(performance: dict[str, Any]) -> str:
    """Format voice performance into human/TTS direction string."""
    pace = performance.get("pace", "fast_clear")
    energy = performance.get("energy", 7)
    tone = performance.get("tone", "confident_explanatory")
    return f"{pace}, energy {energy}/10, {tone.replace('_', ' ')}"
