"""Component-type stratification H/L and the write-before-match integrity gate (v2 §7.2, §14 item 8).

Assignment is a **truth-side** property computed only from
``phase2/validation.json:teacher_components_infix`` through the **infix**
derivation path (``gpu_run4.formulas.parse_infix_component``), so that
stratum assignment and the M0/M1/M3 matcher inputs share the same derivation
path (rule R1) -- never the stored, prefix-derived ``true_structure`` field.

v2 freezes a strict ordering: the strata assignment and the realized-``|H|``
ladder table must be **written to disk and hashed** before any Part A match
indicator is computed anywhere in the code path. :func:`require_strata_frozen`
is the mechanical enforcement of that ordering: the Part A matching entry
point (``scripts.phases.gpu_runclaude1_c0001_phase1_parta`` /
``gpu_runclaude1.matcher``) must present a :class:`StrataFrozenToken` obtained
*only* by calling it after both artifacts exist on disk and their recorded
hash matches the file. There is no code path that lets matching start
without one.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from gpu_run4.formulas import parse_infix_component

from gpu_runclaude1.constants import (
    MIN_H_FOR_STRATIFIED_PRIMARY,
    MIN_L_FOR_STRATIFIED_PRIMARY,
    UNDERPOWERED_H_CEILING,
)

STRATUM_H = "H"
STRATUM_L = "L"

_VARIABLE_LEAF = re.compile(r"x_\d+")


class StrataIntegrityError(RuntimeError):
    """Raised when the write-before-match ordering (v2 §7.2 step 3) is violated."""


def _walk(tree):
    if tree is None:
        return
    yield tree
    for child in tree[1]:
        yield from _walk(child)


def _contains_variable(tree) -> bool:
    return any(_VARIABLE_LEAF.fullmatch(node[0]) for node in _walk(tree))


def component_stratum(component_infix: str) -> str:
    """H iff the parsed tree contains an ``inv`` node whose argument subtree
    contains a variable leaf; L otherwise (v2 §7.2 frozen definition).

    Truths are verified 100% parseable (P1, 80/80 and 240/240 teacher_valid),
    so a parse failure here is an unexpected harness defect, not a
    classification outcome, and is raised rather than silently folded into L.
    """
    tree = parse_infix_component(component_infix)
    if tree is None:
        raise StrataIntegrityError(
            f"stratum assignment requires a parseable truth component, got unparseable: {component_infix!r}"
        )
    for label, children in _walk(tree):
        if label == "inv" and len(children) == 1 and _contains_variable(children[0]):
            return STRATUM_H
    return STRATUM_L


@dataclass(frozen=True)
class ComponentRecord:
    system_id: str
    family: str
    dimension: int
    component_index: int
    stratum: str


def assign_strata(validation_rows: Sequence[dict[str, Any]]) -> list[ComponentRecord]:
    """Assign H/L to every component of every validation system.

    ``validation_rows`` is the parsed content of ``phase2/validation.json``
    (80 rows); each row's ``teacher_components_infix`` is a list of one
    infix string per component, in component-index order.
    """
    records: list[ComponentRecord] = []
    for row in validation_rows:
        system_id = str(row["system_id"])
        family = str(row["family"])
        dimension = int(row["dimension"])
        components = row["teacher_components_infix"]
        if len(components) != dimension:
            raise StrataIntegrityError(
                f"{system_id}: dimension {dimension} does not match "
                f"{len(components)} entries in teacher_components_infix"
            )
        for index, component_infix in enumerate(components):
            records.append(
                ComponentRecord(
                    system_id=system_id,
                    family=family,
                    dimension=dimension,
                    component_index=index,
                    stratum=component_stratum(component_infix),
                )
            )
    return records


def _breakdown(records: Sequence[ComponentRecord], key: str) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for record in records:
        bucket = out.setdefault(str(getattr(record, key)), {STRATUM_H: 0, STRATUM_L: 0})
        bucket[record.stratum] += 1
    return out


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")


def build_component_strata_artifact(records: Sequence[ComponentRecord]) -> dict[str, Any]:
    """Build the v2 §7.2 step 1 payload: |H|, |L|, per-family/per-dimension
    breakdown, plus the frozen fallback disposition, but with no hash field
    yet (the hash is computed over this exact payload by
    :func:`write_component_strata`).
    """
    n_h = sum(1 for r in records if r.stratum == STRATUM_H)
    n_l = sum(1 for r in records if r.stratum == STRATUM_L)
    disposition = "stratified_primary"
    if n_h < MIN_H_FOR_STRATIFIED_PRIMARY or n_l < MIN_L_FOR_STRATIFIED_PRIMARY:
        disposition = "not_measurable_fallback_to_unstratified"
    elif n_h < UNDERPOWERED_H_CEILING:
        disposition = "underpowered_bound_only_eligible"
    return {
        "n_components": len(records),
        "n_h": n_h,
        "n_l": n_l,
        "by_family": _breakdown(records, "family"),
        "by_dimension": _breakdown(records, "dimension"),
        "components": [
            {
                "system_id": r.system_id,
                "family": r.family,
                "dimension": r.dimension,
                "component_index": r.component_index,
                "stratum": r.stratum,
            }
            for r in records
        ],
        "stratum_definition": (
            "H: the component's parsed tree (infix derivation, gpu_run4.formulas.parse_infix_component) "
            "contains at least one 'inv' node whose argument subtree contains a variable leaf x_j. "
            "L: every other component."
        ),
        "derivation_path": "infix",
        "frozen_fallback_disposition": disposition,
    }


def write_component_strata(path: Path, records: Sequence[ComponentRecord]) -> dict[str, Any]:
    """Write v2 §7.2 step 1's artifact with its own SHA256 recorded inside it."""
    payload = build_component_strata_artifact(records)
    digest = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
    payload["sha256_of_component_assignment"] = digest
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return payload


def _hash_without_self(payload: dict[str, Any]) -> str:
    stripped = {k: v for k, v in payload.items() if k != "sha256_of_component_assignment"}
    return hashlib.sha256(_canonical_json_bytes(stripped)).hexdigest()


@dataclass(frozen=True)
class StrataFrozenToken:
    """Proof that the strata (and ladder) artifacts were written and hashed
    before any match indicator was computed. The only way to construct one is
    :func:`require_strata_frozen`.
    """

    strata_sha256: str
    n_h: int
    n_l: int
    component_lookup: dict[tuple[str, int], str] = field(repr=False)


def require_strata_frozen(strata_path: Path, ladder_path: Path) -> StrataFrozenToken:
    """v2 §7.2 step 3 / §14 item 8, enforced mechanically.

    Raises :class:`StrataIntegrityError` unless both artifacts exist, the
    strata file's recorded hash matches its own content, and the ladder
    file records that same hash as the input it was computed from. There is
    no discretionary path around this check: any implementation that calls a
    matcher before this succeeds has violated the preregistration, and Part A
    is undecidable (no remedy short of a new cycle ID, per v2 §14 item 8).
    """
    if not strata_path.is_file():
        raise StrataIntegrityError(
            f"integrity ordering violated: {strata_path} does not exist before matching"
        )
    if not ladder_path.is_file():
        raise StrataIntegrityError(
            f"integrity ordering violated: {ladder_path} does not exist before matching"
        )
    strata_payload = json.loads(strata_path.read_text(encoding="utf-8"))
    recorded = strata_payload.get("sha256_of_component_assignment")
    actual = _hash_without_self(strata_payload)
    if not recorded or recorded != actual:
        raise StrataIntegrityError(
            f"{strata_path} hash mismatch (recorded={recorded!r}, actual={actual!r}); "
            "the strata artifact was modified after freezing, or was never hashed"
        )
    ladder_payload = json.loads(ladder_path.read_text(encoding="utf-8"))
    if ladder_payload.get("sha256_of_component_strata_input") != recorded:
        raise StrataIntegrityError(
            f"{ladder_path} was not computed from the frozen strata file at {strata_path} "
            "(sha256_of_component_strata_input does not match)"
        )
    lookup = {
        (str(row["system_id"]), int(row["component_index"])): str(row["stratum"])
        for row in strata_payload["components"]
    }
    return StrataFrozenToken(
        strata_sha256=recorded,
        n_h=int(strata_payload["n_h"]),
        n_l=int(strata_payload["n_l"]),
        component_lookup=lookup,
    )
