"""Beam generation and structure scoring for GPU_RUN6 problems."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from gpu_run4.inference import integrate_candidate
from gpu_run4.trajectories import r2_score
from gpu_run4_runtime import candidate_infix
from gpu_run6.enzyme import class_match, structural_class


def _component_infixes(infix: str | None) -> list[str]:
    return [part.strip() for part in (infix or "").split("|")]


def evaluate_problem(regressor: Any, row: dict[str, Any], *, generation_seed: int, integration_timeout: float = 5.0,
                     max_scored: int = 50) -> dict[str, Any]:
    """Run beam generation on the input trajectory and score every candidate.

    Selection follows the official API: candidates are sorted by reconstruction R^2
    on the input trajectory, and the first one is the selected equation.
    """
    times = np.asarray(row["times"], dtype=float)
    traj = np.asarray(row["trajectory"], dtype=float)
    np.random.seed(int(generation_seed))  # official fit() permutes points with numpy's global RNG
    started = time.perf_counter()
    try:
        out = regressor.fit(times, traj, sort_candidates=True, sort_metric="r2")
        trees = list((out or {}).get(0) or [])
        failure = None
    except Exception as exc:  # recorded, never hidden
        trees, failure = [], f"GenerationFailure:{type(exc).__name__}"
    wall = time.perf_counter() - started
    candidates = []
    for index, tree in enumerate(trees[:max_scored]):
        infix = candidate_infix(tree)
        n_comp = len(_component_infixes(infix)) if infix else 0
        if row["family"] == "MA_SC":
            cls = "MA" if class_match("MA_SC", infix) else "other"
        else:
            cls = structural_class(infix) if n_comp == 1 else ("INVALID" if not infix else "WRONG_DIM")
        candidates.append({
            "index": index,
            "infix": infix,
            "class": cls,
            "class_match": bool(class_match(row["family"], infix)) if n_comp == row["dimension_observed"] else False,
            "has_inv_x": bool(infix and cls.startswith("R[")),
        })
    selected = candidates[0] if candidates else None
    record: dict[str, Any] = {
        "problem_id": row["problem_id"],
        "family": row["family"],
        "rational": bool(row["rational"]),
        "true_class": row["true_class"],
        "params": row["params"],
        "noise_sigma": row["noise_sigma"],
        "n_candidates": len(candidates),
        "generation_failure": failure,
        "wall_time": wall,
        "class_in_beam": bool(any(c["class_match"] for c in candidates)),
        "rational_in_beam": bool(any(c["class"].startswith("R[") for c in candidates)),
        "selected_infix": selected["infix"] if selected else None,
        "selected_class": selected["class"] if selected else "INVALID",
        "selected_class_match": bool(selected and selected["class_match"]),
        "beam_class_counts": _counts([c["class"] for c in candidates]),
    }
    # numerical fit of the selected candidate: reconstruction and held-out initial conditions
    recon_r2, gen_r2 = float("nan"), []
    if trees:
        pred, fail = integrate_candidate(regressor, times, traj[0], trees[0], timeout_sec=integration_timeout)
        recon_r2 = r2_score(traj, pred) if pred is not None else float("nan")
        for gen in row["generalization"]:
            g_true = np.asarray(gen["trajectory"], dtype=float)
            g_pred, _ = integrate_candidate(regressor, times, g_true[0], trees[0], timeout_sec=integration_timeout)
            gen_r2.append(r2_score(g_true, g_pred) if g_pred is not None else float("nan"))
    record["recon_r2"] = float(recon_r2)
    record["gen_r2"] = [float(v) for v in gen_r2]
    record["gen_r2_min"] = float(np.nanmin(gen_r2)) if gen_r2 and not np.all(np.isnan(gen_r2)) else float("nan")
    record["candidates"] = candidates
    return record


def _counts(values: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return out
