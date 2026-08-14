#!/usr/bin/env python
"""Fail-fast audit: every GPU_RUN2 teacher_expr must fit NeSymReS length_eq."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from data.gnw_synthetic import (  # noqa: E402
    assert_all_teachers_within_length_eq,
    define_gnw_problems,
    teacher_equiv_canonical,
)
from gpu_run2_runtime import load_gpu_run2_configs, nesymres_paths, write_json  # noqa: E402
from models.nesymres_adapter import load_nesymres  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-variants", type=int, default=None)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="optional JSON report path",
    )
    parser.add_argument(
        "--check-equivalence",
        action="store_true",
        help="also assert teacher_expr ≡ canonical_expr for every problem",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    paths = nesymres_paths(config)
    if not paths["weights"].is_file():
        raise FileNotFoundError(f"NeSymReS checkpoint missing: {paths['weights']}")
    _model, params = load_nesymres(paths["weights"], paths["config"], paths["eq_setting"])
    length_eq = int(getattr(_model.cfg, "length_eq", 60))
    del _model
    n_variants = int(args.n_variants or config["n_variants_per_family"])
    specs = define_gnw_problems(
        n_variants_per_family=n_variants,
        variant_seed=int(config["variant_seed"]),
    )
    report = assert_all_teachers_within_length_eq(
        specs,
        params.word2id,
        max_token_len=length_eq,
    )
    if args.check_equivalence:
        bad = []
        for spec in specs:
            if not teacher_equiv_canonical(spec.teacher_expr, spec.canonical_expr):
                bad.append(spec.eq_id)
        report["equivalence_failures"] = bad
        if bad:
            raise RuntimeError(
                f"teacher_expr not equivalent to canonical_expr for {len(bad)} problems: {bad[:12]}"
            )
        report["equivalence_ok"] = True
    print(
        json.dumps(
            {
                "n_problems": report["n_problems"],
                "max_token_len": report["max_token_len"],
                "n_ok": report["n_ok"],
                "max_observed": report["max_observed"],
                "equivalence_ok": report.get("equivalence_ok"),
            },
            indent=2,
        )
    )
    if args.out is not None:
        write_json(args.out, report)
        print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
