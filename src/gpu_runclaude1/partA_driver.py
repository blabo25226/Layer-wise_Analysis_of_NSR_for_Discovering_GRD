"""Part A driver: the only entry point that may compute match indicators over
the stored GPU_RUN5 cells (v2 §7.2 step 3, §14 item 8).

Mechanically gated: :func:`score_cell` requires a
:class:`gpu_runclaude1.strata.StrataFrozenToken`, obtainable only via
:func:`gpu_runclaude1.strata.require_strata_frozen`, which itself requires
the component-strata and ladder artifacts to already be written and hashed
to disk. There is no code path in this module that computes a match
indicator without one -- passing anything else raises ``TypeError``
immediately, before any candidate is touched.
"""

from __future__ import annotations

import dataclasses
import json
import multiprocessing
from pathlib import Path
from typing import Any

from gpu_runclaude1.matcher import MatchResult, score_pair
from gpu_runclaude1.strata import StrataFrozenToken


def _require_token(strata_token: Any) -> None:
    if not isinstance(strata_token, StrataFrozenToken):
        raise TypeError(
            "Part A matching requires a gpu_runclaude1.strata.StrataFrozenToken, obtained "
            "only from require_strata_frozen(strata_path, ladder_path). Matching may not "
            "run before the strata and ladder artifacts are written and hashed to disk "
            "(v2 §7.2 step 3, §14 item 8). There is no remedy for violating this order "
            "short of a new cycle ID."
        )


def score_cell(cell: dict[str, Any], strata_token: StrataFrozenToken) -> list[MatchResult]:
    """Score every usable candidate of one stored cell against its truth.

    ``cell`` is the parsed content of one ``phase3/cells/*_validation_*.json``
    file. Uses ``cell["true_formula"]`` (infix, R1) against each candidate's
    ``candidate_formula_raw`` (also infix).
    """
    _require_token(strata_token)
    true_infix = str(cell["true_formula"])
    return [score_pair(true_infix, str(c.get("candidate_formula_raw") or "")) for c in cell.get("candidates", [])]


def _score_cell_worker(args: tuple) -> list[MatchResult]:
    """Module-level (picklable) worker: score one already-loaded cell.

    Workers never touch the filesystem -- every cell is read once in the
    main process through the guarded :class:`~gpu_runclaude1.io_allowlist.InstrumentedOpener`,
    and only the already-parsed dict, plus the (picklable) StrataFrozenToken,
    crosses the process boundary. This keeps the sealed-artifact guard a
    single-process concern while still parallelizing the CPU-bound matcher
    cascade (v2 §3 "Part A parallelism": process-based, <= 6 workers).
    """
    cell, strata_token = args
    return score_cell(cell, strata_token)


def score_cells_parallel(
    cells: list[dict[str, Any]],
    strata_token: StrataFrozenToken,
    *,
    n_workers: int = 6,
) -> list[list[MatchResult]]:
    """Score many already-loaded cells across up to ``n_workers`` processes.

    Thread-based parallelism is forbidden for this cascade: ``_time_limit``
    (``equation_metrics.py``) silently no-ops off the main thread, removing
    every SymPy wall-clock guard. A separate OS *process* has its own main
    thread, so ``signal.SIGALRM``-based guards fire correctly inside a
    worker -- see :func:`demonstrate_timeout_inside_worker` for the Gate 0
    smoke assertion this requires.
    """
    _require_token(strata_token)
    if n_workers <= 1 or len(cells) <= 1:
        return [score_cell(cell, strata_token) for cell in cells]
    with multiprocessing.Pool(processes=min(n_workers, len(cells))) as pool:
        return pool.map(_score_cell_worker, [(cell, strata_token) for cell in cells])


def _sigalrm_guard_worker(_unused: int) -> dict[str, Any]:
    """Runs inside a worker process: proves ``_time_limit``'s SIGALRM guard
    fires there (it silently no-ops off the main thread of a *thread*, but a
    multiprocessing worker has its own genuine main thread). Deterministic
    (a plain ``time.sleep``, not sympy's data-dependent runtime), unlike a
    "pathological expression" whose actual wall-clock is uncertain.
    """
    import time

    from evaluation.equation_metrics import _SymTimeout, _time_limit

    started = time.perf_counter()
    triggered = False
    try:
        with _time_limit(1.0):
            time.sleep(5.0)
    except _SymTimeout:
        triggered = True
    elapsed = time.perf_counter() - started
    return {"triggered": triggered, "elapsed_sec": elapsed}


def demonstrate_timeout_inside_worker() -> dict[str, Any]:
    """Gate 0 / Stage-6 smoke assertion (v2 §3, §10.1 item 7): prove the
    SymPy wall-clock guard (``_time_limit``, SIGALRM-based) fires *inside a
    worker process*, not just on the main process's main thread -- off the
    main thread of a *thread pool* it silently no-ops, which is exactly why
    v2/v2.1 forbid thread-based parallelism for this cascade and require
    process-based parallelism instead.
    """
    with multiprocessing.Pool(processes=1) as pool:
        (result,) = pool.map(_sigalrm_guard_worker, [0])
    return {
        "triggered": result["triggered"],
        "elapsed_sec": result["elapsed_sec"],
        "ok": result["triggered"] and result["elapsed_sec"] < 2.0,
    }


def serialize_match_results(results: list[MatchResult]) -> list[dict]:
    """Plain-dict, JSON-round-tripped serialization of a cell's MatchResult
    list, for the per-cell resume cache and for byte-identical serial-vs-
    parallel comparison. The JSON round-trip inside this function (not only
    when a cache file is later reloaded) matters: ``dataclasses.asdict``
    preserves the ``tuple`` type of ``MatchResult.components``, but a value
    reloaded from a JSON cache file is always a ``list`` -- comparing a
    freshly-computed result against a cache-reloaded one would otherwise
    report a spurious difference (tuple != list) despite identical content.
    Round-tripping here makes a freshly-computed result and a cached-and-
    reloaded one structurally identical from the start.
    """
    return json.loads(json.dumps([dataclasses.asdict(r) for r in results]))


def _score_cell_worker_safe(args: tuple) -> dict[str, Any]:
    """Failure-isolated worker: one candidate's crash (or an unexpected
    exception scoring the whole cell) must not lose the whole shard. Caught
    here and returned as a labelled failure record rather than propagating
    and killing the worker process (which would silently drop every other
    cell still queued to that worker under ``Pool.map``'s chunking).
    """
    cell, strata_token = args
    cell_id = cell.get("cell_id")
    try:
        results = score_cell(cell, strata_token)
        return {"cell_id": cell_id, "ok": True, "results": serialize_match_results(results)}
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: isolate any per-cell failure
        return {"cell_id": cell_id, "ok": False, "error_type": type(exc).__name__, "error_message": str(exc)}


def score_cells_parallel_resumable(
    cells: list[dict[str, Any]],
    strata_token: StrataFrozenToken,
    *,
    cache_dir: Path,
    n_workers: int = 6,
) -> list[dict[str, Any]]:
    """Score cells in parallel with per-cell failure isolation and resume.

    **Resume.** Before scoring, any cell whose result is already cached at
    ``cache_dir/<cell_id>.json`` is skipped entirely and its cached result is
    reused verbatim -- a restarted run does not recompute completed cells,
    and (since each cell's own file is the sole record of its completion,
    written only after that cell's scoring finishes) does not double-count
    a cell that was only partially processed when a previous run stopped.

    **Failure isolation.** Each cell is scored by :func:`_score_cell_worker_safe`,
    which catches any exception and returns a labelled failure record instead
    of letting it propagate; one cell's crash therefore cannot lose the
    results already computed for other cells in the same shard.

    Returns one dict per input cell, in the same order as ``cells``, each
    either ``{"cell_id", "ok": True, "results": [...]}`` or
    ``{"cell_id", "ok": False, "error_type", "error_message"}``.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    to_score: list[dict[str, Any]] = []
    cached: dict[str, dict] = {}
    for cell in cells:
        cell_id = cell["cell_id"]
        cache_path = cache_dir / f"{cell_id}.json"
        if cache_path.is_file():
            cached[cell_id] = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            to_score.append(cell)

    _require_token(strata_token)
    if to_score:
        n = max(1, min(n_workers, len(to_score)))
        with multiprocessing.Pool(processes=n) as pool:
            for cell, outcome in zip(
                to_score, pool.imap(_score_cell_worker_safe, [(c, strata_token) for c in to_score])
            ):
                cell_id = cell["cell_id"]
                (cache_dir / f"{cell_id}.json").write_text(json.dumps(outcome), encoding="utf-8")
                cached[cell_id] = outcome

    return [cached[cell["cell_id"]] for cell in cells]


def verify_m0_reproduction(cell: dict[str, Any], results: list[MatchResult]) -> dict[str, Any]:
    """v2 §7.6: every recomputed M0 field must exactly reproduce the stored one."""
    candidates = cell.get("candidates", [])
    mismatches = []
    for index, (candidate, result) in enumerate(zip(candidates, results)):
        stored_system = candidate.get("exponent_aware_skeleton_exact")
        if stored_system is not None and float(stored_system) != result.m0_system:
            mismatches.append({"candidate_index": index, "level": "system", "stored": stored_system, "recomputed": result.m0_system})
        stored_components = candidate.get("component_exponent_aware_skeleton_exact") or []
        for component_index, stored_value in enumerate(stored_components):
            if component_index >= len(result.components):
                continue
            recomputed = result.components[component_index].m0
            if float(stored_value) != recomputed:
                mismatches.append(
                    {
                        "candidate_index": index,
                        "level": "component",
                        "component_index": component_index,
                        "stored": stored_value,
                        "recomputed": recomputed,
                    }
                )
    return {
        "cell_id": cell.get("cell_id"),
        "n_candidates": len(candidates),
        "n_mismatches": len(mismatches),
        "mismatches": mismatches,
        "ok": not mismatches,
    }
