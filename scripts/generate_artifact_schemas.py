"""Generate all artifact-specific JSON schemas for Phase 1.

Run: python scripts/generate_artifact_schemas.py
"""
import json
from pathlib import Path

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas" / "artifacts"
SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"

# ── Shared sub-schemas referenced inside data objects ──────────────────────

SCENE_REF = {
    "type": "object",
    "required": ["id"],
    "properties": {
        "id": {"type": "string"},
        "description": {"type": "string"}
    }
}

SOURCE_REF = {
    "type": "object",
    "required": ["title", "url"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "url": {"type": "string"},
        "summary": {"type": "string"},
        "retrieved_at": {"type": "string", "format": "date-time"}
    }
}


def make_artifact_schema(
    artifact_type: str,
    title: str,
    description: str,
    data_required: list[str],
    data_properties: dict,
    data_optional_properties: dict | None = None,
) -> dict:
    """Build a complete artifact schema that wraps the envelope + data contract."""
    data_props = dict(data_properties)
    if data_optional_properties:
        data_props.update(data_optional_properties)

    return {
        "$schema": SCHEMA_DRAFT,
        "$id": f"{artifact_type}.schema",
        "title": title,
        "description": description,
        "type": "object",
        "allOf": [
            {"$ref": "../artifact_envelope.schema.json"},
            {
                "properties": {
                    "artifact_type": {"const": artifact_type},
                    "schema_version": {"const": "2.0"},
                    "data": {
                        "type": "object",
                        "required": data_required,
                        "properties": data_props,
                        "description": f"Payload for {artifact_type}"
                    }
                },
                "required": ["artifact_type", "schema_version", "data"]
            }
        ]
    }


ARTIFACTS = {

    "research_brief": make_artifact_schema(
        artifact_type="research_brief",
        title="Research Brief",
        description="Factual research about the topic. Produced by the research stage before any creative work begins.",
        data_required=["topic", "audience", "sources", "facts", "angles_discovered"],
        data_properties={
            "topic": {"type": "string", "minLength": 3},
            "audience": {"type": "string", "minLength": 1},
            "sources": {
                "type": "array",
                "minItems": 1,
                "items": SOURCE_REF
            },
            "facts": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "minLength": 5}
            },
            "data_points": {
                "type": "array",
                "items": {"type": "string"}
            },
            "expert_views": {
                "type": "array",
                "items": {"type": "string"}
            },
            "audience_questions": {
                "type": "array",
                "items": {"type": "string"}
            },
            "angles_discovered": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "minLength": 5}
            },
            "content_landscape": {"type": "string"},
            "risks": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    ),

    "proposal_packet": make_artifact_schema(
        artifact_type="proposal_packet",
        title="Proposal Packet",
        description="2-3 genuinely different creative concepts. Renderer family and runtime are LOCKED at approval.",
        data_required=["concepts", "selected_concept_id"],
        data_properties={
            "concepts": {
                "type": "array",
                "minItems": 2,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "required": [
                        "concept_id", "hook", "audience_promise",
                        "narrative_structure", "visual_direction", "tone",
                        "target_duration", "renderer_family", "render_runtime",
                        "composition_mode"
                    ],
                    "properties": {
                        "concept_id": {"type": "string"},
                        "hook": {"type": "string", "minLength": 5},
                        "audience_promise": {"type": "string"},
                        "narrative_structure": {"type": "string"},
                        "visual_direction": {"type": "string"},
                        "tone": {"type": "string"},
                        "target_duration": {"type": "number", "minimum": 10},
                        "taste_profile": {"type": "string"},
                        "renderer_family": {
                            "type": "string",
                            "enum": ["explainer", "cinematic", "motion_graphics",
                                     "documentary", "screen_demo", "hybrid"]
                        },
                        "render_runtime": {
                            "type": "string",
                            "enum": ["remotion", "hyperframes", "ffmpeg_pil"]
                        },
                        "composition_mode": {
                            "type": "string",
                            "enum": ["templated", "atelier"]
                        },
                        "asset_strategy": {"type": "string"},
                        "estimated_cost": {"type": "number", "minimum": 0}
                    }
                }
            },
            "selected_concept_id": {
                "type": ["string", "null"],
                "description": "null until a concept is approved/selected"
            }
        }
    ),

    "script": make_artifact_schema(
        artifact_type="script",
        title="Script",
        description="Full narration script with timing, speaker direction, and visual cues.",
        data_required=["sections", "target_duration_seconds", "word_count"],
        data_properties={
            "sections": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["id", "spoken_text", "narrative_role"],
                    "properties": {
                        "id": {"type": "string"},
                        "spoken_text": {"type": "string", "minLength": 1},
                        "timestamp_start": {"type": ["number", "null"]},
                        "timestamp_end": {"type": ["number", "null"]},
                        "speaker_direction": {"type": "string"},
                        "pause_cues": {"type": "array", "items": {"type": "number"}},
                        "emphasis_cues": {"type": "array", "items": {"type": "string"}},
                        "visual_enhancement_cues": {"type": "string"},
                        "narrative_role": {
                            "type": "string",
                            "enum": ["hook", "problem", "process", "proof", "payoff", "cta", "transition"]
                        }
                    }
                }
            },
            "target_duration_seconds": {"type": "number", "minimum": 1},
            "estimated_duration_seconds": {"type": ["number", "null"]},
            "word_count": {"type": "integer", "minimum": 0},
            "breathing_room_seconds": {"type": ["number", "null"]},
            "vo_script_text": {"type": "string"}
        }
    ),

    "art_direction": make_artifact_schema(
        artifact_type="art_direction",
        title="Art Direction",
        description="Creative brief defining the visual identity and motion language for this specific production.",
        data_required=[
            "design_read", "visual_variance", "motion_intensity",
            "information_density", "palette_discipline",
            "typography_personality", "layout_language",
            "signature_device", "anti_patterns"
        ],
        data_properties={
            "design_read": {"type": "string", "minLength": 10},
            "visual_metaphor": {"type": "string"},
            "visual_variance": {"type": "integer", "minimum": 1, "maximum": 10},
            "motion_intensity": {"type": "integer", "minimum": 1, "maximum": 10},
            "information_density": {"type": "integer", "minimum": 1, "maximum": 10},
            "palette_discipline": {
                "type": "object",
                "required": ["primary", "accent_1"],
                "properties": {
                    "primary": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
                    "accent_1": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
                    "accent_2": {"type": ["string", "null"]},
                    "neutral": {"type": ["string", "null"]},
                    "warning": {"type": ["string", "null"]}
                }
            },
            "typography_personality": {"type": "string", "minLength": 5},
            "layout_language": {"type": "string", "minLength": 5},
            "texture_language": {"type": "string"},
            "transition_language": {"type": "string"},
            "reference_strategy": {"type": "string"},
            "signature_device": {"type": "string", "minLength": 3},
            "anti_patterns": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string"}
            },
            "quality_gates": {"type": "object"}
        }
    ),

    "scene_plan": make_artifact_schema(
        artifact_type="scene_plan",
        title="Scene Plan",
        description="Semantic scene-by-scene plan. Every field maps to an executable output.",
        data_required=["scenes", "total_duration_seconds", "variety_score"],
        data_properties={
            "scenes": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": [
                        "id", "type", "start_seconds", "end_seconds",
                        "shot_intent", "narrative_role", "subject",
                        "required_assets"
                    ],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": [
                                "talking_head", "broll", "animation",
                                "character_scene", "diagram", "text_card",
                                "transition", "generated", "screen_recording"
                            ]
                        },
                        "start_seconds": {"type": "number", "minimum": 0},
                        "end_seconds": {"type": "number", "minimum": 0},
                        "script_section_id": {"type": ["string", "null"]},
                        "description": {"type": "string"},
                        "shot_intent": {"type": "string", "minLength": 5},
                        "narrative_role": {"type": "string"},
                        "information_role": {"type": "string"},
                        "subject": {"type": "string", "minLength": 1},
                        "subject_action": {"type": "string"},
                        "environment": {"type": "string"},
                        "composition": {"type": "string"},
                        "camera": {"type": "object"},
                        "motion": {"type": "object"},
                        "animation_sequence": {"type": "array"},
                        "transition_in": {"type": "string"},
                        "transition_out": {"type": "string"},
                        "overlays": {"type": "array"},
                        "captions": {"type": "object"},
                        "required_assets": {"type": "array"},
                        "texture_keywords": {"type": "array", "items": {"type": "string"}},
                        "reference_strategy": {"type": "string"}
                    }
                }
            },
            "total_duration_seconds": {"type": "number", "minimum": 1},
            "variety_score": {"type": "number", "minimum": 0, "maximum": 100},
            "scene_type_distribution": {"type": "object"},
            "technique_usage": {"type": "object"}
        }
    ),

    "asset_manifest": make_artifact_schema(
        artifact_type="asset_manifest",
        title="Asset Manifest",
        description="Every planned asset with its purpose, provider, and fallback chain.",
        data_required=["assets", "total_estimated_cost"],
        data_properties={
            "assets": {
                "type": "array",
                "minItems": 0,
                "items": {
                    "type": "object",
                    "required": ["asset_id", "scene_id", "purpose", "type", "source", "status"],
                    "properties": {
                        "asset_id": {"type": "string"},
                        "scene_id": {"type": "string"},
                        "purpose": {"type": "string", "minLength": 5},
                        "type": {
                            "type": "string",
                            "enum": ["image", "video", "diagram", "chart", "code",
                                     "screenshot", "logo", "icon", "music", "voice",
                                     "sfx", "background", "animation"]
                        },
                        "source": {
                            "type": "string",
                            "enum": ["generated", "stock", "native", "local", "remote"]
                        },
                        "provider": {"type": ["string", "null"]},
                        "model": {"type": ["string", "null"]},
                        "prompt": {"type": ["string", "null"]},
                        "negative_prompt": {"type": ["string", "null"]},
                        "reference_assets": {"type": "array"},
                        "expected_duration": {"type": ["number", "null"]},
                        "quality_requirements": {"type": "object"},
                        "fallback_chain": {"type": "array", "items": {"type": "string"}},
                        "file_path": {"type": ["string", "null"]},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "generating", "ready", "failed"]
                        },
                        "cost_usd": {"type": ["number", "null"]}
                    }
                }
            },
            "total_estimated_cost": {"type": "number", "minimum": 0}
        }
    ),

    "edit_decisions": make_artifact_schema(
        artifact_type="edit_decisions",
        title="Edit Decisions",
        description="Complete timeline contract. The composition runtime executes this exactly.",
        data_required=[
            "total_duration", "platform_profile",
            "render_runtime", "renderer_family", "composition_mode", "tracks"
        ],
        data_properties={
            "total_duration": {"type": "number", "minimum": 1},
            "platform_profile": {"type": "string"},
            "render_runtime": {"type": "string", "enum": ["remotion", "hyperframes", "ffmpeg_pil"]},
            "renderer_family": {"type": "string"},
            "composition_mode": {"type": "string", "enum": ["templated", "atelier"]},
            "tracks": {
                "type": "object",
                "required": ["video"],
                "properties": {
                    "video": {"type": "array"},
                    "narration": {"type": "array"},
                    "music": {"type": "array"},
                    "captions": {"type": "array"},
                    "sfx": {"type": "array"}
                }
            },
            "validation": {
                "type": "object",
                "properties": {
                    "no_gaps": {"type": "boolean"},
                    "no_overlaps": {"type": "boolean"},
                    "all_assets_resolved": {"type": "boolean"},
                    "duration_covered": {"type": "boolean"},
                    "audio_valid": {"type": "boolean"},
                    "captions_valid": {"type": "boolean"},
                    "cta_present": {"type": "boolean"},
                    "renderer_locked": {"type": "boolean"}
                }
            }
        }
    ),

    "render_report": make_artifact_schema(
        artifact_type="render_report",
        title="Render Report",
        description="Output of the composition stage. Records what was actually rendered.",
        data_required=["final_video_path", "duration_rendered", "scenes_rendered"],
        data_properties={
            "final_video_path": {"type": "string"},
            "duration_rendered": {"type": "number", "minimum": 0},
            "scenes_rendered": {"type": "integer", "minimum": 0},
            "render_runtime_used": {"type": "string"},
            "codec": {"type": "string"},
            "resolution": {"type": "string"},
            "fps": {"type": "number"},
            "file_size_bytes": {"type": ["integer", "null"]},
            "render_duration_seconds": {"type": ["number", "null"]},
            "scene_reports": {"type": "array"},
            "errors": {"type": "array"},
            "warnings": {"type": "array"}
        }
    ),

    "review_report": make_artifact_schema(
        artifact_type="review_report",
        title="Review Report",
        description="Structured findings from stage review. Every finding must cite evidence.",
        data_required=["reviewed_stage", "reviewed_artifact_type", "status", "findings"],
        data_properties={
            "reviewed_stage": {"type": "string"},
            "reviewed_artifact_type": {"type": "string"},
            "reviewed_artifact_version": {"type": "integer", "minimum": 1},
            "status": {
                "type": "string",
                "enum": ["approved", "rejected", "warning"]
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["finding", "evidence", "severity"],
                    "properties": {
                        "finding": {"type": "string", "minLength": 5},
                        "evidence": {"type": "string", "minLength": 5},
                        "severity": {
                            "type": "string",
                            "enum": ["info", "warning", "error", "critical"]
                        },
                        "impact": {"type": "string"},
                        "recommended_correction": {"type": "string"}
                    }
                }
            },
            "auto_approved": {"type": "boolean"},
            "reviewer": {"type": "string"}
        }
    ),

    "publish_log": make_artifact_schema(
        artifact_type="publish_log",
        title="Publish Log",
        description="Record of what was published and where.",
        data_required=["final_video_path", "published_at"],
        data_properties={
            "final_video_path": {"type": "string"},
            "published_at": {"type": "string", "format": "date-time"},
            "platform": {"type": "string"},
            "upload_url": {"type": ["string", "null"]},
            "title": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "tags": {"type": "array", "items": {"type": "string"}},
            "thumbnail_path": {"type": ["string", "null"]},
            "status": {
                "type": "string",
                "enum": ["draft", "uploaded", "published", "failed"]
            },
            "errors": {"type": "array"}
        }
    ),
}


def write_schemas() -> None:
    for name, schema in ARTIFACTS.items():
        path = SCHEMAS_DIR / f"{name}.schema.json"
        path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        print(f"  wrote {path.name}")


if __name__ == "__main__":
    write_schemas()
    print(f"\nAll {len(ARTIFACTS)} artifact schemas written to {SCHEMAS_DIR}")
