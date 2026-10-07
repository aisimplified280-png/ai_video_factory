import argparse
import sys
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from production.phase9.planner import generate_plan
from production.phase9.mapper import map_edit_decisions
from production.phase9.scoring import generate_editorial_score
from production.artifact_store import ArtifactStore
from scripts.run_local_production import cmd_render, cmd_qa

def main():
    parser = argparse.ArgumentParser(description="Phase 9 Produce CLI")
    parser.add_argument("command", choices=["produce"])
    parser.add_argument("--script", required=True, help="Path to script artifact (e.g. script.v001.json)")
    parser.add_argument("--production", default="proj_3e27bd7a", help="Production ID")
    args = parser.parse_args()

    if args.command == "produce":
        produce(args)

def produce(args):
    projects_dir = ROOT / "projects"
    project_root = projects_dir / args.production
    
    script_path = Path(args.script)
    if not script_path.is_absolute():
        script_path = ROOT / script_path
        
    store = ArtifactStore(projects_dir)
    
    # 1. Semantic Analysis & Editorial Plan (Phase 9.1)
    print("\n--- PHASE 9.1: EDITORIAL PLANNER ---")
    script_data = json.loads(script_path.read_text("utf-8"))
    
    prod_state_path = project_root / "production_state.json"
    prod_state = json.loads(prod_state_path.read_text("utf-8")) if prod_state_path.exists() else {}
    
    # Load Phase 10 research pack if available
    research_dir = project_root / "research"
    research_pack_path = None
    if (research_dir / "research_pack.latest.json").exists():
        try:
            latest_meta = json.loads((research_dir / "research_pack.latest.json").read_text("utf-8"))
            if "file" in latest_meta and (research_dir / latest_meta["file"]).exists():
                research_pack_path = research_dir / latest_meta["file"]
        except Exception:
            pass
    if not research_pack_path and (research_dir / "research_pack.json").exists():
        research_pack_path = research_dir / "research_pack.json"
    if not research_pack_path and research_dir.exists():
        v_files = sorted(research_dir.glob("research_pack.v*.json"))
        if v_files:
            research_pack_path = v_files[-1]

    if research_pack_path and research_pack_path.exists():
        try:
            prod_state["research_data"] = json.loads(research_pack_path.read_text("utf-8"))
            print(f"Loaded research pack: {research_pack_path.name}")
        except Exception:
            pass
        
    plan_data = generate_plan(script_data, prod_state)
    
    # Save plan.v001.json
    plan_file = project_root / "edit" / "plan.v001.json"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(json.dumps(plan_data, indent=2), "utf-8")
    print(f"Generated {plan_file.name}")
    
    # 2. Edit Mapping (Phase 9.2)
    print("\n--- PHASE 9.2: EDIT DECISION MAPPING ---")
    # Read existing edit_decisions.v001.json
    v1_env = store.latest("edit_decisions", args.production)
    if not v1_env:
        print("ERROR: Could not find edit_decisions.v001.json!")
        sys.exit(1)
    
    v2_data = map_edit_decisions(plan_data, v1_env.data, project_root)
    
    # Persist as v002
    v2_env = store.create(
        "edit_decisions", 
        args.production, 
        "edit", 
        v2_data, 
        producer={"kind": "system", "provider": "cli"},
        metadata={"lineage": {"parent": v1_env.metadata.get("lineage", {}).get("parent", ""), "plan": "plan.v001.json"}}
    )
    store.save(v2_env)
    
    v2_env = store.approve("edit_decisions", args.production, v2_env.artifact_version)
    
    # Update active artifact in ProductionState so the router picks it up
    from production.controller import ProductionController
    controller = ProductionController(projects_root=projects_dir)
    state = controller.state_store.load(args.production)
    state.set_active_version("edit_decisions", v2_env.artifact_version)
    controller.state_store.save(state)
    
    print(f"Generated edit_decisions.v00{v2_env.artifact_version}.json (Hash: {v2_env.content_hash})")
    
    # 3. Existing Renderer (Phase 9.3)
    print("\n--- PHASE 9.3: RENDER MP4 ---")
    # We run the existing Remotion render by patching the production state or just invoking cmd_render
    # cmd_render implicitly uses `store.latest("edit_decisions")` which is now v002!
    code = cmd_render(args.production)
    if code != 0:
        print("ERROR: Render failed.")
        sys.exit(1)
        
    # We must rename remotion_edit-v002.mp4 to remotion_edit-v003.mp4 if required by spec, or just leave it.
    # The artifact store version is v002. So it creates remotion_edit-v002.mp4.
    
    # 4. QA (Phase 9.4)
    print("\n--- PHASE 9.4: QA CHECK ---")
    code = cmd_qa(args.production)
    if code != 0:
        print("ERROR: QA failed.")
        sys.exit(1)
    print("\n--- PHASE 9.5: EDITORIAL SCORING ---")
    qa_report_path = project_root / "qa" / "qa_report.json"
    if qa_report_path.exists():
        qa_data = json.loads(qa_report_path.read_text("utf-8"))
        score_txt = generate_editorial_score(qa_data, v2_data)
        score_file = project_root / "qa" / f"editorial_score_v{v2_env.artifact_version:03d}.txt"
        score_file.write_text(score_txt, "utf-8")
        print(f"Generated {score_file.name}")
        print(score_txt)
    else:
        print("ERROR: QA report not found for scoring.")
        sys.exit(1)
        
    print("\n--- PHASE 9 COMPLETED ---")
    print(f"Check output MP4 at {project_root / 'composition' / f'remotion_edit-v{v2_env.artifact_version:03d}.mp4'}")

if __name__ == "__main__":
    main()
