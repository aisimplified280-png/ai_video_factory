from __future__ import annotations

import math
import re

from PIL import Image, ImageDraw


BACKGROUND = "#F6F8FC"
INK = "#10233F"
BLUE = "#245BDB"
CYAN = "#18A6A6"
CORAL = "#E66C54"
MUTED = "#64758B"
PALE_BLUE = "#DCE8FF"
PALE_CYAN = "#D8F2EF"

LAYOUT_EXECUTORS = {
    "network": "network_layout",
    "split_screen": "split_screen_layout",
    "comparison": "split_screen_layout",
    "horizontal_process": "process_layout",
    "vertical_process": "process_layout",
    "timeline": "timeline_layout",
    "diagram": "layered_diagram_layout",
    "detail_zoom": "detail_layout",
    "centered_hero": "hero_layout",
    "editorial": "editorial_layout",
}

PRIMITIVE_EXECUTORS = {
    "network_nodes": "draw_network_nodes",
    "large_metric": "draw_large_metric",
    "process_flow": "draw_process_flow",
    "comparison_split": "draw_comparison_split",
    "data_bars": "draw_data_bars",
    "stacked_layers": "draw_stacked_layers",
    "map_pins": "draw_map_pins",
}

ACTION_EXECUTORS = {
    "connect": "animate_connections",
    "count_up": "animate_count_up",
    "compare": "reveal_comparison",
    "sequence": "advance_sequence",
    "grow": "grow_visual",
    "reveal": "reveal_visual",
    "isolate": "isolate_bottleneck",
    "transform": "transform_visual",
}


def _text(draw, xy, value, font, fill, anchor="mm"):
    draw.text((int(xy[0]), int(xy[1])), str(value), font=font, fill=fill, anchor=anchor)


def _normalize_shots(raw_shots, duration):
    shots = []
    for index, raw in enumerate(raw_shots or []):
        if not isinstance(raw, dict):
            continue
        start = float(raw.get("start", 0.0))
        end = float(raw.get("end", start))
        if end <= start:
            raise ValueError(f"Editorial shot {index} has a non-positive duration")
        shots.append({
            "start": start,
            "end": end,
            "focus": str(raw.get("focus", f"shot {index + 1}")),
            "visual_story": str(raw.get("visual_story", raw.get("action", "visual progression"))),
            "action": str(raw.get("action", "")).lower(),
        })
    if not shots:
        shots = [{"start": 0.0, "end": duration, "focus": "core idea", "visual_story": "introduce the core idea"}]
    shots.sort(key=lambda item: item["start"])
    if shots[0]["start"] > 0.001:
        raise ValueError("Editorial shot plan must start at 0.0 seconds")
    cursor = 0.0
    for index, shot in enumerate(shots):
        if abs(shot["start"] - cursor) > 0.001:
            relation = "overlaps" if shot["start"] < cursor else "has a timing gap before"
            raise ValueError(f"Editorial shot {index + 1} {relation} the previous shot")
        cursor = shot["end"]
    if cursor < duration:
        shots[-1] = {**shots[-1], "end": duration}
    elif cursor > duration:
        clipped = []
        for shot in shots:
            if shot["start"] >= duration:
                break
            clipped.append({**shot, "end": min(shot["end"], duration)})
        shots = clipped
    return shots


def _resolve_plan(scene):
    render_plan = scene.get("render_plan")
    if not isinstance(render_plan, dict):
        from .planner import build_editorial_plan
        render_plan = build_editorial_plan(scene)["render_plan"]
        scene["render_plan"] = render_plan

    layout = render_plan.get("layout") or {}
    layout_family = str(render_plan.get("layout_family") or layout.get("family") or "editorial").lower()
    primitive = str(render_plan.get("primitive") or "").lower()
    if primitive not in PRIMITIVE_EXECUTORS:
        for item in render_plan.get("primitives", []):
            candidate = str(item.get("name", "") if isinstance(item, dict) else item).lower()
            if candidate in PRIMITIVE_EXECUTORS:
                primitive = candidate
                break
    if primitive not in PRIMITIVE_EXECUTORS:
        primitive = {
            "network": "network_nodes",
            "split_screen": "comparison_split",
            "comparison": "comparison_split",
            "horizontal_process": "process_flow",
            "vertical_process": "process_flow",
            "timeline": "process_flow",
            "diagram": "stacked_layers",
        }.get(layout_family, "large_metric")

    motion = render_plan.get("motion") or {}
    camera = render_plan.get("camera") or {}
    motion_primary = str(motion.get("primary", "reveal")).lower()
    camera_behavior = str(camera.get("behavior", "static")).lower()
    action = str(render_plan.get("action", "")).lower()
    if action not in ACTION_EXECUTORS:
        action = {
            "network_nodes": "connect",
            "large_metric": "count_up",
            "comparison_split": "compare",
            "process_flow": "sequence",
            "stacked_layers": "transform",
        }.get(primitive, "reveal")
    if primitive == "large_metric" and action == "count_up":
        metric_value = render_plan.get("metric_value")
        try:
            float(str(metric_value).replace(",", ""))
        except (TypeError, ValueError):
            action = "reveal"
            render_plan["action"] = action
            render_plan["metric_value"] = None
    duration = float(scene.get("_render_duration_seconds", 0) or 0)
    if duration <= 0:
        duration = max(5.0, max((float(s.get("end", 0)) for s in render_plan.get("shot_plan", []) if isinstance(s, dict)), default=0.0))
    shots = _normalize_shots(render_plan.get("shot_plan"), duration)
    render_plan["shot_plan"] = shots
    return render_plan, layout_family, primitive, action, motion_primary, camera_behavior, duration, shots


def build_editorial_executor(scene: dict, idx: int, total: int):
    """Build pixel operations exclusively from scene.render_plan for editorial scenes."""
    from animation import El, FH1, FH2, FL, FS, W, H

    render_plan, layout_family, primitive, action, motion_primary, camera_behavior, duration, shots = _resolve_plan(scene)
    render_mode = str(scene.get("_template_mode") or (scene.get("template_context") or {}).get("template_mode") or "editorial_explainer")
    layout_primitive = {
        "network": "network_nodes",
        "split_screen": "comparison_split",
        "comparison": "comparison_split",
        "horizontal_process": "process_flow",
        "vertical_process": "process_flow",
        "timeline": "process_flow",
    }.get(layout_family)
    layout_executor = LAYOUT_EXECUTORS.get(layout_family, "editorial_layout")
    if primitive != layout_primitive:
        layout_executor = f"{layout_executor}_scaffold"
    manifest = {
        "render_mode": render_mode,
        "render_plan_source": "scene.render_plan",
        "layout_executor": layout_executor,
        "primitive_executors": [PRIMITIVE_EXECUTORS[primitive]],
        "actions_executed": [],
        "camera_executed": camera_behavior,
        "motion_executed": [motion_primary],
        "shots_executed": [],
        "legacy_template_bypassed": True,
    }
    scene["render_manifest"] = manifest
    role = str(scene.get("role", "process")).upper()
    headline = str(scene.get("headline", scene.get("narration", ""))).strip()
    narration = str(scene.get("narration", ""))
    fact = str(scene.get("supporting_fact", "")).strip()
    entities = render_plan.get("entities") or []
    subject = str(render_plan.get("subject") or (entities[0] if entities else headline))
    tracked_shots = set()
    active_action = {"value": action}
    animation_state = {"progress": 0.0, "time": 0.0}

    def process_labels():
        stop_words = {
            "THE", "AND", "OF", "TO", "A", "AN", "IN", "ON", "FOR", "WHY", "HOW", "IS", "WAS",
            "ARE", "WERE", "WITH", "FROM", "THIS", "THAT", "THEY", "IT", "AS", "BY", "AT", "BE",
            "INTO", "USED", "MAKE", "MAKES", "TRULY", "SUDDENLY", "ENTIRE", "JUST", "NOW",
        }
        labels = []
        for source in (headline, fact, narration):
            for token in re.findall(r"[A-Za-z0-9]+", source.upper()):
                if len(token) < 3 or token in stop_words or token in labels:
                    continue
                labels.append(token[:9])
                if len(labels) == 3:
                    return labels
        return labels + ["NEXT"] * (3 - len(labels))

    flow_labels = process_labels()

    def timeline_labels():
        text = f"{headline} {narration}".lower()
        if "hundred million" in text or "100 million" in text:
            period = "2 MONTHS" if "two months" in text or "2 months" in text else "GROWTH"
            return ["GROWTH", "100M USERS", period]
        return flow_labels

    def shot_at(t_seconds):
        for index, shot in enumerate(shots):
            if shot["start"] <= t_seconds < shot["end"] or (index == len(shots) - 1 and t_seconds <= shot["end"]):
                return index, shot
        return len(shots) - 1, shots[-1]

    def background(img: Image.Image, t_seconds: float = 0.0):
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, W, H), fill=BACKGROUND)
        for y in range(220, H - 180, 120):
            draw.line((84, y, W - 84, y), fill="#E8EDF5", width=1)
        draw.line((84, 205, 84, H - 180), fill="#D7E0ED", width=2)

    def brand_draw(draw, x, y, progress, data):
        draw.rectangle((84, y - 24, 96, y + 24), fill=CYAN)
        _text(draw, (118, y), "AI SIMPLIFIED LAB", FS, INK, anchor="lm")
        draw.text((W - 86, y), f"{idx + 1:02d} / {total:02d}", font=FS, fill=MUTED, anchor="rm")

    def headline_draw(draw, x, y, progress, data):
        words = headline.upper().split()
        if not words:
            return
        max_chars = 25
        line = ""
        lines = []
        for word in words:
            if line and len(line) + len(word) + 1 > max_chars:
                lines.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            lines.append(line)
        for line_index, line_text in enumerate(lines[:3]):
            _text(draw, (x, y + line_index * 76), line_text, FH1 if line_index == 0 else FH2,
                  INK if line_index == 0 else BLUE)

    def draw_network(draw, x, y, scale, phase, shot_index):
        points = [(-245, -120), (-70, -210), (160, -150), (245, 35), (65, 205), (-185, 145)]
        links = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (1, 4), (0, 3)]
        reveal = animation_state["progress"] if active_action["value"] == "connect" else 1.0
        for edge_index, (a, b) in enumerate(links):
            if active_action["value"] == "connect" and edge_index / len(links) > reveal:
                continue
            ax, ay = points[a]
            bx, by = points[b]
            draw.line((x + ax * scale, y + ay * scale, x + bx * scale, y + by * scale), fill=BLUE, width=max(3, int(6 * scale)))
        for point_index, (px, py) in enumerate(points):
            pulse = 4 * math.sin(animation_state["time"] * 2.4) if point_index == shot_index % len(points) else 0
            radius = int((26 + (8 if point_index == shot_index % len(points) else 0) + pulse) * scale)
            fill = CORAL if point_index == shot_index % len(points) else CYAN
            draw.ellipse((x + px * scale - radius, y + py * scale - radius,
                          x + px * scale + radius, y + py * scale + radius), fill=fill, outline=INK, width=3)

    def draw_metric(draw, x, y, scale, phase, shot_index):
        raw_value = render_plan.get("metric_value")
        if raw_value is None:
            label = str(render_plan.get("metric_label") or fact or headline).upper()
            _text(draw, (x, y - 12), label[:24], FH2, BLUE)
            draw.line((x - 170, y + 75, x + 170, y + 75), fill=CORAL, width=8)
            return
        value = float(str(raw_value).replace(",", ""))
        shown = value * animation_state["progress"] if active_action["value"] == "count_up" else value
        value_text = f"{shown:,.0f}" if shown.is_integer() else f"{shown:,.1f}"
        _text(draw, (x, y - 20), value_text, FH1, BLUE)
        _text(draw, (x, y + 102), str(render_plan.get("metric_label") or subject).upper(), FS, INK)
        bar_width = int(440 * max(0.12, animation_state["progress"] if active_action["value"] == "count_up" else 0.78))
        draw.rectangle((x - 220, y + 165, x - 220 + bar_width, y + 190), fill=CORAL)
        draw.rectangle((x - 220 + bar_width, y + 165, x + 220, y + 190), fill=PALE_BLUE)

    def draw_comparison(draw, x, y, scale, phase, shot_index):
        half = int(205 * scale)
        gap = int(22 * scale)
        top, bottom = y - int(190 * scale), y + int(190 * scale)
        draw.rectangle((x - gap - half, top, x - gap, bottom), fill=PALE_BLUE, outline=BLUE, width=4)
        draw.rectangle((x + gap, top, x + gap + half, bottom), fill=PALE_CYAN, outline=CYAN, width=4)
        _text(draw, (x - gap - half // 2, y - 25 * scale), "BEFORE", FL, INK)
        _text(draw, (x + gap + half // 2, y - 25 * scale), "AFTER", FL, INK)
        draw.line((x, top + 40, x, bottom - 40), fill=CORAL, width=6)
        if active_action["value"] == "compare" and phase > 0.5:
            draw.polygon([(x - 22, y - 12), (x + 8, y - 12), (x + 8, y - 32), (x + 42, y),
                          (x + 8, y + 32), (x + 8, y + 12), (x - 22, y + 12)], fill=CORAL)

    def draw_process(draw, x, y, scale, phase, shot_index):
        offsets = [-235, 0, 235] if layout_family != "vertical_process" else [ -180, 0, 180 ]
        for step_index, offset in enumerate(offsets):
            px = x + (offset if layout_family != "vertical_process" else 0)
            py = y if layout_family != "vertical_process" else y + offset
            radius = int(78 * scale)
            fill = CORAL if step_index == shot_index % 3 else (BLUE if step_index <= shot_index % 3 else PALE_BLUE)
            draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=fill, outline=INK, width=4)
            _text(draw, (px, py), flow_labels[step_index], FS, "#FFFFFF" if fill != PALE_BLUE else INK)
            if step_index < 2:
                if layout_family == "vertical_process":
                    next_y = y + offsets[step_index + 1]
                    draw.line((px, py + radius + 12, px, next_y - radius - 18), fill=CYAN, width=8)
                else:
                    next_x = x + offsets[step_index + 1]
                    draw.line((px + radius + 12, py, next_x - radius - 18, py), fill=CYAN, width=8)

    def draw_layout(draw, x, y, scale, phase, shot_index):
        if layout_family == "network":
            draw_network(draw, x, y, scale, phase, shot_index)
        elif layout_family in ("split_screen", "comparison"):
            draw_comparison(draw, x, y, scale, phase, shot_index)
        elif layout_family in ("horizontal_process", "vertical_process"):
            draw_process(draw, x, y, scale, phase, shot_index)
        elif layout_family == "timeline":
            labels = timeline_labels()
            line_y = y + 35
            draw.line((x - 265 * scale, line_y, x + 265 * scale, line_y), fill=BLUE, width=8)
            for dot_index, label in enumerate(labels):
                px = x - 250 * scale + dot_index * 250 * scale
                radius = 29 * scale
                draw.ellipse((px - radius, line_y - radius, px + radius, line_y + radius), fill=CORAL if dot_index == shot_index % 3 else CYAN)
                _text(draw, (px, line_y + 74), label, FS, INK)
        elif layout_family == "diagram":
            for layer in range(3):
                yy = y - 150 * scale + layer * 145 * scale
                draw.line((x - 230 * scale, yy, x + 230 * scale, yy), fill=BLUE, width=max(8, int(22 * scale)))
                _text(draw, (x, yy - 38 * scale), ("MODEL", "TOOLS", "DATA")[layer], FS, INK)
        elif layout_family == "detail_zoom":
            radius = (125 + 20 * math.sin(phase * math.pi)) * scale
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=CORAL, width=max(8, int(18 * scale)))
            draw.ellipse((x - radius * .58, y - radius * .58, x + radius * .58, y + radius * .58), fill=PALE_BLUE, outline=BLUE, width=6)
        else:
            draw_network(draw, x, y, scale * .8, phase, shot_index)

    def draw_layout_scaffold(draw, x, y, scale, shot_index):
        y -= 300
        if layout_family == "network":
            points = [(-90, -30), (0, -65), (95, -20), (35, 55), (-80, 50)]
            for a, b in ((0, 1), (1, 2), (2, 3), (3, 4), (4, 0)):
                draw.line((x + points[a][0], y + points[a][1], x + points[b][0], y + points[b][1]), fill=BLUE, width=4)
            for point_index, (px, py) in enumerate(points):
                draw.ellipse((x + px - 10, y + py - 10, x + px + 10, y + py + 10), fill=CORAL if point_index == shot_index % 5 else CYAN)
        elif layout_family in ("split_screen", "comparison"):
            draw.line((x, y - 55, x, y + 55), fill=CORAL, width=6)
            draw.line((x - 145, y - 55, x - 30, y - 55), fill=BLUE, width=6)
            draw.line((x - 145, y + 55, x - 30, y + 55), fill=BLUE, width=6)
            draw.line((x + 30, y - 55, x + 145, y - 55), fill=CYAN, width=6)
            draw.line((x + 30, y + 55, x + 145, y + 55), fill=CYAN, width=6)
        elif layout_family in ("horizontal_process", "vertical_process", "timeline"):
            draw.line((x - 160, y, x + 160, y), fill=BLUE, width=5)
            for point_index in range(3):
                px = x - 140 + point_index * 140
                draw.ellipse((px - 13, y - 13, px + 13, y + 13), fill=CORAL if point_index == shot_index % 3 else CYAN)
        else:
            draw.ellipse((x - 55, y - 55, x + 55, y + 55), outline=CORAL, width=6)
            draw.ellipse((x - 27, y - 27, x + 27, y + 27), fill=PALE_BLUE, outline=BLUE, width=4)

    def draw_primitive(draw, x, y, scale, phase, shot_index):
        if primitive == "network_nodes":
            draw_network(draw, x, y, scale, phase, shot_index)
        elif primitive == "large_metric":
            draw_metric(draw, x, y, scale, phase, shot_index)
        elif primitive == "process_flow":
            draw_process(draw, x, y, scale, phase, shot_index)
        elif primitive == "comparison_split":
            draw_comparison(draw, x, y, scale, phase, shot_index)
        elif primitive == "data_bars":
            for bar_index, height in enumerate((105, 180, 290, 390)):
                left = x - 235 * scale + bar_index * 125 * scale
                draw.rectangle((left, y + 180 * scale - height * scale, left + 72 * scale, y + 180 * scale),
                               fill=CORAL if bar_index == shot_index % 4 else BLUE)
        elif primitive == "stacked_layers":
            for layer in range(4):
                left = x - 200 * scale + layer * 28 * scale
                top = y - 150 * scale + layer * 90 * scale
                draw.rectangle((left, top, x + 200 * scale, top + 54 * scale), fill=(PALE_BLUE, PALE_CYAN, "#FFE3D9", "#DDEBD8")[layer], outline=BLUE, width=3)
        elif primitive == "map_pins":
            for pin_index, (dx, dy) in enumerate(((-180, -60), (0, 80), (180, -100))):
                px, py = x + dx * scale, y + dy * scale
                draw.ellipse((px - 27 * scale, py - 27 * scale, px + 27 * scale, py + 27 * scale), fill=CORAL if pin_index == shot_index % 3 else BLUE)
                draw.line((px, py + 22 * scale, px, py + 70 * scale), fill=INK, width=5)

    def visual_draw(draw, x, y, progress, data):
        t_seconds = float(getattr(draw, "t_seconds", 0.0))
        scene_progress = max(0.0, min(1.0, t_seconds / max(duration, 0.001)))
        animation_state["progress"] = scene_progress
        animation_state["time"] = t_seconds
        shot_index, shot = shot_at(t_seconds)
        active_action["value"] = shot["action"] if shot["action"] in ACTION_EXECUTORS else action
        if shot_index not in tracked_shots:
            tracked_shots.add(shot_index)
            action_executor = ACTION_EXECUTORS.get(active_action["value"], "reveal_visual")
            if action_executor not in manifest["actions_executed"]:
                manifest["actions_executed"].append(action_executor)
            manifest["shots_executed"].append({
                "index": shot_index,
                "start": shot["start"],
                "end": shot["end"],
                "focus": shot["focus"],
                "visual_story": shot["visual_story"],
                "action": active_action["value"],
            })
        phase = max(0.0, min(1.0, (t_seconds - shot["start"]) / max(shot["end"] - shot["start"], 0.001)))
        if motion_primary in {"grow", "expand_outward", "metric_rise"}:
            scale = 0.82 + 0.18 * scene_progress
        elif motion_primary in {"reveal", "hero_reveal", "layer_reveal"}:
            scale = 0.82 + 0.18 * min(1.0, scene_progress * 2.5)
        elif motion_primary in {"pulse_emphasis", "network_fade"}:
            scale = 0.97 + 0.04 * (0.5 + 0.5 * math.sin(t_seconds * 2.5))
        elif motion_primary in {"progression", "event_flow", "connection_draw"}:
            scale = 0.98 + 0.02 * math.sin(t_seconds * 2.0)
        else:
            scale = 0.98 + 0.015 * math.sin(t_seconds * 1.8)
        scale *= 1.0 + 0.018 * math.sin(t_seconds * 2.2)
        if active_action["value"] == "grow":
            scale *= 0.7 + 0.3 * scene_progress
        visual_x = x + (18 * math.sin(t_seconds * 0.8) if motion_primary in {"progression", "event_flow"} else 0)

        if primitive == layout_primitive:
            draw_layout(draw, visual_x, y, scale, phase, shot_index)
        else:
            draw_layout_scaffold(draw, visual_x, y, scale, shot_index)
            draw_primitive(draw, visual_x, y, scale, phase, shot_index)
        if active_action["value"] == "connect" and primitive != "network_nodes":
            connector_y = y - 330
            connector_points = [x - 130, x, x + 130]
            for connection_index in range(2):
                if phase >= (connection_index + 1) / 2:
                    draw.line((connector_points[connection_index], connector_y,
                               connector_points[connection_index + 1], connector_y), fill=BLUE, width=8)
            for point_index, point_x in enumerate(connector_points):
                radius = 18
                draw.ellipse((point_x - radius, connector_y - radius, point_x + radius, connector_y + radius),
                             fill=CORAL if point_index == shot_index % 3 else CYAN, outline=INK, width=2)
        elif active_action["value"] == "count_up" and primitive != "large_metric":
            _text(draw, (x, y - 330), str(int(100 * phase)), FH2, BLUE)
        elif active_action["value"] == "compare" and primitive != "comparison_split" and phase > 0.5:
            draw.line((x, y - 350, x, y - 275), fill=CORAL, width=8)
            draw.polygon([(x - 20, y - 295), (x, y - 275), (x + 20, y - 295)], fill=CORAL)
        _text(draw, (x, y + 300), shot["focus"].upper(), FL, CORAL if shot_index % 2 else BLUE)
        story = shot["visual_story"][:54]
        _text(draw, (x, y + 350), story, FS, MUTED)
        if active_action["value"] == "isolate":
            draw.ellipse((x - 125, y - 125, x + 125, y + 125), outline=CORAL, width=14)
        elif active_action["value"] == "transform":
            draw.arc((x - 160, y - 160, x + 160, y + 160), 15, 310, fill=CORAL, width=12)

    def fact_draw(draw, x, y, progress, data):
        if fact:
            draw.rectangle((84, y - 30, 100, y + 30), fill=CORAL)
            _text(draw, (125, y), fact[:58], FS, INK, anchor="lm")

    def footer_draw(draw, x, y, progress, data):
        _text(draw, (x, y), f"{subject.upper()}  /  {role}", FS, MUTED)

    elements = [
        El(x=W // 2, y=110, enter_start=0.0, enter_end=0.02, motion="fade", persist=True, draw_fn=brand_draw),
        El(x=W // 2, y=370, enter_start=0.0, enter_end=0.12, motion="fade", draw_fn=headline_draw),
        El(x=W // 2, y=1040, enter_start=0.0, enter_end=0.08, motion="fade", draw_fn=visual_draw),
        El(x=W // 2, y=1550, enter_start=0.0, enter_end=0.04, motion="fade", persist=True, draw_fn=fact_draw),
        El(x=W // 2, y=1765, enter_start=0.0, enter_end=0.02, motion="fade", persist=True, draw_fn=footer_draw),
    ]
    return elements, BACKGROUND, background, manifest