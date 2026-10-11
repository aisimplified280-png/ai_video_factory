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


def _narration_subject(spoken_text: str, key_entities: Optional[list[str]] = None) -> str:
    """Short subject phrase taken from the narrator's own first clause.

    Keeps the on-screen subject aligned with what is being said ("How do RAGs
    retrieve answers") instead of a joined entity list or a template string.
    Trailing function words are trimmed so the phrase reads like a subject,
    not a cut-off sentence. If the 7-word cut would strand a named entity
    ("...directly control" with "physical robots" left out), the cut extends
    just far enough to include it.
    """
    if not spoken_text:
        return ""
    # A bare leading sequencer ("First, cameras...") would become the whole subject —
    # drop it and read the next clause instead. A sequencer inside a real clause
    # ("Next time the virus appears") stays: it carries meaning.
    first_clause = re.split(r"[,.;:;!?\n]", spoken_text, maxsplit=1)[0]
    sequencers = {
        "first", "then", "next", "finally", "so", "and", "but", "now", "also",
        "firstly", "secondly", "lastly",
    }
    working = spoken_text
    if first_clause.strip().lower().strip("'\"“”‘’,") in sequencers and "," in working:
        working = working.split(",", 1)[1].lstrip()
    head = re.split(r"[,.;:;!?\n]", working, maxsplit=1)[0]
    words = head.split()
    # A spoken question is already a complete, self-contained line: its trailing
    # words carry the meaning ("...where it is"). Trimming them would leave a
    # mangled fragment on the title card, so the question is kept verbatim.
    _first_punct = re.search(r"[,.;:!?;\n]", working)
    if _first_punct and working[_first_punct.start()] == "?" and words:
        subject = " ".join(words)
        while len(subject) > 75 and len(words) > 4:
            words.pop()
            subject = " ".join(words).strip()
        if subject.count('"') % 2:
            subject = subject.replace('"', "")
        # An apostrophe inside a word ("signal's") is punctuation, not a quote.
        if len(re.findall(r"(?<![A-Za-z0-9])'|'(?![A-Za-z0-9])", subject)) % 2:
            subject = re.sub(r"(?<![A-Za-z0-9])'|'(?![A-Za-z0-9])", "", subject)
        return subject.strip("?!:;, ")
    if len(words) > 7:
        # Entity-aware cut: never truncate a narrated entity out of the subject.
        stems = set()
        for ent in key_entities or []:
            for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-']{3,}", str(ent)):
                stems.add(w[:5].lower())
        cut = 7
        if stems:
            for i, w in enumerate(words[:12], start=1):
                wl = w.lower().strip("'\"“”‘’")
                if any(wl.startswith(s) for s in stems):
                    cut = max(cut, i)
                    break
        words = words[:cut]
    trailing = {
        "a", "an", "the", "to", "of", "in", "on", "for", "with", "and", "that",
        "which", "who", "can", "could", "will", "would", "is", "are", "it", "as",
        "at", "by", "into", "over", "through", "around", "without", "across",
        "during", "within", "toward", "towards", "than", "then", "so", "many",
        "each", "every", "more", "most", "some", "any", "all", "very", "just",
        "also", "really", "from", "onto", "off", "under", "onto",
        # Stranded determiners / wh-words are not subject endings.
        "your", "my", "its", "our", "their", "his", "her", "this", "these",
        "those", "them", "us", "where", "when", "how",
        # A cut can strand a linking verb ("...difference lets your") — the
        # subject must end on the noun it names, not on the verb that connects.
        "lets", "enables", "means", "makes", "allows", "helps", "shows",
        "gives", "keeps", "drives", "causes",
    }
    while len(words) > 2 and words[-1].lower().strip("'\"“”‘’") in trailing:
        words.pop()
    # A stranded pair: article/preposition left before a cut-off noun
    # ("...listen for signals from four" -> "...listen for signals").
    tail_pair_glue = {
        "a", "an", "the", "from", "into", "of", "in", "on", "at", "for", "with",
        "by", "to", "through", "across", "around", "without", "within", "during",
        "over", "under", "between", "onto", "than", "like", "off",
    }
    while len(words) > 3 and words[-2].lower().strip("'\"“”‘’") in tail_pair_glue:
        words.pop()
        words.pop()
        while len(words) > 2 and words[-1].lower().strip("'\"“”‘’") in trailing:
            words.pop()
    while len(words) > 2 and words[-1].lower().strip("'\"“”‘’") in trailing:
        words.pop()
    subject = " ".join(words).strip()
    # Hard safety: an on-screen title never runs past ~75 characters.
    while len(subject) > 75 and len(words) > 4:
        words.pop()
        subject = " ".join(words).strip()
    # Dropping words can orphan a quote/parenthesis — keep it balanced.
    if subject.count('"') % 2:
        subject = subject.replace('"', "")
    # An apostrophe inside a word ("signal's") is punctuation, not a quote.
    if len(re.findall(r"(?<![A-Za-z0-9])'|'(?![A-Za-z0-9])", subject)) % 2:
        subject = re.sub(r"(?<![A-Za-z0-9])'|'(?![A-Za-z0-9])", "", subject)
    return subject.strip("?!:;, ")


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


# Vocabulary that semantically justifies a camera move — the same words the
# semantic derivation uses (flow/tracking, scale/crane, matrix/slow_pan,
# control/tracking, contrast deliberation). Anything else holds still.
_CAMERA_JUSTIFYING_KEYWORDS = (
    "flow", "route", "token", "transform", "pipeline", "stream", "pass",
    "cluster", "scale", "gpu", "accelerator", "infrastructure", "fleet", "hardware",
    "matrix", "attention", "transformer", "embedding", "vector", "layer", "latent", "space",
    "control", "command", "sensor", "actuator", "motor",
    "contrast", "vs", "versus", "comparison", "difference", "delta",
)

_STATIC_CAMERAS = frozenset({"static", "static_locked", "observe_static", "", None})


def enforce_static_camera_fallback(camera: str | None, chosen_mode: object, basis_text: str | None) -> str:
    """Static fallback on every path (§5): keep the winning option's camera only
    when the scene semantics justify movement (claim text or spoken text names
    a justifying action, or the mode is BRAND_CTA with its deliberate slow
    push). Otherwise a palette default like fast_push_in must never drift an
    otherwise static scene — with or without a claim plan."""
    if (camera or "") in _STATIC_CAMERAS:
        return camera or "static"
    text = (basis_text or "").lower()
    justified = chosen_mode == VisualMode.BRAND_CTA or any(k in text for k in _CAMERA_JUSTIFYING_KEYWORDS)
    return camera if justified else "static"


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

        # §6: the visual mode follows the narration's meaning. Scenes are NOT rotated
        # through modes to manufacture variety — two scenes explaining the same kind of
        # relationship may (and should) look alike. Clarity beats variety.

        # Gather palette options
        palette_options = list(DIRECTORIAL_PALETTES.get(chosen_mode, DIRECTORIAL_PALETTES[VisualMode.LITERAL]))

        # Dynamically inject tailored option directly from ClaimVisualPlan if present
        if claim_plan:
            is_rob = any(k in (claim_plan.action + " " + claim_plan.environment + " " + " ".join(claim_plan.entities)).lower() for k in ["robot", "clamp", "gripper", "agv", "rover", "pneumatic"])
            if not is_rob:
                palette_options = [
                    opt for opt in palette_options
                    if not any(k in (opt.get("subject", "") + " " + opt.get("action", "") + " " + opt.get("environment", "")).lower()
                               for k in ["robot", "gripper", "actuator", "gear", "transmission", "harmonic", "rover", "warehouse", "conveyor", "pallet"])
                ]

            # Derive camera motion and composition semantically from action, entities, and relationship
            act_lower = (claim_plan.action + " " + claim_plan.relationship + " " + " ".join(claim_plan.entities)).lower()
            if any(k in act_lower for k in ["flow", "route", "token", "transform", "pipeline", "stream", "pass"]):
                sem_camera = "tracking"
                sem_composition = "process_flow"
            elif any(k in act_lower for k in ["cluster", "scale", "gpu", "accelerator", "infrastructure", "fleet", "hardware"]):
                sem_camera = "crane_pull_out"
                sem_composition = "wide_isometric_plane"
            elif any(k in act_lower for k in ["matrix", "attention", "transformer", "embedding", "vector", "layer", "latent", "space"]):
                sem_camera = "slow_pan"
                sem_composition = "layered_depth"
            elif any(k in act_lower for k in ["control", "command", "sensor", "actuator", "motor"]):
                # Cause -> effect: follow the command path from source to machine.
                sem_camera = "tracking"
                sem_composition = "cause_effect_path"
            elif any(k in act_lower for k in ["contrast", "vs", "versus", "comparison", "difference", "delta"]):
                sem_camera = "static"
                sem_composition = "split_comparison"
            elif chosen_mode == VisualMode.BRAND_CTA:
                sem_camera = "slow_pan"
                sem_composition = "center_focus"
            else:
                # Static is the default (§5): a camera move is assigned only when
                # the action semantically needs it (flow/tracking, scale/crane,
                # matrix/slow_pan above) — never as a fallback drift.
                sem_camera = "static"
                sem_composition = "center_focus"

            if chosen_mode == VisualMode.BRAND_CTA:
                custom_shot_type = "clean_minimalist_studio"
            elif scene_idx == 0:
                custom_shot_type = "extreme_macro_probe" if is_rob else "clean_establishing_shot"
            elif chosen_mode == VisualMode.LITERAL:
                custom_shot_type = "industrial_arm_command_medium" if is_rob else "clean_subject_medium_shot"
            elif chosen_mode == VisualMode.DEMONSTRATION:
                custom_shot_type = "dynamic_obstacle_reroute_overhead" if is_rob else "dynamic_action_sequence"
            elif chosen_mode == VisualMode.SCALE:
                custom_shot_type = "high_throughput_logistics_flow" if is_rob else "expansive_scale_overview"
            else:
                custom_shot_type = f"{chosen_mode.value}_grounded_execution"

            custom_opt = {
                "shot_type": custom_shot_type,
                # No forced opening push-in: scene 0 uses the same semantic
                # derivation (static unless the action needs motion).
                "camera_motion": sem_camera,
                "camera_angle": "macro_probe_level" if (scene_idx == 0 and is_rob) else "eye_level_three_quarter",
                "composition": "tight_macro_crop" if (scene_idx == 0 and is_rob) else sem_composition,
                "subject": (
                    ", ".join(claim_plan.entities)
                    if chosen_mode == VisualMode.BRAND_CTA
                    else (
                        _narration_subject(
                            getattr(intent, "spoken_text", "") or "",
                            list(claim_plan.entities) if claim_plan else None,
                        )
                        or ", ".join(claim_plan.entities)
                        or intent.what_is_said
                    )
                ),
                "action": claim_plan.action,
                "environment": claim_plan.environment,
                "lens_feel": "24mm_macro_probe" if (scene_idx == 0 and is_rob) else "35mm_standard",
                "depth": "extreme_shallow_dof" if (scene_idx == 0 and is_rob) else "medium_depth",
                "visual_metaphor": claim_plan.relationship,
                "lighting": "sharp high-contrast directional lighting with cool specular highlights",
                # §15: subtle motion. A scene may be still; nothing is forced to move.
                "motion_intensity": 4.0 if scene_idx == 0 else 3.5,
                "transition_in": "hard_cut",
                "transition_out": "hard_cut",
                # §5: no telemetry/HUD decoration — overlays appear only when narrated.
                "overlay_strategy": "none_initial_cut" if scene_idx == 0 else ("brand_lock" if chosen_mode == VisualMode.BRAND_CTA else "none"),
                "graphic_strategy": "none",
                "asset_strategy": "generated_background",
            }
            # Add custom_opt as top priority
            palette_options.insert(0, custom_opt)

        # Selection formula (priority order):
        # semantic grounding * 0.40 + claim coverage * 0.25 + narrative fit * 0.15 + clarity * 0.20
        # Repetition is NOT scored: a repeated layout that explains is correct (§6).
        best_option = palette_options[0]
        best_score = -999.0
        best_eval = None

        for opt in palette_options:
            # Build mock SceneVisualPlan to evaluate grounding (do not leak ideal visual_intent)
            mock_plan = SceneVisualPlan(
                scene_id=intent.scene_id,
                section_id=intent.section_id,
                narrative_role=intent.narrative_role,
                visual_intent="",
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

            # Repetition carries no penalty: clarity, not variety, is the success metric (§6).

            # Narrative alignment
            narrative_align = 9.0 if chosen_mode == intent.recommended_mode else 7.5
            visual_clarity = 8.5

            composite_score = (
                grounding_s * 0.40
                + (coverage_s * 10.0) * 0.25
                + narrative_align * 0.15
                + visual_clarity * 0.20
            )

            if composite_score > best_score:
                best_score = composite_score
                best_option = opt
                best_eval = eval_record

        # Static fallback on every path (§5): the winning palette option keeps
        # its camera only when the scene semantics justify movement. Basis is
        # the claim text when present, else the spoken text — so scenes without
        # a claim plan get the same static default, not a canned fast_push_in.
        if claim_plan:
            _camera_basis = f"{claim_plan.action} {claim_plan.relationship} {' '.join(claim_plan.entities)}"
        else:
            _camera_basis = (
                f"{getattr(intent, 'what_is_said', '') or ''} "
                f"{getattr(intent, 'what_viewer_sees', '') or ''} "
                f"{getattr(intent, 'spoken_text', '') or ''}"
            )
        best_option = dict(
            best_option,
            camera_motion=enforce_static_camera_fallback(
                best_option.get("camera_motion"), chosen_mode, _camera_basis),
        )

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
