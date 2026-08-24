"""Deterministic, CPU-only aggregation for GPU_RUN5 Phase 9.

Phase 9 is intentionally a reader.  It verifies every GPU_RUN5 JSON artifact
against the producing phase manifest before using it, never opens a sealed
test file, and treats an absent or unsupported upstream schema as
``undecidable`` rather than inventing a value.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


OUTCOMES = ("P3", "P4", "P5", "P6", "P7", "R4", "R5")
FINAL_CONDITIONS = (
    "frozen",
    "official_continued_full",
    "grn_full",
    "grn_top3",
    "grn_random3_0",
)


def strict_json(path: Path) -> Any:
    """Load RFC-compatible JSON and reject NaN/Infinity tokens."""

    def reject(value: str) -> None:
        raise ValueError(f"non-finite JSON token {value!r} in {path}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class Artifact:
    phase: int
    name: str
    path: Path
    sha256: str
    value: Any


class ArtifactError(RuntimeError):
    """An available upstream artifact failed its provenance contract."""


class Catalog:
    """Manifest-verified access to one GPU_RUN5 run directory."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = Path(run_dir).resolve()
        self._manifests: dict[int, Mapping[str, Any] | None] = {}
        self.audit: list[dict[str, Any]] = []

    def manifest(self, phase: int) -> Mapping[str, Any] | None:
        if phase in self._manifests:
            return self._manifests[phase]
        path = self.run_dir / f"phase{phase}" / "manifest.json"
        if not path.is_file():
            self._manifests[phase] = None
            self.audit.append({"phase": phase, "name": "manifest.json", "status": "missing"})
            return None
        value = strict_json(path)
        if not isinstance(value, Mapping):
            raise ArtifactError(f"Phase {phase} manifest must be an object")
        if value.get("campaign") not in (None, "GPU_RUN5") or int(value.get("phase", phase)) != phase:
            raise ArtifactError(f"Phase {phase} manifest identity mismatch")
        self._manifests[phase] = value
        self.audit.append(
            {
                "phase": phase,
                "name": "manifest.json",
                "status": "loaded",
                "sha256": sha256_file(path),
                "phase_status": value.get("status"),
                "substage": value.get("substage"),
            }
        )
        return value

    def artifact(self, phase: int, name: str, *, required: bool = False) -> Artifact | None:
        manifest = self.manifest(phase)
        path = self.run_dir / f"phase{phase}" / name
        if manifest is None or not path.is_file():
            if required:
                raise ArtifactError(f"required Phase {phase} artifact missing: {name}")
            self.audit.append({"phase": phase, "name": name, "status": "missing"})
            return None
        hashes = manifest.get("artifact_sha256") or {}
        expected = hashes.get(name) if isinstance(hashes, Mapping) else None
        # Phase 8 keeps the immutable validation freeze under a dedicated key
        # after replacing the validation manifest with the final-test manifest.
        if phase == 8 and name == "final_condition_freeze.json" and expected is None:
            expected = manifest.get("final_condition_freeze_sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            if required:
                raise ArtifactError(f"Phase {phase}/{name} has no signed manifest hash")
            self.audit.append({"phase": phase, "name": name, "status": "unsigned"})
            return None
        observed = sha256_file(path)
        if observed != expected:
            raise ArtifactError(f"Phase {phase}/{name} hash mismatch")
        value = strict_json(path)
        self.audit.append(
            {"phase": phase, "name": name, "status": "verified", "sha256": observed}
        )
        return Artifact(phase, name, path, observed, value)


def _source(artifact: Artifact) -> dict[str, Any]:
    return {
        "phase": artifact.phase,
        "artifact": artifact.name,
        "sha256": artifact.sha256,
    }


def _outcome(
    prediction_id: str,
    registration: Mapping[str, Any],
    *,
    hit: bool | None,
    observed: Any,
    sources: Sequence[Artifact],
    reason: str | None = None,
) -> dict[str, Any]:
    return {
        "id": prediction_id,
        "kind": "forward_prediction" if prediction_id.startswith("P") else "retrospective_hypothesis",
        "registration": dict(registration),
        "observed": observed,
        "outcome": "undecidable" if hit is None else ("hit" if hit else "miss"),
        "reason": reason,
        "sources": [_source(value) for value in sources],
    }


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _lexicographic_better(left: Sequence[Any], right: Sequence[Any]) -> bool | None:
    if len(left) < 3 or len(right) < 3:
        return None
    lhs = tuple(_finite_number(value) for value in left[:3])
    rhs = tuple(_finite_number(value) for value in right[:3])
    if any(value is None for value in lhs + rhs):
        return None
    return tuple(round(value, 12) for value in lhs) > tuple(round(value, 12) for value in rhs)


def evaluate_preregistration(catalog: Catalog) -> dict[str, Any]:
    """Evaluate P3--P7 and R4--R5 from their signed source artifacts."""

    prereg_art = catalog.artifact(0, "preregistration.json", required=True)
    assert prereg_art is not None
    phase0_manifest = catalog.manifest(0)
    if not isinstance(phase0_manifest, Mapping) or phase0_manifest.get("status") != "complete":
        raise ArtifactError("Phase 0 registration manifest is not complete")
    prereg = prereg_art.value
    if not isinstance(prereg, Mapping):
        raise ArtifactError("preregistration.json must be an object")
    predictions = prereg.get("predictions")
    retros = prereg.get("retrospective_hypotheses")
    if not isinstance(predictions, Mapping) or set(predictions) != {"P3", "P4", "P5", "P6", "P7"}:
        raise ArtifactError("forward preregistration IDs differ from fixed P3--P7")
    if not isinstance(retros, Mapping) or set(retros) != {"R4", "R5"}:
        raise ArtifactError("retrospective IDs differ from fixed R4--R5")

    support_art = catalog.artifact(1, "decoded_support.json")
    p6_art = catalog.artifact(3, "p6_validation.json")
    p5_art = catalog.artifact(5, "p5.json")
    p8_art = catalog.artifact(8, "final_result.json")
    forgetting_art = catalog.artifact(8, "odebench_forgetting_summary.json")
    forgetting_audit_art = catalog.artifact(8, "odebench_forgetting_audit.json")
    p8_outcomes_art = catalog.artifact(8, "preregistered_test_outcomes.json")
    p8_manifest = catalog.manifest(8)
    phase_manifests = {phase: catalog.manifest(phase) for phase in (1, 3, 5)}
    if not isinstance(phase_manifests[1], Mapping) or phase_manifests[1].get("status") != "complete":
        support_art = None
    if not isinstance(phase_manifests[3], Mapping) or phase_manifests[3].get("status") != "complete":
        p6_art = None
    if not isinstance(phase_manifests[5], Mapping) or phase_manifests[5].get("status") != "complete":
        p5_art = None
    outcomes: dict[str, dict[str, Any]] = {}

    if support_art is None or not isinstance(support_art.value, Mapping):
        for key in ("R4", "R5"):
            outcomes[key] = _outcome(
                key, retros[key], hit=None, observed=None, sources=[],
                reason="Phase 1 decoded-support artifact is unavailable or unsupported",
            )
    else:
        support = support_art.value
        r4_value = _finite_number(support.get("candidate_variable_denominator_rate"))
        r4_threshold = _finite_number(retros["R4"].get("threshold"))
        outcomes["R4"] = _outcome(
            "R4", retros["R4"],
            hit=(None if r4_value is None or r4_threshold is None else r4_value >= r4_threshold),
            observed={"candidate_variable_denominator_rate": r4_value},
            sources=[support_art],
            reason=None if r4_value is not None else "registered Phase 1 metric is absent",
        )
        r5_value = support.get("variable_denominator_selected_exponent_exact_count")
        r5_threshold = retros["R5"].get("threshold")
        r5_valid = isinstance(r5_value, int) and not isinstance(r5_value, bool)
        outcomes["R5"] = _outcome(
            "R5", retros["R5"],
            hit=(None if not r5_valid else r5_value == r5_threshold),
            observed={
                "exact_count": r5_value if r5_valid else None,
                "n_cells": support.get("variable_denominator_cell_count"),
                "candidate_truth_support_count": support.get(
                    "variable_denominator_group_true_exponent_skeleton_in_beam_count"
                ),
            },
            sources=[support_art],
            reason=None if r5_valid else "registered Phase 1 exact-count metric is absent",
        )
        saved_retrospective = support.get("retrospective_outcomes")
        if isinstance(saved_retrospective, Mapping):
            for key in ("R4", "R5"):
                saved = saved_retrospective.get(key)
                derived = outcomes[key]["outcome"] == "hit"
                if isinstance(saved, Mapping) and saved.get("passed") is not derived:
                    raise ArtifactError(f"Phase 1 saved {key} outcome disagrees with Phase 9 recomputation")

    if p5_art is None or not isinstance(p5_art.value, Mapping):
        outcomes["P5"] = _outcome(
            "P5", predictions["P5"], hit=None, observed=None, sources=[],
            reason="Phase 5 P5 artifact is unavailable or unsupported",
        )
    else:
        row = p5_art.value
        rho = _finite_number(row.get("rho"))
        threshold = _finite_number(predictions["P5"].get("threshold"))
        determinate = row.get("determinate") is True and rho is not None
        outcomes["P5"] = _outcome(
            "P5", predictions["P5"],
            hit=(rho <= threshold if determinate and threshold is not None else None),
            observed={
                "rho": rho,
                "p_value_two_sided": _finite_number(row.get("p_value_two_sided")),
                "n_layers": row.get("n_layers"),
                "determinate": row.get("determinate"),
            },
            sources=[p5_art],
            reason=None if determinate else str(row.get("reason") or "P5 is not determinate"),
        )

    if p6_art is None or not isinstance(p6_art.value, Mapping):
        outcomes["P6"] = _outcome(
            "P6", predictions["P6"], hit=None, observed=None, sources=[],
            reason="Phase 3 paired P6 artifact is unavailable or unsupported",
        )
    else:
        row = p6_art.value
        upper = _finite_number(row.get("ci95_upper"))
        threshold = _finite_number(predictions["P6"].get("threshold"))
        outcomes["P6"] = _outcome(
            "P6", predictions["P6"],
            hit=(None if upper is None or threshold is None else upper < threshold),
            observed={
                "mean_clustered_difference": _finite_number(row.get("mean_clustered_difference")),
                "student_t_95_ci": row.get("student_t_95_ci"),
                "ci95_upper": upper,
                "n_system_clusters": row.get("n_system_clusters"),
            },
            sources=[p6_art],
            reason=None if upper is not None else "registered P6 CI upper bound is absent",
        )

    final_available = (
        p8_art is not None
        and isinstance(p8_art.value, Mapping)
        and p8_art.value.get("status") == "complete"
        and p8_art.value.get("test_accessed") is True
        and p8_outcomes_art is not None
        and isinstance(p8_outcomes_art.value, Mapping)
        and p8_outcomes_art.value.get("schema_version")
        == "gpu_run5_phase8_preregistered_test_outcomes_v1"
        and p8_outcomes_art.value.get("test_accessed") is True
        and isinstance(p8_manifest, Mapping)
        and p8_manifest.get("status") == "complete"
        and p8_manifest.get("substage") == "final-test"
        and p8_manifest.get("test_open_count") == 1
    )
    if not final_available:
        reason = "Phase 8 final test was not opened under the single-open protocol"
        for key in ("P3", "P4", "P7"):
            outcomes[key] = _outcome(
                key, predictions[key], hit=None, observed=None, sources=[], reason=reason
            )
    else:
        final = p8_art.value
        event_ids = {
            final.get("test_open_event_id"),
            p8_outcomes_art.value.get("test_open_event_id"),
            p8_manifest.get("test_open_event_id"),
        }
        if None in event_ids or len(event_ids) != 1:
            raise ArtifactError("Phase 8 final-test open-event identity is inconsistent")
        summaries = final.get("summaries")
        main = summaries.get("main") if isinstance(summaries, Mapping) else None
        frozen = main.get("frozen") if isinstance(main, Mapping) else None
        if not isinstance(frozen, Mapping):
            p3_hit = None
            exact_rate = None
            p3_reason = "Phase 8 main/frozen summary is absent"
        else:
            exact_rate = _finite_number(
                frozen.get("component_exponent_aware_skeleton_exact_system_then_seed_macro")
            )
            if exact_rate is None:
                score = frozen.get("formula_score_vector_without_ce") or []
                exact_rate = _finite_number(score[0]) if isinstance(score, Sequence) and score else None
            threshold = _finite_number(predictions["P3"].get("threshold"))
            p3_hit = None if exact_rate is None or threshold is None else exact_rate < threshold
            p3_reason = None if exact_rate is not None else "Phase 8 frozen exact rate is absent"
        outcomes["P3"] = _outcome(
            "P3", predictions["P3"], hit=p3_hit,
            observed={"component_exponent_aware_skeleton_exact_system_then_seed_macro": exact_rate},
            sources=[p8_art, p8_outcomes_art], reason=p3_reason,
        )
        recon = _finite_number(frozen.get("reconstruction_r2_median")) if isinstance(frozen, Mapping) else None
        p4_clause = (predictions["P4"].get("clauses") or [{}])[0]
        p4_threshold = _finite_number(p4_clause.get("threshold")) if isinstance(p4_clause, Mapping) else None
        p4_hit = None if recon is None or p4_threshold is None or p3_hit is None else recon >= p4_threshold and p3_hit
        outcomes["P4"] = _outcome(
            "P4", predictions["P4"], hit=p4_hit,
            observed={"reconstruction_r2_median": recon, "P3_hit": p3_hit},
            sources=[p8_art, p8_outcomes_art],
            reason=None if p4_hit is not None else "P4 requires both the frozen reconstruction median and determinate P3",
        )

        top = main.get("grn_top3") if isinstance(main, Mapping) else None
        full = main.get("grn_full") if isinstance(main, Mapping) else None
        formula_better = None
        if isinstance(top, Mapping) and isinstance(full, Mapping):
            formula_better = _lexicographic_better(
                top.get("formula_score_vector_without_ce") or [],
                full.get("formula_score_vector_without_ce") or [],
            )
        forgetting_better = None
        forgetting_observed: dict[str, Any] = {}
        if forgetting_art is not None and isinstance(forgetting_art.value, Mapping):
            frows = forgetting_art.value
            fr = frows.get("frozen")
            tr = frows.get("grn_top3")
            ar = frows.get("grn_full")
            if all(isinstance(value, Mapping) for value in (fr, tr, ar)):
                frozen_exact = _finite_number(
                    fr.get("exponent_aware_skeleton_exact_system_then_seed_macro", fr.get("exponent_aware_skeleton_exact_rate"))
                )
                top_exact = _finite_number(
                    tr.get("exponent_aware_skeleton_exact_system_then_seed_macro", tr.get("exponent_aware_skeleton_exact_rate"))
                )
                full_exact = _finite_number(
                    ar.get("exponent_aware_skeleton_exact_system_then_seed_macro", ar.get("exponent_aware_skeleton_exact_rate"))
                )
                if None not in (frozen_exact, top_exact, full_exact):
                    top_drop = _finite_number(
                        tr.get("paired_exponent_aware_skeleton_drop_from_frozen_system_then_seed_macro")
                    )
                    full_drop = _finite_number(
                        ar.get("paired_exponent_aware_skeleton_drop_from_frozen_system_then_seed_macro")
                    )
                    pairing_valid = (
                        tr.get("paired_cell_identity_matches_frozen") is True
                        and ar.get("paired_cell_identity_matches_frozen") is True
                        and forgetting_audit_art is not None
                        and isinstance(forgetting_audit_art.value, Mapping)
                        and forgetting_audit_art.value.get("pass") is True
                    )
                    if (
                        top_drop is not None and full_drop is not None and pairing_valid
                        and math.isclose(top_drop, frozen_exact - top_exact, abs_tol=1e-12)
                        and math.isclose(full_drop, frozen_exact - full_exact, abs_tol=1e-12)
                    ):
                        forgetting_better = top_drop < full_drop
                    forgetting_observed = {
                        "frozen_exact_rate": frozen_exact,
                        "grn_top3_exact_rate": top_exact,
                        "grn_full_exact_rate": full_exact,
                        "grn_top3_drop": top_drop,
                        "grn_full_drop": full_drop,
                        "paired_cell_identity_and_audit_valid": pairing_valid,
                    }
        p7_hit = None if formula_better is None or forgetting_better is None else formula_better and forgetting_better
        # Phase 8 emits its own preregistered adapter next to the raw summaries.
        # Recompute independently above, then fail closed if the two disagree.
        phase8_registered = p8_outcomes_art.value
        if (
            None in (p3_hit, p4_hit, p7_hit, exact_rate, recon)
            or not isinstance(top, Mapping)
            or not isinstance(full, Mapping)
        ):
            raise ArtifactError("Phase 8 final-test schema is incomplete for P3/P4/P7")
        registered_p3 = phase8_registered.get("P3") or {}
        registered_p4 = phase8_registered.get("P4") or {}
        registered_p7 = phase8_registered.get("P7") or {}
        exact_fields_match = (
            _finite_number(registered_p3.get("value")) is not None
            and math.isclose(float(registered_p3["value"]), float(exact_rate), abs_tol=1e-12)
        )
        recon_fields_match = (
            _finite_number(registered_p4.get("reconstruction_r2_median")) is not None
            and math.isclose(float(registered_p4["reconstruction_r2_median"]), float(recon), abs_tol=1e-12)
        )
        p7_fields_match = (
            list(registered_p7.get("grn_top3_formula_score") or [])
            == [round(float(value), 12) for value in (top.get("formula_score_vector_without_ce") or [])]
            and list(registered_p7.get("grn_full_formula_score") or [])
            == [round(float(value), 12) for value in (full.get("formula_score_vector_without_ce") or [])]
            and _finite_number(registered_p7.get("odebench_grn_top3_drop_from_frozen")) == forgetting_observed.get("grn_top3_drop")
            and _finite_number(registered_p7.get("odebench_grn_full_drop_from_frozen")) == forgetting_observed.get("grn_full_drop")
        )
        if not (exact_fields_match and recon_fields_match and p7_fields_match):
            raise ArtifactError("Phase 8 preregistered metric fields disagree with raw summaries")
        recomputed = {"P3": p3_hit, "P4": p4_hit, "P7": p7_hit}
        for prediction_id, supported in recomputed.items():
            registered = phase8_registered.get(prediction_id)
            if not isinstance(registered, Mapping) or registered.get("supported") is not supported:
                raise ArtifactError(
                    f"Phase 8 registered {prediction_id} outcome disagrees with Phase 9 recomputation"
                )
            expected_word = "hit" if supported else "miss"
            if registered.get("outcome") != expected_word:
                raise ArtifactError(f"Phase 8 {prediction_id} outcome label is inconsistent")
        sources = [p8_art, p8_outcomes_art] + ([forgetting_art] if forgetting_art is not None else []) + ([forgetting_audit_art] if forgetting_audit_art is not None else [])
        outcomes["P7"] = _outcome(
            "P7", predictions["P7"], hit=p7_hit,
            observed={
                "grn_top3_formula_better_than_grn_full": formula_better,
                "formula_vectors": {
                    "grn_top3": top.get("formula_score_vector_without_ce") if isinstance(top, Mapping) else None,
                    "grn_full": full.get("formula_score_vector_without_ce") if isinstance(full, Mapping) else None,
                },
                "odebench_forgetting": forgetting_observed or None,
                "grn_top3_forgetting_less_than_grn_full": forgetting_better,
            },
            sources=sources,
            reason=None if p7_hit is not None else "P7 requires Phase 8 formula vectors and signed ODEBench exponent-aware exact rates",
        )

    ordered = [outcomes[key] for key in OUTCOMES]
    return {
        "schema_version": "gpu_run5_preregistration_outcome_v1",
        "campaign": "GPU_RUN5",
        "registration_source": _source(prereg_art),
        "outcomes": ordered,
        "counts": {
            name: sum(row["outcome"] == name for row in ordered)
            for name in ("hit", "miss", "undecidable")
        },
        "test_firewall": {
            "phase8_final_test_available": final_available,
            "phase8_substage": p8_manifest.get("substage") if isinstance(p8_manifest, Mapping) else None,
            "phase8_test_open_count": p8_manifest.get("test_open_count") if isinstance(p8_manifest, Mapping) else None,
            "sealed_test_files_read_by_phase9": False,
        },
    }


def _mean(values: Iterable[Any]) -> float | None:
    finite = [value for item in values if (value := _finite_number(item)) is not None]
    return statistics.fmean(finite) if finite else None


def _top3(values: Any) -> list[str]:
    if isinstance(values, Mapping):
        values = values.get("ranking")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    return [str(value).removeprefix("iole::") for value in values[:3]]


def _jaccard(left: Sequence[str], right: Sequence[str]) -> float | None:
    union = set(left) | set(right)
    return len(set(left) & set(right)) / len(union) if union else None


def cross_run_synthesis(repo_root: Path, catalog: Catalog) -> dict[str, Any]:
    """Adapt within-run rankings without putting incompatible scores on one scale."""

    runs_root = repo_root / "results" / "runs"
    rows: list[dict[str, Any]] = []

    def historical(label: str, model: str, generation: str, paths: Mapping[str, str], adapter: str) -> None:
        resolved = {key: runs_root / value for key, value in paths.items()}
        if not all(path.is_file() for path in resolved.values()):
            rows.append({
                "run": label, "model": model, "generation": generation,
                "status": "unavailable", "reason": "one or more historical source artifacts are absent",
                "sources": [{"path": path.as_posix()} for path in resolved.values()],
            })
            return
        parse_policy = "strict_json"
        try:
            values = {key: strict_json(path) for key, path in resolved.items()}
        except ValueError:
            # GPU_RUN2 predates the repository-wide strict-JSON contract and
            # contains NaN in unrelated diagnostic fields.  Track E needs only
            # its finite rank lists.  Preserve that legacy fact explicitly,
            # convert non-finite tokens to null, and never use a converted
            # numeric value in the synthesis.
            parse_policy = "legacy_nonfinite_tokens_converted_to_null_rank_lists_only"
            values = {
                key: json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda _token: None)
                for key, path in resolved.items()
            }
        if adapter == "gpu2":
            rank = values["rankings"]
            probe, causal, iole = _top3(rank.get("probe")), _top3(rank.get("intervention")), _top3(rank.get("iole"))
            caveat = "saved ablation/intervention order is robustness-oriented; not causal-importance order"
        elif adapter == "gpu3":
            probe = _top3(values["phase4"].get("probe_rank_next_symbol"))
            causal, iole = _top3(values["phase6"].get("intervention_rank")), _top3(values["phase6"].get("iole_rank"))
            caveat = "four-block architecture; k=3 random control is combinatorially weak"
        else:
            rank = values["result_b"]
            probe, causal, iole = _top3(rank.get("probe_ranking")), _top3(rank.get("causal_ranking")), _top3(rank.get("iole_ranking"))
            caveat = "reduced one-seed run; causal and IOLE outcomes are teacher-forcing CE"
        rows.append({
            "run": label, "model": model, "generation": generation, "status": "available",
            "probe_top3": probe, "causal_top3": causal, "iole_top3": iole,
            "probe_causal_top3_jaccard": _jaccard(probe, causal),
            "causal_iole_top3_jaccard": _jaccard(causal, iole),
            "probe_iole_top3_jaccard": _jaccard(probe, iole),
            "caveat": caveat,
            "sources": [{"path": path.relative_to(repo_root).as_posix(), "sha256": sha256_file(path), "provenance": "content_hashed_at_phase9_not_manifest_signed", "parse_policy": parse_policy} for path in resolved.values()],
        })

    historical(
        "GPU_RUN2", "NeSymReS", "GPU_RUN2 fixed full run",
        {"rankings": "gpu_run2_20260815_1d91927/phase4/rankings.json"}, "gpu2",
    )
    historical(
        "GPU_RUN3", "NDformer", "GPU_RUN3 full run",
        {
            "phase4": "gpu_run3_full_20260817/phase4/summary.json",
            "phase6": "gpu_run3_full_20260817/phase6/summary.json",
        }, "gpu3",
    )
    historical(
        "GPU_RUN4", "ODEFormer", "GPU_RUN4 reduced public-checkpoint run",
        {"result_b": "gpu_run4_phase0_01/phase9/result_b.json"}, "gpu4",
    )

    probes = catalog.artifact(4, "probes.json")
    layer_freeze = catalog.artifact(7, "layer_freeze.json")
    causal = catalog.artifact(5, "causal_ranking.json")
    if (
        probes is None or layer_freeze is None or causal is None
        or not isinstance(probes.value, Mapping)
        or not isinstance(layer_freeze.value, Mapping)
        or not isinstance(causal.value, Mapping)
    ):
        rows.append({
            "run": "GPU_RUN5", "model": "ODEFormer", "generation": "GPU_RUN5 fixed run",
            "status": "unavailable", "reason": "Phase 7 rankings are not yet available", "sources": [],
        })
    else:
        probe_scores = {}
        decoder_token = probes.value.get("decoder_token") or {}
        if isinstance(decoder_token, Mapping):
            for layer, attributes in decoder_token.items():
                next_token = attributes.get("next_token") if isinstance(attributes, Mapping) else None
                probe_row = next_token.get("probe") if isinstance(next_token, Mapping) else None
                control = next_token.get("label_shuffle_control") if isinstance(next_token, Mapping) else None
                score = _finite_number(probe_row.get("accuracy")) if isinstance(probe_row, Mapping) else None
                baseline = _finite_number(control.get("accuracy")) if isinstance(control, Mapping) else None
                if score is not None and baseline is not None:
                    probe_scores[str(layer)] = score - baseline
        probe = [layer for layer, _score in sorted(probe_scores.items(), key=lambda item: (-item[1], item[0]))[:3]]
        causal_top = _top3(causal.value.get("ranking"))
        frozen_views = layer_freeze.value.get("views") or {}
        frozen_main = frozen_views.get("main") if isinstance(frozen_views, Mapping) else {}
        iole = _top3(frozen_main.get("iole_formula_ranking") if isinstance(frozen_main, Mapping) else None)
        rows.append({
            "run": "GPU_RUN5", "model": "ODEFormer", "generation": "GPU_RUN5 fixed run",
            "status": "available", "probe_top3": probe, "causal_top3": causal_top, "iole_top3": iole,
            "probe_causal_top3_jaccard": _jaccard(probe, causal_top),
            "causal_iole_top3_jaccard": _jaccard(causal_top, iole),
            "probe_iole_top3_jaccard": _jaccard(probe, iole),
            "caveat": "next-token probe-minus-shuffle, causal intervention, and formula-level IOLE have distinct estimands",
            "sources": [_source(probes), _source(layer_freeze), _source(causal)],
        })
    return {
        "schema_version": "gpu_run5_cross_run_synthesis_v1",
        "comparison_policy": "within-run rank disagreement only; metric magnitudes and layer identities are never compared across models or generations",
        "rows": rows,
    }


def aggregate_results(catalog: Catalog, prereg: Mapping[str, Any], cross_run: Mapping[str, Any]) -> dict[str, Any]:
    support = catalog.artifact(1, "decoded_support.json")
    phase3 = catalog.artifact(3, "summary.json")
    funnel3 = catalog.artifact(3, "failure_funnel.json")
    phase4 = catalog.artifact(4, "summary.json")
    phase5 = catalog.artifact(5, "summary.json")
    funnel5 = catalog.artifact(5, "failure_funnel.json")
    phase6 = catalog.artifact(6, "summary.json")
    phase7 = catalog.artifact(7, "summary.json")
    phase8 = catalog.artifact(8, "final_result.json")
    return {
        "schema_version": "gpu_run5_phase9_results_v1",
        "A_decoded_support": support.value if support is not None else {"status": "unavailable"},
        "B_grn_generation_selection": {
            "summary": phase3.value if phase3 is not None else {"status": "unavailable"},
            "failure_funnel": funnel3.value if funnel3 is not None else None,
        },
        "C_grn_adaptation": {
            "phase6": phase6.value if phase6 is not None else {"status": "unavailable"},
            "phase7": phase7.value if phase7 is not None else {"status": "unavailable"},
            "phase8": phase8.value if phase8 is not None else {"status": "test_not_opened_or_unavailable"},
        },
        "D_layer_analysis": {
            "phase4": phase4.value if phase4 is not None else {"status": "unavailable"},
            "phase5": phase5.value if phase5 is not None else {"status": "unavailable"},
            "failure_funnel": funnel5.value if funnel5 is not None else None,
        },
        "E_cross_model_synthesis": cross_run,
        "preregistration": prereg,
    }


def formula_examples(catalog: Catalog, *, limit_each: int = 5) -> list[dict[str, Any]]:
    """Return deterministic successes and failures, retaining true/predicted equations."""
    selected_art = catalog.artifact(3, "selected.json")
    systems_art = catalog.artifact(2, "validation.json")
    if selected_art is None or systems_art is None or not isinstance(selected_art.value, list) or not isinstance(systems_art.value, list):
        return []
    systems = {str(row.get("system_id")): row for row in systems_art.value if isinstance(row, Mapping)}
    rows = [row for row in selected_art.value if isinstance(row, Mapping) and row.get("selection_rule") == "multi_ic_complexity"]
    rows.sort(key=lambda row: str(row.get("cell_id")))
    successes = [row for row in rows if float(row.get("exponent_aware_skeleton_exact") or 0.0) == 1.0 and row.get("valid") is True]
    failures = [row for row in rows if row.get("valid") is not True or row.get("failure_reason")]
    structural = [row for row in rows if row.get("valid") is True and float(row.get("exponent_aware_skeleton_exact") or 0.0) == 0.0]
    chosen = [("success", row) for row in successes[:limit_each]]
    chosen += [("generation_or_evaluation_failure", row) for row in failures[:limit_each]]
    chosen += [("valid_but_structurally_wrong", row) for row in structural[:limit_each]]
    output = []
    for category, row in chosen:
        system = systems.get(str(row.get("system_id")), {})
        output.append({
            "source_phase": 3,
            "category": category,
            "cell_id": row.get("cell_id"),
            "family": row.get("family"),
            "true_formula": system.get("teacher_infix"),
            "predicted_formula_raw": row.get("candidate_formula_raw"),
            "predicted_formula_canonical": row.get("candidate_formula_canonical"),
            "variable_to_gene": system.get("variable_to_gene"),
            "valid": row.get("valid"),
            "failure_reason": row.get("failure_reason"),
            "exponent_aware_skeleton_exact": row.get("exponent_aware_skeleton_exact"),
            "normalized_variable_aware_ted": row.get("normalized_variable_aware_ted"),
            "input_r2_mean": _mean((row.get("trajectory_metrics") or {}).get("input_r2", [])),
            "generalization_r2_mean": _mean((row.get("trajectory_metrics") or {}).get("generalization_r2", [])),
        })
    failure_count = sum(row["category"] == "generation_or_evaluation_failure" for row in output)
    if failure_count < limit_each:
        # Phase 3 may return a valid selected expression in every validation
        # cell even though candidate generation/evaluation failures exist.
        # Add concrete ODEBench failure expressions from Track A so the report
        # never turns "no selected GRN failure" into "no failure observed".
        odebench_art = catalog.artifact(1, "selected_annotated.json")
        if odebench_art is not None and isinstance(odebench_art.value, list):
            failed = [
                row for row in odebench_art.value
                if isinstance(row, Mapping)
                and (row.get("valid") is not True or row.get("failure_reason"))
            ]
            failed.sort(key=lambda row: (str(row.get("problem_id")), str(row.get("noise_sigma")), str(row.get("subsample_rho"))))
            for row in failed[: limit_each - failure_count]:
                output.append({
                    "source_phase": 1,
                    "category": "generation_or_evaluation_failure",
                    "cell_id": f"{row.get('problem_id')}|n{row.get('noise_sigma')}|r{row.get('subsample_rho')}",
                    "family": "ODEBench",
                    "true_formula": row.get("true_formula_raw"),
                    "predicted_formula_raw": row.get("candidate_formula_raw"),
                    "predicted_formula_canonical": row.get("candidate_formula_canonical"),
                    "variable_to_gene": None,
                    "valid": row.get("valid"),
                    "failure_reason": row.get("failure_reason"),
                    "exponent_aware_skeleton_exact": row.get("exponent_aware_skeleton_exact"),
                    "normalized_variable_aware_ted": row.get("normalized_ted"),
                    "input_r2_mean": _finite_number(row.get("reconstruction_r2")),
                    "generalization_r2_mean": _finite_number(row.get("generalization_r2")),
                })
    return output


def failure_rows(catalog: Catalog) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for phase in (3, 5):
        artifact = catalog.artifact(phase, "failure_funnel.json")
        if artifact is None or not isinstance(artifact.value, Mapping):
            continue
        for key, value in sorted(artifact.value.items()):
            if isinstance(value, Mapping):
                count = value.get("count", value.get("n"))
            else:
                count = value
            rows.append({"phase": phase, "failure_stage": key, "count": count})
    return rows


def condition_rows(catalog: Catalog) -> list[dict[str, Any]]:
    artifact = catalog.artifact(8, "final_result.json")
    if artifact is None or not isinstance(artifact.value, Mapping):
        return []
    summaries = artifact.value.get("summaries")
    rows = []
    if not isinstance(summaries, Mapping):
        return rows
    for view, values in summaries.items():
        if not isinstance(values, Mapping):
            continue
        for condition, metrics in values.items():
            if isinstance(metrics, Mapping):
                row = {"view": view, "condition": condition, **{key: value for key, value in metrics.items() if not isinstance(value, (dict, list))}}
                if isinstance(metrics.get("formula_score_vector_without_ce"), list):
                    row["formula_score_vector_without_ce"] = metrics["formula_score_vector_without_ce"]
                rows.append(row)
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], *, fields: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = sorted({str(key) for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in row.items()})


def _svg(path: Path, title: str, lines: Sequence[str], *, points: Sequence[tuple[float, float, str]] = ()) -> None:
    """Write a dependency-free deterministic SVG summary."""
    width, height = 960, max(360, 130 + 28 * len(lines))
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#fbfbf8"/>', f'<text x="36" y="52" font-family="sans-serif" font-size="25" font-weight="bold">{html.escape(title)}</text>']
    for index, line in enumerate(lines):
        body.append(f'<text x="42" y="{95 + index * 28}" font-family="monospace" font-size="15">{html.escape(str(line))}</text>')
    if points:
        finite = [(x, y, label) for x, y, label in points if math.isfinite(x) and math.isfinite(y)]
        if finite:
            xmin, xmax = min(x for x, _, _ in finite), max(x for x, _, _ in finite)
            ymin, ymax = min(y for _, y, _ in finite), max(y for _, y, _ in finite)
            xspan, yspan = max(xmax - xmin, 1e-12), max(ymax - ymin, 1e-12)
            top = 120 + len(lines) * 28
            plot_h = max(120, height - top - 35)
            body.append(f'<rect x="90" y="{top}" width="820" height="{plot_h}" fill="white" stroke="#555"/>')
            for x, y, label in finite:
                px = 90 + 820 * (x - xmin) / xspan
                py = top + plot_h - plot_h * (y - ymin) / yspan
                body.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4" fill="#2b6cb0"><title>{html.escape(label)}</title></circle>')
    body.append("</svg>\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")


def write_figures(catalog: Catalog, figures: Path, cross_run: Mapping[str, Any]) -> list[Path]:
    figures.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    failures = failure_rows(catalog)
    path = figures / "phase9_failure_funnel.svg"
    _svg(path, "Generation → selection → integration failure funnel", [f"phase {row['phase']} | {row['failure_stage']} | {row['count']}" for row in failures] or ["undecidable: failure artifacts unavailable"])
    outputs.append(path)

    groups_art = catalog.artifact(3, "beam_groups.json")
    selected_family_art = catalog.artifact(3, "selected.json")
    family_lines = []
    if groups_art is not None and isinstance(groups_art.value, list):
        grouped: dict[str, list[float]] = defaultdict(list)
        for row in groups_art.value:
            if isinstance(row, Mapping):
                grouped[str(row.get("family"))].append(float(bool(row.get("true_exponent_aware_skeleton_in_beam"))))
        selected_grouped: dict[str, list[float]] = defaultdict(list)
        if selected_family_art is not None and isinstance(selected_family_art.value, list):
            for row in selected_family_art.value:
                if isinstance(row, Mapping) and row.get("selection_rule") == "multi_ic_complexity":
                    selected_grouped[str(row.get("family"))].append(
                        float(row.get("exponent_aware_skeleton_exact") or 0.0)
                    )
        family_lines = [
            f"{family}: truth-in-beam={statistics.fmean(values):.4f}; selected-exact={statistics.fmean(selected_grouped.get(family) or [0.0]):.4f} (n={len(values)})"
            for family, values in sorted(grouped.items())
        ]
    path = figures / "phase9_family_generation_recovery.svg"
    _svg(path, "Family-level true structure in beam", family_lines or ["undecidable: Phase 3 beam groups unavailable"])
    outputs.append(path)

    p6_art = catalog.artifact(3, "p6_validation.json")
    p6_points = []
    p6_lines = ["undecidable: paired P6 artifact unavailable"]
    if p6_art is not None and isinstance(p6_art.value, Mapping):
        p6_lines = [f"cluster mean difference={p6_art.value.get('mean_clustered_difference')}", f"Student-t 95% CI={p6_art.value.get('student_t_95_ci')}"]
        for row in p6_art.value.get("paired_cell_differences") or []:
            if isinstance(row, Mapping):
                x, y = _finite_number(row.get("official_reconstruction_nrmse")), _finite_number(row.get("multi_ic_nrmse"))
                if x is not None and y is not None:
                    p6_points.append((x, y, str(row.get("system_id"))))
    path = figures / "phase9_single_vs_multi_ic.svg"
    _svg(path, "Single-trajectory vs multi-IC failure-aware NRMSE", p6_lines, points=p6_points)
    outputs.append(path)

    conditions = condition_rows(catalog)
    path = figures / "phase9_final_condition_formula_scores.svg"
    _svg(path, "Frozen / continued / full / selective / random", [f"{row.get('view')} | {row.get('condition')} | exact={row.get('component_exponent_aware_skeleton_exact_rate')} | TED={row.get('failure_aware_component_ted_mean')} | valid={row.get('component_valid_rate')}" for row in conditions] or ["undecidable: final test was not opened"])
    outputs.append(path)

    lens = catalog.artifact(4, "decoder_logit_lens.json")
    probe_art = catalog.artifact(4, "probes.json")
    lens_lines = ["undecidable: DecoderLens artifact unavailable"]
    if lens is not None and isinstance(lens.value, Mapping):
        grouped: dict[str, list[float]] = defaultdict(list)
        for row in lens.value.get("formula_rows") or []:
            if isinstance(row, Mapping):
                value = _finite_number(row.get("normalized_variable_aware_ted"))
                if value is not None:
                    grouped[str(row.get("layer"))].append(value)
        next_token: dict[str, float] = {}
        decoder_token = probe_art.value.get("decoder_token") if probe_art is not None and isinstance(probe_art.value, Mapping) else None
        if isinstance(decoder_token, Mapping):
            for layer, attrs in decoder_token.items():
                row = attrs.get("next_token") if isinstance(attrs, Mapping) else None
                metric = row.get("probe") if isinstance(row, Mapping) else None
                value = _finite_number(metric.get("accuracy")) if isinstance(metric, Mapping) else None
                if value is not None:
                    next_token[str(layer)] = value
        lens_lines = [
            f"{layer}: next-token accuracy={_fmt(next_token.get(layer))}; median variable-aware TED={statistics.median(values):.4f} (n={len(values)})"
            for layer, values in sorted(grouped.items())
        ]
    path = figures / "phase9_decoder_depth_ted.svg"
    _svg(path, "Decoder depth and intermediate formula TED", lens_lines)
    outputs.append(path)

    selected = catalog.artifact(3, "selected.json")
    recon_points, ic_points = [], []
    if selected is not None and isinstance(selected.value, list):
        for row in selected.value:
            if not isinstance(row, Mapping) or row.get("selection_rule") != "multi_ic_complexity":
                continue
            metrics = row.get("trajectory_metrics") or {}
            r2 = _mean(metrics.get("input_r2", []))
            ted = _finite_number(row.get("normalized_variable_aware_ted"))
            inp = _mean(metrics.get("input_nrmse", []))
            gen = _mean(metrics.get("generalization_nrmse", []))
            if r2 is not None and ted is not None:
                recon_points.append((r2, ted, str(row.get("cell_id"))))
            if inp is not None and gen is not None:
                ic_points.append((inp, gen, str(row.get("cell_id"))))
    path = figures / "phase9_reconstruction_vs_ted.svg"
    _svg(path, "Reconstruction fit versus structural TED", [f"n={len(recon_points)}; each point is one validation cell"], points=recon_points)
    outputs.append(path)
    path = figures / "phase9_input_vs_generalization.svg"
    _svg(path, "Input-IC versus generalization-IC NRMSE", [f"n={len(ic_points)}; candidate selection never used generalization IC"], points=ic_points)
    outputs.append(path)

    effects = catalog.artifact(5, "layer_effects.json")
    p5_points = []
    if effects is not None and isinstance(effects.value, Mapping):
        for layer, row in effects.value.items():
            if isinstance(row, Mapping):
                x, y = _finite_number(row.get("damage_ce")), _finite_number(row.get("failure_aware_ted_increase"))
                if x is not None and y is not None:
                    p5_points.append((x, y, str(layer)))
    path = figures / "phase9_delta_ce_vs_delta_ted.svg"
    _svg(path, "Layer intervention: ΔCE versus ΔTED", [f"n_layers={len(p5_points)}; higher means more damage for both registered ranks"], points=p5_points)
    outputs.append(path)

    efficiency_points: list[tuple[float, float, str]] = []
    efficiency_lines: list[str] = []
    final_by_condition = {
        str(row.get("condition")): row
        for row in conditions if row.get("view") == "main"
    }
    training: dict[str, list[tuple[float, float]]] = defaultdict(list)
    phase6_training = catalog.artifact(6, "confirmation_training_index.json")
    if phase6_training is not None and isinstance(phase6_training.value, list):
        for row in phase6_training.value:
            if isinstance(row, Mapping) and row.get("view") == "main":
                params, wall = _finite_number(row.get("trainable_parameters")), _finite_number(row.get("wall_time_sec"))
                if params is not None and wall is not None:
                    training[str(row.get("condition"))].append((params, wall))
    phase8_training = catalog.artifact(8, "selective_checkpoint_index.json")
    if phase8_training is not None and isinstance(phase8_training.value, list):
        for row in phase8_training.value:
            details = row.get("training") if isinstance(row, Mapping) else None
            if isinstance(row, Mapping) and row.get("view") == "main" and isinstance(details, Mapping):
                params, wall = _finite_number(details.get("trainable_parameters")), _finite_number(details.get("wall_time_sec"))
                if params is not None and wall is not None:
                    training[str(row.get("condition"))].append((params, wall))
    training["frozen"] = [(0.0, 0.0)]
    for condition, entries in sorted(training.items()):
        result = final_by_condition.get(condition)
        exact = None
        if isinstance(result, Mapping):
            exact = _finite_number(result.get("component_exponent_aware_skeleton_exact_system_then_seed_macro"))
            if exact is None:
                vector = result.get("formula_score_vector_without_ce") or []
                exact = _finite_number(vector[0]) if isinstance(vector, Sequence) and vector else None
        if exact is None:
            continue
        params = statistics.fmean(value[0] for value in entries)
        wall = statistics.fmean(value[1] for value in entries)
        efficiency_points.append((params, exact, condition))
        efficiency_lines.append(f"{condition}: trainable={params:.0f}; mean training wall={wall:.3f}s; exact macro={exact:.4f}")
    path = figures / "phase9_efficiency_pareto.svg"
    _svg(path, "Efficiency / recovery Pareto", efficiency_lines or ["undecidable: no final recovery joined to signed training records"], points=efficiency_points)
    outputs.append(path)

    cross_lines = []
    for row in cross_run.get("rows") or []:
        cross_lines.append(f"{row.get('run')} ({row.get('model')}): probe∩causal={row.get('probe_causal_top3_jaccard')}; causal∩IOLE={row.get('causal_iole_top3_jaccard')}; probe∩IOLE={row.get('probe_iole_top3_jaccard')}")
    path = figures / "phase9_cross_run_rank_disagreement.svg"
    _svg(path, "Within-run rank disagreement across generations", cross_lines or ["historical artifacts unavailable"])
    outputs.append(path)
    return outputs


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def render_reports(
    repo_root: Path,
    *,
    run_id: str,
    results: Mapping[str, Any],
    prereg: Mapping[str, Any],
    examples: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    """Render the five reports with fact/RQ/discussion/limits/proposals split."""
    out = {row["id"]: row for row in prereg["outcomes"]}
    a = results["A_decoded_support"]
    b = results["B_grn_generation_selection"]
    c = results["C_grn_adaptation"]
    d = results["D_layer_analysis"]
    e = results["E_cross_model_synthesis"]
    example_lines = [
        f"| {row.get('category')} | {row.get('cell_id')} | `{row.get('true_formula')}` | `{row.get('predicted_formula_raw')}` | {_fmt(row.get('failure_reason'))} |"
        for row in examples[:10]
    ] or ["| — | — | — | — | upstream formula records unavailable |"]
    phase8_summaries = (c.get("phase8") or {}).get("summaries") if isinstance(c.get("phase8"), Mapping) else None
    adaptation_lines = []
    if isinstance(phase8_summaries, Mapping):
        for view, values in phase8_summaries.items():
            if not isinstance(values, Mapping):
                continue
            for condition, metrics in values.items():
                if isinstance(metrics, Mapping):
                    adaptation_lines.append(
                        f"| {view} | {condition} | {_fmt(metrics.get('component_exponent_aware_skeleton_exact_system_then_seed_macro', (metrics.get('formula_score_vector_without_ce') or [None])[0]))} | {_fmt(metrics.get('failure_aware_component_ted_mean'))} | {_fmt(metrics.get('component_valid_rate'))} | {_fmt(metrics.get('reconstruction_r2_median'))} |"
                    )
    if not adaptation_lines:
        adaptation_lines = ["| — | test not opened | — | — | — | — |"]
    reports = {
        "GPU_RUN5_decoded_support_report.md": f"""# GPU_RUN5 decoded support report（Result A）

Run: `{run_id}`。数値はmanifest hashで検証した保存済みrecordだけから生成した。

## 事実

- candidate数: {_fmt(a.get('candidate_count') if isinstance(a, Mapping) else None)}
- variable-denominator candidate率: {_fmt(a.get('candidate_variable_denominator_rate') if isinstance(a, Mapping) else None)}
- 変数分母56 cellのselected exponent-aware exact件数: {_fmt(a.get('variable_denominator_selected_exponent_exact_count') if isinstance(a, Mapping) else None)}
- R1 truth form component counts: `{json.dumps(a.get('truth_form_component_counts') if isinstance(a, Mapping) else None, ensure_ascii=False, sort_keys=True)}`
- R2 support denominators: `{json.dumps(a.get('support_denominators') if isinstance(a, Mapping) else None, ensure_ascii=False, sort_keys=True)}`
- R3 rational-with-variable-denominator vs other: `{json.dumps(a.get('selected_rational_vs_other') if isinstance(a, Mapping) else None, ensure_ascii=False, sort_keys=True)}`
- R4: **{out['R4']['outcome']}**、R5: **{out['R5']['outcome']}**。

## RQ判定

Result Aは、モデルが変数分母候補を出せるかと、その候補から正しい指数込み構造を選べるかを分ける。R4/R5の機械判定は `phase9/preregistration_outcome.json` を正とする。

## 考察

候補内supportは事前学習分布そのものの証明ではなく、固定beam・固定corruption下のdecoded supportである。

## 限界

GPU_RUN4の保存済み252 cell再解析であり、新規推論ではない。selected成功例だけでなく全failureを集計へ残した。

## 未実施提案

beam budgetを変える追試は次runとして事前固定し、本runへ事後追加しない。
""",
        "GPU_RUN5_grn_benchmark_report.md": f"""# GPU_RUN5 GRN benchmark report（Result B）

Run: `{run_id}`。

## 事実

- Phase 3 status: {_fmt((b.get('summary') or {{}}).get('status'))}
- validation cells: {_fmt((b.get('summary') or {{}}).get('n_cells'))}
- true exponent-aware skeleton in beam率: {_fmt((b.get('summary') or {{}}).get('true_exponent_aware_skeleton_in_beam_rate'))}
- P6: **{out['P6']['outcome']}**、観測値: `{json.dumps(out['P6']['observed'], ensure_ascii=False, sort_keys=True)}`
- P3: **{out['P3']['outcome']}**、P4: **{out['P4']['outcome']}**。test未開封なら両者は判定不能のまま残す。

## 代表式（成功と失敗を同時掲載）

| 種別 | cell | 真式 | 予測生式 | failure |
|---|---|---|---|---|
{chr(10).join(example_lines)}

変数とsynthetic gene名の対応を含む全例は `graphs/{run_id}/tables/phase9_formula_examples.csv` に保存した。

## RQ判定

P6はsystem-cluster単位のpaired Student-t 95%区間で判定する。P3/P4はPhase 8 main testのfrozen条件を一度だけ開いた場合だけ判定する。

## 考察

数値fitと指数込み構造回復は別結果として読む。family-holdout R07/R08はmain testの部分集合であり、独立な第二testではない。

## 限界

failure-aware penaltyを主集計へ含め、valid式だけの条件付き性能と混同しない。

## 未実施提案

追加ICや探索budgetの変更は本test後に選び直さず、次campaignで固定する。
""",
        "GPU_RUN5_grn_adaptation_report.md": f"""# GPU_RUN5 GRN adaptation report（Result C）

Run: `{run_id}`。

## 事実

- Phase 6: {_fmt((c.get('phase6') or {{}}).get('status'))}
- Phase 7: {_fmt((c.get('phase7') or {{}}).get('status'))}
- Phase 8: {_fmt((c.get('phase8') or {{}}).get('status'))}
- P7: **{out['P7']['outcome']}**、観測値: `{json.dumps(out['P7']['observed'], ensure_ascii=False, sort_keys=True)}`

| view | condition | exact macro | failure-aware TED | valid rate | recon R2 median |
|---|---|---:|---:|---:|---:|
{chr(10).join(adaptation_lines)}

## RQ判定

P7はmain testで `grn_top3` と `grn_full` のformula scoreを事前順序でlexicographic比較し、同時にODEBench exponent-aware exactのfrozenからの低下を比較する。片方でも欠ければ判定不能である。

## 考察

official-continuedは追加学習一般、GRN fullはdomain adaptation、selectiveは適応先の効果を分ける対照である。

## 限界

ODEBench forgettingはsecondary outcomeで選択に使っていない。異なるモデル・世代の絶対scoreは比較しない。

## 未実施提案

Go 6不成立でtestを開かなかった場合、P3/P4/P7を埋めるためだけの事後条件追加は行わない。
""",
        "GPU_RUN5_layer_analysis_report.md": f"""# GPU_RUN5 layer analysis report（Result D）

Run: `{run_id}`。

## 事実

- Phase 4 status: {_fmt((d.get('phase4') or {{}}).get('status'))}
- Phase 5 status: {_fmt((d.get('phase5') or {{}}).get('status'))}
- main causal top3: `{json.dumps((d.get('phase5') or {{}}).get('main_causal_top3'), ensure_ascii=False)}`
- P5: **{out['P5']['outcome']}**、観測値: `{json.dumps(out['P5']['observed'], ensure_ascii=False, sort_keys=True)}`

## RQ判定

P5は16層の介入後 `damage_CE` とfailure-aware `TED increase` の順位相関である。相関が小さいことは「無相関の証明」ではなく、固定panel上でCE順位がsymbolic順位の十分な代理でなかったという限定的結果である。

## 考察

probe、DecoderLens、activation intervention、IOLEは異なるestimandを測るため、一つの重要度へ平均しない。

## 限界

exact lossが全層tieの場合、TED/validが順位を決める。少数panel・共有system依存を残す。

## 未実施提案

別panelで順位安定性を追試するときは確認panelで順位を再選択しない。
""",
        "GPU_RUN5_cross_model_synthesis.md": f"""# GPU_RUN5 cross-model synthesis（Result E）

Run: `{run_id}`。対象はGPU_RUN2 NeSymReS、GPU_RUN3 NDformer、GPU_RUN4/5 ODEFormerである。

## 事実

| run | model | generation | probe top3 | causal top3 | IOLE top3 | status |
|---|---|---|---|---|---|---|
{chr(10).join('| {run} | {model} | {generation} | `{probe}` | `{causal}` | `{iole}` | {status} |'.format(run=row.get('run'), model=row.get('model'), generation=row.get('generation'), probe=json.dumps(row.get('probe_top3'), ensure_ascii=False), causal=json.dumps(row.get('causal_top3'), ensure_ascii=False), iole=json.dumps(row.get('iole_top3'), ensure_ascii=False), status=row.get('status')) for row in e.get('rows', []))}

## RQ判定

横断表は各run内の順位不一致だけを比較する。モデル間で層番号、score強度、CE、TEDを同一尺度へ置かない。

## 考察

「読み出せる」「壊すと悪化する」「更新すると改善する」は別概念であり、世代ごとの不一致は単一の普遍的重要層を支持しない。

## 限界

GPU_RUN2の保存ablation/intervention順位は重要度と逆向きのrobustness順位という既知問題があり、GPU_RUN4はreduced一seedである。表にgenerationを明示して混在を防いだ。

## 未実施提案

同一corpus・同一定義・同一budgetによるモデル横断実験は別campaignとして設計する。
""",
    }
    return reports
