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
from typing import Any, Iterable, Iterator, Mapping, Sequence


OUTCOMES = ("P3", "P4", "P5", "P6", "P7", "R4", "R5")
FINAL_CONDITIONS = (
    "frozen",
    "official_continued_full",
    "grn_full",
    "grn_top3",
    "grn_random3_0",
)
P6_EXPECTED_CELLS = 960
P6_EXPECTED_SYSTEM_CLUSTERS = 80
P5_EXPECTED_LAYERS = frozenset(
    [f"encoder_{index}" for index in range(4)]
    + [f"decoder_{index}" for index in range(12)]
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
        self._derived: dict[str, Any] = {}
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
        if manifest is None:
            if path.is_file():
                raise ArtifactError(f"Phase {phase}/{name} exists without a producer manifest")
            if required:
                raise ArtifactError(f"required Phase {phase} artifact missing: {name}")
            self.audit.append({"phase": phase, "name": name, "status": "missing"})
            return None
        hashes = manifest.get("artifact_sha256") or {}
        advertised = isinstance(hashes, Mapping) and name in hashes
        expected = hashes.get(name) if advertised else None
        # Phase 8 keeps the immutable validation freeze under a dedicated key
        # after replacing the validation manifest with the final-test manifest.
        if phase == 8 and name == "final_condition_freeze.json" and expected is None:
            expected = manifest.get("final_condition_freeze_sha256")
            advertised = expected is not None
        if advertised and (not isinstance(expected, str) or len(expected) != 64):
            raise ArtifactError(f"Phase {phase}/{name} has a malformed advertised hash")
        if advertised and not path.is_file():
            raise ArtifactError(f"Phase {phase}/{name} is signed by the manifest but missing")
        if manifest.get("status") != "complete":
            if required:
                raise ArtifactError(f"required Phase {phase} producer is not complete: {name}")
            self.audit.append(
                {
                    "phase": phase,
                    "name": name,
                    "status": "producer_incomplete",
                    "phase_status": manifest.get("status"),
                }
            )
            return None
        if not path.is_file():
            if required:
                raise ArtifactError(f"required Phase {phase} artifact missing: {name}")
            self.audit.append({"phase": phase, "name": name, "status": "missing"})
            return None
        if not isinstance(expected, str) or len(expected) != 64:
            raise ArtifactError(f"Phase {phase}/{name} exists without a signed manifest hash")
        observed = sha256_file(path)
        if observed != expected:
            raise ArtifactError(f"Phase {phase}/{name} hash mismatch")
        value = strict_json(path)
        self.audit.append(
            {"phase": phase, "name": name, "status": "verified", "sha256": observed}
        )
        return Artifact(phase, name, path, observed, value)

    def indexed_json(
        self, phase: int, index_name: str, *, required: bool = False
    ) -> Iterator[tuple[Mapping[str, Any], Mapping[str, Any]]]:
        """Stream JSON shards from a signed index with full path provenance checks.

        The producer index is itself manifest-signed.  Every row must describe
        one unique, confined regular file using its exact byte size and SHA256.
        Callers therefore never glob a phase directory or trust a path embedded
        in a shard.
        """
        index_art = self.artifact(phase, index_name, required=required)
        if index_art is None:
            return
        if not isinstance(index_art.value, list):
            raise ArtifactError(f"Phase {phase}/{index_name} must be a list")
        phase_root = (self.run_dir / f"phase{phase}").resolve()
        seen: set[str] = set()
        verified = 0
        for position, row in enumerate(index_art.value):
            if not isinstance(row, Mapping):
                raise ArtifactError(
                    f"Phase {phase}/{index_name}[{position}] must be an object"
                )
            relative = row.get("path")
            expected_sha = row.get("sha256")
            expected_bytes = row.get("bytes")
            if (
                not isinstance(relative, str)
                or not relative
                or Path(relative).is_absolute()
                or Path(relative).as_posix() != relative
                or ".." in Path(relative).parts
                or relative in seen
            ):
                raise ArtifactError(
                    f"Phase {phase}/{index_name} has an invalid or duplicate path: {relative!r}"
                )
            if (
                not isinstance(expected_sha, str)
                or len(expected_sha) != 64
                or any(character not in "0123456789abcdef" for character in expected_sha.lower())
                or isinstance(expected_bytes, bool)
                or not isinstance(expected_bytes, int)
                or expected_bytes < 0
            ):
                raise ArtifactError(
                    f"Phase {phase}/{index_name} has malformed size/hash metadata for {relative}"
                )
            seen.add(relative)
            unresolved = phase_root / relative
            if unresolved.is_symlink():
                raise ArtifactError(
                    f"Phase {phase}/{index_name} shard may not be a symlink: {relative}"
                )
            path = unresolved.resolve()
            try:
                path.relative_to(phase_root)
            except ValueError as error:
                raise ArtifactError(
                    f"Phase {phase}/{index_name} contains path traversal: {relative}"
                ) from error
            if not path.is_file():
                raise ArtifactError(
                    f"Phase {phase}/{index_name} shard is missing or not a regular file: {relative}"
                )
            if path.stat().st_size != expected_bytes:
                raise ArtifactError(
                    f"Phase {phase}/{index_name} byte-size mismatch: {relative}"
                )
            observed_sha = sha256_file(path)
            if observed_sha != expected_sha:
                raise ArtifactError(
                    f"Phase {phase}/{index_name} shard hash mismatch: {relative}"
                )
            value = strict_json(path)
            if not isinstance(value, Mapping):
                raise ArtifactError(
                    f"Phase {phase}/{index_name} shard must be an object: {relative}"
                )
            verified += 1
            yield row, value
        self.audit.append(
            {
                "phase": phase,
                "name": index_name,
                "status": "indexed_shards_verified",
                "sha256": index_art.sha256,
                "verified_shard_count": verified,
                "unique_paths": len(seen),
                "path_confinement": True,
                "byte_size_verified": True,
                "shard_sha256_verified": True,
            }
        )


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


def _phase8_ledger_audit(
    catalog: Catalog,
    *,
    manifest: Mapping[str, Any] | None,
    ledger_art: Artifact | None,
    final_art: Artifact | None,
    outcomes_art: Artifact | None,
) -> dict[str, Any]:
    """Validate durable Phase 8 single-open evidence without opening test data."""
    if not all(
        isinstance(value, Mapping)
        for value in (
            manifest,
            ledger_art.value if ledger_art is not None else None,
            final_art.value if final_art is not None else None,
            outcomes_art.value if outcomes_art is not None else None,
        )
    ):
        return {"pass": False, "reason": "signed Phase 8 ledger or final evidence is unavailable"}
    assert ledger_art is not None and final_art is not None and outcomes_art is not None
    assert isinstance(manifest, Mapping)
    ledger = ledger_art.value
    final = final_art.value
    registered = outcomes_art.value
    assert isinstance(ledger, Mapping) and isinstance(final, Mapping) and isinstance(registered, Mapping)

    event_ids = {
        ledger.get("event_id"),
        final.get("test_open_event_id"),
        registered.get("test_open_event_id"),
        manifest.get("test_open_event_id"),
    }
    manifest_hashes = manifest.get("artifact_sha256")
    ledger_final_hashes = ledger.get("final_artifact_sha256")
    ledger_sealed_hashes = ledger.get("sealed_artifact_sha256")
    manifest_sealed_hashes = manifest.get("sealed_artifact_sha256")
    sealed_hashes_well_formed = (
        isinstance(ledger_sealed_hashes, Mapping)
        and set(ledger_sealed_hashes) == {"main", "family_holdout"}
        and all(
            isinstance(digest, str)
            and len(digest) == 64
            and all(character in "0123456789abcdef" for character in digest.lower())
            for digest in ledger_sealed_hashes.values()
        )
    )
    expected_final_hashes = (
        {
            str(name): str(digest)
            for name, digest in manifest_hashes.items()
            if name != "test_open_ledger.json"
        }
        if isinstance(manifest_hashes, Mapping)
        else None
    )
    normalized_ledger_final = (
        {str(name): str(digest) for name, digest in ledger_final_hashes.items()}
        if isinstance(ledger_final_hashes, Mapping)
        else None
    )
    hashes_well_formed = bool(normalized_ledger_final) and all(
        Path(name).name == name
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest.lower())
        for name, digest in normalized_ledger_final.items()
    )
    basic_checks = {
        "schema_supported": ledger.get("schema_version") == "gpu_run5_phase8_test_open_ledger_v1",
        "ledger_complete": ledger.get("status") == "complete",
        "single_open_count": ledger.get("open_count") == 1,
        "final_result_single_open_count": final.get("test_open_count") == 1,
        "event_id_consistent": None not in event_ids and len(event_ids) == 1,
        "sealed_hashes_bound_to_manifest": (
            sealed_hashes_well_formed
            and dict(ledger_sealed_hashes) == dict(manifest_sealed_hashes or {})
        ),
        "final_hash_set_bound_to_manifest": (
            hashes_well_formed
            and normalized_ledger_final == expected_final_hashes
        ),
    }
    if not all(basic_checks.values()):
        failed = [name for name, passed in basic_checks.items() if not passed]
        return {"pass": False, "reason": f"Phase 8 ledger checks failed: {failed}", "checks": basic_checks}

    # Verify every final product bound by the ledger while deliberately never
    # resolving or reading ledger.sealed_paths.
    assert normalized_ledger_final is not None
    for name in sorted(normalized_ledger_final):
        catalog.artifact(8, name, required=True)
    return {
        "pass": True,
        "reason": None,
        "checks": basic_checks,
        "test_open_event_id": next(iter(event_ids)),
        "verified_final_artifact_count": len(normalized_ledger_final),
    }


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
    ledger_art = catalog.artifact(8, "test_open_ledger.json")
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
        r5_expected_n = retros["R5"].get("n_cells")
        r5_observed_n = support.get("variable_denominator_cell_count")
        r5_valid = (
            isinstance(r5_value, int) and not isinstance(r5_value, bool)
            and isinstance(r5_expected_n, int) and r5_observed_n == r5_expected_n
        )
        outcomes["R5"] = _outcome(
            "R5", retros["R5"],
            hit=(None if not r5_valid else r5_value == r5_threshold),
            observed={
                "exact_count": r5_value if r5_valid else None,
                "n_cells": r5_observed_n,
                "candidate_truth_support_count": support.get(
                    "variable_denominator_group_true_exponent_skeleton_in_beam_count"
                ),
            },
            sources=[support_art],
            reason=None if r5_valid else "registered Phase 1 exact count or exact 56-cell coverage is absent",
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
        layers = row.get("layers")
        exact_layer_inventory = (
            isinstance(layers, list)
            and len(layers) == len(P5_EXPECTED_LAYERS)
            and all(isinstance(layer, str) for layer in layers)
            and set(layers) == P5_EXPECTED_LAYERS
        )
        determinate = (
            row.get("determinate") is True and rho is not None
            and row.get("n_layers") == 16
            and row.get("expected_layer_count", 16) == 16
            and exact_layer_inventory
        )
        p5_hit = rho <= threshold if determinate and threshold is not None else None
        if p5_hit is not None and row.get("supported") is not p5_hit:
            raise ArtifactError("Phase 5 saved P5 outcome disagrees with Phase 9 recomputation")
        outcomes["P5"] = _outcome(
            "P5", predictions["P5"],
            hit=p5_hit,
            observed={
                "rho": rho,
                "p_value_two_sided": _finite_number(row.get("p_value_two_sided")),
                "n_layers": row.get("n_layers"),
                "layers": layers if exact_layer_inventory else None,
                "determinate": row.get("determinate"),
            },
            sources=[p5_art],
            reason=(
                None if determinate
                else (
                    str(row.get("reason") or "P5 is not determinate")
                    if exact_layer_inventory
                    else "P5 requires the exact unique encoder_0..3 and decoder_0..11 inventory"
                )
            ),
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
        interval = row.get("student_t_95_ci")
        paired = row.get("paired_cell_differences")
        paired_systems = {
            str(value.get("system_id"))
            for value in paired
            if isinstance(value, Mapping) and value.get("system_id") is not None
        } if isinstance(paired, list) else set()
        interval_valid = (
            isinstance(interval, Sequence) and len(interval) == 2
            and _finite_number(interval[0]) is not None
            and _finite_number(interval[1]) is not None
            and upper is not None
            and math.isclose(float(interval[1]), upper, abs_tol=1e-12)
            and row.get("n_cells") == P6_EXPECTED_CELLS
            and row.get("n_system_clusters") == P6_EXPECTED_SYSTEM_CLUSTERS
            and isinstance(paired, list) and len(paired) == P6_EXPECTED_CELLS
            and len(paired_systems) == P6_EXPECTED_SYSTEM_CLUSTERS
        )
        p6_hit = None if not interval_valid or threshold is None else upper < threshold
        if p6_hit is not None:
            expected_saved = "supported" if p6_hit else "not_supported"
            if row.get("prediction_P6") != expected_saved:
                raise ArtifactError("Phase 3 saved P6 outcome disagrees with Phase 9 recomputation")
        outcomes["P6"] = _outcome(
            "P6", predictions["P6"],
            hit=p6_hit,
            observed={
                "mean_clustered_difference": _finite_number(row.get("mean_clustered_difference")),
                "student_t_95_ci": row.get("student_t_95_ci"),
                "ci95_upper": upper,
                "n_system_clusters": row.get("n_system_clusters"),
            },
            sources=[p6_art],
            reason=None if interval_valid else "P6 requires the fixed 960 paired cells, 80 system clusters, and a consistent Student-t interval",
        )

    ledger_audit = _phase8_ledger_audit(
        catalog,
        manifest=p8_manifest,
        ledger_art=ledger_art,
        final_art=p8_art,
        outcomes_art=p8_outcomes_art,
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
        and ledger_audit["pass"] is True
    )
    if not final_available:
        reason = "Phase 8 final test was not opened under the single-open protocol"
        for key in ("P3", "P4", "P7"):
            outcomes[key] = _outcome(
                key, predictions[key], hit=None, observed=None, sources=[], reason=reason
            )
    else:
        final = p8_art.value
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
            sources=[p8_art, p8_outcomes_art, ledger_art], reason=p3_reason,
        )
        recon = _finite_number(frozen.get("reconstruction_r2_median")) if isinstance(frozen, Mapping) else None
        p4_clause = (predictions["P4"].get("clauses") or [{}])[0]
        p4_threshold = _finite_number(p4_clause.get("threshold")) if isinstance(p4_clause, Mapping) else None
        p4_hit = None if recon is None or p4_threshold is None or p3_hit is None else recon >= p4_threshold and p3_hit
        outcomes["P4"] = _outcome(
            "P4", predictions["P4"], hit=p4_hit,
            observed={"reconstruction_r2_median": recon, "P3_hit": p3_hit},
            sources=[p8_art, p8_outcomes_art, ledger_art],
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
        sources = [p8_art, p8_outcomes_art, ledger_art] + ([forgetting_art] if forgetting_art is not None else []) + ([forgetting_audit_art] if forgetting_audit_art is not None else [])
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
            "phase8_test_open_ledger": ledger_audit,
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
            probe, robustness, iole = _top3(rank.get("probe")), _top3(rank.get("intervention")), _top3(rank.get("iole"))
            causal = []
            caveat = "saved ablation/intervention order estimates robustness (least damage first), not causal importance; causal overlap is intentionally not computed"
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
            "robustness_top3": robustness if adapter == "gpu2" else [],
            "intervention_estimand": "robustness_least_damage" if adapter == "gpu2" else "causal_importance",
            "probe_causal_top3_jaccard": None if adapter == "gpu2" else _jaccard(probe, causal),
            "causal_iole_top3_jaccard": None if adapter == "gpu2" else _jaccard(causal, iole),
            "probe_iole_top3_jaccard": _jaccard(probe, iole),
            "probe_robustness_top3_jaccard": _jaccard(probe, robustness) if adapter == "gpu2" else None,
            "robustness_iole_top3_jaccard": _jaccard(robustness, iole) if adapter == "gpu2" else None,
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
            "robustness_top3": [], "intervention_estimand": "causal_importance",
            "probe_causal_top3_jaccard": _jaccard(probe, causal_top),
            "causal_iole_top3_jaccard": _jaccard(causal_top, iole),
            "probe_iole_top3_jaccard": _jaccard(probe, iole),
            "probe_robustness_top3_jaccard": None,
            "robustness_iole_top3_jaccard": None,
            "caveat": "next-token probe-minus-shuffle, causal intervention, and formula-level IOLE have distinct estimands",
            "sources": [_source(probes), _source(layer_freeze), _source(causal)],
        })
    return {
        "schema_version": "gpu_run5_cross_run_synthesis_v2",
        "comparison_policy": "within-run rank disagreement only; metric magnitudes and layer identities are never compared across models or generations",
        "rows": rows,
    }


def campaign_terminal_state(
    catalog: Catalog, *, phase8_final_test_available: bool
) -> dict[str, Any]:
    """Distinguish a valid terminal No-Go from an unfinished campaign."""
    phase_status = {}
    for phase in range(9):
        manifest = catalog.manifest(phase)
        phase_status[str(phase)] = manifest.get("status") if isinstance(manifest, Mapping) else "missing"
    incomplete = [int(key) for key, value in phase_status.items() if int(key) <= 7 and value != "complete"]
    phase8_manifest = catalog.manifest(8)
    if incomplete:
        return {
            "terminal": False,
            "state": "deferred_upstream_incomplete",
            "reason": f"required phases not complete: {incomplete}",
            "phase_status": phase_status,
        }
    if phase8_final_test_available:
        return {
            "terminal": True,
            "state": "reported_after_final_test",
            "reason": None,
            "phase_status": phase_status,
        }
    if (
        isinstance(phase8_manifest, Mapping)
        and phase8_manifest.get("status") == "complete"
        and phase8_manifest.get("substage") == "validation"
        and phase8_manifest.get("mode") == "full"
        and phase8_manifest.get("test_accessed") is False
    ):
        validation_art = catalog.artifact(8, "validation_summary.json")
        go6_art = catalog.artifact(8, "go6.json")
        go7_art = catalog.artifact(8, "go7.json")
        validation = validation_art.value if validation_art is not None else None
        go6 = go6_art.value if go6_art is not None else None
        go7 = go7_art.value if go7_art is not None else None
        if (
            isinstance(validation, Mapping)
            and isinstance(go6, Mapping)
            and isinstance(go7, Mapping)
            and validation.get("status") == "complete"
            and validation.get("mode") == "full"
            and validation.get("validation_complete") is True
            and validation.get("test_accessed") is False
            and validation.get("final_test_authorized") is False
            and phase8_manifest.get("final_test_authorized") is False
            and isinstance(validation.get("go6"), Mapping)
            and validation["go6"].get("pass") is False
            and validation.get("go6") == go6
            and validation.get("go7") == go7
            and go6.get("pass") is False
            and go6.get("test_accessed") is False
            and go7.get("pass") is False
            and go7.get("test_accessed") is False
        ):
            return {
                "terminal": True,
                "state": "reported_terminal_validation_no_go",
                "reason": "Go 6 failed under the full validation protocol; sealed test correctly remained unopened",
                "phase_status": phase_status,
            }
    return {
        "terminal": False,
        "state": "deferred_phase8_not_terminal",
        "reason": "Phase 8 final test is pending, incomplete, unsupported, or only smoke-validated",
        "phase_status": phase_status,
    }


def required_result_sources_available(
    catalog: Catalog, *, terminal_state: str
) -> dict[str, Any]:
    """Require the signed inputs needed for all five integrated results."""
    required = {
        0: ("preregistration.json",),
        1: ("decoded_support.json", "selected_annotated.json"),
        2: ("validation.json",),
        3: (
            "summary.json", "p6_validation.json", "failure_funnel.json",
            "failure_funnel_records.json", "selected.json", "beam_groups.json",
        ),
        4: (
            "summary.json", "probes.json", "decoder_logit_lens.json",
            "gradient_norms.json", "cka.json",
        ),
        5: ("summary.json", "p5.json", "failure_funnel.json", "layer_effects.json", "causal_ranking.json"),
        6: (
            "summary.json", "confirmation_summary.json",
            "confirmation_training_index.json", "cell_artifact_index.json",
        ),
        7: (
            "summary.json", "layer_freeze.json", "rank_stability.json",
            "iole_contribution.json", "auxiliary_rankings.json",
            "cell_artifact_index.json",
        ),
    }
    if terminal_state == "reported_after_final_test":
        required[8] = (
            "validation_protocol_frozen.json", "p6_for_go8.json",
            "selective_hyperparameter_freeze.json",
            "selective_confirmation_summary.json",
            "selective_checkpoint_index.json",
            "validation_condition_scores.json", "validation_summary.json",
            "go6.json", "go7.json", "final_condition_freeze.json",
            "validation_cell_artifact_index.json", "final_cell_artifact_index.json",
            "final_test_summary.json", "final_shard_audit.json", "final_result.json",
            "preregistered_test_outcomes.json",
            "odebench_forgetting_index.json",
            "odebench_forgetting_summary.json",
            "odebench_forgetting_audit.json",
            "test_open_ledger.json",
        )
    elif terminal_state == "reported_terminal_validation_no_go":
        required[8] = (
            "validation_protocol_frozen.json", "p6_for_go8.json",
            "selective_hyperparameter_freeze.json",
            "selective_confirmation_summary.json",
            "selective_checkpoint_index.json",
            "validation_condition_scores.json", "validation_summary.json",
            "go6.json", "go7.json",
            "validation_cell_artifact_index.json",
        )
    missing = []
    for phase, names in required.items():
        for name in names:
            if catalog.artifact(phase, name) is None:
                missing.append(f"phase{phase}/{name}")
    return {"pass": not missing, "missing": missing}


def _layer_analysis_result(catalog: Catalog) -> dict[str, Any]:
    """Build a compact, signed Track D summary without copying large row artifacts."""
    probes = catalog.artifact(4, "probes.json")
    lens = catalog.artifact(4, "decoder_logit_lens.json")
    gradients = catalog.artifact(4, "gradient_norms.json")
    cka = catalog.artifact(4, "cka.json")
    effects = catalog.artifact(5, "layer_effects.json")
    causal = catalog.artifact(5, "causal_ranking.json")
    phase7_summary = catalog.artifact(7, "summary.json")
    layer_freeze = catalog.artifact(7, "layer_freeze.json")
    rank_stability = catalog.artifact(7, "rank_stability.json")
    contribution = catalog.artifact(7, "iole_contribution.json")
    auxiliary = catalog.artifact(7, "auxiliary_rankings.json")

    probe_scores: dict[str, float] = {}
    if probes is not None and isinstance(probes.value, Mapping):
        decoder_token = probes.value.get("decoder_token")
        if isinstance(decoder_token, Mapping):
            for layer, tasks in decoder_token.items():
                next_token = tasks.get("next_token") if isinstance(tasks, Mapping) else None
                probe = next_token.get("probe") if isinstance(next_token, Mapping) else None
                shuffle = next_token.get("label_shuffle_control") if isinstance(next_token, Mapping) else None
                accuracy = _finite_number(probe.get("accuracy")) if isinstance(probe, Mapping) else None
                baseline = _finite_number(shuffle.get("accuracy")) if isinstance(shuffle, Mapping) else None
                if accuracy is not None and baseline is not None:
                    probe_scores[str(layer)] = accuracy - baseline
    probe_top3 = [
        {"layer": layer, "accuracy_minus_shuffle": value}
        for layer, value in sorted(probe_scores.items(), key=lambda item: (-item[1], item[0]))[:3]
    ]

    lens_by_layer: dict[str, list[float]] = defaultdict(list)
    lens_counts = {"formula_rows": None, "token_rows": None, "failure_count": None}
    if lens is not None and isinstance(lens.value, Mapping):
        formula_rows = lens.value.get("formula_rows")
        token_rows = lens.value.get("token_rows")
        failures = lens.value.get("failures")
        lens_counts = {
            "formula_rows": len(formula_rows) if isinstance(formula_rows, list) else None,
            "token_rows": len(token_rows) if isinstance(token_rows, list) else None,
            "failure_count": len(failures) if isinstance(failures, list) else None,
        }
        for row in formula_rows if isinstance(formula_rows, list) else []:
            if isinstance(row, Mapping):
                value = _finite_number(row.get("normalized_variable_aware_ted"))
                if value is not None:
                    lens_by_layer[str(row.get("layer"))].append(value)
    decoder_lens_ted = [
        {"layer": layer, "median_normalized_variable_aware_ted": statistics.median(values), "n": len(values)}
        for layer, values in sorted(lens_by_layer.items())
    ]

    gradient_top3 = []
    if gradients is not None and isinstance(gradients.value, Mapping):
        rows = gradients.value.get("layers")
        if isinstance(rows, Mapping):
            ranked = []
            for layer, row in rows.items():
                value = _finite_number(row.get("per_sqrt_parameter")) if isinstance(row, Mapping) else None
                if value is not None:
                    ranked.append((str(layer), value))
            gradient_top3 = [
                {"layer": layer, "per_sqrt_parameter": value}
                for layer, value in sorted(ranked, key=lambda item: (-item[1], item[0]))[:3]
            ]

    cka_summary: dict[str, Any] = {}
    if cka is not None and isinstance(cka.value, Mapping):
        for module in ("encoder", "decoder"):
            matrix = cka.value.get(module)
            off_diagonal = []
            if isinstance(matrix, list):
                for i, row in enumerate(matrix):
                    if isinstance(row, list):
                        off_diagonal.extend(
                            value for j, raw in enumerate(row)
                            if i != j and (value := _finite_number(raw)) is not None
                        )
            cka_summary[module] = {
                "n_layers": len(matrix) if isinstance(matrix, list) else None,
                "mean_off_diagonal": statistics.fmean(off_diagonal) if off_diagonal else None,
            }

    causal_top3 = _top3(causal.value.get("ranking")) if causal is not None and isinstance(causal.value, Mapping) else []
    top3_effects = {}
    if effects is not None and isinstance(effects.value, Mapping):
        for layer in causal_top3:
            row = effects.value.get(layer)
            if isinstance(row, Mapping):
                top3_effects[layer] = {
                    key: _finite_number(row.get(key))
                    for key in (
                        "damage_ce", "failure_aware_ted_increase",
                        "component_exact_loss", "component_valid_loss",
                        "generalization_r2_loss", "n_formula_pairs", "n_ce_pairs",
                    )
                }
    available = [
        artifact for artifact in (
            probes, lens, gradients, cka, effects, causal,
            phase7_summary, layer_freeze, rank_stability, contribution,
            auxiliary,
        ) if artifact is not None
    ]
    return {
        "observational": {
            "decoder_next_token_probe_top3": probe_top3,
            "decoder_lens": {"counts": lens_counts, "per_layer_ted": decoder_lens_ted},
            "gradient_norm_top3": gradient_top3,
            "within_module_cka": cka_summary,
        },
        "intervention": {
            "causal_top3": causal_top3,
            "causal_top3_layer_effects": top3_effects,
        },
        "formula_iole": {
            "freeze": layer_freeze.value if layer_freeze is not None else None,
            "rank_stability": rank_stability.value if rank_stability is not None else None,
            "raw_and_normalized_c_l": contribution.value if contribution is not None else None,
            "auxiliary_rankings": auxiliary.value if auxiliary is not None else None,
            "summary": phase7_summary.value if phase7_summary is not None else None,
            "estimand": (
                "failure-aware formula-score recovery from single-layer fine-tuning; "
                "normalized C_l is reported only where full fine-tuning improves frozen"
            ),
        },
        "signed_sources": [_source(artifact) for artifact in available],
        "figure_paths": [
            "figures/phase9_decoder_depth_ted.svg",
            "figures/phase9_delta_ce_vs_delta_ted.svg",
            "figures/phase9_cross_run_rank_disagreement.svg",
        ],
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
    phase8_validation = catalog.artifact(8, "validation_summary.json")
    phase8_final = catalog.artifact(8, "final_result.json")
    go6 = catalog.artifact(8, "go6.json")
    go7 = catalog.artifact(8, "go7.json")
    go8 = catalog.artifact(8, "go8.json")
    failure = failure_analysis(catalog)
    uncertainty = condition_uncertainty(catalog)
    support_result = (
        dict(support.value) if support is not None and isinstance(support.value, Mapping)
        else {"status": "unavailable"}
    )
    if support is not None and isinstance(support.value, Mapping):
        interval_specs = (
            ("candidate_variable_denominator", "candidate_variable_denominator_rate", "candidate_count", None),
            ("all_group_truth_in_beam", "all_group_true_exponent_skeleton_in_beam_rate", "selected_count", None),
            ("variable_group_truth_in_beam", None, "variable_denominator_group_count", "variable_denominator_group_true_exponent_skeleton_in_beam_count"),
            ("variable_selected_exponent_exact", None, "variable_denominator_cell_count", "variable_denominator_selected_exponent_exact_count"),
        )
        rate_intervals = {}
        for label, rate_key, total_key, count_key in interval_specs:
            total = support.value.get(total_key)
            if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
                raise ArtifactError(f"Phase 1 decoded support lacks valid denominator: {total_key}")
            if count_key is not None:
                successes = support.value.get(count_key)
                if isinstance(successes, bool) or not isinstance(successes, int):
                    raise ArtifactError(f"Phase 1 decoded support lacks valid count: {count_key}")
            else:
                rate = _finite_number(support.value.get(rate_key))
                if rate is None:
                    raise ArtifactError(f"Phase 1 decoded support lacks valid rate: {rate_key}")
                successes = int(round(rate * total))
                if abs(successes / total - rate) > 1e-12:
                    raise ArtifactError(f"Phase 1 decoded support rate/count mismatch: {rate_key}")
            rate_intervals[label] = {
                "successes": successes,
                "total": total,
                "rate": successes / total,
                "wilson_95_ci": _wilson_interval(successes, total),
                "interval_kind": "descriptive_naive_Bernoulli_interval",
            }
        support_result["rate_intervals"] = rate_intervals
    return {
        "schema_version": "gpu_run5_phase9_results_v2",
        "A_decoded_support": support_result,
        "B_grn_generation_selection": {
            "summary": phase3.value if phase3 is not None else {"status": "unavailable"},
            "failure_funnel": funnel3.value if funnel3 is not None else None,
            "uncertainty": uncertainty,
        },
        "C_grn_adaptation": {
            "phase6": phase6.value if phase6 is not None else {"status": "unavailable"},
            "phase7": phase7.value if phase7 is not None else {"status": "unavailable"},
            "phase8": (
                phase8_final.value if phase8_final is not None
                else phase8_validation.value if phase8_validation is not None
                else {"status": "unavailable"}
            ),
            "phase8_validation": (
                phase8_validation.value if phase8_validation is not None
                else {"status": "unavailable"}
            ),
            "phase8_final": (
                phase8_final.value if phase8_final is not None
                else {"status": "sealed_test_not_opened"}
            ),
            "go6": go6.value if go6 is not None else None,
            "go7": go7.value if go7 is not None else None,
            "go8": go8.value if go8 is not None else None,
            "sealed_test_remained_unopened": phase8_final is None,
            "uncertainty": uncertainty,
            "condition_metrics": condition_rows(catalog),
        },
        "D_layer_analysis": {
            "phase4": phase4.value if phase4 is not None else {"status": "unavailable"},
            "phase5": phase5.value if phase5 is not None else {"status": "unavailable"},
            "failure_funnel": funnel5.value if funnel5 is not None else None,
            **_layer_analysis_result(catalog),
        },
        "E_cross_model_synthesis": cross_run,
        "preregistration": prereg,
        "failure_analysis": failure,
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
    # Failure analysis already verified every Phase 6--8 shard.  Reuse its
    # deterministic, source-bound representatives instead of opening the same
    # multi-gigabyte indices a second time merely to find examples.
    shard_examples = failure_analysis(catalog).get("representative_formulas") or []
    output.extend(row for row in shard_examples if isinstance(row, Mapping))
    return output


FAILURE_EVENT_TYPES = (
    "timeout",
    "generation",
    "beam_shortfall",
    "parse",
    "ted",
    "nonfinite",
    "component",
    "trajectory",
)


def _failure_types(reason: Any) -> set[str]:
    text = str(reason or "").lower()
    # One saved reason receives one mutually exclusive primary taxonomy label.
    # Independent failures in different fields (for example formula parse and
    # trajectory integration) remain separate event identities.
    if "timeout" in text or "timed out" in text:
        return {"timeout"}
    if any(token in text for token in ("nonfinite", "non-finite", "nan", "inf")):
        return {"nonfinite"}
    if "ted" in text:
        return {"ted"}
    if "parse" in text or "syntax" in text:
        return {"parse"}
    if any(token in text for token in ("trajectory", "integration", "generalization")):
        return {"trajectory"}
    if "component" in text or "dimension" in text:
        return {"component"}
    if any(token in text for token in ("generation", "decode", "empty_beam", "empty beam")):
        return {"generation"}
    return set()


def _cell_identity(cell: Mapping[str, Any], relative: str) -> dict[str, str]:
    return {
        "view": str(cell.get("view") or "unknown"),
        "condition": str(cell.get("condition") or cell.get("layer") or "unknown"),
        "cell_id": str(cell.get("cell_id") or relative),
    }


def failure_analysis(catalog: Catalog) -> dict[str, Any]:
    """Integrate legacy funnels and Phase 6--8 shard failures without double counting.

    ``events`` are mutually unique issue identities; their ``selected`` flag is
    an attribute, not another event.  ``funnel`` is a separate denominator
    layer and therefore never gets summed as if it were an event count.
    """
    cached = catalog._derived.get("failure_analysis")
    if isinstance(cached, Mapping):
        return dict(cached)
    event_keys: set[tuple[Any, ...]] = set()
    events: list[dict[str, Any]] = []
    funnel: dict[tuple[int, str, str], dict[str, int]] = defaultdict(
        lambda: {
            "cells": 0,
            "cells_with_candidates": 0,
            "candidates_saved": 0,
            "expected_candidate_slots": 0,
            "missing_candidate_slots": 0,
            "candidates_formula_evaluated": 0,
            "component_slots": 0,
            "trajectory_slots": 0,
            "selected_cells": 0,
            "selected_valid_cells": 0,
        }
    )
    index_names = {
        6: ("cell_artifact_index.json",),
        7: ("cell_artifact_index.json",),
        8: (
            "validation_cell_artifact_index.json",
            "final_cell_artifact_index.json",
            "odebench_forgetting_index.json",
        ),
    }
    index_coverage: list[dict[str, Any]] = []
    representative_formulas: dict[tuple[int, str], dict[str, Any]] = {}
    for phase, names in index_names.items():
        for index_name in names:
            manifest = catalog.manifest(phase)
            hashes = manifest.get("artifact_sha256") if isinstance(manifest, Mapping) else None
            if not isinstance(hashes, Mapping) or index_name not in hashes:
                continue
            index_art = catalog.artifact(phase, index_name, required=True)
            assert index_art is not None and isinstance(index_art.value, list)
            observed = 0
            for index_row, cell in catalog.indexed_json(phase, index_name, required=True):
                observed += 1
                relative = str(index_row["path"])
                identity = _cell_identity(cell, relative)
                group = (phase, identity["view"], identity["condition"])
                counts = funnel[group]
                counts["cells"] += 1
                candidates = cell.get("candidates")
                candidates = candidates if isinstance(candidates, list) else []
                if candidates:
                    counts["cells_with_candidates"] += 1
                counts["candidates_saved"] += len(candidates)
                selected = cell.get("selected")
                selected_index = (
                    selected.get("candidate_index")
                    if isinstance(selected, Mapping)
                    else cell.get("selected_index")
                )
                if isinstance(selected, Mapping):
                    counts["selected_cells"] += 1
                    selected_structure = selected.get("structure")
                    selected_components = selected.get("component_valid")
                    if not isinstance(selected_components, list) and isinstance(selected_structure, Mapping):
                        selected_components = selected_structure.get("component_valid")
                    if (
                        selected.get("valid") is True
                        or (
                            isinstance(selected_components, list)
                            and bool(selected_components)
                            and all(value is True for value in selected_components)
                        )
                    ):
                        counts["selected_valid_cells"] += 1
                    exact_components = selected.get("component_exponent_aware_skeleton_exact")
                    exact_components = exact_components if isinstance(exact_components, list) else []
                    valid_components = selected.get("component_valid")
                    valid_components = valid_components if isinstance(valid_components, list) else []
                    selected_reason = selected.get("generation_failure") or selected.get("failure_reason")
                    selected_all_valid = bool(valid_components) and all(value is True for value in valid_components)
                    selected_all_exact = bool(exact_components) and all(
                        _finite_number(value) == 1.0 for value in exact_components
                    )
                    if selected_all_valid and selected_all_exact:
                        representative_category = "success"
                    elif selected_all_valid:
                        representative_category = "valid_but_structurally_wrong"
                    else:
                        representative_category = "generation_or_evaluation_failure"
                    report_category = (
                        f"final_test_{representative_category}"
                        if phase == 8 and cell.get("stage") == "final_test"
                        else representative_category
                    )
                    representative_formulas.setdefault(
                        (phase, report_category),
                        {
                            "source_phase": phase,
                            "category": report_category,
                            "cell_id": identity["cell_id"],
                            "family": cell.get("family"),
                            "true_formula": cell.get("true_formula"),
                            "predicted_formula_raw": selected.get("candidate_formula_raw"),
                            "predicted_formula_canonical": selected.get("candidate_formula_canonical"),
                            "variable_to_gene": cell.get("variable_to_gene"),
                            "valid": selected_all_valid,
                            "failure_reason": selected_reason,
                            "exponent_aware_skeleton_exact": exact_components,
                            "normalized_variable_aware_ted": selected.get("component_normalized_variable_aware_ted"),
                            "input_r2_mean": None,
                            "generalization_r2_mean": None,
                            "source_path": relative,
                            "source_sha256": str(index_row["sha256"]),
                        },
                    )

                def add(
                    event_type: str,
                    item_id: str,
                    is_selected: bool,
                    *,
                    reason: Any = None,
                    unit: str,
                    candidate_index: Any = None,
                    component_index: int | None = None,
                    trajectory_role: str | None = None,
                    trajectory_index: int | None = None,
                    missing_candidate_slots: int = 0,
                ) -> None:
                    if event_type not in FAILURE_EVENT_TYPES:
                        raise AssertionError(event_type)
                    reason_text = str(reason) if reason not in (None, "") else None
                    key = (
                        phase, index_name, relative, item_id, event_type,
                        reason_text, component_index, trajectory_role,
                        trajectory_index,
                    )
                    if key in event_keys:
                        return
                    event_keys.add(key)
                    event_payload = {
                        "phase": phase,
                        "stage": cell.get("stage"),
                        "view": identity["view"],
                        "condition": identity["condition"],
                        "layer_name": cell.get("layer"),
                        "cell_id": identity["cell_id"],
                        "system_id": cell.get("system_id"),
                        "family": cell.get("family"),
                        "bundle_index": cell.get("bundle_index"),
                        "noise_sigma": cell.get("noise_sigma"),
                        "subsample_rho": cell.get("subsample_rho"),
                        "unit": unit,
                        "candidate_index": candidate_index,
                        "component_index": component_index,
                        "trajectory_role": trajectory_role,
                        "trajectory_index": trajectory_index,
                        "failure_class": event_type,
                        "reason": reason_text,
                        "selected": bool(is_selected),
                        "missing_candidate_slots": int(missing_candidate_slots),
                        "source_path": relative,
                        "source_sha256": str(index_row["sha256"]),
                        "source_index": index_name,
                        "value": 1,
                        "value_kind": "count",
                    }
                    stable = json.dumps(event_payload, sort_keys=True, ensure_ascii=False)
                    event_payload["event_id"] = hashlib.sha256(stable.encode("utf-8")).hexdigest()
                    event_payload["layer"] = "failure_event"
                    events.append(event_payload)

                expected_beam = cell.get("beam_size")
                if not isinstance(expected_beam, int):
                    expected_beam = cell.get("expected_candidate_count")
                if isinstance(expected_beam, int):
                    counts["expected_candidate_slots"] += expected_beam
                    missing = max(expected_beam - len(candidates), 0)
                    counts["missing_candidate_slots"] += missing
                else:
                    missing = 0
                if missing:
                    add(
                        "beam_shortfall", "cell:beam_shortfall", False,
                        reason="candidate_shortfall", unit="cell",
                        missing_candidate_slots=missing,
                    )
                cell_reason_types: set[str] = set()
                if candidates:
                    for reason in (cell.get("failure_reason"), cell.get("generation_failure")):
                        for event_type in _failure_types(reason):
                            cell_reason_types.add(event_type)
                            add(event_type, f"cell:{event_type}", False, reason=reason, unit="cell")
                    if cell.get("generation_failure") and not _failure_types(cell.get("generation_failure")):
                        add("generation", "cell:generation", False, reason=cell.get("generation_failure"), unit="cell")
                # An empty candidate set still has a saved selected placeholder.
                if not candidates and isinstance(selected, Mapping):
                    placeholder_reason = (
                        cell.get("generation_failure")
                        or selected.get("generation_failure")
                        or selected.get("failure_reason")
                        or cell.get("failure_reason")
                        or "EmptyCandidateSet"
                    )
                    placeholder_types = _failure_types(placeholder_reason) or {"generation"}
                    for event_type in placeholder_types:
                        add(
                            event_type, f"selected_placeholder:{event_type}", True,
                            reason=placeholder_reason or "EmptyCandidateSet",
                            unit="candidate", candidate_index=None,
                        )
                candidate_timeout_recorded = False
                for position, candidate in enumerate(candidates):
                    if not isinstance(candidate, Mapping):
                        add("parse", f"candidate:{position}:malformed", position == selected_index, reason="MalformedCandidateRecord", unit="candidate", candidate_index=position)
                        continue
                    candidate_index = candidate.get("candidate_index", position)
                    is_selected = candidate_index == selected_index
                    if candidate.get("formula_metrics_evaluated") is True:
                        counts["candidates_formula_evaluated"] += 1
                    structure = candidate.get("structure")
                    reasons = [
                        candidate.get("failure_reason"),
                        candidate.get("generation_failure"),
                        candidate.get("trajectory_failure_reason"),
                        structure.get("failure_reason") if isinstance(structure, Mapping) else None,
                    ]
                    candidate_reason_types: set[str] = set()
                    for reason in reasons:
                        for event_type in _failure_types(reason):
                            candidate_reason_types.add(event_type)
                            candidate_timeout_recorded = (
                                candidate_timeout_recorded or event_type == "timeout"
                            )
                            add(event_type, f"candidate:{candidate_index}:{event_type}", is_selected, reason=reason, unit="candidate", candidate_index=candidate_index)
                    invalid_without_reason = (
                        candidate.get("valid") is False
                        and not any(_failure_types(reason) for reason in reasons)
                    )
                    component_valid = candidate.get("component_valid")
                    if not isinstance(component_valid, list) and isinstance(structure, Mapping):
                        component_valid = structure.get("component_valid")
                    component_reasons = candidate.get("component_failure_reason")
                    component_reasons = component_reasons if isinstance(component_reasons, list) else []
                    if isinstance(component_valid, list):
                        counts["component_slots"] += len(component_valid)
                        for component_index, value in enumerate(component_valid):
                            if value is not True:
                                component_reason = (
                                    component_reasons[component_index]
                                    if component_index < len(component_reasons)
                                    else "InvalidComponent"
                                )
                                component_reason_types = _failure_types(component_reason)
                                # Timeout/parse/TED helpers conservatively fill
                                # every component with the same originating
                                # formula-level failure.  Preserve the one
                                # candidate event instead of multiplying it by
                                # dimension.  A distinct component-specific
                                # reason remains a real component event.
                                if not candidate_reason_types or (
                                    component_reason_types
                                    and component_reason_types.isdisjoint(candidate_reason_types)
                                ):
                                    add("component", f"candidate:{candidate_index}:component:{component_index}", is_selected, reason=component_reason, unit="component", candidate_index=candidate_index, component_index=component_index)
                    elif invalid_without_reason:
                        add("component", f"candidate:{candidate_index}:invalid", is_selected, reason="InvalidFormulaWithoutSavedReason", unit="candidate", candidate_index=candidate_index)
                    trajectory = candidate.get("trajectory_metrics")
                    if isinstance(trajectory, Mapping):
                        failure_lists = {
                            str(key).removesuffix("_failures"): values
                            for key, values in trajectory.items()
                            if str(key).endswith("_failures") and isinstance(values, list)
                        }
                        for role, values in sorted(failure_lists.items()):
                            counts["trajectory_slots"] += len(values)
                            for trajectory_index, failure_reason in enumerate(values):
                                if not failure_reason:
                                    continue
                                # Timed-out candidates are filled with timeout
                                # penalties for every role.  Those synthetic
                                # entries describe the same candidate timeout,
                                # not additional integration failures.
                                if (
                                    "timeout" in candidate_reason_types
                                    and "timeout" in str(failure_reason).lower()
                                ):
                                    continue
                                add("trajectory", f"candidate:{candidate_index}:trajectory:{role}:{trajectory_index}", is_selected, reason=failure_reason, unit="trajectory", candidate_index=candidate_index, trajectory_role=role, trajectory_index=trajectory_index)
                clean_timeout_recorded = False
                clean = cell.get("selected_clean_trajectory_metrics")
                clean_roles = clean.get("roles") if isinstance(clean, Mapping) else None
                if isinstance(clean_roles, Mapping):
                    for role, records in sorted(clean_roles.items()):
                        if not isinstance(records, list):
                            continue
                        counts["trajectory_slots"] += len(records)
                        for trajectory_index, record in enumerate(records):
                            reason = record.get("failure") if isinstance(record, Mapping) else "MalformedTrajectoryRecord"
                            if not reason:
                                continue
                            if "timeout" in str(reason).lower():
                                if not candidate_timeout_recorded and not clean_timeout_recorded:
                                    add("timeout", "selected_clean:timeout", True, reason=reason, unit="trajectory", trajectory_role=str(role), trajectory_index=None)
                                    clean_timeout_recorded = True
                            else:
                                add("trajectory", f"selected_clean:{role}:{trajectory_index}", True, reason=reason, unit="trajectory", trajectory_role=str(role), trajectory_index=trajectory_index)
                # The producer flag is a derived cell summary.  Emit a fallback
                # only if no concrete candidate/clean timeout or empty-decode
                # generation event explains it.
                if (
                    cell.get("cell_evaluation_timeout_triggered") is True
                    and candidates
                    and not candidate_timeout_recorded
                    and not clean_timeout_recorded
                    and "timeout" not in cell_reason_types
                ):
                    add("timeout", "cell:unattributed_timeout", False, reason="CellEvaluationTimeout", unit="cell")
            index_coverage.append(
                {
                    "phase": phase,
                    "index": index_name,
                    "signed_index_rows": len(index_art.value),
                    "verified_shards": observed,
                    "pass": observed == len(index_art.value),
                    "source": _source(index_art),
                }
            )

    expected_by_index: dict[tuple[int, str], int | None] = {}
    registered_full_counts = {
        (6, "cell_artifact_index.json"): 7992,
        (7, "cell_artifact_index.json"): 26112,
        (8, "validation_cell_artifact_index.json"): 20736,
        (8, "final_cell_artifact_index.json"): 6000,
        (8, "odebench_forgetting_index.json"): 3780,
    }
    for phase in (6, 7):
        summary_art = catalog.artifact(phase, "summary.json")
        summary = summary_art.value if summary_art is not None else None
        expected = (
            (summary.get("expected_counts") or {}).get("all_decode_cells_total")
            if isinstance(summary, Mapping)
            else None
        )
        expected_by_index[(phase, "cell_artifact_index.json")] = (
            registered_full_counts[(phase, "cell_artifact_index.json")]
            if isinstance(summary, Mapping) and summary.get("mode") == "full"
            else
            int(expected) if isinstance(expected, int) and not isinstance(expected, bool) else None
        )
    validation_art = catalog.artifact(8, "validation_summary.json")
    validation = validation_art.value if validation_art is not None else None
    expected_validation = (
        (validation.get("expected_counts") or {}).get("all_decode_cells_total")
        if isinstance(validation, Mapping)
        else None
    )
    expected_by_index[(8, "validation_cell_artifact_index.json")] = (
        registered_full_counts[(8, "validation_cell_artifact_index.json")]
        if isinstance(validation, Mapping) and validation.get("mode") == "full"
        else int(expected_validation)
        if isinstance(expected_validation, int) and not isinstance(expected_validation, bool) else None
    )
    final_art = catalog.artifact(8, "final_result.json")
    final = final_art.value if final_art is not None else None
    expected_final = (
        (final.get("expected_counts") or {}).get("cells_total")
        if isinstance(final, Mapping)
        else None
    )
    expected_by_index[(8, "final_cell_artifact_index.json")] = (
        registered_full_counts[(8, "final_cell_artifact_index.json")]
        if isinstance(validation, Mapping) and validation.get("mode") == "full"
        else int(expected_final)
        if isinstance(expected_final, int) and not isinstance(expected_final, bool)
        else None
    )
    forgetting_audit_art = catalog.artifact(8, "odebench_forgetting_audit.json")
    forgetting_audit = (
        forgetting_audit_art.value if forgetting_audit_art is not None else None
    )
    expected_forgetting = (
        forgetting_audit.get("expected_cells_total")
        if isinstance(forgetting_audit, Mapping)
        else None
    )
    expected_by_index[(8, "odebench_forgetting_index.json")] = (
        registered_full_counts[(8, "odebench_forgetting_index.json")]
        if isinstance(validation, Mapping) and validation.get("mode") == "full"
        else int(expected_forgetting)
        if isinstance(expected_forgetting, int)
        and not isinstance(expected_forgetting, bool)
        else None
    )
    for row in index_coverage:
        expected = expected_by_index.get((int(row["phase"]), str(row["index"])))
        row["expected_shards"] = expected
        row["pass"] = bool(
            row["pass"] and expected is not None and row["verified_shards"] == expected
        )

    # Phase 3/5 funnels predate sharded Phase 6--8 records.  Preserve them as
    # explicitly separate upstream summaries, never merge them into events.
    upstream: list[dict[str, Any]] = []
    for phase in (3, 5):
        artifact = catalog.artifact(phase, "failure_funnel.json")
        if artifact is None or not isinstance(artifact.value, Mapping):
            continue

        def flatten(value: Mapping[str, Any], prefix: tuple[str, ...] = ()) -> None:
            for key, item in sorted(value.items()):
                path = (*prefix, str(key))
                if isinstance(item, Mapping):
                    flatten(item, path)
                elif (number := _finite_number(item)) is not None:
                    metric = path[-1]
                    upstream.append({
                        "layer": "upstream_funnel",
                        "phase": phase,
                        "subgroup": "/".join(path[:-1]) or "all",
                        "metric": metric,
                        "value": number,
                        "value_kind": "rate" if metric.endswith("_rate") else "count",
                        "source_sha256": artifact.sha256,
                    })
        flatten(artifact.value)

    events.sort(key=lambda row: str(row["event_id"]))
    if len({str(row["event_id"]) for row in events}) != len(events):
        raise ArtifactError("Phase 9 failure event IDs are not unique")
    event_summary_groups: dict[
        tuple[int, str, str, str, str, bool], list[Mapping[str, Any]]
    ] = defaultdict(list)
    for row in events:
        event_summary_groups[(
            int(row["phase"]), str(row["view"]), str(row["condition"]),
            str(row["failure_class"]), str(row["unit"]), bool(row["selected"]),
        )].append(row)
    event_summary_rows = []
    for (phase, view, condition, failure_class, unit, selected), rows in sorted(event_summary_groups.items()):
        denominators = funnel[(phase, view, condition)]
        denominator_metric = {
            "cell": "cells",
            "candidate": "candidates_saved",
            "component": "component_slots",
            "trajectory": "trajectory_slots",
        }[unit]
        denominator = int(denominators[denominator_metric])
        event_summary_rows.append({
            "layer": "failure_event_summary",
            "phase": phase,
            "subgroup": f"{view}/{condition}",
            "metric": failure_class,
            "unit": unit,
            "selected": selected,
            "affected_cells": len({str(row["cell_id"]) for row in rows}),
            "event_count": len(rows),
            "missing_candidate_slots": sum(int(row["missing_candidate_slots"]) for row in rows),
            "denominator_metric": denominator_metric,
            "denominator": denominator,
            "rate": len(rows) / denominator if denominator else None,
            "value": len(rows),
            "value_kind": "count",
        })
    funnel_rows = []
    for (phase, view, condition), values in sorted(funnel.items()):
        for metric, count in values.items():
            funnel_rows.append({
                "layer": "derived_funnel",
                "phase": phase,
                "subgroup": f"{view}/{condition}",
                "metric": metric,
                "value": count,
                "value_kind": "count",
            })
    result = {
        "schema_version": "gpu_run5_phase9_failure_analysis_v2",
        "event_taxonomy": list(FAILURE_EVENT_TYPES),
        "event_identity_unique": True,
        "selected_is_attribute_not_event": True,
        "events": events,
        "event_summary": event_summary_rows,
        "funnel": funnel_rows,
        "upstream_funnels": upstream,
        "index_coverage": index_coverage,
        "representative_formulas": [
            representative_formulas[key] for key in sorted(representative_formulas)
        ],
        "coverage_pass": bool(index_coverage) and all(row["pass"] for row in index_coverage),
    }
    catalog._derived["failure_analysis"] = result
    return result


def failure_rows(catalog: Catalog) -> list[dict[str, Any]]:
    analysis = failure_analysis(catalog)
    return [
        *analysis["event_summary"],
        *analysis["funnel"],
        *analysis["upstream_funnels"],
    ]


def _wilson_interval(successes: int, total: int) -> list[float] | None:
    if total <= 0 or successes < 0 or successes > total:
        return None
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(
        proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total)
    ) / denominator
    return [max(0.0, center - half), min(1.0, center + half)]


def _student_t_ci_n3(values: Sequence[float]) -> list[float] | None:
    """Two-sided 95% Student-t interval for the preregistered three seeds."""
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        return None
    mean = statistics.fmean(values)
    half = 4.302652729696142 * statistics.stdev(values) / math.sqrt(3.0)
    return [mean - half, mean + half]


def condition_uncertainty(catalog: Catalog) -> dict[str, Any]:
    """Recompute descriptive intervals from the signed terminal shards.

    A validation No-Go uses only the selected three-bundle confirmation
    shards.  Screening shards represent nine hyperparameter candidates on a
    reduced panel and must never be pooled into the terminal estimand.
    """
    cached = catalog._derived.get("condition_uncertainty")
    if isinstance(cached, Mapping):
        return dict(cached)
    manifest = catalog.manifest(8)
    hashes = manifest.get("artifact_sha256") if isinstance(manifest, Mapping) else None
    final = isinstance(hashes, Mapping) and "final_cell_artifact_index.json" in hashes
    index_name = (
        "final_cell_artifact_index.json"
        if final
        else "validation_cell_artifact_index.json"
    )
    if not isinstance(hashes, Mapping) or index_name not in hashes:
        result = {
            "schema_version": "gpu_run5_phase9_condition_uncertainty_v1",
            "status": "unavailable",
            "reason": "signed Phase 8 terminal cell index is unavailable",
            "rows": [],
        }
        catalog._derived["condition_uncertainty"] = result
        return result
    streams = [(8, index_name, "final_test" if final else "validation_confirmation")]
    if not final:
        manifest6 = catalog.manifest(6)
        hashes6 = manifest6.get("artifact_sha256") if isinstance(manifest6, Mapping) else None
        if not isinstance(hashes6, Mapping) or "cell_artifact_index.json" not in hashes6:
            raise ArtifactError("Phase 6 signed cell index is required for validation No-Go uncertainty")
        streams.insert(0, (6, "cell_artifact_index.json", "confirmation"))
    totals: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"exact_successes": 0, "valid_successes": 0, "components": 0}
    )
    seed_system_values: dict[
        tuple[str, str, int, str], dict[str, list[float]]
    ] = defaultdict(
        lambda: {"exact": [], "valid": [], "ted": [], "generalization_nrmse": []}
    )
    retained_cells = 0
    skipped_nonterminal_cells = 0
    source_artifacts: list[Artifact] = []
    for source_phase, source_index, expected_stage in streams:
        source_art = catalog.artifact(source_phase, source_index, required=True)
        assert source_art is not None
        source_artifacts.append(source_art)
        for index_row, cell in catalog.indexed_json(source_phase, source_index, required=True):
            if cell.get("stage") != expected_stage:
                if final:
                    raise ArtifactError(
                        f"Phase 8 final index contains non-final shard: {index_row['path']}"
                    )
                skipped_nonterminal_cells += 1
                continue
            retained_cells += 1
            identity = _cell_identity(cell, str(index_row["path"]))
            key = (identity["view"], identity["condition"])
            selected = cell.get("selected")
            selected = selected if isinstance(selected, Mapping) else {}
            exact = selected.get("component_exponent_aware_skeleton_exact")
            valid = selected.get("component_valid")
            ted = selected.get("component_normalized_variable_aware_ted")
            exact_values = list(exact) if isinstance(exact, list) else []
            valid_values = list(valid) if isinstance(valid, list) else []
            ted_values = list(ted) if isinstance(ted, list) else []
            component_count = int(cell.get("dimension") or 0)
            if component_count <= 0:
                raise ArtifactError(
                    f"Phase {source_phase} terminal shard lacks component dimension: {index_row['path']}"
                )
            if not (
                len(exact_values) == len(valid_values) == len(ted_values) == component_count
            ):
                raise ArtifactError(
                    f"Phase {source_phase} terminal shard component metric shape mismatch: "
                    f"{index_row['path']}"
                )
            finite_ted = [_finite_number(value) for value in ted_values]
            if any(value is None for value in finite_ted):
                raise ArtifactError(
                    f"Phase {source_phase} terminal shard has non-finite component TED: {index_row['path']}"
                )
            exact_successes = sum(_finite_number(value) == 1.0 for value in exact_values)
            valid_successes = sum(value is True for value in valid_values)
            totals[key]["components"] += component_count
            totals[key]["exact_successes"] += exact_successes
            totals[key]["valid_successes"] += valid_successes
            bundle = int(cell.get("bundle_index", -1))
            if bundle not in (0, 1, 2):
                raise ArtifactError(f"Phase {source_phase} terminal shard has invalid bundle index: {bundle}")
            system = str(cell.get("system_id") or cell.get("cell_id") or index_row["path"])
            system_values = seed_system_values[(key[0], key[1], bundle, system)]
            system_values["exact"].extend(
                1.0 if _finite_number(value) == 1.0 else 0.0 for value in exact_values
            )
            system_values["valid"].extend(
                1.0 if value is True else 0.0 for value in valid_values
            )
            system_values["ted"].extend(float(value) for value in finite_ted if value is not None)
            if final:
                clean = cell.get("selected_clean_trajectory_metrics")
                roles = clean.get("roles") if isinstance(clean, Mapping) else None
                generalization = roles.get("generalization") if isinstance(roles, Mapping) else None
                if not isinstance(generalization, list) or len(generalization) != 2:
                    raise ArtifactError(
                        f"Phase 8 final shard lacks two generalization IC records: {index_row['path']}"
                    )
                values = [
                    _finite_number(row.get("nrmse")) if isinstance(row, Mapping) else None
                    for row in generalization
                ]
                if any(value is None for value in values):
                    raise ArtifactError(
                        f"Phase 8 final shard has non-finite generalization NRMSE: {index_row['path']}"
                    )
                system_values["generalization_nrmse"].extend(
                    float(value) for value in values if value is not None
                )
    rows = []
    for (view, condition), counts in sorted(totals.items()):
        exact_seed_rates: list[float] = []
        valid_seed_rates: list[float] = []
        ted_seed_means: list[float] = []
        generalization_seed_means: list[float] = []
        seed_component_counts: list[int] = []
        for bundle in (0, 1, 2):
            systems = [
                values
                for (row_view, row_condition, row_bundle, _system), values
                in seed_system_values.items()
                if (row_view, row_condition, row_bundle) == (view, condition, bundle)
            ]
            if not systems:
                raise ArtifactError(
                    f"Phase 8 terminal shards lack bundle {bundle}: {view}/{condition}"
                )
            exact_seed_rates.append(statistics.fmean(
                statistics.fmean(values["exact"]) for values in systems
            ))
            valid_seed_rates.append(statistics.fmean(
                statistics.fmean(values["valid"]) for values in systems
            ))
            ted_seed_means.append(statistics.fmean(
                statistics.fmean(values["ted"]) for values in systems
            ))
            if final:
                generalization_seed_means.append(statistics.fmean(
                    statistics.fmean(values["generalization_nrmse"])
                    for values in systems
                ))
            seed_component_counts.append(sum(len(values["exact"]) for values in systems))
        rows.append({
            "view": view,
            "condition": condition,
            **counts,
            "exact_rate": counts["exact_successes"] / counts["components"],
            "exact_rate_wilson_95_ci": _wilson_interval(
                counts["exact_successes"], counts["components"]
            ),
            "exact_rate_wilson_95_interval_kind": (
                "descriptive_naive_component_interval; repeated corruptions/components are dependent"
            ),
            "valid_rate": counts["valid_successes"] / counts["components"],
            "valid_rate_wilson_95_ci": _wilson_interval(
                counts["valid_successes"], counts["components"]
            ),
            "exact_seed_rates": exact_seed_rates,
            "seed_macro_aggregation": "component/corruption within system, then system within seed",
            "exact_seed_macro_student_t_95_ci": _student_t_ci_n3(exact_seed_rates),
            "valid_seed_rates": valid_seed_rates,
            "valid_seed_macro_student_t_95_ci": _student_t_ci_n3(valid_seed_rates),
            "failure_aware_ted_seed_system_macro_means": ted_seed_means,
            "failure_aware_ted_seed_macro_student_t_95_ci": _student_t_ci_n3(ted_seed_means),
            "failure_aware_generalization_nrmse_seed_system_macro_means": (
                generalization_seed_means if final else None
            ),
            "failure_aware_generalization_nrmse_seed_macro_student_t_95_ci": (
                _student_t_ci_n3(generalization_seed_means) if final else None
            ),
            "seed_component_counts": seed_component_counts,
            "uncertainty_caveat": (
                "Wilson intervals are descriptive naive component intervals, not independent-system "
                "inferential intervals, because components and corruptions repeat systems. The n=3 "
                "Student-t intervals use system-within-seed macro values, are very wide/unstable, "
                "and do not include system-sampling uncertainty because all seeds share the corpus."
            ),
        })
    result = {
        "schema_version": "gpu_run5_phase9_condition_uncertainty_v1",
        "status": "complete",
        "stage": "final_test" if final else "validation_terminal_no_go",
        "included_cell_stages": [stage for _phase, _index, stage in streams],
        "retained_cells": retained_cells,
        "skipped_nonterminal_screening_cells": skipped_nonterminal_cells,
        "sources": [_source(artifact) for artifact in source_artifacts],
        "rows": rows,
    }
    catalog._derived["condition_uncertainty"] = result
    return result


def condition_rows(catalog: Catalog) -> list[dict[str, Any]]:
    artifact = catalog.artifact(8, "final_result.json")
    validation_art = catalog.artifact(8, "validation_summary.json")
    if artifact is not None and isinstance(artifact.value, Mapping):
        summaries = artifact.value.get("summaries")
        stage = "final_test"
    elif validation_art is not None and isinstance(validation_art.value, Mapping):
        summaries = validation_art.value.get("condition_scores")
        stage = "validation_terminal_no_go"
    else:
        return []
    rows = []
    if not isinstance(summaries, Mapping):
        return rows
    uncertainty = {
        (str(row["view"]), str(row["condition"])): row
        for row in condition_uncertainty(catalog).get("rows", [])
    }
    for view, values in summaries.items():
        if not isinstance(values, Mapping):
            continue
        for condition, metrics in values.items():
            if isinstance(metrics, Mapping):
                row = {"stage": stage, "view": view, "condition": condition, **{key: value for key, value in metrics.items() if not isinstance(value, (dict, list))}}
                if isinstance(metrics.get("formula_score_vector_without_ce"), list):
                    row["formula_score_vector_without_ce"] = metrics["formula_score_vector_without_ce"]
            elif isinstance(metrics, list) and len(metrics) >= 3:
                vector = [_finite_number(value) for value in metrics]
                if any(value is None for value in vector[:3]):
                    raise ArtifactError(
                        f"Phase 8 validation score vector is malformed: {view}/{condition}"
                    )
                row = {
                    "stage": stage,
                    "view": view,
                    "condition": condition,
                    "formula_score_vector_without_ce": [float(value) for value in vector[:3] if value is not None],
                    "component_exponent_aware_skeleton_exact_system_then_seed_macro": vector[0],
                    "failure_aware_component_ted_mean": -float(vector[1]),
                    "component_valid_rate": vector[2],
                    "validation_teacher_forcing_ce": -float(vector[3]) if len(vector) > 3 and vector[3] is not None else None,
                }
            else:
                continue
            extra = uncertainty.get((str(view), str(condition)))
            if extra is not None:
                row.update({
                    key: value for key, value in extra.items()
                    if key not in {"view", "condition"}
                })
            rows.append(row)
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], *, fields: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = sorted({str(key) for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fields),
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in row.items()})


def _svg(
    path: Path,
    title: str,
    lines: Sequence[str],
    *,
    points: Sequence[tuple[float, float, str]] = (),
    x_label: str = "x",
    y_label: str = "y",
    reference: str | None = None,
) -> None:
    """Write a dependency-free deterministic SVG summary."""
    width = 960
    height = max(360, (300 if points else 130) + 28 * len(lines))
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#fbfbf8"/>', f'<text x="36" y="52" font-family="sans-serif" font-size="25" font-weight="bold">{html.escape(title)}</text>']
    for index, line in enumerate(lines):
        body.append(f'<text x="42" y="{95 + index * 28}" font-family="monospace" font-size="15">{html.escape(str(line))}</text>')
    if points:
        finite = [(x, y, label) for x, y, label in points if math.isfinite(x) and math.isfinite(y)]
        if finite:
            xmin, xmax = min(x for x, _, _ in finite), max(x for x, _, _ in finite)
            ymin, ymax = min(y for _, y, _ in finite), max(y for _, y, _ in finite)
            if reference == "diagonal":
                # Use one shared data scale so the plot-corner diagonal is
                # mathematically y=x rather than merely a visual diagonal.
                lower, upper = min(xmin, ymin), max(xmax, ymax)
                xmin = ymin = lower
                xmax = ymax = upper
            elif reference == "zero_y":
                ymin, ymax = min(ymin, 0.0), max(ymax, 0.0)
            if xmax == xmin:
                padding = max(abs(xmin) * 0.05, 0.5)
                xmin, xmax = xmin - padding, xmax + padding
            if ymax == ymin:
                padding = max(abs(ymin) * 0.05, 0.5)
                ymin, ymax = ymin - padding, ymax + padding
            xspan, yspan = max(xmax - xmin, 1e-12), max(ymax - ymin, 1e-12)
            top = 120 + len(lines) * 28
            plot_h = max(120, height - top - 35)
            body.append(f'<rect x="90" y="{top}" width="820" height="{plot_h}" fill="white" stroke="#555"/>')
            for tick in range(5):
                fraction = tick / 4
                px = 90 + 820 * fraction
                py = top + plot_h - plot_h * fraction
                xv = xmin + xspan * fraction
                yv = ymin + yspan * fraction
                body.append(f'<line x1="{px:.2f}" y1="{top + plot_h}" x2="{px:.2f}" y2="{top + plot_h + 5}" stroke="#555"/>')
                body.append(f'<text x="{px:.2f}" y="{top + plot_h + 20}" text-anchor="middle" font-family="sans-serif" font-size="11">{xv:.3g}</text>')
                body.append(f'<line x1="85" y1="{py:.2f}" x2="90" y2="{py:.2f}" stroke="#555"/>')
                body.append(f'<text x="80" y="{py + 4:.2f}" text-anchor="end" font-family="sans-serif" font-size="11">{yv:.3g}</text>')
            body.append(f'<text x="500" y="{top + plot_h + 34}" text-anchor="middle" font-family="sans-serif" font-size="13">{html.escape(x_label)}</text>')
            body.append(f'<text x="18" y="{top + plot_h / 2:.2f}" text-anchor="middle" transform="rotate(-90 18 {top + plot_h / 2:.2f})" font-family="sans-serif" font-size="13">{html.escape(y_label)}</text>')
            if reference == "diagonal":
                body.append(f'<line x1="90" y1="{top + plot_h}" x2="910" y2="{top}" stroke="#b33" stroke-dasharray="7,5"/>')
                body.append(f'<text x="805" y="{top + 17}" font-family="sans-serif" font-size="12" fill="#b33">reference: y=x</text>')
            elif reference == "zero_y" and ymin <= 0.0 <= ymax:
                zero_y = top + plot_h - plot_h * (0.0 - ymin) / yspan
                body.append(f'<line x1="90" y1="{zero_y:.2f}" x2="910" y2="{zero_y:.2f}" stroke="#b33" stroke-dasharray="7,5"/>')
                body.append(f'<text x="805" y="{zero_y - 5:.2f}" font-family="sans-serif" font-size="12" fill="#b33">reference: y=0</text>')
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
    _svg(
        path,
        "Generation → selection → integration failure funnel",
        [
            f"phase {row['phase']} | {row['subgroup']} | {row['metric']}={_fmt(row['value'])} ({row['value_kind']})"
            for row in failures
        ] or ["undecidable: failure artifacts unavailable"],
    )
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
                    exact = _finite_number(row.get("exponent_aware_skeleton_exact"))
                    if exact is not None:
                        selected_grouped[str(row.get("family"))].append(exact)
        family_lines = []
        for family, values in sorted(grouped.items()):
            selected_values = selected_grouped.get(family)
            selected_text = (
                f"{statistics.fmean(selected_values):.4f}"
                if selected_values else "undecidable (selected records unavailable)"
            )
            family_lines.append(
                f"{family}: truth-in-beam={statistics.fmean(values):.4f}; selected-exact={selected_text} (beam n={len(values)})"
            )
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
    _svg(path, "Single-trajectory vs multi-IC failure-aware NRMSE", p6_lines, points=p6_points, x_label="single-trajectory NRMSE", y_label="multi-IC NRMSE", reference="diagonal")
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
    _svg(path, "Reconstruction fit versus structural TED", [f"n={len(recon_points)}; each point is one validation cell"], points=recon_points, x_label="input reconstruction R2", y_label="normalized variable-aware TED")
    outputs.append(path)
    path = figures / "phase9_input_vs_generalization.svg"
    _svg(path, "Input-IC versus generalization-IC NRMSE", [f"n={len(ic_points)}; candidate selection never used generalization IC"], points=ic_points, x_label="input-IC NRMSE", y_label="generalization-IC NRMSE", reference="diagonal")
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
    _svg(path, "Layer intervention: ΔCE versus ΔTED", [f"n_layers={len(p5_points)}; blue=layer; dashed red is y=0"], points=p5_points, x_label="damage CE", y_label="failure-aware TED increase", reference="zero_y")
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
    _svg(path, "Efficiency / recovery Pareto", efficiency_lines or ["undecidable: no final recovery joined to signed training records"], points=efficiency_points, x_label="trainable parameters", y_label="exact recovery macro")
    outputs.append(path)

    cross_lines = []
    for row in cross_run.get("rows") or []:
        cross_lines.append(f"{row.get('run')} ({row.get('model')}): probe∩causal={row.get('probe_causal_top3_jaccard')}; causal∩IOLE={row.get('causal_iole_top3_jaccard')}; probe∩IOLE={row.get('probe_iole_top3_jaccard')}; probe∩robustness={row.get('probe_robustness_top3_jaccard')}; robustness∩IOLE={row.get('robustness_iole_top3_jaccard')}")
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


def _md_cell(value: Any) -> str:
    """Escape arbitrary saved text for a GitHub Markdown table cell."""
    return str(value if value is not None else "—").replace("\\", "\\\\").replace("|", "\\|").replace("\r", "").replace("\n", "<br>")


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
    go8 = c.get("go8") if isinstance(c, Mapping) else None
    if isinstance(go8, Mapping) and go8.get("pass") is False:
        progression_note = (
            "**Go 8 は NO-GO だったため、DREAM4・実データへの追加実験は実施しなかった。** "
            "性能不足をデータ側の難しさと混同しないための事前固定停止であり、"
            "Phase 8の一度限りのfinal testは負／混合結果として保持する。"
        )
    elif isinstance(go8, Mapping) and go8.get("pass") is True:
        progression_note = (
            "**Go 8 はGOだった。** DREAM4・実データへの進行可否と実施状況は、"
            "それぞれの署名済み成果物を根拠に別途報告する。"
        )
    else:
        progression_note = (
            "**Go 8は未判定であり、DREAM4・実データへの追加実験は実施していない。**"
        )
    example_lines = [
        f"| {_md_cell(row.get('category'))} | {_md_cell(row.get('cell_id'))} | `{_md_cell(row.get('true_formula'))}` | `{_md_cell(row.get('predicted_formula_raw'))}` | {_md_cell(_fmt(row.get('failure_reason')))} |"
        for row in examples
    ] or ["| — | — | — | — | upstream formula records unavailable |"]
    adaptation_lines = []
    for metrics in c.get("condition_metrics") or []:
        if isinstance(metrics, Mapping):
            vector = metrics.get("formula_score_vector_without_ce") or [None]
            exact = metrics.get(
                "component_exponent_aware_skeleton_exact_system_then_seed_macro",
                vector[0] if isinstance(vector, list) and vector else None,
            )
            adaptation_lines.append(
                f"| {_md_cell(metrics.get('stage'))} | {_md_cell(metrics.get('view'))} | {_md_cell(metrics.get('condition'))} | {_fmt(exact)} | {_fmt(metrics.get('failure_aware_component_ted_mean'))} | {_fmt(metrics.get('component_valid_rate', metrics.get('valid_rate')))} | {_md_cell(metrics.get('exact_rate_wilson_95_ci'))} | {_md_cell(metrics.get('valid_rate_wilson_95_ci'))} | {_md_cell(metrics.get('exact_seed_macro_student_t_95_ci'))} | {_md_cell(metrics.get('failure_aware_ted_seed_macro_student_t_95_ci'))} | {_md_cell(metrics.get('failure_aware_generalization_nrmse_seed_macro_student_t_95_ci'))} |"
            )
    if not adaptation_lines:
        adaptation_lines = ["| — | — | unavailable | — | — | — | — | — | — | — | — |"]
    formula_iole = d.get("formula_iole") if isinstance(d.get("formula_iole"), Mapping) else {}
    iole_freeze = formula_iole.get("freeze") if isinstance(formula_iole.get("freeze"), Mapping) else {}
    iole_contribution = formula_iole.get("raw_and_normalized_c_l")
    iole_contribution = iole_contribution if isinstance(iole_contribution, Mapping) else {}
    iole_eligibility = {
        str(view): {
            "eligible_seeds": row.get("eligible_seeds"),
            "normalized_contribution_reportable": row.get("normalized_contribution_reportable"),
        }
        for view, row in iole_contribution.items()
        if isinstance(row, Mapping)
    }
    iole_score_summary: dict[str, Any] = {}
    for view, payload in iole_contribution.items():
        if not isinstance(payload, Mapping):
            continue
        rows = [row for row in payload.get("rows") or [] if isinstance(row, Mapping)]
        raw_by_seed = {}
        layer_values: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            seed = str(row.get("seed"))
            raw_by_seed.setdefault(seed, {
                "frozen_failure_aware_ted": row.get("frozen_failure_aware_ted"),
                "full_failure_aware_ted": row.get("full_failure_aware_ted"),
                "full_improves_frozen": row.get("full_improves_frozen"),
                "denominator": row.get("denominator"),
            })
            value = _finite_number(row.get("normalized_contribution"))
            if value is not None:
                layer_values[str(row.get("layer"))].append(value)
        normalized_reportable = payload.get("normalized_contribution_reportable") is True
        normalized_layer_means = (
            sorted(
                (
                    {"layer": layer, "mean_normalized_contribution": statistics.fmean(values)}
                    for layer, values in layer_values.items() if values
                ),
                key=lambda row: (-row["mean_normalized_contribution"], row["layer"]),
            )
            if normalized_reportable else []
        )
        iole_score_summary[str(view)] = {
            "raw_base_full_by_seed": raw_by_seed,
            "normalized_contribution_reportable": normalized_reportable,
            "normalized_layer_means": normalized_layer_means,
            "raw_single_layer_rows_source": "phase9/result_d.json formula_iole.raw_and_normalized_c_l.rows",
        }
    reports = {
        "GPU_RUN5_decoded_support_report.md": f"""# GPU_RUN5 decoded support report（Result A）

Run: `{run_id}`。数値はmanifest hashで検証した保存済みrecordだけから生成した。

{progression_note}

## 事実

- candidate数: {_fmt(a.get('candidate_count') if isinstance(a, Mapping) else None)}
- variable-denominator candidate率: {_fmt(a.get('candidate_variable_denominator_rate') if isinstance(a, Mapping) else None)}
- rateのcount / denominator / 記述的Wilson 95%区間: `{json.dumps(a.get('rate_intervals') if isinstance(a, Mapping) else None, ensure_ascii=False, sort_keys=True)}`
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

{progression_note}

## 事実

- Phase 3 status: {_fmt((b.get('summary') or {}).get('status'))}
- validation cells: {_fmt((b.get('summary') or {}).get('n_cells'))}
- true exponent-aware skeleton in beam率: {_fmt((b.get('summary') or {}).get('true_exponent_aware_skeleton_in_beam_rate'))}
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

{progression_note}

## 事実

- Phase 6: {_fmt((c.get('phase6') or {}).get('status'))}
- Phase 7: {_fmt((c.get('phase7') or {}).get('status'))}
- Phase 8 validation: {_fmt((c.get('phase8_validation') or {}).get('status'))}
- Go 6: `{json.dumps(c.get('go6'), ensure_ascii=False, sort_keys=True)}`
- Go 7: `{json.dumps(c.get('go7'), ensure_ascii=False, sort_keys=True)}`
- Go 8: `{json.dumps(c.get('go8'), ensure_ascii=False, sort_keys=True)}`
- Phase 8 final: {_fmt((c.get('phase8_final') or {}).get('status'))}
- sealed test remained unopened: {_fmt(c.get('sealed_test_remained_unopened'))}
- P7: **{out['P7']['outcome']}**、観測値: `{json.dumps(out['P7']['observed'], ensure_ascii=False, sort_keys=True)}`

| stage | view | condition | exact macro | failure-aware TED | valid rate | exact descriptive Wilson | valid descriptive Wilson | exact seed-macro t 95% CI | TED seed-macro t 95% CI | generalization NRMSE seed-macro t 95% CI |
|---|---|---|---:|---:|---:|---|---|---|---|---|
{chr(10).join(adaptation_lines)}

Wilson区間は反復corruptionを含むcomponentをBernoulli試行として数えた**記述的なnaive区間**であり、独立systemに対する推測区間ではない。seed-macro区間はsystem内を先に平均した3 seedsのStudent-t区間であり、少数seedのため非常に広くなり得る。同じsystem corpusを3 seedsで共有するためsystem sampling uncertaintyは含まない。

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

{progression_note}

## 事実

- Phase 4 status: {_fmt((d.get('phase4') or {}).get('status'))}
- Phase 5 status: {_fmt((d.get('phase5') or {}).get('status'))}
- main causal top3: `{json.dumps((d.get('phase5') or {}).get('main_causal_top3'), ensure_ascii=False)}`
- decoder next-token probe top3（accuracy−shuffle）: `{json.dumps((d.get('observational') or {}).get('decoder_next_token_probe_top3'), ensure_ascii=False, sort_keys=True)}`
- gradient norm top3（parameter正規化）: `{json.dumps((d.get('observational') or {}).get('gradient_norm_top3'), ensure_ascii=False, sort_keys=True)}`
- DecoderLens: `{json.dumps((d.get('observational') or {}).get('decoder_lens'), ensure_ascii=False, sort_keys=True)}`
- within-module CKA: `{json.dumps((d.get('observational') or {}).get('within_module_cka'), ensure_ascii=False, sort_keys=True)}`
- causal top3 intervention effects: `{json.dumps((d.get('intervention') or {}).get('causal_top3_layer_effects'), ensure_ascii=False, sort_keys=True)}`
- Phase 7 formula IOLE freeze: `{json.dumps(iole_freeze.get('views'), ensure_ascii=False, sort_keys=True)}`
- confirmation rank stability: `{json.dumps(formula_iole.get('rank_stability'), ensure_ascii=False, sort_keys=True)}`
- raw / normalized C_l eligible seeds: `{json.dumps(iole_eligibility, ensure_ascii=False, sort_keys=True)}`
- raw base/full scores and normalized layer means（reportableなviewのみ）: `{json.dumps(iole_score_summary, ensure_ascii=False, sort_keys=True)}`
- P5: **{out['P5']['outcome']}**、観測値: `{json.dumps(out['P5']['observed'], ensure_ascii=False, sort_keys=True)}`

署名済みsource: `{json.dumps(d.get('signed_sources'), ensure_ascii=False, sort_keys=True)}`。対応図: `{json.dumps(d.get('figure_paths'), ensure_ascii=False)}`。

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

{progression_note}

## 事実

| run | model | generation | probe top3 | causal top3 | robustness top3 | IOLE top3 | intervention estimand | probe∩robustness | robustness∩IOLE | status |
|---|---|---|---|---|---|---|---|---:|---:|---|
{chr(10).join('| {run} | {model} | {generation} | `{probe}` | `{causal}` | `{robustness}` | `{iole}` | {estimand} | {probe_robustness} | {robustness_iole} | {status} |'.format(run=_md_cell(row.get('run')), model=_md_cell(row.get('model')), generation=_md_cell(row.get('generation')), probe=_md_cell(json.dumps(row.get('probe_top3'), ensure_ascii=False)), causal=_md_cell(json.dumps(row.get('causal_top3'), ensure_ascii=False)), robustness=_md_cell(json.dumps(row.get('robustness_top3'), ensure_ascii=False)), iole=_md_cell(json.dumps(row.get('iole_top3'), ensure_ascii=False)), estimand=_md_cell(row.get('intervention_estimand')), probe_robustness=_fmt(row.get('probe_robustness_top3_jaccard')), robustness_iole=_fmt(row.get('robustness_iole_top3_jaccard')), status=_md_cell(row.get('status'))) for row in e.get('rows', []))}

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
