"""GPU_RUN4 Phase 5: observational layer analysis on the analysis-validation split."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.analysis import cka_matrix, collect_encoder_features, gradient_by_layer, probe_layers, probe_score_map  # noqa: E402
from gpu_run4.cli import common_parser, dummy_phase_output, require_previous, write_phase_manifest  # noqa: E402
from gpu_run4.ranking_utils import rank_from_scores  # noqa: E402
from gpu_run4.session import jsonable, open_session  # noqa: E402
from gpu_run4_runtime import write_json  # noqa: E402


def parse_args():
    return common_parser("GPU_RUN4 Phase 5 observational analysis").parse_args()


def _load_split(path: Path, split: str) -> list[dict]:
    import numpy as np

    rows = __import__("json").loads(path.read_text())
    out = []
    for row in rows:
        if row.get("split") != split:
            continue
        row = dict(row)
        row["times"] = np.asarray(row["times"], dtype=float)
        row["trajectory"] = np.asarray(row["trajectory"], dtype=float)
        out.append(row)
    return out


def main() -> int:
    args = parse_args()
    if args.dry_run:
        from gpu_run4_runtime import resolve_run_dir

        dummy_phase_output(resolve_run_dir(args.run_id) / "phase5", 5)
        return 0
    session = open_session(args)
    run_dir = session["run_dir"]
    require_previous(run_dir, "phase4/corpus.json")
    out_dir = run_dir / "phase5"
    out_dir.mkdir(parents=True, exist_ok=True)
    layers = [name for name in session["ranking_layers"] if name.startswith("encoder_")]
    all_layers = session["ranking_layers"]
    train = _load_split(run_dir / "phase4" / "corpus.json", "analysis_train")
    val = _load_split(run_dir / "phase4" / "corpus.json", "analysis_validation")
    train_f = collect_encoder_features(session["model"], train, layers)
    val_f = collect_encoder_features(session["model"], val, layers)
    probes = probe_layers(train_f, val_f)
    grads = gradient_by_layer(session["model"], val, all_layers)
    cka = cka_matrix(val_f["features"], layers)
    dim_scores = probe_score_map(probes, "dimension")
    ranking = {
        "probe_dimension": rank_from_scores(dim_scores, higher_is_better=True),
        "gradient_norm": rank_from_scores(grads, higher_is_better=True),
    }
    go = {
        "hidden_extracted": bool(val_f["features"]),
        "probes_fit": bool(probes),
        "gradients_finite": any(v == v for v in grads.values()),
    }
    payload = {
        "phase": 5,
        "status": "complete" if all(go.values()) else "incomplete",
        "n_train": len(train),
        "n_validation": len(val),
        "layers": all_layers,
        "probes": jsonable(probes),
        "gradient_norm": grads,
        "cka_encoder": cka,
        "rankings": ranking,
        "go_conditions": go,
    }
    write_json(out_dir / "eval.json", jsonable(payload))
    write_json(out_dir / "rankings.json", ranking)
    write_phase_manifest(out_dir, jsonable(payload))
    print(f"Phase 5 {payload['status']}: probe rank={ranking['probe_dimension'][:3]}")
    return 0 if payload["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
