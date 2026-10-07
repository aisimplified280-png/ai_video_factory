"""Tests for stages/art_direction/art_direction_validator.py."""
import pytest
from stages.art_direction.art_direction_validator import ArtDirectionValidator


@pytest.fixture
def valid_art_direction_data():
    return {
        "design_read": (
            "A high-precision technical telemetry aesthetic blending dark carbon backgrounds "
            "with luminescent cyan diagnostics and industrial schematic overlays."
        ),
        "visual_metaphor": "Server rooms behaving like an industrial power grid under surge load",
        "visual_variance": 8,
        "motion_intensity": 6,
        "information_density": 5,
        "palette_discipline": {
            "primary": "#0F172A",
            "accent_1": "#38BDF8",
            "accent_2": "#F43F5E",
            "neutral": "#64748B",
            "warning": "#F59E0B"
        },
        "typography_personality": "Monospace metric labels paired with bold geometric headlines",
        "layout_language": "Asymmetric multi-panel telemetry grid with split diagnostic feeds",
        "texture_language": "Subtle matte carbon finish with 5% fine grain and scanline pulse",
        "transition_language": "Snap zoom cuts and directional whip-pans with zero cross-dissolves",
        "reference_strategy": "Bloomberg telemetry monitors meet Wired schematic infographics",
        "signature_device": "Pulsing diagnostic telemetry HUD overlay on critical metric beats",
        "anti_patterns": [
            "No floating card in every scene",
            "No identical centered hero composition",
            "No text-only explanation without tangible visual anchor",
            "No generic 3D neon brain animations"
        ],
        "quality_gates": {
            "min_visual_variance": 6
        }
    }


def test_art_direction_validator_passes_valid_data(valid_art_direction_data):
    validator = ArtDirectionValidator()
    report = validator.validate(valid_art_direction_data)
    assert report.status == "pass"
    assert report.review.visual_specificity == "pass"
    assert report.review.metaphor_quality == "pass"
    assert report.review.anti_pattern_coverage == "pass"


def test_art_direction_validator_rejects_generic_metaphor(valid_art_direction_data):
    validator = ArtDirectionValidator()
    # Replace with forbidden generic phrase
    valid_art_direction_data["visual_metaphor"] = "modern AI graphics"
    report = validator.validate(valid_art_direction_data)
    assert report.status == "rejected"
    assert any(f.code == "GENERIC_VISUAL_METAPHOR" for f in report.findings)
    assert report.review.metaphor_quality == "reject"


def test_art_direction_validator_rejects_missing_metaphor(valid_art_direction_data):
    validator = ArtDirectionValidator()
    valid_art_direction_data["visual_metaphor"] = ""
    report = validator.validate(valid_art_direction_data)
    assert report.status == "rejected"
    assert any(f.code == "MISSING_VISUAL_METAPHOR" for f in report.findings)


def test_art_direction_validator_rejects_invalid_dial_range(valid_art_direction_data):
    validator = ArtDirectionValidator()
    valid_art_direction_data["visual_variance"] = 15  # Out of 1..10 range
    report = validator.validate(valid_art_direction_data)
    assert report.status == "rejected"
    assert any("VISUAL_VARIANCE" in f.code for f in report.findings)


def test_art_direction_validator_rejects_insufficient_anti_patterns(valid_art_direction_data):
    validator = ArtDirectionValidator()
    valid_art_direction_data["anti_patterns"] = ["No floating card"]  # Only 1, minimum is 3
    report = validator.validate(valid_art_direction_data)
    assert report.status == "rejected"
    assert any(f.code == "INSUFFICIENT_ANTI_PATTERNS" for f in report.findings)


def test_art_direction_validator_rejects_invalid_palette_hex(valid_art_direction_data):
    validator = ArtDirectionValidator()
    valid_art_direction_data["palette_discipline"]["primary"] = "blue"  # Not a valid 6-char hex
    report = validator.validate(valid_art_direction_data)
    assert report.status == "rejected"
    assert any("HEX" in f.code for f in report.findings)
