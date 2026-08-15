"""GNW fine-tune adapter, dummy records, and interpretability hooks (no Phase run)."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from data.gnw_synthetic import to_sampled_dataset  # noqa: E402
from evaluation.equation_records import GPU_RUN2_REQUIRED_FIELDS  # noqa: E402
from evaluation.gpu_run2_rankings import (  # noqa: E402
    mean_nmse_for_families,
    phase4_agreement,
    phase4_conditions,
)
from gpu_run2_experiment import (  # noqa: E402
    activation_at_sequence_position,
    collect_layer_representations,
    dummy_gnw_record,
    filter_index_rows,
    filter_selective_ft_layers,
    flatten_activation_to_batch,
)
from interpretability.probes import (  # noqa: E402
    expression_structure_attributes,
    fit_linear_classifier_probe,
    mean_rank_layer_scores,
    ranking_from_mean_rank,
)
from models.layer_selector import LayerSpec  # noqa: E402
from interpretability.decoder_lens import prefix_tokens_to_equation  # noqa: E402
from interpretability.interventions import (  # noqa: E402
    register_replace_output_hook,
    register_zero_output_hook,
)


def _load_phase3_module():
    path = ROOT / "scripts" / "phases" / "gpu_run2_phase3_interpret.py"
    spec = importlib.util.spec_from_file_location("gpu_run2_phase3_interpret", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_phase4_module():
    path = ROOT / "scripts" / "phases" / "gpu_run2_phase4_contribution.py"
    spec = importlib.util.spec_from_file_location("gpu_run2_phase4_contribution", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_to_sampled_dataset_preserves_oracle_columns():
    class _Spec:
        eq_id = "G01_variant_000"
        family_id = "G01"
        canonical_expr = "1 - x_1"
        teacher_expr = "1 - x_1"
        oracle_inputs = ["x_1"]
        main_split = "train"

    class _Problem:
        spec = _Spec()
        noise = 0.1
        noise_std = 0.02
        X_train = np.arange(6, dtype=float).reshape(3, 2)
        y_train = np.array([0.1, 0.2, 0.3])
        X_id = np.ones((2, 2))
        y_id = np.ones(2)
        X_ood = np.zeros((2, 2))
        y_ood = np.zeros(2)

    sampled = to_sampled_dataset(_Problem(), xy="train")
    assert sampled.spec.family == "G01"
    assert sampled.spec.variable_names == ["x_1"]
    assert sampled.spec.target_expr == "1 - x_1"
    assert sampled.X.shape == (3, 2)


def test_dummy_record_accepts_catalogue_row_without_noise():
    row = {
        "eq_id": "G03_variant_018",
        "family_id": "G03",
        "template_id": "T02_single_regulator",
        "canonical_expr": "x_1 + x_2",
        "raw_gnw_formula": "V*A-delta*x_1",
        "skeleton_expr": "x_1 + x_2",
        "main_split": "validation",
        "structure_split": "train",
        "target_variable": "x_1",
        "oracle_regulators": ["x_2"],
        "oracle_inputs": ["x_1", "x_2"],
        "variable_order": ["x_1", "x_2"],
        "oracle_source_equation_id": "G03_variant_018",
    }
    record = dummy_gnw_record(row, condition="frozen", timeout_sec=30.0, split_view="main")
    assert GPU_RUN2_REQUIRED_FIELDS.issubset(record)
    assert record["noise"] == 0.0
    assert record["data_seed"] == 101


def test_selective_ft_candidates_exclude_output_head():
    registry = {
        "encoder_0": LayerSpec("encoder_0", "encoder", "enc.selfatt1", 0),
        "decoder_2": LayerSpec("decoder_2", "decoder", "decoder_transfomer.layers.2", 2),
        "output_head": LayerSpec("output_head", "head", "fc_out"),
    }
    names = filter_selective_ft_layers(registry)
    assert names == ["encoder_0", "decoder_2"]
    assert "output_head" not in names
    assert "output_head" in filter_selective_ft_layers(registry, include_head=True)


def test_template_and_next_token_probes_are_not_point_mean_regression():
    hidden = np.zeros((32, 2), dtype=np.float64)
    hidden[:16, 0] = 1.0
    hidden[16:, 1] = 1.0
    labels = ["T02_single_regulator"] * 16 + ["T07_two_module_mixture"] * 16
    classified = fit_linear_classifier_probe(hidden, labels)
    assert classified["accuracy"] == pytest.approx(1.0)
    assert "nums[:, -1" not in inspect.getsource(collect_layer_representations)
    attrs = expression_structure_attributes("x_2**2/(1+x_2**2)-x_1", variable_names=["x_1", "x_2"])
    assert attrs["n_variables"] == 2
    assert attrs["n_operators"] >= 2
    mean_ranks = mean_rank_layer_scores(
        {
            "template_accuracy": {"decoder_2": 0.9, "encoder_0": 0.2},
            "next_token_accuracy": {"decoder_2": 0.8, "encoder_0": 0.3},
            "n_operators_r2": {"decoder_2": 0.5, "encoder_0": 0.1},
        },
        higher_is_better={
            "template_accuracy": True,
            "next_token_accuracy": True,
            "n_operators_r2": True,
        },
    )
    assert ranking_from_mean_rank(mean_ranks)[0] == "decoder_2"


def test_filter_index_rows_by_seed_noise_and_split():
    rows = [
        {"eq_id": "a", "main_split": "train", "data_seed": 101, "noise": 0.0},
        {"eq_id": "b", "main_split": "validation", "data_seed": 101, "noise": 0.0},
        {"eq_id": "c", "main_split": "validation", "data_seed": 202, "noise": 0.1},
    ]
    filtered = filter_index_rows(rows, split="validation", data_seed=101, noise=0.0)
    assert [row["eq_id"] for row in filtered] == ["b"]


def test_flatten_activation_pools_variable_sequence_lengths():
    """Batches pad independently; seq dims must not become incompatible features."""
    short = np.ones((4, 20, 512), dtype=np.float32)
    long = np.ones((4, 32, 512), dtype=np.float32) * 2.0
    flat_short = flatten_activation_to_batch(short, batch_size=4)
    flat_long = flatten_activation_to_batch(long, batch_size=4)
    assert flat_short.shape == (4, 512)
    assert flat_long.shape == (4, 512)
    stacked = np.concatenate([flat_short, flat_long], axis=0)
    assert stacked.shape == (8, 512)
    assert np.allclose(flat_short, 1.0)
    assert np.allclose(flat_long, 2.0)


def test_decoder_probe_uses_causal_sequence_position():
    seq_first = np.zeros((5, 3, 4), dtype=np.float32)
    seq_first[1, :, :] = 7.0
    selected = activation_at_sequence_position(seq_first, 3, position=1)
    assert selected.shape == (3, 4)
    assert np.allclose(selected, 7.0)


def test_prefix_tokens_to_equation_parses_add():
    text, parseable = prefix_tokens_to_equation(["add", "x_1", "x_2"], variables=["x_1", "x_2"])
    assert parseable
    assert "x_1" in text and "x_2" in text


def test_zero_and_replace_hooks_change_linear_output():
    linear = torch.nn.Linear(3, 4, bias=False)
    torch.nn.init.ones_(linear.weight)
    x = torch.ones(2, 3)
    baseline = linear(x)
    assert not torch.allclose(baseline, torch.zeros_like(baseline))
    zero_hook = register_zero_output_hook(linear)
    assert torch.allclose(linear(x), torch.zeros_like(baseline))
    zero_hook.remove()
    replacement = torch.full((2, 4), 7.0)
    replace_hook = register_replace_output_hook(linear, replacement)
    assert torch.allclose(linear(x), replacement)
    replace_hook.remove()
    assert torch.allclose(linear(x), baseline)


def test_replace_hook_broadcasts_across_sequence_length():
    """Capture batch n_points may differ from decode n_points (e.g. 80 vs 1024)."""
    from interpretability.interventions import _broadcast_replacement

    replacement = torch.ones(1, 80, 512)
    target = torch.zeros(1, 1024, 512)
    out = _broadcast_replacement(replacement, target)
    assert out.shape == (1, 1024, 512)
    assert torch.allclose(out, torch.ones_like(target))


def test_structure_holdout_nmse_drops_g07_g08():
    records = [
        {"motif": "G01", "nmse": 0.2, "condition": "decoder_0"},
        {"motif": "G07", "nmse": 9.0, "condition": "decoder_0"},
        {"motif": "G08", "nmse": 9.0, "condition": "decoder_0"},
    ]
    all_mean = mean_nmse_for_families(records)
    holdout = mean_nmse_for_families(records, families=["G01", "G02", "G03", "G04", "G05", "G06"])
    assert all_mean > holdout
    assert holdout == pytest.approx(0.2)


def test_structure_safe_eq_ids_excludes_g07_g08():
    phase3 = _load_phase3_module()
    catalogue_by_id = {
        "G01_a": {"eq_id": "G01_a", "family_id": "G01"},
        "G06_b": {"eq_id": "G06_b", "family_id": "G06"},
        "G07_c": {"eq_id": "G07_c", "family_id": "G07"},
        "G08_d": {"eq_id": "G08_d", "family_id": "G08"},
    }
    safe = phase3._structure_safe_eq_ids(
        ["G01_a", "G06_b", "G07_c", "G08_d"],
        catalogue_by_id,
    )
    assert safe == ["G01_a", "G06_b"]
    assert "G07_c" not in safe and "G08_d" not in safe


def test_phase3_probe_split_is_disjoint_and_has_smoke_fallback():
    phase3 = _load_phase3_module()
    train, evaluation = phase3._probe_train_eval_indices(
        ["G01_variant_000", "G02_variant_000", "G03_variant_000"]
    )
    assert set(train).isdisjoint(set(evaluation))
    assert sorted(np.concatenate([train, evaluation]).tolist()) == [0, 1, 2]
    assert len(train) == 2
    assert len(evaluation) == 1


def test_phase3_writes_dual_candidate_layer_files():
    source = (ROOT / "scripts" / "phases" / "gpu_run2_phase3_interpret.py").read_text(
        encoding="utf-8"
    )
    assert "candidate_layers_main.json" in source
    assert "candidate_layers_structure_holdout.json" in source
    assert 'write_json(out_dir / "candidate_layers.json", main_payload)' in source


def test_phase4_loads_dual_candidate_lists():
    source = (ROOT / "scripts" / "phases" / "gpu_run2_phase4_contribution.py").read_text(
        encoding="utf-8"
    )
    assert "candidate_layers_main.json" in source
    assert "candidate_layers_structure_holdout.json" in source
    assert "candidates_union" in source
    assert "raise FileNotFoundError" in source
    assert "candidate_layers=candidates_main" in source
    assert "candidate_layers=candidates_sh" in source


def test_phase4_unit_checkpoint_is_atomic_and_identity_checked(tmp_path):
    phase4 = _load_phase4_module()
    identity = {
        "phase": 4,
        "data_seed": 101,
        "model_seed": 0,
        "noise": 0.0,
        "analysis": "iole",
        "condition": "encoder_1",
        "panel_ids": ["G01_variant_018"],
        "timeout_sec": 30.0,
        "source_commit": "abc",
    }
    path = tmp_path / "unit.json"
    phase4._save_unit(path, identity, nmse=0.2, records=[{"eq_id": "x"}])
    loaded = phase4._load_unit(path, identity)
    assert loaded["results"]["nmse"] == pytest.approx(0.2)
    bad = dict(identity, condition="encoder_2")
    with pytest.raises(RuntimeError, match="identity mismatch"):
        phase4._load_unit(path, bad)


def test_phase4_agreement_includes_decoder_lens_and_holdout_conditions_are_separate():
    candidates = ["decoder_0", "decoder_1", "decoder_2", "decoder_3", "decoder_4"]
    agreement = phase4_agreement(
        iole=["decoder_4", "decoder_3", "decoder_2"],
        ablation=["decoder_4", "decoder_2", "decoder_3"],
        intervention=["decoder_3", "decoder_4", "decoder_2"],
        probe=["decoder_4", "decoder_3", "decoder_1"],
        decoder_lens=["encoder_0", "encoder_1", "encoder_2"],
    )
    methods = set(agreement["methods"])
    assert "decoder_lens" in methods
    assert "probe" in methods
    main = phase4_conditions(
        ["decoder_4", "decoder_3", "decoder_2", "decoder_1", "decoder_0"],
        random_seed=20260812,
        candidate_layers=candidates,
    )
    holdout = phase4_conditions(
        ["decoder_0", "decoder_1", "decoder_2", "decoder_3", "decoder_4"],
        random_seed=20260812,
        candidate_layers=candidates,
    )
    assert main["top_1"] != holdout["top_1"]
    assert set(main) == {"frozen", "full", "top_1", "top_3", "random_3"}


def test_phase5_test_requires_hp_and_does_not_train():
    source = (ROOT / "scripts" / "phases" / "gpu_run2_phase5_selective_ft.py").read_text(
        encoding="utf-8"
    )
    assert 'if args.split == "test":' in source
    assert "Phase 5 test requires validation HP freeze file" in source
    assert "raise FileNotFoundError" in source
    assert "load_phase5_finetuned_checkpoint" in source
    assert 'elif args.split == "test":' in source
    assert "save_phase5_finetuned_checkpoint" in source
    assert "test_reuses_validation_checkpoints" in source
    # train_layers only under validation FT branch, never under test load branch.
    train_idx = source.index("train_layers(")
    test_load_idx = source.index('elif args.split == "test":')
    assert train_idx > test_load_idx
    between = source[test_load_idx:train_idx]
    assert "train_layers" not in between
    assert "load_phase5_finetuned_checkpoint" in between


def test_runner_script_evaluates_test_after_validation_freeze():
    text = (ROOT / "scripts" / "ops" / "run_gpu_run2.ps1").read_text(encoding="utf-8")
    assert '"--split", "validation"' in text
    assert '"--view", "main", "--split", "test"' in text
    assert '"--view", "structure_holdout", "--split", "test"' in text
    assert text.find('"--split", "validation"') < text.find('"--view", "main", "--split", "test"')
