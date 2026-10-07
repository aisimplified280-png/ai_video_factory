"""Live smoke benchmark script for Phase 4 (brief -> research -> proposal -> art_direction -> script -> scene_plan).

Accepts --topic and executes real or configured pipeline to produce real artifacts in projects/<production_id>/
Outputs editorial story progression, visual technique sequences, variety governor metrics, and continuity analysis.

Usage:
    python scripts/smoke_phase4.py --topic "How OpenAI Built An Empire"
    python scripts/smoke_phase4.py --topic "How ChatGPT Agents Work"
    python scripts/smoke_phase4.py --topic "Why AI Models Need More Compute"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import envfile
envfile.load_dotenv()

from production.controller import ProductionController
from production.stage_registry import default_production_registry
from schemas.models.common import RunMode


def print_storyboard_editorial(script_data: dict, scene_plan_data: dict, art_data: dict) -> None:
    """Print editorial director story progression and visual analysis."""
    print("\n" + "=" * 80)
    print(" EDITORIAL STORY PROGRESSION & VISUAL STRATEGY")
    print("=" * 80)

    # Narrative arc & Hook
    print(f"\n[SCRIPT OVERVIEW]")
    print(f"  Title:              {script_data.get('title')}")
    print(f"  Target Duration:    {script_data.get('target_duration', 45.0)}s")
    print(f"  Estimated Duration: {script_data.get('estimated_duration', 0.0):.1f}s")
    print(f"  Spoken Word Count:  {script_data.get('spoken_word_count', 0)} words")
    print(f"  Timing Status:      {script_data.get('timing_status', 'unknown').upper()}")
    cta_val = script_data.get('cta')
    cta_text = cta_val.get('spoken_text') if isinstance(cta_val, dict) else str(cta_val or "")
    print(f"  Hook:               \"{script_data.get('hook')}\"")
    print(f"  CTA:                \"{cta_text}\"")

    # Art direction anchors
    print(f"\n[ART DIRECTION IDENTITY]")
    print(f"  Visual Metaphor:    {art_data.get('visual_metaphor')}")
    print(f"  Design Read:        {art_data.get('design_read')}")
    print(f"  Signature Device:   {art_data.get('signature_device')}")
    print(f"  Visual Variance:    {art_data.get('visual_variance')}/10 | Motion: {art_data.get('motion_intensity')}/10")

    # Progression Map
    scenes = scene_plan_data.get("scenes", [])
    print(f"\n[STORY PROGRESSION ARC ({len(scenes)} Scenes)]")
    narrative_steps = [f"[{s.get('narrative_role', '').upper()}]" for s in scenes]
    print("  " + " -> ".join(narrative_steps))

    print(f"\n[VISUAL TECHNIQUE EVOLUTION]")
    technique_steps = [f"{s.get('visual_technique', '')}" for s in scenes]
    print("  " + " -> ".join(technique_steps))

    # Scene by scene editorial breakdown
    print(f"\n[EDITORIAL SCENE BREAKDOWN]")
    for s in scenes:
        sid = s.get("scene_id")
        start = s.get("start_seconds", 0.0)
        end = s.get("end_seconds", 0.0)
        dur = end - start
        role = s.get("narrative_role", "").upper()
        stype = s.get("type", "scene")
        tech = s.get("visual_technique")
        shots = s.get("shots", [])

        print(f"\n  --- SCENE {sid} ({start:.1f}s - {end:.1f}s | {dur:.1f}s) [{role} / {stype}] ---")
        print(f"    Technique:          {tech}")
        print(f"    Viewer Understands: {s.get('viewer_understanding')}")
        print(f"    Visual Purpose:     {s.get('visual_purpose')}")
        print(f"    Subject & Action:   {s.get('subject')} -- {s.get('subject_action')}")
        print(f"    Environment:        {s.get('environment')}")
        print(f"    Composition:        {s.get('composition_intent')} (Camera: {s.get('camera_intent')} | Motion: {s.get('motion_intent')})")
        print(f"    Text Density:       {s.get('text_density', 'medium')} | Continuity: {s.get('continuity_from_previous', 'origin')} -> {s.get('continuity_to_next', 'next')}")
        if shots:
            shot_items = []
            for shot in shots:
                s_dur = (shot.get("end", 0.0) or shot.get("end_seconds", 0.0)) - (shot.get("start", 0.0) or shot.get("start_seconds", 0.0))
                shot_items.append(f"{shot.get('shot_id')}({s_dur:.1f}s: {shot.get('camera_intent')})")
            print(f"    Shot Rhythm ({len(shots)}):    {', '.join(shot_items)}")

    # Variety Governor Metrics
    print(f"\n[VARIETY GOVERNOR & DIVERSITY METRICS]")
    print(f"  Variety Score:      {scene_plan_data.get('variety_score', 0):.1f} / 100.0")
    unique_types = scene_plan_data.get("metrics", {}).get("unique_scene_types", len(set(s.get("type") for s in scenes)))
    unique_techs = scene_plan_data.get("metrics", {}).get("unique_techniques", len(set(s.get("visual_technique") for s in scenes)))
    consec_types = scene_plan_data.get("metrics", {}).get("max_consecutive_types", 1)
    consec_techs = scene_plan_data.get("metrics", {}).get("max_consecutive_techniques", 1)

    print(f"  Distinct Scene Types:    {unique_types} (Max Consecutive: {consec_types})")
    print(f"  Distinct Techniques:     {unique_techs} (Max Consecutive: {consec_techs})")
    print(f"  CTA Guard Final Scene:   {'PASS' if scenes[-1].get('narrative_role') == 'cta' else 'FAIL'}")


DEFAULT_TOPIC_SOURCES = {
    "How OpenAI Built An Empire": [
        "https://en.wikipedia.org/wiki/OpenAI",
        "https://arxiv.org/abs/2005.14165",
        "https://en.wikipedia.org/wiki/Generative_pre-trained_transformer",
    ],
    "How ChatGPT Agents Work": [
        "https://en.wikipedia.org/wiki/Intelligent_agent",
        "https://arxiv.org/abs/2304.03442",
        "https://en.wikipedia.org/wiki/Prompt_engineering",
    ],
    "Why AI Models Need More Compute": [
        "https://arxiv.org/abs/2001.08361",
        "https://en.wikipedia.org/wiki/AI_accelerator",
        "https://en.wikipedia.org/wiki/Supercomputer",
    ],
}


def run_benchmark(topic: str, pipeline: str = "youtube-short", depth: str = "standard", sources: str | None = None) -> dict:
    """Execute stages through scene_plan and return artifacts."""
    projects_dir = ROOT / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    controller = ProductionController(
        projects_root=projects_dir,
        registry=default_production_registry,
    )
    store = controller.artifact_store

    options = {
        "research_depth": depth,
        "run_mode": RunMode.AUTO.value,
    }
    if sources:
        options["source_urls"] = [s.strip() for s in sources.split(",") if s.strip()]
    elif topic in DEFAULT_TOPIC_SOURCES:
        options["source_urls"] = DEFAULT_TOPIC_SOURCES[topic]

    # 1. Start
    state = controller.start(topic=topic, pipeline=pipeline, options=options)
    pid = state.project_id

    # 2. Research
    res_res = controller.run_stage(pid, "research", options=options)
    if res_res.status.value not in ("ready", "waiting_approval"):
        raise RuntimeError(f"Research failed: {res_res.errors}")
    if res_res.status.value == "waiting_approval":
        controller.approve(pid, stage_name="research")

    # 3. Proposal
    res_prop = controller.run_stage(pid, "proposal")
    if res_prop.status.value not in ("ready", "waiting_approval"):
        raise RuntimeError(f"Proposal failed: {res_prop.errors}")
    if res_prop.status.value == "waiting_approval":
        controller.approve(pid, stage_name="proposal")

    # 4. Art Direction
    res_art = controller.run_stage(pid, "art_direction")
    if res_art.status.value not in ("ready", "waiting_approval"):
        raise RuntimeError(f"Art direction failed: {res_art.errors}")
    if res_art.status.value == "waiting_approval":
        controller.approve(pid, stage_name="art_direction")

    # 5. Script
    res_script = controller.run_stage(pid, "script")
    if res_script.status.value not in ("ready", "waiting_approval"):
        raise RuntimeError(f"Script stage failed: {res_script.errors}")
    if res_script.status.value == "waiting_approval":
        controller.approve(pid, stage_name="script")

    # 6. Scene Plan
    res_sp = controller.run_stage(pid, "scene_plan")
    if res_sp.status.value not in ("ready", "waiting_approval"):
        raise RuntimeError(f"Scene plan stage failed: {res_sp.errors}")
    if res_sp.status.value == "waiting_approval":
        controller.approve(pid, stage_name="scene_plan")

    # Fetch artifacts
    brief_env = store.latest("research_brief", pid)
    prop_env = store.latest("proposal_packet", pid)
    art_env = store.latest("art_direction", pid)
    script_env = store.latest("script", pid)
    scene_env = store.latest("scene_plan", pid)

    return {
        "project_id": pid,
        "topic": topic,
        "brief": brief_env.data if brief_env else {},
        "proposal": prop_env.data if prop_env else {},
        "art_direction": art_env.data if art_env else {},
        "script": script_env.data if script_env else {},
        "scene_plan": scene_env.data if scene_env else {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 4 Live Smoke Benchmark")
    parser.add_argument("--topic", default="How OpenAI Built An Empire", help="Video topic to run")
    parser.add_argument("--pipeline", default="youtube-short", help="Pipeline name")
    parser.add_argument("--depth", default="standard", choices=["minimal", "standard", "deep"], help="Research depth")
    parser.add_argument("--sources", help="Optional comma-separated URLs")
    args = parser.parse_args()

    print(f"\n========================================================")
    print(f" PHASE 4 CREATIVE BENCHMARK RUNNER")
    print(f" Topic:    {args.topic}")
    print(f" Pipeline: {args.pipeline}")
    print(f" Depth:    {args.depth}")
    print(f"========================================================\n")

    try:
        results = run_benchmark(
            topic=args.topic,
            pipeline=args.pipeline,
            depth=args.depth,
            sources=args.sources,
        )
        print_storyboard_editorial(
            script_data=results["script"],
            scene_plan_data=results["scene_plan"],
            art_data=results["art_direction"],
        )
        print("\n" + "=" * 80)
        print(f" SUCCESS: Phase 4 completed for project {results['project_id']}")
        print(f" Artifacts: projects/{results['project_id']}")
        print("=" * 80 + "\n")
        return 0
    except Exception as e:
        print(f"\n[FAIL] Phase 4 benchmark encountered error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
