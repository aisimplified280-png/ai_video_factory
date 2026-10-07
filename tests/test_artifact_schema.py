"""Tests for JSON schema validation of artifact envelope and specific artifact schemas."""
import json
import pytest
from pathlib import Path
import jsonschema

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent / "schemas"
ENVELOPE_SCHEMA_PATH = SCHEMAS_ROOT / "artifact_envelope.schema.json"


@pytest.fixture(scope="module")
def envelope_schema():
    return json.loads(ENVELOPE_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_envelope_schema_validates_valid_envelope(envelope_schema):
    valid_envelope = {
        "artifact_type": "scene_plan",
        "schema_version": "2.0",
        "artifact_version": 1,
        "production_id": "proj_123",
        "stage": "scene_plan",
        "status": "ready",
        "created_at": "2026-10-05T14:00:00Z",
        "updated_at": "2026-10-05T14:00:00Z",
        "producer": {
            "kind": "llm",
            "provider": "gemini",
            "model": "gemini-2.0-flash"
        },
        "content_hash": "sha256:" + "0" * 64,
        "data": {"foo": "bar"}
    }
    jsonschema.validate(valid_envelope, envelope_schema)


@pytest.mark.parametrize("missing_field", [
    "artifact_type", "schema_version", "artifact_version", "production_id",
    "stage", "status", "created_at", "updated_at", "producer", "content_hash", "data"
])
def test_envelope_schema_rejects_missing_required_fields(envelope_schema, missing_field):
    envelope = {
        "artifact_type": "scene_plan",
        "schema_version": "2.0",
        "artifact_version": 1,
        "production_id": "proj_123",
        "stage": "scene_plan",
        "status": "ready",
        "created_at": "2026-10-05T14:00:00Z",
        "updated_at": "2026-10-05T14:00:00Z",
        "producer": {"kind": "system"},
        "content_hash": "sha256:" + "a" * 64,
        "data": {}
    }
    del envelope[missing_field]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(envelope, envelope_schema)


def test_envelope_schema_rejects_invalid_status(envelope_schema):
    envelope = {
        "artifact_type": "scene_plan",
        "schema_version": "2.0",
        "artifact_version": 1,
        "production_id": "proj_123",
        "stage": "scene_plan",
        "status": "invalid_status_value",
        "created_at": "2026-10-05T14:00:00Z",
        "updated_at": "2026-10-05T14:00:00Z",
        "producer": {"kind": "system"},
        "content_hash": "sha256:" + "a" * 64,
        "data": {}
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(envelope, envelope_schema)


def test_envelope_schema_rejects_malformed_hash(envelope_schema):
    envelope = {
        "artifact_type": "scene_plan",
        "schema_version": "2.0",
        "artifact_version": 1,
        "production_id": "proj_123",
        "stage": "scene_plan",
        "status": "ready",
        "created_at": "2026-10-05T14:00:00Z",
        "updated_at": "2026-10-05T14:00:00Z",
        "producer": {"kind": "system"},
        "content_hash": "md5:not_a_valid_sha256",
        "data": {}
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(envelope, envelope_schema)


def test_all_10_artifact_schemas_exist():
    expected_schemas = [
        "research_brief", "proposal_packet", "script", "art_direction",
        "scene_plan", "asset_manifest", "edit_decisions", "render_report",
        "review_report", "publish_log"
    ]
    artifacts_dir = SCHEMAS_ROOT / "artifacts"
    for name in expected_schemas:
        schema_path = artifacts_dir / f"{name}.schema.json"
        assert schema_path.exists(), f"Missing schema file: {schema_path}"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        assert "allOf" in data or "properties" in data
