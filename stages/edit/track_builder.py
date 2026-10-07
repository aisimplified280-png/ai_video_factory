"""Converts planned scene shots into timed, multi-layer semantic edit events."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .timeline import AudioEvent, CaptionEvent, TimelineEvent

_STOPWORDS = frozenset({
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of",
    "on", "or", "the", "to", "with",
})
_CAMERA_CROP = {
    "reveal_space": "full_frame",
    "approach_subject": "medium",
    "expand_scale": "detail",
    "follow_subject": "medium",
    "shift_focus": "close",
    "observe_static": "center_focus",
}
_SFX_ACCENT_TRANSITIONS = frozenset({"light_flash", "match_cut", "zoom_transition", "motion_blur"})


def _tokens(value: Any) -> set[str]:
    words = str(value or "").lower().replace("-", " ").replace("/", " ").split()
    return {word.strip(".,;:!?()[]\"'") for word in words} - _STOPWORDS


class TrackBuilder:
    def build(
        self,
        scenes: list[dict[str, Any]],
        assets: list[dict[str, Any]],
        script_sections: dict[str, dict[str, Any]],
        transitions: dict[str, str],
        safe_zones: dict[str, str] | None = None,
    ) -> tuple[dict[str, list[TimelineEvent]], dict[str, list[AudioEvent]], list[CaptionEvent]]:
        zones = {"caption": "lower_center_safe", "brand": "bottom_safe"}
        if safe_zones:
            zones.update(safe_zones)
        assets_by_scene: dict[str, list[dict]] = defaultdict(list)
        for asset in assets:
            assets_by_scene[asset["scene_id"]].append(asset)
        tracks: dict[str, list[TimelineEvent]] = defaultdict(list)
        narration: list[AudioEvent] = []
        captions: list[CaptionEvent] = []
        sfx: list[AudioEvent] = []
        sfx_by_scene: dict[str, str] = {}
        self._reserve_sfx_markers(scenes, transitions, sfx, sfx_by_scene)

        for scene_index, scene in enumerate(scenes):
            scene_id = scene.get("scene_id") or scene.get("id")
            candidates = assets_by_scene.get(scene_id, [])
            primary = self._select_primary(scene, candidates)
            shots = self._normalized_shots(scene)
            caption_id = f"caption_{scene_id}"
            narration_id = f"narration_{scene_id}"
            accent_id = sfx_by_scene.get(scene_id)
            self._build_primary_shots(scene, scene_id, shots, primary, transitions.get(scene_id), tracks, caption_id, narration_id)
            self._build_support_assets(scene, scene_id, shots, candidates, primary, tracks, caption_id, accent_id)
            section = script_sections.get(scene.get("script_section_id"), {})
            spoken = section.get("spoken_text", "")
            sec_start, sec_end = self._section_bounds(section, scene)
            captions.append(CaptionEvent(
                event_id=caption_id,
                scene_id=scene_id,
                start=sec_start,
                end=sec_end,
                caption_text_reference=section.get("section_id", scene.get("script_section_id", scene_id)),
                emphasis_words=section.get("emphasis_words", [])[:4],
                safe_zone=zones["caption"],
            ))
            narration.append(AudioEvent(
                event_id=narration_id,
                track_id="narration",
                start=sec_start,
                end=sec_end,
                audio_requirement={"required": True, "spoken_text": spoken},
                purpose="script narration",
            ))
            self._build_overlay(scene, scene_id, shots, tracks, caption_id, accent_id)

        total = max((e.end for e in narration), default=0)
        music = [AudioEvent(
            event_id="music_bed",
            track_id="music",
            start=0,
            end=total,
            audio_requirement={"required": True, "mood": "match art direction"},
            purpose="continuous music bed",
        )]
        return dict(tracks), {"narration": narration, "music": music, "sfx": sfx}, captions

    @staticmethod
    def _normalized_shots(scene: dict[str, Any]) -> list[dict[str, Any]]:
        scene_id = scene.get("scene_id") or scene.get("id")
        scene_start = float(scene["start_seconds"])
        scene_end = float(scene["end_seconds"])
        raw = scene.get("shots") or [{
            "shot_id": f"{scene_id}_shot_01",
            "start_seconds": scene_start,
            "end_seconds": scene_end,
            "purpose": scene.get("visual_purpose", "explain"),
            "camera_intent": scene.get("camera_intent", "observe_static"),
            "motion_intent": scene.get("motion_intent", "reveal"),
        }]
        shots = []
        for index, shot in enumerate(raw, start=1):
            start, end = TrackBuilder._shot_bounds(shot, scene_start, scene_end)
            shots.append({
                "shot_id": shot.get("shot_id", f"{scene_id}_shot_{index:02d}"),
                "start": start,
                "end": end,
                "purpose": shot.get("purpose") or scene.get("visual_purpose", "primary visual"),
                "camera_intent": shot.get("camera_intent") or scene.get("camera_intent", "observe_static"),
                "motion_intent": shot.get("motion_intent") or scene.get("motion_intent", "reveal"),
            })
        return shots

    @staticmethod
    def _shot_bounds(shot: dict[str, Any], scene_start: float, scene_end: float) -> tuple[float, float]:
        # Scene-plan beats are scene-relative offsets; some plans use absolute *_seconds.
        if "start_seconds" in shot:
            start = float(shot["start_seconds"])
        else:
            start = scene_start + float(shot.get("start", 0))
        if "end_seconds" in shot:
            end = float(shot["end_seconds"])
        else:
            end = scene_start + float(shot.get("end", scene_end - scene_start))
        return start, end

    @staticmethod
    def _select_primary(scene: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not candidates:
            return None
        scene_text = _tokens(scene.get("visual_purpose")) | _tokens(scene.get("subject"))
        scored = []
        for position, asset in enumerate(candidates):
            score = 0
            if asset.get("visual_role") == "primary":
                score += 100
            purpose = _tokens(asset.get("purpose")) | _tokens(asset.get("subject"))
            score += 5 * len(purpose & scene_text)
            scored.append((score, -position, asset))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return scored[0][2]

    def _build_primary_shots(self, scene, scene_id, shots, primary, transition, tracks, caption_id, narration_id) -> None:
        for shot_index, shot in enumerate(shots):
            start, end = shot["start"], shot["end"]
            tracks["video_primary"].append(TimelineEvent(
                event_id=f"edit_{scene_id}_{shot_index + 1:02d}",
                scene_id=scene_id,
                shot_id=shot["shot_id"],
                track_id="video_primary",
                asset_id=primary["asset_id"] if primary else None,
                start=start,
                end=end,
                duration=round(end - start, 3),
                z_index=10,
                role="primary_visual",
                purpose=shot["purpose"],
                crop=_CAMERA_CROP.get(shot["camera_intent"], "medium"),
                camera_intent=shot["camera_intent"],
                motion_intent=shot["motion_intent"],
                transition_in=transition if shot_index == 0 else "hard_cut",
                transition_out=None,
                caption_ref=caption_id,
                audio_ref=narration_id,
            ))

    def _build_support_assets(self, scene, scene_id, shots, candidates, primary, tracks, caption_id, accent_id) -> None:
        scene_start = float(scene["start_seconds"])
        scene_end = float(scene["end_seconds"])
        reveal = shots[1]["start"] if len(shots) > 1 else scene_start + 0.6
        support_position = 0
        for asset in candidates:
            if primary and asset["asset_id"] == primary["asset_id"]:
                continue
            role = "diagram" if asset.get("type") in {"diagram", "chart", "code", "svg", "native_composition"} else "secondary_visual"
            start = min(reveal + support_position * 0.35, scene_end - 0.5)
            support_position += 1
            if scene_end - start < 0.25:
                continue
            tracks["graphics" if role == "diagram" else "video_secondary"].append(TimelineEvent(
                event_id=f"support_{asset['asset_id']}",
                scene_id=scene_id,
                track_id="graphics" if role == "diagram" else "video_secondary",
                asset_id=asset["asset_id"],
                start=start,
                end=scene_end,
                duration=round(scene_end - start, 3),
                z_index=20 if role == "diagram" else 15,
                role=role,
                purpose=asset.get("purpose", "support visual"),
                crop="center_focus",
                camera_intent="shift_focus",
                motion_intent="emerge",
                caption_ref=caption_id,
                audio_ref=accent_id,
            ))

    def _build_overlay(self, scene, scene_id, shots, tracks, caption_id, accent_id) -> None:
        scene_end = float(scene["end_seconds"])
        payoff = shots[-1]["start"]
        is_cta = scene.get("narrative_role") == "cta"
        tracks["overlays"].append(TimelineEvent(
            event_id=f"overlay_{scene_id}",
            scene_id=scene_id,
            track_id="overlays",
            asset_id=None,
            start=payoff,
            end=scene_end,
            duration=round(scene_end - payoff, 3),
            z_index=30,
            role="brand" if is_cta else "metric",
            purpose="channel branding" if is_cta else f"emphasize {shots[-1]['purpose']}".rstrip(),
            crop="center_focus",
            motion_intent="pulse" if is_cta else "reveal",
            caption_ref=caption_id,
            audio_ref=accent_id,
        ))

    def _reserve_sfx_markers(self, scenes, transitions, sfx, sfx_by_scene) -> None:
        for index, scene in enumerate(scenes):
            scene_id = scene.get("scene_id") or scene.get("id")
            start = float(scene["start_seconds"])
            transition = transitions.get(scene_id)
            if index == 0 and scene.get("narrative_role") == "hook":
                marker = AudioEvent(
                    event_id="sfx_hook_impact",
                    track_id="sfx",
                    start=start,
                    end=round(start + 0.25, 3),
                    audio_requirement={"required": True, "effect": "hook impact", "trigger": f"{scene_id} cold open"},
                    purpose="punctuate the hook cut",
                )
            elif start > 0 and transition in _SFX_ACCENT_TRANSITIONS:
                marker = AudioEvent(
                    event_id=f"sfx_{scene_id}_accent",
                    track_id="sfx",
                    start=start,
                    end=round(start + 0.25, 3),
                    audio_requirement={"required": True, "effect": "scene accent", "trigger": f"{transition} into {scene_id}"},
                    purpose=f"accentuate the {transition} into {scene_id}",
                )
            else:
                continue
            sfx.append(marker)
            sfx_by_scene[scene_id] = marker.event_id

        cta_scenes = [s for s in scenes if s.get("narrative_role") == "cta"]
        if cta_scenes:
            cta = cta_scenes[-1]
            cta_id = cta.get("scene_id") or cta.get("id")
            end = float(cta["end_seconds"])
            start = round(max(float(cta["start_seconds"]), end - 0.5), 3)
            marker = AudioEvent(
                event_id="sfx_cta_resolve",
                track_id="sfx",
                start=start,
                end=end,
                audio_requirement={"required": True, "effect": "subscription resolve", "trigger": f"{cta_id} payoff"},
                purpose="resolve the CTA payoff",
            )
            sfx.append(marker)
            sfx_by_scene[cta_id] = marker.event_id

    @staticmethod
    def _section_bounds(section: dict[str, Any], scene: dict[str, Any]) -> tuple[float, float]:
        return (
            float(section.get("start_seconds", scene["start_seconds"])),
            float(section.get("end_seconds", scene["end_seconds"])),
        )
