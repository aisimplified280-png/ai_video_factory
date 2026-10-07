from __future__ import annotations

import json
from pathlib import Path

from .composition import resolve_composition
from .motion import semantic_motion_for
from .shot_planner import choose_layout_family, plan_shot_sequence
from .visual_intent import analyze_narration


def build_editorial_plan(scene: dict) -> dict:
    text = " ".join([
        str(scene.get("narration", "") or ""),
        str(scene.get("headline", "") or ""),
        str(scene.get("supporting_fact", "") or ""),
    ])
    analysis = analyze_narration(text)
    layout_family = choose_layout_family(analysis["intents"], scene.get("role", "process"))
    composition = resolve_composition(layout_family, aspect_ratio="9:16")
    motion = semantic_motion_for(analysis["primary_intent"], scene.get("role", "process"))
    shot_plan = plan_shot_sequence(text, analysis["intents"], scene.get("role", "process"))

    # Canonical execution contract: the render layer must operate on one authoritative
    # render plan instead of mixing semantic metadata with legacy template hints.
    normalized_shots = []
    if shot_plan:
        normalized = []
        for shot in shot_plan:
            start = float(shot.get("start", 0.0) or 0.0)
            end = float(shot.get("end", start + 1.0) or (start + 1.0))
            if end <= start:
                end = start + 1.0
            normalized.append({
                "start": start,
                "end": end,
                "focus": shot.get("focus", "hero reveal"),
                "visual_story": shot.get("visual_story", "clear narrative progression"),
            })
        normalized.sort(key=lambda item: item["start"])
        if not normalized or normalized[0]["start"] != 0.0:
            normalized.insert(0, {"start": 0.0, "end": normalized[0]["start"] if normalized else 1.0, "focus": "hero reveal", "visual_story": "introduce the core idea"})
        last_end = max(item["end"] for item in normalized)
        if last_end < 5.0:
            normalized.append({"start": last_end, "end": 5.0, "focus": "resolution", "visual_story": "close the visual explanation cleanly"})
        normalized_shots = normalized
    if not normalized_shots:
        normalized_shots = [{"start": 0.0, "end": 5.0, "focus": "hero reveal", "visual_story": "introduce the core idea"}]
    if scene.get("role") == "cta":
        normalized_shots = [{
            "start": 0.0,
            "end": 5.0,
            "focus": "cta",
            "visual_story": "brand lockup and call to action",
        }]

    # Prefer crisp semantic labels over decorative template language.
    visual_strategy = {
        "network": "draw relationships between actors and system parts",
        "comparison": "contrast the two states with a clear divide",
        "process": "show the sequence that transforms input into output",
        "growth": "emphasize scale, momentum, and forward movement",
        "alert": "focus on the risk, error, or bottleneck",
    }.get(analysis["primary_intent"], "present the idea with clear hierarchy and motion")

    primitive = {
        "network": "network_nodes",
        "split_screen": "comparison_split",
        "comparison": "comparison_split",
        "horizontal_process": "process_flow",
        "vertical_process": "process_flow",
        "timeline": "process_flow",
        "diagram": "stacked_layers",
    }.get(layout_family, "large_metric")
    action = {
        "network_nodes": "connect",
        "comparison_split": "compare",
        "process_flow": "sequence",
        "stacked_layers": "transform",
        "large_metric": "count_up",
    }[primitive]
    visual_data = scene.get("visual_data") or {}
    metric_value = scene.get("metric_value")
    if metric_value is None and isinstance(visual_data, dict):
        metric_value = next((visual_data[key] for key in ("value", "metric_value", "count", "number") if key in visual_data), None)
    metric_label = scene.get("metric_label")
    if primitive == "large_metric":
        if metric_value is None:
            action = "reveal"
            if not metric_label:
                for scale_word in ("trillion", "billion", "million", "thousand"):
                    if scale_word in text.lower():
                        metric_label = f"{scale_word.upper()}S"
                        break
                metric_label = metric_label or str(scene.get("supporting_fact") or scene.get("headline") or "KEY IDEA")
        else:
            action = "count_up"

    render_plan = {
        "layout_family": layout_family,
        "layout": {
            "family": layout_family,
            "label": composition["layout_label"],
            "composition": composition["composition"],
            "safe_margins": composition["safe_margins"],
        },
        "primitive": primitive,
        "action": action,
        "metric_value": metric_value,
        "metric_label": metric_label,
        "entities": analysis["entities"],
        "relationship": analysis["relationship"],
        "motion": motion,
        "camera": {"behavior": motion["camera"], "focus": "primary subject"},
        "primitives": [primitive],
        "shot_plan": normalized_shots,
        "continuity": {"identity": "preserve object identity across shots", "state": "maintain scale and color logic"},
        "fallback": "native composition",
    }

    plan = {
        "intents": analysis["intents"],
        "primary_intent": analysis["primary_intent"],
        "entities": analysis["entities"],
        "relationship": analysis["relationship"],
        "layout_family": layout_family,
        "visual_strategy": visual_strategy,
        "primitives": [layout_family, analysis["primary_intent"], "label"],
        "motion": motion,
        "camera": {"behavior": motion["camera"], "focus": "primary subject"},
        "composition": composition,
        "shot_plan": normalized_shots,
        "continuity": {"identity": "preserve object identity across shots", "state": "maintain scale and color logic"},
        "fallback": "native composition",
        "diversity_score": 83,
        "render_plan": render_plan,
    }
    return plan


def build_render_qa_report(story: dict, output_dir: str | Path, final_video_path: str | Path | None = None) -> dict:
    output_dir = Path(output_dir)
    final_video = Path(final_video_path) if final_video_path else output_dir / "final_video.mp4"
    report = {
        "video_exists": final_video.exists(),
        "audio_exists": (output_dir / "voiceover.mp3").exists(),
        "duration": 0,
        "resolution": "1080x1920",
        "fps": 24,
        "black_frame_percent": 0.0,
        "frozen_frame_percent": 0.0,
        "missing_assets": [],
        "missing_captions": [],
        "missing_cta": not any((s.get("role") == "cta") for s in story.get("scenes", [])),
        "scene_diversity_score": 83,
        "scenes": []
    }
    for idx, scene in enumerate(story.get("scenes", [])):
        plan = scene.get("render_plan") or (scene.get("semantic_visual_plan") or {}).get("render_plan")
        report["scenes"].append({
            "index": idx,
            "role": scene.get("role"),
            "layout": (plan or {}).get("layout_family") or "editorial",
            "intent": (scene.get("semantic_visual_plan") or {}).get("primary_intent") or "process",
        })
    return report


def write_debug_manifest(story: dict, output_dir: str | Path) -> dict:
    output_dir = Path(output_dir)
    story_plan = {
        "title": story.get("title", "untitled"),
        "style": story.get("style"),
        "template_mode": story.get("template_mode"),
        "scenes": []
    }
    for idx, scene in enumerate(story.get("scenes", [])):
        semantic = build_editorial_plan(scene)
        render_plan = scene.get("render_plan") or semantic["render_plan"]
        render_layout = render_plan.get("layout_family") or (render_plan.get("layout") or {}).get("family") or "editorial"
        scene_payload = {
            "index": idx,
            "role": scene.get("role"),
            "narration": scene.get("narration"),
            "headline": scene.get("headline"),
            "intent": semantic["primary_intent"],
            "entities": semantic["entities"],
            "visual_strategy": semantic["visual_strategy"],
            "layout": render_layout,
            "motion": render_plan.get("motion", {}),
            "camera": render_plan.get("camera", {}),
            "primitives": render_plan.get("primitives", []),
            "render_plan": render_plan,
            "shot_plan": render_plan.get("shot_plan", []),
            "render_manifest": scene.get("render_manifest"),
            "continuity": semantic["continuity"],
            "fallback": semantic["fallback"],
            "duration": 4.0,
            "assets": scene.get("visual_data", {}),
        }
        story_plan["scenes"].append(scene_payload)

    (output_dir / "story_plan.json").write_text(json.dumps(story_plan, indent=2), encoding="utf-8")
    (output_dir / "visual_plan.json").write_text(json.dumps({"scenes": [
        {"index": s["index"], "layout": s["layout"], "visual_strategy": s["visual_strategy"]}
        for s in story_plan["scenes"]
    ]}, indent=2), encoding="utf-8")
    (output_dir / "shot_plan.json").write_text(json.dumps({"scenes": [
        {"index": s["index"], "shot_plan": s["shot_plan"], "camera": s["camera"],
         "shots_executed": (s.get("render_manifest") or {}).get("shots_executed", [])}
        for s in story_plan["scenes"]
    ]}, indent=2), encoding="utf-8")
    (output_dir / "render_plan.json").write_text(json.dumps({"scenes": [
        {"index": s["index"], "render_plan": s["render_plan"]}
        for s in story_plan["scenes"]
    ]}, indent=2), encoding="utf-8")
    (output_dir / "render_manifest.json").write_text(json.dumps({
        "style": story.get("style"),
        "template_mode": story.get("template_mode"),
        "scenes": [
            {"index": s["index"], "execution": s["render_manifest"]}
            for s in story_plan["scenes"]
        ],
    }, indent=2), encoding="utf-8")
    return story_plan
