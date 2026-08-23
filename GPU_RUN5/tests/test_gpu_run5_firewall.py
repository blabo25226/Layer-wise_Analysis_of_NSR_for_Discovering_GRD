import json

import pytest

from gpu_run5.config import load_sealed_test, sanitize_nonfinite


def test_sealed_test_requires_phase8(tmp_path):
    path = tmp_path / "test.json"
    path.write_text(json.dumps([{"system_id": "held_out"}]))
    with pytest.raises(PermissionError):
        load_sealed_test(path, phase=7)
    assert load_sealed_test(path, phase=8)[0]["system_id"] == "held_out"


def test_nonfinite_values_are_sanitized_for_strict_json():
    assert sanitize_nonfinite({"x": float("nan"), "y": [float("inf"), 1.0]}) == {"x": None, "y": [None, 1.0]}
