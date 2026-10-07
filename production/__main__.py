"""CLI for production infrastructure and ProductionController.

Pipeline & Artifact Commands:
  validate-pipeline <name>   Validate a pipeline definition YAML
  inspect-pipeline <name>    Print pipeline stage topology, policies, and contracts
  list-pipelines             List all available pipeline definitions
  artifact-validate <file>   Validate a JSON artifact file against its schema and envelope
  artifact-hash <file>       Compute canonical deterministic SHA-256 hash of artifact data

Production Controller Commands:
  start                      Start a new production run
  status <project_id>        Inspect production state, active artifacts, and checkpoints
  resume <project_id>        Resume production after crash or interruption
  run <project_id>           Execute next runnable stage (or --until-blocked)
  approve <project_id>       Approve stage output
  reject <project_id>        Reject stage output and trigger revision
  retry <project_id>         Retry a failed stage with same inputs
  revise <project_id>        Revise a stage with feedback notes
  abort <project_id>         Cancel/abort a production
  rerender <project_id>      Validate rerender plan feasibility
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from production.pipeline_loader import PipelineLoader, PipelineNotFoundError, PipelineValidationError
from production.pipeline_validator import PipelineValidator
from production.artifact_store import ArtifactStore, ArtifactStoreError
from production.controller import ProductionController, ControllerError


def cmd_validate_pipeline(args: argparse.Namespace) -> int:
    loader = PipelineLoader()
    validator = PipelineValidator()
    try:
        defn = loader.load(args.name)
        errors = validator.validate(defn)
        if errors:
            print(f"[ERROR] Pipeline '{args.name}' FAILED validation:")
            for e in errors:
                print(f"  - {e}")
            return 1
        print(f"[OK] Pipeline '{args.name}' (v{defn.version}) is VALID.")
        print(f"   Stages: {len(defn.stages)} ({', '.join(defn.all_stage_names())})")
        return 0
    except PipelineNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    except PipelineValidationError as e:
        print(f"[ERROR] Validation error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 3


def cmd_inspect_pipeline(args: argparse.Namespace) -> int:
    loader = PipelineLoader()
    try:
        defn = loader.load(args.name)
        print(f"============================================================")
        print(f" Pipeline: {defn.name} (v{defn.version})")
        print(f" Description: {defn.description}")
        print(f" Target Duration: {defn.target_duration}s | Platform: {defn.platform}")
        print(f" Runtime Policy: {defn.render_runtime_policy.primary} (fallback: {defn.render_runtime_policy.fallback}, strict: {defn.render_runtime_policy.strict})")
        print(f" Budget Cap: ${defn.budget_policy.budget_cap:.2f}")
        print(f"============================================================")
        print(f"STAGE TOPOLOGY & CONTRACTS:")
        for idx, sname in enumerate(defn.all_stage_names(), 1):
            s = defn.stages[sname]
            req_badge = "[REQ]" if s.required else "[OPT]"
            app_mode = defn.effective_approval(sname, defn.run_mode_default)
            print(f" {idx:2d}. {req_badge} {sname:<15} (Approval: {app_mode.value})")
            print(f"     Consumes: {', '.join(s.consumes) or '(none)'}")
            print(f"     Produces: {', '.join(s.produces)}")
            if s.quality_gates:
                qg_str = ", ".join(f"{g.name}({g.type.value})" for g in s.quality_gates)
                print(f"     Quality Gates: {qg_str}")
        print(f"============================================================")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_list_pipelines(args: argparse.Namespace) -> int:
    loader = PipelineLoader()
    pipelines = loader.list_pipelines()
    print(f"Available pipelines ({len(pipelines)}):")
    for name in pipelines:
        try:
            defn = loader.load(name)
            print(f"  * {name:<22} v{defn.version} - {defn.description}")
        except Exception:
            print(f"  * {name:<22} (parse error)")
    return 0


def cmd_artifact_validate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        return 2

    store = ArtifactStore(projects_root=path.parent)
    try:
        from schemas.models.artifact import ArtifactEnvelope
        raw = json.loads(path.read_text(encoding="utf-8"))
        envelope = ArtifactEnvelope.model_validate(raw)
        store.validate(envelope)
        print(f"[OK] Artifact at {path.name} is VALID.")
        print(f"   Type: {envelope.artifact_type} | Version: {envelope.artifact_version} | Status: {envelope.status.value}")
        print(f"   Hash: {envelope.content_hash}")
        return 0
    except ArtifactStoreError as e:
        print(f"[ERROR] Validation failed: {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] Parse error: {e}", file=sys.stderr)
        return 3


def cmd_artifact_hash(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        return 2

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        data = raw.get("data", raw)
        store = ArtifactStore(projects_root=path.parent)
        h = store.compute_hash(data)
        print(f"Canonical SHA-256: {h}")
        return 0
    except Exception as e:
        print(f"[ERROR] Error computing hash: {e}", file=sys.stderr)
        return 1


# ---------------------------------------------------------------------------
# Controller Commands
# ---------------------------------------------------------------------------

def cmd_start(args: argparse.Namespace) -> int:
    controller = ProductionController()
    options = {}
    if args.duration:
        options["target_duration"] = float(args.duration)
    try:
        state = controller.start(
            topic=args.topic,
            pipeline=args.pipeline,
            options=options,
        )
        print(f"[OK] Production started: {state.project_id}")
        print(f"   Pipeline: {state.pipeline} (v{state.pipeline_version})")
        print(f"   Status: {state.status.value} | Current Stage: {state.current_stage}")
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to start production: {e}", file=sys.stderr)
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        summary = controller.status(args.project_id)
        print(f"============================================================")
        print(f" Production ID: {summary['project_id']}")
        print(f" Pipeline:      {summary['pipeline']} (v{summary['pipeline_version']})")
        print(f" Status:        {summary['status'].upper()} (Current: {summary['current_stage'] or 'none'})")
        print(f" Active Artifacts: {summary['active_artifact_versions']}")
        if summary['stale_artifacts']:
            print(f" STALE ARTIFACTS:  {summary['stale_artifacts']}")
        print(f" Revisions:     {summary['revision_count']}")
        print(f" Budget:        Spent ${summary['budget']['actual_cost']:.2f} of ${summary['budget']['budget_cap']:.2f}")
        if summary['last_checkpoint']:
            print(f" Last Checkpoint: {summary['last_checkpoint']['checkpoint_id']} ({summary['last_checkpoint']['event_type']})")
        print(f"============================================================")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_resume(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        state = controller.resume(args.project_id)
        print(f"[OK] Resumed production {state.project_id}: status={state.status.value}, current_stage={state.current_stage}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        if args.until_blocked:
            results = controller.run_until_blocked(args.project_id)
            print(f"[OK] Executed {len(results)} stages:")
            for r in results:
                print(f"  - {r.stage}: {r.status.value.upper()} ({r.message})")
        else:
            result = controller.run_next_stage(args.project_id)
            print(f"[OK] Executed stage '{result.stage}': {result.status.value.upper()}")
            print(f"     {result.message}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_approve(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        state = controller.approve(args.project_id, stage_name=args.stage, actor=args.actor or "human")
        print(f"[OK] Approved stage '{args.stage}' for production {state.project_id}. Current stage now: {state.current_stage}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_reject(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        state = controller.reject(
            args.project_id,
            stage_name=args.stage,
            reason=args.reason or "Rejected via CLI",
            actor=args.actor or "human"
        )
        print(f"[OK] Rejected stage '{args.stage}' for production {state.project_id}.")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_retry(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        res = controller.retry_stage(args.project_id, stage_name=args.stage)
        print(f"[OK] Retried stage '{args.stage}': status={res.status.value}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_revise(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        res = controller.revise_stage(args.project_id, stage_name=args.stage, notes=args.notes or "")
        print(f"[OK] Revised stage '{args.stage}': status={res.status.value}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_abort(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        state = controller.abort(args.project_id, reason=args.reason or "Aborted via CLI")
        print(f"[OK] Aborted production {state.project_id}.")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_rerender(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        info = controller.rerender(args.project_id)
        if info.get("status") == "ready_to_render":
            print(f"[OK] Rerender Plan Ready:")
            print(f"   Production ID: {info['production_id']}")
            print(f"   Runtime:       {info['runtime']}")
            print(f"   Edit Decisions Version: v{info['edit_decisions_version']}")
            return 0
        else:
            print(f"[BLOCKED] Rerender blocked: {info.get('reason')}")
            return 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_research(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        options = {}
        if getattr(args, "depth", None):
            options["research_depth"] = args.depth
        if getattr(args, "sources", None):
            options["source_urls"] = [s.strip() for s in args.sources.split(",") if s.strip()]
        result = controller.run_stage(args.project_id, "research", options=options)
        print(f"[{result.status.value.upper()}] Research Stage: {result.message}")
        return 0 if result.status.value in ("ready", "waiting_approval") else 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_propose(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        kwargs = {}
        if getattr(args, "select", None):
            kwargs["selected_concept_id"] = args.select
        result = controller.run_stage(args.project_id, "proposal", **kwargs)
        print(f"[{result.status.value.upper()}] Proposal Stage: {result.message}")
        return 0 if result.status.value in ("ready", "waiting_approval") else 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_art_direction(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        result = controller.run_stage(args.project_id, "art_direction")
        print(f"[{result.status.value.upper()}] Art Direction Stage: {result.message}")
        return 0 if result.status.value in ("ready", "waiting_approval") else 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_script(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        result = controller.run_stage(args.project_id, "script")
        print(f"[{result.status.value.upper()}] Script Stage: {result.message}")
        return 0 if result.status.value in ("ready", "waiting_approval") else 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_scene_plan(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        result = controller.run_stage(args.project_id, "scene_plan")
        print(f"[{result.status.value.upper()}] Scene Plan Stage: {result.message}")
        return 0 if result.status.value in ("ready", "waiting_approval") else 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def _composition_root() -> Path:
    return Path(__file__).resolve().parent.parent


def cmd_runtime_list(args: argparse.Namespace) -> int:
    from composition.diagnostics import diagnose_all
    from composition.runtime_registry import create_default_registry
    registry = create_default_registry()
    print(f"Registered runtimes ({len(registry.list_registered())}):")
    for diag in diagnose_all(registry):
        record = registry.get(diag["runtime_id"])
        print(f"  * {diag['runtime_id']:<12} {diag['status']:<13} local={record.supports_local} remote={record.supports_remote}")
    return 0


def cmd_runtime_check(args: argparse.Namespace) -> int:
    from composition.diagnostics import diagnose_all, diagnose_runtime
    from composition.runtime_registry import create_default_registry
    registry = create_default_registry()
    targets = [args.runtime] if getattr(args, "runtime", None) else registry.list_registered()
    code = 0
    for runtime_id in targets:
        if not registry.has(runtime_id):
            print(f"[ERROR] Unknown runtime: {runtime_id!r} (registered: {', '.join(registry.list_registered())})", file=sys.stderr)
            return 2
        diag = diagnose_runtime(registry.get(runtime_id))
        print(f"Runtime: {diag['runtime_id']}  status={diag['status']}  version={diag['version']}")
        for check in diag["checks"]:
            print(f"  [{check['status']}] {check['name']}: {check['message']}")
        if diag["status"] != "available":
            code = 1
    return code


def cmd_composition_validate(args: argparse.Namespace) -> int:
    from composition.runtime_router import RuntimeRouter
    root = _composition_root()
    controller = ProductionController(projects_root=root / "projects")
    try:
        state = controller.state_store.load(args.project_id)
        store = controller.artifact_store
        edit = store.latest("edit_decisions", args.project_id)
        proposal = store.latest("proposal_packet", args.project_id)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    router = RuntimeRouter(projects_root=root / "projects")
    result = router.prepare_job(args.project_id, edit, proposal, state=state, store=store)
    print(f"Selected runtime: {edit.data.get('render_runtime')} "
          f"(proposal lock: {proposal.data.get('selected_concept_id')})")
    print(f"Locked runtime:   {edit.data.get('renderer_family')}/{edit.data.get('render_runtime')}/{edit.data.get('composition_mode')}")
    if result.status == "ready":
        job = result.job
        print(f"[OK] Composition job valid: {job.runtime_id} -> {job.output_path} (target={job.execution_target})")
        return 0
    print("[BLOCKED] Composition job invalid:")
    for blocker in result.blockers:
        print(f"  - {blocker.code}: {blocker.message}")
    return 1


def cmd_assets(args: argparse.Namespace) -> int:
    controller = ProductionController()
    try:
        result = controller.run_stage(args.project_id, "assets")
        print(f"[{result.status.value.upper()}] Assets Stage: {result.message}")
        return 0 if result.status.value in ("ready", "waiting_approval") else 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m production", description="Production Infrastructure & Controller CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate-pipeline
    p_val = subparsers.add_parser("validate-pipeline", help="Validate a pipeline definition YAML")
    p_val.add_argument("name", help="Pipeline name (e.g. youtube-short)")
    p_val.set_defaults(func=cmd_validate_pipeline)

    # inspect-pipeline
    p_insp = subparsers.add_parser("inspect-pipeline", help="Inspect pipeline topology and contracts")
    p_insp.add_argument("name", help="Pipeline name")
    p_insp.set_defaults(func=cmd_inspect_pipeline)

    # list-pipelines
    p_list = subparsers.add_parser("list-pipelines", help="List available pipelines")
    p_list.set_defaults(func=cmd_list_pipelines)

    # artifact-validate
    p_art_val = subparsers.add_parser("artifact-validate", help="Validate an artifact JSON file")
    p_art_val.add_argument("file", help="Path to artifact JSON file")
    p_art_val.set_defaults(func=cmd_artifact_validate)

    # artifact-hash
    p_art_hash = subparsers.add_parser("artifact-hash", help="Compute canonical SHA-256 hash")
    p_art_hash.add_argument("file", help="Path to artifact JSON file")
    p_art_hash.set_defaults(func=cmd_artifact_hash)

    # start
    p_start = subparsers.add_parser("start", help="Start a new production run")
    p_start.add_argument("--pipeline", default="youtube-short", help="Pipeline name")
    p_start.add_argument("--topic", required=True, help="Video topic")
    p_start.add_argument("--duration", type=float, help="Target duration in seconds")
    p_start.set_defaults(func=cmd_start)

    # status
    p_status = subparsers.add_parser("status", help="Get production status")
    p_status.add_argument("project_id", help="Production ID")
    p_status.set_defaults(func=cmd_status)

    # resume
    p_resume = subparsers.add_parser("resume", help="Resume production after crash")
    p_resume.add_argument("project_id", help="Production ID")
    p_resume.set_defaults(func=cmd_resume)

    # run
    p_run = subparsers.add_parser("run", help="Execute next stage in production")
    p_run.add_argument("project_id", help="Production ID")
    p_run.add_argument("--until-blocked", action="store_true", help="Run stages until blocked or completed")
    p_run.set_defaults(func=cmd_run)

    # approve
    p_approve = subparsers.add_parser("approve", help="Approve stage output")
    p_approve.add_argument("project_id", help="Production ID")
    p_approve.add_argument("--stage", required=True, help="Stage name")
    p_approve.add_argument("--actor", default="human", help="Actor name")
    p_approve.set_defaults(func=cmd_approve)

    # reject
    p_reject = subparsers.add_parser("reject", help="Reject stage output")
    p_reject.add_argument("project_id", help="Production ID")
    p_reject.add_argument("--stage", required=True, help="Stage name")
    p_reject.add_argument("--reason", default="", help="Rejection reason")
    p_reject.add_argument("--actor", default="human", help="Actor name")
    p_reject.set_defaults(func=cmd_reject)

    # retry
    p_retry = subparsers.add_parser("retry", help="Retry a failed stage")
    p_retry.add_argument("project_id", help="Production ID")
    p_retry.add_argument("--stage", required=True, help="Stage name")
    p_retry.set_defaults(func=cmd_retry)

    # revise
    p_revise = subparsers.add_parser("revise", help="Revise a stage with feedback")
    p_revise.add_argument("project_id", help="Production ID")
    p_revise.add_argument("--stage", required=True, help="Stage name")
    p_revise.add_argument("--notes", default="", help="Revision feedback notes")
    p_revise.set_defaults(func=cmd_revise)

    # abort
    p_abort = subparsers.add_parser("abort", help="Abort a production")
    p_abort.add_argument("project_id", help="Production ID")
    p_abort.add_argument("--reason", default="", help="Abort reason")
    p_abort.set_defaults(func=cmd_abort)

    # rerender
    p_rerender = subparsers.add_parser("rerender", help="Check rerender feasibility")
    p_rerender.add_argument("project_id", help="Production ID")
    p_rerender.set_defaults(func=cmd_rerender)

    # research
    p_res = subparsers.add_parser("research", help="Execute research stage on production")
    p_res.add_argument("project_id", help="Production ID")
    p_res.add_argument("--depth", choices=["minimal", "standard", "deep"], help="Research depth")
    p_res.add_argument("--sources", help="Comma-separated source URLs")
    p_res.set_defaults(func=cmd_research)

    # propose
    p_prop = subparsers.add_parser("propose", help="Execute proposal stage on production")
    p_prop.add_argument("project_id", help="Production ID")
    p_prop.add_argument("--select", help="Pre-select concept ID (e.g. concept_01)")
    p_prop.set_defaults(func=cmd_propose)

    # art-direction
    p_art = subparsers.add_parser("art-direction", help="Execute art direction stage on production")
    p_art.add_argument("project_id", help="Production ID")
    p_art.set_defaults(func=cmd_art_direction)

    # script
    p_script = subparsers.add_parser("script", help="Execute script stage on production")
    p_script.add_argument("project_id", help="Production ID")
    p_script.set_defaults(func=cmd_script)

    # scene-plan
    p_sp = subparsers.add_parser("scene-plan", help="Execute scene plan stage on production")
    p_sp.add_argument("project_id", help="Production ID")
    p_sp.set_defaults(func=cmd_scene_plan)

    # assets
    p_assets = subparsers.add_parser("assets", help="Execute assets stage on production")
    p_assets.add_argument("project_id", help="Production ID")
    p_assets.set_defaults(func=cmd_assets)

    # runtime-list
    p_rt_list = subparsers.add_parser("runtime-list", help="List registered composition runtimes and availability")
    p_rt_list.set_defaults(func=cmd_runtime_list)

    # runtime-check
    p_rt_check = subparsers.add_parser("runtime-check", help="Diagnose composition runtime environment (no rendering)")
    p_rt_check.add_argument("runtime", nargs="?", help="Runtime id (default: all registered)")
    p_rt_check.set_defaults(func=cmd_runtime_check)

    # composition-validate
    p_comp_val = subparsers.add_parser("composition-validate", help="Validate a composition job for a production (no rendering)")
    p_comp_val.add_argument("project_id", help="Production ID")
    p_comp_val.set_defaults(func=cmd_composition_validate)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
