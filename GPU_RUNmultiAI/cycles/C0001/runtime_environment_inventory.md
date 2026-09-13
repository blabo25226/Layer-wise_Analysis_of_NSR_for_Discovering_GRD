# C0001 runtime environment inventory

Date: 2026-09-13
Mode: read-only discovery; no installation or environment mutation

## Suitable existing environment

- Python: `/home/blabo/miniconda3/envs/lansr310/bin/python`
- Python version: 3.10.20
- NumPy: 2.2.6
- SciPy: 1.15.3
- PyTorch: 2.5.1+cu124
- CUDA runtime reported by PyTorch: 12.4
- CUDA available: yes
- scikit-learn: 1.7.2
- OmegaConf: 2.1.2
- SymPy: 1.13.1
- NumExpr: 2.14.1
- pytest: 8.4.2
- `pip check`: no broken requirements

The C0001 GRN, structural evaluation, Scaler, wrapper, simplifier and formula
modules imported successfully in this environment.  Because CUDA is visible,
the CPU-only C0001 audit must explicitly verify CPU execution and zero model
decode/GPU calls.

## Checkpoint inventory

- Path: `assets/odeformer/weights/odeformer.pt`
- Size: 464,822,385 bytes
- SHA256: `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`
- The checksum matches the repository configuration and README.
- The checkpoint was not loaded; C0001 does not require model decode.

## Reproducibility notes

The environment is suitable but not immutable.  Before an accepted run, save
both `conda list --explicit` and `pip freeze --all`, record all actual package
versions in the manifest, and do not update the environment between initial and
resume execution.

The vendored ODEFormer requirements contain older conflicting pins.  Follow
`third_party/README.md`: do not install the vendored tree as an editable package;
use its repository runtime path.  Missing upstream-only packages were not
needed by the C0001 CPU path.

Other discovered Python environments used Python 3.14 and lacked required
scientific dependencies.  No Docker, Podman, uv, Mamba or Micromamba runtime was
available.  No environment was created or modified.
