"""Deterministic test suite for Phase 11 (Script Intelligence) & Phase 12 (Packaging).

Tests:
- Hook story selection & priority
- Shorts script structure (Hook in first 3s, Lead Story, Escalation, Branded CTA)
- Long-form chapterized script generation
- Script retention & subscriber conversion scoring
- Canonical schema compatibility with Phase 9 planner
- 10 YouTube Title candidate generation across psychological angles
- SEO Description generation with citations
- Punchy thumbnail text & documentary prompt generation
"""
from __future__ import annotations

import pytest

from production.phase10.models import ResearchPack, ResearchMode, StoryRecord, StoryScoring, SourceRecord
from production.phase11.models import ScriptFormat, ScriptSection
from production.phase11.story_selector import select_stories_for_script
from production.phase11.scriptwriter import generate_shorts_script, generate_longform_script, score_script
from production.phase12.packager import generate_title_candidates, generate_packaging


@pytest.fixture
def mock_research_pack():
    s1 = StoryRecord(
        story_id="story_001",
        headline="Massive secret leak: OpenAI robot arm crushes hardware benchmark",
        summary="Engineers demonstrated multi-axis manipulation in an industrial logistics facility.",
        trust_score=0.95,
        scoring=StoryScoring(shock_factor=0.9, virality=0.85, trust_score=0.95, overall_score=0.9),
        rank=1,
    )
    s2 = StoryRecord(
        story_id="story_002",
        headline="Destro AI raises $8M to coordinate mixed robot fleets in enterprise warehouses",
        summary="Autonomous pallet transport rovers integrate into existing supply chain facilities.",
        trust_score=0.85,
        scoring=StoryScoring(shock_factor=0.5, virality=0.6, trust_score=0.85, overall_score=0.7),
        rank=2,
    )
    s3 = StoryRecord(
        story_id="story_003",
        headline="Anthropic publishes report on autonomous task classification",
        summary="Research analyzes tasks where physical actuators perform reliably.",
        trust_score=0.90,
        scoring=StoryScoring(shock_factor=0.4, virality=0.5, trust_score=0.90, overall_score=0.65),
        rank=3,
    )

    src = SourceRecord(
        source_id="src_01",
        title="OpenAI Robot Arm Benchmark",
        publisher="techcrunch.com",
        url="https://techcrunch.com/robot-arm",
        retrieved_at="2026-10-07T00:00:00Z",
        source_type="news",
        tier=2,
    )

    return ResearchPack(
        topic="Robotics Warehouse Automation",
        researched_at="2026-10-07T00:00:00Z",
        research_mode=ResearchMode.LIVE,
        provider="multi",
        top_stories=[s1, s2, s3],
        stories=[s1, s2, s3],
        sources=[src],
    )


# ---------------------------------------------------------------------------
# Phase 11: Script Intelligence Tests
# ---------------------------------------------------------------------------

class TestStorySelector:
    def test_hook_story_selection(self, mock_research_pack):
        hook, lineup = select_stories_for_script(mock_research_pack, ScriptFormat.SHORTS)
        # s1 has highest shock and virality
        assert hook.story_id == "story_001"
        assert len(lineup) == 3
        assert lineup[0].story_id == "story_001"


class TestScriptwriter:
    def test_generate_shorts_script_structure(self, mock_research_pack):
        script = generate_shorts_script("Robotics Warehouse Automation", mock_research_pack)
        
        assert script.format == ScriptFormat.SHORTS
        assert len(script.sections) >= 4
        assert script.total_word_count >= 50
        assert script.total_duration_seconds >= 20.0

        # Hook is first
        hook = script.sections[0]
        assert hook.role == "hook"
        assert len(hook.spoken_text.split()) >= 4
        assert "welcome" not in hook.spoken_text.lower()
        assert "hey guys" not in hook.spoken_text.lower()

        # Final section is CTA
        cta = script.sections[-1]
        assert cta.role == "cta"
        assert "subscribe" in cta.spoken_text.lower()
        assert "AI Simplified Lab" in cta.spoken_text

        # Scoring
        assert script.scoring.hook_strength_score >= 0.8
        assert script.scoring.subscriber_conversion_score >= 0.8
        assert script.scoring.retention_score >= 0.8

    def test_canonical_schema_compatible_with_phase9(self, mock_research_pack):
        from production.phase9.planner import generate_plan
        script = generate_shorts_script("Robotics Warehouse Automation", mock_research_pack)
        canonical = script.to_canonical_schema("proj_test")

        assert canonical["schema_version"] == "1.0"
        assert len(canonical["sections"]) >= 4

        # Verify planner accepts this directly
        plan = generate_plan({"data": canonical}, {"research_data": mock_research_pack.to_dict()})
        assert "scene_concepts" in plan
        assert len(plan["scene_concepts"]) == len(canonical["sections"])
        assert plan["diversity_metrics"]["target_met"] is True

    def test_generate_longform_script(self, mock_research_pack):
        script = generate_longform_script("Robotics Warehouse Automation", mock_research_pack)
        assert script.format == ScriptFormat.LONG_FORM
        assert len(script.sections) >= 5
        assert script.total_word_count > 100


# ---------------------------------------------------------------------------
# Phase 12: Packaging Intelligence Tests
# ---------------------------------------------------------------------------

class TestPackagingIntelligence:
    def test_generate_10_title_candidates(self, mock_research_pack):
        titles = generate_title_candidates("Robotics Warehouse Automation", mock_research_pack)
        assert len(titles) == 10
        angles = {t.angle for t in titles}
        assert "curiosity_gap" in angles
        assert "shock_revelation" in angles
        assert "authority" in angles
        for t in titles:
            assert 0.0 <= t.title_score <= 10.0
            assert 0.0 <= t.curiosity_score <= 10.0

    def test_generate_complete_packaging(self, mock_research_pack):
        script = generate_shorts_script("Robotics Warehouse Automation", mock_research_pack)
        pkg = generate_packaging("Robotics Warehouse Automation", script, mock_research_pack)

        assert len(pkg.title_candidates) == 10
        assert pkg.selected_title != ""
        assert pkg.overall_package_score >= 7.0
        assert pkg.title_score >= 7.0
        assert pkg.curiosity_score >= 7.0
        assert pkg.thumbnail_score >= 7.0
        assert len(pkg.hashtags) >= 5
        assert "Subscribe" in pkg.description
        assert "•" in pkg.description  # contains source list

        # Thumbnail
        assert len(pkg.thumbnail_text.split()) <= 4  # Punchy, 1-4 words
        assert "Cinematic documentary" in pkg.thumbnail_prompt or "photography" in pkg.thumbnail_prompt
        assert "anime" not in pkg.thumbnail_prompt.lower()
