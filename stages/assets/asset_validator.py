"""Technical and semantic quality assurance for planned and generated assets."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from PIL import Image, ImageStat
from .asset_manifest import AssetItem, AssetReviewReport


GENERIC_ANTI_KEYWORDS = [
    "futuristic ai brain",
    "glowing blue lines",
    "cyberpunk neon",
    "abstract technology background",
    "generic modern ai",
]


class AssetValidator:
    """Validates technical asset integrity and semantic intent alignment."""

    def __init__(self, min_width: int = 720, min_height: int = 1280) -> None:
        self.min_width = min_width
        self.min_height = min_height

    def validate_technical(self, item: AssetItem) -> tuple[float, list[str]]:
        """Validate file existence, readability, dimensions, and non-blank content."""
        findings: list[str] = []
        score = 100.0

        if not item.file_path:
            return 0.0, ["File path missing or generation unattempted."]

        fpath = Path(item.file_path)
        if not fpath.exists():
            return 0.0, [f"Asset file does not exist on disk: {fpath}"]

        file_size = fpath.stat().st_size
        if file_size < 1024:
            return 0.0, [f"Corrupted or empty file (size: {file_size} bytes)."]

        # Check media readability
        if fpath.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            try:
                with Image.open(fpath) as img:
                    w, h = img.size
                    if w < self.min_width or h < self.min_height:
                        findings.append(f"Sub-optimal resolution {w}x{h} (minimum {self.min_width}x{self.min_height}).")
                        score -= 20.0

                    # Check for blank / solid black frames
                    stat = ImageStat.Stat(img)
                    mean_val = sum(stat.mean) / len(stat.mean)
                    std_dev = sum(stat.stddev) / len(stat.stddev)
                    if mean_val < 3.0 and std_dev < 3.0:
                        return 0.0, ["Asset is a solid black or unrendered frame."]
                    elif std_dev < 1.0:
                        return 0.0, ["Asset is a completely blank or uniform single-color canvas."]
            except Exception as exc:
                return 0.0, [f"Failed to decode image file: {exc}"]
        elif fpath.suffix.lower() in (".mp4", ".mov", ".webm"):
            # Check video header
            try:
                header = fpath.read_bytes()[:64]
                if b"ftyp" not in header and b"isom" not in header and b"moov" not in header and b"\x1aE\xdf\xa3" not in header:
                    findings.append("Unrecognized video container signature.")
                    score -= 30.0
            except Exception as exc:
                return 0.0, [f"Failed to inspect video header: {exc}"]

        return max(0.0, score), findings

    def validate_semantic(self, item: AssetItem, art_direction: dict[str, Any]) -> tuple[float, list[str]]:
        """Validate that the asset prompt/spec reflects planned subject, metaphor, and anti-patterns."""
        findings: list[str] = []
        score = 85.0

        # Check purpose length and specificity
        if len(item.purpose) < 10:
            findings.append("Asset purpose is too terse or generic.")
            score -= 20.0

        # Check subject inheritance in prompt
        full_text = f"{item.prompt or ''} {item.subject} {item.subject_action}".lower()
        subject_words = [w for w in item.subject.lower().split() if len(w) > 3]
        if subject_words:
            matched = sum(1 for w in subject_words if w in full_text)
            if matched == 0:
                findings.append(f"Asset does not reflect subject keywords {item.subject!r}.")
                score -= 30.0

        # Check anti-pattern tropes
        for trope in GENERIC_ANTI_KEYWORDS:
            if trope in full_text:
                findings.append(f"Asset prompt contains discouraged generic trope: {trope!r}.")
                score -= 25.0

        # Reward presence of explicit metaphor
        metaphor = str(art_direction.get("visual_metaphor") or "").lower()
        meta_words = [w for w in metaphor.split() if len(w) > 4]
        if any(w in full_text for w in meta_words):
            score += 10.0

        return max(0.0, min(100.0, score)), findings

    def review_asset(self, item: AssetItem, art_direction: dict[str, Any]) -> dict[str, Any]:
        """Perform combined technical and semantic QA on a single asset."""
        tech_score, tech_findings = self.validate_technical(item)
        sem_score, sem_findings = self.validate_semantic(item, art_direction)
        
        continuity_score = item.continuity_fit or 85.0
        quality_score = round((tech_score * 0.5) + (sem_score * 0.35) + (continuity_score * 0.15), 1)

        all_findings = tech_findings + sem_findings
        finding_text = " | ".join(all_findings) if all_findings else "Meets all technical and semantic criteria."

        # Determine review status
        if tech_score < 50.0:
            status = "reject"
            rec_action = "Regenerate with fallback provider or alternate medium."
        elif tech_score < 75.0 or sem_score < 65.0:
            status = "needs_review"
            rec_action = "Inspect frame manually before final composition."
        elif all_findings:
            status = "warning"
            rec_action = "Acceptable with minor observations."
        else:
            status = "pass"
            rec_action = "Approved for editorial composition."

        item.technical_score = tech_score
        item.semantic_fit = sem_score
        item.quality_score = quality_score
        item.qa_finding = finding_text

        # Update item status if ready
        if status in ("pass", "warning"):
            item.status = "ready"
        elif status == "needs_review":
            item.status = "needs_review"
        else:
            item.status = "failed"

        return {
            "asset_id": item.asset_id,
            "scene_id": item.scene_id,
            "type": item.type,
            "status": status,
            "technical_score": tech_score,
            "semantic_fit": sem_score,
            "continuity_fit": continuity_score,
            "quality_score": quality_score,
            "finding": finding_text,
            "recommended_action": rec_action,
        }

    def generate_review_report(
        self,
        production_id: str,
        assets: list[AssetItem],
        art_direction: dict[str, Any],
    ) -> AssetReviewReport:
        """Run QA across all assets and produce an AssetReviewReport."""
        reviews: list[dict[str, Any]] = []
        for a in assets:
            rev = self.review_asset(a, art_direction)
            reviews.append(rev)

        if not reviews:
            return AssetReviewReport(production_id=production_id, overall_status="pass")

        avg_tech = sum(r["technical_score"] for r in reviews) / len(reviews)
        avg_sem = sum(r["semantic_fit"] for r in reviews) / len(reviews)
        avg_cont = sum(r["continuity_fit"] for r in reviews) / len(reviews)

        statuses = [r["status"] for r in reviews]
        if "reject" in statuses:
            overall = "reject"
        elif "needs_review" in statuses:
            overall = "needs_review"
        elif "warning" in statuses:
            overall = "warning"
        else:
            overall = "pass"

        return AssetReviewReport(
            production_id=production_id,
            overall_status=overall,
            average_technical_score=round(avg_tech, 1),
            average_semantic_fit=round(avg_sem, 1),
            average_continuity_fit=round(avg_cont, 1),
            reviews=reviews,
        )
