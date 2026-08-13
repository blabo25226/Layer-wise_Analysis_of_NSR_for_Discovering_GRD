"""Wall-clock guard for pathological single-problem symbolic decodes."""

from __future__ import annotations

import pickle
import signal
import threading
import time
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeout
from contextlib import contextmanager
from typing import Any, Callable, Iterator, TypeVar

T = TypeVar("T")


class DecodeTimeout(Exception):
    """Raised when one symbolic-regression decode exceeds its time budget."""


@contextmanager
def decode_time_limit(seconds: float) -> Iterator[None]:
    """Limit a decode on the POSIX main thread using ``SIGALRM``.

    Colab and Linux GPU environments execute phase loops on the main thread.
    Windows has no SIGALRM; callers should use :func:`run_with_timeout` or a
    parent-process hard timeout with grace.
    """
    if (
        seconds <= 0
        or not hasattr(signal, "SIGALRM")
        or threading.current_thread() is not threading.main_thread()
    ):
        yield
        return

    def _handler(signum, frame):
        raise DecodeTimeout(f"decode exceeded {seconds:.0f}s")

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def _is_picklable(*objects: Any) -> bool:
    try:
        pickle.dumps(objects)
    except Exception:
        return False
    return True


def run_with_timeout(
    func: Callable[..., T],
    /,
    *args: Any,
    timeout_sec: float,
    **kwargs: Any,
) -> T:
    """Run ``func`` with a hard wall-clock limit.

    POSIX main threads use SIGALRM so the call stays in-process. Elsewhere a
    one-worker process pool is used when ``func``/args are picklable. NeSymReS
    models are not picklable on Windows, so those calls fall back to in-process
    timing: the call is not interrupted mid-CUDA, but a late return is still
    recorded as ``DecodeTimeout`` instead of crashing on pickle.
    """
    seconds = float(timeout_sec)
    if seconds <= 0:
        return func(*args, **kwargs)
    if (
        hasattr(signal, "SIGALRM")
        and threading.current_thread() is threading.main_thread()
    ):
        with decode_time_limit(seconds):
            return func(*args, **kwargs)
    if _is_picklable(func, args, kwargs):
        with ProcessPoolExecutor(max_workers=1) as pool:
            future = pool.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=seconds)
            except FuturesTimeout as exc:
                future.cancel()
                raise DecodeTimeout(f"decode exceeded {seconds:.0f}s") from exc
    started = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - started
    if elapsed > seconds:
        raise DecodeTimeout(
            f"decode exceeded {seconds:.0f}s (in-process fallback after {elapsed:.1f}s)"
        )
    return result
