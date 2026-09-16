"""Frozen source inventory algorithm (preregistration v16 §13.2)."""

from __future__ import annotations

from pathlib import Path

from experiment_runtime import REPO_ROOT
from gpu_run2_runtime import sha256_file

from gpu_runmultiai.constants import SOURCE_INVENTORY_EXTRA_PATHS


def enumerate_source_inventory_paths() -> list[str]:
    paths: list[Path] = []
    paths.extend(sorted((REPO_ROOT / "src/gpu_runmultiai").glob("*.py")))
    paths.extend(SOURCE_INVENTORY_EXTRA_PATHS)
    paths.extend(sorted((REPO_ROOT / "third_party/odeformer").rglob("*.py")))
    rel_paths = sorted({str(path.relative_to(REPO_ROOT)).replace("\\", "/") for path in paths})
    return rel_paths


def build_source_inventory(*, include_hashes: bool = True) -> list[dict[str, str]]:
    inventory: list[dict[str, str]] = []
    for rel_path in enumerate_source_inventory_paths():
        entry: dict[str, str] = {"path": rel_path}
        if include_hashes:
            entry["sha256"] = sha256_file(REPO_ROOT / rel_path)
        inventory.append(entry)
    return inventory
