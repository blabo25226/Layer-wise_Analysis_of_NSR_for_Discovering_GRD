"""Component stratum classification for frozen C0001 corpus."""

from __future__ import annotations

STRICT_HILL_PER_FAMILY = {
    "R01": {0},
    "R02": {0},
    "R03": {0, 1},
    "R04": {1},
    "R05": {0, 1},
    "R06": {0, 1, 2},
    "R07": {1},
    "R08": set(),
}

NON_STRICT_HILL_PER_FAMILY = {
    "R07": {2},
    "R08": {2},
}

LINEAR_PER_FAMILY = {
    "R04": {0},
    "R07": {0},
    "R08": {0, 1},
}


def component_stratum(family: str, component_idx: int) -> str:
    if component_idx in STRICT_HILL_PER_FAMILY.get(family, set()):
        return "strict_hill"
    if component_idx in NON_STRICT_HILL_PER_FAMILY.get(family, set()):
        return "non_strict_hill"
    if component_idx in LINEAR_PER_FAMILY.get(family, set()):
        return "linear"
    return "other"


def is_strict_hill_component(family: str, component_idx: int) -> bool:
    return component_stratum(family, component_idx) == "strict_hill"


def is_linear_component(family: str, component_idx: int) -> bool:
    return component_stratum(family, component_idx) == "linear"
