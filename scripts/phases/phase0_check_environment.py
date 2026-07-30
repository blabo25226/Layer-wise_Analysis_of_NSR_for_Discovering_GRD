"""Phase 0 environment and artifact checks."""

from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CHECKPOINTS = {
    "assets/nesymres/weights/100M.ckpt": ROOT
    / "assets"
    / "nesymres"
    / "weights"
    / "100M.ckpt",
    "assets/nesymres/weights/10M.ckpt": ROOT
    / "assets"
    / "nesymres"
    / "weights"
    / "10M.ckpt",
    "assets/nesymres/weights/model.pt": ROOT
    / "assets"
    / "nesymres"
    / "weights"
    / "model.pt",
}


def check_import(name: str) -> str:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic script
        return f"FAIL ({exc})"
    version = getattr(module, "__version__", "ok")
    return str(version)


def main() -> int:
    print("Python:", sys.version.split()[0], platform.platform())
    for pkg in ("numpy", "torch", "pytorch_lightning", "sympy", "omegaconf", "hydra"):
        print(f"{pkg}: {check_import(pkg)}")
    print("nesymres package root:", ROOT / "third_party" / "nesymres")
    print("tpsr runtime root:", ROOT / "third_party" / "tpsr")
    missing = False
    for label, path in CHECKPOINTS.items():
        ok = path.exists()
        print(f"{label}: {'OK' if ok else 'MISSING'} ({path})")
        if not ok:
            missing = True
    if missing:
        print("Hint: powershell -File scripts/ops/setup_phase0_links.ps1")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
