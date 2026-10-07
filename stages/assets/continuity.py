"""Visual continuity tracking and reference asset linkage across scenes."""
from __future__ import annotations

from typing import Any
from .asset_manifest import AssetItem


class AssetContinuityTracker:
    """Tracks environment identities, recurring subjects, palettes, and links reference assets."""

    def __init__(self) -> None:
        self.known_environments: dict[str, str] = {}  # env_key -> first_asset_id
        self.known_subjects: dict[str, str] = {}      # subj_key -> first_asset_id

    def _normalize_key(self, text: str) -> str:
        words = [w.lower().strip(".,;:()") for w in text.split() if len(w) > 3]
        return " ".join(sorted(set(words[:4])))

    def track_and_link_references(
        self,
        assets: list[AssetItem],
        art_direction: dict[str, Any],
    ) -> None:
        """Assign reference assets to items continuing environments or subjects from earlier scenes."""
        for idx, item in enumerate(assets):
            env_key = self._normalize_key(item.environment)
            subj_key = self._normalize_key(item.subject)

            # Check if this environment was already established in an earlier scene
            ref_candidates: list[str] = []

            # 1. Environment continuity
            if env_key and env_key in self.known_environments:
                earlier_asset_id = self.known_environments[env_key]
                if earlier_asset_id != item.asset_id:
                    ref_candidates.append(earlier_asset_id)
            elif env_key:
                self.known_environments[env_key] = item.asset_id

            # 2. Subject continuity
            if subj_key and subj_key in self.known_subjects:
                earlier_asset_id = self.known_subjects[subj_key]
                if earlier_asset_id != item.asset_id and earlier_asset_id not in ref_candidates:
                    ref_candidates.append(earlier_asset_id)
            elif subj_key:
                self.known_subjects[subj_key] = item.asset_id

            # 3. Explicit continuity check from scene notes
            if item.continuity_requirements and "scene" in item.continuity_requirements.lower():
                # e.g. "Direct continuation from scene 1"
                for prev_item in assets[:idx]:
                    if prev_item.scene_id in item.continuity_requirements.lower():
                        if prev_item.asset_id not in ref_candidates:
                            ref_candidates.append(prev_item.asset_id)

            item.reference_assets = ref_candidates

    def evaluate_continuity_score(
        self,
        assets: list[AssetItem],
        art_direction: dict[str, Any],
    ) -> float:
        """Calculate overall continuity fit score (0-100)."""
        if not assets:
            return 100.0

        score = 85.0  # Base healthy continuity
        palette = art_direction.get("palette_discipline", {})
        has_primary = bool(palette.get("primary"))
        has_accent = bool(palette.get("accent_1"))

        if has_primary and has_accent:
            score += 5.0

        # Reward reference linkages where continuity is maintained
        linked_count = sum(1 for a in assets if a.reference_assets)
        if linked_count > 0:
            score += min(10.0, linked_count * 3.0)

        # Cap between 0 and 100
        return round(min(100.0, max(0.0, score)), 1)
