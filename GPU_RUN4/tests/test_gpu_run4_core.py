"""GPU_RUN4 unit tests for records, architecture audit, ODEBench, and Phase 0 wiring."""

from __future__ import annotations

import sys
from pathlib import Path

import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.architecture import (
    PARSER_DEFAULTS,
    architecture_audit,
    inventory_odeformer,
    parser_defaults_from_source,
    ranking_layer_names,
)
from gpu_run4.cli import common_parser
from gpu_run4.records import (
    FAILURE_REASONS,
    GPU_RUN4_REQUIRED_FIELDS,
    dummy_formula_record,
    dummy_layer_record,
    missing_layer_fields,
    missing_required_fields,
)
from gpu_run4_runtime import (
    FORBIDDEN_IMPORT_ROOT,
    ODEFORER_PACKAGE_ROOT,
    capture_numpy_permutation,
    classify_demo_exception,
    fit_source_uses_permutation,
    install_odeformer_path,
    load_odebench_equations,
    odebench_summary,
    official_demo_arrays,
    paper_model_args,
)


class _FakeAttn(nn.Module):
    def __init__(self, dim: int = 8) -> None:
        super().__init__()
        self.q_lin = nn.Linear(dim, dim)


class _FakeFFN(nn.Module):
    def __init__(self, dim: int = 8) -> None:
        super().__init__()
        self.lin = nn.Linear(dim, dim)


class _FakeTransformer(nn.Module):
    def __init__(self, n_layers: int, *, is_decoder: bool, dim: int = 8, n_heads: int = 2) -> None:
        super().__init__()
        self.n_layers = n_layers
        self.dim = dim
        self.n_heads = n_heads
        self.is_encoder = not is_decoder
        self.is_decoder = is_decoder
        self.n_words = 11
        self.attentions = nn.ModuleList([_FakeAttn(dim) for _ in range(n_layers)])
        self.ffns = nn.ModuleList([_FakeFFN(dim) for _ in range(n_layers)])
        self.layer_norm1 = nn.ModuleList([nn.LayerNorm(dim) for _ in range(n_layers)])
        self.layer_norm2 = nn.ModuleList([nn.LayerNorm(dim) for _ in range(n_layers)])
        self.position_embeddings = None
        if is_decoder:
            self.layer_norm15 = nn.ModuleList([nn.LayerNorm(dim) for _ in range(n_layers)])
            self.encoder_attn = nn.ModuleList([_FakeAttn(dim) for _ in range(n_layers)])
            self.embeddings = nn.Embedding(self.n_words, dim)
            self.proj = nn.Linear(dim, self.n_words, bias=True)
            self.proj.weight = self.embeddings.weight


class _FakeWrapper(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.embedder = nn.Linear(3, 8)
        self.encoder = _FakeTransformer(4, is_decoder=False)
        self.decoder = _FakeTransformer(16, is_decoder=True)
        self.beam_size = 50
        self.beam_temperature = 0.1
        self.beam_type = "sampling"


def test_formula_record_schema() -> None:
    record = dummy_formula_record("unit")
    assert missing_required_fields(record) == []
    assert GPU_RUN4_REQUIRED_FIELDS <= set(record)
    assert record["campaign"] == "GPU_RUN4"
    assert dummy_layer_record() and missing_layer_fields(dummy_layer_record()) == []


def test_plan_failure_reasons_are_named() -> None:
    for reason in (
        "CheckpointDownloadError",
        "ArchitectureMismatch",
        "BeamDecodeTimeout",
        "CandidateIntegrationFailure",
        "ActivationPatchError",
    ):
        assert reason in FAILURE_REASONS


def test_inventory_counts_encoder_decoder_blocks() -> None:
    inventory = inventory_odeformer(_FakeWrapper())
    assert inventory["n_encoder_transformer_layers"] == 4
    assert inventory["n_decoder_transformer_layers"] == 16
    assert inventory["ranking_layers"] == ranking_layer_names(4, 16)
    assert inventory["n_ranking_layers"] == 20
    assert inventory["tied_output_embedding"] is True
    assert inventory["encoder_positional_embeddings"] is False
    assert inventory["decoder_blocks"][0]["cross_attention"] is True
    assert inventory["encoder_blocks"][0]["cross_attention"] is False
    assert inventory["encoder_blocks"][0]["parameter_count"] > 0
    assert inventory["decoder_blocks"][0]["parameter_count"] > 0


def test_architecture_audit_detects_parser_paper_gap() -> None:
    matching = {
        "n_encoder_transformer_layers": 4,
        "n_decoder_transformer_layers": 16,
        "encoder_embedding_dim": 512,
        "decoder_embedding_dim": 512,
        "encoder_n_heads": 16,
        "decoder_n_heads": 16,
        "encoder_positional_embeddings": False,
        "total_parameters": 86_000_000,
        "beam_size": 50,
        "beam_type": "sampling",
        "beam_temperature": 0.1,
    }
    ok = architecture_audit(matching)
    assert ok["matches_paper"] is True
    assert ok["parser_vs_paper_vs_checkpoint"]["n_dec_layers"]["parser"] == 12
    assert ok["parser_vs_paper_vs_checkpoint"]["n_dec_layers"]["paper"] == 16

    bad = dict(matching)
    bad["n_decoder_transformer_layers"] = 12
    bad["encoder_embedding_dim"] = 256
    report = architecture_audit(bad)
    assert report["matches_paper"] is False
    fields = {item["field"] for item in report["mismatches"]}
    assert "n_decoder_layers" in fields
    assert "embedding_dim" in fields


def test_parser_defaults_extracted_from_vendored_source() -> None:
    text = (ODEFORER_PACKAGE_ROOT / "parsers.py").read_text(encoding="utf-8")
    extracted = parser_defaults_from_source(text)
    assert extracted["n_dec_layers"] == PARSER_DEFAULTS["n_dec_layers"]
    assert extracted["enc_emb_dim"] == PARSER_DEFAULTS["enc_emb_dim"]
    assert extracted["beam_type"] == "sampling"
    assert extracted["beam_size"] == 1


def test_official_fit_permutes_trajectories() -> None:
    wrapper = ODEFORER_PACKAGE_ROOT / "odeformer" / "model" / "sklearn_wrapper.py"
    assert fit_source_uses_permutation(wrapper)


def test_odebench_has_63_systems() -> None:
    equations = load_odebench_equations()
    summary = odebench_summary(equations)
    assert summary["n_systems"] == 63
    assert summary["by_dimension"] == {"1": 23, "2": 28, "3": 10, "4": 2}


def test_install_path_rejects_github_source() -> None:
    root = install_odeformer_path()
    assert root == ODEFORER_PACKAGE_ROOT.resolve()
    assert str(FORBIDDEN_IMPORT_ROOT.resolve()) not in sys.path
    import odeformer

    origin = Path(odeformer.__file__).resolve().as_posix()
    assert "GitHubSourceCode" not in origin
    assert "third_party/odeformer" in origin


def test_official_demo_arrays_are_2d() -> None:
    times, trajectory, spec = official_demo_arrays(n_points=50)
    assert times.shape == (50,)
    assert trajectory.shape == (50, 2)
    assert spec["x_scale"] == 2.3


def test_permutation_capture_is_seeded() -> None:
    import numpy as np

    with capture_numpy_permutation(7) as first:
        a = np.random.permutation(8)
    with capture_numpy_permutation(7) as second:
        b = np.random.permutation(8)
    assert first[0] == second[0] == a.tolist() == b.tolist()


def test_phase_cli_flags() -> None:
    parser = common_parser("unit")
    args = parser.parse_args(["--dry-run", "--smoke", "--allow-cpu", "--run-id", "x"])
    assert args.dry_run and args.smoke and args.allow_cpu
    assert args.run_id == "x"


def test_paper_model_args_include_beam_type() -> None:
    args = paper_model_args({"beam_size": 50, "beam_temperature": 0.1, "beam_type": "sampling"})
    assert args == {"beam_size": 50, "beam_temperature": 0.1, "beam_type": "sampling"}


def test_demo_exception_taxonomy() -> None:
    assert classify_demo_exception(TimeoutError("decode timed out")) == "BeamDecodeTimeout"
    assert classify_demo_exception(RuntimeError("CUDA out of memory")) == "OOM"
    assert classify_demo_exception(AttributeError("missing")) == "AttributeError"


def test_parse_error_is_stored_on_invalid_demo_record() -> None:
    record = dummy_formula_record(
        "no_sep",
        candidate_formula_raw="x_0",
        valid=False,
        failure_reason="ParseError",
    )
    assert record["valid"] is False
    assert record["failure_reason"] == "ParseError"


def test_phase0_script_importable() -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "phases"))
    module = __import__("gpu_run4_phase0_preflight")
    assert callable(module.main)
