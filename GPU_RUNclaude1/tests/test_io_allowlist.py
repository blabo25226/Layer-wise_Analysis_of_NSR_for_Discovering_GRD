"""Tests for the C0001 sealed-artifact guard and file-level allowlist (v2 §2.4).

Covers: InstrumentedOpener refusing a sealed path and a directory path;
sealed_paths_read as a genuinely computed field (never a hardcoded []); the
process-level open() interception (a bare open(), not just the wrapper's own
method, raises on a sealed path); dynamic enumeration of every sealed file on
disk (not a hardcoded count); and the content-checked validation-cell glob.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gpu_runclaude1.io_allowlist import (
    AllowlistViolationError,
    InstrumentedOpener,
    SealedArtifactAccessError,
    enumerate_sealed_paths,
    enumerate_validation_cells,
    install_sealed_audit_hook,
    is_sealed_path,
    safe_run_manifest_data_paths,
    sealed_audit_hook_installed,
    sealed_open_guard,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GPU_RUN5_SOURCE_RUN = REPO_ROOT / "results" / "runs" / "gpu_run5_20260823_ddd267b0"


def test_is_sealed_path_checks_the_resolved_filename():
    assert is_sealed_path(Path("/a/b/sealed_test.json"))
    assert is_sealed_path(Path("/a/b/SEALED_OFFICIAL_TEST.JSON"))
    assert not is_sealed_path(Path("/a/b/validation.json"))


def test_instrumented_opener_refuses_a_sealed_path(tmp_path):
    sealed = tmp_path / "sealed_test.json"
    sealed.write_text(json.dumps([{"system_id": "held_out"}]))
    opener = InstrumentedOpener(allowlist=[sealed])  # even if "allowlisted" by mistake
    with pytest.raises(SealedArtifactAccessError):
        opener.read_json(sealed)
    assert opener.sealed_paths_read == []  # the refused read was never recorded as opened


def test_instrumented_opener_refuses_a_directory(tmp_path):
    directory = tmp_path / "some_run_dir"
    directory.mkdir()
    opener = InstrumentedOpener(allowlist=[directory])
    with pytest.raises(AllowlistViolationError):
        opener.read_json(directory)


def test_instrumented_opener_refuses_paths_outside_the_allowlist(tmp_path):
    allowed = tmp_path / "validation.json"
    allowed.write_text("[]")
    other = tmp_path / "other.json"
    other.write_text("[]")
    opener = InstrumentedOpener(allowlist=[allowed])
    with pytest.raises(AllowlistViolationError):
        opener.read_json(other)


def test_sealed_paths_read_is_computed_not_hardcoded(tmp_path):
    """Reading only allowlisted, non-sealed files must leave sealed_paths_read
    empty; the field reflects what was actually opened, not a constant.
    """
    allowed = tmp_path / "validation.json"
    allowed.write_text("[1, 2, 3]")
    opener = InstrumentedOpener(allowlist=[allowed])
    assert opener.read_json(allowed) == [1, 2, 3]
    assert opener.sealed_paths_read == []
    assert len(opener.opened_paths) == 1


def test_process_level_open_guard_intercepts_a_bare_open_call(tmp_path):
    """The stronger guarantee: even a direct `open()` call -- bypassing
    InstrumentedOpener entirely -- raises inside the guard's scope.
    """
    sealed = tmp_path / "sealed_official_test.json"
    sealed.write_text("[]")
    with sealed_open_guard():
        with pytest.raises(SealedArtifactAccessError):
            open(sealed)  # noqa: SIM115 -- intentionally bare, this is the point of the test


def test_process_level_open_guard_does_not_affect_non_sealed_reads(tmp_path):
    normal = tmp_path / "validation.json"
    normal.write_text("hello")
    with sealed_open_guard():
        with open(normal) as handle:
            assert handle.read() == "hello"


def test_process_level_open_guard_uninstalls_after_the_block(tmp_path):
    sealed = tmp_path / "sealed_test.json"
    sealed.write_text("[]")
    with sealed_open_guard():
        pass
    # Outside the guard, a bare open() on the same path must succeed again
    # (proves the interception does not leak into unrelated code).
    with open(sealed) as handle:
        assert handle.read() == "[]"


@pytest.mark.skipif(not GPU_RUN5_SOURCE_RUN.is_dir(), reason="GPU_RUN5 source run not present in this environment")
def test_enumerate_sealed_paths_finds_every_sealed_file_dynamically():
    """Never assume a fixed count: this campaign's results/runs/ tree holds
    sealed artifacts across multiple GPU_RUN5 run directories, not only the
    pinned source run's three.
    """
    found = enumerate_sealed_paths([REPO_ROOT / "results" / "runs"])
    assert len(found) >= 3  # at least the pinned source run's own three
    names = {p.name for p in found}
    assert "sealed_test.json" in names
    assert "sealed_family_holdout_test.json" in names
    assert "sealed_official_test.json" in names
    for path in found:
        assert is_sealed_path(path)


@pytest.mark.skipif(not GPU_RUN5_SOURCE_RUN.is_dir(), reason="GPU_RUN5 source run not present in this environment")
def test_enumerate_validation_cells_is_content_checked():
    cells = enumerate_validation_cells(GPU_RUN5_SOURCE_RUN / "phase3")
    assert len(cells) == 960
    for cell in cells:
        assert "test" not in cell.name.lower()
        assert not is_sealed_path(cell)


def test_safe_run_manifest_data_paths_rejects_a_directory(tmp_path):
    directory = tmp_path / "a_run_root"
    directory.mkdir()
    with pytest.raises(AllowlistViolationError):
        safe_run_manifest_data_paths([directory])


def test_safe_run_manifest_data_paths_rejects_a_sealed_file(tmp_path):
    sealed = tmp_path / "sealed_test.json"
    sealed.write_text("[]")
    with pytest.raises(SealedArtifactAccessError):
        safe_run_manifest_data_paths([sealed])


def test_install_sealed_audit_hook_intercepts_direct_open_from_inside_the_package(tmp_path):
    """v2.1 §2.4 item 7c: a direct open() on a sealed path, executed from
    inside src/gpu_runclaude1, must raise SealedArtifactAccessError. Audit
    hooks cannot be removed once installed (a CPython security property), so
    this installs one (harmless if called more than once in a session) and
    verifies it fires -- it is never uninstalled again.
    """
    sealed = tmp_path / "sealed_official_test.json"
    sealed.write_text("[]")  # written before the hook exists
    install_sealed_audit_hook()
    assert sealed_audit_hook_installed() is True
    with pytest.raises(SealedArtifactAccessError):
        open(sealed)  # noqa: SIM115 -- bare open(), the point of this test


def test_install_sealed_audit_hook_also_intercepts_path_read_text(tmp_path):
    sealed = tmp_path / "sealed_test.json"
    sealed.write_text("[]")
    install_sealed_audit_hook()
    with pytest.raises(SealedArtifactAccessError):
        sealed.read_text()


def test_install_sealed_audit_hook_does_not_affect_ordinary_reads(tmp_path):
    normal = tmp_path / "validation.json"
    normal.write_text("hello")
    install_sealed_audit_hook()
    assert normal.read_text() == "hello"


def test_safe_run_manifest_data_paths_accepts_plain_files(tmp_path):
    plain = tmp_path / "validation.json"
    plain.write_text("[]")
    result = safe_run_manifest_data_paths([plain])
    assert result == [str(plain.resolve())]
