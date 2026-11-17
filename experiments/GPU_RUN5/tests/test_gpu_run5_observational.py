from __future__ import annotations

from collections import Counter

import torch

from gpu_run5.observational import (
    _pool_sequence,
    formula_depth,
    select_stratified_grn_panel,
    token_category,
)


def test_odeformer_sequence_pool_uses_sequence_axis() -> None:
    hidden = torch.arange(1 * 3 * 2, dtype=torch.float32).reshape(1, 3, 2)
    assert _pool_sequence(hidden).tolist() == [2.0, 3.0]


def test_formula_depth_and_token_categories() -> None:
    assert formula_depth("x_0 + x_1**2") >= 3
    assert token_category("x_0") == "variable"
    assert token_category("inv") == "inv"
    assert token_category("pow2") == "integer_power"
    assert token_category("mul") == "multiplication"
    assert token_category("<EOS>") == "eos"
    assert token_category("|") == "separator"
    assert token_category("N1234") == "constant"


def test_stratified_grn_panel_has_exact_dimension_counts_and_family_cap() -> None:
    records = []
    dimension_families = {1: ("R01", "R02"), 2: ("R03", "R04", "R05"), 3: ("R06", "R07", "R08")}
    for dimension, families in dimension_families.items():
        for family in families:
            for index in range(10):
                records.append(
                    {"system_id": f"{family}_{index:02d}", "family": family, "dimension": dimension}
                )
    panel = select_stratified_grn_panel(records)
    assert len(panel) == 24
    assert {dimension: sum(row["dimension"] == dimension for row in panel) for dimension in (1, 2, 3)} == {
        1: 8,
        2: 8,
        3: 8,
    }
    assert max(Counter(row["family"] for row in panel).values()) <= 4
