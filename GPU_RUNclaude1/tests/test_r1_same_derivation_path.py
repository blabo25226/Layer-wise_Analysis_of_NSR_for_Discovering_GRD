"""R1 (research_state.md §8b, adopted after the C0001 retraction): both sides
of any comparison must come from the same derivation path.

``GPU_RUNclaude1/analyses/C0001_RETRACTION_neg_finding.md`` established that
``phase3/cells/*.json:true_structure.exponent_aware_skeleton`` is
**prefix**-derived while candidate skeletons are **infix**-derived, and that
comparing them produced a spurious "0/2040" finding. v2 §7.4/§5 item 1
therefore pins every Part A comparison to feed the **infix** representation
to both sides. These tests verify gpu_runclaude1 never reintroduces that
mixing, both by direct behavior and by static source inspection (so a future
edit that adds a stray ``true_prefix`` read is caught even before running
anything against real data).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gpu_run4.formulas import parse_system
from gpu_runclaude1.matcher import score_pair
from gpu_runclaude1.strata import component_stratum

REPO_ROOT = Path(__file__).resolve().parents[2]
GPU_RUN5_SOURCE_RUN = REPO_ROOT / "results" / "runs" / "gpu_run5_20260823_ddd267b0"

_SRC_ROOT = REPO_ROOT / "src" / "gpu_runclaude1"


def test_score_pair_forces_infix_parsing_on_both_sides_never_auto_detected():
    """A prefix-style token string, if it were auto-detected, would parse
    completely differently from the same text read as infix. score_pair
    must always call parse_system(..., as_prefix=False) -- i.e. it treats
    every input as infix, deterministically, never guessing.
    """
    prefix_like_text = "add,x_0,x_0"  # valid prefix for "x_0 + x_0", nonsense as infix
    forced_infix_parse = parse_system(prefix_like_text, as_prefix=False)
    auto_detected_parse = parse_system(prefix_like_text, as_prefix=None)
    # Auto-detection recognizes the comma-separated operator-prefixed shape
    # as prefix notation; forcing as_prefix=False must not silently agree.
    assert auto_detected_parse["valid"] is True
    assert auto_detected_parse["infix"] == "(x_0 + x_0)"
    assert forced_infix_parse["infix"] != auto_detected_parse["infix"]

    # score_pair, fed the same prefix-looking text on both sides, must
    # therefore NOT silently succeed via prefix auto-detection: forcing infix
    # means "add,x_0,x_0" is correctly treated as *invalid* infix syntax
    # (a ParseError, hence could_not_evaluate) rather than being silently
    # reinterpreted as the prefix expression it would parse as elsewhere.
    # This is the R1 guard operating by construction: there is no path by
    # which score_pair can accidentally treat one side as prefix.
    result = score_pair(prefix_like_text, prefix_like_text)
    assert result.components[0].match_outcome_m3 == "could_not_evaluate"
    assert result.components[0].failure_reason is not None


def test_component_stratum_only_accepts_infix_text_and_documents_it():
    """component_stratum's docstring and implementation are pinned to
    gpu_run4.formulas.parse_infix_component (v2 §7.2): never the prefix path.
    """
    import inspect

    from gpu_runclaude1 import strata as strata_module

    source = inspect.getsource(strata_module.component_stratum)
    assert "parse_infix_component" in source
    assert "parse_prefix_component" not in source


# Actual dict-access shapes, never prose: a module that *reads* one of these
# stored fields would contain one of these literal substrings in code; the
# module docstrings describe the fields in backticked prose instead, which
# does not match (e.g. "``true_structure`` field", not '["true_structure"]').
_FORBIDDEN_FIELD_ACCESS_PATTERNS = (
    '["true_structure"]', "['true_structure']", '.get("true_structure"', ".get('true_structure'",
    '["true_prefix"]', "['true_prefix']", '.get("true_prefix"', ".get('true_prefix'",
    '["teacher_components_prefix"]', "['teacher_components_prefix']",
    '.get("teacher_components_prefix"', ".get('teacher_components_prefix'",
)


def test_matcher_module_never_reads_prefix_or_structure_fields():
    """Static guard: gpu_runclaude1.matcher must never *access* the stored,
    prefix-derived true_structure / true_prefix fields -- those are exactly
    the fields the retracted finding mixed with infix-derived candidate
    skeletons. Checked against the literal dict-access shape, not prose.
    """
    source = (_SRC_ROOT / "matcher.py").read_text(encoding="utf-8")
    for forbidden in _FORBIDDEN_FIELD_ACCESS_PATTERNS:
        assert forbidden not in source, f"matcher.py must never read {forbidden!r} (rule R1)"


def test_strata_module_never_reads_prefix_or_structure_fields():
    source = (_SRC_ROOT / "strata.py").read_text(encoding="utf-8")
    for forbidden in _FORBIDDEN_FIELD_ACCESS_PATTERNS:
        assert forbidden not in source, f"strata.py must never read {forbidden!r} (rule R1)"


@pytest.mark.skipif(not GPU_RUN5_SOURCE_RUN.is_dir(), reason="GPU_RUN5 source run not present in this environment")
def test_r1_retraction_scenario_reproduced_on_real_data():
    """Reproduces the exact shape of the retracted finding on one real cell:
    the stored true_prefix and true_formula (infix) describe the identical
    function but are NOT the same string, and are not even the same parsed
    shape when both are (incorrectly) read as infix. gpu_runclaude1.matcher
    only ever consumes the infix field (true_formula /
    teacher_components_infix); this test documents why that choice matters
    by directly exhibiting the mismatch the retraction found.
    """
    cell_path = GPU_RUN5_SOURCE_RUN / "phase3" / "cells" / "R01_validation_d101_000_b0_n0_r0.json"
    cell = json.loads(cell_path.read_text(encoding="utf-8"))
    true_infix = cell["true_formula"]
    true_prefix = cell["true_prefix"]

    # The two stored fields are different strings describing the same truth.
    assert true_infix != true_prefix

    # Feeding the prefix STRING through the infix-only path (as if it were
    # infix text, exactly the RETRACTION's error) does not reproduce the
    # correct self-identity a genuine infix-vs-infix comparison gives.
    correct_identity = score_pair(true_infix, true_infix)
    assert correct_identity.m3_system == 1.0

    mixed_derivation = score_pair(true_infix, true_prefix)
    assert mixed_derivation.m3_system == 0.0, (
        "feeding a prefix-derived string into the infix-only comparison path must not "
        "spuriously match the infix truth -- if it did, the R1 hazard would be invisible"
    )
