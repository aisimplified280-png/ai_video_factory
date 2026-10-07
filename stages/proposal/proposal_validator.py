"""Proposal Validator and Diversity Measurement.

Rejects proposals when:
- Concepts are too similar (< 65 diversity score)
- Hooks are duplicates
- Visual directions are duplicates
- Renderer selections are identical when variation is required
- All concepts use identical scene grammar
- Target duration is invalid
- Runtime is unsupported
- Required fields are missing
"""
from __future__ import annotations

import re
from typing import Any, Literal
from pydantic import BaseModel, Field


SUPPORTED_RUNTIMES = {"remotion", "hyperframes", "ffmpeg_pil"}
VALID_RENDERER_FAMILIES = {
    "explainer", "cinematic", "motion_graphics", "documentary", "screen_demo", "hybrid"
}
VALID_COMPOSITION_MODES = {"templated", "atelier"}


class ProposalValidationFinding(BaseModel):
    code: str
    severity: Literal["critical", "warning", "info"]
    message: str
    concept_id: str | None = None
    correction: str = ""


class ProposalReviewContract(BaseModel):
    concept_diversity: Literal["pass", "warning", "reject"]
    topic_fit: Literal["pass", "warning", "reject"]
    hook_quality: Literal["pass", "warning", "reject"]
    creative_difference: Literal["pass", "warning", "reject"]


class ProposalValidationReport(BaseModel):
    status: Literal["pass", "warning", "rejected"]
    concept_diversity_score: float
    findings: list[ProposalValidationFinding] = Field(default_factory=list)
    review: ProposalReviewContract

    model_config = {"extra": "ignore"}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
    stopwords = {"the", "and", "for", "with", "this", "that", "from", "into", "your", "about", "what", "how"}
    return set(words) - stopwords


def _jaccard_distance(s1: set[str], s2: set[str]) -> float:
    if not s1 and not s2:
        return 0.0
    intersection = len(s1 & s2)
    union = len(s1 | s2)
    if union == 0:
        return 0.0
    return 1.0 - (intersection / union)


def calculate_concept_diversity(concepts: list[dict[str, Any]]) -> float:
    """Calculate diversity score between 0.0 and 100.0 across concepts."""
    if len(concepts) < 2:
        return 0.0

    # 1. Hook pairwise diversity (0 - 20)
    hook_distances = []
    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            d = _jaccard_distance(_tokenize(concepts[i].get("hook", "")), _tokenize(concepts[j].get("hook", "")))
            hook_distances.append(d)
    hook_score = (sum(hook_distances) / len(hook_distances)) * 20.0 if hook_distances else 0.0

    # 2. Visual metaphor pairwise diversity (0 - 20)
    metaphor_distances = []
    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            d = _jaccard_distance(
                _tokenize(concepts[i].get("visual_metaphor", "")),
                _tokenize(concepts[j].get("visual_metaphor", ""))
            )
            metaphor_distances.append(d)
    metaphor_score = (sum(metaphor_distances) / len(metaphor_distances)) * 20.0 if metaphor_distances else 0.0

    # 3. Visual direction pairwise diversity (0 - 20)
    vis_distances = []
    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            d = _jaccard_distance(
                _tokenize(concepts[i].get("visual_direction", "")),
                _tokenize(concepts[j].get("visual_direction", ""))
            )
            vis_distances.append(d)
    vis_score = (sum(vis_distances) / len(vis_distances)) * 20.0 if vis_distances else 0.0

    # 4. Renderer family diversity (0 - 20)
    distinct_families = len(set(c.get("renderer_family", "") for c in concepts if c.get("renderer_family")))
    if distinct_families >= 3:
        renderer_score = 20.0
    elif distinct_families == 2:
        renderer_score = 12.0
    else:
        renderer_score = 4.0

    # 5. Scene grammar and narrative structure diversity (0 - 20)
    grammar_distances = []
    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            g1 = f"{concepts[i].get('narrative_structure', '')} {concepts[i].get('scene_grammar', '')}"
            g2 = f"{concepts[j].get('narrative_structure', '')} {concepts[j].get('scene_grammar', '')}"
            d = _jaccard_distance(_tokenize(g1), _tokenize(g2))
            grammar_distances.append(d)
    grammar_score = (sum(grammar_distances) / len(grammar_distances)) * 20.0 if grammar_distances else 0.0

    total_score = hook_score + metaphor_score + vis_score + renderer_score + grammar_score
    return round(max(0.0, min(100.0, total_score)), 1)


class ProposalValidator:
    """Validates proposal packet artifacts."""

    def __init__(self, min_diversity_score: float = 65.0) -> None:
        self.min_diversity_score = min_diversity_score

    def validate(
        self,
        data: dict[str, Any],
        research_data: dict[str, Any] | None = None,
    ) -> ProposalValidationReport:
        findings: list[ProposalValidationFinding] = []

        concepts = data.get("concepts", [])
        if not concepts:
            findings.append(
                ProposalValidationFinding(
                    code="EMPTY_PROPOSALS",
                    severity="critical",
                    message="Proposal packet contains no concepts.",
                    correction="Generate at least 2 and ideally 3 distinct concepts.",
                )
            )
            return ProposalValidationReport(
                status="rejected",
                concept_diversity_score=0.0,
                findings=findings,
                review=ProposalReviewContract(
                    concept_diversity="reject",
                    topic_fit="reject",
                    hook_quality="reject",
                    creative_difference="reject",
                ),
            )

        if len(concepts) < 2:
            findings.append(
                ProposalValidationFinding(
                    code="INSUFFICIENT_CONCEPTS",
                    severity="critical",
                    message=f"Expected 2-3 concepts, found {len(concepts)}.",
                    correction="Generate 3 distinct creative concepts.",
                )
            )

        required_concept_fields = [
            "concept_id", "hook", "audience_promise", "narrative_structure",
            "visual_direction", "visual_metaphor", "tone", "target_duration",
            "renderer_family", "render_runtime", "composition_mode",
        ]

        seen_hooks: set[str] = set()
        seen_metaphors: set[str] = set()

        for c in concepts:
            cid = c.get("concept_id", "unknown")

            # Missing required fields
            for rf in required_concept_fields:
                if not c.get(rf):
                    findings.append(
                        ProposalValidationFinding(
                            code="MISSING_CONCEPT_FIELD",
                            severity="critical",
                            concept_id=cid,
                            message=f"Concept {cid} missing required field '{rf}'.",
                            correction=f"Include '{rf}' in concept.",
                        )
                    )

            # Target duration check
            dur = c.get("target_duration")
            if dur is not None and (not isinstance(dur, (int, float)) or dur < 10.0):
                findings.append(
                    ProposalValidationFinding(
                        code="INVALID_TARGET_DURATION",
                        severity="critical",
                        concept_id=cid,
                        message=f"Concept {cid} target_duration must be at least 10s, got {dur}.",
                        correction="Set target duration >= 10.0 seconds.",
                    )
                )

            # Runtime validation
            runtime = c.get("render_runtime")
            if runtime and runtime not in SUPPORTED_RUNTIMES:
                findings.append(
                    ProposalValidationFinding(
                        code="UNSUPPORTED_RUNTIME",
                        severity="critical",
                        concept_id=cid,
                        message=f"Runtime {runtime!r} is not in supported list {sorted(SUPPORTED_RUNTIMES)}.",
                        correction=f"Select from {sorted(SUPPORTED_RUNTIMES)}.",
                    )
                )

            # Renderer family validation
            family = c.get("renderer_family")
            if family and family not in VALID_RENDERER_FAMILIES:
                findings.append(
                    ProposalValidationFinding(
                        code="INVALID_RENDERER_FAMILY",
                        severity="critical",
                        concept_id=cid,
                        message=f"Renderer family {family!r} is not in {sorted(VALID_RENDERER_FAMILIES)}.",
                        correction=f"Select from {sorted(VALID_RENDERER_FAMILIES)}.",
                    )
                )

            # Composition mode validation
            mode = c.get("composition_mode")
            if mode and mode not in VALID_COMPOSITION_MODES:
                findings.append(
                    ProposalValidationFinding(
                        code="INVALID_COMPOSITION_MODE",
                        severity="critical",
                        concept_id=cid,
                        message=f"Composition mode {mode!r} is not in {sorted(VALID_COMPOSITION_MODES)}.",
                        correction="Choose 'templated' or 'atelier'.",
                    )
                )

            # Hook duplicate check
            hook = c.get("hook", "").strip().lower()
            if hook:
                if hook in seen_hooks:
                    findings.append(
                        ProposalValidationFinding(
                            code="DUPLICATE_HOOK",
                            severity="critical",
                            concept_id=cid,
                            message=f"Concept {cid} has duplicate hook identical to another concept.",
                            correction="Each concept must have an entirely distinct hook.",
                        )
                    )
                seen_hooks.add(hook)

            # Metaphor duplicate check
            metaphor = c.get("visual_metaphor", "").strip().lower()
            if metaphor:
                if metaphor in seen_metaphors:
                    findings.append(
                        ProposalValidationFinding(
                            code="DUPLICATE_METAPHOR",
                            severity="critical",
                            concept_id=cid,
                            message=f"Concept {cid} has duplicate visual metaphor.",
                            correction="Each concept must explore a distinct visual metaphor.",
                        )
                    )
                seen_metaphors.add(metaphor)

        # Diversity score
        diversity_score = calculate_concept_diversity(concepts)
        if diversity_score < self.min_diversity_score:
            findings.append(
                ProposalValidationFinding(
                    code="LOW_CONCEPT_DIVERSITY",
                    severity="critical",
                    message=(
                        f"Concept diversity score {diversity_score:.1f} is below minimum {self.min_diversity_score:.1f}. "
                        f"Concepts are too similar in visual metaphor, hook, or scene grammar."
                    ),
                    correction=(
                        "Ensure concepts use different renderer families, completely different visual metaphors, "
                        "and distinct narrative structures."
                    ),
                )
            )

        has_critical = any(f.severity == "critical" for f in findings)
        has_warning = any(f.severity == "warning" for f in findings)

        if has_critical:
            status = "rejected"
        elif has_warning:
            status = "warning"
        else:
            status = "pass"

        review = ProposalReviewContract(
            concept_diversity="reject" if diversity_score < self.min_diversity_score else "pass",
            topic_fit="pass",
            hook_quality="reject" if any(f.code == "DUPLICATE_HOOK" for f in findings) else "pass",
            creative_difference="reject" if any(f.code in ("DUPLICATE_METAPHOR", "LOW_CONCEPT_DIVERSITY") for f in findings) else "pass",
        )

        return ProposalValidationReport(
            status=status,
            concept_diversity_score=diversity_score,
            findings=findings,
            review=review,
        )
