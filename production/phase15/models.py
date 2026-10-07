"""Pydantic models for Phase 15/15B Visual Intelligence, Grounding & Diversity Engine."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class VisualMode(str, Enum):
    """The 15 canonical visual modes defining scene intent."""
    LITERAL = "literal"                        # Direct mechanical / physical execution
    DEMONSTRATION = "demonstration"            # Dynamic choreography showing how tech works
    MECHANISM = "mechanism"                    # Internal workings, sub-components, gears, optics
    METAPHOR = "metaphor"                      # Non-literal conceptual bridge (thought into action)
    ENVIRONMENT = "environment"                # Establishing world, architectural scale, atmosphere
    DETAIL = "detail"                          # Macro close-up, tactile micro-interaction
    HUMAN_IMPACT = "human_impact"              # Human operator, worker, consumer consequence
    SCALE = "scale"                            # Massive fleet, planetary infrastructure, high volume
    ABSTRACT = "abstract"                      # Mathematical tensors, latent vectors, data void
    DATA_VISUALIZATION = "data_visualization"  # Graphs, performance curves, metric deltas
    INTERFACE = "interface"                    # UI/UX telemetry, terminal readouts, HUD crosshairs
    COMPARISON = "comparison"                  # Side-by-side or before/after contrast
    TRANSFORMATION = "transformation"          # State A mutating rapidly into State B
    CONSEQUENCE = "consequence"                # Direct downstream fallout or bottleneck relief
    BRAND_CTA = "brand_cta"                    # Clean branded resolution with minimal clutter
    DATA_INTERFACE = "data_interface"          # Backward compatibility alias for interface


class ClaimType(str, Enum):
    """Canonical factual claim classification (Phase 15B Step 3)."""
    PRODUCT_LAUNCH = "product_launch"
    CAPABILITY = "capability"                  # AI system controls physical machine
    DEMONSTRATION = "demonstration"            # Real-world dynamic execution
    MECHANISM = "mechanism"                    # Technical inner working / feedback loop
    BENCHMARK = "benchmark"                    # Numerical / latency performance metric
    EVENT = "event"                            # Specific occurrence or news event
    COMPANY_ACTION = "company_action"          # Corporate announcement, deployment
    HUMAN_REACTION = "human_reaction"          # Workforce reaction, operator interaction
    BUSINESS_IMPACT = "business_impact"        # Throughput increase, delay reduction, economic change
    TECHNICAL_CHANGE = "technical_change"      # Sensor upgrade, architectural shift
    COMPARISON = "comparison"                  # Legacy fixed routines vs dynamic adaptation
    PREDICTION = "prediction"                  # Future frontier trajectory
    CONSEQUENCE = "consequence"                # Direct downstream result
    ABSTRACT_CONCEPT = "abstract_concept"      # Foundational theory
    BRAND_CALLOUT = "brand_callout"            # Channel branding, subscribe callout


class GroundingLevel(float, Enum):
    """Visual evidence levels (Phase 15B Step 7)."""
    LEVEL_4 = 4.0  # Direct evidence: literally demonstrates the claim
    LEVEL_3 = 3.0  # Strong illustrative evidence: clearly depicts mechanism / action
    LEVEL_2 = 2.0  # Conceptual representation: communicates concept (allowed only if literal impossible)
    LEVEL_1 = 1.0  # Generic topical imagery: merely related to topic (FAILS QA)
    LEVEL_0 = 0.0  # Unrelated: REJECT


class ClaimVisualPlan(BaseModel):
    """Intermediate Claim-to-Visual Grounding representation (Phase 15B Step 2)."""
    claim_id: str
    section_id: str = ""
    scene_id: str = ""
    narration_text: str
    claim_type: ClaimType = ClaimType.CAPABILITY
    entities: list[str] = Field(default_factory=list)               # Preserved named entities
    action: str = ""                                               # Required physical / technical action
    object: str = ""                                               # Physical recipient of action
    environment: str = ""                                          # Required real-world context
    relationship: str = ""                                         # e.g. "AI controls physical machine"
    required_visual_evidence: list[str] = Field(default_factory=list) # Minimum elements that MUST appear
    preferred_visualization: str = ""
    acceptable_alternatives: list[str] = Field(default_factory=list)
    unacceptable_visuals: list[str] = Field(default_factory=list)   # Negative constraints / clichés to forbid
    grounding_level: float = 3.0                                   # Target evidence level (0.0 - 4.0)

    class Config:
        extra = "allow"


class SceneClaimQAEvaluation(BaseModel):
    """Scene-by-scene claim QA audit record (Phase 15B Step 20)."""
    scene_id: str
    narration: str
    claim: str
    claim_type: str
    required_evidence: list[str] = Field(default_factory=list)
    detected_evidence: list[str] = Field(default_factory=list)
    claim_coverage: float = 1.0                   # detected / required (must be >= 0.8)
    visual_grounding_score: float = 8.5          # 0 - 10 (must be >= 7.0)
    entity_match: bool = True                     # PASS/FAIL
    action_match: bool = True                     # PASS/FAIL
    relationship_match: bool = True               # PASS/FAIL
    contradiction_detected: bool = False          # False = PASS
    rejection_reasons: list[str] = Field(default_factory=list)
    decision: str = "PASS"                        # PASS / REJECT


class SceneVisualPlan(BaseModel):
    """Canonical 22-field structured scene specification + Claim Grounding integration."""
    scene_id: str
    section_id: str = ""
    narrative_role: str = "context"
    visual_intent: str = ""
    visual_mode: VisualMode = VisualMode.LITERAL
    subject: str = ""
    action: str = ""
    environment: str = ""
    shot_type: str = "medium"
    camera_angle: str = "eye_level"
    camera_motion: str = "push_in"
    lens_feel: str = "35mm_anamorphic"
    composition: str = "rule_of_thirds"
    depth: str = "shallow_dof"
    lighting: str = "natural_high_contrast"
    motion_intensity: float = 6.0
    transition_in: str = "hard_cut"
    transition_out: str = "hard_cut"
    overlay_strategy: str = "minimal_callout"
    graphic_strategy: str = "none"
    asset_strategy: str = "generated_background"
    visual_prompt: str = ""
    negative_constraints: list[str] = Field(default_factory=list)
    avoid_repetition: list[str] = Field(default_factory=list)

    # Phase 15B Grounding Additions
    claim_plan: Optional[ClaimVisualPlan] = None
    claim_id: str = ""
    claim_type: str = ""
    entities: list[str] = Field(default_factory=list)
    relationship: str = ""
    required_visual_evidence: list[str] = Field(default_factory=list)
    unacceptable_visuals: list[str] = Field(default_factory=list)
    grounding_level: float = 3.0
    visual_grounding_score: float = 8.5
    claim_coverage_score: float = 1.0

    # Backward compatibility aliases
    visual_metaphor: str = ""
    motion_intent: str = "reveal"
    overlay_intent: str = "none"
    background_prompt: str = ""
    camera_movement: str = ""
    subject_action: str = ""
    scene_breakdown: dict[str, str] = Field(default_factory=dict)

    class Config:
        extra = "allow"

    def model_post_init(self, __context: Any) -> None:
        if not self.action and self.subject_action:
            self.action = self.subject_action
        if not self.subject_action and self.action:
            self.subject_action = self.action

        if not self.camera_movement and self.camera_motion:
            self.camera_movement = self.camera_motion
        if not self.camera_motion and self.camera_movement:
            self.camera_motion = self.camera_movement

        if not self.background_prompt and self.visual_prompt:
            self.background_prompt = self.visual_prompt
        if not self.visual_prompt and self.background_prompt:
            self.visual_prompt = self.background_prompt

        if not self.overlay_strategy and self.overlay_intent:
            self.overlay_strategy = self.overlay_intent


class VisualScorecard(BaseModel):
    """Rigorous 10-point visual direction, grounding & diversity evaluation rubric."""
    visual_relevance: float = 0.0          # 0 - 10: does imagery faithfully express script semantics?
    visual_grounding: float = 0.0          # 0 - 10: factual claim grounding score (must be >= 7.0)
    claim_coverage: float = 0.0            # 0.0 - 1.0: fraction of required evidence present (must be >= 0.8)
    visual_diversity: float = 0.0          # 0 - 10: unique environments, shot scales, palettes
    shot_diversity: float = 0.0            # 0 - 10: variance across shot types
    camera_diversity: float = 0.0          # 0 - 10: camera movements and perspective angles
    composition_diversity: float = 0.0     # 0 - 10: framing variance
    motion_diversity: float = 0.0          # 0 - 10: dynamic pace variance
    narrative_alignment: float = 0.0       # 0 - 10: emotional and technical sync with spoken narration
    visual_novelty: float = 0.0            # 0 - 10: freedom from clichés
    text_restraint: float = 0.0            # 0 - 10: restraint against excessive text cards
    overall_visual_direction: float = 0.0  # 0 - 10: composite directorial quality score
    entity_match_rate: float = 1.0         # 0.0 - 1.0
    action_match_rate: float = 1.0         # 0.0 - 1.0
    relationship_match_rate: float = 1.0   # 0.0 - 1.0
    contradiction_count: int = 0           # Must be 0
    passed: bool = False                   # True only if grounding >= 7.0, coverage >= 0.8, diversity >= 6.5
    rejection_reason: Optional[str] = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    scene_evaluations: list[SceneClaimQAEvaluation] = Field(default_factory=list)
