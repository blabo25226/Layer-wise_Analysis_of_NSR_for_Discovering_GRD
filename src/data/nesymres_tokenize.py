"""NeSymReS expression tokenization helpers without importing architectures.data.

``nesymres.architectures.data`` pulls in Hydra/Lightning at import time, which breaks
on some local Python versions. Tokenization only needs SymPy + Generator.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import torch
from sympy import Float, Symbol, sympify
from sympy.core.rules import Transform

from nesymres.dataset.generator import Generator, UnknownSymPyOperator


def constants_to_placeholder(s, symbol: str = "c"):
    """Replace Float literals with a placeholder symbol (NeSymReS skeleton)."""
    sympy_expr = sympify(s) if not hasattr(s, "free_symbols") else s
    return sympy_expr.xreplace(
        Transform(
            lambda x: Symbol(symbol, real=True, nonzero=True),
            lambda x: isinstance(x, Float),
        )
    )


def tokenize(prefix_expr: list, word2id: dict) -> list:
    tokenized_expr = [word2id["S"]]
    for tok in prefix_expr:
        tokenized_expr.append(word2id[tok])
    tokenized_expr.append(word2id["F"])
    return tokenized_expr


def tokens_padding(tokens: Sequence[Sequence[int]]) -> torch.Tensor:
    max_len = max(len(y) for y in tokens)
    p_tokens = torch.zeros(len(tokens), max_len)
    for i, y in enumerate(tokens):
        y_t = torch.tensor(list(y), dtype=torch.long)
        p_tokens[i, :] = torch.cat([y_t, torch.zeros(max_len - y_t.shape[0], dtype=torch.long)])
    return p_tokens


def expression_to_tokens(expr: str, word2id: Dict[str, int]) -> Optional[List[int]]:
    try:
        skeleton = constants_to_placeholder(expr)
        prefix = Generator.sympy_to_prefix(skeleton)
        return tokenize(prefix, word2id)
    except (UnknownSymPyOperator, KeyError, RecursionError, Exception):
        return None
