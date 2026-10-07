"""Render paired editorial scenes to prove render-plan authority at pixel time."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from create_short import render_scene_frames
from video_encoder import FFmpegRawVideoEncoder
from viral_template import create_template_context


DURATION = 5.0
FPS = 24
SHOTS = [
    {"start": 0.0, "end": 1.2, "focus": "signal", "visual_story": "introduce the incoming signal"},
    {"start": 1.2, "end": 2.4, "focus": "connection", "visual_story": "connect the system parts"},
    {"start": 2.4, "end": 3.7, "focus": "transformation", "visual_story": "show the key transformation"},
    {"start": 3.7, "end": 5.0, "focus": "result", "visual_story": "resolve on the useful result"},
]

CASES = {
    "network": {
        "narration": "A network connects separate services so information can move to the right place.",
        "headline": "HOW SYSTEMS CONNECT",
        "base": {"layout_family": "network", "primitive": "network_nodes", "action": "connect", "motion": {"primary": "reveal"}, "camera": {"behavior": "push_in"}, "shot_plan": SHOTS},
        "variant": {"layout_family": "split_screen", "primitive": "network_nodes", "action": "connect", "motion": {"primary": "reveal"}, "camera": {"behavior": "push_in"}, "shot_plan": SHOTS},
    },
    "process": {
        "narration": "A request enters the system, gets processed, and becomes a useful answer.",
        "headline": "FROM REQUEST TO ANSWER",
        "base": {"layout_family": "horizontal_process", "primitive": "process_flow", "action": "sequence", "motion": {"primary": "reveal"}, "camera": {"behavior": "static"}, "shot_plan": SHOTS},
        "variant": {"layout_family": "horizontal_process", "primitive": "large_metric", "action": "count_up", "motion": {"primary": "reveal"}, "camera": {"behavior": "static"}, "shot_plan": SHOTS},
    },
    "comparison": {
        "narration": "With more compute, the same model can handle larger workloads and deliver stronger results.",
        "headline": "MORE COMPUTE, MORE CAPABILITY",
        "base": {"layout_family": "split_screen", "primitive": "comparison_split", "action": "compare", "motion": {"primary": "reveal"}, "camera": {"behavior": "push_in"}, "shot_plan": [{"start": 0.0, "end": 5.0, "focus": "before and after", "visual_story": "compare the two outcomes"}]},
        "variant": {"layout_family": "split_screen", "primitive": "comparison_split", "action": "compare", "motion": {"primary": "grow"}, "camera": {"behavior": "static"}, "shot_plan": SHOTS},
    },
}


def render_case(name: str, variant_name: str, case: dict, plan: dict, target: Path):
    target.mkdir(parents=True, exist_ok=True)
    mode = "editorial_explainer"
    scene = {
        "kind": mode,
        "_template_mode": mode,
        "template_context": create_template_context(mode, "process"),
        "role": "process",
        "headline": case["headline"],
        "narration": case["narration"],
        "supporting_fact": "Same narration; only the render plan changes.",
        "render_plan": copy.deepcopy(plan),
        "_render_duration_seconds": DURATION,
    }
    output_mp4 = target / "final_scene.mp4"
    encoder = FFmpegRawVideoEncoder(output_mp4, fps=FPS, width=1080, height=1920)
    encoder.start()
    sample_frames = {0, 28, 57, 88, 118}
    for frame_index, frame in enumerate(render_scene_frames(
        scene, 0, 1, DURATION, intro_seconds=DURATION, style_name=mode, subs=None
    )):
        encoder.encode_frame(frame)
        if frame_index in sample_frames:
            frame.save(target / f"frame_{frame_index:03d}.png")
    encoder.close()

    decoded_frame = target / "encoded_frame_2s.png"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-ss", "2.0", "-i", str(output_mp4),
        "-frames:v", "1", str(decoded_frame),
    ], check=True)

    (target / "render_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    (target / "shot_plan.json").write_text(json.dumps(plan.get("shot_plan", []), indent=2), encoding="utf-8")
    (target / "render_manifest.json").write_text(
        json.dumps(scene.get("render_manifest", {}), indent=2), encoding="utf-8"
    )
    print(f"{name}/{variant_name}: {output_mp4} ({len(scene.get('render_manifest', {}).get('shots_executed', []))} shots executed)")


def main():
    output_root = ROOT / "benchmark" / "render-plan-authority"
    for name, case in CASES.items():
        for variant_name, plan_key in (("baseline", "base"), ("variant", "variant")):
            render_case(name, variant_name, case, case[plan_key], output_root / name / variant_name)
    print(f"BENCHMARK_ROOT={output_root}")


if __name__ == "__main__":
    main()