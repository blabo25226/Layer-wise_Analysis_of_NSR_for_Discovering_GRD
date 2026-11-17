# Test data and leakage

- Validation is for ranking, tuning, early stopping, model selection, and design iteration.
- Final test is accessed only after the relevant method and endpoint are frozen.
- Do not use final-test observations to choose layers, seeds, hyperparameters, equation filters, or metrics.
- Preserve split provenance and construct derivative/trajectory features only in an order that does not leak across
  temporal or structural splits.
- If leakage is discovered, mark the affected conclusion invalidated and create a clean rerun rather than patching
  the claim.
- Sealed or holdout artifacts must be listed in state and accessed only by the stage/role that is allowed to do so.
