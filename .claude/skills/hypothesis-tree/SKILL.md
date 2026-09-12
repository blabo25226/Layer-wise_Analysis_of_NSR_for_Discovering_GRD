---
name: hypothesis-tree
description: Maintains a tree of competing scientific hypotheses and chooses the next LANSR experiment by expected information gain rather than benchmark optimism. Use at the beginning and end of every GPU_RUNclaude1 cycle and after any unexpected result.
---

# Hypothesis Tree

For each hypothesis record:
- ID
- parent hypothesis
- status
- falsifiable statement
- supporting observations
- conflicting observations
- competing explanations
- literature status
- expected information gain
- compute cost
- experiment needed to discriminate
- result required to reject it

Prefer experiments that distinguish multiple explanations simultaneously.

Do not repeatedly optimize one benchmark if the experiment no longer changes scientific belief.

Update:
`GPU_RUNclaude1/hypothesis_tree.md`.
