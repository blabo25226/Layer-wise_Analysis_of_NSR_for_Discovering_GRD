# Compute budget and hardware

Choose experiments by expected information gain divided by compute and engineering cost.

Before large runs:
- verify correct device/environment
- verify disk capacity
- verify output path isolation
- run focused tests
- run a smoke test
- establish a compute ceiling

Do not repeatedly crash-loop the GPU or fill storage without new information.
A modest recoverable run failure is not a hard stop; diagnose and retry within the declared budget.
