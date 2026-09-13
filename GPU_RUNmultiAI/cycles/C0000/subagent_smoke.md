# C0000-T004 Codex subagent smoke

## Scope

Infrastructure-only, read-only validation. This is not a scientific result.

## Observed state

- Integration branch: `20260912_multiAI_research`
- Base/invocation commit: `4a97d31ec77c286c1305529c6d57f6836e498b75`
- Canonical `.agent/` rules and `GPU_RUNmultiAI/research_state.md`: readable
- Claude/Cursor/Gemini wrapper dependencies: resolved and executable
- Three C0000 worktrees: present, clean at inspection, and attached to distinct branches
- Unrelated legacy GPU_RUN5 worktree records: eight prunable records, left untouched

## Verdict

**PASS** — a Codex subagent received a bounded self-contained task, independently inspected primary infrastructure,
reported a state mismatch, and later completed a write/validate/commit fallback in the Gemini task worktree.

The subagent did not inspect or import scientific content from PR #4 / `GPU_RUNclaude1`.
