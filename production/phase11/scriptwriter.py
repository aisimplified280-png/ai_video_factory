"""Natural Script Synthesis Engine for Phase 11.

Generates human, conversational, high-retention narration for AI Simplified Lab:
- Never blindly pastes raw news headlines or release notes.
- Synthesizes clear, punchy, spoken English.
- Captivates viewers in the critical first 3 seconds.
- Explains real-world technical implications in accessible language.
- Structured rhythm: Hook -> Advance -> Escalation -> Stakes -> Branded CTA.
"""
from __future__ import annotations

import re
from typing import Any, Optional, Sequence
from ..phase10.models import ResearchPack, StoryRecord
from .models import ScriptArtifact, ScriptFormat, ScriptSection, ScriptScore
from .story_selector import select_stories_for_script

WORDS_PER_SECOND = 2.6


def _estimate_duration(text: str) -> float:
    words = len(text.split())
    pauses = text.count(".") * 0.35 + text.count(",") * 0.15 + text.count("?") * 0.4
    return round(max(1.5, (words / WORDS_PER_SECOND) + pauses), 1)


# ---------------------------------------------------------------------------
# Dynamic scene structure — the scene count is earned from the target runtime,
# never from a fixed "5 scenes" / "10 scenes" template (<3 minutes alone means
# nothing: a 90s brief and a 180s brief do not deserve the same scene count).
# ---------------------------------------------------------------------------

def scene_count_for_duration(duration: float) -> int:
    """Scenes a narration earns from its runtime (~1 beat per 8s short / 12s extended)."""
    if duration >= 90.0:
        return max(6, min(14, int(round(duration / 12.0))))
    return max(5, min(7, int(round(duration / 8.0))))


_MIDDLE_ROLES = ("mechanism", "escalation", "pipeline")

_ROLE_INTENT = {
    "hook": "emerge",
    "lead_story": "reveal",
    "mechanism": "flow",
    "escalation": "dramatic_cut",
    "pipeline": "connect",
    "implication": "scale_up",
    "cta": "branded_callout",
}


def role_sequence(scene_count: int) -> list[str]:
    """hook -> lead -> middle beats (cycled) -> implication (stakes) -> cta."""
    n = max(2, scene_count)
    if n == 2:
        return ["hook", "cta"]
    if n == 3:
        return ["hook", "lead_story", "cta"]
    middle = [_MIDDLE_ROLES[i % len(_MIDDLE_ROLES)] for i in range(n - 4)]
    return ["hook", "lead_story", *middle, "implication", "cta"]


# Fabrication / hype markers the LLM narration must never contain (§26: no
# invented events, no empty hype). A hit rejects the whole sample.
_EDITORIAL_RED_FLAGS = (
    "research team", "released a new version", "released a new", "breakthrough",
    "revolution", "revolutionize", "revolutionary", "game-changing",
    "in this video", "we will explore",
    "intense research and debate", "according to the research",
    # filler / unverifiable claims
    "powerful ai", "cutting-edge", "state of the art", "state-of-the-art",
    "never before", "is not just",
)


def _accept_llm_script(
    data: object,
    *,
    scene_count: int,
    target_words: int,
    channel_name: str,
) -> Optional[list[dict[str, Any]]]:
    """Structural + editorial gate for raw LLM output.

    Position owns the role sequence; the model owns the prose. Returns
    normalized section dicts, or None (with the failing gate printed) when
    the sample must be discarded.
    """
    def _reject(reason: str) -> None:
        print(f"  -> [Script Intelligence Gate] rejected LLM sample: {reason}")
        return None

    if not isinstance(data, dict) or not isinstance(data.get("sections"), list):
        return _reject("no sections array")
    raw = data["sections"]
    if len(raw) != scene_count:
        return _reject(f"expected {scene_count} sections, got {len(raw)}")

    joined = " ".join(str(s.get("spoken_text", "")) for s in raw if isinstance(s, dict)).lower()
    hit = next((flag for flag in _EDITORIAL_RED_FLAGS if flag in joined), None)
    if hit:
        return _reject(f"red-flag wording {hit!r}")

    roles = role_sequence(scene_count)
    per_budget = max(8, target_words / scene_count)
    min_words = max(5, int(per_budget * 0.45))
    max_words = int(per_budget * 2.0)

    normalized: list[dict[str, Any]] = []
    total = 0
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            return _reject(f"section {idx + 1} is not an object")
        spoken = str(item.get("spoken_text", "")).strip()
        words = spoken.split()
        # Placeholder / echo rejection ("...", "(narration)", truncations).
        if not spoken or spoken in {"...", "…"} or "<" in spoken or ">" in spoken:
            return _reject(f"section {idx + 1} placeholder text {spoken[:24]!r}")
        if not (min_words <= len(words) <= max_words):
            return _reject(
                f"section {idx + 1} has {len(words)}w outside {min_words}-{max_words}w budget"
            )
        total += len(words)
        normalized.append({
            "role": roles[idx],
            "spoken_text": spoken,
            "emphasis_words": [str(w).upper() for w in item.get("emphasis_words", [])[:3]],
            "primary_subject": str(item.get("primary_subject", "")).strip(),
            "visual_intent": str(item.get("visual_intent", "")).strip() or _ROLE_INTENT.get(roles[idx], "reveal"),
        })

    if not (target_words * 0.70 <= total <= target_words * 1.60):
        return _reject(
            f"total {total}w outside {int(target_words * 0.70)}-{int(target_words * 1.60)}w bounds"
        )
    if "subscribe" not in normalized[-1]["spoken_text"].lower():
        return _reject("cta missing subscribe ask")
    if channel_name.lower() not in normalized[-1]["spoken_text"].lower():
        return _reject(f"cta missing channel name {channel_name!r}")
    return normalized


def _sections_to_artifact(
    topic: str,
    sections: list[ScriptSection],
    research_pack: ResearchPack,
    channel_name: str,
    fmt: ScriptFormat = ScriptFormat.SHORTS,
) -> ScriptArtifact:
    total_words = sum(s.word_count for s in sections)
    total_dur = sum(s.estimated_duration_seconds for s in sections)
    hook_story, stories = select_stories_for_script(research_pack, fmt)
    return ScriptArtifact(
        topic=topic.strip(),
        format=fmt,
        hook_story_id=hook_story.story_id,
        sections=sections,
        total_duration_seconds=round(total_dur, 1),
        total_word_count=total_words,
        scoring=score_script(sections),
        grounded_claims=[_clean_headline(s.headline) for s in stories[:3]],
        channel_name=channel_name,
    )


# Honest structural beats for the procedural fallback: they describe the shape
# of the explanation (flow, focus, scale, stakes) without inventing a single
# event, number, or claim about the topic. Distinct lines -> no repetition at
# the maximum scene count (14 scenes -> 10 middle beats).
_FALLBACK_BEATS = [
    "The core mechanism is simple: each part does one job, then hands off to the next.",
    "Run those parts together and the behavior changes — that interaction is the story.",
    "Follow the flow end to end: input moves through each stage and comes out as a result.",
    "Zoom in on the piece doing the heavy lifting — it is smaller than it looks.",
    "Compare the two sides: what stays fixed, and what adapts as conditions change.",
    "Scale it up: the same pattern repeats across thousands of requests at once.",
    "Where it breaks, it breaks in an interesting way — and the fix is architectural.",
    "Strip the jargon away and you are left with a decision: route, filter, or store.",
    "Each step here maps to a real component engineers work with daily.",
    "Hold on to this picture — every later idea builds on top of it.",
]


def _topic_subject(topic: str) -> str:
    """Short grammatical subject for prose interpolation: the first clause of
    the topic. Works for one-word inputs ('RAG') and sentence topics alike
    ('how RAG retrieves answers: chunking, ...' -> 'how RAG retrieves answers').
    """
    head = re.split(r"[:;,—–-]", topic, maxsplit=1)[0].strip()
    words = head.split()
    if len(words) > 7:
        words = words[:7]
    return " ".join(words) or topic.strip()


def _procedural_sections(
    topic: str,
    research_pack: ResearchPack,
    channel_name: str,
    scene_count: int,
) -> list[ScriptSection]:
    """Honest, topic-slotted scaffolding used when LLM synthesis is unavailable.

    research_pack feeds provenance (hook story / grounded claims) upstream in
    _sections_to_artifact; here the prose stays structural so it is
    grammatical for ANY topic shape — a single word or a full sentence.
    """
    topic_clean = topic.strip()
    roles = role_sequence(scene_count)
    subject = _topic_subject(topic_clean)

    stop = {"the", "of", "a", "an", "and", "for", "with", "that", "this",
            "from", "into", "how", "when", "what", "why", "process"}
    topic_core = [w for w in re.findall(r"[A-Za-z0-9]+", subject) if w.lower() not in stop][:3]
    if not topic_core:
        topic_core = ["EXPLAINED", "SIMPLY", "CLEARLY"]

    texts: dict[str, str] = {
        "hook": f"Let's break down {subject} — clearly, simply, without the jargon.",
        "lead_story": "Here is the core question: how does this actually work, start to finish?",
        "implication": "Once it clicks, you will recognize this pattern across modern AI systems.",
        "cta": f"And this is just the beginning. Subscribe to {channel_name} for daily frontier AI briefings.",
    }

    beat_idx = 0
    sections: list[ScriptSection] = []
    for idx, role in enumerate(roles):
        if role in texts:
            text = texts[role]
        else:
            text = _FALLBACK_BEATS[beat_idx % len(_FALLBACK_BEATS)]
            beat_idx += 1
        emphasis = (
            [w.upper() for w in topic_core] if role in ("hook", "lead_story")
            else ["BREAK_DOWN", "SUBSCRIBE", "DAILY"] if role == "cta"
            else ["EACH", "STEP", "NEXT"] if role in ("mechanism", "pipeline")
            else ["CONNECTS", "INTERACTION", "SCALE"] if role == "escalation"
            else ["PATTERN", "RECOGNIZE", "SYSTEMS"]
        )
        sections.append(ScriptSection(
            section_id=f"sec_{idx + 1:02d}",
            scene_id=f"scene_{idx + 1:02d}",
            role=role,
            spoken_text=text,
            estimated_duration_seconds=_estimate_duration(text),
            word_count=len(text.split()),
            emphasis_words=emphasis[:3],
            visual_intent=_ROLE_INTENT.get(role, "reveal"),
            primary_subject=channel_name if role == "cta" else topic_clean,
            retention_trigger="immediate_curiosity" if role == "hook" else "conversion_lock" if role == "cta" else "fast_pacing",
        ))
    return sections


def resolve_working_topic(topic: str) -> str:
    """Upscale a very short (1-2 word) topic into a concrete working topic.

    One-word inputs ("RAG", "transformers") are too thin to research, script,
    or ground visuals against. The LLM expands them into a specific,
    explainable one-sentence topic; an honest structural fallback keeps the
    pipeline alive with no LLM at all.
    """
    cleaned = topic.strip()
    if len(cleaned.split()) > 2:
        return cleaned
    prompt = (
        'You are the topic editor for "AI Simplified Lab", an AI/technology explainer channel. '
        "Expand this video topic into a specific, concrete one-sentence working topic for a short explainer video. "
        "Interpret it as an AI/technology subject. Name the actual mechanism or pieces the video will explain "
        '(for example "naive rag" -> "how naive RAG retrieves answers: chunking, embeddings, and top-k search"). '
        "No invented news, no hype, no events. "
        f'Topic: "{cleaned}". '
        'Return JSON only: {"working_topic": "the expanded topic"}'
    )
    try:
        res = call_llm_json(prompt)
        if isinstance(res, dict):
            wt = str(res.get("working_topic", "")).strip()
            wt_words = wt.split()
            if 6 <= len(wt_words) <= 26 and cleaned.lower() in wt.lower():
                return wt
    except Exception:
        pass
    return f"{cleaned} explained: how it works, step by step"


def _clean_headline(headline: str) -> str:
    """Strip news tickers, source attribution, and metadata boilerplate."""
    h = headline
    h = re.sub(r"^(special report|first shift|industry insights|breaking|report|exclusive):\s*", "", h, flags=re.IGNORECASE)
    h = re.sub(r"\s+[-|—]\s+[\w\s\.]+$", "", h)  # strip trailing publisher with space delimiter
    h = re.sub(r"\s*—\s*release notes.*$", "", h, flags=re.IGNORECASE)
    h = re.sub(r"[^\w\s\$\-\,\.]", "", h)
    return h.strip()


def _synthesize_lead_sentence(story: StoryRecord, topic: str) -> str:
    """Synthesize clean, natural spoken English explaining the primary development."""
    clean_title = _clean_headline(story.headline)
    text_lower = (clean_title + " " + story.summary + " " + topic).lower()

    if "robot" in text_lower or "manipulat" in text_lower or "arm" in text_lower or "astra" in text_lower:
        if "fleet" in text_lower or "coordinate" in text_lower or "warehouse" in text_lower:
            return "A new system can now coordinate entire fleets of robots instead of controlling them one at a time."
        if "benchmark" in text_lower or "crush" in text_lower or "speed" in text_lower:
            return "New benchmark data reveals frontier models manipulating physical objects with unprecedented speed and precision."
        return "Advanced neural networks can now directly control physical robots with real-time sensor feedback."
    elif "chip" in text_lower or "hardware" in text_lower or "wafer" in text_lower:
        return "A new architecture breakthrough allows AI accelerators to process reasoning models at a fraction of the power."
    elif any(k in text_lower for k in ("term", "token", "embedding", "attention", "transformer", "neural", "concept")):
        return "It all starts with tokens: text is shattered into numerical fragments and projected into high-dimensional vector embeddings."
    elif "agent" in text_lower or "software" in text_lower:
        return "Autonomous software agents are now executing multi-step production pipelines without human intervention."
    else:
        return f"A new system can now coordinate frontier {topic} workflows in live production environments."


def _synthesize_escalation_sentence(story: StoryRecord, topic: str) -> str:
    """Synthesize narrative escalation showing operational impact."""
    clean_title = _clean_headline(story.headline)
    text_lower = (clean_title + " " + story.summary + " " + topic).lower()

    if "warehouse" in text_lower or "logistics" in text_lower or "fleet" in text_lower or "robot" in text_lower:
        return "Instead of rigid pre-programmed routines, these machines adapt dynamically to moving obstacles and inventory shifts."
    elif "chip" in text_lower or "hardware" in text_lower:
        return "By eliminating memory bottlenecks on silicon, latency drops low enough for instant local decision-making."
    elif any(k in text_lower for k in ("term", "token", "embedding", "attention", "transformer", "concept")):
        return "Through multi-head self-attention, the neural network calculates dynamic mathematical weights between every single token simultaneously."
    elif "agent" in text_lower:
        return "Instead of basic single-turn prompts, these systems debug errors and adjust their strategy on the fly."
    else:
        return "Instead of isolated prototypes, these autonomous systems are entering live production environments right now."


try:
    from ..llm_client import call_llm_json, bust_llm_cache
except Exception:
    try:
        from production.llm_client import call_llm_json, bust_llm_cache
    except Exception:
        from llm_client import call_llm_json, bust_llm_cache


def _llm_synthesize_shorts_script(
    topic: str,
    research_pack: ResearchPack,
    channel_name: str = "AI Simplified Lab",
    target_duration: float = 30.0,
) -> Optional[ScriptArtifact]:
    """Use active LLM to generate authentic, topic-specific narration grounded in research."""
    try:
        # ~2.4 spoken words per second, matching the procedural estimator.
        scene_count = scene_count_for_duration(target_duration)
        roles = role_sequence(scene_count)
        target_words = max(55, int(round(target_duration * 2.4)))
        per_budget = max(8, int(round(target_words / scene_count)))
        story_context = []
        for s in (research_pack.stories or [])[:4]:
            story_context.append(f"- Headline: {s.headline}\n  Summary: {s.summary}")
        context_str = "\n".join(story_context) if story_context else "No prior news stories found."

        cta_line = f"And this is just the beginning. Subscribe to {channel_name} for daily frontier AI briefings."
        role_lines = "\n".join(
            f'   - Scene {i + 1}: role "{role}"'
            + (" — a gripping 3-second opener naming the specific idea." if role == "hook"
               else f' — MUST be copied exactly: "{cta_line}"' if role == "cta"
               else f" — one concrete idea in {per_budget} words (±40%): mechanism, contrast, or stakes.")
            for i, role in enumerate(roles)
        )
        prompt = f"""You are the lead tech scriptwriter for "{channel_name}", an elite channel breaking down AI models, software architectures, algorithms, and developer tools.
Write an authentic, highly engaging {scene_count}-scene YouTube Shorts script (about {target_duration:.0f} seconds) for: "{topic}".

Verified Research Context:
{context_str}

CRITICAL EDITORIAL RULES:
1. Real spoken English only — never placeholder text such as "..." or "(narration)". Every scene is finished narration.
2. NO hype and NO invented events: never use words like breakthrough, revolutionary, game-changing, revolutionize; never mention research teams, product releases, benchmark numbers, or events that did not happen.
3. If the topic is a concept, architecture, or technique, explain how it actually works — real steps, components, comparisons, trade-offs (concrete verbs like split, embed, search, rank, assemble).
4. If the topic is software/models, talk about the software — never physical warehouse robots.
5. THE WORD BUDGET IS STRICT: every scene is {per_budget} words (within ±40%), and the whole script totals about {target_words} words. Count your words before you answer.
6. Never expand or guess acronyms (RAG, MCP, LLM, BPE): use them exactly as written, with no parenthetical definitions — a wrong expansion is worse than none.
7. No filler adjectives (powerful, cutting-edge, amazing, incredible) — show what the thing DOES with concrete verbs and specifics instead.
8. Scene roles in this exact order: {", ".join(roles)}.
{role_lines}

Output a JSON object with a "sections" array of exactly {scene_count} entries, one per role, in order.
Each entry has exactly these keys: "role" (copy from the list above), "spoken_text" (the finished narration), "primary_subject" (a short 2-4 word subject name), "visual_intent" (one of: emerge, reveal, flow, dramatic_cut, connect, scale_up, branded_callout), "emphasis_words" (3 short uppercase words)."""
        normalized = None
        for _attempt in range(1, 4):
            data = call_llm_json(prompt)
            normalized = _accept_llm_script(
                data,
                scene_count=scene_count,
                target_words=target_words,
                channel_name=channel_name,
            )
            if normalized is not None:
                break
            # Never re-serve a rejected generation: bust the cache entry so
            # the next attempt asks the model for a fresh sample.
            bust_llm_cache(prompt)
        if normalized is None:
            print("  -> [Script Intelligence Warning] LLM script failed editorial/structural checks after 3 attempts; using procedural fallback.")
            return None

        sections: list[ScriptSection] = []
        for idx, item in enumerate(normalized):
            spoken = item["spoken_text"]
            sections.append(ScriptSection(
                section_id=f"sec_{idx + 1:02d}",
                scene_id=f"scene_{idx + 1:02d}",
                role=item["role"],
                spoken_text=spoken,
                estimated_duration_seconds=_estimate_duration(spoken),
                word_count=len(spoken.split()),
                emphasis_words=item["emphasis_words"] or ["FRONTIER", "AI", "SYSTEM"],
                visual_intent=item["visual_intent"],
                primary_subject=item["primary_subject"] or topic.strip(),
                retention_trigger=(
                    "immediate_curiosity" if idx == 0
                    else "conversion_lock" if idx == len(normalized) - 1
                    else "fast_pacing"
                ),
            ))
        total_words = sum(s.word_count for s in sections)
        print(f"  -> [Script Intelligence] Synthesized authentic narration via LLM ({len(sections)} scenes, {total_words} words).")
        return _sections_to_artifact(topic, sections, research_pack, channel_name)
    except Exception as exc:
        print(f"  -> [Script Intelligence Warning] LLM generation failed ({exc}); using procedural fallback.")
    return None


def _generate_extended_duration_script(
    topic: str,
    research_pack: ResearchPack,
    channel_name: str = "AI Simplified Lab",
    target_duration: float = 120.0,
) -> ScriptArtifact:
    """Extended YouTube Short (90s-180s): LLM synthesis first, honest structural fallback.

    Scene count follows the runtime (scene_count_for_duration): a 3-minute
    brief earns more scenes than a 90s one — neither is a fixed template.
    """
    llm_script = _llm_synthesize_shorts_script(
        topic, research_pack, channel_name, target_duration=target_duration
    )
    if llm_script:
        return llm_script

    print("  -> [Script Intelligence Fallback] Using procedural heuristic fallback template.")
    scene_count = scene_count_for_duration(target_duration)
    sections = _procedural_sections(topic, research_pack, channel_name, scene_count)
    return _sections_to_artifact(topic, sections, research_pack, channel_name)


def generate_shorts_script(
    topic: str,
    research_pack: ResearchPack,
    channel_name: str = "AI Simplified Lab",
    target_duration: float = 30.0,
) -> ScriptArtifact:
    """Generate a high-retention YouTube Shorts script in AI Simplified Lab voice (supports up to 180s / 3 mins)."""
    if target_duration >= 90.0:
        return _generate_extended_duration_script(topic, research_pack, channel_name, target_duration=target_duration)

    # 1. Attempt authentic LLM synthesis first
    llm_script = _llm_synthesize_shorts_script(topic, research_pack, channel_name, target_duration=target_duration)
    if llm_script:
        return llm_script

    # 2. Procedural heuristic fallback if the LLM is offline or the sample
    #    failed the editorial/structural gates: honest, topic-slotted
    #    scaffolding that invents no events, numbers, or claims.
    print("  -> [Script Intelligence Fallback] Using procedural heuristic fallback template.")
    scene_count = scene_count_for_duration(target_duration)
    sections = _procedural_sections(topic, research_pack, channel_name, scene_count)
    return _sections_to_artifact(topic, sections, research_pack, channel_name)


def generate_longform_script(
    topic: str,
    research_pack: ResearchPack,
    channel_name: str = "AI Simplified Lab",
) -> ScriptArtifact:
    """Generate a multi-chapter long-form video script."""
    hook_story, stories = select_stories_for_script(research_pack, ScriptFormat.LONG_FORM)
    sections: list[ScriptSection] = []

    intro = f"Frontier AI systems just hit a major inflection point in {topic}. In this breakdown, we examine the engineering shifts and what they mean for the industry."
    sections.append(ScriptSection(
        section_id="sec_01",
        scene_id="scene_01",
        role="hook",
        spoken_text=intro,
        estimated_duration_seconds=_estimate_duration(intro),
        word_count=len(intro.split()),
        emphasis_words=["INFLECTION", "BREAKDOWN", "ENGINEERING"],
        visual_intent="reveal",
        primary_subject=topic,
    ))

    for idx, story in enumerate(stories, start=2):
        clean_headline = _clean_headline(story.headline)
        body = f"Chapter {idx - 1}: {_synthesize_lead_sentence(story, topic)} {_synthesize_escalation_sentence(story, topic)}"
        sections.append(ScriptSection(
            section_id=f"sec_{idx:02d}",
            scene_id=f"scene_{idx:02d}",
            role=f"chapter_{idx - 1}",
            spoken_text=body,
            estimated_duration_seconds=_estimate_duration(body),
            word_count=len(body.split()),
            emphasis_words=["CHAPTER", "ADVANCE", "DEPLOYMENT"],
            visual_intent="focus",
            primary_subject=clean_headline[:40],
        ))

    cta = f"Which of these developments do you think is most disruptive? Drop your thoughts below and subscribe to {channel_name} for weekly frontier AI breakdowns."
    cta_idx = len(sections) + 1
    sections.append(ScriptSection(
        section_id=f"sec_{cta_idx:02d}",
        scene_id=f"scene_{cta_idx:02d}",
        role="cta",
        spoken_text=cta,
        estimated_duration_seconds=_estimate_duration(cta),
        word_count=len(cta.split()),
        emphasis_words=["DISRUPTIVE", "SUBSCRIBE", "WEEKLY"],
        visual_intent="branded_callout",
        primary_subject=channel_name,
    ))

    total_words = sum(s.word_count for s in sections)
    total_dur = sum(s.estimated_duration_seconds for s in sections)
    scoring = score_script(sections)

    return ScriptArtifact(
        topic=topic,
        format=ScriptFormat.LONG_FORM,
        hook_story_id=hook_story.story_id,
        sections=sections,
        total_duration_seconds=total_dur,
        total_word_count=total_words,
        scoring=scoring,
        grounded_claims=[_clean_headline(s.headline) for s in stories],
        channel_name=channel_name,
    )


def score_script(sections: Sequence[ScriptSection]) -> ScriptScore:
    """Evaluate script retention, hook strength, and subscriber conversion."""
    if not sections:
        return ScriptScore(retention_score=0.0, hook_strength_score=0.0, subscriber_conversion_score=0.0)

    first_sec = sections[0]
    first_text = first_sec.spoken_text.lower()
    banned_openings = ["welcome back", "hello everyone", "in this video", "today we are", "hey guys"]
    has_banned = any(b in first_text for b in banned_openings)
    has_punchy_hook = any(w in first_text for w in ["smarter", "fast", "unprecedented", "massive", "robots", "leap", "change"])

    hook_score = 0.96 if (not has_banned and has_punchy_hook) else 0.50 if has_banned else 0.82

    avg_dur = sum(s.estimated_duration_seconds for s in sections) / len(sections)
    pacing_ok = 2.5 <= avg_dur <= 10.0
    all_have_emphasis = all(len(s.emphasis_words) >= 2 for s in sections)
    retention_score = 0.94 if (pacing_ok and all_have_emphasis) else 0.80

    last_sec = sections[-1]
    has_subscribe = "subscribe" in last_sec.spoken_text.lower()
    sub_score = 0.95 if has_subscribe else 0.40

    total_words = sum(s.word_count for s in sections)
    total_dur = max(1.0, sum(s.estimated_duration_seconds for s in sections))
    wpm = round((total_words / total_dur) * 60, 1)

    return ScriptScore(
        retention_score=round(retention_score, 2),
        hook_strength_score=round(hook_score, 2),
        subscriber_conversion_score=round(sub_score, 2),
        word_pacing_wpm=wpm,
    )
