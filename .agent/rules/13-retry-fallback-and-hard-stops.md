# Retry, fallback and hard stops

## Recoverable failures

Examples:
- worker process exits nonzero
- test failure
- implementation bug
- null/negative result
- reviewer disagreement
- one experiment crash
- missing optional artifact that can be regenerated

Default response:
1. diagnose
2. retry once when safe
3. route to a different worker/model if useful
4. reduce scope or create a new preregistered cycle if scientific design changed
5. continue

## Hard stops

Stop autonomous research only for conditions such as:
- wrong branch/worktree with risk of destroying unrelated work
- unavoidable leakage that cannot be isolated
- credentials/new paid access required
- private/confidential data concern
- destructive Git/history operation required
- unsafe hardware/storage state
- substantial compute ceiling increase requiring human approval
- ethics/licensing decision requiring a human
- repeated crash loop with no new information
- contradictory repository state that cannot be reconciled safely

Always persist a precise hard-stop reason and recovery request.
