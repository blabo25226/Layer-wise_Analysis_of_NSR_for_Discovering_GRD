# GPU_RUNclaude1 — Claude Autonomous Research Track

## Purpose

`GPU_RUNclaude1` is an autonomous research track separated from the human-led LANSR research line.

- Branch: `20260909_researce_GPU_RUNclaude1`
- Working campaign directory: `GPU_RUNclaude1/`
- Main supervisor agent: `lansr-research-supervisor`
- Main loop specification: `RESEARCH_LOOP.md`
- Persistent state: `research_state.md`

The default operating mode is:

> Claude continues research autonomously.  
> Humans periodically read reports and syntheses.  
> Routine scientific failure is not a stop condition.

## Start

From the repository root:

```bash
git branch --show-current
git status --short
claude --agent lansr-research-supervisor
```

Then instruct:

```text
Read GPU_RUNclaude1/RESEARCH_LOOP.md and GPU_RUNclaude1/research_state.md.
Start or continue the autonomous LANSR research loop.
Use the configured specialist subagents and skills.
Do not pause for routine decisions; stop only at a documented hard stop.
```

## Human-facing outputs

Humans should normally inspect:

```text
GPU_RUNclaude1/reports/
GPU_RUNclaude1/syntheses/
GPU_RUNclaude1/research_state.md
GPU_RUNclaude1/human_review_queue.md
```

Every cycle must produce a research report whether the hypothesis is supported, unsupported, or undecidable.

## Cycle ID

Use sequential IDs:

```text
C0001
C0002
C0003
...
```

Hypotheses use:

```text
H0001
H0002
...
```

## Important distinction

A high trajectory reconstruction score is not equivalent to correct symbolic recovery.
A correct-looking symbolic equation is not automatically a biological causal mechanism.
These distinctions are mandatory throughout GPU_RUNclaude1.
