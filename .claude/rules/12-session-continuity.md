# Session Continuity and the Research Loop

## Why the loop stops on its own

Claude Code is turn-based. A turn ends when the assistant stops making tool calls.

- While background subagents are running, each completion **re-invokes** the supervisor
  automatically, so the research loop continues without intervention.
- When every background task has finished and the supervisor writes its report, **nothing remains to
  re-invoke it**, and the turn ends — even mid-cycle, even with an explicit instruction to continue.

An instruction like "continue autonomously and never stop" does not change this. It governs *decision
making* (do not stop for a negative result, a refuted hypothesis, or a fixable bug), not the
turn structure.

## The mechanism that actually persists

Use `/loop`. It re-fires a prompt so the supervisor is re-entered after the chain drains.

```
/loop GPU_RUNclaude1の自律研究ループを継続。GPU_RUNclaude1/RESEARCH_LOOP.md のStage順に進め、
GPU_RUNclaude1/research_state.md の現在位置から再開する。hard stop以外では停止しない。
```

- Omit the interval to let the supervisor self-pace via `ScheduleWakeup`. Preferred for this campaign,
  because cycle stages have very uneven durations (a literature pass and a full CPU experiment differ
  by orders of magnitude).
- Give an interval (`/loop 30m ...`) only when polling an external state the harness cannot notify on.
- Do **not** schedule short wakeups to poll for background subagents. Harness-tracked work re-invokes
  the supervisor on completion, so polling is wasted. A long fallback (1200 s or more) exists only to
  survive a hung or silently-dead task.
- End the loop with `ScheduleWakeup(stop: true)`, or the user can stop it from `/tasks`.

## `/schedule` is not a substitute

`/schedule` runs cron-driven agents in the cloud, as **separate sessions**. They do not inherit the
current session's context — frozen preregistration content, retractions, standing rules, unresolved
reviewer findings. Reconstruction from `research_state.md` is possible by design, but same-session
`/loop` preserves continuity and is preferred while a cycle is in flight.

## `research_state.md` is the only durable state

Chat memory is not state. Neither is a subagent's summary. `GPU_RUNclaude1/research_state.md` is the
single artifact from which a cold session can reconstruct the campaign, so it must be accurate enough
to resume from at any moment, not only at cycle boundaries.

Whenever the supervisor is about to end a turn mid-cycle, `research_state.md` must already record:
- the current cycle ID and the stage within it
- which frozen preregistration version is binding
- what is running, what is blocked, and on what
- any retraction or correction not yet reflected in downstream artifacts
- the next concrete action

Do not rely on being re-invoked to write this down later.
