---
name: symbolic-regression-evaluation
description: Applies the LANSR-specific evaluation contract for symbolic regression and ODE discovery. Use whenever analyzing or comparing predicted equations, ODEFormer candidates, NeSymReS outputs, GRN equations, or layer interventions.
---

# Symbolic Regression Evaluation

Never collapse evaluation into one fit score.

Separate:

## Numerical fit
- NMSE
- R²
- trajectory reconstruction
- generalization trajectory error

## Formula recovery
- exact recovery
- canonical equivalence
- symbolic equivalence
- skeleton recovery
- tree-edit or structural distance

## Variables
- precision
- recall
- F1
- unnecessary variables

## Candidate generation and selection
When candidate sets are available:
- truth/skeleton coverage in candidate set
- oracle best candidate
- selected candidate
- generation failure vs selection failure

## Safety/validity
- parse validity
- NaN/Inf
- integration failure
- denominator margin
- singularity
- extrapolation behavior
- biologically impossible values when relevant

## Complexity
- node count
- operator count
- equation length

## Layer analysis
Keep distinct:
- probe/readout
- gradients
- representation similarity
- causal intervention/ablation
- IOLE/single-layer adaptation
- selective fine-tuning

High R² does not prove correct equations.
