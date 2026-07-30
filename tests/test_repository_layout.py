"""Regression checks for executable paths after repository reorganization."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gpu_shell_entrypoints_resolve_repository_root_from_ops_directory() -> None:
    for name in ("run_gpu_pipeline.sh", "run_gpu_campaign.sh"):
        source = (ROOT / "scripts" / "ops" / name).read_text(encoding="utf-8")
        assert 'SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)' in source
        assert 'REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)' in source
        assert 'cd "$REPO_ROOT"' in source
