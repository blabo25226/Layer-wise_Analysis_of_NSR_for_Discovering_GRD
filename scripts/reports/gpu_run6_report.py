#!/usr/bin/env python
"""GPU_RUN6 analysis: statistics for H1-H9, tables, and figures.

Usage: python scripts/reports/gpu_run6_report.py --run-id <id>
Reads results/runs/<id>/ and writes graphs/<id>/{tables,figures}/ plus results/runs/<id>/summary.json.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402
from sklearn.linear_model import LogisticRegression, Ridge  # noqa: E402
from sklearn.metrics import balanced_accuracy_score, r2_score  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from gpu_run6.enzyme import FAMILIES_1D, POLY_1D, RATIONAL_1D  # noqa: E402

ENC = [f"encoder_{i}" for i in range(4)]
DEC = [f"decoder_{i}" for i in range(12)]
ALL = ENC + DEC
B = 2000
RNG = np.random.default_rng(20261118)


def boot_mean(x, b=B):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return float("nan"), float("nan"), float("nan")
    idx = RNG.integers(0, len(x), size=(b, len(x)))
    m = x[idx].mean(axis=1)
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def boot_diff(a, b_, b=B):
    a, b_ = np.asarray(a, float), np.asarray(b_, float)
    ia = RNG.integers(0, len(a), size=(b, len(a)))
    ib = RNG.integers(0, len(b_), size=(b, len(b_)))
    d = a[ia].mean(1) - b_[ib].mean(1)
    return float(a.mean() - b_.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def fmt(m, lo, hi, nd=2):
    return f"{m:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"


def load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


class Report:
    def __init__(self, run_id):
        self.rd = ROOT / "results/runs" / run_id
        self.gd = ROOT / "graphs" / run_id
        (self.gd / "tables").mkdir(parents=True, exist_ok=True)
        (self.gd / "figures").mkdir(parents=True, exist_ok=True)
        self.summary = {"run_id": run_id}
        self.layer_scores = {}

    def table(self, name, header, rows):
        lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
        lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
        (self.gd / "tables" / f"{name}.md").write_text("\n".join(lines) + "\n")
        return "\n".join(lines)

    # ------------------------------------------------------------------ behaviour
    def behavior(self):
        for arm in ("eval", "eval_noise"):
            path = self.rd / "behavior" / f"base_{arm}.jsonl"
            if not path.exists():
                continue
            recs = load_jsonl(path)
            by = defaultdict(list)
            for r in recs:
                by[r["family"]].append(r)
            rows, fam_sum = [], {}
            for fam in list(FAMILIES_1D) + ["MA_SC", "MA_S"]:
                v = by.get(fam, [])
                if not v:
                    continue
                cib = boot_mean([x["class_in_beam"] for x in v])
                sel = boot_mean([x["selected_class_match"] for x in v])
                rib = np.mean([x["rational_in_beam"] for x in v])
                r2 = np.nanmedian([x["recon_r2"] for x in v])
                g = np.nanmedian([x["gen_r2_min"] for x in v])
                top = Counter(x["selected_class"] for x in v).most_common(3)
                rows.append([fam, len(v), fmt(*cib), fmt(*sel), f"{rib:.2f}", f"{r2:.4f}", f"{g:.3f}",
                             ", ".join(f"{k}:{n}" for k, n in top)])
                fam_sum[fam] = {"n": len(v), "class_in_beam": cib, "selected_match": sel, "rational_in_beam": float(rib),
                                "recon_r2_median": float(r2), "gen_r2_min_median": float(g), "selected_top": top}
            self.table(f"behavior_{arm}", ["family", "n", "class_in_beam [95% CI]", "selected match [95% CI]",
                                           "any rational in beam", "recon R² median", "gen R² min median",
                                           "selected classes (top 3)"], rows)
            self.summary[f"behavior_{arm}"] = fam_sum
            rat = [x["class_in_beam"] for x in recs if x["family"] in RATIONAL_1D]
            pol = [x["class_in_beam"] for x in recs if x["family"] in POLY_1D]
            h1 = boot_diff(rat, pol)
            self.summary[f"H1_{arm}"] = {"rational_minus_poly": h1,
                                         "supported": bool(h1[2] < 0 and h1[0] <= -0.3)}
            mism = [x for x in recs if x["family"] in RATIONAL_1D and not x["selected_class_match"]]
            match = [x for x in recs if x["family"] in RATIONAL_1D and x["selected_class_match"]]
            self.summary[f"H2_{arm}"] = {
                "n_mismatch": len(mism),
                "recon_r2_median_mismatch": float(np.nanmedian([x["recon_r2"] for x in mism])) if mism else None,
                "gen_r2_min_median_mismatch": float(np.nanmedian([x["gen_r2_min"] for x in mism])) if mism else None,
                "gen_r2_min_median_match": float(np.nanmedian([x["gen_r2_min"] for x in match])) if match else None,
                "share_mismatch_recon_ge_099": float(np.mean([x["recon_r2"] >= 0.99 for x in mism])) if mism else None,
                "supported": bool(mism and np.nanmedian([x["recon_r2"] for x in mism]) >= 0.99)}
            mm = [x for x in recs if x["family"] == "MM_S"]
            mid = [x["class_in_beam"] for x in mm if 0.1 <= x["params"]["K"] <= 3]
            ext = [x["class_in_beam"] for x in mm if not (0.1 <= x["params"]["K"] <= 3)]
            if mid and ext:
                h3 = boot_diff(mid, ext)
                self.summary[f"H3_{arm}"] = {"mid_minus_extreme": h3, "n_mid": len(mid), "n_extreme": len(ext),
                                             "supported": bool(h3[1] > 0)}
            for fam in ("MA_SC", "MA_S"):
                if fam in fam_sum:
                    self.summary.setdefault(f"H4_{arm}", {})[fam] = fam_sum[fam]["class_in_beam"]
            if arm == "eval":
                self._fig_behavior(fam_sum, mm)

    def _fig_behavior(self, fam_sum, mm):
        fams = [f for f in list(FAMILIES_1D) + ["MA_S", "MA_SC"] if f in fam_sum]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        m = [fam_sum[f]["class_in_beam"][0] for f in fams]
        lo = [fam_sum[f]["class_in_beam"][0] - fam_sum[f]["class_in_beam"][1] for f in fams]
        hi = [fam_sum[f]["class_in_beam"][2] - fam_sum[f]["class_in_beam"][0] for f in fams]
        colors = ["#c0504d" if f in RATIONAL_1D or f == "MA_S" else ("#7f7f7f" if f == "MA_SC" else "#4f81bd") for f in fams]
        axes[0].bar(fams, m, yerr=[lo, hi], color=colors, capsize=3)
        axes[0].set_ylabel("true structural class in beam (50)")
        axes[0].set_title("(a) structure recovery by family (red = rational)")
        axes[0].set_ylim(0, 1.05)
        axes[0].tick_params(axis="x", rotation=30)
        ks = np.array([x["params"]["K"] for x in mm])
        y = np.array([x["class_in_beam"] for x in mm], dtype=float)
        bins = [0.03, 0.1, 0.3, 1, 3, 10, 30.01]
        centers, rates, ns = [], [], []
        for a, b in zip(bins[:-1], bins[1:]):
            sel = (ks >= a) & (ks < b)
            if sel.sum():
                centers.append(math.sqrt(a * b))
                rates.append(y[sel].mean())
                ns.append(int(sel.sum()))
        axes[1].semilogx(centers, rates, "o-", color="#c0504d")
        for c, r, n in zip(centers, rates, ns):
            axes[1].annotate(f"n={n}", (c, r), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
        axes[1].set_xlabel("K (Michaelis constant, units of S0)")
        axes[1].set_ylabel("MM_S class in beam")
        axes[1].set_title("(b) MM_S recovery vs saturation regime")
        axes[1].set_ylim(-0.05, 1.05)
        fig.tight_layout()
        fig.savefig(self.gd / "figures" / "fig1_behavior.png", dpi=150)
        plt.close(fig)

    # ------------------------------------------------------------------ lenses
    def lens(self):
        path = self.rd / "lens" / "lens_eval.json"
        if not path.exists():
            return
        L = json.loads(path.read_text())
        out = {}
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        for fam in ("MM_S", "MM_P", "SI", "HILL2", "MA_S"):
            rows = [r for r in L if r["family"] == fam]
            if not rows:
                continue
            pos = [r["words"].index("inv") for r in rows]
            lr = np.array([np.array(r["logit_rank"])[:, p] for r, p in zip(rows, pos)])
            tl = np.array([np.array(r["tuned_lens"])[:, p] for r, p in zip(rows, pos)])
            fin = np.array([r["final"][p] for r, p in zip(rows, pos)])
            out[fam] = {"logit_rank_median": np.median(lr, 0).tolist(), "tuned_logp_mean": tl.mean(0).tolist(),
                        "final_inv_logp_mean": float(fin.mean()),
                        "share_inv_final_rank1": float(np.mean(np.array(lr)[:, -1] == 1)),
                        "min_logit_rank_any_layer_median": float(np.median(lr.min(1)))}
            axes[0].plot(range(12), np.median(lr, 0), marker="o", label=fam)
            axes[1].plot(range(12), tl.mean(0), marker="o", label=fam)
        # tuned-lens rank needs ranks; approximate with log-prob relative to uniform
        axes[0].set_yscale("log")
        axes[0].set_title("(a) logit-lens rank of the true 'inv' token (median)")
        axes[0].set_xlabel("decoder layer")
        axes[1].axhline(-math.log(10293), color="k", ls=":", lw=1, label="uniform")
        axes[1].set_title("(b) tuned-lens log p('inv') (mean)")
        axes[1].set_xlabel("decoder layer")
        axes[0].legend(fontsize=8)
        axes[1].legend(fontsize=8)
        # category-wise tuned-lens log-prob gain per layer, rational vs polynomial targets
        cat = defaultdict(list)
        from gpu_run6.layers import token_category
        for r in L:
            grp = "rational" if r["rational"] else "polynomial"
            tl = np.array(r["tuned_lens"])
            for p, w in enumerate(r["words"]):
                c = token_category(w)
                if c in ("operator", "inv", "variable"):
                    cat[(grp, "structure")].append(tl[:, p])
                elif c == "constant":
                    cat[(grp, "constant")].append(tl[:, p])
        for (grp, c), v in sorted(cat.items()):
            axes[2].plot(range(12), np.mean(v, 0), marker=".", ls="-" if grp == "rational" else "--", label=f"{grp}/{c}")
        axes[2].set_title("(c) tuned-lens target log p by token type")
        axes[2].set_xlabel("decoder layer")
        axes[2].legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(self.gd / "figures" / "fig2_lens.png", dpi=150)
        plt.close(fig)
        self.summary["H6_lens"] = out
        # layer score for H9: tuned-lens target log-prob gain per layer on rational targets
        rat = [np.array(r["tuned_lens"]).mean(1) for r in L if r["rational"]]
        m = np.mean(rat, 0)
        gain = np.diff(np.concatenate([[m[0]], m]))
        self.layer_scores["tuned_lens_gain"] = dict(zip(DEC, gain.tolist()))
        # block skip
        sk = [r for r in L if "skip" in r]
        if sk:
            from gpu_run6.layers import token_category
            drop_r, drop_p = defaultdict(list), defaultdict(list)
            sdrop_r, sdrop_p = defaultdict(list), defaultdict(list)
            inv_drop = defaultdict(list)
            for r in sk:
                base = np.sum(r["final"])
                smask = np.array([token_category(w) in ("operator", "inv", "variable") for w in r["words"]])
                sbase = np.sum(np.array(r["final"])[smask])
                for layer, lp in r["skip"].items():
                    d = base - np.sum(lp)
                    (drop_r if r["rational"] else drop_p)[layer].append(d)
                    (sdrop_r if r["rational"] else sdrop_p)[layer].append(sbase - np.sum(np.array(lp)[smask]))
                    if "inv" in r["words"]:
                        p = r["words"].index("inv")
                        inv_drop[layer].append(r["final"][p] - lp[p])
            layers = DEC[1:]
            rows = [[l_, f"{np.mean(drop_r[l_]):.2f}", f"{np.mean(drop_p[l_]):.2f}", f"{np.mean(sdrop_r[l_]):.2f}",
                     f"{np.mean(sdrop_p[l_]):.2f}", f"{np.mean(inv_drop[l_]):.2f}"] for l_ in layers]
            self.table("block_skip", ["skipped block", "drop, all tokens (rational)", "drop, all tokens (polynomial)",
                                      "drop, structure tokens (rational)", "drop, structure tokens (polynomial)",
                                      "drop of log p('inv')"], rows)
            self.summary["block_skip"] = {l_: {"rational": float(np.mean(drop_r[l_])), "poly": float(np.mean(drop_p[l_])),
                                               "struct_rational": float(np.mean(sdrop_r[l_])),
                                               "struct_poly": float(np.mean(sdrop_p[l_])),
                                               "inv": float(np.mean(inv_drop[l_]))} for l_ in layers}
            self.layer_scores["block_skip_drop"] = {l_: float(np.mean(drop_r[l_])) for l_ in layers}

    # ------------------------------------------------------------------ probes
    def probes(self):
        path = self.rd / "probe_features.npz"
        if not path.exists():
            return
        Z = np.load(path)
        meta = json.loads((self.rd / "probe_meta.json").read_text())
        ytr = np.array([m["rational"] for m in meta["probe_train"]], dtype=int)
        yte = np.array([m["rational"] for m in meta["eval"]], dtype=int)
        ftr = [m["family"] for m in meta["probe_train"]]
        fte = [m["family"] for m in meta["eval"]]

        def fit_eval(Xtr, ytr_, Xte, yte_):
            clf = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=5000))
            clf.fit(Xtr, ytr_)
            return balanced_accuracy_score(yte_, clf.predict(Xte))

        # Hewitt-Liang style control task: random 4-vs-3 partitions of the 7 families
        fams = list(FAMILIES_1D)
        true_part = frozenset(RATIONAL_1D)
        rng = np.random.default_rng(7)
        parts = []
        while len(parts) < 10:
            p = frozenset(rng.choice(fams, size=4, replace=False).tolist())
            if p != true_part and p not in parts:
                parts.append(p)
        rows, res = [], {}
        base_acc = fit_eval(Z["probe_train__base"], ytr, Z["eval__base"], yte)
        for layer in ALL:
            Xtr, Xte = Z[f"probe_train__{layer}"], Z[f"eval__{layer}"]
            acc = fit_eval(Xtr, ytr, Xte, yte)
            perm = fit_eval(Xtr, rng.permutation(ytr), Xte, yte)
            ctl = np.mean([fit_eval(Xtr, np.array([f in p for f in ftr], int), Xte, np.array([f in p for f in fte], int))
                           for p in parts])
            res[layer] = {"acc": acc, "permuted": perm, "control_task": float(ctl), "selectivity": float(acc - ctl)}
            rows.append([layer, f"{acc:.3f}", f"{perm:.3f}", f"{ctl:.3f}", f"{acc - ctl:+.3f}"])
        rows.append(["input statistics (baseline)", f"{base_acc:.3f}", "", "", ""])
        self.table("probe_rational", ["layer", "balanced acc", "label-permuted", "control task (random family split)",
                                      "selectivity"], rows)
        # log K regression on MM_S
        def kidx(split):
            return [i for i, m in enumerate(meta[split]) if m["family"] == "MM_S"]
        itr, ite = kidx("probe_train"), kidx("eval")
        ktr = np.log10([meta["probe_train"][i]["K"] for i in itr])
        kte = np.log10([meta["eval"][i]["K"] for i in ite])
        kres = {}
        for layer in ALL + ["base"]:
            key = layer
            Xtr, Xte = Z[f"probe_train__{key}"][itr], Z[f"eval__{key}"][ite]
            reg = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(Xtr, ktr)
            kres[layer] = float(r2_score(kte, reg.predict(Xte)))
        self.table("probe_logK", ["layer", "R² (log10 K, MM_S)"], [[k, f"{v:.3f}"] for k, v in kres.items()])
        dec_best = max(DEC, key=lambda l_: res[l_]["acc"])
        self.summary["H5_probe"] = {"per_layer": res, "input_baseline": base_acc, "logK_r2": kres,
                                    "best_decoder_layer": dec_best,
                                    "supported": bool(any(res[l_]["acc"] - res[l_]["permuted"] >= 0.2
                                                          and res[l_]["acc"] >= base_acc - 0.05 for l_ in DEC))}
        self.layer_scores["probe_acc"] = {l_: res[l_]["acc"] for l_ in ALL}
        fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
        ax[0].plot(range(16), [res[l_]["acc"] for l_ in ALL], "o-", label="rational vs polynomial")
        ax[0].plot(range(16), [res[l_]["control_task"] for l_ in ALL], "s--", label="control task (random family split)")
        ax[0].plot(range(16), [res[l_]["permuted"] for l_ in ALL], "x:", label="label-permuted")
        ax[0].axhline(base_acc, color="k", ls=":", lw=1, label="input statistics")
        ax[0].axvline(3.5, color="grey", lw=0.5)
        ax[0].set_xticks(range(16), [l_.replace("encoder_", "E").replace("decoder_", "D") for l_ in ALL], fontsize=7)
        ax[0].set_ylabel("balanced accuracy")
        ax[0].set_title("(a) probe: is the law rational?")
        ax[0].legend(fontsize=7)
        ax[1].plot(range(16), [kres[l_] for l_ in ALL], "o-")
        ax[1].axhline(kres["base"], color="k", ls=":", lw=1, label="input statistics")
        ax[1].set_xticks(range(16), [l_.replace("encoder_", "E").replace("decoder_", "D") for l_ in ALL], fontsize=7)
        ax[1].set_ylabel("R²")
        ax[1].set_title("(b) probe: log10 K of MM_S")
        ax[1].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(self.gd / "figures" / "fig3_probe.png", dpi=150)
        plt.close(fig)

    # ------------------------------------------------------------------ patching
    def patching(self):
        path = self.rd / "patch" / "patch.json"
        if not path.exists():
            return
        P = json.loads(path.read_text())
        out = {}
        keys = [k for k in ("to_rational", "to_rational_random", "to_poly") if any(k in p for p in P)]
        for key in keys:
            gaps = np.array([np.sum(p[key]["clean"]) - np.sum(p[key]["corrupt"]) for p in P if key in p])
            sel = [p for p in P if key in p and np.sum(p[key]["clean"]) - np.sum(p[key]["corrupt"]) > 1.0]
            rest = {}
            for layer in ALL:
                vals = [(np.sum(p[key]["patched"][layer]) - np.sum(p[key]["corrupt"])) /
                        (np.sum(p[key]["clean"]) - np.sum(p[key]["corrupt"])) for p in sel]
                rest[layer] = float(np.median(vals)) if vals else float("nan")
            selfp = max([p[key]["self_patch_max_abs_diff"] for p in P if key in p] or [float("nan")])
            out[key] = {"gap_mean": boot_mean(gaps), "share_gap_gt_1": float(np.mean(gaps > 1)), "n_pairs": len(gaps),
                        "restoration_median": rest, "self_patch_max_abs_diff": selfp}
        rmse = [p["pair_rmse"] for p in P]
        rrm = [p.get("random_pair_rmse", float("nan")) for p in P]
        out["pair_rmse_median"] = {"matched": float(np.median(rmse)), "random": float(np.nanmedian(rrm))}
        self.summary["H7_patch"] = out
        rows = [[k, fmt(*out[k]["gap_mean"]), f"{out[k]['share_gap_gt_1']:.2f}", out[k]["n_pairs"],
                 f"{out[k]['self_patch_max_abs_diff']:.1e}"] for k in keys]
        self.table("patch_gap", ["direction", "clean − corrupt log p (mean [95% CI])", "share gap > 1 nat", "pairs",
                                 "self-patch max |Δ|"], rows)
        self.table("patch_restoration", ["layer"] + keys,
                   [[l_] + [f"{out[k]['restoration_median'][l_]:.2f}" for k in keys] for l_ in ALL])
        self.layer_scores["patch_restoration"] = out[keys[1] if len(keys) > 2 else keys[0]]["restoration_median"]
        fig, ax = plt.subplots(figsize=(7, 3.8))
        for k, ls in zip(keys, ("-", "--", ":")):
            ax.plot(range(16), [out[k]["restoration_median"][l_] for l_ in ALL], marker="o", ls=ls, label=k)
        ax.axvline(3.5, color="grey", lw=0.5)
        ax.set_xticks(range(16), [l_.replace("encoder_", "E").replace("decoder_", "D") for l_ in ALL], fontsize=7)
        ax.set_ylabel("restored fraction (median, pairs with gap > 1 nat)")
        ax.set_title("activation patching (denoising)")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(self.gd / "figures" / "fig4_patching.png", dpi=150)
        plt.close(fig)

    # ------------------------------------------------------------------ adaptation
    def adapt(self):
        path = self.rd / "adapt" / "conditions.jsonl"
        if not path.exists():
            return
        C = {c["condition"]: c for c in load_jsonl(path)}
        if "base" not in C:
            return
        base = C["base"]
        train_f = ["MM_S", "SI", "HILL2"]

        def rat_ce(c):
            return float(np.mean([c["tf"]["ce"][f] for f in train_f if f in c["tf"]["ce"]]))

        fams = ["MM_S", "SI", "HILL2", "MM_P", "MA_S", "LIN", "QUAD", "QUAD2"]
        rows = []
        for name in ["base", "full"] + [k for k in C if k.startswith("lr")]:
            if name not in C:
                continue
            c = C[name]
            rows.append([name, f"{rat_ce(c):.3f}", f"{c['generic_ce']:.3f}"] +
                        [f"{c['beam'].get(f, {}).get('class_in_beam', float('nan')):.2f}" for f in fams])
        self.table("adapt_main", ["condition", "TF CE (MM_S/SI/HILL2)", "generic CE"] + [f"{f} in-beam" for f in fams], rows)
        # H8 from the full-FT behaviour records
        h8 = {}
        if (self.rd / "adapt" / "beh_full.jsonl").exists():
            bb = load_jsonl(self.rd / "adapt" / "beh_base.jsonl")
            bf = load_jsonl(self.rd / "adapt" / "beh_full.jsonl")
            for group, fl in (("train_families", train_f), ("heldout_families", ["MM_P", "MA_S"]),
                              ("polynomial_controls", ["LIN", "QUAD", "QUAD2"])):
                a = [x["class_in_beam"] for x in bf if x["family"] in fl]
                b_ = [x["class_in_beam"] for x in bb if x["family"] in fl]
                h8[group] = {"full_minus_base": boot_diff(a, b_), "full": float(np.mean(a)), "base": float(np.mean(b_))}
            h8["generic_ce"] = {"base": base["generic_ce"], "full": C["full"]["generic_ce"]}
            h8["supported_a"] = bool(h8["train_families"]["full_minus_base"][1] > 0)
        self.summary["H8_adapt"] = h8
        single, into, outof, wc = {}, {}, {}, {}
        for l_ in ALL:
            if f"single_{l_}" in C:
                single[l_] = rat_ce(base) - rat_ce(C[f"single_{l_}"])
            if f"swap_into_base_{l_}" in C:
                into[l_] = rat_ce(base) - rat_ce(C[f"swap_into_base_{l_}"])
            if f"swap_out_of_full_{l_}" in C and "full" in C:
                outof[l_] = rat_ce(C[f"swap_out_of_full_{l_}"]) - rat_ce(C["full"])
        if "full" in C and "weight_change" in C["full"]:
            wc = C["full"]["weight_change"]
        self.layer_scores.update({"single_ft_ce_gain": single, "swap_into_base_ce_gain": into,
                                  "swap_out_of_full_ce_loss": outof, "weight_change": wc})
        beam_single = {l_: np.mean([C[f"single_{l_}"]["beam"].get(f, {}).get("class_in_beam", np.nan) for f in train_f])
                       for l_ in ALL if f"single_{l_}" in C}
        rows = [[l_, f"{single.get(l_, np.nan):.3f}", f"{beam_single.get(l_, np.nan):.2f}", f"{into.get(l_, np.nan):.3f}",
                 f"{outof.get(l_, np.nan):.3f}", f"{wc.get(l_, np.nan):.4f}"] for l_ in ALL]
        self.table("adapt_layers", ["block", "single-block FT: CE gain", "single-block FT: in-beam (train fam.)",
                                    "swap into base: CE gain", "swap out of full: CE loss", "relative weight change"], rows)
        # exploratory: does adaptation add input-dependent selection, or swap the output bias?
        sel_rows, sel = [], {}
        for f_ in sorted((self.rd / "adapt").glob("beh_*.jsonl")):
            cond = f_.stem[len("beh_"):]
            recs = load_jsonl(f_)
            rat = [bool(x.get("selected_class_match")) for x in recs if x["rational"]]
            pol = [bool(x.get("selected_class_match")) for x in recs if not x["rational"]]
            if rat and pol:
                sel[cond] = {"rational_selected_match": float(np.mean(rat)), "polynomial_selected_match": float(np.mean(pol)),
                             "n_rational": len(rat), "n_polynomial": len(pol)}
        order = ["base", "full"] + [c for c in sel if c.startswith("single_")] + [c for c in sel if c.startswith("lr")]
        for c in order:
            if c in sel:
                v = sel[c]
                sel_rows.append([c, f"{v['rational_selected_match']:.2f}", f"{v['polynomial_selected_match']:.2f}",
                                 f"{v['rational_selected_match'] + v['polynomial_selected_match'] - 1:+.2f}",
                                 f"{v['n_rational']}/{v['n_polynomial']}"])
        self.table("adapt_selection", ["condition", "rational: selected class correct", "polynomial: selected class correct",
                                       "discrimination (sum − 1)", "n (rat/poly)"], sel_rows)
        self.summary["adapt_selection"] = sel
        self.summary["adapt_layers"] = {"single": single, "single_beam": beam_single, "into": into, "outof": outof,
                                        "weight_change": wc, "full_ce": rat_ce(C["full"]) if "full" in C else None,
                                        "base_ce": rat_ce(base)}
        fig, ax = plt.subplots(figsize=(8, 3.8))
        xs = range(16)
        for d, lab in ((single, "single-block FT"), (into, "swap FT block into base"), (outof, "remove block from full FT")):
            ax.plot(xs, [d.get(l_, np.nan) for l_ in ALL], marker="o", label=lab)
        if "full" in C:
            ax.axhline(rat_ce(base) - rat_ce(C["full"]), color="k", ls=":", lw=1, label="full FT gain")
        ax.axvline(3.5, color="grey", lw=0.5)
        ax.set_xticks(range(16), [l_.replace("encoder_", "E").replace("decoder_", "D") for l_ in ALL], fontsize=7)
        ax.set_ylabel("Δ teacher-forced CE (MM_S/SI/HILL2)")
        ax.set_title("adaptation localisation")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(self.gd / "figures" / "fig5_adapt.png", dpi=150)
        plt.close(fig)

    # ------------------------------------------------------------------ method agreement
    def agreement(self):
        names = [k for k, v in self.layer_scores.items() if v]
        mat = np.full((len(names), len(names)), np.nan)
        pairs = []
        for i, a in enumerate(names):
            for j, b in enumerate(names):
                common = [l_ for l_ in ALL if l_ in self.layer_scores[a] and l_ in self.layer_scores[b]
                          and np.isfinite(self.layer_scores[a][l_]) and np.isfinite(self.layer_scores[b][l_])]
                if len(common) >= 5:
                    rho = spearmanr([self.layer_scores[a][l_] for l_ in common],
                                    [self.layer_scores[b][l_] for l_ in common]).correlation
                    mat[i, j] = rho
                    if i < j:
                        pairs.append({"a": a, "b": b, "rho": float(rho), "n_layers": len(common)})
        small = [p for p in pairs if abs(p["rho"]) < 0.5]
        # preregistered set (plan.md H9) excludes the post-hoc swap_out_of_full score
        prereg = [p for p in pairs if "swap_out_of_full_ce_loss" not in (p["a"], p["b"])]
        prereg_small = [p for p in prereg if abs(p["rho"]) < 0.5]

        def decoder_only_rho(a, b):
            ks = [l_ for l_ in DEC if l_ in self.layer_scores[a] and l_ in self.layer_scores[b]
                  and np.isfinite(self.layer_scores[a][l_]) and np.isfinite(self.layer_scores[b][l_])]
            return float(spearmanr([self.layer_scores[a][k] for k in ks], [self.layer_scores[b][k] for k in ks]).correlation), len(ks)

        dec_pairs = []
        for p in prereg:
            r, n = decoder_only_rho(p["a"], p["b"])
            dec_pairs.append({"a": p["a"], "b": p["b"], "rho": r, "n_layers": n})
        self.summary["H9_agreement"] = {
            "pairs": pairs, "share_abs_rho_lt_0.5": len(small) / max(len(pairs), 1),
            "prereg_pairs": len(prereg), "prereg_share_abs_rho_lt_0.5": len(prereg_small) / max(len(prereg), 1),
            "supported": bool(len(prereg_small) > len(prereg) / 2),
            "sensitivity_decoder_only": {"pairs": dec_pairs,
                                         "share_abs_rho_lt_0.5": float(np.mean([abs(p["rho"]) < 0.5 for p in dec_pairs]))},
            "layer_scores": self.layer_scores}
        self.table("method_agreement_decoder_only", ["method A", "method B", "Spearman ρ (decoder only)", "layers"],
                   [[p["a"], p["b"], f"{p['rho']:+.2f}", p["n_layers"]] for p in dec_pairs])
        self.table("layer_scores", ["block"] + names,
                   [[l_] + [f"{self.layer_scores[n].get(l_, float('nan')):.3f}" for n in names] for l_ in ALL])
        self.table("method_agreement", ["method A", "method B", "Spearman ρ", "layers"],
                   [[p["a"], p["b"], f"{p['rho']:+.2f}", p["n_layers"]] for p in pairs])
        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(mat, vmin=-1, vmax=1, cmap="RdBu_r")
        ax.set_xticks(range(len(names)), names, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(names)), names, fontsize=8)
        for i in range(len(names)):
            for j in range(len(names)):
                if np.isfinite(mat[i, j]):
                    ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im)
        ax.set_title("per-layer importance: Spearman ρ between methods")
        fig.tight_layout()
        fig.savefig(self.gd / "figures" / "fig6_method_agreement.png", dpi=150)
        plt.close(fig)

    def run(self):
        for step in (self.behavior, self.lens, self.probes, self.patching, self.adapt, self.agreement):
            step()
        text = json.dumps(self.summary, indent=1, default=lambda o: o if not isinstance(o, np.generic) else o.item())
        (self.rd / "summary.json").write_text(text)
        (self.gd / "summary.json").write_text(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    Report(ap.parse_args().run_id).run()
