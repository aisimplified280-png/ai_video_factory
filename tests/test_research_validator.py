"""Tests for stages/research/research_validator.py."""
import pytest
from stages.research.research_validator import ResearchValidator


def test_research_validator_passes_valid_brief():
    validator = ResearchValidator(depth="standard", is_time_sensitive=False)
    data = {
        "topic": "Mixture of Experts Architecture",
        "audience": "AI Engineers",
        "sources": [
            {
                "source_id": "src_001",
                "title": "Outrageously Large Neural Networks: The Sparsely-Gated MoE",
                "url": "https://arxiv.org/abs/1701.06538",
                "domain": "arxiv.org",
                "published_at": "2024-01-15T00:00:00Z",
                "content_excerpt": "MoE layers route tokens to specialized expert networks via a gating network."
            },
            {
                "source_id": "src_002",
                "title": "Mixtral of Experts Announcement",
                "url": "https://mistral.ai/news/mixtral-of-experts/",
                "domain": "mistral.ai",
                "published_at": "2024-02-10T00:00:00Z",
                "content_excerpt": "Mixtral 8x7B uses 12B active parameters per token while retaining 47B total capacity."
            },
            {
                "source_id": "src_003",
                "title": "DeepSeek-V3 Technical Report",
                "url": "https://github.com/deepseek-ai/DeepSeek-V3",
                "domain": "github.com",
                "published_at": "2024-12-20T00:00:00Z",
                "content_excerpt": "DeepSeek-V3 adopts Multi-head Latent Attention and auxiliary-loss-free load balancing."
            }
        ],
        "facts": [
            {
                "claim": "Mixtral 8x7B processes tokens with 12.9B active parameters.",
                "source_ids": ["src_002"],
                "confidence": 0.98
            },
            {
                "claim": "Gating routers selectively activate a sparse subset of expert feed-forward blocks.",
                "source_ids": ["src_001"],
                "confidence": 0.95
            },
            {
                "claim": "DeepSeek-V3 utilizes auxiliary-loss-free strategy for balanced expert routing.",
                "source_ids": ["src_003"],
                "confidence": 0.94
            }
        ],
        "angles_discovered": [
            "Why MoE enables datacenter-class intelligence at consumer inference cost",
            "The memory bandwidth bottleneck vs compute efficiency trade-off"
        ],
    }

    report = validator.validate(data)
    assert report.status == "pass"
    assert report.depth_met is True
    assert report.review.source_quality == "pass"
    assert report.review.evidence_quality == "pass"


def test_research_validator_rejects_empty_research():
    validator = ResearchValidator()
    report = validator.validate({"topic": "AI", "sources": [], "facts": []})
    assert report.status == "rejected"
    assert any(f.code == "EMPTY_RESEARCH" for f in report.findings)


def test_research_validator_rejects_unsupported_claim():
    validator = ResearchValidator(depth="minimal")
    data = {
        "topic": "Transformers",
        "sources": [
            {
                "source_id": "src_001",
                "title": "Attention Is All You Need",
                "url": "https://arxiv.org/abs/1706.03762",
                "content_excerpt": "The Transformer is the first transduction model relying entirely on self-attention."
            }
        ],
        "facts": [
            {
                "claim": "Attention mechanism replaces recurrence entirely.",
                "source_ids": ["src_001"],
                "confidence": 0.99
            },
            {
                "claim": "Quantum computers run transformers 1000x faster.",
                "source_ids": [],  # Unsupported claim!
                "confidence": 0.50
            }
        ],
        "angles_discovered": ["Attention mechanism overview"]
    }
    report = validator.validate(data)
    assert report.status == "rejected"
    assert any(f.code == "UNSUPPORTED_CLAIM" for f in report.findings)
    assert report.review.evidence_quality == "reject"


def test_research_validator_rejects_hallucinated_source_reference():
    validator = ResearchValidator(depth="minimal")
    data = {
        "topic": "Transformers",
        "sources": [
            {
                "source_id": "src_001",
                "title": "Attention Paper",
                "url": "https://arxiv.org/abs/1706.03762",
                "content_excerpt": "Transformer architecture"
            }
        ],
        "facts": [
            {
                "claim": "Self attention has O(n^2) complexity.",
                "source_ids": ["src_999"],  # src_999 doesn't exist!
                "confidence": 0.95
            },
            {
                "claim": "Residual connections prevent gradient decay.",
                "source_ids": ["src_001"],
                "confidence": 0.95
            }
        ],
        "angles_discovered": ["Attention complexity"]
    }
    report = validator.validate(data)
    assert report.status == "rejected"
    assert any(f.code == "HALLUCINATED_SOURCE_REFERENCE" for f in report.findings)


def test_research_validator_detects_duplicate_sources():
    validator = ResearchValidator(depth="standard")
    data = {
        "topic": "Diffusion Models",
        "sources": [
            {"source_id": "src_001", "title": "Paper 1", "url": "https://arxiv.org/abs/2006.11239", "content_excerpt": "DDPM excerpt"},
            {"source_id": "src_002", "title": "Paper 1 Dup", "url": "https://arxiv.org/abs/2006.11239/", "content_excerpt": "DDPM excerpt dup"},
            {"source_id": "src_003", "title": "Paper 3", "url": "https://arxiv.org/abs/2105.05233", "content_excerpt": "Guided diffusion"}
        ],
        "facts": [
            {"claim": "Denoising score matching learns data distribution.", "source_ids": ["src_001"], "confidence": 0.9},
            {"claim": "Classifier guidance improves sample fidelity.", "source_ids": ["src_003"], "confidence": 0.9},
            {"claim": "Langevin dynamics samples from reverse process.", "source_ids": ["src_001"], "confidence": 0.9}
        ],
        "angles_discovered": ["Physics of diffusion", "Speed vs quality trade-off"]
    }
    report = validator.validate(data)
    assert any(f.code == "DUPLICATE_SOURCE" for f in report.findings)


def test_research_validator_rejects_stale_sources_for_current_topic():
    # Time-sensitive topic with ancient sources
    validator = ResearchValidator(depth="minimal", is_time_sensitive=True)
    data = {
        "topic": "Latest GPT-5 Launch Announcement Today",
        "sources": [
            {
                "source_id": "src_001",
                "title": "GPT-2 Release",
                "url": "https://openai.com/research/better-language-models",
                "published_at": "2019-02-14T00:00:00Z",  # Over 5 years old
                "content_excerpt": "GPT-2 is a 1.5B parameter transformer model."
            }
        ],
        "facts": [
            {"claim": "GPT-2 was released in 2019.", "source_ids": ["src_001"], "confidence": 0.99},
            {"claim": "Model was trained on WebText dataset.", "source_ids": ["src_001"], "confidence": 0.99}
        ],
        "angles_discovered": ["Language model scaling history"]
    }
    report = validator.validate(data)
    assert report.status == "rejected"
    assert any(f.code == "STALE_SOURCES_FOR_CURRENT_TOPIC" for f in report.findings)
    assert report.review.freshness == "reject"
