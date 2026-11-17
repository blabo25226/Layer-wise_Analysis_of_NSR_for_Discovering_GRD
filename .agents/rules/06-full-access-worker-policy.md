# Full-access worker policy

Workers are expected to have normal autonomous access inside their assigned worktree:
- read/write/create/delete task files
- shell
- tests/lint/build
- ordinary Git operations
- experiment commands
- repository-local scripts
- normal research network access when the provider supports it

Do not ask the human for approval for routine task-local operations.

"Full access" does not authorize:
- credential harvesting
- reading unrelated secrets
- destructive shared-history operations
- modifying private/confidential data outside the task
- making external purchases or creating paid resources without authorization
- changing research ethics/licensing decisions on the human's behalf

If a routine operation fails because of a provider permission prompt, record it as an infrastructure issue and use the
configured fallback rather than terminating the research campaign.
