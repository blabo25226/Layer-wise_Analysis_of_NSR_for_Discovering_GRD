"""Tests for the C0001 sealed-artifact guard and file-level allowlist (v2.1 §2.4).

Covers: InstrumentedOpener refusing a sealed path and a directory path;
sealed_paths_read as a genuinely computed field (never a hardcoded []); the
process-level open() interception, both the `builtins.open` context manager
and the stronger `sys.addaudithook` guard (a bare open(), not just the
wrapper's own method, raises on a sealed path); dynamic enumeration of every
sealed file on disk (not a hardcoded count); and the content-checked
validation-cell glob.

Ordering note: `sys.addaudithook` guards, once installed, cannot be
uninstalled for the life of the process (a CPython security property). The
three tests that install one (`test_install_sealed_audit_hook_*`) are placed
at the **end** of this file, after every test whose own assertions depend on
a bare `open()` behaving normally outside of any C0001 guard.
"""

from __future__ import annotations

import json
import os
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


def _write_sealed_fixture(tmp_path: Path, name: str, content: str) -> Path:
    """Write a fixture under a sealed-looking name safely regardless of
    whether the process-wide audit hook is already installed: write under a
    plain name first, then `os.rename` into place -- a rename is not an
    `open`/`os.open` audit event, so it is unaffected by the hook either way.
    """
    plain = tmp_path / f"_staging_{name}"
    plain.write_text(content)
    target = tmp_path / name
    os.rename(plain, target)
    return target


def test_is_sealed_path_checks_the_resolved_filename():
    assert is_sealed_path(Path("/a/b/sealed_test.json"))
    assert is_sealed_path(Path("/a/b/SEALED_OFFICIAL_TEST.JSON"))
    assert not is_sealed_path(Path("/a/b/validation.json"))


def test_instrumented_opener_refuses_a_sealed_path(tmp_path):
    sealed = _write_sealed_fixture(tmp_path, "sealed_test.json", json.dumps([{"system_id": "held_out"}]))
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
    sealed = _write_sealed_fixture(tmp_path, "sealed_official_test.json", "[]")
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
    """The `builtins.open` context manager (unlike the addaudithook guard
    below) genuinely uninstalls itself: a bare open() outside the block
    succeeds again. This must run before any test in this file installs the
    permanent addaudithook guard, since that guard would make this
    assertion fail for an unrelated reason.
    """
    sealed = _write_sealed_fixture(tmp_path, "sealed_test.json", "[]")
    with sealed_open_guard():
        pass
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
    sealed = _write_sealed_fixture(tmp_path, "sealed_test.json", "[]")
    with pytest.raises(SealedArtifactAccessError):
        safe_run_manifest_data_paths([sealed])


def test_safe_run_manifest_data_paths_accepts_plain_files(tmp_path):
    plain = tmp_path / "validation.json"
    plain.write_text("[]")
    result = safe_run_manifest_data_paths([plain])
    assert result == [str(plain.resolve())]


# ---------------------------------------------------------------------------
# sys.addaudithook guard tests (v2.1 §2.4 item 7): kept last in this file --
# see the module docstring's ordering note.
# ---------------------------------------------------------------------------


def test_install_sealed_audit_hook_intercepts_direct_open_from_inside_the_package(tmp_path):
    """v2.1 §2.4 item 7c: a direct open() on a sealed path, executed from
    inside src/gpu_runclaude1, must raise SealedArtifactAccessError. Audit
    hooks cannot be removed once installed (a CPython security property), so
    this installs one (harmless if called more than once in a session) and
    verifies it fires -- it is never uninstalled again.
    """
    sealed = _write_sealed_fixture(tmp_path, "sealed_official_test.json", "[]")
    install_sealed_audit_hook()
    assert sealed_audit_hook_installed() is True
    with pytest.raises(SealedArtifactAccessError):
        open(sealed)  # noqa: SIM115 -- bare open(), the point of this test


def test_install_sealed_audit_hook_also_intercepts_path_read_text(tmp_path):
    sealed = _write_sealed_fixture(tmp_path, "sealed_test.json", "[]")
    install_sealed_audit_hook()
    with pytest.raises(SealedArtifactAccessError):
        sealed.read_text()


def test_install_sealed_audit_hook_does_not_affect_ordinary_reads(tmp_path):
    normal = tmp_path / "validation.json"
    normal.write_text("hello")
    install_sealed_audit_hook()
    assert normal.read_text() == "hello"


# ---------------------------------------------------------------------------
# Static AST guard (v2.1 §2.4 item 7d / F6): no file-read call site in the
# C0001 phase scripts may reference a GPU_RUN5-source-rooted path directly --
# every such read must go through the InstrumentedOpener API instead.
# ---------------------------------------------------------------------------
import ast

_FORBIDDEN_READ_FUNCS = {"open", "read_text", "read_bytes", "loadtxt", "load"}
_SOURCE_ROOT_NAME = "GPU_RUN5_SOURCE_RUN"


def _call_func_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _references_source_root(node: ast.AST) -> bool:
    return any(
        isinstance(sub, ast.Name) and sub.id == _SOURCE_ROOT_NAME for sub in ast.walk(node)
    )


def _forbidden_read_sites(source: str) -> list[str]:
    tree = ast.parse(source)
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_func_name(node)
        if name not in _FORBIDDEN_READ_FUNCS:
            continue
        if any(_references_source_root(arg) for arg in node.args) or any(
            _references_source_root(kw.value) for kw in node.keywords
        ):
            violations.append(f"line {node.lineno}: {name}(...) referencing {_SOURCE_ROOT_NAME}")
    return violations


def test_phase_scripts_never_read_a_source_root_path_directly():
    """Every GPU_RUN5-source-rooted path must be read through
    InstrumentedOpener (`opener.read_json`/`sha256`/`fingerprints`), never a
    bare `open`/`read_text`/`read_bytes`/`np.load` call. This is a static
    guarantee complementing the runtime `sys.addaudithook` guard.
    """
    scripts_dir = REPO_ROOT / "scripts" / "phases"
    phase_scripts = sorted(scripts_dir.glob("gpu_runclaude1_c0001_phase*.py"))
    assert len(phase_scripts) >= 5
    all_violations = {}
    for script in phase_scripts:
        violations = _forbidden_read_sites(script.read_text(encoding="utf-8"))
        if violations:
            all_violations[script.name] = violations
    assert not all_violations, f"unguarded reads of the source root found: {all_violations}"


def test_library_modules_never_read_a_source_root_path_directly():
    """Same guarantee for src/gpu_runclaude1/ itself (excluding
    io_allowlist.py, which implements the guarded API and legitimately
    contains the low-level `open`/`read_bytes` calls the API wraps).
    """
    src_dir = REPO_ROOT / "src" / "gpu_runclaude1"
    modules = sorted(p for p in src_dir.glob("*.py") if p.name != "io_allowlist.py")
    assert modules
    all_violations = {}
    for module in modules:
        violations = _forbidden_read_sites(module.read_text(encoding="utf-8"))
        if violations:
            all_violations[module.name] = violations
    assert not all_violations, f"unguarded reads of the source root found: {all_violations}"
