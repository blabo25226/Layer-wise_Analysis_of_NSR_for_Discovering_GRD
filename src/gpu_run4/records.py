"""GPU_RUN4 formula records and failure-aware schema."""

from __future__ import annotations

from typing import Any, Mapping

GPU_RUN4_REQUIRED_FIELDS = frozenset(
    {
        "campaign",
        "problem_id",
        "benchmark",
        "system_name",
        "dimension",
        "split",
        "condition",
        "true_formula_raw",
        "true_formula_prefix",
        "true_formula_canonical",
        "true_formula_skeleton",
        "candidate_index",
        "candidate_formula_raw",
        "candidate_formula_canonical",
        "candidate_formula_skeleton",
        "selected",
        "reconstruction_r2",
        "generalization_r2",
        "canonical_exact",
        "skeleton_exact",
        "symbolic_equivalent",
        "ted_raw",
        "ted_skeleton",
        "complexity",
        "valid",
        "failure_reason",
        "wall_time",
        "beam_size",
        "beam_temperature",
    }
)

GPU_RUN4_LAYER_FIELDS = frozenset(
    {
        "module_name",
        "module_group",
        "layer_index",
        "analysis_type",
    }
)

FAILURE_REASONS = (
    "CheckpointDownloadError",
    "CheckpointLoadError",
    "ArchitectureMismatch",
    "OfficialConfigMismatch",
    "InputRescaleError",
    "BeamDecodeTimeout",
    "InvalidPrefix",
    "ParseError",
    "CandidateIntegrationFailure",
    "GeneralizationIntegrationFailure",
    "ConstantOptimizationFailure",
    "NaN",
    "Inf",
    "SymbolicEquivalenceTimeout",
    "TEDParseError",
    "TEDTimeout",
    "ActivationHookError",
    "ActivationPatchError",
    "OOM",
    "MissingPhase0",
    "MissingCheckpoint",
    "CUDAUnavailable",
)


def make_formula_record(
    *,
    problem_id: str,
    benchmark: str = "",
    system_name: str = "",
    dimension: int | None = None,
    split: str = "validation",
    condition: str = "",
    true_formula_raw: str = "",
    true_formula_prefix: str = "",
    true_formula_canonical: str = "",
    true_formula_skeleton: str = "",
    candidate_index: int | None = None,
    candidate_formula_raw: str = "",
    candidate_formula_canonical: str = "",
    candidate_formula_skeleton: str = "",
    selected: bool | None = None,
    reconstruction_r2: float | None = None,
    generalization_r2: float | None = None,
    canonical_exact: float | None = None,
    skeleton_exact: float | None = None,
    symbolic_equivalent: float | None = None,
    ted_raw: float | None = None,
    ted_skeleton: float | None = None,
    complexity: float | None = None,
    valid: bool | None = None,
    failure_reason: str | None = None,
    wall_time: float | None = None,
    beam_size: int | None = None,
    beam_temperature: float | None = None,
    **extra: Any,
) -> dict[str, Any]:
    record = {
        "campaign": "GPU_RUN4",
        "problem_id": problem_id,
        "benchmark": benchmark,
        "system_name": system_name,
        "dimension": dimension,
        "split": split,
        "condition": condition,
        "true_formula_raw": true_formula_raw,
        "true_formula_prefix": true_formula_prefix,
        "true_formula_canonical": true_formula_canonical,
        "true_formula_skeleton": true_formula_skeleton,
        "candidate_index": candidate_index,
        "candidate_formula_raw": candidate_formula_raw,
        "candidate_formula_canonical": candidate_formula_canonical,
        "candidate_formula_skeleton": candidate_formula_skeleton,
        "selected": selected,
        "reconstruction_r2": reconstruction_r2,
        "generalization_r2": generalization_r2,
        "canonical_exact": canonical_exact,
        "skeleton_exact": skeleton_exact,
        "symbolic_equivalent": symbolic_equivalent,
        "ted_raw": ted_raw,
        "ted_skeleton": ted_skeleton,
        "complexity": complexity,
        "valid": valid,
        "failure_reason": failure_reason,
        "wall_time": wall_time,
        "beam_size": beam_size,
        "beam_temperature": beam_temperature,
    }
    record.update(extra)
    missing = GPU_RUN4_REQUIRED_FIELDS - set(record)
    if missing:
        raise ValueError(f"GPU_RUN4 formula record missing fields: {sorted(missing)}")
    return record


def dummy_formula_record(problem_id: str = "smoke_dummy", **overrides: Any) -> dict[str, Any]:
    payload = dict(
        problem_id=problem_id,
        benchmark="official_demo",
        system_name="harmonic_oscillator_demo",
        dimension=2,
        split="validation",
        condition="dry_run",
        true_formula_raw="x_0' = -x_1 | x_1' = x_0",
        true_formula_prefix="sub,0,x_1 | x_0",
        true_formula_canonical="neg(x_1)|x_0",
        true_formula_skeleton="neg(x_1)|x_0",
        candidate_index=0,
        candidate_formula_raw="x_0",
        candidate_formula_canonical="x_0",
        candidate_formula_skeleton="x_0",
        selected=True,
        reconstruction_r2=0.0,
        generalization_r2=0.0,
        canonical_exact=0.0,
        skeleton_exact=0.0,
        symbolic_equivalent=0.0,
        ted_raw=4.0,
        ted_skeleton=4.0,
        complexity=1.0,
        valid=True,
        failure_reason=None,
        wall_time=0.0,
        beam_size=50,
        beam_temperature=0.1,
    )
    payload.update(overrides)
    return make_formula_record(**payload)


def missing_required_fields(record: Mapping[str, Any]) -> list[str]:
    return sorted(GPU_RUN4_REQUIRED_FIELDS - set(record))


def missing_layer_fields(record: Mapping[str, Any]) -> list[str]:
    return sorted(GPU_RUN4_LAYER_FIELDS - set(record))


def dummy_layer_record(module_name: str = "encoder_0", **overrides: Any) -> dict[str, Any]:
    payload = {
        "module_name": module_name,
        "module_group": "encoder",
        "layer_index": 0,
        "analysis_type": "inventory",
    }
    payload.update(overrides)
    return payload
