"""Live smoke test script for Phase 3 (brief -> research -> proposal -> art_direction).

Accepts --topic and executes real providers to produce artifacts in projects/<production_id>/
NOT executed during pytest.

Usage:
    python scripts/smoke_phase3.py --topic "How AI Agents Work"
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 3 Live Smoke Integration Test")
    parser.add_argument("--topic", default="How AI Agents Work", help="Video topic to research and develop")
    parser.add_argument("--pipeline", default="youtube-short", help="Pipeline name")
    parser.add_argument("--depth", default="standard", choices=["minimal", "standard", "deep"], help="Research depth")
    parser.add_argument("--sources", help="Optional comma-separated URLs")
    args = parser.parse_args()

    print(f"\n========================================================")
    print(f" PHASE 3 LIVE SMOKE TEST")
    print(f" Topic: {args.topic}")
    print(f" Pipeline: {args.pipeline}")
    print(f" Depth: {args.depth}")
    print(f"========================================================\n")

    projects_dir = ROOT / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    controller = ProductionController(
        projects_root=projects_dir,
        registry=default_production_registry,
    )

    options = {
        "research_depth": args.depth,
        "run_mode": RunMode.AUTO.value,
    }
    if args.sources:
        options["source_urls"] = [s.strip() for s in args.sources.split(",") if s.strip()]

    # 1. Start production (creates brief)
    print("[1/4] Starting production and generating seed brief...")
    state = controller.start(topic=args.topic, pipeline=args.pipeline, options=options)
    print(f"      Project ID: {state.project_id}")

    # 2. Execute Research Stage
    print("\n[2/4] Executing Research Stage...")
    res_result = controller.run_stage(state.project_id, "research", options=options)
    print(f"      Status: {res_result.status.value.upper()}")
    print(f"      Message: {res_result.message}")
    if res_result.status.value not in ("ready", "waiting_approval"):
        print(f"[FAIL] Research stage stopped: {res_result.errors}")
        return 1

    # 3. Execute Proposal Stage
    print("\n[3/4] Executing Proposal Stage...")
    prop_result = controller.run_stage(state.project_id, "proposal")
    print(f"      Status: {prop_result.status.value.upper()}")
    print(f"      Message: {prop_result.message}")
    if prop_result.status.value not in ("ready", "waiting_approval"):
        print(f"[FAIL] Proposal stage stopped: {prop_result.errors}")
        return 1

    # 4. Execute Art Direction Stage
    print("\n[4/4] Executing Art Direction Stage...")
    art_result = controller.run_stage(state.project_id, "art_direction")
    print(f"      Status: {art_result.status.value.upper()}")
    print(f"      Message: {art_result.message}")
    if art_result.status.value not in ("ready", "waiting_approval"):
        print(f"[FAIL] Art direction stage stopped: {art_result.errors}")
        return 1

    print("\n========================================================")
    print(f" SUCCESS: Phase 3 pipeline completed for project {state.project_id}")
    print(f" Artifacts created in: {projects_dir / state.project_id}")
    print("========================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
