import json

import pytest

from gpu_run5.config import load_sealed_test


def test_sealed_test_requires_phase8(tmp_path):
    path = tmp_path / "test.json"
    path.write_text(json.dumps([{"system_id": "held_out"}]))
    with pytest.raises(PermissionError):
        load_sealed_test(path, phase=7)
    assert load_sealed_test(path, phase=8)[0]["system_id"] == "held_out"
