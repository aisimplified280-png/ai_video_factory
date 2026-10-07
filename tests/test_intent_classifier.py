"""Tests for intent classification and entity separation."""
import pytest
from stages.script.intent_classifier import (
    VALID_PRIMARY_INTENTS,
    classify_intent,
    extract_entities_and_emphasis,
)


def test_classify_intent_limits_intents():
    # Primary intent should be in VALID_PRIMARY_INTENTS
    primary, secondaries = classify_intent(
        narrative_role="mechanism",
        spoken_text="How it works is that every request triggers the cluster assembly.",
    )
    assert primary in VALID_PRIMARY_INTENTS
    assert primary == "show_process"
    assert len(secondaries) <= 2
    assert primary not in secondaries


def test_classify_intent_prevents_keyword_explosion():
    # Pass 8 explicit secondaries, should be capped to at most 2
    primary, secondaries = classify_intent(
        narrative_role="hook",
        spoken_text="Massive compute explosion revealed across models.",
        explicit_secondary=["show_scale", "show_evidence", "warn", "compare", "humanize", "conclude"],
    )
    assert len(secondaries) <= 2


def test_extract_entities_and_emphasis_separates_words():
    # Case from specification:
    # "AI models need MORE processing power because every new capability increases the COMPUTATION required."
    text = "AI models need MORE processing power because every new capability increases the COMPUTATION required."

    extracted = extract_entities_and_emphasis(
        spoken_text=text,
        primary_subject_hint="AI models",
        entities_hint=["AI models", "processing power", "computation", "capability"],
        keywords_hint=["compute", "scaling"],
        emphasis_hint=["MORE", "COMPUTATION"],
    )

    assert "MORE" in extracted.emphasis_words
    assert "COMPUTATION" in extracted.emphasis_words

    # Hard rule: Emphasis words must NEVER be in entities!
    for emp in extracted.emphasis_words:
        assert emp not in extracted.entities
        assert emp.lower() not in [e.lower() for e in extracted.entities]

    assert "AI models" in extracted.entities
    assert "processing power" in extracted.entities
    assert extracted.primary_subject == "AI models"
    assert "compute" in extracted.keywords
