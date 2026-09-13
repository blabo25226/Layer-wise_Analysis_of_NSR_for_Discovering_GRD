"""Sealed-path deny-on-attempt access guard (preregistration v9 §11)."""

from __future__ import annotations

import builtins
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

DENY_DIR_NAMES = frozenset({"test", "sealed", "final_test"})


@dataclass
class AccessAttempt:
    attempted_operation: str
    attempted_path_norm: str
    attempted_path_real: str


@dataclass
class SealedPathGuard:
    output_root_abs: Path
    attempts: list[AccessAttempt] = field(default_factory=list)
    _installed: bool = False
    _originals: dict[str, Any] = field(default_factory=dict)

    def campaign_relative_components(self, path: Path) -> list[str] | None:
        try:
            rel = path.resolve().relative_to(self.output_root_abs.resolve())
        except ValueError:
            return None
        return list(rel.parts)

    def is_denied(self, path_norm: str | Path, path_real: str | Path) -> bool:
        for candidate in (Path(path_norm), Path(path_real)):
            components = self.campaign_relative_components(candidate)
            if components is None or not components:
                continue
            if not components[0].startswith("gpu_run5_"):
                continue
            for index, name in enumerate(components):
                if name in DENY_DIR_NAMES:
                    return True
                if name == "predictions" and "phase8" in components[:index]:
                    return True
        return False

    def _check(self, operation: str, path: str | os.PathLike[str]) -> None:
        norm = os.path.normpath(os.path.abspath(os.fspath(path)))
        real = os.path.realpath(norm)
        if self.is_denied(norm, real):
            self.attempts.append(
                AccessAttempt(
                    attempted_operation=operation,
                    attempted_path_norm=norm,
                    attempted_path_real=real,
                )
            )
            raise PermissionError(f"sealed-path guard denied {operation} on {norm}")

    def install(self) -> None:
        if self._installed:
            return
        self._originals = {
            "open": builtins.open,
            "os_open": os.open,
            "os_stat": os.stat,
            "os_listdir": os.listdir,
            "os_scandir": os.scandir,
        }

        def guarded_open(file, mode="r", *args, **kwargs):
            mode_str = str(mode)
            if not any(flag in mode_str for flag in ("w", "a", "x")):
                self._check("open", file)
            return self._originals["open"](file, mode, *args, **kwargs)

        def guarded_os_open(path, flags, *args, **kwargs):
            if flags & os.O_WRONLY == 0 and flags & os.O_RDWR == 0:
                self._check("os.open", path)
            return self._originals["os_open"](path, flags, *args, **kwargs)

        def guarded_stat(path, *args, **kwargs):
            self._check("os.stat", path)
            return self._originals["os_stat"](path, *args, **kwargs)

        def guarded_listdir(path="."):
            self._check("os.listdir", path)
            return self._originals["os_listdir"](path)

        def guarded_scandir(path="."):
            self._check("os.scandir", path)
            return self._originals["os_scandir"](path)

        builtins.open = guarded_open
        os.open = guarded_os_open
        os.stat = guarded_stat
        os.listdir = guarded_listdir
        os.scandir = guarded_scandir
        self._patch_pathlib()
        self._installed = True

    def _patch_pathlib(self) -> None:
        from pathlib import Path

        originals: dict[str, Callable[..., Any]] = {
            "open": Path.open,
            "stat": Path.stat,
            "iterdir": Path.iterdir,
            "glob": Path.glob,
            "rglob": Path.rglob,
        }
        self._originals["pathlib"] = originals

        guard = self

        def wrap(method_name: str):
            original = originals[method_name]

            def wrapper(path_self, *args, **kwargs):
                if method_name == "open":
                    mode = args[0] if args else "r"
                    if "r" in str(mode):
                        guard._check(f"Path.{method_name}", path_self)
                else:
                    guard._check(f"Path.{method_name}", path_self)
                return original(path_self, *args, **kwargs)

            return wrapper

        Path.open = wrap("open")
        Path.stat = wrap("stat")
        Path.iterdir = wrap("iterdir")
        Path.glob = wrap("glob")
        Path.rglob = wrap("rglob")

    def restore(self) -> None:
        if not self._installed:
            return
        builtins.open = self._originals["open"]
        os.open = self._originals["os_open"]
        os.stat = self._originals["os_stat"]
        os.listdir = self._originals["os_listdir"]
        os.scandir = self._originals["os_scandir"]
        from pathlib import Path

        pathlib_originals = self._originals.get("pathlib", {})
        for name, func in pathlib_originals.items():
            setattr(Path, name, func)
        self._installed = False

    def attempt_count(self) -> int:
        return len(self.attempts)

    def to_log(self) -> list[dict[str, str]]:
        return [
            {
                "attempted_operation": item.attempted_operation,
                "attempted_path_norm": item.attempted_path_norm,
                "attempted_path_real": item.attempted_path_real,
            }
            for item in self.attempts
        ]
