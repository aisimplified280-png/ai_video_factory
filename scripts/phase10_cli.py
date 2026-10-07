import argparse
import sys
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import envfile
envfile.load_dotenv()

from production.phase10.researcher import research
from production.phase10.models import ResearchMode, ClaimStatus
from production.artifact_store import ArtifactStore

PROJECTS_DIR = ROOT / "projects"


def main():
    parser = argparse.ArgumentParser(description="Phase 10 Research Engine CLI")
    parser.add_argument("command", choices=["research"])
    parser.add_argument("--topic", required=True, help="Topic to research")
    parser.add_argument("--production", required=True, help="Production ID")
    parser.add_argument(
        "--provider",
        default=os.getenv("SEARCH_PROVIDER", "brave"),
        choices=["all", "multi", "google_news", "official", "reddit", "brave"],
        help="Search provider to use (default: env SEARCH_PROVIDER or brave)",
    )
    parser.add_argument(
        "--freshness",
        default="7d",
        choices=["1d", "7d", "30d", "1y"],
        help="Freshness window for search results (default: 7d)",
    )
    parser.add_argument(
        "--top-stories",
        type=int,
        default=5,
        help="Number of top stories to select and rank (default: 5)",
    )
    args = parser.parse_args()

    if args.command == "research":
        run_research(args)


def run_research(args):
    project_root = PROJECTS_DIR / args.production
    research_dir = project_root / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n==========================================")
    print(f"      PHASE 10: RESEARCH ENGINE")
    print(f"==========================================")
    print(f"Topic       : {args.topic}")
    print(f"Provider    : {args.provider}")
    print(f"Freshness   : {args.freshness or 'unrestricted'}")

    pack = research(
        args.topic,
        freshness=args.freshness,
        provider_name=args.provider,
        top_n_stories=args.top_stories,
    )

    print(f"\nActive Provider : {pack.provider or 'N/A'}")
    print(f"Research Mode   : {pack.research_mode.value}")
    print(f"Queries Issued  : {len(pack.queries_issued)}")
    for q in pack.queries_issued:
        print(f"  • {q}")

    if pack.research_mode == ResearchMode.UNAVAILABLE:
        print(f"\n[WARN] LIVE_RESEARCH_UNAVAILABLE — no search provider configured.")
        print("       Set BRAVE_SEARCH_API_KEY or use --provider multi / --provider google_news.")
        pack_dict = pack.to_dict()
        _write_versioned(pack_dict, research_dir, "research_pack")
        sys.exit(1)

    print(f"\nSources Retrieved : {len(pack.sources)}")
    for src in pack.sources[:10]:
        print(f"  [Tier {src.tier}] [{src.source_type.upper()}] {src.publisher or src.url[:50]} — {src.title[:65]}")

    # Claim breakdown
    confirmed = [c for c in pack.claims if c.status == ClaimStatus.CONFIRMED]
    likely = [c for c in pack.claims if c.status == ClaimStatus.LIKELY]
    single = [c for c in pack.claims if c.status == ClaimStatus.SINGLE_SOURCE]
    unverified = [c for c in pack.claims if c.status == ClaimStatus.UNVERIFIED]
    conflicting = [c for c in pack.claims if c.status == ClaimStatus.CONFLICTING]

    print(f"\nClaims Verified : {len(pack.claims)} total")
    print(f"  CONFIRMED    : {len(confirmed)}")
    print(f"  LIKELY       : {len(likely)}")
    print(f"  SINGLE_SOURCE: {len(single)}")
    print(f"  UNVERIFIED   : {len(unverified)}")
    print(f"  CONFLICTING  : {len(conflicting)}")

    # Visual Facts (Phase 10.3)
    vf = pack.visual_facts
    print(f"\n--- VISUAL FACT EXTRACTION (Phase 10.3) ---")
    print(f"  Keywords  : {', '.join(vf.visual_keywords[:8])}")
    print(f"  Locations : {', '.join(vf.locations[:4])}")
    print(f"  Objects   : {', '.join(vf.objects[:4])}")
    print(f"  Actions   : {', '.join(vf.actions[:3])}")
    print(f"  Prompt Seed:\n    \"{vf.visual_prompt_seed}\"")

    # Top Stories (Phase 10.4)
    if pack.top_stories:
        print(f"\n--- TOP {len(pack.top_stories)} RANKED STORIES (Phase 10.4) ---")
        for s in pack.top_stories:
            sc = s.scoring
            print(f"  #{s.rank} [Score: {sc.overall_score:.2f} | Trust: {sc.trust_score:.2f} | Rel: {sc.relevance:.2f} | Visual: {sc.visual_potential:.2f} | Shock: {sc.shock_factor:.2f}]")
            print(f"     \"{s.headline[:85]}\"")

    pack_dict = pack.to_dict()
    artifact_path = _write_versioned(pack_dict, research_dir, "research_pack")
    print(f"\nSaved Artifact : {artifact_path}")
    print(f"==========================================\n")


def _write_versioned(data: dict, research_dir: Path, artifact_type: str) -> Path:
    """Write versioned artifact file and update .latest pointer."""
    existing = sorted(research_dir.glob(f"{artifact_type}.v*.json"))
    next_ver = len(existing) + 1
    filename = f"{artifact_type}.v{next_ver:03d}.json"
    filepath = research_dir / filename

    content = json.dumps(data, indent=2, default=str)
    filepath.write_text(content, "utf-8")

    latest_ptr = {
        "version": next_ver,
        "file": filename,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (research_dir / f"{artifact_type}.latest.json").write_text(
        json.dumps(latest_ptr, indent=2), "utf-8"
    )
    return filepath


if __name__ == "__main__":
    main()
