"""Integration test for end-to-end Phase 3 + Phase 4 stages via ProductionController."""
import pytest
from pathlib import Path

from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind
from production.artifact_store import ArtifactStore
from production.controller import ProductionController
from production.pipeline_loader import PipelineLoader
from production.stage_registry import StageRegistry, register_phase3_handlers, register_phase4_handlers
from stages.research.research_director import ResearchHandler
from stages.research.source_collector import DirectUrlSourceProvider, MockSourceProvider, SourceRecord
from stages.proposal.proposal_director import ProposalHandler
from stages.art_direction.art_direction_director import ArtDirectionHandler
from stages.script.script_director import ScriptHandler
from stages.scene_plan.scene_planner import ScenePlanHandler


@pytest.fixture
def clean_workspace(tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_full_pipeline_through_scene_plan(clean_workspace):
    # Setup custom deterministic registry with fake LLMs for test
    registry = StageRegistry()

    # Deterministic LLM response mocks
    def fake_research_llm(prompt, system=""):
        return {
            "topic": "How OpenAI Built An Empire",
            "audience": "Developers and AI builders",
            "content_landscape": "Overview of company transformation from small research lab to global platform.",
            "facts": [
                {"claim": "OpenAI began in 2015 as a non-profit artificial intelligence research laboratory.", "source_ids": ["src_001"], "confidence": 0.99},
                {"claim": "The release of ChatGPT in late 2022 catalyzed mass-market generative AI adoption.", "source_ids": ["src_002"], "confidence": 0.98},
                {"claim": "Scaling model compute requirements transitioned OpenAI into commercial cloud partnerships.", "source_ids": ["src_003"], "confidence": 0.95},
            ],
            "data_points": ["User growth reached 100M weekly active users in record time"],
            "expert_views": ["Compute scale drove capability leaps."],
            "audience_questions": ["How did a research lab become commercial infrastructure?"],
            "angles_discovered": [
                "Small laboratory expanding into global infrastructure",
                "From academic non-profit to commercial cloud infrastructure",
            ],
            "risks": ["Compute capital bottlenecks"],
        }, "mock_prov", "mock_model", 300

    def fake_proposal_llm(prompt, system=""):
        return {
            "concepts": [
                {
                    "concept_id": "concept_01",
                    "title": "Industrial Laboratory to Empire",
                    "hook": "OpenAI didn't build an empire with algorithms; they built it with infrastructure.",
                    "audience_promise": "Understand how physical compute power created a platform empire.",
                    "narrative_structure": "hook -> origin -> breakthrough -> expansion -> cta",
                    "visual_direction": "High-contrast technical documentary with physical architectural metaphors.",
                    "visual_metaphor": "small laboratory expanding into global infrastructure",
                    "tone": "cinematic and analytical",
                    "pacing": "progressive acceleration",
                    "scene_grammar": "macro environment shots transitioning to global network maps",
                    "renderer_family": "explainer",
                    "render_runtime": "remotion",
                    "composition_mode": "atelier",
                    "asset_strategy": "generated video environments and telemetry overlays",
                    "target_duration": 45.0,
                    "reasoning": "Strong match for corporate transformation.",
                },
                {
                    "concept_id": "concept_02",
                    "title": "Historical Timeline Archive",
                    "hook": "In 2015, a small group of researchers made a bet that broke the internet.",
                    "audience_promise": "See the documentary timeline of unexpected viral AI expansion.",
                    "narrative_structure": "timeline -> archive -> evidence -> cta",
                    "visual_direction": "Documentary archival style with historic records and documents.",
                    "visual_metaphor": "historical timeline expanding across geographic maps",
                    "tone": "documentary",
                    "pacing": "measured documentary",
                    "scene_grammar": "document stacks and archival footage",
                    "renderer_family": "documentary",
                    "render_runtime": "ffmpeg_pil",
                    "composition_mode": "templated",
                    "asset_strategy": "archival screenshots",
                    "target_duration": 45.0,
                    "reasoning": "Documentary archival approach.",
                },
            ]
        }, "mock_prov", "mock_model", 400

    def fake_art_llm(prompt, system=""):
        return {
            "design_read": "High-contrast technical documentary with physical architectural metaphors.",
            "visual_metaphor": "small laboratory expanding into global infrastructure",
            "visual_variance": 8,
            "motion_intensity": 7,
            "information_density": 6,
            "signature_device": "Persistent telemetry thread",
            "typography_personality": "Monospace metric labels paired with bold geometric headlines",
            "layout_language": "Asymmetric technical grid with directional flow lines",
            "texture_language": "Subtle matte finish with 5% fine grain",
            "transition_language": "Directional whip-pans and snap zoom cuts",
            "reference_strategy": "Bloomberg telemetry monitors meet technical schematics",
            "anti_patterns": [
                "no floating cards every scene",
                "no text-only explanation without visual anchor",
                "no identical centered hero",
            ],
            "palette_discipline": {
                "primary": "#0A0D14",
                "secondary": "#1E2638",
                "accent_1": "#00FF88",
                "accent_2": "#00CCFF",
                "text": "#F0F4FC",
                "mood": "industrial technical",
            },
        }, "mock_prov", "mock_model", 350

    def fake_script_llm(prompt, system=""):
        return {
            "title": "How OpenAI Built An Empire",
            "hook": "OpenAI did not conquer tech with code alone—they did it by industrializing research.",
            "target_duration_seconds": 45.0,
            "sections": [
                {
                    "section_id": "sec_01",
                    "narrative_role": "hook",
                    "spoken_text": "OpenAI did not conquer tech with code alone—they did it by industrializing research.",
                    "emphasis_words": ["INDUSTRIALIZING"],
                    "visual_intent": "Cold open on a small quiet research lab bench before explosive server rack expansion.",
                    "primary_intent": "reveal",
                    "secondary_intents": ["show_scale"],
                    "primary_subject": "OpenAI expansion",
                    "entities": ["OpenAI"],
                },
                {
                    "section_id": "sec_02",
                    "narrative_role": "mechanism",
                    "spoken_text": "In 2015, they started as a tiny non-profit, but soon realized transformer models eat exponential compute.",
                    "emphasis_words": ["EXPONENTIAL"],
                    "visual_intent": "Research papers stacking rapidly into blueprints for massive server architecture.",
                    "primary_intent": "show_history",
                    "secondary_intents": ["show_scale"],
                    "primary_subject": "Transformer compute",
                    "entities": ["Transformer models"],
                },
                {
                    "section_id": "sec_03",
                    "narrative_role": "evidence",
                    "spoken_text": "They traded non-profit purity for billions in cloud compute, turning academic hypotheses into ChatGPT.",
                    "emphasis_words": ["BILLIONS"],
                    "visual_intent": "Cloud infrastructure blades locking together as global traffic surges across network lines.",
                    "primary_intent": "show_evidence",
                    "secondary_intents": ["show_process"],
                    "primary_subject": "Cloud compute",
                    "entities": ["ChatGPT", "Cloud infrastructure"],
                },
                {
                    "section_id": "sec_04",
                    "narrative_role": "payoff",
                    "spoken_text": "The result is no longer just a research lab; it is the operating system for global AI.",
                    "emphasis_words": ["OPERATING"],
                    "visual_intent": "Worldwide telemetry map showing millions of simultaneous API calls.",
                    "primary_intent": "explain",
                    "secondary_intents": ["show_scale"],
                    "primary_subject": "Global AI OS",
                    "entities": ["Operating system"],
                },
                {
                    "section_id": "sec_05",
                    "narrative_role": "cta",
                    "spoken_text": "Subscribe to AI Simplified Lab for more breakdowns like this.",
                    "emphasis_words": ["SUBSCRIBE"],
                    "visual_intent": "Channel brand signature mark with kinetic subscriber trigger.",
                    "primary_intent": "conclude",
                    "secondary_intents": [],
                    "primary_subject": "Channel identity",
                    "entities": ["AI Simplified Lab"],
                },
            ],
        }, "mock_prov", "mock_model", 450

    def fake_scene_llm(prompt, system=""):
        return {
            "scenes": [
                {
                    "scene_id": "scene_01",
                    "type": "animation",
                    "script_section_id": "sec_01",
                    "start_seconds": 0.0,
                    "end_seconds": 7.0,
                    "narrative_role": "hook",
                    "information_role": "reveal",
                    "viewer_understanding": "Viewer feels the contrast between a quiet startup office and industrial compute infrastructure.",
                    "visual_purpose": "establish scale",
                    "visual_metaphor": "small laboratory expanding into global infrastructure",
                    "subject": "Research lab origins",
                    "subject_action": "Desk lamps dimming as massive electrical cables lead outward",
                    "environment": "Dim startup laboratory",
                    "composition_intent": "wide isometric landscape",
                    "camera_intent": "reveal_space",
                    "motion_intent": "emerge",
                    "visual_technique": "scale_transition",
                },
                {
                    "scene_id": "scene_02",
                    "type": "diagram",
                    "script_section_id": "sec_02",
                    "start_seconds": 7.0,
                    "end_seconds": 18.0,
                    "narrative_role": "mechanism",
                    "information_role": "show_history",
                    "viewer_understanding": "Viewer sees documents and model papers evolving into physical server infrastructure blueprints.",
                    "visual_purpose": "show mechanism",
                    "visual_metaphor": "small laboratory expanding into global infrastructure",
                    "subject": "Architecture blueprints",
                    "subject_action": "Research papers stacking into volumetric server chassis",
                    "environment": "Technical drafting plane",
                    "composition_intent": "split-screen dynamic",
                    "camera_intent": "approach_subject",
                    "motion_intent": "assemble",
                    "visual_technique": "timeline_progression",
                },
                {
                    "scene_id": "scene_03",
                    "type": "broll",
                    "script_section_id": "sec_03",
                    "start_seconds": 18.0,
                    "end_seconds": 30.0,
                    "narrative_role": "evidence",
                    "information_role": "show_evidence",
                    "viewer_understanding": "Viewer connects commercial cloud funding directly to row upon row of humming server blades.",
                    "visual_purpose": "provide evidence",
                    "visual_metaphor": "small laboratory expanding into global infrastructure",
                    "subject": "Hyperscale cloud clusters",
                    "subject_action": "Server blade racks locking together under intense operational telemetry",
                    "environment": "Hyperscale data facility",
                    "composition_intent": "macro focal detail",
                    "camera_intent": "shift_focus",
                    "motion_intent": "flow",
                    "visual_technique": "evidence_wall",
                },
                {
                    "scene_id": "scene_04",
                    "type": "generated",
                    "script_section_id": "sec_04",
                    "start_seconds": 30.0,
                    "end_seconds": 40.0,
                    "narrative_role": "payoff",
                    "information_role": "explain",
                    "viewer_understanding": "Viewer sees the company as the backbone infrastructure connecting global products and users.",
                    "visual_purpose": "reveal consequence",
                    "visual_metaphor": "small laboratory expanding into global infrastructure",
                    "subject": "Worldwide AI network",
                    "subject_action": "Pulsing network nodes linking millions of global consumer devices",
                    "environment": "Planetary data visualization",
                    "composition_intent": "asymmetrical network view",
                    "camera_intent": "expand_scale",
                    "motion_intent": "connect",
                    "visual_technique": "network_build",
                },
                {
                    "scene_id": "scene_05",
                    "type": "text_card",
                    "script_section_id": "sec_05",
                    "start_seconds": 40.0,
                    "end_seconds": 45.0,
                    "narrative_role": "cta",
                    "information_role": "conclude",
                    "viewer_understanding": "Viewer knows how to continue following the channel and subscribe.",
                    "visual_purpose": "Convert attention into subscription.",
                    "visual_metaphor": "small laboratory expanding into global infrastructure",
                    "subject": "AI Simplified Lab Brand Identity",
                    "subject_action": "Brand mark assembly and subscriber action trigger",
                    "environment": "Branded studio space",
                    "composition_intent": "centered brand focus",
                    "camera_intent": "expand_scale",
                    "motion_intent": "pulse",
                    "visual_technique": "kinetic_typography",
                },
            ]
        }, "mock_prov", "mock_model", 550

    mock_sources = [
        SourceRecord(
            source_id="src_01",
            title="OpenAI Corporate History",
            url="https://openai.com/research/history",
            domain="openai.com",
            published_at="2024-01-15T00:00:00Z",
            source_type="official_announcement",
            content_excerpt="OpenAI transitioned from non-profit lab to hyperscale AI powerhouse.",
            relevance_score=0.95,
        ),
        SourceRecord(
            source_id="src_02",
            title="Scaling Compute Architectures",
            url="https://arxiv.org/abs/1706.03762",
            domain="arxiv.org",
            published_at="2024-03-20T00:00:00Z",
            source_type="documentation",
            content_excerpt="Compute clusters now scale to tens of thousands of GPUs.",
            relevance_score=0.92,
        ),
        SourceRecord(
            source_id="src_03",
            title="ChatGPT Launch Analysis",
            url="https://techcrunch.com/2023/03/14/gpt-4",
            domain="techcrunch.com",
            published_at="2024-06-10T00:00:00Z",
            source_type="reputable_publication",
            content_excerpt="Consumer adoption catalyzed global enterprise cloud contracts.",
            relevance_score=0.90,
        ),
    ]
    source_provider = MockSourceProvider(mock_sources)

    # Register handlers
    registry.register("research", ResearchHandler(source_provider=source_provider, llm_caller=fake_research_llm))
    registry.register("proposal", ProposalHandler(llm_caller=fake_proposal_llm))
    registry.register("art_direction", ArtDirectionHandler(llm_caller=fake_art_llm))
    registry.register("script", ScriptHandler(llm_caller=fake_script_llm))
    registry.register("scene_plan", ScenePlanHandler(llm_caller=fake_scene_llm))

    controller = ProductionController(
        projects_root=clean_workspace / "projects",
        registry=registry,
    )
    store = controller.artifact_store

    # 1. Start production
    state = controller.start(
        topic="How OpenAI Built An Empire",
        pipeline="youtube-short",
    )
    pid = state.project_id

    # 2. Run research
    res_res = controller.run_stage(pid, "research")
    assert res_res.status.value == "ready", f"Research failed: {res_res.message} - {res_res.errors}"

    # 3. Run proposal
    res_prop = controller.run_stage(pid, "proposal")
    assert res_prop.status.value in ("ready", "waiting_approval")
    if res_prop.status.value == "waiting_approval":
        controller.approve(pid, stage_name="proposal")

    # 4. Run art direction
    res_art = controller.run_stage(pid, "art_direction")
    assert res_art.status.value in ("ready", "waiting_approval")
    if res_art.status.value == "waiting_approval":
        controller.approve(pid, stage_name="art_direction")

    # 5. Run script
    res_script = controller.run_stage(pid, "script")
    assert res_script.status.value in ("ready", "waiting_approval")
    if res_script.status.value == "waiting_approval":
        controller.approve(pid, stage_name="script")

    # 6. Run scene plan
    res_sp = controller.run_stage(pid, "scene_plan")
    assert res_sp.status.value in ("ready", "waiting_approval")
    if res_sp.status.value == "waiting_approval":
        controller.approve(pid, stage_name="scene_plan")

    # Verify all 5 artifacts exist in ArtifactStore
    for atype in ["research_brief", "proposal_packet", "art_direction", "script", "scene_plan"]:
        envelope = store.latest(atype, pid)
        assert envelope is not None
        assert envelope.artifact_type == atype
        assert envelope.data is not None
        assert envelope.content_hash.startswith("sha256:")

    # Verify scene plan details
    sp_envelope = store.latest("scene_plan", pid)
    assert len(sp_envelope.data["scenes"]) == 5
    assert sp_envelope.data["scenes"][-1]["narrative_role"] == "cta"
    assert sp_envelope.data["variety_score"] >= 70.0
