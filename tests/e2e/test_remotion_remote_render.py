"""Remote render contract tests. Fixture results pass here; a real synced
worker_result.json is validated when present, skipped (never passed) when absent.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from composition.remotion.renderer import validate_worker_result


def _completed(**overrides):
    result = {"status": "completed", "job_id": "proj_3e27bd7a", "runtime": "remotion",
              "runtime_version": "4.0.0", "output_file": "/work/final_video.mp4",
              "duration": 38.83, "resolution": "1080x1920", "fps": 30,
              "audio_present": False, "exit_code": 0, "render_seconds": 123.0}
    result.update(overrides)
    return result


def test_completed_worker_result_contract():
    assert validate_worker_result(_completed()) == []


def test_completed_result_requires_all_keys():
    result = _completed()
    del result["output_file"]
    violations = validate_worker_result(result)
    assert any("output_file" in violation for violation in violations)


def test_completed_result_rejects_wrong_runtime():
    violations = validate_worker_result(_completed(runtime="ffmpeg_pil"))
    assert any("wrong runtime" in violation for violation in violations)


def test_completed_result_rejects_nonzero_exit():
    violations = validate_worker_result(_completed(exit_code=1))
    assert any("nonzero exit_code" in violation for violation in violations)


def test_failed_worker_result_contract():
    assert validate_worker_result({"status": "failed", "code": "REMOTION_RENDER_FAILED",
                                   "message": "boom", "logs": []}) == []


def test_failed_result_requires_code_and_message():
    violations = validate_worker_result({"status": "failed", "code": "X"})
    assert any("message" in violation for violation in violations)


def test_unknown_status_rejected():
    assert validate_worker_result({"status": "running"}) != []


def test_real_synced_worker_result_if_present():
    """Validates the actual synced worker result when a remote run completed.

    Skipped when no result has synced back yet. A skip is an explicit
    not-run, never a pass.
    """
    candidates = sorted((ROOT / "projects").glob("*/composition/*worker_result.json"))
    candidates += sorted((ROOT / "projects").glob("*/composition/*/worker_result.json"))
    if not candidates:
        pytest.skip("no synced worker_result.json yet (remote render not executed)")
    for path in candidates:
        result = json.loads(path.read_text(encoding="utf-8"))
        assert validate_worker_result(result) == [], path
        assert result["status"] == "completed"
