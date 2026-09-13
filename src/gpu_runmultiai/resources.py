"""Frozen resource ceilings for C0001 audit execution."""

from __future__ import annotations

import os
import time
from pathlib import Path

from gpu_runmultiai.invariants import ResourceCeilingError

CPU_WALL_LIMIT_SEC = 4 * 3600
DISK_LIMIT_BYTES = 1 * 1024 * 1024 * 1024


class ResourceMonitor:
    def __init__(self, output_dir: Path) -> None:
        self._start = time.monotonic()
        self._output_dir = output_dir.resolve()

    def elapsed_sec(self) -> float:
        return time.monotonic() - self._start

    def assert_within_limits(self) -> None:
        if self.elapsed_sec() > CPU_WALL_LIMIT_SEC:
            raise ResourceCeilingError(
                f"CPU wall-time ceiling exceeded: {self.elapsed_sec():.1f}s > {CPU_WALL_LIMIT_SEC}s"
            )
        usage = _directory_size_bytes(self._output_dir)
        if usage > DISK_LIMIT_BYTES:
            raise ResourceCeilingError(
                f"disk ceiling exceeded: {usage} bytes > {DISK_LIMIT_BYTES} bytes under {self._output_dir}"
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
