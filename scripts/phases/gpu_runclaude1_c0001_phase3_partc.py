"""GPU_RUNclaude1 C0001 Phase 3: Part C -- model error vs search error (v2 §8.2, §8.3).

GPU, forward passes only. Runs only on the in-support subset from Phase 2.
``--smoke`` scores a small number of real cells (default 2) end to end --
conditioning-identity assertions, the summed-log-prob regression identity
(NC1), and the paired Stahlberg-Byrne indicator -- and asserts peak VRAM
stays within the frozen ceiling. It does not run the full corpus; that is
Stage 6/7's job.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_runclaude1 import config as c0001_config  # noqa: E402
from gpu_runclaude1.constants import PEAK_VRAM_GIB_CEILING, SUM_LOGPROB_REGRESSION_TOLERANCE  # noqa: E402
from gpu_runclaude1.io_allowlist import GPU_RUN5_ALLOWLIST_RELATIVE, InstrumentedOpener, install_sealed_audit_hook, sealed_open_guard  # noqa: E402
from gpu_runclaude1.partc import cell_input_payload_sha256, verify_cell_identity  # noqa: E402

GPU_RUN5_SOURCE_RUN = ROOT / "results" / "runs" / "gpu_run5_20260823_ddd267b0"
CHECKPOINT_PATH = ROOT / "assets" / "odeformer" / "weights" / "odeformer.pt"


# v2.1 Gate B->C. Supervisor finding 2026-09-09: v2.1 specifies this gate but it
# was not implemented here, leaving a preregistered gate dependent on operator
# discipline. Made mechanical below, before any GPU work.
PART_C_MIN_IN_SUPPORT = 30  # v2.1 Gate B->C power floor

# v2.1 §12.1: per-component gain, stratum, and family, one row per component.
# Gate B->C item (ii)'s second half needs this to verify in-support systems
# truly have zero Part A component gains.
PART_A_COMPONENT_SUMMARY_RELATIVE = "phase1/partA_component_summary.json"


def _verdict_of_record(primary: dict | None) -> str | None:
    """The verdict of record, not merely the stored ``verdict`` field.

    Supervisor finding 2026-09-09: ``compute_primary_endpoint`` (before its
    own fix, same date) always wrote ``verdict_non_match_direction`` even
    when the two-sided sensitivity analysis disagreed on the rung, so an
    older or externally produced ``partA_endpoints.json`` can carry a
    ``verdict`` that looks like an ordinary ladder rung
    (e.g. ``no_gain_observed_bound_only``) while ``sensitivity_agrees`` sits
    ``false`` right beside it. v2.1 §10.3 lists that disagreement as one of
    the ``undecidable`` criteria in its own right, so this gate derives the
    verdict of record from both fields rather than trusting ``verdict``
    alone -- robust to an artifact written before the endpoints.py fix, and
    correct for one written after it.
    """
    if not primary:
        return None
    if primary.get("sensitivity_agrees") is False:
        return "undecidable (two-sided sensitivity disagreement)"
    return primary.get("verdict")


def gate_b_to_c(run_root: Path) -> dict:
    """Decide whether Part C may run at all (v2.1 Gate B->C).

    Three independent refusals, item (i) split across two:

    1. Part C is **not** run if Part A confirmed a matcher-attributable gain.
       A confirmed gain means E0 is live, and v2.1 gives replication priority
       over the E2/E3 question -- running Part C would spend GPU budget on a
       question the cycle has been redirected away from.
    2. Part C is **not** run if Part A's verdict of record is any
       ``undecidable`` variant (v2.1 §10.1 Gate B->C item (i): "Proceed to
       Part C only if ... Part A is **not** `undecidable`"). Supervisor
       finding 2026-09-09: this half of item (i) was entirely unimplemented
       here, so a run whose Part A landed on ``undecidable`` (via the
       sensitivity-disagreement path above, or any other) proceeded to Part C
       anyway -- a preregistered gate violation, not a judgment call.
    3. Part C requires at least ``PART_C_MIN_IN_SUPPORT`` in-support systems
       (item (ii) first half), **and** every in-support system must show
       zero Part A component gains (item (ii) second half: "in-support
       truths that were still never generated"). The second half needs
       ``phase1/partA_component_summary.json``; its absence is a refusal,
       never an assumed pass, exactly like every other missing-artifact case
       in this function.

    A missing upstream artifact is a refusal, never a pass: Part C must not run
    on the assumption that an unwritten gate would have been satisfied.
    """
    reasons: list[str] = []
    verdict = None
    n_in_support = None
    in_support_system_ids = None
    component_gain_violations: list[str] | None = None

    endpoints_path = run_root / "phase1" / "partA_endpoints.json"
    if not endpoints_path.is_file():
        reasons.append(f"Part A endpoints missing: {endpoints_path}")
    else:
        primary = json.loads(endpoints_path.read_text(encoding="utf-8")).get("primary")
        verdict = _verdict_of_record(primary)
        if verdict == "matcher_attributable_gain_confirmed":
            reasons.append(
                "Part A verdict is matcher_attributable_gain_confirmed; v2.1 gives replication "
                "priority over Part C"
            )
        elif verdict is None:
            reasons.append("Part A verdict absent from partA_endpoints.json")
        elif str(verdict).startswith("undecidable"):
            reasons.append(
                f"Part A verdict of record is {verdict!r}; v2.1 Gate B->C item (i) forbids "
                "Part C when Part A is undecidable"
            )

    support_path = run_root / "phase2" / "partB_in_support_systems.json"
    if not support_path.is_file():
        reasons.append(f"Part B in-support census missing: {support_path}")
    else:
        support_payload = json.loads(support_path.read_text(encoding="utf-8"))
        n_in_support = support_payload.get("n_in_support")
        in_support_system_ids = support_payload.get("system_ids")
        if not isinstance(n_in_support, int):
            reasons.append("Part B n_in_support absent or not an integer")
        elif n_in_support < PART_C_MIN_IN_SUPPORT:
            reasons.append(
                f"n_in_support {n_in_support} < {PART_C_MIN_IN_SUPPORT} (v2.1 Gate B->C power floor)"
            )

    if in_support_system_ids is not None:
        summary_path = run_root / PART_A_COMPONENT_SUMMARY_RELATIVE
        if not summary_path.is_file():
            reasons.append(
                f"Part A component summary missing: {summary_path}; cannot verify Gate B->C item "
                "(ii)'s zero-component-gain condition for the in-support systems"
            )
        else:
            summary_rows = json.loads(summary_path.read_text(encoding="utf-8"))
            in_support_set = set(in_support_system_ids)
            offending = sorted(
                {
                    str(row.get("system_id"))
                    for row in summary_rows
                    if row.get("system_id") in in_support_set and int(row.get("gain") or 0) == 1
                }
            )
            component_gain_violations = offending
            if offending:
                shown = ", ".join(offending[:5]) + ("..." if len(offending) > 5 else "")
                reasons.append(
                    f"{len(offending)} in-support system(s) show a nonzero Part A component gain, "
                    f"contradicting Gate B->C item (ii): {shown}"
                )

    return {
        "gate": "B->C",
        "ok": not reasons,
        "reasons": reasons,
        "part_a_verdict": verdict,
        "n_in_support": n_in_support,
        "min_in_support_required": PART_C_MIN_IN_SUPPORT,
        "component_gain_violations": component_gain_violations,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUNclaude1 C0001 Phase 3 (Part C)")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--smoke-cells", type=int, default=2)
    parser.add_argument("--allow-cpu", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_root = c0001_config.resolve_run_dir_for_phase(args.run_id, is_first_phase=False)
    out_dir = c0001_config.phase_dir(run_root, 3)

    if args.dry_run:
        c0001_config.write_manifest(out_dir, 3, "dry_run", note="dry-run: no GPU work, no data touched")
        print(f"Phase 3 dry-run: {out_dir}")
        return 0

    # v2.1 Gate B->C, enforced before any GPU work. --smoke exercises the Part C
    # code path itself and runs before Parts A/B exist, so the gate is enforced
    # only on a real invocation -- the same convention as Phase 1's hard abort.
    if not args.smoke:
        gate = gate_b_to_c(run_root)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "gate_b_to_c.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
        if not gate["ok"]:
            c0001_config.write_manifest(out_dir, 3, "skipped", go_conditions=gate)
            print(f"Phase 3 skipped by Gate B->C: {gate['reasons']}")
            return 0

    import numpy as np
    import torch

    from gpu_run4.architecture import unwrap_model
    from gpu_run4.training import (
        teacher_forced_summed_logprob,
        teacher_forced_summed_logprob_batch,
        teacher_forcing_loss,
    )
    from gpu_run4_runtime import load_odeformer_model, select_device
    from gpu_run5.evaluation import select_candidate
    from gpu_runclaude1.constants import (
        CELL_REENCODING_MISMATCH_CELL_MAX_FRACTION,
        FAILURE_PENALTY,
        UNRELIABLE_REENCODING_CELL_MAX_FRACTION,
    )
    from gpu_runclaude1.partc import (
        audit_reencoding_roundtrip,
        check_distinct_payload_count,
        classify_token_class,
        stahlberg_byrne_indicator,
    )
    from gpu_runclaude1.partc_endpoints import (
        compute_c2s9,
        compute_cell_rank_panel,
        corpus_attribution_rule,
        corpus_proportion_endpoint,
        evaluate_null_credibility,
        reference_resolution_gate,
        rollup_system,
        two_stage_cluster_bootstrap_continuous,
    )
    from gpu_runclaude1.partc_reencoding import infix_to_model_tokens, reencode_infix_via_model

    device = select_device(allow_cpu=args.allow_cpu)
    if torch.cuda.is_available():
        # v2.1 V2-MIN-10: a real allocator cap at the frozen VRAM ceiling,
        # not only a post-hoc tripwire -- GPU 0 is shared with the user's
        # live desktop. set_per_process_memory_fraction takes a fraction of
        # the *device's total* memory, not of what happens to be free right
        # now, so this fails fast (torch.cuda.OutOfMemoryError) rather than
        # silently degrading if the process ever tries to exceed the ceiling.
        total_bytes = torch.cuda.get_device_properties(0).total_memory
        ceiling_bytes = PEAK_VRAM_GIB_CEILING * (1024 ** 3)
        fraction = min(ceiling_bytes / total_bytes, 1.0)
        torch.cuda.set_per_process_memory_fraction(fraction, device=0)
        torch.cuda.reset_peak_memory_stats()
    model = load_odeformer_model(CHECKPOINT_PATH, device=device)
    env = unwrap_model(model).env

    from gpu_runclaude1.io_allowlist import enumerate_validation_cells

    install_sealed_audit_hook()  # v2.1 §2.4 item 7a: process-wide, before any file access
    allowlist = [GPU_RUN5_SOURCE_RUN / rel for rel in GPU_RUN5_ALLOWLIST_RELATIVE]
    opener = InstrumentedOpener(allowlist)
    all_cell_paths = enumerate_validation_cells(GPU_RUN5_SOURCE_RUN / "phase3")
    opener.extend_allowlist(all_cell_paths)
    with sealed_open_guard():
        validation_rows = opener.read_json(GPU_RUN5_SOURCE_RUN / "phase2" / "validation.json")
        rows_by_system = {row["system_id"]: row for row in validation_rows}

        n_cells = args.smoke_cells if args.smoke else len(all_cell_paths)
        cells = [opener.read_json(p) for p in all_cell_paths[:n_cells]]

    # v2 §8.2: Part C runs only on the in-support subset from Part B. --smoke
    # runs before Part B necessarily exists (same convention as Gate B->C
    # above), so it scores whatever cells it is given without this filter.
    in_support_system_ids: set | None = None
    n_in_support: int | None = None
    if not args.smoke:
        support_payload = json.loads(
            (run_root / "phase2" / "partB_in_support_systems.json").read_text(encoding="utf-8")
        )
        in_support_system_ids = set(support_payload["system_ids"])
        n_in_support = int(support_payload["n_in_support"])

    records: list[dict] = []
    regression_checks: list[dict] = []
    payload_hashes_by_system: dict[str, set] = {}
    n_cell_identity_mismatches = 0
    n_cells_considered_for_reencoding = 0
    n_cells_unreliable_reencoding = 0
    n_candidates_total = 0
    n_candidates_mismatch = 0
    per_system_sb_sel: dict[str, list[int]] = {}
    per_system_sb_best: dict[str, list[int]] = {}
    per_system_family: dict[str, str] = {}
    per_system_gap_summed: dict[str, list[float]] = {}
    per_system_gap_per_token: dict[str, list[float]] = {}
    rank_panels = []
    gt_token_lengths_pool: list[int] = []
    gt_logprob_sums_pool: list[float] = []
    sb_sel_pool: list[int] = []
    token_class_ranks: dict[str, list[int]] = {}

    with torch.no_grad():
        for cell in cells:
            if in_support_system_ids is not None and cell["system_id"] not in in_support_system_ids:
                continue  # v2 §8.2: out-of-support systems conflate E1' with E2

            identity = verify_cell_identity(cell)
            if not identity.ok:
                n_cell_identity_mismatches += 1
                records.append({
                    "cell_id": cell.get("cell_id"), "system_id": cell.get("system_id"),
                    "excluded": True, "failure_reason": identity.failure_reason,
                })
                continue
            payload_hashes_by_system.setdefault(cell["system_id"], set()).add(identity.payload_sha256)

            row = rows_by_system[cell["system_id"]]
            input_obs = cell["observations"]["input"][0]
            times = np.asarray(input_obs["times"], dtype=float)
            traj = np.asarray(input_obs["observed_trajectory"], dtype=float)
            tree_encoded_gt = row["tree_encoded"]

            # NC1 regression check: identical computation to the original
            # (pre-wiring) script, kept unmodified.
            loss = teacher_forcing_loss(model, times, traj, tree_encoded_gt)
            sum_lp_gt, n_tok_gt, _per_token_unused = teacher_forced_summed_logprob(model, times, traj, tree_encoded_gt)
            mean_ce = float(loss)
            identity_error = abs((sum_lp_gt / n_tok_gt) - (-mean_ce))
            regression_checks.append({
                "cell_id": cell["cell_id"], "sum_logprob": sum_lp_gt, "n_tokens": n_tok_gt,
                "mean_ce": mean_ce, "identity_error": identity_error,
            })

            # v2 §8.2 step 4: re-encode + audit every candidate before any of
            # them are scored. GT-affine (C2-S4) is not attempted this cycle
            # -- a documented scope limitation, not a silent drop; see the
            # accompanying report. Every candidate that is not usable
            # (invalid, or fails the round-trip) is still recorded with its
            # failure reason (rule 03), never dropped silently.
            candidates = cell["candidates"]
            n_cells_considered_for_reencoding += 1
            candidate_audit = []
            n_mismatch_this_cell = 0
            for candidate in candidates:
                n_candidates_total += 1
                raw = str(candidate.get("candidate_formula_raw") or "")
                stored_canonical = str(candidate.get("candidate_formula_canonical") or "")
                reencoded = reencode_infix_via_model(env, raw)
                if reencoded.canonical is None:
                    roundtrip_exact = False
                    failure_reason = reencoded.failure_reason
                else:
                    audit = audit_reencoding_roundtrip(reencoded.canonical, stored_canonical)
                    roundtrip_exact = audit.exact
                    failure_reason = audit.failure_reason
                if not roundtrip_exact:
                    n_mismatch_this_cell += 1
                    n_candidates_mismatch += 1
                usable = bool(candidate.get("valid")) and roundtrip_exact
                tokens = None
                if usable:
                    tokens, tok_failure = infix_to_model_tokens(env, raw)
                    if tokens is None:
                        usable = False
                        failure_reason = tok_failure
                candidate_audit.append({
                    "candidate_index": candidate.get("candidate_index"),
                    "valid": bool(candidate.get("valid")),
                    "candidate_reencoding_roundtrip_exact": roundtrip_exact,
                    "candidate_reencoding_mismatch": (not roundtrip_exact),
                    "failure_reason": failure_reason,
                    "usable": usable,
                    "tokens": tokens,
                })

            mismatch_fraction = (n_mismatch_this_cell / len(candidates)) if candidates else 0.0
            # v2 §8.2 step 4: >10% of a cell's candidates mismatching makes
            # the cell `unreliable_reencoding`, excluded from the Part C
            # decision endpoint (but still reported).
            cell_unreliable = mismatch_fraction > CELL_REENCODING_MISMATCH_CELL_MAX_FRACTION
            if cell_unreliable:
                n_cells_unreliable_reencoding += 1

            # The selected candidate under the frozen selection rule. v2 §8.3
            # cites `gpu_run5_selection.py:11`, which is
            # `src/evaluation/gpu_run5_selection.py`'s `formula_selection_key`
            # -- a system x bundle complexity-lambda scorer, never used to
            # pick a per-cell candidate index anywhere in this repository.
            # The function that actually performs per-cell candidate
            # selection is `select_candidate` in `src/gpu_run5/evaluation.py`
            # (imported here), and its "official_reconstruction" rule -- the
            # comparator GPU_RUN5's own registered P6 prediction is measured
            # against (`_paired_p6`, "comparator": "official_reconstruction")
            # -- returns `candidate_index` 0 unconditionally. This is used as
            # the frozen selection rule; the citation mismatch is reported to
            # the supervisor as an ambiguity in v2.1 §8.3, not resolved by a
            # choice among the other rules.
            selected_index = select_candidate(candidates, "official_reconstruction", penalty=FAILURE_PENALTY, complexity_lambda=0.0)

            # Score GT-mult (with per-position ranks, for C2-S5) and every
            # usable candidate against ONE cached encoder pass (v2 §8.2
            # step 2).
            usable_entries = [c for c in candidate_audit if c["usable"]]
            sequences: list[tuple[str, list[str]]] = [("gt_mult", list(tree_encoded_gt))]
            sequences.extend((f"candidate_{entry['candidate_index']}", entry["tokens"]) for entry in usable_entries)
            seq_tokens = [tokens for _role, tokens in sequences]
            scored = teacher_forced_summed_logprob_batch(model, times, traj, seq_tokens, compute_ranks=True)
            by_role = {role: scored[i] for i, (role, _tok) in enumerate(sequences)}

            gt_sum_lp, gt_n_tok, gt_per_token, gt_ranks, gt_token_ids = by_role["gt_mult"]
            for token_id, rank in zip(gt_token_ids, gt_ranks):
                token_str = env.equation_id2word.get(token_id, "<UNK>")
                token_class_ranks.setdefault(classify_token_class(token_str), []).append(rank)

            usable_lp_sums: list[float] = []
            usable_lp_lengths: list[int] = []
            candidate_rows: list[dict] = []
            lp_sel = None
            lp_sel_token_length = None
            for entry in candidate_audit:
                role = f"candidate_{entry['candidate_index']}"
                is_selected = entry["candidate_index"] == selected_index
                base_row = {
                    "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                    "candidate_index": entry["candidate_index"], "valid": entry["valid"],
                    "candidate_reencoding_roundtrip_exact": entry["candidate_reencoding_roundtrip_exact"],
                    "candidate_reencoding_mismatch": entry["candidate_reencoding_mismatch"],
                    "is_selected_candidate": is_selected,
                    "selected_candidate_index_by_rule": selected_index,
                    "cell_reliability_flag": "unreliable_reencoding" if cell_unreliable else "reliable",
                    "generation_coverage_scope": "cell",
                }
                if entry["usable"]:
                    c_sum_lp, c_n_tok, _c_per_token, _c_ranks, _c_ids = by_role[role]
                    usable_lp_sums.append(c_sum_lp)
                    usable_lp_lengths.append(c_n_tok)
                    if is_selected:
                        lp_sel = c_sum_lp
                        lp_sel_token_length = c_n_tok
                    base_row.update({
                        "excluded": False,
                        "candidate_logprob_sum": c_sum_lp,
                        "candidate_token_length": c_n_tok,
                        "candidate_logprob_per_token": (c_sum_lp / c_n_tok) if c_n_tok else None,
                    })
                else:
                    base_row.update({"excluded": True, "failure_reason": entry["failure_reason"]})
                candidate_rows.append(base_row)

            # lp_best is an ORACLE quantity (rule 03): the max over usable
            # candidates, never presented as achieved search/selection
            # performance.
            lp_best = max(usable_lp_sums) if usable_lp_sums else None

            sb = None
            if lp_sel is not None and lp_best is not None:
                sb = stahlberg_byrne_indicator(gt_sum_lp, lp_sel, lp_best)

            # A cell contributes to the corpus decision endpoint only if it
            # is not `unreliable_reencoding` and both lp_sel and lp_best were
            # obtained (the selected candidate itself must have round-tripped
            # and been valid).
            cell_usable_for_decision = (not cell_unreliable) and (sb is not None)
            if cell_usable_for_decision:
                per_system_sb_sel.setdefault(cell["system_id"], []).append(sb.sb_sel)
                per_system_sb_best.setdefault(cell["system_id"], []).append(sb.sb_best)
                per_system_family[cell["system_id"]] = cell["family"]
                gt_token_lengths_pool.append(gt_n_tok)
                gt_logprob_sums_pool.append(gt_sum_lp)
                sb_sel_pool.append(sb.sb_sel)
                per_system_gap_summed.setdefault(cell["system_id"], []).append(gt_sum_lp - lp_sel)
                if lp_sel_token_length:
                    per_system_gap_per_token.setdefault(cell["system_id"], []).append(
                        (gt_sum_lp / gt_n_tok) - (lp_sel / lp_sel_token_length)
                    )

            if usable_lp_sums:
                rank_panels.append(compute_cell_rank_panel(gt_sum_lp, gt_n_tok, usable_lp_sums, usable_lp_lengths))

            records.append({
                "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                "excluded": False,
                "cell_input_payload_sha256": identity.payload_sha256,
                "gt_encoding": "mult",
                "gt_logprob_sum": gt_sum_lp,
                "gt_token_length": gt_n_tok,
                "gt_logprob_per_token": (gt_sum_lp / gt_n_tok) if gt_n_tok else None,
                "per_token_logprobs": gt_per_token,
                "gt_token_rank_profile": gt_ranks,
                "n_usable_candidates": len(usable_entries),
                "n_candidates_total": len(candidates),
                "selected_candidate_index_by_rule": selected_index,
                "lp_sel": lp_sel,
                "lp_best": lp_best,
                "sb_sel": sb.sb_sel if sb else None,
                "sb_best": sb.sb_best if sb else None,
                "candidate_reencoding_mismatch_fraction_this_cell": mismatch_fraction,
                "cell_reliability_flag": "unreliable_reencoding" if cell_unreliable else "reliable",
                "generation_coverage_scope": "cell",
            })
            records.extend(candidate_rows)

    peak_vram_gib = (torch.cuda.max_memory_allocated() / (1024 ** 3)) if torch.cuda.is_available() else 0.0
    regression_ok = all(r["identity_error"] < SUM_LOGPROB_REGRESSION_TOLERANCE for r in regression_checks) if regression_checks else False

    # NC3: identity assertions, including the 10-distinct-payload check (P11).
    distinct_payload_report = check_distinct_payload_count(payload_hashes_by_system)
    all_systems_distinct_ok = bool(distinct_payload_report) and all(v["ok"] for v in distinct_payload_report.values())

    unreliable_fraction = (
        (n_cells_unreliable_reencoding / n_cells_considered_for_reencoding) if n_cells_considered_for_reencoding else 0.0
    )
    overall_mismatch_rate = (n_candidates_mismatch / n_candidates_total) if n_candidates_total else 0.0

    nc = evaluate_null_credibility(
        regression_identity_ok=regression_ok,
        unreliable_reencoding_cell_fraction=unreliable_fraction,
        n_cell_identity_mismatches=n_cell_identity_mismatches,
        all_systems_distinct_payload_ok=all_systems_distinct_ok,
        n_in_support=n_in_support if n_in_support is not None else 0,
    )

    reencoding_audit = {
        "n_candidates_total": n_candidates_total,
        "n_candidates_mismatch": n_candidates_mismatch,
        "candidate_mismatch_rate": overall_mismatch_rate,
        "n_cells_considered": n_cells_considered_for_reencoding,
        "n_cells_unreliable_reencoding": n_cells_unreliable_reencoding,
        "unreliable_reencoding_cell_fraction": unreliable_fraction,
        "unreliable_reencoding_cell_max_fraction": UNRELIABLE_REENCODING_CELL_MAX_FRACTION,
        "cell_reencoding_mismatch_cell_max_fraction": CELL_REENCODING_MISMATCH_CELL_MAX_FRACTION,
        "affine_encoding_attempted_this_cycle": False,
    }
    identity_audit = {
        "n_cell_identity_mismatches": n_cell_identity_mismatches,
        "distinct_payload_report": distinct_payload_report,
        "all_systems_distinct_payload_ok": all_systems_distinct_ok,
    }

    go = {
        "regression_identity_ok": regression_ok,
        "peak_vram_within_ceiling": peak_vram_gib <= PEAK_VRAM_GIB_CEILING,
        "n_cells_scored": len(regression_checks),
        "reduced_scope_smoke": args.smoke,
        "gate_c_to_report_ok": nc.gate_c_to_report_ok,
    }
    status = "complete" if (regression_ok or not regression_checks) and go["peak_vram_within_ceiling"] else "incomplete"

    endpoints: dict = {
        "prior_information_disclosed": "GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md §0.1-§0.4",
        "reduced_scope_smoke": args.smoke,
        "n_in_support": n_in_support,
        "null_credibility": {
            "nc1_regression_identity_ok": nc.nc1_regression_identity_ok,
            "nc2_reencoding_audit_ok": nc.nc2_reencoding_audit_ok,
            "nc3_identity_assertions_ok": nc.nc3_identity_assertions_ok,
            "nc4_s7_reported": nc.nc4_s7_reported,
            "nc5_n_in_support_ok": nc.nc5_n_in_support_ok,
            "gate_c_to_report_ok": nc.gate_c_to_report_ok,
        },
    }

    if not nc.gate_c_to_report_ok:
        # v2.1 §10.1 Gate C->report: reported only if NC1-NC3 pass.
        endpoints["status"] = "undecidable"
        endpoints["reason"] = "Gate C->report failed: NC1-NC3 not all satisfied; see null_credibility"
    else:
        rollups = {
            sid: rollup_system(sid, per_system_family[sid], per_system_sb_sel[sid], per_system_sb_best.get(sid, []))
            for sid in per_system_sb_sel
        }
        family_of_system = dict(per_system_family)
        indicators_e3 = {sid: r.e3_system for sid, r in rollups.items()}
        indicators_e2 = {sid: r.e2_system for sid, r in rollups.items()}
        indicators_e3_best = {sid: r.e3_system_best for sid, r in rollups.items()}
        indicators_e2_best = {sid: r.e2_system_best for sid, r in rollups.items()}

        c2p = corpus_proportion_endpoint(indicators_e3, family_of_system, n_in_support)
        c2s1 = corpus_proportion_endpoint(indicators_e2, family_of_system, n_in_support)
        c2p_best = corpus_proportion_endpoint(indicators_e3_best, family_of_system, n_in_support)
        c2s1_best = corpus_proportion_endpoint(indicators_e2_best, family_of_system, n_in_support)

        mean_sb_rate = float(np.mean([r.sb_rate_sel for r in rollups.values() if r.sb_rate_sel is not None])) if rollups else None

        gap_summed_by_system = {sid: float(np.mean(v)) for sid, v in per_system_gap_summed.items()}
        gap_per_token_by_system = {sid: float(np.mean(v)) for sid, v in per_system_gap_per_token.items()}
        c2s3_summed = two_stage_cluster_bootstrap_continuous(gap_summed_by_system, family_of_system)
        c2s3_per_token = two_stage_cluster_bootstrap_continuous(gap_per_token_by_system, family_of_system)

        reference_gate = reference_resolution_gate(rank_panels)
        c2s9 = compute_c2s9(gt_token_lengths_pool, gt_logprob_sums_pool, sb_sel_pool)
        attribution = corpus_attribution_rule(c2p.cluster_bootstrap, c2s1.cluster_bootstrap)

        def _prop(p) -> dict:
            return {
                "k": p.k, "n": p.n, "rate": p.rate, "wilson_95": list(p.wilson_95),
                "cluster_bootstrap": {
                    "point_estimate": p.cluster_bootstrap.point_estimate,
                    "ci_low": p.cluster_bootstrap.ci_low, "ci_high": p.cluster_bootstrap.ci_high,
                    "n_resamples": p.cluster_bootstrap.n_resamples, "seed": p.cluster_bootstrap.seed,
                },
            }

        endpoints["status"] = attribution
        endpoints["C2_P_search_error_system_rate"] = {**_prop(c2p), "inference": "primary"}
        endpoints["C2_S1_model_error_system_rate"] = {**_prop(c2s1), "inference": "descriptive"}
        endpoints["C2_S2_sb_best_variants"] = {
            "mean_sb_rate_across_systems": mean_sb_rate,
            "C2_P_sb_best": _prop(c2p_best),
            "C2_S1_sb_best": _prop(c2s1_best),
            "inference": "descriptive",
        }
        endpoints["C2_S3_paired_gap"] = {
            "summed": {
                "point_estimate": c2s3_summed.point_estimate, "ci_low": c2s3_summed.ci_low, "ci_high": c2s3_summed.ci_high,
            },
            "per_token": {
                "point_estimate": c2s3_per_token.point_estimate, "ci_low": c2s3_per_token.ci_low, "ci_high": c2s3_per_token.ci_high,
            },
            "inference": "descriptive",
            "note": "the per-token variant may not bear a decision (v2 §8.3 length policy)",
        }
        endpoints["C2_S4_affine_vs_mult"] = {
            "attempted_this_cycle": False,
            "note": "GT-affine not attempted this cycle (scope limitation, see report); treated as "
            "100% AffineEncodingUnavailable, which trivially satisfies the >20%-missing drop rule",
            "dropped": True,
            "inference": "descriptive",
        }
        endpoints["C2_S5_token_rank_profile_by_class"] = {
            token_class: {
                "n": len(ranks), "mean_rank": float(np.mean(ranks)) if ranks else None,
                "median_rank": float(np.median(ranks)) if ranks else None,
            }
            for token_class, ranks in token_class_ranks.items()
        } | {"inference": "descriptive"}
        endpoints["C2_S6_rank_panel"] = {
            "gate": {
                "n_cells_considered": reference_gate.n_cells_considered,
                "n_cells_exceeding": reference_gate.n_cells_exceeding,
                "fraction_exceeding": reference_gate.fraction_exceeding,
                "gate_ok": reference_gate.gate_ok,
            },
            "interpretable": reference_gate.gate_ok,
            "mean_rank_pct_sum": (
                float(np.mean([p.rank_pct_sum for p in rank_panels if p.rank_pct_sum is not None]))
                if any(p.rank_pct_sum is not None for p in rank_panels) else None
            ),
            "mean_below_all_indicator": (
                float(np.mean([p.below_all_indicator for p in rank_panels if p.below_all_indicator is not None]))
                if any(p.below_all_indicator is not None for p in rank_panels) else None
            ),
            "inference": "descriptive",
            "note": "T=0.1 upper-tail sample (STAT-C4): a low rank does not establish model error; "
            "no E2/E3 attribution may cite this panel",
        }
        endpoints["C2_S7_reference_resolution_gate"] = {
            "n_cells_considered": reference_gate.n_cells_considered,
            "n_cells_exceeding": reference_gate.n_cells_exceeding,
            "fraction_exceeding": reference_gate.fraction_exceeding,
            "gate_ok": reference_gate.gate_ok,
            "inference": "descriptive",
        }
        endpoints["C2_S8_instrument_audit"] = {**reencoding_audit, **identity_audit, "inference": "descriptive"}
        endpoints["C2_S9_length_correlations"] = {
            "n": c2s9.n, "r_length_vs_lp_gt": c2s9.r_length_vs_lp_gt, "r_length_vs_sb_sel": c2s9.r_length_vs_sb_sel,
            "inference": "exploratory",
        }
        endpoints["corpus_attribution_rule_outcome"] = attribution
        endpoints["dead_zone_disclosed"] = (
            "neither_E2_nor_E3_predominant is the expected corpus-level outcome at n_in_support "
            "~30-60 (v2 §8.3); distinct from undecidable"
        )
        endpoints["n_systems_with_zero_usable_cells"] = max(0, (n_in_support or 0) - len(rollups))

    (out_dir / "partC_instrument_test.json").write_text(
        json.dumps({"regression_checks": regression_checks, "tolerance": SUM_LOGPROB_REGRESSION_TOLERANCE, "ok": regression_ok}, indent=2),
        encoding="utf-8",
    )
    (out_dir / "partC_identity_audit.json").write_text(json.dumps(identity_audit, indent=2), encoding="utf-8")
    (out_dir / "partC_reencoding_audit.json").write_text(json.dumps(reencoding_audit, indent=2), encoding="utf-8")
    (out_dir / "partC_endpoints.json").write_text(json.dumps(endpoints, indent=2), encoding="utf-8")
    (out_dir / "partC_cell_records.jsonl").write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    (out_dir / "gpu_telemetry.jsonl").write_text(json.dumps({"peak_vram_gib": peak_vram_gib, "device": device}) + "\n", encoding="utf-8")
    c0001_config.write_manifest(out_dir, 3, status, go_conditions=go, peak_vram_gib=peak_vram_gib)
    print(f"Phase 3 {status}: {out_dir} (peak VRAM {peak_vram_gib:.3f} GiB)")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
