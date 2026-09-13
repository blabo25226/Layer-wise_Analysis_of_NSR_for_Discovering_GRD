"""Child-process simplifier worker with sealed-path guard install."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_runmultiai.config_paths import output_root_abs
from gpu_runmultiai.guard_side_channel import append_guard_attempts, child_side_channel_path
from gpu_runmultiai.sealed_guard import SealedPathGuard

output_root = output_root_abs()
guard = SealedPathGuard(output_root_abs=output_root)
guard.install()
side_channel_path = child_side_channel_path()

from gpu_runmultiai.odeformer_runtime import decode_system_tree, get_env, require_odeformer, tree_to_system_infix


def _flush_guard_attempts() -> list[dict[str, str]]:
    attempts = guard.to_log()
    append_guard_attempts(side_channel_path, attempts)
    return attempts


def main() -> int:
    payload = json.loads(sys.stdin.read())
    prefixes = payload["prefixes"]
    timeout_sec = float(payload.get("timeout_sec", 5.0))
    require_odeformer()
    env = get_env()
    try:
        tree = decode_system_tree(env, prefixes)
        simplified = env.simplifier.simplify_tree(tree, expand=False, resimplify=False)
        infix = tree_to_system_infix(simplified)
        prefix = simplified.prefix() if hasattr(simplified, "prefix") else ""
        print(
            json.dumps(
                {
                    "ok": True,
                    "infix": infix,
                    "prefix": prefix,
                    "guard_attempts": _flush_guard_attempts(),
                }
            )
        )
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "failure_reason": type(exc).__name__,
                    "guard_attempts": _flush_guard_attempts(),
                }
            )
        )
        return 1
    finally:
        guard.restore()


if __name__ == "__main__":
    raise SystemExit(main())
