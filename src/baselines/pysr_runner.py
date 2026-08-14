"""Small, dependency-isolated PySR adapter used by local CPU runs."""

from __future__ import annotations

from typing import Sequence

import numpy as np


def fit_pysr_expression(
    X: np.ndarray,
    y: np.ndarray,
    variable_names: Sequence[str],
    *,
    niterations: int,
    random_state: int = 0,
    timeout_in_seconds: float | None = None,
    binary_operators: Sequence[str] | None = None,
    unary_operators: Sequence[str] | None = None,
    operator_set: str | None = None,
) -> str:
    """Fit one bounded PySR problem and return its best expression."""
    from pysr import PySRRegressor

    if operator_set == "gpu_run2":
        from evaluation.operator_policy import pysr_operator_kwargs

        mapped = pysr_operator_kwargs()
        binary_operators = binary_operators or mapped["binary_operators"]
        unary_operators = unary_operators or mapped["unary_operators"]
    kwargs = dict(
        niterations=niterations,
        binary_operators=list(binary_operators or ["+", "-", "*", "/"]),
        unary_operators=list(unary_operators or ["square"]),
        maxsize=20,
        progress=False,
        verbosity=0,
        temp_equation_file=True,
        random_state=random_state,
        parallelism="multithreading",
        extra_sympy_mappings={
            "square": lambda x: x**2,
            "cube": lambda x: x**3,
            "pow4": lambda x: x**4,
            "pow5": lambda x: x**5,
        },
    )
    if timeout_in_seconds is not None:
        kwargs["timeout_in_seconds"] = float(timeout_in_seconds)
    model = PySRRegressor(**kwargs)
    model.fit(X, y, variable_names=list(variable_names))
    return str(model.get_best()["equation"])
