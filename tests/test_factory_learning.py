"""Unit tests for Phase 14 Factory Learning System."""
import pytest
from pathlib import Path
from production.phase14.learning_engine import FactoryLearningSystem
from production.phase14.models import VideoMetrics, VideoRecord
from production.phase12.models import TitleCandidate


@pytest.fixture
def temp_learning_system(tmp_path):
    mem_file = tmp_path / "factory_memory.json"
    return FactoryLearningSystem(memory_path=mem_file)


def test_initial_baseline_loaded(temp_learning_system):
    sys = temp_learning_system
    assert len(sys.records) >= 3
    insights = sys.get_learning_insights()
    assert insights.total_videos_analyzed >= 3
    assert len(insights.top_title_angles) > 0
    assert len(insights.winning_keywords) > 0


def test_record_new_video_metrics(temp_learning_system):
    sys = temp_learning_system
    initial_count = len(sys.records)

    metrics = VideoMetrics(
        views=65000,
        ctr_percent=12.5,
        avg_watch_percentage=89.2,
        subscribers_gained=520,
        retention_dropoff_3s=94.0,
    )
    rec = sys.record_video_metrics(
        production_id="test_prod_100",
        topic="Robotics AI",
        title="Robots Just Replaced Another Human Team",
        title_angle="shock_revelation",
        metrics=metrics,
        hook_text="Warehouse robots are getting smarter fast.",
        hook_style="fast_assertion",
        visual_style="documentary_industrial",
        thumbnail_text="ROBOTS REPLACED",
    )

    assert rec.composite_performance_score > 90.0
    assert len(sys.records) == initial_count + 1

    # Verify insights update
    insights = sys.get_learning_insights()
    assert insights.total_videos_analyzed == initial_count + 1


def test_learned_title_boosts(temp_learning_system):
    sys = temp_learning_system
    candidates = [
        TitleCandidate(title="Robots Just Took Another Human Job", angle="shock_revelation", title_score=9.0, curiosity_score=9.0),
        TitleCandidate(title="Predicting The Future Of Robotics", angle="passive_academic", title_score=8.5, curiosity_score=8.0),
    ]

    boosted = sys.apply_learned_title_boosts(candidates)
    assert len(boosted) == 2
    # The high-performing title with winning angle + keyword should be boosted and ranked #1
    top = boosted[0]
    assert top.angle == "shock_revelation"
    assert top.title_score >= 9.2
