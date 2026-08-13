"""Stage a completed GPU_RUN2 archive for Google Drive backup + SHA256 check.

The local run directory remains the source of truth. This script never reads
or writes checkpoint files inside a Drive sync folder during training/decode.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import (  # noqa: E402
    load_gpu_run2_configs,
    resolve_run_dir,
    sha256_file,
    utc_now,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage GPU_RUN2 archive for Drive backup")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--dest", type=Path, required=True, help="staging or Drive folder")
    parser.add_argument("--archive", type=Path, help="explicit archive path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    archive = args.archive or (run_dir / f"{run_dir.name}.tar.gz")
    digest_file = Path(str(archive) + ".sha256")
    if not archive.is_file():
        print(f"archive not found: {archive}")
        return 1
    dest = args.dest.expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)
    staged_tmp = dest / (archive.name + ".partial")
    staged = dest / archive.name
    shutil.copy2(archive, staged_tmp)
    staged_tmp.replace(staged)
    local_hash = sha256_file(archive)
    remote_hash = sha256_file(staged)
    ok = local_hash == remote_hash and archive.stat().st_size == staged.stat().st_size
    if digest_file.is_file():
        shutil.copy2(digest_file, dest / digest_file.name)
    status = {
        "backup_status": "ok" if ok else "checksum_mismatch",
        "at_utc": utc_now(),
        "source": str(archive),
        "destination": str(staged),
        "local_sha256": local_hash,
        "remote_sha256": remote_hash,
        "local_bytes": archive.stat().st_size,
        "remote_bytes": staged.stat().st_size,
    }
    write_json(run_dir / "backup_status.json", status)
    print(json.dumps(status, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
