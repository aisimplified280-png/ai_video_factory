"""Tests for production/pipeline_loader.py."""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from production.pipeline_loader import (
    PipelineLoader,
    PipelineNotFoundError,
    PipelineParseError,
    PipelineValidationError,
)
from schemas.models.pipeline import PipelineDefinition, StageDefinition


def test_list_pipelines():
    loader = PipelineLoader()
    pipelines = loader.list_pipelines()
    assert "youtube-short" in pipelines
    assert "animated-explainer" in pipelines
    assert "ai-news-short" in pipelines
    assert "tutorial-short" in pipelines
    assert len(pipelines) >= 4


def test_load_all_standard_pipelines():
    loader = PipelineLoader()
    for name in ["youtube-short", "animated-explainer", "ai-news-short", "tutorial-short"]:
        defn = loader.load(name)
        assert isinstance(defn, PipelineDefinition)
        assert defn.name == name
        assert len(defn.stages) >= 8
        assert len(defn.required_stages) >= 8
        assert defn.target_duration > 0


def test_load_caching():
    loader = PipelineLoader()
    defn1 = loader.load("youtube-short")
    defn2 = loader.load("youtube-short")
    assert defn1 is defn2

    loader.clear_cache()
    defn3 = loader.load("youtube-short")
    assert defn1 is not defn3
    assert defn1.name == defn3.name


def test_load_nonexistent_pipeline_raises():
    loader = PipelineLoader()
    with pytest.raises(PipelineNotFoundError):
        loader.load("nonexistent_pipeline_12345")


def test_load_malformed_yaml_raises():
    with TemporaryDirectory() as td:
        pdir = Path(td)
        bad_yaml = pdir / "bad.yaml"
        bad_yaml.write_text("invalid: [yaml: unclosed", encoding="utf-8")

        loader = PipelineLoader(pipeline_dir=pdir)
        with pytest.raises(PipelineParseError):
            loader.load("bad")


def test_get_stage_success():
    loader = PipelineLoader()
    stage = loader.get_stage("youtube-short", "research")
    assert isinstance(stage, StageDefinition)
    assert stage.name == "research"
    assert "research_brief" in stage.produces
    assert "brief" in stage.consumes


def test_get_stage_unknown_raises_key_error():
    loader = PipelineLoader()
    with pytest.raises(KeyError):
        loader.get_stage("youtube-short", "nonexistent_stage_xyz")


def test_loader_validate_method():
    loader = PipelineLoader()
    defn = loader.validate("youtube-short")
    assert defn.name == "youtube-short"
