"""GPU_RUN3 Phase 5: encoder intermediate decode and decoder logit-lens."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.architecture import inventory_ndformer  # noqa: E402
from gpu_run3.cli import common_parser, dummy_phase_output, require_previous, write_phase_manifest  # noqa: E402
from gpu_run3.corpus import build_analysis_corpus  # noqa: E402
from gpu_run3.decoderlens import decoder_logit_lens, encoder_intermediate_decode, encoder_ted_trajectory  # noqa: E402
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
    return common_parser("GPU_RUN3 Phase 5 DecoderLens / intermediate decoding").parse_args()


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase5"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 5, extra={"analysis": "encoder_intermediate_decode"})
        print(f"Phase 5 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    seed_everything(args.seed)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    inventory = inventory_ndformer(model)
    corpus = build_analysis_corpus(seed=args.seed)
    records = [row for row in corpus["records"] if row["split"] == "analysis_validation"]
    if args.smoke:
        records = records[:1]
    outputs = []
    for row in records:
        examples = [ex for ex in row["teacher_forcing"] if ex.get("target")][:4]
        if not examples:
            continue
        model.set_data(Xv=row["Xv"], Xe=row["Xe"], A=row["A"], G=row["G"], Y=row["Y"], root_type=row["root_type"], cache_data_emb=True)
        prefixes = [ex["prefix"] for ex in examples]
        targets = [ex["target"] for ex in examples]
        encoder_rows = encoder_intermediate_decode(model, inventory["encoder_blocks"], prefixes, true_targets=targets)
        encoder_rows = encoder_ted_trajectory(encoder_rows, true_prefix=row["prefix"])
        decoder_rows = decoder_logit_lens(model, inventory["decoder_blocks"], prefixes, true_targets=targets)
        outputs.append({"problem_id": row["problem_id"], "encoder": encoder_rows, "decoder": decoder_rows})
    summary = {"phase": 5, "status": "complete", "provenance": "layer_analysis", "n_problems": len(outputs)}
    write_json(out_dir / "trajectories.json", outputs)
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, summary)
    print(f"Phase 5 complete: {out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
