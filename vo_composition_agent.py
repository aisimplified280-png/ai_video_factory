"""VO-Sync & Scene Composition Agent for AI SIMPLIFIED LAB.

Handles:
  1. Dynamic Layout Scaling & Spatial Relativity: Prevents element overlap, enforces card container bounds and clean orbital positioning.
  2. Connecting Arrow Anchor Resolver: Dynamically calculates exact from->to endpoints for arrows connecting central hubs to satellite nodes.
  3. Voice-Over VTT Word-Level Sync: Maps element entry timing to exact spoken narration timestamps.
  4. Progressive Element Sequencing: Prevents all-at-once entry; staggers elements dynamically.
  5. Active VO Focal Spotlight: Highlights visual presence on active spoken element.
"""
from __future__ import annotations

from typing import List, Dict, Any


def arrange_scene_layout(elements: List[Dict[str, Any]], scene_title: str = "", scene_duration: float = 4.0,
                         template_mode: str = "") -> List[Dict[str, Any]]:
    """Dynamic Element Layout, Spatial Relativity & Scale Resolver.

    For viral_short_v1 scenes, this is a NO-OP — layout is owned by viral_template.py.
    """
    if not elements:
        return []

    # ── VIRAL / EDITORIAL BYPASS: layout is fully controlled by template mode ──
    if template_mode in ("viral_explainer", "viral_news", "viral_short_v1", "viral_short_v2", "editorial_explainer", "editorial_viral"):
        return elements
    # Also detect via element markers
    if elements and elements[0].get("_viral_scene"):
        return elements

    # ── LLM INTENT PRESERVATION ──
    # If the LLM has already hallucinated specific x, y coordinates or custom python code, 
    # we MUST backup those exact coordinates so our fallback templating doesn't destroy the AI's creativity.
    for el in elements:
        if "x" in el: el["_ai_x"] = el["x"]
        if "y" in el: el["_ai_y"] = el["y"]
        if "width" in el: el["_ai_w"] = el["width"]
        if "height" in el: el["_ai_h"] = el["height"]
        if "motion" in el: el["_ai_m"] = el["motion"]
        if "enter_start" in el: el["_ai_s"] = el["enter_start"]

    # ── PURPOSE AUDITOR: PURGE MEANINGLESS / EMPTY DECORATIVE ELEMENTS ──
    clean_elements = []
    for el in elements:
        etype = str(el.get("type", "")).lower()
        txt = str(el.get("text") or el.get("title") or el.get("label") or el.get("heading") or "").strip()
        code = str(el.get("python_draw_code") or "").strip()
        
        # Discard generic empty custom boxes or cards without text or drawing logic
        if etype in ("custom", "box", "card", "text") and not txt and not code:
            continue
        clean_elements.append(el)
    elements = clean_elements

    if not elements:
        return []

    num_els = len(elements)
    
    # ── IDENTIFY CATEGORIES & HERO CONTAINER ──
    containers = [e for e in elements if e.get("type") in ("layers", "layers_stack", "vs_card", "mac_window", "code_editor", "comparison_grid")]
    arrows = [e for e in elements if e.get("type") in ("arrow", "data_flow", "hash_flow")]
    satellites = [e for e in elements if e.get("type") in ("database", "server", "cloud", "smartphone", "terminal", "ai_icon", "icon")]
    badges = [e for e in elements if e.get("type") in ("badge", "pill", "tech_header")]
    metrics = [e for e in elements if e.get("type") in ("metric", "stat", "counter", "impact_callout")]
    
    # ── CASE A: SCENE WITH A LARGE PRIMARY CONTAINER (layers, vs_card, mac_window) ──
    if containers:
        hero = containers[0]
        hero["x"] = 0.5
        hero["y"] = 0.46
        hero["width"] = max(float(hero.get("width", 0.82)), 0.82)
        hero["height"] = max(float(hero.get("height", 0.40)), 0.40)
        hero["enter_start"] = 0.05
        hero["motion"] = hero.get("motion", "scale")
        
        # Position non-container elements relative to the primary container
        non_hero = [e for e in elements if e is not hero]
        sat_idx = 0
        
        for el in non_hero:
            etype = el.get("type")
            if etype in ("badge", "pill", "tech_header"):
                el["x"] = 0.5
                el["y"] = 0.16
                el["enter_start"] = 0.02
                el["motion"] = "slide_down"
            elif etype in ("metric", "stat", "progress_bar", "data_flow"):
                el["x"] = 0.5
                el["y"] = 0.76
                el["enter_start"] = 0.35
                el["motion"] = "slide_up"
            elif etype in ("database", "server", "cloud", "smartphone", "terminal"):
                # Position satellite icons in clear side columns outside container bounds
                side_coords = [
                    (0.16, 0.26), (0.84, 0.26),
                    (0.16, 0.66), (0.84, 0.66),
                    (0.5, 0.78)
                ]
                cx, cy = side_coords[min(sat_idx, len(side_coords) - 1)]
                el["x"] = cx
                el["y"] = cy
                el["enter_start"] = round(0.20 + sat_idx * 0.15, 2)
                el["motion"] = "pop"
                sat_idx += 1
            elif etype == "arrow":
                # Connect from container to satellite
                el["from_x"] = 0.5
                el["from_y"] = 0.46
                el["to_x"] = 0.5
                el["to_y"] = 0.76
                el["enter_start"] = 0.45
                el["motion"] = "draw_line"

        return elements

    # ── CASE B: SCENE WITH CENTRAL HUB & SATELLITES (Network / Architecture Diagram) ──
    if satellites and num_els >= 3:
        # First element is the central hub/core (whether custom, cloud, or ai_model)
        hub = elements[0]
        hub["x"] = 0.5
        hub["y"] = 0.44
        hub["width"] = 0.28
        hub["height"] = 0.14
        hub["enter_start"] = 0.05
        hub["motion"] = "pop"
        
        other_nodes = [e for e in elements if e is not hub and e.get("type") not in ("arrow", "data_flow")]
        cardinal_slots = [
            (0.18, 0.20), # Top-Left
            (0.82, 0.20), # Top-Right
            (0.18, 0.68), # Bottom-Left
            (0.82, 0.68), # Bottom-Right
            (0.50, 0.78)  # Bottom-Center
        ]
        
        for idx, node in enumerate(other_nodes):
            cx, cy = cardinal_slots[min(idx, len(cardinal_slots) - 1)]
            node["x"] = cx
            node["y"] = cy
            node["enter_start"] = round(0.15 + idx * 0.12, 2)
            node["motion"] = "slide_down" if cy < 0.4 else "slide_up"

        # Resolve explicit connecting arrows between Hub and Satellites
        arrow_idx = 0
        for el in elements:
            if el.get("type") in ("arrow", "data_flow"):
                if arrow_idx < len(other_nodes):
                    target_sat = other_nodes[arrow_idx]
                    el["from_x"] = 0.5
                    el["from_y"] = 0.44
                    el["to_x"] = target_sat["x"]
                    el["to_y"] = target_sat["y"]
                    el["enter_start"] = round(target_sat["enter_start"] + 0.08, 2)
                    el["motion"] = "draw_line"
                    arrow_idx += 1
                else:
                    el["from_x"] = 0.5
                    el["from_y"] = 0.44
                    el["to_x"] = 0.5
                    el["to_y"] = 0.76
                    el["enter_start"] = 0.40
                    el["motion"] = "draw_line"
                    
        # Position remaining badges/text outside hub orbit
        for el in elements:
            if el not in satellites and el.get("type") not in ("arrow", "data_flow"):
                if el.get("type") in ("badge", "pill", "tech_header"):
                    el["x"] = 0.5
                    el["y"] = 0.15
                    el["enter_start"] = 0.02
                else:
                    el["x"] = 0.5
                    el["y"] = 0.78
                    el["enter_start"] = 0.50

        return elements

    # ── CASE C: STANDARD 1, 2, OR 3 ELEMENT VERTICAL STACK ──
    if num_els == 1:
        el = elements[0]
        el["x"] = 0.5
        el["y"] = 0.50
        el["width"] = max(float(el.get("width", 0.85)), 0.85)
        el["height"] = max(float(el.get("height", 0.38)), 0.38)
        el["motion"] = "scale"
        el["enter_start"] = 0.05

        if scene_duration >= 2.5 and scene_title:
            badge_title = scene_title.upper()[:30]
            top_badge = {
                "type": "badge",
                "text": badge_title,
                "x": 0.5,
                "y": 0.18,
                "width": 0.65,
                "height": 0.06,
                "motion": "slide_down",
                "enter_start": 0.02,
                "color": "ACCENT",
                "persist": True
            }
            elements = [top_badge, el]
            el["y"] = 0.52

    elif num_els == 2:
        elements[0]["x"] = 0.5
        elements[0]["y"] = 0.32
        elements[0]["width"] = max(float(elements[0].get("width", 0.85)), 0.85)
        elements[0]["height"] = max(float(elements[0].get("height", 0.28)), 0.28)
        elements[0]["motion"] = "pop"
        elements[0]["enter_start"] = 0.05

        elements[1]["x"] = 0.5
        elements[1]["y"] = 0.68
        elements[1]["width"] = max(float(elements[1].get("width", 0.85)), 0.85)
        elements[1]["height"] = max(float(elements[1].get("height", 0.26)), 0.26)
        elements[1]["motion"] = "slide_up"
        elements[1]["enter_start"] = 0.35

    elif num_els == 3:
        elements[0]["x"] = 0.5
        elements[0]["y"] = 0.18
        elements[0]["motion"] = "slide_down"
        elements[0]["enter_start"] = 0.05

        elements[1]["x"] = 0.5
        elements[1]["y"] = 0.48
        elements[1]["motion"] = "scale" if elements[1].get("type") in ("mac_window", "vs_card", "layers") else "pop"
        elements[1]["enter_start"] = 0.25

        elements[2]["x"] = 0.5
        elements[2]["y"] = 0.76
        elements[2]["motion"] = "slide_up"
        elements[2]["enter_start"] = 0.55

    else:
        # 4+ ELEMENT BALANCED STACK
        y_positions = [0.18, 0.38, 0.60, 0.78]
        stagger_step = min(0.18, 0.70 / num_els)

        for i, el in enumerate(elements):
            el["enter_start"] = round(i * stagger_step, 2)
            el["x"] = 0.5 if i % 3 == 0 else (0.24 if i % 2 == 1 else 0.76)
            el["y"] = y_positions[min(i, len(y_positions) - 1)]

    # ── RESTORE LLM INTENT (WITH COLLISION SAFETY) ──
    # If the LLM lazily assigned the exact same (x,y) to multiple elements, don't restore them
    # because they will smash on top of each other. Let the fallback template handle them.
    for i, el in enumerate(elements):
        if "_ai_x" in el and "_ai_y" in el:
            # Check for collision with any other element's restored coordinates
            collision = False
            for j, other in enumerate(elements):
                if i != j and "_ai_x" in other and "_ai_y" in other:
                    dist = ((el["_ai_x"] - other["_ai_x"])**2 + (el["_ai_y"] - other["_ai_y"])**2)**0.5
                    if dist < 0.05:
                        collision = True
                        break
            if not collision:
                el["x"] = el["_ai_x"]
                el["y"] = el["_ai_y"]
        elif "_ai_x" in el: el["x"] = el["_ai_x"]
        elif "_ai_y" in el: el["y"] = el["_ai_y"]
        
        if "_ai_w" in el: el["width"] = el["_ai_w"]
        if "_ai_h" in el: el["height"] = el["_ai_h"]
        if "_ai_m" in el: el["motion"] = el["_ai_m"]
        if "_ai_s" in el: el["enter_start"] = el["_ai_s"]

    return elements


def sync_elements_to_vo_timing(elements: List[Dict[str, Any]], subs: List[Dict[str, Any]], scene_duration: float) -> List[Dict[str, Any]]:
    """Voice-Over Audio VTT Synchronization Agent: Maps elements to exact spoken narration timestamps."""
    if not elements or not subs or scene_duration <= 0.1:
        return elements

    for el in elements:
        if el.get("persist") and float(el.get("enter_start", 0.0)) < 0.04:
            continue

        keywords = []
        if el.get("sync_word"):
            keywords.append(str(el["sync_word"]).lower())
        if el.get("text"):
            keywords.extend(str(el["text"]).lower().split())
        if el.get("title"):
            keywords.extend(str(el["title"]).lower().split())

        keywords = [k for k in keywords if len(k) > 2 and k not in ("none", "null", "type", "card", "custom", "with", "from", "this", "that")]

        match_start = None
        if keywords:
            for s in subs:
                sub_txt = s.get("text", "").lower()
                for kw in keywords:
                    if kw in sub_txt or any(w.startswith(kw) for w in sub_txt.split()):
                        match_start = s.get("start", 0.0)
                        break
                if match_start is not None:
                    break

        if match_start is not None:
            el["enter_start"] = max(0.05, min(0.88, round(match_start / scene_duration, 3)))
            el["enter_end"] = round(min(1.0, el["enter_start"] + 0.18), 3)

    return elements



def process_scene_composition(scene: Dict[str, Any], subs: List[Dict[str, Any]] = None, scene_duration: float = 4.0) -> Dict[str, Any]:
    """Master Scene Composition Agent entry point.

    For viral_short_v1 scenes: returns unchanged (layout owned by viral_template.py).
    VO subtitle sync still runs for viral scenes via make_scene_frames.
    """
    # \u2500\u2500 VIRAL BYPASS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    from viral_template import is_viral_template_scene
    if is_viral_template_scene(scene):
        return scene

    scene_title = scene.get("heading") or scene.get("title") or scene.get("scene_title") or ""
    v_scene = scene.get("visual_scene")

    if isinstance(v_scene, dict) and v_scene.get("objects"):
        objs = v_scene["objects"]
        objs = arrange_scene_layout(objs, scene_title=scene_title, scene_duration=scene_duration)
        if subs:
            objs = sync_elements_to_vo_timing(objs, subs, scene_duration)
        v_scene["objects"] = objs
    elif scene.get("elements"):
        els = scene["elements"]
        els = arrange_scene_layout(els, scene_title=scene_title, scene_duration=scene_duration)
        if subs:
            els = sync_elements_to_vo_timing(els, subs, scene_duration)
        scene["elements"] = els

    return scene
