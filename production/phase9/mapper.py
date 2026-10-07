import copy
import shutil
from pathlib import Path
from production.phase15.models import SceneVisualPlan, VisualMode
from production.phase15.visual_generator import generate_scene_asset


def _canonical_camera_intent(raw: str | None) -> str:
    """Map any directorial camera string into Remotion's executing camera intents."""
    if not raw:
        return "approach_subject"
    raw_lower = str(raw).lower()
    if any(w in raw_lower for w in ["pull_out", "pullout", "crane_pull", "retreat"]):
        return "pull_out"
    if any(w in raw_lower for w in ["fast_push_in", "push_in", "pushin", "reveal_space", "approach"]):
        return "approach_subject"
    if any(w in raw_lower for w in ["zoom", "dolly", "expand_scale"]):
        return "expand_scale"
    if any(w in raw_lower for w in ["overhead_track", "track", "follow"]):
        return "follow_subject"
    if any(w in raw_lower for w in ["focus", "shift"]):
        return "shift_focus"
    if any(w in raw_lower for w in ["pan", "lateral", "cross"]):
        return "cross_system"
    if any(w in raw_lower for w in ["static", "steady", "breathe", "observe_static"]):
        return "observe_static"
    return "approach_subject"


def _canonical_transition(raw: str | None, scene_idx: int) -> str:
    """Map directorial transition string into Remotion's supported transitions."""
    if not raw or raw == "hard_cut" or scene_idx == 0:
        return "hard_cut"
    raw_lower = str(raw).lower()
    if "wipe" in raw_lower:
        return "directional_wipe"
    if "zoom" in raw_lower:
        return "zoom_transition"
    if "motion_blur" in raw_lower or "blur" in raw_lower:
        return "motion_blur"
    if "light_flash" in raw_lower or "flash" in raw_lower:
        return "light_flash"
    if "dissolve" in raw_lower or "cross" in raw_lower:
        return "cross_dissolve"
    if "fade" in raw_lower:
        return "fade"
    return "hard_cut"


def map_edit_decisions(plan_data, v1_data, project_root):
    """Maps Phase 15 visual intelligence plan into Remotion timeline and assets."""
    v2_data = copy.deepcopy(v1_data)
    timeline = v2_data.get("timeline", [])
    
    # Index concepts by scene_id ("scene_01") and section_id ("sec_01")
    concepts_by_scene = {}
    concepts_by_sec = {}
    for c in plan_data.get("scene_concepts", []):
        if c.get("scene_id"):
            concepts_by_scene[c["scene_id"]] = c
        if c.get("section_id"):
            concepts_by_sec[c["section_id"]] = c

    assets_dir = Path(project_root) / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Filter timeline events to only active scene concepts planned for this production
    active_scene_ids = set(concepts_by_scene.keys()) | {
        c.get("section_id", "").replace("sec_", "scene_") for c in plan_data.get("scene_concepts", []) if c.get("section_id")
    }
    if active_scene_ids:
        timeline = [
            ev for ev in timeline
            if (
                ev.get("scene_id") in active_scene_ids
                or ev.get("scene_id", "").replace("scene_", "sec_") in concepts_by_sec
            )
            and ev.get("role") not in ("metric", "overlay")
        ]
        v2_data["timeline"] = timeline
        if timeline:
            v2_data["total_duration"] = round(max(ev.get("end", 0.0) for ev in timeline), 2)

        # Synchronize CTA to the last planned scene
        cta_concept = next((c for c in reversed(plan_data.get("scene_concepts", [])) if c.get("narrative_role") == "cta"), None)
        if not cta_concept and plan_data.get("scene_concepts"):
            cta_concept = plan_data["scene_concepts"][-1]

        if cta_concept:
            cta_scene_id = cta_concept.get("scene_id") or cta_concept.get("section_id", "").replace("sec_", "scene_")
            cta_events = [ev for ev in timeline if ev.get("scene_id") == cta_scene_id]
            if cta_events:
                cta_start = min(ev.get("start", 0.0) for ev in cta_events)
                cta_end = max(ev.get("end", 0.0) for ev in cta_events)
                v2_data["cta"] = {
                    "scene_id": cta_scene_id,
                    "start": cta_start,
                    "end": cta_end,
                    "channel_branding": "AI Simplified Lab",
                    "caption_event_id": f"caption_{cta_scene_id}",
                    "audio_asset_id": None,
                    "audio_requirement": {
                        "required": True,
                        "spoken_text": "Subscribe to AI Simplified Lab for daily frontier AI briefings.",
                    },
                }

        # Filter caption tracks
        if "caption_track" in v2_data:
            v2_data["caption_track"] = [
                c for c in v2_data["caption_track"]
                if c.get("scene_id") in active_scene_ids
            ]

        # Filter and adjust audio tracks
        total_dur = v2_data.get("total_duration", 30.0)
        if "audio_tracks" in v2_data:
            audio = v2_data["audio_tracks"]
            if "narration" in audio:
                audio["narration"] = [
                    c for c in audio["narration"]
                    if any(sc in c.get("event_id", "") for sc in active_scene_ids) or c.get("start", 0.0) < total_dur
                ]
            if "music" in audio:
                for c in audio["music"]:
                    if c.get("end", 0.0) > total_dur:
                        c["end"] = total_dur
            if "sfx" in audio:
                new_sfx = []
                for c in audio["sfx"]:
                    if c.get("event_id") == "sfx_cta_resolve":
                        c["start"] = max(0.0, total_dur - 0.5)
                        c["end"] = total_dur
                        new_sfx.append(c)
                    elif c.get("start", 0.0) < total_dur:
                        new_sfx.append(c)
                audio["sfx"] = new_sfx


    # 1. Generate & stage distinct visual asset for each planned scene
    for i, c in enumerate(plan_data.get("scene_concepts", [])):
        scene_id = c.get("scene_id")
        if not scene_id:
            continue

        target_png = assets_dir / f"ast_{scene_id}_primary.png"
        
        # Build lightweight SceneVisualPlan wrapper for generator
        vmode_val = c.get("visual_mode", "environment")
        try:
            vmode = VisualMode(vmode_val)
        except Exception:
            vmode = VisualMode.ENVIRONMENT

        plan_obj = SceneVisualPlan(
            scene_id=scene_id,
            section_id=c.get("section_id", "sec_01"),
            visual_mode=vmode,
            shot_type=c.get("shot_type", "cinematic"),
            camera_angle=c.get("camera_angle", "eye_level"),
            camera_motion=c.get("camera_motion", "approach_subject"),
            composition=c.get("composition", "rule_of_thirds"),
            subject=c.get("subject", "Industrial system"),
            action=c.get("action", "operating"),
            environment=c.get("environment", "industrial facility"),
            visual_metaphor=c.get("visual_metaphor", "precision"),
            lighting=c.get("lighting", "directional lighting"),
            motion_intensity=float(c.get("motion_intensity", 6.0)),
            transition_in=c.get("transition_in", "hard_cut"),
            transition_out=c.get("transition_out", "hard_cut"),
            overlay_strategy=c.get("overlay_strategy", "minimal_callout"),
            visual_prompt=c.get("visual_prompt", c.get("background_prompt", "")),
        )

        from production.phase17.multi_layer_generator import generate_scene_layers
        from production.phase17.style_systems import get_style_system
        style = get_style_system("claude_editorial")
        layers = generate_scene_layers(
            scene_index=i,
            narration=c.get("visual_intent", c.get("visual_story", "")),
            output_dir=target_png.parent,
            scene_id=scene_id,
            style=style,
        )

    # 2. Map Directorial Intent to Timeline Events
    for i, event in enumerate(timeline):
        scene_id = event.get("scene_id")
        concept = concepts_by_scene.get(scene_id)
        if not concept and scene_id:
            # Map "scene_01" -> "sec_01"
            sec_mapped = scene_id.replace("scene_", "sec_")
            concept = concepts_by_sec.get(sec_mapped)

        if not concept:
            continue

        # Point timeline events directly to the Phase 16 primary asset
        if event.get("role") in ("diagram", "primary_visual", "image", "broll", "foreground"):
            event["asset_id"] = f"ast_{scene_id}_primary"
            event["role"] = "primary_visual"

        shot_id = event.get("shot_id") or ""
        raw_cam = concept.get("camera_motion") or event.get("camera_intent")
        event["camera_intent"] = _canonical_camera_intent(raw_cam)
        event["motion_intent"] = concept.get("motion_intent", event.get("motion_intent", "reveal"))

        # Map framing & composition crop with intra-scene cut variation
        comp = concept.get("composition", "rule_of_thirds")
        shot_type = concept.get("shot_type", "")

        if shot_id.endswith("_01") or not shot_id:
            # First shot establishes scene's primary planned framing
            if "macro" in comp or "macro" in shot_type or "close" in shot_type:
                event["crop"] = "close_up"
            elif "wide" in comp or "wide" in shot_type or "aerial" in shot_type:
                event["crop"] = "wide"
            elif "studio" in shot_type or "brand" in shot_type:
                event["crop"] = "centered_studio"
            else:
                event["crop"] = "medium"
        elif shot_id.endswith("_02"):
            # Second shot provides dynamic angle/scale cut
            event["crop"] = "medium" if event.get("crop") != "medium" else "close_up"
            event["camera_intent"] = "approach_subject" if event["camera_intent"] != "approach_subject" else "cross_system"
        elif shot_id.endswith("_03"):
            # Third shot focuses on macro detail or wide context
            event["crop"] = "detail"
            event["camera_intent"] = "shift_focus"

        # Apply transitions (Phase 17 Transformative Transitions)
        from production.phase17.transition_director import assign_transformative_transitions
        transforms = assign_transformative_transitions(len(timeline))
        event["transition_in"] = transforms[i % len(transforms)]

        # Apply overlay intent (e.g. no text initially for hook)
        overlay_strat = concept.get("overlay_strategy") or concept.get("overlay_intent")
        if overlay_strat == "none_initial_cut" and (shot_id.endswith("_01") or not shot_id):
            event["overlay_disabled"] = True

        event["visual_requirement"] = {
            "type": "generated_background",
            "visual_mode": concept.get("visual_mode"),
            "shot_type": concept.get("shot_type"),
            "subject": concept["subject"],
            "environment": concept["environment"],
        }

        # Ensure visual variety across adjacent timeline cuts
        if i > 0:
            prev = timeline[i - 1]
            if (
                event.get("camera_intent") == prev.get("camera_intent")
                and event.get("motion_intent") == prev.get("motion_intent")
            ):
                event["camera_intent"] = "cross_system" if prev.get("camera_intent") != "cross_system" else "follow_subject"

    return v2_data
