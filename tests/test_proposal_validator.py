"""Tests for stages/proposal/proposal_validator.py."""
import pytest
from stages.proposal.proposal_validator import (
    ProposalValidator,
    calculate_concept_diversity,
)


@pytest.fixture
def divergent_concepts():
    return [
        {
            "concept_id": "concept_01",
            "title": "The Mechanical Brain",
            "concept_family": "system_visualization",
            "hook": "Ever wonder what happens inside an AI cluster in the first 10 milliseconds of a prompt?",
            "audience_promise": "See the physical clockwork of token generation unfold.",
            "narrative_structure": "Macro cluster zoom -> Switch routing -> Matrix multiplier core -> Output token",
            "visual_direction": "Hyper-realistic architectural cross-section with glowing telemetry buses",
            "visual_metaphor": "Server rooms behaving like an industrial power grid under surge load",
            "tone": "Urgent and technical",
            "pacing": "Metric-driven rhythmic cuts",
            "scene_grammar": "Split diagnostic HUD with circuit telemetry and micro latency gauges",
            "renderer_family": "explainer",
            "render_runtime": "remotion",
            "composition_mode": "atelier",
            "asset_strategy": "modular svg schematics and synthetic telemetry",
            "target_duration": 35.0,
            "reasoning": "Grounds abstract matrix math in physical infrastructure."
        },
        {
            "concept_id": "concept_02",
            "title": "The Intelligence Timeline",
            "concept_family": "timeline_history",
            "hook": "In 2017, eight researchers published a paper that broke computing forever.",
            "audience_promise": "Track the unclassified race from a single research lab to global dominance.",
            "narrative_structure": "Archive reveal -> Geographic expansion map -> Power inflection -> Modern reality",
            "visual_direction": "Documentary archival aesthetic with classified redactive stamps and high-contrast maps",
            "visual_metaphor": "Small clandestine research laboratory expanding into planetary surveillance network",
            "tone": "Investigative and historical",
            "pacing": "Documentary cadence with hard evidentiary reveals",
            "scene_grammar": "Archival paper stills, declassified ink transitions, expanding world maps",
            "renderer_family": "documentary",
            "render_runtime": "ffmpeg_pil",
            "composition_mode": "templated",
            "asset_strategy": "historical photography, high-res map vector layers, paper textures",
            "target_duration": 35.0,
            "reasoning": "Humanizes AI through chronology and geopolitical stakes."
        },
        {
            "concept_id": "concept_03",
            "title": "The Awakening Network",
            "concept_family": "cinematic_story",
            "hook": "What if millions of autonomous AI agents started talking without human supervisors?",
            "audience_promise": "Witness the emergent cascade of synthetic coordination.",
            "narrative_structure": "Single isolated node -> Multi-agent gossip protocol -> Cascading synchronization -> Swarm intelligence",
            "visual_direction": "Dark minimalist canvas with bioluminescent fiber lines and volumetric depth",
            "visual_metaphor": "Starlit constellation awakening into a dense living neural organism",
            "tone": "Mysterious and awe-inspiring",
            "pacing": "Slow ambient build accelerating into exponential cascade",
            "scene_grammar": "Deep coordinate zooms, particle trails, orbital camera sweeps",
            "renderer_family": "motion_graphics",
            "render_runtime": "hyperframes",
            "composition_mode": "atelier",
            "asset_strategy": "3D particle simulations, volumetric glow shaders, dynamic typography",
            "target_duration": 35.0,
            "reasoning": "Captures the visceral awe of multi-agent emergent behavior."
        }
    ]


def test_diversity_score_high_for_divergent_concepts(divergent_concepts):
    score = calculate_concept_diversity(divergent_concepts)
    assert score >= 65.0, f"Expected diversity score >= 65, got {score}"


def test_diversity_score_low_for_repetitive_concepts():
    repetitive_concepts = [
        {
            "concept_id": "concept_01",
            "hook": "How AI works in 30 seconds with dark blue cards",
            "visual_metaphor": "dark blue cards with modern tech graphics",
            "visual_direction": "dark blue cards with glowing borders",
            "renderer_family": "explainer",
            "narrative_structure": "Intro -> Body -> Outro",
            "scene_grammar": "centered card layout"
        },
        {
            "concept_id": "concept_02",
            "hook": "How AI works in 30 seconds with bigger dark blue cards",
            "visual_metaphor": "dark blue cards with modern tech graphics and bigger text",
            "visual_direction": "dark blue cards with bigger glowing borders",
            "renderer_family": "explainer",
            "narrative_structure": "Intro -> Body -> Outro",
            "scene_grammar": "centered card layout"
        },
        {
            "concept_id": "concept_03",
            "hook": "How AI works in 30 seconds with animated dark blue cards",
            "visual_metaphor": "dark blue cards with modern tech graphics and animations",
            "visual_direction": "dark blue cards with subtle animations",
            "renderer_family": "explainer",
            "narrative_structure": "Intro -> Body -> Outro",
            "scene_grammar": "centered card layout"
        }
    ]
    score = calculate_concept_diversity(repetitive_concepts)
    assert score < 50.0, f"Expected low diversity score for trivial variations, got {score}"


def test_proposal_validator_passes_divergent_packet(divergent_concepts):
    validator = ProposalValidator(min_diversity_score=65.0)
    packet_data = {
        "concepts": divergent_concepts,
        "selected_concept_id": None
    }
    report = validator.validate(packet_data)
    assert report.status == "pass"
    assert report.concept_diversity_score >= 65.0
    assert report.review.concept_diversity == "pass"


def test_proposal_validator_rejects_duplicate_hook(divergent_concepts):
    validator = ProposalValidator()
    # Duplicate hook between concept 1 and 2
    divergent_concepts[1]["hook"] = divergent_concepts[0]["hook"]
    packet_data = {"concepts": divergent_concepts, "selected_concept_id": None}
    report = validator.validate(packet_data)
    assert report.status == "rejected"
    assert any(f.code == "DUPLICATE_HOOK" for f in report.findings)


def test_proposal_validator_rejects_unsupported_runtime(divergent_concepts):
    validator = ProposalValidator()
    divergent_concepts[0]["render_runtime"] = "flash_player"  # invalid runtime
    packet_data = {"concepts": divergent_concepts, "selected_concept_id": None}
    report = validator.validate(packet_data)
    assert report.status == "rejected"
    assert any(f.code == "UNSUPPORTED_RUNTIME" for f in report.findings)


def test_proposal_validator_rejects_invalid_duration(divergent_concepts):
    validator = ProposalValidator()
    divergent_concepts[0]["target_duration"] = 5.0  # Under 10s minimum
    packet_data = {"concepts": divergent_concepts, "selected_concept_id": None}
    report = validator.validate(packet_data)
    assert report.status == "rejected"
    assert any(f.code == "INVALID_TARGET_DURATION" for f in report.findings)
