"""Research Director — coordinates real source collection, ranking, synthesis, and validation.

Implements StageHandler for the 'research' stage.
Never fabricates sources. If external research is needed but no search provider
is configured, explicitly blocks with RESEARCH_PROVIDER_UNAVAILABLE.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field

import models
from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ProducerKind
from schemas.models.production import ProductionState
from production.stage_registry import StageHandler, StageHandlerResult, StageResultStatus
from stages.research.source_collector import (
    ResearchSourceProvider,
    DirectUrlSourceProvider,
    ConfiguredSearchProvider,
    SourceRecord,
)
from stages.research.source_ranker import SourceRanker
from stages.research.research_prompts import RESEARCH_SYSTEM_PROMPT, build_research_prompt
from stages.research.research_validator import ResearchValidator, DEPTH_REQUIREMENTS


TIME_SENSITIVE_KEYWORDS = {
    "latest", "today", "this week", "recent", "newly launched",
    "current", "breaking", "news", "v2", "update", "announces", "just released",
}


class ResearchRequest(BaseModel):
    """Typed research request parameters."""
    production_id: str
    topic: str
    audience: str = "general_tech"
    platform: str = "youtube_shorts"
    content_type: str = "explainer"
    is_time_sensitive: bool = False
    source_urls: list[str] = Field(default_factory=list)
    research_depth: Literal["minimal", "standard", "deep"] = "standard"

    model_config = {"extra": "ignore"}


def is_topic_time_sensitive(topic: str) -> bool:
    """Detect if topic indicates breaking or current news."""
    t_lower = topic.lower()
    return any(kw in t_lower for kw in TIME_SENSITIVE_KEYWORDS)


class ResearchHandler:
    """Production stage handler for research stage."""

    def __init__(
        self,
        source_provider: ResearchSourceProvider | None = None,
        llm_caller: Any | None = None,
    ) -> None:
        self.source_provider = source_provider
        self.llm_caller = llm_caller or models.call_llm_json

    def _build_request(
        self,
        state: ProductionState,
        inputs: dict[str, ArtifactEnvelope],
        options: dict[str, Any],
    ) -> ResearchRequest:
        topic = str(state.metadata.get("topic") or options.get("topic") or "AI Technology")
        audience = str(options.get("audience") or state.metadata.get("audience") or "general_tech")
        platform = str(options.get("platform") or state.platform or "youtube_shorts")
        content_type = str(options.get("content_type") or "explainer")

        # Detect time sensitivity
        is_time_sensitive = bool(
            options.get("is_time_sensitive") or
            state.metadata.get("is_time_sensitive") or
            state.pipeline == "ai-news-short" or
            is_topic_time_sensitive(topic)
        )

        depth = str(options.get("research_depth") or ("deep" if state.pipeline == "ai-news-short" else "standard"))
        if depth not in ("minimal", "standard", "deep"):
            depth = "standard"

        # Explicit user-supplied URLs
        raw_urls = options.get("source_urls") or state.metadata.get("source_urls") or []
        if isinstance(raw_urls, str):
            raw_urls = [u.strip() for u in raw_urls.split(",") if u.strip()]

        return ResearchRequest(
            production_id=state.project_id,
            topic=topic,
            audience=audience,
            platform=platform,
            content_type=content_type,
            is_time_sensitive=is_time_sensitive,
            source_urls=list(raw_urls),
            research_depth=depth,
        )

    def run(
        self,
        stage_name: str,
        state: ProductionState,
        inputs: dict[str, ArtifactEnvelope],
        **kwargs: Any,
    ) -> StageHandlerResult:
        options = dict(kwargs.get("options") or {})
        req = self._build_request(state, inputs, options)

        collected_sources: list[SourceRecord] = []
        direct_provider = DirectUrlSourceProvider()

        # 1. Fetch direct URLs if specified
        for url in req.source_urls:
            rec = direct_provider.extract_content(url)
            if rec:
                rec.source_type = "user_direct"
                collected_sources.append(rec)

        # 2. Check if external search is required
        min_required = DEPTH_REQUIREMENTS[req.research_depth]["min_sources"]
        needs_search = len(collected_sources) < min_required

        if needs_search:
            search_prov = self.source_provider or ConfiguredSearchProvider()
            if not search_prov.is_available():
                return StageHandlerResult(
                    status=StageResultStatus.BLOCKED,
                    message=(
                        f"Research blocked: RESEARCH_PROVIDER_UNAVAILABLE. "
                        f"Topic {req.topic!r} requires at least {min_required} sources, "
                        f"but only {len(collected_sources)} direct URLs were provided and "
                        f"no external search API is configured."
                    ),
                    errors=["RESEARCH_PROVIDER_UNAVAILABLE"],
                )

            # Perform search
            search_query = f"{req.topic} AI latest overview documentation" if req.is_time_sensitive else f"{req.topic} AI architecture explanation"
            search_results = search_prov.search(search_query, limit=max(min_required * 2, 5))
            collected_sources.extend(search_results)

        if not collected_sources:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message=f"Research blocked: RESEARCH_EMPTY. Search for {req.topic!r} returned 0 sources.",
                errors=["RESEARCH_EMPTY"],
            )

        # 3. Quality ranking and deduplication
        ranker = SourceRanker(topic=req.topic, is_time_sensitive=req.is_time_sensitive)
        ranked_sources = ranker.rank_and_deduplicate(collected_sources)

        if len(ranked_sources) < min_required:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message=(
                    f"Research blocked: INSUFFICIENT_SOURCES. Gathered {len(ranked_sources)} "
                    f"usable sources, minimum {min_required} required for depth '{req.research_depth}'."
                ),
                errors=["INSUFFICIENT_SOURCES"],
            )

        # 4. LLM Synthesis
        prompt = build_research_prompt(
            topic=req.topic,
            audience=req.audience,
            platform=req.platform,
            sources=ranked_sources,
            depth=req.research_depth,
            is_time_sensitive=req.is_time_sensitive,
        )

        try:
            parsed_data, prov_name, model_name, tokens = self.llm_caller(
                prompt=prompt,
                system=RESEARCH_SYSTEM_PROMPT,
            )
        except Exception as exc:
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message=f"LLM research synthesis failed: {exc}",
                errors=[str(exc)],
            )

        # 5. Populate verified sources list in brief data
        parsed_data["sources"] = [s.model_dump() for s in ranked_sources]
        parsed_data["topic"] = req.topic
        parsed_data["audience"] = req.audience

        # 6. Validate brief
        validator = ResearchValidator(depth=req.research_depth, is_time_sensitive=req.is_time_sensitive)
        validation_report = validator.validate(parsed_data)

        if validation_report.status == "rejected":
            error_msgs = [f"[{f.code}] {f.message}" for f in validation_report.findings if f.severity == "critical"]
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message="Research brief failed factual validation: " + "; ".join(error_msgs),
                errors=error_msgs,
                warnings=[f.message for f in validation_report.findings if f.severity == "warning"],
            )

        # 7. Record provenance
        prompt_hash = f"sha256:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()}"
        est_cost = round(tokens * 0.000001, 6)

        producer = ProducerInfo(
            kind=ProducerKind.LLM,
            provider=prov_name,
            model=model_name,
            prompt_hash=prompt_hash,
            estimated_cost=est_cost,
        )

        warnings = [f.message for f in validation_report.findings if f.severity == "warning"]

        return StageHandlerResult(
            status=StageResultStatus.READY,
            data=parsed_data,
            producer=producer,
            warnings=warnings,
            message=(
                f"Research brief completed with {len(ranked_sources)} sources, "
                f"{len(parsed_data.get('facts', []))} facts, and "
                f"{len(parsed_data.get('angles_discovered', []))} angles."
            ),
        )
