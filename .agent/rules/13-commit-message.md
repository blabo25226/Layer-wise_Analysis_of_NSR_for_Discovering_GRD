
# Git Commit Message Rule

Commit messages must be concise.

Format:
<imperative summary, preferably <= 72 characters>

Optional body:

- Only when necessary
- Maximum 2-4 short lines
- Describe WHAT changed and WHY
- Do not include investigation history, experiment results, agent discussions,
  self-criticism, audit trails, or research conclusions.

Detailed reasoning belongs in:

- research reports
- issue/PR descriptions
- cycle logs
- documentation

Bad:
"Retract the non-identity claim: ... [50 lines of analysis]"

Good:
"Retract incorrect affine rewrite finding"

Do not use commit messages as research logs.
