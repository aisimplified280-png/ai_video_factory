"""Asset Director and production stage handler for Phase 5 Asset Intelligence."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw

from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind
from production.stage_registry import StageHandlerResult, StageResultStatus
from production.state import ProductionState
from .asset_manifest import (
    AssetItem,
    AssetManifestPayload,
    AssetReviewReport,
    AssetGenerationReport,
)
from .asset_selector import AssetSelector
from .asset_prompts import build_asset_generation_prompt
from .continuity import AssetContinuityTracker
from .asset_validator import AssetValidator
from .providers import (
    AssetCache,
    AssetProvider,
    NativeDiagramProvider,
    LocalLibraryProvider,
    DallEProvider,
    MockAssetProvider,
)
from tools.selectors.image_selector import ImageProviderSelector
from tools.selectors.video_selector import VideoProviderSelector
from tools.selectors.diagram_selector import DiagramProviderSelector


class AssetHandler:
    """Production stage handler for editorial asset intelligence and manifest generation."""

    def __init__(
        self,
        providers: dict[str, AssetProvider] | None = None,
        asset_cache: AssetCache | None = None,
        use_mock: bool = False,
    ) -> None:
        self.use_mock = use_mock
        self.selector = AssetSelector()
        self.continuity_tracker = AssetContinuityTracker()
        self.validator = AssetValidator()
        self.image_selector = ImageProviderSelector()
        self.video_selector = VideoProviderSelector()
        self.diagram_selector = DiagramProviderSelector()

        # Initialize providers
        if use_mock:
            mock = MockAssetProvider()
            self.providers: dict[str, AssetProvider] = {
                "image_generator": mock,
                "video_generator": mock,
                "native_diagram": mock,
                "local_library": mock,
                "dall_e": mock,
                "mock_provider": mock,
            }
        else:
            self.providers = providers or {
                "native_diagram": NativeDiagramProvider(),
                "local_library": LocalLibraryProvider(),
                "dall_e": DallEProvider(),
                "image_generator": DallEProvider(),
            }

        self.cache = asset_cache

    def _generate_contact_sheet(
        self,
        assets: list[AssetItem],
        output_dir: Path,
    ) -> Path:
        """Create an HTML contact sheet and image collage for human inspection."""
        output_dir.mkdir(parents=True, exist_ok=True)
        html_file = output_dir / "contact_sheet.html"
        
        cards_html = []
        collage_images = []

        for a in assets:
            fpath_str = a.file_path or ""
            fname = Path(fpath_str).name if fpath_str else "No File"
            status_color = "#00FF88" if a.status == "ready" else ("#F59E0B" if a.status == "needs_review" else "#EF4444")
            
            # Collect for image collage if valid image
            if fpath_str and Path(fpath_str).exists() and Path(fpath_str).suffix.lower() in (".png", ".jpg", ".jpeg"):
                try:
                    with Image.open(fpath_str) as img:
                        # Thumbnail for collage
                        thumb = img.copy().convert("RGB")
                        thumb.thumbnail((360, 640))
                        collage_images.append((thumb, a.asset_id, a.type))
                except Exception:
                    pass

            cards_html.append(f"""
            <div style="border: 1px solid #1E293B; background: #0F172A; border-radius: 8px; padding: 16px; margin: 12px; width: 340px; box-sizing: border-box;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: bold; color: #38BDF8;">{a.asset_id}</span>
                    <span style="background: {status_color}; color: #000; font-size: 11px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">{a.status.upper()}</span>
                </div>
                <div style="font-size: 12px; color: #94A3B8; margin-bottom: 8px;">Scene: <b>{a.scene_id}</b> | Medium: <b>{a.type}</b> ({a.source})</div>
                <div style="font-size: 13px; color: #F1F5F9; margin-bottom: 8px;"><b>Subject:</b> {a.subject}</div>
                <div style="font-size: 12px; color: #CBD5E1; margin-bottom: 8px;"><b>Purpose:</b> {a.purpose}</div>
                <div style="font-size: 11px; color: #64748B; margin-bottom: 12px;"><b>Provider:</b> {a.provider or 'None'} | <b>Cost:</b> ${a.cost_usd or 0.0:.3f}</div>
                {f'<img src="{fname}" style="width: 100%; border-radius: 4px; border: 1px solid #334155;" />' if fpath_str and Path(fpath_str).suffix.lower() in ('.png', '.jpg', '.jpeg') else '<div style="background: #1E293B; height: 180px; display: flex; align-items: center; justify-content: center; color: #64748B;">Video / Programmatic Asset</div>'}
                <div style="font-size: 11px; color: #94A3B8; margin-top: 8px;"><b>QA Finding:</b> {a.qa_finding or 'None'}</div>
            </div>
            """)

        html_content = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>Asset Contact Sheet</title>
            <style>
                body {{ background: #0A0D14; color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 24px; }}
                h1 {{ color: #F8FAFC; margin-bottom: 4px; }}
                .grid {{ display: flex; flex-wrap: wrap; justify-content: flex-start; }}
            </style>
        </head>
        <body>
            <h1>Asset Contact Sheet & QA Inspection</h1>
            <p style="color: #64748B; margin-top: 0;">AI Simplified Lab Production System // Phase 5 Asset Manifest</p>
            <div class="grid">
                {''.join(cards_html)}
            </div>
        </body>
        </html>"""

        html_file.write_text(html_content, encoding="utf-8")

        # Build composite PNG image collage if images exist
        if collage_images:
            cols = min(3, len(collage_images))
            rows = (len(collage_images) + cols - 1) // cols
            card_w, card_h = 360, 640
            sheet_img = Image.new("RGB", (cols * card_w, rows * card_h), color="#0A0D14")
            for idx, (thumb, aid, atype) in enumerate(collage_images):
                r = idx // cols
                c = idx % cols
                x = c * card_w + (card_w - thumb.width) // 2
                y = r * card_h + (card_h - thumb.height) // 2
                sheet_img.paste(thumb, (x, y))
            sheet_png = output_dir / "contact_sheet.png"
            sheet_img.save(sheet_png, format="PNG")

        return html_file

    def run(
        self,
        stage_name: str,
        state: ProductionState,
        inputs: dict[str, ArtifactEnvelope],
        **kwargs: Any,
    ) -> StageHandlerResult:
        # 1. Validate upstream scene_plan
        scene_plan_art = inputs.get("scene_plan")
        if not scene_plan_art or not scene_plan_art.data:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Asset stage blocked: missing required 'scene_plan' artifact.",
                errors=["MISSING_UPSTREAM_SCENE_PLAN"],
            )

        # Retrieve art direction and proposal
        art_direction_data = {}
        if "art_direction" in inputs and inputs["art_direction"].data:
            art_direction_data = inputs["art_direction"].data
        elif hasattr(state, "artifacts") and "art_direction" in state.artifacts:
            # Fallback load from store if available
            pass

        proposal_data = {}
        if "proposal_packet" in inputs and inputs["proposal_packet"].data:
            proposal_data = inputs["proposal_packet"].data

        scenes = scene_plan_art.data.get("scenes", [])
        if not scenes:
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message="Scene plan contains 0 scenes.",
                errors=["EMPTY_SCENE_PLAN"],
            )

        # 2. Plan Assets across Scenes
        planned_assets: list[AssetItem] = []
        for idx, sc in enumerate(scenes):
            asset_item = self.selector.select_asset_strategy(
                scene=sc,
                scene_idx=idx,
                total_scenes=len(scenes),
                art_direction=art_direction_data,
                production_id=state.project_id,
            )
            # Build prompts for generated items
            pos_prompt, neg_prompt = build_asset_generation_prompt(
                asset_item=asset_item,
                art_direction=art_direction_data,
            )
            asset_item.prompt = pos_prompt
            asset_item.negative_prompt = neg_prompt
            planned_assets.append(asset_item)

        # 3. Track Visual Continuity and Reference Linkages
        self.continuity_tracker.track_and_link_references(
            assets=planned_assets,
            art_direction=art_direction_data,
        )
        continuity_score = self.continuity_tracker.evaluate_continuity_score(
            assets=planned_assets,
            art_direction=art_direction_data,
        )
        for a in planned_assets:
            a.continuity_fit = continuity_score

        # 4. Prepare Asset Output Directory and Cache
        projects_root = Path(kwargs.get("projects_root") or "projects")
        asset_dir = projects_root / state.project_id / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        if not self.cache:
            self.cache = AssetCache(cache_dir=projects_root / ".cache" / "assets")

        # 5. Asset Generation & Fallback Loop
        total_spent = 0.0
        generation_attempts: list[dict[str, Any]] = []
        budget_cap = state.budget.budget_cap if hasattr(state, "budget") else 10.0
        remaining_budget = max(0.0, budget_cap - total_spent)

        native_provider = self.providers.get("native_diagram") or NativeDiagramProvider()
        local_provider = self.providers.get("local_library") or LocalLibraryProvider()

        for item in planned_assets:
            # Check cache
            cached_path = self.cache.get(item) if self.cache else None
            if cached_path:
                item.file_path = str(cached_path)
                item.status = "ready"
                generation_attempts.append({
                    "asset_id": item.asset_id,
                    "action": "cache_hit",
                    "file_path": str(cached_path),
                    "cost_usd": 0.0,
                })
                continue

            # Identify target provider
            prov_name = item.provider_strategy
            provider = self.providers.get(prov_name)

            # Check provider availability & budget
            need_fallback = False
            fallback_reason = ""

            if not provider or not provider.is_available():
                need_fallback = True
                fallback_reason = f"Primary provider {prov_name!r} unavailable or unconfigured."
            elif prov_name == "dall_e" and remaining_budget < 0.040:
                need_fallback = True
                fallback_reason = "Insufficient budget for neural generation."

            # Execution attempt
            gen_res = None
            if not need_fallback and provider:
                try:
                    gen_res = provider.generate(item, asset_dir)
                    if not gen_res.get("success"):
                        need_fallback = True
                        fallback_reason = gen_res.get("error", "Generation returned failure")
                except Exception as exc:
                    need_fallback = True
                    fallback_reason = str(exc)

            # Fallback Execution Chain
            if need_fallback:
                # Execute semantic fallback
                if item.type in ("diagram", "chart") or "native_diagram" in item.fallback_chain:
                    gen_res = native_provider.generate(item, asset_dir)
                    item.fallback_used = "native_diagram"
                    item.provider = "native_diagram"
                elif item.type == "logo" or "local_library" in item.fallback_chain:
                    gen_res = local_provider.generate(item, asset_dir)
                    item.fallback_used = "local_library"
                    item.provider = "local_library"
                else:
                    # Fallback for images: native technical schematic/canvas
                    gen_res = native_provider.generate(item, asset_dir)
                    item.fallback_used = "native_diagram_schematic"
                    item.provider = "native_diagram"

                generation_attempts.append({
                    "asset_id": item.asset_id,
                    "action": "fallback_applied",
                    "original_strategy": prov_name,
                    "actual_strategy": item.provider,
                    "reason": fallback_reason,
                })

            if gen_res and gen_res.get("success"):
                item.file_path = gen_res["file_path"]
                cost = float(gen_res.get("cost_usd", 0.0))
                item.cost_usd = cost
                total_spent += cost
                remaining_budget = max(0.0, budget_cap - total_spent)
                item.status = "ready"
                if self.cache and Path(item.file_path).exists():
                    self.cache.put(item, Path(item.file_path))
            else:
                item.status = "failed"

        # 6. Technical & Semantic Quality Assurance
        review_report = self.validator.generate_review_report(
            production_id=state.project_id,
            assets=planned_assets,
            art_direction=art_direction_data,
        )

        # 7. Generate Contact Sheet
        self._generate_contact_sheet(planned_assets, asset_dir)

        # 8. Write Review & Generation Reports to Project Assets Directory
        rev_file = asset_dir / "asset_review_report.json"
        rev_file.write_text(json.dumps(review_report.model_dump(), indent=2), encoding="utf-8")

        gen_report = AssetGenerationReport(
            production_id=state.project_id,
            total_cost_usd=round(total_spent, 4),
            generation_attempts=generation_attempts,
        )
        gen_file = asset_dir / "asset_generation_report.json"
        gen_file.write_text(json.dumps(gen_report.model_dump(), indent=2), encoding="utf-8")

        # 9. Build Manifest Payload
        medium_dist: dict[str, int] = {}
        source_dist: dict[str, int] = {}
        for a in planned_assets:
            medium_dist[a.type] = medium_dist.get(a.type, 0) + 1
            source_dist[a.source] = source_dist.get(a.source, 0) + 1

        manifest_payload = AssetManifestPayload(
            assets=planned_assets,
            total_estimated_cost=round(total_spent, 4),
            actual_cost=round(total_spent, 4),
            medium_distribution=medium_dist,
            source_distribution=source_dist,
            metadata={
                "production_id": state.project_id,
                "overall_qa_status": review_report.overall_status,
                "average_technical_score": review_report.average_technical_score,
                "average_semantic_fit": review_report.average_semantic_fit,
                "continuity_score": continuity_score,
            },
        )

        producer = ProducerInfo(
            kind=ProducerKind.TOOL,
            provider="asset_director",
            model="asset_intelligence_v2",
        )

        return StageHandlerResult(
            status=StageResultStatus.READY,
            data=manifest_payload.to_schema_dict(),
            producer=producer,
            message=(
                f"Asset stage resolved {len(planned_assets)} assets across {len(medium_dist)} media types. "
                f"QA Status: {review_report.overall_status.upper()} (Tech: {review_report.average_technical_score:.1f}, "
                f"Semantic: {review_report.average_semantic_fit:.1f}, Continuity: {continuity_score:.1f})."
            ),
        )
