# Compute Budget and Hardware

Before a full GPU run:
- inspect GPU usage and temperature
- inspect disk
- run smoke test
- define per-cycle compute ceiling

Autonomous execution may proceed within the ceiling.

Hard stop if:
- substantial ceiling increase is required
- unsafe GPU/storage state appears
- repeated crash loops consume compute without information
- new paid service/credentials are needed

A failed hypothesis is not justification for unlimited compute.
