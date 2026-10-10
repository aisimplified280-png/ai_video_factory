"""Phase 18 Authoritative Artifact Synchronization & Lineage Enforcement.

Enforces strict canonical lineage:
  1. scene_plan (explicit 4-layer depth + character specs)
  2. asset_manifest (registers all bg, mid, char, fg, and primary assets)
  3. art_direction (reflects canonical Royal Blue style system)
  4. edit_decisions (mapped strictly from 1, 2, 3 with multi-track z-indices)

All upstream artifacts are created and approved BEFORE edit_decisions is finalized.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemas.models.artifact import ProducerInfo
from schemas.models.common import ProducerKind
from production.artifact_store import ArtifactStore
from production.phase17.style_systems import StyleSystem, get_style_system
from .visual_director import UnifiedVisualPlan


_DIAGRAM_TOPOLOGIES = (
    "process_flow", "object_transformation", "layered_architecture", "bipartite",
)


def _native_diagram_graph(graph: Any) -> bool:
    """Flow-like topologies render as a NATIVE vector diagram in Remotion: nodes
    and edges from the semantic scene graph animate in sequence (element motion)
    instead of the page moving. Single source of truth for both the manifest and
    the timeline decision."""
    return (
        graph is not None
        and bool(getattr(graph, "nodes", None))
        and getattr(graph, "topology", None) in _DIAGRAM_TOPOLOGIES
    )


def _verify_renderer_lock(repo_root: Path) -> bool:
    """Renderer lock, MEASURED from files: the composer entry exists and the
    Remotion runtime versions are pinned exactly (no ^/~ drift)."""
    pkg = repo_root / "remotion-composer" / "package.json"
    entry = repo_root / "remotion-composer" / "src" / "Root.tsx"
    if not pkg.exists() or not entry.exists():
        return False
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
        deps = data.get("dependencies", {})
        pins = [deps.get("remotion", ""), deps.get("@remotion/cli", "")]
        return all(p and p[0] not in "^~" for p in pins)
    except Exception:
        return False


def sync_authoritative_artifacts(
    store: ArtifactStore,
    state: Any,
    visual_plan: UnifiedVisualPlan,
    script_envelope: Any,
    proposal_envelope: Any,
    style_system: StyleSystem,
    projects_root: Path,
) -> dict[str, Any]:
    """Persist and approve all canonical artifacts in authoritative order."""
    production_id = visual_plan.production_id
    project_dir = projects_root / production_id

    # -------------------------------------------------------------
    # 1. Authoritative SCENE_PLAN
    # -------------------------------------------------------------
    scenes_payload = []
    for sc in visual_plan.scenes:
        scenes_payload.append({
            "id": sc.scene_id,
            "scene_id": sc.scene_id,
            "type": "generated",
            "start_seconds": sc.start_seconds,
            "end_seconds": sc.end_seconds,
            "shot_intent": sc.shot_type,
            "narrative_role": sc.narrative_role,
            "subject": sc.subject,
            "action": sc.action,
            "visual_purpose": sc.visual_purpose,
            "visual_metaphor": sc.visual_metaphor,
            "environment": sc.environment,
            "depth_strategy": "background_midground_foreground",
            "signature_device_usage": "none",
            "transition_in": sc.transition_in,
            "transition_out": sc.transition_out,
            "character_spec": sc.character_spec.to_dict(),
            "required_assets": [l.asset_id for l in sc.layers],
        })

    # Measured variety of the GENERATED plan — distinct visual topologies and
    # distinct node labels — never a fixed score (§9 QA honesty).
    _topos = [getattr(getattr(sc, "scene_graph", None), "topology", None) or "focal" for sc in visual_plan.scenes]
    _node_labels = [n.label for sc in visual_plan.scenes if getattr(sc, "scene_graph", None) for n in sc.scene_graph.nodes]
    _topo_ratio = (len(set(_topos)) / len(_topos)) if _topos else 0.0
    _label_ratio = (len(set(_node_labels)) / len(_node_labels)) if _node_labels else 0.0
    scene_plan_payload = {
        "scenes": scenes_payload,
        "total_duration_seconds": visual_plan.total_duration_seconds,
        "variety_score": round(100.0 * (0.5 * _topo_ratio + 0.5 * _label_ratio), 1),
        "variety_measure": {
            "distinct_topologies": len(set(_topos)),
            "scene_count": len(_topos),
            "distinct_node_labels": len(set(_node_labels)),
            "node_label_count": len(_node_labels),
        },
    }

    scene_env = store.create(
        "scene_plan",
        production_id,
        "scene_plan",
        scene_plan_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="phase18_visual_director"),
    )
    store.save(scene_env)
    store.approve("scene_plan", production_id, scene_env.artifact_version)
    state.set_active_version("scene_plan", scene_env.artifact_version)

    # -------------------------------------------------------------
    # 2. Authoritative ASSET_MANIFEST (Empirically verified files)
    # -------------------------------------------------------------
    manifest_assets = []
    all_ready = True
    for sc in visual_plan.scenes:
        # Flow-like topologies render as a NATIVE vector diagram in Remotion:
        # nodes/edges from the semantic scene graph, so elements themselves
        # animate in sequence (element motion) instead of the page moving.
        graph = getattr(sc, "scene_graph", None)
        diagram_spec = None
        if _native_diagram_graph(graph):
            # Semantic information must survive to the renderer: node_type, shape_style
            # and icon decide HOW each node is drawn (cylinder vs kernel vs card vs a
            # real object glyph); the edge relationship decides HOW each connector is
            # drawn (one-way arrow vs two-sided contrast vs transformation).
            diagram_spec = {
                "topology": graph.topology,
                "composition_intent": getattr(graph, "composition_intent", ""),
                "nodes": [
                    {
                        "id": n.id,
                        "label": n.label,
                        "details": list(n.details[:3]),
                        "primary": bool(n.is_primary),
                        "node_type": getattr(n.node_type, "value", str(n.node_type)),
                        "shape_style": n.shape_style,
                        "icon": getattr(n, "icon", ""),
                        "x": (n.bounds[0] + n.bounds[2]) / 2.0,
                        "y": (n.bounds[1] + n.bounds[3]) / 2.0,
                        "w": float(n.bounds[2] - n.bounds[0]),
                        "h": float(n.bounds[3] - n.bounds[1]),
                    }
                    for n in graph.nodes
                ],
                "connectors": [
                    {
                        "from": e.from_node,
                        "to": e.to_node,
                        "label": e.label or "",
                        "relationship": e.relationship,
                    }
                    for e in graph.edges
                ],
            }
        for lyr in sc.layers:
            full_path = Path(lyr.relative_path)
            if not full_path.is_absolute():
                full_path = projects_root.parent / lyr.relative_path
            
            is_valid = full_path.exists() and full_path.stat().st_size > 0
            if not is_valid:
                all_ready = False

            manifest_assets.append({
                "asset_id": lyr.asset_id,
                "scene_id": sc.scene_id,
                "purpose": lyr.purpose,
                "role": lyr.role,
                "z_index": lyr.z_index,
                "type": "image",
                "source": "generated",
                "status": "ready" if is_valid else "pending",
                "file_path": lyr.relative_path,
                # The PNG stays registered (QA/fallback); nativeSpec makes the
                # renderer prefer the animated vector diagram when eligible.
                "diagram_spec": diagram_spec if lyr.role == "midground" else None,
                # The constant global canvas renders INSTEAD of per-scene
                # backgrounds: background PNGs are diagnostics only, clearly
                # labelled and never part of the live timeline (§10).
                "rendered_in_timeline": lyr.role != "background",
            })

    manifest_payload = {
        "assets": manifest_assets,
        "total_estimated_cost": 0.0,
        "all_assets_ready": all_ready,
    }

    manifest_env = store.create(
        "asset_manifest",
        production_id,
        "assets",
        manifest_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="phase18_asset_director"),
    )
    store.save(manifest_env)
    store.approve("asset_manifest", production_id, manifest_env.artifact_version)
    state.set_active_version("asset_manifest", manifest_env.artifact_version)

    # -------------------------------------------------------------
    # 3. Authoritative ART_DIRECTION
    # -------------------------------------------------------------
    art_payload = {
        "design_read": f"Phase 18 {style_system.name}: {style_system.description}",
        # §6/§15/§4: clarity over variety, subtle motion, no filler content.
        "visual_variance": 5,
        "motion_intensity": 4,
        "information_density": 4,
        "palette_discipline": {
            "primary": style_system.primary_bg,
            "accent_1": style_system.accent,
            "accent_2": style_system.accent_secondary,
            "neutral": style_system.secondary_text,
        },
        "typography_personality": style_system.name,
        "layout_language": "Single-subject explanatory composition with clear hierarchy and intentional whitespace",
        "signature_device": "Consistent subject-first explanatory framing",
        "anti_patterns": [
            "decoration without a narrative purpose (telemetry cards, side rails, HUD frames)",
            "generic technical labels absent from the narration (STAGE 1, ENGINE, PIPELINE)",
            "forced motion on a scene that simply states a fact",
            "glowing cyan wires in black void",
        ],
    }
    art_env = store.create(
        "art_direction",
        production_id,
        "art_direction",
        art_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="phase18_art_director"),
    )
    store.save(art_env)
    store.approve("art_direction", production_id, art_env.artifact_version)
    state.set_active_version("art_direction", art_env.artifact_version)

    # -------------------------------------------------------------
    # 4. Authoritative EDIT_DECISIONS (Multi-Layer Timeline)
    # Strict 4-layer depth: bg, mid, char, fg.
    # Primary composite is reserved for single-track fallback/exports only.
    # -------------------------------------------------------------
    timeline_events = []
    bg_track = []
    mid_track = []
    char_track = []
    fg_track = []
    primary_track = []
    narration_track = []
    caption_track = []

    for sc in visual_plan.scenes:
        # Diagram eligibility for THIS scene — never a stale value carried over
        # from another loop (the manifest loop's last scene is the CTA).
        sc_has_diagram = _native_diagram_graph(getattr(sc, "scene_graph", None))
        for lyr in sc.layers:
            # §10: per-scene backgrounds are NOT part of the live timeline — the
            # constant global canvas renders instead. Their PNGs remain in the
            # manifest as clearly-labelled diagnostics.
            if lyr.role == "background":
                continue
            ev = {
                "event_id": f"event_{lyr.asset_id}",
                "scene_id": sc.scene_id,
                "shot_id": f"{sc.scene_id}_shot_01",
                "track_id": f"video_{lyr.role}",
                "role": lyr.role,
                "asset_id": lyr.asset_id,
                "start": sc.start_seconds,
                "end": sc.end_seconds,
                "duration": sc.duration_seconds,
                "z_index": lyr.z_index,
                "parallax_factor": lyr.parallax_factor,
                "purpose": lyr.purpose,
                "framing": sc.shot_type,
                "camera_intent": sc.camera_motion,
                # Static is the default (§5): elements hold still unless the
                # motion explains something. Diagram events assemble in sequence
                # (element choreography that mirrors the narrated flow); baked
                # cards, mascot and framing never receive forced motion.
                "motion_intent": "assemble" if (lyr.role == "midground" and sc_has_diagram) else None,
                "transition_in": sc.transition_in,
                "transition_out": sc.transition_out,
                "character_spec": sc.character_spec.to_dict() if lyr.role == "character" else None,
            }
            if lyr.role in ("primary_visual", "primary_composite"):
                # Primary track only for fallback single-layer timeline
                primary_track.append(ev)
            else:
                # Strictly 4 distinct depth layers in live Remotion multi_layer_timeline
                timeline_events.append(ev)
                if lyr.role == "midground":
                    mid_track.append(ev)
                elif lyr.role == "character":
                    char_track.append(ev)
                elif lyr.role == "foreground":
                    fg_track.append(ev)

        # Narration track
        audio_file = f"projects/{production_id}/audio/narration_{sc.scene_id}.mp3"
        narration_ev = {
            "event_id": f"narration_{sc.scene_id}",
            "track": "narration",
            "start": sc.start_seconds,
            "end": sc.end_seconds,
            "audio_asset_id": audio_file,
            "requirement": {"required": True, "spoken_text": sc.spoken_text},
        }
        narration_track.append(narration_ev)

        # Caption track
        caption_ev = {
            "event_id": f"caption_{sc.scene_id}",
            "scene_id": sc.scene_id,
            "start": sc.start_seconds,
            "end": sc.end_seconds,
            "audio_duration": sc.duration_seconds,
            "caption_text_reference": sc.section_id,
            "safe_zone": "caption",
            "emphasis_words": sc.emphasis_words,
        }
        caption_track.append(caption_ev)

    total_dur = visual_plan.total_duration_seconds
    cta_sc = visual_plan.scenes[-1]
    cta_audio_file = f"projects/{production_id}/audio/narration_{cta_sc.scene_id}.mp3"

    # §9 QA honesty: every validation flag below is MEASURED here from the actual
    # plan and files — never a hardcoded success claim.
    _scenes_sorted = sorted(visual_plan.scenes, key=lambda s: s.start_seconds)
    _no_gaps = all(abs(s.start_seconds - p.end_seconds) <= 0.011 for p, s in zip(_scenes_sorted, _scenes_sorted[1:]))
    _no_overlaps = all(s.start_seconds >= p.end_seconds - 0.011 for p, s in zip(_scenes_sorted, _scenes_sorted[1:]))
    _duration_covered = bool(_scenes_sorted) and abs(_scenes_sorted[-1].end_seconds - total_dur) <= 0.011
    _audio_valid = all(
        (projects_root.parent / f"projects/{production_id}/audio/narration_{s.scene_id}.mp3").exists()
        for s in visual_plan.scenes
    )
    _captions_valid = len(caption_track) == len(visual_plan.scenes) and all(
        c["end"] > c["start"] and bool(c.get("caption_text_reference")) for c in caption_track
    )
    _cta_present = cta_sc.narrative_role.lower() in ("cta", "outro") or "cta" in cta_sc.scene_id.lower()
    _renderer_lock = _verify_renderer_lock(projects_root.parent)

    edit_payload = {
        "production_id": production_id,
        "total_duration": total_dur,
        "platform_profile": "profiles/youtube_short.json",
        "platform": {
            "profile": "profiles/youtube_short.json",
            "resolution": {"width": 1080, "height": 1920},
            "fps": 30,
            "duration_constraints": {"minimum_seconds": 10, "maximum_seconds": 180},
            "safe_zones": {
                "caption": {"top": 1400, "bottom": 1650, "left": 100, "right": 980},
                "cta": {"top": 1650, "bottom": 1850, "left": 100, "right": 980},
                "brand": {"top": 100, "bottom": 250, "left": 100, "right": 980},
            },
        },
        "runtime_lock_source": {
            "artifact_type": "proposal_packet",
            "version": proposal_envelope.artifact_version,
            "content_hash": proposal_envelope.content_hash,
            "locked_at": "2026-10-08T00:00:00Z",
            "locked_concept_id": "c1",
        },
        "render_runtime": "remotion",
        "renderer_family": "explainer",
        "composition_mode": "atelier",
        "timeline": primary_track,  # primary track as baseline for backwards-compatible loaders
        "multi_layer_timeline": timeline_events, # Strictly 4-layer events with z-index & parallax (no duplicate primary)
        "video_tracks": {
            "video_bg": bg_track,
            "video_mid": mid_track,
            "video_char": char_track,
            "video_fg": fg_track,
        },
        "audio_tracks": {
            "narration": narration_track,
            "music": [{"event_id": "music_bed", "track": "music", "start": 0.0, "end": total_dur, "audio_asset_id": None, "requirement": {"required": False}}],
            "sfx": [{"event_id": "sfx_cta_resolve", "track": "sfx", "start": max(0.0, total_dur - 0.5), "end": total_dur, "audio_asset_id": None, "requirement": {"required": False}}],
        },
        "caption_track": caption_track,
        "tracks": {
            "video": ["video_bg", "video_mid", "video_char", "video_fg"],
            "narration": ["narration"],
            "music": ["music"],
            "captions": ["captions"],
            "sfx": ["sfx"],
        },
        "cta": {
            "scene_id": cta_sc.scene_id,
            "start": cta_sc.start_seconds,
            "end": total_dur,
            "channel_branding": "AI Simplified Lab",
            "caption_event_id": f"caption_{cta_sc.scene_id}",
            "audio_asset_id": cta_audio_file,
            "audio_requirement": {
                "required": True,
                "spoken_text": cta_sc.spoken_text or "Subscribe to AI Simplified Lab for daily frontier AI briefings.",
            },
        },
        "validation": {
            "no_gaps": _no_gaps,
            "no_overlaps": _no_overlaps,
            "all_assets_resolved": all_ready,
            "duration_covered": _duration_covered,
            "audio_valid": _audio_valid,
            "captions_valid": _captions_valid,
            "cta_present": _cta_present,
            "renderer_locked": _renderer_lock,
        },
    }

    edit_env = store.create(
        "edit_decisions",
        production_id,
        "edit",
        edit_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="phase18_edit_director"),
        metadata={"lineage": {"scene_plan": f"scene_plan.v{scene_env.artifact_version:03d}.json"}},
    )
    store.save(edit_env)
    store.approve("edit_decisions", production_id, edit_env.artifact_version)
    state.set_active_version("edit_decisions", edit_env.artifact_version)

    return edit_payload
