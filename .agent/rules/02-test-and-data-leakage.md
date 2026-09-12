# Test and Data Leakage

- Final test sets are sealed until methods are fixed.
- Hyperparameters, layer rankings, early stopping, and model selection use validation only.
- For trajectory data, split at the trajectory/system level before constructing derivative-derived rows when derivatives are used.
- Do not inspect final-test examples to debug model behavior.
- If leakage is discovered, invalidate affected conclusions and create a clean rerun.
