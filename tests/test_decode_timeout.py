from __future__ import annotations

import signal
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.decode_timeout import DecodeTimeout, decode_time_limit, run_with_timeout


def test_disabled_decode_timeout_is_noop() -> None:
    with decode_time_limit(0):
        pass


@pytest.mark.skipif(not hasattr(signal, "SIGALRM"), reason="SIGALRM requires POSIX")
def test_decode_timeout_interrupts_main_thread() -> None:
    with pytest.raises(DecodeTimeout, match="decode exceeded"):
        with decode_time_limit(0.01):
            time.sleep(0.1)


class _UnpicklableReturn:
    def __call__(self):
        return 7

    def __getstate__(self):
        raise TypeError("not picklable")


class _UnpicklableSlow:
    def __call__(self):
        time.sleep(0.05)
        return 1

    def __getstate__(self):
        raise TypeError("not picklable")


def test_run_with_timeout_falls_back_for_unpicklable_callable() -> None:
    assert run_with_timeout(_UnpicklableReturn(), timeout_sec=1.0) == 7


def test_run_with_timeout_inprocess_late_return_is_timeout() -> None:
    with pytest.raises(DecodeTimeout, match="in-process fallback"):
        run_with_timeout(_UnpicklableSlow(), timeout_sec=0.01)
