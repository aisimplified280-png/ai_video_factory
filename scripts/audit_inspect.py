"""Dense per-scene + boundary inspection of a finished production (audit evidence).

For a given production this produces projects/<id>/audit/ with:
  mp4_truth.json       ffprobe facts about the ENCODED mp4 (codec/fps/duration/streams)
  scene_XX_mid.png     full-resolution frame at every scene midpoint
  boundary_XX.png      dense 10-frame strip spanning every scene boundary (-0.40s..+0.40s)
  scene_table.json     one row per scene: narration, required visual evidence,
                       judged visible description + semantic verdict, topology and
                       shapes (for repetition analysis), mascot spec, transitions
and prints a markdown skeleton of the required audit table.

Usage:
  python scripts/audit_inspect.py --production prod_gps_audit
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402

from production.controller import ProductionController  # noqa: E402
from production.stage_registry import default_production_registry  # noqa: E402

BOUNDARY_OFFSETS = [-0.40, -0.30, -0.20, -0.10, -0.034, 0.034, 0.10, 0.20, 0.30, 0.40]
STRIP_W = 216


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{proc.stdout}\n{proc.stderr}")


def _frame_at(mp4: Path, t: float, out: Path) -> None:
    _run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(mp4),
          "-frames:v", "1", "-y", str(out)])


def _probe(mp4: Path) -> dict:
    proc = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(mp4)],
        capture_output=True, text=True, timeout=120,
    )
    info = json.loads(proc.stdout or "{}")
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    return {
        "file": str(mp4),
        "bytes": mp4.stat().st_size,
        "codec": video.get("codec_name"),
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": video.get("r_frame_rate"),
        "duration_seconds": float(info.get("format", {}).get("duration", 0.0)),
        "audio_streams": [
            {"codec": a.get("codec_name"), "channels": a.get("channels"),
             "duration": a.get("duration"), "sample_rate": a.get("sample_rate")}
            for a in audio
        ],
    }


def _boundary_strip(mp4: Path, boundary_t: float, scene_out: Path, label: str) -> None:
    tmp_dir = scene_out.parent / "_strip_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    frame_paths = []
    for i, off in enumerate(BOUNDARY_OFFSETS):
        p = tmp_dir / f"{scene_out.stem}_{i:02d}.png"
        _frame_at(mp4, boundary_t + off, p)
        frame_paths.append(p)
    with Image.open(frame_paths[0]) as probe:
        base_w, base_h = probe.size
    scale = STRIP_W / base_w
    fh = int(base_h * scale)
    label_h = 30
    gap = 8
    canvas = Image.new("RGB", (len(frame_paths) * STRIP_W + (len(frame_paths) - 1) * gap,
                               fh + label_h), (245, 245, 247))
    draw = ImageDraw.Draw(canvas)
    for i, (p, off) in enumerate(zip(frame_paths, BOUNDARY_OFFSETS)):
        x = i * (STRIP_W + gap)
        with Image.open(p) as img:
            canvas.paste(img.convert("RGB").resize((STRIP_W, fh)), (x, label_h))
        marker = ">> BOUNDARY <<" if abs(off) <= 0.034 else f"{off:+.2f}s"
        color = (220, 38, 38) if abs(off) <= 0.034 else (30, 41, 59)
        draw.text((x + 6, 8), marker, fill=color)
    canvas.save(scene_out)
    for p in frame_paths:
        try:
            p.unlink(missing_ok=True)
        except PermissionError:
            pass
    try:
        tmp_dir.rmdir()
    except OSError:
        pass


def _rows(scene_plan: dict, edit: dict, script: dict, manifest: dict, judge: dict) -> list[dict]:
    judge_by_scene = {j["scene_id"]: j for j in judge.get("scene_judgements", [])}
    sections = script.get("sections", [])
    narration_by_start = {}
    for nar in edit.get("audio_tracks", {}).get("narration", []):
        narration_by_start[round(float(nar.get("start", -1)), 2)] = nar
    diagram_by_scene = {}
    for asset in manifest.get("assets", []):
        if asset.get("diagram_spec"):
            diagram_by_scene[asset.get("scene_id", "")] = asset["diagram_spec"]

    rows = []
    scenes = scene_plan.get("scenes", [])
    for idx, sc in enumerate(scenes):
        start = float(sc["start_seconds"])
        nar = narration_by_start.get(round(start, 2), {})
        spoken = (nar.get("requirement") or {}).get("spoken_text", "")
        section = sections[idx] if idx < len(sections) else {}
        spec = diagram_by_scene.get(sc["scene_id"])
        j = judge_by_scene.get(sc["scene_id"], {})
        char = sc.get("character_spec") or {}
        rows.append({
            "index": idx + 1,
            "scene_id": sc["scene_id"],
            "role": sc.get("narrative_role"),
            "start": start,
            "end": float(sc["end_seconds"]),
            "narration": spoken,
            "required_visual_evidence": {
                "visual_intent": section.get("visual_intent", section.get("primary_intent", "")),
                "primary_subject": section.get("primary_subject", sc.get("subject", "")),
                "emphasis_words": section.get("emphasis_words", []),
                "subject_from_judge": _judge_subject(j),
                "diagram_topology": (spec or {}).get("topology"),
                "diagram_labels": [n.get("label") for n in (spec or {}).get("nodes", [])],
                "diagram_icons": [n.get("icon") for n in (spec or {}).get("nodes", [])],
                "diagram_shapes": [n.get("shape_style") for n in (spec or {}).get("nodes", [])],
                "edge_relationships": sorted({c.get("relationship") for c in (spec or {}).get("connectors", [])}),
            },
            "rendered_visual": j.get("visible_description", "(not judged)"),
            "semantic_evidence": j.get("semantic_evidence", "n/a"),
            "semantic_score": j.get("semantic_grounding_score"),
            "judge_passed": j.get("passed"),
            "judge_reasons": j.get("reasons", []),
            "topology": (spec or {}).get("topology"),
            "transition_in": sc.get("transition_in"),
            "transition_out": sc.get("transition_out"),
            "mascot": {
                "motion": char.get("motion"),
                "action": char.get("action"),
                "target": char.get("target"),
                "target_anchor": char.get("target_anchor"),
                "position": char.get("position"),
            },
        })
    return rows


def _judge_subject(judgement: dict) -> str:
    text = judgement.get("visible_description", "")
    if "subject '" in text:
        try:
            return text.split("subject '", 1)[1].split("'", 1)[0]
        except IndexError:
            return ""
    return ""


def _repetition_flags(rows: list[dict]) -> None:
    """Flag rows that reuse an earlier scene's RENDERING template.

    Signature = the render path: diagram scenes by topology+shape mix, the CTA
    by its brand card, everything else by the focal-card template. Two focal
    scenes with different subjects still draw the same template — that IS the
    repetition an audit wants surfaced (stated honestly, not hidden).
    """
    seen: dict[str, int] = {}
    for row in rows:
        shapes = ",".join(sorted(set(row["required_visual_evidence"]["diagram_shapes"])))
        if row["topology"]:
            sig = f"diagram:{row['topology']}|{shapes}"
        elif row["role"] in ("cta", "outro"):
            sig = "cta_card"
        else:
            sig = "focal_card"
        if sig in seen:
            row["template_repetition"] = f"repeats scene {seen[sig]} template ({sig})"
        else:
            row["template_repetition"] = "unique"
            seen[sig] = row["index"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", required=True)
    args = parser.parse_args()
    pid = args.production

    controller = ProductionController(projects_root=ROOT / "projects", registry=default_production_registry)
    store = controller.artifact_store
    scene_plan = store.latest("scene_plan", pid).data
    edit = store.latest("edit_decisions", pid).data
    script = store.latest("script", pid).data
    manifest = store.latest("asset_manifest", pid).data
    judge_path = ROOT / "projects" / pid / "qa" / "visual_judge_scorecard.json"
    judge = json.loads(judge_path.read_text(encoding="utf-8")) if judge_path.exists() else {}

    videos = sorted((ROOT / "projects" / pid / "composition").glob("*_edit-v*.mp4"))
    if not videos:
        print(f"[ERROR] no rendered mp4 under projects/{pid}/composition")
        return 1
    mp4 = videos[-1]

    audit_dir = ROOT / "projects" / pid / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    truth = _probe(mp4)
    (audit_dir / "mp4_truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    print(f"[MP4] {truth['codec']} {truth['width']}x{truth['height']}@{truth['fps']} "
          f"{truth['duration_seconds']:.2f}s audio={len(truth['audio_streams'])} stream(s)")

    rows = _rows(scene_plan, edit, script, manifest, judge)
    _repetition_flags(rows)

    # Scene midpoints (full resolution) + dense boundary strips.
    for row in rows:
        mid = (row["start"] + row["end"]) / 2.0
        mid_path = audit_dir / f"scene_{row['index']:02d}_mid.png"
        _frame_at(mp4, mid, mid_path)
        row["mid_frame"] = str(mid_path.relative_to(ROOT))
    boundaries = rows[:-1]  # a strip spans row[i].end -> row[i+1].start; last scene has no exit
    for row in boundaries:
        strip = audit_dir / f"boundary_{row['index']:02d}_{row['index'] + 1:02d}.png"
        _boundary_strip(mp4, row["end"], strip, f"{row['scene_id']} -> next")
        row["boundary_strip"] = str(strip.relative_to(ROOT))
    rows[-1]["boundary_strip"] = None

    (audit_dir / "scene_table.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    print("\n| Scene | Narration | Required visual evidence | Actual rendered visual | "
          "Template repetition | Transition result | Mascot useful? |")
    print("|---|---|---|---|---|---|---|")
    for row in rows:
        narration = (row["narration"] or "")[:70].replace("|", "/")
        req = row["required_visual_evidence"]
        req_bits = ", ".join(b for b in [
            req.get("diagram_topology") or "",
            " / ".join(x for x in req.get("diagram_icons", []) if x) or "",
            req.get("primary_subject", ""),
        ] if b)[:70].replace("|", "/")
        actual = (row["rendered_visual"] or "")[:70].replace("|", "/")
        print(f"| {row['index']} {row['scene_id']} ({row['role']}) | {narration} | {req_bits} | "
              f"{actual} | {row['template_repetition']} | {row['transition_in']}->{row['transition_out']} "
              f"strip:{row['boundary_strip'] or '-'} | {row['mascot']['motion']} @ {row['mascot']['target']} |")

    print(f"\n[OK] audit artifacts in {audit_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
