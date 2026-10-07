"""Metrics and editorial warnings for a finished semantic edit plan."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


class RhythmAnalyzer:
    def analyze(self, events: list[dict[str, Any]], total_duration: float) -> dict[str, Any]:
        primary = sorted(
            (e for e in events if e.get("role") == "primary_visual"),
            key=lambda e: float(e["start"]),
        )
        durations = [float(e["duration"]) for e in primary]
        starts = [float(e["start"]) for e in primary]
        cut_intervals = [round(b - a, 3) for a, b in zip(starts, starts[1:])]
        transitions = [e.get("transition_in") for e in primary[1:] if e.get("transition_in")]
        changes: dict[str, int] = defaultdict(int)
        for event in primary:
            changes[event.get("scene_id")] += 1
        high_energy = [e for e in primary if e.get("scene_id", "").endswith("01") or e.get("motion_intent") in {"pulse", "travel", "transform"}]
        transition_counts = dict(Counter(transitions))
        return {
            "shot_count": len(primary),
            "average_shot_duration": round(sum(durations) / len(durations), 3) if durations else 0,
            "average_cut_interval": round(sum(cut_intervals) / len(cut_intervals), 3) if cut_intervals else 0,
            "cut_intervals": cut_intervals,
            "visual_changes_per_scene": dict(changes),
            "longest_static_interval": round(max(durations), 3) if durations else 0,
            "shortest_interval": round(min(durations), 3) if durations else 0,
            "high_energy_beat_density": round(len(high_energy) / total_duration, 3) if total_duration else 0,
            "transition_frequency": round(len(transitions) / total_duration, 3) if total_duration else 0,
            "visual_reset_frequency": round(len(primary) / total_duration, 3) if total_duration else 0,
            "transition_diversity": len(set(transitions)),
            "layer_diversity": len({e.get("role") for e in events}),
            "framing_diversity": len({e.get("crop") for e in primary if e.get("crop")}),
            "camera_intent_diversity": len({e.get("camera_intent") for e in primary if e.get("camera_intent")}),
            "motion_intent_diversity": len({e.get("motion_intent") for e in primary if e.get("motion_intent")}),
            "transition_counts": transition_counts,
        }

    def warnings(self, rhythm: dict[str, Any]) -> list[dict[str, str]]:
        findings = []
        if rhythm["shot_count"] > 2 and rhythm["transition_diversity"] <= 1:
            findings.append({"severity": "warning", "code": "TRANSITION_REPETITION", "evidence": "All cuts use one transition type.", "correction": "Introduce a continuity-appropriate transition change."})
        dominant = max(rhythm["transition_counts"].values(), default=0)
        if rhythm["shot_count"] > 3 and dominant / rhythm["shot_count"] >= 0.75:
            findings.append({"severity": "warning", "code": "TRANSITION_DOMINANCE", "evidence": f"One transition covers {dominant} of {rhythm['shot_count']} primary shots.", "correction": "Vary a later cut only where the narrative relationship supports it."})
        if rhythm["longest_static_interval"] > 6:
            findings.append({"severity": "warning", "code": "LONG_STATIC_INTERVAL", "evidence": f"Longest primary shot is {rhythm['longest_static_interval']}s.", "correction": "Add a meaningful visual change or preserve it as an intentional reveal."})
        return findings
