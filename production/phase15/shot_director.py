"""Phase 15/15B Shot Director & Claim Grounding Engine.

Orchestrates distinct directorial decisions for each scene:
- Grounding-First Selection: Factual claim evidence dominates over pure diversity (Phase 15B Step 22)
- Integrates ClaimVisualPlan, preserving entities, actions, and relationships
- Enforces VisualMemory anti-repetition constraints across scenes
- Strictly prevents > 2 consecutive scenes from using the same VisualMode
- Filters unacceptable visuals / generic clichés
- Outputs canonical 22-field SceneVisualPlan with full claim grounding metadata
"""
from __future__ import annotations

import re
from typing import Any, Optional
from .models import ClaimType, ClaimVisualPlan, GroundingLevel, SceneVisualPlan, VisualMode
from .semantic_analyzer import SemanticSceneIntent
from .claim_grounder import evaluate_claim_grounding


class VisualMemory:
    """Historical buffer of recent directorial choices within the video."""

    def __init__(self, max_history: int = 5) -> None:
        self.history: list[SceneVisualPlan] = []
        self.max_history = max_history

    def record(self, plan: SceneVisualPlan) -> None:
        self.history.append(plan)

    def get_prohibited(self, lookback: int = 2) -> dict[str, set[str]]:
        """Return attributes used in the last `lookback` scenes to forbid repetition."""
        recent = self.history[-lookback:] if lookback else self.history
        return {
            "visual_modes": {p.visual_mode.value for p in recent},
            "shot_types": {p.shot_type for p in recent},
            "camera_movements": {p.camera_motion for p in recent},
            "environments": {p.environment for p in recent},
            "subjects": {p.subject for p in recent},
            "compositions": {p.composition for p in recent},
        }

    def consecutive_mode_count(self, mode: VisualMode) -> int:
        """Count how many consecutive recent scenes already used this mode."""
        count = 0
        for p in reversed(self.history):
            if p.visual_mode == mode:
                count += 1
            else:
                break
        return count

    def compute_repetition_penalty(self, option: dict[str, Any], candidate_mode: VisualMode) -> float:
        """Weighted penalties (Phase 15 Step 5):
        same visual mode: -2.0
        same shot type: -2.0
        same camera motion: -2.0
        same composition: -2.0
        same environment: -1.0
        same subject: -1.0
        """
        penalty = 0.0
        if not self.history:
            return 0.0
        recent = self.history[-2:]
        for p in recent:
            if candidate_mode == p.visual_mode:
                penalty -= 2.0
            if option.get("shot_type") == p.shot_type:
                penalty -= 2.0
            if option.get("camera_motion") == p.camera_motion or option.get("camera_movement") == p.camera_motion:
                penalty -= 2.0
            if option.get("composition") == p.composition:
                penalty -= 2.0
            if option.get("environment") == p.environment:
                penalty -= 1.0
            if option.get("subject") == p.subject:
                penalty -= 1.0
        return penalty


DIRECTORIAL_PALETTES: dict[VisualMode, list[dict[str, Any]]] = {
    VisualMode.DETAIL: [
        {
            "shot_type": "extreme_macro_probe",
            "camera_motion": "fast_push_in",
            "camera_angle": "macro_probe_level",
            "composition": "tight_macro_crop",
            "subject": "precision robotic gripper mechanism",
            "action": "sub-millimeter pneumatic clamping onto high-speed physical target with zero play",
            "environment": "high-precision industrial robotics testing rig",
            "lens_feel": "24mm_macro_probe",
            "depth": "extreme_shallow_dof",
            "visual_metaphor": "tactile physical precision and raw kinetic response",
            "lighting": "razor-sharp directional specular highlights across brushed titanium joints",
            "motion_intensity": 8.0,
            "transition_in": "hard_cut",
            "transition_out": "hard_cut",
            "overlay_strategy": "none_initial_cut",
            "graphic_strategy": "none",
            "asset_strategy": "generated_background",
        },
        {
            "shot_type": "micro_actuator_closeup",
            "camera_motion": "tracking",
            "camera_angle": "low_macro_angle",
            "composition": "asymmetric_focal_plane",
            "subject": "hydraulic joint actuator array",
            "action": "rapid micro-rotations adjusting torque under closed-loop sensor feedback",
            "environment": "cleanroom component diagnostic station",
            "lens_feel": "50mm_macro",
            "depth": "shallow_dof",
            "visual_metaphor": "intense industrial craftsmanship",
            "lighting": "high-contrast cool neutral white with shallow depth of field",
            "motion_intensity": 7.0,
            "transition_in": "hard_cut",
            "transition_out": "hard_cut",
            "overlay_strategy": "subtle_telemetry",
            "graphic_strategy": "telemetry_hud",
            "asset_strategy": "generated_background",
        },
    ],
    VisualMode.LITERAL: [
        {
            "shot_type": "industrial_arm_command_medium",
            "camera_motion": "tracking",
            "camera_angle": "eye_level_three_quarter",
            "composition": "balanced_rule_of_thirds",
            "subject": "six-axis industrial robotic arm directly controlled by AI model",
            "action": "articulating with sub-millimeter precision to manipulate component under closed-loop sensor feedback",
            "environment": "high-precision industrial robotics automated workcell with optical telemetry HUD",
            "lens_feel": "35mm_standard",
            "depth": "medium_depth",
            "visual_metaphor": "direct artificial intelligence manifestation into physical mechanical agency",
            "lighting": "sharp industrial task lighting with directional cool specular bevels",
            "motion_intensity": 7.5,
            "transition_in": "hard_cut",
            "transition_out": "hard_cut",
            "overlay_strategy": "subtle_telemetry",
            "graphic_strategy": "telemetry_hud",
            "asset_strategy": "generated_background",
        },
        {
            "shot_type": "dual_actuator_workcell_wide",
            "camera_motion": "push_in",
            "camera_angle": "elevated_45",
            "composition": "layered_depth",
            "subject": "dual robotic arms executing synchronized physical assembly",
            "action": "rapid physical component insertion with real-time optical tracking feedback",
            "environment": "automated advanced manufacturing cell",
            "lens_feel": "40mm_prime",
            "depth": "shallow_dof",
            "visual_metaphor": "physical automation replacing manual labor",
            "lighting": "high-contrast overhead lighting with crisp shadows",
            "motion_intensity": 8.0,
            "transition_in": "hard_cut",
            "transition_out": "hard_cut",
            "overlay_strategy": "minimal_callout",
            "graphic_strategy": "none",
            "asset_strategy": "generated_background",
        },
    ],
    VisualMode.DEMONSTRATION: [
        {
            "shot_type": "dynamic_obstacle_reroute_overhead",
            "camera_motion": "overhead_track",
            "camera_angle": "high_overhead_45",
            "composition": "wide_isometric_plane",
            "subject": "autonomous logistics machines dynamically rerouting around obstacles",
            "action": "active sensor detection cone detecting unexpected obstacle and dynamically recalculating vector trajectory around it without stopping",
            "environment": "automated fulfillment warehouse floor with LED floor grid markers and dynamic obstacle zone",
            "lens_feel": "35mm_orthographic_look",
            "depth": "deep_focus_infinite",
            "visual_metaphor": "emergent swarm agility and dynamic real-time obstacle avoidance",
            "lighting": "crisp industrial floodlighting with yellow safety corridors and cyan sensor cones",
            "motion_intensity": 8.0,
            "transition_in": "directional_wipe",
            "transition_out": "hard_cut",
            "overlay_strategy": "subtle_telemetry",
            "graphic_strategy": "vector_paths",
            "asset_strategy": "generated_background",
        },
        {
            "shot_type": "swarm_choreography_isometric",
            "camera_motion": "lateral_tracking",
            "camera_angle": "isometric_30",
            "composition": "rule_of_thirds",
            "subject": "fleet of autonomous mobile robots interweaving seamlessly",
            "action": "multiple autonomous units coordinating high-speed intersections with zero stopping",
            "environment": "high-density sorting hub with dynamic digital floor pathways",
            "lens_feel": "50mm_standard",
            "depth": "medium_depth",
            "visual_metaphor": "seamless multi-agent coordination",
            "lighting": "neutral ambient with illuminated LED safety pathways",
            "motion_intensity": 7.5,
            "transition_in": "hard_cut",
            "transition_out": "hard_cut",
            "overlay_strategy": "subtle_telemetry",
            "graphic_strategy": "vector_paths",
            "asset_strategy": "generated_background",
        },
    ],
    VisualMode.SCALE: [
        {
            "shot_type": "high_throughput_logistics_flow",
            "camera_motion": "crane_pull_out",
            "camera_angle": "steep_downward_crane",
            "composition": "multi_tier_depth_perspective",
            "subject": "high-speed dual-channel automated logistics flow eliminating bottlenecks",
            "action": "hundreds of automated rovers and sorting conveyors moving inventory rapidly with zero delays and minimal human intervention",
            "environment": "modern automated distribution mega-terminal with multi-tier high-speed sorting corridors",
            "lens_feel": "18mm_ultra_wide",
            "depth": "atmospheric_depth_haze",
            "visual_metaphor": "frictionless industrial throughput and zero-delay logistics",
            "lighting": "bright high-throughput green status indicators with industrial ambient illumination",
            "motion_intensity": 7.0,
            "transition_in": "cross_dissolve",
            "transition_out": "hard_cut",
            "overlay_strategy": "minimal_callout",
            "graphic_strategy": "telemetry_hud",
            "asset_strategy": "generated_background",
        },
        {
            "shot_type": "high_aerial_crane_reveal",
            "camera_motion": "crane_pull_out",
            "camera_angle": "steep_downward_crane",
            "composition": "multi_tier_depth_perspective",
            "subject": "multi-tier automated fulfillment mega-terminal",
            "action": "hundreds of automated rovers, gantry systems, and conveyor lines flowing in high-speed synchrony",
            "environment": "vast multi-level distribution mega-facility spanning into the horizon",
            "lens_feel": "18mm_ultra_wide",
            "depth": "atmospheric_depth_haze",
            "visual_metaphor": "irreversible planetary-scale industrial automation",
            "lighting": "warm amber warning beacons casting long dramatic shadows against cold structural steel",
            "motion_intensity": 6.5,
            "transition_in": "cross_dissolve",
            "transition_out": "hard_cut",
            "overlay_strategy": "minimal_callout",
            "graphic_strategy": "none",
            "asset_strategy": "generated_background",
        },
    ],
    VisualMode.BRAND_CTA: [
        {
            "shot_type": "clean_minimalist_studio",
            "camera_motion": "steady_breathing",
            "camera_angle": "level_horizon",
            "composition": "clean_minimalist_center",
            "subject": "channel insignia and kinetic briefing brand mark",
            "action": "subtle breathing pulse of electric blue rim light around dark matte brand badge",
            "environment": "minimalist dark obsidian architectural studio with polished reflection floor",
            "lens_feel": "50mm_clean_prime",
            "depth": "shallow_mirror_reflection",
            "visual_metaphor": "authoritative, trustworthy frontier AI intelligence",
            "lighting": "dark graphite rim lighting with subtle cyan specular glow, elegant negative space",
            "motion_intensity": 3.0,
            "transition_in": "light_flash",
            "transition_out": "fade",
            "overlay_strategy": "brand_lock",
            "graphic_strategy": "subscribe_badge",
            "asset_strategy": "generated_background",
        },
    ],
    VisualMode.MECHANISM: [
        {
            "shot_type": "internal_actuator_cutaway",
            "camera_motion": "push_in",
            "camera_angle": "isometric_30",
            "composition": "layered_depth",
            "subject": "harmonic drive transmission gears and closed-loop motor bus",
            "action": "flawless high-torque gear tooth engagement rotating under microsecond sensor telemetry",
            "environment": "precision robotic actuator assembly bench",
            "lens_feel": "50mm_prime",
            "depth": "deep_depth_plane",
            "visual_metaphor": "microscopic precision delivering macroscopic mechanical power",
            "lighting": "directional rim light exposing gear tooth tolerances and lubricant sheen",
            "motion_intensity": 7.5,
            "transition_in": "hard_cut",
            "transition_out": "hard_cut",
            "overlay_strategy": "subtle_telemetry",
            "graphic_strategy": "telemetry_hud",
            "asset_strategy": "generated_background",
        },
    ],
    VisualMode.COMPARISON: [
        {
            "shot_type": "split_screen_bench_contrast",
            "camera_motion": "tracking",
            "camera_angle": "symmetric_flat",
            "composition": "split_contrast_frame",
            "subject": "traditional rigid robotics versus dynamic adaptive AI robotics",
            "action": "rigid arm halting upon obstruction while adaptive system smoothly reroutes",
            "environment": "dual comparative robotic testing bench",
            "lens_feel": "40mm_prime",
            "depth": "uniform_plane",
            "visual_metaphor": "the obsolescence of pre-programmed code",
            "lighting": "amber warning on left, clean cyan status on right",
            "motion_intensity": 7.0,
            "transition_in": "directional_wipe",
            "transition_out": "hard_cut",
            "overlay_strategy": "split_metric",
            "graphic_strategy": "comparison_labels",
            "asset_strategy": "generated_background",
        },
    ],
    VisualMode.METAPHOR: [
        {
            "shot_type": "neural_data_flight",
            "camera_motion": "dolly_through",
            "camera_angle": "eye_level_flythrough",
            "composition": "asymmetric_leading_lines",
            "subject": "synaptic neural data stream bridging into robotic motor bus",
            "action": "electric cyan pulses racing through three-dimensional tensor lattice into physical actuators",
            "environment": "abstract dark neural matrix and illuminated data pathways",
            "lens_feel": "35mm_anamorphic",
            "depth": "volumetric_light_conduits",
            "visual_metaphor": "the invisible artificial mind manifesting into physical force",
            "lighting": "luminescent electric cyan and deep cobalt bioluminescent glow against dark void",
            "motion_intensity": 7.0,
            "transition_in": "zoom_transition",
            "transition_out": "motion_blur",
            "overlay_strategy": "none",
            "graphic_strategy": "none",
            "asset_strategy": "generated_background",
        },
    ],
    VisualMode.INTERFACE: [
        {
            "shot_type": "telemetry_hud_terminal",
            "camera_motion": "static_locked",
            "camera_angle": "flat_ortho",
            "composition": "centered_grid",
            "subject": "live robot telemetry command dashboard",
            "action": "streaming vector coordinates and actuator latency indicators updating in real time",
            "environment": "industrial terminal screen with dark high-contrast theme",
            "lens_feel": "50mm_flat",
            "depth": "shallow_dof",
            "visual_metaphor": "telemetry feedback and verified control authority",
            "lighting": "cyan and emerald phosphor glow against dark background",
            "motion_intensity": 4.0,
            "transition_in": "hard_cut",
            "transition_out": "hard_cut",
            "overlay_strategy": "subtle_telemetry",
            "graphic_strategy": "telemetry_hud",
            "asset_strategy": "generated_background",
        },
    ],
    VisualMode.ENVIRONMENT: [
        {
            "shot_type": "establishing_wide",
            "camera_motion": "slow_push_in",
            "camera_angle": "wide_level",
            "composition": "rule_of_thirds",
            "subject": "modern automated robotics deployment facility",
            "action": "continuous synchronized operations in clean industrial setting",
            "environment": "advanced robotic distribution and research lab",
            "lens_feel": "24mm_wide",
            "depth": "deep_depth_plane",
            "visual_metaphor": "the dawn of autonomous infrastructure",
            "lighting": "cool neutral architectural lighting",
            "motion_intensity": 5.0,
            "transition_in": "hard_cut",
            "transition_out": "hard_cut",
            "overlay_strategy": "minimal_callout",
            "graphic_strategy": "none",
            "asset_strategy": "generated_background",
        },
    ],
}
DIRECTORIAL_PALETTES[VisualMode.DATA_INTERFACE] = DIRECTORIAL_PALETTES[VisualMode.INTERFACE]
DIRECTORIAL_PALETTES[VisualMode.ABSTRACT] = DIRECTORIAL_PALETTES[VisualMode.METAPHOR]
DIRECTORIAL_PALETTES[VisualMode.DATA_VISUALIZATION] = DIRECTORIAL_PALETTES[VisualMode.INTERFACE]
DIRECTORIAL_PALETTES[VisualMode.TRANSFORMATION] = DIRECTORIAL_PALETTES[VisualMode.COMPARISON]
DIRECTORIAL_PALETTES[VisualMode.CONSEQUENCE] = DIRECTORIAL_PALETTES[VisualMode.SCALE]
DIRECTORIAL_PALETTES[VisualMode.HUMAN_IMPACT] = DIRECTORIAL_PALETTES[VisualMode.LITERAL]


class ShotDirector:
    """Directs scene visual execution, prioritizing claim grounding over diversity (Phase 15B)."""

    def __init__(self) -> None:
        self.memory = VisualMemory()

    def direct_scenes(
        self,
        intents: list[SemanticSceneIntent],
        topic: str,
    ) -> list[SceneVisualPlan]:
        """Convert semantic intents into grounded, diverse SceneVisualPlans."""
        self.memory = VisualMemory()
        plans: list[SceneVisualPlan] = []

        for i, intent in enumerate(intents):
            plan = self._direct_single_scene(intent, i, len(intents), topic)
            self.memory.record(plan)
            plans.append(plan)

        return plans

    def _direct_single_scene(
        self,
        intent: SemanticSceneIntent,
        scene_idx: int,
        total_scenes: int,
        topic: str,
    ) -> SceneVisualPlan:
        prohibited = self.memory.get_prohibited(lookback=2)
        chosen_mode = intent.recommended_mode
        claim_plan = intent.claim_plan

        # Enforce Rule: No more than 2 consecutive scenes may use the same visual mode
        if self.memory.consecutive_mode_count(chosen_mode) >= 2:
            for alt in intent.fallback_modes:
                if self.memory.consecutive_mode_count(alt) < 2 and alt.value not in prohibited["visual_modes"]:
                    chosen_mode = alt
                    break
            else:
                for candidate_mode in VisualMode:
                    if candidate_mode != chosen_mode and self.memory.consecutive_mode_count(candidate_mode) == 0:
                        chosen_mode = candidate_mode
                        break

        # Gather palette options
        palette_options = list(DIRECTORIAL_PALETTES.get(chosen_mode, DIRECTORIAL_PALETTES[VisualMode.LITERAL]))

        # Dynamically inject tailored option directly from ClaimVisualPlan if present
        if claim_plan:
            if chosen_mode == VisualMode.BRAND_CTA:
                custom_shot_type = "clean_minimalist_studio"
            elif scene_idx == 0:
                custom_shot_type = "extreme_macro_probe"
            elif chosen_mode == VisualMode.LITERAL:
                custom_shot_type = "industrial_arm_command_medium"
            elif chosen_mode == VisualMode.DEMONSTRATION:
                custom_shot_type = "dynamic_obstacle_reroute_overhead"
            elif chosen_mode == VisualMode.SCALE:
                custom_shot_type = "high_throughput_logistics_flow"
            else:
                custom_shot_type = f"{chosen_mode.value}_grounded_execution"

            custom_opt = {
                "shot_type": custom_shot_type,
                "camera_motion": "push_in" if scene_idx == 0 else "tracking",
                "camera_angle": "macro_probe_level" if scene_idx == 0 else "eye_level_three_quarter",
                "composition": "tight_macro_crop" if scene_idx == 0 else "balanced_rule_of_thirds",
                "subject": ", ".join(claim_plan.entities) or intent.what_is_said,
                "action": claim_plan.action,
                "environment": claim_plan.environment,
                "lens_feel": "24mm_macro_probe" if scene_idx == 0 else "35mm_standard",
                "depth": "extreme_shallow_dof" if scene_idx == 0 else "medium_depth",
                "visual_metaphor": claim_plan.relationship,
                "lighting": "sharp high-contrast directional lighting with cool specular highlights",
                "motion_intensity": 8.0 if scene_idx == 0 else 7.0,
                "transition_in": "hard_cut",
                "transition_out": "hard_cut",
                "overlay_strategy": "none_initial_cut" if scene_idx == 0 else ("brand_lock" if chosen_mode == VisualMode.BRAND_CTA else "subtle_telemetry"),
                "graphic_strategy": "none" if scene_idx == 0 else "telemetry_hud",
                "asset_strategy": "generated_background",
            }
            # Add custom_opt as top priority
            palette_options.insert(0, custom_opt)

        # Step 22 Selection Formula:
        # score = grounding_score * 0.35 + claim_coverage * 0.25 + narrative_alignment * 0.20 + visual_clarity * 0.10 + diversity * 0.10
        best_option = palette_options[0]
        best_score = -999.0
        best_eval = None

        for opt in palette_options:
            # Build mock SceneVisualPlan to evaluate grounding
            mock_plan = SceneVisualPlan(
                scene_id=intent.scene_id,
                section_id=intent.section_id,
                narrative_role=intent.narrative_role,
                visual_intent=intent.what_viewer_sees,
                visual_mode=chosen_mode,
                subject=opt.get("subject", ""),
                action=opt.get("action", ""),
                environment=opt.get("environment", ""),
                shot_type=opt.get("shot_type", "medium"),
                camera_motion=opt.get("camera_motion", "push_in"),
                composition=opt.get("composition", "rule_of_thirds"),
                visual_prompt=f"{opt.get('subject')} {opt.get('action')} in {opt.get('environment')}",
            )

            # Evaluate claim grounding
            if claim_plan:
                eval_record = evaluate_claim_grounding(claim_plan, mock_plan)
                grounding_s = eval_record.visual_grounding_score
                coverage_s = eval_record.claim_coverage
            else:
                grounding_s = 8.0
                coverage_s = 1.0
                eval_record = None

            # Repetition penalty (diversity)
            rep_penalty = self.memory.compute_repetition_penalty(opt, chosen_mode)
            diversity_norm = max(0.0, min(10.0, 10.0 + rep_penalty))

            # Narrative alignment
            narrative_align = 9.0 if chosen_mode == intent.recommended_mode else 7.5
            visual_clarity = 8.5

            composite_score = (
                grounding_s * 0.35
                + (coverage_s * 10.0) * 0.25
                + narrative_align * 0.20
                + visual_clarity * 0.10
                + diversity_norm * 0.10
            )

            if composite_score > best_score:
                best_score = composite_score
                best_option = opt
                best_eval = eval_record

        # Construct final prompt strictly describing evidence (Step 7 + Phase 15B)
        bg_prompt = (
            f"Ultra-detailed cinematic documentary photography, {best_option['shot_type']} of {best_option['subject']}, "
            f"{best_option['action']}, inside {best_option['environment']}. "
            f"{best_option['lighting']}, {best_option['composition']}, depth of {best_option['depth']}, "
            f"8k resolution, photorealistic, clean negative space, vertical 9:16 composition, "
            f"no visible human faces, no artificial cartoon stylization."
        )

        unacceptable_list = claim_plan.unacceptable_visuals if claim_plan else []
        negative_constraints = [
            "no cartoon stylization",
            "no anime",
            "no visible human faces",
            "no low-resolution blur",
            "no generic AI brain clichés without physical machine",
        ] + [f"no {u}" for u in unacceptable_list[:3]]

        avoid_rep = list(prohibited["environments"]) + list(prohibited["shot_types"])

        plan = SceneVisualPlan(
            scene_id=intent.scene_id,
            section_id=intent.section_id,
            narrative_role=intent.narrative_role,
            visual_intent=intent.what_viewer_sees,
            visual_mode=chosen_mode,
            subject=best_option["subject"],
            action=best_option["action"],
            environment=best_option["environment"],
            shot_type=best_option["shot_type"],
            camera_angle=best_option["camera_angle"],
            camera_motion=best_option["camera_motion"],
            lens_feel=best_option["lens_feel"],
            composition=best_option["composition"],
            depth=best_option["depth"],
            lighting=best_option["lighting"],
            motion_intensity=best_option["motion_intensity"],
            transition_in=best_option["transition_in"],
            transition_out=best_option["transition_out"],
            overlay_strategy=best_option["overlay_strategy"],
            graphic_strategy=best_option["graphic_strategy"],
            asset_strategy=best_option["asset_strategy"],
            visual_prompt=bg_prompt,
            negative_constraints=negative_constraints,
            avoid_repetition=avoid_rep,
            # Grounding additions
            claim_plan=claim_plan,
            claim_id=claim_plan.claim_id if claim_plan else "",
            claim_type=claim_plan.claim_type.value if claim_plan else "",
            entities=claim_plan.entities if claim_plan else [],
            relationship=claim_plan.relationship if claim_plan else "",
            required_visual_evidence=claim_plan.required_visual_evidence if claim_plan else [],
            unacceptable_visuals=claim_plan.unacceptable_visuals if claim_plan else [],
            grounding_level=claim_plan.grounding_level if claim_plan else GroundingLevel.LEVEL_3.value,
            visual_grounding_score=best_eval.visual_grounding_score if best_eval else 8.5,
            claim_coverage_score=best_eval.claim_coverage if best_eval else 1.0,
            # Backward compatibility fields
            visual_metaphor=best_option.get("visual_metaphor", ""),
            motion_intent="reveal",
            overlay_intent=best_option["overlay_strategy"],
            background_prompt=bg_prompt,
            camera_movement=best_option["camera_motion"],
            subject_action=best_option["action"],
            scene_breakdown={
                "location": best_option["environment"],
                "main_subject": best_option["subject"],
                "camera": f"{best_option['camera_motion']}, {best_option['camera_angle']}, vertical 9:16",
                "lighting": best_option["lighting"],
                "action": best_option["action"],
                "emotion": intent.what_viewer_feels[:60],
                "visual_mode": chosen_mode.value,
                "shot_type": best_option["shot_type"],
            },
            supporting_graphics=[],
        )
        return plan
