"""Research Validator and Review Contract.

Validation checks:
- source count
- source URL validity
- duplicate sources
- claim/source linkage (UNSUPPORTED_CLAIM)
- fact count
- angle count
- missing evidence
- time-sensitive freshness
- hallucinated source metadata
- empty research

Returns structured findings with pass / warning / rejected review contract.
"""
from __future__ import annotations

import urllib.parse
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field


class ValidationFinding(BaseModel):
    code: str
    severity: Literal["critical", "warning", "info"]
    message: str
    claim: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    correction: str = ""


class ResearchReviewContract(BaseModel):
    source_quality: Literal["pass", "warning", "reject"]
    evidence_quality: Literal["pass", "warning", "reject"]
    freshness: Literal["pass", "warning", "reject"]


class ResearchValidationReport(BaseModel):
    status: Literal["pass", "warning", "rejected"]
    findings: list[ValidationFinding] = Field(default_factory=list)
    review: ResearchReviewContract
    depth_met: bool = True

    model_config = {"extra": "ignore"}


DEPTH_REQUIREMENTS = {
    "minimal": {"min_sources": 1, "min_facts": 2, "min_angles": 1},
    "standard": {"min_sources": 3, "min_facts": 3, "min_angles": 2},
    "deep": {"min_sources": 5, "min_facts": 5, "min_angles": 3},
}

SUSPICIOUS_DOMAINS = {"example.com", "fake.url", "placeholder.com", "test.com", "lorem.ipsum"}


class ResearchValidator:
    """Validates research artifacts against rigorous factual & provenance criteria."""

    def __init__(self, depth: str = "standard", is_time_sensitive: bool = False) -> None:
        self.depth = depth.lower() if depth in DEPTH_REQUIREMENTS else "standard"
        self.is_time_sensitive = is_time_sensitive
        self.reqs = DEPTH_REQUIREMENTS[self.depth]

    def validate(self, data: dict[str, Any]) -> ResearchValidationReport:
        findings: list[ValidationFinding] = []

        topic = data.get("topic", "")
        sources = data.get("sources", [])
        facts = data.get("facts", [])
        angles = data.get("angles_discovered", [])

        # 1. Empty research check
        if not sources or not facts:
            findings.append(
                ValidationFinding(
                    code="EMPTY_RESEARCH",
                    severity="critical",
                    message="Research brief contains no sources or no facts.",
                    correction="Collect real sources and extract factual claims.",
                )
            )
            return ResearchValidationReport(
                status="rejected",
                findings=findings,
                review=ResearchReviewContract(
                    source_quality="reject",
                    evidence_quality="reject",
                    freshness="reject",
                ),
                depth_met=False,
            )

        # 2. Source Count Check
        if len(sources) < self.reqs["min_sources"]:
            findings.append(
                ValidationFinding(
                    code="INSUFFICIENT_SOURCES",
                    severity="critical",
                    message=(
                        f"Research depth '{self.depth}' requires at least {self.reqs['min_sources']} "
                        f"sources, found {len(sources)}."
                    ),
                    correction=f"Gather at least {self.reqs['min_sources']} authoritative sources.",
                )
            )

        # 3. Source URL Validity and Suspicious/Fabricated Domains
        known_source_ids: set[str] = set()
        seen_urls: set[str] = set()
        stale_source_count = 0
        now = datetime.now(timezone.utc)

        for src in sources:
            sid = src.get("source_id", "")
            url = src.get("url", "").strip()
            title = src.get("title", "").strip()

            if sid:
                known_source_ids.add(sid)

            if not url or not (url.startswith("http://") or url.startswith("https://")):
                findings.append(
                    ValidationFinding(
                        code="INVALID_SOURCE_URL",
                        severity="critical",
                        message=f"Source {sid!r} has invalid URL {url!r}.",
                        source_ids=[sid] if sid else [],
                        correction="Ensure source URL is a well-formed http(s) URL.",
                    )
                )
                continue

            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            if domain in SUSPICIOUS_DOMAINS or "placeholder" in url:
                findings.append(
                    ValidationFinding(
                        code="FABRICATED_SOURCE_DETECTED",
                        severity="critical",
                        message=f"Source {sid!r} uses suspicious or placeholder domain: {domain}.",
                        source_ids=[sid] if sid else [],
                        correction="Do not fabricate sources; only real verified URLs are permitted.",
                    )
                )

            # Duplicate source check
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/").lower()
            if clean_url in seen_urls:
                findings.append(
                    ValidationFinding(
                        code="DUPLICATE_SOURCE",
                        severity="warning",
                        message=f"Duplicate source URL detected: {url}.",
                        source_ids=[sid] if sid else [],
                        correction="Deduplicate sources before brief generation.",
                    )
                )
            seen_urls.add(clean_url)

            # Freshness / Recency check
            pub_date = src.get("published_at")
            if pub_date:
                try:
                    dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    if (now - dt).days > 180:
                        stale_source_count += 1
                except Exception:
                    pass

        # 4. Time-sensitive freshness check
        if self.is_time_sensitive:
            if stale_source_count == len(sources) and len(sources) > 0:
                findings.append(
                    ValidationFinding(
                        code="STALE_SOURCES_FOR_CURRENT_TOPIC",
                        severity="critical",
                        message=(
                            f"Topic {topic!r} is time-sensitive, but all {len(sources)} "
                            f"sources are older than 180 days."
                        ),
                        correction="Gather current sources with recent publication dates.",
                    )
                )
            elif not any(src.get("published_at") for src in sources):
                findings.append(
                    ValidationFinding(
                        code="MISSING_PUBLICATION_DATES",
                        severity="warning",
                        message="Time-sensitive topic has sources without published_at timestamps.",
                        correction="Preserve original publication dates from sources.",
                    )
                )

        # 5. Fact Count Check
        if len(facts) < self.reqs["min_facts"]:
            findings.append(
                ValidationFinding(
                    code="INSUFFICIENT_FACTS",
                    severity="critical",
                    message=(
                        f"Research depth '{self.depth}' requires at least {self.reqs['min_facts']} "
                        f"facts, found {len(facts)}."
                    ),
                    correction=f"Extract at least {self.reqs['min_facts']} verifiable facts from sources.",
                )
            )

        # 6. Claim / Source Linkage (Crucial Anti-Hallucination Gate)
        for idx, fact in enumerate(facts, 1):
            if isinstance(fact, str):
                # Legacy or plain string fact: no source linkage attached
                findings.append(
                    ValidationFinding(
                        code="UNSUPPORTED_CLAIM",
                        severity="critical",
                        claim=fact,
                        source_ids=[],
                        message=f"Fact #{idx} has no linked source IDs.",
                        correction="Attach source_ids to all factual claims.",
                    )
                )
            elif isinstance(fact, dict):
                claim_text = fact.get("claim", "")
                src_ids = fact.get("source_ids", [])
                if not claim_text:
                    findings.append(
                        ValidationFinding(
                            code="EMPTY_CLAIM",
                            severity="critical",
                            message=f"Fact #{idx} has empty claim text.",
                            correction="Provide non-empty claim statement.",
                        )
                    )
                    continue

                if not src_ids:
                    findings.append(
                        ValidationFinding(
                            code="UNSUPPORTED_CLAIM",
                            severity="critical",
                            claim=claim_text,
                            source_ids=[],
                            message=f"Claim #{idx} {claim_text!r} has no supporting source_ids.",
                            correction="Remove claim or cite supporting source_ids.",
                        )
                    )
                else:
                    # Check if cited source_ids actually exist
                    missing_ids = [s for s in src_ids if s not in known_source_ids]
                    if missing_ids:
                        findings.append(
                            ValidationFinding(
                                code="HALLUCINATED_SOURCE_REFERENCE",
                                severity="critical",
                                claim=claim_text,
                                source_ids=missing_ids,
                                message=f"Claim #{idx} references non-existent sources {missing_ids}.",
                                correction="Only cite sources present in the brief sources list.",
                            )
                        )

        # 7. Angle Count Check
        if len(angles) < self.reqs["min_angles"]:
            findings.append(
                ValidationFinding(
                    code="INSUFFICIENT_ANGLES",
                    severity="critical",
                    message=(
                        f"Research depth '{self.depth}' requires at least {self.reqs['min_angles']} "
                        f"angles, found {len(angles)}."
                    ),
                    correction=f"Synthesize at least {self.reqs['min_angles']} distinct editorial angles.",
                )
            )

        # Determine overall status and review contract
        has_critical = any(f.severity == "critical" for f in findings)
        has_warning = any(f.severity == "warning" for f in findings)

        if has_critical:
            status = "rejected"
        elif has_warning:
            status = "warning"
        else:
            status = "pass"

        source_quality = (
            "reject" if any(f.code in ("INSUFFICIENT_SOURCES", "FABRICATED_SOURCE_DETECTED", "EMPTY_RESEARCH") for f in findings)
            else ("warning" if any(f.code in ("DUPLICATE_SOURCE",) for f in findings) else "pass")
        )
        evidence_quality = (
            "reject" if any(f.code in ("UNSUPPORTED_CLAIM", "INSUFFICIENT_FACTS", "HALLUCINATED_SOURCE_REFERENCE") for f in findings)
            else "pass"
        )
        freshness = (
            "reject" if any(f.code in ("STALE_SOURCES_FOR_CURRENT_TOPIC",) for f in findings)
            else ("warning" if any(f.code in ("MISSING_PUBLICATION_DATES",) for f in findings) else "pass")
        )

        return ResearchValidationReport(
            status=status,
            findings=findings,
            review=ResearchReviewContract(
                source_quality=source_quality,
                evidence_quality=evidence_quality,
                freshness=freshness,
            ),
            depth_met=not has_critical,
        )
