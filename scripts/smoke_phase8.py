"""Phase 8 smoke test: artifacts -> composition job -> props -> validate.

With --render, attempts a real render through the Remotion adapter (blocks
honestly when the toolchain is unavailable). With --remote, packages the
remote worker bundle instead of rendering. Post-render steps (ffprobe,
frames, contact sheet, render report) run only after a real render.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import envfile
envfile.load_dotenv()

from composition.remotion.props_builder import PropsError, build_production_props
from composition.remotion.renderer import ffprobe_info, package_remote_bundle
from composition.remotion.runtime import RemotionRuntime
from composition.runtime_router import RuntimeRouter
from production.controller import ProductionController
from production.stage_registry import default_production_registry


def load_chain(controller: ProductionController, production_id: str) -> dict:
    store = controller.artifact_store
    edit = store.latest("edit_decisions", production_id)
    return {
        "edit": edit,
        "proposal": store.latest("proposal_packet", production_id),
        "scene_plan": store.latest("scene_plan", production_id).data,
        "manifest": store.latest("asset_manifest", production_id).data,
        "art_direction": store.latest("art_direction", production_id).data,
        "script": store.latest("script", production_id).data,
    }


def run(production_id: str, render: bool = False, remote: bool = False,
        preview: bool = False, output: str | None = None) -> int:
    controller = ProductionController(projects_root=ROOT / "projects", registry=default_production_registry)
    try:
        state = controller.state_store.load(production_id)
        chain = load_chain(controller, production_id)
    except Exception as exc:
        print(f"[ERROR] Cannot load production: {exc}")
        return 2

    router = RuntimeRouter(projects_root=ROOT / "projects")
    result = router.prepare_job(production_id, chain["edit"], chain["proposal"], state=state, store=controller.artifact_store)
    if result.status != "ready":
        print("[BLOCKED] Composition job invalid:")
        for blocker in result.blockers:
            print(f"  - {blocker.code}: {blocker.message}")
        return 1
    job = result.job
    print(f"[OK] Composition job valid: {job.runtime_id} edit=v{job.edit_artifact_version:03d} mode={job.composition_mode}")

    profile = json.loads((ROOT / job.platform_profile).read_text(encoding="utf-8"))
    workdir = ROOT / "projects" / production_id / "composition" / "remotion_work"
    public_dir = workdir / "public"
    try:
        props, warnings = build_production_props(
            edit_data=chain["edit"].data,
            scene_plan_data=chain["scene_plan"],
            manifest_data=chain["manifest"],
            art_direction_data=chain["art_direction"],
            script_data=chain["script"],
            platform_profile=profile,
            projects_root=ROOT / "projects",
            public_dir=public_dir,
        )
    except PropsError as exc:
        print(f"[BLOCKED] Props materialization failed: {exc}")
        return 1
    props["editArtifactVersion"] = chain["edit"].artifact_version
    props["editArtifactHash"] = chain["edit"].content_hash
    props["previewMode"] = preview
    props_path = workdir / "props.json"
    props_path.write_text(json.dumps(props, indent=2), encoding="utf-8")
    print(f"[OK] Props materialized: {len(props['events'])} events, {len(props['assets'])} assets, "
          f"{len(props['scenes'])} scenes ({'warnings: ' + '; '.join(warnings) if warnings else 'no warnings'})")

    adapter = RemotionRuntime()
    if remote:
        import warnings as _warnings
        _warnings.warn("The --remote flag is deprecated: the factory is fully local now. "
                       "Packaging the bundle anyway for archival purposes.", DeprecationWarning)
        print("[DEPRECATED] --remote: local rendering is the normal path; bundle packaged for archive only.")
        asset_files = sorted((public_dir / "assets").glob("*"))
        bundle = package_remote_bundle(
            job=job, props_path=props_path,
            artifact_payloads={
                "edit_decisions": chain["edit"].data,
                "scene_plan": chain["scene_plan"],
                "asset_manifest": chain["manifest"],
                "art_direction": chain["art_direction"],
                "script": chain["script"],
                "platform": profile,
            },
            asset_files=asset_files,
            bundle_path=workdir / f"{production_id}_remotion-bundle.zip",
            composer_dir=ROOT / "remotion-composer",
        )
        print(f"[OK] Remote bundle packaged: {bundle} (see remotion-composer/REMOTE_WORKER.md)")
        return 0

    if not render:
        print("[OK] Validation complete (no --render requested; nothing executed).")
        return 0

    out_path = Path(output) if output else (workdir / "final_video.mp4")
    outcome = adapter.render(props_path, out_path, workdir / "render_manifest.json")
    if outcome["status"] != "ready":
        print(f"[{outcome['status'].upper()}] {outcome['code']}: {outcome['message']}")
        return 1
    info = ffprobe_info(out_path)
    print(f"[OK] Rendered: {out_path}")
    print(json.dumps({"streams": len(info.get("streams", [])), "duration": info.get("format", {}).get("duration")}, indent=2))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 8 Remotion smoke test")
    parser.add_argument("--production", required=True)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--remote", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    sys.exit(run(args.production, render=args.render, remote=args.remote, preview=args.preview, output=args.output))
