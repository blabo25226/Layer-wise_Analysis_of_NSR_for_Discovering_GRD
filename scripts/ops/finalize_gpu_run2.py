"""GPU_RUN2 completion: schema check, true-vs-pred tables, archive, SHA256."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.equation_records import GPU_RUN2_REQUIRED_FIELDS  # noqa: E402
from gpu_run2_runtime import (  # noqa: E402
    graphs_dir,
    load_gpu_run2_configs,
    resolve_run_dir,
    sha256_file,
    utc_now,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finalize a GPU_RUN2 run")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--skip-archive", action="store_true")
    return parser.parse_args()


def _iter_records(run_dir: Path) -> list[tuple[str, dict]]:
    rows = []
    for path in run_dir.rglob("*_records.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and "eq_id" in item:
                    rows.append((str(path.relative_to(run_dir)), item))
    return rows


def _validate_records(rows: list[tuple[str, dict]]) -> list[str]:
    issues = []
    for location, row in rows:
        missing = sorted(GPU_RUN2_REQUIRED_FIELDS - set(row))
        if missing:
            issues.append(f"{location}:{row.get('eq_id')}: missing {missing}")
            continue
        if not row.get("valid_pred") and not row.get("failure_reason"):
            issues.append(f"{location}:{row.get('eq_id')}: failed row has no failure_reason")
        if row.get("timeout") and row.get("failure_reason") not in {None, "DecodeTimeout"}:
            # timeout may coexist with a more specific reason; still require a reason.
            if not row.get("failure_reason"):
                issues.append(f"{location}:{row.get('eq_id')}: timeout without reason")
        if "ood_nmse" in row and "domain_ood_nmse" not in row:
            issues.append(f"{location}:{row.get('eq_id')}: bare ood_nmse is forbidden")
    return issues


def _write_true_vs_pred_table(rows: list[tuple[str, dict]], tables_dir: Path) -> Path:
    tables_dir.mkdir(parents=True, exist_ok=True)
    path = tables_dir / "true_vs_pred.csv"
    fieldnames = [
        "eq_id",
        "condition",
        "noise",
        "structure_regime",
        "true_expr",
        "pred_expr",
        "exact",
        "skeleton",
        "symbolic_equivalent",
        "domain_id_nmse",
        "domain_ood_nmse",
        "valid_or_failure",
        "source_file",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for source, row in rows:
            writer.writerow(
                {
                    "eq_id": row.get("eq_id"),
                    "condition": row.get("condition"),
                    "noise": row.get("noise"),
                    "structure_regime": row.get("structure_regime"),
                    "true_expr": row.get("true_canonical") or row.get("true_expr"),
                    "pred_expr": row.get("pred_simplified") or row.get("pred_raw"),
                    "exact": row.get("exact"),
                    "skeleton": row.get("skeleton"),
                    "symbolic_equivalent": row.get("symbolic_equivalent"),
                    "domain_id_nmse": row.get("domain_id_nmse"),
                    "domain_ood_nmse": row.get("domain_ood_nmse"),
                    "valid_or_failure": (
                        "valid" if row.get("valid_pred") else row.get("failure_reason")
                    ),
                    "source_file": source,
                }
            )
    return path


def _archive(run_dir: Path) -> tuple[Path, str]:
    archive = run_dir / f"{run_dir.name}.tar.gz"
    tmp = run_dir / f"{run_dir.name}.tar.gz.partial"
    with tarfile.open(tmp, "w:gz") as tar:
        for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
            if path.name.endswith(".partial") or path.suffix in {".tar", ".gz"} and path.name.startswith(run_dir.name):
                continue
            tar.add(path, arcname=str(path.relative_to(run_dir)))
    tmp.replace(archive)
    digest_path = run_dir / f"{run_dir.name}.tar.gz.sha256"
    digest_path.write_text(sha256_file(archive) + "  " + archive.name + "\n", encoding="utf-8")
    return archive, sha256_file(archive)


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    run_id = run_dir.name
    figures_dir, tables_dir = graphs_dir(run_id, config=config)
    required_dirs = ["phase0", "phase1", "phase2", "phase3", "phase4", "phase5"]
    missing_dirs = [name for name in required_dirs if not (run_dir / name).is_dir()]
    records = _iter_records(run_dir)
    issues = _validate_records(records)
    if missing_dirs:
        issues.append(f"missing phase directories: {missing_dirs}")
    table_path = _write_true_vs_pred_table(records, tables_dir) if records else None
    archive_info = None
    if not args.skip_archive and not issues:
        archive, digest = _archive(run_dir)
        archive_info = {"archive": str(archive), "sha256": digest}
    report = {
        "status": "complete" if not issues else "validation_failed",
        "at_utc": utc_now(),
        "n_records": len(records),
        "issues": issues,
        "true_vs_pred_table": str(table_path) if table_path else None,
        "figures_dir": str(figures_dir),
        "tables_dir": str(tables_dir),
        "archive": archive_info,
    }
    write_json(run_dir / "finalize.json", report)
    manifest_path = run_dir / "manifest.json"
    manifest = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({"finalize": report, "status": report["status"], "at_utc": utc_now()})
    write_json(manifest_path, manifest)
    print(f"finalize status={report['status']} records={len(records)} issues={len(issues)}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
