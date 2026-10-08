"""Regression tests for Issue #10: Remote Remotion worker workflow."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from composition.remotion.renderer import package_remote_bundle, REMOTE_BUNDLE_VERSION, validate_worker_result
from scripts.remotion_worker import canonical_hash


def test_colab_worker_notebook_exists_and_valid():
    """Verify colab/remotion_worker.ipynb exists, has valid structure, and references remotion_worker.py."""
    nb_path = ROOT / "colab" / "remotion_worker.ipynb"
    assert nb_path.is_file(), "colab/remotion_worker.ipynb must exist in repository"

    nb_data = json.loads(nb_path.read_text(encoding="utf-8"))
    assert "cells" in nb_data
    assert len(nb_data["cells"]) >= 5

    # Verify code cells reference the worker script and remote-job workflow
    all_code = "\n".join("".join(c.get("source", [])) for c in nb_data["cells"] if c.get("cell_type") == "code")
    assert "remotion_worker.py" in all_code
    assert "--bundle" in all_code
    assert "worker_result.json" in all_code


def test_remote_bundle_package_and_worker_dry_run(tmp_path):
    """Verify package_remote_bundle creates a valid bundle that remotion_worker.py can consume."""
    edit_decisions = {"test": True, "scenes": []}
    edit_hash = canonical_hash(edit_decisions)

    fake_props = {
        "productionId": "proj_remote_test_01",
        "editArtifactVersion": 1,
        "editArtifactHash": edit_hash,
        "lock": {
            "renderer_family": "explainer",
            "render_runtime": "remotion",
            "composition_mode": "atelier",
        },
        "events": [],
        "assets": [],
        "captions": [],
        "audio": [],
        "cta": {"scene_id": "scene_05"},
    }
    props_file = tmp_path / "props.json"
    props_file.write_text(json.dumps(fake_props, indent=2), encoding="utf-8")

    job = {
        "production_id": "proj_remote_test_01",
        "edit_artifact_version": 1,
        "edit_artifact_hash": edit_hash,
        "renderer_family": "explainer",
        "composition_mode": "atelier",
        "platform_profile": "profiles/youtube_short.json",
        "output_format": "mp4",
        "remote_policy": "auto",
    }

    artifact_payloads = {
        "edit_decisions": edit_decisions,
        "scene_plan": {"scenes": []},
        "asset_manifest": {"assets": []},
        "art_direction": {"palette": {}},
        "script": {"sections": []},
    }

    # Dummy asset file
    dummy_asset = tmp_path / "sample.png"
    dummy_asset.write_bytes(b"\x89PNG\r\n\x1a\n")

    bundle_zip_dest = tmp_path / "bundle.zip"
    composer_dir = ROOT / "remotion-composer"

    # 1. Produce remote bundle with embedded composer
    bundle_path = package_remote_bundle(
        job=job,
        props_path=props_file,
        artifact_payloads=artifact_payloads,
        asset_files=[dummy_asset],
        bundle_path=bundle_zip_dest,
        composer_dir=composer_dir,
        include_composer=True,
    )
    assert bundle_path.is_file()

    # 2. Inspect bundle contents
    import zipfile
    with zipfile.ZipFile(bundle_path) as zf:
        namelist = zf.namelist()
        assert "remote_job.json" in namelist
        assert "props/props.json" in namelist
        assert "props/edit_decisions.json" in namelist
        assert "assets/sample.png" in namelist
        assert "composer/package.json" in namelist

        remote_job_data = json.loads(zf.read("remote_job.json").decode("utf-8"))
        assert remote_job_data["bundle_version"] == REMOTE_BUNDLE_VERSION
        assert remote_job_data["runtime"] == "remotion"
        assert remote_job_data["production_id"] == "proj_remote_test_01"

    # 3. Execute scripts/remotion_worker.py in --dry-run mode
    worker_script = ROOT / "scripts" / "remotion_worker.py"
    worker_workdir = tmp_path / "worker_workdir"
    sync_dir = tmp_path / "worker_sync"
    cmd = [
        sys.executable,
        str(worker_script),
        "--bundle", str(bundle_path),
        "--workdir", str(worker_workdir),
        "--sync-dir", str(sync_dir),
        "--dry-run",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"Worker dry-run failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    assert "dry-run: validation complete" in proc.stdout

    # 4. Verify worker_result.json was generated and satisfies contract
    result_file = sync_dir / "worker_result.json"
    assert result_file.is_file()
    result_data = json.loads(result_file.read_text(encoding="utf-8"))
    assert result_data["status"] == "completed"
    assert result_data["dry_run"] is True
    assert result_data["job_id"] == "proj_remote_test_01"
