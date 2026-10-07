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
from typing import Sequence
from ..phase10.models import ResearchPack, StoryRecord
from .models import ScriptArtifact, ScriptFormat, ScriptSection, ScriptScore
from .story_selector import select_stories_for_script

WORDS_PER_SECOND = 2.6


def _estimate_duration(text: str) -> float:
    words = len(text.split())
    pauses = text.count(".") * 0.35 + text.count(",") * 0.15 + text.count("?") * 0.4
    return round(max(1.5, (words / WORDS_PER_SECOND) + pauses), 1)


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


def generate_shorts_script(
    topic: str,
    research_pack: ResearchPack,
    channel_name: str = "AI Simplified Lab",
) -> ScriptArtifact:
    """Generate a high-retention, 35-50s YouTube Shorts script in AI Simplified Lab voice."""
    hook_story, stories = select_stories_for_script(research_pack, ScriptFormat.SHORTS)
    topic_clean = topic.strip()
    topic_lower = topic_clean.lower()

    sections: list[ScriptSection] = []

    # 1. THE HOOK (First 3 Seconds): Immediate curiosity & high energy
    if "robot" in topic_lower or "astra" in topic_lower:
        hook_text = "Warehouse robots are getting smarter fast."
        hook_emphasis = ["ROBOTS", "SMARTER", "FAST"]
    elif "hardware" in topic_lower or "chip" in topic_lower:
        hook_text = "AI chip engineering just took a massive leap."
        hook_emphasis = ["CHIP", "MASSIVE", "LEAP"]
    elif "agent" in topic_lower:
        hook_text = "Autonomous AI agents just entered real production."
        hook_emphasis = ["AUTONOMOUS", "REAL", "PRODUCTION"]
    elif any(k in topic_lower for k in ("term", "token", "concept", "attention", "embedding", "glossary", "basics", "explained")):
        hook_text = "Ever wonder how AI actually understands human language?"
        hook_emphasis = ["HOW", "AI", "UNDERSTANDS", "LANGUAGE"]
    else:
        hook_text = f"Something unprecedented just happened in {topic_clean}."
        hook_emphasis = ["UNPRECEDENTED", "HAPPENED", "BREAKTHROUGH"]

    hook_dur = _estimate_duration(hook_text)
    sections.append(ScriptSection(
        section_id="sec_01",
        scene_id="scene_01",
        role="hook",
        spoken_text=hook_text,
        estimated_duration_seconds=hook_dur,
        word_count=len(hook_text.split()),
        emphasis_words=hook_emphasis,
        visual_intent="emerge",
        primary_subject=topic_clean,
        retention_trigger="immediate_curiosity",
    ))

    # 2. LEAD STORY: Concrete technological advance
    lead_text = _synthesize_lead_sentence(hook_story, topic_clean)
    lead_dur = _estimate_duration(lead_text)
    sections.append(ScriptSection(
        section_id="sec_02",
        scene_id="scene_02",
        role="lead_story",
        spoken_text=lead_text,
        estimated_duration_seconds=lead_dur,
        word_count=len(lead_text.split()),
        emphasis_words=["TOKENS", "VECTORS", "EMBEDDINGS"] if "token" in lead_text.lower() else ["COORDINATE", "INDUSTRIAL", "PRECISION"],
        visual_intent="reveal",
        primary_subject="Tokens & Vector Embeddings" if any(k in topic_lower for k in ("term", "token", "concept", "attention", "embedding", "glossary")) else "Industrial Automation",
        retention_trigger="concrete_breakthrough",
    ))

    # 3. ESCALATION: How it works & why it matters
    s2 = stories[1] if len(stories) > 1 else hook_story
    escalation_text = _synthesize_escalation_sentence(s2, topic_clean)
    esc_dur = _estimate_duration(escalation_text)
    sections.append(ScriptSection(
        section_id="sec_03",
        scene_id="scene_03",
        role="escalation",
        spoken_text=escalation_text,
        estimated_duration_seconds=esc_dur,
        word_count=len(escalation_text.split()),
        emphasis_words=["ATTENTION", "WEIGHTS", "MATHEMATICAL"] if "attention" in escalation_text.lower() else ["ADAPT", "DYNAMICALLY", "REAL_TIME"],
        visual_intent="dramatic_cut",
        primary_subject="Multi-Head Self-Attention" if any(k in topic_lower for k in ("term", "token", "concept", "attention", "embedding", "glossary")) else "Autonomous Fleet",
        retention_trigger="pattern_interrupt",
    ))

    # 4. IMPLICATION & STAKES: The broader impact
    if "robot" in topic_lower or "warehouse" in topic_lower:
        impl_text = "That means facilities can move inventory faster, with fewer delays and less human intervention."
        impl_words = ["INVENTORY", "FASTER", "FEWER_DELAYS"]
    elif any(k in topic_lower for k in ("term", "token", "concept", "attention", "embedding", "glossary", "basics", "explained")):
        impl_text = "By mastering tokens, vectors, and attention, you understand the core mechanics powering all modern frontier models."
        impl_words = ["MASTERING", "TOKENS", "VECTORS", "ATTENTION", "MODELS"]
    else:
        impl_text = "This fundamentally rewrites how software coordinates with physical real-world operations."
        impl_words = ["REWRITES", "PHYSICAL", "OPERATIONS"]

    impl_dur = _estimate_duration(impl_text)
    sections.append(ScriptSection(
        section_id="sec_04",
        scene_id="scene_04",
        role="implication",
        spoken_text=impl_text,
        estimated_duration_seconds=impl_dur,
        word_count=len(impl_text.split()),
        emphasis_words=impl_words,
        visual_intent="scale_up",
        primary_subject="Transformer Architecture & Output" if any(k in topic_lower for k in ("term", "token", "concept", "attention", "embedding", "glossary")) else "Logistics Scale",
        retention_trigger="high_stakes",
    ))

    # 5. PUNCHY CLIFFHANGER & BRANDED CTA
    cta_text = f"And this is just the beginning. Subscribe to {channel_name} for daily frontier AI briefings."
    cta_dur = _estimate_duration(cta_text)
    sections.append(ScriptSection(
        section_id="sec_05",
        scene_id="scene_05",
        role="cta",
        spoken_text=cta_text,
        estimated_duration_seconds=cta_dur,
        word_count=len(cta_text.split()),
        emphasis_words=["BEGINNING", "SUBSCRIBE", "DAILY"],
        visual_intent="branded_callout",
        primary_subject=channel_name,
        retention_trigger="conversion_lock",
    ))

    total_words = sum(s.word_count for s in sections)
    total_dur = sum(s.estimated_duration_seconds for s in sections)
    scoring = score_script(sections)

    grounded_claims = [_clean_headline(s.headline) for s in stories]

    return ScriptArtifact(
        topic=topic_clean,
        format=ScriptFormat.SHORTS,
        hook_story_id=hook_story.story_id,
        sections=sections,
        total_duration_seconds=total_dur,
        total_word_count=total_words,
        scoring=scoring,
        grounded_claims=grounded_claims,
        channel_name=channel_name,
    )


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
