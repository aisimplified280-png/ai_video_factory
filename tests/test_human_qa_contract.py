"""Unit tests for Human visual relevance dynamic contract evaluation (Issue #14)."""
from __future__ import annotations

from pathlib import Path
from PIL import Image
import pytest

from production.phase16.design_system import create_default_design_system
from production.phase16.evidence_contract import VisualEvidenceContract
from production.phase16.human_qa import evaluate_human_visual_relevance


def test_human_perception_rejects_robotics_for_software_domain(tmp_path: Path):
    design_system = create_default_design_system()
    # Create a dummy image
    img = Image.new("RGB", (1920, 1080), color=(240, 244, 250))
    frame_path = tmp_path / "frame_01.png"
    img.save(frame_path)

    # Contract describes a software topic (RAG retrieval) but primary_subject is physical robotics
    contract = VisualEvidenceContract(
        scene_id="scene_02",
        start_seconds=5.0,
        end_seconds=10.0,
        narration="Amazon Bedrock now offers native RAG capabilities with serverless vector stores.",
        claim="Native RAG retrieval from vector database",
        primary_subject="Robotic arm swinging across assembly line",
        action="manipulator kinematic arm swings across industrial floor",
        environment="manufacturing plant",
        story_specific_anchors=["robotic arm", "actuator"],
    )

    result = evaluate_human_visual_relevance(frame_path, contract, design_system, scene_idx=1)

    # Must reject due to severe domain mismatch
    assert result.passed is False
    assert result.human_visual_relevance_score <= 5.0
    assert "Domain mismatch" in result.visual_mismatch


def test_human_perception_passes_aligned_contract(tmp_path: Path):
    design_system = create_default_design_system()
    img = Image.new("RGB", (1920, 1080), color=(245, 247, 250))
    frame_path = tmp_path / "frame_02.png"
    img.save(frame_path)

    contract = VisualEvidenceContract(
        scene_id="scene_01",
        start_seconds=0.0,
        end_seconds=6.0,
        narration="Vector databases store embeddings as high-dimensional coordinates for fast semantic retrieval.",
        claim="Vector embeddings clustered in geometric space",
        primary_subject="High-dimensional vector embedding space",
        action="clusters query points in semantic index",
        environment="clean technical cloud diagram studio",
        story_specific_anchors=["cosine distance", "vector clusters"],
    )

    result = evaluate_human_visual_relevance(frame_path, contract, design_system, scene_idx=0)

    assert result.passed is True
    assert result.human_visual_relevance_score >= 7.0
    assert result.visual_mismatch == "None"
