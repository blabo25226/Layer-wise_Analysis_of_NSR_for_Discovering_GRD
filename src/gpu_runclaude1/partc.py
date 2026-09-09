"""Part C support: payload identity, re-encoding audit, and the E2/E3 discriminator (v2 §8.2, §8.3).

GPU forward passes themselves go through
``gpu_run4.training.teacher_forced_summed_logprob`` (additive, beside
``teacher_forcing_loss``); this module holds the CPU-only, torch-free pieces:
the conditioning-identity digest, the cell-identity assertions, the
normalized re-encoding audit, and the paired Stahlberg-Byrne indicator.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from typing import Any, Optional, Sequence

import numpy as np

from gpu_runclaude1.constants import N_DISTINCT_PAYLOADS_PER_SYSTEM, N_CELLS_PER_SYSTEM

_SEPARATOR_PATTERN = "|"
_SEPARATOR_REPLACEMENT = ",|,"


def cell_input_payload_sha256(times: Sequence[float], observed_trajectory: Sequence, initial_condition: Sequence[float]) -> str:
    """SHA256 over the float64 little-endian bytes of the exact arrays passed
    to ``_point_bag``, concatenated ``times || observed_trajectory ||
    initial_condition``, each preceded by its shape as little-endian int64
    (v2 §8.2 step 1a). A digest of the object actually used, not of a
    filename or a checksum computed upstream of the corruption pipeline.
    """
    digest = hashlib.sha256()
    for array in (times, observed_trajectory, initial_condition):
        arr = np.asarray(array, dtype=np.float64)
        digest.update(struct.pack("<q", arr.ndim))
        for dim in arr.shape:
            digest.update(struct.pack("<q", int(dim)))
        digest.update(arr.tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True)
class CellIdentityCheck:
    ok: bool
    failure_reason: Optional[str]
    payload_sha256: Optional[str]


def verify_cell_identity(cell: dict[str, Any]) -> CellIdentityCheck:
    """v2 §8.2 step 1b: assert the record's parsed identity fields agree with
    the values encoded in its own ``cell_id``, and that ``candidate_set_hash``
    / ``cache_identity`` are present. Any failure -> ``CellIdentityMismatch``,
    excluded and counted, never silently dropped.
    """
    cell_id = str(cell.get("cell_id", ""))
    parts = cell_id.split("_")
    # cell_id format: "<family>_validation_d<seed>_<variant>_b<bundle>_n<noise>_r<rho>"
    try:
        bundle_token = next(p for p in parts if p.startswith("b") and p[1:].isdigit())
        bundle_index_from_id = int(bundle_token[1:])
    except StopIteration:
        return CellIdentityCheck(False, "CellIdentityMismatch", None)
    if int(cell.get("bundle_index", -1)) != bundle_index_from_id:
        return CellIdentityCheck(False, "CellIdentityMismatch", None)
    if not cell.get("candidate_set_hash"):
        return CellIdentityCheck(False, "CellIdentityMismatch", None)
    if not cell.get("cache_identity"):
        return CellIdentityCheck(False, "CellIdentityMismatch", None)
    input_obs = (cell.get("observations") or {}).get("input") or []
    if not input_obs:
        return CellIdentityCheck(False, "CellIdentityMismatch", None)
    payload = input_obs[0]
    try:
        digest = cell_input_payload_sha256(
            payload["times"], payload["observed_trajectory"], payload["initial_condition"]
        )
    except (KeyError, TypeError, ValueError):
        return CellIdentityCheck(False, "CellIdentityMismatch", None)
    return CellIdentityCheck(True, None, digest)


def check_distinct_payload_count(payload_hashes_by_system: dict[str, set[str]]) -> dict[str, dict[str, Any]]:
    """v2 §8.2 step 1c: exactly 10 distinct payload digests per system (P11);
    12 or 1 indicates a cell mixup or a stale cache.
    """
    out = {}
    for system_id, hashes in payload_hashes_by_system.items():
        n_distinct = len(hashes)
        out[system_id] = {
            "n_distinct_payloads": n_distinct,
            "ok": n_distinct == N_DISTINCT_PAYLOADS_PER_SYSTEM,
        }
    return out


def normalize_prefix_separator(text: str) -> str:
    """v2 §8.2 step 4: the frozen ``|`` <-> ``,|,`` normalization before any
    re-encoding round-trip comparison. Unnormalized, raw prefix round-trip
    equality is 20/80 (1-D systems only); normalized, 80/80 (Q8).
    """
    if _SEPARATOR_REPLACEMENT in text:
        return text
    return text.replace(_SEPARATOR_PATTERN, _SEPARATOR_REPLACEMENT)


@dataclass(frozen=True)
class ReencodingAuditResult:
    exact: bool
    failure_reason: Optional[str]


def audit_reencoding_roundtrip(reencoded_canonical: str, stored_canonical: str) -> ReencodingAuditResult:
    normalized_reencoded = normalize_prefix_separator(reencoded_canonical)
    normalized_stored = normalize_prefix_separator(stored_canonical)
    if normalized_reencoded == normalized_stored:
        return ReencodingAuditResult(True, None)
    return ReencodingAuditResult(False, "CandidateReencodingMismatch")


@dataclass(frozen=True)
class StahlbergByrneResult:
    lp_gt: float
    lp_sel: float
    lp_best: float
    sb_sel: int
    sb_best: int


def stahlberg_byrne_indicator(lp_gt: float, lp_sel: float, lp_best: float) -> StahlbergByrneResult:
    """The paired Stahlberg-Byrne discriminator (v2 §8.3, DOI
    10.18653/v1/D19-1331): the model preferred the truth over what search
    actually returned iff ``lp_gt > lp_sel``.
    """
    return StahlbergByrneResult(
        lp_gt=lp_gt,
        lp_sel=lp_sel,
        lp_best=lp_best,
        sb_sel=int(lp_gt > lp_sel),
        sb_best=int(lp_gt > lp_best),
    )


def system_attribution(sb_rate: float) -> dict[str, bool]:
    """``E3_system(s) = 1[sb_rate >= 0.5]``; ``E2_system(s) = 1[sb_rate == 0]`` (v2 §8.3)."""
    return {"E3_system": sb_rate >= 0.5, "E2_system": sb_rate == 0.0}


# Token-class taxonomy for C2-S5 (v2 §8.3): "operator, mantissa, exponent,
# the `|` separator". The frozen text names exactly these four classes but
# does not give a vocabulary mapping; this classifier is grounded in the
# model's own emitted vocabulary (odeformer.envs.encoders.FloatSequences /
# ConstantEncoder), inspected directly against a real decoded token stream
# (v2 §8.2 step 1's `tree_encoded`, e.g. "add", "+", "N1954", "E-4", "x_0",
# "INT-", "1"): a float leaf is always the triple (sign, mantissa, exponent).
# Sign and mantissa are grouped as "mantissa" (both carry the token's
# magnitude, as opposed to "exponent"); this grouping choice is recorded
# here, not silently assumed, since the frozen text does not itself split
# out a fifth "sign" class. Anything not numeric or the separator --
# operators, variables (`x_0`, ...), and the leaf `y` -- falls to
# "operator", the frozen taxonomy's catch-all for structural/non-numeric
# tokens.
def classify_token_class(token: str) -> str:
    """One of ``"separator"``, ``"mantissa"``, ``"exponent"``, ``"operator"``
    for a single decoded vocabulary token string (v2 §8.3 C2-S5).
    """
    if token == "|":
        return "separator"
    if token in ("+", "-"):
        return "mantissa"  # FloatSequences.encode's leading sign token
    if token.startswith("N") and (token[1:].isdigit() or (len(token) > 1 and token[1] == "+") or (len(token) > 1 and token[1] == "-")):
        return "mantissa"  # FloatSequences.encode's "N<mantissa digits>"
    if token.startswith("E") and token[1:].lstrip("-").isdigit():
        return "exponent"  # FloatSequences.encode's "E<exponent>"
    if token.startswith("INT"):
        return "mantissa"  # ConstantEncoder / integer-literal sign marker
    if token.replace("-", "", 1).isdigit():
        return "mantissa"  # a bare digit token following an INT+/INT- marker
    return "operator"
