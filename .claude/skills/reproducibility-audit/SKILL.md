---
name: reproducibility-audit
description: Audits LANSR code and experiment design for leakage, split mistakes, seed unfairness, baseline budget mismatch, checkpoint confusion, hidden fallback, and artifact provenance errors. Use before every full experiment and after major implementation changes.
---

# Reproducibility Audit

Audit:
- branch and commit
- dirty working tree interpretation
- data provenance
- split construction
- trajectory split before derivative construction when derivatives are used
- validation-only model selection
- final-test sealing
- paired seeds/data order/init
- equal hyperparameter opportunities
- equal or explicitly reported compute budget
- failure handling
- checkpoint SHA256 and architecture
- no runtime dependency on investigation-only code
- no old result reuse
- manifest completeness
- resume semantics
- per-problem prediction preservation

Severity:
- CRITICAL
- MAJOR
- MINOR
- NOTE

CRITICAL blocks the full run.
