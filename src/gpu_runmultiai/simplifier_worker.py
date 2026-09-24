"""Child-process simplifier worker with sealed-path guard install."""

from __future__ import annotations

import atexit
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.phases.guard_bootstrap import install_guard_from_entry

child_guard = install_guard_from_entry(__file__)

from gpu_runmultiai.guard_side_channel import append_guard_attempts, child_side_channel_path

side_channel_path = child_side_channel_path()
_side_channel_flushed = 0


def _durable_append_new_attempts() -> None:
    """Append guard rows not yet written to the child side channel (§12.5 durability)."""
    global _side_channel_flushed
    if _side_channel_flushed >= len(child_guard.attempts):
        return
    new_rows = [
        {
            "attempted_operation": item.attempted_operation,
            "attempted_path_norm": item.attempted_path_norm,
            "attempted_path_real": item.attempted_path_real,
        }
        for item in child_guard.attempts[_side_channel_flushed:]
    ]
    append_guard_attempts(side_channel_path, new_rows)
    _side_channel_flushed = len(child_guard.attempts)


def _install_durable_guard_flush() -> None:
    original_check = child_guard._check

    def durable_check(operation: str, path: object) -> None:
        try:
            original_check(operation, path)
        except PermissionError:
            _durable_append_new_attempts()
            raise

    child_guard._check = durable_check  # type: ignore[method-assign]


_install_durable_guard_flush()
atexit.register(_durable_append_new_attempts)


def _flush_guard_attempts() -> list[dict[str, str]]:
    _durable_append_new_attempts()
    return child_guard.to_log()


def main() -> int:
    from gpu_runmultiai.odeformer_runtime import decode_system_tree, get_env, require_odeformer, tree_to_system_infix

    payload = json.loads(sys.stdin.read())
    prefixes = payload["prefixes"]
    timeout_sec = float(payload.get("timeout_sec", 5.0))
    try:
        require_odeformer()
        env = get_env()
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
        _durable_append_new_attempts()


if __name__ == "__main__":
    raise SystemExit(main())
