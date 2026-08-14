"""GNW synthetic benchmark v1 for GPU_RUN2.

Implements GeneNetWeaver Hill-type mRNA equations for families G01–G08.
Analytic targets are evaluated directly; finite differences are not used.

Parameter initialization follows GNW commit
``5016f55ab04c111f29d7d0b3a4881d4725d49467`` (``Gene.java``, ``HillGene.java``,
``RegulatoryModule.java``, ``GnwSettings.java``), with Hill coefficients
restricted to ``{1,2,3,4,5}`` so true formulas are expressible under the
GPU_RUN2 operator allowlist. Runtime code does not import ``GitHubSourceCode/``.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import sympy as sp

from data.synthetic_grn import add_gaussian_noise

GNW_SOURCE_COMMIT = "5016f55ab04c111f29d7d0b3a4881d4725d49467"
VARIANT_SEED = 20260812
N_VARIANTS_PER_FAMILY = 30
FAMILY_IDS = ("G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08")
ALLOWED_HILL_N = (1, 2, 3, 4, 5)
TARGET_VARIABLE = "x_1"
WEAK_ACTIVATION = 0.25
MAIN_TRAIN_VARIANTS = tuple(range(18))
MAIN_VAL_VARIANTS = tuple(range(18, 24))
MAIN_TEST_VARIANTS = tuple(range(24, 30))
STRUCTURE_TRAIN_FAMILIES = ("G01", "G02", "G03", "G04", "G05")
STRUCTURE_VAL_FAMILIES = ("G06",)
STRUCTURE_TEST_FAMILIES = ("G07", "G08")

_X_SYMBOL = re.compile(r"^x_(\d+)$")


@dataclass(frozen=True)
class RegulatoryModuleSpec:
    """One GNW regulatory module."""

    is_enhancer: bool
    binds_as_complex: bool
    activators: tuple[str, ...]
    deactivators: tuple[str, ...]


@dataclass(frozen=True)
class FamilySpec:
    family_id: str
    template_id: str
    description: str
    oracle_regulators: tuple[str, ...]
    modules: tuple[RegulatoryModuleSpec, ...]


# Algebraic templates. Sign / module polarity differences keep distinct family_ids.
ALGEBRAIC_TEMPLATE_IDS = {
    "G01": "T01_basal",
    "G02": "T02_single_regulator",
    "G03": "T02_single_regulator",
    "G04": "T04_two_independent_activators",
    "G05": "T05_two_complex_activators",
    "G06": "T06_activator_deactivator",
    "G07": "T07_two_module_mixture",
    "G08": "T07_two_module_mixture",
}


def algebraic_template_id(family_id: str) -> str:
    if family_id not in ALGEBRAIC_TEMPLATE_IDS:
        raise KeyError(f"unknown family {family_id}")
    return ALGEBRAIC_TEMPLATE_IDS[family_id]


FAMILY_SPECS: dict[str, FamilySpec] = {
    "G01": FamilySpec(
        family_id="G01",
        template_id=ALGEBRAIC_TEMPLATE_IDS["G01"],
        description="no inputs; basal transcription and mRNA degradation",
        oracle_regulators=(),
        modules=(),
    ),
    "G02": FamilySpec(
        family_id="G02",
        template_id=ALGEBRAIC_TEMPLATE_IDS["G02"],
        description="single activator",
        oracle_regulators=("x_2",),
        modules=(
            RegulatoryModuleSpec(
                is_enhancer=True,
                binds_as_complex=False,
                activators=("x_2",),
                deactivators=(),
            ),
        ),
    ),
    "G03": FamilySpec(
        family_id="G03",
        template_id=ALGEBRAIC_TEMPLATE_IDS["G03"],
        description="single repressor",
        oracle_regulators=("x_2",),
        modules=(
            RegulatoryModuleSpec(
                is_enhancer=False,
                binds_as_complex=False,
                activators=("x_2",),
                deactivators=(),
            ),
        ),
    ),
    "G04": FamilySpec(
        family_id="G04",
        template_id=ALGEBRAIC_TEMPLATE_IDS["G04"],
        description="two activators, independent binding",
        oracle_regulators=("x_2", "x_3"),
        modules=(
            RegulatoryModuleSpec(
                is_enhancer=True,
                binds_as_complex=False,
                activators=("x_2", "x_3"),
                deactivators=(),
            ),
        ),
    ),
    "G05": FamilySpec(
        family_id="G05",
        template_id=ALGEBRAIC_TEMPLATE_IDS["G05"],
        description="two activators, complex binding",
        oracle_regulators=("x_2", "x_3"),
        modules=(
            RegulatoryModuleSpec(
                is_enhancer=True,
                binds_as_complex=True,
                activators=("x_2", "x_3"),
                deactivators=(),
            ),
        ),
    ),
    "G06": FamilySpec(
        family_id="G06",
        template_id=ALGEBRAIC_TEMPLATE_IDS["G06"],
        description="activator plus deactivator, independent binding",
        oracle_regulators=("x_2", "x_3"),
        modules=(
            RegulatoryModuleSpec(
                is_enhancer=True,
                binds_as_complex=False,
                activators=("x_2",),
                deactivators=("x_3",),
            ),
        ),
    ),
    "G07": FamilySpec(
        family_id="G07",
        template_id=ALGEBRAIC_TEMPLATE_IDS["G07"],
        description="enhancer module plus repressor module",
        oracle_regulators=("x_2", "x_3"),
        modules=(
            RegulatoryModuleSpec(
                is_enhancer=True,
                binds_as_complex=False,
                activators=("x_2",),
                deactivators=(),
            ),
            RegulatoryModuleSpec(
                is_enhancer=False,
                binds_as_complex=False,
                activators=("x_3",),
                deactivators=(),
            ),
        ),
    ),
    "G08": FamilySpec(
        family_id="G08",
        template_id=ALGEBRAIC_TEMPLATE_IDS["G08"],
        description="two independent enhancer modules",
        oracle_regulators=("x_2", "x_3"),
        modules=(
            RegulatoryModuleSpec(
                is_enhancer=True,
                binds_as_complex=False,
                activators=("x_2",),
                deactivators=(),
            ),
            RegulatoryModuleSpec(
                is_enhancer=True,
                binds_as_complex=False,
                activators=("x_3",),
                deactivators=(),
            ),
        ),
    ),
}


@dataclass
class GnwProblemSpec:
    """One GNW parameter variant before point sampling."""

    eq_id: str
    family_id: str
    variant_index: int
    main_split: str
    structure_split: str
    target_variable: str
    oracle_regulators: list[str]
    oracle_inputs: list[str]
    variable_order: list[str]
    parameters: dict[str, Any]
    template_id: str
    raw_gnw_formula: str
    substituted_formula: str
    canonical_expr: str
    skeleton_expr: str
    oracle_source_equation_id: str
    gnw_source_commit: str = GNW_SOURCE_COMMIT
    variant_seed: int = VARIANT_SEED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GnwSampledProblem:
    """Sampled analytic points for one problem, one data seed, and one noise."""

    spec: GnwProblemSpec
    data_seed: int
    noise: float
    X_train: np.ndarray
    y_train_clean: np.ndarray
    y_train: np.ndarray
    X_id: np.ndarray
    y_id: np.ndarray
    X_ood: np.ndarray
    y_ood: np.ndarray
    noise_std: float
    sy_train: float
    support_id: tuple[float, float]
    support_ood: tuple[float, float]

    def to_manifest_row(self) -> dict[str, Any]:
        row = self.spec.to_dict()
        row.update(
            {
                "data_seed": int(self.data_seed),
                "noise": float(self.noise),
                "noise_std": float(self.noise_std),
                "sy_train": float(self.sy_train),
                "n_train": int(self.X_train.shape[0]),
                "n_id": int(self.X_id.shape[0]),
                "n_ood": int(self.X_ood.shape[0]),
                "support_id": list(self.support_id),
                "support_ood": list(self.support_ood),
                "X_train_sha256": _array_fingerprint(self.X_train),
                "y_train_clean_sha256": _array_fingerprint(self.y_train_clean),
                "y_train_sha256": _array_fingerprint(self.y_train),
                "X_id_sha256": _array_fingerprint(self.X_id),
                "y_id_sha256": _array_fingerprint(self.y_id),
                "X_ood_sha256": _array_fingerprint(self.X_ood),
                "y_ood_sha256": _array_fingerprint(self.y_ood),
            }
        )
        return row


def latin_hypercube(
    n_points: int,
    low: Sequence[float],
    high: Sequence[float],
    rng: np.random.Generator,
) -> np.ndarray:
    """Latin hypercube sample in a box. Does not share points across calls."""
    if n_points <= 0:
        raise ValueError("n_points must be positive")
    low_a = np.asarray(low, dtype=float)
    high_a = np.asarray(high, dtype=float)
    if low_a.shape != high_a.shape or low_a.ndim != 1:
        raise ValueError("low and high must be 1D sequences of the same length")
    n_dim = low_a.size
    cut = np.linspace(0.0, 1.0, n_points + 1)
    u = rng.uniform(cut[:-1], cut[1:], size=(n_dim, n_points))
    for dim in range(n_dim):
        rng.shuffle(u[dim])
    return (low_a + u.T * (high_a - low_a)).astype(np.float64)


def module_activation(
    concentrations: Mapping[str, float | np.ndarray] | Sequence[float],
    *,
    activators: Sequence[str] | Sequence[float],
    deactivators: Sequence[str] | Sequence[float],
    k: Mapping[str, float] | Sequence[float],
    n: Mapping[str, float] | Sequence[float],
    binds_as_complex: bool,
) -> float | np.ndarray:
    """GNW ``RegulatoryModule.computeActivation``.

    Independent binding::

        m = prod_{r in A} xi_r / prod_{r in A∪D} (1 + xi_r)

    Complex binding::

        m = prod_{r in A} xi_r / (1 + prod_{r in A} xi_r
            + 1_{|D|>0} prod_{r in A∪D} xi_r)

    where ``xi_r = (x_r / K_r)^{n_r}``.
    """
    if isinstance(concentrations, Mapping):
        names = list(activators) + list(deactivators)
        xs = [_as_array(concentrations[name]) for name in names]
        ks = [_as_array(k[name]) for name in names]  # type: ignore[index]
        ns = [_as_array(n[name]) for name in names]  # type: ignore[index]
        n_act = len(activators)
    else:
        xs = [_as_array(v) for v in concentrations]
        ks = [_as_array(v) for v in k]  # type: ignore[arg-type]
        ns = [_as_array(v) for v in n]  # type: ignore[arg-type]
        n_act = len(activators)
    xi = [(x / k_i) ** n_i for x, k_i, n_i in zip(xs, ks, ns)]
    numerator = np.ones_like(xi[0], dtype=float) if xi else np.array(1.0)
    for value in xi[:n_act]:
        numerator = numerator * value
    if binds_as_complex:
        denominator = 1.0 + numerator
        if len(xi) > n_act:
            all_inputs = numerator.copy()
            for value in xi[n_act:]:
                all_inputs = all_inputs * value
            denominator = denominator + all_inputs
    else:
        denominator = np.ones_like(numerator, dtype=float)
        for value in xi:
            denominator = denominator * (1.0 + value)
        if not xi:
            denominator = np.array(1.0)
    activation = numerator / denominator
    if np.ndim(activation) == 0:
        return float(activation)
    return activation


def mix_module_states(
    activations: Sequence[float | np.ndarray],
    alphas: Sequence[float],
) -> float | np.ndarray:
    """GNW state mixture ``alpha_i(m) = sum_s alpha_s prod_j m_j^{s_j}(1-m_j)^{1-s_j}``."""
    n_modules = len(activations)
    n_states = 1 << n_modules
    if len(alphas) != n_states:
        raise ValueError(f"expected {n_states} alpha values, got {len(alphas)}")
    m = [_as_array(v) for v in activations]
    out = np.zeros_like(m[0] if m else np.array(1.0), dtype=float)
    for state, alpha in enumerate(alphas):
        term = np.ones_like(out, dtype=float) * float(alpha)
        for j, mj in enumerate(m):
            active = (state >> j) & 1
            term = term * (mj if active else (1.0 - mj))
        out = out + term
    if np.ndim(out) == 0:
        return float(out)
    return out


def hill_xi(x: np.ndarray | float, k: float, n: int) -> np.ndarray | float:
    return (np.asarray(x, dtype=float) / float(k)) ** int(n)


def evaluate_family(
    family_id: str,
    X: np.ndarray,
    parameters: Mapping[str, Any],
) -> np.ndarray:
    """Evaluate analytic mRNA RHS ``V * alpha(m) - delta * x_1`` on oracle columns."""
    spec = FAMILY_SPECS[family_id]
    X = np.asarray(X, dtype=float)
    columns = {name: X[:, i] for i, name in enumerate(oracle_inputs_for(spec))}
    x1 = columns[TARGET_VARIABLE]
    v = float(parameters["V"])
    delta = float(parameters["delta"])
    activations = []
    for index, module in enumerate(spec.modules):
        k_map = {name: float(parameters[f"K_{name}"]) for name in (*module.activators, *module.deactivators)}
        n_map = {name: int(parameters[f"n_{name}"]) for name in (*module.activators, *module.deactivators)}
        activations.append(
            module_activation(
                columns,
                activators=module.activators,
                deactivators=module.deactivators,
                k=k_map,
                n=n_map,
                binds_as_complex=module.binds_as_complex,
            )
        )
    alphas = list(parameters["alpha"])
    relative = mix_module_states(activations, alphas) if spec.modules else float(alphas[0])
    return np.asarray(v * relative - delta * x1, dtype=float).ravel()


def oracle_inputs_for(spec: FamilySpec) -> list[str]:
    regulators = sorted(spec.oracle_regulators, key=_gene_id)
    return [TARGET_VARIABLE, *regulators]


def oracle_metadata_from_expression(
    canonical_expr: str,
    *,
    target_variable: str = TARGET_VARIABLE,
    family_regulators: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Extract oracle variables from a simplified SymPy expression.

    A variable is included only if it remains a free symbol after canonical
    simplification. ``x_i`` itself is always an input even if a degenerate
    simplification dropped the degradation term.
    """
    parsed = sp.sympify(canonical_expr)
    free = {str(symbol) for symbol in parsed.free_symbols}
    present = sorted((name for name in free if _X_SYMBOL.match(name)), key=_gene_id)
    regulators = [name for name in present if name != target_variable]
    if family_regulators is not None:
        expected = sorted(family_regulators, key=_gene_id)
        extra = [name for name in regulators if name not in expected]
        if extra:
            raise RuntimeError(
                f"canonical expression introduced unexpected regulators {extra}: {canonical_expr}"
            )
        # Coefficients that cancelled a regulator are dropped, as required.
    inputs = [target_variable, *regulators]
    return {
        "target_variable": target_variable,
        "oracle_regulators": regulators,
        "oracle_inputs": inputs,
        "variable_order": inputs,
    }


def main_split_for_variant(variant_index: int) -> str:
    if variant_index in MAIN_TRAIN_VARIANTS:
        return "train"
    if variant_index in MAIN_VAL_VARIANTS:
        return "validation"
    if variant_index in MAIN_TEST_VARIANTS:
        return "test"
    raise ValueError(f"variant_index out of range: {variant_index}")


def structure_split_for_family(family_id: str) -> str:
    if family_id in STRUCTURE_TRAIN_FAMILIES:
        return "train"
    if family_id in STRUCTURE_VAL_FAMILIES:
        return "validation"
    if family_id in STRUCTURE_TEST_FAMILIES:
        return "test"
    raise KeyError(f"unknown family {family_id}")


def structure_regime_for(view: str, family_id: str) -> str:
    """``id`` / ``ood`` relative to the active split view, not a bare 'OOD' label."""
    if view == "main":
        return "id"
    if view == "structure_holdout":
        return "ood" if family_id in STRUCTURE_TEST_FAMILIES else "id"
    raise ValueError(f"unknown split view {view!r}")


def define_gnw_problems(
    *,
    n_variants_per_family: int = N_VARIANTS_PER_FAMILY,
    variant_seed: int = VARIANT_SEED,
    family_ids: Sequence[str] = FAMILY_IDS,
) -> list[GnwProblemSpec]:
    """Create the fixed 240-problem (default) GNW v1 catalogue without sampling X."""
    if n_variants_per_family < 1:
        raise ValueError("n_variants_per_family must be >= 1")
    rng = np.random.default_rng(int(variant_seed))
    problems: list[GnwProblemSpec] = []
    for family_id in family_ids:
        family = FAMILY_SPECS[family_id]
        for variant_index in range(n_variants_per_family):
            parameters = sample_family_parameters(family, rng)
            formulas = build_family_formulas(family, parameters)
            oracle = oracle_metadata_from_expression(
                formulas["canonical_expr"],
                family_regulators=family.oracle_regulators,
            )
            # Self variable is always an input, even if a regulator cancelled.
            if oracle["target_variable"] not in oracle["oracle_inputs"]:
                oracle["oracle_inputs"] = [TARGET_VARIABLE, *oracle["oracle_regulators"]]
                oracle["variable_order"] = list(oracle["oracle_inputs"])
            eq_id = f"{family_id}_variant_{variant_index:03d}"
            problems.append(
                GnwProblemSpec(
                    eq_id=eq_id,
                    family_id=family_id,
                    variant_index=variant_index,
                    main_split=main_split_for_variant(variant_index)
                    if n_variants_per_family == N_VARIANTS_PER_FAMILY
                    else _scaled_main_split(variant_index, n_variants_per_family),
                    structure_split=structure_split_for_family(family_id),
                    target_variable=oracle["target_variable"],
                    oracle_regulators=list(oracle["oracle_regulators"]),
                    oracle_inputs=list(oracle["oracle_inputs"]),
                    variable_order=list(oracle["variable_order"]),
                    parameters=_jsonable_parameters(parameters),
                    template_id=family.template_id,
                    raw_gnw_formula=formulas["raw_gnw_formula"],
                    substituted_formula=formulas["substituted_formula"],
                    canonical_expr=formulas["canonical_expr"],
                    skeleton_expr=formulas["skeleton_expr"],
                    oracle_source_equation_id=eq_id,
                    variant_seed=int(variant_seed),
                )
            )
    return problems


def sample_family_parameters(family: FamilySpec, rng: np.random.Generator) -> dict[str, Any]:
    """GNW half-life / K / n / alpha initialization, with n restricted to 1–5."""
    half_life = _truncated_gaussian(rng, 5.0, 50.0, 27.5, 7.5)
    delta = math.log(2.0) / half_life
    vmax = delta  # GNW non-dimensionalization: max_ = delta_
    k: dict[str, float] = {}
    n_hill: dict[str, int] = {}
    for module in family.modules:
        for name in (*module.activators, *module.deactivators):
            k[name] = float(rng.uniform(0.01, 1.0))
            n_hill[name] = _sample_restricted_hill_n(rng)
    alphas, dalpha = _initialize_alpha(family, rng)
    parameters: dict[str, Any] = {
        "half_life": float(half_life),
        "delta": float(delta),
        "V": float(vmax),
        "alpha": [float(a) for a in alphas],
        "dalpha": [float(a) for a in dalpha],
        "weak_activation": WEAK_ACTIVATION,
    }
    for name, value in k.items():
        parameters[f"K_{name}"] = float(value)
    for name, value in n_hill.items():
        parameters[f"n_{name}"] = int(value)
    parameters["modules"] = [
        {
            "is_enhancer": module.is_enhancer,
            "binds_as_complex": module.binds_as_complex,
            "activators": list(module.activators),
            "deactivators": list(module.deactivators),
        }
        for module in family.modules
    ]
    return parameters


def build_family_formulas(family: FamilySpec, parameters: Mapping[str, Any]) -> dict[str, str]:
    """Expand A/B templates into raw, substituted, and canonical SymPy strings."""
    x1, x2, x3 = sp.symbols("x_1 x_2 x_3", positive=True)
    v = sp.Symbol("V", positive=True)
    delta = sp.Symbol("delta", positive=True)
    k2, k3 = sp.symbols("K_2 K_3", positive=True)
    n2, n3 = sp.symbols("n_2 n_3", integer=True, positive=True)

    def q_symbol(x, k, n_sym, n_value: int | None = None):
        if n_value is None:
            return (x / k) ** n_sym
        if int(n_value) == 1:
            return x / k
        return (x / k) ** int(n_value)

    def h_of(q):
        return q / (1 + q)

    def A(m, a0, a1):
        return a0 * (1 - m) + a1 * m

    def B(m1, m2, a00, a10, a01, a11):
        return (
            a00 * (1 - m1) * (1 - m2)
            + a10 * m1 * (1 - m2)
            + a01 * (1 - m1) * m2
            + a11 * m1 * m2
        )

    alpha = [sp.Symbol(f"alpha_{i}") for i in range(len(parameters["alpha"]))]
    fid = family.family_id
    if fid == "G01":
        raw = v - delta * x1
    elif fid in {"G02", "G03"}:
        q2 = q_symbol(x2, k2, n2)
        raw = v * A(h_of(q2), alpha[0], alpha[1]) - delta * x1
    elif fid == "G04":
        q2 = q_symbol(x2, k2, n2)
        q3 = q_symbol(x3, k3, n3)
        m = (q2 * q3) / ((1 + q2) * (1 + q3))
        raw = v * A(m, alpha[0], alpha[1]) - delta * x1
    elif fid == "G05":
        q2 = q_symbol(x2, k2, n2)
        q3 = q_symbol(x3, k3, n3)
        m = (q2 * q3) / (1 + q2 * q3)
        raw = v * A(m, alpha[0], alpha[1]) - delta * x1
    elif fid == "G06":
        q2 = q_symbol(x2, k2, n2)
        q3 = q_symbol(x3, k3, n3)
        m = q2 / ((1 + q2) * (1 + q3))
        raw = v * A(m, alpha[0], alpha[1]) - delta * x1
    elif fid in {"G07", "G08"}:
        q2 = q_symbol(x2, k2, n2)
        q3 = q_symbol(x3, k3, n3)
        raw = v * B(h_of(q2), h_of(q3), alpha[0], alpha[1], alpha[2], alpha[3]) - delta * x1
    else:  # pragma: no cover
        raise KeyError(fid)

    subs: dict[sp.Symbol, float | int] = {
        v: float(parameters["V"]),
        delta: float(parameters["delta"]),
    }
    if "K_x_2" in parameters:
        subs[k2] = float(parameters["K_x_2"])
        subs[n2] = int(parameters["n_x_2"])
    if "K_x_3" in parameters:
        subs[k3] = float(parameters["K_x_3"])
        subs[n3] = int(parameters["n_x_3"])
    for i, value in enumerate(parameters["alpha"]):
        subs[alpha[i]] = float(value)

    # Rebuild with integer exponents after substitution for a fully numeric tree.
    # Avoid sp.simplify: G07/G08 rational trees can take unbounded time.
    numeric_raw = sp.together(_numeric_family_expression(family, parameters))
    canonical = sp.cancel(numeric_raw)
    skeleton = _to_skeleton_expr(canonical)
    return {
        "raw_gnw_formula": str(raw),
        "substituted_formula": str(numeric_raw),
        "canonical_expr": str(canonical),
        "skeleton_expr": str(skeleton),
    }


def _numeric_family_expression(family: FamilySpec, parameters: Mapping[str, Any]) -> sp.Expr:
    x1, x2, x3 = sp.symbols("x_1 x_2 x_3", positive=True)
    v = sp.Float(parameters["V"])
    delta = sp.Float(parameters["delta"])
    alphas = [sp.Float(a) for a in parameters["alpha"]]

    def q(var, name: str):
        k = sp.Float(parameters[f"K_{name}"])
        n_val = int(parameters[f"n_{name}"])
        if n_val == 1:
            return var / k
        return (var / k) ** n_val

    def h(qv):
        return qv / (1 + qv)

    def A(m, a0, a1):
        return a0 * (1 - m) + a1 * m

    def B(m1, m2, a00, a10, a01, a11):
        return (
            a00 * (1 - m1) * (1 - m2)
            + a10 * m1 * (1 - m2)
            + a01 * (1 - m1) * m2
            + a11 * m1 * m2
        )

    fid = family.family_id
    if fid == "G01":
        return v - delta * x1
    if fid in {"G02", "G03"}:
        return v * A(h(q(x2, "x_2")), alphas[0], alphas[1]) - delta * x1
    if fid == "G04":
        q2, q3 = q(x2, "x_2"), q(x3, "x_3")
        m = (q2 * q3) / ((1 + q2) * (1 + q3))
        return v * A(m, alphas[0], alphas[1]) - delta * x1
    if fid == "G05":
        q2, q3 = q(x2, "x_2"), q(x3, "x_3")
        m = (q2 * q3) / (1 + q2 * q3)
        return v * A(m, alphas[0], alphas[1]) - delta * x1
    if fid == "G06":
        q2, q3 = q(x2, "x_2"), q(x3, "x_3")
        m = q2 / ((1 + q2) * (1 + q3))
        return v * A(m, alphas[0], alphas[1]) - delta * x1
    if fid in {"G07", "G08"}:
        return (
            v
            * B(h(q(x2, "x_2")), h(q(x3, "x_3")), alphas[0], alphas[1], alphas[2], alphas[3])
            - delta * x1
        )
    raise KeyError(fid)


def sample_problem_points(
    spec: GnwProblemSpec,
    *,
    data_seed: int,
    noise: float,
    n_train: int = 1024,
    n_eval: int = 256,
    support_id: tuple[float, float] = (0.1, 2.0),
    support_ood: tuple[float, float] = (0.05, 2.5),
    paired_clean_train: tuple[np.ndarray, np.ndarray] | None = None,
    paired_id: tuple[np.ndarray, np.ndarray] | None = None,
    paired_ood: tuple[np.ndarray, np.ndarray] | None = None,
) -> GnwSampledProblem:
    """Sample LHS points and analytic targets. Noise 0.0/0.1 share clean X."""
    if noise not in (0.0, 0.1) and noise != 0:
        # Allow tiny smoke noises in tests, but keep the production pair explicit.
        if noise < 0:
            raise ValueError("noise must be non-negative")
    n_vars = len(spec.oracle_inputs)
    rng = np.random.default_rng(_point_seed(data_seed, spec.eq_id, "design"))
    if paired_clean_train is None:
        X_train = latin_hypercube(n_train, [support_id[0]] * n_vars, [support_id[1]] * n_vars, rng)
        y_train_clean = evaluate_family(spec.family_id, X_train, spec.parameters)
    else:
        X_train, y_train_clean = paired_clean_train
        X_train = np.asarray(X_train, dtype=float)
        y_train_clean = np.asarray(y_train_clean, dtype=float).ravel()
    if paired_id is None:
        rng_id = np.random.default_rng(_point_seed(data_seed, spec.eq_id, "id"))
        X_id = latin_hypercube(n_eval, [support_id[0]] * n_vars, [support_id[1]] * n_vars, rng_id)
        y_id = evaluate_family(spec.family_id, X_id, spec.parameters)
    else:
        X_id, y_id = paired_id
        X_id = np.asarray(X_id, dtype=float)
        y_id = np.asarray(y_id, dtype=float).ravel()
    if paired_ood is None:
        rng_ood = np.random.default_rng(_point_seed(data_seed, spec.eq_id, "ood"))
        X_ood = latin_hypercube(n_eval, [support_ood[0]] * n_vars, [support_ood[1]] * n_vars, rng_ood)
        y_ood = evaluate_family(spec.family_id, X_ood, spec.parameters)
    else:
        X_ood, y_ood = paired_ood
        X_ood = np.asarray(X_ood, dtype=float)
        y_ood = np.asarray(y_ood, dtype=float).ravel()

    sy_train = float(np.std(y_train_clean))
    noise_rng = np.random.default_rng(_point_seed(data_seed, spec.eq_id, "noise"))
    if float(noise) == 0.0:
        y_train = y_train_clean.copy()
        noise_std = 0.0
    else:
        y_train = add_gaussian_noise(y_train_clean, float(noise), noise_rng)
        noise_std = float(noise) * (sy_train + 1e-8)
    return GnwSampledProblem(
        spec=spec,
        data_seed=int(data_seed),
        noise=float(noise),
        X_train=X_train,
        y_train_clean=y_train_clean,
        y_train=y_train,
        X_id=X_id,
        y_id=y_id,
        X_ood=X_ood,
        y_ood=y_ood,
        noise_std=noise_std,
        sy_train=sy_train,
        support_id=(float(support_id[0]), float(support_id[1])),
        support_ood=(float(support_ood[0]), float(support_ood[1])),
    )


def build_paired_noise_problems(
    specs: Sequence[GnwProblemSpec],
    *,
    data_seed: int,
    noises: Sequence[float] = (0.0, 0.1),
    n_train: int = 1024,
    n_eval: int = 256,
    support_id: tuple[float, float] = (0.1, 2.0),
    support_ood: tuple[float, float] = (0.05, 2.5),
) -> list[GnwSampledProblem]:
    """Share clean X across noise conditions; only epsilon changes."""
    sampled: list[GnwSampledProblem] = []
    for spec in specs:
        clean = sample_problem_points(
            spec,
            data_seed=data_seed,
            noise=0.0,
            n_train=n_train,
            n_eval=n_eval,
            support_id=support_id,
            support_ood=support_ood,
        )
        for noise in noises:
            if float(noise) == 0.0:
                sampled.append(clean)
                continue
            sampled.append(
                sample_problem_points(
                    spec,
                    data_seed=data_seed,
                    noise=float(noise),
                    n_train=n_train,
                    n_eval=n_eval,
                    support_id=support_id,
                    support_ood=support_ood,
                    paired_clean_train=(clean.X_train, clean.y_train_clean),
                    paired_id=(clean.X_id, clean.y_id),
                    paired_ood=(clean.X_ood, clean.y_ood),
                )
            )
    return sampled


def filter_by_main_split(specs: Sequence[GnwProblemSpec], split: str) -> list[GnwProblemSpec]:
    return [spec for spec in specs if spec.main_split == split]


def filter_by_structure_split(specs: Sequence[GnwProblemSpec], split: str) -> list[GnwProblemSpec]:
    return [spec for spec in specs if spec.structure_split == split]


def phase4_validation_panel(
    specs: Sequence[GnwProblemSpec],
    *,
    per_family: int = 2,
) -> list[GnwProblemSpec]:
    """Smallest ``per_family`` validation variants per family, before any prediction."""
    by_family: dict[str, list[GnwProblemSpec]] = {fid: [] for fid in FAMILY_IDS}
    for spec in specs:
        if spec.main_split != "validation":
            continue
        by_family.setdefault(spec.family_id, []).append(spec)
    panel: list[GnwProblemSpec] = []
    for family_id in FAMILY_IDS:
        members = sorted(by_family.get(family_id, []), key=lambda item: item.variant_index)
        panel.extend(members[:per_family])
    return panel


def save_problem_npz(problem: GnwSampledProblem, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        X_train=problem.X_train,
        y_train=problem.y_train,
        y_train_clean=problem.y_train_clean,
        X_id=problem.X_id,
        y_id=problem.y_id,
        X_ood=problem.X_ood,
        y_ood=problem.y_ood,
        meta=np.array(problem.to_manifest_row()),
    )
    return path


def to_sampled_dataset(
    problem: "GnwSampledProblem",
    *,
    xy: str = "train",
) -> "SampledDataset":
    """Wrap a GNW sampled problem as the existing fine-tune ``SampledDataset``."""
    from data.synthetic_grn import EquationSpec, SampledDataset

    if xy == "train":
        X, y = problem.X_train, problem.y_train
    elif xy in {"id", "domain_id"}:
        X, y = problem.X_id, problem.y_id
    elif xy in {"ood", "domain_ood"}:
        X, y = problem.X_ood, problem.y_ood
    else:
        raise ValueError(f"xy must be train/id/ood, got {xy!r}")
    return SampledDataset(
        spec=EquationSpec(
            eq_id=problem.spec.eq_id,
            family=problem.spec.family_id,
            target_expr=problem.spec.canonical_expr,
            variable_names=list(problem.spec.oracle_inputs),
            parameters={"noise": float(problem.noise)},
            split=problem.spec.main_split,
            motif=problem.spec.canonical_expr,
        ),
        X=np.asarray(X, dtype=float),
        y=np.asarray(y, dtype=float).ravel(),
        noise_std=float(problem.noise_std),
    )


def sampled_dataset_from_npz(path: Path, *, xy: str = "train") -> "SampledDataset":
    """Load one Phase-1 GNW npz as ``SampledDataset`` for NeSymReS fine-tuning."""
    from data.synthetic_grn import EquationSpec, SampledDataset

    payload = load_problem_npz(path)
    meta = payload["meta"]
    if xy == "train":
        X, y = payload["X_train"], payload["y_train"]
    elif xy in {"id", "domain_id"}:
        X, y = payload["X_id"], payload["y_id"]
    elif xy in {"ood", "domain_ood"}:
        X, y = payload["X_ood"], payload["y_ood"]
    else:
        raise ValueError(f"xy must be train/id/ood, got {xy!r}")
    return SampledDataset(
        spec=EquationSpec(
            eq_id=str(meta["eq_id"]),
            family=str(meta["family_id"]),
            target_expr=str(meta.get("canonical_expr") or ""),
            variable_names=list(meta["oracle_inputs"]),
            parameters={"noise": float(meta.get("noise", 0.0))},
            split=str(meta.get("main_split") or "train"),
            motif=str(meta.get("canonical_expr") or ""),
        ),
        X=np.asarray(X, dtype=float),
        y=np.asarray(y, dtype=float).ravel(),
        noise_std=float(meta.get("noise_std", 0.0)),
    )


def load_problem_npz(path: Path) -> dict[str, Any]:
    data = np.load(path, allow_pickle=True)
    meta_raw = data["meta"]
    meta = meta_raw.item() if getattr(meta_raw, "ndim", 0) == 0 else meta_raw
    if isinstance(meta, bytes):
        meta = meta.decode("utf-8")
    if isinstance(meta, str):
        import json

        meta = json.loads(meta)
    return {
        "X_train": data["X_train"],
        "y_train": data["y_train"],
        "y_train_clean": data["y_train_clean"],
        "X_id": data["X_id"],
        "y_id": data["y_id"],
        "X_ood": data["X_ood"],
        "y_ood": data["y_ood"],
        "meta": dict(meta),
    }


def catalogue_fingerprint(specs: Sequence[GnwProblemSpec]) -> str:
    from gpu_run2_runtime import fingerprint_json

    payload = [spec.to_dict() for spec in specs]
    return fingerprint_json(payload)


def _initialize_alpha(
    family: FamilySpec, rng: np.random.Generator
) -> tuple[list[float], list[float]]:
    """Port of ``HillGene.randomInitializationOfAlpha``."""
    n_modules = len(family.modules)
    n_states = 1 << n_modules
    dalpha = []
    for module in family.modules:
        value = _truncated_gaussian(rng, WEAK_ACTIVATION, 1.0, 0.625, 0.125)
        if not module.is_enhancer:
            value *= -1.0
        dalpha.append(value)
    max_pos = sum(v for v in dalpha if v > 0)
    max_neg = sum(v for v in dalpha if v < 0)
    if n_modules == 0 or max_pos == 0:
        alpha0 = 1.0
    elif max_neg == 0:
        alpha0 = _low_basal(rng)
    else:
        alpha0 = _truncated_gaussian(rng, WEAK_ACTIVATION, 1.0 - WEAK_ACTIVATION, 0.5, 1.0 / 12.0)

    dalpha = list(dalpha)
    if max_pos > 0 and alpha0 + max_pos < 1.0:
        positive = [(i, v) for i, v in enumerate(dalpha) if v > 0]
        index, _ = min(positive, key=lambda item: item[1])
        dalpha[index] += 1.0 - alpha0 - max_pos
        max_pos = sum(v for v in dalpha if v > 0)
    if max_neg < 0 and alpha0 + max_neg > WEAK_ACTIVATION:
        negative = [(i, v) for i, v in enumerate(dalpha) if v < 0]
        index, _ = max(negative, key=lambda item: item[1])
        dalpha[index] += -alpha0 - max_neg + _low_basal(rng)

    alphas = [0.0] * n_states
    alphas[0] = float(np.clip(alpha0, 0.0, 1.0))
    for state in range(1, n_states):
        value = alphas[0]
        for j, delta_a in enumerate(dalpha):
            if (state >> j) & 1:
                value += delta_a
        alphas[state] = float(np.clip(value, 0.0, 1.0))
    return alphas, dalpha


def _low_basal(rng: np.random.Generator) -> float:
    return float(np.clip(rng.normal(0.0, 0.05), 0.0, WEAK_ACTIVATION))


def _sample_restricted_hill_n(rng: np.random.Generator) -> int:
    """GNW n ~ truncated N(2, 2^2) on [1, 10], then snap to {1,2,3,4,5}."""
    value = _truncated_gaussian(rng, 1.0, 10.0, 2.0, 2.0)
    return int(np.clip(round(value), 1, 5))


def _truncated_gaussian(
    rng: np.random.Generator, low: float, high: float, mean: float, stdev: float
) -> float:
    for _ in range(10000):
        value = float(rng.normal(mean, stdev))
        if low <= value <= high:
            return value
    return float(np.clip(mean, low, high))


def _gene_id(name: str) -> int:
    match = _X_SYMBOL.match(name)
    if not match:
        raise ValueError(f"not a gene variable: {name}")
    return int(match.group(1))


def _as_array(value: float | np.ndarray) -> np.ndarray:
    return np.asarray(value, dtype=float)


def _point_seed(data_seed: int, eq_id: str, tag: str) -> int:
    # Deterministic 31-bit seed from data seed + problem + stream tag.
    payload = f"{data_seed}:{eq_id}:{tag}".encode("utf-8")
    import hashlib

    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:4], "little") & 0x7FFFFFFF


def _array_fingerprint(array: np.ndarray) -> str:
    import hashlib

    data = np.ascontiguousarray(array).astype(np.float64)
    return hashlib.sha256(data.tobytes()).hexdigest()


def _jsonable_parameters(parameters: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in parameters.items():
        if isinstance(value, (np.floating, float)):
            out[key] = float(value)
        elif isinstance(value, (np.integer, int)):
            out[key] = int(value)
        else:
            out[key] = value
    return out


def _to_skeleton_expr(expr: sp.Expr) -> sp.Expr:
    """Replace continuous coefficients with ``c``; keep integer Pow exponents and 0/1."""
    placeholder = sp.Symbol("c")

    def rec(node: sp.Expr) -> sp.Expr:
        if isinstance(node, sp.Pow):
            exponent = node.exp
            if exponent.is_Integer:
                return sp.Pow(rec(node.base), exponent)
            return sp.Pow(rec(node.base), rec(exponent))
        if isinstance(node, sp.Number):
            if node in (0, 1, -1):
                return node
            return placeholder
        if node.args:
            return node.func(*(rec(arg) for arg in node.args))
        return node

    return rec(expr)


def _scaled_main_split(variant_index: int, n_variants: int) -> str:
    """For catalogues smaller than 30 variants, keep an 18:6:6-like ratio.

    Smoke must use ``n_variants >= 3`` so each family has train/validation/test.
    Smaller catalogues are allowed for unit tests that only need formulas; they
    put every variant in train.
    """
    if n_variants < 3:
        return "train"
    n_train = max(1, round(n_variants * 18 / 30))
    n_val = max(1, round(n_variants * 6 / 30))
    n_test = n_variants - n_train - n_val
    if n_test < 1 or n_train < 1 or n_val < 1:
        # Deterministic fallback (e.g. n_variants == 3): 1/1/1.
        n_train, n_val = 1, 1
        n_test = n_variants - 2
    if variant_index < n_train:
        return "train"
    if variant_index < n_train + n_val:
        return "validation"
    return "test"
