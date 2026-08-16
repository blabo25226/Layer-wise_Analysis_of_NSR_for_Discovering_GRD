"""GPU_RUN2 Phase 0: local RTX 2070 preflight and schema smoke."""

from __future__ import annotations

import argparse
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from evaluation.decode_timeout import DecodeTimeout, decode_time_limit, run_with_timeout  # noqa: E402
from evaluation.equation_records import GPU_RUN2_REQUIRED_FIELDS, make_gpu_run2_equation_record  # noqa: E402
from evaluation.operator_policy import (  # noqa: E402
    filter_prefix_tokens,
    load_operator_config,
    validate_candidate_expression,
)
from gpu_run2_runtime import (  # noqa: E402
    cpu_identity,
    decode_timeout_sec,
    git_info,
    load_gpu_run2_configs,
    nesymres_paths,
    resolve_run_dir,
    sha256_file,
    utc_now,
    write_json,
)


def _preflight_sleep(seconds: float) -> None:
    import time

    time.sleep(float(seconds))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN2 Phase 0 preflight")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--allow-cpu", action="store_true", help="do not fail if CUDA is missing")
    parser.add_argument("--smoke-problems", type=int, default=2)
    return parser.parse_args()


def checkpoint_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return sha256_file(path)


def smoke_operator_and_timeout(timeout_sec: float) -> dict:
    import torch
    from types import SimpleNamespace

    from nesymres.architectures.model import _gpu_run2_mask_scores

    ok_pow, reason_pow = validate_candidate_expression("x_1**2 / (1 + x_2**3) - 0.2*x_1")
    bad_pow, reason_bad = validate_candidate_expression("x_1**x_2")
    bad_fn, reason_fn = validate_candidate_expression("tan(x_1) + x_2")
    prefix_ok, _ = filter_prefix_tokens(["mul", "x_1", "pow", "x_2", "3"])
    prefix_bad, prefix_reason = filter_prefix_tokens(["pow", "x_1", "x_2"])
    word2id = {"P": 0, "S": 1, "F": 2, "c": 3, "x_1": 4, "x_2": 5, "add": 6, "sin": 7}
    mask_params = SimpleNamespace(
        word2id=word2id,
        id2word={token_id: token for token, token_id in word2id.items()},
        allowed_token_ids={0, 1, 2, 3, 4, 5, 6},
        allowed_pow_exponent_ids=set(),
        allowed_variable_ids={word2id["x_1"]},
    )
    masked = _gpu_run2_mask_scores(
        torch.zeros((1, len(word2id))),
        torch.tensor([[word2id["S"], 0]]),
        1,
        mask_params,
    )
    decode_mask_ok = (
        torch.isfinite(masked[0, word2id["x_1"]]).item()
        and not torch.isfinite(masked[0, word2id["x_2"]]).item()
        and not torch.isfinite(masked[0, word2id["sin"]]).item()
        and not torch.isfinite(masked[0, word2id["F"]]).item()
    )
    timeout_fired = False
    try:
        with decode_time_limit(0.01):
            if hasattr(os, "fork") or sys.platform != "win32":
                import time

                time.sleep(0.2)
    except DecodeTimeout:
        timeout_fired = True
    if not timeout_fired:
        try:
            run_with_timeout(_preflight_sleep, 0.2, timeout_sec=0.01)
        except DecodeTimeout:
            timeout_fired = True
    dummy = make_gpu_run2_equation_record(
        eq_id="G02_variant_000",
        predicted_expr="x_1",
        variable_names=["x_1", "x_2"],
        scores={
            "valid_pred": 1.0,
            "nmse": 0.1,
            "r2": 0.9,
            "sym_exact": 0.0,
            "sym_skeleton": 0.0,
            "sym_equiv": 0.0,
            "complexity": 3.0,
            "var_f1": 1.0,
            "var_precision": 1.0,
            "var_recall": 1.0,
            "domain_id_nmse": 0.1,
            "domain_ood_nmse": 0.2,
        },
        true_expr="1 - x_1",
        true_raw="V - delta*x_1",
        true_canonical="1 - x_1",
        true_skeleton="c - x_1",
        pred_canonical="x_1",
        pred_skeleton="x_1",
        motif="G02",
        split="validation",
        split_view="main",
        noise=0.0,
        data_seed=101,
        training_seed=0,
        condition="smoke",
        domain_regime="id",
        structure_regime="id",
        parameter_split="main",
        target_variable="x_1",
        oracle_regulators=["x_2"],
        oracle_inputs=["x_1", "x_2"],
        variable_order=["x_1", "x_2"],
        oracle_source_equation_id="G02_variant_000",
        decoder="smoke",
        timeout_budget_sec=timeout_sec,
    )
    missing = sorted(GPU_RUN2_REQUIRED_FIELDS - set(dummy))
    return {
        "allowed_integer_pow_ok": ok_pow and reason_pow is None,
        "variable_pow_rejected": (not bad_pow) and reason_bad == "DisallowedPowerExponent",
        "tan_rejected": (not bad_fn) and str(reason_fn).startswith("DisallowedOperator"),
        "prefix_integer_pow_ok": prefix_ok,
        "prefix_variable_pow_rejected": (not prefix_bad) and prefix_reason == "DisallowedPowerExponent",
        "decode_token_mask_active": bool(decode_mask_ok),
        "timeout_mechanism_present": timeout_fired,
        "record_schema_missing": missing,
        "timeout_budget_sec": timeout_sec,
    }


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase0"
    out_dir.mkdir(parents=True, exist_ok=True)
    timeout_sec = decode_timeout_sec(config)
    os.environ.setdefault("LANSR_DECODE_TIMEOUT_SEC", str(int(timeout_sec)))
    paths = nesymres_paths(config)
    cuda_ok = False
    gpu_name = None
    torch_version = None
    try:
        import torch

        torch_version = torch.__version__
        cuda_ok = bool(torch.cuda.is_available())
        if cuda_ok:
            gpu_name = torch.cuda.get_device_name(0)
    except Exception as exc:
        torch_version = f"import_failed:{exc}"
    if not cuda_ok and not args.allow_cpu:
        write_json(
            out_dir / "preflight_failed.json",
            {"error": "CUDA is not available", "at_utc": utc_now()},
        )
        print("CUDA is not available. Pass --allow-cpu for a CPU-only schema smoke.")
        return 1
    weights_hash = checkpoint_sha256(paths["weights"])
    if paths["weights"].is_file() is False and not args.allow_cpu:
        print(f"Missing NeSymReS checkpoint: {paths['weights']}")
        return 1
    smoke = smoke_operator_and_timeout(timeout_sec)
    if smoke["record_schema_missing"]:
        print(f"equation schema missing fields: {smoke['record_schema_missing']}")
        return 1
    if not smoke["decode_token_mask_active"]:
        print("NeSymReS decode token mask smoke failed")
        return 1
    manifest = {
        "phase": 0,
        "status": "complete",
        "at_utc": utc_now(),
        "run_dir": str(run_dir),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu": cpu_identity(),
        "git": git_info(),
        "torch": torch_version,
        "cuda_ok": cuda_ok,
        "gpu_name": gpu_name,
        "timeout_sec": timeout_sec,
        "operator_config": load_operator_config(),
        "nesymres_paths": {k: str(v) for k, v in paths.items()},
        "checkpoint_sha256": weights_hash,
        "checkpoint_exists": paths["weights"].is_file(),
        "smoke": smoke,
        "gnw_source_commit": config.get("gnw_source_commit"),
        "seed_bundles": config.get("seed_bundles"),
        "noises": config.get("noises"),
        "fail_fast_on_oom": bool(config.get("fail_fast_on_oom", True)),
    }
    write_json(out_dir / "preflight.json", manifest)
    write_json(run_dir / "manifest.json", {"status": "running", "phase0": manifest, "at_utc": utc_now()})
    print(f"Phase 0 complete: {out_dir / 'preflight.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
