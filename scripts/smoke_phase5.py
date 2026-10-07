"""Live smoke benchmark script for Phase 5 (brief -> research -> proposal -> art_direction -> script -> scene_plan -> assets).

Executes full agentic pipeline to produce real visual assets, technical/semantic QA reports,
continuity tracking, provider selection, and an asset contact sheet.

Usage:
    python scripts/smoke_phase5.py --topic "How OpenAI Built An Empire"
    python scripts/smoke_phase5.py --topic "Why AI Models Need More Compute"
"""
from __future__ import annotations

import argparse
import json
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


def print_asset_intelligence_report(
    manifest_data: dict,
    review_data: dict,
    gen_data: dict,
    art_data: dict,
    scene_plan_data: dict,
    project_dir: Path,
) -> None:
    """Print comprehensive Phase 5 Asset Intelligence summary."""
    print("\n" + "=" * 80)
    print(" PHASE 5: ASSET INTELLIGENCE & PRODUCTION BENCHMARK REPORT")
    print("=" * 80)

    # Overview
    assets = manifest_data.get("assets", [])
    print(f"\n[ASSET MANIFEST OVERVIEW]")
    print(f"  Production ID:       {manifest_data.get('production_id')}")
    print(f"  Total Assets:        {len(assets)}")
    print(f"  Visual Metaphor:     {art_data.get('visual_metaphor')}")
    print(f"  Signature Device:    {art_data.get('signature_device')}")

    # Asset medium breakdown
    type_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    provider_counts: dict[str, int] = {}
    for ast in assets:
        t = ast.get("type", "unknown")
        s = ast.get("source", "unknown")
        p = ast.get("provider", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
        source_counts[s] = source_counts.get(s, 0) + 1
        provider_counts[p] = provider_counts.get(p, 0) + 1

    print(f"\n[MEDIUM DIVERSITY (ANTI-HOMOGENEITY CHECK)]")
    for t, c in sorted(type_counts.items()):
        pct = (c / len(assets) * 100) if assets else 0
        print(f"  - {t:<15}: {c:>2} ({pct:>5.1f}%)")

    print(f"\n[SOURCE STRATEGY]")
    for s, c in sorted(source_counts.items()):
        print(f"  - {s:<15}: {c:>2}")

    print(f"\n[PROVIDERS USED]")
    for p, c in sorted(provider_counts.items()):
        print(f"  - {p:<15}: {c:>2}")

    # Cost & Execution
    print(f"\n[FINANCIAL AUDIT]")
    print(f"  Total Estimated Cost: ${gen_data.get('total_estimated_cost', 0.0):.4f}")
    print(f"  Total Actual Cost:    ${gen_data.get('total_actual_cost', 0.0):.4f}")
    print(f"  Total Gen Time:       {gen_data.get('total_generation_time_s', 0.0):.2f}s")
    print(f"  Budget Status:        {'PASSED' if not gen_data.get('budget_blocked') else 'BLOCKED'}")

    # Asset item table
    print(f"\n[ASSET SPECIFICATIONS & PROVENANCE]")
    print("-" * 80)
    for idx, ast in enumerate(assets, 1):
        aid = ast.get("asset_id")
        sid = ast.get("scene_id")
        atype = ast.get("type")
        source = ast.get("source")
        provider = ast.get("provider")
        purpose = ast.get("purpose")
        subject = ast.get("subject")
        prompt = ast.get("prompt") or "(native declarative spec)"
        fpath = ast.get("file_path")
        refs = ast.get("reference_assets", [])
        status = ast.get("status")

        # Review match
        rev = next((r for r in review_data.get("reviews", []) if r.get("asset_id") == aid), {})
        tech_score = rev.get("technical_score", 0.0)
        sem_score = rev.get("semantic_fit", 0.0)
        cont_score = rev.get("continuity_fit", 0.0)
        rev_status = rev.get("status", "unknown").upper()

        print(f"\nAsset #{idx:02d}: {aid} [Scene: {sid}] -> {atype.upper()} via {provider} ({source})")
        print(f"  Purpose:      \"{purpose}\"")
        print(f"  Subject:      {subject}")
        if refs:
            print(f"  Continuity:   References prior asset {refs} (Score: {cont_score:.1f})")
        print(f"  Prompt/Spec:  {prompt[:120]}..." if len(prompt) > 120 else f"  Prompt/Spec:  {prompt}")
        print(f"  File:         {Path(fpath).name if fpath else 'None'}")
        print(f"  QA Review:    Tech: {tech_score:.1f} | Semantic: {sem_score:.1f} | Result: [{rev_status}]")
        if rev.get("findings"):
            print(f"  Findings:     {', '.join(rev.get('findings'))}")

    # Critical anti-template test: compare 3 scenes
    if len(assets) >= 3:
        print("\n" + "=" * 80)
        print(" CRITICAL ANTI-TEMPLATE VERIFICATION (3 SCENES COMPARISON)")
        print("=" * 80)
        sample_indices = [0, len(assets) // 2, len(assets) - 1]
        for i in sample_indices:
            a = assets[i]
            print(f"\nScene {a.get('scene_id')}:")
            print(f"  Role/Purpose: {a.get('purpose')}")
            print(f"  Subject:      {a.get('subject')}")
            print(f"  Medium:       {a.get('type')} ({a.get('source')})")
            print(f"  Action/Spec:  {a.get('subject_action')}")

    # Artifact paths
    print("\n" + "=" * 80)
    print(" ARTIFACT OUTPUTS & INSPECTION")
    print("=" * 80)
    assets_dir = project_dir / "assets"
    print(f"  Asset Directory:     {assets_dir}")
    print(f"  Asset Manifest:      {assets_dir / 'asset_manifest.v001.json'}")
    print(f"  Review Report:       {assets_dir / 'asset_review_report.json'}")
    print(f"  Generation Report:   {assets_dir / 'asset_generation_report.json'}")
    contact_sheet_html = assets_dir / "contact_sheet.html"
    contact_sheet_png = assets_dir / "contact_sheet.png"
    if contact_sheet_html.exists():
        print(f"  Contact Sheet HTML:  {contact_sheet_html}")
    if contact_sheet_png.exists():
        print(f"  Contact Sheet Image: {contact_sheet_png}")
    print("=" * 80 + "\n")


DEFAULT_TOPIC_SOURCES: dict[str, list[str]] = {
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


def run_smoke(topic: str, pipeline_name: str = "youtube-short") -> None:
    print(f"\n>>> Running Phase 5 Smoke Benchmark for: '{topic}'")
    print(f">>> Pipeline: {pipeline_name}\n")

    projects_dir = ROOT / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    controller = ProductionController(
        projects_root=projects_dir,
        registry=default_production_registry,
    )
    store = controller.artifact_store

    options = {
        "research_depth": "standard",
        "run_mode": RunMode.AUTO.value,
    }
    if topic in DEFAULT_TOPIC_SOURCES:
        options["source_urls"] = DEFAULT_TOPIC_SOURCES[topic]

    # 1. Start production
    state = controller.start(topic=topic, pipeline=pipeline_name, options=options)
    pid = state.project_id
    print(f"Production initialized: {pid}")
    project_dir = projects_dir / pid

    # 2. Execute stages sequentially
    stages = ["research", "proposal", "art_direction", "script", "scene_plan", "assets"]
    for stage_name in stages:
        print(f"Executing stage: [{stage_name}]...")
        res = controller.run_stage(pid, stage_name, options=options)
        if res.status.value not in ("ready", "waiting_approval"):
            print(f"ERROR in stage [{stage_name}]: {res.errors}")
            sys.exit(1)
        if res.status.value == "waiting_approval":
            controller.approve(pid, stage_name=stage_name)
        print(f"  -> [{stage_name}] completed successfully (Status: {res.status.value})")

    # Load artifacts and reports for reporting
    manifest_art = store.latest("asset_manifest", pid)
    art_dir_art = store.latest("art_direction", pid)
    scene_plan_art = store.latest("scene_plan", pid)

    manifest_data = manifest_art.data if manifest_art else {}
    art_data = art_dir_art.data if art_dir_art else {}
    scene_plan_data = scene_plan_art.data if scene_plan_art else {}

    review_path = project_dir / "assets" / "asset_review_report.json"
    review_data = json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else {}

    gen_path = project_dir / "assets" / "asset_generation_report.json"
    gen_data = json.loads(gen_path.read_text(encoding="utf-8")) if gen_path.exists() else {}

    # Print summary
    print_asset_intelligence_report(
        manifest_data=manifest_data,
        review_data=review_data,
        gen_data=gen_data,
        art_data=art_data,
        scene_plan_data=scene_plan_data,
        project_dir=project_dir,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 5 Asset Intelligence Smoke Benchmark")
    parser.add_argument("--topic", default="How OpenAI Built An Empire", help="Video topic")
    parser.add_argument("--pipeline", default="youtube-short", help="Pipeline name")
    args = parser.parse_args()

    run_smoke(args.topic, args.pipeline)
