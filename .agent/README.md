# Multi-AI Research OS — Canonical Instructions

`.agent/` is the vendor-neutral source of truth for the autonomous `GPU_RUNmultiAI/` research campaign.

## Instruction precedence

1. Explicit human instruction.
2. Repository-root `AGENTS.md`.
3. `.agent/rules/*`.
4. The active role in `.agent/agents/*`.
5. The active skill in `.agent/skills/*`.
6. A task handoff file.

If instructions conflict at the same level, prefer the safer interpretation that preserves scientific validity,
existing work, and reproducibility, then record the conflict.

## Campaign scope

- Persistent campaign state: `GPU_RUNmultiAI/`
- Reusable code: `src/`, `scripts/`, `configs/`, `tests/`, and established repository locations.
- Campaign-specific plans/reviews/reports/manifests: `GPU_RUNmultiAI/`.
- Use GPU_RUN5-style explicit plans, reports, commands, provenance, and per-run artifacts, but organize repeated
  autonomous research as numbered cycles (`C0001`, `C0002`, ...).

## Historical-source boundary

The retired PR #4 / `GPU_RUNclaude1` track is a **process-design reference only**.
Do not import its scientific conclusions, results, measured values, cycle decisions, or experimental artifacts into
`GPU_RUNmultiAI/` unless the human explicitly authorizes it.

## Operating principle

All workers may have full operational access in their assigned worktree.
Prevent collisions by branch/worktree isolation and declared write scopes, not by making workers read-only.

Research should continue until a defined hard stop occurs. A model session ending is not a scientific hard stop.
Persist state so a watchdog or the next session can resume exactly.
