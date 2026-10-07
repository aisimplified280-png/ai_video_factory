"""Content Intelligence CLI (Phase 11 + 12).

Orchestrates:
  Topic + Research
  → Story Selection & Narrative Escalation
  → High-Retention Shorts & Long-Form Script Generation
  → Script Scoring (retention, hook, subscriber conversion)
  → YouTube Packaging (10 titles, SEO description, thumbnail prompt, CTR score)
  → Versioned Artifact Persistence (script.vXXX.json & topic_package.vXXX.json)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import envfile
envfile.load_dotenv()

from production.phase10.researcher import research
from production.phase10.models import ResearchPack, ResearchMode
from production.phase11.scriptwriter import generate_shorts_script, generate_longform_script
from production.phase12.packager import generate_packaging

PROJECTS_DIR = ROOT / "projects"


def main():
    parser = argparse.ArgumentParser(description="Phase 11 + 12 Content Intelligence CLI")
    parser.add_argument("command", choices=["package", "script"])
    parser.add_argument("--topic", required=True, help="Topic for research and scriptwriting")
    parser.add_argument("--production", default="proj_3e27bd7a", help="Production ID")
    parser.add_argument(
        "--provider",
        default=os.getenv("SEARCH_PROVIDER", "multi"),
        choices=["all", "multi", "google_news", "official", "reddit", "brave"],
        help="Search provider to use (default: multi)",
    )
    parser.add_argument(
        "--freshness",
        default="7d",
        choices=["1d", "7d", "30d", "1y"],
        help="Freshness window for search results (default: 7d)",
    )
    args = parser.parse_args()

    project_root = PROJECTS_DIR / args.production
    project_root.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================")
    print(f"   PHASE 11 + 12: CONTENT & PACKAGING INTELLIGENCE")
    print(f"=======================================================")
    print(f"Topic       : {args.topic}")
    print(f"Production  : {args.production}")
    print(f"Provider    : {args.provider}")
    print(f"Freshness   : {args.freshness}")

    # 1. Load or Run Research Pack
    research_dir = project_root / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    latest_r_ptr = research_dir / "research_pack.latest.json"
    research_pack = None

    if latest_r_ptr.exists():
        try:
            r_meta = json.loads(latest_r_ptr.read_text("utf-8"))
            r_file = research_dir / r_meta.get("file", "")
            if r_file.exists():
                r_data = json.loads(r_file.read_text("utf-8"))
                if r_data.get("topic") == args.topic and r_data.get("research_mode") == "live":
                    research_pack = ResearchPack(**r_data)
                    print(f"\nLoaded existing research pack: {r_file.name}")
        except Exception:
            pass

    if research_pack is None:
        print(f"\nExecuting live research via '{args.provider}'...")
        research_pack = research(
            args.topic,
            freshness=args.freshness,
            provider_name=args.provider,
            top_n_stories=5,
        )
        if research_pack.research_mode == ResearchMode.UNAVAILABLE:
            print(f"[WARN] Live research unavailable. Continuing with synthetic topic anchors.")

    # 2. Generate Phase 11 Script Intelligence
    print(f"\n--- PHASE 11: SCRIPT INTELLIGENCE ---")
    script_shorts = generate_shorts_script(args.topic, research_pack)
    script_longform = generate_longform_script(args.topic, research_pack)

    sc = script_shorts.scoring
    print(f"Selected Hook Story  : {script_shorts.hook_story_id}")
    print(f"Shorts Word Count    : {script_shorts.total_word_count} words (~{script_shorts.total_duration_seconds:.1f}s)")
    print(f"Hook Strength Score  : {sc.hook_strength_score:.2f} / 1.0")
    print(f"Retention Score      : {sc.retention_score:.2f} / 1.0")
    print(f"Subscriber Conv Score: {sc.subscriber_conversion_score:.2f} / 1.0")
    print(f"Target Word Pacing   : {sc.word_pacing_wpm:.0f} WPM")

    print(f"\nShorts Section Lineup:")
    for s in script_shorts.sections:
        print(f"  [{s.section_id}] ({s.role.upper()} | {s.estimated_duration_seconds:.1f}s): {s.spoken_text}")
        print(f"       Emphasis: {', '.join(s.emphasis_words)}")

    # Save canonical script via ArtifactStore
    from production.artifact_store import ArtifactStore
    from schemas.models.artifact import ProducerInfo
    from schemas.models.common import ProducerKind
    store = ArtifactStore(PROJECTS_DIR)
    canonical_script = script_shorts.to_canonical_schema(args.production)
    producer = ProducerInfo(kind=ProducerKind.SYSTEM, provider="content_intelligence")
    envelope = store.create(
        artifact_type="script",
        production_id=args.production,
        stage="script",
        data=canonical_script,
        producer=producer,
    )
    saved_script_path = store.save(envelope)
    store.approve("script", args.production, envelope.artifact_version)
    print(f"\nPersisted Script: {saved_script_path.name}")

    # 3. Generate Phase 12 Packaging Intelligence
    print(f"\n--- PHASE 12: PACKAGING INTELLIGENCE ---")
    topic_package = generate_packaging(
        args.topic,
        script_shorts=script_shorts,
        research_pack=research_pack,
        script_longform=script_longform,
    )

    print(f"\nSelected Title     : \"{topic_package.selected_title}\"")
    print(f"Title Score        : {topic_package.title_score:.1f} / 10.0")
    print(f"Curiosity Score    : {topic_package.curiosity_score:.1f} / 10.0")
    print(f"Thumbnail Score    : {topic_package.thumbnail_score:.1f} / 10.0")
    print(f"Overall Score      : {topic_package.overall_package_score:.1f} / 10.0")
    print(f"Thumbnail Text     : \"{topic_package.thumbnail_text}\"")
    print(f"Thumbnail Prompt   : \"{topic_package.thumbnail_prompt[:110]}...\"")

    print(f"\nTop 5 Title Candidates:")
    for idx, t in enumerate(topic_package.title_candidates[:5], start=1):
        print(f"  #{idx} [{t.angle.upper()} | Title: {t.title_score:.1f} | Curiosity: {t.curiosity_score:.1f}] {t.title}")

    # Save topic_package.vXXX.json
    brief_dir = project_root / "brief"
    brief_dir.mkdir(parents=True, exist_ok=True)
    saved_pkg_path = _write_versioned(topic_package.to_dict(), brief_dir, "topic_package")
    print(f"\nPersisted Topic Package: {saved_pkg_path.name}")
    print(f"=======================================================\n")


def _write_versioned(data: dict, output_dir: Path, artifact_type: str) -> Path:
    """Write versioned artifact file and update .latest pointer."""
    existing = sorted(output_dir.glob(f"{artifact_type}.v*.json"))
    next_ver = len(existing) + 1
    filename = f"{artifact_type}.v{next_ver:03d}.json"
    filepath = output_dir / filename

    content = json.dumps(data, indent=2, default=str)
    filepath.write_text(content, "utf-8")

    latest_ptr = {
        "version": next_ver,
        "file": filename,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_dir / f"{artifact_type}.latest.json").write_text(
        json.dumps(latest_ptr, indent=2), "utf-8"
    )
    return filepath


if __name__ == "__main__":
    main()
