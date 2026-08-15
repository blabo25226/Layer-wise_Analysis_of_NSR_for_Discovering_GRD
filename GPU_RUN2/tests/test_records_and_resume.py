"""Equation records, two-axis OOD fields, failure reasons, and resume."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.equation_metrics import score_domain_predictions  # noqa: E402
from evaluation.equation_records import (  # noqa: E402
    GPU_RUN2_REQUIRED_FIELDS,
    make_gpu_run2_equation_record,
)
import evaluation.reproduction_bias as reproduction_bias  # noqa: E402
from evaluation.reproduction_bias import (  # noqa: E402
    aggregate_reproduction,
    canonical_prefix_tree,
    classify_reproduction,
    corpus_fingerprint,
)
from resumable_evaluation import (  # noqa: E402
    load_problem_json_checkpoint,
    remaining_eq_ids,
    save_problem_json_checkpoint,
)
from training.selective_layers import (  # noqa: E402
    build_gpu_run2_conditions,
    sample_random_layers_gpu_run2,
)
import numpy as np


def _base_kwargs(**overrides):
    payload = dict(
        eq_id="G02_variant_001",
        predicted_expr="x_1 + x_2",
        variable_names=["x_1", "x_2"],
        scores={
            "valid_pred": 1.0,
            "nmse": 0.2,
            "r2": 0.7,
            "sym_exact": 0.0,
            "sym_skeleton": 1.0,
            "sym_equiv": 0.0,
            "complexity": 5.0,
            "var_f1": 1.0,
            "var_precision": 1.0,
            "var_recall": 1.0,
            "domain_id_nmse": 0.2,
            "domain_ood_nmse": 0.4,
        },
        true_expr="x_2**2/(1+x_2**2)-x_1",
        true_raw="V*A(h2)-delta*x_1",
        true_canonical="x_2**2/(1+x_2**2)-x_1",
        true_skeleton="x_2**c/(c+x_2**c)-x_1",
        pred_canonical="x_1 + x_2",
        pred_skeleton="x_1 + x_2",
        motif="G02",
        split="test",
        split_view="main",
        noise=0.0,
        data_seed=101,
        training_seed=0,
        condition="top_3",
        domain_regime="id",
        structure_regime="id",
        parameter_split="main",
        target_variable="x_1",
        oracle_regulators=["x_2"],
        oracle_inputs=["x_1", "x_2"],
        variable_order=["x_1", "x_2"],
        oracle_source_equation_id="G02_variant_001",
        decoder="nesymres",
        timeout_budget_sec=30.0,
    )
    payload.update(overrides)
    return payload


def test_gpu_run2_record_has_required_two_axis_fields():
    record = make_gpu_run2_equation_record(**_base_kwargs())
    assert GPU_RUN2_REQUIRED_FIELDS.issubset(record)
    assert record["domain_regime"] == "id"
    assert record["structure_regime"] == "id"
    assert "ood_nmse" not in record
    assert record["domain_id_nmse"] == pytest.approx(0.2)
    assert record["domain_ood_nmse"] == pytest.approx(0.4)


def test_timeout_and_operator_failures_are_stored():
    timeout = make_gpu_run2_equation_record(
        **_base_kwargs(
            predicted_expr="",
            scores={
                "valid_pred": 0.0,
                "nmse": float("inf"),
                "r2": float("-inf"),
                "sym_exact": 0.0,
                "sym_skeleton": 0.0,
                "sym_equiv": 0.0,
                "complexity": 0.0,
                "var_f1": 0.0,
                "var_precision": 0.0,
                "var_recall": 0.0,
                "domain_id_nmse": float("inf"),
                "domain_ood_nmse": float("inf"),
            },
            failure_reason="DecodeTimeout",
            timeout=True,
        )
    )
    assert timeout["failure_reason"] == "DecodeTimeout"
    assert timeout["timeout"] is True
    assert not timeout["valid_pred"]


def test_domain_scores_keep_id_and_ood_separate():
    y_id = np.array([1.0, 1.2, 0.8])
    y_ood = np.array([2.0, 2.5, 1.5])
    pred_id = np.array([1.0, 1.1, 0.9])
    pred_ood = np.array([3.0, 2.0, 1.0])
    scores = score_domain_predictions(
        y_id=y_id,
        pred_id=pred_id,
        y_ood=y_ood,
        pred_ood=pred_ood,
        predicted_expr="x_1",
        true_vars=["x_1"],
        true_expr="x_1",
    )
    assert scores["domain_id_nmse"] != scores["domain_ood_nmse"]
    assert "ood_nmse" not in scores


def test_problem_checkpoint_skips_completed_prefix(tmp_path: Path):
    path = tmp_path / "phase5.json"
    identity = {"phase": 5, "condition": "top_3", "noise": 0.0}
    records = [{"eq_id": "a", "pred_raw": "x_1"}]
    save_problem_json_checkpoint(
        path,
        identity=identity,
        completed_eq_ids=["a"],
        records=records,
    )
    loaded = load_problem_json_checkpoint(path, expected_identity=identity)
    assert loaded is not None
    remaining = remaining_eq_ids(["a", "b", "c"], loaded["completed_eq_ids"])
    assert remaining == ["b", "c"]
    with pytest.raises(RuntimeError, match="identity mismatch"):
        load_problem_json_checkpoint(path, expected_identity={"phase": 5, "condition": "full"})
    with pytest.raises(RuntimeError, match="problem order mismatch"):
        remaining_eq_ids(["b", "a"], ["a"])


def test_random_3_redraws_only_when_identical_to_top3():
    candidates = ["decoder_0", "decoder_1", "decoder_2", "decoder_3", "decoder_4"]
    top3 = ["decoder_2", "decoder_3", "decoder_4"]
    drawn = sample_random_layers_gpu_run2(candidates, 3, seed=7, top_layers=top3)
    assert len(drawn) == 3
    assert len(set(drawn)) == 3
    again = sample_random_layers_gpu_run2(candidates, 3, seed=7, top_layers=top3)
    assert drawn == again
    conditions = build_gpu_run2_conditions(
        ["decoder_4", "decoder_3", "decoder_2", "decoder_1", "decoder_0"],
        random_seed=20260812,
        candidate_layers=candidates,
    )
    assert set(conditions) == {"frozen", "full", "top_1", "top_3", "random_3"}
    assert conditions["frozen"] == []
    assert conditions["full"] is None
    assert conditions["top_1"] == ["decoder_4"]
    assert conditions["top_3"] == ["decoder_4", "decoder_3", "decoder_2"]
    assert set(conditions["random_3"]) != set(conditions["top_3"])


def test_reproduction_bias_uses_finetuning_corpus_templates():
    train = ["0.5*x_2**2/(1.2 + x_2**2) - 0.3*x_1", "1 - x_1"]
    corpus = corpus_fingerprint(train)
    assert corpus["n_unique_templates"] >= 1
    hit = classify_reproduction(
        "0.4*x_2**2/(0.9 + x_2**2) - 0.2*x_1",
        train_templates=train,
        train_exact=train,
        true_expr=train[0],
    )
    miss = classify_reproduction(
        "x_2*x_3 - x_1",
        train_templates=train,
        train_exact=train,
        true_expr="x_2*x_3 - x_1",
    )
    assert hit["reproduced"] is True
    assert miss["novel"] is True


def test_reproduction_canonicalization_falls_back_after_timeout(monkeypatch):
    def slow_simplify(expr):
        time.sleep(1.0)
        return expr

    monkeypatch.setattr(reproduction_bias.sp, "simplify", slow_simplify)
    started = time.monotonic()
    tree = canonical_prefix_tree("x_1 + 1", timeout_sec=0.01)
    elapsed = time.monotonic() - started
    assert tree is not None
    assert elapsed < 0.5


def test_reproduction_aggregate_caches_training_template_fingerprints(monkeypatch):
    calls = 0
    original = reproduction_bias.canonical_prefix_tree

    def counted(expr, **kwargs):
        nonlocal calls
        calls += 1
        return original(expr, **kwargs)

    monkeypatch.setattr(reproduction_bias, "canonical_prefix_tree", counted)
    rows = [
        {"pred_simplified": "x_1 + 1", "true_canonical": "x_1 + 1", "valid_pred": 1.0},
        {"pred_simplified": "x_1 - 1", "true_canonical": "x_1 - 1", "valid_pred": 1.0},
    ]
    result = aggregate_reproduction(rows, train_templates=["x_1 + 1", "x_2 + 1"])
    assert result["n_total"] == 2
    assert calls == 2
