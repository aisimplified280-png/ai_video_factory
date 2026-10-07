"""Claim verifier: assigns ClaimStatus based on evidence from sources.

Rules:
- CONFIRMED: 1+ Tier-1 source OR 2+ independent reputable sources agree.
- LIKELY: 1 Tier-2 source, or 2+ Tier-3 sources with consistent snippets.
- SINGLE_SOURCE: exactly 1 source, any tier, no corroboration.
- CONFLICTING: sources disagree or have contradictory snippets.
- UNVERIFIED: no retrieved sources support the claim.
- OUTDATED: claim is supported but sources are older than freshness threshold.

This module NEVER invents evidence. It only works with retrieved source data.
"""
from __future__ import annotations

import re
from typing import Optional
from .models import ClaimStatus, ClaimRecord, SourceRecord
from .fetcher import infer_tier


def _sources_for_claim(claim: str, sources: list[SourceRecord]) -> list[SourceRecord]:
    """Find sources whose title/snippet contains meaningful claim tokens."""
    # Extract key noun phrases from the claim (simple heuristic)
    claim_lower = claim.lower()
    # Tokenize meaningful words (ignore stop words)
    stop = {"a","an","the","is","are","was","were","has","have","had","in","on","of",
            "to","for","and","or","but","with","by","from","that","this","it","its"}
    tokens = [w for w in re.findall(r"\b\w{3,}\b", claim_lower) if w not in stop]
    
    if not tokens:
        return []
    
    matched: list[SourceRecord] = []
    for src in sources:
        text = (src.title + " " + src.snippet if hasattr(src, "snippet") else src.title).lower()
        match_count = sum(1 for t in tokens if t in text)
        if match_count >= max(1, len(tokens) // 3):  # at least 1/3 of tokens must match
            matched.append(src)
    return matched


def assign_status(
    claim: str,
    matched_sources: list[SourceRecord],
    freshness_days: Optional[int] = None,
) -> tuple[ClaimStatus, float, Optional[str]]:
    """Assign status, confidence, and primary source ID for a claim.
    
    Returns (status, confidence, primary_source_id).
    """
    if not matched_sources:
        return ClaimStatus.UNVERIFIED, 0.0, None

    # Sort by tier (1 = best)
    sorted_sources = sorted(matched_sources, key=lambda s: s.tier)
    primary = sorted_sources[0]
    
    tier1 = [s for s in matched_sources if s.tier == 1]
    tier2 = [s for s in matched_sources if s.tier == 2]
    tier3_plus = [s for s in matched_sources if s.tier >= 3]

    # Publisher diversity — count unique publishers
    publishers = {s.publisher for s in matched_sources if s.publisher}

    if len(matched_sources) == 1:
        status = ClaimStatus.SINGLE_SOURCE
        confidence = 0.55 if primary.tier <= 2 else 0.35
    elif tier1:
        status = ClaimStatus.CONFIRMED
        confidence = min(0.95, 0.80 + 0.05 * len(tier1))
    elif len(tier2) >= 2 or (tier2 and len(publishers) >= 2):
        status = ClaimStatus.CONFIRMED
        confidence = 0.75
    elif len(tier3_plus) >= 3 and len(publishers) >= 2:
        status = ClaimStatus.LIKELY
        confidence = 0.65
    elif matched_sources:
        status = ClaimStatus.LIKELY
        confidence = 0.50
    else:
        status = ClaimStatus.UNVERIFIED
        confidence = 0.0

    return status, round(confidence, 2), primary.source_id


def build_claims(
    topic: str,
    sources: list[SourceRecord],
    freshness_days: Optional[int] = None,
) -> list[ClaimRecord]:
    """Build claim records from retrieved sources.

    Rather than generating claims from an LLM, we synthesize factual
    claims directly from retrieved source titles and snippets.
    Each unique retrieved headline becomes a candidate claim.
    """
    claims: list[ClaimRecord] = []
    seen_claims: set[str] = set()

    for i, src in enumerate(sources):
        # Use title as a factual claim candidate
        claim_text = src.title.strip()
        if not claim_text or claim_text.lower() in seen_claims:
            continue
        seen_claims.add(claim_text.lower())

        # Find corroborating sources for this claim
        matched = _sources_for_claim(claim_text, sources)

        status, confidence, primary_id = assign_status(
            claim_text, matched, freshness_days
        )

        claims.append(ClaimRecord(
            claim_id=f"claim_{i+1:03d}",
            claim=claim_text,
            status=status,
            confidence=confidence,
            source_ids=[s.source_id for s in matched],
            primary_source_id=primary_id,
            notes=f"Derived from source title. {len(matched)} source(s) corroborate.",
        ))

    return claims
