"""Hard validation for Phase 6's renderer-neutral canonical edit contract."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .timeline import LayerRole, TransitionType, resolve_asset_path

_TEMPLATE_TERMS = ("herocard", "statcard", "infocard", "featurecard")
_REQUIRED_PARENTS = ("research_brief", "proposal_packet", "art_direction", "script", "scene_plan", "asset_manifest")


class EditValidator:
    def validate(
        self,
        edit: dict[str, Any],
        scene_plan: dict[str, Any],
        asset_manifest: dict[str, Any],
        proposal: dict[str, Any],
        projects_root: Path | str | None = None,
        production_id: str | None = None,
        script: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        findings: list[dict[str, str]] = []
        scenes = scene_plan.get("scenes", [])
        scene_ids = {s.get("scene_id") or s.get("id") for s in scenes}
        assets = {a.get("asset_id"): a for a in asset_manifest.get("assets", [])}
        events = edit.get("timeline", [])
        total = float(edit.get("total_duration", 0))
        pid = production_id or edit.get("production_id")
        ids = [e.get("event_id") for e in events]
        if len(ids) != len(set(ids)):
            findings.append(self._critical("DUPLICATE_EVENT_ID", "Timeline contains duplicate event IDs.", "Give each event a unique stable ID."))
        for event in events:
            self._event_checks(event, scene_ids, assets, total, pid, projects_root, findings)
        self._primary_coverage(events, total, findings)
        self._scene_coverage(scenes, events, findings)
        self._cta_checks(edit, scenes, findings, script)
        self._renderer_lock(edit, proposal, findings)
        self._caption_checks(edit.get("caption_track", []), edit.get("audio_tracks", {}).get("narration", []), findings)
        self._audio_checks(edit.get("audio_tracks", {}), total, findings)
        self._platform_checks(edit, findings)
        self._editorial_warnings(edit, scenes, events, list(assets.values()), findings)
        status = "rejected" if any(f["severity"] == "critical" for f in findings) else ("warning" if findings else "pass")
        flags = {
            "no_gaps": not any(f["code"] == "TIMELINE_GAP" for f in findings),
            "no_overlaps": not any(f["code"] == "TIMELINE_OVERLAP" for f in findings),
            "all_assets_resolved": not any(f["code"] in {"INVALID_ASSET_REFERENCE", "MISSING_ASSET_FILE", "PRIMARY_ASSET_UNRESOLVED", "ASSET_SCENE_MISMATCH"} for f in findings),
            "duration_covered": not any(f["code"] in {"TIMELINE_GAP", "TIMELINE_ENDS_EARLY", "TIMELINE_EXCEEDS_DURATION", "PLATFORM_DURATION_INVALID"} for f in findings),
            "audio_valid": not any(f["code"].startswith("AUDIO_") and f["severity"] == "critical" for f in findings),
            "captions_valid": not any(f["code"].startswith("CAPTION_") and f["severity"] == "critical" for f in findings),
            "cta_present": not any(f["code"].startswith("CTA_") for f in findings),
            "renderer_locked": not any(f["code"] == "RENDERER_MISMATCH" for f in findings),
        }
        return {"status": status, "findings": findings, "flags": flags}

    @staticmethod
    def validate_artifact_lineage(edit_envelope: Any, inputs: dict[str, Any]) -> dict[str, Any]:
        """Verify persisted edit lineage against the exact locked parent versions/hashes."""
        findings: list[dict[str, str]] = []
        parents = {p.artifact_type: p for p in getattr(edit_envelope, "parent_artifacts", []) or []}
        for artifact_type in _REQUIRED_PARENTS:
            parent = parents.get(artifact_type)
            source = inputs.get(artifact_type)
            if parent is None or source is None:
                findings.append(EditValidator._critical("LINEAGE_PARENT_MISSING", f"Edit lineage is missing locked parent {artifact_type}.", "Persist all six locked upstream parents with the edit artifact."))
                continue
            if parent.version != source.artifact_version:
                findings.append(EditValidator._critical("LINEAGE_VERSION_MISMATCH", f"Locked {artifact_type} v{parent.version} does not match active v{source.artifact_version}.", "Regenerate the edit after the approved upstream revision."))
            if parent.content_hash != source.content_hash:
                findings.append(EditValidator._critical("LINEAGE_HASH_MISMATCH", f"Locked {artifact_type} hash does not match the active artifact.", "Regenerate the edit after the approved upstream revision."))
            if source.status.value not in {"ready", "approved"}:
                findings.append(EditValidator._critical("LINEAGE_STALE_PARENT", f"Locked parent {artifact_type} has status {source.status.value}.", "Use only ready or approved upstream artifacts."))
        status = "rejected" if findings else "pass"
        return {"status": status, "findings": findings}

    def _event_checks(self, event, scene_ids, assets, total, production_id, projects_root, findings):
        start, end, duration = float(event.get("start", -1)), float(event.get("end", -1)), float(event.get("duration", -1))
        if end <= start or duration <= 0:
            findings.append(self._critical("INVALID_DURATION", f"{event.get('event_id')} has zero or negative duration.", "Use a positive end-start duration."))
        elif abs((end - start) - duration) > 0.02:
            findings.append(self._critical("DURATION_MISMATCH", f"{event.get('event_id')} duration does not match bounds.", "Set duration to end minus start."))
        if start < 0 or end > total + 0.02:
            findings.append(self._critical("TIMELINE_EXCEEDS_DURATION", f"{event.get('event_id')} sits outside total duration.", "Keep every event within the edit timeline."))
        if event.get("scene_id") not in scene_ids:
            findings.append(self._critical("INVALID_SCENE_REFERENCE", f"{event.get('event_id')} references an unknown scene.", "Reference a scene_plan scene ID."))
        if event.get("role") not in LayerRole.__args__:
            findings.append(self._critical("INVALID_LAYER", f"{event.get('event_id')} has invalid layer {event.get('role')!r}.", "Use a canonical semantic layer."))
        for key in ("transition_in", "transition_out"):
            if event.get(key) and event[key] not in TransitionType.__args__:
                findings.append(self._critical("INVALID_TRANSITION", f"{event.get('event_id')} has invalid {key}.", "Use a supported semantic transition."))
        asset_id = event.get("asset_id")
        if asset_id:
            asset = assets.get(asset_id)
            if asset is None:
                findings.append(self._critical("INVALID_ASSET_REFERENCE", f"{event.get('event_id')} references missing asset {asset_id}.", "Use an asset from asset_manifest."))
            elif asset.get("scene_id") != event.get("scene_id"):
                findings.append(self._critical("ASSET_SCENE_MISMATCH", f"{event.get('event_id')} uses {asset_id} outside its planned {asset.get('scene_id')}.", "Keep each asset in its planned scene or revise the manifest."))
            elif not self._asset_resolved(asset, production_id, projects_root):
                findings.append(self._critical("MISSING_ASSET_FILE", f"Asset {asset_id} has no real file or declared native generation reference.", "Generate the file or declare native composition/diagram metadata."))

    @staticmethod
    def _asset_resolved(asset: dict, production_id: str | None, projects_root: Path | str | None) -> bool:
        if asset.get("type") == "native_composition" or asset.get("source") == "native" or bool(asset.get("diagram_spec")):
            return True
        file_path = asset.get("file_path")
        if not file_path:
            return False
        if urlparse(str(file_path)).scheme in {"http", "https"}:
            return True
        if not production_id:
            return False
        resolved = resolve_asset_path(production_id, asset, projects_root)
        return resolved is not None and resolved.exists()

    def _primary_coverage(self, events, total, findings):
        primary = sorted((e for e in events if e.get("role") == "primary_visual"), key=lambda e: float(e["start"]))
        cursor = 0.0
        for event in primary:
            start, end = float(event["start"]), float(event["end"])
            if start > cursor + 0.02:
                findings.append(self._critical("TIMELINE_GAP", f"Primary visual gap from {cursor:.2f}s to {start:.2f}s.", "Cover every timeline interval with a primary visual."))
            if start < cursor - 0.02:
                findings.append(self._critical("TIMELINE_OVERLAP", f"Primary visuals overlap at {start:.2f}s.", "Keep primary visual events sequential."))
            cursor = max(cursor, end)
        if cursor < total - 0.02:
            findings.append(self._critical("TIMELINE_ENDS_EARLY", f"Primary visuals end at {cursor:.2f}s, before {total:.2f}s.", "Extend primary coverage to total duration."))

    def _scene_coverage(self, scenes, events, findings):
        by_scene = defaultdict(list)
        for event in events:
            by_scene[event.get("scene_id")].append(event)
        shots_by_scene = {}
        for scene in scenes:
            sid = scene.get("scene_id") or scene.get("id")
            expected = set()
            for index, shot in enumerate(scene.get("shots") or [], start=1):
                expected.add(shot.get("shot_id") or f"{sid}_shot_{index:02d}")
            shots_by_scene[sid] = expected
        for scene in scenes:
            sid = scene.get("scene_id") or scene.get("id")
            current = by_scene[sid]
            if not current:
                findings.append(self._critical("SCENE_WITHOUT_VISUAL", f"Scene {sid} has no visual event.", "Create at least one event."))
                continue
            if scene.get("narrative_role") != "cta" and not any(e.get("role") == "primary_visual" for e in current):
                findings.append(self._critical("SCENE_WITHOUT_PRIMARY", f"Scene {sid} lacks a primary visual.", "Assign a planned primary asset."))
            for event in current:
                if event.get("role") == "primary_visual" and not event.get("asset_id"):
                    findings.append(self._critical("PRIMARY_ASSET_UNRESOLVED", f"Scene {sid} has a primary shot without a resolved asset.", "Select a manifest asset for every primary shot; never leave it empty."))
                if event.get("shot_id") and event["shot_id"] not in shots_by_scene.get(sid, set()):
                    findings.append(self._critical("INVALID_SHOT_REFERENCE", f"{event.get('event_id')} references unknown shot {event['shot_id']} in {sid}.", "Use a shot_id from the scene plan."))
            if scene.get("text_density") == "high" and sum(1 for e in current if e.get("role") == "primary_visual") < 2:
                findings.append(self._warning("LOW_VISUAL_CHANGE_FOR_INTENSITY", f"High-density scene {sid} has only one primary shot.", "Add another information-driven visual change or lower the declared density."))

    def _cta_checks(self, edit, scenes, findings, script=None):
        cta = edit.get("cta") or {}
        cta_scenes = [s for s in scenes if s.get("narrative_role") == "cta"]
        if not cta_scenes:
            findings.append(self._critical("CTA_MISSING", "Scene plan has no CTA scene.", "Keep a CTA as final narrative scene."))
            return
        final = cta_scenes[-1]
        final_id = final.get("scene_id") or final.get("id")
        if cta.get("scene_id") != final_id or float(cta.get("end", -1)) < float(edit.get("total_duration", 0)) - .02:
            findings.append(self._critical("CTA_NOT_FINAL", "CTA is not the final timeline section.", "Place CTA after payoff and extend it to the end."))
        cta_start = float(cta.get("start", 0))
        trailing = [e.get("event_id") for e in edit.get("timeline", []) if e.get("scene_id") != final_id and float(e.get("start", 0)) >= cta_start - 0.02]
        if trailing:
            findings.append(self._critical("CTA_NOT_FINAL", f"Informational events {trailing} begin during or after the CTA.", "End all informational visuals before the CTA begins."))
        if not any(e.get("scene_id") == final_id and e.get("role") in {"primary_visual", "brand", "diagram", "metric"} for e in edit.get("timeline", [])):
            findings.append(self._critical("CTA_VISUAL_MISSING", "CTA has no visual event.", "Reserve a brand or primary visual for the CTA."))
        if not cta.get("audio_requirement"):
            findings.append(self._critical("CTA_AUDIO_MISSING", "CTA has no deferred audio requirement.", "Reserve CTA spoken text for later audio."))
        if script:
            script_cta = script.get("cta", {})
            caption = next((c for c in edit.get("caption_track", []) if c.get("event_id") == cta.get("caption_event_id")), None)
            if script_cta.get("section_id") and (caption is None or caption.get("caption_text_reference") != script_cta["section_id"]):
                findings.append(self._critical("CTA_SCRIPT_MISMATCH", "CTA caption does not reference the script CTA section.", "Align the CTA caption with the script CTA section."))
            if script_cta.get("spoken_text") and cta.get("audio_requirement", {}).get("spoken_text") != script_cta["spoken_text"]:
                findings.append(self._critical("CTA_AUDIO_MISMATCH", "CTA audio requirement does not match the script CTA text.", "Copy the script CTA text exactly into the deferred audio requirement."))

    def _renderer_lock(self, edit, proposal, findings):
        selected = next((c for c in proposal.get("concepts", []) if c.get("concept_id") == proposal.get("selected_concept_id")), None)
        if not selected:
            findings.append(self._critical("RENDERER_MISMATCH", "No selected proposal concept locks the runtime.", "Provide an approved selected concept."))
            return
        for key in ("renderer_family", "render_runtime", "composition_mode"):
            if edit.get(key) != selected.get(key):
                findings.append(self._critical("RENDERER_MISMATCH", f"Edit {key} differs from proposal lock.", "Copy the approved proposal render lock exactly."))

    def _caption_checks(self, captions, narration, findings):
        narr_ids = {e.get("event_id", "").replace("narration_", "") for e in narration}
        for caption in captions:
            if caption.get("scene_id") not in narr_ids:
                findings.append(self._critical("CAPTION_REFERENCE_INVALID", f"Caption {caption.get('event_id')} has no narration reference.", "Align captions to a narration scene."))
            if float(caption.get("end", 0)) <= float(caption.get("start", 0)):
                findings.append(self._critical("CAPTION_DURATION_INVALID", f"Caption {caption.get('event_id')} has invalid duration.", "Use a positive timing window."))

    def _audio_checks(self, tracks, total, findings):
        narration = tracks.get("narration", [])
        if not narration:
            findings.append(self._critical("AUDIO_NARRATION_MISSING", "Narration timing references are missing.", "Reserve narration for every script section."))
            return
        if min(float(e.get("start", 0)) for e in narration) > .02 or max(float(e.get("end", 0)) for e in narration) < total - .02:
            findings.append(self._critical("AUDIO_NARRATION_COVERAGE", "Narration does not cover script duration.", "Align narration references to the script timing."))
        if not tracks.get("sfx"):
            findings.append(self._warning("AUDIO_SFX_MISSING", "No SFX timing reference is reserved.", "Reserve at least the hook impact and CTA resolve."))

    def _platform_checks(self, edit, findings):
        platform = edit.get("platform") or {}
        constraints = platform.get("duration_constraints") if isinstance(platform, dict) else None
        if not platform:
            findings.append(self._warning("PLATFORM_PROFILE_MISSING", "Edit has no locked platform profile snapshot.", "Copy profiles/youtube_short.json into the edit metadata."))
            return
        total = float(edit.get("total_duration", 0))
        minimum = float((constraints or {}).get("minimum_seconds", 0))
        maximum = float((constraints or {}).get("maximum_seconds", total or 0))
        if total < minimum - 0.02 or (maximum and total > maximum + 0.02):
            findings.append(self._critical("PLATFORM_DURATION_INVALID", f"Timeline duration {total:.2f}s is outside {minimum:.0f}-{maximum:.0f}s.", "Conform the edit to the platform duration constraints."))

    def _editorial_warnings(self, edit, scenes, events, assets, findings):
        primary = [e for e in events if e.get("role") == "primary_visual"]
        self._repetition_warning(primary, "transition_in", "TRANSITION_DOMINANCE", "transition", findings)
        self._repetition_warning(primary, "crop", "FRAMING_REPETITION", "framing", findings)
        scene_counts: dict[str, set[str]] = defaultdict(set)
        for event in primary:
            if event.get("asset_id"):
                scene_counts[event["asset_id"]].add(event.get("scene_id"))
        if len(scenes) > 2 and scene_counts:
            dominant, covered = max(scene_counts.items(), key=lambda item: len(item[1]))
            if len(covered) / len(scenes) > 0.5:
                findings.append(self._warning("PRIMARY_ASSET_DOMINANCE", f"{dominant} dominates {len(covered)} of {len(scenes)} scenes.", "Distribute primary visuals across planned assets unless continuity requires one subject."))
        used = {e.get("asset_id") for e in events if e.get("asset_id")}
        unused_primary = sorted(a.get("asset_id") for a in assets if a.get("visual_role") == "primary" and a.get("asset_id") not in used)
        if unused_primary:
            findings.append(self._warning("UNUSED_PRIMARY_ASSET", f"Planned primary assets unused: {', '.join(unused_primary)}.", "Unused alternates are acceptable, but confirm coverage is clearer without them."))
        for index, scene in enumerate(scenes):
            sid = scene.get("scene_id") or scene.get("id")
            if index > 0 and not str(scene.get("continuity_from_previous") or "").strip():
                findings.append(self._warning("CONTINUITY_LINK_MISSING", f"Scene {sid} has no incoming continuity link.", "Preserve the scene plan's continuity chain."))
            if index < len(scenes) - 1 and not str(scene.get("continuity_to_next") or "").strip():
                findings.append(self._warning("CONTINUITY_LINK_MISSING", f"Scene {sid} has no outgoing continuity link.", "Preserve the scene plan's continuity chain."))
        vocabulary = " ".join([
            str(e.get("purpose")) for e in events
        ] + [str(a.get("purpose")) for a in assets]).lower().replace(" ", "").replace("-", "").replace("_", "")
        if any(term in vocabulary for term in _TEMPLATE_TERMS):
            findings.append(self._warning("TEMPLATE_VOCABULARY", "Edit vocabulary contains card-template language.", "Use semantic layers, not HeroCard/StatCard-style components."))

    @staticmethod
    def _repetition_warning(primary, field, code, label, findings) -> None:
        values = [e.get(field) for e in primary if e.get(field)]
        if len(primary) > 3 and values:
            top, count = Counter(values).most_common(1)[0]
            if count / len(primary) >= 0.75:
                findings.append(EditValidator._warning(code, f"The same {label} ({top}) covers {count} of {len(primary)} primary shots.", f"Vary {label} only where the narrative relationship supports it."))

    @staticmethod
    def _critical(code, evidence, correction):
        return {"severity": "critical", "code": code, "evidence": evidence, "correction": correction}

    @staticmethod
    def _warning(code, evidence, correction):
        return {"severity": "warning", "code": code, "evidence": evidence, "correction": correction}
