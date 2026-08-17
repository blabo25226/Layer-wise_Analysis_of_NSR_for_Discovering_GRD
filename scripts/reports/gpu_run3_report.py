"""Assemble the GPU_RUN3 deliverables (plan section 18) from a finished run directory.

Emits:
  GPU_RUN3/GPU_RUN3_nd2_reproduction_report.md   (18.1)
  GPU_RUN3/GPU_RUN3_layer_analysis_report.md     (18.2)
  graphs/<run_id>/tables/problem_formulas.csv    (18.3)
  graphs/<run_id>/tables/layer_summary.csv       (18.4)

Missing phases are reported as missing rather than silently omitted.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3_runtime import graphs_dir, load_gpu_run3_configs, resolve_run_dir  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="GPU_RUN3 report builder")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out-dir", default=str(ROOT / "GPU_RUN3"))
    return parser.parse_args()


def _read(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "unreadable", "error": str(exc)}


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _fmt(value, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int,)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "inf"
        return f"{value:.{digits}f}"
    return str(value)


def _table(header: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(cell) for cell in row) + " |")
    return "\n".join(out)


def _missing(name: str) -> str:
    return f"> `{name}` is missing from this run directory; the section below is incomplete.\n"


def build_reproduction_report(run_dir: Path, run_id: str) -> str:
    preflight = _read(run_dir / "phase0" / "preflight.json") or {}
    phase1 = _read(run_dir / "phase1" / "summary.json")
    phase2 = _read(run_dir / "phase2" / "summary.json")
    phase3 = _read(run_dir / "phase3" / "summary.json")

    lines = [
        "# GPU_RUN3 — ND2 reproduction report",
        "",
        f"Run ID: `{run_id}`  ",
        f"Campaign: GPU_RUN3  ",
        "Provenance: `upstream_reproduction`",
        "",
        "## 1. Environment and provenance",
        "",
    ]
    software = preflight.get("software", {})
    hardware = preflight.get("cpu", {})
    lines.append(
        _table(
            ["item", "value"],
            [
                ["LANSR commit", (preflight.get("git") or {}).get("commit")],
                ["ND2 upstream", preflight.get("nd2_upstream_url")],
                ["ND2 package fingerprint", preflight.get("nd2_package_fingerprint")],
                ["checkpoint SHA256", preflight.get("checkpoint_sha256")],
                ["Zenodo", preflight.get("nd2_zenodo")],
                ["Python", software.get("python")],
                ["PyTorch", software.get("torch")],
                ["CUDA", software.get("cuda_version")],
                ["GPU", software.get("gpu_name")],
                ["CPU", hardware.get("cpu_brand")],
                ["device", preflight.get("device")],
                ["timestamp (UTC)", preflight.get("at_utc")],
            ],
        )
    )
    arch = preflight.get("architecture_summary", {})
    lines += [
        "",
        "### NDformer architecture",
        "",
        _table(
            ["item", "value"],
            [
                ["encoder Transformer blocks", arch.get("n_encoder_transformer_layers")],
                ["decoder Transformer blocks", arch.get("n_decoder_transformer_layers")],
                ["total parameters", arch.get("total_parameters")],
                ["ranking layers", ", ".join(arch.get("ranking_layers") or [])],
            ],
        ),
        "",
        "### Go conditions (Phase 0)",
        "",
        _table(
            ["condition", "result"],
            [[k, v] for k, v in (preflight.get("go_conditions") or {}).items()],
        ),
        "",
        "## 2. RQ2 — NDformer policy reproduction (Phase 1)",
        "",
    ]
    if not phase1:
        lines.append(_missing("phase1/summary.json"))
    else:
        lines.append(
            _table(
                ["metric", "value"],
                [
                    ["split", phase1.get("split")],
                    ["seeds", ", ".join(str(s) for s in phase1.get("seeds") or [])],
                    ["problems", phase1.get("n_problems")],
                    ["teacher-forcing examples", phase1.get("n_examples")],
                    ["valid rate", phase1.get("valid_rate")],
                    ["cross entropy", phase1.get("mean_ce")],
                    ["top-1 accuracy", phase1.get("mean_top1")],
                    ["top-5 accuracy", phase1.get("mean_topk")],
                    ["mean true-symbol rank", phase1.get("mean_rank")],
                    ["mean true-symbol probability", phase1.get("mean_true_prob")],
                    ["mean policy entropy", phase1.get("mean_entropy")],
                    ["std of CE across problems", phase1.get("std_ce_across_problems")],
                ],
            )
        )
        per_seed = phase1.get("per_seed") or []
        if per_seed:
            lines += [
                "",
                "Per seed:",
                "",
                _table(
                    ["seed", "problems", "examples", "CE", "top-1", "top-5", "valid rate"],
                    [
                        [s["seed"], s["n_problems"], s["n_examples"], s["mean_ce"], s["mean_top1"], s["mean_topk"], s["valid_rate"]]
                        for s in per_seed
                    ],
                ),
            ]
        failures = phase1.get("failure_counts") or {}
        lines += ["", f"Policy-level failures: {failures if failures else 'none'}", ""]

    lines += ["## 3. Pipeline reproduction (Phase 2, KUR)", ""]
    if not phase2:
        lines.append(_missing("phase2/summary.json"))
    else:
        rows = [
            ["true formula", phase2.get("true_formula")],
            ["predicted formula (guided)", phase2.get("guided_pred")],
            ["valid", phase2.get("guided_valid")],
            ["exact", phase2.get("guided_exact")],
            ["ted_raw", phase2.get("guided_ted_raw")],
            ["ted_skeleton", phase2.get("guided_ted_skeleton")],
            ["fit error (RMSE)", phase2.get("guided_fit_error")],
            ["search nodes", phase2.get("search_nodes")],
            ["candidates", phase2.get("candidate_count")],
            ["wall time (s)", phase2.get("wall_time")],
            ["failure reason", phase2.get("failure_reason")],
            ["network", json.dumps(phase2.get("network"))],
        ]
        lines.append(_table(["item", "value"], rows))
        unguided = phase2.get("unguided")
        if unguided:
            lines += [
                "",
                "Unguided (uniform) MCTS control on the same problem and budget:",
                "",
                _table(["item", "value"], [[k, v] for k, v in unguided.items()]),
            ]

    lines += ["", "## 4. RQ1 — synthetic benchmark reproduction (Phase 3)", ""]
    if not phase3:
        lines.append(_missing("phase3/summary.json"))
    else:
        lines.append(
            _table(
                ["metric", "value"],
                [
                    ["seeds", ", ".join(str(s) for s in phase3.get("seeds") or [])],
                    ["guided runs", phase3.get("n_runs")],
                    ["systems", phase3.get("n_systems")],
                    ["valid", phase3.get("n_valid")],
                    ["exact recoveries", phase3.get("n_exact")],
                    ["skeleton recoveries", phase3.get("n_skeleton")],
                    ["mean ted_raw", phase3.get("mean_ted_raw")],
                    ["mean R2", phase3.get("mean_r2")],
                ],
            )
        )
        per_system = phase3.get("per_system") or {}
        if per_system:
            lines += [
                "",
                "### Per system",
                "",
                _table(
                    ["system", "n", "valid", "exact", "skeleton", "mean TED", "mean RMSE", "mean R2", "mean nodes", "mean s"],
                    [
                        [
                            stats.get("paper_name", key),
                            stats.get("n"),
                            stats.get("n_valid"),
                            stats.get("n_exact"),
                            stats.get("n_skeleton"),
                            stats.get("mean_ted_raw"),
                            stats.get("mean_fit_error"),
                            stats.get("mean_r2"),
                            stats.get("mean_search_nodes"),
                            stats.get("mean_wall_time"),
                        ]
                        for key, stats in per_system.items()
                    ],
                ),
                "",
                "### True vs recovered formulas",
                "",
            ]
            for key, stats in per_system.items():
                lines.append(f"**{stats.get('paper_name', key)}**")
                lines.append("")
                lines.append(f"- true: `{stats.get('true_formula')}`")
                for index, pred in enumerate(stats.get("pred_formulas") or []):
                    lines.append(f"- predicted (run {index + 1}): `{pred}`")
                if stats.get("failure_reasons"):
                    lines.append(f"- failures: {', '.join(stats['failure_reasons'])}")
                lines.append("")
        unguided = phase3.get("unguided")
        if unguided:
            lines += [
                "### NDformer guidance vs unguided MCTS",
                "",
                _table(["item", "value"], [[k, v] for k, v in unguided.items()]),
                "",
            ]

    recomputed = _read(run_dir / "structural_metrics_recomputed.json")
    lines += ["## 5. Structural metrics under one canonicalization", ""]
    if not recomputed:
        lines.append(_missing("structural_metrics_recomputed.json"))
    else:
        canon = recomputed.get("canonicalization") or {}
        lines += [
            "Phases can be written under different canonicalization revisions, so every",
            "stored formula is re-scored once, uniformly, from its saved prefix. Constants",
            f"are compared at {canon.get('numeric_significant_digits')} significant digits and the identities",
            f"{', '.join(canon.get('folds') or [])} are folded (tolerance {canon.get('identity_atol')}).",
            "",
            _table(
                ["metric", "as recorded", "recanonicalized"],
                [
                    ["exact recoveries", recomputed.get("n_exact_as_recorded"), recomputed.get("n_exact")],
                    ["records re-scored", recomputed.get("n_recomputed"), recomputed.get("n_recomputed")],
                    ["records whose score changed", "-", recomputed.get("n_changed")],
                    ["skeleton recoveries", "-", recomputed.get("n_skeleton")],
                ],
            ),
            "",
            "### Re-scored records",
            "",
            _table(
                ["problem", "condition", "exact", "skeleton", "TED", "was exact", "was TED", "RMSE"],
                [
                    [
                        row.get("problem_id"),
                        row.get("condition"),
                        row.get("exact"),
                        row.get("skeleton"),
                        row.get("ted_raw"),
                        row.get("exact_as_recorded"),
                        row.get("ted_raw_as_recorded"),
                        row.get("fit_error"),
                    ]
                    for row in (recomputed.get("records") or [])
                    if row.get("status") == "recomputed"
                ],
            ),
            "",
        ]

    lines += [
        "## 6. Reading these numbers",
        "",
        "- Fit error and formula recovery are reported separately: a low RMSE does not",
        "  mean the true network dynamics formula was recovered (plan section 6.5).",
        "- Every run is stored per problem in `phase3/records.jsonl`, including failures,",
        "  timeouts and invalid formulas (plan section 6.4).",
        "- KUR's official network file ships only in the Zenodo archive; when it is absent",
        "  the run falls back to an Erdos-Renyi graph and flags `used_er_fallback`.",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_layer_report(run_dir: Path, run_id: str) -> str:
    phase4 = _read(run_dir / "phase4" / "summary.json")
    phase5 = _read(run_dir / "phase5" / "summary.json")
    phase6 = _read(run_dir / "phase6" / "summary.json")
    phase7 = _read(run_dir / "phase7" / "summary.json")
    phase8 = _read(run_dir / "phase8" / "report.json")
    phase9 = _read(run_dir / "phase9" / "summary.json")

    lines = [
        "# GPU_RUN3 — NDformer layer-analysis report",
        "",
        f"Run ID: `{run_id}`  ",
        "Provenance: `layer_analysis`",
        "",
        "Interpretations are kept distinct throughout (plan section 6.6): a probe shows",
        "information is linearly readable, ablation shows a block is required, activation",
        "intervention shows it is causally influential, and IOLE shows it can adapt.",
        "",
        "## 1. RQ3 — layer-wise information (Phase 4)",
        "",
    ]
    if not phase4:
        lines.append(_missing("phase4/summary.json"))
    else:
        layers = phase4.get("ranking_layers") or []
        lines += [
            f"Probes fit on `{phase4.get('probe_fit_split')}` and scored on `{phase4.get('probe_eval_split')}`; "
            "each score is paired with a shuffled-label control fitted the same way.",
            "",
        ]
        for task, scores in (phase4.get("probe_scores") or {}).items():
            control = (phase4.get("probe_control_scores") or {}).get(task, {})
            delta = (phase4.get("probe_minus_control") or {}).get(task, {})
            lines += [
                f"### Probe task: `{task}`",
                "",
                _table(
                    ["layer", "score", "shuffled-label control", "score - control"],
                    [[name, scores.get(name), control.get(name), delta.get(name)] for name in layers],
                ),
                "",
            ]
        lines += [
            "### Gradient norm and feature variation",
            "",
            _table(
                ["layer", "gradient norm", "per-parameter", "parameters", "within-problem variation"],
                [
                    [
                        name,
                        (phase4.get("gradient_norm") or {}).get(name),
                        (phase4.get("gradient_norm_normalized") or {}).get(name),
                        (phase4.get("parameter_counts") or {}).get(name),
                        (phase4.get("within_problem_feature_variation") or {}).get(name),
                    ]
                    for name in layers
                ],
            ),
            "",
            phase4.get("note", ""),
            "",
            "### CKA (problem-level representations)",
            "",
            _table(
                ["pair", "CKA"],
                [[key, value] for key, value in sorted((phase4.get("cka_problem_level") or {}).items())],
            ),
            "",
        ]

    lines += ["## 2. RQ6 — where formula structure forms (Phase 5)", ""]
    if not phase5:
        lines.append(_missing("phase5/summary.json"))
    else:
        for label, key in (("Encoder intermediate decode", "encoder_layer_summary"), ("Decoder logit lens", "decoder_layer_summary")):
            stats = phase5.get(key) or {}
            lines += [
                f"### {label}",
                "",
                _table(
                    ["layer", "n", "true-symbol rank", "true-symbol prob.", "top-1", "entropy", "mean TED"],
                    [
                        [
                            name,
                            row.get("n"),
                            row.get("mean_true_symbol_rank"),
                            row.get("mean_true_symbol_probability"),
                            row.get("top1_accuracy"),
                            row.get("mean_entropy"),
                            row.get("mean_ted_raw"),
                        ]
                        for name, row in stats.items()
                    ],
                ),
                "",
            ]
        lines += [phase5.get("note", ""), "", f"Failures: {phase5.get('n_failures')}", ""]

    lines += ["## 3. RQ4 — causal layer contribution (Phase 6)", ""]
    if not phase6:
        lines.append(_missing("phase6/summary.json"))
    else:
        baseline = phase6.get("baseline") or {}
        lines += [
            f"Panel: {phase6.get('n_panel_problems')} validation problems, seed {phase6.get('seed')}. "
            f"Baseline CE {_fmt(baseline.get('cross_entropy'))}, top-1 {_fmt(baseline.get('top1_accuracy'))}.",
            "",
            "### Layer effects (delta vs the same panel's baseline)",
            "",
            _table(
                ["layer", "dCE skip", "dCE zero", "dCE mean", "dCE patch", "dtop1 skip", "dtrue-prob skip"],
                [
                    [
                        name,
                        eff.get("delta_ce_skip"),
                        eff.get("delta_ce_zero"),
                        eff.get("delta_ce_mean"),
                        eff.get("delta_ce_patch"),
                        eff.get("delta_top1_skip"),
                        eff.get("delta_true_prob_skip"),
                    ]
                    for name, eff in (phase6.get("layer_effects") or {}).items()
                ],
            ),
            "",
            "### IOLE single-layer fine-tuning",
            "",
            _table(
                ["condition", "cross entropy"],
                [[k, v] for k, v in (phase6.get("iole_ce") or {}).items()],
            ),
            "",
            "### Parameter update sensitivity (controlled full fine-tune)",
            "",
            _table(
                ["layer", "||dtheta||", "||theta||", "relative"],
                [
                    [name, stats.get("delta_l2"), stats.get("theta_l2"), stats.get("relative_l2")]
                    for name, stats in (phase6.get("update_sensitivity") or {}).items()
                ],
            ),
            "",
        ]

    lines += ["## 4. RQ5/RQ7 — layer ranking and selective fine-tuning (Phase 7)", ""]
    if not phase7:
        lines.append(_missing("phase7/summary.json"))
    else:
        lines += [
            f"Consensus ranking (frozen on validation): {', '.join(phase7.get('consensus') or [])}",
            "",
            f"Ranking sources: {json.dumps(phase7.get('rank_sources'))}",
            "",
        ]
        if phase7.get("degraded_rank_sources"):
            lines += [f"Degraded / unavailable ranking sources: {phase7['degraded_rank_sources']}", ""]
        pairwise = ((phase7.get("rank_agreement") or {}).get("pairwise")) or {}
        if pairwise:
            lines += [
                "### Ranking agreement",
                "",
                _table(
                    ["pair", "spearman", "kendall", "top-3 overlap"],
                    [
                        [key, value.get("spearman"), value.get("kendall"), value.get("topk_overlap")]
                        for key, value in pairwise.items()
                    ],
                ),
                "",
            ]
        lines += [
            "### Validation fine-tuning comparison",
            "",
            _table(
                ["condition", "layers", "trainable ratio", "CE", "top-1", "top-5", "train s"],
                [
                    [
                        row.get("condition"),
                        ", ".join(row.get("layers") or []) if row.get("layers") else ("all" if row.get("condition") == "full" else "none"),
                        row.get("trainable_ratio"),
                        row.get("cross_entropy"),
                        row.get("top1_accuracy"),
                        row.get("topk_accuracy"),
                        (row.get("train") or {}).get("wall_time"),
                    ]
                    for row in (phase7.get("results") or [])
                ],
            ),
            "",
        ]

    lines += ["## 5. Final held-out test (Phase 8)", ""]
    if not phase8:
        lines.append(_missing("phase8/report.json"))
    else:
        result_b = phase8.get("result_b_layer_analysis") or {}
        baseline = result_b.get("test_baseline_policy") or {}
        lines += [
            f"analysis_test problems: {phase8.get('test_n_problems')}. Evaluated once, after every "
            "method, layer ranking and budget was frozen on validation.",
            "",
            _table(
                ["metric", "official checkpoint on test"],
                [
                    ["cross entropy", baseline.get("cross_entropy")],
                    ["top-1", baseline.get("top1_accuracy")],
                    ["top-5", baseline.get("topk_accuracy")],
                    ["valid rate", baseline.get("valid_rate")],
                    ["examples", baseline.get("n_examples")],
                ],
            ),
            "",
            "### Frozen conditions on the test split",
            "",
            _table(
                ["condition", "trainable ratio", "CE", "top-1", "MCTS exact", "MCTS mean TED"],
                [
                    [
                        row.get("condition"),
                        row.get("trainable_ratio"),
                        row.get("cross_entropy"),
                        row.get("top1_accuracy"),
                        (row.get("mcts_summary") or {}).get("n_exact"),
                        (row.get("mcts_summary") or {}).get("mean_ted_raw"),
                    ]
                    for row in (result_b.get("test_conditions") or [])
                ],
            ),
            "",
        ]

    lines += ["## 6. RQ8 — distance to the pretraining distribution (Phase 9)", ""]
    if not phase9:
        lines.append(_missing("phase9/summary.json"))
    else:
        lines += [
            _table(
                ["item", "value"],
                [
                    ["queries", phase9.get("n_queries")],
                    ["catalog size", phase9.get("catalog_size")],
                    ["catalog source", phase9.get("catalog_source")],
                    ["mean retrieved_nearest_ted (skeleton)", phase9.get("mean_retrieved_nearest_ted_skeleton")],
                    ["mean retrieved_nearest_ted (raw)", phase9.get("mean_retrieved_nearest_ted_raw")],
                ],
            ),
            "",
            phase9.get("note", ""),
            "",
        ]
    return "\n".join(lines) + "\n"


def write_problem_table(run_dir: Path, tables: Path) -> Path:
    rows = _read_jsonl(run_dir / "phase3" / "records.jsonl")
    for name in ("guided_mcts.json", "unguided_mcts.json"):
        record = _read(run_dir / "phase2" / name)
        if record:
            rows = [record] + rows
    recomputed = _read(run_dir / "structural_metrics_recomputed.json") or {}
    by_problem = {
        (row.get("problem_id"), row.get("condition")): row
        for row in (recomputed.get("records") or [])
        if row.get("status") == "recomputed"
    }
    header = [
        "problem_id",
        "system",
        "seed",
        "condition",
        "true_formula",
        "predicted_formula",
        "exact",
        "skeleton",
        "symbolic_equivalent",
        "ted_raw",
        "ted_skeleton",
        "exact_as_recorded",
        "ted_raw_as_recorded",
        "fit_error",
        "complexity",
        "valid",
        "failure_reason",
        "search_nodes",
        "candidate_count",
        "wall_time",
    ]
    path = tables / "problem_formulas.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            # Prefer the uniformly recanonicalized score when one exists.
            final = by_problem.get((row.get("problem_id"), row.get("condition")), {})
            writer.writerow(
                [
                    row.get("problem_id"),
                    row.get("system_name") or row.get("system_id"),
                    row.get("seed"),
                    row.get("condition"),
                    row.get("true_formula_raw"),
                    row.get("pred_formula_raw"),
                    final.get("exact", row.get("exact")),
                    final.get("skeleton", row.get("skeleton")),
                    final.get("symbolic_equivalent", row.get("symbolic_equivalent")),
                    final.get("ted_raw", row.get("ted_raw")),
                    final.get("ted_skeleton", row.get("ted_skeleton")),
                    row.get("exact"),
                    row.get("ted_raw"),
                    row.get("fit_error"),
                    row.get("complexity"),
                    row.get("valid"),
                    row.get("failure_reason"),
                    row.get("search_nodes"),
                    row.get("candidate_count"),
                    row.get("wall_time"),
                ]
            )
    return path


def write_layer_table(run_dir: Path, tables: Path) -> Path:
    phase4 = _read(run_dir / "phase4" / "summary.json") or {}
    phase5 = _read(run_dir / "phase5" / "summary.json") or {}
    phase6 = _read(run_dir / "phase6" / "summary.json") or {}
    phase7 = _read(run_dir / "phase7" / "summary.json") or {}
    layers = phase4.get("ranking_layers") or phase6.get("ranking_layers") or []

    def position(ranking, name):
        ranking = [item.replace("iole::", "") for item in (ranking or [])]
        return ranking.index(name) + 1 if name in ranking else None

    path = tables / "layer_summary.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "layer",
                "probe_rank",
                "gradient_rank",
                "decoderlens_rank",
                "iole_rank",
                "ablation_rank",
                "intervention_rank",
                "update_sensitivity_rank",
                "consensus_rank",
            ]
        )
        for name in layers:
            writer.writerow(
                [
                    name,
                    position(phase4.get("probe_rank_next_symbol"), name),
                    position(phase4.get("gradient_rank"), name),
                    position(phase5.get("decoderlens_rank"), name),
                    position(phase6.get("iole_rank"), name),
                    position(phase6.get("ablation_rank"), name),
                    position(phase6.get("intervention_rank"), name),
                    position(phase6.get("update_sensitivity_rank"), name),
                    position(phase7.get("consensus"), name),
                ]
            )
    return path


def main() -> int:
    args = parse_args()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    if not run_dir.is_dir():
        raise SystemExit(f"run directory not found: {run_dir}")
    _figures, tables = graphs_dir(args.run_id, config=config)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    repro = out_dir / "GPU_RUN3_nd2_reproduction_report.md"
    layer = out_dir / "GPU_RUN3_layer_analysis_report.md"
    repro.write_text(build_reproduction_report(run_dir, args.run_id), encoding="utf-8")
    layer.write_text(build_layer_report(run_dir, args.run_id), encoding="utf-8")
    problem_table = write_problem_table(run_dir, tables)
    layer_table = write_layer_table(run_dir, tables)
    for path in (repro, layer, problem_table, layer_table):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
