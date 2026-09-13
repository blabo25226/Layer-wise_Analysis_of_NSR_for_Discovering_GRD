---
name: implementation-handoff
description: Turn a frozen scientific plan into a bounded implementation task for Cursor/Claude/Luna.
---
# Implementation Handoff

Before coding:
- inspect existing utilities (delegate to Cursor when 5+ substantive files)
- define minimal reusable changes
- state frozen scientific constraints
- define expected files/artifacts
- define acceptance tests
- isolate write scope

Route multi-file implementation to Cursor `repo-operator` first per `.agent/rules/08-routing-and-delegation.md`.

Implementation rules:
- no final-test-driven edits
- add tests
- fail explicitly
- preserve old artifacts
- save equations/failures/provenance
- scientific design changes return to the PI rather than being silently implemented
