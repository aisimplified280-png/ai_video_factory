"""Capability-aware medium and strategy selector for editorial asset planning."""
from __future__ import annotations

from typing import Any
from .asset_manifest import AssetItem


class AssetSelector:
    """Selects the optimal visual medium, source strategy, and semantic fallback chain for each scene."""

    def select_asset_strategy(
        self,
        scene: dict[str, Any],
        scene_idx: int,
        total_scenes: int,
        art_direction: dict[str, Any],
        production_id: str,
    ) -> AssetItem:
        scene_id = scene.get("scene_id") or f"scene_{scene_idx + 1:02d}"
        role = str(scene.get("narrative_role") or "context").lower()
        tech = str(scene.get("visual_technique") or "cinematic_broll").lower()
        stype = str(scene.get("type") or "image").lower()
        subject = str(scene.get("subject") or "Core System")
        subject_action = str(scene.get("subject_action") or "Dynamic transformation")
        purpose = str(scene.get("visual_purpose") or f"Establish visual clarity for {role}")
        environment = str(scene.get("environment") or "Technical high-contrast workspace")
        composition = str(scene.get("composition_intent") or "wide asymmetrical layout")
        camera = str(scene.get("camera_intent") or "approach_subject")
        motion = str(scene.get("motion_intent") or "assemble")
        dur = float(scene.get("end_seconds", 5.0) - scene.get("start_seconds", 0.0))

        # Enforce valid purpose length
        if len(purpose) < 5 or purpose.lower() in ("visual", "scene image", "placeholder"):
            purpose = f"Visually communicate the {role} of {subject} within the overarching metaphor."

        # Medium & Source Strategy Selection
        if role == "cta" or tech == "kinetic_typography" or stype == "text_card":
            # CTA / Brand Identity
            asset_type = "logo"
            source_strategy = "local_library"
            fallback_chain = [
                "local_library_brand",
                "native_vector_logo",
                "native_composition",
                "explicit_blocker",
            ]
            provider_strategy = "local_library"

        elif tech in (
            "diagram_reveal",
            "system_assembly",
            "system_explosion",
            "network_build",
            "interface_walkthrough",
            "code_walkthrough",
        ) or stype == "diagram":
            # Explanatory systems & native diagrams
            asset_type = "diagram"
            source_strategy = "native"
            fallback_chain = [
                "programmatic_svg",
                "pil_canvas_diagram",
                "generated_image_technical_schematic",
                "explicit_blocker",
            ]
            provider_strategy = "native_diagram"

        elif tech in ("data_dashboard", "stat_punch") or "chart" in subject.lower():
            # Numerical evidence & metric dashboards
            asset_type = "chart"
            source_strategy = "native"
            fallback_chain = [
                "programmatic_svg_chart",
                "pil_metric_dashboard",
                "generated_technical_infographic",
                "explicit_blocker",
            ]
            provider_strategy = "native_diagram"

        elif tech in ("timeline_progression", "document_stack", "evidence_wall"):
            # Historical records / archival montage / evidence
            asset_type = "image"
            source_strategy = "generated"  # Or web archive
            fallback_chain = [
                "primary_image_generator",
                "programmatic_evidence_canvas",
                "native_diagram",
                "explicit_blocker",
            ]
            provider_strategy = "image_generator"

        elif stype in ("broll", "generated", "animation") or tech in (
            "cinematic_broll",
            "analogy_visualization",
            "cause_effect",
            "scale_transition",
            "object_transformation",
        ):
            # Physical metaphor / scale / cinematic environment
            # If motion is critical and video generation is supported, prefer video; else high-res generated image
            asset_type = "video" if stype == "broll" and dur >= 4.0 else "image"
            source_strategy = "generated"
            if asset_type == "video":
                fallback_chain = [
                    "primary_video_generator",
                    "generated_image_with_native_camera_motion",
                    "native_technical_animation",
                    "explicit_blocker",
                ]
                provider_strategy = "video_generator"
            else:
                fallback_chain = [
                    "primary_image_generator",
                    "secondary_image_generator",
                    "native_technical_schematic",
                    "explicit_blocker",
                ]
                provider_strategy = "image_generator"

        else:
            asset_type = "image"
            source_strategy = "generated"
            fallback_chain = [
                "primary_image_generator",
                "native_diagram",
                "explicit_blocker",
            ]
            provider_strategy = "image_generator"

        # Style & Quality requirements inherited from Art Direction
        palette = art_direction.get("palette_discipline", {})
        quality_reqs = {
            "min_width": 1080,
            "min_height": 1920,
            "aspect_ratio": "9:16",
            "palette_primary": palette.get("primary", "#0F172A"),
            "palette_accent": palette.get("accent_1", "#38BDF8"),
            "texture": art_direction.get("texture_language", "Subtle matte technical grain"),
            "anti_patterns": art_direction.get("anti_patterns", []),
            "min_technical_score": 80.0,
            "min_semantic_fit": 70.0,
        }

        # Structured diagram specification if native diagram/chart
        diagram_spec = None
        if asset_type in ("diagram", "chart"):
            diagram_spec = {
                "diagram_type": tech if tech != "kinetic_typography" else "system_assembly",
                "subject": subject,
                "action": subject_action,
                "nodes": [
                    {"id": "node_01", "label": subject, "type": "primary"},
                    {"id": "node_02", "label": "Operational Load", "type": "metric"},
                    {"id": "node_03", "label": "Output Telemetry", "type": "flow"},
                ],
                "connectors": [
                    {"from": "node_01", "to": "node_02", "label": "Drives"},
                    {"from": "node_02", "to": "node_03", "label": "Streams"},
                ],
                "color_accent": palette.get("accent_1", "#38BDF8"),
                "background_color": palette.get("primary", "#0A0D14"),
            }

        asset_id = f"ast_{scene_id}_primary"
        return AssetItem(
            asset_id=asset_id,
            scene_id=scene_id,
            purpose=purpose,
            visual_role="primary",
            type=asset_type,
            source=source_strategy,
            provider=provider_strategy,
            expected_duration=round(dur, 2),
            quality_requirements=quality_reqs,
            fallback_chain=fallback_chain,
            status="pending",
            subject=subject,
            subject_action=subject_action,
            environment=environment,
            composition_requirements=composition,
            camera_requirements=camera,
            motion_requirements=motion,
            style_requirements=art_direction.get("design_read", "Industrial technical high contrast"),
            continuity_requirements=scene.get("continuity_from_previous", ""),
            source_strategy=source_strategy,
            provider_strategy=provider_strategy,
            diagram_spec=diagram_spec,
            metadata={
                "production_id": production_id,
                "visual_technique": tech,
                "narrative_role": role,
            },
        )
