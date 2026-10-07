"""Phase 6 Edit Director: creates the canonical editorial plan, never a render."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from production.stage_registry import StageHandlerResult, StageResultStatus
from schemas.models.artifact import ProducerInfo
from schemas.models.common import ProducerKind
from .edit_validator import EditValidator
from .rhythm_analyzer import RhythmAnalyzer
from .timeline import CTAPlan, EditDecisionsPayload, RuntimeLockSource, ValidationFlags
from .track_builder import TrackBuilder
from .transition_planner import TransitionPlanner

FACTORY_ROOT = Path(__file__).resolve().parents[2]
PLATFORM_PROFILE_PATH = Path("profiles/youtube_short.json")


def load_platform_lock() -> dict[str, Any]:
    """Load the canonical YouTube Short platform constraints once per edit.

    Composition details still belong to the later runtime; this snapshot only
    locks resolution, frame rate, safe zones, and duration constraints.
    """
    profile = json.loads((FACTORY_ROOT / PLATFORM_PROFILE_PATH).read_text(encoding="utf-8"))
    return {
        "profile": PLATFORM_PROFILE_PATH.as_posix(),
        "resolution": profile["resolution"],
        "fps": profile["fps"],
        "duration_constraints": profile["duration_constraints"],
        "safe_zones": profile["safe_zones"],
    }


class EditDirector:
    """Resolve locked upstream intent into an executable semantic edit decision artifact."""
    def __init__(self) -> None:
        self.transitions = TransitionPlanner()
        self.tracks = TrackBuilder()
        self.validator = EditValidator()
        self.rhythm = RhythmAnalyzer()

    def run(self, stage_name: str, state: Any, inputs: dict[str, Any], **kwargs: Any) -> StageHandlerResult:
        required = ("research_brief", "proposal_packet", "art_direction", "script", "scene_plan", "asset_manifest")
        missing = [key for key in required if not inputs.get(key) or not inputs[key].data]
        if missing:
            return StageHandlerResult(status=StageResultStatus.BLOCKED, message=f"Edit stage blocked: missing required upstream artifacts: {', '.join(missing)}.", errors=[f"MISSING_UPSTREAM_{key.upper()}" for key in missing])
        try:
            platform = load_platform_lock()
        except (OSError, ValueError, KeyError) as exc:
            return StageHandlerResult(status=StageResultStatus.BLOCKED, message=f"Edit stage blocked: canonical platform profile is unavailable: {exc}.", errors=["PLATFORM_PROFILE_MISSING"])
        proposal, art, script, scene_plan, manifest = (inputs["proposal_packet"].data, inputs["art_direction"].data, inputs["script"].data, inputs["scene_plan"].data, inputs["asset_manifest"].data)
        selected = next((c for c in proposal.get("concepts", []) if c.get("concept_id") == proposal.get("selected_concept_id")), None)
        if not selected:
            return StageHandlerResult(status=StageResultStatus.BLOCKED, message="Edit stage blocked: proposal has no selected concept and therefore no render lock.", errors=["MISSING_RENDER_LOCK"])
        override_rejection = self._reject_runtime_override(kwargs.get("runtime_override"), selected)
        if override_rejection is not None:
            return override_rejection
        proposal_envelope = inputs["proposal_packet"]
        lock_source = RuntimeLockSource(
            artifact_type="proposal_packet",
            version=proposal_envelope.artifact_version,
            content_hash=proposal_envelope.content_hash,
            locked_at=(proposal.get("decision_log") or {}).get("timestamp") or proposal_envelope.updated_at.isoformat(),
            locked_concept_id=proposal.get("selected_concept_id"),
        )
        scenes = scene_plan.get("scenes", [])
        assets = manifest.get("assets", [])
        if not scenes or not assets:
            return StageHandlerResult(status=StageResultStatus.BLOCKED, message="Edit stage blocked: scene plan or asset manifest is empty.", errors=["EMPTY_EDIT_INPUT"])
        total = round(float(script.get("estimated_duration_seconds") or scene_plan.get("total_duration_seconds") or scenes[-1]["end_seconds"]), 3)
        script_sections = {s.get("section_id"): s for s in script.get("sections", [])}
        transition_map = self.transitions.plan_sequence(scenes)
        video_tracks, audio_tracks, captions = self.tracks.build(scenes, assets, script_sections, transition_map, safe_zones=platform["safe_zones"])
        timeline = [event for events in video_tracks.values() for event in events]
        cta_scene = next((s for s in reversed(scenes) if s.get("narrative_role") == "cta"), scenes[-1])
        cta_id = cta_scene.get("scene_id") or cta_scene.get("id")
        cta_caption = next(c for c in captions if c.scene_id == cta_id)
        cta = CTAPlan(scene_id=cta_id, start=float(cta_scene["start_seconds"]), end=total, channel_branding="AI Simplified Lab", caption_event_id=cta_caption.event_id, audio_requirement={"required": True, "spoken_text": script.get("cta", {}).get("spoken_text", "Subscribe to AI Simplified Lab for more AI breakdowns like this.")})
        provisional = {"production_id": state.project_id, "total_duration": total, "platform_profile": PLATFORM_PROFILE_PATH.as_posix(), "platform": platform, "renderer_family": selected["renderer_family"], "render_runtime": selected["render_runtime"], "composition_mode": selected["composition_mode"], "timeline": [e.model_dump() for e in timeline], "video_tracks": {key: [e.model_dump() for e in value] for key, value in video_tracks.items()}, "audio_tracks": {key: [e.model_dump() for e in value] for key, value in audio_tracks.items()}, "caption_track": [c.model_dump() for c in captions], "cta": cta.model_dump()}
        validation = self.validator.validate(provisional, scene_plan, manifest, proposal, production_id=state.project_id, script=script)
        rhythm = self.rhythm.analyze(provisional["timeline"], total)
        rhythm_findings = self.rhythm.warnings(rhythm)
        utilization = self._asset_utilization(assets, provisional["timeline"])
        proof = self.timeline_proof(provisional, manifest)
        review = self._review(validation, rhythm, rhythm_findings, utilization, selected, cta, proof)
        payload = EditDecisionsPayload(production_id=state.project_id, total_duration=total, platform_profile=PLATFORM_PROFILE_PATH.as_posix(), platform=platform, runtime_lock_source=lock_source, renderer_family=selected["renderer_family"], render_runtime=selected["render_runtime"], composition_mode=selected["composition_mode"], timeline=timeline, video_tracks=video_tracks, audio_tracks=audio_tracks, caption_track=captions, validation=ValidationFlags(**validation["flags"]), cta=cta, asset_utilization_report=utilization, rhythm=rhythm, edit_review_report=review, metadata={"art_direction_signature_device": art.get("signature_device"), "transition_plan": transition_map, "phase": 6, "platform_lock": platform, "timeline_proof": proof}).to_payload()
        all_findings = validation["findings"] + rhythm_findings
        if validation["status"] == "rejected":
            return StageHandlerResult(status=StageResultStatus.FAILED, message="Edit decisions failed validation: " + "; ".join(f["code"] for f in validation["findings"]), errors=[f["code"] for f in validation["findings"] if f["severity"] == "critical"])
        return StageHandlerResult(status=StageResultStatus.READY, data=payload, producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="phase6_edit_director", model="deterministic"), warnings=[f"[{f['code']}] {f['evidence']}" for f in all_findings if f["severity"] == "warning"], message=f"Edit decisions generated: {len(scenes)} scenes, {rhythm['shot_count']} shots, {rhythm['average_shot_duration']}s average shot duration.")

    @staticmethod
    def _reject_runtime_override(override: Any, selected: dict[str, Any]) -> StageHandlerResult | None:
        """Reject any edit-stage attempt to replace the approved proposal runtime lock.

        A genuine runtime change must arrive as a new approved proposal version;
        in that workflow the override already matches the newly locked proposal.
        """
        if override is None:
            return None
        locked = {
            "renderer_family": selected.get("renderer_family"),
            "render_runtime": selected.get("render_runtime"),
            "composition_mode": selected.get("composition_mode"),
        }
        if not isinstance(override, dict) or set(override) != set(locked) or any(override[key] != locked[key] for key in locked):
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Edit stage blocked: runtime overrides are rejected. Change the approved proposal decision, then regenerate the edit.",
                errors=["RUNTIME_OVERRIDE_REJECTED"],
            )
        return None

    @staticmethod
    def _asset_utilization(assets: list[dict], events: list[dict]) -> dict:
        used = [event["asset_id"] for event in events if event.get("asset_id")]
        counts = Counter(used)
        primary = [e for e in events if e.get("role") == "primary_visual"]
        return {"used_assets": sorted(counts), "unused_assets": sorted(a["asset_id"] for a in assets if a.get("asset_id") not in counts), "asset_reuse_count": dict(counts), "primary_asset_count": len({e.get("asset_id") for e in primary if e.get("asset_id")}), "fallback_asset_count": sum(1 for a in assets if a.get("fallback_used"))}

    @staticmethod
    def timeline_proof(edit: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
        """Prove, without rendering, that the timeline uses the planned assets coherently."""
        assets = {asset.get("asset_id"): asset for asset in manifest.get("assets", [])}
        primary = [e for e in edit.get("timeline", []) if e.get("role") == "primary_visual"]
        checks = []
        shared_terms = 0
        for event in primary:
            asset = assets.get(event.get("asset_id")) if event.get("asset_id") else None
            if asset is None:
                resolution = "unresolved"
            elif asset.get("file_path"):
                resolution = "manifest file"
            elif asset.get("source") == "native" or asset.get("diagram_spec") or asset.get("type") == "native_composition":
                resolution = "native generation reference"
            else:
                resolution = "unresolved"
            event_terms = set(str(event.get("purpose", "")).lower().split())
            asset_terms = set(str((asset or {}).get("purpose", "")).lower().split())
            shared = sorted(event_terms & asset_terms - {"the", "and", "of", "to", "a"})
            shared_terms += len(shared)
            checks.append({
                "event_id": event.get("event_id"),
                "scene_id": event.get("scene_id"),
                "shot_id": event.get("shot_id"),
                "asset_id": event.get("asset_id"),
                "asset_scene_id": (asset or {}).get("scene_id"),
                "event_purpose": event.get("purpose"),
                "asset_purpose": (asset or {}).get("purpose"),
                "shared_purpose_terms": shared,
                "resolution": resolution,
                "reference": (asset or {}).get("file_path") or (asset or {}).get("diagram_spec") or (asset or {}).get("source"),
            })
        bound = [e for e in primary if e.get("caption_ref") and e.get("audio_ref")]
        return {
            "primary_shots_checked": len(primary),
            "resolved_primary_shots": sum(1 for c in checks if c["resolution"] != "unresolved"),
            "manifest_scene_matches": sum(1 for c in checks if c["asset_scene_id"] == c["scene_id"]),
            "average_shared_purpose_terms": round(shared_terms / len(checks), 3) if checks else 0,
            "caption_audio_bound_shots": len(bound),
            "shot_checks": checks,
        }

    @staticmethod
    def _review(validation, rhythm, rhythm_findings, utilization, selected, cta, proof):
        critical = {f["code"] for f in validation["findings"] if f["severity"] == "critical"}
        warnings = [f["code"] for f in validation["findings"] if f["severity"] == "warning"] + [f["code"] for f in rhythm_findings]
        status = validation["status"]
        severity = "critical" if status == "rejected" else ("warning" if warnings else "pass")

        def section(evidence: str, bad: bool) -> dict[str, str]:
            section_status = "warning" if (bad and status != "rejected") else status
            return {
                "status": section_status,
                "evidence": evidence,
                "severity": "critical" if status == "rejected" and bad else ("warning" if bad else "pass"),
                "correction": "Resolve validation findings." if bad else "None",
            }

        timeline_bad = bool(critical & {"TIMELINE_GAP", "TIMELINE_OVERLAP", "TIMELINE_ENDS_EARLY", "TIMELINE_EXCEEDS_DURATION", "INVALID_DURATION", "DURATION_MISMATCH", "DUPLICATE_EVENT_ID", "PLATFORM_DURATION_INVALID"})
        asset_bad = bool(critical & {"INVALID_ASSET_REFERENCE", "MISSING_ASSET_FILE", "PRIMARY_ASSET_UNRESOLVED", "ASSET_SCENE_MISMATCH"})
        narrative_bad = bool(critical & {"SCENE_WITHOUT_VISUAL", "SCENE_WITHOUT_PRIMARY", "INVALID_SCENE_REFERENCE"})
        transition_bad = "TRANSITION_REPETITION" in warnings or "TRANSITION_DOMINANCE" in warnings
        cta_bad = bool([code for code in critical if code.startswith("CTA_")])
        render_bad = "RENDERER_MISMATCH" in critical
        findings = validation["findings"] + rhythm_findings
        return {
            "timeline_quality": section(f"{rhythm['shot_count']} timed primary shots; average cut interval {rhythm['average_cut_interval']}s", timeline_bad),
            "asset_alignment": section(f"{proof['resolved_primary_shots']} of {proof['primary_shots_checked']} primary shots resolve to manifest assets in their planned scenes", asset_bad),
            "narrative_alignment": section("Every scene is represented by timeline events." if not narrative_bad else "Scene coverage is incomplete.", narrative_bad),
            "rhythm_quality": section(f"Average shot duration {rhythm['average_shot_duration']} seconds; {rhythm['transition_diversity']} transition types.", transition_bad or timeline_bad),
            "transition_quality": section(f"{rhythm['transition_diversity']} semantic transition types; no renderer-specific effects.", transition_bad),
            "cta_quality": section(f"CTA from {cta.start:.2f}s to {cta.end:.2f}s is final.", cta_bad),
            "render_lock": section(f"Locked to {selected['renderer_family']}/{selected['render_runtime']}/{selected['composition_mode']}.", render_bad),
            "overall_severity": severity,
            "findings": findings,
        }

    @staticmethod
    def write_human_reports(output_dir: Path, payload: dict[str, Any]) -> None:
        """Smoke/CLI helper: report persistence outside artifact data is deliberately explicit."""
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "edit_review_report.json").write_text(json.dumps(payload["edit_review_report"], indent=2), encoding="utf-8")
        (output_dir / "asset_utilization_report.json").write_text(json.dumps(payload["asset_utilization_report"], indent=2), encoding="utf-8")
        proof = payload["metadata"].get("timeline_proof", {})
        generation = {
            "phase": 6,
            "total_duration": payload["total_duration"],
            "platform": payload["metadata"].get("platform_lock", {}),
            "runtime_lock_source": payload.get("runtime_lock_source", {}),
            "scene_count": len({e["scene_id"] for e in payload["timeline"]}),
            "shot_count": payload["rhythm"]["shot_count"],
            "average_shot_duration": payload["rhythm"]["average_shot_duration"],
            "average_cut_interval": payload["rhythm"]["average_cut_interval"],
            "transition_diversity": payload["rhythm"]["transition_diversity"],
            "transition_counts": payload["rhythm"]["transition_counts"],
            "layer_count": len(payload["video_tracks"]),
            "layer_names": sorted(payload["video_tracks"]),
            "layer_roles": sorted({e["role"] for e in payload["timeline"]}),
            "asset_utilization": payload["asset_utilization_report"],
            "timeline_proof": proof,
            "cta_timing": {"start": payload["cta"]["start"], "end": payload["cta"]["end"]},
            "timeline_coverage": payload["validation"]["duration_covered"],
            "narration_coverage": payload["validation"]["audio_valid"],
            "visual_change_count": payload["rhythm"]["shot_count"],
        }
        (output_dir / "edit_generation_report.json").write_text(json.dumps(generation, indent=2), encoding="utf-8")
        scene_events: dict[str, list[dict[str, Any]]] = {}
        for event in payload["timeline"]:
            scene_events.setdefault(event["scene_id"], []).append(event)
        captions = {c["scene_id"]: c for c in payload["caption_track"]}
        narration = {e["event_id"].replace("narration_", ""): e for e in payload["audio_tracks"].get("narration", [])}
        lines = [
            "# Edit Summary",
            "",
            f"Total duration: {payload['total_duration']:.2f}s across {len(scene_events)} scenes.",
            f"Platform: {payload['platform_profile']} at {payload['metadata']['platform_lock']['resolution']['width']}x{payload['metadata']['platform_lock']['resolution']['height']} and {payload['metadata']['platform_lock']['fps']}fps.",
            "",
        ]
        for scene_id in sorted(scene_events, key=lambda value: min(e["start"] for e in scene_events[value])):
            primary = sorted((e for e in scene_events[scene_id] if e["role"] == "primary_visual"), key=lambda e: e["start"])
            first, last = primary[0], primary[-1]
            caption = captions.get(scene_id, {})
            spoken = narration.get(scene_id, {}).get("audio_requirement", {}).get("spoken_text", "")
            lines.append(f"## {first['start']:.1f}–{last['end']:.1f}s · {scene_id}")
            lines.append(f"Primary asset {first['asset_id']}: {first['purpose']} becomes {last['purpose']}.")
            for event in primary:
                lines.append(f"- {event['start']:.1f}–{event['end']:.1f}s: {event['purpose']} ({event.get('camera_intent')}, {event.get('motion_intent')}, {event.get('transition_in')}).")
            if caption:
                lines.append(f"Caption {caption.get('caption_text_reference')} from {caption.get('start'):.1f}–{caption.get('end'):.1f}s; emphasis: {', '.join(caption.get('emphasis_words', [])) or 'none'}.")
            if spoken:
                lines.append(f"Narration: {spoken[:140]}{'...' if len(spoken) > 140 else ''}")
            lines.append("")
        (output_dir / "edit_summary.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
