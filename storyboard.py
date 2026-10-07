"""AI Storyboard Planner — auto-generates scene content from a topic.

Given just a topic + style, produces a fully fleshed-out storyboard with
narration, headings, and visual direction. Uses AI if available, otherwise
generates high-quality local templates optimised for virality.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from styles import get_style, auto_detect_style, SceneTemplate

try:
    from models import best_model_order
except Exception:
    best_model_order = None


def clean_concept(topic: str) -> str:
    subject = topic.strip().rstrip("?.! ")
    concept = re.sub(
        r"^(how does|what is|what are|why does|why do|can you explain|tell me about|explain)\s+",
        "", subject, flags=re.I)
    concept = re.sub(r"\s+(work|works|function|operate)\s*$", "", concept, flags=re.I).strip()
    concept = re.sub(r"^(a|an|the)\s+", "", concept, flags=re.I).strip()
    return concept or subject


def split_comparison(topic: str) -> tuple[str, str]:
    """Extract 'A' and 'B' from topics like 'Docker vs Kubernetes'."""
    for sep in [" vs ", " versus ", " or ", " compared to "]:
        if sep in topic.lower():
            parts = re.split(sep, topic, flags=re.I)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
    return "", ""


def note_keywords(notes: str, max_items: int = 3) -> list[str]:
    """Pull short topic phrases out of the user's notes, e.g.
    'Mention privacy and encryption' -> ['Privacy', 'Encryption']."""
    if not notes:
        return []
    parts = re.split(r"[,;.]|\band\b", notes, flags=re.I)
    out = []
    for p in parts:
        p = p.strip()
        p = re.sub(r"^(mention|include|cover|focus on|talk about|explain)\b:?\.?\s*", "", p, flags=re.I)
        p = re.sub(r"^(beginner|advanced|general)\s+audience\.?\s*", "", p, flags=re.I).strip(" .")
        if 2 <= len(p) <= 26 and len(p.split()) <= 3:
            label = p.title() if p.islower() else p
            if label.lower() not in {x.lower() for x in out}:
                out.append(label)
        if len(out) >= max_items:
            break
    return out


def is_script_text(text: str) -> bool:
    """Detect if text is a full pre-written voiceover script rather than a short topic phrase."""
    if not text:
        return False
    t = text.strip()
    return len(t) > 70 and (len(re.split(r"[.!?\n]+", t)) >= 2 or "\n" in t)


def validate_and_refine_storyboard(story: dict, style_name: str, topic: str = "") -> dict:
    """Semantic Quality Auditor.
    
    Validates scenes to ensure they contain semantic meaning and aren't just empty objects.
    Does NOT inject UI widgets or badges. A cinematic shot might be entirely valid with just one object.
    """
    if not story or "scenes" not in story or not story["scenes"]:
        return story

    from viral_template import is_viral_template_scene
    if is_viral_template_scene(story["scenes"][0]):
        return story

    scenes = story["scenes"]
    clean_scenes = []

    for i, s in enumerate(scenes):
        heading = s.get("heading", s.get("title", "")).strip()
        if heading.lower().startswith("scene "): heading = ""
        if heading: s["heading"] = heading
        
        # Check if the AI used the new visual_scene object or the legacy elements array
        if "visual_scene" in s:
            v_scene = s["visual_scene"]
            # Ensure mandatory fields exist for the compositor
            v_scene.setdefault("visual_concept", "Abstract concept")
            v_scene.setdefault("environment", "Minimalist space")
            v_scene.setdefault("camera_choreography", "static")
            v_scene.setdefault("render_strategy", "hybrid")
            v_scene.setdefault("objects", [])
            
            # Programmatic Visual Uniqueness Auditor
            score = v_scene.get("visual_uniqueness_score", 100)
            if isinstance(score, (int, float)) and score < 70:
                print(f"  [Auditor Warning] Scene {i+1} has a low uniqueness score ({score}). Consider regenerating if visual output feels generic.")
            
            # Audit objects for empty text cards
            valid_objs = []
            for obj in v_scene["objects"]:
                obj_type = str(obj.get("type", "unknown")).lower()
                text = str(obj.get("text", "")).strip()
                if obj_type in ("box", "card", "text") and not text:
                    continue
                valid_objs.append(obj)
            v_scene["objects"] = valid_objs
        else:
            # Legacy element filtering
            raw_els = s.get("elements", [])
            validated_els = []
            for el in raw_els:
                el_type = str(el.get("type", "text")).lower()
                text = str(el.get("text", "")).strip()
                if el_type in ("box", "card") and not text:
                    continue
                validated_els.append(el)
            s["elements"] = validated_els

        clean_scenes.append(s)

    story["scenes"] = clean_scenes
    return story


def generate_storyboard(topic: str, style_name: str = "auto", notes: str = "",
                        target_duration: float = 30.0) -> dict:
    """Generate a complete storyboard. Handles topics OR full scripts seamlessly."""
    raw_script = topic if is_script_text(topic) else (notes if is_script_text(notes) else "")
    
    # Force cast to float to prevent string division TypeErrors
    try:
        target_duration = float(target_duration)
    except (ValueError, TypeError):
        target_duration = 30.0

    # Auto duration calculation if requested
    if target_duration <= 0:
        if raw_script:
            words = len(raw_script.split())
            target_duration = max(15.0, round(words / 2.5, 1))
        else:
            target_duration = 30.0

    if style_name == "auto":
        # Deterministic — no LLM call needed
        style_name = auto_detect_style(topic)
        print(f"  -> Auto-detected style: {style_name}")

    style = get_style(style_name)
    concept = clean_concept(topic if not raw_script else (topic[:30] if len(topic) < 80 else "Tech Breakdown"))
    display = concept.title() if concept.islower() else concept

    # Reward System: Check instant zero-token blueprint cache first
    from reward_system import get_cached_blueprint, calculate_reward_score, save_high_reward_blueprint
    # CACHE DISABLED FOR UNIQUE GENERATION PER USER REQUEST:
    # cached_story = get_cached_blueprint(topic)
    # if cached_story:
    #     return cached_story

    # Try AI storyboard first
    ai_story = None
    if (os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENROUTER_API_KEY") or os.getenv("OLLAMA_HOST")):
        try:
            ai_story = _ai_storyboard(topic, concept, style_name, notes, target_duration, raw_script=raw_script)
        except Exception as ex:
            raise RuntimeError(f"AI storyboard generation failed: {ex}")

        if ai_story:
            validated = validate_and_refine_storyboard(ai_story, style_name, topic=topic)
            reward, breakdown = calculate_reward_score(validated)
            print(f"  -> [Reward System] Storyboard Score: {reward}/100 | Breakdown: {breakdown}")
            save_high_reward_blueprint(topic, validated, reward)
            return validated
        
    raise RuntimeError("No AI API keys configured or all AI providers failed. Mock templates are disabled by user request.")


def _local_storyboard(topic: str, concept: str, display: str,
                      style, notes: str, duration: float, style_name: str = "explainer", raw_script: str = "") -> dict:
    scenes = []
    script_sentences = [s.strip() for s in re.split(r"[.!?\n]+", raw_script) if len(s.strip()) > 5] if raw_script else []
    
    total_scenes = max(len(script_sentences), style.scene_count) if script_sentences else style.scene_count
    per_scene = duration / total_scenes

    # All possible format values
    concept_a, concept_b = "", ""
    if style_name == "comparison":
        concept_a, concept_b = split_comparison(topic)
    if not concept_a:
        concept_a = display
    if not concept_b:
        concept_b = "Alternative"

    # Prefer the user's own words (from notes) over generic placeholders.
    kw = note_keywords(notes)
    while len(kw) < 3:
        kw.append("")
    p1 = kw[0] or f"{display} Basics"
    p2 = kw[1] or f"How {display} Works"
    p3 = kw[2] or f"Why {display} Matters"

    fmt = dict(
        concept=display, topic=topic, duration=int(duration),
        concept_simple=f"{display} explained",
        concept_explanation=f"At its core, {concept} works by turning a complex process into simple repeatable steps.",
        concept_a=concept_a, concept_b=concept_b, winner=concept_a,
        point_1=p1, point_2=p2, point_3=p3,
        point_1_narration=f"First: {p1.lower()} — this is where {concept} starts.",
        point_2_narration=f"Then: {p2.lower()} — the key step most people miss.",
        point_3_narration=f"Finally: {p3.lower()} — the part that actually matters.",
        scene_count=total_scenes,
    )

    def short(text: str, limit: int = 20) -> str:
        text = text.strip()
        return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."

    for i in range(total_scenes):
        tmpl = style.scenes[i % len(style.scenes)]
        heading = tmpl.heading.format_map(fmt) if tmpl.heading else ""
        subheading = tmpl.subheading.format_map(fmt) if tmpl.subheading else ""
        
        # Override narration with exact user script sentence if provided
        if script_sentences and i < len(script_sentences):
            narration = script_sentences[i]
        else:
            narration = tmpl.narration.format_map(fmt) if tmpl.narration else ""

        left = short(tmpl.left.format_map(fmt)) if tmpl.left else ""
        right = short(tmpl.right.format_map(fmt)) if tmpl.right else ""

        scene = {
            "kind": tmpl.kind,
            "heading": heading,
            "subheading": subheading,
            "left": left,
            "right": right,
            "narration": narration,
            "motion": tmpl.motion,
            "start_seconds": round(i * per_scene, 2),
            "end_seconds": round((i + 1) * per_scene, 2),
            "asset": f"scenes/{i + 1:02d}-{tmpl.kind}.png",
            "elements": [dict(e) for e in tmpl.elements] if hasattr(tmpl, "elements") else []
        }
        scenes.append(scene)

    return {
        "title": topic.strip(),
        "tagline": f"{style.description}",
        "style": style.name,
        "scenes": scenes,
        "source": "local-template",
        "notes": notes,
        "provider_attempts": [{"provider": "local", "detail": "Local template generation", "status": "used"}],
    }


# ── AI Storyboard ────────────────────────────────────────────────────────

def _call_openrouter(prompt):
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    last_error = None
    # "openrouter/auto" lets OpenRouter route to a working model itself.
    models = models_for("openrouter", "OPENROUTER_MODELS", ["openrouter/auto"])
    for model in models:
        body = json.dumps({"model": model,
                           "messages": [{"role": "user", "content": prompt}],
                           "response_format": {"type": "json_object"},
                           "temperature": 0.9, "max_tokens": 2000}).encode()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions", body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "HTTP-Referer": "http://localhost:5000",
                     "X-Title": "AI SIMPLIFIED LAB Video Factory"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                payload = json.load(resp)
            choices = payload.get("choices", [])
            if not choices:
                raise ValueError(f"OpenRouter model {model} returned no choices")
            text = choices[0].get("message", {}).get("content", "")
            story = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip()))
            tokens = payload.get("usage", {}).get("total_tokens", 0)
            if len(story.get("scenes", [])) >= 4:
                story["source"] = "openrouter"
                return story, f"model {model}", tokens
            last_error = ValueError(f"Model {model} returned {len(story.get('scenes', []))} scenes")
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("No OpenRouter model succeeded")


def _provider_order() -> list[str]:
    """Try providers in auto-ranked order: whichever provider owns the
    best-ranked working model goes first. Unranked providers keep their
    default position at the end."""
    order = ["openai", "gemini", "openrouter", "ollama"]
    if best_model_order:
        try:
            seen = []
            for p, _ in best_model_order():
                if p not in seen:
                    seen.append(p)
            if seen:
                return seen + [p for p in order if p not in seen]
        except Exception:
            pass
    return order


def _call_agent(prompt: str, role_name: str) -> tuple[dict, str]:
    """Helper to run a prompt through the provider fallback chain."""
    calls = {"openai": _call_openai, "gemini": _call_gemini,
             "openrouter": _call_openrouter, "ollama": _call_ollama}
    attempts = []
    
    for provider in _provider_order():
        try:
            result, detail, tokens = calls[provider](prompt)
            attempts.append({"provider": provider, "detail": detail, "status": "success", "tokens": tokens})
            result["provider_attempts"] = attempts
            return result, detail
        except RuntimeError as exc:
            attempts.append({"provider": provider, "detail": str(exc), "status": "skipped"})
        except Exception as exc:
            attempts.append({"provider": provider, "detail": f"{type(exc).__name__}: {exc}", "status": "failed"})
            print(f"    [!] {provider} failed in {role_name}: {exc}")
            
    print(f"  -> FATAL: {role_name} Agent failed on all providers.")
    return None, f"{role_name} Agent failed on all providers."


def _ai_storyboard(topic, concept, style_name, notes, duration, raw_script="") -> dict:
    """Generate storyboard via AI. Routes directly to locked VIRAL_SHORT_V1."""
    if style_name == "legacy_kinetic":
        return _ai_legacy_kinetic_storyboard(topic, concept, style_name, notes, duration, raw_script)
    return _ai_viral_storyboard(topic, concept, style_name, notes, duration, raw_script)


def _ai_legacy_kinetic_storyboard(topic, concept, style_name, notes, duration, raw_script="") -> dict:
    """Legacy kinetic studio generator for backward compatibility."""
    style = get_style("legacy_kinetic")
    target_scenes = max(4, int(duration / 3.5))
    cot_prompt = f"""You are the automated content engine for AI Simplified Lab.
Topic: {topic}
Duration: {int(duration)} seconds ({target_scenes} scenes).
Context: {notes or 'General audience'}
Style: {style.description}
Return JSON with 'title', 'tagline', and 'scenes' (each having kind: 'custom', narration, bg_color, visual_scene)."""
    script, detail = _call_agent(cot_prompt, "Legacy Kinetic Studio")
    if script:
        script["source"] = f"Legacy Kinetic ({detail})"
    return script


def _ai_viral_storyboard(topic, concept, style_name, notes, duration, raw_script="") -> dict:
    """Generate a locked VIRAL_SHORT_V1 storyboard with EXACTLY 6 scenes.

    The AI is asked ONLY for editorial content:
      role, headline (max 6 words), narration, hero_type, hero_label,
      supporting_fact, visual_data, motion_energy.

    No python_draw_code. No pixel coordinates. No invented styles.
    The renderer owns all visual decisions.
    """
    from viral_template import (
        HERO_PRIMITIVES, VIRAL_EXPLAINER, VIRAL_NEWS, auto_detect_template_mode,
        build_semantic_visual_plan, create_template_context,
        ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA,
    )

    if style_name in (VIRAL_EXPLAINER, VIRAL_NEWS, "editorial_explainer", "editorial_viral"):
        template_mode = style_name
    else:
        template_mode = auto_detect_template_mode(topic)

    is_news = (template_mode == VIRAL_NEWS)
    target_scenes = 6

    if is_news:
        structure = """
Scene structure for VIRAL NEWS (EXACTLY 6 scenes):
1. role: "hook"     — Stop-scrolling hook. Big claim about the news event.
2. role: "problem"  — What happened? The core news event in simple terms.
3. role: "process"  — What changed? The mechanism / what is different now.
4. role: "proof"    — The most important / craziest detail or number.
5. role: "payoff"   — Why it matters. The real-world impact.
6. role: "cta"      — AI SIMPLIFIED LAB channel subscribe."""
    else:
        structure = """
Scene structure for VIRAL EXPLAINER (EXACTLY 6 scenes):
1. role: "hook"     — Stop-scrolling hook. Big question or claim.
2. role: "problem"  — Simple analogy or relatable problem setup.
3. role: "process"  — How it works. The mechanism step by step.
4. role: "proof"    — Real example, demo, or evidence.
5. role: "payoff"   — The aha moment. Key takeaway.
6. role: "cta"      — AI SIMPLIFIED LAB channel subscribe."""

    hero_list = ", ".join(sorted(HERO_PRIMITIVES))

    narration_directive = ""
    if raw_script:
        narration_directive = f"""
IMPORTANT: The user provided an EXACT pre-written voice-over script:
{raw_script}
Divide it evenly across the 6 scenes.
"""

    viral_prompt = f"""You are the content director for AI SIMPLIFIED LAB — a YouTube Shorts channel.

Topic: {topic}
Template mode: {template_mode}
Duration: 30 seconds (EXACTLY 6 scenes)
Context: {notes or 'General audience, beginner-friendly.'}
{narration_directive}
{structure}

You must return EXACTLY this JSON structure with EXACTLY 6 scenes — no extra fields, no markdown, no python_draw_code:

{{
  "template_mode": "{template_mode}",
  "title": "Short video title (max 60 chars)",
  "tagline": "One sentence tagline",
  "scenes": [
    {{
      "role": "hook",
      "narration": "Exact spoken words for this scene. 12-20 words. Punchy.",
      "headline": "MAX 6 WORDS ALL CAPS",
      "hero_type": "one of: {hero_list}",
      "hero_label": "Short label shown on/near hero visual (3-5 words max)",
      "supporting_fact": "One short fact, stat, or key point shown below hero",
      "visual_data": {{
        "note": "Optional. For pipeline: steps=[]. For code_panel: lines=[]. For stat_burst: value='', label=''. For data_stream: left='', center='', right=''. For comparison_split: left='', right=''. For keyword_burst: keyword='', subtitle=''. Leave empty if not needed."
      }},
      "motion_energy": "high"
    }}
  ]
}}

RULES (MANDATORY):
- Return EXACTLY 6 scenes matching the 6 roles: hook, problem, process, proof, payoff, cta.
- hero_type MUST be chosen from the list above. Do NOT invent new hero types.
- headline MUST be at most 6 words.
- narration must be spoken words only (no stage directions, no visual cues).
- Do NOT include python_draw_code in any field.
- Do NOT include x, y, width, height, pixel coordinates.
- Do NOT invent visual styles or background colors.
- The CTA scene (last) always has role: "cta" and hero_type: "cta_brand".
- For news topics: do NOT fabricate statistics, screenshots, or quotes.
- narration should be natural conversational English, not stiff or robotic.
- Each scene's narration must make sense as a standalone spoken sentence.
- visual_data should only include data relevant to the hero_type.
- motion_energy must be exactly "high", "medium", or "low".

Return JSON ONLY. No markdown. No preamble. No explanation.
"""

    studio_label = "Editorial Studio" if template_mode in ("editorial_explainer", "editorial_viral") else "VIRAL_SHORT_V2 Studio"
    print(f"  -> {studio_label} [{template_mode}]: Planning 6 scenes...")
    script, detail = _call_agent(viral_prompt, studio_label)
    if not script:
        return None

    # Validate, normalize, and enforce exactly 6 viral scenes
    script = _validate_viral_storyboard(script, template_mode, topic, target_scenes=6)

    # Stamp template mode, kind, and template_context onto every scene
    for i, scene in enumerate(script.get("scenes", [])):
        role = scene.get("role", "process")
        is_editorial_mode = template_mode in ("editorial_explainer", "editorial_viral")
        scene["kind"] = template_mode if is_editorial_mode else "viral_short_v2"
        scene["_template_mode"] = template_mode
        scene["template_context"] = create_template_context(template_mode, role)
        scene["visual_plan"] = build_semantic_visual_plan(scene, i, len(script.get("scenes", [])))
        if template_mode in ("editorial_explainer", "editorial_viral"):
            from editorial import build_editorial_plan
            scene["semantic_visual_plan"] = build_editorial_plan(scene)
            scene["render_plan"] = scene["semantic_visual_plan"]["render_plan"]
        scene.pop("python_draw_code", None)
        scene.pop("elements", None)
        scene.pop("visual_scene", None)

    script["template_mode"] = template_mode
    script["style"] = template_mode
    script["source"] = f"{studio_label} [{template_mode}] ({detail})"

    # Real Pipeline Debug Logging
    print(f"\n[PIPELINE]")
    print(f"topic={topic}")
    print(f"\n[PIPELINE]")
    print(f"template_version={'EDITORIAL_RENDER_PLAN' if template_mode in ('editorial_explainer', 'editorial_viral') else 'VIRAL_SHORT_V2'}")
    print(f"\n[PIPELINE]")
    print(f"template_mode={template_mode}")
    print(f"\n[PIPELINE]")
    print(f"scene_count={len(script['scenes'])}")
    for i, sc in enumerate(script["scenes"]):
        print(f"\n[PIPELINE]")
        print(f"scene_{i+1}_role={sc.get('role', '')}")

    return script


def _validate_viral_storyboard(script: dict, template_mode: str, topic: str, target_scenes: int = 6) -> dict:
    """Validate, repair, and strictly enforce exactly 6 scenes for VIRAL_SHORT_V2."""
    from viral_template import (
        resolve_hero_type, sanitize_text, truncate_headline, create_template_context,
        build_semantic_visual_plan, validate_visual_plan,
        ROLE_HOOK, ROLE_PROBLEM, ROLE_PROCESS, ROLE_PROOF, ROLE_PAYOFF, ROLE_CTA,
        EXPLAINER_ROLES, NEWS_ROLES, HERO_FALLBACK, VIRAL_NEWS,
    )

    is_news = (template_mode == VIRAL_NEWS)
    canonical_roles = NEWS_ROLES if is_news else EXPLAINER_ROLES

    raw_scenes = script.get("scenes", [])
    if not isinstance(raw_scenes, list):
        raw_scenes = []

    # Map existing scenes to canonical 6 roles
    validated_scenes = []
    for i in range(6):
        target_role = canonical_roles[i]
        
        # Find matching scene or use index i
        matched_scene = None
        if i < len(raw_scenes):
            s = raw_scenes[i]
            if isinstance(s, dict):
                matched_scene = s

        if not matched_scene:
            # Create default scene for this role
            matched_scene = {
                "role": target_role,
                "headline": f"{target_role.upper()} INSIGHT",
                "narration": f"Key point about {topic}.",
                "hero_type": "cta_brand" if target_role == ROLE_CTA else HERO_FALLBACK,
                "hero_label": topic[:24],
                "supporting_fact": "",
                "visual_data": {},
                "motion_energy": "high" if i == 0 else "medium",
            }

        # Enforce canonical role
        matched_scene["role"] = target_role

        # Headline
        hl_raw = str(matched_scene.get("headline", topic[:30].upper()))
        hl = truncate_headline(hl_raw)
        matched_scene["headline"] = hl if hl else topic[:30].upper()

        # Narration
        narr = sanitize_text(str(matched_scene.get("narration", "")), f"Let's explore {topic}.")
        matched_scene["narration"] = narr

        # Hero type
        if target_role == ROLE_CTA:
            matched_scene["hero_type"] = "cta_brand"
            matched_scene["headline"] = "SUBSCRIBE TO AI SIMPLIFIED LAB"
            if not matched_scene.get("hero_label"):
                matched_scene["hero_label"] = "AI Simplified Lab"
            matched_scene["supporting_fact"] = sanitize_text(
                str(matched_scene.get("supporting_fact", "More AI breakdowns from AI Simplified Lab")),
                "More AI breakdowns from AI Simplified Lab",
            )
        else:
            matched_scene["hero_type"] = resolve_hero_type(str(matched_scene.get("hero_type", "")))
            # Optional supporting fact
            matched_scene["supporting_fact"] = sanitize_text(str(matched_scene.get("supporting_fact", "")), "")

        # Hero label
        matched_scene["hero_label"] = sanitize_text(str(matched_scene.get("hero_label", "")), "")

        # Visual data
        vd = matched_scene.get("visual_data")
        matched_scene["visual_data"] = vd if isinstance(vd, dict) else {}

        # Motion energy
        me = str(matched_scene.get("motion_energy", "medium")).lower()
        if me not in ("high", "medium", "low"):
            me = "high" if i == 0 else "medium"
        matched_scene["motion_energy"] = me

        visual_intent = {
            ROLE_HOOK: "Open with a strong product or system framing and a high-contrast hero reveal.",
            ROLE_PROBLEM: "Show the pain point or broken flow that creates the problem to solve.",
            ROLE_PROCESS: "Explain the sequential mechanism with a clear flow or pipeline structure.",
            ROLE_PROOF: "Demonstrate evidence, measurements, or a concrete result that validates the claim.",
            ROLE_PAYOFF: "Land the big take-away and compress the impact into an unmistakable result.",
            ROLE_CTA: "Close with a clean branded invitation that feels premium and on-brand.",
        }.get(target_role, "Show the core idea clearly and keep the scene readable.")

        preferred_primitive = {
            ROLE_HOOK: "hero_orb",
            ROLE_PROBLEM: "comparison_split",
            ROLE_PROCESS: "pipeline",
            ROLE_PROOF: "code_panel",
            ROLE_PAYOFF: "keyword_burst",
            ROLE_CTA: "cta_brand",
        }.get(target_role, "hero_glow")

        camera_behavior = {
            ROLE_HOOK: "push_in",
            ROLE_PROBLEM: "pan_left",
            ROLE_PROCESS: "pan_right",
            ROLE_PROOF: "focus_reveal",
            ROLE_PAYOFF: "push_in",
            ROLE_CTA: "static",
        }.get(target_role, "static")

        motion_intensity = {
            ROLE_HOOK: "high",
            ROLE_PROBLEM: "medium",
            ROLE_PROCESS: "medium",
            ROLE_PROOF: "medium",
            ROLE_PAYOFF: "high",
            ROLE_CTA: "low",
        }.get(target_role, "medium")

        plan = build_semantic_visual_plan(matched_scene, i, 6)
        ok, issues = validate_visual_plan(matched_scene)
        if not ok:
            plan["visual_intent"] = visual_intent
            plan["preferred_primitive"] = preferred_primitive
            plan["camera_behavior"] = camera_behavior
            plan["motion_intensity"] = motion_intensity

        # Enforce viral fields & clean forbidden fields
        matched_scene["kind"] = "viral_short_v2"
        matched_scene["scene_role"] = target_role
        matched_scene["visual_intent"] = plan.get("visual_intent", visual_intent)
        matched_scene["main_concept"] = plan.get("main_concept", target_role)
        matched_scene["primary_subject"] = sanitize_text(str(plan.get("primary_subject", matched_scene.get("headline", target_role.upper()))), target_role.upper())
        matched_scene["secondary_subjects"] = list(plan.get("secondary_subjects") or [])
        matched_scene["preferred_primitive"] = plan.get("preferred_primitive", preferred_primitive)
        matched_scene["camera_behavior"] = plan.get("camera_behavior", camera_behavior)
        matched_scene["motion_intensity"] = plan.get("motion_intensity", motion_intensity)
        matched_scene["visual_density"] = plan.get("visual_density", "medium")
        matched_scene["emphasis_words"] = plan.get("emphasis_words", [])
        matched_scene["visual_plan"] = plan
        try:
            from editorial import build_editorial_plan
            matched_scene["semantic_visual_plan"] = build_editorial_plan(matched_scene)
        except Exception:
            pass
        matched_scene["_template_mode"] = template_mode
        matched_scene["template_context"] = create_template_context(template_mode, target_role)
        matched_scene.pop("python_draw_code", None)
        matched_scene.pop("elements", None)
        matched_scene.pop("visual_scene", None)
        matched_scene.pop("x", None)
        matched_scene.pop("y", None)
        matched_scene.pop("width", None)
        matched_scene.pop("height", None)

        validated_scenes.append(matched_scene)

    script["scenes"] = validated_scenes[:6]
    return script


def models_for(provider: str, variable: str, defaults: list[str]) -> list[str]:
    """Model try-order for one provider.

    1. Explicit user pin (OPENAI_MODELS=... etc.) always wins.
    2. Otherwise the auto-ranked order from models.py (live-probed, cached 24h).
    3. Otherwise the built-in defaults.
    """
    pin = [x.strip() for x in os.getenv(variable, "").split(",") if x.strip()]
    if pin:
        return pin
    if best_model_order:
        try:
            ranked = [m for (p, m) in best_model_order() if p == provider]
            if ranked:
                return ranked
        except Exception:
            pass
    return defaults


def _call_openai(prompt):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    last_error = None
    models = models_for("openai", "OPENAI_MODELS", ["gpt-5-mini", "gpt-5.2", "gpt-4.1-mini"])
    for model in models:
        body = json.dumps({"model": model, "input": prompt, "store": False,
                           "text": {"format": {"type": "json_object"}, "verbosity": "low"}}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/responses", body,
                                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                                    method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.load(resp)
            text = payload.get("output_text", "") or "".join(
                p.get("text", "") for i in payload.get("output", [])
                for p in i.get("content", []) if p.get("type") == "output_text")
            story = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip()))
            tokens = payload.get("usage", {}).get("total_tokens", 0)
            if len(story.get("scenes", [])) >= 4:
                story["source"] = "openai"
                return story, f"model {model}", tokens
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("No OpenAI model succeeded")


def _call_gemini(prompt):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    last_error = None
    models = models_for("gemini", "GEMINI_MODELS", ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-3.8-flash"])
    for model in models:
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                           "generationConfig": {"response_mime_type": "application/json", "temperature": 0.3}}).encode()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", body,
            headers={"x-goog-api-key": key, "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.load(resp)
            candidates = payload.get("candidates", [])
            if not candidates:
                raise ValueError(f"Gemini model {model} returned no candidates")
            parts = candidates[0].get("content", {}).get("parts", [])
            text_parts = [p.get("text", "") for p in parts if "text" in p and not p.get("thought", False)]
            if not text_parts:
                text_parts = [p.get("text", "") for p in parts if "text" in p]
            text = "".join(text_parts)
            story = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip()))
            tokens = payload.get("usageMetadata", {}).get("totalTokenCount", 0)
            if len(story.get("scenes", [])) >= 4:
                story["source"] = "gemini"
                return story, f"model {model}", tokens
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("No Gemini model succeeded")


def _call_ollama(prompt):
    host = os.getenv("OLLAMA_HOST")
    if not host:
        raise RuntimeError("OLLAMA_HOST not set")
    last_error = None
    models = models_for("ollama", "OLLAMA_MODELS", ["qwen2.5:0.5b"])
    for model in models:
        body = json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json"}).encode()
        req = urllib.request.Request(f"{host.rstrip('/')}/api/generate", body,
                                    headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.load(resp)
            story = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", payload["response"].strip()))
            tokens = payload.get("prompt_eval_count", 0) + payload.get("eval_count", 0)
            if len(story.get("scenes", [])) >= 4:
                story["source"] = "ollama"
                return story, f"model {model}", tokens
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("No Ollama model succeeded")
