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


try:
    from ..llm_client import call_llm_json
except Exception:
    try:
        from production.llm_client import call_llm_json
    except Exception:
        from llm_client import call_llm_json


def _llm_synthesize_shorts_script(
    topic: str,
    research_pack: ResearchPack,
    channel_name: str = "AI Simplified Lab",
) -> Optional[ScriptArtifact]:
    """Use active LLM to generate authentic, topic-specific narration grounded in research."""
    try:
        story_context = []
        for s in (research_pack.stories or [])[:4]:
            story_context.append(f"- Headline: {s.headline}\n  Summary: {s.summary}")
        context_str = "\n".join(story_context) if story_context else "No prior news stories found."

        prompt = f"""You are the lead tech scriptwriter for "{channel_name}", an elite channel breaking down AI models, software architectures, algorithms, and developer tools.
Write an authentic, highly engaging 5-scene YouTube Shorts script for: "{topic}".

Verified Research Context:
{context_str}

CRITICAL EDITORIAL RULES:
1. Do NOT use generic placeholder formulas like "Something unprecedented just happened in {topic}". Write factual, specific, punchy sentences about what actually happened, the technical mechanism, and why developers/engineers care.
2. If the topic is software/models (like "jev vs other models", "MCP", "Transformers"), do NOT talk about physical warehouse robots! Talk about model inference, latency, evaluation benchmarks, decision-making, or software architecture.
3. Scene 1 (Hook, 10-15 words): A gripping first 3 seconds mentioning the specific core breakthrough, comparison, or dilemma.
4. Scene 2 (Lead Story, 14-20 words): What specifically changed or was released based on the research.
5. Scene 3 (Mechanism / Contrast, 14-20 words): How the technology actually works, benchmark numbers, or architectural difference.
6. Scene 4 (Implication / Stakes, 12-18 words): What this means for production systems, developers, or industry scale.
7. Scene 5 (CTA, 14-18 words): Conclude the thought and end with: "And this is just the beginning. Subscribe to {channel_name} for daily frontier AI briefings."
8. TOTAL WORDS: The entire script across all 5 scenes must total at least 55 to 80 words (around 12-18 words per scene) to match optimal YouTube Shorts duration.

Output MUST be a JSON object with this exact schema:
{{
  "sections": [
    {{
      "role": "hook",
      "spoken_text": "...",
      "primary_subject": "short 2-4 word specific subject name",
      "visual_intent": "emerge",
      "emphasis_words": ["WORD1", "WORD2", "WORD3"]
    }},
    {{
      "role": "lead_story",
      "spoken_text": "...",
      "primary_subject": "short 2-4 word specific subject name",
      "visual_intent": "reveal",
      "emphasis_words": ["WORD1", "WORD2", "WORD3"]
    }},
    {{
      "role": "escalation",
      "spoken_text": "...",
      "primary_subject": "short 2-4 word specific subject name",
      "visual_intent": "dramatic_cut",
      "emphasis_words": ["WORD1", "WORD2", "WORD3"]
    }},
    {{
      "role": "implication",
      "spoken_text": "...",
      "primary_subject": "short 2-4 word specific subject name",
      "visual_intent": "scale_up",
      "emphasis_words": ["WORD1", "WORD2", "WORD3"]
    }},
    {{
      "role": "cta",
      "spoken_text": "And this is just the beginning. Subscribe to {channel_name} for daily frontier AI briefings.",
      "primary_subject": "{channel_name}",
      "visual_intent": "branded_callout",
      "emphasis_words": ["BEGINNING", "SUBSCRIBE", "DAILY"]
    }}
  ]
}}"""
        data = call_llm_json(prompt)
        if not data or not isinstance(data.get("sections"), list) or len(data["sections"]) < 4:
            return None

        sections: list[ScriptSection] = []
        for idx, sec_data in enumerate(data["sections"][:5]):
            sc_id = f"scene_{idx+1:02d}"
            sec_id = f"sec_{idx+1:02d}"
            role = str(sec_data.get("role", "context")).lower()
            spoken = str(sec_data.get("spoken_text", "")).strip()
            if not spoken:
                continue
            dur = _estimate_duration(spoken)
            emphasis = [str(w).upper() for w in sec_data.get("emphasis_words", [])[:3]]
            subj = str(sec_data.get("primary_subject", topic.strip()))
            intent = str(sec_data.get("visual_intent", "reveal"))
            sections.append(ScriptSection(
                section_id=sec_id,
                scene_id=sc_id,
                role=role,
                spoken_text=spoken,
                estimated_duration_seconds=dur,
                word_count=len(spoken.split()),
                emphasis_words=emphasis or ["FRONTIER", "AI", "SYSTEM"],
                visual_intent=intent,
                primary_subject=subj,
                retention_trigger="immediate_curiosity" if idx == 0 else "fast_pacing",
            ))

        if len(sections) >= 4:
            total_words = sum(s.word_count for s in sections)
            if total_words < 50:
                print(f"  -> [Script Intelligence Warning] LLM script too brief ({total_words} words < 50); using heuristic fallback.")
                return None
            total_dur = sum(s.estimated_duration_seconds for s in sections)
            scoring = score_script(sections)
            print(f"  -> [Script Intelligence] Synthesized authentic narration via LLM ({len(sections)} scenes, {total_words} words).")
            return ScriptArtifact(
                topic=topic.strip(),
                format=ScriptFormat.SHORTS,
                hook_story_id=research_pack.stories[0].story_id if research_pack.stories else "story_01",
                sections=sections,
                total_duration_seconds=round(total_dur, 1),
                total_word_count=total_words,
                scoring=scoring,
                grounded_claims=[s.headline for s in (research_pack.stories or [])[:3]],
                channel_name=channel_name,
            )
    except Exception as exc:
        print(f"  -> [Script Intelligence Warning] LLM generation failed ({exc}); using procedural fallback.")
    return None


def _generate_extended_duration_script(
    topic: str,
    research_pack: ResearchPack,
    channel_name: str = "AI Simplified Lab",
    target_duration: float = 120.0,
) -> ScriptArtifact:
    """Generate an extended YouTube Short (90s - 180s / up to 3 mins) with multi-scene technical depth."""
    topic_clean = topic.strip()
    topic_lower = topic_clean.lower()
    sections: list[ScriptSection] = []

    is_gen_ai = any(k in topic_lower for k in ("gen ai", "generative ai", "generative", "foundation model", "llm"))

    if is_gen_ai:
        scene_defs = [
            ("sec_01", "scene_01", "hook",
             "What is Generative AI, and how does it actually create brand new text, code, and images out of thin air?",
             ["GENERATIVE", "CREATE", "IMAGES"], "emerge", "Generative AI Core Concept"),
            ("sec_02", "scene_02", "lead_story",
             "Unlike classical AI that only classifies existing data, generative models learn probability distributions to synthesize entirely novel outputs.",
             ["CLASSIFIES", "PROBABILITY", "SYNTHESIZE"], "reveal", "Synthesis vs Classification"),
            ("sec_03", "scene_03", "mechanism",
             "At the architectural core is the Transformer, using multi-head self-attention to calculate mathematical relationships across entire sequences simultaneously.",
             ["TRANSFORMER", "SELF_ATTENTION", "SEQUENCES"], "flow", "Transformer Attention Matrix"),
            ("sec_04", "scene_04", "pipeline",
             "Input prompts are tokenized into numerical IDs and mapped into dense vector embeddings within a continuous high-dimensional semantic space.",
             ["TOKENIZED", "EMBEDDINGS", "VECTOR_SPACE"], "connect", "Vector Embedding Space"),
            ("sec_05", "scene_05", "escalation",
             "Generation proceeds by predicting probability logits for the next token, filtered through temperature parameters to balance creative variety with logical coherence.",
             ["PREDICTING", "LOGITS", "TEMPERATURE"], "dramatic_cut", "Token Sampling & Temperature"),
            ("sec_06", "scene_06", "mechanism",
             "Beyond text, diffusion models power generative image creation by iteratively reversing gaussian noise through deep convolutional U-Net denoisers.",
             ["DIFFUSION", "DENOISING", "GAUSSIAN"], "transform", "Diffusion Denoising Process"),
            ("sec_07", "scene_07", "implication",
             "Training frontier foundation models requires clusters of specialized tensor accelerators processing quadrillions of floating-point operations every second.",
             ["CLUSTERS", "ACCELERATORS", "FLOPS"], "scale_up", "Compute & GPU Clusters"),
            ("sec_08", "scene_08", "mechanism",
             "In production architectures, generative models connect to vector databases via retrieval-augmented generation to ground answers in verified external truth.",
             ["RETRIEVAL", "DATABASES", "GROUNDING"], "connect", "RAG & Vector Grounding"),
            ("sec_09", "scene_09", "implication",
             "The newest frontier introduces reasoning models that execute test-time compute to verify logic and solve complex multi-step problems autonomously.",
             ["REASONING", "TEST_TIME", "AUTONOMOUS"], "focus", "Reasoning & Agent Architecture"),
            ("sec_10", "scene_10", "cta",
             f"This is fundamentally rewiring modern software development. Subscribe to {channel_name} for daily frontier AI architecture breakdowns.",
             ["REWIRING", "SUBSCRIBE", "BREAKDOWNS"], "branded_callout", channel_name),
        ]
    else:
        hook_story, stories = select_stories_for_script(research_pack, ScriptFormat.LONG_FORM)
        scene_defs = [
            ("sec_01", "scene_01", "hook",
             f"Something extraordinary is happening in {topic_clean}, and engineers are rethinking the entire technology stack.",
             ["EXTRAORDINARY", "RETHINKING", "STACK"], "emerge", topic_clean),
            ("sec_02", "scene_02", "lead_story",
             f"The latest engineering breakthroughs allow {topic_clean} systems to operate with unprecedented speed and precision.",
             ["BREAKTHROUGHS", "PRECISION", "SPEED"], "reveal", f"{topic_clean} Advance"),
            ("sec_03", "scene_03", "mechanism",
             "Under the hood, specialized algorithmic pipelines eliminate legacy bottlenecks and optimize throughput across production clusters.",
             ["ALGORITHMIC", "PIPELINES", "THROUGHPUT"], "flow", "Algorithmic Pipeline"),
            ("sec_04", "scene_04", "pipeline",
             "Data streams through high-concurrency ingestion layers that normalize and route inputs directly to target processing nodes.",
             ["HIGH_CONCURRENCY", "NORMALIZATION", "ROUTING"], "connect", "Ingestion Fabric"),
            ("sec_05", "scene_05", "escalation",
             "Instead of fragile single-point architectures, modern deployments adapt dynamically to fluctuating loads and fault conditions.",
             ["DYNAMIC", "DEPLOYMENTS", "FAULT_TOLERANT"], "dramatic_cut", "Adaptive Resilience"),
            ("sec_06", "scene_06", "mechanism",
             "Deep telemetry layers monitor internal states, ensuring low latency and deterministic execution in mission-critical environments.",
             ["TELEMETRY", "LOW_LATENCY", "DETERMINISTIC"], "focus", "Runtime Telemetry"),
            ("sec_07", "scene_07", "implication",
             "This transition unlocks unprecedented computational efficiency, reducing operational overhead by orders of magnitude.",
             ["EFFICIENCY", "REDUCING", "OVERHEAD"], "scale_up", "Operational Scale"),
            ("sec_08", "scene_08", "mechanism",
             "Integrated validation frameworks continuously inspect outputs, preventing silent regressions and guaranteeing system safety.",
             ["VALIDATION", "REGRESSIONS", "SAFETY"], "connect", "Verification Mesh"),
            ("sec_09", "scene_09", "implication",
             "As frontier architectures mature, autonomous workflows are replacing static manual tooling across enterprise infrastructure.",
             ["MATURE", "AUTONOMOUS", "WORKFLOWS"], "transform", "Autonomous Shift"),
            ("sec_10", "scene_10", "cta",
             f"And this is just the beginning of the platform shift. Subscribe to {channel_name} for daily deep-dive technical briefings.",
             ["PLATFORM_SHIFT", "SUBSCRIBE", "BRIEFINGS"], "branded_callout", channel_name),
        ]

    for sec_id, sc_id, role, text, emphasis, intent, subj in scene_defs:
        dur = _estimate_duration(text)
        sections.append(ScriptSection(
            section_id=sec_id,
            scene_id=sc_id,
            role=role,
            spoken_text=text,
            estimated_duration_seconds=dur,
            word_count=len(text.split()),
            emphasis_words=emphasis,
            visual_intent=intent,
            primary_subject=subj,
            retention_trigger="fast_pacing",
        ))

    total_words = sum(s.word_count for s in sections)
    total_dur = sum(s.estimated_duration_seconds for s in sections)
    scoring = score_script(sections)

    return ScriptArtifact(
        topic=topic_clean,
        format=ScriptFormat.SHORTS,
        hook_story_id="story_01",
        sections=sections,
        total_duration_seconds=round(total_dur, 1),
        total_word_count=total_words,
        scoring=scoring,
        grounded_claims=[s.headline for s in (research_pack.stories or [])[:3]],
        channel_name=channel_name,
    )


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

    # 2. Procedural heuristic fallback if LLM is offline
    print("  -> [Script Intelligence Fallback] Using procedural heuristic fallback template.")
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
