"""File-level input allowlist and instrumented opener (v2.1 §2.4, rule 02, rule 05 defect 7).

C0001 must never read a sealed test artifact, and never pass a directory to a
byte-reading fingerprinter (``scripts/ops/run_manifest.py:28 tree_sha256``
does ``rglob("*")`` and would byte-read every file under a GPU_RUN5 run root,
including every sealed artifact beneath it.

**There are 7 sealed files on disk in this campaign's `results/runs/` tree,
not 3**: `gpu_run5_20260823_ddd267b0` (the pinned source run) holds all
three named artifacts (`phase2/sealed_test.json`,
`phase2/sealed_family_holdout_test.json`, `phase4/sealed_official_test.json`);
two further abandoned run directories, `gpu_run5_20260823_8cd0b6fa` and
`gpu_run5_20260823_fec3a894`, each hold a further two. This count is never
hardcoded anywhere in this module -- :func:`enumerate_sealed_paths` and
:func:`is_sealed_path` operate on the resolved filename, not a fixed list, so
they cover all 7 (and any future sealed artifact) without modification.

**`phase4/sealed_official_test.json`'s precise status**: its outcomes have
never been analyzed by any test-open ledger event, but its *bytes* were
already read once, outside any ledger, by its own producing phase
(`scripts/phases/gpu_run5_phase4.py:119,152`, which computes and persists its
SHA256 as ordinary provenance). "Outcomes never evaluated" is accurate;
"bytes never read" / "unspent, untouched" is not, and this module makes no
such claim -- C0001 additionally never reads it under any doctrine.

This module is the mechanical enforcement:

* :data:`SEALED_NAME_PREFIXES` names what a "sealed" path looks like, checked
  on every resolved path, not on the string a caller happened to pass.
* :class:`InstrumentedOpener` is the *only* sanctioned way C0001 code reads a
  file from the GPU_RUN5 source run. It maintains the allowlist, refuses
  anything not on it (including any directory), and its
  ``sealed_paths_read`` property is a *computed* field over what was actually
  opened -- never a hardcoded ``[]`` (AUDIT-MAJ-2/3).
* :func:`assert_no_directory_argument` / :func:`safe_run_manifest_args` are
  the guard used before any ``scripts/ops/run_manifest.py`` invocation.
* :func:`enumerate_validation_cells` performs the content-checked glob v2
  requires (``assert len(glob(...)) == 960`` and ``assert all("test" not in
  name)``) so the guarantee is about file contents, not merely path shape.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

SEALED_NAME_PREFIXES = ("sealed",)

# v2 §2.4 item 1 -- the frozen file-level allowlist, relative to the GPU_RUN5
# source run root (`results/runs/gpu_run5_20260823_ddd267b0/`).
GPU_RUN5_ALLOWLIST_RELATIVE = (
    "phase2/train.json",
    "phase2/validation.json",
    "phase3/all_candidates.json",
    "phase3/beam_groups.json",
    "phase4/fixed_grn_validation_panel.json",
)

# replication only (v2 §15); a different run root (GPU_RUN4's).
GPU_RUN4_REPLICATION_ALLOWLIST_RELATIVE = (
    "phase2/all_candidates.json",
)

EXPECTED_VALIDATION_CELL_COUNT = 960


class SealedArtifactAccessError(PermissionError):
    """Raised when C0001 code resolves a path that looks like a sealed artifact."""


class AllowlistViolationError(PermissionError):
    """Raised when a path outside the frozen file-level allowlist is opened."""


def is_sealed_path(path: Path) -> bool:
    """True iff the path's own filename starts with 'sealed' (case-insensitive).

    Checked on the *resolved* path's name, never on a caller-supplied string,
    so an alias or a different casing cannot slip past the guard.
    """
    return Path(path).name.lower().startswith(SEALED_NAME_PREFIXES)


def enumerate_validation_cells(phase3_dir: Path) -> list[Path]:
    """Content-checked glob of the 960 validation cell files (v2 §2.4 item 4).

    Asserts the count is exactly 960 and that no matched filename contains
    "test", so the guarantee is about what was actually found, not about the
    glob pattern being trusted blindly.
    """
    phase3_dir = Path(phase3_dir)
    cells = sorted(phase3_dir.glob("cells/*_validation_*.json"))
    if len(cells) != EXPECTED_VALIDATION_CELL_COUNT:
        raise AllowlistViolationError(
            f"expected exactly {EXPECTED_VALIDATION_CELL_COUNT} validation cell files, "
            f"found {len(cells)} under {phase3_dir / 'cells'}"
        )
    for cell in cells:
        if "test" in cell.name.lower():
            raise SealedArtifactAccessError(f"validation cell glob matched a 'test' filename: {cell}")
        if is_sealed_path(cell):
            raise SealedArtifactAccessError(f"validation cell glob matched a sealed-looking filename: {cell}")
    return cells


class InstrumentedOpener:
    """The only sanctioned reader of GPU_RUN5 / GPU_RUN4 source-run artifacts.

    Every path this cycle opens is recorded. ``sealed_paths_read`` is
    therefore a computed property, not a field a phase script can forget to
    populate or a value that can drift from what actually happened.
    """

    def __init__(self, allowlist: Iterable[Path]):
        self._allowlist: set[Path] = {Path(p).resolve() for p in allowlist}
        self._opened: list[Path] = []

    def extend_allowlist(self, paths: Iterable[Path]) -> None:
        self._allowlist.update(Path(p).resolve() for p in paths)

    @property
    def allowlist(self) -> frozenset[Path]:
        return frozenset(self._allowlist)

    @property
    def opened_paths(self) -> list[Path]:
        return list(self._opened)

    @property
    def sealed_paths_read(self) -> list[str]:
        """Computed, not hardcoded: every opened path that looks sealed."""
        return [str(p) for p in self._opened if is_sealed_path(p)]

    def _check(self, path: Path) -> Path:
        resolved = Path(path).resolve()
        if resolved.is_dir():
            raise AllowlistViolationError(
                f"C0001 file-level allowlist forbids directory reads: {resolved}"
            )
        if is_sealed_path(resolved):
            raise SealedArtifactAccessError(f"refused to open a sealed-looking path: {resolved}")
        if resolved not in self._allowlist:
            raise AllowlistViolationError(f"path is not on the C0001 input allowlist: {resolved}")
        self._opened.append(resolved)
        return resolved

    def read_json(self, path: Path) -> Any:
        resolved = self._check(path)
        return json.loads(resolved.read_text(encoding="utf-8"))

    def read_bytes(self, path: Path) -> bytes:
        return self._check(path).read_bytes()

    def sha256(self, path: Path) -> str:
        resolved = self._check(path)
        digest = hashlib.sha256()
        with resolved.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def fingerprints(self) -> dict[str, str]:
        """SHA256 of every path actually opened so far (v2 R/phase0/input_fingerprints.json)."""
        out: dict[str, str] = {}
        for path in self._opened:
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            out[str(path)] = digest.hexdigest()
        return out


def assert_no_directory_argument(paths: Iterable[Path]) -> None:
    """Guard used before any ``scripts/ops/run_manifest.py --data-path`` call.

    Raises if any argument resolves to a directory or to a sealed-looking
    name; a directory would make ``tree_sha256``'s ``rglob("*")`` byte-read
    every file beneath it (rule 02, AUDIT-MAJ-2/3, research_state.md §8
    defect 7).
    """
    for path in paths:
        resolved = Path(path).resolve()
        if resolved.is_dir():
            raise AllowlistViolationError(
                f"run_manifest.py --data-path must never receive a directory: {resolved}"
            )
        if is_sealed_path(resolved):
            raise SealedArtifactAccessError(f"run_manifest.py --data-path resolves to a sealed path: {resolved}")


def safe_run_manifest_data_paths(paths: Iterable[Path]) -> list[str]:
    """Validate and stringify a file list for ``run_manifest.py --data-path`` use."""
    resolved = [Path(p).resolve() for p in paths]
    assert_no_directory_argument(resolved)
    return [str(p) for p in resolved]


def enumerate_sealed_paths(search_roots: Iterable[Path]) -> list[Path]:
    """Enumerate every ``sealed*`` file under the given roots.

    Used only by tests and by the guard below to demonstrate the guard is
    not counting on a hardcoded, possibly stale list: at audit time the
    campaign's `results/runs/` tree held **7** sealed files across three
    GPU_RUN5 run directories (two spent seals each in two older runs, plus
    the pinned source run's three), not just the three under the one run
    C0001 actually reads from. The guard in this module never assumes a
    count; it checks the *name* of every path actually resolved, in any run
    directory.
    """
    found: list[Path] = []
    for root in search_roots:
        root = Path(root)
        if not root.is_dir():
            continue
        found.extend(sorted(p for p in root.rglob("sealed*") if p.is_file()))
    return found


# ---------------------------------------------------------------------------
# Process-level interception (v2 §2.4 items 2-3, hardened): the
# InstrumentedOpener above only helps if every read genuinely goes through
# it. This context manager additionally patches the builtin ``open`` for its
# duration so a bare ``open()`` call on a sealed-looking path -- anywhere,
# including a bug that bypassed InstrumentedOpener entirely -- still raises.
# It is opt-in (a context manager phase scripts enter explicitly), not
# installed unconditionally at import time, so it cannot leak into unrelated
# code running in the same process/test session.
# ---------------------------------------------------------------------------
_real_open = builtins.open


def _sealed_guarded_open(file, *args, **kwargs):
    try:
        path_text = os.fspath(file)
    except TypeError:
        path_text = None
    if path_text is not None and is_sealed_path(Path(path_text)):
        raise SealedArtifactAccessError(
            f"global open() guard refused a sealed-looking path: {path_text}"
        )
    return _real_open(file, *args, **kwargs)


@contextmanager
def sealed_open_guard() -> Iterator[None]:
    """Intercept ``builtins.open`` for the duration of the block so that any
    direct ``open()`` call -- not just calls through
    :class:`InstrumentedOpener` -- raises on a sealed-looking path. C0001
    phase entry points wrap their whole run in this.
    """
    builtins.open = _sealed_guarded_open  # type: ignore[assignment]
    try:
        yield
    finally:
        builtins.open = _real_open  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# v2.1 §2.4 item 7a (V2-MAJ-6): a `sys.addaudithook` interception, stronger
# than the `builtins.open` context manager above (which remains as
# defense-in-depth for the common case). The audit hook fires on the CPython
# "open" event for *every* filesystem open performed by Python-level code in
# the process -- `open()`, `io.open()`, `Path.open()`/`read_text`/
# `read_bytes()`, `numpy.load`, `pandas.read_*` -- not only a bare `open()`.
#
# A CPython audit hook, once added, **cannot be removed** (a deliberate
# security property: an attacker who compromised a hook could otherwise
# uninstall it). This function is therefore meant to be called exactly once,
# early in a phase script's entry point, before any C0001 module that might
# open a file. Calling it more than once (e.g. once per test in the same
# session) is harmless -- each call adds one more redundant, equivalent hook.
# ---------------------------------------------------------------------------
_sealed_audit_hook_installed = False


def _sealed_audit_hook(event: str, args: tuple) -> None:
    if event not in ("open", "os.open"):
        return
    path = args[0] if args else None
    if path is None:
        return
    try:
        path_text = os.fspath(path)
    except TypeError:
        return
    if is_sealed_path(Path(path_text)):
        raise SealedArtifactAccessError(
            f"sys.addaudithook refused a sealed-looking path: {path_text}"
        )


def install_sealed_audit_hook() -> None:
    """Install the process-wide audit-event guard (v2.1 §2.4 item 7a).

    Wording, frozen: ``sealed_paths_read`` is the set of ``sealed*``-matching
    paths this hook observed, which is empty iff no such path was opened by
    any Python-level code running under the hook in this process -- it is
    not a claim that every path C0001 opened is enumerated, only that every
    filesystem open reaching the CPython audit-event system was checked.
    """
    global _sealed_audit_hook_installed
    sys.addaudithook(_sealed_audit_hook)
    _sealed_audit_hook_installed = True


def sealed_audit_hook_installed() -> bool:
    return _sealed_audit_hook_installed
