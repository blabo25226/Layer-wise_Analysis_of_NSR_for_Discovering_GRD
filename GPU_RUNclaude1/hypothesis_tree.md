# Hypothesis Tree

This is the persistent tree of competing explanations and research directions.

## Status labels
- `OPEN`
- `ACTIVE`
- `SUPPORTED`
- `UNSUPPORTED`
- `UNDECIDABLE`
- `INVALIDATED`
- `DEFERRED`
- `ABANDONED`

## Root problem

Why do current neural symbolic regression systems often achieve good trajectory fit while failing robust structural/formula recovery for GRN-like dynamics?

## Initial branches

### H-A — Generation bottleneck
Status: OPEN

The true GRN structure is often absent from the candidate set, so no candidate selection procedure can recover it.

Competing subhypotheses:
- H-A1: pretrained grammar/distribution underrepresents Hill/variable-denominator structures.
- H-A2: beam/search budget is insufficient.
- H-A3: tokenization/constant representation hinders recovery.
- H-A4: dimensionality causes candidate coverage collapse.

### H-B — Selection bottleneck
Status: OPEN

The true structure enters the candidate set, but trajectory-local scoring selects alternative equations.

Subhypotheses:
- H-B1: multiple initial conditions improve identifiability.
- H-B2: structural regularization improves selection.
- H-B3: out-of-trajectory evaluation improves selection.

### H-C — Adaptation bottleneck
Status: OPEN

Fine-tuning improves in-domain structure at the cost of prior capability/generalization.

Subhypotheses:
- H-C1: selective FT improves Pareto tradeoff.
- H-C2: layer selection criterion is the main limitation.
- H-C3: parameter-efficient adaptation outperforms literal layer selection.

### H-D — Layer interpretation mismatch
Status: OPEN

Different "important layer" metrics answer fundamentally different questions rather than noisily estimating one latent ranking.

Subhypotheses:
- H-D1: probe = representational availability.
- H-D2: ablation = causal necessity.
- H-D3: IOLE = adaptation capacity.
- H-D4: their disagreement is predictable from task stage or token position.

### H-E — Identifiability/data bottleneck
Status: OPEN

Formula ambiguity arises from insufficient trajectory excitation rather than model weakness.

Subhypotheses:
- H-E1: initial-condition diversity is more important than sample density.
- H-E2: intervention trajectories reduce equivalence classes.
- H-E3: noise/subsampling interacts with structural ambiguity nonlinearly.

The supervisor must refine this tree from literature and completed experiments.
