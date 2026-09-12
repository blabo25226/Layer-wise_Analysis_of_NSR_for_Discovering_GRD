"""Run directory, phase manifest, and provenance helpers for GPU_RUNclaude1 C0001.

Mirrors ``src/gpu_run5/config.py``'s pattern (``run_dir``, ``phase_dir``,
``write_manifest``, ``budget``) but does not reuse it directly:
``gpu_run5.config.write_manifest`` hardcodes ``{"campaign": "GPU_RUN5", ...}``
(AUDIT-MIN-4), which would mislabel every C0001 phase manifest. This module
is C0001's own, correctly labelled ``GPU_RUNclaude1_C0001`` (v2 §12).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from experiment_runtime import REPO_ROOT
from gpu_run2_runtime import utc_now, write_json

from gpu_runclaude1.constants import BRANCH, CAMPAIGN


def git_commit(length: int | None = None) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True, check=True
    )
    commit = result.stdout.strip()
    return commit[:length] if length else commit


def git_branch() -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"], cwd=REPO_ROOT, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


def git_status_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True, check=True
    )
    return not result.stdout.strip()


def run_id_for(short_commit: str | None = None) -> str:
    """``gpu_runclaude1_c0001_<short7>``, ``<short7>`` = the first 7 chars of
    the commit **at run start** (v2 §12).
    """
    short = short_commit or git_commit(7)
    return f"gpu_runclaude1_c0001_{short}"


def candidate_run_dir(run_id: str | None = None) -> Path:
    name = run_id or run_id_for()
    return REPO_ROOT / "results" / "runs" / name


def resolve_new_run_dir(run_id: str | None = None) -> Path:
    """Never overwrite an existing run directory (rule 05, v2 §12): if the
    candidate name already exists on disk, append ``_v2``, ``_v3``, ...
    """
    base = candidate_run_dir(run_id)
    if not base.exists():
        return base
    suffix = 2
    while True:
        candidate = base.parent / f"{base.name}_v{suffix}"
        if not candidate.exists():
            return candidate
        suffix += 1


def resolve_run_dir_for_phase(run_id: str | None, *, is_first_phase: bool) -> Path:
    """The run directory a phase script should use.

    Phase 0 (or any phase invoked standalone with no ``--run-id``, e.g. for
    its own isolated smoke test) picks a fresh, collision-avoided directory
    (v2 §12: never overwrite an existing ``results/runs/*``). Every later
    phase of the *same* run is invoked with the run ID phase 0 actually
    resolved to and must reuse it idempotently: it must not itself dodge
    sideways into ``_v2`` merely because phase 0 already created that
    directory on disk.
    """
    if run_id and not is_first_phase:
        return candidate_run_dir(run_id)
    return resolve_new_run_dir(run_id)


def phase_dir(root: Path, phase: int) -> Path:
    path = Path(root) / f"phase{phase}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_manifest(out_dir: Path, phase: int, status: str, **payload: Any) -> Path:
    body = {
        "campaign": CAMPAIGN,
        "branch": BRANCH,
        "commit": git_commit(),
        "phase": int(phase),
        "status": status,
        "at_utc": utc_now(),
        **payload,
    }
    return write_json(Path(out_dir) / "manifest.json", body)


def require_previous(run_dir: Path, relative: str) -> Path:
    path = Path(run_dir) / relative
    if not path.is_file():
        raise FileNotFoundError(f"required previous-phase artifact missing: {path}")
    return path
