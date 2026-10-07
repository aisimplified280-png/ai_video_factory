"""Deterministic timing engine for script generation and validation.

Calculates spoken duration, pause cues, section timestamps, and validates duration
bounds for short-form video (30-60s).
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class TimingFinding(BaseModel):
    """Structured timing validation finding."""
    code: str
    severity: str  # "critical", "warning"
    message: str
    evidence: str = ""
    correction: str = ""


class TimingValidationResult(BaseModel):
    """Result of validating script timing."""
    status: str  # "valid", "warning", "invalid"
    total_duration_seconds: float
    total_word_count: int
    findings: list[TimingFinding] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.status != "invalid"


def count_words(text: str) -> int:
    """Accurately count spoken words, ignoring punctuation."""
    if not text:
        return 0
    # Split on whitespace after stripping leading/trailing punctuation
    cleaned = re.sub(r"[^\w\s'-]", " ", text)
    words = [w for w in cleaned.split() if w.strip()]
    return len(words)


def estimate_spoken_duration(
    text: str,
    speaking_rate_wps: float = 2.6,
    pause_after: float = 0.25,
) -> float:
    """Estimate spoken duration in seconds from text based on speaking rate and punctuation pauses.

    Default rate: 2.6 words/sec (~156 words/min), ideal for clear energetic narration.
    Punctuation adds natural conversational breathing room:
    - Period / question / exclamation: +0.4s
    - Semicolon / colon / dash: +0.25s
    - Comma: +0.15s
    """
    words = count_words(text)
    if words == 0:
        return 0.0

    base_duration = words / speaking_rate_wps

    # Add pauses based on punctuation
    period_count = len(re.findall(r"[.!?]+(?:\s|$)", text))
    dash_count = len(re.findall(r"[:;—–-]+(?:\s|$)", text))
    comma_count = len(re.findall(r"[,]+(?:\s|$)", text))

    punctuation_pause = (period_count * 0.40) + (dash_count * 0.25) + (comma_count * 0.15)
    total = base_duration + punctuation_pause + pause_after
    return round(total, 2)


def apply_script_timing(
    sections: list[dict[str, Any]],
    target_duration: float = 45.0,
    speaking_rate_wps: float = 2.6,
) -> tuple[list[dict[str, Any]], float, int]:
    """Calculate and assign deterministic timestamps to script sections.

    Returns:
        (updated_sections, total_duration_seconds, total_word_count)
    """
    current_time = 0.0
    total_words = 0
    updated_sections = []

    for idx, sec in enumerate(sections):
        sec_copy = dict(sec)
        spoken_text = sec_copy.get("spoken_text", "")
        sec_words = count_words(spoken_text)
        total_words += sec_words

        pause_after = float(sec_copy.get("pause_after", 0.25))
        duration = estimate_spoken_duration(
            spoken_text,
            speaking_rate_wps=speaking_rate_wps,
            pause_after=pause_after,
        )

        # Minimum section duration: 1.5s
        duration = max(1.5, duration)

        start_time = round(current_time, 2)
        end_time = round(current_time + duration, 2)

        sec_copy["duration"] = duration
        sec_copy["estimated_start"] = start_time
        sec_copy["estimated_end"] = end_time
        sec_copy["timestamp_start"] = start_time
        sec_copy["timestamp_end"] = end_time

        # Ensure id / section_id are synchronized
        sec_id = sec_copy.get("section_id") or sec_copy.get("id") or f"sec_{idx + 1:02d}"
        sec_copy["id"] = sec_id
        sec_copy["section_id"] = sec_id

        current_time = end_time
        updated_sections.append(sec_copy)

    total_duration = round(current_time, 2)
    return updated_sections, total_duration, total_words


def validate_script_timing(
    sections: list[dict[str, Any]],
    min_duration: float = 30.0,
    max_duration: float = 60.0,
    min_words: int = 50,
) -> TimingValidationResult:
    """Validate timing sequence, duration bounds, and section continuity."""
    findings: list[TimingFinding] = []
    total_words = sum(count_words(sec.get("spoken_text", "")) for sec in sections)

    if not sections:
        findings.append(
            TimingFinding(
                code="EMPTY_SECTIONS",
                severity="critical",
                message="Script contains no sections.",
                correction="Add script sections.",
            )
        )
        return TimingValidationResult(
            status="invalid",
            total_duration_seconds=0.0,
            total_word_count=0,
            findings=findings,
        )

    last_end = 0.0
    for idx, sec in enumerate(sections):
        start = sec.get("estimated_start") if sec.get("estimated_start") is not None else sec.get("timestamp_start", 0.0)
        end = sec.get("estimated_end") if sec.get("estimated_end") is not None else sec.get("timestamp_end", 0.0)
        duration = sec.get("duration", (end - start) if end is not None and start is not None else 0.0)

        if duration <= 0:
            findings.append(
                TimingFinding(
                    code="INVALID_SECTION_DURATION",
                    severity="critical",
                    message=f"Section {sec.get('id', idx)} duration {duration}s is non-positive.",
                    evidence=f"start={start}, end={end}",
                    correction="Ensure section has spoken text and valid duration.",
                )
            )

        if idx > 0 and start < last_end - 0.05:
            findings.append(
                TimingFinding(
                    code="SECTION_TIMING_OVERLAP",
                    severity="critical",
                    message=f"Section {sec.get('id', idx)} starts ({start}s) before previous section ends ({last_end}s).",
                    evidence=f"start={start} < last_end={last_end}",
                    correction="Sequence section timestamps monotonically.",
                )
            )

        gap = start - last_end
        if idx > 0 and gap > 2.0:
            findings.append(
                TimingFinding(
                    code="EXCESSIVE_TIMING_GAP",
                    severity="warning",
                    message=f"Gap of {gap:.2f}s between sections {idx - 1} and {idx}.",
                    evidence=f"gap={gap:.2f}s",
                    correction="Reduce dead air or insert transition cues.",
                )
            )

        last_end = max(last_end, end)

    total_duration = round(last_end, 2)

    # Check duration bounds
    if total_duration < min_duration:
        findings.append(
            TimingFinding(
                code="SCRIPT_TOO_SHORT",
                severity="critical",
                message=f"Total script duration {total_duration}s is below minimum {min_duration}s.",
                evidence=f"duration={total_duration}s < min={min_duration}s",
                correction="Expand explanations or add supporting evidence beats.",
            )
        )
    elif total_duration > max_duration:
        findings.append(
            TimingFinding(
                code="SCRIPT_TOO_LONG",
                severity="critical",
                message=f"Total script duration {total_duration}s exceeds maximum {max_duration}s for short-form.",
                evidence=f"duration={total_duration}s > max={max_duration}s",
                correction="Tighten narration and remove non-essential words.",
            )
        )

    # Check word count
    if total_words < min_words:
        findings.append(
            TimingFinding(
                code="WORD_COUNT_TOO_LOW",
                severity="critical",
                message=f"Total word count {total_words} is below minimum {min_words} words.",
                evidence=f"words={total_words} < min={min_words}",
                correction="Provide more substantive explanation in narration.",
            )
        )

    # Determine status
    has_critical = any(f.severity == "critical" for f in findings)
    has_warning = any(f.severity == "warning" for f in findings)

    status = "invalid" if has_critical else ("warning" if has_warning else "valid")
    return TimingValidationResult(
        status=status,
        total_duration_seconds=total_duration,
        total_word_count=total_words,
        findings=findings,
    )
