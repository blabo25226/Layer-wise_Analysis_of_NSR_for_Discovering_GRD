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
    return f"> `{name}` がこのrunディレクトリに存在しません。以下のセクションは不完全です。\n"


def _avg(values) -> float:
    finite = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def build_reproduction_report(run_dir: Path, run_id: str) -> str:
    preflight = _read(run_dir / "phase0" / "preflight.json") or {}
    phase1 = _read(run_dir / "phase1" / "summary.json")
    phase2 = _read(run_dir / "phase2" / "summary.json")
    phase3 = _read(run_dir / "phase3" / "summary.json")

    lines = [
        "# GPU_RUN3 — ND² 再現レポート",
        "",
        f"Run ID: `{run_id}`  ",
        f"キャンペーン: GPU_RUN3  ",
        "provenance: `upstream_reproduction`（公式実装の再現）",
        "",
        "## 1. 実行環境とprovenance",
        "",
    ]
    software = preflight.get("software", {})
    hardware = preflight.get("cpu", {})
    lines.append(
        _table(
            ["項目", "値"],
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
        "### NDformer アーキテクチャ",
        "",
        _table(
            ["項目", "値"],
            [
                ["encoder Transformer blocks", arch.get("n_encoder_transformer_layers")],
                ["decoder Transformer blocks", arch.get("n_decoder_transformer_layers")],
                ["total parameters", arch.get("total_parameters")],
                ["ranking layers", ", ".join(arch.get("ranking_layers") or [])],
            ],
        ),
        "",
        "### Go条件（Phase 0）",
        "",
        _table(
            ["条件", "結果"],
            [[k, v] for k, v in (preflight.get("go_conditions") or {}).items()],
        ),
        "",
        "## 2. RQ2 — NDformer policyの再現（Phase 1）",
        "",
    ]
    if not phase1:
        lines.append(_missing("phase1/summary.json"))
    else:
        lines.append(
            _table(
                ["指標", "値"],
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
                "シード別:",
                "",
                _table(
                    ["seed", "問題数", "例数", "CE", "top-1", "top-5", "valid率"],
                    [
                        [s["seed"], s["n_problems"], s["n_examples"], s["mean_ce"], s["mean_top1"], s["mean_topk"], s["valid_rate"]]
                        for s in per_seed
                    ],
                ),
            ]
        failures = phase1.get("failure_counts") or {}
        lines += ["", f"policyレベルの失敗: {failures if failures else 'なし'}", ""]

    lines += ["## 3. パイプライン再現（Phase 2、KUR）", ""]
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
        lines.append(_table(["項目", "値"], rows))
        unguided = phase2.get("unguided")
        if unguided:
            lines += [
                "",
                "同一問題・同一予算での unguided（一様）MCTS 対照:",
                "",
                _table(["項目", "値"], [[k, v] for k, v in unguided.items()]),
            ]

    lines += ["", "## 4. RQ1 — synthetic benchmarkの再現（Phase 3）", ""]
    if not phase3:
        lines.append(_missing("phase3/summary.json"))
    else:
        lines.append(
            _table(
                ["指標", "値"],
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
        # Structural columns come from the uniform recanonicalization; the values
        # Phase 3 recorded live are kept beside them so the difference is visible.
        rescored = _read(run_dir / "structural_metrics_recomputed.json") or {}
        by_system: dict[str, list[dict]] = {}
        for row in rescored.get("records") or []:
            if row.get("status") != "recomputed" or row.get("condition") != "ndformer_mcts":
                continue
            by_system.setdefault(str(row.get("system_id")), []).append(row)
        if per_system:
            lines += [
                "",
                "### システム別",
                "",
                "`exact` / `skeleton` / `平均TED` は再正規化後の値（第5節）。",
                "`exact（記録時）` はPhase 3が再スコアリング前に書いた値。",
                "",
                _table(
                    [
                        "システム",
                        "n",
                        "valid",
                        "exact",
                        "exact（記録時）",
                        "skeleton",
                        "平均TED",
                        "平均RMSE",
                        "平均R2",
                        "平均ノード数",
                        "平均秒",
                    ],
                    [
                        [
                            stats.get("paper_name", key),
                            stats.get("n"),
                            stats.get("n_valid"),
                            (
                                sum(1 for r in by_system[key] if r.get("exact") == 1.0)
                                if key in by_system
                                else stats.get("n_exact")
                            ),
                            stats.get("n_exact"),
                            (
                                sum(1 for r in by_system[key] if r.get("skeleton") == 1.0)
                                if key in by_system
                                else stats.get("n_skeleton")
                            ),
                            (
                                _avg([r.get("ted_raw") for r in by_system[key]])
                                if key in by_system
                                else stats.get("mean_ted_raw")
                            ),
                            stats.get("mean_fit_error"),
                            stats.get("mean_r2"),
                            stats.get("mean_search_nodes"),
                            stats.get("mean_wall_time"),
                        ]
                        for key, stats in per_system.items()
                    ],
                ),
                "",
                "### 真の式と回復された式",
                "",
            ]
            for key, stats in per_system.items():
                lines.append(f"**{stats.get('paper_name', key)}**")
                lines.append("")
                lines.append(f"- 真値: `{stats.get('true_formula')}`")
                for index, pred in enumerate(stats.get("pred_formulas") or []):
                    lines.append(f"- 予測（run {index + 1}）: `{pred}`")
                if stats.get("failure_reasons"):
                    lines.append(f"- 失敗: {', '.join(stats['failure_reasons'])}")
                lines.append("")
        unguided = phase3.get("unguided")
        if unguided:
            lines += [
                "### NDformer誘導あり vs unguided MCTS",
                "",
                _table(["項目", "値"], [[k, v] for k, v in unguided.items()]),
                "",
            ]

    recomputed = _read(run_dir / "structural_metrics_recomputed.json")
    lines += ["## 5. 単一の正規化による構造メトリクス", ""]
    if not recomputed:
        lines.append(_missing("structural_metrics_recomputed.json"))
    else:
        canon = recomputed.get("canonicalization") or {}
        lines += [
            "フェーズごとに異なる正規化リビジョンで結果が書かれうるため、保存されたprefixから",
            "全ての式を一度だけ一律に再スコアリングしている。定数は",
            f"{canon.get('numeric_significant_digits')}桁の有効数字で比較し、恒等式",
            f"{', '.join(canon.get('folds') or [])} を畳み込む（許容誤差 {canon.get('identity_atol')}）。",
            "",
            _table(
                ["指標", "記録時", "再正規化後"],
                [
                    ["exact回復数", recomputed.get("n_exact_as_recorded"), recomputed.get("n_exact")],
                    ["再スコアリング件数", recomputed.get("n_recomputed"), recomputed.get("n_recomputed")],
                    ["スコアが変化した件数", "-", recomputed.get("n_changed")],
                    ["skeleton回復数", "-", recomputed.get("n_skeleton")],
                ],
            ),
            "",
            "### 再スコアリングされたレコード",
            "",
            _table(
                ["問題", "条件", "exact", "skeleton", "TED", "記録時exact", "記録時TED", "RMSE"],
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
        "## 6. 数値の読み方",
        "",
        "- fit errorと式の回復は分けて報告している。RMSEが小さくても真のnetwork dynamics式を",
        "  回復したとは限らない（plan §6.5）。",
        "- 全runはproblem単位で `phase3/records.jsonl` に保存され、失敗・timeout・invalidな式も",
        "  除外せず含まれる（plan §6.4）。",
        "- KURの公式ネットワークファイルはZenodoアーカイブにのみ同梱される。存在しない場合は",
        "  Erdős–Rényiグラフにフォールバックし、`used_er_fallback` を立てる。",
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
        "# GPU_RUN3 — NDformer 層解析レポート",
        "",
        f"Run ID: `{run_id}`  ",
        "provenance: `layer_analysis`（層解析）",
        "",
        "解釈は最後まで区別している（plan §6.6）。probeは情報が線形に読み出せることを、",
        "ablationはそのブロックが必要であることを、activation interventionは因果的に影響することを、",
        "IOLEはその層だけで適応できることを、それぞれ示す。混同しない。",
        "",
        "## 1. RQ3 — 層ごとの情報表現（Phase 4）",
        "",
    ]
    if not phase4:
        lines.append(_missing("phase4/summary.json"))
    else:
        layers = phase4.get("ranking_layers") or []
        lines += [
            f"probeは `{phase4.get('probe_fit_split')}` で学習し、`{phase4.get('probe_eval_split')}` で評価した。"
            "各スコアには同じ手順で学習したラベルシャッフル対照を併記している。",
            "",
        ]
        for task, scores in (phase4.get("probe_scores") or {}).items():
            control = (phase4.get("probe_control_scores") or {}).get(task, {})
            delta = (phase4.get("probe_minus_control") or {}).get(task, {})
            lines += [
                f"### probeタスク: `{task}`",
                "",
                _table(
                    ["層", "スコア", "ラベルシャッフル対照", "スコア − 対照"],
                    [[name, scores.get(name), control.get(name), delta.get(name)] for name in layers],
                ),
                "",
            ]
        lines += [
            "### gradient normと特徴量の変動",
            "",
            _table(
                ["層", "gradient norm", "パラメータ当たり", "パラメータ数", "問題内変動"],
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
            "encoderの活性はデコード中のprefixに依存しないため、problem内変動はほぼ0になる。"
            "したがってnext_symbolのような例単位のタスクはdecoderブロックについてのみ意味を持つ。",
            "",
            "### CKA（問題単位の表現）",
            "",
            _table(
                ["層ペア", "CKA"],
                [[key, value] for key, value in sorted((phase4.get("cka_problem_level") or {}).items())],
            ),
            "",
        ]

    lines += ["## 2. RQ6 — 数式構造はどの層で形成されるか（Phase 5）", ""]
    if not phase5:
        lines.append(_missing("phase5/summary.json"))
    else:
        for label, key in (("encoder中間層のデコード", "encoder_layer_summary"), ("decoder logit lens", "decoder_layer_summary")):
            stats = phase5.get(key) or {}
            lines += [
                f"### {label}",
                "",
                _table(
                    ["層", "n", "真シンボル順位", "真シンボル確率", "top-1", "エントロピー", "平均TED"],
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
        lines += [
            "encoder_intermediate_decode は各encoderブロックのmemoryを学習済みdecoderへ渡す手法である。"
            "DecoderLensと同じ趣旨だが同一の手法ではない。NDformerには層ごとのdecoder対応が無いためである。",
            "",
            f"失敗数: {phase5.get('n_failures')}",
            "",
        ]

    lines += ["## 3. RQ4 — 層の因果的寄与（Phase 6）", ""]
    if not phase6:
        lines.append(_missing("phase6/summary.json"))
    else:
        baseline = phase6.get("baseline") or {}
        lines += [
            f"パネル: validation {phase6.get('n_panel_problems')}問題、seed {phase6.get('seed')}。"
            f"baseline CE {_fmt(baseline.get('cross_entropy'))}、top-1 {_fmt(baseline.get('top1_accuracy'))}。",
            "",
            "### 層ごとの効果（同一パネルのbaselineとの差分）",
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
            "### IOLE 単一層fine-tuning",
            "",
            _table(
                ["条件", "cross entropy"],
                [[k, v] for k, v in (phase6.get("iole_ce") or {}).items()],
            ),
            "",
            "### パラメータ更新感度（統制された全層FT）",
            "",
            _table(
                ["層", "||Δθ||", "||θ||", "相対値"],
                [
                    [name, stats.get("delta_l2"), stats.get("theta_l2"), stats.get("relative_l2")]
                    for name, stats in (phase6.get("update_sensitivity") or {}).items()
                ],
            ),
            "",
        ]

    lines += ["## 4. RQ5/RQ7 — 層ランキングと選択的fine-tuning（Phase 7）", ""]
    if not phase7:
        lines.append(_missing("phase7/summary.json"))
    else:
        lines += [
            f"consensusランキング（validationで固定）: {', '.join(phase7.get('consensus') or [])}",
            "",
            f"ランキングの情報源: {json.dumps(phase7.get('rank_sources'))}",
            "",
        ]
        if phase7.get("degraded_rank_sources"):
            lines += [f"劣化・利用不可のランキング情報源: {phase7['degraded_rank_sources']}", ""]
        pairwise = ((phase7.get("rank_agreement") or {}).get("pairwise")) or {}
        if pairwise:
            lines += [
                "### ランキングの一致度",
                "",
                _table(
                    ["ペア", "Spearman", "Kendall", "top-3一致率"],
                    [
                        [key, value.get("spearman"), value.get("kendall"), value.get("topk_overlap")]
                        for key, value in pairwise.items()
                    ],
                ),
                "",
            ]
        # RQ5's random control is uninformative at k=3 when only 4 blocks are ranked
        # (there are just 4 possible 3-subsets), so derive the k=1 random baseline
        # from the Phase 6 IOLE sweep, which already trained every layer alone.
        iole_ce = {
            name.replace("iole::", ""): value
            for name, value in ((phase6.get("iole_ce") or {}).items())
            if name not in {"frozen", "full"}
        }
        top1 = (phase7.get("conditions") or {}).get("top_1") or []
        if iole_ce and top1:
            values = [v for v in iole_ce.values() if v is not None and math.isfinite(float(v))]
            expected_random = sum(values) / len(values) if values else float("nan")
            chosen = iole_ce.get(top1[0], float("nan"))
            random_3 = set((phase7.get("conditions") or {}).get("random_3") or [])
            top_3 = set((phase7.get("conditions") or {}).get("top_3") or [])
            lines += [
                "### RQ5 ランダム対照",
                "",
                f"`random_3` は {sorted(random_3)}、`top_3` は {sorted(top_3)}。"
                f"両者は{'同一' if random_3 == top_3 else '異なる'}。"
                f"ランキング対象が{len(phase7.get('consensus') or [])}ブロックしかないため3要素の部分集合は数通りしかなく、"
                "ランダムに3層選ぶとtop 3と構造的に重複してしまう。したがって"
                "このアーキテクチャではk=3の比較でRQ5に答えられない。",
                "",
                "k=1なら比較は成立する。Phase 6のIOLEスイープ（全ブロックを同一予算で単独学習）が、"
                "ランダムに1層選んだ場合の分布そのものなので、これを対照として使う:"
                "",
                "",
                _table(
                    ["量", "cross entropy"],
                    [
                        [f"top_1（{top1[0]}）", chosen],
                        ["ランダム1層の期待値（全ブロック平均）", expected_random],
                        ["top_1の優位", expected_random - chosen if values else float("nan")],
                        ["最悪の単一層", max(values) if values else float("nan")],
                        ["最良の単一層", min(values) if values else float("nan")],
                    ],
                ),
                "",
            ]
        lines += [
            "### validationでのfine-tuning比較",
            "",
            _table(
                ["条件", "対象層", "学習パラメータ比", "CE", "top-1", "top-5", "学習秒"],
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

    lines += ["## 5. 最終test評価（Phase 8）", ""]
    if not phase8:
        lines.append(_missing("phase8/report.json"))
    else:
        result_b = phase8.get("result_b_layer_analysis") or {}
        baseline = result_b.get("test_baseline_policy") or {}
        lines += [
            f"analysis_test の問題数: {phase8.get('test_n_problems')}。手法・層ランキング・予算をすべてvalidationで"
            "固定した後、一度だけ評価した。",
            "",
            _table(
                ["指標", "公式checkpointのtest評価"],
                [
                    ["cross entropy", baseline.get("cross_entropy")],
                    ["top-1", baseline.get("top1_accuracy")],
                    ["top-5", baseline.get("topk_accuracy")],
                    ["valid rate", baseline.get("valid_rate")],
                    ["examples", baseline.get("n_examples")],
                ],
            ),
            "",
            "### 固定条件のtest split評価",
            "",
            _table(
                ["条件", "学習パラメータ比", "CE", "top-1", "MCTS exact", "MCTS平均TED"],
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

    lines += ["## 6. RQ8 — 事前学習分布との距離（Phase 9）", ""]
    if not phase9:
        lines.append(_missing("phase9/summary.json"))
    else:
        lines += [
            _table(
                ["項目", "値"],
                [
                    ["クエリ数", phase9.get("n_queries")],
                    ["カタログ数", phase9.get("catalog_size")],
                    ["カタログ生成元", phase9.get("catalog_source")],
                    ["平均 retrieved_nearest_ted（skeleton）", phase9.get("mean_retrieved_nearest_ted_skeleton")],
                    ["平均 retrieved_nearest_ted（raw）", phase9.get("mean_retrieved_nearest_ted_raw")],
                ],
            ),
            "",
            "公式の式文法からサンプリングしたカタログに対する近似検索であり、100万件の事前学習アーカイブ"
            "全体との厳密な最近傍ではない。そのため plan §12 に従い retrieved_nearest_ted と表記する。",
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
