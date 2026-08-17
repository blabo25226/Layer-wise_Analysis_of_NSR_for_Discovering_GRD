"""GPU_RUN3 Phase 8: frozen-method test evaluation and integrated reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.cli import common_parser, dummy_phase_output, require_previous, write_phase_manifest  # noqa: E402
from gpu_run3.corpus import build_analysis_corpus  # noqa: E402
from gpu_run3.policy import teacher_forcing_metrics  # noqa: E402
from gpu_run3.records import dummy_formula_record  # noqa: E402
from gpu_run3_runtime import (  # noqa: E402
    load_gpu_run3_configs,
    load_ndformer,
    nd2_paths,
    require_python_310,
    resolve_run_dir,
    seed_everything,
    select_device,
    write_json,
)


def parse_args():
    parser = common_parser("GPU_RUN3 Phase 8 final test / integrated analysis")
    parser.add_argument("--force-test", action="store_true", help="evaluate analysis_test; default still requires frozen conditions")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase8"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(
            out_dir,
            8,
            extra={
                "result_a": "nd2_reproduction",
                "result_b": "ndformer_layer_analysis",
                "records": [dummy_formula_record("phase8_dummy")],
            },
        )
        print(f"Phase 8 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    conditions_path = require_previous(run_dir, "phase7/conditions.json")
    frozen = json.loads(conditions_path.read_text(encoding="utf-8"))
    if frozen.get("frozen_on_split") != "analysis_validation":
        raise RuntimeError("layer ranking was not frozen on analysis_validation")
    seed_everything(args.seed)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    corpus = build_analysis_corpus(seed=args.seed)
    test_rows = [row for row in corpus["records"] if row["split"] == "analysis_test"]
    policy_rows = []
    for row in test_rows:
        examples = [ex for ex in row["teacher_forcing"] if ex.get("target")]
        model.set_data(Xv=row["Xv"], Xe=row["Xe"], A=row["A"], G=row["G"], Y=row["Y"], root_type=row["root_type"], cache_data_emb=True)
        metrics = teacher_forcing_metrics(model, examples)
        policy_rows.append({"problem_id": row["problem_id"], **{k: v for k, v in metrics.items() if k != "rows"}})
    phase1 = _read(run_dir / "phase1" / "summary.json")
    phase3 = _read(run_dir / "phase3" / "summary.json")
    phase7 = _read(run_dir / "phase7" / "summary.json")
    report = {
        "phase": 8,
        "status": "complete",
        "result_a_nd2_reproduction": {
            "policy": phase1,
            "synthetic_benchmark": phase3,
        },
        "result_b_layer_analysis": {
            "conditions": frozen,
            "selective_ft": phase7,
            "test_policy": policy_rows,
        },
        "test_n": len(test_rows),
        "note": "analysis_test evaluated once after ranking/conditions were frozen on validation.",
    }
    write_json(out_dir / "report.json", report)
    write_json(out_dir / "summary.json", {"phase": 8, "status": "complete", "test_n": len(test_rows)})
    write_phase_manifest(out_dir, report)
    print(f"Phase 8 complete: {out_dir / 'report.json'}")
    return 0


def _read(path: Path):
    if not path.is_file():
        return {"status": "missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
