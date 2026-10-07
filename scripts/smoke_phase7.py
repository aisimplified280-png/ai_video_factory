"""Phase 7 smoke test: probe the real local environment for composition runtimes.

Reports Python, Node, npm, Remotion, HyperFrames, and FFmpeg availability and
writes output/runtime_capabilities.json. Renders nothing.
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

from composition.diagnostics import diagnose_all
from composition.runtime_capabilities import CAPABILITY_DESCRIPTIONS
from composition.runtime_registry import create_default_registry


def run(output_path: Path | None = None) -> dict:
    registry = create_default_registry()
    diagnostics = diagnose_all(registry)
    report = {
        "runtimes": [
            {
                "runtime_id": diag["runtime_id"],
                "status": diag["status"],
                "version": diag["version"],
                "supports_local": registry.get(diag["runtime_id"]).supports_local,
                "supports_remote": registry.get(diag["runtime_id"]).supports_remote,
                "capabilities": sorted(registry.get(diag["runtime_id"]).capabilities),
                "checks": diag["checks"],
            }
            for diag in diagnostics
        ],
        "capability_descriptions": CAPABILITY_DESCRIPTIONS,
    }
    target = output_path or (ROOT / "output" / "runtime_capabilities.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "=" * 68)
    print(" PHASE 7: RUNTIME CAPABILITY SMOKE TEST (no rendering)")
    print("=" * 68)
    for entry in report["runtimes"]:
        print(f"\n{entry['runtime_id']}: {entry['status']}")
        print(f"  local={entry['supports_local']} remote={entry['supports_remote']} "
              f"capabilities={len(entry['capabilities'])}")
        for check in entry["checks"]:
            print(f"  [{check['status']}] {check['name']}: {check['message']}")
    print(f"\nWrote: {target}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 7 runtime capability smoke test")
    parser.add_argument("--output", default=None, help="Report path (default: output/runtime_capabilities.json)")
    args = parser.parse_args()
    run(Path(args.output) if args.output else None)
