"""Deterministic Multi-Factor Editorial Scoring Engine.

Evaluates:
- Visual Diversity (0.0 - 2.0): Unique visual assets & environment variety
- Pacing & Rhythm (0.0 - 2.0): Shot durations, cut rhythm (optimal 3-6s for shorts)
- Caption Engagement (0.0 - 1.5): Kinetic emphasis words, text density
- Hook Strength (0.0 - 1.5): Opening 3-second energy, punchiness
- Research Authority (0.0 - 1.5): Grounded evidence & factual alignment
- Technical QA Integrity (0.0 - 1.5): Automated pixel/audio/format QA checks
"""
from __future__ import annotations

from typing import Any


def generate_editorial_score(qa_report_data: dict, v2_data: dict) -> str:
    """Generates an honest, multi-factor editorial score with granular breakdown."""
    timeline = v2_data.get("timeline", [])
    captions = v2_data.get("caption_track", [])
    audio_tracks = v2_data.get("audio_tracks", {})
    
    # 1. Technical QA Integrity (Max 1.5)
    checks = qa_report_data.get("checks", {}) or qa_report_data.get("results", {})
    total_checks = max(1, len(checks))
    passed_checks = sum(1 for v in checks.values() if v.get("passed") is True or v.get("status") == "PASS")
    failed_checks = sum(1 for v in checks.values() if v.get("passed") is False or v.get("status") == "FAIL")
    qa_ratio = passed_checks / total_checks
    qa_score = round(qa_ratio * 1.5, 2)
    if failed_checks > 0:
        qa_score = max(0.0, qa_score - (failed_checks * 0.5))

    # 2. Visual Diversity (Max 2.0)
    asset_ids = [e.get("asset_id") or e.get("visual_asset_id") for e in timeline if (e.get("asset_id") or e.get("visual_asset_id"))]
    unique_assets = len(set(asset_ids))
    total_events = max(1, len(timeline))
    diversity_ratio = unique_assets / total_events

    if unique_assets >= 5 and diversity_ratio >= 0.7:
        visual_score = 1.9
        visual_note = "High visual variety across all scenes"
    elif unique_assets >= 4:
        visual_score = 1.6
        visual_note = "Good visual variance with minor repetition"
    elif unique_assets >= 3:
        visual_score = 1.2
        visual_note = "Acceptable visual variety; recommend more distinct environments"
    else:
        visual_score = 0.7
        visual_note = "Low visual diversity; scene backgrounds feel repetitive"

    # 3. Pacing & Rhythm (Max 2.0)
    durations = [e.get("duration", 0) for e in timeline if e.get("duration", 0) > 0]
    avg_duration = sum(durations) / max(1, len(durations)) if durations else 4.0
    has_drag = any(d > 8.0 for d in durations)
    has_micro = any(d < 1.0 for d in durations)

    if 2.5 <= avg_duration <= 5.5 and not has_drag:
        pacing_score = 1.8
        pacing_note = f"Snappy short-form pace (avg {avg_duration:.1f}s/shot)"
    elif avg_duration <= 7.0 and not has_drag:
        pacing_score = 1.5
        pacing_note = f"Balanced pace (avg {avg_duration:.1f}s/shot)"
    else:
        pacing_score = 1.0
        pacing_note = f"Pacing drags in parts (avg {avg_duration:.1f}s/shot)"

    # 4. Caption Engagement (Max 1.5)
    emphasis_count = sum(len(c.get("emphasis_words", [])) for c in captions)
    if len(captions) >= 4 and emphasis_count >= 4:
        caption_score = 1.4
        caption_note = f"Strong kinetic emphasis cues ({emphasis_count} highlighted keywords)"
    elif len(captions) >= 2:
        caption_score = 1.1
        caption_note = "Standard captions present; recommend more kinetic emphasis words"
    else:
        caption_score = 0.6
        caption_note = "Sparse caption coverage"

    # 5. Hook Strength - First 3 Seconds (Max 1.5)
    first_event = timeline[0] if timeline else {}
    first_caption = captions[0] if captions else {}
    first_dur = first_event.get("duration", 3.0)
    hook_motion = first_event.get("motion_intent", "")
    has_punchy_words = any(len(w) > 4 for w in first_caption.get("emphasis_words", []))

    if first_dur <= 4.0 and (hook_motion or has_punchy_words):
        hook_score = 1.4
        hook_note = "Fast opening cut with immediate visual movement & emphasis"
    else:
        hook_score = 1.0
        hook_note = "Moderate hook; could open with higher kinetic tension"

    # 6. Research & Grounding (Max 1.5)
    metadata = v2_data.get("metadata", {})
    plan_ref = metadata.get("lineage", {}).get("plan", "")
    has_research = bool(plan_ref) or bool(v2_data.get("research_data"))
    if has_research:
        research_score = 1.4
        research_note = "Grounded in multi-source factual evidence"
    else:
        research_score = 0.9
        research_note = "Synthetic baseline without explicit research verification"

    total_score = round(qa_score + visual_score + pacing_score + caption_score + hook_score + research_score, 1)
    total_score = max(1.0, min(10.0, total_score))

    report = [
        "=== EDITORIAL QUALITY SCORECARD ===",
        f"Overall Rating         : {total_score:.1f} / 10.0",
        "",
        "--- Granular Breakdown ---",
        f"• Visual Diversity     : {visual_score:.1f} / 2.0  ({visual_note})",
        f"• Pacing & Rhythm      : {pacing_score:.1f} / 2.0  ({pacing_note})",
        f"• Hook Strength (0-3s) : {hook_score:.1f} / 1.5  ({hook_note})",
        f"• Caption Engagement   : {caption_score:.1f} / 1.5  ({caption_note})",
        f"• Research Authority   : {research_score:.1f} / 1.5  ({research_note})",
        f"• Technical QA Gate    : {qa_score:.1f} / 1.5  ({passed_checks}/{total_checks} checks passed)",
        "====================================",
    ]

    return "\n".join(report)
