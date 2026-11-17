---
name: session-continuity
description: Checkpoint a live research session so another Codex/worker invocation or watchdog can resume without human reconstruction.
---
# Session Continuity

Before session/turn completion:
1. update `GPU_RUNmultiAI/research_state.md`
2. persist task outputs or commits
3. record unfinished worker state
4. record exact next action
5. set hard_stop and reason if applicable
6. otherwise leave campaign `status: active`

Never use "continue autonomously" as a substitute for persistent state.
A future watchdog should need only the repository and state file to resume.
