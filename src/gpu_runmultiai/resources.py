"""Frozen resource ceilings for C0001 audit execution."""

from __future__ import annotations

import os
import time
from pathlib import Path

from gpu_runmultiai.constants import ELAPSED_WALL_CEILING_SEC, OUTPUT_DIR_BYTE_CEILING
from gpu_runmultiai.invariants import ResourceCeilingError

BYTE_CONVENTION = "decimal_gb"
CPU_WALL_LIMIT_SEC = ELAPSED_WALL_CEILING_SEC
DISK_LIMIT_BYTES = OUTPUT_DIR_BYTE_CEILING


class ResourceMonitor:
    def __init__(self, output_dir: Path) -> None:
        self._start = time.monotonic()
        self._output_dir = output_dir.resolve()

    def elapsed_sec(self) -> float:
        return time.monotonic() - self._start

    def dir_bytes(self) -> int:
        return _directory_size_bytes(self._output_dir)

    def snapshot(self) -> dict[str, Any]:
        """Non-raising resource measurement for abort evidence after a ceiling breach."""
        return {
            "elapsed_sec": self.elapsed_sec(),
            "output_dir_bytes": self.dir_bytes(),
            "elapsed_wall_ceiling_sec": CPU_WALL_LIMIT_SEC,
            "output_dir_byte_ceiling": DISK_LIMIT_BYTES,
            "byte_convention": BYTE_CONVENTION,
            "elapsed_exceeded": self.elapsed_sec() > CPU_WALL_LIMIT_SEC,
            "bytes_exceeded": self.dir_bytes() > DISK_LIMIT_BYTES,
        }

    def assert_within_limits(self) -> None:
        if self.elapsed_sec() > CPU_WALL_LIMIT_SEC:
            raise ResourceCeilingError(
                f"elapsed wall ceiling exceeded: {self.elapsed_sec():.1f}s > {CPU_WALL_LIMIT_SEC}s"
            )
        usage = self.dir_bytes()
        if usage > DISK_LIMIT_BYTES:
            raise ResourceCeilingError(
                f"output directory byte ceiling exceeded: {usage} bytes > {DISK_LIMIT_BYTES} bytes under {self._output_dir}"
            )


def _directory_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                continue
    return total
