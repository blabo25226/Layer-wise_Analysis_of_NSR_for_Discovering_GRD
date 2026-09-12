# Push and Pull Request Maintenance

Authorized by the user on 2026-09-09. This **supersedes** the earlier restriction
"Push only if allowed by repository/user settings" in `RESEARCH_LOOP.md` Stage 12, and the general
default of pushing only on an explicit per-instance request. No further confirmation is needed for
routine pushes or PR description updates on the campaign branch.

## Push

Push to the campaign branch at a moderate, regular cadence. Do not ask first.

Push when:
- a cycle stage completes (preregistration frozen, implementation done, smoke passed, experiment
  finished, report written, manifest archived)
- a retraction or correction lands — these must not sit unpushed, because a wrong claim in an
  unpushed commit is invisible to reviewers
- roughly every few commits, so the remote never trails far behind

Do not push:
- mid-edit or with a broken test suite. Run `python -m pytest -q` first and keep it green
- with `--force` or any history rewrite. Still forbidden, without exception
- to `main` or any branch other than the campaign branch, unless explicitly asked
- large raw artifacts or checkpoints. `results/runs/` stays gitignored; preserve hashes and paths

Only the campaign branch `20260909_researce_GPU_RUNclaude1` is in scope. Opening, merging or closing
a PR still requires an explicit request; **updating an open PR's description does not**.

## Pull request description

Keep the open PR's body current as the campaign's human-facing summary. Update it at a moderate
cadence — not every commit, but do not let it go stale across a whole cycle.

Update the PR body when:
- a cycle completes, or its verdict changes (supported / unsupported / undecidable / invalidated)
- a preregistration is frozen, amended or superseded
- a claim is retracted or corrected
- a review returns CRITICAL findings, or a gate flips
- a new instrument fact is established that constrains future work

The body should let a reviewer who has read no other file understand: what question the cycle asks,
what is frozen, what has been established, what was retracted, what is still open, and where to push
back. Prefer appending to a dated running log over rewriting history, so a reviewer can see how the
campaign's understanding changed. State negative and null results as plainly as positive ones, and
never quietly drop a retraction from the body once it has appeared there.

### Mechanics — `gh pr edit --body-file` can silently fail

Observed 2026-09-09 with gh 2.46.0: `gh pr edit 4 --body-file <path>` exited without error (emitting
only an unrelated Projects-classic deprecation notice) yet **left the body empty**. Reading it back
and appending then destroyed the description outright.

Use the REST API instead, and always verify:

```bash
python3 -c "import json;json.dump({'body':open('BODY.md').read()},open('P.json','w'))"
gh api -X PATCH repos/<owner>/<repo>/pulls/<n> --input P.json --jq '.body | length'
gh api repos/<owner>/<repo>/pulls/<n> --jq '.body' | wc -c      # confirm non-trivial
```

Rules that follow from this:

- **Never append to a body you have not verified you actually read.** A read that returns one byte is
  a failed read, not an empty description. Check the byte count before appending.
- **Always verify after writing**, by reading the body back and confirming a plausible length.
- **Keep the full assembled body in the scratchpad** (`pr4_body.md` + the running log), so the
  description can be reconstructed if a write clobbers it. Write bodies to the scratchpad, never into
  the repository.

## Relationship to the commit-message rule

`.claude/rules/13-commit-message.md` keeps commit messages short. That rule and this one work
together: detailed reasoning belongs in the PR description, the cycle report and the campaign logs —
**not** in commit messages. When there is a lot to say, say it in the PR body and keep the commit
subject to one line.
