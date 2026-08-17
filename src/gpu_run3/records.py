"""GPU_RUN3 formula records, canonicalization, and failure-aware schema."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

GPU_RUN3_REQUIRED_FIELDS = frozenset(
    {
        "campaign",
        "problem_id",
        "system_name",
        "formula_id",
        "split",
        "condition",
        "true_formula_raw",
        "true_formula_canonical",
        "true_formula_skeleton",
        "pred_formula_raw",
        "pred_formula_canonical",
        "pred_formula_skeleton",
        "fit_error",
        "exact",
        "skeleton",
        "symbolic_equivalent",
        "ted_raw",
        "ted_skeleton",
        "complexity",
        "valid",
        "failure_reason",
        "search_nodes",
        "candidate_count",
        "wall_time",
    }
)

GPU_RUN3_LAYER_FIELDS = frozenset(
    {
        "module_name",
        "layer_index",
        "analysis_type",
    }
)


def make_formula_record(
    *,
    problem_id: str,
    system_name: str = "",
    formula_id: str = "",
    split: str = "validation",
    condition: str = "",
    true_formula_raw: str = "",
    true_formula_canonical: str = "",
    true_formula_skeleton: str = "",
    pred_formula_raw: str = "",
    pred_formula_canonical: str = "",
    pred_formula_skeleton: str = "",
    fit_error: float | None = None,
    exact: float | None = None,
    skeleton: float | None = None,
    symbolic_equivalent: float | None = None,
    ted_raw: float | None = None,
    ted_skeleton: float | None = None,
    ted_variable_aware: float | None = None,
    complexity: float | None = None,
    valid: bool | None = None,
    failure_reason: str | None = None,
    search_nodes: int | None = None,
    candidate_count: int | None = None,
    wall_time: float | None = None,
    prefix: Sequence[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    record = {
        "campaign": "GPU_RUN3",
        "problem_id": problem_id,
        "system_name": system_name,
        "formula_id": formula_id or problem_id,
        "split": split,
        "condition": condition,
        "true_formula_raw": true_formula_raw,
        "true_formula_canonical": true_formula_canonical,
        "true_formula_skeleton": true_formula_skeleton,
        "pred_formula_raw": pred_formula_raw,
        "pred_formula_canonical": pred_formula_canonical,
        "pred_formula_skeleton": pred_formula_skeleton,
        "fit_error": fit_error,
        "exact": exact,
        "skeleton": skeleton,
        "symbolic_equivalent": symbolic_equivalent,
        "ted_raw": ted_raw,
        "ted_skeleton": ted_skeleton,
        "ted_variable_aware": ted_variable_aware,
        "complexity": complexity,
        "valid": valid,
        "failure_reason": failure_reason,
        "search_nodes": search_nodes,
        "candidate_count": candidate_count,
        "wall_time": wall_time,
        "prefix": list(prefix or []),
    }
    record.update(extra)
    missing = GPU_RUN3_REQUIRED_FIELDS - set(record)
    if missing:
        raise ValueError(f"GPU_RUN3 formula record missing fields: {sorted(missing)}")
    return record


def dummy_formula_record(problem_id: str = "smoke_dummy", **overrides: Any) -> dict[str, Any]:
    payload = dict(
        problem_id=problem_id,
        system_name="KUR",
        formula_id="KUR",
        split="validation",
        condition="dry_run",
        true_formula_raw="omega + aggr(sin(sour(x)-targ(x)))",
        true_formula_canonical="add,omega,aggr,sin,sub,sour,x,targ,x",
        true_formula_skeleton="add,omega,aggr,sin,sub,sour,x,targ,x",
        pred_formula_raw="omega",
        pred_formula_canonical="omega",
        pred_formula_skeleton="omega",
        fit_error=1.0,
        exact=0.0,
        skeleton=0.0,
        symbolic_equivalent=0.0,
        ted_raw=4.0,
        ted_skeleton=4.0,
        complexity=1.0,
        valid=True,
        failure_reason=None,
        search_nodes=0,
        candidate_count=1,
        wall_time=0.0,
        prefix=["omega"],
    )
    payload.update(overrides)
    return make_formula_record(**payload)


def missing_required_fields(record: Mapping[str, Any]) -> list[str]:
    return sorted(GPU_RUN3_REQUIRED_FIELDS - set(record))
