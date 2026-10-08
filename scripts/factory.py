"""Autonomous Video Factory CLI (Phase 13 + Phase 14).

Complete end-to-end autonomous video production pipeline:
  Topic
  ↓
  Research (Phase 10: Live Multi-Provider Web Retrieval)
  ↓
  Story Selection (Phase 11: Authority, Virality, Visual Potential)
  ↓
  Script Synthesis (Phase 11: Natural AI Simplified Lab narration)
  ↓
  Learned Packaging (Phase 12 + 14: Heuristic boosts from channel memory)
  ↓
  Visual Planning (Phase 9: Semantic scene & diversity planning)
  ↓
  Edit Decision Mapping (Phase 9: Seamless timeline construction)
  ↓
  Render (Remotion MP4 with WAV Chromium-safe audio)
  ↓
  Automated QA (12 Evidence-based QA gates)
  ↓
  Multi-Factor Editorial Scoring (10-point rigorous rubric)
  ↓
  Release Package Assembly (output/<topic_slug>/)

Commands:
  python scripts/factory.py produce --topic "<topic>" [--production <id>] [--freshness 7d]
  python scripts/factory.py record-metrics --production <id> --views <n> --ctr <pct> --watch-pct <pct> --subs <n>
  python scripts/factory.py insights
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import envfile
envfile.load_dotenv()

from production.artifact_store import ArtifactStore
from production.phase9.planner import generate_plan
from production.phase9.mapper import map_edit_decisions
from production.phase9.scoring import generate_editorial_score
from production.phase10.models import ResearchPack, ResearchMode
from production.phase10.researcher import research
from production.phase11.scriptwriter import generate_shorts_script, generate_longform_script
from production.phase12.packager import generate_packaging
from production.phase14.learning_engine import get_learning_system
from production.phase14.models import VideoMetrics
from schemas.models.artifact import ProducerInfo
from schemas.models.common import ProducerKind
from scripts.run_local_production import cmd_render, cmd_qa

PROJECTS_DIR = ROOT / "projects"
OUTPUT_DIR = ROOT / "output"


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "_", s)


def cmd_produce(args: argparse.Namespace, progress_cb: Any = None) -> int:
    def _prog(frac: float, msg: str):
        if progress_cb:
            try:
                progress_cb(frac, msg)
            except Exception:
                pass

    topic = args.topic.strip()
    production_id = args.production
    topic_slug = _slugify(topic)
    project_root = PROJECTS_DIR / production_id
    project_root.mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(PROJECTS_DIR)
    learning_sys = get_learning_system()

    _prog(0.05, "Initializing Autonomous Factory Engine...")
    print("======================================================================")
    print("           AUTONOMOUS VIDEO FACTORY — PRODUCTION RUN                  ")
    print("======================================================================")
    print(f"Topic       : {topic}")
    print(f"Production  : {production_id}")
    print(f"Provider    : {args.provider}")
    print(f"Freshness   : {args.freshness}")
    print("======================================================================\n")

    # 1. RESEARCH
    _prog(0.12, "[1/8] Executing Live Research Engine (Phase 10)...")
    print("[1/8] EXECUTING RESEARCH ENGINE (PHASE 10)...")
    research_dir = project_root / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    research_pack = research(
        topic,
        freshness=args.freshness,
        provider_name=args.provider,
        top_n_stories=5,
    )
    print(f"  -> Retrieved {len(research_pack.sources)} sources, {len(research_pack.stories)} stories.")
    if research_pack.stories:
        print(f"  -> Top story: {research_pack.stories[0].headline}")

    # 2. SCRIPT INTELLIGENCE
    _prog(0.25, "[2/8] Synthesizing Natural Script & Voiceover (Phase 11)...")
    print("\n[2/8] SYNTHESIZING NATURAL SCRIPT (PHASE 11)...")
    script_shorts = generate_shorts_script(topic, research_pack)
    script_longform = generate_longform_script(topic, research_pack)

    print(f"  -> Generated {len(script_shorts.sections)} sections ({script_shorts.total_word_count} words, ~{script_shorts.total_duration_seconds:.1f}s)")
    for sec in script_shorts.sections:
        print(f"     [{sec.role.upper()}]: {sec.spoken_text}")

    canonical_script = script_shorts.to_canonical_schema(production_id)
    script_envelope = store.create(
        artifact_type="script",
        production_id=production_id,
        stage="script",
        data=canonical_script,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="autonomous_factory"),
    )
    store.save(script_envelope)
    store.approve("script", production_id, script_envelope.artifact_version)
    print(f"  -> Persisted canonical script: script.v{script_envelope.artifact_version:03d}.json")

    # 3. PACKAGING INTELLIGENCE + LEARNING BOOSTS
    _prog(0.38, "[3/8] Packaging Intelligence & Title Optimization (Phase 12)...")
    print("\n[3/8] PACKAGING INTELLIGENCE & FACTORY LEARNING (PHASE 12 + 14)...")
    topic_package = generate_packaging(
        topic,
        script_shorts=script_shorts,
        research_pack=research_pack,
        script_longform=script_longform,
    )
    # Apply historical learning boosts from factory memory
    boosted_titles = learning_sys.apply_learned_title_boosts(topic_package.title_candidates)
    topic_package.title_candidates = boosted_titles
    if boosted_titles:
        topic_package.selected_title = boosted_titles[0].title
        topic_package.title_score = boosted_titles[0].title_score
        topic_package.curiosity_score = boosted_titles[0].curiosity_score

    print(f"  -> Selected Title  : \"{topic_package.selected_title}\"")
    print(f"  -> Title Score     : {topic_package.title_score:.1f} / 10.0")
    print(f"  -> Curiosity Score : {topic_package.curiosity_score:.1f} / 10.0")
    print(f"  -> Thumbnail Text  : \"{topic_package.thumbnail_text}\"")
    print(f"  -> Thumbnail Prompt: \"{topic_package.thumbnail_prompt[:90]}...\"")

    # Persist topic_package
    brief_dir = project_root / "brief"
    brief_dir.mkdir(parents=True, exist_ok=True)
    pkg_file = brief_dir / "topic_package.latest.json"
    pkg_file.write_text(json.dumps(topic_package.to_dict(), indent=2), "utf-8")

    # 4. SEMANTIC VISUAL PLANNING & DESIGN SYSTEM (PHASE 16)
    _prog(0.50, "[4/8] Semantic Visual Planning & Claim Grounding (Phase 15/16)...")
    print("\n[4/8] SEMANTIC VISUAL PLANNING & EDITORIAL DESIGN SYSTEM (PHASE 16)...")
    prod_state_path = project_root / "production_state.json"
    prod_state = json.loads(prod_state_path.read_text("utf-8")) if prod_state_path.exists() else {}
    prod_state["research_data"] = research_pack.to_dict()

    from production.phase16.design_system import create_default_design_system
    from production.phase16.evidence_contract import extract_evidence_contract
    from production.phase16.sync import sync_phase16_production_artifacts
    from production.phase16.human_qa import audit_production_frames

    design_system = create_default_design_system(production_id, topic)
    bible_json = project_root / "brief" / "visual_style_bible.json"
    bible_json.write_text(json.dumps(design_system.to_dict(), indent=2), "utf-8")
    bible_md = project_root / "brief" / "VISUAL_STYLE_BIBLE.md"
    bible_md.write_text(design_system.generate_style_bible_markdown(), "utf-8")

    plan_data = generate_plan({"data": canonical_script}, prod_state)
    plan_file = project_root / "edit" / "plan.v001.json"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(json.dumps(plan_data, indent=2), "utf-8")
    print(f"  -> Generated {len(plan_data.get('scene_concepts', []))} scene visual concepts with Editorial Intelligence styling.")

    # Setup Production Controller & State
    from production.controller import ProductionController
    controller = ProductionController(projects_root=PROJECTS_DIR)
    try:
        state = controller.state_store.load(production_id)
    except Exception:
        from schemas.models.common import RunMode
        state = controller.state_store.create(
            project_id=production_id,
            pipeline="youtube-short",
            pipeline_version="2.0",
            target_duration=float(canonical_script.get("estimated_duration_seconds", 30.0)),
            aspect_ratio="9:16",
            platform="youtube_shorts",
            style="claude_editorial",
            run_mode=RunMode.AUTO,
            budget_cap=10.0,
        )

    # Ensure proposal_packet exists
    try:
        proposal_env = store.latest("proposal_packet", production_id)
    except Exception:
        proposal_payload = {
            "selected_concept_id": "c1",
            "concepts": [
                {
                    "concept_id": "c1",
                    "hook": "Warehouse robots getting smarter fast",
                    "audience_promise": "Frontier AI robotics breakdown",
                    "narrative_structure": "Editorial documentary",
                    "visual_direction": "Claude Editorial",
                    "tone": "Direct, authoritative",
                    "target_duration": float(canonical_script.get("estimated_duration_seconds", 30.0)),
                    "renderer_family": "explainer",
                    "render_runtime": "remotion",
                    "composition_mode": "atelier",
                },
                {
                    "concept_id": "c2",
                    "hook": "Robots are taking over logistics",
                    "audience_promise": "Autonomous fleet inspection",
                    "narrative_structure": "Cinematic tech review",
                    "visual_direction": "Industrial High-Contrast",
                    "tone": "Provocative",
                    "target_duration": float(canonical_script.get("estimated_duration_seconds", 30.0)),
                    "renderer_family": "cinematic",
                    "render_runtime": "remotion",
                    "composition_mode": "atelier",
                },
            ],
            "decision_log": {
                "selected_concept_id": "c1",
                "decision_reason": "Factory automatic lock",
                "selection_mode": "auto",
                "timestamp": "2026-10-07T00:00:00Z",
                "actor": "system",
                "locked_decisions": {
                    "renderer_family": "explainer",
                    "render_runtime": "remotion",
                    "composition_mode": "atelier",
                },
            },
        }
        proposal_env = store.create(
            "proposal_packet",
            production_id,
            "proposal",
            proposal_payload,
            producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="autonomous_factory"),
        )
        store.save(proposal_env)
        store.approve("proposal_packet", production_id, proposal_env.artifact_version)
    state.set_active_version("proposal_packet", proposal_env.artifact_version)

    # 5. NEURAL TTS & 4-LAYER DEPTH ASSETS (PHASE 18)
    _prog(0.65, "[5/8] Generating Neural TTS & 4-Layer Depth Assets (Phase 18)...")
    print("\n[5/8] GENERATING NEURAL TTS & 4-LAYER DEPTH ASSETS (PHASE 18)...")
    audio_dir = project_root / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    import edge_tts, asyncio
    sections = canonical_script.get("sections", [])
    for idx, sec in enumerate(sections):
        sc_id = f"scene_{idx+1:02d}"
        spoken = sec.get("spoken_text", "")
        if spoken:
            comm = edge_tts.Communicate(spoken, "en-US-JennyNeural")
            asyncio.run(comm.save(str(audio_dir / f"narration_{sc_id}.mp3")))

    # Measure exact audio durations with ffprobe
    def _get_audio_dur(p: Path) -> float:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)]
        try:
            out = subprocess.check_output(cmd, text=True)
            return max(1.5, float(out.strip()))
        except Exception:
            return 5.0

    measured_durations = [
        _get_audio_dur(audio_dir / f"narration_scene_{i+1:02d}.mp3")
        for i in range(len(sections))
    ]

    # Direct canonical 4-layer scenes with mascot bot
    from production.phase18.visual_director import direct_production_scenes
    from production.phase18.character_director import render_character_asset
    from production.phase18.sync import sync_authoritative_artifacts
    from production.phase17.multi_layer_generator import generate_scene_layers
    from production.phase17.style_systems import get_style_system

    active_style = get_style_system("claude_editorial")
    visual_plan = direct_production_scenes(
        production_id=production_id,
        sections=sections,
        topic=topic,
        measured_durations=measured_durations,
        research_context=research_pack.summary if hasattr(research_pack, "summary") else "",
    )

    # Persist physical multi-layer assets & transparent mascot bot
    assets_dir = project_root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    print(f"  -> Directing {len(visual_plan.scenes)} scenes with 4-layer depth & mascot bot.")
    for idx, sc in enumerate(visual_plan.scenes):
        generate_scene_layers(
            scene_index=idx,
            narration=sc.spoken_text or sc.visual_purpose,
            output_dir=assets_dir,
            scene_id=sc.scene_id,
            style=active_style,
            topic=topic,
            subject=sc.subject,
            visual_purpose=sc.visual_purpose,
            visual_metaphor=sc.visual_metaphor,
            narrative_role=sc.narrative_role,
        )
        char_png = assets_dir / f"char_{sc.scene_id}.png"
        render_character_asset(sc.character_spec, char_png)

    # Synchronize and approve all canonical artifacts in authoritative order
    mapped_data = sync_authoritative_artifacts(
        store=store,
        state=state,
        visual_plan=visual_plan,
        script_envelope=script_envelope,
        proposal_envelope=proposal_env,
        style_system=active_style,
        projects_root=PROJECTS_DIR,
    )
    state.set_active_version("script", script_envelope.artifact_version)
    controller.state_store.save(state)
    edit_version = state.get_active_version("edit_decisions")
    print(f"  -> Persisted canonical artifacts: scene_plan, asset_manifest, art_direction, edit_decisions.v{edit_version:03d}.json (Phase 18 Depth & Mascot Enabled).")

    # Build backward-compatible plan_data for downstream reports
    plan_data = {
        "production_id": production_id,
        "topic": topic,
        "scene_concepts": [
            {
                "scene_id": sc.scene_id,
                "section_id": sc.section_id,
                "narrative_role": sc.narrative_role,
                "visual_intent": sc.visual_purpose,
                "visual_mode": "environment",
                "shot_type": sc.shot_type,
                "camera_motion": sc.camera_motion,
                "composition": sc.composition,
                "subject": sc.subject,
                "action": sc.action,
                "environment": sc.environment,
                "visual_prompt": f"{sc.subject} in {sc.environment}",
                "claim_id": f"claim_{sc.scene_id}",
                "claim_type": "capability",
                "entities": [sc.subject],
                "relationship": sc.action,
                "required_visual_evidence": [sc.subject],
                "unacceptable_visuals": [],
                "grounding_level": 3.0,
                "visual_grounding_score": 8.5,
                "claim_coverage_score": 1.0,
            }
            for sc in visual_plan.scenes
        ]
    }

    # 6. COMPOSITION & RENDER
    _prog(0.78, "[6/8] Remotion Engine: Rendering Video & Kinetic Subtitles...")
    print("\n[6/8] REMOTION COMPOSITION & RENDER (PHASE 18)...")
    render_code = cmd_render(production_id)
    if render_code != 0:
        print("  [ERROR] Remotion render failed.")
        return 1
    rendered_mp4 = project_root / "composition" / f"remotion_edit-v{edit_version:03d}.mp4"
    if not rendered_mp4.exists():
        print(f"  [ERROR] Rendered file missing: {rendered_mp4}. Zero fallback permitted.")
        return 1

    print(f"  -> Rendered MP4: {rendered_mp4.name} ({rendered_mp4.stat().st_size / (1024*1024):.1f} MB)")

    # 7. AUTOMATED QA GATES & INDEPENDENT VISUAL JUDGE
    _prog(0.90, "[7/8] Verifying Automated QA Gates & Visual Scorecards...")
    print("\n[7/8] VERIFYING AUTOMATED QA GATES & INDEPENDENT VISUAL JUDGE (PHASE 18)...")
    qa_code = cmd_qa(production_id)
    if qa_code != 0:
        print("  [ERROR] Technical QA gate failed; release blocked.")
        return 1
    qa_report_path = project_root / "qa" / "qa_report.json"
    qa_data = json.loads(qa_report_path.read_text("utf-8")) if qa_report_path.exists() else {}
    passed_checks = sum(1 for c in qa_data.get("checks", {}).values() if c.get("passed"))
    total_checks = len(qa_data.get("checks", {}))
    print(f"  -> Technical QA Gate: {passed_checks}/{total_checks} checks passed.")

    # Phase 18 Strict Independent Visual Judge Release Gate
    from production.phase18.visual_judge import audit_and_enforce_release_gate, VisualGateRejectionError
    try:
        judge_scorecard = audit_and_enforce_release_gate(
            mp4_path=rendered_mp4,
            visual_plan=visual_plan,
            output_dir=project_root / "qa",
        )
        print(f"  -> Independent Visual Judge PASSED: Score = {judge_scorecard.final_score}/10.0 (Grounding: {judge_scorecard.semantic_grounding}, Art: {judge_scorecard.art_direction}, Comp: {judge_scorecard.composition}, Depth: {judge_scorecard.depth_separation})")
    except VisualGateRejectionError as e:
        print(f"  [ERROR] Visual Gate Rejection: {e}")
        return 1

    # Phase 15/15B Claim Grounding Evaluation
    from production.phase15.frame_qa import extract_keyframes_and_evaluate_mp4
    from production.phase15.models import SceneVisualPlan, VisualMode, ClaimType
    scene_plans_for_qa = [
        SceneVisualPlan(
            scene_id=c.get("scene_id", f"scene_{idx+1:02d}"),
            section_id=c.get("section_id", ""),
            narrative_role=c.get("narrative_role", "context"),
            visual_intent=c.get("visual_intent", ""),
            visual_mode=VisualMode(c.get("visual_mode", "environment")),
            shot_type=c.get("shot_type", "medium"),
            camera_motion=c.get("camera_motion", "approach_subject"),
            composition=c.get("composition", "rule_of_thirds"),
            subject=c.get("subject", ""),
            action=c.get("action", ""),
            environment=c.get("environment", ""),
            visual_prompt=c.get("visual_prompt", ""),
            claim_id=c.get("claim_id", ""),
            claim_type=ClaimType(c.get("claim_type")) if c.get("claim_type") in [ct.value for ct in ClaimType] else ClaimType.CAPABILITY,
            entities=c.get("entities", []),
            relationship=c.get("relationship", ""),
            required_visual_evidence=c.get("required_visual_evidence", []),
            unacceptable_visuals=c.get("unacceptable_visuals", []),
            grounding_level=c.get("grounding_level", 3.0),
            visual_grounding_score=c.get("visual_grounding_score", 8.5),
            claim_coverage_score=c.get("claim_coverage_score", 1.0),
        )
        for idx, c in enumerate(plan_data.get("scene_concepts", []))
    ]
    qa_frames_dir = project_root / "qa" / "frames"
    visual_scorecard, keyframe_paths, legacy_sheet = extract_keyframes_and_evaluate_mp4(
        rendered_mp4,
        scene_plans_for_qa,
        qa_frames_dir,
        topic=topic,
    )

    # Phase 16 Human Visual Relevance & Art Direction Consistency Pixel Audit
    contracts_for_qa = [
        extract_evidence_contract(
            narration=c.get("visual_intent", c.get("visual_story", "")),
            scene_id=c.get("scene_id", f"scene_{idx+1:02d}"),
            section_id=c.get("section_id", f"sec_{idx+1:02d}"),
            topic=topic,
            narrative_role=c.get("narrative_role", "context"),
        )
        for idx, c in enumerate(plan_data.get("scene_concepts", []))
    ]
    human_scorecard, contact_sheet = audit_production_frames(
        keyframe_paths,
        contracts_for_qa,
        design_system,
        qa_frames_dir,
    )
    print(f"  -> Human Visual QA: Final Visual Quality = {human_scorecard.final_visual_quality_score}/10.0, Human Relevance = {human_scorecard.overall_human_relevance}/10.0, Art Direction = {human_scorecard.overall_art_direction}/10.0")
    print(f"  -> Contact Sheet Generated: {contact_sheet.name}")

    # Phase 17 Visual Language Scorecard
    from production.phase17.visual_qa import evaluate_visual_language
    vl_eval = evaluate_visual_language(
        project_root,
        plan_data.get("scene_concepts", []),
        mapped_data.get("timeline", []),
        frames_dir=qa_frames_dir,
    )
    print(f"  -> Visual Language QA (Phase 17): Score = {vl_eval.visual_language_score}/10.0 (Environment: {vl_eval.environment_variety_score}, Depth: {vl_eval.depth_parallax_score}, Transitions: {vl_eval.transition_score})")

    qa_data["visual_scorecard"] = visual_scorecard.model_dump()
    qa_data["human_visual_scorecard"] = human_scorecard.model_dump()
    qa_data["visual_language_scorecard"] = vl_eval.to_dict()
    qa_report_path.write_text(json.dumps(qa_data, indent=2), "utf-8")
    (qa_frames_dir / "visual_language_qa_report.json").write_text(json.dumps(vl_eval.to_dict(), indent=2), "utf-8")

    # 8. MULTI-FACTOR EDITORIAL SCORING & RELEASE ASSEMBLY
    _prog(0.98, "[8/8] Assembling Final Package into output/...")
    print("\n[8/8] EDITORIAL SCORING & OUTPUT PACKAGE ASSEMBLY...")
    score_txt = generate_editorial_score(qa_data, mapped_data)
    score_file = project_root / "qa" / f"editorial_score_v{edit_version:03d}.txt"
    score_file.write_text(score_txt, "utf-8")
    print(score_txt)

    # Assemble final release package into output/<topic_slug>/
    release_dir = OUTPUT_DIR / topic_slug
    release_dir.mkdir(parents=True, exist_ok=True)

    dest_mp4 = release_dir / "video.mp4"
    shutil.copy2(rendered_mp4, dest_mp4)
    shutil.copy2(rendered_mp4, release_dir / "final_video.mp4")
    if contact_sheet.exists():
        shutil.copy2(contact_sheet, release_dir / "contact_sheet.png")
        shutil.copy2(contact_sheet, release_dir / "preview.png")
    qa_claim_file = qa_frames_dir / "claim_visual_qa_report.json"
    if qa_claim_file.exists():
        shutil.copy2(qa_claim_file, release_dir / "claim_visual_qa_report.json")
    human_qa_file = qa_frames_dir / "human_visual_qa_report.json"
    if human_qa_file.exists():
        shutil.copy2(human_qa_file, release_dir / "human_visual_qa_report.json")
    if bible_json.exists():
        shutil.copy2(bible_json, release_dir / "visual_style_bible.json")
    vl_qa_file = qa_frames_dir / "visual_language_qa_report.json"
    if vl_qa_file.exists():
        shutil.copy2(vl_qa_file, release_dir / "visual_language_qa_report.json")

    (release_dir / "title.txt").write_text(topic_package.selected_title, "utf-8")
    (release_dir / "description.txt").write_text(topic_package.description, "utf-8")
    (release_dir / "thumbnail_text.txt").write_text(topic_package.thumbnail_text, "utf-8")
    (release_dir / "thumbnail_prompt.txt").write_text(topic_package.thumbnail_prompt, "utf-8")
    vo_script_content = "\n\n".join(
        f"[{sec.get('role', 'SCENE').upper()}]: {sec.get('spoken_text', '')}"
        for sec in canonical_script.get("sections", [])
    )
    (release_dir / "vo_script.txt").write_text(vo_script_content, "utf-8")

    factory_manifest = {
        "topic": topic,
        "production_id": production_id,
        "selected_title": topic_package.selected_title,
        "title_score": topic_package.title_score,
        "curiosity_score": topic_package.curiosity_score,
        "thumbnail_score": topic_package.thumbnail_score,
        "overall_package_score": topic_package.overall_package_score,
        "video_duration_seconds": mapped_data.get("total_duration", 0.0),
        "qa_checks_passed": f"{passed_checks}/{total_checks}",
        "produced_at": datetime.now(timezone.utc).isoformat(),
        "release_assets": {
            "video_mp4": str(dest_mp4.name),
            "title_txt": "title.txt",
            "description_txt": "description.txt",
            "thumbnail_prompt_txt": "thumbnail_prompt.txt",
        },
    }
    (release_dir / "factory_manifest.json").write_text(json.dumps(factory_manifest, indent=2), "utf-8")
    legacy_manifest = {
        "title": topic_package.selected_title,
        "source": "autonomous-factory-v2",
        "style": "claude_editorial",
        "scenes": [
            {"scene_id": s.get("scene_id"), "end_seconds": s.get("end", 0.0), "asset": "preview.png"}
            for s in mapped_data.get("timeline", [])
        ],
        "video": "final_video.mp4",
        "preview": "preview.png",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (release_dir / "manifest.json").write_text(json.dumps(legacy_manifest, indent=2), "utf-8")

    _prog(1.0, "Production Complete")
    print(f"\n======================================================================")
    print(f"   AUTONOMOUS FACTORY PRODUCTION COMPLETE: 100% READY FOR RELEASE     ")
    print(f"======================================================================")
    print(f"Output Directory : {release_dir}")
    print(f"Final Video      : {dest_mp4} ({dest_mp4.stat().st_size / (1024*1024):.1f} MB)")
    print(f"Selected Title   : {topic_package.selected_title}")
    print(f"Thumbnail Text   : {topic_package.thumbnail_text}")
    print(f"Manifest         : {release_dir / 'factory_manifest.json'}")
    print(f"======================================================================\n")
    return 0


def cmd_record_metrics(args: argparse.Namespace) -> int:
    learning_sys = get_learning_system()
    metrics = VideoMetrics(
        views=args.views,
        ctr_percent=args.ctr,
        avg_watch_percentage=args.watch_pct,
        subscribers_gained=args.subs,
        retention_dropoff_3s=args.retention_3s,
    )
    rec = learning_sys.record_video_metrics(
        production_id=args.production,
        topic=args.topic,
        title=args.title,
        title_angle=args.angle,
        metrics=metrics,
        hook_text=args.hook,
    )
    print("\nRecorded video performance in Factory Learning Memory:")
    print(f"  Production ID  : {rec.production_id}")
    print(f"  Title          : \"{rec.selected_title}\"")
    print(f"  Composite Score: {rec.composite_performance_score:.1f} / 100.0")
    print(f"  Views          : {rec.metrics.views:,}")
    print(f"  CTR            : {rec.metrics.ctr_percent:.1f}%")
    print(f"  Avg Watch %    : {rec.metrics.avg_watch_percentage:.1f}%")
    print(f"  Subs Gained    : {rec.metrics.subscribers_gained:,}")
    return 0


def cmd_insights() -> int:
    learning_sys = get_learning_system()
    insights = learning_sys.get_learning_insights()
    print("\n======================================================================")
    print("                 FACTORY LEARNING INTELLIGENCE INSIGHTS                ")
    print("======================================================================")
    print(f"Total Videos Analyzed : {insights.total_videos_analyzed}")
    print("\nTop Performing Title Angles:")
    for a in insights.top_title_angles:
        print(f"  - {a['angle']:<18} | Count: {a['count']} | Avg CTR: {a['avg_ctr']:.1f}% | Avg Score: {a['avg_score']:.1f}")

    print("\nTop Performing Hook Styles:")
    for h in insights.top_hook_patterns:
        print(f"  - {h['style']:<18} | Count: {h['count']} | Avg Watch %: {h['avg_watch_percentage']:.1f}%")

    print("\nTop Performing Visual Styles:")
    for v in insights.top_visual_styles:
        print(f"  - {v['visual_style']:<25} | Count: {v['count']} | Avg Retention: {v['avg_retention']:.1f}%")

    print(f"\nWinning Keywords in High-Retention Videos:")
    print(f"  {', '.join(insights.winning_keywords)}")
    print(f"\nRecommended Visual Direction:")
    print(f"  {insights.recommended_visual_direction}")
    print("======================================================================\n")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Autonomous Video Factory (Phase 13 + 14)")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # produce
    p_prod = subparsers.add_parser("produce", help="Run autonomous video production end-to-end")
    p_prod.add_argument("--topic", required=True, help="Video topic to research, script, package, and render")
    p_prod.add_argument("--production", default="proj_3e27bd7a", help="Production ID (default: proj_3e27bd7a)")
    p_prod.add_argument("--provider", default="multi", choices=["all", "multi", "google_news", "official", "reddit", "brave"])
    p_prod.add_argument("--freshness", default="7d", choices=["1d", "7d", "30d", "1y"])

    # record-metrics
    p_rec = subparsers.add_parser("record-metrics", help="Record real-world YouTube analytics for a video")
    p_rec.add_argument("--production", required=True, help="Production ID")
    p_rec.add_argument("--topic", required=True, help="Video topic")
    p_rec.add_argument("--title", required=True, help="Published video title")
    p_rec.add_argument("--angle", default="shock_revelation", help="Title angle")
    p_rec.add_argument("--hook", default="", help="Spoken hook")
    p_rec.add_argument("--views", type=int, required=True, help="Total view count")
    p_rec.add_argument("--ctr", type=float, required=True, help="Actual CTR (%)")
    p_rec.add_argument("--watch-pct", type=float, required=True, help="Average percentage viewed (%)")
    p_rec.add_argument("--subs", type=int, default=0, help="Subscribers gained")
    p_rec.add_argument("--retention-3s", type=float, default=85.0, help="Retention at 3s (%)")

    # insights
    subparsers.add_parser("insights", help="Display aggregated factory learning insights")

    args = parser.parse_args()

    if args.subcommand == "produce":
        sys.exit(cmd_produce(args))
    elif args.subcommand == "record-metrics":
        sys.exit(cmd_record_metrics(args))
    elif args.subcommand == "insights":
        sys.exit(cmd_insights())


if __name__ == "__main__":
    main()
