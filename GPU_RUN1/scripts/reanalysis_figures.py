#!/usr/bin/env python
"""GPU_RUN1 再解析の図表を生成する。

保存済みJSONのみを入力とし、新規の学習・推論は行わない。
出力先は AGENTS.md 6.3 / graphs/README.md の規約に従い
``graphs/<run-id>/figures/`` と ``graphs/<run-id>/tables/`` である。

入力（すべて ``results/runs/<run-id>/`` 配下）
    phase4_multiseed/raw_scores_seed{0,1,2}.json
    phase4_multiseed/equations_seed{0,1,2}.json
    phase4_multiseed/layer_rankings.json
    phase5_multiseed/summary.json
    phase5_seed{0,1,2}/selective_results.json
    phase6_noise_multiseed/summary.json
    phase7_multiseed/summary.json
    phase8_lodo_seed{0,1,2}/lodo_results.json
    phase8_pysr_seed{0,1,2}/pysr_results.json
    data/synthetic/<suite>/index.json

図中テキストは英語である。実行環境にCJKフォントが無い場合に日本語が
豆腐化するのを避けるためであり、caption と本文レポートは日本語で書く。

使用例::

    python GPU_RUN1/scripts/reanalysis_figures.py \
        --run-id colab_reduced_20260729_03 \
        --suite diverse_gpu_n0.1
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

# ---------------------------------------------------------------- style

BLUE = "#1f6fb4"
RED = "#c0504d"
GREY = "0.6"

#: 図の体裁。publication向けに8/7/6ptの三段構成、上・右のspineを落とす。
RC = {
    "font.family": "sans-serif",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "legend.frameon": False,
    "figure.dpi": 200,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.titleweight": "normal",
    "axes.titlelocation": "left",
    "lines.linewidth": 1.2,
    "patch.linewidth": 0.6,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}

LAYERS = [
    "pretrained", "output_head",
    "encoder_0", "encoder_1", "encoder_2", "encoder_3", "encoder_4", "encoder_5",
    "decoder_0", "decoder_1", "decoder_2", "decoder_3", "decoder_4",
    "all_params",
]

#: Phase 6 の 2x2（探索法 x fine-tuning）
NOISE_METHODS = ["pretrained_beam", "selective_beam", "pretrained_tpsr", "selective_tpsr"]
NOISE_LABELS = ["beam\nno FT", "beam\nsel. FT", "TPSR\nno FT", "TPSR\nsel. FT"]

#: Phase 8 の3方法
HUMAN_METHODS = ["pretrained_beam", "selective_beam", "pysr"]
HUMAN_LABELS = ["NeSymReS\nno FT", "NeSymReS\nselective FT", "PySR"]
HUMAN_COLORS = [GREY, BLUE, RED]

SELECTORS = ["corr", "lasso", "mi", "oracle"]
SELECTOR_LABELS = ["correlation", "lasso", "mutual inf.", "oracle"]

#: 指数多重集合の表示順。train pool と test 真値の双方に現れる集合を網羅する。
EXP_SETS = [(), (2,), (2, 2), (3,), (3, 3), (4, 4), (2, 2, 2), (2, 2, 2, 2)]


def panel_letter(ax, letter, dx=-0.18, dy=1.02):
    """axes左上外側に太字のpanel letterを置く。"""
    ax.text(dx, dy, letter.lower(), transform=ax.transAxes,
            fontweight="bold", fontsize=plt.rcParams["font.size"] + 1,
            va="bottom", ha="left")


# ---------------------------------------------------------------- helpers

def skeleton_of(eq_id: str) -> str:
    """式IDから末尾のsplit・インスタンス番号を除き骨格名を返す。"""
    return re.sub(r"_(train|val|test)_\d+$", "", eq_id)


def exponents_of(expr: str) -> list[int]:
    """式文字列に現れる ``**n`` の指数を昇順の多重集合として返す。"""
    return sorted(int(m) for m in re.findall(r"\*\*(\d+)", expr))


def exponent_set_fractions(counter: collections.Counter) -> np.ndarray:
    """指数多重集合のCounterを EXP_SETS 順の相対頻度に変換する。"""
    total = max(sum(counter.values()), 1)
    return np.array([counter.get(s, 0) for s in EXP_SETS], dtype=float) / total


def exp_set_label(s: tuple[int, ...]) -> str:
    return "none" if not s else "\u00b7".join(map(str, s))


def student_t_ci95(values) -> float:
    """Student t による95%信頼区間の半幅。少数seedのため正規近似は使わない。"""
    from math import sqrt
    v = np.asarray([x for x in values if x is not None], dtype=float)
    n = len(v)
    if n < 2:
        return float("nan")
    # t_{0.975, df} を scipy 無しで得るため、小さいdfのみ表引きする。
    tcrit = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
             6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}
    t = tcrit.get(n - 1, 1.96)
    return t * v.std(ddof=1) / sqrt(n)


# ---------------------------------------------------------------- loaders

def load_suite_index(repo: Path, run: Path, suite: str) -> list[dict]:
    """合成データsuiteのindexを読む。

    GPU runは使用したsuiteを ``results/runs/<run-id>/input_data/<suite>/`` に
    同梱するため、そこを優先する。無い場合は ``results/synthetic/`` と
    ``data/synthetic/`` を順に探す。
    """
    candidates = [
        run / "input_data" / suite / "index.json",
        repo / "results" / "synthetic" / suite / "index.json",
        repo / "data" / "synthetic" / suite / "index.json",
    ]
    for path in candidates:
        if path.exists():
            with path.open() as fh:
                return json.load(fh)
    raise SystemExit("suite index not found; tried:\n  " + "\n  ".join(map(str, candidates)))


def load_validation_equations(run: Path, seeds) -> pd.DataFrame:
    """Phase 4 の per-problem 記録（validation split）を一枚の表にする。"""
    rows = []
    for seed in seeds:
        path = run / "phase4_multiseed" / f"equations_seed{seed}.json"
        with path.open() as fh:
            payload = json.load(fh)
        for condition, records in payload.items():
            for rec in records:
                rows.append(dict(
                    seed=seed, condition=condition, eq_id=rec["eq_id"],
                    skeleton=skeleton_of(rec["eq_id"]),
                    true=rec["true"], pred=rec["pred"], nmse=rec["nmse"],
                    var_f1=rec["var_f1"], complexity=rec["complexity"],
                    failure_reason=rec.get("failure_reason"),
                    sym_exact=rec.get("sym_exact"),
                    sym_skeleton=rec.get("sym_skeleton"),
                    sym_equiv=rec.get("sym_equiv"),
                    sym_recovery=rec.get("sym_recovery"),
                ))
    return add_exponent_columns(pd.DataFrame(rows))


def add_exponent_columns(df: pd.DataFrame) -> pd.DataFrame:
    """真値・予測の指数多重集合とその一致フラグを付与する。"""
    df["true_exp"] = df["true"].map(lambda s: exponents_of(str(s)))
    df["pred_exp"] = df["pred"].map(lambda s: exponents_of(str(s)))
    df["exp_match"] = [t == p for t, p in zip(df.true_exp, df.pred_exp)]
    return df


def load_test_equations(run: Path, seeds, condition="all_params") -> pd.DataFrame:
    """Phase 5 の per-problem 記録（test split）を一枚の表にする。"""
    rows = []
    for seed in seeds:
        path = run / f"phase5_seed{seed}" / "selective_results.json"
        with path.open() as fh:
            payload = json.load(fh)
        for cond in payload:
            if cond["condition"] != condition:
                continue
            for rec in cond["per_problem"]:
                rows.append(dict(
                    seed=seed, condition=cond["condition"], eq_id=rec["eq_id"],
                    skeleton=skeleton_of(rec["eq_id"]),
                    true=rec["true"], pred=rec["pred"], nmse=rec["nmse"],
                    var_f1=rec["var_f1"], complexity=rec["complexity"],
                    failure_reason=rec.get("failure_reason"),
                    sym_exact=rec.get("sym_exact"),
                    sym_skeleton=rec.get("sym_skeleton"),
                    sym_equiv=rec.get("sym_equiv"),
                    sym_recovery=rec.get("sym_recovery"),
                ))
    return add_exponent_columns(pd.DataFrame(rows))


def recovery_by_skeleton(df: pd.DataFrame) -> pd.DataFrame:
    """骨格別の skeleton recovery と指数集合一致率。"""
    agg = {"skeleton_recovery": ("sym_skeleton", "mean"), "n": ("sym_skeleton", "size")}
    if "exp_match" in df:
        agg["exp_match"] = ("exp_match", "mean")
    out = df.groupby("skeleton").agg(**agg)
    if "exp_match" not in out:
        out["exp_match"] = np.nan
    return out


# ---------------------------------------------------------------- figures

def fig_layer_contribution(run: Path, seeds, out: Path) -> Path:
    """図1: 単層fine-tuningの寄与プロファイル（validation）。"""
    raw = {}
    for seed in seeds:
        with (run / "phase4_multiseed" / f"raw_scores_seed{seed}.json").open() as fh:
            raw[seed] = json.load(fh)
    pen = pd.DataFrame({s: raw[s]["penalized_nmse"] for s in seeds}).reindex(LAYERS)
    ce = pd.DataFrame({s: raw[s]["val_ce"] for s in seeds}).reindex(LAYERS)

    inner = [L for L in LAYERS if L not in ("pretrained", "all_params")]
    x = np.arange(len(inner))
    fig, axes = plt.subplots(2, 1, figsize=(5.4, 4.4), sharex=True)

    for ax, frame, ylabel, title in (
        (axes[0], pen, "failure-penalized NMSE\n(validation)",
         "Single-layer fine-tuning: decoder middle layers carry the contribution"),
        (axes[1], ce, "validation cross-entropy", None),
    ):
        sub = frame.loc[inner]
        mean = sub.mean(axis=1).values
        err = np.array([student_t_ci95(sub.loc[L].values) for L in inner])
        colors = [BLUE if L.startswith("decoder") else GREY for L in inner]
        ax.bar(x, mean, yerr=err, color=colors, capsize=2.5,
               error_kw=dict(lw=0.8, ecolor="0.25"), zorder=2)
        for i, L in enumerate(inner):
            ax.scatter([i] * len(seeds), sub.loc[L].values, s=7, color="0.1", zorder=5, lw=0)
        # 参照線（pretrained / all layers）も軸内に収める。
        top = max(max(mean + err), frame.loc["pretrained"].mean()) * 1.14
        ax.set_ylim(0, top)
        for label, key, style in (("pretrained", "pretrained", ":"), ("all layers", "all_params", "--")):
            ref = frame.loc[key].mean()
            ax.axhline(ref, ls=style, lw=0.9, color="0.25", zorder=1)
            # 破線の上に置く。線の上に重ねると読めなくなる。
            ax.text(len(inner) - 0.35, ref + 0.012 * top, label, fontsize=5.5, color="0.25",
                    va="bottom", ha="left")
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title, pad=6)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([L.replace("_", " ") for L in inner], rotation=45, ha="right")
    axes[1].set_xlim(-0.8, len(inner) + 1.6)
    axes[1].legend(handles=[Patch(color=BLUE, label="decoder"), Patch(color=GREY, label="encoder / head")],
                   loc="upper right", fontsize=6, bbox_to_anchor=(1.0, 0.72))
    for ax, letter in zip(axes, "ab"):
        panel_letter(ax, letter, dx=-0.11, dy=1.02)
    fig.tight_layout()
    path = out / "phase4_layer_contribution.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return path


def fig_recovery_and_equivalence(run: Path, suite_index, val: pd.DataFrame,
                                 test: pd.DataFrame, out: Path) -> Path:
    """図2: 式回復の分解と同等性検定。"""
    with (run / "phase5_multiseed" / "summary.json").open() as fh:
        p5 = json.load(fh)
    margin = p5["nmse_equivalence_margin"]

    val_fam = recovery_by_skeleton(val[val.condition == "all_params"]).sort_values(
        "skeleton_recovery", ascending=False)
    test_fam = recovery_by_skeleton(test)

    fig, axes = plt.subplots(1, 3, figsize=(8.4, 3.2),
                             gridspec_kw=dict(width_ratios=[1.18, 1.0, 1.0]))

    # (a) 骨格別 recovery。上段 validation（訓練済み骨格）、下段 test（未知骨格）。
    ax = axes[0]
    names = list(val_fam.index) + list(test_fam.index)
    y = np.arange(len(names))[::-1].astype(float)
    y[len(val_fam):] -= 0.8  # 2ブロックの間に視覚的な間隔を入れる
    values = list(val_fam.skeleton_recovery) + list(test_fam.skeleton_recovery)
    exp_match = list(val_fam.exp_match) + list(test_fam.exp_match)
    colors = [BLUE] * len(val_fam) + [RED] * len(test_fam)
    ax.barh(y, values, color=colors, height=0.62, zorder=2)
    ax.scatter(exp_match, y, marker="|", s=95, color="0.05", zorder=5, lw=1.4)
    ax.set_yticks(y)
    ax.set_yticklabels([n.replace("_", " ") for n in names])
    ax.axhline((y[len(val_fam) - 1] + y[len(val_fam)]) / 2, color="0.4", lw=0.8)
    ax.set_xlabel("rate (all-layer FT, 3 seeds)")
    ax.set_xlim(0, 1.30)
    ax.set_ylim(y[-1] - 0.7, y[0] + 0.7)
    ax.text(1.28, y[3], "validation\nskeletons seen\nin training",
            fontsize=6, color=BLUE, ha="right", va="center")
    ax.text(1.28, y[len(val_fam) + 1], "test\nskeletons absent\nfrom training",
            fontsize=6, color=RED, ha="right", va="center")
    ax.set_title("Recovery is family-specific,\nnot uniformly zero", pad=6)
    # 凡例は軸下の外側へ。バーも test ブロックの注記も隠さない。
    ax.legend(handles=[Patch(color="0.45", label="skeleton recovery"),
                       plt.Line2D([], [], marker="|", ls="", color="0.05", ms=7,
                                  label="exponent-set match")],
              loc="upper left", fontsize=6, ncol=2, columnspacing=1.0,
              handlelength=1.4, bbox_to_anchor=(0.0, -0.20))

    # (b) 指数多重集合の分布。予測は訓練poolに追従しtest真値を出力しない。
    ax = axes[1]
    train_counter = collections.Counter(
        tuple(exponents_of(r["motif"])) for r in suite_index if r["split"] == "train")
    true_counter = collections.Counter(tuple(e) for e in test.true_exp)
    pred_counter = collections.Counter(tuple(e) for e in test.pred_exp)
    x = np.arange(len(EXP_SETS))
    width = 0.27
    for offset, counter, color, label in (
        (-width, train_counter, "0.55", "train pool (true)"),
        (0.0, true_counter, RED, "test (true)"),
        (width, pred_counter, BLUE, "test (predicted)"),
    ):
        ax.bar(x + offset, exponent_set_fractions(counter), width, color=color, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels([exp_set_label(s) for s in EXP_SETS], rotation=45, ha="right")
    ax.set_xlabel("exponent multiset in expression", labelpad=1)
    ax.set_ylabel("fraction of problems")
    ax.set_ylim(0, 0.50)
    ax.set_title("Predicted exponents follow the\ntraining pool, not the test truth", pad=6)
    ax.legend(fontsize=6, loc="upper right")

    # (c) 事前指定marginに対する paired 差。
    ax = axes[2]
    equiv = p5["top_vs_full_equivalence"]
    improvement = p5["top_minus_random_improvement"]
    rows = [("top-1 \u2212 full FT", equiv["top_1"]),
            ("top-2 \u2212 full FT", equiv["top_2"]),
            ("top-3 \u2212 full FT", equiv["top_3"])]
    yy = np.array([3.0, 2.0, 1.0, -0.15])
    for i, (_, stat) in enumerate(rows):
        ax.errorbar(stat["mean"], yy[i], xerr=stat["ci95"], fmt="o", ms=4.5,
                    color=BLUE, capsize=2.5, lw=1.1, zorder=3)
    ax.errorbar(improvement["mean"], yy[3], xerr=improvement["ci95"], fmt="s", ms=4.5,
                color=RED, capsize=2.5, lw=1.1, zorder=3)
    ax.axvline(0, color="0.2", lw=0.9, zorder=1)
    ax.axvspan(-margin, margin, color="0.9", zorder=0)
    ax.set_yticks(yy)
    ax.set_yticklabels([r[0] for r in rows] + ["random-3 \u2212 top-3"])
    ax.set_xlabel("\u0394 failure-penalized NMSE (test)", labelpad=1)
    ax.set_xlim(-0.010, 0.0135)
    ax.set_ylim(-0.85, 3.8)
    ax.set_title("Top-k matches full FT;\ntop vs random undecided", pad=6)
    ax.text(0.0132, 3.6, f"grey band = pre-specified\nequivalence margin \u00b1{margin:g}",
            fontsize=5.5, color="0.35", ha="right", va="top")
    ax.text(0.0132, -0.75, "positive favors top-3", fontsize=5.5, color=RED,
            ha="right", va="bottom")

    for ax, letter in zip(axes, "abc"):
        panel_letter(ax, letter, dx=-0.25, dy=1.05)
    fig.tight_layout()
    path = out / "phase45_recovery_and_equivalence.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return path


def fig_baselines_and_transfer(run: Path, out: Path, noise="0.1") -> Path:
    """図3: 探索法・実ネットワーク転移・regulator selection。"""
    with (run / "phase6_noise_multiseed" / "summary.json").open() as fh:
        p6 = json.load(fh)
    with (run / "phase7_multiseed" / "summary.json").open() as fh:
        p7 = json.load(fh)
    noise_summary = p6["summary"][noise]

    fig, axes = plt.subplots(1, 3, figsize=(8.6, 3.3),
                             gridspec_kw=dict(width_ratios=[1.0, 1.05, 1.05]))

    # (a) 2x2: 探索法 x fine-tuning。実時間とvalid rateを注記する。
    ax = axes[0]
    stats = [noise_summary[m]["penalized_nmse"] for m in NOISE_METHODS]
    colors = [GREY, BLUE, GREY, BLUE]
    x = np.arange(len(NOISE_METHODS))
    ax.bar(x, [s["mean"] for s in stats], yerr=[s["ci95"] for s in stats], color=colors,
           capsize=2.5, error_kw=dict(lw=0.8, ecolor="0.25"), zorder=2)
    for i, m in enumerate(NOISE_METHODS):
        ax.scatter([i] * len(noise_summary[m]["penalized_nmse"]["values"]),
                   noise_summary[m]["penalized_nmse"]["values"],
                   s=7, color="0.1", zorder=5, lw=0)
        minutes = noise_summary[m]["elapsed_sec"]["mean"] / 60
        valid = noise_summary[m]["valid_rate"]["mean"]
        ax.text(i, stats[i]["mean"] + stats[i]["ci95"] + 0.004,
                f"{minutes:.0f} min\nvalid {valid:.2f}",
                ha="center", va="bottom", fontsize=5.5, color="0.25")
    ratio = np.mean([
        noise_summary["pretrained_tpsr"]["elapsed_sec"]["mean"] / noise_summary["pretrained_beam"]["elapsed_sec"]["mean"],
        noise_summary["selective_tpsr"]["elapsed_sec"]["mean"] / noise_summary["selective_beam"]["elapsed_sec"]["mean"],
    ])
    ax.set_xticks(x)
    ax.set_xticklabels(NOISE_LABELS, fontsize=6)
    ax.set_ylabel(f"failure-penalized NMSE\n(test, noise {noise})")
    ax.set_ylim(0, 0.122)
    ax.set_title(f"Selective FT beats decode search;\nTPSR costs ~{ratio:.0f}\u00d7 the wall time", pad=6)
    ax.text(0.99, 0.99, "lower = better", transform=ax.transAxes, ha="right", va="top",
            fontsize=6, color="0.35")
    ax.legend(handles=[Patch(color=GREY, label="no fine-tuning"), Patch(color=BLUE, label="selective FT")],
              fontsize=6, loc="upper center", bbox_to_anchor=(0.5, 0.93))

    # (b) DREAM4転移。破線は平均予測器（NMSE=1）。
    ax = axes[1]
    combos = [("10", "pretrained_oracle"), ("10", "selective_corr"), ("10", "selective_oracle"),
              ("100", "pretrained_oracle"), ("100", "selective_corr"), ("100", "selective_oracle")]
    xs = np.array([0, 1, 2, 3.6, 4.6, 5.6])
    colors = [GREY, RED, BLUE] * 2
    stats = [p7["sizes"][size]["sr"][method]["penalized_nmse"] for size, method in combos]
    ax.bar(xs, [s["mean"] for s in stats], yerr=[s["ci95"] for s in stats], color=colors,
           capsize=2.5, error_kw=dict(lw=0.8, ecolor="0.25"), zorder=2, width=0.8)
    ax.axhline(1.0, ls="--", lw=1.0, color="0.15", zorder=1)
    ax.text(5.95, 1.01, "NMSE = 1  (mean predictor)", fontsize=5.5, color="0.15",
            ha="right", va="bottom")
    ax.set_xticks(xs)
    ax.set_xticklabels(["oracle\nno FT", "corr\nsel.FT", "oracle\nsel.FT"] * 2, fontsize=5.5)
    ax.set_ylabel("failure-penalized NMSE (DREAM4)")
    ax.set_ylim(0, 1.22)
    ax.text(1, -0.255, "Size10 (p=10)", transform=ax.get_xaxis_transform(),
            ha="center", fontsize=6.5, color="0.15")
    ax.text(4.6, -0.255, "Size100 (p=100)", transform=ax.get_xaxis_transform(),
            ha="center", fontsize=6.5, color="0.15")
    ax.set_title("Real-network transfer fails:\nevery arm near the mean predictor", pad=6)

    # (c) regulator selection の edge F1。
    ax = axes[2]
    x = np.arange(len(SELECTORS))
    width = 0.36
    for j, (size, color) in enumerate((("10", BLUE), ("100", RED))):
        stats = [p7["sizes"][size]["selection_edge_f1"][s] for s in SELECTORS]
        ax.bar(x + (j - 0.5) * width, [s["mean"] for s in stats], width,
               yerr=[s["ci95"] for s in stats], color=color, capsize=2,
               error_kw=dict(lw=0.8, ecolor="0.25"), label=f"Size{size} (p={size})", zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(SELECTOR_LABELS, rotation=30, ha="right")
    ax.set_ylabel("regulator-selection edge F1")
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=6, loc="upper center")
    ax.set_title("Empirical selectors collapse at p=100;\nthe oracle is unchanged", pad=6)
    ax.text(0.02, 0.62, "higher = better", transform=ax.transAxes, ha="left",
            fontsize=6, color="0.35")

    for ax, letter in zip(axes, "abc"):
        panel_letter(ax, letter, dx=-0.27, dy=1.05)
    fig.tight_layout()
    path = out / "phase67_baselines_and_transfer.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return path


def load_human_folds(run: Path, seeds) -> pd.DataFrame:
    """Phase 8 の per-fold 記録（donor別）を一枚の表にする。"""
    rows = []
    for seed in seeds:
        with (run / f"phase8_lodo_seed{seed}" / "lodo_results.json").open() as fh:
            lodo = json.load(fh)
        for fold in lodo["per_fold"]:
            for method in ("pretrained_beam", "selective_beam"):
                if method in fold:
                    rows.append(dict(seed=seed, donor=fold["holdout"], method=method,
                                     in_donor=fold[method]["in"], holdout=fold[method]["hold"]))
        pysr_path = run / f"phase8_pysr_seed{seed}" / "pysr_results.json"
        if pysr_path.exists():
            with pysr_path.open() as fh:
                pysr = json.load(fh)
            for fold in pysr["per_fold"]:
                rows.append(dict(seed=seed, donor=fold["holdout"], method="pysr",
                                 in_donor=fold["pysr"]["in"], holdout=fold["pysr"]["hold"]))
    return pd.DataFrame(rows)


def fig_human_lodo(run: Path, folds: pd.DataFrame, out: Path) -> Path:
    """図4: ヒトデータ leave-one-donor-out。"""
    with (run / "phase8_lodo_multiseed" / "summary.json").open() as fh:
        p8 = json.load(fh)

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2),
                             gridspec_kw=dict(width_ratios=[1.0, 1.15]))

    # (a) in-donor と held-out donor。
    ax = axes[0]
    x = np.arange(len(HUMAN_METHODS))
    width = 0.34
    for j, (key, hatch) in enumerate((("mean_in", ""), ("mean_hold", "///"))):
        stats = [p8["summary"][m][key] for m in HUMAN_METHODS]
        ax.bar(x + (j - 0.5) * width, [s["mean"] for s in stats], width,
               yerr=[s["ci95"] for s in stats], color=HUMAN_COLORS, hatch=hatch,
               edgecolor="white", capsize=2.5, error_kw=dict(lw=0.8, ecolor="0.25"), zorder=2)
        for i, s in enumerate(stats):
            ax.scatter([x[i] + (j - 0.5) * width] * len(s["values"]), s["values"],
                       s=7, color="0.1", zorder=5, lw=0)
    ax.axhline(1.0, ls="--", lw=1.0, color="0.15", zorder=1)
    ax.text(2.45, 1.015, "NMSE = 1 (mean predictor)", fontsize=5.5, color="0.15",
            ha="right", va="bottom")
    ax.set_xticks(x)
    ax.set_xticklabels(HUMAN_LABELS, fontsize=6)
    ax.set_ylabel("NMSE (finite-difference targets)")
    ax.set_ylim(0, 1.50)
    ax.set_title("Every method loses most of its fit\non a held-out donor", pad=6)
    # 凡例は軸下の外側へ。gap 注記と競合させない。
    ax.legend(handles=[Patch(facecolor="0.75", edgecolor="white", label="in-donor (fit)"),
                       Patch(facecolor="0.75", edgecolor="white", hatch="///",
                             label="held-out donor")],
              fontsize=6, loc="upper left", ncol=2, columnspacing=1.0,
              handlelength=1.4, bbox_to_anchor=(0.0, -0.13))
    for i, m in enumerate(HUMAN_METHODS):
        gap = p8["summary"][m]["gap_mean"]
        ax.text(x[i], 1.46, f"gap\n{gap['mean']:+.2f}\u00b1{gap['ci95']:.2f}",
                ha="center", va="top", fontsize=5.5, color="0.2")

    # (b) donor別 holdout NMSE。donor 11 で順序が逆転する。
    ax = axes[1]
    donors = ["1", "2", "10", "11"]
    markers = dict(pretrained_beam="o", selective_beam="s", pysr="^")
    labels = dict(pretrained_beam="NeSymReS no FT", selective_beam="NeSymReS selective FT",
                  pysr="PySR")
    for method, color in zip(HUMAN_METHODS, HUMAN_COLORS):
        means = folds[folds.method == method].groupby("donor").holdout.mean().reindex(donors)
        ax.plot(range(len(donors)), means.values, marker=markers[method], ms=5,
                color=color, lw=1.2, zorder=3, label=labels[method])
        for i, donor in enumerate(donors):
            points = folds[(folds.method == method) & (folds.donor == donor)].holdout.values
            ax.scatter([i] * len(points), points, s=6, color=color, alpha=0.55, zorder=2, lw=0)
    ax.axhline(1.0, ls="--", lw=1.0, color="0.15", zorder=1)
    ax.set_xticks(range(len(donors)))
    ax.set_xticklabels([f"donor {d}" for d in donors])
    ax.set_ylabel("held-out-donor NMSE")
    ax.set_ylim(0, 1.15)
    ax.set_title("Donor 11 breaks the ordering:\nn=4 donors cannot support a ranking", pad=6)
    ax.legend(fontsize=6, loc="center left")
    ax.text(0.99, 0.99, "points = 3 seeds", transform=ax.transAxes, ha="right", va="top",
            fontsize=6, color="0.35")

    for ax, letter in zip(axes, "ab"):
        panel_letter(ax, letter, dx=-0.20, dy=1.05)
    fig.tight_layout()
    path = out / "phase8_human_lodo.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------- tables

def table_condition_summary(run: Path, val: pd.DataFrame, out: Path) -> Path:
    """validation の層別 recovery と test の条件別 penalized NMSE を統合する。"""
    with (run / "phase5_multiseed" / "summary.json").open() as fh:
        p5 = json.load(fh)
    validation = (val.groupby("condition")
                  .agg(skeleton_recovery=("sym_skeleton", "mean"),
                       sym_exact=("sym_exact", "mean"),
                       sym_equiv=("sym_equiv", "mean"),
                       nmse_median=("nmse", "median"),
                       var_f1=("var_f1", "mean"),
                       n_problems=("sym_skeleton", "size"))
                  .reset_index())
    validation.insert(0, "split", "validation (phase4)")
    test = pd.DataFrame([
        dict(split="test (phase5)", condition=cond,
             penalized_nmse=stat["penalized_nmse"]["mean"],
             penalized_nmse_ci95=stat["penalized_nmse"]["ci95"],
             valid_rate=stat["valid_rate"]["mean"],
             sym_recovery=0.0, n_seeds=3)
        for cond, stat in p5["conditions"].items()])
    merged = pd.concat([validation, test], ignore_index=True, sort=False)
    path = out / "phase45_condition_summary.csv"
    merged.round(4).to_csv(path, index=False)
    return path


def table_skeleton_recovery(val: pd.DataFrame, test: pd.DataFrame, out: Path) -> Path:
    """骨格別 recovery（validation / test）。"""
    v = recovery_by_skeleton(val[val.condition == "all_params"]).reset_index()
    v.insert(0, "split", "validation")
    t = recovery_by_skeleton(test).reset_index()
    t.insert(0, "split", "test")
    merged = pd.concat([v, t], ignore_index=True)
    path = out / "phase45_skeleton_recovery.csv"
    merged.round(4).to_csv(path, index=False)
    return path


def table_human_folds(folds: pd.DataFrame, out: Path) -> Path:
    """donor別・方法別の in-donor / holdout NMSE。"""
    pivot = (folds.groupby(["method", "donor"])[["in_donor", "holdout"]]
             .agg(["mean", "std", "count"]))
    pivot.columns = ["_".join(c) for c in pivot.columns]
    path = out / "phase8_human_per_donor.csv"
    pivot.round(4).to_csv(path)
    return path


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2],
                        help="リポジトリのルート")
    parser.add_argument("--run-id", default="colab_reduced_20260729_03",
                        help="results/runs/<run-id> と graphs/<run-id> の識別子")
    parser.add_argument("--suite", default="diverse_gpu_n0.1",
                        help="data/synthetic/<suite> の合成データ suite 名")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    args = parser.parse_args()

    run = args.repo / "results" / "runs" / args.run_id
    if not run.is_dir():
        raise SystemExit(f"run directory not found: {run}")
    figures = args.repo / "graphs" / args.run_id / "figures"
    tables = args.repo / "graphs" / args.run_id / "tables"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(RC)

    suite_index = load_suite_index(args.repo, run, args.suite)
    val = load_validation_equations(run, args.seeds)
    test = load_test_equations(run, args.seeds)
    folds = load_human_folds(run, args.seeds)

    written = [
        fig_layer_contribution(run, args.seeds, figures),
        fig_recovery_and_equivalence(run, suite_index, val, test, figures),
        fig_baselines_and_transfer(run, figures),
        fig_human_lodo(run, folds, figures),
        table_condition_summary(run, val, tables),
        table_skeleton_recovery(val, test, tables),
        table_human_folds(folds, tables),
    ]
    for path in written:
        print(path.relative_to(args.repo))


if __name__ == "__main__":
    main()
