"""Validator for scene plan stage output artifacts.

Enforces viewer understanding, non-generic visual metaphors, shot beat coverage,
script-to-scene alignment, CTA finality, and Variety Governor rules.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field

from stages.scene_plan.beat_analyzer import validate_shots_coverage
from stages.scene_plan.scene_prompts import (
    VALID_CAMERA_INTENTS,
    VALID_MOTION_INTENTS,
    VALID_SCENE_TYPES,
    VALID_VISUAL_TECHNIQUES,
)
from stages.scene_plan.variety_governor import VarietyGovernor

GENERIC_METAPHOR_SUBSTRINGS: list[str] = [
    "modern ai graphics",
    "futuristic technology",
    "futuristic ai",
    "dynamic visuals",
    "technology visualization",
    "dynamic network",
    "abstract shapes",
    "generic graphics",
]

GENERIC_VIEWER_UNDERSTANDINGS: list[str] = [
    "viewer sees ai visualization",
    "viewer sees graphic",
    "viewer understands ai",
    "viewer sees technology",
    "viewer watches video",
]


class SceneFinding(BaseModel):
    """Structured finding for scene plan validation."""
    code: str
    severity: str  # "critical", "warning"
    message: str
    evidence: str = ""
    correction: str = ""


class SceneValidationReport(BaseModel):
    """Complete validation report for a scene plan artifact."""
    status: str  # "approved", "warning", "rejected"
    findings: list[SceneFinding] = Field(default_factory=list)
    variety_score: float = 0.0

    @property
    def is_valid(self) -> bool:
        return self.status != "rejected"


class SceneValidator:
    """Validates complete scene plan and individual scene specifications."""

    def __init__(self, variety_governor: VarietyGovernor | None = None) -> None:
        self.variety_governor = variety_governor or VarietyGovernor()

    def validate(
        self,
        scene_plan_data: dict[str, Any],
        script_data: dict[str, Any] | None = None,
        art_direction_data: dict[str, Any] | None = None,
    ) -> SceneValidationReport:
        findings: list[SceneFinding] = []

        scenes = scene_plan_data.get("scenes", [])
        if not scenes:
            findings.append(
                SceneFinding(
                    code="EMPTY_SCENE_PLAN",
                    severity="critical",
                    message="Scene plan contains zero scenes.",
                    correction="Generate at least 4 narrative scenes.",
                )
            )
            return SceneValidationReport(status="rejected", findings=findings, variety_score=0.0)

        # 1. Validate individual scenes
        last_end = 0.0
        covered_section_ids: set[str] = set()

        for idx, sc in enumerate(scenes):
            sc_id = sc.get("scene_id") or sc.get("id") or f"scene_{idx + 1}"
            start = sc.get("start_seconds", 0.0)
            end = sc.get("end_seconds", 0.0)
            dur = round(end - start, 2)

            if dur <= 0:
                findings.append(
                    SceneFinding(
                        code="INVALID_SCENE_TIMING",
                        severity="critical",
                        message=f"Scene {sc_id} has non-positive duration ({dur}s).",
                        evidence=f"start={start}, end={end}",
                        correction="Ensure end_seconds > start_seconds.",
                    )
                )

            if idx > 0 and start < last_end - 0.05:
                findings.append(
                    SceneFinding(
                        code="SCENE_TIMING_OVERLAP",
                        severity="critical",
                        message=f"Scene {sc_id} start ({start}s) overlaps previous scene end ({last_end}s).",
                        evidence=f"start={start} < last_end={last_end}",
                        correction="Make scene timestamps monotonically continuous.",
                    )
                )

            last_end = max(last_end, end)

            # Record referenced script section
            sec_ref = sc.get("script_section_id")
            if sec_ref:
                covered_section_ids.add(sec_ref)

            # Scene Type validation
            stype = sc.get("type")
            if stype not in VALID_SCENE_TYPES:
                findings.append(
                    SceneFinding(
                        code="INVALID_SCENE_TYPE",
                        severity="critical",
                        message=f"Scene {sc_id} has invalid type {stype!r}.",
                        evidence=f"type={stype}",
                        correction=f"Must be one of: {', '.join(sorted(VALID_SCENE_TYPES))}",
                    )
                )

            # Viewer Understanding validation
            vu = (sc.get("viewer_understanding") or "").strip().lower()
            if not vu:
                findings.append(
                    SceneFinding(
                        code="MISSING_VIEWER_UNDERSTANDING",
                        severity="critical",
                        message=f"Scene {sc_id} is missing required viewer_understanding.",
                        correction="State what the viewer understands visually from this scene.",
                    )
                )
            else:
                for gen_vu in GENERIC_VIEWER_UNDERSTANDINGS:
                    if gen_vu in vu:
                        findings.append(
                            SceneFinding(
                                code="GENERIC_VIEWER_UNDERSTANDING",
                                severity="critical",
                                message=f"Scene {sc_id} has generic viewer understanding: {gen_vu!r}.",
                                evidence=f"viewer_understanding='{vu}'",
                                correction="Describe the exact mental model or mechanism the viewer grasps.",
                            )
                        )
                        break

            # Visual Purpose validation
            vp = (sc.get("visual_purpose") or "").strip()
            if not vp:
                findings.append(
                    SceneFinding(
                        code="MISSING_VISUAL_PURPOSE",
                        severity="critical",
                        message=f"Scene {sc_id} is missing required visual_purpose.",
                        correction="Provide why this visual beat exists (e.g. establish scale, show mechanism).",
                    )
                )

            # Visual Metaphor validation
            vm = (sc.get("visual_metaphor") or "").strip().lower()
            if not vm:
                findings.append(
                    SceneFinding(
                        code="MISSING_VISUAL_METAPHOR",
                        severity="critical",
                        message=f"Scene {sc_id} is missing required visual_metaphor.",
                        correction="Ground scene in the art direction visual metaphor.",
                    )
                )
            else:
                for gen_vm in GENERIC_METAPHOR_SUBSTRINGS:
                    if gen_vm in vm:
                        findings.append(
                            SceneFinding(
                                code="GENERIC_VISUAL_METAPHOR",
                                severity="critical",
                                message=f"Scene {sc_id} uses forbidden generic visual metaphor: {gen_vm!r}.",
                                evidence=f"visual_metaphor='{vm}'",
                                correction="Use concrete physical or structural metaphors (e.g. power grid, archive).",
                            )
                        )
                        break

            # Subject and Subject Action validation
            subject = (sc.get("subject") or "").strip()
            action = (sc.get("subject_action") or "").strip()
            if not subject:
                findings.append(
                    SceneFinding(
                        code="MISSING_SCENE_SUBJECT",
                        severity="critical",
                        message=f"Scene {sc_id} has no defined visual subject.",
                        correction="Specify the primary physical/diagrammatic subject.",
                    )
                )
            if not action:
                findings.append(
                    SceneFinding(
                        code="MISSING_SUBJECT_ACTION",
                        severity="warning",
                        message=f"Scene {sc_id} has no defined subject action.",
                        correction="Describe what the subject does or how it transforms.",
                    )
                )

            # Shot beat coverage validation
            shots = sc.get("shots") or []
            if shots:
                shot_errs = validate_shots_coverage(shots, dur)
                for err in shot_errs:
                    findings.append(
                        SceneFinding(
                            code="INVALID_SHOT_COVERAGE",
                            severity="critical",
                            message=f"Scene {sc_id} shot error: {err}",
                            evidence=f"shots_count={len(shots)}",
                            correction="Ensure shots start at 0, end at scene duration, without gaps or overlaps.",
                        )
                    )

        # 2. Whole-Video CTA Finality Rule
        final_scene = scenes[-1]
        final_role = (final_scene.get("narrative_role") or "").lower()
        if final_role != "cta":
            findings.append(
                SceneFinding(
                    code="CTA_NOT_FINAL_SCENE",
                    severity="critical",
                    message="CTA must ALWAYS be the final scene of the video.",
                    evidence=f"final_scene_role='{final_role}'",
                    correction="Ensure the last scene is the channel CTA beat.",
                )
            )

        # Check for multiple CTAs or CTA placed earlier
        cta_scenes = [i for i, s in enumerate(scenes) if (s.get("narrative_role") or "").lower() == "cta"]
        if len(cta_scenes) > 1:
            findings.append(
                SceneFinding(
                    code="MULTIPLE_CTA_SCENES",
                    severity="warning",
                    message=f"Detected multiple CTA scenes at indices {cta_scenes}.",
                    correction="Keep only one concluding CTA scene.",
                )
            )

        # 3. Script-to-Scene Alignment
        if script_data:
            script_sections = script_data.get("sections", [])
            expected_sec_ids = {
                (s.get("section_id") or s.get("id"))
                for s in script_sections
                if s.get("section_id") or s.get("id")
            }
            uncovered = expected_sec_ids - covered_section_ids
            if uncovered:
                findings.append(
                    SceneFinding(
                        code="UNCOVERED_SCRIPT_SECTIONS",
                        severity="critical",
                        message=f"Script sections {list(uncovered)} are not covered by any scene in the plan.",
                        evidence=f"uncovered={list(uncovered)}",
                        correction="Ensure every script section has a corresponding visual scene.",
                    )
                )

        # 4. Variety Governor Evaluation
        variety_rep = self.variety_governor.evaluate(scenes, art_direction=art_direction_data)
        for vf in variety_rep.findings:
            findings.append(
                SceneFinding(
                    code=vf.code,
                    severity=vf.severity,
                    message=vf.message,
                    evidence=vf.evidence,
                    correction=vf.correction,
                )
            )

        has_critical = any(f.severity == "critical" for f in findings)
        has_warning = any(f.severity == "warning" for f in findings)
        status = "rejected" if has_critical else ("warning" if has_warning else "approved")

        return SceneValidationReport(
            status=status,
            findings=findings,
            variety_score=variety_rep.variety_score,
        )
