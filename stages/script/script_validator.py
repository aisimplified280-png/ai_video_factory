"""Validator for script stage output artifacts.

Enforces hook quality, CTA placement, timing constraints, intent limits,
entity/emphasis separation, and visual intent answers.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field

from stages.script.timing import validate_script_timing
from stages.script.intent_classifier import VALID_PRIMARY_INTENTS

FORBIDDEN_HOOK_PREFIXES: list[str] = [
    "today we're going to discuss",
    "today we are going to discuss",
    "today we will discuss",
    "today we're looking at",
    "today we are looking at",
    "artificial intelligence is changing",
    "ai is changing",
    "in this video",
    "let's take a look at",
    "let's dive into",
    "have you ever wondered",
    "welcome back to",
    "so today",
]

WEAK_VISUAL_INTENTS: list[str] = [
    "headline and supporting text",
    "text on screen",
    "simple text card",
    "floating card",
    "just text",
    "title and subtitle",
]


class ScriptFinding(BaseModel):
    """Structured finding for script validation."""
    code: str
    severity: str  # "critical", "warning"
    message: str
    evidence: str = ""
    correction: str = ""


class ScriptValidationReport(BaseModel):
    """Complete validation report for a script artifact."""
    status: str  # "approved", "warning", "rejected"
    findings: list[ScriptFinding] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.status != "rejected"


class ScriptValidator:
    """Validates full script artifact against creative and structural rules."""

    def __init__(
        self,
        min_duration: float = 30.0,
        max_duration: float = 60.0,
        min_words: int = 50,
        min_sections: int = 4,
    ) -> None:
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.min_words = min_words
        self.min_sections = min_sections

    def validate(self, script_data: dict[str, Any]) -> ScriptValidationReport:
        findings: list[ScriptFinding] = []

        sections = script_data.get("sections", [])
        if not sections or len(sections) < self.min_sections:
            findings.append(
                ScriptFinding(
                    code="INSUFFICIENT_SECTIONS",
                    severity="critical",
                    message=f"Script has {len(sections)} sections, minimum required is {self.min_sections}.",
                    evidence=f"sections={len(sections)}",
                    correction="Structure script with at least 4 narrative beats.",
                )
            )
            return ScriptValidationReport(status="rejected", findings=findings)

        # 1. Hook Validation
        hook_section = sections[0]
        hook_text = (hook_section.get("spoken_text") or script_data.get("hook", "")).strip().lower()
        for forbidden in FORBIDDEN_HOOK_PREFIXES:
            if hook_text.startswith(forbidden):
                findings.append(
                    ScriptFinding(
                        code="GENERIC_HOOK_REJECTED",
                        severity="critical",
                        message=f"Opening hook uses forbidden generic opening: {forbidden!r}.",
                        evidence=f"hook='{hook_text[:60]}...'",
                        correction="Replace with a bold question, surprising contrast, or dramatic mechanism.",
                    )
                )
                break

        # 2. CTA Validation
        cta_section = next((s for s in sections if s.get("narrative_role") == "cta"), None)
        if not cta_section:
            findings.append(
                ScriptFinding(
                    code="MISSING_CTA_SECTION",
                    severity="critical",
                    message="Script is missing a required CTA narrative section.",
                    correction="Include a closing section with narrative_role='cta'.",
                )
            )
        else:
            # CTA must be the final section
            if sections[-1].get("narrative_role") != "cta":
                findings.append(
                    ScriptFinding(
                        code="CTA_NOT_FINAL_SECTION",
                        severity="critical",
                        message="CTA section must be the final section of the script.",
                        evidence=f"last_section_role='{sections[-1].get('narrative_role')}'",
                        correction="Move the CTA to the end of the script.",
                    )
                )

        # 3. Timing Validation
        timing_res = validate_script_timing(
            sections=sections,
            min_duration=self.min_duration,
            max_duration=self.max_duration,
            min_words=self.min_words,
        )
        for tf in timing_res.findings:
            findings.append(
                ScriptFinding(
                    code=tf.code,
                    severity=tf.severity,
                    message=tf.message,
                    evidence=tf.evidence,
                    correction=tf.correction,
                )
            )

        # 4. Section Visual Intent & Question Validation
        for idx, sec in enumerate(sections):
            sec_id = sec.get("id") or sec.get("section_id") or f"sec_{idx + 1}"
            visual_intent = (sec.get("visual_intent") or "").strip().lower()
            if not visual_intent:
                findings.append(
                    ScriptFinding(
                        code="MISSING_VISUAL_INTENT",
                        severity="critical",
                        message=f"Section {sec_id} is missing required visual_intent.",
                        correction="Answer the visual question: what will the viewer see that is not spoken?",
                    )
                )
            else:
                for weak in WEAK_VISUAL_INTENTS:
                    if weak in visual_intent:
                        findings.append(
                            ScriptFinding(
                                code="WEAK_VISUAL_INTENT",
                                severity="critical",
                                message=f"Section {sec_id} has generic/weak visual intent: {weak!r}.",
                                evidence=f"visual_intent='{visual_intent}'",
                                correction="Provide physical metaphors, spatial relationships, or dynamic visual mechanics.",
                            )
                        )
                        break

            # 5. Intent Limits Validation
            primary_intent = sec.get("primary_intent")
            if primary_intent and primary_intent not in VALID_PRIMARY_INTENTS:
                findings.append(
                    ScriptFinding(
                        code="INVALID_PRIMARY_INTENT",
                        severity="warning",
                        message=f"Section {sec_id} has unrecognized primary intent: {primary_intent!r}.",
                        evidence=f"primary_intent={primary_intent}",
                        correction=f"Use one of: {', '.join(sorted(VALID_PRIMARY_INTENTS))}",
                    )
                )

            secondaries = sec.get("secondary_intents") or []
            if len(secondaries) > 2:
                findings.append(
                    ScriptFinding(
                        code="TOO_MANY_SECONDARY_INTENTS",
                        severity="critical",
                        message=f"Section {sec_id} has {len(secondaries)} secondary intents (max 2 allowed).",
                        evidence=f"secondaries={secondaries}",
                        correction="Limit secondary intents to 0-2 to prevent keyword explosion.",
                    )
                )

            # 6. Entity Separation Validation
            emphasis_words = [w.lower() for w in (sec.get("emphasis_words") or [])]
            entities = [e.lower() for e in (sec.get("entities") or [])]
            overlap = set(emphasis_words).intersection(set(entities))
            if overlap:
                findings.append(
                    ScriptFinding(
                        code="EMPHASIS_AS_ENTITY_LEAK",
                        severity="critical",
                        message=f"Section {sec_id} treats emphasis words as entities: {list(overlap)}.",
                        evidence=f"overlapping={list(overlap)}",
                        correction="Do not place emphasis words in the entities list.",
                    )
                )

        has_critical = any(f.severity == "critical" for f in findings)
        has_warning = any(f.severity == "warning" for f in findings)

        status = "rejected" if has_critical else ("warning" if has_warning else "approved")
        return ScriptValidationReport(status=status, findings=findings)
