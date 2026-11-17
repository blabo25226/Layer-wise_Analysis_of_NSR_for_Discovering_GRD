#!/usr/bin/env python
"""GPU_RUN6 runner: enzyme-kinetics effective laws and layer-wise analysis of ODEFormer.

Usage: python scripts/phases/gpu_run6.py <phase> --run-id <id> [--smoke]
Phases: data, behavior, tunedlens, lens, probe, patch, adapt, report (see experiments/GPU_RUN6/README.md).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.architecture import unwrap_model  # noqa: E402
from gpu_run4_runtime import install_odeformer_path, load_odeformer_model, make_symbolic_regressor  # noqa: E402
from gpu_run6 import enzyme  # noqa: E402

CONFIG = yaml.safe_load((ROOT / "configs/gpu_run6/base.yaml").read_text())


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_dir(run_id: str) -> Path:
    path = ROOT / "results/runs" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=_json_default))


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, frozenset):
        return sorted(o)
    raise TypeError(type(o))


def read_json(path: Path):
    return json.loads(path.read_text())


def load_model(device: str = "cuda"):
    install_odeformer_path()
    ckpt = ROOT / CONFIG["odeformer_checkpoint"]
    digest = hashlib.sha256(ckpt.read_bytes()).hexdigest()
    if digest != CONFIG["odeformer_checkpoint_sha256"]:
        raise RuntimeError(f"checkpoint sha mismatch {digest}")
    wrapped = unwrap_model(load_odeformer_model(ckpt, device=device))
    wrapped.eval()
    return wrapped


def make_regressor(wrapped):
    g = CONFIG["generation"]
    return make_symbolic_regressor(wrapped, rescale=bool(g["rescale"]), beam_size=int(g["beam_size"]),
                                   beam_temperature=float(g["beam_temperature"]), beam_type=str(g["beam_type"]))


def provenance(rd: Path, phase: str, extra: dict | None = None) -> None:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src/gpu_run6", "scripts/phases/gpu_run6.py",
                            "configs/gpu_run6"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    write_json(rd / f"provenance_{phase}.json", {
        "phase": phase, "commit": commit, "code_dirty": bool(dirty), "python": platform.python_version(),
        "torch": torch.__version__, "cuda": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "config": CONFIG, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **(extra or {}),
    })


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

def _set(families, seed, n, sigma=0.0):
    return [enzyme.make_problem(f, seed, i, noise_sigma=sigma) for f in families for i in range(n)]


def generic_samples(wrapped, n: int, seed: int) -> list[dict]:
    from gpu_run4.corpus import generate_one
    env = wrapped.env
    env.rng = np.random.RandomState(seed)
    np.random.seed(seed)
    out, attempts = [], 0
    while len(out) < n and attempts < n * 30:
        attempts += 1
        row = generate_one(env, train=True)
        if row is None or not row["valid"] or not row.get("tree_encoded"):
            continue
        out.append({"problem_id": f"generic_s{seed}_{len(out):04d}", "times": row["times"].tolist(),
                    "trajectory": row["trajectory"].tolist(), "tree_encoded": list(row["tree_encoded"]),
                    "infix": row["infix"], "dimension": row["dimension"]})
    return out


def phase_data(args):
    rd = run_dir(args.run_id)
    s, z = CONFIG["seeds"], CONFIG["sizes"]
    k = 4 if args.smoke else 1
    fams_eval = list(enzyme.FAMILIES_1D) + ["MA_SC", "MA_S"]
    sets = {
        "eval": _set(fams_eval, s["evaluation"], z["eval_per_family"] // k),
        "eval_noise": _set(fams_eval, s["evaluation"], z["noise_eval_per_family"] // k, z["noise_sigma"]),
        "probe_train": _set(enzyme.FAMILIES_1D, s["probe_train"], z["probe_train_per_family"] // k),
        "ft_train": _set(CONFIG["finetune"]["train_families"], s["finetune_train"], z["finetune_train_per_family"] // k),
        "ft_val": _set(CONFIG["finetune"]["train_families"], s["finetune_validation"], 20 // k),
        "patch_pool": _set(["QUAD"], s["patch_pool"], z["patch_pool_quad"] // k),
    }
    # leakage audit: no identical trajectories or prefixes across sets
    seen = {}
    for name, rows in sets.items():
        for r in rows:
            if r["checksum"] in seen and seen[r["checksum"]] != name:
                raise RuntimeError(f"leakage {name} vs {seen[r['checksum']]}")
            seen[r["checksum"]] = name
    wrapped = load_model()
    sets["generic_lens"] = generic_samples(wrapped, z["tuned_lens_samples"] // k, s["tuned_lens_generator"])
    sets["generic_heldout"] = generic_samples(wrapped, z["generic_heldout"] // k, s["generic_heldout"])
    for name, rows in sets.items():
        write_json(rd / "data" / f"{name}.json", rows)
        log(f"{name}: {len(rows)}")
    provenance(rd, "data", {"counts": {k_: len(v) for k_, v in sets.items()}})


# ---------------------------------------------------------------------------
# behaviour
# ---------------------------------------------------------------------------

def run_behavior(wrapped, rows, out_path: Path, seed_offset: int = 0) -> list[dict]:
    from gpu_run6.behavior import evaluate_problem
    reg = make_regressor(wrapped)
    done = {}
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            rec = json.loads(line)
            done[rec["problem_id"]] = rec
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as fh:
        for i, row in enumerate(rows):
            if row["problem_id"] in done:
                continue
            torch.manual_seed(seed_offset + i)
            rec = evaluate_problem(reg, row, generation_seed=seed_offset + i)
            fh.write(json.dumps(rec, default=_json_default) + "\n")
            fh.flush()
            done[row["problem_id"]] = rec
            if i % 50 == 0:
                log(f"{out_path.name}: {i}/{len(rows)}")
    return [done[r["problem_id"]] for r in rows]


def phase_behavior(args):
    rd = run_dir(args.run_id)
    wrapped = load_model()
    for name in ("eval", "eval_noise"):
        rows = read_json(rd / "data" / f"{name}.json")
        run_behavior(wrapped, rows, rd / "behavior" / f"base_{name}.jsonl", seed_offset=CONFIG["seeds"]["evaluation"] * 1000)
    provenance(rd, "behavior")


# ---------------------------------------------------------------------------
# lenses
# ---------------------------------------------------------------------------

def _np(row):
    return np.asarray(row["times"], dtype=float), np.asarray(row["trajectory"], dtype=float)


def phase_tunedlens(args):
    from gpu_run6.layers import train_tuned_lens
    rd = run_dir(args.run_id)
    wrapped = load_model()
    for p in wrapped.parameters():
        p.requires_grad = False
    samples = read_json(rd / "data" / "generic_lens.json")
    for s_ in samples:
        s_["times"], s_["trajectory"] = _np(s_)
    lens, hist = train_tuned_lens(wrapped, samples, epochs=CONFIG["sizes"]["tuned_lens_epochs"], lr=1e-3,
                                  seed=CONFIG["seeds"]["tuned_lens_generator"], log=log)
    torch.save(lens.state_dict(), rd / "tuned_lens.pt")
    write_json(rd / "tuned_lens_history.json", hist)
    provenance(rd, "tunedlens")


def _tuned(wrapped, rd):
    from gpu_run6.layers import N_DEC, TunedLens
    lens = TunedLens(wrapped.decoder.proj.in_features, N_DEC).to(next(wrapped.parameters()).device)
    lens.load_state_dict(torch.load(rd / "tuned_lens.pt"))
    lens.eval()
    return lens


def phase_lens(args):
    from gpu_run6.layers import block_skip_logprobs, encode_tokens, lens_logprobs
    rd = run_dir(args.run_id)
    wrapped = load_model()
    lens = _tuned(wrapped, rd)
    rows = [r for r in read_json(rd / "data" / "eval.json") if r["family"] != "MA_SC"]
    out = []
    for i, row in enumerate(rows):
        t, y = _np(row)
        tokens = encode_tokens(wrapped, row["true_prefix"])
        res = lens_logprobs(wrapped, t, y, tokens, tuned=lens)
        rec = {"problem_id": row["problem_id"], "family": row["family"], "rational": row["rational"],
               "K": row["params"].get("K"), "words": res["words"], "final": res["final"],
               "logit_lens": res["logit_lens"], "tuned_lens": res["tuned_lens"], "logit_rank": res["logit_rank"]}
        if row["index"] < 20:  # block-skip intervention on a fixed subset
            rec["skip"] = block_skip_logprobs(wrapped, t, y, tokens)
        out.append(rec)
        if i % 100 == 0:
            log(f"lens {i}/{len(rows)}")
    write_json(rd / "lens" / "lens_eval.json", out)
    provenance(rd, "lens")


# ---------------------------------------------------------------------------
# probes
# ---------------------------------------------------------------------------

def phase_probe(args):
    from gpu_run6.layers import ALL_LAYERS, encode_tokens, input_baseline_features, probe_features
    rd = run_dir(args.run_id)
    wrapped = load_model()
    feats = {}
    for name in ("probe_train", "eval"):
        rows = [r for r in read_json(rd / "data" / f"{name}.json") if r["family"] in enzyme.FAMILIES_1D]
        X = {layer: [] for layer in ALL_LAYERS}
        base, meta = [], []
        for row in rows:
            t, y = _np(row)
            f = probe_features(wrapped, t, y, encode_tokens(wrapped, row["true_prefix"]))
            for layer in ALL_LAYERS:
                X[layer].append(f[layer])
            base.append(input_baseline_features(t, y))
            meta.append({"problem_id": row["problem_id"], "family": row["family"], "rational": row["rational"],
                         "K": row["params"].get("K")})
        feats[name] = {"X": {k: np.asarray(v) for k, v in X.items()}, "base": np.asarray(base), "meta": meta}
        log(f"probe features {name}: {len(rows)}")
    np.savez_compressed(rd / "probe_features.npz",
                        **{f"{s}__{k}": v for s in feats for k, v in feats[s]["X"].items()},
                        **{f"{s}__base": feats[s]["base"] for s in feats})
    write_json(rd / "probe_meta.json", {s: feats[s]["meta"] for s in feats})
    provenance(rd, "probe")


# ---------------------------------------------------------------------------
# patching
# ---------------------------------------------------------------------------

def phase_patch(args):
    from gpu_run6.layers import encode_tokens, patching_curve
    rd = run_dir(args.run_id)
    wrapped = load_model()
    eval_rows = read_json(rd / "data" / "eval.json")
    pool = read_json(rd / "data" / "patch_pool.json")
    pool_traj = np.asarray([np.asarray(p["trajectory"])[:, 0] for p in pool])
    n = CONFIG["sizes"]["patch_pairs"] // (4 if args.smoke else 1)
    out = []
    rng = np.random.default_rng(CONFIG["seeds"]["patch_pool"])
    for fam in ("MM_S", "SI", "HILL2"):
        rows = [r for r in eval_rows if r["family"] == fam][:n]
        for row in rows:
            x = np.asarray(row["trajectory"])[:, 0]
            j = int(np.argmin(((pool_traj - x[None]) ** 2).mean(axis=1)))
            partner = pool[j]
            # rational clean -> polynomial corrupt, scored on the rational target
            res_r = patching_curve(wrapped, row, partner, encode_tokens(wrapped, row["true_prefix"]))
            # polynomial clean -> rational corrupt, scored on the polynomial target (reverse direction)
            res_p = patching_curve(wrapped, partner, row, encode_tokens(wrapped, partner["true_prefix"]))
            # unmatched control partner: a pool trajectory chosen at random (fixed RNG)
            k = int(rng.integers(0, len(pool)))
            res_u = patching_curve(wrapped, row, pool[k], encode_tokens(wrapped, row["true_prefix"]))
            out.append({"problem_id": row["problem_id"], "family": fam, "partner": partner["problem_id"],
                        "pair_rmse": float(np.sqrt(((pool_traj[j] - x) ** 2).mean())),
                        "random_partner": pool[k]["problem_id"],
                        "random_pair_rmse": float(np.sqrt(((pool_traj[k] - x) ** 2).mean())),
                        "to_rational": res_r, "to_poly": res_p, "to_rational_random": res_u})
        log(f"patch {fam} done")
    write_json(rd / "patch" / "patch.json", out)
    provenance(rd, "patch")


# ---------------------------------------------------------------------------
# adaptation
# ---------------------------------------------------------------------------

def _prep_records(wrapped, rows):
    from gpu_run6.layers import encode_tokens
    for r in rows:
        r["times_np"], r["trajectory_np"] = _np(r)
        r["tokens"] = r.get("tree_encoded") or encode_tokens(wrapped, r["true_prefix"])
    return rows


@torch.no_grad()
def tf_metrics(wrapped, rows) -> dict:
    """Teacher-forced mean CE per family and mean log p of the first 'inv' token on rational targets."""
    from gpu_run6.layers import forward_teacher
    per_fam: dict[str, list] = {}
    inv_lp: dict[str, list] = {}
    for r in rows:
        res = forward_teacher(wrapped, r["times_np"], r["trajectory_np"], r["tokens"])
        fam = r.get("family", "generic")
        per_fam.setdefault(fam, []).append(float(-res["target_logp"].mean()))
        if "inv" in res["target_words"]:
            inv_lp.setdefault(fam, []).append(float(res["target_logp"][res["target_words"].index("inv")]))
    return {"ce": {f: float(np.mean(v)) for f, v in per_fam.items()},
            "inv_logp": {f: float(np.mean(v)) for f, v in inv_lp.items()}}


def phase_adapt(args):
    from gpu_run6.adapt import block_state, clone, finetune, load_block_state, relative_weight_change
    from gpu_run6.layers import ALL_LAYERS
    rd = run_dir(args.run_id)
    out_dir = rd / "adapt"
    out_dir.mkdir(exist_ok=True)
    base = load_model()
    ft = CONFIG["finetune"]
    smoke = args.smoke
    train = _prep_records(base, read_json(rd / "data" / "ft_train.json"))
    eval_all = read_json(rd / "data" / "eval.json")
    n_eval = CONFIG["sizes"]["finetune_eval_per_family"] // (3 if smoke else 1)
    fams = list(ft["train_families"]) + list(ft["heldout_families"]) + ["LIN", "QUAD", "QUAD2"]
    eval_rows = _prep_records(base, [r for r in eval_all if r["family"] in fams and r["index"] < n_eval])
    # small beam panel for every condition; full beam panel for base and full FT
    panel = [r for r in eval_rows if r["index"] < (4 if smoke else 12)]
    generic = _prep_records(base, read_json(rd / "data" / "generic_heldout.json")[: (20 if smoke else 100)])
    steps = 20 if smoke else int(ft["steps"])
    layers = ["encoder_0", "decoder_11"] if smoke else list(ALL_LAYERS)

    results_path = out_dir / "conditions.jsonl"
    done = set()
    if results_path.exists():
        done = {json.loads(l)["condition"] for l in results_path.read_text().splitlines()}

    def evaluate(model, name, beam_rows, extra):
        if name in done:
            return
        tf = tf_metrics(model, eval_rows)
        gen = tf_metrics(model, generic)["ce"].get("generic")
        beh = run_behavior(model, beam_rows, out_dir / f"beh_{name}.jsonl", seed_offset=CONFIG["seeds"]["evaluation"] * 1000)
        summary = {}
        for fam in fams:
            recs = [b for b in beh if b["family"] == fam]
            if recs:
                summary[fam] = {"n": len(recs), "class_in_beam": float(np.mean([b["class_in_beam"] for b in recs])),
                                "selected_match": float(np.mean([b["selected_class_match"] for b in recs])),
                                "rational_selected": float(np.mean([b["selected_class"].startswith("R[") for b in recs])),
                                "recon_r2_median": float(np.nanmedian([b["recon_r2"] for b in recs]))}
        rec = {"condition": name, "tf": tf, "generic_ce": gen, "beam": summary, **extra}
        with results_path.open("a") as fh:
            fh.write(json.dumps(rec, default=_json_default) + "\n")
        done.add(name)
        log(f"adapt {name}: generic_ce={gen:.3f} " + " ".join(f"{f}:{v['class_in_beam']:.2f}" for f, v in summary.items()))

    evaluate(base, "base", eval_rows, {})
    base_states = {layer: block_state(base, layer) for layer in ALL_LAYERS}

    def train_condition(name, trainable, lr):
        model = clone(base)
        info = finetune(model, train, trainable=trainable, steps=steps, lr=lr, batch=int(ft["batch"]), seed=int(ft["seed"]))
        return model, info

    # full fine-tuning
    full_path = out_dir / "full_ft_state.pt"
    if "full" not in done or not full_path.exists():
        full, info = train_condition("full", None, float(ft["lr"]))
        torch.save({k: v.cpu() for k, v in full.state_dict().items()}, full_path)
        wchange = {layer: relative_weight_change(base, full, layer) for layer in ALL_LAYERS}
        evaluate(full, "full", eval_rows, {"train": {"losses_tail": info["losses"][-20:], "wall": info["wall_time"],
                                                       "trainable_parameters": info["trainable_parameters"]},
                                           "weight_change": wchange})
    full = clone(base)
    full.load_state_dict(torch.load(full_path))
    full.eval()
    full_states = {layer: block_state(full, layer) for layer in ALL_LAYERS}
    del full

    # single-block fine-tuning
    for layer in layers:
        name = f"single_{layer}"
        if name in done:
            continue
        model, info = train_condition(name, {layer}, float(ft["lr"]))
        evaluate(model, name, panel, {"train": {"losses_tail": info["losses"][-20:], "wall": info["wall_time"],
                                                 "trainable_parameters": info["trainable_parameters"]}})
        del model
        torch.cuda.empty_cache()

    # transplant: put one fine-tuned block into the base model (forward swap) and the reverse
    for layer in layers:
        for direction in ("into_base", "out_of_full"):
            name = f"swap_{direction}_{layer}"
            if name in done:
                continue
            model = clone(base)
            if direction == "into_base":
                load_block_state(model, layer, full_states[layer])
            else:
                for other in ALL_LAYERS:
                    load_block_state(model, other, full_states[other])
                load_block_state(model, layer, base_states[layer])
            model.eval()
            evaluate(model, name, panel, {})
            del model

    # learning-rate sensitivity on a subset
    for lr in ([] if smoke else ft["lr_sensitivity"]):
        for trainable, tag in ((None, "full"), ({"decoder_11"}, "single_decoder_11"), ({"decoder_3"}, "single_decoder_3"),
                               ({"encoder_2"}, "single_encoder_2")):
            name = f"lr{lr:g}_{tag}"
            if name in done:
                continue
            model, info = train_condition(name, trainable, float(lr))
            evaluate(model, name, panel, {"lr": lr})
            del model
    provenance(rd, "adapt", {"steps": steps})


PHASES = {"data": phase_data, "behavior": phase_behavior, "tunedlens": phase_tunedlens, "lens": phase_lens,
          "probe": phase_probe, "patch": phase_patch, "adapt": phase_adapt}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=sorted(PHASES) + ["all"])
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    os.chdir(ROOT)
    phases = ["data", "behavior", "tunedlens", "lens", "probe", "patch", "adapt"] if args.phase == "all" else [args.phase]
    for phase in phases:
        log(f"=== phase {phase} ===")
        PHASES[phase](args)


if __name__ == "__main__":
    main()
