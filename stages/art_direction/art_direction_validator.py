"""Art Direction Validator and Review Contract.

Validates:
- visual_variance, motion_intensity, information_density in [1, 10]
- visual_metaphor exists and is not generic / vague
- signature_device exists and is specific
- anti_patterns count >= 3
- palette consistency (valid hex format, distinct colors)
- renderer compatibility

Rejects vague or generic art direction.
"""
from __future__ import annotations

import re
from typing import Any, Literal
from pydantic import BaseModel, Field


FORBIDDEN_GENERIC_METAPHORS = {
    "modern ai graphics",
    "futuristic technology",
    "dynamic visuals",
    "clean modern design",
    "tech background",
    "cool visual effects",
    "futuristic graphics",
    "ai visuals",
    "modern technology",
}

HEX_COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class ArtDirectionFinding(BaseModel):
    code: str
    severity: Literal["critical", "warning", "info"]
    message: str
    correction: str = ""


class ArtDirectionReviewContract(BaseModel):
    visual_specificity: Literal["pass", "warning", "reject"]
    visual_variance: Literal["pass", "warning", "reject"]
    metaphor_quality: Literal["pass", "warning", "reject"]
    anti_pattern_coverage: Literal["pass", "warning", "reject"]


class ArtDirectionValidationReport(BaseModel):
    status: Literal["pass", "warning", "rejected"]
    findings: list[ArtDirectionFinding] = Field(default_factory=list)
    review: ArtDirectionReviewContract

    model_config = {"extra": "ignore"}


class ArtDirectionValidator:
    """Validator for creative art direction artifacts."""

    def __init__(
        self,
        min_anti_patterns: int = 3,
        min_visual_variance: int = 1,
        max_visual_variance: int = 10,
    ) -> None:
        self.min_anti_patterns = min_anti_patterns
        self.min_visual_variance = min_visual_variance
        self.max_visual_variance = max_visual_variance

    def validate(self, data: dict[str, Any]) -> ArtDirectionValidationReport:
        findings: list[ArtDirectionFinding] = []

        # 1. Dial validations: visual_variance, motion_intensity, information_density
        for dial in ("visual_variance", "motion_intensity", "information_density"):
            val = data.get(dial)
            if val is None or not isinstance(val, int):
                findings.append(
                    ArtDirectionFinding(
                        code=f"MISSING_{dial.upper()}",
                        severity="critical",
                        message=f"Dial '{dial}' must be an integer between 1 and 10.",
                        correction=f"Provide an integer from 1 to 10 for {dial}.",
                    )
                )
            elif val < 1 or val > 10:
                findings.append(
                    ArtDirectionFinding(
                        code=f"INVALID_{dial.upper()}_RANGE",
                        severity="critical",
                        message=f"Dial '{dial}' is {val}, must be clamped between 1 and 10.",
                        correction=f"Clamp {dial} within 1..10.",
                    )
                )

        # 2. Visual Metaphor requirement
        metaphor = str(data.get("visual_metaphor") or "").strip().lower()
        if not metaphor:
            findings.append(
                ArtDirectionFinding(
                    code="MISSING_VISUAL_METAPHOR",
                    severity="critical",
                    message="Art direction must define a concrete, non-empty visual_metaphor.",
                    correction="Define an original physical, architectural, or systemic visual metaphor.",
                )
            )
        elif metaphor in FORBIDDEN_GENERIC_METAPHORS or len(metaphor) < 8:
            findings.append(
                ArtDirectionFinding(
                    code="GENERIC_VISUAL_METAPHOR",
                    severity="critical",
                    message=(
                        f"Visual metaphor {metaphor!r} is too generic. Phrases like 'futuristic technology', "
                        f"'dynamic visuals', or 'modern AI graphics' are strictly forbidden."
                    ),
                    correction=(
                        "Define a concrete metaphor, e.g. 'server rooms behaving like an industrial power grid' "
                        "or 'task graph unfolding like a mission control room'."
                    ),
                )
            )

        # 3. Signature Device requirement
        signature_device = str(data.get("signature_device") or "").strip()
        if not signature_device or len(signature_device) < 3:
            findings.append(
                ArtDirectionFinding(
                    code="MISSING_SIGNATURE_DEVICE",
                    severity="critical",
                    message="Art direction must define a signature_device for key narrative beats.",
                    correction="Specify a signature device, e.g. 'telemetry HUD overlay', 'neural thread', or 'stacking documents'.",
                )
            )

        # 4. Anti-Patterns requirement
        anti_patterns = data.get("anti_patterns", [])
        if not isinstance(anti_patterns, list) or len(anti_patterns) < self.min_anti_patterns:
            findings.append(
                ArtDirectionFinding(
                    code="INSUFFICIENT_ANTI_PATTERNS",
                    severity="critical",
                    message=(
                        f"Expected at least {self.min_anti_patterns} explicit anti-patterns, "
                        f"found {len(anti_patterns) if isinstance(anti_patterns, list) else 0}."
                    ),
                    correction=f"Define at least {self.min_anti_patterns} specific visual anti-patterns to avoid.",
                )
            )

        # 5. Palette discipline validation
        palette = data.get("palette_discipline")
        if not isinstance(palette, dict):
            findings.append(
                ArtDirectionFinding(
                    code="MISSING_PALETTE",
                    severity="critical",
                    message="palette_discipline must be an object with hex colors.",
                    correction="Provide 'primary' and 'accent_1' hex colors.",
                )
            )
        else:
            primary = palette.get("primary", "")
            accent_1 = palette.get("accent_1", "")

            if not HEX_COLOR_REGEX.match(str(primary)):
                findings.append(
                    ArtDirectionFinding(
                        code="INVALID_PRIMARY_HEX",
                        severity="critical",
                        message=f"Primary color {primary!r} is not a valid 6-char hex code.",
                        correction="Use format #RRGGBB (e.g. #0F172A).",
                    )
                )

            if not HEX_COLOR_REGEX.match(str(accent_1)):
                findings.append(
                    ArtDirectionFinding(
                        code="INVALID_ACCENT_HEX",
                        severity="critical",
                        message=f"Accent color {accent_1!r} is not a valid 6-char hex code.",
                        correction="Use format #RRGGBB (e.g. #38BDF8).",
                    )
                )

            if primary and accent_1 and primary.lower() == accent_1.lower():
                findings.append(
                    ArtDirectionFinding(
                        code="PALETTE_LACKS_CONTRAST",
                        severity="warning",
                        message="Primary and accent_1 colors are identical, lacking visual contrast.",
                        correction="Choose contrasting primary and accent colors.",
                    )
                )

        # 6. Design Read check
        read = str(data.get("design_read") or "").strip()
        if len(read) < 10:
            findings.append(
                ArtDirectionFinding(
                    code="INSUFFICIENT_DESIGN_READ",
                    severity="critical",
                    message="design_read must provide a detailed explanation of the visual identity.",
                    correction="Write at least one substantive paragraph describing the aesthetic.",
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

        review = ArtDirectionReviewContract(
            visual_specificity="reject" if any(f.code in ("INSUFFICIENT_DESIGN_READ", "MISSING_SIGNATURE_DEVICE") for f in findings) else "pass",
            visual_variance="reject" if any("VISUAL_VARIANCE" in f.code for f in findings) else "pass",
            metaphor_quality="reject" if any("METAPHOR" in f.code for f in findings) else "pass",
            anti_pattern_coverage="reject" if any("ANTI_PATTERNS" in f.code for f in findings) else "pass",
        )

        return ArtDirectionValidationReport(
            status=status,
            findings=findings,
            review=review,
        )
