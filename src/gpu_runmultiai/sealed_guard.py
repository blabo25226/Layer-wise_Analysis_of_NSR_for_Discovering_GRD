"""Sealed-path deny-on-attempt access guard (preregistration v9 §11)."""

from __future__ import annotations

import builtins
import functools
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


def _is_fd(path: object) -> bool:
    return isinstance(path, int) and not isinstance(path, bool)


def _path_strings(path: object) -> tuple[str, str] | None:
    if _is_fd(path):
        return None
    fspath = os.fspath(path)
    norm = os.path.normpath(os.path.abspath(fspath))
    real = os.path.realpath(norm)
    return norm, real


def _is_under_root(real: str, root: str) -> bool:
    real_norm = os.path.normpath(real)
    root_norm = os.path.normpath(root)
    return real_norm == root_norm or real_norm.startswith(root_norm + os.sep)


@dataclass
class SealedPathGuard:
    output_root_abs: Path
    attempts: list[AccessAttempt] = field(default_factory=list)
    child_attempts: list[AccessAttempt] = field(default_factory=list)
    _installed: bool = False
    _originals: dict[str, Any] = field(default_factory=dict)
    _output_root_real: str = field(init=False, repr=False)
    _in_internal: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self._output_root_real = os.path.realpath(os.path.abspath(os.fspath(self.output_root_abs)))

    def campaign_relative_components(self, path: str | Path) -> list[str] | None:
        try:
            real = os.path.realpath(os.path.abspath(os.fspath(path)))
        except (OSError, TypeError, ValueError):
            return None
        if not _is_under_root(real, self._output_root_real):
            return None
        rel = os.path.relpath(real, self._output_root_real)
        if rel in (".", ""):
            return []
        return [part for part in rel.split(os.sep) if part]

    def is_denied(self, path_norm: str | Path, path_real: str | Path) -> bool:
        for candidate in (path_norm, path_real):
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

    def _check(self, operation: str, path: object) -> None:
        if self._in_internal:
            return
        resolved = _path_strings(path)
        if resolved is None:
            return
        norm, real = resolved
        self._in_internal = True
        try:
            if self.is_denied(norm, real):
                self.attempts.append(
                    AccessAttempt(
                        attempted_operation=operation,
                        attempted_path_norm=norm,
                        attempted_path_real=real,
                    )
                )
                raise PermissionError(f"sealed-path guard denied {operation} on {norm}")
        finally:
            self._in_internal = False

    def _is_write_open_mode(self, mode: object) -> bool:
        mode_str = str(mode)
        return any(flag in mode_str for flag in ("w", "a", "x", "+"))

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

        guard = self
        originals = self._originals

        @functools.wraps(originals["open"])
        def guarded_open(file, mode="r", *args, **kwargs):
            if guard._is_write_open_mode(mode):
                guard._check("open(write)", file)
            else:
                guard._check("open", file)
            return originals["open"](file, mode, *args, **kwargs)

        @functools.wraps(originals["os_open"])
        def guarded_os_open(path, flags, *args, **kwargs):
            if _is_fd(path):
                return originals["os_open"](path, flags, *args, **kwargs)
            if flags & (os.O_WRONLY | os.O_RDWR):
                guard._check("os.open(write)", path)
            elif flags & os.O_RDONLY:
                guard._check("os.open", path)
            return originals["os_open"](path, flags, *args, **kwargs)

        @functools.wraps(originals["os_stat"])
        def guarded_stat(path, *args, **kwargs):
            if not _is_fd(path):
                guard._check("os.stat", path)
            return originals["os_stat"](path, *args, **kwargs)

        @functools.wraps(originals["os_listdir"])
        def guarded_listdir(path=".", *args, **kwargs):
            if not _is_fd(path):
                guard._check("os.listdir", path)
            return originals["os_listdir"](path, *args, **kwargs)

        @functools.wraps(originals["os_scandir"])
        def guarded_scandir(path=".", *args, **kwargs):
            if not _is_fd(path):
                guard._check("os.scandir", path)
            return originals["os_scandir"](path, *args, **kwargs)

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

            @functools.wraps(original)
            def wrapper(path_self, *args, **kwargs):
                if method_name == "open":
                    mode = kwargs.get("mode", args[0] if args else "r")
                    if guard._is_write_open_mode(mode):
                        guard._check(f"Path.{method_name}(write)", path_self)
                    else:
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

    def extend_child_attempts(self, rows: list[dict[str, str]]) -> None:
        for row in rows:
            attempt = AccessAttempt(
                attempted_operation=row["attempted_operation"],
                attempted_path_norm=row["attempted_path_norm"],
                attempted_path_real=row["attempted_path_real"],
            )
            self.child_attempts.append(attempt)
            self.attempts.append(attempt)

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
